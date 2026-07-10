"""
Job board aggregator - Milestone 1.

Fetches job postings from every source registered in `sources/__init__.py`,
normalizes them into a single common schema, and writes the combined result
to jobs.json. It also upserts every fetched job into PostgreSQL (see
database.py/database.sql/MIGRATION.md) - jobs.json remains the frontend's
data source and is always written regardless of whether the database save
succeeds, so a missing/unreachable PostgreSQL install never breaks a run.

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
import time
from datetime import datetime, timezone

import database
from sources import SOURCES

OUTPUT_FILE = "jobs.json"


def collect_all_jobs():
    """
    Run every registered job source.

    Returns (all_jobs, provider_runs): the combined, normalized job list (for
    jobs.json, exactly as before), plus a list of (provider_name, jobs,
    duration_seconds) - one entry per source - used to populate PostgreSQL
    per-provider without changing what gets written to jobs.json.
    """
    all_jobs = []
    provider_runs = []
    for source in SOURCES:
        start = time.monotonic()
        jobs = source.run()
        duration = time.monotonic() - start
        provider_runs.append((source.name, jobs, duration))
        all_jobs.extend(jobs)
    return all_jobs, provider_runs


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


def save_to_database(provider_runs, run_time):
    """
    Upsert every provider's jobs into PostgreSQL and record run stats.

    Any failure here (PostgreSQL not installed, service not running, bad
    credentials, etc.) is caught and logged rather than raised, so a missing
    database never prevents jobs.json from being produced.
    """
    try:
        conn = database.get_connection()
    except Exception as exc:
        print(f"[database] skipped - could not connect to PostgreSQL: {exc}")
        return

    try:
        database.init_schema(conn)
        for provider, jobs, duration in provider_runs:
            inserted, updated, duplicates = database.save_jobs(conn, provider, jobs)
            database.save_run(
                conn, provider, run_time, len(jobs), inserted, updated, duplicates, duration
            )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        conn.close()
        print(f"[database] failed to save jobs: {exc}")
        return

    try:
        database.print_reports(conn)
    except Exception as exc:
        print(f"[database] jobs were saved, but the report queries failed: {exc}")
    finally:
        conn.close()


def main():
    run_time = datetime.now(timezone.utc)

    all_jobs, provider_runs = collect_all_jobs()
    deduped_jobs = dedupe_jobs(all_jobs)
    dropped = len(all_jobs) - len(deduped_jobs)
    if dropped:
        print(f"Removed {dropped} duplicate job(s)")

    save_jobs(deduped_jobs)
    print(f"Saved {len(deduped_jobs)} total jobs to {OUTPUT_FILE}")

    save_to_database(provider_runs, run_time)


if __name__ == "__main__":
    main()
