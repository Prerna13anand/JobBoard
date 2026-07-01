"""
Job board aggregator - Milestone 1.

Fetches job postings from every source registered in `sources/__init__.py`,
normalizes them into a single common schema, and writes the combined result
to jobs.json.

Currently wired up:
    - Arbeitnow Job Board API
    - Himalayas Jobs API
    - RemoteOK Jobs API
    - Jobicy Jobs API
    - The Muse Jobs API
    - Bundesagentur fur Arbeit Jobsuche API

Adding a new source (Greenhouse, Lever, etc.) in a later milestone only
requires creating a new module in sources/ and registering it in
sources/__init__.py - this file does not need to change.

Since multiple sources can list the same job (or the same source can, in
theory, return duplicates across pages), jobs are deduplicated by URL after
being collected - the URL is the one field guaranteed to uniquely identify
a specific job posting.

Usage:
    python jobs.py
"""

import json

from sources import SOURCES

OUTPUT_FILE = "jobs.json"


def collect_all_jobs():
    """Run every registered job source and return the combined, normalized list."""
    all_jobs = []
    for source in SOURCES:
        all_jobs.extend(source.run())
    return all_jobs


def dedupe_jobs(jobs):
    """Remove duplicate jobs, keyed by URL. The first occurrence wins."""
    seen_urls = set()
    deduped = []
    for job in jobs:
        url = job.get("url")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        deduped.append(job)
    return deduped


def save_jobs(jobs, output_file=OUTPUT_FILE):
    """Write the normalized job list to a JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


def main():
    jobs = collect_all_jobs()
    deduped_jobs = dedupe_jobs(jobs)
    dropped = len(jobs) - len(deduped_jobs)
    if dropped:
        print(f"Removed {dropped} duplicate job(s)")

    save_jobs(deduped_jobs)
    print(f"Saved {len(deduped_jobs)} total jobs to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
