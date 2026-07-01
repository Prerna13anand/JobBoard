"""
Jobicy Jobs API source.

API docs: https://jobi.cy/apidocs

The endpoint accepts a `count` query param but caps it at 100 regardless of
what's requested, and has no page/offset param at all (passing one returns
an HTTP 400). So, like RemoteOK, this is a single-shot fetch of the most
recent ~100 remote jobs rather than something we can paginate through.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date

API_URL = "https://jobicy.com/api/v2/remote-jobs"
REQUEST_TIMEOUT = 15

# Highest job count the API will actually honor per request.
MAX_COUNT = 100


class JobicySource(BaseJobSource):
    name = "jobicy"

    def fetch_raw(self):
        """Fetch the current job list from the Jobicy API."""
        response = requests.get(API_URL, params={"count": MAX_COUNT}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()

        return payload.get("jobs", [])

    def normalize(self, raw_job):
        """Map a Jobicy job record onto the project's standard schema."""
        # Fold industry, employment type, and seniority into tags, since the
        # standard schema only has one tags field.
        tags = dedupe_tags(
            raw_job.get("jobIndustry"),
            raw_job.get("jobType"),
            [raw_job["jobLevel"]] if raw_job.get("jobLevel") else None,
        )

        return {
            "title": raw_job.get("jobTitle", ""),
            "company": raw_job.get("companyName", ""),
            "location": raw_job.get("jobGeo") or "Worldwide",
            "url": raw_job.get("url", ""),
            "tags": tags,
            # Jobicy is a remote-only job board, so every listing is remote.
            "remote": True,
            "posted": iso_string_to_date(raw_job.get("pubDate")),
        }
