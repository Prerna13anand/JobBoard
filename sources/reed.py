"""
Reed Jobseeker API source (UK job board).

API docs: https://www.reed.co.uk/developers/jobseeker

Endpoint: GET https://www.reed.co.uk/api/1.0/search
Authentication is HTTP Basic Auth with the API key as the username and an
empty password - not a header or query param.

No keyword is required - omitting it returns a general browse of all
current UK postings, matching the "fetch broadly" pattern used by the
other sources in this project.

Pagination is via `resultsToTake` (capped at 100 - higher values silently
fall back to 100) and `resultsToSkip`. Live testing found a hard result-
window ceiling: `resultsToSkip` around 9,900+ returns an HTTP 500 rather
than an empty page, similar in spirit to the boundary Bundesagentur hits.
Pagination is therefore capped safely below that boundary, and - as with
Bundesagentur - a failed page request stops the loop rather than crashing,
keeping whatever was already collected.

The search response has no job-category/employment-type field at all
(unlike every other source integrated so far), so `tags` is always empty
for this source; there's nothing in the payload to build them from.
"""

import requests
from requests.auth import HTTPBasicAuth

from .base import BaseJobSource
from .config import REED_API_KEY
from .utils import uk_date_to_iso

API_URL = "https://www.reed.co.uk/api/1.0/search"

PAGE_SIZE = 100

# Comfortably below the ~9,900-9,920 boundary where resultsToSkip starts
# returning HTTP 500 (see module docstring).
MAX_PAGES = 90

REQUEST_TIMEOUT = 15

# Reed has no dedicated remote flag, so - as with Jooble/Bundesagentur/
# Adzuna - remote-friendly postings are detected via keyword.
REMOTE_KEYWORDS = ("remote",)


class ReedSource(BaseJobSource):
    name = "reed"

    def fetch_raw(self):
        """Fetch pages of jobs from the Reed API, up to the discovered result-window boundary."""
        if not REED_API_KEY:
            raise ValueError("REED_API_KEY is not set")

        auth = HTTPBasicAuth(REED_API_KEY, "")
        jobs = []

        for page in range(MAX_PAGES):
            try:
                response = requests.get(
                    API_URL,
                    auth=auth,
                    params={"resultsToTake": PAGE_SIZE, "resultsToSkip": page * PAGE_SIZE},
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                payload = response.json()
            except requests.RequestException as exc:
                print(f"[{self.name}] stopped early at page {page + 1}: {exc}")
                break

            page_jobs = payload.get("results", [])
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break

        return jobs

    def normalize(self, raw_job):
        """Map a Reed job record onto the project's standard schema."""
        title = raw_job.get("jobTitle", "")
        location = raw_job.get("locationName") or "Unknown"

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": raw_job.get("employerName", ""),
            "location": location,
            "url": raw_job.get("jobUrl", ""),
            # Reed's search response has no category/employment-type field
            # to draw tags from.
            "tags": [],
            "remote": remote,
            "posted": uk_date_to_iso(raw_job.get("date")),
        }
