"""
Taiwan Ministry of Labor Open Job API source (legacy free.taiwanjobs.gov.tw
web service, listed as open data on data.gov.tw dataset 44062).

Endpoint: GET https://free.taiwanjobs.gov.tw/webservice_taipei/Webservice.ashx
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via live requests (no credentials sent) returning normal 200
responses with real job data.

API quirk: the response is XML, but its tag names embed a Chinese-language
field description in full-width parentheses directly in the tag itself,
e.g. `<OCCU_DESC（職務名稱）>...</OCCU_DESC（職務名稱）>`. Those parentheses
are not valid XML Name characters, so Python's stdlib `xml.etree.ElementTree`
rejects the raw response outright ("not well-formed"). Before parsing, a
regex strips the parenthetical suffix from tag delimiters only (matching
`<TAG（...）>` / `</TAG（...）>` specifically, not free text), leaving any
full-width punctuation inside the actual CDATA content untouched.

Pagination: only a `count` parameter was found (no working offset/page/
skip/start parameter - several were tried live and all were silently
ignored). `count` is capped at 1,000 regardless of what's requested
(confirmed live: count=1500 still returns exactly 1,000 records) - this
matches the ~1,000-record ceiling noted in prior research. Since there is
no confirmed way to page past that single call, this source fetches one
call at the cap and reports whatever it returns, the same "single largest
available fetch" approach used for Jobicy/RemoteJobs.org-style feeds with
no real pagination. Live testing also saw one transient truncated/invalid
response out of several identical requests, so a failed parse is handled
the same way a failed request is - logged and treated as no data for this
run, rather than crashing the whole aggregation.
"""

import re
import xml.etree.ElementTree as ET

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry

API_URL = "https://free.taiwanjobs.gov.tw/webservice_taipei/Webservice.ashx"

# Documented/confirmed maximum actually honored for `count`.
PAGE_SIZE = 1000

REQUEST_TIMEOUT = 30

# Matches only tag delimiters like <OCCU_DESC（職務名稱）> or
# </OCCU_DESC（職務名稱）>, not any parenthetical text inside CDATA content.
_TAG_SUFFIX_RE = re.compile(r"<(/?)([A-Za-z0-9_]+)（[^）]*）>")

REMOTE_KEYWORDS = ("remote", "遠端", "居家辦公", "在家工作")


def _yyyymmdd_to_iso(date_string):
    """Convert a "YYYYMMDD" date string (e.g. "20260611") to ISO "YYYY-MM-DD"."""
    if not date_string or len(date_string) != 8 or not date_string.isdigit():
        return ""
    return f"{date_string[0:4]}-{date_string[4:6]}-{date_string[6:8]}"


class TaiwanMOLSource(BaseJobSource):
    name = "taiwan_mol"

    def fetch_raw(self):
        """Fetch the current job list from the Taiwan MOL open job web service."""
        try:
            response = request_with_retry(
                requests.get,
                API_URL,
                params={"count": PAGE_SIZE},
                timeout=REQUEST_TIMEOUT,
            )
            cleaned = _TAG_SUFFIX_RE.sub(r"<\1\2>", response.text)
            root = ET.fromstring(cleaned)
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"[{self.name}] failed to fetch or parse the feed: {exc}")
            return []

        jobs = []
        for data in root.findall("Data"):
            jobs.append({child.tag: (child.text or "").strip() for child in data})

        return jobs

    def normalize(self, raw_job):
        """Map a Taiwan MOL job record onto the project's standard schema."""
        title = raw_job.get("OCCU_DESC", "")
        location = raw_job.get("CITYNAME") or "Taiwan"

        tags = dedupe_tags(
            [raw_job["CJOB_NAME1"]] if raw_job.get("CJOB_NAME1") else None,
            [raw_job["CJOB_NAME2"]] if raw_job.get("CJOB_NAME2") else None,
            [raw_job["WK_TYPE"]] if raw_job.get("WK_TYPE") else None,
        )

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": raw_job.get("COMPNAME", ""),
            "location": location,
            "url": raw_job.get("URL_QUERY", ""),
            "tags": tags,
            "remote": remote,
            "posted": _yyyymmdd_to_iso(raw_job.get("TRANDATE", "")),
        }
