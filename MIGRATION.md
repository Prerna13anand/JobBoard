# PostgreSQL Migration Guide

This project stores every fetched job in PostgreSQL in addition to writing
`jobs.json` (the frontend keeps reading `jobs.json` - the database is an
additional, independent store used for history/reporting across runs).

The database is entirely optional: if PostgreSQL isn't installed or isn't
reachable, `python jobs.py` still fetches every provider and writes
`jobs.json` exactly as before - the database step is skipped with a printed
warning instead of failing the run.

## 1. Install PostgreSQL

If you don't already have PostgreSQL installed locally, install it from
https://www.postgresql.org/download/ (or via your OS package manager) and
make sure the server is running. Note the port it listens on - the default
is `5432`, but if you have multiple PostgreSQL versions installed side by
side, one of them may have been configured to listen on a different port
(e.g. `5433`) to avoid a conflict. You can check with:

```bash
psql -U postgres -h localhost -p 5432 -c "SELECT version();"
```

If that fails with "connection refused", try `-p 5433`.

## 2. Create the database

```bash
createdb -U postgres -h localhost -p 5432 jobboard
```

(Or, from `psql`: `CREATE DATABASE jobboard;`)

## 3. Apply the schema

Two equivalent ways to do this:

**Option A - psql directly:**

```bash
psql -U postgres -h localhost -p 5432 -d jobboard -f database.sql
```

**Option B - let jobs.py do it automatically:**

`jobs.py` calls `database.init_schema()` on every run, which applies
`database.sql` itself (every statement is `CREATE TABLE IF NOT EXISTS`, so
this is always safe to re-run). You only need step 3 if you want the tables
to exist before the first run, e.g. to inspect the empty schema.

## 4. Configure credentials

Copy `.env.example` to `.env` if you haven't already:

```bash
cp .env.example .env
```

Then fill in the PostgreSQL section, either as one connection string:

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/jobboard
```

or as individual variables:

```
PGHOST=localhost
PGPORT=5432
PGDATABASE=jobboard
PGUSER=postgres
PGPASSWORD=yourpassword
```

`DATABASE_URL` takes priority if both are set. If neither is set at all,
`database.py` falls back to `localhost:5432/jobboard` with user `postgres`
and an empty password.

## 5. Install the Python driver

```bash
pip install -r requirements.txt
```

This installs `psycopg2-binary` alongside the project's existing
dependencies.

## 6. Run it

```bash
python jobs.py
```

This fetches every provider, writes `jobs.json` as before, then upserts
every job into PostgreSQL and prints the six reporting queries (total jobs,
jobs by provider, jobs by country, remote vs non-remote, duplicate counts,
and new jobs added in this run). The same reports can be re-run any time by
hand with `psql -f database.sql`, or individually - see the comments in
`database.sql` for each labeled query.

## Re-running / updating the schema later

`database.sql` is idempotent, so if it's ever extended with new tables or
columns, re-applying it (via `psql -f database.sql` or just running
`jobs.py` again) picks up the change without needing a separate migration
tool - there's no data to lose since every statement only adds structure
that doesn't already exist.
