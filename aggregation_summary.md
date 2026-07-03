# Job Aggregation Summary

## Project Status

- Phase 1 (No-auth API Integration): Completed
- Phase 2 (API-key Provider Integration): Completed
- Phase 3 (ATS Provider Integration): Completed

## Data Sources

### Phase 1 - No-auth providers

| Source | Jobs Fetched | Notes |
|---|---|---|
| Arbeitnow | 931 | Fully paginated via `links.next`; returned every job currently listed (capped at 200 pages / 20,000 jobs as a safety ceiling, never reached). |
| Himalayas | 3,000 | Offset-paginated (`offset`/`limit`), but `limit` is ignored server-side and always returns 20 jobs/page. Reports 90,000+ total jobs; fetching the full archive would take thousands of sequential requests, so pulls are capped at 150 pages (3,000 most recent postings, sorted newest-first). |
| RemoteOK | 100 | No pagination at all - a `page` param is silently ignored. Endpoint always returns the ~100 most recent jobs in a single request. Requires a browser-like `User-Agent` header or the request is blocked (403). |
| Jobicy | 100 | No pagination - a `page` param returns an explicit HTTP 400. The `count` param is honored up to a hard cap of 100. |
| The Muse | 2,000 | Page-paginated with a fixed page size of 20. Reports 400,000+ jobs across 20,000+ pages, but the public (unauthenticated) API hard-rejects any page number ≥ 100 with a 400 error - so 100 pages (2,000 jobs) is the maximum obtainable without an API key. |
| Bundesagentur für Arbeit | 10,000 | Offset-paginated (`page`/`size`) via the public Jobsuche API used by arbeitsagentur.de itself. Enforces a hard result-window limit of `page * size` <= 10,000 regardless of the 1,000,000+ jobs reported as available - 50 pages of 200 fetches the maximum allowed. Requires an `X-API-Key` header, satisfied with the well-known public key the official website ships in its own frontend (not a personal/secret credential). Requests now retry up to 3 times with exponential backoff (2s, then 4s) on timeouts and connection errors before a page is given up on - added after live runs showed occasional transient read timeouts around page 20-50 that a retry reliably recovers from. |

### Phase 2 - API-key providers

| Source | Jobs Fetched | Notes |
|---|---|---|
| Jooble | 1,129 | Requires a non-empty `keywords` value; a single space is sent as a wildcard. `ResultOnPage` honored up to 100/page, but the wildcard query's real result window empties out around page 12 regardless of the much larger reported total - pagination stops on a short page rather than exhausting a self-imposed cap. |
| USAJOBS | 10,000 | Auth via three headers (`Host`, `User-Agent`, `Authorization-Key`), not a query param. `ResultsPerPage` tested well above the commonly-cited 500, but the API's real reachable result window caps at exactly 10,000 regardless of page size - reached with 20 pages of 500. `remote` is a genuine field (`UserArea.Details.RemoteIndicator`), not a heuristic. |
| Adzuna | 2,000 | Country-scoped endpoint (`us` used here); no keyword required. `results_per_page` silently caps at 50. No pagination ceiling was found in testing (checked to page 5000), so - unlike the hard-capped APIs above - pagination is self-limited to 40 pages (2,000 jobs) to avoid unnecessary requests. |
| Reed | 9,000 | Auth via HTTP Basic Auth (API key as username, empty password). `resultsToTake` caps at 100/page. `resultsToSkip` returns HTTP 500 (not an empty page) above roughly 9,900-9,920, so pagination is capped safely below that boundary. No job-category/employment-type field exists in the response, so `tags` is always empty for this source. |
| SerpApi | 50 | Google Jobs via a metered, paid API (confirmed: 200 searches/month on the free plan via a real account-balance check before implementation). Cursor-based pagination, 10 jobs/page; capped at 5 pages (50 jobs) by design to conserve quota rather than pushed to any technical limit. `posted_at` is relative text ("3 days ago"), converted to an approximate date; `work_from_home` is a genuine boolean field. |
| OpenWeb Ninja | 47 | JSearch API; metered (200 requests/month free tier). Cursor-based pagination; capped at 5 pages (50 jobs max) for the same quota-conservation reason as SerpApi. The account initially returned a 403 "not subscribed" error - not a code issue - and a nested response nuance (jobs live under `data.jobs`, not `data` directly) was corrected once real access was confirmed. |
| CareerJet | 2,000 | Current v4 API (`search.api.careerjet.net`), distinct from the older "affid"-based widget API. Requires the account's calling IP to be allowlisted on CareerJet's dashboard, and a `Referer` header (any value) - neither is mentioned in the documentation as reviewed. `page_size` is documented as adjustable but silently ignored (always 20/page); dates are RFC 2822 formatted, not ISO. No pagination ceiling found, so capped at 100 pages (2,000 jobs) like Adzuna. |
| TheirStack | 0 | Jobs-search endpoint only (company enrichment/contacts/CRM endpoints on the same platform were deliberately not used). Bills **1 API credit per job returned** - a different cost model than any other source here - confirmed via a free account-balance check before testing. At least one filter (`posted_at_max_age_days` used here, set broadly) is required. Designed to cap at 50 jobs to conserve credits, but the account's current plan does not include Jobs API access at all: every request now returns HTTP 402 Payment Required. This is a plan/billing restriction, not a code defect - the source is skipped gracefully by the same error handling every other source failure uses. |

