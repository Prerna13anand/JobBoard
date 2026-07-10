"""
4dayweek.io RSS feed source (jobs from companies offering a 4-day week or
other flexible schedules).

Feed: https://4dayweek.io/feed
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via a live request (no credentials sent, default requests
User-Agent) returning a normal 200 response with 50 real, currently-posted
jobs. The feed is explicitly the site's official public output: it declares
its own `<atom:link rel="self">`, a `<ttl>`, and is not blocked by
https://4dayweek.io/robots.txt.

The site also serves an internal `/api/jobs` endpoint (unauthenticated,
richer data incl. per-job location/work-arrangement), but robots.txt
explicitly lists `Disallow: /api/` - that endpoint backs the site's own
frontend and isn't intended for external use, so it is deliberately not
used here in favor of the officially-published RSS feed.

No pagination: `?page=`/`?limit=` query params return HTTP 200 but are
silently ignored (byte-for-byte identical response aside from
`lastBuildDate`, confirmed live) - the feed always returns the newest 50
items, the same "single largest available fetch" approach used for other
no-pagination sources in this project (We Work Remotely, NoDesk).

Feed items have no dedicated company-name field in `<title>` alone, but
each item also carries an `<author>` tag that was confirmed live to
consistently equal the company name and to consistently match the
"... at {author}" suffix of `<title>` across all 50 items - so `<author>`
is used directly as company, and stripped off `<title>` to recover the
job title.

Feed items have no location or remote/onsite/hybrid field at all (that
data only exists in the disallowed `/api/jobs` endpoint), so `location`
falls back to "Unknown" and `remote` is left `False`, matching the
"Unknown" convention used elsewhere in this project (e.g. Greenhouse,
Ashby) when a source genuinely provides no location data - unlike We Work
Remotely/NoDesk, 4dayweek.io is not a remote-only board so defaulting to
"Worldwide"/`True` would be inaccurate.
"""

import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

from .base import BaseJobSource
from .utils import request_with_retry

API_URL = "https://4dayweek.io/feed"
REQUEST_TIMEOUT = 15


def _rfc2822_to_iso(date_string):
    """Convert an RSS pubDate (RFC 2822, e.g. "Fri, 10 Jul 2026 02:38:39 GMT") to ISO "YYYY-MM-DD"."""
    if not date_string:
        return ""
    try:
        return parsedate_to_datetime(date_string).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


class FourDayWeekSource(BaseJobSource):
    name = "fourdayweek"

    def fetch_raw(self):
        """Fetch the current job list from the 4dayweek.io RSS feed."""
        try:
            response = request_with_retry(requests.get, API_URL, timeout=REQUEST_TIMEOUT)
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"[{self.name}] failed to fetch or parse the feed: {exc}")
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        fields = ("title", "link", "pubDate", "author")
        jobs = []
        for item in channel.findall("item"):
            job = {}
            for tag in fields:
                el = item.find(tag)
                job[tag] = el.text.strip() if el is not None and el.text else ""
            jobs.append(job)

        return jobs

    def normalize(self, raw_job):
        """Map a 4dayweek.io RSS item onto the project's standard schema."""
        raw_title = raw_job.get("title", "")
        company = raw_job.get("author", "")
        suffix = f" at {company}"
        title = raw_title[: -len(suffix)] if company and raw_title.endswith(suffix) else raw_title

        return {
            "title": title,
            "company": company,
            "location": "Unknown",
            "url": raw_job.get("link", ""),
            "tags": [],
            "remote": False,
            "posted": _rfc2822_to_iso(raw_job.get("pubDate")),
        }
