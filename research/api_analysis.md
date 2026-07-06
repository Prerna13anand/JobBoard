# API & Dataset Analysis — Master Research Document

**Purpose:** A single research reference for the Job Aggregation Platform, intended to be
consumed by a later implementation/reporting pass. This document is **analysis and
research only** — no source code, `jobs.py`, or `jobs.json` was modified in producing it,
and no aggregation run was performed.

**Dataset analyzed:** `jobs.json` — **155,794** unique job records (the deduplicated output
of the latest pipeline run).

**Reference dates used:**
- The snapshot was generated on/around **2026‑07‑04**; the newest `posted` date present in
  the data is **2026‑07‑03** (treated as the effective "fetch date").
- "Today" for freshness math is **2026‑07‑06** (current date at time of analysis).
- Where it matters, freshness is reported against **both** reference points, because the
  2–3 day gap between fetch and analysis materially changes the "last 24 hours" bucket.

**Method note:** All counts in Sections 1–3 were computed by a throwaway, read‑only script
that loaded `jobs.json` and aggregated it in memory. Region/country attribution is derived
from the free‑text `location` field using a keyword/token classifier (countries, major
cities, US state names + abbreviations, and region keywords), so region figures are
**approximate** — the residual "Other/Unknown" bucket quantifies the classifier's limits
and is reported honestly rather than being forced into a region.

---

## SECTION 1 — Regional Coverage Analysis

### 1.1 Jobs by region

| Region | Jobs | % of dataset |
|---|---:|---:|
| United States | 79,427 | 51.0% |
| Europe (continental, non‑UK) | 21,886 | 14.0% |
| United Kingdom | 10,305 | 6.6% |
| LATAM | 6,955 | 4.5% |
| Singapore / Southeast Asia | 4,629 | 3.0% |
| Canada | 3,436 | 2.2% |
| Remote / Worldwide (region‑less) | 822 | 0.5% |
| **Other / Unclassified** | **28,334** | **18.2%** |
| **Total** | **155,794** | **100%** |

**Sum of the six requested target regions:** **126,638 jobs (81.3%)** of the dataset.

The "Other / Unclassified" bucket (18.2%) is dominated by (a) large non‑target markets the
project pulls in incidentally — India, China, Australia, Japan, the Gulf states, etc. — and
(b) location strings too ambiguous for confident attribution (e.g. bare city names shared
across countries, department‑only strings, or "Multiple locations").

### 1.2 Percentage contribution by region (target regions only)

Normalized to the 126,638 jobs that fall into a requested region:

| Region | Share of target‑region jobs |
|---|---:|
| United States | 62.7% |
| Europe | 17.3% |
| United Kingdom | 8.1% |
| LATAM | 5.5% |
| Singapore / Southeast Asia | 3.7% |
| Canada | 2.7% |

### 1.3 Jobs by country — Top 25

| # | Country | Jobs | % |
|---:|---|---:|---:|
| 1 | United States | 79,427 | 51.0% |
| 2 | *Unknown / Other (unclassified)* | 17,708 | 11.4% |
| 3 | Germany | 12,167 | 7.8% |
| 4 | United Kingdom | 10,305 | 6.6% |
| 5 | *LATAM (country not resolved)* | 4,497 | 2.9% |
| 6 | India | 3,471 | 2.2% |
| 7 | Canada | 3,436 | 2.2% |
| 8 | France | 2,218 | 1.4% |
| 9 | China | 1,435 | 0.9% |
| 10 | Australia | 1,225 | 0.8% |
| 11 | Europe (country not resolved) | 1,171 | 0.8% |
| 12 | Malaysia | 1,094 | 0.7% |
| 13 | Spain | 1,057 | 0.7% |
| 14 | Indonesia | 1,010 | 0.6% |
| 15 | Mexico | 909 | 0.6% |
| 16 | Singapore | 881 | 0.6% |
| 17 | Saudi Arabia | 855 | 0.5% |
| 18 | Remote / Worldwide | 822 | 0.5% |
| 19 | Philippines | 770 | 0.5% |
| 20 | Ireland | 734 | 0.5% |
| 21 | Japan | 720 | 0.5% |
| 22 | Brazil | 654 | 0.4% |
| 23 | Netherlands | 610 | 0.4% |
| 24 | Poland | 590 | 0.4% |
| 25 | UAE | 580 | 0.4% |

*(Rows 2, 5, and 11 are classifier residuals, not real countries; they are retained here so
the percentages remain honest and traceable.)*

### 1.4 Where the volume actually comes from (source attribution)

Because `jobs.json` carries no `source` field, provider attribution was reconstructed from
each record's URL host. This is the single most important context for the regional numbers:

| URL host (provider) | Jobs | % |
|---|---:|---:|
| jobs.smartrecruiters.com (SmartRecruiters) | 65,193 | 41.8% |
| jobs.lever.co (Lever) | 17,755 | 11.4% |
| usajobs.gov (USAJOBS) | 10,000 | 6.4% |
| greenhouse.io (Greenhouse, two hosts) | 14,930 | 9.6% |
| reed.co.uk (Reed) | 9,000 | 5.8% |
| arbeitsagentur.de + ams.at + others (Bundesagentur) | ~7,800 | ~5.0% |
| jobs.ashbyhq.com (Ashby) | 5,171 | 3.3% |
| apply.workable.com (Workable) | 4,159 | 2.7% |
| himalayas.app (Himalayas) | 2,964 | 1.9% |
| adzuna.com (Adzuna) | 2,001 | 1.3% |
| themuse.com (The Muse) | 2,000 | 1.3% |
| jooble.org / jobviewtrack.com (Jooble) | ~3,100 | ~2.0% |
| arbeitnow.com (Arbeitnow) | 930 | 0.6% |

### 1.5 Observations

- **The dataset is overwhelmingly US‑centric (51%)** and, more precisely, **enterprise‑ATS**
  centric. A single provider — **SmartRecruiters — supplies 41.8% of all jobs**, and Lever
  another 11.4%. The US skew is therefore largely an artifact of *which companies* were
  hand‑curated into the ATS provider lists, not of a balanced global crawl.
- **Canada (2.2%) is the weakest of the six target regions**, despite being a first‑class
  target. There is currently **no Canada‑specific source**; Canadian jobs appear only
  incidentally through global ATS boards (e.g. Wealthsimple, Shopify‑adjacent companies) and
  Adzuna, which is configured for `us` only.
- **The UK (6.6%) is well covered for its size**, almost entirely by the dedicated Reed
  source (5.8% of the whole dataset on its own). Remove Reed and UK coverage collapses.
- **Europe (14%) is really "Germany + a long tail."** Germany alone (12,167) is 56% of the
  European total, driven by the two German public‑agency sources (Bundesagentur / AMS).
  France, Spain, Netherlands, Poland, Ireland are present but thin.
- **LATAM (4.5%) is stronger than expected**, but ~65% of it (4,497 of 6,955) could not be
  resolved to a specific country — these are overwhelmingly **remote "LATAM"/"Latin America"
  postings from Lever/Greenhouse companies** that hire nearshore, rather than jobs physically
  located in a LATAM city. Real in‑country volume (Mexico 909, Brazil 654, plus a tail) is
  modest.
- **Singapore / SEA (3.0%)** is carried by Malaysia (1,094), Indonesia (1,010), Singapore
  (881), and the Philippines (770). There is **no dedicated SEA source** — this is entirely
  incidental coverage, which is why it's shallow and skewed toward whichever global companies
  happen to staff the region.
- **18.2% is unclassifiable.** A meaningful fraction of that is genuinely non‑target markets
  (India, China, Gulf, Australia), but some is target‑region volume lost to messy location
  strings. This is a data‑quality ceiling on any location‑based feature (filters, maps,
  regional counts) in the frontend.
- **Only ~11% of jobs are remote** (see §3/§6), so the "region" of a job is meaningful for
  the vast majority of the dataset — location quality matters.

---

## SECTION 2 — Job Freshness Analysis

Freshness is computed from the normalized `posted` (`YYYY-MM-DD`) field. 155,779 of 155,794
records (99.99%) carry a parseable date; only **15** are unparseable/blank.

### 2.1 Freshness relative to "today" (2026‑07‑06)

| Bucket | Jobs | % |
|---|---:|---:|
| Last 24 hours | 0 | 0.0% |
| Last 3 days | 18,580 | 11.9% |
| Last 7 days | 17,929 | 11.5% |
| Last 14 days | 26,530 | 17.0% |
| Last 30 days | 17,374 | 11.2% |
| Older than 30 days | 75,366 | 48.4% |
| Unknown | 15 | 0.0% |

### 2.2 Freshness relative to the fetch date (2026‑07‑03, the newest date in the data)

This is the fairer view of "how fresh was the data *when it was collected*":

| Bucket (age at fetch) | Jobs | % |
|---|---:|---:|
| ≤ 24 hours | 24,052 | 15.4% |
| ≤ 3 days | 6,582 | 4.2% |
| ≤ 7 days | 11,884 | 7.6% |
| ≤ 14 days | 24,610 | 15.8% |
| ≤ 30 days | 16,949 | 10.9% |
| Older than 30 days | 71,702 | 46.0% |
| Unknown | 15 | 0.0% |

### 2.3 Deep‑staleness tail

| Age | Jobs | % |
|---|---:|---:|
| Older than 90 days | 45,075 | 28.9% |
| Older than 180 days | 29,640 | 19.0% |
| Older than 365 days | 21,768 | 14.0% |

- **Oldest posting:** 2009‑12‑05. **Median posting date:** 2026‑06‑09 (~24 days before fetch).

### 2.4 Observations

- **The "Last 24 hours = 0" line is an artifact of the 3‑day gap** between the fetch
  (2026‑07‑03) and the analysis date (2026‑07‑06). Against the fetch date, **15.4% of the
  dataset was ≤ 24h old**, which is genuinely fresh. The takeaway is not "the data is dead"
  but "**the data is a static snapshot and ages the moment it's written**."
- **About half the dataset (46–48%) is older than 30 days**, and a substantial **14% is over
  a year old** (with a long tail back to 2009). Enterprise ATS boards (SmartRecruiters, and
  to a lesser extent Greenhouse/Lever) are the main contributors of stale postings: they
  return a company's *entire* currently‑open board, which includes evergreen/hard‑to‑fill
  roles that have been open for months, government/union postings, and requisitions that are
  effectively perpetual.
- **The freshest sources are the remote/aggregator feeds** (Himalayas, RemoteOK, Jobicy, The
  Muse, Arbeitnow) which are natively newest‑first, and the government feeds (USAJOBS,
  Bundesagentur) which rotate quickly. The **stalest** are the large ATS boards.
- **The snapshot has no notion of expiry.** A job removed from the source after the fetch
  remains in `jobs.json` until the next full run overwrites the file. There is no incremental
  update and no "last seen" timestamp, so dead links accumulate between runs.

### 2.5 Possible improvements (discussion only — not implemented)

1. **Run more frequently / on a schedule.** The single biggest freshness lever is simply
   re‑running the pipeline (daily or hourly for the fast feeds). Freshness decays linearly
   with time‑since‑fetch; nothing else matters if the snapshot is a week old.
2. **Capture a `fetched_at` / `last_seen` timestamp per run** so the frontend can show "data
   as of X" and compute age honestly, and so stale records can be detected.
3. **Apply per‑source recency filters where the API supports them.** Several providers accept
   a max‑age/date filter (TheirStack `posted_at_max_age_days`, Adzuna `max_days_old`,
   USAJOBS `DatePosted`, The Muse has publication ordering, Jooble `datecreatedfrom`). Using
   these would drop the deep‑stale tail at the source instead of ingesting and storing it.
4. **Sort/weight ATS boards toward recent requisitions**, or cap how far back an ATS board's
   postings are ingested, since those boards are the primary source of >90‑day staleness.
5. **Add an age‑based filter/badge in the UI** (already have `posted`) so users can restrict
   to "last 7/30 days," turning a data limitation into a user‑visible feature.
6. **Incremental refresh with expiry:** on each run, mark records not seen this run as
   expired rather than silently carrying them forward, to stop dead‑link accumulation.

---

## SECTION 3 — Duplicate Analysis

**No records were removed or modified.** This section measures duplication and researches
strategies only.

### 3.1 Current state of duplication in `jobs.json`

The pipeline already deduplicates **by exact `url`** (`jobs.py:dedupe_jobs`). Confirmed
against the data:

| Check | Result |
|---|---|
| Exact‑URL duplicates remaining | **0** |
| Records with empty URL | **0** |

So the URL‑keyed dedup is working perfectly on its own terms. The interesting question is
**how much *non‑URL* duplication remains** — i.e. the same real job represented by more than
one row with different URLs.

### 3.2 Collision counts under alternative keys

| Candidate key | Extra rows (beyond first) | Distinct colliding groups |
|---|---:|---:|
| `url` (current) | 0 | 0 |
| `title` + `company` | 35,300 | 11,340 |
| `title` + `company` + `location` | 8,290 | 4,963 |
| `company` + `location` + `title[:40]` | 9,797 | — |
| `title` only | 46,968 | — |

**Crucial caveat:** every one of the 11,340 `title+company` groups spans **more than one
distinct URL**. That means these are **not** URL duplicates that slipped through — they are
either (a) genuinely distinct postings that happen to share a title, or (b) true cross‑URL
duplicates. Inspecting the largest groups makes clear that (a) dominates:

```
 876×  BoxLunch — "Sales Associate"
 869×  BoxLunch — "Part-Time Assistant Manager - Level 1"
 862×  BoxLunch — "Seasonal Sales Associate"
 268×  Domino's — "Delivery Driver"
 240×  TSMG — "Mapping Data Collection Driver"
 158×  Transportation Security Administration — "Transportation Security Officer"
  96×  Costa Coffee — "Barista"
```

These are the **same role posted at hundreds of different physical locations**, each a
legitimately separate requisition with its own URL. This is the single most important finding
in this section: **aggressive `title+company` deduplication would destroy tens of thousands of
real, distinct jobs.** The `title+company+location` key is far safer (8,290 extra rows) but
still collapses multiple genuine openings for the same role in the same city.

The **true** duplicate problem — the same job surfaced by two *different providers* under two
different URLs — is real but much smaller and harder to isolate. It is most likely between:
overlapping aggregators (Jooble ↔ Adzuna ↔ Careerjet ↔ The Muse all re‑list third‑party
postings), and between an aggregator and the original ATS board it scraped.

### 3.3 Deduplication strategies — strengths & weaknesses

| Strategy | How it works | Strengths | Weaknesses |
|---|---|---|---|
| **Exact URL** *(current)* | Hash/set on the canonical posting URL | O(n), deterministic, zero false positives, no config; the URL is the one field that truly identifies a posting | Misses the same job at different URLs (tracking params, aggregator wrappers, cross‑provider re‑lists); a normalized URL would catch more |
| **Normalized URL** | Lowercase host, strip query/UTM/fragment, strip trailing slash before comparing | Catches tracking‑param variants and http/https/www differences at near‑zero cost | Some sites encode the real identity *in* query params — over‑stripping merges distinct jobs; aggregator redirect wrappers still differ |
| **Title match** | Group by normalized title | Trivial | Useless alone — 46,968 collisions, mostly unrelated jobs sharing generic titles ("Software Engineer") |
| **Company match** | Group by employer | Useful as a *blocking* key to shrink comparisons | Never a dedup key by itself — a company has many distinct jobs |
| **Location match** | Group/compare by location | Good secondary signal to separate same‑title roles across cities | Free‑text and inconsistent ("Remote" vs "Remote, US" vs "Worldwide"); weak alone |
| **Description match** | Compare posting body text (exact or hashed) | Very strong signal — bodies are long and distinctive; near‑identical bodies ⇒ same job even across providers | **Not available in this schema** (no `description` field); expensive to fetch/store/compare; boilerplate (EEO, benefits) causes false merges |
| **Fuzzy matching** | Similarity (Levenshtein / token‑set ratio / Jaccard / cosine over TF‑IDF) on title (+company/location) above a threshold | Catches near‑duplicates exact keys miss ("Sr. Engineer" vs "Senior Engineer", cross‑provider phrasing) | O(n²) unless blocked; threshold tuning trades false merges vs misses; at 155k rows must be paired with blocking to be tractable |
| **Hashing** | Store a hash (MD5/SHA1) of a chosen key for O(1) set membership | Makes any *exact* key cheap and memory‑light at scale; how URL dedup should scale | Only ever matches *identical* inputs — as brittle as whatever field is hashed; not fuzzy |
| **SimHash / MinHash (LSH)** | Locality‑sensitive hashing of shingled text; near‑duplicates share buckets | Brings fuzzy, description/title‑level near‑dup detection down to ~O(n); industry standard for large corpora | More machinery; needs the text to hash (ideally descriptions); tuning of shingle size / band count |
| **Composite key** | Concatenate several normalized fields, e.g. `norm(title) | norm(company) | norm(city)` | Cheap (still O(n) hashing), far more precise than any single field, tunable by adding/removing fields | Still exact‑match on each component — a one‑character location difference defeats it; must choose fields carefully to avoid merging real distinct jobs (see BoxLunch) |

### 3.4 Recommendation for this project

A **two‑tier strategy**, layered on top of (not replacing) the current URL dedup:

1. **Tier 1 — keep exact‑URL dedup, but normalize the URL first.** Lowercase the host, drop
   the fragment, and strip known tracking/query parameters (`utm_*`, `gh_src`, `ref`,
   `source`, session ids) before hashing. This is O(n), risk‑free for real jobs, and mops up
   the cheapest cross‑variant duplicates (especially aggregator tracking wrappers). This is
   the highest‑value, lowest‑risk change.

2. **Tier 2 — a conservative composite key for cross‑provider near‑dups, applied with
   blocking.** Block on `company` (normalized), then within each company block compare
   `title`+`location`. Only collapse when title **and** location match closely (exact
   normalized location, or high fuzzy similarity on title). Critically, **do not** collapse
   on `title+company` alone — §3.2 proves that erases ~35k legitimate multi‑location roles.
   Blocking on company keeps the fuzzy comparison tractable (small groups) instead of O(n²)
   over 155k rows.

3. **Do not pursue description‑based or LSH dedup yet** — the schema has no description field,
   so it would require fetching and storing full bodies for 155k jobs. Revisit only if
   descriptions are added to the schema later.

**Net:** the current URL dedup is correct and should stay as the backbone; the realistic
upside is (a) URL normalization and (b) a *careful, location‑aware* composite/fuzzy pass for
cross‑provider overlap — explicitly guarded against the multi‑location false‑merge trap.

---

## SECTION 4 — API Research (providers currently in use)

20 sources are registered (`sources/__init__.py`). Details below are drawn from each source
module's implementation and its docstring, which record behavior confirmed by live testing
during implementation. Fields not applicable to a given provider are marked "—".

### Phase 1 — No‑auth providers

#### Arbeitnow — `https://www.arbeitnow.com/api/job-board-api`
- **Auth:** None.
- **Rate/request limits:** None documented/encountered.
- **Pagination:** Cursor via `links.next`; 100 jobs/page. Followed to exhaustion (safety cap
  200 pages / 20,000 jobs, never reached — ~930 jobs currently).
