"""
Adzuna Job Search API source.

API docs: https://developer.adzuna.com/docs/search

Endpoint: GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
Adzuna's index is split per country rather than being global, so a country
code is required in the URL path; "us" is used here for broad general
private-sector coverage, complementing the country-specific Bundesagentur
(Germany) and USAJOBS (US federal) sources already in the project.
Authentication is via `app_id`/`app_key` query params (not headers).

No keyword ("what") is required - omitting it returns a general browse of
all current postings for the country, matching the "fetch broadly" pattern
used by the other sources in this project.

Pagination is via the page number in the URL path plus `results_per_page`,
which is honored up to 50 (values above that silently fall back to 50
rather than erroring). Unlike Himalayas/The Muse/Bundesagentur/USAJOBS,
live testing found no pagination ceiling - pages far beyond what's needed
here (checked up to page 5000) still returned fresh, non-overlapping
results. Since Adzuna's country-wide index runs into the millions of jobs,
pagination is capped at a fixed number of pages (consistent with the
similarly self-capped Himalayas/The Muse sources) rather than exhausting
it, to avoid excessive requests.
"""

import requests

from .base import BaseJobSource
from .config import ADZUNA_APP_ID, ADZUNA_APP_KEY
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://api.adzuna.com/v1/api/jobs"
COUNTRY = "us"

# Highest page size the API will actually honor per request.
PAGE_SIZE = 50

# 40 pages * 50 jobs/page = 2,000 jobs - a self-imposed cap in the same
# ballpark as the other broad-but-uncapped sources (Himalayas, The Muse),
# since Adzuna's own index has no discovered pagination ceiling.
MAX_PAGES = 40

REQUEST_TIMEOUT = 30

# Adzuna has no dedicated remote flag, so - as with Jooble/Bundesagentur -
# remote-friendly postings are detected via keyword in the title/location.
REMOTE_KEYWORDS = ("remote",)


class AdzunaSource(BaseJobSource):
    name = "adzuna"

    def fetch_raw(self):
        """Fetch pages of jobs from the Adzuna API for the configured country."""
        if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
            raise ValueError("ADZUNA_APP_ID and ADZUNA_APP_KEY must both be set")

        jobs = []

        for page in range(1, MAX_PAGES + 1):
            response = request_with_retry(
                requests.get,
                f"{API_URL}/{COUNTRY}/search/{page}",
                params={
                    "app_id": ADZUNA_APP_ID,
                    "app_key": ADZUNA_APP_KEY,
                    "results_per_page": PAGE_SIZE,
                },
                timeout=REQUEST_TIMEOUT,
            )
            payload = response.json()

            page_jobs = payload.get("results", [])
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break

        return jobs

    def normalize(self, raw_job):
        """Map an Adzuna job record onto the project's standard schema."""
        title = raw_job.get("title", "")
        location = (raw_job.get("location") or {}).get("display_name") or "Unknown"

        category_label = (raw_job.get("category") or {}).get("label")
        tags = dedupe_tags(
            [category_label] if category_label else None,
            [raw_job["contract_time"]] if raw_job.get("contract_time") else None,
            [raw_job["contract_type"]] if raw_job.get("contract_type") else None,
        )

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": (raw_job.get("company") or {}).get("display_name", ""),
            "location": location,
            "url": raw_job.get("redirect_url", ""),
            "tags": tags,
            "remote": remote,
            "posted": iso_string_to_date(raw_job.get("created")),
        }
