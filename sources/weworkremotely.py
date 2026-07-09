"""
We Work Remotely RSS feed source (remote-only job board).

Feed: https://weworkremotely.com/remote-jobs.rss
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via a live request (no credentials sent) returning a normal 200
response with 100 real, currently-posted jobs (newest one published just
hours before this was checked). We Work Remotely also publishes per-category
feeds (programming, design, etc.) - only the main combined feed is used
here to keep this source to the single official feed URL, matching what
was verified live.

There is no pagination: RSS has no offset/page mechanism, and the feed
always returns the newest 100 items - the same "single largest available
fetch" approach used for other no-pagination sources in this project
(Jobicy, RemoteJobs.org's page-less predecessor cases, etc.).

Feed items have no dedicated company-name field. Every item's `<title>`
was confirmed live to consistently follow a "Company: Job Title" format
(checked across many items, e.g. "Cranky Concierge: Travel Coordinator",
"Lemon.io: Senior React Full-stack Developer") - split on the first ": "
to recover both.

Feed items have no dedicated posted-date-only field either: `<pubDate>` is
an RFC 2822 datetime string (e.g. "Wed, 08 Jul 2026 22:56:12 +0000"), parsed
via the stdlib `email.utils.parsedate_to_datetime` (no new dependency).
"""

import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry

API_URL = "https://weworkremotely.com/remote-jobs.rss"
REQUEST_TIMEOUT = 15


def _rfc2822_to_iso(date_string):
    """Convert an RSS pubDate (RFC 2822, e.g. "Wed, 08 Jul 2026 22:56:12 +0000") to ISO "YYYY-MM-DD"."""
    if not date_string:
        return ""
    try:
        return parsedate_to_datetime(date_string).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


class WeWorkRemotelySource(BaseJobSource):
    name = "weworkremotely"

    def fetch_raw(self):
        """Fetch the current job list from the We Work Remotely RSS feed."""
        try:
            response = request_with_retry(requests.get, API_URL, timeout=REQUEST_TIMEOUT)
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"[{self.name}] failed to fetch or parse the feed: {exc}")
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        fields = ("title", "region", "country", "skills", "category", "type", "pubDate", "link")
        jobs = []
        for item in channel.findall("item"):
            job = {}
            for tag in fields:
                el = item.find(tag)
                job[tag] = el.text.strip() if el is not None and el.text else ""
            jobs.append(job)

        return jobs

    def normalize(self, raw_job):
        """Map a We Work Remotely RSS item onto the project's standard schema."""
        raw_title = raw_job.get("title", "")
        if ": " in raw_title:
            company, title = raw_title.split(": ", 1)
        else:
            company, title = "", raw_title

        location = raw_job.get("region") or raw_job.get("country") or "Worldwide"

        # skills is a comma-separated, Oxford-comma list (e.g. "AWS, React,
        # and TypeScript"), so strip a leading "and " left over from splitting.
        skills = []
        for skill in raw_job.get("skills", "").split(","):
            skill = skill.strip()
            if skill.lower().startswith("and "):
                skill = skill[4:].strip()
            if skill:
                skills.append(skill)
        category = raw_job.get("category")
        job_type = raw_job.get("type")
        tags = dedupe_tags(skills, [category] if category else None, [job_type] if job_type else None)

        return {
            "title": title,
            "company": company,
            "location": location,
            "url": raw_job.get("link", ""),
            "tags": tags,
            # We Work Remotely is a remote-only job board, so every listing is remote.
            "remote": True,
            "posted": _rfc2822_to_iso(raw_job.get("pubDate")),
        }
