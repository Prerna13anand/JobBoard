"""
Lever Postings API source.

API docs: https://github.com/lever/postings-api

Endpoint: GET https://api.lever.co/v0/postings/{site}?mode=json
No authentication is required for GET requests (Lever only requires an
API key for POST-ing applications, which this project never does).

Lever is company-based rather than a single global index: each company
publishes its postings under its own "site" slug. The list of companies
to fetch is COMPANY_SLUGS below - adding a new company later only
requires adding its slug to that list; fetch_raw() already iterates over
it automatically, no logic changes needed.

Pagination is offset-based (`skip` + `limit`), confirmed working live, but
every company tested here returned its complete list in a single
unpaginated call (largest: 276 postings) - unlike Greenhouse, Lever does
support real pagination, so it's implemented as a proper loop (matching
the project's usual pattern) rather than assumed unnecessary, in case a
configured company's board ever exceeds one page.

Each company is fetched independently. A failure on any page for a given
company is caught and logged, stopping pagination for just that company
while keeping whatever pages it already successfully fetched (the same
per-page fault isolation used in bundesagentur.py) - and the remaining
companies are still processed regardless.

Lever's job objects carry no company display name field at all (unlike
Greenhouse's `company_name`), so fetch_raw() tags each raw job with the
site slug it came from, and normalize() derives a display name from that
slug (e.g. "15five" -> "15Five"; verified this reproduces the real
stylization for every configured company).

`workplaceType` is a genuine field ("remote", "hybrid", "onsite", or
"unspecified" per the docs) confirmed via live data across several
companies, so `remote` is read directly from it rather than a keyword
heuristic.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, timestamp_to_iso_date

API_URL = "https://api.lever.co/v0/postings"

# Company site slugs to fetch. Confirmed live against the real API before
# picking this initial set - many other well-known companies (e.g.
# "netflix", "shopify", "notion") either have no open postings on Lever or
# 404 outright, having moved to a different ATS. Add a new company by
# adding its slug here; no other code changes are needed.
COMPANY_SLUGS = [
    "palantir",
    "farfetch",
    "ro",
    "outreach",
    "highspot",
    "wealthfront",
    "prosper",
    "articulate",
    "15five",
]

PAGE_SIZE = 100
REQUEST_TIMEOUT = 15


class LeverSource(BaseJobSource):
    name = "lever"

    def fetch_raw(self):
        """Fetch every configured company's job postings from the Lever Postings API."""
        jobs = []

        for slug in COMPANY_SLUGS:
            skip = 0

            while True:
                try:
                    response = requests.get(
                        f"{API_URL}/{slug}",
                        params={"mode": "json", "skip": skip, "limit": PAGE_SIZE},
                        timeout=REQUEST_TIMEOUT,
                    )
                    response.raise_for_status()
                    page_jobs = response.json()
                except requests.RequestException as exc:
                    print(f"[{self.name}] skipped company '{slug}': {exc}")
                    break

                if not page_jobs:
                    break

                # Lever's job objects don't carry a company display name,
                # so the site slug is stashed on each raw record for
                # normalize() to derive one from.
                for job in page_jobs:
                    job["_company_slug"] = slug
                jobs.extend(page_jobs)

                if len(page_jobs) < PAGE_SIZE:
                    break
                skip += PAGE_SIZE

        return jobs

    def normalize(self, raw_job):
        """Map a Lever job record onto the project's standard schema."""
        categories = raw_job.get("categories") or {}
        location = categories.get("location") or "Unknown"

        tags = dedupe_tags(
            [categories["team"]] if categories.get("team") else None,
            [categories["department"]] if categories.get("department") else None,
            [categories["commitment"]] if categories.get("commitment") else None,
        )

        created_at = raw_job.get("createdAt")
        # createdAt is Unix epoch milliseconds, not seconds.
        posted = timestamp_to_iso_date(created_at / 1000) if created_at else ""

        return {
            "title": raw_job.get("text", ""),
            "company": _company_name_from_slug(raw_job.get("_company_slug", "")),
            "location": location,
            "url": raw_job.get("hostedUrl", ""),
            "tags": tags,
            "remote": raw_job.get("workplaceType") == "remote",
            "posted": posted,
        }


def _company_name_from_slug(slug):
    """Derive a display name from a Lever site slug (e.g. "15five" -> "15Five")."""
    return slug.replace("-", " ").title()
