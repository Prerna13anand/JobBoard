"""
Get on Board Jobs API (tech recruitment platform for Latin America).

API docs: https://www.getonbrd.com/api-doc.html (OpenAPI spec at
https://www.getonbrd.com/doc/openapi.yaml)

The docs describe two facets of the API: a "Public API" ("Open to anyone
... No authentication required") covering job categories, company
profiles, and a job search endpoint, and a "Private API" that needs a
paid subscription. `GET /api/v0/jobs` looks public in the spec but is
actually a Private API endpoint in practice - confirmed live it returns
HTTP 401 with no credentials. The documented Public API's search endpoint,
`GET /api/v0/search/jobs`, was confirmed live to work with zero
credentials and no request headers beyond a plain `Accept: application/json`.

That search endpoint requires at least one filter (`query`, `companies`,
`featured`, `remote`, `country_code`, or `board_host` - an empty/missing
filter returns HTTP 422). Since `remote` is a plain boolean covering every
job on the board (confirmed live: `remote=true` and `remote=false` are
non-overlapping and together account for the whole board), both values are
fetched to cover the full listing without picking an arbitrary keyword.

Pagination is page-number based (`page`, `per_page`), with `per_page`
capped at 120 (confirmed live: requesting more is silently clamped to 120)
and a `meta.total_pages` in every response to know when to stop. At the
time of writing this is ~3 pages of remote jobs + ~9 pages of non-remote
jobs (~1,250 jobs total) - MAX_PAGES_PER_FILTER is set well above that to
allow for growth while still bounding the loop.

`expand=["company","tags"]` is passed on every request so the company name
and human-readable tag names come back inlined in the same response,
avoiding a second request per job.

No rate-limit headers or documented quota were observed on live requests;
`request_with_retry` still covers transient 429/5xx responses.
"""

import json

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry, timestamp_to_iso_date

API_URL = "https://www.getonbrd.com/api/v0/search/jobs"
REQUEST_TIMEOUT = 15
PER_PAGE = 120

# Confirmed live: `remote` is a non-nullable boolean on every job, so these
# two filters together cover the entire board with no overlap.
REMOTE_FILTERS = ("true", "false")

# Self-imposed cap per remote/non-remote filter - current live totals are
# ~3 and ~9 pages respectively at PER_PAGE=120; this comfortably covers
# both with room for growth, without risking an unbounded loop if
# `meta.total_pages` were ever to misbehave.
MAX_PAGES_PER_FILTER = 50


class GetOnBoardSource(BaseJobSource):
    name = "getonboard"

    def fetch_raw(self):
        """Fetch every remote and non-remote job page from the Get on Board search API."""
        jobs = []
        for remote_filter in REMOTE_FILTERS:
            jobs.extend(self._fetch_filter(remote_filter))
        return jobs

    def _fetch_filter(self, remote_filter):
        jobs = []
        page = 1
        while page <= MAX_PAGES_PER_FILTER:
            params = {
                "remote": remote_filter,
                "expand": json.dumps(["company", "tags"]),
                "per_page": PER_PAGE,
                "page": page,
            }
            try:
                response = request_with_retry(
                    requests.get,
                    API_URL,
                    params=params,
                    headers={"Accept": "application/json"},
                    timeout=REQUEST_TIMEOUT,
                )
                payload = response.json()
            except requests.RequestException as exc:
                print(f"[{self.name}] stopped early (remote={remote_filter}): {exc}")
                break

            page_jobs = payload.get("data") or []
            if not page_jobs:
                break
            jobs.extend(page_jobs)

            total_pages = (payload.get("meta") or {}).get("total_pages", page)
            if page >= total_pages:
                break
            page += 1

        return jobs

    def normalize(self, raw_job):
        """Map a Get on Board search result onto the project's standard schema."""
        attrs = raw_job.get("attributes", {})

        company_data = ((attrs.get("company") or {}).get("data") or {}).get("attributes") or {}
        company = company_data.get("name", "")

        countries = attrs.get("countries") or []
        location = ", ".join(countries) or "Unknown"

        tag_entries = ((attrs.get("tags") or {}).get("data")) or []
        tag_names = [tag.get("attributes", {}).get("name") for tag in tag_entries]
        category = attrs.get("category_name")
        tags = dedupe_tags(tag_names, [category] if category else None)

        return {
            "title": attrs.get("title", ""),
            "company": company,
            "location": location,
            "url": f"https://www.getonbrd.com/jobs/{raw_job.get('id', '')}",
            "tags": tags,
            "remote": bool(attrs.get("remote", False)),
            "posted": timestamp_to_iso_date(attrs.get("published_at")),
        }