### Phase 3 - ATS providers

Unlike Phase 1/2, these sources are not a single global index - each is company-based, fetching one job board per configured company across a curated list of employers verified live before being added.

| Source | Jobs Fetched | Notes |
|---|---|---|
| Greenhouse | 22,728 | Company-based Job Board API (`boards-api.greenhouse.io`), no auth. Single-shot fetch per company - no pagination exists or is needed. `content=true` also returns `departments` (used for tags) at no extra cost. `company_name` is provided directly per job, so no slug-to-display-name mapping is needed. |
| Lever | 17,755 | Company-based Postings API (`api.lever.co`), no auth for GET. Supports real offset/limit pagination, though every configured company has returned its full list in a single page in practice. No company display-name field on job objects, so a name is derived from the site slug (e.g. `15five` -> `15Five`). `workplaceType` is a genuine remote/hybrid/onsite field. |
| Ashby | 5,171 | Public Job Posting API (`api.ashbyhq.com/posting-api`), no auth. Single-shot fetch per company board. No company name field at all on job objects (unlike Greenhouse), so each configured slug is mapped to a manually-verified display name rather than derived mechanically. `isRemote` is a genuine boolean. |
| SmartRecruiters | 65,193 | Public Posting API (`api.smartrecruiters.com/v1/companies`), no auth despite the docs implying an API key is required. Real offset/limit pagination is required - some boards run into the thousands of postings (Domino's alone: 24,000+). Unknown/empty company identifiers return HTTP 200 with an empty result rather than a 404, so verifying a company required checking `totalFound > 0`, not just status code. No public job-ad URL field in the response, so URLs are constructed from the company identifier and posting ID. |
| Workable | 7,644 | Public widget API (`apply.workable.com/api/v1/widget/accounts`), no auth - distinct from Workable's authenticated SPI API used for full ATS access, which was deliberately not used. Single-shot fetch per company. The account-level `name` field gives the company display name directly. Some companies return the same job's shortcode/URL more than once (once per posted city) - a genuine data characteristic, correctly collapsed by the pipeline's existing URL-based deduplication rather than needing source-level special-casing. |
| Teamtailor | 474 | No usable public API without a per-company API key (`api.teamtailor.com`); instead, every Teamtailor-hosted career site exposes a public, no-auth RSS feed at `{subdomain}.teamtailor.com/jobs.rss`, discovered via the career site's own HTML. Single-shot fetch per company (no pagination). Some companies are only reachable on Teamtailor's North-America data stack (`{subdomain}.na.teamtailor.com`) rather than the default domain. Dates are RFC 822 (RSS format), not ISO, requiring a separate conversion helper. |

## Aggregation Statistics

- **Total sources integrated:** 20 (6 Phase 1 + 8 Phase 2 + 6 Phase 3); 19 contributed jobs in the latest run (TheirStack blocked by its account's current API plan - see notes above)
- **Total jobs fetched (pre-dedup):** 159,322 (sum of the per-provider counts above, from the latest full pipeline run)
- **Duplicate jobs removed:** 3,528
- **Final unique jobs:** 155,794
- **Duplicate URLs remaining:** 0
- **Schema validation result:** Passed - all records contain exactly the 7 required fields with correct types (strings, list of strings, boolean), across every Phase 1, Phase 2, and Phase 3 source

## Technical Highlights

- **Modular source architecture:** Every provider lives in its own module under `sources/`, implementing a shared `BaseJobSource` interface (`fetch_raw()` + `normalize()`). Adding a new source never requires touching `jobs.py` - only a new module plus one line in `sources/__init__.py`'s `SOURCES` registry.
- **Large-scale aggregation:** The pipeline now pulls from 20 sources in a single run, fetching 159,322 jobs pre-dedup and writing 155,794 unique jobs to `jobs.json` - spanning general job-search APIs, government job boards, and dozens of individually-configured company boards across six different ATS platforms.
- **Multi-provider normalization:** Every source maps its provider-specific fields onto one common schema (`title`, `company`, `location`, `url`, `tags`, `remote`, `posted`), including provider-specific quirks such as merging multiple tag-like fields, deriving `remote` from location text or a genuine boolean/status field where available, and converting varied date formats (Unix timestamps, ISO strings, RFC 822/2822 strings) into a consistent `YYYY-MM-DD` string.
- **Deduplication by URL:** After collecting jobs from all sources, `jobs.py` deduplicates the combined list keyed on the job's `url` - the one field guaranteed to uniquely identify a specific posting, including across sources that occasionally surface the same externally-hosted job, and across ATS sources that occasionally list the same posting more than once (e.g. Workable jobs open in multiple cities).
- **Schema validation:** Output is verified after every merge to confirm all records have the correct keys, correct field types, and no duplicate URLs before being written to `jobs.json`.
- **Error handling:** Each source's `run()` method isolates failures - a network error, bad response, or per-record normalization issue in one source is logged and skipped rather than aborting the entire aggregation run, so a single broken API can't take down the whole pipeline.
- **Retry mechanism for Bundesagentur:** Bundesagentur's requests now retry up to 3 times with exponential backoff (2s, then 4s) on timeouts and connection errors before a page is given up on, and its request timeout was raised from 15s to 30s - added after live runs showed occasional transient read timeouts that a retry reliably recovers from, without changing its pagination logic, schema, or logging format.
- **Pagination support:** Implemented per-source according to what each API actually allows - full pagination (Arbeitnow), capped/best-effort pagination up to a documented or discovered limit (Himalayas, The Muse, Bundesagentur, USAJOBS, Reed, CareerJet, SmartRecruiters), single-shot fetches for APIs with no pagination (RemoteOK, Jobicy, Greenhouse, Ashby, Workable, Teamtailor), real but rarely-needed pagination (Lever), or deliberately conservative pagination on metered/paid APIs to control cost rather than exhaust a technical limit (SerpApi, OpenWeb Ninja, TheirStack).
- **API key management:** Phase 2 sources read their API keys/credentials exclusively from `sources/config.py`, which loads them from a git-ignored `.env` file via `python-dotenv`. No credential is ever hardcoded, and any Phase 2 source with a missing or empty credential raises inside `fetch_raw()`, which the existing `BaseJobSource.run()` error handling already catches and logs - skipping that source gracefully using the same mechanism as any other fetch failure, with no special-casing required.
- **ATS integrations:** Phase 3 added six applicant-tracking-system providers (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Teamtailor), each company-based rather than a single global index - fetching one job board per configured company across a curated, individually-verified list of employers per provider. All six use public, no-auth endpoints (in Teamtailor's case, a public RSS feed rather than its authenticated Web API), so none require any `.env` configuration.

## API Observations - Phase 1

- **Arbeitnow:** Clean, fully-paginated REST API with a `links.next` cursor; no meaningful limits encountered.
- **Himalayas:** Advertises an adjustable `limit` param that the server actually ignores (always 20/page); very large total archive (90,000+) made full pagination impractical, so recency-based capping was used instead.
- **RemoteOK:** Single-page snapshot API (no pagination); blocks requests lacking a standard `User-Agent` header.
- **Jobicy:** Single-page snapshot API; explicitly rejects unsupported pagination params with a 400 error rather than ignoring them.
- **The Muse:** Reports a very large total job count, but the public API silently caps usable pagination at page 99 (returns a 400 "page too high" error beyond that) - discovered by hitting the error during implementation and adjusting the page ceiling accordingly.
- **Bundesagentur für Arbeit:** Requires an API key header, but a public, non-secret key (used by the agency's own website) is sufficient. Enforces a strict `page * size <= 10,000` result-window limit typical of Elasticsearch-backed search APIs; some listings link out to third-party ATS pages (`externeUrl`) while others exist only on arbeitsagentur.de, requiring a constructed fallback URL from the job's reference number.

## API Observations - Phase 2

- **Jooble:** Requires a non-empty `keywords` value (no unscoped browse mode); a wildcard single-space query approximates one. The real usable result window for a broad query is far smaller than the reported total match count.
- **USAJOBS:** Documentation-heavy site that couldn't be rendered for inspection, so behavior was confirmed entirely via live requests. Auth is three headers rather than a single key param. Provides a genuine `remote` boolean, unlike most other sources.
- **Adzuna:** Country-scoped index (one query per country); silently caps `results_per_page` at 50 regardless of the requested value. No pagination ceiling found - the only source alongside CareerJet where that's true.
- **Reed:** Basic Auth instead of a header/query-param key. Hits a hard result-window boundary that surfaces as an HTTP 500 rather than an empty page, unlike every other capped source. No job-category data at all in its response.
- **SerpApi:** The first metered, pay-per-request source integrated; a real account-balance check (a free lookup) was done before any billable search. Only relative posting dates are available, not absolute ones.
- **OpenWeb Ninja:** Also metered. Initially blocked by an account-level "not subscribed" condition unrelated to the code; once resolved, a nested-response detail (`data.jobs`, not `data`) needed correcting against real data.
- **CareerJet:** The current v4 API differs substantially from older "affid"-based examples still found online. Two requirements - IP allowlisting and a mandatory `Referer` header - were undocumented in the reviewed docs and only surfaced through live testing (the first needed a dashboard change on the account itself). Dates are RFC 2822, not ISO.
- **TheirStack:** The only source that bills per job returned rather than per request - a materially different cost model that shaped how pagination was capped. Its platform also hosts non-job resources (company/contact/CRM data) that were deliberately left untouched, using only the jobs-search endpoint. As of the latest run, the account's plan no longer includes Jobs API access at all, so every request returns HTTP 402 Payment Required - a billing/plan limitation, not a bug, and not fixable in code.

## API Observations - Phase 3

- **Greenhouse:** No auth needed at all, and no pagination exists on the public Job Board API - one request returns a company's entire board. `company_name` comes directly on each job, unlike every other ATS provider here, so no manual name mapping was needed.
- **Lever:** Real offset/limit pagination is supported, but in practice no configured company's board has ever needed a second page. No company display-name field on job objects, so a name is derived from the URL slug (e.g. `15five` -> `15Five`) - verified to reproduce the real stylization for every configured company.
- **Ashby:** Also single-shot, no pagination. Unlike Greenhouse, job objects carry no company name field at all, so - like Lever - a display name has to come from somewhere else; unlike Lever's slugs, Ashby's are too inconsistently stylized for a mechanical rule (e.g. `elevenlabs` -> "ElevenLabs", `moderntreasury` -> "Modern Treasury"), so each is manually mapped instead of derived.
- **SmartRecruiters:** The only Phase 3 source where pagination is both real and actually needed - some company boards run into the thousands of postings. An unknown or empty company identifier returns HTTP 200 with an empty result instead of a 404, so "does this company exist" had to be checked via `totalFound > 0`, not response status. No public job-ad URL field exists in the response, so URLs are built from the company identifier and posting ID rather than read directly.
- **Workable:** The public widget API used here is a completely different, unauthenticated surface from Workable's documented (and auth-gated) SPI API. Single-shot per company. One data quirk discovered live: a single job open across multiple cities can appear as multiple entries sharing the exact same URL - not a bug, and already handled correctly by the pipeline's existing URL-based deduplication.
- **Teamtailor:** Has no usable public API without a company-issued API key; the only viable public data source turned out to be each career site's own `jobs.rss` feed, found by inspecting a real career site's HTML rather than the official docs. A subset of companies only resolve under a region-specific subdomain (`.na.teamtailor.com`) rather than the default one. Dates are RFC 822 (the RSS standard), not ISO 8601 like most other sources here.

## Phase 2 Final Status

Phase 2 (API-key provider integration) is complete. Eight additional sources - Jooble, USAJOBS, Adzuna, Reed, SerpApi, OpenWeb Ninja, CareerJet, and TheirStack - are integrated using the same modular `BaseJobSource` pattern as Phase 1, reading credentials exclusively from environment variables via `sources/config.py`. Every Phase 2 source was verified with real API requests during implementation, confirmed to normalize correctly into the shared schema, and confirmed to skip gracefully when its credentials are absent.

## Phase 3 Final Status

Phase 3 (ATS provider integration) is complete. Six additional sources - Greenhouse, Lever, Ashby, SmartRecruiters, Workable, and Teamtailor - are integrated using the same modular `BaseJobSource` pattern as Phase 1 and Phase 2, each fetching one job board per individually-verified company rather than a single global index. All six use public, no-auth endpoints, so none required any new environment variables or changes to `sources/config.py`. Every Phase 3 source was verified with real API requests during implementation and confirmed to normalize correctly into the shared schema before being run through the complete aggregation pipeline.

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

The overall project architecture remains modular on both sides. On the backend, Phase 2 added eight API-key providers - Jooble, USAJOBS, Adzuna, Reed, SerpApi, OpenWeb Ninja, CareerJet, and TheirStack - as self-contained modules, without changing the aggregation pipeline, the frontend, or any Phase 1 source. Credentials for these providers are read from environment variables via `sources/config.py`, never hardcoded. Phase 3 later added six ATS (applicant tracking system) providers - Greenhouse, Lever, Ashby, SmartRecruiters, Workable, and Teamtailor - using this exact same modular pattern: each is a self-contained, company-based module with no changes required to the aggregation pipeline, the frontend, or any existing source, and no new environment variables since every ATS provider uses a public, no-auth endpoint. This same modular pattern leaves room to later support additional API-key or ATS providers as needed.

## Final Status

Phase 1 is complete.

Phase 2 is complete.

Phase 3 is complete.

Frontend Milestones 2-5 are complete.

The project now aggregates jobs from all Phase 1, Phase 2, and Phase 3 providers - 20 sources in total - into a single normalized dataset of 155,794 unique jobs, and is ready for review and future expansion.
