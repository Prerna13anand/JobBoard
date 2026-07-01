# Job Aggregation Summary

## Project Status

- Phase 1 (No-auth API Integration): Completed

## Data Sources

| Source | Jobs Fetched | Notes |
|---|---|---|
| Arbeitnow | 898 | Fully paginated via `links.next`; returned every job currently listed (capped at 200 pages / 20,000 jobs as a safety ceiling, never reached). |
| Himalayas | 3,000 | Offset-paginated (`offset`/`limit`), but `limit` is ignored server-side and always returns 20 jobs/page. Reports 90,000+ total jobs; fetching the full archive would take thousands of sequential requests, so pulls are capped at 150 pages (3,000 most recent postings, sorted newest-first). |
| RemoteOK | 100 | No pagination at all - a `page` param is silently ignored. Endpoint always returns the ~100 most recent jobs in a single request. Requires a browser-like `User-Agent` header or the request is blocked (403). |
| Jobicy | 100 | No pagination - a `page` param returns an explicit HTTP 400. The `count` param is honored up to a hard cap of 100. |
| The Muse | 2,000 | Page-paginated with a fixed page size of 20. Reports 400,000+ jobs across 20,000+ pages, but the public (unauthenticated) API hard-rejects any page number ≥ 100 with a 400 error - so 100 pages (2,000 jobs) is the maximum obtainable without an API key. |
| Bundesagentur für Arbeit | 10,000 | Offset-paginated (`page`/`size`) via the public Jobsuche API used by arbeitsagentur.de itself. Enforces a hard result-window limit of `page * size` <= 10,000 regardless of the 1,000,000+ jobs reported as available - 50 pages of 200 fetches the maximum allowed. Requires an `X-API-Key` header, satisfied with the well-known public key the official website ships in its own frontend (not a personal/secret credential). |

## Aggregation Statistics

- **Total sources integrated:** 6
- **Total jobs fetched (pre-dedup):** 16,098
- **Duplicate jobs removed:** 185
- **Final unique jobs:** 15,913
- **Duplicate URLs remaining:** 0
- **Schema validation result:** Passed - all records contain exactly the 7 required fields with correct types (strings, list of strings, boolean)

## Technical Highlights

- **Modular source architecture:** Every provider lives in its own module under `sources/`, implementing a shared `BaseJobSource` interface (`fetch_raw()` + `normalize()`). Adding a new source never requires touching `jobs.py` - only a new module plus one line in `sources/__init__.py`'s `SOURCES` registry.
- **Job normalization:** Every source maps its provider-specific fields onto one common schema (`title`, `company`, `location`, `url`, `tags`, `remote`, `posted`), including provider-specific quirks such as merging multiple tag-like fields, deriving `remote` from location text where no explicit flag exists, and converting varied date formats (Unix timestamps, ISO strings) into a consistent `YYYY-MM-DD` string.
- **Deduplication by URL:** After collecting jobs from all sources, `jobs.py` deduplicates the combined list keyed on the job's `url` - the one field guaranteed to uniquely identify a specific posting, including across sources that occasionally surface the same externally-hosted job.
- **Schema validation:** Output is verified after every merge to confirm all records have the correct keys, correct field types, and no duplicate URLs before being written to `jobs.json`.
- **Error handling:** Each source's `run()` method isolates failures - a network error, bad response, or per-record normalization issue in one source is logged and skipped rather than aborting the entire aggregation run, so a single broken API can't take down the whole pipeline.
- **Pagination support:** Implemented per-source according to what each API actually allows - full pagination (Arbeitnow), capped/best-effort pagination up to a documented or discovered limit (Himalayas, The Muse, Bundesagentur), or single-shot fetches for APIs with no pagination (RemoteOK, Jobicy).

## API Observations

