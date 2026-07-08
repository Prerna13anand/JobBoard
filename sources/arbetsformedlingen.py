"""
Arbetsformedlingen JobSearch API source (Swedish Public Employment Service).

API docs: https://jobsearch.api.jobtechdev.se/ (maintained by JobTech Dev,
part of Arbetsformedlingen); source at gitlab.com/arbetsformedlingen/job-ads/jobsearch-apis

Endpoint: GET https://jobsearch.api.jobtechdev.se/search
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via live requests (no credentials sent) returning normal 200
responses with real job data across ~40,000 currently open postings.

No keyword (`q`) is required - omitting it returns a general browse of all
current postings, matching the "fetch broadly" pattern used by other
sources in this project.

Pagination is via `offset` + `limit`. Both have hard, API-enforced
ceilings confirmed via live testing: `limit` maxes out at 100 (101 returns
an HTTP 400), and `offset` is rejected outright above 2000 (offset=2000
succeeds, offset=2001 returns an HTTP 400) - so a single query can only
ever reach ~2,100 of the ~40,000 total postings. This is a documented
limit of the API itself, not a self-imposed cap like the Himalayas/The
Muse/Adzuna page caps elsewhere in this project.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://jobsearch.api.jobtechdev.se/search"

PAGE_SIZE = 100  # documented/confirmed maximum for `limit`
# The API rejects offset values above 2000 - a hard ceiling enforced by
# the API itself (see module docstring), not a self-imposed cap.
MAX_OFFSET = 2000

REQUEST_TIMEOUT = 30

# Arbetsformedlingen has no dedicated remote flag, so - as with Adzuna/
# Reed/Jooble/Bundesagentur/CareerOneStop - remote-friendly postings are
# detected via keyword, in both English and Swedish.
REMOTE_KEYWORDS = ("remote", "distans", "hemarbete")


class ArbetsformedlingenSource(BaseJobSource):
    name = "arbetsformedlingen"

    def fetch_raw(self):
        """Fetch pages of jobs from the Arbetsformedlingen JobSearch API, up to its offset ceiling."""
        headers = {"Accept": "application/json"}
        jobs = []
        offset = 0

        while offset <= MAX_OFFSET:
            response = request_with_retry(
                requests.get,
                API_URL,
                headers=headers,
                params={"limit": PAGE_SIZE, "offset": offset},
                timeout=REQUEST_TIMEOUT,
            )
            payload = response.json()

            page_jobs = payload.get("hits") or []
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break
            offset += PAGE_SIZE

        return jobs

    def normalize(self, raw_job):
        """Map an Arbetsformedlingen job record onto the project's standard schema."""
        title = raw_job.get("headline", "")

        address = raw_job.get("workplace_address") or {}
        location_parts = [part for part in (address.get("municipality"), address.get("region")) if part]
        location = ", ".join(location_parts) if location_parts else "Sweden"

        employer = raw_job.get("employer") or {}
        company = employer.get("name") or employer.get("workplace") or ""

        occupation_field = (raw_job.get("occupation_field") or {}).get("label")
        occupation_group = (raw_job.get("occupation_group") or {}).get("label")
        employment_type = (raw_job.get("employment_type") or {}).get("label")
        tags = dedupe_tags(
            [occupation_field] if occupation_field else None,
            [occupation_group] if occupation_group else None,
            [employment_type] if employment_type else None,
        )

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": company,
            "location": location,
            "url": raw_job.get("webpage_url", ""),
            "tags": tags,
            "remote": remote,
            "posted": iso_string_to_date(raw_job.get("publication_date")),
        }
