"""
Working Nomads Jobs API (remote-only job board).

Endpoint: https://www.workingnomads.com/api/exposed_jobs/
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via a live request (no credentials sent, default requests
User-Agent) returning a normal 200 response with 36 real, currently-posted
jobs. This is the same endpoint the site's own jobs page fetches from
(found embedded in https://www.workingnomads.com/jobs's page source), and
robots.txt (`User-agent: *` / `Disallow:` with no paths) places no
restriction on it.

No pagination: `page`/`limit`/`category`/`tag` query params were all
tried live and are silently ignored (byte-for-byte identical response
each time) - the endpoint always returns the same 36 most recent jobs,
the same "single largest available fetch" approach used for other
no-pagination sources in this project (We Work Remotely, NoDesk). No
separate per-category endpoint or RSS feed was found either (checked
`/jobs/rss`, `/feed`, `/rss` - all 404 or redirect back to `/jobs`).

Each job record already comes with clean, dedicated fields - company_name,
category_name, a comma-separated tags string, a free-text location, and an
ISO 8601 pub_date with UTC offset - so unlike We Work Remotely/NoDesk
there's no title-splitting needed here.

Working Nomads is a remote-only job board (its listings are all remote by
definition, confirmed by every sampled `location` value being either a
plain region/"Global" or an explicit "... Remote"/timezone-window string,
never an onsite address), so every listing is marked `remote: True`, the
same convention already used for We Work Remotely and NoDesk.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://www.workingnomads.com/api/exposed_jobs/"
REQUEST_TIMEOUT = 15


class WorkingNomadsSource(BaseJobSource):
    name = "workingnomads"

    def fetch_raw(self):
        """Fetch the current job list from the Working Nomads jobs API."""
        try:
            response = request_with_retry(requests.get, API_URL, timeout=REQUEST_TIMEOUT)
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"[{self.name}] failed to fetch or parse the job list: {exc}")
            return []

        return payload if isinstance(payload, list) else []

    def normalize(self, raw_job):
        """Map a Working Nomads job record onto the project's standard schema."""
        tags_string = raw_job.get("tags") or ""
        tags = [tag.strip() for tag in tags_string.split(",") if tag.strip()]
        category = raw_job.get("category_name")
        tags = dedupe_tags(tags, [category] if category else None)

        return {
            "title": raw_job.get("title", ""),
            "company": raw_job.get("company_name", ""),
            "location": raw_job.get("location") or "Worldwide",
            "url": raw_job.get("url", ""),
            "tags": tags,
            # Working Nomads is a remote-only job board, so every listing is remote.
            "remote": True,
            "posted": iso_string_to_date(raw_job.get("pub_date")),
        }