- **Arbeitnow:** Clean, fully-paginated REST API with a `links.next` cursor; no meaningful limits encountered.
- **Himalayas:** Advertises an adjustable `limit` param that the server actually ignores (always 20/page); very large total archive (90,000+) made full pagination impractical, so recency-based capping was used instead.
- **RemoteOK:** Single-page snapshot API (no pagination); blocks requests lacking a standard `User-Agent` header.
- **Jobicy:** Single-page snapshot API; explicitly rejects unsupported pagination params with a 400 error rather than ignoring them.
- **The Muse:** Reports a very large total job count, but the public API silently caps usable pagination at page 99 (returns a 400 "page too high" error beyond that) - discovered by hitting the error during implementation and adjusting the page ceiling accordingly.
- **Bundesagentur für Arbeit:** Requires an API key header, but a public, non-secret key (used by the agency's own website) is sufficient. Enforces a strict `page * size <= 10,000` result-window limit typical of Elasticsearch-backed search APIs; some listings link out to third-party ATS pages (`externeUrl`) while others exist only on arbeitsagentur.de, requiring a constructed fallback URL from the job's reference number.

## Final Status

Phase 1 (no-auth API integration and aggregation) is complete. Six sources are fully integrated into a modular, extensible pipeline that normalizes, merges, deduplicates, and validates job data into `jobs.json`. The project is ready to begin frontend development (Milestones 2-5).

# Frontend Implementation

## Milestone 2 – Render Job Board

Built the initial frontend (`index.html`, `style.css`, `script.js`) on top of the aggregated dataset:

- Loads `jobs.json` via `fetch()` and renders it once the data arrives.
- Renders every job as a responsive card (title, company, location, remote/on-site badge, tags, posted date), laid out in a CSS Grid that reflows across screen sizes.
- Displays the total job count in the header (e.g. "15,913 jobs").
- Shows a loading message while `jobs.json` is being fetched.
- Shows a friendly error message if `jobs.json` fails to load.

## Milestone 3 – Search

Added a live search box above the job grid:

- Filters the displayed jobs as the user types.
- Matches against job title, company name, and tags.
- Matching is case-insensitive.
- The displayed job count updates live to reflect the number of matches.
- Displays "No jobs found." when nothing matches the current query.

## Milestone 4 – Location Filter

Added a location filter that composes with search:

- A dropdown populated dynamically from the unique `location` values found in `jobs.json` (not hardcoded), sorted alphabetically, with "All Locations" as the default.
- Search and location filters apply together (AND logic) - results must satisfy both.
- A "Clear Filters" button resets the search box and location dropdown and restores the full job list.

## Milestone 5 – Final Polish

Completed the frontend with sorting and input debouncing:

- Sort by Newest - orders jobs by the `posted` field, most recent first (default).
- Sort by Title A-Z - orders jobs alphabetically by title.
- Sorting composes with search and the location filter, following the pipeline: filter by search -> filter by location -> sort -> render.
- The search input is debounced (~280ms) so filtering doesn't run on every single keystroke, without changing search behavior or results.
- The existing loading and error states from Milestone 2 were preserved as-is.
- The responsive card layout and styling from earlier milestones were preserved.

## Frontend Testing

The frontend was tested both manually and with automated Playwright tests driving a real headless browser against the page (served locally, since `fetch()` requires HTTP rather than `file://`). Verified:

- Search matches on title, company, and tags, case-insensitively.
- Location filtering restricts results to the selected location, populated dynamically from the dataset.
- Sorting - both Newest (descending by `posted`) and Title A-Z (ascending, case-insensitive) - produces correctly ordered results.
- Search + Location + Sort combinations all apply correctly together, with job counts cross-checked against independently computed expected values.
- Debounced search delays filtering until typing pauses, then produces the correct final result.
- The loading state appears while `jobs.json` is being fetched and clears once rendering completes.
- The error state displays a friendly message when `jobs.json` fails to load.
- No console errors occur during normal interaction (search, filter, sort, clear, and combinations thereof).

## Architecture

The backend aggregation pipeline (`jobs.py`, `sources/`) was not modified during any of the frontend milestones - all frontend work only reads the `jobs.json` file the backend produces. The frontend is a static HTML/CSS/JavaScript application with no build step, structured around small, composable functions (`applyFilters`, `applySort`, `updateView`, etc.) rather than one large script, so it stays easy to extend.

The overall project architecture remains modular on both sides. On the backend, new job sources can be added as self-contained modules without changing the aggregation pipeline. This leaves room to later support:

- Greenhouse
- Lever
- API-key providers such as Jooble, Adzuna, Reed, CareerJet, etc.

## Final Status

Phase 1 is complete.

Frontend Milestones 2-5 are complete.

The project is ready for review and future expansion.
