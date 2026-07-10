"""
PostgreSQL persistence layer for the JobBoard aggregator.

Sits alongside jobs.json rather than replacing it: jobs.py still writes
jobs.json exactly as before, and additionally calls save_run_results() here
to upsert every fetched job into PostgreSQL and print the reporting queries
from database.sql. If PostgreSQL isn't reachable (not installed, wrong
credentials, service down), jobs.py catches that and continues - the JSON
output is never blocked on the database being available.

Connection settings are read from environment variables (loaded from .env
via python-dotenv, same as sources/config.py):

    DATABASE_URL            full libpq connection string, takes priority
                             if set (e.g. postgresql://user:pass@host:port/db)
    PGHOST                  default: localhost
    PGPORT                  default: 5432
    PGDATABASE              default: jobboard
    PGUSER                  default: postgres
    PGPASSWORD              default: '' (empty)

See MIGRATION.md for how to create the database and apply the schema.
"""

import hashlib
import os
import sys

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("PGDATABASE", "jobboard")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "")

SCHEMA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.sql")

# Location text has no standard format across 46+ providers (city names,
# "Worldwide", "Time zone: CET (+/- 3 hours)", "USA or Canada only", etc.), so
# this only recognizes the common "City, Country" / bare-country-name case.
# Anything else is left NULL rather than guessed wrong.
_NON_COUNTRY_LOCATIONS = {"worldwide", "remote", "anywhere", "global", "unknown", ""}

_UPSERT_JOB_SQL = """
    INSERT INTO jobs (
        provider, title, company, location, country, url,
        remote, posted_date, tags, dedup_key, first_seen, last_seen, created_at
    )
    VALUES (
        %(provider)s, %(title)s, %(company)s, %(location)s, %(country)s, %(url)s,
        %(remote)s, %(posted_date)s, %(tags)s, %(dedup_key)s, now(), now(), now()
    )
    ON CONFLICT (dedup_key) DO UPDATE SET
        provider    = EXCLUDED.provider,
        title       = EXCLUDED.title,
        company     = EXCLUDED.company,
        location    = EXCLUDED.location,
        country     = EXCLUDED.country,
        url         = EXCLUDED.url,
        remote      = EXCLUDED.remote,
        posted_date = EXCLUDED.posted_date,
        tags        = EXCLUDED.tags,
        last_seen   = now()
    RETURNING (xmax = 0) AS inserted
"""

_INSERT_RUN_SQL = """
    INSERT INTO provider_runs (
        provider, run_time, jobs_fetched, jobs_inserted, jobs_updated, duplicates, duration
    )
    VALUES (%(provider)s, %(run_time)s, %(jobs_fetched)s, %(jobs_inserted)s,
            %(jobs_updated)s, %(duplicates)s, %(duration)s)
"""


def get_connection():
    """Open a new connection to the JobBoard PostgreSQL database."""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return psycopg2.connect(
        host=PGHOST, port=PGPORT, dbname=PGDATABASE, user=PGUSER, password=PGPASSWORD
    )


def init_schema(conn):
    """Apply database.sql (idempotent - safe to run on every startup)."""
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()


def guess_country(location):
    """Best-effort guess at a country from a free-text location string (see module docstring)."""
    if not location:
        return None
    tail = location.split(",")[-1].strip()
    if not tail or tail.lower() in _NON_COUNTRY_LOCATIONS:
        return None
    if any(ch.isdigit() for ch in tail):
        return None
    return tail