- **Result limit:** Effectively the whole board (~930).
- **Date filter:** — (no server-side filter; `created_at` unix timestamp returned).
- **Country/Location/Keyword/Company/Category filters:** — (full‑board browse only).
- **Limitations:** EU‑heavy (German market); small absolute volume; no filtering — you take
  the whole board or nothing.

#### Himalayas — `https://himalayas.app/jobs/api`
- **Auth:** None.
- **Rate limits:** None hit; large archive discourages heavy paging.
- **Pagination:** `offset`/`limit`, but `limit` is **ignored server‑side** — always 20/page.
  Reports 90,000+ total; project caps at 150 pages = 3,000 newest.
- **Result limit:** Self‑capped at 3,000 (of 90k+ available).
- **Date filter:** Implicit (newest‑first ordering).
- **Country/Keyword/Company/Category filters:** Not used by this project, **but a richer
  `/jobs/api/search` endpoint exists** that supports keyword, country, seniority, employment
  type, company, and timezone filters — currently untapped.
- **Limitations:** Remote‑only board (every job is `remote:true`); fixed 20/page makes full
  pulls slow; only a recent slice is taken.

#### RemoteOK — `https://remoteok.com/api`
- **Auth:** None, but **requires a browser‑like `User‑Agent`** or returns 403.
- **Pagination:** None — `page` is silently ignored. Single JSON array of ~100 newest jobs
  (first element is a legal notice, skipped).
- **Result limit:** ~100.
- **Filters (all):** — (snapshot only).
- **Limitations:** Tiny volume; remote‑only; snapshot API.

#### Jobicy — `https://jobicy.com/api/v2/remote-jobs`
- **Auth:** None.
- **Pagination:** None — any page/offset param returns **HTTP 400**. `count` honored up to a
  hard cap of 100.
- **Result limit:** 100.
- **Filters:** `count` only in project; API also supports `geo`, `industry`, `tag` (unused).
- **Limitations:** Remote‑only; single snapshot of ~100.

