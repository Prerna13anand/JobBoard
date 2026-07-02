"""
OpenWeb Ninja JSearch Jobs API source.

API docs: https://www.openwebninja.com/api/jsearch (the interactive docs
at .../jsearch/docs are a JS-rendered page that couldn't be inspected
directly, so this was verified as far as possible via live requests
against the real endpoint with the registered key instead).

Endpoint: GET https://api.openwebninja.com/jsearch/search-v2
Authentication is an `x-api-key` header. A search `query` is required,
same situation as Jooble/SerpApi; a generic term is used to approximate a
general browse rather than scoping to one job type.

Like SerpApi, this is a metered, paid service (free plan: 200
requests/month), so pagination is kept deliberately small rather than
pushed to whatever the API would technically allow.

Pagination is cursor-based (`cursor` param, echoed back in the response
for the next page) - OpenWebNinja replaced page-number pagination with
this on `search-v2`. A successful response is shaped as
`{"status", "request_id", "parameters", "data": {"jobs": [...], "cursor": "..."}}`
- the job list and next cursor are nested under `data`, not top-level.
"""

import requests

from .base import BaseJobSource
from .config import OPENWEBNINJA_API_KEY
from .utils import dedupe_tags, iso_string_to_date, timestamp_to_iso_date

API_URL = "https://api.openwebninja.com/jsearch/search-v2"

# Adzuna/Jooble/SerpApi-style wildcard: a non-empty `query` is required,
# and this project has no single search term to scope results to.
SEARCH_QUERY = "jobs"

# Kept small since this is a metered, paid API (200 requests/month on the
# free plan) - see module docstring.
MAX_PAGES = 5

REQUEST_TIMEOUT = 20


class OpenWebNinjaSource(BaseJobSource):
    name = "openwebninja"

    def fetch_raw(self):
        """Fetch pages of jobs from the JSearch API using a wildcard search."""
        if not OPENWEBNINJA_API_KEY:
            raise ValueError("OPENWEBNINJA_API_KEY is not set")

        headers = {"x-api-key": OPENWEBNINJA_API_KEY}
        params = {"query": SEARCH_QUERY}
        jobs = []

        for _ in range(MAX_PAGES):
            response = requests.get(API_URL, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()

            data = payload.get("data") or {}
            page_jobs = data.get("jobs", [])
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            cursor = data.get("cursor")
            if not cursor:
                break
            params["cursor"] = cursor

        return jobs

    def normalize(self, raw_job):
        """Map a JSearch job record onto the project's standard schema."""
        location = raw_job.get("job_location") or ", ".join(
            part
            for part in (raw_job.get("job_city"), raw_job.get("job_state"), raw_job.get("job_country"))
            if part
        )

        url = raw_job.get("job_apply_link") or (raw_job.get("apply_options") or [{}])[0].get("apply_link", "")

        employment_type = raw_job.get("job_employment_type")
        tags = dedupe_tags([employment_type] if employment_type else None)

        posted = iso_string_to_date(raw_job.get("job_posted_at_datetime_utc")) or timestamp_to_iso_date(
            raw_job.get("job_posted_at_timestamp")
        )

        return {
            "title": raw_job.get("job_title", ""),
            "company": raw_job.get("employer_name", ""),
            "location": location or "Unknown",
            "url": url,
            "tags": tags,
            "remote": bool(raw_job.get("job_is_remote", False)),
            "posted": posted,
        }
