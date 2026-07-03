"""
Workable public Job Board widget API source.

API docs: https://help.workable.com/hc/en-us/articles/115012771647-Using-the-Workable-API-to-create-a-careers-page

Endpoint: GET https://apply.workable.com/api/v1/widget/accounts/{account_subdomain}
No authentication is required for this endpoint (confirmed live) - it's
the same public, no-auth widget API Workable's own embeddable careers-page
widgets use. This is a different surface from the authenticated SPI API
(`https://{subdomain}.workable.com/spi/v3/jobs`, requires a Bearer token
with the `r_jobs` scope) - that one is part of the full recruiting/hiring
ATS API and is not used here, per "public job listing endpoints only".

Workable is company-based rather than a single global index: each company
publishes its postings under its own "account subdomain" (slug) - the same
shape as Greenhouse/Lever/Ashby/SmartRecruiters. The list of companies to
fetch is COMPANY_SLUGS below - adding a new company later only requires
adding its slug to that list; fetch_raw() already iterates over it
automatically, no logic changes needed.

An unknown account subdomain 404s (confirmed live, unlike SmartRecruiters
which returns 200 with an empty result) - so "verified" here means both
HTTP 200 *and* a non-empty `jobs` array.

The API returns a company's entire job list in a single response - no
page/offset/cursor params are documented or exist, confirmed live (one
request returned every job for every company tested here, largest being
1,718). So, like Greenhouse/Ashby, this is a single-shot fetch per company
rather than a paginated one.

Each company is fetched independently, and a failure fetching one company
(bad slug, network error, etc.) is caught and logged so the remaining
companies still get processed - the same per-company fault isolation used
in greenhouse.py/ashby.py.

The account-level response carries a top-level `name` field (the company's
display name) - unlike Lever/Ashby, which have no company field at all -
so, like Greenhouse's `company_name`, no manual slug-to-display-name
mapping is needed; fetch_raw() just tags every job in a company's response
with that account-level name.

Each job carries a genuine public `url` field directly (confirmed live,
format `https://apply.workable.com/j/{shortcode}`), so - unlike
SmartRecruiters - no URL needs to be constructed manually.

`telecommuting` is a genuine boolean field on every job (confirmed via
live data across every company tested here), so - like Ashby's `isRemote`
- `remote` is read directly from it rather than a keyword heuristic.

Every company slug below was confirmed live against the real API before
being added: ~200 candidate slugs were tried this session (sourced from
real apply.workable.com career-page links surfaced via search, not
guessed) and only the 89 that returned HTTP 200 with at least one active
job were kept. Workable's customer base skews toward small-and-mid-size
businesses rather than large enterprises (per Workable's own published
customer stats), so - unlike Ashby/SmartRecruiters - very few Fortune
500/unicorn-scale boards could be verified live; coverage instead leans
toward staffing agencies, consulting/IT-services firms, fintech,
healthcare, legal, and retail/e-commerce brands, which is where this
project found genuine large, active Workable job boards.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://apply.workable.com/api/v1/widget/accounts"

# Company account subdomains to fetch. Every slug below was confirmed
# live against the real API (HTTP 200 and a non-empty jobs array) before
# being added. Add a new company by adding its slug here; no other code
# changes are needed - fetch_raw() iterates over this list automatically.
COMPANY_SLUGS = [
    # AI / Software
    "huggingface",
    "thingtrax",
    "smartassets",
    "becoming",
    "eqltech",
    "v2-ai",
    "satsuma",
    "rokt",
    "mealsuite",
    "enfos-inc",
    "woundlocalcareers",

    # Staffing & Recruiting
    "hire-resolve-the-top-recruitment-agency",
    "pearltalent",
    "remote-recruitment",
    "joinremotely",
    "valatam",
    "ace-it-careers-1",
    "keller-executive-search",
    "zipdev",

    # Consulting / IT Services
    "two95-international-inc-3",
    "unit8",
    "rtm-business-group",
    "itg",
    "levelagency",
    "it1",
    "c-serv",
    "tiger-analytics",
    "devsinc-17",
    "taskforce",

    # FinTech / Banking
    "wealthbridge-financial-group",
    "firsthelpfinancial",
    "smartfinancial",
    "fsnb",
    "ebcfinancialgroup",
    "aviso",
    "borrowell",
    "withplum",
    "valsoft-corp",
    "k1x",

    # Healthcare / Biotech / Pharma
    "assist-rx",
    "ascendis-pharma",
    "tetrascience",
    "symmetrio",
    "calvary-hospital",
    "wider-circle",
    "organox",
    "texashealthaction",
    "flourishresearch",
    "curology",

    # Education
    "tutor-me-education-1",
    "braven",

    # Legal
    "bushand-bush-law-group",
    "leap-legal-software",
    "legalvision",
    "zirtual-llc",
    "persuit-1",
    "lawyer",

    # Manufacturing / Logistics / Construction
    "charger-logistics-inc",
    "bergen-logistics-1",
    "mi-homes",
    "classet",

    # Cybersecurity
    "action1",
    "wavestrong",
    "aetos-systems-inc",
    "myteam",
    "dispel",
    "securityriskadvisors",
    "leadtech",
    "evolv-technology",
    "maveriscareers",

    # Retail / E-commerce
    "tarte-inc",
    "blue-nile",
    "the-normal-brand",
    "huckberry",
    "bci-brands",
    "wolfandbadger",
    "theouai",
    "hustler-marketing",
    "david-protein",
    "skylight-frame",

    # Real Estate / Hospitality
    "ahsproperties",
    "tvg-hospitality",
    "hospitable",
    "ws-development",

    # Gaming / Crypto
    "green-man-gaming",
    "stakefish",

    # Defense / Government
    "pacific-defense",
    "c4-planning-solutions-llc",
    "wearenoble",
]

REQUEST_TIMEOUT = 30


class WorkableSource(BaseJobSource):
    name = "workable"

    def fetch_raw(self):
        """Fetch every configured company's full job list from the Workable widget API."""
        jobs = []

        for slug in COMPANY_SLUGS:
            try:
                response = request_with_retry(
                    requests.get,
                    f"{API_URL}/{slug}",
                    timeout=REQUEST_TIMEOUT,
                )
                payload = response.json()
            except requests.RequestException as exc:
                print(f"[{self.name}] skipped company '{slug}': {exc}")
                continue

            # The company display name lives at the account level, not per
            # job, so it's stashed on each raw record for normalize().
            company_name = payload.get("name", "")
            page_jobs = payload.get("jobs", [])
            for job in page_jobs:
                job["_company_name"] = company_name
            jobs.extend(page_jobs)

        return jobs

    def normalize(self, raw_job):
        """Map a Workable job record onto the project's standard schema."""
        city = raw_job.get("city") or ""
        country = raw_job.get("country") or ""
        location = ", ".join(part for part in (city, country) if part) or "Unknown"

        tags = dedupe_tags(
            [raw_job["department"]] if raw_job.get("department") else None,
            [raw_job["function"]] if raw_job.get("function") else None,
            [raw_job["employment_type"]] if raw_job.get("employment_type") else None,
        )

        posted = iso_string_to_date(raw_job.get("published_on") or raw_job.get("created_at"))

        return {
            "title": raw_job.get("title", ""),
            "company": raw_job.get("_company_name", ""),
            "location": location,
            "url": raw_job.get("url", ""),
            "tags": tags,
            "remote": bool(raw_job.get("telecommuting")),
            "posted": posted,
        }
