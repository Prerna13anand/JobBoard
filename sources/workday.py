"""
Workday public Careers (CXS) API source.

Endpoint: POST https://{tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
No authentication is required (confirmed live across 20 real tenants below,
with no API key, Bearer token, cookie, or even a non-default User-Agent -
plain `requests.post` with a JSON body works as-is). This is the same
public, keyless endpoint Workday's own embeddable career-site search
widget calls - there is no separate "public" vs "authenticated" split
here the way Workable/Teamtailor have one (their write-side ATS APIs
need per-account credentials Workday's read-side career search does not).

Workday is company-based rather than a single global index, and more
fragmented than Greenhouse/Lever/Ashby/Workable/Teamtailor/SmartRecruiters:
each company (a Workday "tenant") is hosted on one of several numbered
Workday data centers (wd1, wd3, wd5, wd12, wd108, etc. - confirmed live,
no consistent pattern predicts which number a given tenant uses), and
publishes its jobs under its own "site" name, which is often *not* the
tenant name itself (e.g. tenant "pwc" -> site "Global_Experienced_Careers",
tenant "matthey" -> site "Ext_Career_Site"). COMPANY_TENANTS below stores
the full (tenant, wd_server, site, display_name) tuple per company -
adding a new one later only requires adding its tuple to that list;
fetch_raw() already iterates over it automatically, no logic changes
needed.

Unlike every other ATS source in this project, Workday's endpoint genuinely
paginates via `offset`/`limit` in the POST body (confirmed live: offset=20
returns a different page, response `total` stays consistent across pages) -
`limit` is capped at exactly 20 server-side (confirmed live: limit=25/30/50
all return HTTP 400, only limit<=20 succeeds). Several tenants here have
enormous job counts (PwC: 4,340; Target: 2,000; Salesforce: 1,473) that
would take hundreds of requests to exhaust, so - matching the EURES/Adzuna
precedent elsewhere in this project for oversized indexes - each company
is capped at MAX_PAGES_PER_COMPANY (10 pages = 200 jobs), a bounded,
well-mannered sample rather than an attempt to fetch every tenant's entire
history.

Each company is fetched independently, and a failure fetching one page
(bad tenant/site, network error, non-JSON error body) is caught and
logged so the remaining companies still get processed - the same
per-company fault isolation used in greenhouse.py/ashby.py/workable.py/
teamtailor.py/recruitee.py.

The list endpoint's job records carry no company name at all (confirmed
live) and no company-scoped display name is derivable from the payload -
the same gap Ashby/Lever have - so, like Ashby's COMPANY_BOARDS, a
display name is curated per tenant in COMPANY_TENANTS rather than fetched
(fetching it would need one extra per-job detail request, since the
per-tenant `hiringOrganization.name` field only exists on the *job detail*
endpoint, GET .../job/{externalPath} - not worth doubling this source's
request count just for a label already knowable from the tenant itself).

Each job's `externalPath` (e.g. "/job/Belfast/AI-Product-Lead_JR_18068")
combines with the tenant/server/site already used for the API call to
build a working public job URL directly - confirmed live against the
`externalUrl` field on the job detail endpoint for a sample of jobs -
so no extra request is needed for that either.

`postedOn` is relative text ("Posted Today", "Posted Yesterday", "Posted
N Days Ago", "Posted 30+ Days Ago" - the exact set confirmed live across
several tenants), not an absolute date; only the job detail endpoint
carries a real ISO `startDate`. Fetching every job's detail page just for
an exact date isn't worth one extra request per job (hundreds to
thousands per run), so `postedOn` is parsed into an approximate ISO date
locally in this module instead ("30+ Days Ago" is treated as exactly 30 -
a floor, not an exact figure).

`locationsText` is a single free-text string, sometimes a place name
("Belfast"), sometimes a count ("6 Locations") for multi-location postings
with no place names at all - passed through as-is like other sources'
raw location strings. No dedicated remote/hybrid field exists anywhere in
the list payload (unlike Ashby's `isRemote`/Workable's `telecommuting`),
so `remote` is a keyword check against title + location, the same
approach used for EURES/MyJobMag/Mustakbil in this project - live checks
across several large tenants found this rarely matches, consistent with
Workday's customer base skewing toward large, office-based enterprises
and government agencies rather than remote-first companies.

Every tenant below was confirmed live (HTTP 200 and a non-zero `total`)
before being added, sourced from real myworkdayjobs.com URLs surfaced via
search, not guessed.
"""

import re
from datetime import date, timedelta

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry

