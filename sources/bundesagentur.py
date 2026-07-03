"""
Bundesagentur fur Arbeit (German Federal Employment Agency) Jobsuche API source.

API docs / community reference: https://github.com/bundesAPI/jobsuche-api

This is the same public REST API that powers arbeitsagentur.de's own job
search (https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs).
It doesn't require personal registration, but every client - including the
official website - must send an `X-API-Key` header. The value used below
("jobboerse-jobsuche") is the well-known public key the Arbeitsagentur
website itself ships in its own frontend JavaScript; it is not a secret
tied to any individual account.

Pagination is offset-based via `page`/`size`, but the API enforces a hard
result-window limit: `page * size` cannot exceed 10,000, regardless of how
many jobs are reported as available (`maxErgebnisse`, which is typically
over a million). Using the largest page size that stays within that window
(size=200, pages 1-50) fetches the maximum 10,000 jobs the API allows.
"""

import time

import requests

from .base import BaseJobSource
from .utils import dedupe_tags

API_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
API_KEY = "jobboerse-jobsuche"

PAGE_SIZE = 200

# 50 pages * 200 jobs/page = 10,000 jobs, the API's hard result-window cap.
MAX_PAGES = 50

REQUEST_TIMEOUT = 30

# A single page gets up to this many total attempts (the original request
# plus retries) before it's treated as a real failure - covers transient
# network hiccups (timeouts, connection resets) rather than a persistent
# problem with the API or the result-window cap.
MAX_ATTEMPTS_PER_PAGE = 3
RETRY_DELAY_SECONDS = 2

# Cheap heuristic for remote-friendly postings: this API has no dedicated
# remote/home-office flag on the job listing itself, so we look for the
# common German phrasing in the title/occupation text instead.
REMOTE_KEYWORDS = ("home office", "homeoffice", "remote")


class BundesagenturSource(BaseJobSource):
    name = "bundesagentur"

    def fetch_raw(self):
        """Fetch pages of jobs from the Jobsuche API, up to the API's result-window cap."""
        jobs = []

        for page in range(1, MAX_PAGES + 1):
            payload = None

            for attempt in range(1, MAX_ATTEMPTS_PER_PAGE + 1):
                try:
                    response = requests.get(
                        API_URL,
                        headers={"X-API-Key": API_KEY},
                        params={"page": page, "size": PAGE_SIZE},
                        timeout=REQUEST_TIMEOUT,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    break
                except requests.RequestException as exc:
                    last_exc = exc
                    if attempt < MAX_ATTEMPTS_PER_PAGE:
                        print(
                            f"[{self.name}] page {page} attempt {attempt}/{MAX_ATTEMPTS_PER_PAGE} failed: "
                            f"{exc} - retrying"
                        )
                        time.sleep(RETRY_DELAY_SECONDS)

            if payload is None:
                # A single bad page (e.g. a transient error, or the result
                # window boundary being hit sooner than expected) shouldn't
                # discard jobs already collected from earlier pages.
                print(f"[{self.name}] stopped early at page {page}: {last_exc}")
                break

            page_jobs = payload.get("stellenangebote", [])
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break

        return jobs

    def normalize(self, raw_job):
        """Map a Jobsuche API job record onto the project's standard schema."""
        title = raw_job.get("titel") or raw_job.get("beruf") or ""

        location_info = raw_job.get("arbeitsort") or {}
        location_parts = [location_info.get("ort"), location_info.get("land")]
        location = ", ".join(part for part in location_parts if part and part != "null")

        # Postings hosted directly on arbeitsagentur.de have no external
        # URL, so build the canonical job-detail link from its reference
        # number instead.
        url = raw_job.get("externeUrl") or (
            f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{raw_job['refnr']}"
            if raw_job.get("refnr")
            else ""
        )

        tags = dedupe_tags(
            [raw_job["beruf"]] if raw_job.get("beruf") else None,
            [raw_job["studiengang"]] if raw_job.get("studiengang") else None,
        )

        haystack = title.lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": raw_job.get("arbeitgeber", ""),
            "location": location or "Deutschland",
            "url": url,
            "tags": tags,
            "remote": remote,
            # Already provided as an ISO "YYYY-MM-DD" string - no conversion needed.
            "posted": raw_job.get("aktuelleVeroeffentlichungsdatum", ""),
        }
