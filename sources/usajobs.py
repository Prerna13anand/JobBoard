"""
USAJOBS Search API source (U.S. federal government job postings).

API docs: https://developer.usajobs.gov/ - the docs site is a heavy
single-page app that couldn't be rendered for inspection, so the details
below were confirmed by making live requests against the real endpoint
with a registered key/email instead of relying on documentation text.

Endpoint: GET https://data.usajobs.gov/api/search
Authentication is three required headers rather than a query param:
    Host: data.usajobs.gov
    User-Agent: <email registered with USAJOBS>
    Authorization-Key: <API key issued to that email>

Pagination is via `Page` + `ResultsPerPage`. `ResultsPerPage` accepted
values far larger than typical (tested up to 5000 in a single request),
but latency scales with page size (~13s at 5000 vs ~2s at 500), so a more
moderate page size is used for reliability. The API's total reachable
result window is capped at exactly 10,000 (`SearchResultCountAll`),
confirmed by requesting an offset of 10,000, which returned zero results -
20 pages of 500 reaches that entire window. No specific numeric rate limit
is published; third-party sources describe it as "rate limited per
User-Agent string" with no documented number, so page count is kept to
this same 10,000-job ceiling rather than hammering the endpoint further.
"""

import requests

from .base import BaseJobSource
from .config import USAJOBS_API_KEY, USAJOBS_EMAIL
from .utils import dedupe_tags, iso_string_to_date

API_URL = "https://data.usajobs.gov/api/search"

PAGE_SIZE = 500

# 20 pages * 500 jobs/page = 10,000 jobs, the API's confirmed result-window cap.
MAX_PAGES = 20

REQUEST_TIMEOUT = 30


class USAJobsSource(BaseJobSource):
    name = "usajobs"

    def fetch_raw(self):
        """Fetch pages of jobs from the USAJOBS Search API, up to its result-window cap."""
        if not USAJOBS_API_KEY or not USAJOBS_EMAIL:
            raise ValueError("USAJOBS_API_KEY and USAJOBS_EMAIL must both be set")

        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": USAJOBS_EMAIL,
            "Authorization-Key": USAJOBS_API_KEY,
        }

        jobs = []

        for page in range(1, MAX_PAGES + 1):
            response = requests.get(
                API_URL,
                headers=headers,
                params={"Page": page, "ResultsPerPage": PAGE_SIZE},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()

            items = payload.get("SearchResult", {}).get("SearchResultItems", [])
            if not items:
                break

            jobs.extend(item["MatchedObjectDescriptor"] for item in items)

            if len(items) < PAGE_SIZE:
                break

        return jobs

    def normalize(self, raw_job):
        """Map a USAJOBS MatchedObjectDescriptor onto the project's standard schema."""
        job_categories = [category["Name"] for category in raw_job.get("JobCategory") or [] if category.get("Name")]
        tags = dedupe_tags(job_categories)

        details = (raw_job.get("UserArea") or {}).get("Details") or {}
        remote = bool(details.get("RemoteIndicator", False))

        return {
            "title": raw_job.get("PositionTitle", ""),
            "company": raw_job.get("OrganizationName", ""),
            "location": raw_job.get("PositionLocationDisplay") or "Unknown",
            "url": raw_job.get("PositionURI", ""),
            "tags": tags,
            "remote": remote,
            "posted": iso_string_to_date(raw_job.get("PublicationStartDate")),
        }
