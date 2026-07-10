"""
NHS Jobs public XML search feed source (United Kingdom, health-sector jobs).

Endpoint: GET https://www.jobs.nhs.uk/api/v1/search_xml
Public and free - no registration, no API key, no auth header of any
kind. This is a separate, undocumented surface from NHS's official
"Self-Serve Job Adverts API" (documented at nhsbsa.nhs.uk), which
requires an eligibility application (organisation must be UK-based,
public-facing, and post health/NHS-associated roles at no cost to
jobseekers) reviewed by NHSBSA staff before a credentialed feed is
issued - not self-serve, and not what this module uses. This endpoint
needs none of that.

Confirmed live and stable across two separate verification passes: real,
current job postings (titles, employers, live apply URLs, post/close
dates in the near future) with rich, complete fields on every one of 100
sampled records (no missing title/employer/url/dates). Several signals
suggest this is a deliberately-built external feed rather than an
accidental internal leak: the URL explicitly names its output format
("search_xml", distinct from whatever the site's own JS frontend calls),
success responses are XML while error responses are JSON (implying a
dedicated XML-transformation layer sitting in front of a JSON backend,
built specifically for this output), and no rate limiting was observed
across rapid repeated calls. That said, it remains undocumented - NHS
could change or remove it without notice, the same risk already flagged
for EURES's undocumented endpoint elsewhere in this project.

Pagination is genuine and was independently confirmed live, not just
assumed: `page` (1-based) has no effect on its own, but combined with an
explicit `limit`, each page returns a distinct set of jobs (confirmed by
comparing job IDs across pages 1, 2, 3, 5, 50, 70-120). `limit` is capped
at 100 (requesting 500/1000/5000 all silently return exactly 100).
Pages kept returning distinct live data through at least page 120
(12,000 jobs deep) before falling to zero results around page 130-150
(this appears to be the full current live list, not a hard technical
ceiling), and pages far beyond that (500+) return a JSON error instead of
XML - so MAX_PAGES below is set well past where live data was observed to
run out, as a safety net against a runaway loop rather than a limit this
project expects to hit; the real stop condition in practice is a page
coming back empty.

Each `vacancyDetails` item carries a `locations` element with one or more
child `location` strings (multi-site postings are common), a genuine
`employer` field (the NHS trust/organisation name), and a direct
`url` to the live listing - so, unlike Job Bank Canada elsewhere in this
project, there's no missing-company-name or missing-URL problem here.
`postDate` is ISO 8601 with unusually high sub-second precision (e.g.
"2026-01-07T16:22:37.450927298", 9 fractional digits rather than the
usual 6) - this project's existing `iso_string_to_date` util was
confirmed to still parse it correctly.

No dedicated remote/on-site field exists (NHS clinical/operational roles
are overwhelmingly in-person), so `remote` is a keyword check against
title + location, the same approach used for EURES/MyJobMag/Mustakbil/
Workday/Fantastic.jobs in this project - expected to rarely if ever match
here.
"""

import xml.etree.ElementTree as ET

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://www.jobs.nhs.uk/api/v1/search_xml"

PAGE_SIZE = 100  # confirmed maximum actually honored for `limit`

# Safety net only - live data was observed to run out (an empty page)
# around page 130-150 (~13,000-15,000 jobs); pages far beyond that return
# a JSON error instead of XML. Not a limit this project expects to hit.
MAX_PAGES = 200

REQUEST_TIMEOUT = 30

REMOTE_KEYWORDS = ("remote", "work from home", "telecommute")


class NHSJobsSource(BaseJobSource):
    name = "nhsjobs"

    def fetch_raw(self):
        """Fetch pages of jobs from the NHS Jobs public XML search feed."""
        jobs = []

        for page in range(1, MAX_PAGES + 1):
            try:
                response = request_with_retry(
                    requests.get,
                    API_URL,
                    params={"page": page, "limit": PAGE_SIZE},
                    timeout=REQUEST_TIMEOUT,
                )
                root = ET.fromstring(response.content)
            except (requests.RequestException, ET.ParseError) as exc:
                print(f"[{self.name}] stopped at page {page}: {exc}")
                break

            page_jobs = root.findall("vacancyDetails")
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break

        return jobs

    def normalize(self, raw_job):
        """Map an NHS Jobs <vacancyDetails> element onto the project's standard schema."""
        title_el = raw_job.find("title")
        employer_el = raw_job.find("employer")
        url_el = raw_job.find("url")
        post_date_el = raw_job.find("postDate")
        type_el = raw_job.find("type")

        locations_el = raw_job.find("locations")
        locations = [
            loc.text.strip() for loc in (locations_el.findall("location") if locations_el is not None else [])
            if loc.text and loc.text.strip()
        ]
        location = ", ".join(locations) or "United Kingdom"

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        tags = dedupe_tags([type_el.text] if type_el is not None and type_el.text else None)

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": employer_el.text.strip() if employer_el is not None and employer_el.text else "",
            "location": location,
            "url": url_el.text.strip() if url_el is not None and url_el.text else "",
            "tags": tags,
            "remote": remote,
            "posted": iso_string_to_date(post_date_el.text if post_date_el is not None else None),
        }
