"""
Himalayas Jobs API source.

API docs: https://himalayas.app/jobs/api

The endpoint is offset-paginated (`offset`/`limit`) and reports `totalCount`,
but it ignores whatever `limit` is requested and always returns 20 jobs per
page. At last check `totalCount` was over 90,000 - fetching the entire
archive would take thousands of sequential requests (each takes a few
seconds), which is impractical for a lightweight aggregator and unfriendly
to a free public API. Jobs are returned newest-first, so we cap how many
pages we follow (MAX_PAGES) to grab a large, recent slice instead of the
entire history. Raise MAX_PAGES if a fuller pull is ever needed.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, timestamp_to_iso_date

API_URL = "https://himalayas.app/jobs/api"
PAGE_SIZE = 20  # fixed by the API regardless of the `limit` param we send

# How many pages (of PAGE_SIZE jobs each) to pull per run. 150 pages is
# 3,000 of the most recent postings - a good-sized, fast-to-fetch snapshot
# without trying to page through the entire multi-thousand-page archive.
MAX_PAGES = 150

REQUEST_TIMEOUT = 15


class HimalayasSource(BaseJobSource):
    name = "himalayas"

    def fetch_raw(self):
        """Fetch pages of jobs from the Himalayas API, newest first."""
        jobs = []

        for page in range(MAX_PAGES):
            offset = page * PAGE_SIZE
            response = requests.get(
                API_URL,
                params={"limit": PAGE_SIZE, "offset": offset},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()

            page_jobs = payload.get("jobs", [])
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            # Stop once we've paged past the reported total.
            if offset + PAGE_SIZE >= payload.get("totalCount", 0):
                break

        return jobs

    def normalize(self, raw_job):
        """Map a Himalayas job record onto the project's standard schema."""
        location_restrictions = raw_job.get("locationRestrictions") or []
        location = ", ".join(location_restrictions) if location_restrictions else "Worldwide"

        # Fold employment type and seniority into tags alongside the job's
        # categories, since the standard schema only has one tags field.
        tags = dedupe_tags(
            raw_job.get("categories"),
            raw_job.get("parentCategories"),
            raw_job.get("seniority"),
            [raw_job["employmentType"]] if raw_job.get("employmentType") else None,
        )

        return {
            "title": raw_job.get("title", ""),
            "company": raw_job.get("companyName", ""),
            "location": location,
            "url": raw_job.get("applicationLink", ""),
            "tags": tags,
            # Himalayas is a remote-only job board, so every listing is remote.
            "remote": True,
            "posted": timestamp_to_iso_date(raw_job.get("pubDate")),
        }
