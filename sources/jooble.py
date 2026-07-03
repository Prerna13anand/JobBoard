"""
Jooble Jobs API source.

API docs: https://jooble.org/api/about (registration required for a key);
technical reference: https://help.jooble.org/en/support/solutions/articles/60001448238-rest-api-documentation

Endpoint: POST https://jooble.org/api/{api_key} - the API key is part of
the URL path rather than a header or query param. `keywords` is a required
body field (an empty string is rejected with a 400); this project has no
single search term to scope results to, so a single space is sent as a
wildcard-style query, which was confirmed (by live testing against the
real API) to return the broadest result set available.

Pagination is via `page` + `ResultOnPage`. `ResultOnPage` is honored up to
100; values above that silently fall back to the default of 30 rather than
clamping or erroring. Despite the API reporting hundreds of thousands of
total matches for a broad query, the actually retrievable result window is
far smaller in practice - pages run out (return an empty `jobs` list)
around page 12 at ResultOnPage=100, i.e. ~1,100-1,200 jobs - so, like
Himalayas, pagination simply stops the first time a page comes back short.

If JOOBLE_API_KEY isn't configured, fetch_raw() raises so the existing
BaseJobSource.run() error handling logs it and skips this source, the same
way any other fetch failure is handled.
"""

import requests

from .base import BaseJobSource
from .config import JOOBLE_API_KEY
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://jooble.org/api"

# Jooble requires a non-empty `keywords` value; a single space acts as a
# wildcard, matching the broadest possible result set observed during
# testing rather than scoping results to one specific job type.
SEARCH_KEYWORDS = " "

PAGE_SIZE = 100

# Safety ceiling. The wildcard query's actual result window runs out well
# before this (around page 12), but pagination stops on a short/empty page
# regardless - see module docstring.
MAX_PAGES = 20

REQUEST_TIMEOUT = 30

# Jooble aggregates general (mostly on-site) postings with no dedicated
# remote flag, so - similar to the Bundesagentur source - remote-friendly
# listings are detected via keyword, checking both the title and location
# (some listings literally have a location of "Remote").
REMOTE_KEYWORDS = ("remote",)


class JoobleSource(BaseJobSource):
    name = "jooble"

    def fetch_raw(self):
        """Fetch pages of jobs from the Jooble API using a wildcard search."""
        if not JOOBLE_API_KEY:
            raise ValueError("JOOBLE_API_KEY is not set")

        jobs = []
        api_url = f"{API_URL}/{JOOBLE_API_KEY}"

        for page in range(1, MAX_PAGES + 1):
            response = request_with_retry(
                requests.post,
                api_url,
                json={"keywords": SEARCH_KEYWORDS, "page": str(page), "ResultOnPage": str(PAGE_SIZE)},
                timeout=REQUEST_TIMEOUT,
            )
            payload = response.json()

            page_jobs = payload.get("jobs", [])
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break

        return jobs

    def normalize(self, raw_job):
        """Map a Jooble job record onto the project's standard schema."""
        title = raw_job.get("title", "")
        location = raw_job.get("location") or "Unknown"

        tags = dedupe_tags([raw_job["type"]] if raw_job.get("type") else None)

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": raw_job.get("company", ""),
            "location": location,
            "url": raw_job.get("link", ""),
            "tags": tags,
            "remote": remote,
            "posted": iso_string_to_date(raw_job.get("updated")),
        }
