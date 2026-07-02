"""
TheirStack Jobs API source.

API docs: https://theirstack.com/en/docs/api-reference/jobs/search_jobs_v1
(cross-checked against the machine-readable spec at
https://api.theirstack.com/openapi.json, since TheirStack's docs site also
covers unrelated resources - company enrichment, hiring signals, contacts,
CRM data - that this integration must not touch; only the jobs endpoint is
used here).

Endpoint: POST https://api.theirstack.com/v1/jobs/search
Authentication is an `Authorization: Bearer <key>` header.

At least one of a specific set of filters is required by the API (e.g.
`posted_at_max_age_days`, `posted_at_gte/lte`, or a company filter) - an
empty/unfiltered "browse everything" request is rejected. To maximize the
job pool without narrowing to specific companies, `posted_at_max_age_days`
is set broadly (30 days) - this widens which jobs are eligible to be
returned, but does not affect billing (see below), so there's no downside
to keeping it broad.

IMPORTANT - billing model: unlike every other metered source in this
project (SerpApi, OpenWebNinja bill per request), TheirStack bills
**1 API credit per job returned**, confirmed via the account's real
credit balance (https://api.theirstack.com/v0/billing/credit-balance,
itself a free/unbilled lookup) before writing this integration. Because
cost scales directly with job count rather than request count, MAX_JOBS
is kept deliberately small (50, matching the SerpApi/OpenWebNinja
convention), and fetch_raw() trims the final page's `limit` so it never
requests more jobs than still needed to reach that cap - avoiding paying
for jobs beyond the intended total.

Pagination is page-based (0-indexed `page` + `limit`, no documented
maximum on `limit`).

Response fields were confirmed against a real request: `remote` is a
genuine (nullable) boolean, and `date_posted` is already an ISO
"YYYY-MM-DD" string, so no conversion is needed for either.
"""

import requests

from .base import BaseJobSource
from .config import THEIRSTACK_API_KEY
from .utils import dedupe_tags

API_URL = "https://api.theirstack.com/v1/jobs/search"

# Broadens the pool of eligible jobs without affecting billing (cost is
# per job returned, not per match) - see module docstring.
POSTED_AT_MAX_AGE_DAYS = 30

PAGE_SIZE = 25

# Kept small since this API bills 1 credit per job returned - see module
# docstring.
MAX_JOBS = 50

REQUEST_TIMEOUT = 20


class TheirStackSource(BaseJobSource):
    name = "theirstack"

    def fetch_raw(self):
        """Fetch pages of jobs from the TheirStack Jobs API, capped at MAX_JOBS to limit credit spend."""
        if not THEIRSTACK_API_KEY:
            raise ValueError("THEIRSTACK_API_KEY is not set")

        headers = {"Authorization": f"Bearer {THEIRSTACK_API_KEY}", "Content-Type": "application/json"}
        jobs = []
        page = 0

        while len(jobs) < MAX_JOBS:
            limit = min(PAGE_SIZE, MAX_JOBS - len(jobs))

            response = requests.post(
                API_URL,
                headers=headers,
                json={
                    "posted_at_max_age_days": POSTED_AT_MAX_AGE_DAYS,
                    "page": page,
                    "limit": limit,
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()

            page_jobs = payload.get("data", [])
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < limit:
                break
            page += 1

        return jobs

    def normalize(self, raw_job):
        """Map a TheirStack job record onto the project's standard schema."""
        location = (
            raw_job.get("location")
            or raw_job.get("long_location")
            or raw_job.get("short_location")
            or raw_job.get("country")
            or "Unknown"
        )

        seniority = raw_job.get("seniority")
        tags = dedupe_tags(raw_job.get("employment_statuses"), [seniority] if seniority else None)

        return {
            "title": raw_job.get("job_title", ""),
            "company": raw_job.get("company", ""),
            "location": location,
            "url": raw_job.get("url", ""),
            "tags": tags,
            "remote": bool(raw_job.get("remote", False)),
            "posted": (raw_job.get("date_posted") or "")[:10],
        }
