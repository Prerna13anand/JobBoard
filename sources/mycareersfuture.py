"""
MyCareersFuture Jobs API source (Singapore government job portal, run by
Workforce Singapore / SSG).

Endpoint: POST https://api.mycareersfuture.gov.sg/v2/search
Public and free - no registration, no API key, no auth header of any kind.
Confirmed via live requests (no credentials sent) returning normal 200
responses with real job data (71,509 current postings). This is the same
endpoint the mycareersfuture.gov.sg website itself calls - there is no
officially published developer API product or documentation page for it
(the integration details here come from directly probing the live
endpoint), so treat this source as somewhat more fragile than the
officially documented ones elsewhere in this project: it could change
shape without notice.

No keyword/body filters are required - an empty `{"page": N}` body returns
a general browse of all current postings, matching the "fetch broadly"
pattern used by other sources in this project.

Pagination is page-based, but the documented `limit` field in the request
body is silently ignored - every response comes back with exactly 20
results (confirmed live: passing limit=1 still returns 20). Unlike
Arbetsformedlingen and CareerOneStop, there is no hard page ceiling either:
requests for pages far beyond the response's own `_links.last` (page 3575
for the current ~71,500 total) still return HTTP 200 with 20 results
rather than erroring or emptying out. Since there's no natural stopping
point to discover and the total is enormous, pagination is capped at a
fixed, self-imposed number of pages here - the same approach used for the
similarly uncapped Himalayas/The Muse/Adzuna feeds - rather than trying to
walk all ~71,500 postings on every run.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry

API_URL = "https://api.mycareersfuture.gov.sg/v2/search"

# Fixed page size the API actually returns regardless of any requested
# `limit` (see module docstring).
PAGE_SIZE = 20

# Self-imposed cap - the API itself has no discovered ceiling, so this
# keeps each run to a reasonable, well-mannered number of requests against
# a foreign government service. 100 pages * 20 jobs/page = 2,000 jobs.
MAX_PAGES = 100

REQUEST_TIMEOUT = 15

# MyCareersFuture has no dedicated remote flag (the `flexibleWorkArrangements`
# field exists in the schema but was empty in every sample checked), so
# remote-friendly postings are detected via keyword, as with several other
# sources in this project.
REMOTE_KEYWORDS = ("remote", "work from home", "wfh")


class MyCareersFutureSource(BaseJobSource):
    name = "mycareersfuture"

    def fetch_raw(self):
        """Fetch pages of jobs from the MyCareersFuture API, up to a self-imposed page cap."""
        jobs = []

        for page in range(MAX_PAGES):
            try:
                response = request_with_retry(
                    requests.post,
                    API_URL,
                    json={"page": page},
                    timeout=REQUEST_TIMEOUT,
                )
                payload = response.json()
            except requests.RequestException as exc:
                print(f"[{self.name}] stopped early at page {page}: {exc}")
                break

            page_jobs = payload.get("results") or []
            if not page_jobs:
                break

            jobs.extend(page_jobs)

        return jobs

    def normalize(self, raw_job):
        """Map a MyCareersFuture job record onto the project's standard schema."""
        title = raw_job.get("title", "")

        posted_company = raw_job.get("postedCompany") or {}
        hiring_company = raw_job.get("hiringCompany") or {}
        company = posted_company.get("name") or hiring_company.get("name") or ""

        districts = (raw_job.get("address") or {}).get("districts") or []
        district_names = [d["region"] for d in districts if d.get("region")]
        location = ", ".join(dict.fromkeys(district_names)) if district_names else "Singapore"

        categories = [c["category"] for c in raw_job.get("categories") or [] if c.get("category")]
        employment_types = [
            e["employmentType"] for e in raw_job.get("employmentTypes") or [] if e.get("employmentType")
        ]
        tags = dedupe_tags(categories, employment_types)

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": company,
            "location": location,
            "url": (raw_job.get("metadata") or {}).get("jobDetailsUrl", ""),
            "tags": tags,
            "remote": remote,
            # Already an ISO "YYYY-MM-DD" string, no conversion needed.
            "posted": (raw_job.get("metadata") or {}).get("newPostingDate", ""),
        }
