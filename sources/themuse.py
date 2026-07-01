"""
The Muse Jobs API source.

API docs: https://www.themuse.com/developers/api/v2

The endpoint is page-paginated with a fixed page size of 20 (a `per_page`
param is accepted but ignored). It reports over 400,000 jobs across
20,000+ pages, but the unauthenticated public API hard-rejects any page
number >= 100 with a 400 "Value `page` is too high" error - so 100 pages
(2,000 jobs) is the most this source can ever return without an API key.
Jobs are returned newest-first, so this is a recent slice, not the archive.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date

API_URL = "https://www.themuse.com/api/public/jobs"

# Hard ceiling enforced by the public API itself (page 100+ returns a 400).
MAX_PAGES = 100

REQUEST_TIMEOUT = 15

# The Muse marks a job as remote by including this pseudo-location among
# its `locations`, rather than via a dedicated boolean field.
REMOTE_LOCATION_NAME = "Flexible / Remote"


class TheMuseSource(BaseJobSource):
    name = "themuse"

    def fetch_raw(self):
        """Fetch pages of jobs from The Muse API, newest first."""
        jobs = []

        for page in range(MAX_PAGES):
            response = requests.get(API_URL, params={"page": page}, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()

            page_jobs = payload.get("results", [])
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if page + 1 >= payload.get("page_count", 0):
                break

        return jobs

    def normalize(self, raw_job):
        """Map a The Muse job record onto the project's standard schema."""
        location_names = [loc.get("name") for loc in raw_job.get("locations", []) if loc.get("name")]
        location = ", ".join(location_names) if location_names else "Worldwide"

        # categories/levels/tags are each lists of {"name": ...} objects
        # rather than plain strings, so pull out the names before merging.
        tags = dedupe_tags(
            [c["name"] for c in raw_job.get("categories", []) if c.get("name")],
            [l["name"] for l in raw_job.get("levels", []) if l.get("name")],
            [t["name"] for t in raw_job.get("tags", []) if t.get("name")],
        )

        return {
            "title": raw_job.get("name", ""),
            "company": (raw_job.get("company") or {}).get("name", ""),
            "location": location,
            "url": (raw_job.get("refs") or {}).get("landing_page", ""),
            "tags": tags,
            "remote": REMOTE_LOCATION_NAME in location_names,
            "posted": iso_string_to_date(raw_job.get("publication_date")),
        }
