"""
NAV Arbeidsplassen Job Vacancy Feed source (Norwegian Labour and Welfare
Administration - NAV), via the current "stilling-feed" API.

Docs: https://navikt.github.io/pam-stilling-feed/
Endpoint: GET https://pam-stilling-feed.nav.no/api/v1/feed

IMPORTANT - this replaces NAV's older "public-feed" API (the one most
prior research on this provider refers to), which was shut down in May
2025; its README now just points here. Confirmed live.

Authentication is required (unlike every other Phase 1 source in this
project): every request needs an `Authorization: Bearer <token>` header.
However, no registration is needed to obtain a usable token - a public,
no-signup token is available via a plain GET to
https://pam-stilling-feed.nav.no/api/publicToken (confirmed live), which
NAV's own docs say "can be used for experiments". That endpoint returns
plain text ("Current public token for Nav Job Vacancy Feed:\n<token>"),
not JSON, and the token "will rotate at irregular intervals" - so it's
fetched fresh on every run rather than hardcoded. A private/registered
token is only needed for higher-volume production use, per NAV's docs.

Architecture note: this is a continuous, chronologically-ordered change-feed
(every edit/create/expiry to an ad appends a new entry) going back to
~2019, not a "current postings" search endpoint like every other source in
this project - confirmed live: the very first page (no filtering) is 100%
INACTIVE ads from the start of the feed. NAV's own docs describe fetching
via `If-Modified-Since` to start from a given point in time instead of
page one, which was confirmed live to work: sending that header set to a
recent cutoff returned a healthy mix of ACTIVE and INACTIVE entries from
around that date instead of years-old history. This source uses that
header on the first request only, then walks forward via each page's
`next_url` (confirmed live: cursor-based, 1,000 items/page), keeping only
entries whose `_feed_entry.status` is "ACTIVE". Per NAV's docs, `next_id`
becomes null once the feed has caught up to the present moment; a
self-imposed page cap also guards against an unbounded walk since the
exact volume of intervening (non-active) feed entries isn't predictable.

Each feed item's own `url` field is an internal API path
(`/api/v1/feedentry/{uuid}`, itself requiring the bearer token) rather than
a public link - not something to put in this project's `url` field.
Instead, the public job-posting URL pattern
`https://arbeidsplassen.nav.no/stillinger/stilling/{uuid}` was confirmed
live (fetched the page, its title matched the ad's real title) and is used
here instead.
"""

import time
from email.utils import formatdate
from urllib.parse import urljoin

import requests

from .base import BaseJobSource
from .utils import iso_string_to_date, request_with_retry

BASE_URL = "https://pam-stilling-feed.nav.no"
PUBLIC_TOKEN_URL = f"{BASE_URL}/api/publicToken"
FEED_URL = f"{BASE_URL}/api/v1/feed"
PUBLIC_JOB_URL = "https://arbeidsplassen.nav.no/stillinger/stilling/{uuid}"

# How far back to jump on the very first request instead of starting at
# the beginning of the feed (~2019) - see module docstring.
LOOKBACK_DAYS = 30

# Safety cap on how many pages (1,000 items each) to walk forward looking
# for ACTIVE entries. The feed is expected to signal a natural stop
# (next_id == null) once caught up to the present, but the actual number
# of pages needed to get there from LOOKBACK_DAYS isn't predictable, so
# this bounds the worst case at a reasonable number of requests.
MAX_PAGES = 20

REQUEST_TIMEOUT = 30

# NAV has no dedicated remote flag, so - as with several other sources in
# this project - remote-friendly postings are detected via keyword, in
# both English and Norwegian.
REMOTE_KEYWORDS = ("remote", "hjemmekontor", "fjernarbeid")


class NAVNorwaySource(BaseJobSource):
    name = "nav_norway"

    def _fetch_public_token(self):
        """Fetch a fresh no-registration public token (plain text response, rotates irregularly)."""
        response = request_with_retry(requests.get, PUBLIC_TOKEN_URL, timeout=REQUEST_TIMEOUT)
        return response.text.strip().splitlines()[-1].strip()

    def fetch_raw(self):
        """Walk the NAV job vacancy feed forward from a recent cutoff, collecting active ads."""
        try:
            token = self._fetch_public_token()
        except requests.RequestException as exc:
            print(f"[{self.name}] failed to fetch a public token: {exc}")
            return []

        headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
        cutoff = formatdate(time.time() - LOOKBACK_DAYS * 86400, usegmt=True)

        jobs = []
        url = FEED_URL
        request_headers = {**headers, "If-Modified-Since": cutoff}

        for _ in range(MAX_PAGES):
            try:
                response = request_with_retry(
                    requests.get, url, headers=request_headers, timeout=REQUEST_TIMEOUT
                )
                payload = response.json()
            except requests.RequestException as exc:
                print(f"[{self.name}] stopped early: {exc}")
                break

            for item in payload.get("items") or []:
                entry = item.get("_feed_entry") or {}
                if entry.get("status") == "ACTIVE":
                    jobs.append(item)

            next_id = payload.get("next_id")
            next_url = payload.get("next_url")
            if not next_id or not next_url:
                break

            url = urljoin(BASE_URL, next_url)
            # If-Modified-Since is only needed to establish the starting point;
            # next_url already encodes the current position in the feed.
            request_headers = headers

        return jobs

    def normalize(self, raw_job):
        """Map a NAV feed item onto the project's standard schema."""
        entry = raw_job.get("_feed_entry") or {}
        title = entry.get("title") or raw_job.get("title", "")
        job_id = entry.get("uuid") or raw_job.get("id", "")
        location = entry.get("municipal") or "Norway"

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": entry.get("businessName", ""),
            "location": location,
            "url": PUBLIC_JOB_URL.format(uuid=job_id) if job_id else "",
            # No category/skill data at this feed's summary level (only
            # available per-ad via the internal detail endpoint, which
            # this source deliberately avoids calling once per posting).
            "tags": [],
            "remote": remote,
            "posted": iso_string_to_date(raw_job.get("date_modified")),
        }