def dedup_key_for(job):
    """A stable dedup key for a normalized job: its URL, or a hash of its identifying fields."""
    url = (job.get("url") or "").strip()
    if url:
        return url
    raw = "|".join([job.get("title") or "", job.get("company") or "", job.get("location") or ""])
    return "hash:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def save_jobs(conn, provider, jobs):
    """
    Upsert one provider's normalized jobs into the jobs table.

    Returns (inserted, updated, duplicates) counts:
      - inserted: brand new dedup_key, not previously stored
      - updated: dedup_key already existed (from this or an earlier run);
        last_seen and any changed fields are refreshed
      - duplicates: the same dedup_key appeared more than once within this
        provider's own fetch results in this run (only the first is written)
    """
    inserted = updated = duplicates = 0
    seen_keys = set()

    with conn.cursor() as cur:
        for job in jobs:
            key = dedup_key_for(job)
            if key in seen_keys:
                duplicates += 1
                continue
            seen_keys.add(key)

            location = job.get("location") or ""
            cur.execute(
                _UPSERT_JOB_SQL,
                {
                    "provider": provider,
                    "title": job.get("title") or "",
                    "company": job.get("company") or "",
                    "location": location,
                    "country": guess_country(location),
                    "url": job.get("url") or "",
                    "remote": bool(job.get("remote")),
                    "posted_date": job.get("posted") or None,
                    "tags": job.get("tags") or [],
                    "dedup_key": key,
                },
            )
            was_inserted = cur.fetchone()[0]
            if was_inserted:
                inserted += 1
            else:
                updated += 1

    return inserted, updated, duplicates


def save_run(conn, provider, run_time, jobs_fetched, jobs_inserted, jobs_updated, duplicates, duration):
    """Record one provider's run statistics in provider_runs."""
    with conn.cursor() as cur:
        cur.execute(
            _INSERT_RUN_SQL,
            {
                "provider": provider,
                "run_time": run_time,
                "jobs_fetched": jobs_fetched,
                "jobs_inserted": jobs_inserted,
                "jobs_updated": jobs_updated,
                "duplicates": duplicates,
                "duration": duration,
            },
        )


# One (label, SQL) pair per report requested for every run - see database.sql
# for the standalone, manually-runnable version of each of these.
REPORT_QUERIES = [
    ("Total jobs stored", "SELECT COUNT(*) AS total_jobs FROM jobs"),
    (
        "Jobs by provider",
        "SELECT provider, COUNT(*) AS job_count FROM jobs GROUP BY provider ORDER BY job_count DESC",
    ),
    (
        "Jobs by country",
        "SELECT COALESCE(country, 'Unknown') AS country, COUNT(*) AS job_count "
        "FROM jobs GROUP BY country ORDER BY job_count DESC",
    ),
    (
        "Remote vs non-remote",
        "SELECT remote, COUNT(*) AS job_count FROM jobs GROUP BY remote ORDER BY remote DESC",
    ),
    (
        "Duplicates (all-time / latest run)",
        "SELECT "
        "  (SELECT COALESCE(SUM(duplicates), 0) FROM provider_runs) AS total_duplicates, "
        "  (SELECT COALESCE(SUM(duplicates), 0) FROM provider_runs "
        "     WHERE run_time = (SELECT MAX(run_time) FROM provider_runs)) AS duplicates_last_run",
    ),
    (
        "New jobs added in the latest run",
        "SELECT COUNT(*) AS new_jobs_last_run FROM jobs "
        "WHERE first_seen >= (SELECT MAX(run_time) FROM provider_runs)",
    ),
]


def _safe_print(text):
    """Print text that may contain characters this terminal's encoding can't display.

    Some job locations/company names round-trip through PostgreSQL as
    non-ASCII text (e.g. "Perú", "México"), and Windows consoles are often
    stuck on a legacy codepage (cp1252 etc.) that can't encode them -
    printing those directly raises UnicodeEncodeError. The data itself is
    unaffected either way; this only makes the terminal report robust to it.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding))


def print_reports(conn):
    """Run every report query in REPORT_QUERIES and print the results."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for label, sql in REPORT_QUERIES:
            cur.execute(sql)
            rows = cur.fetchall()
            _safe_print(f"\n-- {label} --")
            if not rows:
                _safe_print("  (no rows)")
                continue
            for row in rows:
                _safe_print("  " + ", ".join(f"{k}={v}" for k, v in row.items()))
