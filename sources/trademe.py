"""
Trade Me Jobs Search API source (New Zealand).

Docs: https://developer.trademe.co.nz/api-reference/search-methods/jobs-search
Endpoint: GET https://api.trademe.co.nz/v1/Search/Jobs.json

Free to use, but not anonymous: a bare request with no credentials at all
returns HTTP 401 ("This API requires that you supply your application
credentials") - confirmed live. What's needed is an OAuth 1.0a *consumer*
key/secret (from a free Trade Me membership + a registered "application"
at My Trade Me > My Applications > Developer options); per Trade Me's own
authentication docs this endpoint accepts "a valid OAuth request (with a
consumer key, a signature and optionally a callback, but without a
token)" - i.e. two-legged OAuth, no per-user access-token/authorization
step is needed for this read-only public search endpoint. Signing is done
with `requests_oauthlib.OAuth1` (new dependency - `oauthlib`/
`requests-oauthlib` are the standard, well-tested libraries for this;
nothing else in this project needed OAuth 1.0a before).

Sandbox applications on Trade Me's developer site are auto-approved;
production registration is "subject to Trade Me's approval process and
terms and conditions" per their docs - not documented as guaranteed
same-day, unlike the instant self-serve keys other sources in this
project use (Adzuna, Reed, Findwork, etc.). Like France Travail elsewhere
in this project, this module was written directly against Trade Me's own
API reference (endpoint, parameters, response field names, date format)
with no live credentials available to fully exercise an end-to-end fetch
while writing it - field names below are as documented, not confirmed
against a real response.

Pagination is via `page` (1-based) and `rows` (results per page) query
parameters. `rows` is documented as capped at 25 for unauthenticated
calls and 500 once authenticated (this project always sends credentials,
so 500 is used). The response carries `TotalCount`/`Page`/`PageSize`
alongside the `List` of jobs - pagination continues until a page returns
fewer than `rows` jobs, the same "shorter page ends the loop" convention
used elsewhere in this project (Greenhouse, Ashby, etc.), with a
self-imposed page-count ceiling as a safety net since NZ's total live job
count is nowhere near it.

Trade Me dates are serialized in the legacy Microsoft JSON format, e.g.
`"/Date(1626749989730+1200)/"` (milliseconds since the Unix epoch, plus
an optional timezone offset) - parsed locally in this module via regex,
then converted with this project's existing `timestamp_to_iso_date`
(which expects seconds, hence the /1000).

No dedicated remote/hybrid field is documented on job listings, so
`remote` is a keyword check against title + location, the same approach
used for EURES/MyJobMag/Mustakbil/Workday in this project.
"""

import re

import requests
from requests_oauthlib import OAuth1

from .base import BaseJobSource
from .config import TRADEME_CONSUMER_KEY, TRADEME_CONSUMER_SECRET
from .utils import dedupe_tags, request_with_retry, timestamp_to_iso_date

SEARCH_URL = "https://api.trademe.co.nz/v1/Search/Jobs.json"
LISTING_URL_TEMPLATE = "https://www.trademe.co.nz/a/jobs/listing/{listing_id}"

PAGE_SIZE = 500  # documented maximum once authenticated (unauthenticated calls are capped at 25)

# Self-imposed safety net, not a real ceiling this project expects to hit -
# New Zealand's entire live job market is a small fraction of this.
MAX_PAGES = 20

REQUEST_TIMEOUT = 30

REMOTE_KEYWORDS = ("remote", "work from home", "telecommute")

_MS_DATE_RE = re.compile(r"/Date\((-?\d+)")


def _trademe_date_to_iso(date_string):
    """Convert Trade Me's "/Date(1626749989730+1200)/" format to ISO "YYYY-MM-DD"."""
    if not date_string:
        return ""
    match = _MS_DATE_RE.search(date_string)
    if not match:
        return ""
    return timestamp_to_iso_date(int(match.group(1)) / 1000)


class TradeMeSource(BaseJobSource):
    name = "trademe"

    def fetch_raw(self):
        """Fetch pages of jobs from the Trade Me Jobs Search API."""
        if not TRADEME_CONSUMER_KEY or not TRADEME_CONSUMER_SECRET:
            raise ValueError("TRADEME_CONSUMER_KEY and TRADEME_CONSUMER_SECRET must both be set")

        auth = OAuth1(TRADEME_CONSUMER_KEY, client_secret=TRADEME_CONSUMER_SECRET, signature_type="auth_header")

        jobs = []
        for page in range(1, MAX_PAGES + 1):
            try:
                response = request_with_retry(
                    requests.get,
                    SEARCH_URL,
                    auth=auth,
                    params={"page": page, "rows": PAGE_SIZE},
                    timeout=REQUEST_TIMEOUT,
                )
                payload = response.json()
            except (requests.RequestException, ValueError) as exc:
                print(f"[{self.name}] stopped at page {page}: {exc}")
                break

            page_jobs = payload.get("List") or []
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break

        return jobs

    def normalize(self, raw_job):
        """Map a Trade Me job listing onto the project's standard schema."""
        title = raw_job.get("Title", "")

        agency = raw_job.get("Agency") or {}
        company = raw_job.get("Company") or agency.get("Name") or ""

        location = ", ".join(
            part for part in (raw_job.get("Suburb"), raw_job.get("Region")) if part
        ) or raw_job.get("JobLocation") or "New Zealand"

        listing_id = raw_job.get("ListingId")
        url = LISTING_URL_TEMPLATE.format(listing_id=listing_id) if listing_id else ""

        job_type = raw_job.get("JobType")
        job_category = raw_job.get("JobCategory")
        tags = dedupe_tags([job_type] if job_type else None, [job_category] if job_category else None)

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "tags": tags,
            "remote": remote,
            "posted": _trademe_date_to_iso(raw_job.get("StartDate")),
        }
