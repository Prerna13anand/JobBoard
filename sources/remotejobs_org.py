"""
RemoteJobs.org Jobs API source (remote-only job board).

Endpoint: GET https://www.remotejobs.org/api/v1/jobs
(The bare `remotejobs.org` host 308-redirects to `www.remotejobs.org` for
this path; `requests` follows that automatically, but the `www` host is
used directly here to avoid the extra hop.)

Public and free - no registration, no API key, no auth header of any kind.
Confirmed via live requests (no credentials sent) returning normal 200
responses with real job data (2,464 current postings). The API's own
response links to docs at `https://remotejobs.org/api/v1/docs`, but that
page 404s - there is no working published documentation to reference
beyond the response shape itself.

No keyword is required - omitting one returns a general browse of all
current postings, matching the "fetch broadly" pattern used by other
sources in this project.

Pagination is via `offset` + `limit`. `limit` is silently capped at 50
regardless of what's requested (confirmed live: passing limit=1000 still
comes back with `pagination.limit: 50`). The response's `pagination.total`
count is not a reliable page-size signal near the end of the result set -
the last page was observed still returning a full 50 records (rather than
the ~14 remaining unique ones) even though `has_more` had already flipped
to `false`. So, unlike every offset-paginated source elsewhere in this
project, the loop here stops on the `has_more` flag itself rather than on
"fewer results than requested".

Live testing also surfaced real rate limiting partway through a full fetch
(an HTTP 429 around page 23). As with Reed, a failed page request stops
the loop rather than crashing, keeping whatever was already collected
instead of losing the whole run to one bad page.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://www.remotejobs.org/api/v1/jobs"

PAGE_SIZE = 50  # documented/confirmed maximum actually honored for `limit`

# Safety net only: `has_more` is expected to end the loop well before this
# (current total is ~2,464 jobs, i.e. ~50 pages), but this guards against
# an unbounded loop if the API ever fails to flip has_more to false.
MAX_OFFSET = 10000

REQUEST_TIMEOUT = 15


class RemoteJobsOrgSource(BaseJobSource):
    name = "remotejobs_org"

    def fetch_raw(self):
        """Fetch pages of jobs from the RemoteJobs.org API until its own has_more flag turns false."""
        jobs = []
        offset = 0

        while offset <= MAX_OFFSET:
            try:
                response = request_with_retry(
                    requests.get,
                    API_URL,
                    params={"limit": PAGE_SIZE, "offset": offset},
                    timeout=REQUEST_TIMEOUT,
                )
                payload = response.json()
            except requests.RequestException as exc:
                print(f"[{self.name}] stopped early at offset {offset}: {exc}")
                break

            page_jobs = payload.get("data") or []
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if not (payload.get("pagination") or {}).get("has_more"):
                break
            offset += PAGE_SIZE

        return jobs

    def normalize(self, raw_job):
        """Map a RemoteJobs.org job record onto the project's standard schema."""
        company = (raw_job.get("company") or {}).get("name", "")

        category = (raw_job.get("category") or {}).get("name")
        job_type = raw_job.get("type")
        tags = dedupe_tags([category] if category else None, [job_type] if job_type else None)

        return {
            "title": raw_job.get("title", ""),
            "company": company,
            "location": raw_job.get("location") or "Worldwide",
            "url": raw_job.get("url") or raw_job.get("apply_url", ""),
            "tags": tags,
            # RemoteJobs.org is a remote-only job board, so every listing is remote.
            "remote": True,
            "posted": iso_string_to_date(raw_job.get("posted_at")),
        }
