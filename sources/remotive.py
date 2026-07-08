"""
Remotive Jobs API source (remote-only job board).

API docs: https://remotive.com/api-jobs
Endpoint: GET https://remotive.com/api/remote-jobs

Public and free - no registration, no API key, no auth header of any kind.
Confirmed via live requests (no credentials sent) returning normal 200
responses with real job data.

The `category`, `search`, and `limit` query params documented for this
endpoint were tested live and found to have no effect: a request with
`category=software-dev` returned the exact same 28 jobs, spanning 12
different categories, as an entirely unfiltered request. Since filtering
isn't reliable, and the current live job count is small, this source
always fetches the full unfiltered set in one call rather than relying on
params that don't work - there's no pagination to do here either way, since
one call already returns everything.

Rate limits aren't a fixed published number, but the API's own response
carries an explicit usage notice: max ~4 requests/day advised, "excessive
requests will be blocked." This project's aggregator does a single run
(and therefore a single request to this source) at a time, well within
that guidance.

Remotive's own terms (embedded in every API response) ask that the original
job URL be preserved as a link back to Remotive, which this source already
does via the `url` field below.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date

API_URL = "https://remotive.com/api/remote-jobs"
REQUEST_TIMEOUT = 15


class RemotiveSource(BaseJobSource):
    name = "remotive"

    def fetch_raw(self):
        """Fetch the current job list from the Remotive API."""
        response = requests.get(API_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()

        return payload.get("jobs", [])

    def normalize(self, raw_job):
        """Map a Remotive job record onto the project's standard schema."""
        category = raw_job.get("category")
        tags = dedupe_tags(raw_job.get("tags"), [category] if category else None)

        return {
            "title": raw_job.get("title", ""),
            "company": raw_job.get("company_name", ""),
            "location": raw_job.get("candidate_required_location") or "Worldwide",
            "url": raw_job.get("url", ""),
            "tags": tags,
            # Remotive is a remote-only job board, so every listing is remote.
            "remote": True,
            "posted": iso_string_to_date(raw_job.get("publication_date")),
        }
