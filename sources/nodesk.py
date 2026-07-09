"""
NoDesk RSS feed source (remote-only job board).

Feed: https://nodesk.co/remote-jobs/index.xml
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via a live request (no credentials sent, default requests
User-Agent) returning a normal 200 response with real, currently-posted
jobs (newest one published hours before this was checked). The feed URL
itself was not documented anywhere - it was found via the `<link
rel=alternate type=application/rss+xml>` tag on https://nodesk.co/remote-jobs/.

No pagination: `?page=`/`?paged=` query params return HTTP 200 but are
silently ignored (byte-for-byte identical response, confirmed live) - this
looks like a statically pre-rendered file rather than a server-rendered
feed, so there is nothing to paginate. The feed carries only its 10 most
recent postings at any time, the same "single largest available fetch"
approach used for other no-pagination sources in this project (We Work
Remotely, Jobspresso).

Two real formatting quirks, found via live testing:

- The feed is not strictly valid XML: description/title text uses raw HTML
  named entities like `&rsquo;` outside of CDATA, which aren't among XML's
  five predefined entities and make `ET.fromstring` raise a parse error
  as-is. Every such named entity is resolved to its literal Unicode
  character before parsing (numeric references and the five real XML
  entities are left alone for the XML parser itself to handle).
- Titles are inconsistently double-HTML-escaped by the site (e.g. the raw
  feed contains "...Designer &amp;amp; Packaging..." - one level of XML
  entity decoding only gets to the literal text "&amp;", not a real "&").
  `html.unescape` is run a second time after parsing, the same fix already
  used for Jobspresso's `&nbsp;` case in this project.

Feed items have no dedicated company-name or location field. Every item's
`<title>` was confirmed live to consistently follow a "Job Title at
Company" format (e.g. "Analytics Engineer at Metabase") - split on the
*last* " at " (company names were not observed to contain " at ", while a
job title occasionally could, so splitting from the right is safer than
We Work Remotely's from-the-left split on its "Company: Title" format).

There is no location data anywhere in the feed (no dedicated field, and
descriptions are free-text job bodies, not reliably parseable for a
structured location) - NoDesk is a remote-only board, so every listing is
marked `remote: True` with `location` falling back to "Worldwide", the
same default already used for RemoteJobs.org and Jobspresso.
"""

import html
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from html.entities import html5

import requests

from .base import BaseJobSource
from .utils import request_with_retry

API_URL = "https://nodesk.co/remote-jobs/index.xml"
REQUEST_TIMEOUT = 15

# The five entities XML itself predefines; only these are safe to leave for
# ET.fromstring to resolve. Numeric references (&#8217;) are also left alone.
_XML_PREDEFINED_ENTITIES = {"amp;", "lt;", "gt;", "quot;", "apos;"}
_NAMED_ENTITY_RE = re.compile(r"&(#?\w+;)")


def _fix_non_xml_entities(text):
    """Resolve HTML5 named entities (e.g. &rsquo;) that aren't valid bare XML entities."""

    def replace(match):
        entity = match.group(1)
        if entity.startswith("#") or entity in _XML_PREDEFINED_ENTITIES:
            return match.group(0)
        return html5.get(entity, match.group(0))

    return _NAMED_ENTITY_RE.sub(replace, text)


def _rfc2822_to_iso(date_string):
    """Convert an RSS pubDate (RFC 2822, e.g. "Wed, 08 Jul 2026 08:00:00 +0200") to ISO "YYYY-MM-DD"."""
    if not date_string:
        return ""
    try:
        return parsedate_to_datetime(date_string).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


class NoDeskSource(BaseJobSource):
    name = "nodesk"

    def fetch_raw(self):
        """Fetch the current job list from the NoDesk remote-jobs RSS feed."""
        try:
            response = request_with_retry(requests.get, API_URL, timeout=REQUEST_TIMEOUT)
            fixed_xml = _fix_non_xml_entities(response.content.decode("utf-8"))
            root = ET.fromstring(fixed_xml.encode("utf-8"))
        except (requests.RequestException, ET.ParseError, UnicodeDecodeError) as exc:
            print(f"[{self.name}] failed to fetch or parse the feed: {exc}")
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        fields = ("title", "link", "pubDate")
        jobs = []
        for item in channel.findall("item"):
            job = {}
            for tag in fields:
                el = item.find(tag)
                job[tag] = el.text.strip() if el is not None and el.text else ""
            jobs.append(job)

        return jobs

    def normalize(self, raw_job):
        """Map a NoDesk RSS item onto the project's standard schema."""
        raw_title = html.unescape(raw_job.get("title", ""))
        if " at " in raw_title:
            title, company = raw_title.rsplit(" at ", 1)
        else:
            title, company = raw_title, ""

        return {
            "title": title.strip(),
            "company": company.strip(),
            "location": "Worldwide",
            "url": raw_job.get("link", ""),
            "tags": [],
            # NoDesk is a remote-only job board, so every listing is remote.
            "remote": True,
            "posted": _rfc2822_to_iso(raw_job.get("pubDate")),
        }
