"""
Arbeitnow Job Board API source.

API docs: https://www.arbeitnow.com/api/job-board-api

The endpoint returns 100 jobs per page and exposes the next page's URL at
`links.next`. To pull as many jobs as possible, we follow that link until
there are no more pages (or a safety cap is hit, to avoid hammering the API
if something goes wrong).
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, timestamp_to_iso_date

API_URL = "https://www.arbeitnow.com/api/job-board-api"

# Hard ceiling on how many pages we'll follow. At 100 jobs/page this is
# 20,000 jobs, comfortably more than the board currently lists, while still
# protecting us from an infinite pagination loop.
MAX_PAGES = 200

# Seconds to wait for a response before giving up on a request.
REQUEST_TIMEOUT = 15


class ArbeitnowSource(BaseJobSource):
    name = "arbeitnow"

    def fetch_raw(self):
        """Fetch every page of jobs from the Arbeitnow API."""
        jobs = []
        next_url = API_URL

        for _ in range(MAX_PAGES):
            if not next_url:
                break

            response = requests.get(next_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()

            jobs.extend(payload.get("data", []))
            next_url = payload.get("links", {}).get("next")

        return jobs

    def normalize(self, raw_job):
        """Map an Arbeitnow job record onto the project's standard schema."""
        # Arbeitnow splits employment type ("Full-time", "Contract", ...)
        # into `job_types` separately from `tags` (skills/topics). We merge
        # them into a single `tags` list since the standard schema only has
        # one tags field, de-duplicating while preserving order.
        tags = dedupe_tags(raw_job.get("tags"), raw_job.get("job_types"))

        return {
            "title": raw_job.get("title", ""),
            "company": raw_job.get("company_name", ""),
            "location": raw_job.get("location", ""),
            "url": raw_job.get("url", ""),
            "tags": tags,
            "remote": bool(raw_job.get("remote", False)),
            "posted": timestamp_to_iso_date(raw_job.get("created_at")),
        }
