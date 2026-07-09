"""
Recruitee (Tellent) public Careers Site API source.

Docs: https://docs.recruitee.com/reference/intro-to-careers-site-api,
https://docs.recruitee.com/reference/offers

Endpoint: GET https://{company_subdomain}.recruitee.com/api/offers/
No authentication is required (confirmed both live and in the docs, which
state outright: "This API does not require authorization and is available
under your Careers Site address"). This is a distinct surface from
Recruitee's internal ATS API, which needs a personal Bearer token created
per-account in Settings and is scoped to that account's own hiring data -
not usable by (or relevant to) a third-party aggregator like this project,
and not the API used here.

Recruitee is company-based rather than a single global index: each company
publishes its postings under its own subdomain (occasionally a custom one
picked at signup rather than the company's own name, e.g. Solutions 4
Delivery -> "s4d", Radix.AI's careers redirect to "superlinear" - its
actual Recruitee account name) - the same shape as Greenhouse/Lever/Ashby/
Workable/SmartRecruiters/Teamtailor. COMPANY_SLUGS below stores each
confirmed subdomain; adding a new company later only requires adding its
slug to that list, no other logic changes needed.

The endpoint returns a company's entire published job list in a single
response under an `offers` key, with no `meta`/`page`/`total_count`
field anywhere in the payload (confirmed live, including against a 90-job
company) - so, like the other ATS sources in this project, this is a
single-shot fetch per company, not a paginated one.

Each company is fetched independently, and a failure fetching one company
(bad slug, network error, etc.) is caught and logged so the remaining
companies still get processed - the same per-company fault isolation used
in greenhouse.py/ashby.py/workable.py/teamtailor.py.

Unlike Workable/Teamtailor, no channel-level "stash the company name on
each job" step is needed here: every offer already carries its own
`company_name` field directly (confirmed live across every company
tested).

`location` arrives pre-formatted as a single combined string (e.g.
"Hoofddorp, Noord-Holland, Nederland"), and `remote` is a genuine boolean
on every offer (confirmed live) - so, like Ashby's `isRemote` and
Workable's `telecommuting`, it's read directly rather than a keyword
heuristic. A separate `hybrid` boolean also exists but isn't used, since
this project's schema only has one remote/not-remote flag - matching
Teamtailor's choice to treat only the fully-remote state as `remote: True`.

`published_at` is "YYYY-MM-DD HH:MM:SS UTC" (e.g. "2026-07-09 08:02:15
UTC") - neither ISO 8601 nor RFC 2822, so neither of the project's
existing date utils applies; parsed locally in this module instead, the
same approach already used for Teamtailor's RFC 822 dates.

Every company slug below was confirmed live against the real API (HTTP
200 and a non-empty `offers` array) before being added, sourced from
Recruitee's own published customer case studies and search results (not
guessed) - real companies with 0 open roles at check time (e.g. Betty
Blocks) were left out, matching Workable's own inclusion bar.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry

API_URL_TEMPLATE = "https://{}.recruitee.com/api/offers/"

# Company subdomains to fetch. Every slug below was confirmed live against
# the real API (HTTP 200 and a non-empty `offers` array) before being
# added. Add a new company by adding its slug here; no other code changes
# are needed - fetch_raw() iterates over this list automatically.
COMPANY_SLUGS = [
    "transavia",
    "sirclecollection",
    "bettercollective",
    "myjewellery",
    "helloprint",
    "fastned",
    "bunq",
    "cmcom",
    "trustedshops",
    "werkenbijvancranenbroek",
    "s4d",
    "kaizo",
    "doctenasa",
    "heidelbergmaterialsbenelux",
    "peak",
    "cerbaresearch",
    "mobietrain",
    "eurail",
    "jobs",
    "vacancies",
    "superlinear",
]

REQUEST_TIMEOUT = 30


def _recruitee_date_to_iso(date_string):
    """Convert Recruitee's "YYYY-MM-DD HH:MM:SS UTC" published_at into ISO "YYYY-MM-DD"."""
    if not date_string:
        return ""
    return date_string[:10]


class RecruiteeSource(BaseJobSource):
    name = "recruitee"

    def fetch_raw(self):
        """Fetch every configured company's published offers from the Recruitee Careers Site API."""
        jobs = []

        for slug in COMPANY_SLUGS:
            try:
                response = request_with_retry(
                    requests.get,
                    API_URL_TEMPLATE.format(slug),
                    timeout=REQUEST_TIMEOUT,
                )
                payload = response.json()
            except (requests.RequestException, ValueError) as exc:
                print(f"[{self.name}] skipped company '{slug}': {exc}")
                continue

            jobs.extend(payload.get("offers", []))

        return jobs

    def normalize(self, raw_job):
        """Map a Recruitee offer record onto the project's standard schema."""
        tags = dedupe_tags(
            raw_job.get("tags") or [],
            [raw_job["department"]] if raw_job.get("department") else None,
            [raw_job["employment_type_code"]] if raw_job.get("employment_type_code") else None,
        )

        return {
            "title": raw_job.get("title", ""),
            "company": raw_job.get("company_name", ""),
            "location": raw_job.get("location") or "Unknown",
            "url": raw_job.get("careers_url", ""),
            "tags": tags,
            "remote": bool(raw_job.get("remote")),
            "posted": _recruitee_date_to_iso(raw_job.get("published_at")),
        }
