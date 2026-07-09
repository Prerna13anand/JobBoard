"""
Hong Kong Government Job Vacancy Open Data API source (Civil Service
Bureau, published via data.gov.hk).

Endpoint: GET https://www.csb.gov.hk/datagovhk/gov-vacancies/gov-job-vacancies-en.json
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via a live request (no credentials sent) returning a normal 200
response with real job data (57 current vacancies). Listed on data.gov.hk
as an open dataset; the data dictionary is published at
https://www.csb.gov.hk/datagovhk/gov-vacancies/gov-job-vacancies-data-dictionary-en.pdf

This is a static, pre-generated JSON file refreshed on a schedule rather
than a queryable API - there is nothing to paginate (the whole current
vacancy list is returned in one response) and no query params are
accepted.

API quirk: the response body starts with a UTF-8 byte-order mark, which
makes `requests`' built-in `.json()` raise ("Unexpected UTF-8 BOM").
`response.content.decode("utf-8-sig")` strips it before parsing.

Scope note: this feed covers Hong Kong civil service / government
vacancies only (not the broader Hong Kong private-sector job market), and
carries no location field of its own since every posting is within Hong
Kong - `location` is therefore fixed to "Hong Kong" below.

There is no per-posting URL in this feed either - `depturl`/`onlineformurl`
are blank on every record checked, and the real application system
(csboa2.csb.gov.hk's "JVE" - Job Vacancies Enquiry - portal) is a
session-based search form with no confirmed way to deep-link a specific
`jobid` from a plain GET request. Rather than fabricate a URL that might
not resolve to the right posting, `url` points every job at the same real,
working entry point to that search system - a documented limitation of
this specific feed, not a bug.
"""

import json

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry

API_URL = "https://www.csb.gov.hk/datagovhk/gov-vacancies/gov-job-vacancies-en.json"

# The feed has no per-posting URL (see module docstring) - every job links
# here, the real entry point to the Civil Service Bureau's vacancy search
# system, rather than a fabricated per-job link that might not resolve.
JVE_SEARCH_URL = "https://csboa.csb.gov.hk/Redirect_JVE_en.html"

REQUEST_TIMEOUT = 15

REMOTE_KEYWORDS = ("remote", "work from home", "wfh")


class HKGovVacanciesSource(BaseJobSource):
    name = "hk_gov_vacancies"

    def fetch_raw(self):
        """Fetch the current vacancy list from the Hong Kong government's open data feed."""
        try:
            response = request_with_retry(requests.get, API_URL, timeout=REQUEST_TIMEOUT)
            # The feed is UTF-8-with-BOM, which requests' own .json() rejects.
            payload = json.loads(response.content.decode("utf-8-sig"))
        except (requests.RequestException, ValueError) as exc:
            print(f"[{self.name}] failed to fetch or parse the feed: {exc}")
            return []

        jobs = []
        for group in payload.get("common") or []:
            jobs.extend(group.get("vacancies") or [])

        return jobs

    def normalize(self, raw_job):
        """Map a Hong Kong government vacancy record onto the project's standard schema."""
        title = raw_job.get("jobname", "")
        tags = dedupe_tags(raw_job.get("academic"))

        haystack = title.lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": raw_job.get("deptnamejve", ""),
            "location": "Hong Kong",
            "url": JVE_SEARCH_URL,
            "tags": tags,
            "remote": remote,
            # Already an ISO "YYYY-MM-DD" string, no conversion needed.
            "posted": raw_job.get("pubdate", ""),
        }
