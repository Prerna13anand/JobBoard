"""
EURES (European Job Mobility Portal) source, run by the European Labour
Authority / European Commission.

Endpoint: POST https://europa.eu/eures/api/jv-searchengine/public/jv-search/search
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via live requests (no credentials sent) returning normal 200
responses with real job data across ~2.19 million current postings spanning
all EU/EEA countries. This is the same endpoint the eures.europa.eu job
search frontend itself calls (found by tracing its live network requests,
then confirmed directly) - there is no officially published developer API
product or documentation page for it, so treat this source as somewhat
more fragile than the officially documented ones elsewhere in this
project: it could change shape without notice.

An empty `{}` POST body returns a general browse of all current postings
across every country, matching the "fetch broadly" pattern used by other
sources in this project. Note that `page`/`resultsPerPage` must be sent in
the JSON body, not as query-string params - the query string is only used
by the Angular frontend for its own URL/routing state and is silently
ignored by the API itself (confirmed live: query-string values had no
effect; body values did).

Pagination: `resultsPerPage` is capped at 50 (51+ returns HTTP 400,
confirmed live) and `page` is rejected above roughly 200 (200 succeeds,
250+ fails) - a combined ~10,000-record reachable window, the classic
Elasticsearch default result-window ceiling also seen on USAJOBS in this
project. Given the enormous total (~2.19M), pagination here is additionally
self-capped well below that hard ceiling, matching the Adzuna/MyCareersFuture
approach for similarly oversized indexes, to keep each run to a reasonable
number of requests against EU infrastructure.

Two real data-quality gaps worth knowing about, found via live testing:

- No job list item has a URL field at all. The real per-posting URL was
  found by tracing what the frontend navigates to when a result is
  clicked, and confirmed by loading it and matching page content to the
  clicked job: https://europa.eu/eures/portal/jv-se/jv-details/{id}?lang=en
- `employer` is frequently null (roughly 8 of 10 in a live sample) - some
  postings simply don't have employer data attached at the source (varies
  by which national job bank contributed the ad). Unlike Job Bank Canada
  (which never has employer data at all), this is a partial gap, not a
  structural absence, so `company` falls back to an empty string rather
  than being fabricated.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry, timestamp_to_iso_date

API_URL = "https://europa.eu/eures/api/jv-searchengine/public/jv-search/search"
JOB_DETAIL_URL = "https://europa.eu/eures/portal/jv-se/jv-details/{job_id}?lang=en"

# Documented/confirmed maximum actually honored for `resultsPerPage`.
PAGE_SIZE = 50

# Self-imposed cap, well below the API's own confirmed ~200-page ceiling
# (a 10,000-record result window) - the live total is ~2.19 million jobs,
# so this is a bounded, well-mannered sample rather than an attempt to
# exhaust the index, matching the Adzuna/MyCareersFuture approach for
# similarly oversized feeds. 40 pages * 50 jobs/page = 2,000 jobs.
MAX_PAGES = 40

REQUEST_TIMEOUT = 30

REMOTE_KEYWORDS = ("remote", "telework", "teleworking")


class EuresSource(BaseJobSource):
    name = "eures"

    def fetch_raw(self):
        """Fetch pages of jobs from the EURES search API, up to a self-imposed page cap."""
        jobs = []

        for page in range(1, MAX_PAGES + 1):
            try:
                response = request_with_retry(
                    requests.post,
                    API_URL,
                    json={"page": page, "resultsPerPage": PAGE_SIZE},
                    timeout=REQUEST_TIMEOUT,
                )
                payload = response.json()
            except requests.RequestException as exc:
                print(f"[{self.name}] stopped early at page {page}: {exc}")
                break

            page_jobs = payload.get("jvs") or []
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break

        return jobs

    def normalize(self, raw_job):
        """Map a EURES job vacancy record onto the project's standard schema."""
        title = raw_job.get("title", "")
        job_id = raw_job.get("id", "")

        employer = raw_job.get("employer") or {}
        company = employer.get("name") or ""

        location_map = raw_job.get("locationMap") or {}
        location = ", ".join(location_map.keys()) or "Europe"

        schedule_codes = raw_job.get("positionScheduleCodes") or []
        offering_code = raw_job.get("positionOfferingCode")
        tags = dedupe_tags(schedule_codes, [offering_code] if offering_code else None)

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        creation_date = raw_job.get("creationDate")
        posted = timestamp_to_iso_date(creation_date / 1000) if creation_date else ""

        return {
            "title": title,
            "company": company,
            "location": location,
            "url": JOB_DETAIL_URL.format(job_id=job_id) if job_id else "",
            "tags": tags,
            "remote": remote,
            "posted": posted,
        }
