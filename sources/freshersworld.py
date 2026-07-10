"""
Freshersworld RSS feed source (freshersworld.com - India-focused entry-level/
fresher job board).

Feed: https://www.freshersworld.com/feed
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via a live request (no credentials sent) returning a normal 200
response with 30 real, currently-posted jobs. robots.txt's generic
`User-agent: *` block disallows many site sections (`/jobsearch`,
`/view`, etc.) but not `/feed`, and it explicitly allows `ClaudeBot`.

No pagination: `?page=` and other query params are silently ignored -
confirmed live by fetching the feed twice a few hundred milliseconds
apart, both with and without `?page=2`. Both pairs showed the exact same
kind of one-item drift (a new posting pushed onto the front, the oldest
dropped off the back), proving the feed is just a live, constantly
updating "most recent 30" window and the query param has no effect at
all - the same "single largest available fetch" approach used for other
no-pagination sources in this project (We Work Remotely, NoDesk, Hasjob).

Feed items have no dedicated company, location, or tag fields:

- `<title>` was confirmed live to consistently follow a "{Job Title} Jobs
  Opening in {Company} at {Location}" format (occasionally concatenated
  with no space, e.g. "Senior OfficerJobs Opening in ..." - the regex
  below matches on the literal "Jobs Opening in" / " at " anchors so that
  quirk doesn't matter) - split into title/company/location.
- `<description>` was confirmed live to consistently end with a
  "For more {Category} Jobs click here" link - extracted as a single tag.

There's no posted-date field at all (only a "Last Date of Application"
deadline buried in the description, which is a different thing and not
parsed as if it were a posting date), so `posted` is left empty.

No location in the live sample ever indicated a remote/work-from-home
role (all onsite India/Nepal cities), so `remote` defaults to `False` -
unlike We Work Remotely/NoDesk this is not a remote-only board.

Freshersworld blocks requests without a browser-like User-Agent header
(confirmed live: the default `requests` User-Agent gets an HTTP 403, a
plain "Mozilla/5.0" does not), so one is set explicitly below - the same
fix already used for RemoteOK in this project.
"""

import re
import xml.etree.ElementTree as ET

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry

API_URL = "https://www.freshersworld.com/feed"
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobBoardBot/1.0)"}

_TITLE_RE = re.compile(r"^(.*?)Jobs Opening in (.*?) at (.*)$")
_CATEGORY_RE = re.compile(r"For more (.*?) Jobs click here")


def _parse_title(raw_title):
    """Split a "{Title} Jobs Opening in {Company} at {Location}" feed title into its parts."""
    match = _TITLE_RE.match(raw_title or "")
    if not match:
        return raw_title or "", "", ""
    title, company, location = match.groups()
    return title.strip(), company.strip(), location.strip()


def _extract_category(description):
    """Pull the "For more {Category} Jobs click here" category out of an item's description."""
    match = _CATEGORY_RE.search(description or "")
    return match.group(1).strip() if match else None


class FreshersworldSource(BaseJobSource):
    name = "freshersworld"

    def fetch_raw(self):
        """Fetch the current job list from the Freshersworld RSS feed."""
        try:
            response = request_with_retry(
                requests.get, API_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT
            )
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"[{self.name}] failed to fetch or parse the feed: {exc}")
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        fields = ("title", "link", "description")
        jobs = []
        for item in channel.findall("item"):
            job = {}
            for tag in fields:
                el = item.find(tag)
                job[tag] = el.text.strip() if el is not None and el.text else ""
            jobs.append(job)

        return jobs

    def normalize(self, raw_job):
        """Map a Freshersworld RSS item onto the project's standard schema."""
        title, company, location = _parse_title(raw_job.get("title", ""))
        category = _extract_category(raw_job.get("description"))

        return {
            "title": title,
            "company": company,
            "location": location or "Unknown",
            "url": raw_job.get("link", ""),
            "tags": dedupe_tags([category] if category else None),
            "remote": False,
            "posted": "",
        }
