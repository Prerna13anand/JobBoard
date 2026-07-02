"""
CareerJet Publisher API source (v4).

API docs: https://www.careerjet.com/partners/api/ - this is the current
v4 API, which differs from CareerJet's older "affid"-based v2/v3 widget
API still referenced in many third-party tutorials; the details below
follow the current official docs (and live testing, where the docs were
incomplete) as instructed.

Endpoint: GET https://search.api.careerjet.net/v4/query
Authentication is HTTP Basic Auth with the API key as the username and an
empty password (same pattern as Reed).

`keywords`, `user_ip`, and `user_agent` are all required parameters.
`keywords` is handled the same wildcard way as Jooble/SerpApi/OpenWebNinja
(this project has no single search term to scope to). `user_ip` and
`user_agent` describe the end user making a search on a live site; this
project is a backend batch aggregator with no such per-request user, so a
generic placeholder IP and the same descriptive bot user agent already
used for RemoteOK are sent instead.

Two requirements were discovered only through live testing and are not
mentioned in the documentation page as summarized:
  1. The account must have its calling server IP allowlisted on
     CareerJet's partner dashboard - without it, every request returns
     403 "Unauthorized access from IP ...". (Confirmed by an independent
     IP-echo check that the rejected IP was this environment's actual
     outbound IP, not the `user_ip` parameter's value.)
  2. A `Referer` header must be present - without it, requests that pass
     the IP check still get 403 "Undeclared referrer. Please add a
     Referer header." Any non-empty value works; it doesn't need to match
     a specific registered domain, so a neutral placeholder is used.

Pagination is via `page`; the documented `page_size` parameter (range
1-100) is accepted but silently ignored - every page returns exactly 20
jobs regardless of what's requested. No pagination ceiling was found in
testing (checked up to page 100, still returning fresh results, matching
Adzuna's situation), so - like Adzuna - pages are capped at a fixed,
self-imposed number (100 pages * 20 jobs/page = 2,000 jobs) rather than
exhausting the reported ~320,000+ total matches.

The `date` field is RFC 2822 formatted (e.g. "Wed, 01 Jul 2026 07:59:08
GMT"), not ISO 8601 as initially assumed from the docs - confirmed via a
real response - so it's parsed with `email.utils.parsedate_to_datetime`
rather than the project's usual `iso_string_to_date` helper.
"""

from email.utils import parsedate_to_datetime

import requests
from requests.auth import HTTPBasicAuth

from .base import BaseJobSource
from .config import CAREERJET_API_KEY

API_URL = "https://search.api.careerjet.net/v4/query"

# Adzuna/Jooble/SerpApi/OpenWebNinja-style wildcard: `keywords` is
# required, and this project has no single search term to scope to.
SEARCH_KEYWORDS = "jobs"

# CareerJet's `user_ip`/`user_agent` describe an end user of a live search
# page; this project has no such per-request user, so a generic
# placeholder IP and the same bot user agent already used for RemoteOK
# are sent instead.
USER_IP = "127.0.0.1"
USER_AGENT = "Mozilla/5.0 (compatible; JobBoardBot/1.0)"

# A Referer header is required (see module docstring); any value works,
# so a neutral, non-affiliated placeholder is used.
REFERER = "https://example.com/"

# The API always returns 20 jobs/page regardless of the documented
# `page_size` param, which is silently ignored (confirmed via testing).
PAGE_SIZE = 20

# Self-imposed cap: no pagination ceiling was found (unlike Bundesagentur/
# The Muse/USAJOBS), matching Adzuna's situation - 100 pages * 20 = 2,000
# jobs, the same target volume used for Adzuna.
MAX_PAGES = 100

REQUEST_TIMEOUT = 15

# CareerJet has no dedicated remote flag, so - as with Jooble/Bundesagentur/
# Adzuna/Reed - remote-friendly postings are detected via keyword.
REMOTE_KEYWORDS = ("remote",)


class CareerJetSource(BaseJobSource):
    name = "careerjet"

    def fetch_raw(self):
        """Fetch pages of jobs from the CareerJet v4 API using a wildcard search."""
        if not CAREERJET_API_KEY:
            raise ValueError("CAREERJET_API_KEY is not set")

        auth = HTTPBasicAuth(CAREERJET_API_KEY, "")
        headers = {"Referer": REFERER}
        jobs = []

        for page in range(1, MAX_PAGES + 1):
            response = requests.get(
                API_URL,
                auth=auth,
                headers=headers,
                params={
                    "keywords": SEARCH_KEYWORDS,
                    "user_ip": USER_IP,
                    "user_agent": USER_AGENT,
                    "page": page,
                    "page_size": PAGE_SIZE,
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()

            page_jobs = payload.get("jobs", [])
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break

        return jobs

    def normalize(self, raw_job):
        """Map a CareerJet job record onto the project's standard schema."""
        title = raw_job.get("title", "")
        location = raw_job.get("locations") or "Unknown"

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": raw_job.get("company", ""),
            "location": location,
            "url": raw_job.get("url", ""),
            # CareerJet's response has no job-category/employment-type
            # field to draw tags from, same situation as Reed.
            "tags": [],
            "remote": remote,
            "posted": _rfc2822_to_iso(raw_job.get("date")),
        }


def _rfc2822_to_iso(date_string):
    """Convert CareerJet's RFC 2822 "date" string (e.g. "Wed, 01 Jul 2026 07:59:08 GMT") to ISO "YYYY-MM-DD"."""
    if not date_string:
        return ""

    try:
        return parsedate_to_datetime(date_string).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""
