"""
Hasjob Atom feed source (hasjob.co - India-focused tech/startup job board).

Feed: https://hasjob.co/feed
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via a live request (no credentials sent) returning a normal 200
response with the site's currently-active job postings. robots.txt only
disallows `/edit/*`, `/confirm/*`, `/withdraw/*`, and `/admin/*` - `/feed`
is unrestricted.

No pagination: `?page=`/`?start=` query params return HTTP 200 but are
silently ignored (byte-for-byte identical response, confirmed live) - the
feed always returns every currently-active listing, the same "single
largest available fetch" approach used for other no-pagination sources in
this project (We Work Remotely, NoDesk, Working Nomads).

Each `<entry>` has a dedicated `<location>` field but no dedicated company
field - the company name is only present as the first `<a>` link (wrapped
in `<strong>`) inside `<content>`, e.g. `<strong><a href="...">Acme
Inc</a></strong><br/>Bangalore` - confirmed live and consistent across
every sampled entry, so it's extracted with a regex anchored on that
`<strong><a>...</a></strong>` wrapper rather than parsed as a full HTML
document (avoiding a new dependency).

Hasjob is not a remote-only board (it lists onsite India-based roles
alongside remote ones), so `remote` is derived from the `<location>` text
itself: values observed live are either a real city/region ("Gwalior",
"Bangalore/Chennai/Pune") or "Anywhere"/"remote" for remote roles - the
latter are treated as remote.
"""

import re
import xml.etree.ElementTree as ET

import requests

from .base import BaseJobSource
from .utils import iso_string_to_date, request_with_retry

API_URL = "https://hasjob.co/feed"
REQUEST_TIMEOUT = 15

_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
_COMPANY_RE = re.compile(r"<strong>\s*<a[^>]*>(.*?)</a>\s*</strong>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_REMOTE_LOCATIONS = {"anywhere", "remote"}


def _extract_company(content_html):
    """Pull the company name out of the first `<strong><a>...</a></strong>` in an entry's content."""
    match = _COMPANY_RE.search(content_html or "")
    if not match:
        return ""
    return _TAG_RE.sub("", match.group(1)).strip()


class HasjobSource(BaseJobSource):
    name = "hasjob"

    def fetch_raw(self):
        """Fetch the current job list from the Hasjob Atom feed."""
        try:
            response = request_with_retry(requests.get, API_URL, timeout=REQUEST_TIMEOUT)
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"[{self.name}] failed to fetch or parse the feed: {exc}")
            return []

        jobs = []
        for entry in root.findall("atom:entry", _ATOM_NS):
            title_el = entry.find("atom:title", _ATOM_NS)
            link_el = entry.find("atom:link", _ATOM_NS)
            location_el = entry.find("atom:location", _ATOM_NS)
            published_el = entry.find("atom:published", _ATOM_NS)
            content_el = entry.find("atom:content", _ATOM_NS)

            jobs.append(
                {
                    "title": title_el.text.strip() if title_el is not None and title_el.text else "",
                    "url": link_el.get("href", "") if link_el is not None else "",
                    "location": location_el.text.strip() if location_el is not None and location_el.text else "",
                    "published": published_el.text.strip() if published_el is not None and published_el.text else "",
                    "content": content_el.text if content_el is not None else "",
                }
            )

        return jobs

    def normalize(self, raw_job):
        """Map a Hasjob Atom entry onto the project's standard schema."""
        location = raw_job.get("location") or "Unknown"

        return {
            "title": raw_job.get("title", ""),
            "company": _extract_company(raw_job.get("content")),
            "location": location,
            "url": raw_job.get("url", ""),
            "tags": [],
            "remote": location.strip().lower() in _REMOTE_LOCATIONS,
            "posted": iso_string_to_date(raw_job.get("published")),
        }
