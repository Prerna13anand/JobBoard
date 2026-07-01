"""
RemoteOK Jobs API source.

API docs: https://remoteok.com/api

The endpoint returns a single JSON array with no pagination support (a
`page` query param is accepted but silently ignored) - it's always the
~100 most recently posted jobs. The first array element is a legal/terms
notice rather than a job record, so it's skipped.

RemoteOK blocks requests without a browser-like User-Agent header, so one
is set explicitly below.
"""

import requests

from .base import BaseJobSource
from .utils import timestamp_to_iso_date

API_URL = "https://remoteok.com/api"
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobBoardBot/1.0)"}


class RemoteOKSource(BaseJobSource):
    name = "remoteok"

    def fetch_raw(self):
        """Fetch the current job list from the RemoteOK API."""
        response = requests.get(API_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        jobs = response.json()

        # Drop the leading legal-notice entry; real job records all have an id.
        return [job for job in jobs if job.get("id")]

    def normalize(self, raw_job):
        """Map a RemoteOK job record onto the project's standard schema."""
        location = (raw_job.get("location") or "").strip(", ")

        return {
            "title": raw_job.get("position", ""),
            "company": raw_job.get("company", ""),
            "location": location or "Worldwide",
            "url": raw_job.get("url", ""),
            "tags": raw_job.get("tags") or [],
            # RemoteOK is a remote-only job board, so every listing is remote.
            "remote": True,
            "posted": timestamp_to_iso_date(raw_job.get("epoch")),
        }
