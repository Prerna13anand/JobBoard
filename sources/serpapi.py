"""
SerpApi Google Jobs API source.

API docs: https://serpapi.com/google-jobs-api

Endpoint: GET https://serpapi.com/search?engine=google_jobs
Authentication is an `api_key` query param. Unlike every other source in
this project, SerpApi is a metered, paid service that scrapes Google
Jobs results - each request is a billable "search" against the account's
plan (the free plan is 250 searches/month total, confirmed by checking
https://serpapi.com/account.json with the real key before writing this
integration). A search (`q`) is required, same situation as Jooble; a
generic term is used to approximate a general browse rather than scoping
to one job type.

Pagination is token-based (`next_page_token` from `serpapi_pagination`),
not page-number-based, and returns at most 10 jobs per request. Because
each page costs one billable search, MAX_PAGES is kept deliberately small
(5 pages = 50 jobs per run) to avoid burning through the account's monthly
quota - a very different tradeoff than the free APIs elsewhere in this
project, where pagination is pushed to the API's own limits.

Google Jobs has no absolute posting date - `detected_extensions.posted_at`
is a relative string like "3 days ago" or "Just posted" - so it's
converted to an approximate ISO date rather than parsed as a real
timestamp; unrecognized phrasing falls back to an empty string.

`detected_extensions.work_from_home` is a genuine boolean remote flag when
present, so - unlike the keyword-heuristic sources - `remote` is read
directly from it (defaulting to False when absent, same as USAJOBS).
"""

import re
from datetime import datetime, timedelta, timezone

import requests

from .base import BaseJobSource
from .config import SERPAPI_API_KEY
from .utils import dedupe_tags, request_with_retry

API_URL = "https://serpapi.com/search"

# Adzuna/Jooble-style wildcard: SerpApi requires a non-empty `q`, and this
# project has no single search term to scope results to.
SEARCH_QUERY = "jobs"

# Each page is a billable search against the account's monthly quota, so
# this is kept small (5 pages * 10 jobs/page = 50 jobs per run) rather than
# pushed to whatever the API would technically allow.
MAX_PAGES = 5

REQUEST_TIMEOUT = 30

_RELATIVE_POSTED_PATTERN = re.compile(r"(\d+)\+?\s*(minute|hour|day|week|month|year)s?\s+ago")
_RELATIVE_UNIT_TO_DAYS = {"minute": 0, "hour": 0, "day": 1, "week": 7, "month": 30, "year": 365}


def _relative_posted_to_iso(text):
    """Best-effort conversion of Google Jobs' relative "posted_at" text (e.g. "3 days ago") to an ISO date."""
    if not text:
        return ""

    normalized = text.strip().lower()
    today = datetime.now(timezone.utc).date()

    if normalized in ("just posted", "today"):
        return today.strftime("%Y-%m-%d")
    if normalized == "yesterday":
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")

    match = _RELATIVE_POSTED_PATTERN.search(normalized)
    if not match:
        return ""

    amount, unit = int(match.group(1)), match.group(2)
    days = amount * _RELATIVE_UNIT_TO_DAYS[unit]
    return (today - timedelta(days=days)).strftime("%Y-%m-%d")


class SerpApiSource(BaseJobSource):
    name = "serpapi"

    def fetch_raw(self):
        """Fetch pages of jobs from the SerpApi Google Jobs engine using a wildcard search."""
        if not SERPAPI_API_KEY:
            raise ValueError("SERPAPI_API_KEY is not set")

        jobs = []
        params = {"engine": "google_jobs", "q": SEARCH_QUERY, "api_key": SERPAPI_API_KEY}

        for _ in range(MAX_PAGES):
            response = request_with_retry(requests.get, API_URL, params=params, timeout=REQUEST_TIMEOUT)
            payload = response.json()

            page_jobs = payload.get("jobs_results", [])
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            next_token = (payload.get("serpapi_pagination") or {}).get("next_page_token")
            if not next_token:
                break
            params["next_page_token"] = next_token

        return jobs

    def normalize(self, raw_job):
        """Map a SerpApi Google Jobs record onto the project's standard schema."""
        detected = raw_job.get("detected_extensions") or {}

        # Prefer the original posting's own link over Google's tracking-
        # wrapped share_link, which is more likely to change between runs.
        url = (
            raw_job.get("source_link")
            or (raw_job.get("apply_options") or [{}])[0].get("link")
            or raw_job.get("share_link", "")
        )

        schedule_type = detected.get("schedule_type")
        tags = dedupe_tags([schedule_type] if schedule_type else None)

        return {
            "title": raw_job.get("title", ""),
            "company": raw_job.get("company_name", ""),
            "location": raw_job.get("location") or "Unknown",
            "url": url,
            "tags": tags,
            "remote": bool(detected.get("work_from_home", False)),
            "posted": _relative_posted_to_iso(detected.get("posted_at")),
        }
