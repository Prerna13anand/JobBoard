"""
MyJobMag "Detailed RSS Feed" source (Nigeria job board).

Feed: https://www.myjobmag.com/jobsxml_by_categories.xml
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via a live request (no credentials sent, default requests
User-Agent) returning a normal 200 response with real, currently-posted
jobs (newest ones published minutes before this was checked, several
carrying a future `expiryDate` a week or two out - these are open, live
postings, not a stale archive).

MyJobMag documents five feeds on https://www.myjobmag.com/feeds/: a
"Summarized RSS Feed" (title/industry/link only, company embedded in the
title as "Position at Company"), this "Detailed RSS Feed" (dedicated
`<company>`/`<location>`/`<position>` fields - used here since it maps
onto this project's schema without any title-splitting heuristics), two
"Aggregate Feed" variants (company but no location), and a blog feed
(not jobs). All four job feeds return exactly 100 items with no
documented way to request more or fewer.

No pagination: `robots.txt` disallows every query-string URL
(`Disallow: /*?`) and specifically `Disallow: /&page=`, and the feeds
page itself documents no page/limit parameter for any of the five feeds -
so, as with We Work Remotely/Jobspresso/NoDesk in this project, this
source fetches the single default feed (its newest 100 postings) with no
pagination attempted.

Despite the XML prolog declaring `encoding="iso-8859-1"` and the feed
using several HTML named entities that aren't valid bare XML (`&rsquo;`,
`&mdash;`, `&nbsp;`, etc. - confirmed live), every field this source
reads (`title`, `position`, `company`, `location`, `link`, `pubDate`) is
wrapped in a CDATA section, where such entities are literal text rather
than parsed XML entities - so, unlike NoDesk's feed, this one parses
cleanly with a plain `ET.fromstring` on the raw response bytes (letting
the parser honor the declared iso-8859-1 encoding itself) with no
entity-fixing needed. Those problem entities only ever appear inside the
free-text `<description>` field, which this project's schema doesn't use.

This feed only ever covers MyJobMag's Nigeria site (myjobmag.com);
per-item `<location>` values seen live are Nigerian states (e.g. "Lagos",
"Abuja") or "All" for nationwide roles - MyJobMag's other country sites
(Ghana, Kenya, South Africa, UK) are separate domains with their own
feeds, not covered by this one URL.
"""

import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry

API_URL = "https://www.myjobmag.com/jobsxml_by_categories.xml"
REQUEST_TIMEOUT = 15

REMOTE_KEYWORDS = ("remote", "work from home", "telecommute")


def _rfc2822_to_iso(date_string):
    """Convert an RSS pubDate (RFC 2822, e.g. "Thu, 9 Jul 2026 16:56:52 GMT") to ISO "YYYY-MM-DD"."""
    if not date_string:
        return ""
    try:
        return parsedate_to_datetime(date_string).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


class MyJobMagSource(BaseJobSource):
    name = "myjobmag"

    def fetch_raw(self):
        """Fetch the current job list from the MyJobMag Detailed RSS feed."""
        try:
            response = request_with_retry(requests.get, API_URL, timeout=REQUEST_TIMEOUT)
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"[{self.name}] failed to fetch or parse the feed: {exc}")
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        fields = ("position", "company", "location", "industry", "link", "pubDate")
        jobs = []
        for item in channel.findall("item"):
            job = {}
            for tag in fields:
                el = item.find(tag)
                job[tag] = el.text.strip() if el is not None and el.text else ""
            jobs.append(job)

        return jobs

    def normalize(self, raw_job):
        """Map a MyJobMag RSS item onto the project's standard schema."""
        title = raw_job.get("position", "")
        location = raw_job.get("location") or "Nigeria"

        industry = raw_job.get("industry")
        tags = dedupe_tags([industry] if industry else None)

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": raw_job.get("company", ""),
            "location": location,
            "url": raw_job.get("link", ""),
            "tags": tags,
            "remote": remote,
            "posted": _rfc2822_to_iso(raw_job.get("pubDate")),
        }