#### The Muse — `https://www.themuse.com/api/public/jobs`
- **Auth:** None (an API key raises rate limits but isn't used here).
- **Rate limits:** Unauthenticated tier is throttled; public tier **hard‑rejects `page ≥ 100`
  with HTTP 400**.
- **Pagination:** `page`, fixed 20/page (`per_page` ignored). Reports 400,000+ jobs but only
  100 pages (2,000) reachable without a key.
- **Result limit:** 2,000 (unauth ceiling).
- **Filters:** API supports `category`, `level`, `location`, `company` params (project uses
  none — full browse). `location` filtering could target regions directly.
- **Limitations:** 2,000‑job hard ceiling without an API key; fixed page size.

#### Bundesagentur für Arbeit (Jobsuche) — `https://rest.arbeitsagentur.de/.../v4/jobs`
- **Auth:** `X‑API‑Key` header using the **well‑known public key** (`jobboerse-jobsuche`)
  shipped in the agency's own frontend — not a personal secret.
- **Rate limits:** None published; occasional transient timeouts (handled with 3× backoff).
- **Pagination:** `page`/`size`; **hard result window `page*size ≤ 10,000`** regardless of
  1,000,000+ reported. size=200 × 50 pages = 10,000 max.
- **Result limit:** 10,000.
- **Date filter:** `veroeffentlichtseit` (days) supported (unused).
- **Country/Location filters:** `wo`/`umkreis` (place + radius) supported (unused).
- **Keyword filter:** `was` supported (unused — broad browse).
- **Limitations:** Germany‑only; German‑language; 10k window; no dedicated remote flag
  (keyword heuristic used).

### Phase 2 — API‑key providers

#### Jooble — `POST https://jooble.org/api/{key}`
- **Auth:** API key **in the URL path** (registration required).
- **Rate/request limits:** Free plan has a daily request cap (not publicly numbered).
- **Pagination:** `page` + `ResultOnPage` (honored ≤100; >100 silently falls back to 30).
  Broad wildcard query's real result window empties around **page 12 (~1,100–1,200 jobs)**
  despite huge reported totals.
- **Result limit:** ~1,129 in practice for a wildcard query.
- **Date filter:** `datecreatedfrom` supported (unused).
- **Country/Location:** `location` supported (unused). **Keyword:** required (`keywords`;
  empty rejected — a single space is sent as a wildcard). **Company/Category:** —.
- **Limitations:** No true unscoped browse; usable window far smaller than reported totals;
  aggregator ⇒ cross‑provider duplication and redirect URLs (`jobviewtrack.com`).

#### USAJOBS — `https://data.usajobs.gov/api/search`
- **Auth:** Three headers — `Host`, `User-Agent` (registered email), `Authorization-Key`.
- **Rate limits:** "Rate limited per User‑Agent," no published number; kept modest.
- **Pagination:** `Page` + `ResultsPerPage` (tested to 5000/page; latency scales). **Hard
  result window = 10,000** (`SearchResultCountAll`).
- **Result limit:** 10,000.
- **Date filter:** `DatePosted` (days) supported (unused). **Keyword:** `Keyword`.
  **Location:** `LocationName`, `Radius`. **Category:** `JobCategoryCode`. **Company:** —
  (federal agencies only). All present in API; project browses broadly.
- **Limitations:** **US federal government only** (no private sector); genuine `remote` flag;
  10k window.

#### Adzuna — `https://api.adzuna.com/v1/api/jobs/{country}/search/{page}`
- **Auth:** `app_id` + `app_key` query params (registration).
- **Rate limits:** Free tier is call‑capped per day (unnumbered here); modest.
- **Pagination:** `page` path + `results_per_page` (silently capped at 50). **No pagination
  ceiling found** (tested to page 5000); project self‑caps at 40 pages (2,000).
- **Result limit:** 2,000 (self‑imposed; index is millions).
- **Date filter:** `max_days_old` supported (unused). **Country:** **required in URL path** —
  currently `us` only, but Adzuna supports ~16 countries (gb, ca, de, fr, nl, it, es, pl, br,
  in, au, sg, etc.). **Location/Keyword/Category:** `where`, `what`, `category` supported
  (unused). **Company:** `company` filter supported.
- **Limitations:** **Index is per‑country** — the project only queries the US, leaving every
  other Adzuna country (including Canada, UK, and several EU markets) unused despite the key
  already covering them.

#### Reed — `https://www.reed.co.uk/api/1.0/search`
- **Auth:** HTTP Basic (API key as username, empty password).
- **Rate limits:** None hit.
- **Pagination:** `resultsToTake` (≤100) + `resultsToSkip`. **Hard boundary ~9,900:** beyond
  it returns **HTTP 500** (not empty); project caps at 90 pages (9,000).
- **Result limit:** ~9,000.
- **Date filter:** — (none in search response). **Location:** `locationName` + `distance`.
  **Keyword:** `keywords`. **Company:** — . **Category:** — (no category field at all, so
  `tags` always empty for Reed).
- **Limitations:** **UK‑only**; no tags/category data; 500 error at the window boundary.

#### SerpApi (Google Jobs) — `https://serpapi.com/search?engine=google_jobs`
- **Auth:** `api_key` query param. **Metered/paid — free plan 250 searches/month.**
- **Rate/request limits:** Each page = one billable search; project caps at 5 pages (50 jobs).
- **Pagination:** `next_page_token`, ≤10 jobs/page.
- **Result limit:** 50/run (deliberately tiny to conserve quota).
- **Date filter:** only relative (`posted_at` = "3 days ago", converted approximately).
  **Location/Keyword:** `location`, `q` (required). **Company/Category:** via `q` only.
- **Limitations:** Cost per request; only relative dates; genuine `work_from_home` flag;
  scrapes Google Jobs (ToS/stability considerations).

#### OpenWeb Ninja (JSearch) — `https://api.openwebninja.com/jsearch/search-v2`
- **Auth:** `x-api-key` header. **Metered/paid — free plan 200 requests/month.**
- **Pagination:** cursor (`cursor` echoed back); project caps at 5 pages.
- **Result limit:** ~50/run (quota conservation).
- **Date filter:** `date_posted` param supported by API (unused). **Location:** `country`,
  `location`. **Keyword:** `query` (required). **Company/Category:** via query.
- **Limitations:** Cost; low free quota; JS‑rendered docs; genuine `job_is_remote` flag.

#### Careerjet — `https://search.api.careerjet.net/v4/query`
- **Auth:** HTTP Basic (API key as username). **Also requires:** the calling server IP to be
  **allowlisted** on Careerjet's dashboard, **and** a `Referer` header (any value) — both
  undocumented, found via live testing.
- **Pagination:** `page`; `page_size` documented but **silently ignored** (always 20/page).
  No ceiling found; project caps at 100 pages (2,000).
- **Result limit:** 2,000 (self‑imposed; 320,000+ matches reported).
- **Date filter:** — . **Location:** `location`. **Keyword:** `keywords` (required).
  **Country:** via localized `locale_code`/`location`. **Category/Company:** —.
- **Limitations:** IP‑allowlist + Referer gotchas; RFC 2822 dates; no category (empty `tags`);
  aggregator ⇒ cross‑provider dup risk.

#### TheirStack — `POST https://api.theirstack.com/v1/jobs/search`
- **Auth:** `Authorization: Bearer`. **Bills 1 credit PER JOB RETURNED** (unique cost model).
- **Pagination:** 0‑indexed `page` + `limit` (no documented max); project trims to `MAX_JOBS=50`.
- **Result limit:** 50/run by design; **currently 0** — the account's plan returns **HTTP 402
  Payment Required**, so the source contributes nothing (handled gracefully).
- **Date filter:** `posted_at_max_age_days` / `posted_at_gte/lte` (at least one filter is
  **required** — no unfiltered browse). **Company/Location/Category:** rich filter set
  available.
- **Limitations:** Cost scales with jobs, not requests; requires a filter; **plan‑gated off
  entirely right now.**

### Phase 3 — ATS providers (company‑based; one board per curated company)

Shared characteristics: each is **not a global index** — it fetches a hand‑curated list of
company boards verified live before inclusion. Coverage is therefore a function of the curated
company list, not of any query.

#### Greenhouse — `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs`
- **Auth:** None. `content=true` adds departments (tags) + description free.
- **Pagination:** None — one request returns a company's **entire** board.
- **Result limit:** Whole board per company (largest ~491). **Filters:** — (per‑company only).
- **Company list:** ~230 slugs. `company_name` provided directly.
- **Limitations:** Coverage bounded by curated slug list; many big names have left Greenhouse
  or use non‑obvious slugs; no remote flag (keyword heuristic).

#### Lever — `https://api.lever.co/v0/postings/{slug}?mode=json`
- **Auth:** None for GET.
- **Pagination:** `skip`/`limit` (real), but every company returns its full list in one page
  in practice.
- **Result limit:** Whole board per company. **Filters:** — .
- **Company list:** ~180 slugs. No company‑name field ⇒ derived from slug. Genuine
  `workplaceType` (remote/hybrid/onsite).
- **Limitations:** Skews smaller/venture‑backed companies; **big multi‑location retail boards
  (BoxLunch etc.) inflate near‑duplicate title counts** (see §3).

#### Ashby — `https://api.ashbyhq.com/posting-api/job-board/{slug}`
- **Auth:** None.
- **Pagination:** None — single‑shot per company (largest ~593).
- **Company list:** 102 verified slugs (of ~350 tried). No company‑name field ⇒ manual
  slug→name map. Genuine `isRemote` boolean.
- **Limitations:** Customer base skews growth‑stage AI/SaaS/FinTech; thin in
  manufacturing/logistics/consulting.

#### SmartRecruiters — `https://api.smartrecruiters.com/v1/companies/{slug}/postings`
- **Auth:** None on this public posting endpoint (CORS `*`). (Distinct from the token‑gated
  partner feed.)
- **Pagination:** `offset`/`limit` (100/page), **real and required** — some boards are huge
  (Domino's 24,445; Bosch 4,647).
- **Result limit:** Whole board per company. Unknown slug returns **HTTP 200 with
  `totalFound:0`** (not 404), so verification checks `totalFound > 0`.
- **Company list:** 100 verified slugs. `company:{identifier,name}` provided. Genuine
  `location.remote` boolean. URL constructed from identifier + posting id.
- **Limitations:** **This one provider is 41.8% of the entire dataset**, dominating regional
  and freshness distributions and driving most large multi‑location duplicate clusters.

#### Workable — `https://apply.workable.com/api/v1/widget/accounts/{slug}`
- **Auth:** None (public widget API; distinct from the token‑gated SPI API).
- **Pagination:** None — single‑shot per company (largest ~1,718). Unknown slug 404s.
- **Company list:** 89 verified slugs. Account‑level `name` gives company; genuine
  `telecommuting` boolean.
- **Limitations:** Skews SMB/staffing/consulting; **a single job open in multiple cities can
  repeat the same URL** (correctly collapsed by existing URL dedup).

#### Teamtailor — `https://{subdomain}.teamtailor.com/jobs.rss` (public RSS)
- **Auth:** None — the documented Web API needs a per‑company token, so a **public RSS feed**
  is used instead.
- **Pagination:** None — full published list per feed (largest ~95).
- **Company list:** 25 verified subdomains (some only resolve under `.na.teamtailor.com`).
  Channel `<title>` gives company; `<remoteStatus>` field ("fully" ⇒ remote); RFC 822 dates.
- **Limitations:** Smallest ATS contributor (~474); relies on RSS, not a real API; subdomain
  discovery is manual.

### 4.1 Cross‑cutting limitations

- **Curated‑list ceiling:** six of 20 sources (all ATS) only see hand‑picked companies —
  coverage grows only by manually adding verified slugs.
- **Hard result windows:** several sources cap at 10,000 (USAJOBS, Bundesagentur) or ~9,900
  (Reed) regardless of true inventory.
- **Metered/paid sources** (SerpApi, OpenWeb Ninja, TheirStack) are deliberately throttled to
  ~50 jobs/run and contribute little; TheirStack currently contributes zero (402).
- **Broad‑browse wildcards** (Jooble, Careerjet, SerpApi, OpenWeb Ninja) waste the providers'
  real strength — their filtering — and maximize cross‑provider duplication.
- **`remote` and `tags` quality varies** — genuine booleans on some sources, keyword
  heuristics on others; Reed/Careerjet supply no categories at all.

---

## SECTION 5 — Regional APIs (additional FREE / PUBLIC candidates)

Research into sources that could strengthen the six target regions. "Should add?" is a
recommendation for the later implementation pass, not an action taken here.

### Canada

**1. Adzuna — Canada index (`country = ca`)** — *(already reachable with the existing key)*
- **Coverage:** Broad private‑sector Canadian postings, nationwide.
- **Auth:** Existing `app_id`/`app_key` (already configured).
- **Docs:** https://developer.adzuna.com/
- **Advantages:** Zero new credentials — the current Adzuna source only queries `us`; adding a
  `ca` pass (or iterating a country list) is a config change, not a new integration. Same
  normalization already written.
- **Limitations:** Same per‑country 2,000 self‑cap and free‑tier call limits as the US pass.
- **Should add?** **Yes — highest ROI Canada option.** Canada is the weakest target region
  (2.2%) and this is nearly free to enable.

**2. Job Bank (Government of Canada) — XML feed / Open Government dataset**
- **Coverage:** The national public job board — very broad Canadian coverage incl. NOC codes,
  salary, location.
- **Auth:** XML feed requires **requesting access** from Job Bank (partner arrangement); a
  **monthly bulk dataset** is freely downloadable from the Open Government Portal with no auth.
- **Docs:** https://www.jobbank.gc.ca/ ; https://open.canada.ca/data (dataset
  `ea639e28-c0fc-48bf-b5dd-b8899bd43072`).
- **Advantages:** Authoritative, huge Canadian volume, structured fields, free.
- **Limitations:** No modern real‑time REST API; XML feed needs approval; the open dataset is
  **monthly** (poor freshness) and bulk (needs its own ingestion path).
- **Should add?** **Maybe (second priority).** Great coverage but the freshness/format friction
  is real; prefer Adzuna‑CA first, consider the open dataset for breadth.

**3. Lightcast Jobs — Canada** — commercial/paid API. **Should add? No** (paid; out of scope
for a free‑source project).

### United States

**1. The Muse `location` filter / Adzuna already `us`** — *(already integrated; underused)*
- Adzuna‑US and The Muse already contribute; The Muse's `location` param could target US
  metros specifically. **Should add? Already present** — recommend *using the filters* rather
  than a new source.

**2. RemoteJobs.org API — `https://remotejobs.org/api-access`**
- **Coverage:** Remote jobs (US‑heavy), filterable by category/type/keyword.
- **Auth:** **None** — no signup, no key.
- **Docs:** https://remotejobs.org/api-access
- **Advantages:** Free, no key, JSON, complements the existing remote feeds.
- **Limitations:** Remote‑only (won't help on‑site US coverage); overlaps RemoteOK/Himalayas ⇒
  duplication.
- **Should add?** **Low priority** — US on‑site coverage is already strong via ATS; marginal.

**3. NLx / DirectEmployers / state workforce feeds** — large aggregated US public‑workforce
inventory, but access is partnership‑gated. **Should add? No** (not openly public).

*US is already the best‑covered region (51%); new US sources add duplication more than reach.*

### United Kingdom

**1. Adzuna — GB index (`country = gb`)** — *(existing key)*
- **Coverage:** Broad UK private sector. **Auth:** existing key. **Docs:** as above.
- **Advantages:** Free to enable; diversifies beyond Reed (currently the *only* real UK
  source, 5.8% of the whole dataset — a single point of failure).
- **Limitations:** Overlaps Reed ⇒ dedup needed.
- **Should add?** **Yes** — cheap resilience for a region that currently rides on one provider.

**2. GOV.UK "Find a job" service** — the successor to Universal Jobmatch.
- **Coverage:** Large UK public job board. **Auth:** historically offered employer/partner
  data feeds rather than an open developer REST API.
- **Docs:** https://findajob.dwp.gov.uk/
- **Advantages:** Authoritative, high volume, free.
- **Limitations:** No well‑documented open pull API for third parties; access is feed/partner
  based — needs verification before committing.
- **Should add?** **Investigate** — promising but access model unconfirmed.

**3. Careerjet UK locale** — *(Careerjet already integrated)* — could run a UK‑scoped locale
pass. **Should add? Optional** (duplication risk).

### Europe

**1. Adzuna — multi‑country (de, fr, nl, it, es, pl, at …)** — *(existing key)*
- **Coverage:** Country‑by‑country private‑sector across most of the EU.
- **Auth:** existing key. **Advantages:** One integration already written; iterating a country
  list instantly broadens Europe beyond the German‑agency dominance. **Limitations:** per‑country
  2,000 cap; free‑tier call budget across many countries.
- **Should add?** **Yes — top European lever.** Europe is currently 56% Germany; Adzuna spreads
  it across France/Spain/NL/Poland/etc. cheaply.

**2. France Travail (ex‑Pôle emploi) — "Offres d'emploi" API**
- **Coverage:** Very large French national job board.
- **Auth:** Free, but requires **registration + OAuth2** on the France Travail developer portal.
- **Docs:** https://francetravail.io/
- **Advantages:** Authoritative, huge French volume, rich filters (location, ROME code, date),
  free.
- **Limitations:** OAuth flow + app registration; French‑language; France‑only.
- **Should add?** **Yes (medium priority)** — France is under‑represented (1.4%) and this is the
  authoritative national source.

**3. EURES (European Employment Services) — `eures.europa.eu`**
- **Coverage:** Pan‑EU, ~3M jobs across member states.
- **Auth:** No clean, openly documented public REST API — the input/export APIs are for member
  national services (e.g. the Norwegian NAV integration); third‑party access is largely via
  scrapers (Apify etc.).
- **Docs:** https://eures.europa.eu/ (portal); national‑service integration specs on GitHub.
- **Advantages:** Enormous breadth if accessible.
- **Limitations:** **No supported public pull API** for an aggregator; scraping only ⇒ fragile
  and ToS‑questionable.
- **Should add?** **No (not as a first‑class source)** — revisit only if an official partner
  feed becomes available.

**4. Austria AMS / other national agencies** — AMS data already appears (`jobs.ams.at`,
`jobexport.de`) incidentally. National agency APIs (Austria, Netherlands, etc.) exist but are
individually integrated per country. **Should add? Selectively**, after Adzuna‑EU + France
Travail.

### Singapore

**1. MyCareersFuture (GovTech Singapore) — `https://api.mycareersfuture.gov.sg/v2/jobs`**
- **Coverage:** Singapore's national government job portal — ~80,000–90,000 active listings,
  20+ structured fields (SGD salary min/max, employment type, seniority, district/region,
  skills, employer UEN).
- **Auth:** **None** — public, no key/account, 100 jobs/page paginated.
- **Docs:** https://www.mycareersfuture.gov.sg/ (public v2 endpoint; community‑documented).
- **Advantages:** **Free, no auth, high volume, richly structured, authoritative** for
  Singapore — by far the strongest single fix for the weak SG/SEA region.
- **Limitations:** Singapore‑only; unofficial/undocumented public endpoint (could change);
  need to confirm ToS for aggregation.
- **Should add?** **Yes — top SEA priority.** Directly converts the thinnest target region into
  a well‑covered one with a single no‑auth integration.

### Southeast Asia (beyond Singapore)

**1. Adzuna — Singapore (`sg`)** — if the SG index is covered by the plan, it adds SG private
sector; SEA beyond that (MY/ID/PH/TH/VN) is **not** in Adzuna's country set. **Should add?**
Enable `sg` if available.

**2. JobStreet / Jobsdb (SEEK group)** — dominant SEA boards (MY, ID, PH, SG, TH, VN).
- **Auth:** **No public API** — SEEK exposes partner APIs only; third‑party access is scraping.
- **Advantages:** Would massively expand SEA if accessible. **Limitations:** No open API;
  scraping is fragile/ToS‑risky.
- **Should add?** **No** (no public API).

**3. Kalibrr (PH/ID)** and similar regional boards — mostly no open public API.
- **Should add?** **No** unless a documented feed is found.

**4. Curated ATS expansion (Greenhouse/Lever/Workable) for SEA‑headquartered companies** —
e.g. Grab, Sea/Shopee, GoTo, Carousell.
- **Advantages:** Uses the existing, proven ATS integrations — just add verified slugs.
- **Should add?** **Yes (complementary)** — the realistic way to deepen SEA beyond Singapore
  without a regional API existing.

### LATAM

**1. Adzuna — Brazil (`br`) and Mexico (`mx`)** — *(existing key)*
- **Coverage:** Broad private sector in the two largest LATAM markets.
- **Auth:** existing key. **Advantages:** Free to enable; adds real *in‑country* LATAM volume
  (currently most LATAM jobs are remote‑nearshore, not location‑specific). **Limitations:**
  only BR/MX in Adzuna's set; per‑country cap.
- **Should add?** **Yes — top LATAM lever.**

**2. Himalayas `/jobs/api/search` with `country`/region filter** — *(Himalayas already
integrated; richer endpoint unused)*
- **Advantages:** The project already talks to Himalayas; switching/adding the search endpoint
  unlocks country‑filtered remote‑LATAM queries with no new provider.
- **Limitations:** Remote‑only; overlaps existing Himalayas pull.
- **Should add?** **Yes (cheap)** — reuse an existing source better.

**3. Curated ATS expansion for LATAM companies** (Nubank, MercadoLibre, Rappi, dLocal — some
already present via Greenhouse/Lever) — add verified slugs. **Should add? Yes (complementary).**

**4. Regional boards (Computrabajo, Bumeran, Get on Board)** — Get on Board has a tech‑focused
LATAM board; Computrabajo/Bumeran are large but **no documented open API**. **Should add?**
Only if a public feed is confirmed (Get on Board worth investigating; the others are
scraping‑only ⇒ no).

### 5.1 Regional‑API summary

| Region | Best free/public add | Effort | Priority |
|---|---|---|---|
| Canada | Adzuna `ca` (existing key) | Trivial (config) | **High** |
| Canada | Job Bank open dataset | Medium (bulk/ingest) | Medium |
| UK | Adzuna `gb` (de‑risk single‑source Reed) | Trivial | **High** |
| UK | GOV.UK Find a Job feed | Unknown (verify access) | Investigate |
| Europe | Adzuna multi‑country (fr/es/nl/pl/it/at) | Trivial | **High** |
| Europe | France Travail API | Medium (OAuth) | Medium |
| Europe | EURES | — | Not now (no public API) |
| Singapore | MyCareersFuture public API | Low (no auth) | **High** |
| SEA (rest) | ATS slug expansion (Grab/Sea/GoTo…) | Low | Medium |
| SEA (rest) | JobStreet/Jobsdb | — | Not now (no public API) |
| LATAM | Adzuna `br` + `mx` | Trivial | **High** |
| LATAM | Himalayas search endpoint (country filter) | Low | Medium |

**Headline:** the **single existing Adzuna key already unlocks Canada, the UK, most of Europe,
and the two biggest LATAM markets** — it is currently querying only `us`. That plus the no‑auth
**MyCareersFuture** endpoint would materially strengthen five of the six target regions with
minimal new integration work.

---

## SECTION 6 — Recommendations (analysis only — nothing implemented)

### 6.1 How to improve coverage
1. **Use Adzuna's per‑country index instead of `us` only.** One already‑integrated, already‑keyed
   source can add Canada (`ca`), UK (`gb`), Germany/France/Spain/Netherlands/Poland/Italy/Austria,
   and Brazil/Mexico. This is the **highest‑leverage change in the entire document** and touches
   only configuration‑level breadth, not the pipeline.
2. **Add MyCareersFuture (Singapore)** — free, no auth, ~80k structured jobs — to fix the weakest
   region directly.
3. **Add France Travail** (medium effort, OAuth) for authoritative French coverage.
4. **Grow the ATS curated lists toward under‑covered regions** — add verified Canadian, SEA, and
   LATAM company slugs to Greenhouse/Lever/Workable, which already work and need only new slugs.
5. **Reduce over‑reliance on SmartRecruiters** (41.8% of data). It's fine to keep, but coverage
   *balance* improves by growing everything else, not by adding more enterprise‑ATS retail volume.

### 6.2 How to improve freshness
1. **Schedule regular re‑runs** (daily for the whole pipeline; more often for the small fast
   feeds). Freshness is dominated by time‑since‑fetch; this is the #1 lever.
2. **Record a `fetched_at`/run timestamp** and surface "data as of X" so age is honest and
   computable.
3. **Apply provider‑side recency filters** where available (Adzuna `max_days_old`, USAJOBS
   `DatePosted`, Jooble `datecreatedfrom`, TheirStack `posted_at_max_age_days`, The Muse
   ordering) to stop ingesting the deep‑stale tail (14% of data is >1 year old).
4. **Cap or down‑weight very old ATS requisitions** — the >90‑day tail (28.9%) is almost entirely
   large ATS boards.
5. **Expose a "last N days" filter/badge in the UI** (the `posted` field already supports it).

### 6.3 How to reduce duplicates
1. **Keep exact‑URL dedup as the backbone** — it already yields 0 URL duplicates and 0 false
   positives.
2. **Normalize URLs before hashing** (lowercase host, strip fragments + `utm_*`/tracking params)
   to catch cheap cross‑variant duplicates, especially from aggregator wrappers.
3. **Add a conservative, location‑aware composite/fuzzy pass** for cross‑provider dupes: block on
   normalized `company`, then require close `title` **and** `location` match before collapsing.
4. **Never dedup on `title+company` alone** — proven to erase ~35,000 legitimate multi‑location
   roles (BoxLunch/Domino's/TSA pattern).
5. **Prefer targeted queries over wildcard browses** on aggregators (Jooble/Careerjet/SerpApi/
   OpenWeb Ninja) to reduce cross‑provider overlap at the source.

### 6.4 How to increase useful jobs
1. **Trade wildcard breadth for filtered relevance** on the aggregators — targeted region/keyword
   queries return fewer but more useful, less‑duplicated jobs than a space‑wildcard browse.
2. **Improve location normalization** so the 18.2% "unclassified" shrinks — better location data
   makes filters, regional counts, and any map feature actually work.
3. **Backfill `tags` where missing** (7.5% empty; Reed/Careerjet supply none) from title/keyword
   inference, so search/filtering has something to match on.
4. **Consider adding `description` to the schema** — it unlocks far better search *and* enables
   description‑based dedup later.
5. **Prune the deep‑stale/expired tail** so "useful" isn't diluted by year‑old dead listings.

### 6.5 How to stay within API limits
1. **Respect the hard result windows** already discovered and encoded (USAJOBS/Bundesagentur
   10,000; Reed ~9,900) — don't page past them.
2. **Keep metered sources capped** (SerpApi 250/mo, OpenWeb Ninja 200/mo, TheirStack per‑job
   billing) at their current small budgets; treat them as garnish, not backbone. **TheirStack is
   plan‑gated to 402 right now — leave it graceful‑skip until the plan changes.**
3. **Budget Adzuna calls across countries** — if adding many `country` passes, respect the free
   tier's daily call cap by capping pages per country (the existing 40‑page/2,000‑job self‑cap is
   a good template).
4. **Reuse the existing retry/backoff helper** (`request_with_retry`, 429/5xx aware) for any new
   source, and keep per‑company fault isolation so one bad board never aborts a run.
5. **Cache/stagger ATS company fetches** — hundreds of per‑company requests per run; spacing them
   and reusing sessions avoids tripping provider throttles as the curated lists grow.
6. **Prefer no‑auth/high‑ceiling sources first** (Adzuna multi‑country, MyCareersFuture, ATS slug
   expansion) before spending scarce metered quota.

---

## Sources (external research)

- Canada Job Bank & Open Government dataset — https://www.jobbank.gc.ca/ ,
  https://open.canada.ca/data/en/dataset/ea639e28-c0fc-48bf-b5dd-b8899bd43072
- EURES portal — https://eures.europa.eu/
- MyCareersFuture (Singapore, GovTech) — https://www.mycareersfuture.gov.sg/ ,
  https://www.developer.tech.gov.sg/products/categories/data-and-apis/
- Adzuna developer docs — https://developer.adzuna.com/
- France Travail (ex‑Pôle emploi) developer portal — https://francetravail.io/
- Himalayas Jobs API — https://himalayas.app/api
- RemoteJobs.org free API — https://remotejobs.org/api-access
- ATS public job‑posting APIs overview — https://cavuno.com/blog/ats-platforms-public-job-posting-apis
- Provider behavior for Sections 4/6 is otherwise drawn from the live‑tested implementation
  notes in each `sources/*.py` module of this repository.

---
---

# EXPANSION RESEARCH (Sections 7–15)

*Appended as a second research pass ahead of implementation. Sections 1–6 above are
unchanged. Everything below is analysis and market research only — no code, `jobs.py`,
`jobs.json`, reports, or charts were created or modified, and no recommendation was
implemented. Where an external API is named, its availability was verified against official
documentation or the provider's own site where possible; sources are unverifiable or
uncertain claims are explicitly flagged rather than assumed.*

---

## SECTION 7 — Executive Summary

*(Written for engineering managers — readable in under two minutes.)*

**What we have today.** The platform aggregates **155,794 unique jobs** from **20 integrated
providers** (6 no‑auth APIs, 8 API‑key APIs, 6 company‑based ATS sources) into one normalized
schema, deduplicated by URL, and served to a static frontend. Nineteen of the 20 sources
currently contribute (TheirStack is plan‑gated off).

**Regional coverage.** Coverage is **broad but heavily skewed to the United States (51%)**.
The six target regions together account for ~81% of jobs: US 51%, Europe 14% (mostly Germany),
UK 6.6% (essentially all Reed), LATAM 4.5% (mostly remote/nearshore, not in‑country),
Singapore/SEA 3.0% (incidental), and **Canada just 2.2% — the weakest**. A further 18% is
non‑target markets (India, China, Australia, Gulf) or unclassifiable location text. **A single
provider, SmartRecruiters, is 41.8% of the entire dataset** — the balance of the data is
determined more by our curated company lists than by any global crawl.

**Freshness.** At collection time the data was reasonable — **~54% of jobs were posted within
the last 30 days** — but it degrades fast because the dataset is a **static snapshot with no
refresh schedule and no expiry**. **46% is older than 30 days, 29% older than 90 days, and 14%
older than a year** (tail back to 2009), concentrated in the large enterprise ATS boards.

**Duplicates.** URL‑level deduplication is **working perfectly (0 duplicate URLs, 0 empty
URLs)**. Apparent title+company "duplicates" (35k) are overwhelmingly **legitimately distinct
multi‑location roles**, so no aggressive dedup is warranted; the real, smaller risk is
cross‑provider overlap between aggregators.

**Strengths.** Clean modular architecture (add a source = one file + one line); strong US and
German coverage; genuine breadth across general APIs, government boards, and 6 ATS platforms;
robust error isolation and retry; a normalized 7‑field schema with 99.99% date coverage.

**Weaknesses.** US/enterprise over‑concentration; Canada and SEA under‑served; UK is a
single‑source dependency (Reed); ~46% stale data with no auto‑expiry; ~18% of locations
unclassifiable; only ~11% remote; metered sources contribute almost nothing; **no India source
at all** despite India being the 6th‑largest country already present incidentally.

**Top opportunities.** (1) **Switch Adzuna from `us`‑only to multi‑country** — one existing,
already‑keyed integration unlocks Canada, UK, most of Europe, and Brazil/Mexico. (2) **Add
MyCareersFuture (Singapore)** — free, no‑auth, ~80k structured jobs. (3) **Schedule regular
re‑runs + record `fetched_at`** to fix freshness. (4) **Add India** via the National Career
Service open dataset and/or a commercial ATS‑feed API. (5) **De‑risk the UK** with a second
source. These are mostly low‑effort, high‑yield, and legally clean.

---

## SECTION 8 — Current Jobs Summary

Freshness measured against the dataset's **collection date (2026‑07‑03**, the newest `posted`
value present), which is the fair reference for "how current the jobs were when fetched."
Buckets below are **cumulative** ("within N days" includes everything fresher).

| Window (age at collection) | Jobs (in window, exclusive) | Cumulative "within" | Cumulative % |
|---|---:|---:|---:|
| Within 24 hours | 24,052 | 24,052 | 15.4% |
| Within 3 days | +6,582 | 30,634 | 19.7% |
| Within 7 days | +11,884 | 42,518 | 27.3% |
| Within 14 days | +24,610 | 67,128 | 43.1% |
| Within 30 days | +16,949 | 84,077 | 54.0% |
| Older than 30 days | 71,702 | — | 46.0% |
| Unknown / unparseable date | 15 | — | 0.0% |

**Headline calculations**
- **Total current jobs (≤ 30 days): 84,077 → 54.0% of the dataset.**
- **Stale jobs (> 30 days, incl. unknown): 71,717 → 46.0%.**
- Deep‑stale tail: **28.9% > 90 days, 19.0% > 180 days, 14.0% > 365 days.**

**What this indicates about dataset health.** At the moment of collection the dataset was
*moderately healthy* — a slim majority of jobs were fresh, and 27% were within a week. But the
**46% stale fraction is a structural problem, not a collection accident**: the enterprise ATS
boards (SmartRecruiters/Greenhouse/Lever) return every currently‑open requisition, including
evergreen, perpetual, and hard‑to‑fill roles that have been open for months. Because the
snapshot has **no expiry mechanism**, these accumulate, and every day after collection the
whole file ages further with no offsetting refresh. A user browsing today (3 days post‑fetch)
already sees "0 jobs in the last 24h." The dataset is therefore **fit for a periodic bulk
board, but not yet for a freshness‑sensitive product** without scheduling and expiry.

**Practical methods to auto‑detect expired / inactive jobs in future syncs** *(research only)*
1. **Presence diffing across runs (most reliable).** Keep a per‑job `first_seen`/`last_seen`.
   If a URL that appeared in run *N* is absent in run *N+1*, mark it `expired`. For ATS boards
   that return the *entire* current board each run, absence is a definitive "closed" signal.
2. **HTTP liveness probe.** Periodically HEAD/GET the job URL; `404/410/redirect‑to‑listing`
   ⇒ expired. Cheap for a sample, heavier at full scale (rate‑limit/backoff needed).
3. **Provider expiry fields where available.** Some APIs expose validity windows (e.g. Adzuna
   `max_days_old`, USAJOBS `ApplicationCloseDate`, Bundesagentur publication dates, ATS
   `status` flags). Honor them at ingest.
4. **Age‑based soft expiry.** Flag/hide anything older than a configurable threshold (e.g. 45
   days) as "likely inactive" even without a hard signal — turns the stale tail into a filter.
5. **Content‑hash change detection.** If a re‑fetched posting's body/title/status changes to a
   "closed"/"no longer accepting" state, expire it.
6. **Sitemap/board‑count reconciliation.** Compare the count returned by an ATS board this run
   vs last; a large drop for a company flags mass closures to re‑verify.

Recommended combination: **(1) presence diffing as the backbone**, augmented by **(3) provider
fields** and **(4) age‑based soft expiry**, with **(2) liveness probing** reserved for spot
checks. This requires persisting run‑to‑run state (a small index keyed by normalized URL),
which the current single‑file snapshot does not yet do.

---

## SECTION 9 — API Priority Matrix (existing providers)

Legend — **Free/Paid**: F=free/no‑cost, K=free but key required, $=metered/paid.
**Usefulness / Expansion** rated Low→High. **Max realistic jobs** = observed or capped ceiling
per run. Filters: ✓=supported by API (✓* = supported but unused by our integration; ✗=not
available).

| Provider | Region | Auth | Cost | Max jobs | Pagination | Rate limit | Date flt | Loc flt | Company flt | Category flt | Usefulness | Expansion | **Priority** |
|---|---|---|---|---:|---|---|:--:|:--:|:--:|:--:|---|---|---|
| SmartRecruiters | Global (co‑list) | None | F | Whole boards (65k now) | offset/limit | none hit | ✗ | ✗ | n/a | ✗ | High | High (add slugs) | **Critical** |
| Adzuna | Per‑country | Key | K | 2k/country (self‑cap) | page+size(50) | daily cap | ✓* | ✓* | ✓* | ✓* | High | **Very High** | **Critical** |
| Lever | Global (co‑list) | None | F | Whole boards (18k) | skip/limit | none hit | ✗ | ✗ | n/a | ✗ | High | High (add slugs) | **High** |
| Greenhouse | Global (co‑list) | None | F | Whole boards (15k) | none | none hit | ✗ | ✗ | n/a | ✗ (depts) | High | High (add slugs) | **High** |
| USAJOBS | US federal | 3 headers | K | 10,000 | page+size | per‑UA (soft) | ✓* | ✓* | ✗ | ✓* | High | Low (federal only) | **High** |
| Reed | UK | Basic key | K | ~9,000 | take/skip | none hit | ✗ | ✓* | ✗ | ✗ | High | Medium | **High** |
| Bundesagentur | Germany | Public key | F | 10,000 | page+size | none pub | ✓* | ✓* | ✗ | ✗ | High | Medium (regions) | **High** |
| Ashby | Global (co‑list) | None | F | Whole boards (5k) | none | none hit | ✗ | ✗ | n/a | ✗ | Medium | Medium | **Medium** |
| Workable | Global (co‑list) | None | F | Whole boards (4k) | none | none hit | ✗ | ✗ | n/a | ✗ | Medium | Medium | **Medium** |
| Himalayas | Remote/global | None | F | 3,000 (of 90k) | offset(20) | none hit | ✓* | ✓* | ✓* | ✓* | Medium | Medium (search API) | **Medium** |
| The Muse | Global | None(key opt) | F | 2,000 (unauth cap) | page(20) | throttled | ✗ | ✓* | ✓* | ✓* | Medium | Medium (key raises cap) | **Medium** |
| Jooble | Global | Path key | K | ~1,100 | page+size | daily cap | ✓* | ✓* | ✗ | ✗ | Medium | Medium | **Medium** |
| Careerjet | Global | Basic+IP | K | 2,000 | page(20) | none hit | ✗ | ✓* | ✗ | ✗ | Medium | Medium | **Medium** |
| Arbeitnow | EU | None | F | ~930 | cursor(100) | none | ✗ | ✗ | ✗ | ✗ | Low | Low | **Low** |
| RemoteOK | Remote | UA header | F | ~100 | none | none | ✗ | ✗ | ✗ | ✗ | Low | Low | **Low** |
| Jobicy | Remote | None | F | 100 | none | none | ✗ | ✓* | ✗ | ✓* | Low | Low | **Low** |
| Teamtailor | Global (co‑list) | None (RSS) | F | ~474 | none | none | ✗ | ✗ | n/a | ✗ | Low | Low | **Low** |
| SerpApi | Global | Key | $ | 50/run | token(10) | 250/mo | ~rel | ✓* | ✗ | ✗ | Low | Low (cost) | **Low** |
| OpenWeb Ninja | Global | Key | $ | ~50/run | cursor | 200/mo | ✓* | ✓* | ✗ | ✗ | Low | Low (cost) | **Low** |
| TheirStack | Global | Bearer | $ | 0 now (402) | page+limit | per‑job bill | ✓ req | ✓* | ✓* | ✗ | Low | Low (plan‑gated) | **Low** |

**Reasoning for the priority tiers**

- **Critical — SmartRecruiters & Adzuna.** SmartRecruiters is *already* the backbone (41.8%);
  keeping it healthy and extending its slug list is business‑critical. Adzuna is Critical for a
  different reason: it is the **single highest‑leverage untapped asset** — one keyed integration
  that can immediately add Canada, UK, Europe, and LATAM by iterating the country path.
- **High — Lever, Greenhouse, USAJOBS, Reed, Bundesagentur.** Each is a large, free/near‑free
  backbone for a major region (Lever/Greenhouse = global tech volume; USAJOBS = authoritative US
  federal; Reed = the *only* real UK source; Bundesagentur = the German backbone). High volume,
  reliable, but bounded (curated lists, federal‑only, single‑country, or hard windows).
- **Medium — Ashby, Workable, Himalayas, The Muse, Jooble, Careerjet.** Solid, free/keyed
  contributors that add real breadth but are individually smaller, overlap other sources
  (aggregators), or have untapped upside (Himalayas search endpoint, The Muse API key).
- **Low — Arbeitnow, RemoteOK, Jobicy, Teamtailor, SerpApi, OpenWeb Ninja, TheirStack.** Small
  absolute volume (≤~1k), or metered/paid sources deliberately throttled to ~50 jobs, or (in
  TheirStack's case) currently contributing zero. Keep them (cheap breadth / genuine‑remote
  flags) but they are not where growth comes from.

---

## SECTION 10 — Additional APIs by Region

Exhaustive market survey per target region. Each candidate is classified by **availability
type** using this taxonomy: **Official Public API · Partner/Employer API · Enterprise/Commercial
API · Free API · Free‑Tier API · Free‑Trial API · RapidAPI Wrapper · RSS/XML Feed · ATS
Integration · Open Dataset · No Public API · Scraping Required · Not Recommended.**

**Verification note:** availability was checked against official docs/provider sites where
possible (citations in the Sources list at the end of this document). Volume/freshness figures
are best‑estimate ranges; anything unverified is flagged "(unverified)". **No API is assumed to
exist without evidence** — several well‑known boards are explicitly recorded as having *no*
public API.

For readability each region is a table of the core decision columns, followed by notes on the
recommended candidates covering the remaining attributes (docs, rate limits, pagination,
filters, legal, viability). Providers already integrated are omitted here (see §4/§9) except
where an *expansion* of that provider is the recommendation.

### 10.1 Canada

| Source | Availability type | Coverage / countries | Auth | Pricing / free tier | Est. volume | Freshness | Integration ease | **Recommendation** |
|---|---|---|---|---|---|---|---|---|
| Adzuna `ca` | Free‑Tier API (existing key) | Broad private sector, CA | app_id/key | Free tier (daily cap) | 10k–100k+ | Good | **Trivial** (config) | **Add — top priority** |
| Job Bank (ESDC) XML feed | Partner/Employer API | National, all CA | Access request | Free | 100k+ | Good (live) | Medium (approval) | Investigate/Add |
| Job Bank Open Dataset | Open Dataset | National, all CA | None | Free | 100k+ monthly | Poor (monthly) | Medium (bulk ETL) | Maybe (breadth) |
| Jobbank "Job Match"/NLx | Partner API | CA + US (NLx) | Partner approval | Free (gated) | large | Good | Hard (governance) | Low |
| Eluta / Workopolis / Indeed CA | No Public API / Scraping | CA | — | — | large | — | — | **Not recommended** |
| Provincial portals (e.g. BC/ON) | RSS/XML or Open Dataset (varies) | Provincial | None (varies) | Free | small–med | Varies | Medium | Niche/optional |
| ATS slug expansion (GH/Lever/Workable) | ATS Integration | CA‑HQ companies (Shopify, Wealthsimple, etc.) | None | Free | 5k–20k | Good | Low (add slugs) | **Add (complementary)** |

**Notes — recommended Canada candidates**
- **Adzuna `ca`** — Docs: developer.adzuna.com. Pagination page+`results_per_page`(≤50), same
  as US. Filters: `what`,`where`,`max_days_old`,`category`,`company` (all ✓). Legal: sanctioned
  developer API, ToS‑clean. Viability: high (stable commercial API). The *only* change is adding
  `ca` to the country path — near‑zero effort, immediately fixes the weakest region.
- **Job Bank XML feed** — Government of Canada (ESDC). Auth: request feed access for your use
  case. Filters: NOC code, location, salary, employment terms. Legal: government open data,
  clean but agreement‑bound. Viability: high (authoritative) but the platform is dated and the
  *open* variant refreshes only **monthly** (freshness caveat). Prefer Adzuna‑CA first, then this
  for breadth/authority.

### 10.2 United States

| Source | Availability type | Coverage | Auth | Pricing / free tier | Est. volume | Freshness | Ease | **Recommendation** |
|---|---|---|---|---|---|---|---|---|
| CareerOneStop "List Jobs V2" (US DOL/NLx) | Official Public API (gated) | US, National Labor Exchange | API token; **v2 needs NLx partner approval** | Free (gated) | very large | Good | Medium‑Hard | Investigate/Add |
| Adzuna `us` | Free‑Tier API (already integrated) | US | key | Free tier | — | Good | — | Already in use |
| USAJOBS (integrated) | Free‑Tier API | US federal | headers | Free | 10k cap | Good | — | Already in use |
| Findwork.dev API | Free‑Tier API | US/remote tech | token | Free tier | 10k–50k (unverified) | Good | Low | Optional |
| Fantastic Jobs "Active Jobs DB" (RapidAPI) | RapidAPI Wrapper / Commercial | US + English‑speaking, ATS‑sourced | RapidAPI key | Free trial; ~$1/1k jobs | 3M+/mo ATS | **Excellent (hourly)** | Low | **Add (if budget)** |
| Coresignal Jobs | Enterprise/Commercial | Global incl US | key | From $49/mo; datasets $1k+ | 399M records | Good | Low‑Med | Enterprise only |
| Indeed (Publisher/Sponsored/Job Sync) | Partner/Commercial (no consumer search) | US+global | partner | Publisher API deprecated; Sponsored €3/call | huge | Excellent | — | **Not recommended** (no open search) |
| ZipRecruiter API | Partner API | US | partner approval | Paid/partner | large | Good | Hard | Low |
| Ladders / Dice / Built In | No Public API / Scraping | US niche | — | — | med | — | — | Not recommended |
| USA state workforce boards (NLx members) | Partner API / Open Dataset (varies) | State | varies | Free (gated) | large | Good | Hard | Via CareerOneStop instead |

**Notes — recommended US candidates**
- **CareerOneStop List Jobs V2** — Docs: careeronestop.org/Developers/WebAPI. Sponsor: US DOL;
  data from **NLx (National Labor Exchange)**, co‑sponsored by DirectEmployers + NASWA. Auth:
  registered token; **v2 (since Aug 2024) requires approval via the NLx Research Hub Governance
  Board.** Pagination + keyword/occupation(O*NET)/location filters. Legal: government API, clean
  but access‑gated. Viability: high. Verdict: **strong, authoritative, free — but gated;** worth
  applying since it dramatically broadens *non‑federal* US coverage (USAJOBS is federal‑only).
- **Fantastic Jobs / Active Jobs DB** — Docs: fantastic.jobs + RapidAPI. **ATS‑sourced** (Workday,
  Greenhouse, Lever, BambooHR, SuccessFactors, Oracle — 54 platforms, 200k+ career sites),
  **hourly refresh**, LinkedIn included. Pricing: **free trial, then ~$1 per 1,000 jobs**.
  Filters: title, location, date, remote, source. Legal: commercial ToS (they handle sourcing).
  Viability: high. Verdict: **the best single freshness/coverage upgrade if any paid budget
  exists** — it directly complements our per‑company ATS work by covering ATS platforms we don't.
- *US is already our strongest region; prioritize CareerOneStop (breadth, free) over more remote
  aggregators that mostly add duplication.*

### 10.3 United Kingdom

| Source | Availability type | Coverage | Auth | Pricing / free tier | Est. volume | Freshness | Ease | **Recommendation** |
|---|---|---|---|---|---|---|---|---|
| Adzuna `gb` | Free‑Tier API (existing key) | UK | key | Free tier | 100k+ | Good | **Trivial** | **Add — de‑risk Reed** |
| GOV.UK "Find a Job" (DWP) | Partner/Employer API + Bulk feed | GB | account/agreement | Free (gated) | 100k+ | Good | Medium (verify read access) | Investigate |
| Careerjet `uk` locale | Free‑Tier API (already integrated) | UK | key | Free | 2k/run | Good | Low (locale param) | Optional |
| NHS Jobs | No documented public API / Scraping | UK health | — | — | 20k+ | Good | — | Not recommended (no API) |
| Civil Service Jobs | No public consumer API (feed for employers) | UK gov | — | — | med | Good | — | Not recommended |
| CV‑Library / Totaljobs / Reed rivals | Partner/Commercial (no open API) | UK | partner | Paid | large | Good | Hard | Low |

**Notes — recommended UK candidates**
- **Adzuna `gb`** — same integration as CA/US; UK is a large Adzuna market. **Removes the current
  single‑source risk**: today ~100% of real UK coverage rides on Reed. Trivial effort.
- **GOV.UK Find a Job (DWP)** — listed in the DWP API Catalogue (api.gov.uk/dwp). A **bulk‑upload
  spec** exists (that path is for *employers posting* jobs). Third‑party *read/search* access is
  not clearly public — **verify the consumer‑read model before committing.** Authoritative and
  free if a read feed is available; otherwise treat as partner‑only.

### 10.4 Europe

| Source | Availability type | Coverage / countries | Auth | Pricing / free tier | Est. volume | Freshness | Ease | **Recommendation** |
|---|---|---|---|---|---|---|---|---|
| Adzuna multi‑country (`fr,de,es,nl,it,at,pl`) | Free‑Tier API (existing key) | 7+ EU markets | key | Free tier | 100k+/country | Good | **Trivial** | **Add — top EU lever** |
| France Travail "Offres d'emploi v2" | Official Public API | France | OAuth2 (free reg) | Free | 500k+ | Good | Medium (OAuth) | **Add (medium)** |
| EURES | No supported public pull API (member‑service export only) | EU‑wide (~3M) | — | — | 3M | Good | — | Not now |
| Bundesagentur (integrated) | Free API | DE | public key | Free | 10k cap | Good | — | In use (expand filters) |
| Arbeitsmarktservice AMS (AT) | Open Dataset / feed (appears via jobs.ams.at) | Austria | varies | Free | med | Good | Medium | Optional |
| Jobs.cz / Profesia (CZ/SK) | No public API / partner | CZ/SK | partner | Paid | med | Good | Hard | Low |
| StepStone / Xing (DE) | No public consumer API | DACH | — | — | large | Good | — | Not recommended |
| National PES portals (NL/ES/IT/PL) | Open Dataset / feed (varies by country) | Per country | varies | Free (varies) | med–large | Varies | Hard (per‑country) | Selective |

**Notes — recommended Europe candidates**
- **Adzuna multi‑country** — Europe is currently **56% Germany**; adding France/Spain/Netherlands/
  Italy/Austria/Poland Adzuna passes spreads coverage cheaply across the continent with the key we
  already hold. Highest EU ROI.
- **France Travail (ex‑Pôle emploi)** — Docs: francetravail.io. Auth: **free registration +
  OAuth2 client‑credentials**. Filters: location, ROME occupation code, date, contract type.
  Legal: official government API, clean. Viability: high. Adds the authoritative French national
  board (France is only ~1.4% today). Effort is the OAuth handshake — modest.

### 10.5 Singapore

| Source | Availability type | Coverage | Auth | Pricing / free tier | Est. volume | Freshness | Ease | **Recommendation** |
|---|---|---|---|---|---|---|---|---|
| MyCareersFuture (GovTech SG) | Official Public API (no‑auth v2) | Singapore national | **None** | Free | ~80k–90k | Good | **Low** | **Add — top SEA priority** |
| Adzuna `sg` | Free‑Tier API (if plan covers SG) | SG | key | Free tier | med | Good | Trivial | Add if available |
| Careers@Gov (SG public service) | No documented API / portal | SG gov | — | — | small | Good | — | Optional/scraping |
| ATS slugs (SEA‑HQ: Grab, Sea/Shopee, GoTo) | ATS Integration | SG + SEA | None | Free | 5k+ | Good | Low | **Add (complementary)** |

**Notes**
- **MyCareersFuture** — endpoint `api.mycareersfuture.gov.sg/v2/jobs`, **no auth**, 100 jobs/page
  pagination, 20+ structured fields (SGD salary min/max, employment type, seniority,
  district/region, skills, employer UEN). Legal: government portal — **confirm ToS permits
  aggregation** (public no‑auth endpoint, community‑documented, not a formally published dev
  API — small viability risk it changes). Verdict: **single best fix for the weakest‑but‑one
  region**, minimal effort.

### 10.6 Southeast Asia (beyond Singapore)

| Source | Availability type | Coverage / countries | Auth | Pricing | Est. volume | Freshness | Ease | **Recommendation** |
|---|---|---|---|---|---|---|---|---|
| JobStreet / Jobsdb (SEEK) | No public API (partner only) / Scraping | MY,ID,PH,SG,TH,VN | — | — | very large | Good | — | **Not recommended** |
| Kalibrr (PH/ID) | No documented public API | PH,ID | — | — | large | Good | — | Not recommended |
| ATS slug expansion (Grab, GoTo, Carousell, Ninja Van) | ATS Integration | SEA | None | Free | 5k–15k | Good | Low | **Add (only realistic route)** |
| Adzuna (SEA) | Free‑Tier API | limited SEA coverage | key | Free tier | small | Good | Trivial | Marginal |
| Careerjet localized (my/ph/id/th/vn) | Free‑Tier API (already integrated) | SEA | key | Free | 2k/run | Good | Low | Optional |
| Fantastic Jobs Active Jobs DB | Commercial/RapidAPI | English‑speaking incl PH/SG | key | ~$1/1k | large | Excellent | Low | Add if budget |

**Notes** — SEA has **no strong free public API** outside Singapore. The dominant boards
(JobStreet/Jobsdb, part of SEEK) expose **partner APIs only** — scraping would be required and is
**not recommended** (ToS/fragility). The realistic, legal path to deepen SEA is **ATS slug
expansion** for SEA‑headquartered companies plus optional Careerjet locales.

### 10.7 LATAM

| Source | Availability type | Coverage / countries | Auth | Pricing | Est. volume | Freshness | Ease | **Recommendation** |
|---|---|---|---|---|---|---|---|---|
| Adzuna `br` + `mx` | Free‑Tier API (existing key) | Brazil, Mexico | key | Free tier | 100k+ | Good | **Trivial** | **Add — top LATAM lever** |
| Get on Board (getonbrd.com) | Public API (likely free/low) — verify | LATAM tech, remote | key (likely) | Free/low (unverified) | 5k–20k tech | Good | Low‑Med | **Investigate/Add** |
| Himalayas search endpoint (country filter) | Free API (already integrated, richer endpoint) | Remote‑LATAM | None | Free | subset of 90k | Good | Low | **Add (cheap)** |
| Computrabajo / Bumeran / Elempleo | No public API / Scraping | MX,AR,CO,CL,BR | — | — | very large | Good | — | Not recommended |
| ATS slugs (Nubank, MercadoLibre, Rappi, dLocal) | ATS Integration | LATAM | None | Free | 5k–15k | Good | Low | **Add (complementary)** |
| Working Nomads / remote LATAM boards | RSS/Free API (varies) | Remote LATAM | varies | Free | small | Good | Low | Optional |

**Notes**
- **Adzuna `br`/`mx`** — adds real **in‑country** LATAM volume (today ~65% of our LATAM is remote
  "LATAM" nearshore listings, not location‑specific). Trivial effort.
- **Get on Board** — curated LATAM tech board; the site advertises an API and ATS integrations.
  **Verify the public read API's auth/pricing before committing** (likely free/low‑cost). Good
  quality, tech‑focused; modest volume.

### 10.8 India *(full detail in Section 11)*

| Source | Availability type | Coverage | Auth | Pricing | Est. volume | Freshness | Ease | **Recommendation** |
|---|---|---|---|---|---|---|---|---|
| National Career Service (NCS) | Open Dataset (data.gov.in) — no live API | India national | None (dataset) | Free | large (aggregate) | Poor (dataset) | Medium (ETL) | Investigate |
| Naukri "public v2" internal endpoint | No official API (India‑IP gated) | India | none (India IP) | — (grey) | very large | Good | Med (legal risk) | Not recommended |
| Fantastic Jobs / Coresignal (incl. India) | Commercial/RapidAPI | India incl. | key | Paid/trial | large | Good/Excellent | Low | Add if budget |
| ATS slugs (Indian‑HQ: Razorpay, Zoho, Freshworks, Swiggy) | ATS Integration | India | None | Free | 5k–20k | Good | Low | **Add (best free route)** |

---

## SECTION 11 — India Job API Research (dedicated)

India is the **6th‑largest country already in our dataset (3,471 jobs, incidental)** yet has
**no dedicated source**. It is a large, high‑value market. Findings below were verified against
official sources/provider sites where possible; **claims of "no public API" mean no official
developer API could be found — not that one is impossible.**

### 11.1 Major job boards / platforms

| Platform | Official API? | Availability type | Auth | Pricing / free tier | Est. jobs | Freshness | Filters | Scraping needed? | Legal risk | Integration | **Recommended?** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Naukri** (Info Edge) | No official public API | No Public API (internal v2 exists, India‑IP gated) | none (India IP) | — | 1M+ | Good | rich (internal) | Yes (grey) | **High** (ToS) | Med‑Hard | **No** |
| **Foundit** (ex‑Monster) | No official public API | No Public API / Scraping | — | — | 800k+ | Good | — | Yes | High | — | No |
| **Apna** | No public API | No Public API / Scraping | — | — | large (blue‑collar) | Good | — | Yes | High | — | No |
| **TimesJobs** | No public API | No Public API / Scraping | — | — | med | Med | — | Yes | High | — | No |
| **Shine** | No public API | No Public API / Scraping | — | — | med | Med | — | Yes | High | — | No |
| **Freshersworld** | No public API (RSS historically) | RSS/XML (verify) | none | Free | med (fresher) | Med | limited | Maybe | Med | Low‑Med | Investigate |
| **Cutshort** | No public API | No Public API | — | — | small (tech) | Good | — | Yes | Med | — | No |
| **Wellfound** (AngelList) | No official public API | No Public API / Scraping | — | — | med (startup) | Good | — | Yes | Med | — | No |
| **Internshala** | No public API | No Public API / Scraping | — | — | large (intern/fresher) | Good | — | Yes | Med | — | No |
| **LinkedIn** | No open jobs API (partner only) | Partner/Enterprise API | OAuth partner | Paid/partner | huge | Excellent | rich | — | High | Hard | No |
| **Indeed India** | Publisher API deprecated; partner only | Partner/Commercial | partner | Paid | huge | Excellent | rich | — | High | Hard | No |
| **WorkIndia** | No public API | No Public API / Scraping | — | — | large (blue‑collar) | Good | — | Yes | High | — | No |
| **Hirect** | No public API | No Public API | — | — | med | Good | — | Yes | Med | — | No |

### 11.2 Government / public sources

| Source | Official API? | Availability type | Auth | Pricing | Est. jobs | Freshness | Legal | **Recommended?** |
|---|---|---|---|---|---|---|---|---|
| **National Career Service (NCS)** | No live developer API; **data published on data.gov.in** | Open Dataset | None (dataset); API keys for some OGD resources | Free | large (aggregate vacancies) | **Poor** (periodic dataset) | Clean (Gov open data) | **Investigate** (breadth, but freshness/format friction) |
| **data.gov.in OGD platform** | Some resources have APIs | Open Dataset / Official API (per resource) | API key (free) | Free | varies | Varies | Clean | Investigate |
| **State employment exchanges / Rojgar portals** | Mostly no API | No Public API / Open Dataset (varies) | varies | Free | med | Poor | Clean | Low (fragmented) |
| **Government recruitment (SSC/UPSC/RRB/state PSC)** | No jobs API (notifications only) | No Public API / RSS (varies) | — | Free | small (notifications) | Med | Clean | Niche only |

### 11.3 Commercial / aggregator / ATS routes (the realistic legal options)

| Source | Availability type | Auth | Pricing / free tier | India coverage | Freshness | Integration | **Recommended?** |
|---|---|---|---|---|---|---|---|
| **Fantastic Jobs / Active Jobs DB** (RapidAPI) | Commercial / RapidAPI Wrapper | key | Free trial; ~$1/1k jobs | India ATS + boards incl. | **Excellent (hourly)** | Low | **Yes (if budget)** |
| **Coresignal** | Enterprise/Commercial | key | $49/mo+; datasets $1k+ | India incl. (399M multi‑source) | Good | Low‑Med | Enterprise only |
| **JobsPikr** | Commercial | key | Paid (custom) | India incl. (Naukri/Monster feeds) | Good | Low | If budget |
| **RapidAPI "JSearch"** (already via OpenWeb Ninja) | RapidAPI Wrapper | key | Free tier (metered) | India via Google Jobs | Good | Low (reuse) | **Add India query (cheap)** |
| **ATS slug expansion — Indian‑HQ companies** | ATS Integration | None | Free | Razorpay, Zoho, Freshworks, Swiggy, Zomato, Groww, CRED, PhonePe, Meesho, Postman, Zeta, Browserstack | Good | **Low** | **Yes — best free route** |
| **Keka / Darwinbox / Zoho Recruit** (India‑popular ATS) | Enterprise ATS (per‑customer keys) | token | — | India SMB/enterprise | Good | Hard (no aggregate feed) | No (no public aggregate) |

### 11.4 Niche / sector / campus / staffing (India)

| Source | Availability type | Notes | **Recommended?** |
|---|---|---|---|
| iimjobs / hirist / updazz (Info Edge niche) | No public API / Scraping | Tech & management niche | No |
| Practo/health, BFSI, manufacturing boards | No public API (mostly) | Sector‑specific, fragmented | No |
| University/campus portals (Superset, Unstop/Dare2Compete) | Partner/Enterprise (per‑institution) | Campus hiring; no open aggregate API | Investigate (Unstop has scale) |
| Staffing/consultancies (TeamLease, Quess, Randstad IN) | No public API | Bulk hiring via own ATS | No |
| Instahyre, Cutshort, Wellfound | No public API / Scraping | Tech startup hiring | No |

### 11.5 India — implementation priority ranking

1. **ATS slug expansion for Indian‑HQ companies** — *free, legal, low effort, good freshness.*
   The single best India move: reuse existing Greenhouse/Lever/Ashby/Workable integrations with
   verified Indian company slugs (many Indian unicorns run these ATS). **Priority: High.**
2. **Add an India‑scoped query to existing metered APIs (JSearch/OpenWeb Ninja, SerpApi)** —
   cheap, reuses code, gives immediate India volume via Google Jobs. **Priority: Medium‑High.**
3. **Fantastic Jobs / Active Jobs DB (paid)** — if any budget exists, best coverage+freshness for
   India ATS/boards including LinkedIn. **Priority: Medium (budget‑gated).**
4. **National Career Service open dataset (data.gov.in)** — free & authoritative but poor
   freshness and bulk‑ETL friction. **Priority: Medium (breadth play).**
5. **Coresignal / JobsPikr (enterprise)** — only at scale/with budget. **Priority: Low.**
6. **Naukri/Foundit/Apna/LinkedIn/Indeed scraping** — **Not recommended** (no official API,
   ToS/legal risk, high maintenance). **Priority: Avoid.**

**Bottom line for India:** there is **no free, official, real‑time consumer jobs API** for the
big Indian boards. Legal, low‑maintenance coverage comes from **(a) ATS slug expansion** and
**(b) reusing our metered/Google‑Jobs sources with an India query**; deeper coverage requires a
**paid aggregator** (Fantastic Jobs). Scraping the major boards is explicitly not recommended.

---

## SECTION 12 — Estimated Coverage Expansion

Estimates are **order‑of‑magnitude planning figures**, not guarantees — actual yield depends on
free‑tier caps, per‑country self‑caps, and dedup. "Net new" accounts for expected overlap with
what we already collect. Effort/maintenance are engineering‑time judgments.

| # | Expansion | Est. gross jobs | Est. **net new** | Eng effort | Maint. effort | Dup rate | Freshness | Business value | **Priority** |
|---|---|---:|---:|---|---|---|---|---|---|
| 1 | Adzuna → multi‑country (ca, gb, fr, de, es, nl, it, br, mx, +) | ~2k × ~12 = 24k | **~20k** | **1 day** | Low | Low‑Med | Good | **Very High** | **Critical** |
| 2 | MyCareersFuture (Singapore) | ~80k avail; cap ~10–20k | **~15k** | 1–2 days | Low | Low | Good | High | **Critical** |
| 3 | ATS slug expansion (all 6 ATS, all regions incl. India/SEA/LATAM/CA) | +50–100 slugs | **~30–60k** | 2–4 days (ongoing) | **Medium** (slugs rot) | Low | Good | High | **High** |
| 4 | France Travail (France) | 500k avail; cap ~10k | **~10k** | 2–3 days (OAuth) | Low | Low | Good | Medium‑High | **High** |
| 5 | CareerOneStop / NLx (US non‑federal) | very large; gated | **~10–20k** (if approved) | 3–5 days + approval | Low | Med (vs ATS) | Good | Medium | Medium |
| 6 | Scheduling + expiry (freshness, not volume) | 0 new | **0** (quality) | 2–4 days | Medium | — | **Transforms** | **Very High** | **Critical** |
| 7 | Fantastic Jobs Active Jobs DB (paid) | 3M+/mo | **~50k+** (budget‑bound) | 1–2 days | Low | Low (ATS) | **Excellent** | High | Medium (budget) |
| 8 | Himalayas search endpoint + The Muse API key | +a few k each | **~5k** | 1–2 days | Low | Med | Good | Low‑Med | Medium |
| 9 | India: ATS slugs + India query on metered APIs | — | **~10–20k** | 2–3 days | Medium | Low | Good | Medium‑High | High |
| 10 | Job Bank CA / NCS India open datasets | large | **~20–50k** | 4–6 days (bulk ETL) | Medium | Med | **Poor (monthly)** | Medium | Low‑Med |

**Rollup (free/low‑cost, high‑confidence path — items 1,2,3,4,6,9):** realistically
**~85k–125k net‑new jobs**, taking the dataset from ~156k toward **~240k–280k**, while
**item 6 (scheduling + expiry) fixes the 46% stale problem** independent of volume. With the
paid item 7, six‑figure additional volume is available. None of the high‑priority items require
scraping or carry meaningful legal risk.

---

## SECTION 13 — API Comparison Matrix (existing + candidate)

One consolidated matrix. **E** = existing/integrated, **C** = candidate. Filters:
✓ available · ✓* available‑but‑unused · ✗ none. **Incremental sync** = does the API support
date/`updated_since`/cursor filtering that enables cheap delta pulls?

| API | E/C | Region | Auth | Free | Free tier | Paid | Pag. | Date flt | Country flt | Kw flt | Cat flt | Company flt | Remote flt | Incr. sync | Max est. jobs | Integ. difficulty | **Recommendation** |
|---|:--:|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---:|---|---|
| SmartRecruiters | E | Global | none | ✓ | — | — | ✓ | ✗ | ✗ | ✗ | ✗ | n/a | ✓(bool) | ✗ | boards (65k) | Low | Keep (Critical) |
| Adzuna | E | Per‑country | key | — | ✓ | ✓ | ✓ | ✓* | ✓* (path) | ✓* | ✓* | ✓* | via kw | ✓ (max_days_old) | 2k/country | Low | **Expand countries** |
| Lever | E | Global | none | ✓ | — | — | ✓ | ✗ | ✗ | ✗ | ✗ | n/a | ✓ | ✗ | boards (18k) | Low | Keep + slugs |
| Greenhouse | E | Global | none | ✓ | — | — | ✗ | ✗ | ✗ | ✗ | ✗ | n/a | ✗ | ✗ | boards (15k) | Low | Keep + slugs |
| USAJOBS | E | US fed | headers | — | ✓ | — | ✓ | ✓* | ✓* | ✓* | ✓* | ✗ | ✓(bool) | ✓ (DatePosted) | 10k | Low | Keep |
| Reed | E | UK | basic | — | ✓ | — | ✓ | ✗ | ✗ | ✓* | ✗ | ✗ | via kw | ✗ | 9k | Low | Keep + add Adzuna gb |
| Bundesagentur | E | DE | pub key | ✓ | — | — | ✓ | ✓* | ✓* | ✓* | ✗ | ✗ | via kw | ✓ (since) | 10k | Low | Keep |
| Ashby | E | Global | none | ✓ | — | — | ✗ | ✗ | ✗ | ✗ | ✗ | n/a | ✓(bool) | ✗ | boards (5k) | Low | Keep |
| Workable | E | Global | none | ✓ | — | — | ✗ | ✗ | ✗ | ✗ | ✗ | n/a | ✓(bool) | ✗ | boards (4k) | Low | Keep |
| Himalayas | E | Remote | none | ✓ | — | — | ✓ | ✓* | ✓* | ✓* | ✓* | ✓* | ✓ | ✓ (search) | 90k avail | Low | **Use search endpt** |
| The Muse | E | Global | none/key | ✓ | ✓(key) | — | ✓ | ✗ | ✗ | ✗ | ✓* | ✓* | ✗ | 2k unauth | Low | Add key |
| Jooble | E | Global | path key | — | ✓ | ✓ | ✓ | ✓* | ✓* | ✓ | ✗ | ✗ | via kw | ✓ | ~1.1k | Low | Keep |
| Careerjet | E | Global | basic+IP | — | ✓ | — | ✓ | ✗ | ✓* | ✓ | ✗ | ✗ | via kw | ✗ | 2k | Medium | Keep |
| Arbeitnow | E | EU | none | ✓ | — | — | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓(bool) | ✗ | ~0.9k | Low | Keep |
| RemoteOK | E | Remote | UA | ✓ | — | — | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓(all) | ✗ | ~0.1k | Low | Keep |
| Jobicy | E | Remote | none | ✓ | — | — | ✗ | ✗ | ✓* | ✗ | ✓* | ✗ | ✓(all) | ✗ | 0.1k | Low | Keep |
| Teamtailor | E | Global | none | ✓ | — | — | ✗ | ✗ | ✗ | ✗ | ✗ | n/a | ✓ | ✗ | ~0.5k | Medium | Keep |
| SerpApi | E | Global | key | — | ✓ | ✓ | ✓ | ~rel | ✓* | ✓ | ✗ | ✗ | ✓(bool) | ✗ | 50/run | Low | Keep (cap) |
| OpenWeb Ninja | E | Global | key | — | ✓ | ✓ | ✓ | ✓* | ✓* | ✓ | ✗ | ✗ | ✓(bool) | ✓ | 50/run | Low | Keep (cap) |
| TheirStack | E | Global | bearer | — | — | ✓ | ✓ | ✓ | ✓* | ✗ | ✗ | ✓* | ✓ | ✓ | 0 (402) | Low | Park |
| **CareerOneStop/NLx** | C | US | token | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | — | ✓ | very large | Med (gated) | Investigate |
| **MyCareersFuture** | C | SG | none | ✓ | ✓ | — | ✓ | ✓ | n/a | ✓ | ✓ | ✓ | ✓ | ✓ | ~80k | Low | **Add** |
| **France Travail** | C | FR | OAuth2 | ✓ | ✓ | — | ✓ | ✓ | n/a | ✓ | ✓ | ✗ | — | ✓ | 500k | Medium | **Add** |
| **Job Bank CA (feed/dataset)** | C | CA | req/none | ✓ | ✓ | — | n/a | ✓ | ✓ | ✓ | ✓ | ✗ | — | dataset | Medium | Investigate |
| **Fantastic Jobs / Active Jobs DB** | C | Global | key | — | ✓(trial) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 3M+/mo | Low | Add (budget) |
| **Coresignal** | C | Global | key | — | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 399M | Med | Enterprise |
| **Get on Board** | C | LATAM | key? | ✓? | ✓? | — | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | ~5–20k | Low‑Med | Investigate |
| **NCS India (dataset)** | C | IN | none | ✓ | ✓ | — | n/a | ✓ | n/a | ✓ | ✗ | ✗ | — | dataset | Med | Investigate |
| **JSearch India query** | C | IN | key | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | metered | Low | Add |

---

## SECTION 14 — Engineering Roadmap

Prioritized, grouped by horizon. Each item: **impact · effort · risk · business value ·
priority · dependencies.** Nothing here is implemented — this is a plan.

### Immediate improvements (1–2 days)
1. **Adzuna → multi‑country.** *Impact:* +~20k net‑new across CA/UK/EU/LATAM, fixes 3 weak
   regions. *Effort:* ~1 day (iterate a country list over existing code). *Risk:* Low (free‑tier
   call budget). *Value:* Very High. *Priority:* **Critical.** *Deps:* existing Adzuna key
   (present).
2. **MyCareersFuture (Singapore).** *Impact:* +~15k, transforms SEA. *Effort:* 1–2 days
   (new no‑auth source module). *Risk:* Low‑Med (undocumented public endpoint could change;
   confirm ToS). *Value:* High. *Priority:* **Critical.** *Deps:* none.
3. **Record `fetched_at` per run + surface "data as of X".** *Impact:* honest freshness, enables
   expiry. *Effort:* ~0.5 day. *Risk:* Low. *Value:* High (foundation for freshness work).
   *Priority:* **High.** *Deps:* none.

### Short term (1 week)
4. **Scheduled re‑runs + presence‑diff expiry.** *Impact:* fixes the 46% stale problem;
   auto‑expire closed jobs. *Effort:* 2–4 days (scheduler + run‑to‑run state index). *Risk:*
   Medium (state persistence, first real move off single‑file snapshot). *Value:* Very High.
   *Priority:* **Critical.** *Deps:* item 3.
5. **France Travail (France).** *Impact:* +~10k authoritative FR. *Effort:* 2–3 days (OAuth2).
   *Risk:* Low. *Value:* Medium‑High. *Priority:* **High.** *Deps:* free registration.
6. **India via ATS slugs + India query on metered APIs.** *Impact:* +~10–20k, opens a major
   market legally. *Effort:* 2–3 days. *Risk:* Low (ATS) / Low (reuse metered). *Value:*
   Medium‑High. *Priority:* **High.** *Deps:* none.
7. **URL normalization in dedup + conservative cross‑provider pass.** *Impact:* cleaner data,
   fewer aggregator dupes without erasing multi‑location roles. *Effort:* 1–2 days. *Risk:*
   Medium (must guard the multi‑location false‑merge). *Value:* Medium. *Priority:* **High.**
   *Deps:* none.
8. **De‑risk UK (Adzuna gb) + The Muse API key + Himalayas search endpoint.** *Impact:* resiliency
   + a few k jobs. *Effort:* 1–2 days total. *Risk:* Low. *Value:* Medium. *Priority:* Medium.

### Medium term (1 month)
9. **Broad ATS slug expansion program (all regions).** *Impact:* +~30–60k, the main lever for
   balancing regional coverage. *Effort:* ongoing (verification tooling helps). *Risk:* Medium
   (slug rot / maintenance). *Value:* High. *Priority:* **High.** *Deps:* a slug‑verification
   helper to keep lists healthy.
10. **CareerOneStop/NLx (US non‑federal).** *Impact:* large authoritative US breadth. *Effort:*
    3–5 days + partner approval. *Risk:* Medium (governance approval, may be denied). *Value:*
    Medium. *Priority:* Medium. *Deps:* NLx approval.
11. **Location normalization layer.** *Impact:* shrinks the 18% unclassifiable, powers real
    regional filters/maps. *Effort:* 3–5 days. *Risk:* Low‑Med. *Value:* Medium‑High. *Priority:*
    **High.** *Deps:* none.
12. **Add `description` to schema (+ provider passes that supply it).** *Impact:* far better
    search; unlocks description‑based dedup. *Effort:* 3–5 days + storage growth. *Risk:* Medium
    (file size — see §15). *Value:* Medium‑High. *Priority:* Medium.

### Long term
13. **Move off the single‑file snapshot to a datastore** (see §15). *Impact:* enables incremental
    sync, expiry, scale, and API serving. *Value:* Very High at scale. *Priority:* High once
    volume approaches ~500k. *Deps:* items 3/4.
14. **Paid aggregator (Fantastic Jobs / Coresignal) for freshness+breadth.** *Impact:* six‑figure
    volume, hourly freshness. *Effort:* 1–2 days integration. *Risk:* Low tech / cost. *Value:*
    High. *Priority:* Medium (budget decision).
15. **Automated slug/company discovery + health monitoring.** *Impact:* keeps ATS coverage
    growing without manual curation. *Effort:* larger. *Value:* High (sustains item 9). *Priority:*
    Medium.

---

## SECTION 15 — Final Conclusions

**Current platform maturity.** The platform is a **well‑engineered, mature v1 aggregator**: a
clean, extensible source architecture (20 providers behind one interface), a normalized schema
with 99.99% date coverage, correct URL deduplication, and disciplined error isolation. It is
**production‑grade as a periodic bulk board**, but not yet as a freshness‑ or scale‑sensitive
product — it is a **static snapshot with no scheduling, no expiry, and no persistent per‑job
state.**

**Regional strengths.** United States (51%, deep across federal + private ATS); Germany/Europe
(strong via public agencies); UK (well‑covered *for its size*, via Reed); a surprisingly useful
remote/LATAM nearshore layer.

**Regional weaknesses.** **Canada (2.2%)** and **SEA (3.0%)** are thin; **India has no dedicated
source** despite being the 6th country by volume; **UK is a single‑source dependency**; Europe is
**over‑concentrated in Germany**; the whole dataset is **over‑concentrated in one provider
(SmartRecruiters, 41.8%)**.

**Coverage quality.** Broad but **skewed by curation, not balanced by design**; ~18% of locations
are unclassifiable, capping the quality of any location‑based feature.

**API limitations.** Hard result windows (10k on USAJOBS/Bundesagentur, ~9.9k on Reed); curated
company lists that grow only manually; metered sources throttled to ~50 jobs/run; several major
boards (Naukri, JobStreet, LinkedIn, Indeed consumer search) have **no public API** — off‑limits
without scraping we should not do.

**Duplicate quality.** **Excellent at the URL level (0 dupes).** The remaining risk is
cross‑provider overlap, which is real but modest; the key insight is that naive title/company
dedup would *destroy* ~35k legitimate multi‑location jobs, so dedup must stay conservative.

**Freshness quality.** **The weakest dimension.** ~54% current at collection, but **46% stale,
14% over a year old, and no auto‑refresh or expiry** — freshness degrades every day after a run.
This is the highest‑value area to fix and is largely an *architecture/scheduling* problem, not a
sourcing one.

**Future expansion opportunities.** Mostly **free and already unlocked**: multi‑country Adzuna,
MyCareersFuture, France Travail, ATS slug expansion, and India via ATS + metered queries — plus
optional paid aggregators for step‑change volume/freshness.

### Top 10 Recommendations
1. Enable **Adzuna multi‑country** (CA, GB, EU, BR, MX) — biggest free win.
2. Add **MyCareersFuture** (Singapore) — free, ~15k, fixes SEA.
3. Introduce **scheduled re‑runs + `fetched_at`** — foundation for freshness.
4. Implement **presence‑diff expiry** to auto‑retire closed jobs.
5. **De‑risk the UK** with Adzuna `gb` (stop depending solely on Reed).
6. Add **France Travail** for authoritative French coverage.
7. Launch an **ATS slug‑expansion program** targeting CA/SEA/LATAM/India companies.
8. Add **India** via ATS slugs + an India query on existing metered APIs.
9. Add **URL normalization + a conservative, location‑aware cross‑provider dedup** pass.
10. Build a **location‑normalization layer** to shrink the 18% unclassifiable bucket.

### Top 10 APIs to integrate next
1. Adzuna (multi‑country) — *existing key, config‑level.*
2. MyCareersFuture (SG) — *free, no auth.*
3. France Travail (FR) — *free, OAuth2.*
4. CareerOneStop / NLx (US non‑federal) — *free, partner‑gated.*
5. Job Bank Canada (feed/open dataset) — *free/authoritative.*
6. Get on Board (LATAM tech) — *verify public API.*
7. National Career Service India (open dataset) — *free breadth.*
8. Fantastic Jobs / Active Jobs DB — *paid, best freshness (budget).*
9. Himalayas **search** endpoint — *reuse existing source, add filters.*
10. The Muse with **API key** — *raises the 2k unauth cap.*

### Top 10 highest‑ROI improvements
1. Adzuna multi‑country (huge coverage / ~1 day).
2. Scheduling + expiry (fixes 46% stale / days).
3. MyCareersFuture (fixes weakest region / ~1–2 days).
4. ATS slug expansion (regional balance / ongoing, low‑cost).
5. `fetched_at` + freshness UI badge (trust / ~0.5 day).
6. URL normalization in dedup (cleaner data / ~1 day).
7. India via ATS + metered query (new market / ~2–3 days).
8. Adzuna `gb` UK de‑risk (resilience / trivial).
9. Location normalization (unlocks filters/maps / ~3–5 days).
10. Provider‑side recency filters to drop the stale tail at ingest (~1–2 days).

### Can the current architecture scale to millions of jobs?

**Not as‑is.** The design is excellent for its current scale but has three hard ceilings:

1. **Storage/serving model.** A single **~54 MB `jobs.json` at 156k** jobs implies **~350 MB at
   1M** and **>1 GB at 3M**. The frontend `fetch()`es and renders the *entire* file in‑browser —
   already heavy, and untenable at millions. **A database + a paginated/queryable API is required.**
2. **No incremental sync / state.** Every run re‑fetches and overwrites everything; there is no
   delta pull, no per‑job `last_seen`, no expiry. At millions of jobs, full re‑crawls become slow
   and wasteful and freshness/expiry become impossible without persistent state.
3. **Curation and dedup at scale.** ATS coverage grows by hand‑curated slugs (doesn't scale to
   millions), and exact‑URL dedup won't catch the far larger cross‑provider overlap a
   million‑job corpus implies.

**Architectural improvements needed as the dataset grows:**
- **Persistent datastore** (Postgres/OpenSearch/Elastic) replacing the JSON file, with a
  **paginated search API** the frontend queries — no more whole‑file loads.
- **Incremental/delta ingestion** with per‑job `first_seen`/`last_seen`, provider cursors/date
  filters, and **automated expiry** (presence diff + liveness).
- **Scalable dedup** — normalized‑URL keys plus blocked fuzzy/LSH matching (and description‑based
  matching once descriptions are stored) to handle cross‑provider overlap.
- **Automated source discovery/health** (slug verification, dead‑source alerts) so coverage scales
  without linear manual effort.
- **Decoupled pipeline** — per‑source workers, queueing, and rate‑limit budgeting so one slow/large
  provider can't stall a run, with observability on volume/freshness/dupes per source per run.

**Conclusion:** the current architecture is the *right foundation* and can comfortably grow into
the **low hundreds of thousands** with the roadmap above. Reaching **millions** is achievable but
requires graduating from "fetch → dedup → one JSON file" to a **datastore‑backed, incrementally
synced, queryable service** — an evolution the existing modular source design makes
straightforward to adopt without rewriting the providers.

---

## Sources (external research — Sections 7–15)

- CareerOneStop Web API (US DOL / NLx) — https://www.careeronestop.org/Developers/WebAPI/web-api.aspx ,
  https://www.careeronestop.org/Developers/WebAPI/Jobs/list-jobs-v2.aspx
- National Labor Exchange (NLx) — https://www.usnlx.com/
- National Career Service (India) & Open Government Data — https://www.ncs.gov.in/ ,
  https://www.data.gov.in/catalog/national-career-service-ncs
- Fantastic Jobs / Active Jobs DB — https://fantastic.jobs/api ,
  https://rapidapi.com/fantastic-jobs-fantastic-jobs-default/api/active-jobs-db
- Coresignal jobs data — https://coresignal.com/pricing/ , https://docs.coresignal.com/
- Indeed Partner (Job Sync / Sponsored Jobs) — https://docs.indeed.com/
- GOV.UK "Find a Job" / DWP API Catalogue — https://www.api.gov.uk/dwp/ ,
  https://findajob.dwp.gov.uk/
- Get on Board (LATAM tech jobs) — https://www.getonbrd.com/
- Wellfound (AngelList) — https://wellfound.com/ (no official public jobs API found; scraping only)
- Naukri / Foundit (India) — https://www.naukri.com/ , https://www.foundit.in/ (no official public
  API found; third‑party scrapers only)
