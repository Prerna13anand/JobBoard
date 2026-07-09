"""
Jobspresso RSS feed source (remote-only job board).

Feed: https://jobspresso.co/jobs/feed/
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via a live request (no credentials sent, default requests
User-Agent) returning a normal 200 response with real, currently-posted
jobs (newest one published minutes before this was checked).

Pagination via `?paged=N` was confirmed to work live (each page returns 20
items, reachable at least 50 pages deep, back to 2020) - but
jobspresso.co/robots.txt disallows every query-string URL site-wide
(`Disallow: /*?`), so pagination is intentionally not used here out of
respect for that policy. This matches the We Work Remotely source in this
project: a single fetch of the default feed (the newest 20 postings), no
pagination.

Feed items have no dedicated company-name or location field. Every item's
`<dc:creator>` was confirmed live to consistently follow a
"Company<br>(pin icon)&nbsp;Location" format (e.g.
"Airalo<br>(pin)&nbsp;United Kingdom, Spain, Dubai") - split on "<br>" to
recover both, then strip the leading pin icon and HTML whitespace entity
from the location half.

Feed items have no category/tag data (every item checked live had an empty
`<category>` list), so `tags` is always empty for this source.

`<pubDate>` is an RFC 2822 datetime string, parsed the same way as We Work
Remotely's feed in this project (via the stdlib
`email.utils.parsedate_to_datetime`).
"""

import html
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

from .base import BaseJobSource
from .utils import request_with_retry

API_URL = "https://jobspresso.co/jobs/feed/"
REQUEST_TIMEOUT = 15

DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
CREATOR_TAG = f"{{{DC_NAMESPACE}}}creator"

# The pin icon Jobspresso prefixes each location with inside <dc:creator>.
LOCATION_PIN = "⚲"


def _rfc2822_to_iso(date_string):
    """Convert an RSS pubDate (RFC 2822, e.g. "Wed, 08 Jul 2026 22:56:12 +0000") to ISO "YYYY-MM-DD"."""
    if not date_string:
        return ""
    try:
        return parsedate_to_datetime(date_string).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


class JobspressoSource(BaseJobSource):
    name = "jobspresso"

    def fetch_raw(self):
        """Fetch the current job list from the Jobspresso jobs RSS feed."""
        try:
            response = request_with_retry(requests.get, API_URL, timeout=REQUEST_TIMEOUT)
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"[{self.name}] failed to fetch or parse the feed: {exc}")
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        jobs = []
        for item in channel.findall("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            creator_el = item.find(CREATOR_TAG)

            jobs.append(
                {
                    "title": title_el.text.strip() if title_el is not None and title_el.text else "",
                    "link": link_el.text.strip() if link_el is not None and link_el.text else "",
                    "pubDate": pub_el.text.strip() if pub_el is not None and pub_el.text else "",
                    "creator": creator_el.text if creator_el is not None and creator_el.text else "",
                }
            )

        return jobs

    def normalize(self, raw_job):
        """Map a Jobspresso RSS item onto the project's standard schema."""
        creator = html.unescape(raw_job.get("creator", ""))
        if "<br>" in creator:
            company, location = creator.split("<br>", 1)
        else:
            company, location = creator, ""

        company = company.strip()
        location = location.replace(LOCATION_PIN, "").strip() or "Worldwide"

        return {
            "title": raw_job.get("title", ""),
            "company": company,
            "location": location,
            "url": raw_job.get("link", ""),
            "tags": [],
            # Jobspresso is a remote-only job board, so every listing is remote.
            "remote": True,
            "posted": _rfc2822_to_iso(raw_job.get("pubDate")),
        }