# Each entry: (tenant, wd_server, site, display_name). All four are needed
# to build both the API URL and the public job URL - see module docstring.
COMPANY_TENANTS = [
    ("kainos", "wd3", "kainos", "Kainos"),
    ("pwc", "wd3", "Global_Experienced_Careers", "PwC"),
    ("salesforce", "wd12", "External_Career_Site", "Salesforce"),
    ("lseg", "wd3", "Careers", "LSEG"),
    ("matthey", "wd3", "Ext_Career_Site", "Johnson Matthey"),
    ("weir", "wd3", "Weir_External_Careers", "Weir Group"),
    ("if", "wd3", "Careers", "If Insurance"),
    ("workday", "wd5", "Workday", "Workday"),
    ("communitybrands", "wd1", "Momentive_External_Careers", "Momentive (Community Brands)"),
    ("snapfinance", "wd1", "Snap_External_Careers", "Snap Finance"),
    ("ttc", "wd1", "Toro_External_Careers", "The Toro Company"),
    ("saputo", "wd5", "Saputo_External_Careers", "Saputo"),
    ("target", "wd5", "targetcareers", "Target"),
    ("standard", "wd1", "Search", "The Standard"),
    ("medtronic", "wd1", "MedtronicCareers", "Medtronic"),
    ("maine", "wd5", "Executive", "State of Maine"),
    ("nc", "wd108", "NC_Careers", "State of North Carolina"),
    ("oregon", "wd5", "SOR_External_Career_Site", "State of Oregon"),
    ("okgov", "wd1", "okgovjobs", "State of Oklahoma"),
    ("denver", "wd1", "CCD-denver-denvergov-CSC_Jobs-Civil_service_jobs-Police_Jobs-Fire_Jobs", "City and County of Denver"),
]

PAGE_SIZE = 20  # confirmed maximum accepted by the API; anything higher returns HTTP 400
MAX_PAGES_PER_COMPANY = 10  # self-imposed cap - see module docstring

REQUEST_TIMEOUT = 30

REMOTE_KEYWORDS = ("remote", "work from home", "telecommute")

_DAYS_AGO_RE = re.compile(r"posted\s+(\d+)\+?\s+days?\s+ago", re.IGNORECASE)


def _posted_on_to_iso(posted_on):
    """Convert Workday's relative postedOn text (e.g. "Posted 3 Days Ago") to an approximate ISO date."""
    if not posted_on:
        return ""

    text = posted_on.strip().lower()
    today = date.today()

    if text == "posted today":
        return today.isoformat()
    if text == "posted yesterday":
        return (today - timedelta(days=1)).isoformat()

    match = _DAYS_AGO_RE.match(text)
    if match:
        return (today - timedelta(days=int(match.group(1)))).isoformat()

    return ""


class WorkdaySource(BaseJobSource):
    name = "workday"

    def fetch_raw(self):
        """Fetch every configured tenant's job list from the Workday CXS API, paginated up to a self-imposed cap."""
        jobs = []

        for tenant, wd_server, site, display_name in COMPANY_TENANTS:
            api_url = f"https://{tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
            job_url_base = f"https://{tenant}.{wd_server}.myworkdayjobs.com/{site}"
            offset = 0

            for _ in range(MAX_PAGES_PER_COMPANY):
                try:
                    response = request_with_retry(
                        requests.post,
                        api_url,
                        json={"appliedFacets": {}, "limit": PAGE_SIZE, "offset": offset, "searchText": ""},
                        timeout=REQUEST_TIMEOUT,
                    )
                    payload = response.json()
                except (requests.RequestException, ValueError) as exc:
                    print(f"[{self.name}] stopped '{tenant}' at offset {offset}: {exc}")
                    break

                page_jobs = payload.get("jobPostings") or []
                if not page_jobs:
                    break

                for job in page_jobs:
                    job["_company_name"] = display_name
                    external_path = job.get("externalPath") or ""
                    job["_url"] = f"{job_url_base}{external_path}" if external_path else ""
                jobs.extend(page_jobs)

                if len(page_jobs) < PAGE_SIZE:
                    break
                offset += PAGE_SIZE

        return jobs

    def normalize(self, raw_job):
        """Map a Workday CXS job posting record onto the project's standard schema."""
        title = raw_job.get("title", "")
        location = raw_job.get("locationsText") or "Unknown"

        time_type = raw_job.get("timeType")
        tags = dedupe_tags([time_type] if time_type else None)

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": raw_job.get("_company_name", ""),
            "location": location,
            "url": raw_job.get("_url", ""),
            "tags": tags,
            "remote": remote,
            "posted": _posted_on_to_iso(raw_job.get("postedOn")),
        }
