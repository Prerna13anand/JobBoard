"""
Findwork.dev Jobs API source (US/remote tech job board).

API docs: https://findwork.dev/developers/

Endpoint: GET https://findwork.dev/api/jobs/
Authentication is a required `Authorization: Token <key>` header - confirmed
live that an unauthenticated request is rejected outright with an HTTP 401
("Authentication credentials were not provided."), unlike every Phase 1
source in this project. The token is free but requires registering an
account at findwork.dev first (see .env.example).

No keyword is required - omitting one returns a general browse of all
current postings, matching the "fetch broadly" pattern used by other
sources in this project.

Pagination is standard Django REST Framework page-number pagination:
`count`/`next`/`previous`/`results`, 100 jobs per page (confirmed live),
with `next` already being a full, ready-to-fetch URL - the same "follow
the provided next link" pattern used for NAV Norway's feed pagination.

Rate limiting: confirmed live via `X-Ratelimit-Limit`/`X-Ratelimit-Remaining`
response headers (limit of 10). Live testing hit a real HTTP 429 partway
through a full fetch (around page 11) despite `request_with_retry`'s
built-in backoff - the limit resets slower than a few retries can cover.
As with Reed/RemoteJobs.org, a failed page request stops the loop rather
than crashing, keeping whatever was already collected instead of losing
the whole run to one rate-limited page.
"""

import requests

from .base import BaseJobSource
from .config import FINDWORK_API_KEY
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://findwork.dev/api/jobs/"

# Self-imposed cap - the current live total is ~3,200 jobs (~33 pages at
# 100/page); this comfortably covers that with room for growth, without
# risking an unbounded loop if `next` were ever to misbehave.
MAX_PAGES = 50

REQUEST_TIMEOUT = 20


class FindworkSource(BaseJobSource):
    name = "findwork"

    def fetch_raw(self):
        """Fetch pages of jobs from the Findwork.dev API, following its next-page links."""
        if not FINDWORK_API_KEY:
            raise ValueError("FINDWORK_API_KEY is not set")

        headers = {"Authorization": f"Token {FINDWORK_API_KEY}"}
        jobs = []
        url = API_URL

        for _ in range(MAX_PAGES):
            try:
                response = request_with_retry(requests.get, url, headers=headers, timeout=REQUEST_TIMEOUT)
                payload = response.json()
            except requests.RequestException as exc:
                print(f"[{self.name}] stopped early: {exc}")
                break

            page_jobs = payload.get("results") or []
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            url = payload.get("next")
            if not url:
                break

        return jobs

    def normalize(self, raw_job):
        """Map a Findwork.dev job record onto the project's standard schema."""
        remote = bool(raw_job.get("remote", False))
        location = raw_job.get("location") or ("Worldwide" if remote else "Unknown")

        employment_type = raw_job.get("employment_type")
        tags = dedupe_tags(raw_job.get("keywords"), [employment_type] if employment_type else None)

        return {
            "title": raw_job.get("role", ""),
            "company": raw_job.get("company_name", ""),
            "location": location,
            "url": raw_job.get("url", ""),
            "tags": tags,
            "remote": remote,
            "posted": iso_string_to_date(raw_job.get("date_posted")),
        }
