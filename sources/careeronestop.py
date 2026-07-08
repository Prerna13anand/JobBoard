"""
CareerOneStop "List Jobs V2" API source (US DOL, sourced from NLx - the
National Labor Exchange, co-sponsored by DirectEmployers and NASWA).

API docs: https://www.careeronestop.org/Developers/WebAPI/Jobs/list-jobs-v2.aspx
Registration ("Request data access"): https://www.careeronestop.org/Developers/WebAPI/web-api.aspx

Endpoint: GET https://api.careeronestop.org/v2/jobsearch/{userId}/{keyword}/{location}/{radius}/{sortColumns}/{sortOrder}/{startRow}/{pageSize}/{days}
Authentication is two-part: `userId` is embedded in the URL path, and the API
Token is sent as an `Authorization: Bearer <token>` header - both issued
together during CareerOneStop's free Web API registration ("Request data
access" on the page above).

`keyword` is required by the API (an empty request errors); "0" means "all
jobs" for the given location, matching the "fetch broadly" pattern used by
other sources in this project. `location` is set to "US" for a nationwide
search (which makes `radius` a no-op, though the URL shape still requires a
value), and `days=0` disables date filtering entirely (return postings of
any age).

Pagination is via `startRow` (0-indexed) + `pageSize`. Both have hard,
API-enforced ceilings: `pageSize` maxes out at 250, and `startRow` only
accepts values up to 500 - so a single (keyword, location) query can only
ever reach ~750 total results, regardless of how many jobs actually match.
This is a documented limit of the API itself (higher startRow values are
rejected), not a self-imposed cap like the Himalayas/The Muse/Adzuna page
caps elsewhere in this project.
"""

import requests

from .base import BaseJobSource
from .config import CAREERONESTOP_API_TOKEN, CAREERONESTOP_USER_ID
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://api.careeronestop.org/v2/jobsearch"

KEYWORD = "0"  # "0" = all jobs, matching the "fetch broadly" pattern used elsewhere
LOCATION = "US"  # nationwide search
RADIUS = "0"  # ignored for a nationwide ("US") location, but required in the URL shape
DAYS = "0"  # 0 = no date filtering, return postings of any age
SORT_COLUMNS = "0"  # 0 = sort by relevance
SORT_ORDER = "0"  # paired with sortColumns=0 to get the most relevant postings first

PAGE_SIZE = 250  # documented maximum
# The API rejects startRow values above 500 - a hard ceiling enforced by
# CareerOneStop itself (see module docstring), not a self-imposed cap.
MAX_START_ROW = 500

REQUEST_TIMEOUT = 30

# CareerOneStop has no dedicated remote flag, so - as with Adzuna/Reed/
# Jooble/Bundesagentur - remote-friendly postings are detected via keyword.
REMOTE_KEYWORDS = ("remote",)


class CareerOneStopSource(BaseJobSource):
    name = "careeronestop"

    def fetch_raw(self):
        """Fetch pages of jobs from the CareerOneStop List Jobs V2 API, up to its startRow ceiling."""
        if not CAREERONESTOP_USER_ID or not CAREERONESTOP_API_TOKEN:
            raise ValueError("CAREERONESTOP_USER_ID and CAREERONESTOP_API_TOKEN must both be set")

        headers = {"Authorization": f"Bearer {CAREERONESTOP_API_TOKEN}"}
        jobs = []
        start_row = 0

        while start_row <= MAX_START_ROW:
            url = (
                f"{API_URL}/{CAREERONESTOP_USER_ID}/{KEYWORD}/{LOCATION}/{RADIUS}/"
                f"{SORT_COLUMNS}/{SORT_ORDER}/{start_row}/{PAGE_SIZE}/{DAYS}"
            )
            response = request_with_retry(requests.get, url, headers=headers, timeout=REQUEST_TIMEOUT)
            payload = response.json()

            page_jobs = payload.get("Jobs") or []
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break
            start_row += PAGE_SIZE

        return jobs

    def normalize(self, raw_job):
        """Map a CareerOneStop/NLx job record onto the project's standard schema."""
        title = raw_job.get("JobTitle", "")
        location = raw_job.get("Location") or "Unknown"

        tags = dedupe_tags(["Federal contractor"] if raw_job.get("Fc") else None)

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": raw_job.get("Company", ""),
            "location": location,
            "url": raw_job.get("URL", ""),
            "tags": tags,
            "remote": remote,
            "posted": iso_string_to_date(raw_job.get("AcquisitionDate")),
        }
