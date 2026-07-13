-- JobBoard PostgreSQL schema.
--
-- Run this once against a fresh database to create the tables this project
-- needs (see MIGRATION.md for the full setup walkthrough):
--
--   psql -U postgres -h localhost -p 5432 -d jobboard -f database.sql
--
-- Every statement below is idempotent (CREATE ... IF NOT EXISTS), so running
-- this file again on a database that already has the schema is a no-op.
--
-- `database.py`'s init_schema() runs this same file programmatically, so it
-- never needs to be applied by hand - it's kept here too so the schema has
-- one canonical, human-readable definition, and so it can be applied with
-- plain `psql` on a machine with no Python environment set up yet.

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

-- One row per unique job posting. "Unique" is enforced by dedup_key, not by
-- id: dedup_key is the job's URL when the source provided one, or a stable
-- sha256 hash of (provider, title, company, location) for the rare job with
-- no URL - see database.py's dedup_key_for(). Re-running jobs.py updates
-- last_seen (and any changed fields) on existing rows via ON CONFLICT rather
-- than inserting duplicates.
CREATE TABLE IF NOT EXISTS jobs (
    id                BIGSERIAL PRIMARY KEY,
    provider          TEXT NOT NULL,
    title             TEXT NOT NULL,
    company           TEXT NOT NULL DEFAULT '',
    location          TEXT NOT NULL DEFAULT '',
    country           TEXT,
    work_arrangement  TEXT,
    url               TEXT NOT NULL DEFAULT '',
    remote            BOOLEAN NOT NULL DEFAULT FALSE,
    posted_date       DATE,
    tags              TEXT[] NOT NULL DEFAULT '{}',
    dedup_key         TEXT NOT NULL UNIQUE,
    first_seen        TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Added after the table already existed in deployed databases - ADD COLUMN
-- IF NOT EXISTS makes this safe to apply alongside the CREATE TABLE above
-- regardless of whether this is a fresh database or an existing one.
-- work_arrangement is a normalized 'remote' / 'hybrid' / 'onsite' tag
-- derived from location text by normalize_countries.py, independent of
-- country (e.g. "Remote - US" is both work_arrangement='remote' and
-- country='United States') - see MIGRATION.md.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS work_arrangement TEXT;

CREATE INDEX IF NOT EXISTS idx_jobs_provider ON jobs (provider);
CREATE INDEX IF NOT EXISTS idx_jobs_country ON jobs (country);
CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs (remote);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON jobs (first_seen);
CREATE INDEX IF NOT EXISTS idx_jobs_work_arrangement ON jobs (work_arrangement);

-- One row per provider per jobs.py invocation ("run"). All providers fetched
-- in the same invocation share the same run_time (set once at the start of
-- jobs.py's main()), so "the latest run" = every row with
-- run_time = (SELECT MAX(run_time) FROM provider_runs) - see the reporting
-- queries below.
CREATE TABLE IF NOT EXISTS provider_runs (
    id              BIGSERIAL PRIMARY KEY,
    provider        TEXT NOT NULL,
    run_time        TIMESTAMPTZ NOT NULL,
    jobs_fetched    INTEGER NOT NULL DEFAULT 0,
    jobs_inserted   INTEGER NOT NULL DEFAULT 0,
    jobs_updated    INTEGER NOT NULL DEFAULT 0,
    duplicates      INTEGER NOT NULL DEFAULT 0,
    duration        NUMERIC(10, 3) NOT NULL DEFAULT 0  -- seconds
);

CREATE INDEX IF NOT EXISTS idx_provider_runs_run_time ON provider_runs (run_time);
CREATE INDEX IF NOT EXISTS idx_provider_runs_provider ON provider_runs (provider);

-- ---------------------------------------------------------------------------
-- Reporting queries
--
-- These are also run automatically (via database.print_reports()) at the end
-- of every `python jobs.py` invocation. They're included here standalone so
-- they can be run by hand with psql at any time. Each is a plain SELECT, so
-- running this whole file (e.g. via init_schema()) is always safe even after
-- the tables already exist - the SELECTs just return a result set that's
-- discarded.
-- ---------------------------------------------------------------------------

-- 1. Total jobs stored
SELECT COUNT(*) AS total_jobs FROM jobs;

-- 2. Jobs grouped by provider
SELECT provider, COUNT(*) AS job_count
FROM jobs
GROUP BY provider
ORDER BY job_count DESC;

-- 3. Jobs grouped by country (jobs with no reliably-parsed country show as 'Unknown')
SELECT COALESCE(country, 'Unknown') AS country, COUNT(*) AS job_count
FROM jobs
GROUP BY country
ORDER BY job_count DESC;

-- 4. Remote vs non-remote counts
SELECT remote, COUNT(*) AS job_count
FROM jobs
GROUP BY remote
ORDER BY remote DESC;

-- 5. Duplicate count (jobs skipped because the same URL/hash repeated within
--    a single provider's own fetch - not the same thing as an updated
--    existing row, which is tracked separately in jobs_updated)
--    - all-time, across every run:
SELECT COALESCE(SUM(duplicates), 0) AS total_duplicates FROM provider_runs;
--    - most recent run only:
SELECT COALESCE(SUM(duplicates), 0) AS duplicates_last_run
FROM provider_runs
WHERE run_time = (SELECT MAX(run_time) FROM provider_runs);

-- 6. New jobs added during the latest run (first_seen falls at/after the
--    most recent run_time recorded in provider_runs)
SELECT COUNT(*) AS new_jobs_last_run
FROM jobs
WHERE first_seen >= (SELECT MAX(run_time) FROM provider_runs);