- Adzuna developer docs — https://developer.adzuna.com/
- France Travail (ex‑Pôle emploi) developer portal — https://francetravail.io/
- MyCareersFuture (GovTech Singapore) — https://www.mycareersfuture.gov.sg/ ,
  https://www.developer.tech.gov.sg/
- Job Bank Canada / Open Government — https://www.jobbank.gc.ca/ , https://open.canada.ca/data
- ATS public job‑posting APIs overview — https://cavuno.com/blog/ats-platforms-public-job-posting-apis

*(Availability classifications reflect official documentation as reviewed in July 2026. Items
marked "verify"/"unverified"/"no public API found" were not confirmable to first‑party developer
docs at research time and must be validated before any integration work.)*

---
---

# DEEPER RESEARCH (Sections 16–17)

*Third research pass. Sections 1–15 above are unchanged. Still analysis/research only — no code,
`jobs.py`, `jobs.json`, reports, or charts created or modified; nothing implemented. External
claims verified against official docs where possible and flagged where not.*

---

## SECTION 16 — Expanded India API & Recruitment Market Research

This section deepens Section 11 into a comprehensive survey of the **Indian recruitment
ecosystem**, not just the headline boards. The single most important structural finding shapes
everything below:

> **India has a large, active online‑hiring market but almost no *aggregatable* public job
> APIs.** The big consumer boards (Naukri, Foundit, Apna, Shine, TimesJobs, Instahyre, etc.)
> expose **no official public developer API** for reading listings; the India‑popular ATS/HRMS
> platforms (Darwinbox, Keka, Zoho Recruit, Freshteam, GreytHR, CEIPAL) expose **per‑tenant
> APIs that require each individual employer's own OAuth credentials**, not a global feed like
> Greenhouse/Lever. So the realistic, legal routes to Indian jobs are: **(a) the global ATS
> sources we already run, extended with Indian‑HQ company slugs; (b) reusing our Google‑Jobs /
> metered sources with an India query; (c) the government open‑data route; and (d) a paid
> aggregator that already polls Indian ATS/boards.** Scraping the consumer boards is possible
> but **not recommended** (ToS + India‑IP gating + maintenance).

