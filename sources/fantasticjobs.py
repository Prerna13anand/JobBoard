"""
Fantastic.jobs "Active ATS Jobs" API source.

Docs: https://developer.fantastic.jobs/ (public OpenAPI spec fetched
directly from https://data.fantastic.jobs/openapi and used to write this
module - endpoint paths, every parameter, and the full response schema
below are pulled straight from it, not guessed).

Endpoint: GET https://data.fantastic.jobs/v1/active-ats
Requires an `Authorization: Bearer <API_KEY>` header - confirmed live
(a request with no header returns 401 "No Authorization Header"; a
request with a bogus token returns 401 "Authorization Failed", proving
the endpoint is live and the auth mechanism is exactly this). A free
account at developer.fantastic.jobs gets a 7-day trial with no credit
card required and an API key issued immediately from the subscriptions
page; the paid tier beyond that is metered (~$1 per 1,000 jobs), the same
pay-per-call shape as Adzuna/SerpApi already in this project.

Fantastic.jobs is also listed on RapidAPI as "Active Jobs DB" - this
module uses the direct fantastic.jobs API instead, the same choice
already made for OpenWebNinja over its RapidAPI wrapper ("JSearch")
elsewhere in this project, since the direct API needs only a single
Bearer header (no RapidAPI markup or second X-RapidAPI-Host header) and
avoids paying a reseller margin on top of the same data.

This is the ATS-sourced half of Fantastic.jobs' data (3M+ jobs/month from
54 ATS platforms and 200k+ career sites, per their own published figures).
A second endpoint, `/v1/active-jb`, covers job-board-sourced listings
(LinkedIn, Wellfound, Y Combinator) with a near-identical schema - not
integrated here, to keep this source to one well-defined feed; it would
be a natural follow-up addition later using the same pattern.

`time_frame` is a required parameter selecting how far back to look
(`1h`/`24h`/`7d`/`6m`); `7d` is used here to match the "fetch broadly"
pattern used elsewhere in this project. `limit` is capped at 1000 per
the spec (confirmed in the parameter schema); pagination is via `offset`,
incremented by `limit` each call until a page returns fewer results than
requested. Given the enormous scale of this feed, each run is capped at
MAX_PAGES as a self-imposed, well-mannered ceiling - the same approach
already used for oversized indexes elsewhere in this project (EURES,
Workday, Adzuna).

Every job carries a genuine `url` field (a required field per the schema,
confirmed live), so no URL needs to be constructed manually. `organization`
is the company name directly. `locations_derived` is an array of
normalized, geocoded location strings - joined for this project's single
`location` string field. `ai_work_arrangement` is a genuine AI-derived
work-arrangement classification (`"Remote Solely"`, `"Remote OK"`,
`"Hybrid"`, `"On-site"`) - read directly for `remote`, the same "read a
real field instead of a keyword heuristic" approach already used for
Ashby/Workable/Recruitee/Trade Me in this project, with a fallback to the
schema-standard `location_type == "TELECOMMUTE"` field for jobs where the
AI enrichment didn't run.
"""

import requests

from .base import BaseJobSource
from .config import FANTASTICJOBS_API_KEY
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://data.fantastic.jobs/v1/active-ats"

TIME_FRAME = "7d"
PAGE_SIZE = 1000  # documented maximum; higher values are rejected by the API

# Self-imposed cap, well below this feed's true scale (millions of jobs/month) -
# a bounded, well-mannered sample rather than an attempt to exhaust the index.
MAX_PAGES = 20

REQUEST_TIMEOUT = 30

REMOTE_WORK_ARRANGEMENTS = {"Remote Solely", "Remote OK"}


class FantasticJobsSource(BaseJobSource):
    name = "fantasticjobs"

    def fetch_raw(self):
        """Fetch pages of jobs from the Fantastic.jobs Active ATS Jobs API, up to a self-imposed page cap."""
        if not FANTASTICJOBS_API_KEY:
            raise ValueError("FANTASTICJOBS_API_KEY must be set")

        headers = {"Authorization": f"Bearer {FANTASTICJOBS_API_KEY}"}
        jobs = []
        offset = 0

        for _ in range(MAX_PAGES):
            try:
                response = request_with_retry(
                    requests.get,
                    API_URL,
                    headers=headers,
                    params={"time_frame": TIME_FRAME, "limit": PAGE_SIZE, "offset": offset},
                    timeout=REQUEST_TIMEOUT,
                )
                page_jobs = response.json()
            except (requests.RequestException, ValueError) as exc:
                print(f"[{self.name}] stopped at offset {offset}: {exc}")
                break

            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break
            offset += PAGE_SIZE

        return jobs

    def normalize(self, raw_job):
        """Map a Fantastic.jobs Active ATS Jobs record onto the project's standard schema."""
        locations = raw_job.get("locations_derived") or []
        location = ", ".join(locations) or "Unknown"

        employment_type = raw_job.get("employment_type") or []
        taxonomies = raw_job.get("ai_taxonomies_a") or []
        tags = dedupe_tags(employment_type, taxonomies)

        work_arrangement = raw_job.get("ai_work_arrangement")
        if work_arrangement:
            remote = work_arrangement in REMOTE_WORK_ARRANGEMENTS
        else:
            remote = raw_job.get("location_type") == "TELECOMMUTE"

        return {
            "title": raw_job.get("title", ""),
            "company": raw_job.get("organization") or "",
            "location": location,
            "url": raw_job.get("url", ""),
            "tags": tags,
            "remote": remote,
            "posted": iso_string_to_date(raw_job.get("date_posted")),
        }
