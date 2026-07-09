"""
Mustakbil.com RSS feed source (Pakistan-founded, multi-country job board).

Feed: https://rss.mustakbil.com/jobs-rss
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via a live request (no credentials sent, default requests
User-Agent) returning a normal 200 response with 500 real, currently-posted
jobs (newest ones published hours before this was checked). robots.txt at
mustakbil.com only blocks known SEO/scraping bots by name (AhrefsBot,
SemrushBot, MJ12bot, etc.) and Google Ads bots from /account/ - nothing
that applies to a generic client fetching this feed.

Despite the name, this is not Pakistan-only: 354 of 500 live items were
Pakistan, but the rest spanned 20+ countries (US, UAE, South Africa,
Philippines, Nigeria, Saudi Arabia, Canada, etc.), each served from a
country subdomain (e.g. `ca.mustakbil.com/jobs/job/...` for the Canada
listings) while all items come back in this one combined feed.

No pagination: `?page=`, `?p=`, and `?start=` all return HTTP 200 but are
byte-for-byte identical to the base feed (confirmed live) - like NoDesk,
this looks like a single pre-built feed rather than a paginated one, so
there is nothing to page through. The feed already returns 500 items in
one fetch, larger than any other RSS source in this project.

Two formatting quirks, found via live testing:

- Every field is CDATA-wrapped, so - as with MyJobMag - entities inside
  it are literal text, not parsed XML entities. Unlike MyJobMag, some of
  those literal entities land in fields this project actually reads
  (title, company, category, and item-level pubdate all contain leftover
  numeric/named references like `&#x2B;` for "+", `&#xEB;` for "e" with a
  circumflex, and `&amp;` for "&") - each is resolved with `html.unescape`
  before use, the same fix already applied to Jobspresso/NoDesk.
- `<title>` always follows "<Job Title> Jobs in <City>, <Country>"
  (confirmed live across all 500 items, zero exceptions) - since dedicated
  `<city>`/`<country>` fields already exist, that redundant suffix is
  stripped back off to leave a clean job title.
"""

import html
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry

API_URL = "https://rss.mustakbil.com/jobs-rss"
REQUEST_TIMEOUT = 15

REMOTE_KEYWORDS = ("remote", "work from home", "telecommute")


def _rfc2822_to_iso(date_string):
    """Convert an RSS pubdate (RFC 2822, e.g. "Wed, 08 Jul 2026 22:32:39 +0000") to ISO "YYYY-MM-DD"."""
    if not date_string:
        return ""
    try:
        return parsedate_to_datetime(date_string).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


class MustakbilSource(BaseJobSource):
    name = "mustakbil"

    def fetch_raw(self):
        """Fetch the current job list from the Mustakbil.com jobs RSS feed."""
        try:
            response = request_with_retry(requests.get, API_URL, timeout=REQUEST_TIMEOUT)
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"[{self.name}] failed to fetch or parse the feed: {exc}")
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        fields = ("title", "company", "city", "country", "category", "link", "pubdate")
        jobs = []
        for item in channel.findall("item"):
            job = {}
            for tag in fields:
                el = item.find(tag)
                job[tag] = el.text.strip() if el is not None and el.text else ""
            jobs.append(job)

        return jobs

    def normalize(self, raw_job):
        """Map a Mustakbil.com RSS item onto the project's standard schema."""
        title = html.unescape(raw_job.get("title", ""))
        city = raw_job.get("city", "")
        country = raw_job.get("country", "")

        suffix = f"Jobs in {city}, {country}"
        if city and country and title.endswith(suffix):
            title = title[: -len(suffix)].strip()

        location = ", ".join(part for part in (city, country) if part)

        category = html.unescape(raw_job.get("category", ""))
        tags = dedupe_tags([category] if category else None)

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": html.unescape(raw_job.get("company", "")).strip(),
            "location": location,
            "url": raw_job.get("link", ""),
            "tags": tags,
            "remote": remote,
            "posted": _rfc2822_to_iso(html.unescape(raw_job.get("pubdate", ""))),
        }