**Availability taxonomy** (same as §10): Official Public API · Partner API · Enterprise/Per‑tenant
API · Commercial API · RapidAPI Wrapper · Open Dataset · RSS/XML · ATS Integration · No Public
API · Scraping Required · Not Recommended.

### 16.1 Government & public sector

| Source | Official API? | Type | Auth | Free tier / pricing | Docs | Rate limits | Pagination | Filters | Est. volume | Freshness | Integration | Legal | Scraping? | **Recommendation** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| National Career Service (NCS) | No live dev API | Open Dataset (data.gov.in) | None (dataset); OGD key for some resources | Free | data.gov.in/catalog/national-career-service-ncs | n/a (bulk) | file/CSV | date, state, sector (in data) | Large (national vacancies) | **Poor (periodic)** | Medium (ETL) | Clean (Gov open data) | No | **Investigate** (breadth; freshness‑limited) |
| data.gov.in OGD platform | Some resources have REST APIs | Official Public API / Open Dataset | Free API key | Free | data.gov.in | modest | per‑resource | per‑resource | Varies | Varies | Medium | Clean | No | Investigate |
| State employment exchanges / Rojgar portals (e.g. Rojgar Sangam UP, MP Rojgar, Maha Jobs) | Mostly none | No Public API / Open Dataset (varies) | varies | Free | per‑state | — | — | — | Med (per state) | Poor | Hard (fragmented, 28+ states) | Clean | Often yes | **Low** (fragmentation kills ROI) |
| Central recruitment (SSC, UPSC, RRB, IBPS, state PSCs) | No jobs API | No Public API / RSS notifications | — | Free | per‑body | — | — | — | Small (exam notices, not listings) | Med | Hard | Clean | Yes | **Niche only** (govt exam notices, not job listings) |
| Ministry of Labour / e‑Shram | No jobs API (worker registry) | No Public API | — | — | labour.gov.in | — | — | — | n/a (registry, not vacancies) | — | — | Clean | — | **Not applicable** |

