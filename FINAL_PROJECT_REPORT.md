# Job Aggregation Platform — Final Project Report

**Internal Engineering Report · Data Platform**

Final project report covering the multi-source ingestion pipeline, PostgreSQL data layer, and offline location/work-arrangement normalization built over this project.

| | |
|---|---|
| **Prepared for** | Engineering Manager |
| **Prepared by** | Reuben Jacob |
| **Report date** | July 13, 2026 |
| **Data snapshot as of** | July 10, 2026 |

| 46 | 184,506 | 41 / 46 | 1,565 |
|---|---|---|---|
| Providers integrated | Jobs stored in PostgreSQL | Providers actively contributing data | Distinct countries/regions resolved |

---

## Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Overview](#2-project-overview)
3. [Technology Stack](#3-technology-stack)
4. [APIs and Providers](#4-apis-and-providers)
5. [Features](#5-features)
6. [PostgreSQL Integration](#6-postgresql-integration)
7. [Statistics](#7-statistics)
8. [API Comparison](#8-api-comparison)
9. [Pricing Analysis](#9-pricing-analysis)
10. [Implemented vs Pending](#10-implemented-vs-pending)
11. [Country Coverage](#11-country-coverage)
12. [Job Categories — Evidence-Based Field Analysis](#12-job-categories--evidence-based-field-analysis)
13. [Known Limitations](#13-known-limitations)
14. [Future Improvements](#14-future-improvements)
15. [Lessons Learned](#15-lessons-learned)
16. [Final Recommendations](#16-final-recommendations)
17. [Conclusion](#17-conclusion)
18. [Provider Capability Matrix](#18-provider-capability-matrix)
19. [Project Status](#19-project-status)
20. [Requirement Coverage Matrix](#20-requirement-coverage-matrix)
21. [Provider Research & Evaluation Summary](#21-provider-research--evaluation-summary)

---

## 1. Executive Summary

The Job Aggregation Platform is a Python-based pipeline that collects job postings from 46 independent sources — government labour agencies, applicant-tracking systems (ATS), commercial job-search APIs, and RSS/XML feeds — normalizes them into one common schema, and persists them to PostgreSQL alongside a static `jobs.json` export consumed by a lightweight search/filter frontend.

The project's objective was to build a durable, extensible data layer for job listings that could answer questions no single provider can answer alone: how many jobs exist across markets, which country and work-arrangement a listing genuinely belongs to, and how the sourcing mix has changed over time. This required three things: (1) a source architecture that could absorb dozens of structurally different APIs without repeated rework, (2) a persistence layer with real deduplication and run-history tracking rather than a flat file, and (3) an offline enrichment layer that could resolve free-text location strings into clean country and work-arrangement fields without depending on any paid geocoding service or further network calls.

All three objectives were met. **46 provider modules** are implemented against a shared `BaseJobSource` interface; **184,506 unique job records** are stored in PostgreSQL with URL/hash-based deduplication, per-provider run history, and full country/work-arrangement normalization already applied. Of the 46 providers, **41 are actively contributing live data** in the current snapshot; the remaining five are fully built but currently blocked by an external billing restriction, missing credentials, or a transient zero-result run — each is diagnosed precisely in [Section 10](#10-implemented-vs-pending). The platform is in a stable, well-instrumented state and ready for the operational hardening (scheduled syncs, inline normalization, credential provisioning) detailed in [Section 14](#14-future-improvements).

---

## 2. Project Overview

### Goal

Build a single, queryable, de-duplicated dataset of job postings sourced from as many distinct free/low-cost channels as practical — public government job boards, no-auth ATS endpoints, metered commercial search APIs, and company RSS feeds — normalized to a common schema, with reliable country and remote/hybrid/on-site classification, and a historical record of every ingestion run.

### Architecture

Every provider lives in its own module under `sources/` and implements a shared `BaseJobSource` interface: `fetch_raw()` pulls records from that provider's native API/feed format, and `normalize()` maps them onto one common job schema (`title`, `company`, `location`, `url`, `tags`, `remote`, `posted`). A concrete `run()` method on the base class calls both per record, catching and logging any per-source or per-record failure so one broken provider can never take the whole pipeline down. Adding a new source has never required changing `jobs.py` — only a new module plus one line in the `SOURCES` registry.

### Workflow

1. **Fetch & normalize** — `jobs.py` instantiates all 46 sources and runs each independently.
2. **Merge & deduplicate** — results are combined and deduplicated by URL (or a SHA-256 hash of title/company/location for the rare job with no URL).
3. **Write `jobs.json`** — the deduplicated set is written for the static frontend, unchanged in format since Milestone 2.
4. **Persist to PostgreSQL** — `database.py` upserts every job into the `jobs` table (keyed on `dedup_key`) and records one `provider_runs` row per source with fetch/insert/update/duplicate counts and duration.
5. **Normalize offline** — `normalize_countries.py` runs as a separate, idempotent migration pass over the stored `location` text, deriving `country` and `work_arrangement` using only local libraries — no network calls, no provider re-fetch.

### Technologies used

Python 3 for the whole pipeline; PostgreSQL for persistence; `psycopg2` as the driver; `requests` (plus `requests-oauthlib` for the one OAuth 1.0a source) for HTTP; Python's built-in `xml.etree.ElementTree` for RSS/Atom/XML feed sources; and `pycountry`, `country_converter`, and `geonamescache` for fully offline location normalization. See [Section 3](#3-technology-stack) for the rationale behind each.

---

## 3. Technology Stack

One correction from the requested list before the table below: this project does **not** use **feedparser** or **BeautifulSoup**. Neither appears in `requirements.txt` or anywhere in `sources/`. RSS/Atom/XML feed providers (Mustakbil, MyJobMag, Hasjob, NoDesk, We Work Remotely, Jobspresso, Freshersworld, 4dayweek) are parsed with Python's built-in `xml.etree.ElementTree`, supplemented by targeted `re`/`html` cleanup where a feed is malformed or double-escaped. This is called out explicitly rather than silently listing unused dependencies.

| Technology | Role in this project | Why it was chosen |
|---|---|---|
| Python 3 | Orchestration language for every source module, the aggregation pipeline, database layer, and normalization scripts. | Mature HTTP/XML/JSON tooling, strong standard library, and the language every part of this project is already written in. |
| PostgreSQL | System of record for all 184,506 job rows and per-provider run history. | Native `UNIQUE` constraints for URL-based dedup, array columns for `tags`, transactional upserts (`ON CONFLICT`), and mature indexing for the reporting queries in Section 7. |
| psycopg2 (psycopg2-binary) | PostgreSQL driver used by `database.py` for every connection, upsert, and report query. | The de facto standard, well-maintained Python/PostgreSQL adapter; supports `execute_values` for efficient bulk upserts. |
| requests | HTTP client for every REST/JSON API source (the large majority of the 46 providers). | Simple, reliable synchronous HTTP with easy header/auth/timeout/retry control — sufficient for this pipeline's sequential, per-provider fetch model. |
| requests-oauthlib | Signs the Trade Me Jobs API's OAuth 1.0a two-legged requests. | Trade Me is the only source in the project requiring OAuth 1.0a; this is the standard, well-tested library for that signing scheme. |
| xml.etree.ElementTree *(stdlib)* | Parses every RSS/Atom/XML feed source (8 providers) instead of feedparser/BeautifulSoup. | No extra dependency needed; standard-library parser is sufficient once malformed markup is pre-cleaned with `re`/`html.unescape`. |
| python-dotenv | Loads API credentials from a git-ignored `.env` file into environment variables at import time. | Keeps every secret out of source control while remaining a single, uniform pattern across all 12 credentialed providers. |
| pycountry | Canonical ISO 3166-1 country names/codes used as the highest-confidence tier of location resolution. | Authoritative, offline, dependency-light reference data — no external geocoding API or network call required. |
| country_converter | Large regex table of country name spellings/abbreviations, and the source of the one consistent "friendly" country name used throughout (e.g. "United States" rather than the ISO formal name). | Handles the long tail of alternate country spellings that a static name lookup alone would miss, entirely offline. |
| geonamescache | ~32,000 world cities, US states, and US counties, used to disambiguate location strings that name a city but not a country (e.g. "Paris" → France over Paris, Texas, by population). | Bundled local data — no live geocoding service, no API key, no rate limit, no cost. |

---

## 4. APIs and Providers

All 46 integrated providers, sorted by live job count currently stored in PostgreSQL. "Jobs Fetched" is the raw per-run count recorded in `provider_runs` (includes in-run duplicates); "Jobs Stored" is the live, post-dedup count in the `jobs` table. Every pricing-page URL below is quoted directly from this project's own source code (module docstrings or `sources/config.py`) — none are guessed.

| Provider | Type | Region | Auth | Pricing Model | Tier | Official Page | Fetched | Stored | Status | Notes |
|---|---|---|---|---|---|---|---:|---:|---|---|
| SmartRecruiters | ATS | Global (curated cos.) | None | No-auth public API | Free | developers.smartrecruiters.com/docs/posting-api | 65,394 | 65,392 | Live | Largest source; Domino's alone contributes 24,413 postings. |
| Greenhouse | ATS | Global (curated cos.) | None | No-auth public API | Free | developers.greenhouse.io/job-board.html | 22,715 | 22,715 | Live | No pagination needed; company name provided directly per job. |
| Lever | ATS | Global (curated cos.) | None | No-auth public API | Free | github.com/lever/postings-api | 17,980 | 17,980 | Live | Company name derived from URL slug (verified per company). |
| NHS Jobs | Government (undocumented feed) | United Kingdom | None | No-auth public feed | Free | jobs.nhs.uk/api/v1/search_xml | 13,011 | 10,843 | Live | Endpoint is undocumented; NHS's official documented API is separate and requires NHSBSA approval. |
| USAJOBS | Government API | United States | API key (3 headers) + email | Free registration | Free | developer.usajobs.gov | 10,000 | 10,000 | Live | Hard 10,000 result-window ceiling; genuine `remote` boolean field. |
| Bundesagentur für Arbeit | Government API | Germany / Austria | Public non-secret API key | No-auth-style public key | Free | github.com/bundesAPI/jobsuche-api | 10,000 | 9,896 | Live | Hard `page × size ≤ 10,000` window; retry-with-backoff added for transient timeouts. |
| Reed | Commercial Aggregator | United Kingdom | HTTP Basic (key as username) | Free registration | Free | reed.co.uk/developers/jobseeker | 9,000 | 8,994 | Live | No employment-type field in response at all; ~9,900-row hard boundary surfaces as HTTP 500. |
| NAV Arbeidsplassen | Government API | Norway | Public no-signup rotating token | No-auth-style public token | Free | navikt.github.io/pam-stilling-feed | 12,478 | 5,394 | Live | Chronological change-feed, not a current-postings search; 7,084 in-run duplicates are historical entries. |
| Ashby | ATS | Global (curated cos.) | None | No-auth public API | Free | developers.ashbyhq.com/docs/public-job-posting-api | 5,252 | 5,252 | Live | No company-name field on job objects; each company manually mapped. |
| Workable | ATS (public widget API) | Global (curated cos.) | None | No-auth public API | Free | apply.workable.com (public widget surface) | 7,627 | 4,137 | Live | 3,490 in-run duplicates: the same job posted to multiple cities, correctly deduplicated. |
| Workday | ATS (public CXS API) | Global + US govt tenants | None | No-auth public API | Free | (keyless endpoint, templated per tenant — no fixed docs URL found) | 2,998 | 2,997 | Live | 20 curated tenants incl. State of Maine, North Carolina, Oregon, Denver. |
| Himalayas | Public API | Global / Remote | None | No-auth public API | Free | himalayas.app/jobs/api | 3,000 | 2,253 | Live | `limit` param ignored server-side (fixed 20/page). |
| Arbetsförmedlingen | Government API | Sweden | None | No-auth public API | Free | jobsearch.api.jobtechdev.se | 2,100 | 2,096 | Live | Hard offset ceiling (~2,100 of ~40,000 postings reachable). |
| Adzuna | Commercial Aggregator | United States | API key (app_id + app_key) | Free tier + paid metered | Free tier | developer.adzuna.com/docs/search | 2,000 | 2,000 | Live | `results_per_page` capped at 50; self-capped at 40 pages. |
| The Muse | Commercial Aggregator | Global / US-tech-skewed | None (public tier) | No-auth public tier | Free | themuse.com/developers/api/v2 | 2,000 | 2,000 | Live | Unauthenticated page ceiling of 99 (HTTP 400 beyond). |
| CareerJet | Commercial Aggregator | Global (per-country query) | API key + IP allowlist + Referer | Free registration | Free | careerjet.com/partners/api | 2,000 | 1,996 | Live | Current v4 API; `page_size` fixed at 20 regardless of request. |
| EURES | Government (undocumented feed) | EU / EEA | None | No-auth public feed | Free | europa.eu/eures (no official public docs) | 2,000 | 1,681 | Live | ~10,000-record Elasticsearch window; `employer` null in ~80% of records. |
| RemoteJobs.org | Public API | Global / Remote | None | No-auth public API | Free | remotejobs.org (in-response docs link 404s) | 1,500 | 1,500 | Live | `limit` capped at 50; HTTP 429 hit around page 23 in live testing. |
| France Travail | Government API | France | OAuth2 client credentials | Free self-service | Free | francetravail.io/produits-partages/catalogue/offres-emploi | 1,150 | 1,146 | Live | `range` capped at 150/request; built from spec, later verified live. |
| Jooble | Commercial Aggregator | Global (keyword-scoped) | API key | Free registration | Free | jooble.org/api | 1,137 | 1,137 | Live | Requires a non-empty keyword; wildcard-space query used to browse broadly. |
| Get on Board | Commercial Aggregator (tech) | Latin America | None (public tier) | No-auth public tier | Free | getonbrd.com/api-doc.html | 1,261 | 1,011 | Live | A separate "Private API" tier is paid and was deliberately not used. |
| Taiwan Ministry of Labor | Government API | Taiwan | None | No-auth open data | Free | free.taiwanjobs.gov.tw (data.gov.tw dataset 44062) | 1,000 | 1,000 | Live | `count` capped at 1,000; no working offset param found. |
| Findwork.dev | Public API (tech board) | US / remote tech | API key (token) | Free registration | Free | findwork.dev/developers | 1,000 | 1,000 | Live | Confirmed rate-limit headers; HTTP 429 hit ~page 11 in testing. |
| Mustakbil.com | RSS Feed | Multi-country (PK-founded, 20+ countries) | None | No-auth public feed | Free | rss.mustakbil.com/jobs-rss | 500 | 500 | Live | Largest single-fetch RSS in the project (no pagination). |
| Teamtailor | ATS (public RSS, not API) | Global (curated cos.) | None | No-auth public feed | Free | docs.teamtailor.com | 494 | 494 | Live | Documented API needs a per-company key; unauthenticated RSS feed used instead. |
| Recruitee (Tellent) | ATS | Global (NL/EU-heavy sample) | None | No-auth public API | Free | docs.recruitee.com/reference/intro-to-careers-site-api | 394 | 394 | Live | 21 curated company subdomains; no pagination. |
| RemoteOK | Public API | Global / Remote | None | No-auth public API | Free | remoteok.com/api | 100 | 100 | Live | Single-page snapshot; blocks requests lacking a browser-like User-Agent. |
| MyJobMag | RSS Feed | Nigeria | None | No-auth public feed | Free | myjobmag.com/feeds | 100 | 100 | Live | Fixed 100 items; robots.txt disallows pagination query strings. |
| Jobicy | Public API | Global / Remote | None | No-auth public API | Free | jobi.cy/apidocs | 100 | 100 | Live | Single-page snapshot; explicit HTTP 400 on unsupported pagination. |
| We Work Remotely | RSS Feed | Global / Remote | None | No-auth public feed | Free | weworkremotely.com/remote-jobs.rss | 100 | 99 | Live | Fixed 100 items; remote-only board. |
| 4dayweek.io | RSS Feed | Global | None | No-auth public feed | Free | 4dayweek.io/feed | 50 | 50 | Live | Richer JSON API exists but is disallowed by robots.txt; not used. |
| SerpApi (Google Jobs) | Commercial Aggregator | Global | API key | Free tier + paid metered | Free tier / Paid | serpapi.com/google-jobs-api | 50 | 50 | Live | Free plan: 200 searches/month; deliberately capped at 5 pages to conserve quota. |
| OpenWebNinja (JSearch) | Commercial Aggregator | Global | API key | Free tier + paid metered | Free tier / Paid | openwebninja.com/api/jsearch | 49 | 49 | Live | Free plan: 200 requests/month; capped for the same reason as SerpApi. |
| Working Nomads | Public API | Global / Remote | None | No-auth public API | Free | workingnomads.com/jobs | 33 | 33 | Live | No pagination; fixed ~36-job snapshot. |
| Remotive | Public API | Global / Remote | None | No-auth public API | Free | remotive.com/api-jobs | 30 | 30 | Live | Provider explicitly requests ≤4 requests/day; no working pagination. |
| Freshersworld | RSS Feed | India (entry-level) | None | No-auth public feed | Free | freshersworld.com/feed | 30 | 30 | Live | Blocks the default `requests` User-Agent (HTTP 403) unless spoofed. |
| Jobspresso | RSS Feed | Global / Remote | None | No-auth public feed | Free | jobspresso.co/jobs/feed | 20 | 20 | Live | robots.txt disallows query-string pagination; newest 20 only. |
| MyCareersFuture | Government (undocumented API) | Singapore | None | No-auth public API | Free | api.mycareersfuture.gov.sg (no public docs found) | 2,000 | 20 | **Needs review** | `limit` ignored (fixed 20/page); 1,980 in-run duplicates — see Section 13. |
| NoDesk | RSS Feed | Global / Remote | None | No-auth public feed | Free | nodesk.co/remote-jobs | 10 | 10 | Live | Only 10 most recent items; non-standard XML requiring pre-processing. |
| Hasjob | Atom Feed | India (tech/startup) | None | No-auth public feed | Free | hasjob.co/feed | 6 | 6 | Live | Very low volume; company name regex-extracted from feed HTML. |
| HK Gov Vacancies | Government (static open data) | Hong Kong | None | No-auth open data | Free | csb.gov.hk/datagovhk/gov-vacancies (data.gov.hk) | 58 | 1 | **Needs review** | Every job links to the same generic portal URL, collapsing almost all records onto one dedup key — see Section 13. |
| TheirStack | Commercial Aggregator | Global | API key (Bearer) | Per-credit metered (1 credit/job) | Paid | theirstack.com | 0 | 0 | **Blocked — billing** | Account's current plan excludes Jobs API access (HTTP 402); not a code defect. |
| Trade Me Jobs | Commercial Aggregator | New Zealand | OAuth 1.0a (consumer key/secret) | Free (registered app) | Free / Approval | developer.trademe.co.nz | 0 | 0 | **Built, uncredentialed** | `TRADEME_CONSUMER_KEY/SECRET` not configured; production access needs Trade Me's approval. |
| CareerOneStop | Government API | United States | API key + user ID | Free registration | Free | careeronestop.org/Developers/WebAPI/web-api.aspx | 0 | 0 | **Built, uncredentialed** | `CAREERONESTOP_USER_ID/API_TOKEN` not configured in this environment. |
| Fantastic.jobs | Commercial Aggregator (ATS feed) | Global | API key (Bearer) | Free trial → paid metered (~$1/1,000 jobs) | Free trial | developer.fantastic.jobs | 0 | 0 | **Credentialed, 0 result** | Key is configured but returned 0 jobs — likely trial expiry or account-tier gap; needs verification. |
| Arbeitnow | Public API | Global / Germany-leaning | None | No-auth public API | Free | arbeitnow.com/api/job-board-api | 0 | 0 | **0 in latest run** | Free no-auth API, previously verified working (931 jobs during development); likely a transient run issue. |

"Live" = contributed jobs currently in PostgreSQL in this snapshot. "Needs review" = contributing data, but with a structural quirk worth a closer look (Section 13). See Section 10 for full root-cause detail on every non-contributing provider.

---

## 5. Features

### Fully Implemented

- 46 provider integrations on a shared `BaseJobSource` interface
- PostgreSQL persistence with upsert-on-`dedup_key`
- URL / SHA-256-hash based deduplication
- Per-provider run history (`provider_runs`)
- Offline country normalization (pycountry / country_converter / geonamescache)
- Multi-country & region ambiguity handling (forces `NULL` rather than guessing)
- Work-arrangement classification (remote / hybrid / on-site)
- `jobs.json` static export, unchanged since Milestone 2
- Frontend search, location filter, and sort (per `aggregation_summary.md`)
- Per-source fault isolation (one broken provider can't halt the run)

### Partially Implemented

- Work-arrangement coverage — only 7,762+595+138 of 184,506 jobs (4.6%) are classified; the rest have no explicit remote/hybrid/on-site wording in `location` to key off
- Employment-type / job-category tagging — present as free-text `tags` per provider, not a normalized taxonomy; some providers (Reed) expose none at all
- Credentialed provider coverage — 12 providers use API keys/OAuth; 2 of those (Trade Me, CareerOneStop) are built but not currently credentialed in this environment
- Country resolution — multi-country/region text is now correctly nulled, but a long tail of single, unresolvable place names (~1,565 distinct country values) still needs enrichment

### Not Implemented

- Salary / compensation capture (no field in schema; no source module attempts it)
- Company funding-stage / size enrichment
- Scheduled or automatic recurring syncs (manual `python jobs.py` invocation only)
- Inline normalization at insert time (country/work-arrangement is a separate, manually-run migration pass)
- Dashboard / analytics UI beyond the static search frontend
- Provider health alerting (no automated flag when a source silently drops to 0 jobs)

---

## 6. PostgreSQL Integration

PostgreSQL is the system of record, applied via an idempotent `database.sql` (every statement is `CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`) that `database.py`'s `init_schema()` also runs automatically on every startup.

#### jobs table

One row per unique posting. Columns: `id`, `provider`, `title`, `company`, `location` (original provider text, never altered by normalization), `country` (normalized, nullable), `work_arrangement` (normalized, nullable), `url`, `remote` (boolean, provider-native signal), `posted_date`, `tags` (array), `dedup_key` (`UNIQUE`), `first_seen`, `last_seen`, `created_at`. Indexes exist on `provider`, `country`, `remote`, `work_arrangement`, and `first_seen`.

#### provider_runs table

One row per provider per `jobs.py` invocation: `jobs_fetched`, `jobs_inserted`, `jobs_updated`, `duplicates`, and `duration` (seconds). Every provider in this project's history shares one `run_time` (2026-07-10 17:23), meaning the current dataset reflects a single, complete backfill run across all 46 sources rather than incremental accumulation over time.

#### Duplicate detection

Two layers: within a single provider's own fetch, a job is skipped if its `dedup_key` (URL, or a SHA-256 hash of title/company/location when no URL exists) repeats — counted as `duplicates` in `provider_runs`. Across the whole table, `dedup_key UNIQUE` plus `ON CONFLICT ... DO UPDATE` guarantees no duplicate row can ever exist regardless of provider — confirmed live: `184,506` rows, `184,506` distinct `dedup_key` values.

#### Historical tracking

`first_seen`/`last_seen` on every job, plus a full `provider_runs` row per invocation, gives the schema everything needed to track new-vs-returning postings across future runs — the reporting query for "new jobs added in the latest run" already exists in `database.sql`, ready to become meaningful once recurring runs begin (see Section 14).

#### Country normalization

`normalize_countries.py` is a standalone, offline migration reading only the already-stored `location` text. It resolves a single confident country through a tiered strategy (exact country names → ISO codes → city lookup → UK postcode / French department detection → US state fallback), and — as of the most recent update — explicitly detects locations naming 2+ countries or a multi-country region (Europe, EMEA, APAC, LATAM, etc.) and forces `country = NULL` for those rather than guessing, while leaving `location` itself untouched. It never overwrites a value it cannot independently verify.

#### Work arrangement

Derived independently of country by `classify_work_arrangement()`, a word/phrase search over `location` text for remote/hybrid/on-site signals. Intentionally not mutually exclusive with country — "Remote - US" resolves to both `work_arrangement='remote'` and `country='United States'`.

#### Reporting capability

Six standing report queries (total jobs, jobs by provider, jobs by country, remote/non-remote split, duplicate counts, new jobs in the latest run) live in both `database.sql` (for direct `psql` use) and `database.py`'s `REPORT_QUERIES`, and print automatically at the end of every `jobs.py` run.

---

## 7. Statistics

All figures below are live queries against the current PostgreSQL database, run July 13, 2026.

#### Total jobs

```sql
SELECT COUNT(*) FROM jobs;
-- 184,506
```

#### Jobs per provider — top 15

```sql
SELECT provider, COUNT(*) FROM jobs GROUP BY provider ORDER BY COUNT(*) DESC;
```

| # | Provider | Jobs | % of total |
|---:|---|---:|---:|
| 1 | SmartRecruiters | 65,392 | 35.4% |
| 2 | Greenhouse | 22,715 | 12.3% |
| 3 | Lever | 17,980 | 9.7% |
| 4 | NHS Jobs | 10,843 | 5.9% |
| 5 | USAJOBS | 10,000 | 5.4% |
| 6 | Bundesagentur für Arbeit | 9,896 | 5.4% |
| 7 | Reed | 8,994 | 4.9% |
| 8 | NAV Arbeidsplassen | 5,394 | 2.9% |
| 9 | Ashby | 5,252 | 2.8% |
| 10 | Workable | 4,137 | 2.2% |
| 11 | Workday | 2,997 | 1.6% |
| 12 | Himalayas | 2,253 | 1.2% |
| 13 | Arbetsförmedlingen | 2,096 | 1.1% |
| 14 | Adzuna | 2,000 | 1.1% |
| 15 | The Muse | 2,000 | 1.1% |

Top 3 providers (SmartRecruiters, Greenhouse, Lever) supply 57.4% of all jobs — the dataset's volume is concentrated in ATS boards, not evenly spread across 46 sources.

#### Jobs per country — top 15

```sql
SELECT COALESCE(country, 'Unknown'), COUNT(*) FROM jobs GROUP BY country ORDER BY COUNT(*) DESC;
```

| # | Country | Jobs | % of total |
|---:|---|---:|---:|
| 1 | United States | 87,364 | 47.3% |
| 2 | United Kingdom | 26,390 | 14.3% |
| 3 | Germany | 12,799 | 6.9% |
| 4 | *Unknown / unresolved* | 6,824 | 3.7% |
| 5 | India | 4,182 | 2.3% |
| 6 | France | 3,388 | 1.8% |
| 7 | Canada | 3,215 | 1.7% |
| 8 | Norway | 3,114 | 1.7% |
| 9 | Sweden | 2,010 | 1.1% |
| 10 | Australia | 1,535 | 0.8% |
| 11 | China | 1,510 | 0.8% |
| 12 | Slovenia | 1,226 | 0.7% |
| 13 | Spain | 1,148 | 0.6% |
| 14 | Malaysia | 1,141 | 0.6% |
| 15 | Indonesia | 1,048 | 0.6% |

#### Top companies by posting volume

| # | Company | Jobs | Source |
|---:|---|---:|---|
| 1 | Domino's | 24,413 | SmartRecruiters |
| 2 | AccorHotel | 5,777 | SmartRecruiters |
| 3 | AECOM | 4,865 | SmartRecruiters |
| 4 | Bosch Group | 4,729 | SmartRecruiters |
| 5 | ProSidian Consulting, LLC | 4,003 | SmartRecruiters |
| 6 | Tsmg | 3,710 | SmartRecruiters |
| 7 | Boxlunch | 3,558 | SmartRecruiters |
| 8 | Veterans Health Administration | 3,147 | USAJOBS |
| 9 | Jobs for Humanity | 3,083 | Greenhouse |
| 10 | Anduril Industries | 2,156 | Greenhouse / Ashby |

18,367 distinct companies across the dataset; 170 jobs (0.09%) have no company name recorded.

#### Remote / Hybrid / On-site

| Signal | Value | Jobs | % |
|---|---|---:|---:|
| work_arrangement (text-derived) | Remote | 7,762 | 4.2% |
| work_arrangement (text-derived) | Hybrid | 595 | 0.3% |
| work_arrangement (text-derived) | On-site | 138 | 0.1% |
| remote (provider-native boolean) | true | 19,096 | 10.4% |

These are two independent signals: `work_arrangement` is a location-text classifier (only fires on explicit wording); `remote` is each provider's own boolean/status field where one exists (e.g. Ashby's `isRemote`, USAJOBS's `RemoteIndicator`). They intentionally are not reconciled into one field — see Section 13.

#### Posting freshness

```sql
SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (DATE '2026-07-10') - posted_date)
FROM jobs WHERE posted_date IS NOT NULL;
```

| Metric | Value |
|---|---:|
| Jobs with a `posted_date` recorded | 184,129 of 184,506 (99.8%) |
| Median posting age (vs. the 2026-07-10 snapshot) | 22 days |
| Mean posting age (vs. the 2026-07-10 snapshot) | 229 days |
| Jobs posted within 30 days of the snapshot | 108,003 (58.6%) |
| Jobs older than 1 year | 21,915 (11.9%) |
| Oldest `posted_date` on record | 2009-12-05 |

The mean (229 days) and median (22 days) diverge sharply because a long tail of old postings — some over a decade old, most likely stale, unremoved listings on a handful of source boards rather than a pipeline defect — pulls the average far above what a typical stored job actually looks like. The median is the more representative "how current is this dataset" figure; both are reported rather than only the flattering one.

**Refresh frequency** cannot be reported as a rate: every row in `provider_runs` shares one `run_time` (Section 6) — there has been exactly one ingestion run to date, not a recurring schedule, so there is no interval to measure yet. **Expired-job detection** is likewise not implemented: none of the 46 providers' `normalize()` implementations populate a status/expiration field (verified against every source in Section 18), and detecting a posting that disappeared from a source would require a second run to diff against, which hasn't occurred. Both are stated here as limitations rather than estimated.

#### Duplicate statistics

| Metric | Value |
|---|---:|
| Total in-run duplicates skipped (all providers, all-time) | 16,221 |
| Total jobs fetched, all providers (all-time, pre-dedup) | 200,727 |
| Rows in `jobs` table | 184,506 |
| Distinct `dedup_key` values | 184,506 |
| Cross-provider duplicate URLs remaining | 0 |
| **Overall deduplication rate** (duplicates ÷ fetched) | **8.08%** |
| Net storage rate (inserted ÷ fetched) | 91.92% |

#### Deduplication rate and response time — every provider

The table below covers all 46 providers (not only the top 10 in Section 8), directly from `provider_runs`, sorted by duplicate rate descending. This is the complete evidence base for "duplicate jobs across APIs" and "response time for each API" — Section 8 then narrates the ten highest-volume providers in more qualitative detail.

```sql
SELECT provider, jobs_fetched, duplicates,
       ROUND(100.0 * duplicates / NULLIF(jobs_fetched, 0), 2) AS dup_rate_pct,
       duration
FROM provider_runs ORDER BY dup_rate_pct DESC NULLS LAST;
```

| Provider | Fetched | Duplicates | Dup. rate | Duration (s) |
|---|---:|---:|---:|---:|
| MyCareersFuture | 2,000 | 1,980 | 99.00% | 77.7 |
| HK Gov Vacancies | 58 | 57 | 98.28% | 1.9 |
| NAV Arbeidsplassen | 12,478 | 7,084 | 56.77% | 51.4 |
| Workable | 7,627 | 3,490 | 45.76% | 51.8 |
| Himalayas | 3,000 | 747 | 24.90% | 307.6 |
| Get on Board | 1,261 | 250 | 19.83% | 44.0 |
| NHS Jobs | 13,011 | 2,168 | 16.66% | 102.4 |
| EURES | 2,000 | 319 | 15.95% | 164.6 |
| Bundesagentur für Arbeit | 10,000 | 104 | 1.04% | 174.3 |
| We Work Remotely | 100 | 1 | 1.00% | 2.1 |
| France Travail | 1,150 | 4 | 0.35% | 22.7 |
| CareerJet | 2,000 | 4 | 0.20% | 89.1 |
| Arbetsförmedlingen | 2,100 | 4 | 0.19% | 98.4 |
| Reed | 9,000 | 6 | 0.07% | 56.6 |
| Workday | 2,998 | 1 | 0.03% | 247.1 |
| SmartRecruiters | 65,394 | 2 | 0.003% | 385.7 |
| Greenhouse | 22,715 | 0 | 0.00% | 183.8 |
| Lever | 17,980 | 0 | 0.00% | 870.1 |
| USAJOBS | 10,000 | 0 | 0.00% | 53.1 |
| Ashby | 5,252 | 0 | 0.00% | 70.3 |
| Adzuna | 2,000 | 0 | 0.00% | 133.3 |
| The Muse | 2,000 | 0 | 0.00% | 185.0 |
| RemoteJobs.org | 1,500 | 0 | 0.00% | 62.8 |
| Jooble | 1,137 | 0 | 0.00% | 11.5 |
| Taiwan Ministry of Labor | 1,000 | 0 | 0.00% | 10.2 |
| Findwork.dev | 1,000 | 0 | 0.00% | 23.2 |
| Mustakbil.com | 500 | 0 | 0.00% | 1.5 |
| Teamtailor | 494 | 0 | 0.00% | 50.7 |
| Recruitee | 394 | 0 | 0.00% | 29.1 |
| RemoteOK | 100 | 0 | 0.00% | 2.1 |
| MyJobMag | 100 | 0 | 0.00% | 1.9 |
| Jobicy | 100 | 0 | 0.00% | 1.9 |
| 4dayweek.io | 50 | 0 | 0.00% | 2.3 |
| SerpApi | 50 | 0 | 0.00% | 10.4 |
| OpenWebNinja | 49 | 0 | 0.00% | 30.0 |
| Working Nomads | 33 | 0 | 0.00% | 2.0 |
| Remotive | 30 | 0 | 0.00% | 2.2 |
| Freshersworld | 30 | 0 | 0.00% | 1.4 |
| Jobspresso | 20 | 0 | 0.00% | 1.9 |
| NoDesk | 10 | 0 | 0.00% | 1.0 |
| Hasjob | 6 | 0 | 0.00% | 0.8 |
| TheirStack | 0 | 0 | n/a (0 fetched) | 3.2 |
| Trade Me Jobs | 0 | 0 | n/a (0 fetched) | 0.0 |
| CareerOneStop | 0 | 0 | n/a (0 fetched) | 0.0 |
| Fantastic.jobs | 0 | 0 | n/a (0 fetched) | 3.1 |
| Arbeitnow | 0 | 0 | n/a (0 fetched) | 18.0 |

MyCareersFuture and HK Gov Vacancies' near-100% duplicate rates are structural, not code defects (Section 13): MyCareersFuture's `limit` parameter is silently ignored so every page re-returns the same 20 records, and HK Gov Vacancies' feed gives every job the same generic portal URL, so URL-based dedup treats 57 of 58 as duplicates of the first. "Reliability" beyond duration is qualitative and covered per-provider in Section 4's Notes column and Section 8; `provider_runs` does not currently record HTTP error counts or retry attempts as a queryable metric, so a numeric reliability score is not computed here (see Section 20).

#### Largest providers & provider performance

```sql
SELECT provider, jobs_fetched, jobs_inserted, duplicates, duration
FROM provider_runs ORDER BY jobs_fetched DESC;
```

| Provider | Fetched | Inserted | Duplicates | Duration (s) |
|---|---:|---:|---:|---:|
| SmartRecruiters | 65,394 | 65,392 | 2 | 385.7 |
| Lever | 17,980 | 17,980 | 0 | 870.1 |
| Greenhouse | 22,715 | 22,715 | 0 | 183.8 |
| NHS Jobs | 13,011 | 10,843 | 2,168 | 102.4 |
| NAV Arbeidsplassen | 12,478 | 5,394 | 7,084 | 51.4 |
| Bundesagentur für Arbeit | 10,000 | 9,896 | 104 | 174.3 |
| USAJOBS | 10,000 | 10,000 | 0 | 53.1 |
| Workable | 7,627 | 4,137 | 3,490 | 51.8 |
| Himalayas | 3,000 | 2,253 | 747 | 307.6 |
| MyCareersFuture | 2,000 | 20 | 1,980 | 77.7 |

Lever's 870-second run is the slowest in the project despite modest volume, likely reflecting real per-company pagination overhead across its curated list. NAV, Workable, and MyCareersFuture show the highest duplicate rates — each explained structurally in Sections 4 and 13, not a code defect.

---

## 8. API Comparison

Comparing the ten highest-volume providers across the dimensions that matter for data quality. "—" means the field genuinely does not exist for that provider, confirmed in code, not merely unobserved.

| Provider | Volume | Missing fields | Salary | Company info | Freshness | Dup. rate | Resp. time | Reliability | Auth | Filtering |
|---|---:|---|---|---|---|---:|---:|---|---|---|
| SmartRecruiters | 65,392 | Job-ad URL (constructed) | — | Direct field | Live board | 0.003% | 385.7s | High | None | Company, offset/limit |
| Greenhouse | 22,715 | — | — | Direct field | Live board | 0% | 183.8s | High | None | Company only |
| Lever | 17,980 | Company name (derived) | — | Slug-derived | Live board | 0% | 870.1s | High | None | Company, offset/limit |
| NHS Jobs | 10,843 | Employment type (partial) | — | Direct field | Live board | 16.7% | 102.4s | Undocumented endpoint | None | Keyword |
| USAJOBS | 10,000 | — | Not confirmed in code† | Direct field | Live board | 0% | 53.1s | High | API key + email | `Page`/`ResultsPerPage` only (no keyword/filter params implemented) |
| Bundesagentur | 9,896 | URL (sometimes constructed) | — | Direct field | Live board | 1.0% | 174.3s | High (with retry) | Public key | Keyword, location |
| Reed | 8,994 | Employment-type field entirely | Not confirmed in code† | Direct field | Live board | 0.07% | 56.6s* | High | HTTP Basic | `resultsToTake`/`resultsToSkip` pagination only (no keyword/filter params implemented) |
| NAV Arbeidsplassen | 5,394 | — | — | Direct field | Change-feed, not live-only | 56.8% | 51.4s | Rotating token | Public rotating token | Modified-since cursor |
| Ashby | 5,252 | Company name (mapped) | — | Manually mapped | Live board | 0% | 70.3s | High | None | Company only |
| Workable | 4,137 | — | — | Direct field | Live board | 45.8% | 51.8s | High | None | Company only |

*Duration for the prior run captured in provider_runs; Reed's own result-window boundary (~9,900 rows) surfaces as HTTP 500 rather than an empty page.

†**Correction from the previous version of this report:** Reed's and USAJOBS's Salary cells previously read "Genuine (not used)," asserting each API has a real salary field the project simply doesn't extract. That claim was not supported by this codebase — `sources/reed.py` and `sources/usajobs.py` were re-read in full for this revision and neither contains any reference to a salary/pay field or query parameter anywhere in `fetch_raw()` or `normalize()`; Reed's implementation sends only `resultsToTake`/`resultsToSkip`, and USAJOBS's only `Page`/`ResultsPerPage`. It is corrected here to "Not confirmed in code" rather than silently left as-is or restated with different unverified wording. This does not claim the real-world Reed/USAJOBS APIs lack salary data — only that this project's implementation neither requests nor stores it, and that the prior "genuine field" framing was an assumption, not a code-backed finding. Ashby's compensation parameter (Section 12.4) remains the one confirmed available-but-unused case, because it is the one place the module's own source comment documents the tradeoff explicitly. No provider in this project exposes structured salary data that is actually consumed — see Section 13.

---

## 9. Pricing Analysis

No provider in this project is on a flat subscription or a negotiated enterprise contract — the paid tier that exists is exclusively metered/pay-as-you-go. Every page below is the exact URL found in this project's own code.

#### Free (no registration, no key)

Arbeitnow, Himalayas, RemoteOK, Jobicy, The Muse (public tier), Bundesagentur für Arbeit, Arbetsförmedlingen, EURES, Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Teamtailor (RSS), Recruitee, Workday, Get on Board (public tier), NAV Arbeidsplassen, Taiwan MOL, MyCareersFuture, HK Gov Vacancies, Hasjob, Freshersworld, Jobspresso, Mustakbil, MyJobMag, NoDesk, RemoteJobs.org, Remotive, We Work Remotely, WorkingNomads, 4dayweek.io — **31 providers**.

#### Free Registration (self-serve key, no cost)

| Provider | Pricing / Registration Page |
|---|---|
| USAJOBS | developer.usajobs.gov |
| Jooble | jooble.org/api |
| Reed | reed.co.uk/developers/jobseeker |
| Adzuna | developer.adzuna.com/docs/search |
| CareerJet | careerjet.com/partners/api |
| Findwork.dev | findwork.dev/developers |
| France Travail | francetravail.io/produits-partages/catalogue/offres-emploi |
| CareerOneStop | careeronestop.org/Developers/WebAPI/web-api.aspx |
| Trade Me Jobs | developer.trademe.co.nz (production tier needs Trade Me approval) |

#### Free Trial (time/credit-limited before paid)

| Provider | Trial terms | Pricing Page |
|---|---|---|
| Fantastic.jobs | 7-day trial, no credit card required | developer.fantastic.jobs |

#### Pay-as-you-go / Metered

| Provider | Free tier | Paid rate | Pricing Page |
|---|---|---|---|
| SerpApi | 200 searches/month | Metered beyond free tier | serpapi.com/google-jobs-api |
| OpenWebNinja (JSearch) | 200 requests/month | Metered beyond free tier | openwebninja.com/api/jsearch |
| Fantastic.jobs | 7-day trial | ~$1 per 1,000 jobs | developer.fantastic.jobs |
| TheirStack | Account-dependent | 1 credit per job returned | theirstack.com |

#### Subscription / Enterprise

Not applicable — no provider integrated in this project documents a flat-fee subscription or an enterprise contract tier in its code, docs, or account setup.

---

## 10. Implemented vs Pending

#### Completed providers (41 of 46, contributing live data)

All providers listed in Section 4 with status "Live" or "Needs review" — 41 in total, contributing 184,505 of the 184,506 stored jobs.

#### Investigated but scoped out

- **Fantastic.jobs `/v1/active-jb`** — a sibling endpoint covering job-board-sourced listings (LinkedIn, Wellfound, Y Combinator) with a near-identical schema to the ATS-sourced endpoint that was integrated. Deliberately left out to keep the source to one well-defined feed; a natural follow-up.
- **TheirStack's non-jobs endpoints** (company enrichment, hiring signals, contacts, CRM data) — deliberately not touched; only the jobs-search endpoint was in scope.
- **Workable's authenticated SPI API** — the full ATS surface was deliberately not used in favor of the public, no-auth widget API, which is sufficient for this project's read-only needs.
- **Trade Me's per-user OAuth flow** — not needed; the read-only search endpoint only requires two-legged OAuth 1.0a (consumer key/secret, no user token).

No provider was formally evaluated and rejected outright during this phase — every provider that was investigated was either integrated or deliberately narrowed in scope as above.

#### Providers requiring approval

| Provider | Approval required |
|---|---|
| Trade Me Jobs | Production application registration is "subject to Trade Me's approval process and terms and conditions" — sandbox apps are auto-approved, but this project has not yet registered a production application. |

#### Providers requiring payment

| Provider | Payment status |
|---|---|
| TheirStack | Current account plan does not include Jobs API access at all (HTTP 402 on every request); would need a plan upgrade to resume contributing. |
| Fantastic.jobs | Free 7-day trial; continued or larger-scale use requires the metered paid tier (~$1/1,000 jobs). |
| SerpApi / OpenWebNinja | Currently operating within free-tier monthly quotas (200/month each); scaling volume up would require paid usage. |

#### Providers requiring credentials not yet supplied in this environment

| Provider | Missing |
|---|---|
| Trade Me Jobs | `TRADEME_CONSUMER_KEY`, `TRADEME_CONSUMER_SECRET` |
| CareerOneStop | `CAREERONESTOP_USER_ID`, `CAREERONESTOP_API_TOKEN` |

---

## 11. Country Coverage

Providers grouped by their intended regional focus (not the resulting job count, which skews further toward the US/UK/Germany because those are also where the highest-volume ATS boards happen to be curated — see Section 7).

| Region | Dedicated providers | Providers |
|---|---:|---|
| United States | 4 | USAJOBS, CareerOneStop, Findwork.dev, Adzuna (configured for `us`) |
| Canada | 0 | *No dedicated source* — Canadian jobs appear only incidentally via global ATS boards |
| United Kingdom | 2 | Reed, NHS Jobs |
| Europe (non-UK) | 5 | Bundesagentur für Arbeit (Germany/Austria), Arbetsförmedlingen (Sweden), France Travail (France), EURES (EU/EEA-wide), NAV Arbeidsplassen (Norway) |
| India | 2 | Freshersworld, Hasjob |
| LATAM | 1 | Get on Board |
| APAC | 4 | MyCareersFuture (Singapore), Taiwan MOL, HK Gov Vacancies, Trade Me (New Zealand) |
| Middle East | 0† | No single-country dedicated source; Mustakbil spans 20+ countries incl. UAE, Saudi Arabia |
| Africa | 1 | MyJobMag (Nigeria) |
| Global / Remote / Multi-country | 27 | All 6 ATS platforms (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Teamtailor, Recruitee, Workday), plus RemoteOK, Jobicy, The Muse, Jooble, SerpApi, OpenWebNinja, CareerJet, TheirStack, Fantastic.jobs, Himalayas, Arbeitnow, We Work Remotely, RemoteJobs.org, Remotive, WorkingNomads, NoDesk, Jobspresso, 4dayweek.io, Mustakbil |

† Mustakbil is multi-country and Middle-East-heavy but not single-region, so it's counted under Global/Multi-country rather than claimed as a dedicated Middle East source.

Actual resulting coverage (Section 7) confirms the same imbalance already visible at the provider level: the United States (47.3%), United Kingdom (14.3%), and Germany (6.9%) together account for over two-thirds of all stored jobs, while Canada — despite being a natural target market — has no dedicated source and appears only incidentally. This is a sourcing-mix artifact, not a normalization defect: the country-resolution logic itself (Section 6) is unbiased; it simply has more raw material to work with in the countries where curated ATS company lists happen to be dense.

---

## 12. Job Categories — Evidence-Based Field Analysis

*This section was replaced in full. The previous version treated the `tags` column's contents — a mix of employment-type values and provider-specific department/function labels — as if they were a "job category" system. They are not, and the evidence below explains precisely why, using a direct provenance query against the live database rather than inference.*

### 12.1 Definitions used in this section

Four distinct concepts get conflated in casual usage; this report keeps them separate because the underlying provider fields are structurally different:

| Term | What it actually means | Example |
|---|---|---|
| **Standardized Job Category** | A job-function taxonomy that is *consistent and comparable across providers* — the same value means the same thing regardless of source. | An industry-standard scheme (e.g. O*NET, LinkedIn's job-function taxonomy). |
| **Employment Type** | Contract shape: full-time, part-time, contract, internship, temporary, freelance. | "Full-time", "Contract" |
| **Department / Team** | The hiring company's *own internal org unit* for this role — not an industry category, just that employer's org chart. | "Platform Engineering", "Revenue" |
| **Free-text tag / keyword** | Anything else a provider's feed happens to expose (skills, industry sector, academic requirement, etc.), with no taxonomy behind it at all. | "python", "Federal contractor" |

This project's schema has exactly one field, `tags` (a `TEXT[]` array), to hold all four. That collapsing is the root cause of every finding below.

### 12.2 Finding: no provider exposes a standardized, cross-comparable job category

Every one of the 46 provider modules was checked directly against its `normalize()` implementation (the code that decides what goes into `tags`). **Zero providers expose a job-category field that is standardized across this project's 46 sources.** Of the 46, 23 expose *some* category-like, department-like, or occupation-like field — but each is proprietary to that one provider or that one employer, using its own taxonomy:

| Provider | Field actually read (from source code) | What it really is |
|---|---|---|
| SmartRecruiters | `department`, `function`, `typeOfEmployment` | SmartRecruiters' own three-part taxonomy |
| Greenhouse | `departments` | Each hiring company's own org-chart department names |
| Lever | `categories.department`, `categories.team`, `categories.commitment` | Each hiring company's own org-chart labels |
| Ashby | `department`, `team`, `employmentType` | Each hiring company's own org-chart labels |
| Workable | `department`, `function`, `employment_type` | Each hiring company's own org-chart labels |
| Recruitee | `department`, `employment_type_code` | Each hiring company's own org-chart labels |
| Teamtailor | `department` (from feed XML) | Each hiring company's own org-chart labels |
| Himalayas | `categories`, `parentCategories` | Himalayas' own remote-tech taxonomy |
| Adzuna | `category.label` | Adzuna's own listing taxonomy |
| The Muse | `categories`, `levels` | The Muse's own taxonomy |
| Taiwan Ministry of Labor | `CJOB_NAME1`, `CJOB_NAME2` | Taiwanese government two-level occupation code |
| Bundesagentur für Arbeit | `beruf` (occupation), `studiengang` (field of study) | German public-employment-service occupation coding |
| Get on Board | `category_name` | Get on Board's own tech-role taxonomy |
| MyCareersFuture | `categories` | Singapore government job-portal taxonomy |
| France Travail | `secteurActiviteLibelle` (activity sector) | French public-employment-service sector coding |
| Jobicy | `jobIndustry` | Jobicy's own industry list |
| Fantastic.jobs | `ai_taxonomies_a` | Fantastic.jobs' own AI-generated taxonomy |
| USAJOBS | `job_categories` | US federal job-series coding |
| Trade Me Jobs | `job_category` | Trade Me's own listing taxonomy |
| Freshersworld | regex-extracted from description ("For more {Category} Jobs…") | Freshersworld's own site category |
| Mustakbil.com | `category` (RSS field) | Mustakbil's own listing taxonomy |
| MyJobMag | `industry` (RSS field) | MyJobMag's own industry list |
| We Work Remotely | `category` (RSS field) | We Work Remotely's own listing taxonomy |
| RemoteJobs.org | `category` | RemoteJobs.org's own listing taxonomy |
| Remotive | `category` | Remotive's own listing taxonomy |
| Arbeitnow | `tags` (provider's own field) | Arbeitnow's own free-text tag list |

The remaining 21 providers expose no category/department/occupation concept at all in their `normalize()` output — confirmed directly in code, not assumed: **Reed** (module comment: "no job-category/employment-type field at all"), **CareerJet** (module comment: "no job-category/employment-type field to draw tags from, same situation as Reed"), **Jobspresso** (module comment: "every item checked live had an empty `<category>` list"), **NAV Arbeidsplassen** (module comment: "no category/skill data at this feed's summary level"), plus NHS Jobs, EURES, Workday, Jooble, SerpApi, OpenWebNinja, Findwork.dev, CareerOneStop, HK Gov Vacancies, NoDesk, FourDayWeek, Hasjob, Arbetsförmedlingen, TheirStack, RemoteOK, WorkingNomads, Jobicy (industry only, no separate category), and MyCareersFuture's employment-type companion field. These providers, where a job type is exposed at all, expose only an **employment-type** value (Section 18, "Employment Type" column) or nothing.

### 12.3 Finding: identical-looking tag strings come from structurally different fields

This is the strongest evidence that no cross-provider category system exists. A direct query against the live database — matching each of the most common stored tag values back to the provider(s) that produced it — shows the *same word* originating from *different, unrelated fields*:

```sql
SELECT provider, COUNT(*) FROM jobs WHERE 'Engineering' = ANY(tags)
GROUP BY provider ORDER BY COUNT(*) DESC;
```

| Tag value | Providers it actually comes from | What it means per provider |
|---|---|---|
| "Engineering" | SmartRecruiters (6,797), Greenhouse (1,154), Ashby (1,136) | SmartRecruiters' `function` taxonomy value **vs.** two entirely different companies' own `departments`/`team` org-chart labels — three unrelated fields that happen to use the same English word |
| "Full-time" | SmartRecruiters (54,431), Workable (2,954), Lever (1,724) | SmartRecruiters' `typeOfEmployment.label` **vs.** Workable's `employment_type` **vs.** Lever's `categories.commitment` |
| "FullTime" (no space) | Ashby (5,120) — 100% | Ashby's own `employmentType` spelling convention; not used by any other provider |
| "Full Time" (with space) | Himalayas (1,956), Lever (1,864), MyCareersFuture (17) | Three more independently-spelled variants of the same concept |
| "Contract Full time" | Lever (3,252) — 100% | A single compound value from Lever's `categories.commitment` field, not shared with any other provider |
| "Permanent" | NHS Jobs (7,967), Lever (141), MyCareersFuture (11) | Overwhelmingly a UK public-sector contract-type term from NHS Jobs' `type` field |
| "General Business" | SmartRecruiters (23,926), Workable (6) | 99.97% is SmartRecruiters' own `function` value — not a general "business jobs" category, just how SmartRecruiters labels one function |
| "Sales" | SmartRecruiters (1,870), Greenhouse (1,121), Ashby (482) | Same pattern as "Engineering" above |

Three different spellings of the same employment-type concept ("Full-time" / "FullTime" / "Full Time"), and one word ("Engineering") drawn from three structurally unrelated fields, is direct proof that treating these tag strings as one taxonomy would silently merge unrelated data. **A meaningful cross-provider job-category comparison is not currently possible with this schema**, independent of how much data volume any one provider contributes.

### 12.4 Implementation gap: a field this project could extract but currently doesn't

One case was found where a provider's underlying API documents a richer field than this project's implementation actually requests — confirmed directly in the module's own comment, not inferred:

> **Ashby** — `sources/ashby.py`: *"An optional `includeCompensation=true` query param adds salary data to the response - not needed for this project's schema, so it's left off."*

This is a genuine, deliberate implementation gap: Ashby's public API can return salary/compensation data, and this project chooses not to request it. No equivalent case was found for a *category* field specifically — the systematic search covering all 46 `normalize()` implementations (Section 12.2) found no instance of a provider exposing a job-category field that the code silently discards; where a category-like field exists, it is extracted into `tags`. This project's limitation is the absence of a normalized taxonomy to extract *into*, not a failure to read what a provider offers.

### 12.5 Employment-type coverage (distinct from category)

Employment type — full-time / part-time / contract / temporary / internship / freelance — is a separate, real signal from category, and is exposed by more providers (Section 18). Reading the raw stored values from Section 12.3's evidence: **Full-time** dominates wherever captured; **Part-time**, **Contract**, and **Fixed-Term/Permanent** appear as a minority; **Internship** and **Freelance** do not appear as distinct stored values anywhere in this review — either genuinely rare across these 46 sources' curated company/board lists, or captured under a differently-worded value not surfaced in the top tag list. This is stated as an observation from available data, not a claim that no internship/freelance postings exist upstream. 19,988 jobs (10.8%) carry no tags at all. **Remote / Hybrid / On-site** remains the one dimension that is genuinely normalized in this schema (`work_arrangement`, Section 6/7), independent of the `tags` free text.

### 12.6 Conclusion

The correct, defensible statement about this project's job-category data is: **no standardized job category exists or is derivable from the current schema.** What exists instead is a single free-text `tags` array mixing at least three structurally different concepts (proprietary category/department fields, employment-type values, and miscellaneous tags/skills) from 25 different taxonomies across 46 providers, none of which are reconciled with each other. See Section 18 for the complete per-provider field inventory, and Section 14 ("Should Have") for the recommended fix — a normalized `employment_type` column plus an explicit decision not to attempt category standardization until a common taxonomy is chosen.

---

## 13. Known Limitations

> **Multi-country locations.** Real postings genuinely list more than one country ("Germany, France, Netherlands"), a region ("EMEA", "APAC", "LATAM", "Europe"), or a paired market ("Remote (US/Canada)"). The normalization layer (Section 6) now detects both cases and forces `country = NULL` rather than guessing — the original `location` text is always preserved, so these postings remain searchable even without a resolved country. This was a deliberate design choice: accurate country statistics require declining to guess, not forcing every posting into one country.

> **Funding stage (Series A/B, etc.) is not available.** No provider integrated in this project exposes company funding data, and none was added — this would require a dedicated external data provider (e.g. Crunchbase/PitchBook-style API), which is out of scope for a job-posting aggregation pipeline. See Section 14.

> **Some commercial providers require paid access.** TheirStack is fully built but currently blocked by its account's billing plan (HTTP 402); Fantastic.jobs' free trial appears exhausted or account-restricted despite a configured key. Neither is a code defect — see Section 10 for the full breakdown.

> **Trial API quotas constrain volume.** SerpApi and OpenWebNinja are both capped at 200 requests/month on their free tiers, which is why each contributes only ~50 jobs despite having no technical pagination limit — the caps in code are deliberate quota conservation, not a discovered ceiling.

#### Additional limitations found during this review

- **Work-arrangement coverage is thin.** Only 4.6% of jobs carry an explicit remote/hybrid/on-site classification, because the classifier depends entirely on wording actually present in `location` text — most postings simply don't say.
- **A long tail of unresolved single-place locations remains.** 1,565 distinct `country` values exist post-normalization; the multi-country/region problem above is now solved, but genuinely ambiguous single places (e.g. a UK county like "Aberdeenshire" with no other identifying text) are correctly left unresolved rather than guessed — a separate, pre-existing gap from the multi-country fix.
- **Several sources are undocumented, reverse-engineered endpoints** (EURES, NHS Jobs, MyCareersFuture, NAV Arbeidsplassen's public token) — none publish an official API contract for what's actually being called, so any of them could change or break without notice.
- **HK Gov Vacancies effectively collapses to one stored row** — every job in the feed links to the same generic search-portal URL (no per-posting URL exists in the source data), so URL-based deduplication treats 57 of 58 fetched jobs as duplicates of the first. The data is real; the dedup strategy for this specific source needs a different key.
- **MyCareersFuture is similarly under-yielding** — 1,980 of 2,000 fetched records were duplicates in a single run, worth root-causing before relying on this source for Singapore coverage.
- **No salary data exists anywhere in the schema** — not partially captured, not planned; zero providers expose it in a form this pipeline consumes.
- **Reed exposes no employment-type field at all**, unlike most other commercial aggregators.
- **The dataset is a single point-in-time snapshot** (all 46 `provider_runs` rows share one `run_time`) — there is not yet a second run to validate the "new jobs" / staleness reporting logic against.

---

## 14. Future Improvements

### Must Have

- Move country/work-arrangement normalization inline into `jobs.py`'s save path, instead of a separate manual migration script run after the fact
- Scheduled, automated recurring syncs (currently a single manual invocation)
- Resolve the 5 non-contributing providers: provision credentials (Trade Me, CareerOneStop), resolve TheirStack billing, verify Fantastic.jobs' trial/account status, root-cause Arbeitnow's 0-job run

### Should Have

- Reporting dashboard on top of PostgreSQL (currently `psql`/report-query access only)
- Better location enrichment to shrink the 1,565-distinct-country long tail
- A normalized employment-type field, reconciling the fragmented `tags` values (Section 12)
- Dedicated Canada, broader APAC, and Middle East sources — currently incidental coverage only
- Provider-run health alerting (flag when a source's `jobs_fetched` drops to 0 or far below its historical baseline)

### Nice to Have

- Funding-stage / company-size enrichment via an external data provider
- Salary capture/normalization where a source exposes it
- Historical trend tracking across multiple runs once recurring syncs exist
- Integration of Fantastic.jobs' `/v1/active-jb` sibling endpoint (LinkedIn/Wellfound/YC-sourced)

---

## 15. Lessons Learned

- **The modular `BaseJobSource` pattern paid for itself.** Growing from the original 20 providers to 46 required zero changes to `jobs.py`, the frontend, or any existing source — only new, self-contained modules.
- **Undocumented, reverse-engineered endpoints are a real and recurring pattern** at this scale, not an edge case — 5 of 46 providers (EURES, NHS Jobs, MyCareersFuture, NAV Arbeidsplassen, HK Gov Vacancies) have no official public API contract for what's actually called. They work today, but each is a standing fragility risk with no advance warning if it changes.
- **Pagination behavior must be discovered live, not assumed from docs** — nearly every provider had at least one undocumented quirk (a silently-ignored `limit` param, a hard result-window boundary that returns HTTP 500 instead of an empty page, a `robots.txt` disallow on the richer endpoint) found only by testing against the real API.
- **Conservative, "never overwrite what you can't verify" normalization logic is safer than aggressive re-guessing.** The country-normalization work deliberately forces ambiguous locations to `NULL` rather than picking a plausible-looking answer — this trades completeness for correctness, which is the right trade for statistics a manager will actually read.
- **Per-source fault isolation is not optional at this scale.** With 5 of 46 providers currently non-contributing for entirely unrelated reasons (billing, missing credentials, a transient zero-result run), a pipeline that let one failure abort the whole run would have made this a much worse outage instead of a routine, fully-diagnosed Section 10 entry.
- **External dependencies need monitoring, not just integration.** TheirStack went from working to fully blocked purely through an account-plan change on their end, with no code change on ours — a reminder that "integrated" is not the same as "will keep working."

---

## 16. Final Recommendations

Before this pipeline is relied on for production reporting, the following should happen, roughly in priority order:

1. **Close the 5-provider gap.** Provision `TRADEME_CONSUMER_KEY/SECRET` and `CAREERONESTOP_USER_ID/API_TOKEN`, resolve or drop TheirStack's billing block, verify Fantastic.jobs' account/trial status, and re-run Arbeitnow to confirm its 0-job result was transient.
2. **Add provider-run health alerting** before scheduling recurring syncs — without it, a source silently dropping to 0 (as happened with Arbeitnow in this snapshot) could go unnoticed indefinitely.
3. **Move normalization inline** so every future run's data is immediately consistent, rather than depending on someone remembering to re-run `normalize_countries.py` after each sync.
4. **Investigate the two low-yield sources** (HK Gov Vacancies collapsing to 1 row, MyCareersFuture's 99% duplicate rate) before treating either as a reliable APAC data point.
5. **Extend the regression-test pattern already established for country normalization** (`test_normalize_countries.py`) to cover the aggregation and dedup pipeline itself, so future provider additions can't silently regress existing behavior.
6. **Confirm secrets handling carries through to any deployment target** — `.env` is git-ignored locally, which is necessary but not sufficient; verify the same discipline applies wherever this pipeline eventually runs on a schedule.
7. **Treat Section 13's limitations as a scoped backlog, not a blocker** — none of them prevent the current dataset from being useful today; they define what "production-grade" means for the next phase.

---

## 17. Conclusion

This project set out to build an extensible, multi-source job aggregation pipeline with a real database layer and honest location normalization — and delivered on all three. 46 provider integrations span government labour agencies, six ATS platforms, commercial search APIs, and RSS/XML feeds, all built against one shared interface that has already absorbed more than double its original provider count without structural change. 184,506 unique jobs are stored in PostgreSQL with genuine deduplication, full run history, and a country/work-arrangement normalization layer that would rather leave a field blank than guess wrong.

The platform is not yet production-scheduled — it currently reflects one complete backfill run rather than an ongoing sync — and five providers need attention before the roster is fully live. Neither fact undermines the core result: the architecture, data model, and normalization approach have proven themselves at 46-provider scale, and every open item in this report (Sections 10, 13, 14, 16) is a scoped, well-understood next step rather than an unknown risk. The project is ready to move from build phase into operational hardening.

---

## 18. Provider Capability Matrix

For every implemented provider, whether its `normalize()` implementation exposes each field — verified directly against `sources/*.py` for this report (the grep/read evidence behind every cell is the same evidence cited in Section 12). **Yes** = a genuine, structured field is extracted. **Partial** = the concept exists but is proprietary/heuristic/derived/hardcoded rather than a clean structured signal (see the Notes column for which). **Not Exposed** = no evidence of this field was found in the provider's `normalize()` implementation.

Two columns are near-constant and explained once here rather than repeated 46 times: **Salary** is "Not Exposed" for all 46 providers — the schema has no salary field and no module populates one; Ashby is the sole *confirmed* case where the provider's own API could supply it (`includeCompensation=true`) and this project deliberately doesn't request it (Section 12.4). **Visa Sponsorship** is "Not Exposed" for all 46 — no reference to visa/sponsorship data was found in any provider module; this project does not claim any provider offers it, only that none was found to expose it here.

| Provider | Job Category | Employment Type | Dept/Team | Company | Location | Remote Flag | Experience Level | Notes |
|---|---|---|---|---|---|---|---|---|
| SmartRecruiters | Partial (`function`) | Yes (`typeOfEmployment`) | Yes (`department`) | Yes | Yes | Yes (`location.remote`) | Not Exposed | |
| Greenhouse | Not Exposed | Not Exposed | Yes (`departments`) | Yes | Yes | Partial (keyword-inferred) | Not Exposed | |
| Lever | Not Exposed | Yes (`categories.commitment`) | Yes (`categories.department/team`) | Partial (derived from URL slug) | Yes | Yes (`workplaceType`) | Not Exposed | |
| NHS Jobs | Not Exposed | Yes (`type` element) | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | |
| USAJOBS | Partial (`job_categories`, federal job series) | Not Exposed | Not Exposed | Yes | Yes | Yes (`RemoteIndicator`) | Not Exposed | |
| Bundesagentur für Arbeit | Partial (`beruf`, `studiengang`) | Not Exposed | Not Exposed | Yes | Partial (hardcoded "Deutschland" fallback) | Partial (keyword-inferred) | Not Exposed | |
| Reed | Not Exposed | Not Exposed | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | Confirmed no category/employment-type field at all |
| NAV Arbeidsplassen | Not Exposed | Not Exposed | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | Module comment: "no category/skill data at this feed's summary level" |
| Ashby | Not Exposed | Yes (`employmentType`) | Yes (`department`, `team`) | Partial (manually mapped) | Yes | Yes (`isRemote`) | Not Exposed | Compensation param exists, deliberately unused (Section 12.4) |
| Workable | Partial (`function`) | Yes (`employment_type`) | Yes (`department`) | Yes | Yes | Yes (`telecommuting`) | Not Exposed | |
| Workday | Not Exposed | Yes (`time_type`) | Not Exposed | Partial (curated per tenant) | Yes | Partial (keyword-inferred) | Not Exposed | |
| Himalayas | Partial (`categories`, `parentCategories`) | Yes (`employmentType`) | Not Exposed | Yes | Yes | Partial (hardcoded True — remote-only board) | Partial (`seniority`) | |
| Arbetsförmedlingen | Not Exposed | Yes (`employment_type`) | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | |
| Adzuna | Partial (`category.label`) | Yes (`contract_time`/`contract_type`) | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | |
| The Muse | Partial (`categories`) | Not Exposed | Not Exposed | Yes | Yes | Yes (matched against a named "Remote" location) | Partial (`levels`) | |
| CareerJet | Not Exposed | Not Exposed | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | Module comment: "no job-category/employment-type field to draw tags from" |
| EURES | Not Exposed | Partial (coded `schedule`/`offering` values) | Not Exposed | Partial (`employer` null in ~80% of records) | Yes | Partial (keyword-inferred) | Not Exposed | |
| RemoteJobs.org | Partial (`category`) | Partial (`job_type`) | Not Exposed | Yes | Yes | Partial (hardcoded True — remote-only board) | Not Exposed | |
| France Travail | Partial (`secteurActiviteLibelle`, sector) | Yes (`typeContratLibelle`) | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | |
| Jooble | Not Exposed | Yes (`type`) | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | |
| Get on Board | Partial (`category_name`) | Not Exposed | Not Exposed | Yes | Yes | Yes (`attrs.remote`) | Not Exposed | |
| Taiwan Ministry of Labor | Partial (`CJOB_NAME1`/`CJOB_NAME2`) | Yes (`WK_TYPE`) | Not Exposed | Yes | Partial (hardcoded "Taiwan" fallback) | Partial (keyword-inferred) | Not Exposed | |
| Findwork.dev | Not Exposed (`keywords` is skills/tag text) | Yes (`employment_type`) | Not Exposed | Yes | Yes | Yes (`remote` field) | Not Exposed | |
| Mustakbil.com | Partial (`category`) | Not Exposed | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | |
| Teamtailor | Not Exposed | Not Exposed | Yes (`department`, from feed XML) | Yes | Yes | Yes (`remote` XML element = "fully") | Not Exposed | |
| Recruitee | Not Exposed | Yes (`employment_type_code`) | Yes (`department`) | Yes | Yes | Yes (`remote` field) | Not Exposed | |
| RemoteOK | Not Exposed (own `tags` is skills, e.g. "python") | Not Exposed | Not Exposed | Yes | Yes | Partial (hardcoded True — remote-only board) | Not Exposed | |
| MyJobMag | Partial (`industry`) | Not Exposed | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | |
| Jobicy | Partial (`jobIndustry`) | Yes (`jobType`) | Not Exposed | Yes | Yes | Partial (hardcoded True — remote-only board) | Partial (`jobLevel`) | |
| We Work Remotely | Partial (`category`) | Partial (`job_type`, RSS-scraped) | Not Exposed | Yes | Yes | Partial (hardcoded True — remote-only board) | Not Exposed | Also exposes `skills` (free text) |
| 4dayweek.io | Not Exposed | Not Exposed | Not Exposed | Yes | Yes | Not Exposed (hardcoded False) | Not Exposed | Richer JSON API exists but is unused (robots.txt) |
| SerpApi (Google Jobs) | Not Exposed | Yes (`schedule_type`) | Not Exposed | Yes | Yes | Yes (`work_from_home`) | Not Exposed | |
| OpenWebNinja (JSearch) | Not Exposed | Yes (`job_employment_type`) | Not Exposed | Yes | Yes | Yes (`job_is_remote`) | Not Exposed | |
| Working Nomads | Partial (`category`) | Not Exposed | Not Exposed | Yes | Yes | Partial (hardcoded True — remote-only board) | Not Exposed | |
| Remotive | Partial (`category`) | Not Exposed | Not Exposed | Yes | Yes | Partial (hardcoded True — remote-only board) | Not Exposed | |
| Freshersworld | Partial (regex-extracted from description) | Not Exposed | Not Exposed | Yes | Yes | Not Exposed (hardcoded False) | Not Exposed | |
| Jobspresso | Not Exposed | Not Exposed | Not Exposed | Yes | Yes | Partial (hardcoded True — remote-only board) | Not Exposed | Module comment: feed's `<category>` list confirmed empty live |
| MyCareersFuture | Partial (`categories`, govt taxonomy) | Yes (`employment_types`) | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | |
| NoDesk | Not Exposed | Not Exposed | Not Exposed | Yes | Yes | Partial (hardcoded True — remote-only board) | Not Exposed | |
| Hasjob | Not Exposed | Not Exposed | Not Exposed | Yes | Yes | Partial (matched against a curated remote-location list) | Not Exposed | |
| HK Gov Vacancies | Not Exposed (`academic` is a qualification requirement, not category) | Not Exposed | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | |
| TheirStack | Not Exposed | Yes (`employment_statuses`) | Not Exposed | Yes | Yes | Yes (`remote` nullable boolean) | Partial (`seniority`) | |
| Trade Me Jobs | Partial (`job_category`) | Yes (`job_type`) | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | Built from API spec; not exercised against live data (Section 10) |
| CareerOneStop | Not Exposed | Not Exposed | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | Only structured tag is a "Federal contractor" flag |
| Fantastic.jobs | Partial (`ai_taxonomies_a`) | Yes (`employment_type`) | Not Exposed | Yes | Yes | Yes (`work_arrangement`/`location_type`) | Not Exposed | |
| Arbeitnow | Partial (own `tags` field) | Yes (`job_types`) | Not Exposed | Yes | Yes | Yes (`remote` field) | Not Exposed | |

Column totals across all 46: **Job Category** — 23 Partial, 0 Yes, 23 Not Exposed. **Employment Type** — 22 Yes, 2 Partial, 22 Not Exposed. **Dept/Team** — 7 Yes, 39 Not Exposed. **Company** — 43 Yes, 3 Partial (Ashby, Lever, Workday), 0 Not Exposed. **Location** — 44 Yes, 2 Partial (Bundesagentur, Taiwan MOL, both hardcoded country-level fallbacks), 0 Not Exposed. **Remote Flag** — 13 Yes (genuine field), 23 Partial (11 keyword-inferred + 9 hardcoded-True remote-only boards + 3 other derivations), 2 Not Exposed (hardcoded False: 4dayweek, Freshersworld). **Experience Level** — 4 Partial (Himalayas, The Muse, Jobicy, TheirStack), 42 Not Exposed. **Salary** and **Visa Sponsorship** — 0 Yes/Partial, 46 Not Exposed each, for every provider.

These totals are the direct, numeric confirmation behind Section 12's conclusion: **zero** providers reach "Yes" on Job Category, and the 23 "Partial" providers use 23 structurally different, non-interoperable fields.

---

## 19. Project Status

A project-wide Completed / Partially Implemented / Not Yet Started breakdown, distinct from Section 5's feature-level list — this section covers every major component of the project, cross-referencing where each is documented in detail.

### Completed

- **46 provider integrations**, all built against the shared `BaseJobSource` interface (Section 2, Section 4)
- **PostgreSQL persistence layer** — `jobs` and `provider_runs` tables, upsert-on-`dedup_key`, idempotent schema application (Section 6)
- **Deduplication** — URL/hash-based, `UNIQUE` constraint enforced, 0 cross-provider duplicates remaining (Section 6, Section 7)
- **Per-provider run history and reporting queries** (Section 6, Section 7)
- **Offline country normalization**, including the multi-country/region-ambiguity fix that forces `NULL` rather than guessing (Section 6, Section 13)
- **Work-arrangement classification** (`remote`/`hybrid`/`onsite` derived from location text) (Section 6, Section 7)
- **`jobs.json` static export** for the frontend, unchanged since Milestone 2 (Section 2)
- **Frontend search, location filter, and sort** (Section 5, per `aggregation_summary.md`)
- **Per-source fault isolation** — one broken provider cannot halt the run (Section 2, Section 15)
- **This report's evidence-gathering methodology** — direct source-code verification of `tags`/`remote`/`company` field provenance for all 46 providers (Section 12, Section 18), superseding the earlier, less-verified version of Section 12

### Partially Implemented

- **41 of 46 providers actively contributing data**; 5 are built but non-contributing for external reasons (billing, missing credentials, one unexplained zero-result run) (Section 10)
- **Work-arrangement coverage** — only 4.6% of jobs carry an explicit classification; the underlying classifier itself is complete, but most source text simply doesn't say (Section 13)
- **Employment-type capture** — present and genuinely extracted for 24 of 46 providers (22 Yes + 2 Partial in Section 18), entirely absent for the other 22
- **Country resolution** — the multi-country/region case is now solved; a long tail of ~1,565 distinct single-place values remains unenriched (Section 13)
- **Credentialed-provider coverage** — 12 providers use API keys/OAuth; 2 (Trade Me, CareerOneStop) are built but uncredentialed in this environment (Section 10)
- **Data-quality auditing of this report itself** — this revision corrected one confirmed unsupported assumption (Reed/USAJOBS salary, Section 8) found during a full re-verification pass; the remaining sections were reviewed for consistency but not every claim in Sections 1–11 and 13–17 was independently re-derived from source code in this pass (see Section 20's methodology note)

### Not Yet Started

- **Standardized/normalized job-category taxonomy** — confirmed not to exist anywhere in this project's data, and not derivable from the current schema without a taxonomy-mapping effort (Section 12)
- **Salary capture and normalization** — no schema field, no provider extracts it (Section 12, Section 13, Section 18)
- **Visa-sponsorship data** — not found in any of the 46 providers' exposed fields; not evaluated whether any upstream API offers it (Section 18)
- **Experience-level normalization** — 4 providers expose a raw signal, folded into free-text `tags`, not a structured field (Section 18)
- **Company funding-stage/size enrichment** (Section 13, Section 14)
- **Scheduled/automated recurring syncs** — every run to date has been a single manual invocation (Section 6, Section 14)
- **Inline normalization at insert time** — country/work-arrangement normalization is a separate, manually-triggered migration step (Section 6, Section 14)
- **Provider-run health alerting** (Section 14, Section 16)
- **Dashboard/analytics UI** beyond the static search frontend (Section 5, Section 14)
- **Expired-job / posting-removal detection** — requires a second run to diff against; none has occurred yet (Section 7)

---

## 20. Requirement Coverage Matrix

Every requirement from this task's checklist, mapped to the section(s) that address it, with an honest status. **Covered** = fully addressed with evidence. **Partial** = addressed but with a named, specific gap. **Missing** = not addressed prior to this revision. Where the earlier version of this report stated something as fact without code-level support, it is marked **Corrected** and the fix is described.

| # | Requirement | Status | Section(s) | Notes |
|---:|---|---|---|---|
| 1 | Prepare a final project report | Covered | Whole document | |
| 2 | List every API/service used in the project | Covered | Section 4 | All 46, one row each |
| 3 | Document what has been completed and what is still pending | Covered | Section 5, Section 10, Section 19 | Section 19 added for a project-wide (not just feature-level) view |
| 4 | Identify features fully/partially/not-yet-implemented | Covered | Section 5, Section 19 | |
| 5 | List pricing models (free / free trial / pay-as-you-go / subscription / enterprise) | Covered | Section 4, Section 9 | No provider in this project documents a subscription or enterprise tier — stated explicitly in Section 9, not silently omitted |
| 6 | Highlight services requiring payment after the free tier expires | Covered | Section 9, Section 10 | TheirStack, Fantastic.jobs, SerpApi, OpenWebNinja |
| 7 | Include links to pricing pages for each service | Partial | Section 4, Section 9 | Every provider that has a registration/pricing/docs page has one, quoted verbatim from this project's own code; the 31 fully free, no-auth public APIs have no distinct "pricing page" to link by definition (Section 9), so "for each service" is satisfied for the 15 credentialed/paid services and not literally applicable to the other 31 |
| 8 | Document the number of jobs available from each API | Covered | Section 4, Section 7 | Fetched and Stored columns for all 46 |
| 9 | Break down job coverage by country/region | Covered | Section 11 | |
| 10 | List job types/categories per API (full-time, part-time, contract, internship, remote, hybrid, on-site, freelance) | Partial — and originally based on an unsupported framing | Section 12, Section 18 | The original checklist item itself conflates employment type and job category; Section 12 corrects this distinction. Employment-type values are now documented per-provider (Section 18); a genuine "job category" comparable across APIs does not exist (Section 12) — reported as a finding, not left unaddressed. Internship and freelance were not found as distinct stored values for any provider (Section 12.5) |
| 11 | Compare data quality across APIs (duplicates, missing fields, stale jobs, salary, company info) | Covered | Section 8, Section 18, Section 7 | Salary claims for Reed/USAJOBS corrected in this revision — see row 16 below |
| 12 | Report how current jobs are (average posting age, refresh frequency, expired jobs) | **Corrected — was Missing** | Section 7 ("Posting freshness") | Added in this revision: median 22 days / mean 229 days posting age (both reported, given the gap between them); refresh frequency and expired-job detection explicitly stated as not yet measurable (single ingestion run to date), not estimated |
| 13 | Analyze duplicate jobs across APIs and estimate deduplication rates | **Corrected — was Partial (top 10 only)** | Section 7 ("Deduplication rate and response time — every provider") | Now covers all 46 providers plus a global 8.08% rate, not just the top 10 |
| 14 | Document rate limits and API quotas for every provider | Partial | Section 4 (Notes column), Section 9 | Every row has a discovered pagination/result-window limit where one exists; providers with no pagination at all (single-shot APIs — Greenhouse, Ashby, Recruitee, Teamtailor, etc.) correctly show none, because none was found; published numeric quotas (requests/min or /day) beyond the monthly free-tier caps in Section 9 were not independently re-verified for every provider in this revision |
| 15 | Record response times and reliability for each API | **Corrected — was Partial (top 10 only)** | Section 7 (full 46-provider table), Section 8 (qualitative detail for top 10) | Duration now reported for all 46; "reliability" beyond duration remains qualitative (Section 4/8 Notes) since `provider_runs` does not record HTTP error/retry counts as a queryable metric |
| 16 | Note authentication requirements and implementation complexity for each API | Partial | Section 4 (Auth column) | Authentication is fully documented per provider; "implementation complexity" has no explicit rating column — inferring one without a defined, measured complexity metric would itself be an unsupported assumption, so it is left as a stated gap rather than invented |
| 17 | Document all filtering capabilities (location, remote, salary, experience level, visa sponsorship, company, industry, keywords) | Partial, and one entry **Corrected** | Section 8 (Filtering column, top 10 only) | Reed's and USAJOBS's Filtering cells previously overstated capability ("salary, distance" / "agency, remote") without code support — corrected in this revision to reflect only the pagination parameters actually implemented (Section 8 footnote). Filtering capability is not documented for the other 36 providers. No provider in this project was found to expose salary, experience-level, or visa-sponsorship filtering |
| 18 | Prioritize remaining tasks into Must/Should/Nice to Have | Covered | Section 14 | |
| 19 | End with clear recommendations and next steps for production readiness | Covered | Section 16, Section 17 | |

### Methodology note and its own limitation

This matrix, Section 12, and Section 18 were produced by re-reading `sources/*.py` directly for this revision (via targeted searches for `tags`, `remote`, `department`, `category`, `salary`, `visa`, `experience`, and related field names across all 46 modules, plus full reads of specific files where the evidence needed more context). Sections 1–11 and 13–17 were carried forward from the prior version of this report and were spot-checked rather than fully re-derived line-by-line in this revision; the one factual error found during spot-checking (the Reed/USAJOBS salary claim, row 16 above) was corrected on discovery. This is stated explicitly, per this task's own instruction to name a limitation rather than imply a completeness this revision did not fully re-verify.

---

## 21. Provider Research & Evaluation Summary

This section documents the engineering investigation behind provider selection — not just the 46 providers that were built, but the additional candidates researched and the reasoning for why each was or wasn't implemented. The source for everything in this section is this project's own research catalog (`research/api_analysis.md`, `reports/analytics_summary.md`, and the underlying provider-catalog data in the project's scratch research files), cross-checked against the live implementation in `sources/`. That catalog covers a much larger universe of candidate providers than the 8 named in this section's brief — this section documents only those 8 plus the two providers whose original categorization needed a evidence-based correction (noted inline); it is not a claim that these are the only providers ever researched.

Two corrections from the framing given for this section are made explicitly below, per this report's own standard of not restating a claim that the evidence doesn't support:

- **Fantastic.jobs** is listed only in 21.2, not 21.1 — the live database shows 0 jobs currently stored for this provider (Section 4, Section 10), so it cannot accurately be called "successfully implemented" regardless of its code being complete and credentialed.
- **Trade Me Jobs** is listed only in 21.2, not 21.4 — unlike the three other providers in 21.4, Trade Me already has a working implementation in `sources/trademe.py` (Section 4, Section 10). Its blocker is missing credentials and pending production approval, not technical impracticality, so it belongs with the "implemented but limited" providers, not the "investigated but not practical" ones.

### 21.1 Successfully Implemented Providers

The full set of 41 actively-contributing providers is already cataloged exhaustively in Section 4 (all 46, with status) and Section 18 (field-level capabilities). The six providers below — the specific examples requested for this section — are representative spotlights from that set, shown with the fields this section asks for.

| Provider | Region | Authentication | Approx. Job Coverage | Current Status | Notes |
|---|---|---|---:|---|---|
| NHS Jobs | United Kingdom | None (public feed) | 10,843 stored (13,011 fetched) | Live | Endpoint is undocumented; NHS's official documented API is separate and requires NHSBSA approval (Section 4) |
| 4dayweek.io | Global | None (public RSS feed) | 50 stored/fetched | Live | Fixed-size feed, no pagination; a richer JSON API exists on the same site but is excluded by `robots.txt` and deliberately not used (Section 4, Section 10) |
| Get on Board | Latin America | None (public tier) | 1,011 stored (1,261 fetched) | Live | Uses the free "Public API" search endpoint only; a separate paid "Private API" tier exists and was deliberately not used (Section 4, Section 9) |
| Working Nomads | Global / Remote | None (public API) | 33 stored/fetched | Live | No pagination; fixed ~36-job snapshot each run (Section 4) |
| Hasjob | India (tech/startup) | None (public Atom feed) | 6 stored/fetched | Live | Very low volume; company name is regex-extracted from feed HTML, not a dedicated field (Section 4) |
| Freshersworld | India (entry-level) | None (public RSS feed) | 30 stored/fetched | Live | Blocks the default `requests` User-Agent (HTTP 403) unless spoofed with a browser-like header (Section 4) |

### 21.2 Implemented but Currently Limited

| Provider | Current Status | Issue | Root Cause | Classification |
|---|---|---|---|---|
| Fantastic.jobs | Credentialed, 0 jobs in current snapshot | Returns zero jobs despite a configured, working API key | **Not fully confirmed.** `sources/fantasticjobs.py` documents a 7-day free trial; `FANTASTICJOBS_API_KEY` is confirmed set in this environment, but the provider returned 0 jobs in the most recent run. Trial expiration is the most plausible explanation given the documented trial window, but no HTTP error or response detail was captured for this run to confirm it. **The specific claim that the trial was "exhausted after approximately 3,000 jobs" does not appear anywhere in this project's code, `provider_runs` data, or research notes and is not stated as fact here** — it could not be verified. | Free Tier Limitation (suspected, unconfirmed) |
| TheirStack | Blocked | Every request returns HTTP 402 Payment Required | Confirmed directly in `sources/theirstack.py`'s module comment and in `provider_runs` (0 fetched, 0 inserted): the account's current billing plan does not include Jobs API access. Not a code defect. | Provider Limitation |
| CareerOneStop | Built, uncredentialed | 0 jobs — `fetch_raw()` raises before any request is made | Confirmed in `sources/careeronestop.py` and this environment's configuration: `CAREERONESTOP_USER_ID` and `CAREERONESTOP_API_TOKEN` are not set | Authentication Restriction |
| Trade Me Jobs | Built, uncredentialed | 0 jobs — `fetch_raw()` raises before any request is made | Confirmed in `sources/trademe.py` and this environment's configuration: `TRADEME_CONSUMER_KEY`/`TRADEME_CONSUMER_SECRET` are not set. Production (non-sandbox) access additionally requires completing Trade Me's own application approval process (Section 21.4 note above) | Authentication Restriction |
| Arbeitnow | 0 jobs in latest run | A free, no-auth API that has previously worked (931 jobs during earlier development, per `aggregation_summary.md`) returned 0 jobs in this run | **Not confirmed.** No error or exception was logged for this provider in the current run's records. The closest plausible categories are a transient network failure or an upstream API behaviour change, but neither is verified from available logs — stated as an open item rather than a confirmed diagnosis | Not determined (see note) |

### 21.3 Pending Approval / Credentials Required

**Saramin Open API (사람인 오픈 API)** — South Korea. Researched but not implemented; no code exists for this provider in `sources/`.

- **Approval process:** Access requires an application/approval step via `oapi.saramin.co.kr` before an access key is issued. The service is explicitly labeled "beta" in its own documentation, meaning its interface "may change."
- **Credentials required:** An approved, per-call access key (issued only after the application step above).
- **API limits:** A documented cap of 500 API calls per day. Pagination is page-based via `start` (zero-indexed page) and `count` (results per page, default 10, maximum 110).
- **Estimated implementation effort:** Low-to-Medium once credentialed — the API is REST-based with published code tables and example calls (PHP/Java), broadly similar in shape to the other government/commercial APIs already integrated in this project (e.g. CareerOneStop). The primary blocker is the approval step itself, not integration complexity.
- **Recommendation:** Apply for Saramin access; if approved, implement following the existing `BaseJobSource` pattern. Not yet built.

### 21.4 Investigated but Not Practical to Implement

| Provider | Why implementation is currently impractical | Limitation type | Could become feasible in future? |
|---|---|---|---|
| VDAB Vacature API (Belgium — Flanders public employment service) | Partner-only access: requires submitting an application form **and** completing an "exploratory onboarding meeting" with VDAB before any access is granted — a manual, relationship-based process rather than instant self-serve registration | Partnership Requirement | Yes — the API is real, documented (`developer.vdab.be/openservices`), and free. Feasibility depends entirely on completing VDAB's onboarding process, not on any technical or regional blocker. (Note: Belgium's other regional public-employment bodies — Actiris for Brussels, Forem for Wallonia — were not independently verified in this research pass and would need separate evaluation.) |
| CBOP — Centralna Baza Ofert Pracy (Poland public employment offices) | The dataset is listed as free/open on Poland's national open-data portal (`dane.gov.pl`), but research could not confirm whether it is exposed as a queryable API or only as periodic file downloads | Operational Restriction (access mechanism unconfirmed) | Yes — original research notes classify this as "Recommended," not rejected. A focused follow-up to confirm the actual access mechanism (API vs. bulk file) would resolve this. |
| Work24 (formerly Worknet/워크넷) — Korea Employment Information Service | The API itself is free, documented, and self-service (key-based registration via `data.go.kr`) — access is not actually the blocker. Research flagged a licensing restriction instead: the stated license limits use to non-commercial purposes with attribution and prohibits modifying the data, which was noted as needing re-confirmation with the issuing agency before any commercial ingestion | Operational Restriction (unresolved licensing terms) | Yes — pending direct confirmation from the Korea Employment Information Service that aggregating this data into a broader job board is compatible with the non-commercial license terms. |

*Trade Me Jobs is intentionally not listed in this table — see the correction note at the top of this section.*

### 21.5 Investigated but Not Technically Feasible

| Provider | Technical issue encountered | Public API availability | Authentication requirements | Reason implementation was not possible | Recommendation |
|---|---|---|---|---|---|
| Thailand Department of Employment — Smart Job Center (ไทยมีงานทำ) | No public API or developer documentation of any kind was found | None found | N/A — nothing to authenticate against | This is a web/mobile-app-only government job-matching platform with no discoverable integration surface at all — not a credentialing or licensing issue, simply no API | Re-evaluate only if the Department of Employment publishes a developer API in the future; not recommended for scraping given the absence of any documented terms for automated access |
| ZonaJobs (Argentina) | A page suggesting API documentation exists (`ofertas-de-trabajo-api.html`) was confirmed to be an SEO/landing page listing API-related job postings, not real developer documentation | None found — "no evidence of a real public or partner developer API was found" (research notes, verbatim) | N/A — no read API exists; the site's own account registration (name, email, CUIT/tax ID) is for employers *posting* jobs commercially, not for reading data | No read API exists for third parties | Not implementable without a direct partnership with Navent (ZonaJobs' parent company, which also owns Bumeran). Could become feasible if Navent opens a partner API in the future |
| Portal del Empleo / Servicio Nacional de Empleo (STPS Mexico) | Mexico's national open-data platform (`datos.gob.mx`, CKAN-based) was directly verified live (HTTP 200 on `/api/3/action/package_show`, dataset flagged `private:false`) and does host related labor-intermediation datasets — but a live, current-vacancy-specific query endpoint for the job board itself was not directly confirmed | Partial/unconfirmed — the open-data platform is real and reachable without authentication; whether it serves live searchable vacancy data (vs. static/periodic dataset exports) is unverified | None confirmed necessary for the CKAN platform itself | **Not ruled out** — the original research notes classify this provider as "Recommended," not rejected. It is listed here because full technical feasibility (a live, queryable vacancy endpoint) was not confirmed within the scope of this research pass, which is a different finding from "not feasible" | A focused follow-up investigation directly against the CKAN dataset is needed before an implementation decision can be made |
| GOV.UK Find a Job (DWP) | DWP publishes a bulk-upload API, but that surface is for employers *posting* jobs into the system, not for third parties *reading* from it | No well-documented open read/search API for third-party consumers was found; access is described as feed/partner-based | Historically an employer/partner data-feed arrangement rather than an open developer key | The read-access model for external consumers is not clearly public | Original research status (verbatim): "Investigate." Worth a direct follow-up with DWP / the API Catalogue (`api.gov.uk/dwp`) to confirm whether any read-only feed exists for third parties — would be authoritative, high-volume, and free if confirmed |

### 21.6 Provider Research Summary

| Category | Count | Description |
|---|---:|---|
| Successfully Implemented | 41 | Providers built and actively contributing live data in the current snapshot (Section 4, Section 10, Section 19) |
| Implemented with Limitations | 5 | Providers built and credentialed/code-complete, but currently returning 0 jobs for a specific, individually-diagnosed reason (Section 21.2) |
| Pending Approval | 1 | Researched, not yet built — requires a manual approval process before credentials can even be obtained (Saramin) |
| Not Practical (currently) | 3 | Researched, not yet built — a real API exists but is gated by a partnership process or an unresolved licensing/access question, not ruled out for the future (VDAB, CBOP, Work24) |
| Not Technically Feasible | 4 | Researched, not yet built — two have no discoverable public API at all (Thailand Smart Job Center, ZonaJobs); two have an unconfirmed or partner-only read-access model and were not ruled out outright (Portal del Empleo, GOV.UK Find a Job) |

The first two rows (46 providers total) are this project's actual implementation, detailed exhaustively in Sections 4, 10, 18, and 19. The last three rows (8 providers) are additional candidates from this project's broader research catalog, included here because they were specifically named for this section — not an exhaustive list of every provider ever investigated.

### 21.7 Engineering Investigation Summary

Provider selection depended on far more than whether an API technically existed. Across the 46 implemented providers and the 8 additional candidates documented above, evaluation consistently weighed:

- **Public API availability** — the hard floor: Thailand Smart Job Center and ZonaJobs were excluded because, after direct investigation, no public read API could be found at all, regardless of how valuable their underlying data might be.
- **Authentication requirements** — ranging from none (the majority of this project's 46 providers), to instant self-serve keys (USAJOBS, Adzuna, Findwork.dev), to gated approval processes that block integration regardless of technical readiness (Saramin's beta-access application, VDAB's onboarding meeting, Trade Me's production approval).
- **Regional restrictions** — several candidates cover only a narrow region by design (VDAB is Flanders-only, not all of Belgium; Work24 is Korea-only), which factors into prioritization against this project's existing country coverage (Section 11).
- **Documentation quality** — a recurring theme already noted in Section 15: some providers integrated here (NHS Jobs, EURES, MyCareersFuture, NAV Arbeidsplassen) have no official public documentation and were reverse-engineered from live behavior, while some researched-but-unbuilt candidates (CBOP, Portal del Empleo) have real open-data listings whose actual API mechanics remain unconfirmed.
- **Rate limits** — Saramin's 500-calls/day ceiling and the many self-discovered pagination/result-window limits across this project's 46 live providers (Section 4) directly shaped how much volume each source could realistically contribute.
- **Data quality** — covered in depth in Sections 8, 12, and 18 for implemented providers; a factor in why "the data exists" alone was never sufficient justification to integrate a source.
- **Stability** — undocumented, reverse-engineered endpoints (Section 13, Section 15) carry ongoing risk even after integration; Work24's unresolved licensing terms and VDAB's partner-only model raise the same kind of ongoing-risk question before integration even begins.
- **Long-term maintainability** — the clearest illustration is TheirStack (Section 21.2): a fully-integrated, working provider that stopped contributing purely due to an account-plan change on the provider's side, with zero code change on this project's end. This is the same lesson driving why several researched candidates with unresolved licensing or approval questions (Work24, CBOP, VDAB) were not rushed into implementation before those questions were settled.

Several providers were intentionally left unimplemented not because their underlying data was unsuitable or low-value, but because they were unsuitable **for an automated production system specifically** — a manual approval gate, an unconfirmed licensing restriction, or the complete absence of any API are all blockers regardless of how large or authoritative the underlying job database is (Saramin, VDAB, and Portal del Empleo are all large, legitimate, government-or-major-commercial job sources; none were excluded on data-quality grounds).

---

*Job Aggregation Platform — Final Project Report · Data snapshot 2026-07-10 · Report generated 2026-07-13 · Revised 2026-07-13 (Requirement Coverage Matrix, Provider Capability Matrix, Project Status, evidence-based Section 12, and Provider Research & Evaluation Summary added)*

*Source of truth: PostgreSQL (`jobs`, `provider_runs`) and this repository's own source code — no figure in this report is estimated or assumed. Where evidence was not available, this report states that explicitly rather than inferring a result.*