**Notes.** NCS is the only government source with real breadth, but it publishes **datasets**
(periodic) rather than a live searchable API, so freshness and bulk‑ETL friction are real. State
portals are individually small and total ~28+ different systems with no common API — high effort,
low per‑integration yield. Government *recruitment bodies* publish exam **notifications**, not
aggregatable job listings.

### 16.2 Private job boards / consumer platforms

| Platform | Owner | Official API? | Type | Auth | Est. jobs | Freshness | Filters | Scraping? | Legal risk | Integration | **Recommended?** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Naukri** | Info Edge | No official public API | No Public API (internal v2, India‑IP gated) | none (India IP) | 1M+ | Good | rich (internal) | Yes | **High** | Med‑Hard | **No** |
| **Foundit** (ex‑Monster) | Foundit | No official public API | No Public API / Scraping | — | 800k+ | Good | — | Yes | High | — | No |
| **Shine** | HT Media | No public API | No Public API / Scraping | — | med | Med | — | Yes | High | — | No |
| **TimesJobs** | Times Group | No public API | No Public API / Scraping | — | med | Med | — | Yes | High | — | No |
| **Apna** | Apna | No public API | No Public API / Scraping | — | Large (blue‑collar) | Good | — | Yes | High | — | No |
| **WorkIndia** | WorkIndia | No public API | No Public API / Scraping | — | Large (blue‑collar) | Good | — | Yes | High | — | No |
| **Cutshort** | Cutshort | No public API | No Public API | — | Small (tech) | Good | — | Yes | Med | — | No |
| **Instahyre** | Instahyre | No public API | No Public API / Scraping | — | Med (tech) | Good | — | Yes | Med | — | No |
| **Hirist** | Info Edge | No public API | No Public API / Scraping | — | Med (tech) | Good | — | Yes | High | — | No |
| **iimjobs** | Info Edge | No public API | No Public API / Scraping | — | Med (mgmt) | Good | — | Yes | High | — | No |
| **Freshersworld** | Freshersworld | Historically RSS/XML | RSS/XML (verify current) | none | Med (fresher) | Med | limited | Maybe | Med | Low‑Med | **Investigate** (only board with a historical feed) |
| **Internshala** | Internshala | No public API | No Public API / Scraping | — | Large (intern/fresher) | Good | — | Yes | Med | — | No |
| **Unstop** (ex‑Dare2Compete) | Unstop | No public jobs API | No Public API (assessment/competition platform) | — | Med (campus/intern) | Good | — | Yes | Med | — | **No** (not a job‑listing API) |
| **Wellfound** (AngelList) | Wellfound | No official public API | No Public API / Scraping | — | Med (startup) | Good | — | Yes | Med | — | No |
| **Hasjob** | HasGeek | Public listings (small) | RSS/JSON (verify) | none | Small (tech, community) | Med | limited | Maybe | Low | Low | Investigate (tiny volume) |
| **HackerEarth Jobs** | HackerEarth | No public jobs API | No Public API (assessment platform w/ job listings) | — | Small | Good | — | Yes | Med | — | No |
| **Superset** | Superset | No public API | Enterprise/Per‑institution (campus placement) | partner | Med (campus) | Good | — | — | Med | Hard | No (per‑college gated) |
| **Indeed India** | Indeed | Publisher API deprecated | Partner/Commercial (no consumer search) | partner | Huge | Excellent | rich | — | High | Hard | **No** |
| **LinkedIn India** | Microsoft | No open jobs API | Partner/Enterprise | OAuth partner | Huge | Excellent | rich | — | High | Hard | **No** |

**Notes.** This is the crux: **every major Indian consumer board is "No Public API."** Three of
the biggest (Naukri, Hirist, iimjobs) are Info Edge properties with no external read API; Naukri's
internal v2 endpoint only reliably serves India residential IPs and using it is a ToS grey area.
The only glimmers are **Freshersworld** (a historical XML/RSS feed — worth verifying it still
exists) and tiny community boards (**Hasjob**). Unstop and HackerEarth are assessment/competition
platforms, not job‑listing APIs.

### 16.3 Recruitment / ATS / HR platforms (as *sources* of Indian listings)

The question for each: does it expose an **aggregatable public job feed**, or only a
**per‑customer** API needing each employer's own credentials?

| Platform | Origin | Public aggregate feed? | Type | Auth model | Aggregatable for us? | **Recommendation** |
|---|---|---|---|---|---|---|
| **Greenhouse** | US | Yes (per‑company board, no auth) | ATS Integration *(already integrated)* | none | **Yes** — add Indian‑HQ slugs | **Add India slugs** |
| **Lever** | US | Yes (per‑company, no auth) | ATS Integration *(integrated)* | none | **Yes** | **Add India slugs** |
| **Ashby** | US | Yes (per‑company, no auth) | ATS Integration *(integrated)* | none | **Yes** | **Add India slugs** |
| **Workable** | US | Yes (widget API, no auth) | ATS Integration *(integrated)* | none | **Yes** | **Add India slugs** |
| **SmartRecruiters** | US | Yes (postings API, no auth) | ATS Integration *(integrated)* | none | **Yes** | **Add India slugs** |
| **Teamtailor** | SE | Yes (RSS per company) | RSS/XML *(integrated)* | none | Yes | Add India slugs |
| **Workday** | US | Per‑tenant career‑site JSON (CxS) | Enterprise/Per‑tenant | none but per‑tenant endpoint | Partial (per‑company endpoints; heavy, used by many large Indian enterprises) | **Investigate** (new integration; high enterprise‑India value) |
| **Zoho Recruit** | **India** | Per‑customer API only | Enterprise/Per‑tenant API | OAuth per account | **No aggregate feed** | No (per‑tenant) |
| **Freshteam** (Freshworks) | **India** | Per‑customer API only | Enterprise/Per‑tenant API | token per account | No aggregate feed | No |
| **Darwinbox** | **India** | Per‑customer API (application data) | Enterprise/Per‑tenant API | token per tenant | No aggregate feed | No |
| **Keka** | **India** | HRMS/payroll; no job‑board feed | Enterprise/Per‑tenant | token | No | No |
| **GreytHR** | **India** | HRMS/payroll; no job feed | Enterprise/Per‑tenant | token | No | No |
| **CEIPAL** | US/India | Staffing ATS; aggregates boards *inward* | Enterprise/Per‑tenant | token | No (consumes, doesn't publish) | No |
| **Recruit CRM** | India | Per‑customer API | Enterprise/Per‑tenant | key per account | No aggregate feed | No |
| **BambooHR** | US | Per‑customer; some public career pages | Enterprise/Per‑tenant | key per account | Limited | No (per‑tenant) |

**Notes.** The India‑origin ATS/HRMS stack (Zoho Recruit, Freshteam, Darwinbox, Keka, GreytHR,
Recruit CRM) is uniformly **per‑tenant** — useful only if you are that specific employer's
integration partner, so **not aggregatable**. The productive insight is the opposite direction:
**many Indian companies host their careers on the *global* ATS we already integrate** (Greenhouse,
Lever, Ashby, Workable, SmartRecruiters) — so Indian coverage grows by **adding Indian‑HQ company
slugs to our existing sources**, not by integrating Indian ATS vendors. **Workday** is the notable
gap: many large Indian enterprises use Workday career sites (per‑tenant CxS JSON endpoints), a
potential new ATS integration with high enterprise‑India value but meaningful per‑tenant plumbing.

### 16.4 Staffing companies (India)

| Firm | Public jobs API/feed? | Type | Notes | **Recommendation** |
|---|---|---|---|---|
| TeamLease | No | No Public API | Bulk staffing via own systems | No |
| Quess Corp | No | No Public API | Own portal | No |
| Randstad India | No public India feed | No Public API | Global Randstad, no open API | No |
| Adecco India | No | No Public API | — | No |
| ManpowerGroup India | No | No Public API | — | No |
| Kelly Services India | No | No Public API | — | No |

**Notes.** Major Indian staffing firms **do not expose public job APIs or feeds**; their jobs
surface on their own portals or the consumer boards. No realistic aggregation route. **Not
recommended.**

### 16.5 Regional / niche / sector boards (India)

| Category | Examples | Public API? | **Recommendation** |
|---|---|---|---|
| Regional state boards | Rojgar Sangam (UP), MahaJobs, MP Rojgar, Telangana T‑Jobs | No / open‑data (varies) | Low (fragmented) |
| Tech niche | Cutshort, Instahyre, Hirist, HackerEarth, AngelList/Wellfound | No public API | No |
| Healthcare | Practo Jobs, medical‑council boards | No public API | No |
| Manufacturing / blue‑collar | Apna, WorkIndia, Betterplace | No public API | No |
| Finance / BFSI | BankBazaar careers, bank recruitment portals | No public API (notices only) | No |
| Startup hiring | Wellfound, Cutshort, YC‑India company ATS | ATS route only | Via ATS slugs |
| Campus / graduate | Superset, Unstop, college placement cells | Per‑institution / no API | No (gated) |
| Recruitment consultancies | ABC Consultants, Michael Page India | No public API | No |

**Notes.** The long tail is uniformly **No Public API**; regional government boards are open‑data
at best and fragmented across states. None offer favorable ROI versus the ATS‑slug route.

### 16.6 India sources ranked (Coverage · Data quality · Freshness · Ease · ROI)

Scored Low / Med / High. "ROI" weights legal‑clean, low‑maintenance yield.

| Rank | Source / route | Coverage | Data quality | Freshness | Ease of impl. | **Expected ROI** |
|---:|---|---|---|---|---|---|
| 1 | **ATS slug expansion — Indian‑HQ companies** (Greenhouse/Lever/Ashby/Workable/SmartRecruiters) | Med‑High | **High** | **Good** | **High (reuse)** | **High** |
| 2 | **India query on existing metered/Google‑Jobs sources** (JSearch/OpenWeb Ninja, SerpApi) | Med | High | Good | **High (reuse)** | **High** |
| 3 | **Fantastic Jobs / Active Jobs DB** (paid, incl. India ATS+boards) | High | High | **Excellent** | High | High (budget‑gated) |
| 4 | **Workday India career sites** (new per‑tenant ATS integration) | Med‑High (enterprise) | High | Good | Med‑Hard | Med‑High |
| 5 | **National Career Service open dataset** (data.gov.in) | High (aggregate) | Med | **Poor** | Med (ETL) | Med |
| 6 | **Coresignal / JobsPikr** (enterprise data) | High | High | Good | Med | Med (cost) |
| 7 | **Freshersworld RSS/XML** (if still live) | Low‑Med (freshers) | Med | Med | Low | Low‑Med |
| 8 | State employment portals / OGD per‑state | Med (aggregate) | Med | Poor | **Hard** | Low |
| 9 | Naukri/Foundit/Apna/LinkedIn/Indeed **scraping** | High | High | Good | Med | **Negative** (legal/maintenance) — **avoid** |

**India bottom line.** Prioritize **#1 (ATS slugs) and #2 (India query on existing sources)** —
both free/cheap, legal, low‑maintenance, and reuse code. Consider **#3 (paid aggregator)** for a
step change, and **#5 (NCS dataset)** for authoritative breadth despite poor freshness. Everything
below the line is fragmented, gated, or legally inadvisable.

---

## SECTION 17 — API Filter Optimization Research

This section audits **every currently‑integrated provider** for the filters its API supports, whether
our integration uses them, and what we'd gain by using them. The recurring theme:

> **Most of our integrations deliberately run *unfiltered* "browse everything" queries.** That was
> the right call for a first pass (maximize breadth simply), but it leaves three big levers on the
> table: **(1) date filters** to cut the 46% stale tail at ingest; **(2) location/country filters**
> to target weak regions; and — most powerfully — **(3) query partitioning** (splitting one broad
> query into several filtered ones) to **bypass the hard result‑window caps** that currently limit
> USAJOBS/Bundesagentur/Reed/The Muse/Jooble/Himalayas to the *first* N jobs of a much larger index.

Legend for the per‑provider filter audit: **✓used** (we use it) · **✓avail** (API supports it, we
don't use it) · **✗** (not offered by the API) · **n/a**.

### 17.1 Per‑provider filter audit

**Adzuna** — *Current impl:* `results_per_page=50`, `country=us` only, 40 pages (2,000). No search
filters.
- Location ✓avail (`where`) · Country ✓avail‑but‑fixed (`us` only, path) · Region/City ✓avail
  (`where`) · Keyword ✓avail (`what`,`what_and`,`what_or`,`what_exclude`) · Company ✓avail
  (`company`) · Department ✗ · Category ✓avail (`category`) · Job type ✓avail (`full_time`,
  `part_time`,`contract`,`permanent`) · Salary ✓avail (`salary_min`,`salary_max`) · **Date ✓avail
  (`max_days_old`)** · Remote ✗ (keyword heuristic) · Experience ✗ · Industry ~via category ·
  Pagination page+size · Incremental ✓ (`max_days_old`, `sort_by=date`).
- *Using none of these.* **Biggest opportunity in the whole project:** `country` (multi‑country →
  §10 coverage), `max_days_old` (freshness), `category`/`where` (partition to exceed the effective
  window and target regions). Impact: **very high coverage + freshness**, low complexity.

**Bundesagentur** — *Current impl:* `page`/`size` only (10,000 cap).
- Location ✓avail (`wo`) · Region/City ✓avail (`wo` + `umkreis` radius) · Keyword ✓avail (`was`) ·
  Company ✗ (arbeitgeber filter limited) · Category ✗ · Job type ✓avail (`arbeitszeit`,
  `angebotsart`, `befristung`) · Salary ✗ · **Date ✓avail (`veroeffentlichtseit` = days since
  published)** · Remote ✗ (keyword) · Experience ✗ · Pagination page+size · Incremental ✓
  (`veroeffentlichtseit`).
- *Using none.* `veroeffentlichtseit` → freshness; **partition by `wo`/region or `angebotsart` to
  pull multiple 10k windows and exceed the single‑window cap** (bypass result limit). Impact: high
  coverage (DE) + freshness; medium complexity.

**USAJOBS** — *Current impl:* `Page`/`ResultsPerPage=500` only (10,000 cap).
- Location ✓avail (`LocationName`) · Region/City ✓avail (`LocationName`,`Radius`) · Keyword ✓avail
  (`Keyword`) · Company ✗ (federal agencies via `Organization`) · Category ✓avail
  (`JobCategoryCode` — O*NET series) · Job type ✓avail (`PositionScheduleTypeCode`) · Salary ✓avail
  (`RemunerationMinimumAmount`/Max, `PayGradeLow/High`) · **Date ✓avail (`DatePosted` = days)** ·
  Remote ✓avail (`RemoteIndicator`) · Experience ~via pay grade · Pagination page+size ·
  Incremental ✓ (`DatePosted`).
- *Using none.* **Partition by `JobCategoryCode` or `LocationName` to exceed the 10k window**
  (bypass limit); `DatePosted` → freshness. Impact: medium‑high coverage + freshness; medium
  complexity.

**Reed** — *Current impl:* `resultsToTake=100`/`resultsToSkip` only (~9,000 cap; 500 at boundary).
- Location ✓avail (`locationName`,`distanceFromLocation`) · Keyword ✓avail (`keywords`) · Company
  ✓avail (`employerId`) · Category ✗ (none in response) · Job type ✓avail (`fullTime`,`partTime`,
  `contract`,`temp`,`permanent`) · Salary ✓avail (`minimumSalary`,`maximumSalary`) · Date ✗ (no
  date filter param) · Remote ✗ (keyword) · Pagination take/skip · Incremental ✗.
- *Using none.* **Partition by `keywords`/`locationName`/salary bands to exceed the ~9.9k window**
  (the single biggest way to grow UK volume from Reed); `locationName` also targets UK regions.
  Impact: high UK coverage; medium complexity.

**The Muse** — *Current impl:* `page` only (2,000 unauth cap).
- Location ✓avail (`location`) · Keyword ✗ (no free‑text) · Company ✓avail (`company`) · Category
  ✓avail (`category`) · Level ✓avail (`level`) · Job type ~via category · Date ✗ · Remote ~via
  location "Flexible/Remote" · Pagination page(20) · Incremental ✗.
- *Using none.* **Partition by `category`+`location`+`level` to pull many 2k slices and exceed the
  2,000 unauth window** (bypass limit); adding an **API key** raises the page ceiling too. Impact:
  medium‑high coverage; low‑medium complexity.

**Himalayas** — *Current impl:* basic `/jobs/api` newest‑first, offset/limit(20), 3,000 of 90k.
- A richer **`/jobs/api/search`** endpoint supports: Location/Country ✓avail (`country`,
  `worldwide`) · Keyword ✓avail · Company ✓avail (`companySlug`) · Category ✓avail · Seniority
  ✓avail · Job type ✓avail (`employmentType`) · Timezone ✓avail · Sort ✓avail · Date ~via sort ·
  Remote (all remote).
- *Using none of the search filters.* **Partition by `country`/`category` to pull far more than the
  current 3k of the 90k archive** (bypass the recency cap) and target regions (e.g. LATAM/SEA remote
  roles). Impact: medium‑high coverage; low complexity (same provider).

**Jooble** — *Current impl:* wildcard `keywords=" "`, ~1,100 cap.
- Location ✓avail (`location`,`radius`) · Keyword ✓used(wildcard) · Salary ✓avail (`salary`) ·
  **Date ✓avail (`datecreatedfrom`)** · Company ✗ · Category ✗ · Pagination page+size · Incremental
  ✓ (`datecreatedfrom`).
- *Wildcard only.* **Partition by real `keywords`/`location` to exceed the ~1.1k wildcard window**
  and cut duplicates (targeted queries overlap other providers less); `datecreatedfrom` → freshness.
  Impact: medium coverage + freshness + fewer dupes; low complexity.

**Careerjet** — *Current impl:* wildcard `keywords="jobs"`, `us`‑ish default, 2,000 cap.
- Location ✓avail (`location`) · Country/Region ✓avail (`locale_code` → localized sites incl. UK,
  DE, IN, SEA, LATAM) · Keyword ✓used(wildcard) · Contract ✓avail (`contracttype`,`contractperiod`)
  · Company ✗ · Category ✗ · Salary ✗ · Date ✗ · Pagination page(20).
- *Wildcard/default locale.* **`locale_code` is a cheap way to add regional coverage** (run IN, SG,
  BR, GB locales); keyword partitioning to exceed the 2k cap. Impact: medium coverage; low‑medium
  complexity.

**SerpApi (Google Jobs)** — *Current impl:* wildcard `q="jobs"`, 5 pages (50), metered.
- Location ✓avail (`location`,`uule`) · Keyword ✓used(wildcard) · **Date ✓avail (`chips`
  date_posted=today/3days/week)** · Job type ✓avail (`chips` employment_type) · Remote ✓avail
  (`ltype=1`) · Company ~via q · Pagination token(10).
- *Wildcard only, tiny cap (cost).* Could use `location`/`chips` for targeted, fresh, regional pulls
  — but **metered (250/mo)**, so keep small; best used for a *specific* gap (e.g. a fresh India or
  SEA query) rather than broad. Impact: low volume (cost‑bound), high per‑call relevance.

**OpenWeb Ninja (JSearch)** — *Current impl:* wildcard `query="jobs"`, 5 pages (~50), metered.
- Location/Country ✓avail (`country`) · Keyword ✓used(wildcard) · **Date ✓avail (`date_posted`)** ·
  Job type ✓avail (`employment_types`) · Remote ✓avail (`remote_jobs_only`) · Experience ✓avail
  (`job_requirements`) · Pagination page.
- *Wildcard only, tiny cap (200/mo).* **`country=in` + `date_posted=today` is the cheapest way to
  add fresh India volume** — the highest‑value use of this metered source. Impact: targeted (India
  §16), cost‑bound.

**TheirStack** — *Current impl:* `posted_at_max_age_days=30` (only source already using a date
filter!), capped 50, currently 402.
- Date ✓used · Company ✓avail · Location ✓avail · Remote ✓avail · rich filters; requires ≥1 filter.
- *Blocked by plan (402).* If reinstated, its filters are strong but billing is per‑job — keep
  narrow. Impact: parked.

**ATS sources (Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Teamtailor)** — *Current impl:*
fetch each company's **whole board**; no query filters.
- These public endpoints expose **little/no server‑side filtering** (Greenhouse/Ashby/Workable/
  Teamtailor return the full board; SmartRecruiters supports `limit`/`offset` and some `q`/country
  params; Lever supports `skip`/`limit`). Whole‑board fetch is actually **optimal** here — we *want*
  everything per company. The lever for these is **not filters but the company list** (add slugs;
  §16). Date/region filtering, if needed, is best applied **post‑ingest** (we already have `posted`
  and `location`).

**Arbeitnow / RemoteOK / Jobicy** — small snapshot/whole‑board feeds.
- Arbeitnow: no filters (full board) — fine. RemoteOK: no real filters (tag path param exists but
  volume ~100). **Jobicy:** `geo`, `industry`, `tag` ✓avail (we use `count` only) — `geo` could
  target regions, but total volume is ~100 so impact is negligible.

### 17.2 What the unused filters would buy us

| Lever (filter class) | Providers where unused | Increases coverage? | Improves freshness? | Reduces duplicates? | Bypasses result caps? | Reduces irrelevant jobs? |
|---|---|:--:|:--:|:--:|:--:|:--:|
| **Date** (`max_days_old`/`DatePosted`/`veroeffentlichtseit`/`datecreatedfrom`/`date_posted`) | Adzuna, Bundesagentur, USAJOBS, Jooble, JSearch, SerpApi | — | **Yes (large)** | Slight | — | Slight |
| **Country/locale** (Adzuna path, Careerjet `locale_code`, JSearch `country`, Himalayas `country`) | Adzuna, Careerjet, JSearch, Himalayas | **Yes (large)** | — | — | Partial | Yes |
| **Location/region** (`where`/`wo`/`LocationName`/`locationName`/`location`) | Adzuna, Bundesagentur, USAJOBS, Reed, Muse | Yes | — | — | **Yes (partition)** | Yes |
| **Category/keyword partitioning** | USAJOBS, Reed, Muse, Bundesagentur, Jooble, Careerjet, Himalayas | **Yes (large)** | — | Yes (targeted) | **Yes (main lever)** | Yes |
| **Remote** (`RemoteIndicator`/`remote_jobs_only`/`ltype`) | USAJOBS, JSearch, SerpApi | — | — | — | — | Yes (if remote wanted) |

**Key mechanics.**
- **Query partitioning is the only way to exceed the hard windows** (USAJOBS 10k, Bundesagentur
  10k, Reed ~9.9k, Muse 2k, Jooble ~1.1k, Himalayas 3k‑of‑90k). Splitting one broad query into K
  non‑overlapping filtered queries (by category, location bucket, or date range) yields up to ~K×
  the single‑window ceiling. This is the **highest‑coverage‑upside change available without adding
  providers.**
- **Date filters cut the stale tail at the source** — directly attacking the 46% >30‑day problem
  (§8) for the six providers that support them.
- **Targeted (non‑wildcard) aggregator queries reduce cross‑provider duplication** — the wildcard
  browses on Jooble/Careerjet/SerpApi/JSearch maximize overlap; scoping them lowers it.

### 17.3 Rough impact estimates (planning figures, not guarantees)

| Filter change | Est. useful‑job increase | Est. duplicate change | Est. stale‑job decrease | Complexity |
|---|---|---|---|---|
| Adzuna: multi‑country + `max_days_old` | **+15–25k** net‑new (regions) | Low new dupes | Fewer stale at ingest | **Low** |
| Muse: category×location partitioning (+API key) | +3–8k (beyond 2k cap) | Low | — | Low‑Med |
| Reed: keyword/location partitioning | +5–15k (beyond ~9.9k) | Low | — | Medium |
| USAJOBS: category partitioning + `DatePosted` | +5–15k (beyond 10k) | Low | Fewer stale | Medium |
| Bundesagentur: region partitioning + `veroeffentlichtseit` | +5–15k (DE, beyond 10k) | Low | Fewer stale | Medium |
| Himalayas: switch to `/search` + `country` partition | +5–20k (of the 90k archive) | Low | — | Low |
| Jooble/Careerjet: real keywords + locale/date | +2–5k; **fewer dupes** | **Reduces dupes** | Fewer stale (Jooble date) | Low‑Med |
| JSearch/SerpApi: `country=in`+`date_posted` (India/SEA) | +1–3k targeted (metered) | Low | Fresh only | Low |

*(Ranges are indicative; real yield depends on free‑tier call budgets, partition overlap, and
post‑dedup. Partitioning trades more API calls for more coverage — budget accordingly, §6.5.)*

### 17.4 Prioritized filter improvements (effort vs impact)

**Tier 1 — do first (low effort, high impact)**
1. **Adzuna `country` iteration + `max_days_old`.** One code change unlocks CA/UK/EU/LATAM *and*
   trims stale jobs. Highest impact/effort ratio in the document. *(Low effort.)*
2. **Himalayas → `/jobs/api/search` with `country` partitioning.** Same provider; unlocks far more
   of the 90k archive and regional targeting. *(Low effort.)*
3. **Jooble/Careerjet: replace wildcard with real keyword/locale + date.** Cuts dupes, adds
   regional reach, improves Jooble freshness. *(Low‑med effort.)*
4. **JSearch `country=in`+`date_posted` (and SEA).** Cheapest India/SEA volume from an existing
   metered source. *(Low effort.)*

**Tier 2 — high‑value, moderate effort (window bypass via partitioning)**
5. **The Muse: category×location partitioning (+ API key).** Break the 2k unauth ceiling.
6. **Reed: keyword/location/salary partitioning.** Break the ~9.9k UK ceiling.
7. **USAJOBS: `JobCategoryCode` partitioning + `DatePosted`.** Break the 10k ceiling + freshness.
8. **Bundesagentur: `wo`/region partitioning + `veroeffentlichtseit`.** Break the 10k ceiling +
   freshness.

**Tier 3 — situational / low‑volume**
9. **Jobicy `geo`, RemoteOK tags** — negligible volume; skip unless trivial.
10. **SerpApi targeted `chips`** — reserve scarce quota for a specific fresh/regional gap.

**Not worth changing:** ATS sources (whole‑board fetch is already optimal — grow the *company
list*, not filters); Arbeitnow (full board). For these, apply any date/region **filtering
post‑ingest**, since `posted`/`location` are already in the schema.

**Overall:** the filter work splits cleanly into **(a) "turn on" wins** (date + country/locale
filters we simply aren't sending — Tier 1) and **(b) "partition to bypass caps"** (Tier 2, the
main coverage lever for the hard‑windowed sources). Together they could add **~40–90k useful,
fresher, less‑duplicated jobs without integrating a single new provider** — complementary to, and
cheaper than, most of the new‑source work in §10–§12.

---
---

# CLOSING RESEARCH (Sections 18–19)

*Fourth research pass. Sections 1–17 above are unchanged. Still analysis/research only — no code,
`jobs.py`, `jobs.json`, reports, or charts created or modified; nothing implemented. External
claims verified against official docs/provider sites where possible and flagged where not.*

---

## SECTION 18 — Additional Regional Platform Verification

This section documents named regional platforms that were **investigated and found to be
unsuitable** — either they expose **no public API** (consumer read access), or the only API they
offer is a **partner/employer feed for *posting* jobs** (revenue‑share backfill or job‑insertion),
not a free open feed we could aggregate *from*. Documenting these negative conclusions is
deliberate: it records that the obvious "big regional board" candidates were checked and ruled out,
so implementation time isn't spent rediscovering dead ends.

**Recurring pattern.** The large commercial regional boards almost universally follow one of three
models, none of which gives an aggregator a clean free read feed:
1. **No public API at all** → the only route is scraping (ToS‑risky, fragile) → **Not recommended.**
2. **Partner/Publisher feed** (Talent.com, Jobrapido, Jobillico) → an XML/API for *posting* jobs
   into them or *backfilling from* them under a commercial revenue‑share agreement → **feasible
   only via a paid partnership**, not free/open.
3. **StepStone/SEEK/Info Edge consolidation** → many "different" boards are the same owner behind
   one gated partner API (e.g. TotalJobs/Jobsite/CWJobs = StepStone; JobStreet/JobsDB = SEEK) →
   **one gate, no open consumer API.**

Classification per platform uses: **Official Public API · Partner/Publisher API · Enterprise API ·
RSS Feed · Free tier · Paid · No Public API · Scraping Required · Not Recommended.**

### 18.1 Canada

| Platform | Official/Public API | Partner/Enterprise API | RSS | Free tier | Paid access | Docs | Auth | Legally feasible to integrate? | Scraping required? | **Recommendation** |
|---|---|---|---|---|---|---|---|---|---|---|
| **Eluta** | No | No | No | — | — | None | — | Only via scraping | Yes | **Not recommended** (job search engine, no API) |
| **Workopolis** | No (defunct/redirects to Talent.com) | No | No | — | — | None | — | No | Yes | **Not recommended** (effectively merged into Talent.com) |
| **Jobillico** | No (consumer read) | **Yes — Partner/Employer API (job *insertion*, XML)** | No | No | Paid (posting) | jobillico.com/api/help | key (partner) | Only as a *posting* partner, not for reading listings | No (but wrong direction) | **Not recommended** (API is for posting jobs, not aggregating them) |
| **Talent.com Canada** | No open consumer API | **Yes — Publisher XML feed + self‑serve backfill API** | Feed | No | Paid / revenue‑share | employers.talent.com/publishers | key (partner) | Yes, **only via commercial publisher partnership** | No | **Conditional** — viable only with a paid publisher deal; not free/open |
| **WowJobs** | No | No (Talent.com‑owned aggregator) | No | — | — | None | — | No | Yes | **Not recommended** |

### 18.2 United Kingdom

| Platform | Official/Public API | Partner/Enterprise API | RSS | Free tier | Paid | Docs | Auth | Legally feasible? | Scraping required? | **Recommendation** |
|---|---|---|---|---|---|---|---|---|---|---|
| **TotalJobs** | No | Partner only (StepStone group) | No | — | Paid | Partner‑gated | partner | Only as StepStone partner | Yes (otherwise) | **Not recommended** |
| **CV‑Library** | No open consumer API | **Yes — Partner/Employer API** (posting + CV search) | No | No | Paid | Partner docs | key (partner) | Only via paid partner account | No (wrong direction) | **Not recommended** (partner posting/CV API, not job aggregation) |
| **Jobsite** | No | Partner only (StepStone group) | No | — | Paid | Partner‑gated | partner | Only as partner | Yes | **Not recommended** |
| **CWJobs** | No | Partner only (StepStone group) | No | — | Paid | Partner‑gated | partner | Only as partner | Yes | **Not recommended** |

*(All four UK boards route through StepStone's partner ecosystem — a single gated commercial
channel with no open consumer read API. Use Adzuna `gb` + Reed instead, per §10.3.)*

### 18.3 Europe

| Platform | Official/Public API | Partner/Enterprise API | RSS | Free tier | Paid | Docs | Auth | Legally feasible? | Scraping required? | **Recommendation** |
|---|---|---|---|---|---|---|---|---|---|---|
| **StepStone** | No open consumer API | **Enterprise/Partner API** (api.stepstone.com — ATS/Talentsoft ecosystem) | No | No | Paid | api.stepstone.com (partner KB) | OAuth/partner | Only via partner/enterprise agreement | Yes (otherwise) | **Not recommended** (partner ecosystem, not open job read) |
| **Xing Jobs** | No (legacy public API deprecated) | Partner/Enterprise (New Work SE) | No | — | Paid | Partner‑gated | OAuth partner | Only as partner | Yes | **Not recommended** |
| **Jobrapido** | No open API | **Publisher/Partner feed** (aggregator backfill) | Feed | No | Paid / revenue‑share | Partner‑gated | key (partner) | Only via commercial publisher deal | No | **Conditional** (paid partnership only; it is itself an aggregator ⇒ heavy overlap/dupes) |
| **Welcome to the Jungle** | **No** | No | No | — | — | None (official) | — | Only via scraping | Yes | **Not recommended** (no official API; 3rd‑party scrapers only) |

*(For Europe, prefer Adzuna multi‑country + France Travail + Bundesagentur, per §10.4.)*

### 18.4 LATAM

| Platform | Official/Public API | Partner/Enterprise API | RSS | Free tier | Paid | Docs | Auth | Legally feasible? | Scraping required? | **Recommendation** |
|---|---|---|---|---|---|---|---|---|---|---|
| **Computrabajo** | **No** | No | No | — | — | None | — | Only via scraping | Yes | **Not recommended** (largest LATAM board, but no API) |
| **Bumeran** | **No** | No | No | — | — | None | — | Only via scraping | Yes | **Not recommended** |
| **Get on Board** | **Yes — public API exists** (getonbrd.com) | ATS integrations too | (feeds) | Likely free/low (verify) | — | getonbrd.com (verify endpoint) | key (likely) | **Yes — the one exception here** | No | **Investigate / Add** (LATAM tech; the only LATAM board on this list with a real public API — consistent with §10.7) |
| **OCC Mundial** | **No** | No (Mexico's largest board) | No | — | — | None | — | Only via scraping | Yes | **Not recommended** |

*(For LATAM, prefer Adzuna `br`/`mx` + Get on Board + Himalayas country filter + LATAM ATS slugs,
per §10.7.)*

### 18.5 Southeast Asia

| Platform | Official/Public API | Partner/Enterprise API | RSS | Free tier | Paid | Docs | Auth | Legally feasible? | Scraping required? | **Recommendation** |
|---|---|---|---|---|---|---|---|---|---|---|
| **JobStreet** | No | **Partner only (SEEK group)** | No | — | Paid | Partner‑gated | partner | Only as SEEK partner | Yes (otherwise) | **Not recommended** (dominant SEA board, no public API) |
| **JobsDB** | No | Partner only (SEEK group) | No | — | Paid | Partner‑gated | partner | Only as partner | Yes | **Not recommended** |
| **Kalibrr** | No documented public API | Possibly partner | No | — | — | None (public) | — | Only via scraping | Yes | **Not recommended** |
| **Glints** | **No** | No | No | — | — | None (official) | — | Only via scraping | Yes | **Not recommended** (14M+ users across ID/MY/SG/VN/PH/TW, but 3rd‑party scrapers only) |

*(SEA has no strong free public board API outside MyCareersFuture (SG). The realistic legal route
to deepen the rest of SEA is ATS slug expansion for SEA‑HQ companies, per §10.6.)*

### 18.6 Section 18 conclusion

Across all five regions, **the large commercial boards are consistently closed** to free aggregation
— either no API (Eluta, Workopolis, WowJobs, Welcome to the Jungle, Computrabajo, Bumeran, OCC
Mundial, Glints, Kalibrr) or a **paid partner/posting channel** (Talent.com, Jobillico, CV‑Library,
Jobrapido, StepStone/SEEK families). **The single exception is Get on Board (LATAM)**, which does
expose a public API and remains a genuine candidate. This validates the strategy in §10–§12 and §16:
**growth should come from open ATS feeds (slug expansion), sanctioned developer APIs (Adzuna,
France Travail, MyCareersFuture, USAJOBS, CareerOneStop), and — where budget allows — a paid
aggregator (Fantastic Jobs) that has *already* licensed/normalized these closed sources**, rather
than from scraping the closed regional boards.

---

## SECTION 19 — Final Prioritized Implementation Roadmap

One concise, ranked roadmap consolidating everything above into five priorities. Coverage figures
are net‑new planning estimates (post‑dedup); effort is engineering time; all items are legally clean
(no scraping). **Nothing here is implemented — this is the recommended sequence.**

### Priority 1 — Unlock Adzuna multi‑country + date filter *(the single highest‑ROI change)*
- **Expected coverage increase:** ~**15–25k** net‑new jobs across Canada, UK, and continental
  Europe/LATAM (turns the 3 weakest target regions around at once).
- **Engineering effort:** **Low** (~1 day) — iterate a country list over the existing, already‑keyed
  Adzuna source and add `max_days_old`; no new integration.
- **Maintenance effort:** **Low** (stable commercial API).
- **Business value:** **Very High** — biggest coverage gain per hour of work; also trims stale jobs.
- **Risks:** Free‑tier daily call budget across many countries (mitigate by capping pages/country).
- **Dependencies:** Existing Adzuna key (already present). None else.

### Priority 2 — Freshness foundation: scheduling + `fetched_at` + presence‑diff expiry
- **Expected coverage increase:** **0 new jobs — this is a quality fix**, but it addresses the
  worst dimension (§8: 46% stale, no expiry). Transforms perceived data health.
- **Engineering effort:** **Medium** (~3–5 days) — a scheduler, a per‑job `first_seen`/`last_seen`
  index, and expiry on absence; first real step off the single‑file snapshot.
- **Maintenance effort:** **Medium** (run‑to‑run state to persist and monitor).
- **Business value:** **Very High** — without it, every other gain ages out; enables "last N days"
  UX and dead‑link removal.
- **Risks:** State persistence complexity; needs storage beyond one JSON file eventually.
- **Dependencies:** `fetched_at` capture (do first, ~0.5 day) precedes expiry logic.

### Priority 3 — Coverage for the weak regions: MyCareersFuture + ATS slug expansion + India query
- **Expected coverage increase:** ~**40–70k** net‑new — MyCareersFuture SG (~15k), ATS slug
  expansion across CA/SEA/LATAM/India (~30–60k), India query on existing metered/Google‑Jobs sources
  (~10–20k, overlaps counted).
- **Engineering effort:** **Low–Medium** (MyCareersFuture ~1–2 days no‑auth; slug expansion 2–4 days
  + ongoing; India query ~1 day reuse).
- **Maintenance effort:** **Medium** (ATS slugs rot; MyCareersFuture is an undocumented public
  endpoint that could change).
- **Business value:** **High** — directly fixes Canada/SEA/India, the biggest coverage gaps.
- **Risks:** MyCareersFuture ToS/stability; slug‑list upkeep; metered‑source quotas.
- **Dependencies:** None hard; benefits from a slug‑verification helper.

### Priority 4 — Bypass result‑window caps via query partitioning + France Travail
- **Expected coverage increase:** ~**20–50k** net‑new — partitioning Reed/USAJOBS/The Muse/
  Bundesagentur/Himalayas by category/location/date to extract multiples of their single‑window
  ceilings (§17), plus France Travail (~10k authoritative FR).
- **Engineering effort:** **Medium** (per‑source partition logic; France Travail OAuth 2–3 days).
- **Maintenance effort:** **Low–Medium** (more API calls to budget; partition schemes to maintain).
- **Business value:** **High** — grows volume from providers we *already* run, no new closed‑board risk.
- **Risks:** Higher call volume vs free‑tier budgets; partition overlap needs dedup.
- **Dependencies:** Existing sources; France Travail free registration.

### Priority 5 — Data‑quality & scale hardening: dedup + location normalization + (optional) paid aggregator
- **Expected coverage increase:** Modest net‑new from a paid aggregator if adopted (~50k+,
  budget‑gated); the rest is **quality** — URL normalization + conservative cross‑provider dedup
  (§3), and a location‑normalization layer to shrink the 18% unclassifiable (§1).
- **Engineering effort:** **Medium** (dedup 1–2 days; location layer 3–5 days; aggregator 1–2 days).
- **Maintenance effort:** **Low–Medium** (aggregator cost; normalization rules to tune).
- **Business value:** **Medium–High** — cleaner data powers filters/maps; sets up the move to a
  datastore for scale (§15).
- **Risks:** Dedup false‑merges (guard the multi‑location trap, §3.4); paid‑aggregator cost.
- **Dependencies:** Best after P1–P4 so there's more data to clean; datastore migration for true scale.

### Roadmap summary table

| Priority | Focus | Net‑new jobs | Eng effort | Maint. | Business value | Key risk |
|---|---|---:|---|---|---|---|
| **P1** | Adzuna multi‑country + date | 15–25k | Low | Low | Very High | Call budget |
| **P2** | Freshness (schedule + expiry) | 0 (quality) | Medium | Medium | Very High | State/storage |
| **P3** | Weak regions (SG/ATS/India) | 40–70k | Low‑Med | Medium | High | Slug/ToS upkeep |
| **P4** | Window‑bypass + France Travail | 20–50k | Medium | Low‑Med | High | Call volume |
| **P5** | Dedup/location/paid aggregator | ~quality (+50k opt.) | Medium | Low‑Med | Med‑High | False‑merge/cost |

### Conclusion — what to build first with only two weeks of engineering time

With a **two‑week budget**, spend it on the changes that are cheap, legally clean, and hit the two
worst problems (coverage skew and staleness) hardest — deliberately **not** on new closed‑board
integrations:

1. **Days 1–2 — Priority 1 (Adzuna multi‑country + `max_days_old`).** One change, ~20k net‑new jobs,
   fixes Canada/UK/Europe/LATAM coverage immediately. Highest ROI available.
2. **Days 2–3 — capture `fetched_at`** and add a "data as of X / last N days" signal (front half of
   Priority 2) — cheap, and it makes freshness honest right away.
3. **Days 3–6 — Priority 2 core: scheduling + presence‑diff expiry.** Fixes the 46% stale problem and
   stops dead‑link accumulation — the biggest *quality* win.
4. **Days 6–9 — Priority 3 first slice: MyCareersFuture (SG)** + a **first batch of Indian/SEA/Canada
   ATS slugs** on the existing ATS sources. Directly fills the biggest regional gaps, low effort.
5. **Days 9–12 — one window‑bypass partition (Priority 4)** on the highest‑value capped source
   (Reed for UK, or The Muse) as a proof‑of‑pattern, plus **URL normalization in dedup** (front half
   of Priority 5) to keep the new volume clean.
6. **Days 12–14 — integration testing, dedup verification, and budget/rate‑limit tuning** across the
   newly added country/slug passes.

This sequence realistically adds **~40–70k net‑new, better‑distributed jobs and fixes freshness**
within two weeks, **without any scraping or new commercial contracts** — deferring France Travail,
full window‑partitioning, the location‑normalization layer, the paid aggregator, and the datastore
migration to the following iteration. In short: **turn on the filters and countries we already have
access to, make the data refresh and expire, and plug the worst regional gaps with the one no‑auth
government API and our existing ATS machinery — before spending effort or money on anything new.**
