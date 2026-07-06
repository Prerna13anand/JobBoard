# Job Aggregation Platform — Analytics Summary

**Prepared for:** Engineering & Product Management
**Data source:** `jobs.json` (155,794 unique job records, latest pipeline run)
**Reference document:** `research/api_analysis.md` (regional, freshness, duplicate, and API
research — this report computes and presents the management-facing numbers; see that document
for full methodology, provider-by-provider detail, and expansion recommendations)
**Snapshot date:** newest `posted` value in the data is 2026-07-03; "today" for age calculations
is 2026-07-06.

---

## Executive Summary

The platform aggregates **155,794 unique jobs** from **20 registered providers** (19 currently
contributing) into a single normalized schema. Coverage is broad but **heavily concentrated**:
one region (United States, 51%) and one provider (SmartRecruiters, 41.8%) dominate the dataset,
and a single employer (Domino's) alone accounts for **15.7% of all jobs**. Deduplication is
working correctly — **zero duplicate URLs remain** — though a large volume of same-title,
same-company postings reflects genuine multi-location retail/logistics roles rather than
aggregation errors. Freshness is moderate: **54% of jobs were within 30 days old at collection
time**, but **46% are stale**, with no scheduled refresh or expiry in place to keep that ratio
from worsening. Remote roles are a small minority (10.9%). The dataset is production-ready as a
periodic bulk job board; the highest-value next steps are broadening regional/provider balance
and introducing a refresh-and-expiry cycle (see `research/api_analysis.md` §§14, 19 for the
detailed roadmap).

---

## Dataset Overview

| Metric | Value |
|---|---:|
| Total unique jobs | **155,794** |
| Registered providers | 20 |
| Providers contributing in latest run | 19 (TheirStack blocked — HTTP 402 plan restriction) |
| Distinct companies represented | **9,497** |
| Jobs with empty/missing company name | 45 (0.03%) |
| Jobs with empty/missing location | 72 (0.05%) |
| Jobs with empty `tags` | 11,762 (7.5%) |
| Jobs with a parseable `posted` date | 155,779 (99.99%) |
| Duplicate URLs remaining in dataset | **0** |
| Schema fields | `title`, `company`, `location`, `url`, `tags`, `remote`, `posted` (7 fields, fully normalized) |

The dataset is a **static snapshot** — a single JSON file rewritten on each full pipeline run,
with no incremental sync, no per-job history, and no expiry mechanism.

---

## Regional Coverage

| Region | Jobs | % of dataset |
|---|---:|---:|
| United States | 79,427 | 51.0% |
| Europe (continental, non-UK) | 21,886 | 14.0% |
| United Kingdom | 10,305 | 6.6% |
| LATAM | 6,955 | 4.5% |
| Singapore / Southeast Asia | 4,629 | 3.0% |
| Canada | 3,436 | 2.2% |
| Remote / Worldwide (no fixed region) | 822 | 0.5% |
| Other / Unclassified location text | 28,334 | 18.2% |

**Sum of the six primary target regions: 126,638 jobs (81.3%)** of the dataset.

**Top countries by job count:**

| Rank | Country | Jobs | % |
|---:|---|---:|---:|
| 1 | United States | 79,427 | 51.0% |
| 2 | Germany | 12,167 | 7.8% |
| 3 | United Kingdom | 10,305 | 6.6% |
| 4 | India | 3,471 | 2.2% |
| 5 | Canada | 3,436 | 2.2% |
| 6 | France | 2,218 | 1.4% |
| 7 | China | 1,435 | 0.9% |
| 8 | Australia | 1,225 | 0.8% |

**Observation:** the United States alone exceeds the combined total of every other region.
Canada is the weakest of the six primary target regions at 2.2% — under half the size of the
UK's dedicated coverage despite both being first-class targets. 18.2% of jobs carry location
text too ambiguous to classify into a region, which caps the reliability of any location-based
filter or map feature at its current form.

---

## Provider Coverage

Provider attribution reconstructed from each job's URL host (the schema does not carry an
explicit `source` field):

| Provider | Jobs | % of dataset |
|---|---:|---:|
| SmartRecruiters | 65,193 | 41.8% |
| Lever | 17,755 | 11.4% |
| Greenhouse (both hosts) | 14,930 | 9.6% |
| USAJOBS | 10,000 | 6.4% |
| Reed | 9,000 | 5.8% |
| Bundesagentur (+ AMS) | ~7,800 | ~5.0% |
| Ashby | 5,171 | 3.3% |
| Workable | 4,159 | 2.7% |
| Jooble | ~3,100 | ~2.0% |
| Himalayas | 2,964 | 1.9% |
| Adzuna | 2,001 | 1.3% |
| The Muse | 2,000 | 1.3% |
| Arbeitnow | 930 | 0.6% |
| Teamtailor | 474 | 0.3% |
| SerpApi, OpenWeb Ninja, Careerjet, RemoteOK, Jobicy (combined) | ~350 | ~0.2% |
| TheirStack | 0 | 0.0% (plan-gated, HTTP 402) |

**Observation:** a single provider, SmartRecruiters, supplies **more than 4 in 10 jobs** in the
entire dataset. The top three providers (SmartRecruiters, Lever, Greenhouse) together account
for **62.8%** of all jobs. Regional and company composition is therefore driven largely by
*which companies were curated into these ATS provider lists*, not by a balanced global crawl.
Six metered/low-yield sources (SerpApi, OpenWeb Ninja, Careerjet, RemoteOK, Jobicy, Arbeitnow)
combined contribute under 1% of total volume.

---

## Job Freshness

Age measured against the dataset's collection date (2026-07-03):

| Age at collection | Jobs | Cumulative "within" | Cumulative % |
|---|---:|---:|---:|
| Within 24 hours | 24,052 | 24,052 | 15.4% |
| Within 3 days | +6,582 | 30,634 | 19.7% |
| Within 7 days | +11,884 | 42,518 | 27.3% |
| Within 14 days | +24,610 | 67,128 | 43.1% |
| Within 30 days | +16,949 | 84,077 | **54.0%** |
| Older than 30 days | 71,702 | — | **46.0%** |
| Unknown / unparseable | 15 | — | 0.0% |

**Total current jobs (≤ 30 days): 84,077 → 54.0% of the dataset.**
**Total stale jobs (> 30 days, incl. unknown): 71,717 → 46.0% of the dataset.**

**Deep-stale tail:**

| Age | Jobs | % |
|---|---:|---:|
| Older than 90 days | 45,075 | 28.9% |
| Older than 180 days | 29,640 | 19.0% |
| Older than 365 days | 21,768 | 14.0% |

Oldest posting on record: **2009-12-05**. Median posting date: **2026-06-09**.

**Observation:** at collection time, a slim majority of the dataset was fresh, but nearly half
is already stale, and 14% is over a year old. The dataset has **no scheduled refresh and no
expiry logic**, so this ratio only worsens with time — every day since collection, the "current"
fraction shrinks with no offsetting mechanism. This is a structural/architectural issue rather
than a sourcing issue: it is concentrated in large enterprise ATS boards that return every
currently-open requisition, including long-standing evergreen roles.

---

## Duplicate Analysis

| Check | Result |
|---|---:|
| Exact-URL duplicates remaining | **0** |
| Jobs with empty URL | **0** |
| Title + company collisions ("apparent duplicates") | 35,300 extra rows across 11,340 groups |
| Title + company + location collisions | 8,290 extra rows across 4,963 groups |
| Title+company groups spanning more than one distinct URL | 11,340 (100% of those groups) |

**Observation:** the pipeline's URL-based deduplication is working exactly as intended — zero
duplicate URLs and zero empty URLs remain. The 35,300 title+company "collisions" are **not**
missed duplicates: every one of those 11,340 groups spans multiple distinct URLs, and inspection
shows they are overwhelmingly **the same role posted at hundreds of separate physical
locations** (see Company Distribution below — Domino's "Delivery Driver," BoxLunch "Sales
Associate," etc.). Applying a naive title+company dedup rule would have erased tens of thousands
of legitimate, distinct job openings. The real (and much smaller) duplicate risk is
cross-provider overlap between aggregator-style sources, which current URL-keyed dedup does not
directly measure.

---

## Remote Jobs

| Metric | Value |
|---|---:|
| Jobs marked `remote: true` | 16,992 |
| Share of dataset | **10.9%** |
| Jobs marked `remote: false` | 138,802 (89.1%) |

**Observation:** roughly 1 in 9 jobs in the dataset is remote. Several sources are remote-only
by construction (Himalayas, RemoteOK, Jobicy), while most others derive `remote` either from a
genuine API field (Ashby, Lever, Workable, SmartRecruiters, Teamtailor, USAJOBS, SerpApi,
OpenWeb Ninja, TheirStack, Himalayas, RemoteOK, Jobicy) or a keyword heuristic on
title/location (Adzuna, Bundesagentur, Jooble, Reed, Greenhouse, Careerjet). Given only ~11% of
the dataset is remote, location quality (see Regional Coverage) is materially important for the
vast majority of listings.

---

## Company Distribution

| Metric | Value |
|---|---:|
| Distinct companies in dataset | **9,497** |
| Companies with exactly 1 job (long tail) | 5,505 (58.0% of distinct companies) |
| Share of dataset held by top 10 companies | 58,922 jobs — **37.8%** |
| Share of dataset held by top 25 companies | 74,061 jobs — **47.5%** |
| Share of dataset held by top 100 companies | 99,334 jobs — **63.8%** |

**Top companies by job count:**

| Rank | Company | Jobs | % of dataset |
|---:|---|---:|---:|
| 1 | Domino's | 24,448 | 15.69% |
| 2 | AccorHotel | 5,695 | 3.66% |
| 3 | AECOM | 4,802 | 3.08% |
| 4 | Bosch Group | 4,655 | 2.99% |
| 5 | ProSidian Consulting, LLC | 4,003 | 2.57% |
| 6 | BoxLunch | 3,512 | 2.25% |
| 7 | TSMG | 3,430 | 2.20% |
| 8 | Veterans Health Administration | 3,109 | 2.00% |
| 9 | Jobs for Humanity | 3,098 | 1.99% |
| 10 | Anduril Industries | 2,170 | 1.39% |

**Observation:** company concentration is extreme at the top. **Domino's alone represents
15.7% of every job in the entire platform** — nearly one in six listings — because its
SmartRecruiters board lists each store-level opening (delivery driver, assistant manager, etc.)
as a separate posting across thousands of locations nationwide. The top 10 companies alone
account for **37.8%** of the dataset. At the other extreme, the median company contributes very
little: 58% of all distinct companies (5,505 of 9,497) appear with only a single job. This
bimodal distribution — a handful of very large multi-location employers plus a long tail of
single-posting companies — is the direct cause of the "duplicate-looking" title+company
collisions discussed above.

---

## API Coverage

| Metric | Value |
|---|---:|
| Total registered providers | 20 |
| Phase 1 — no-auth APIs | 6 (Arbeitnow, Himalayas, RemoteOK, Jobicy, The Muse, Bundesagentur) |
| Phase 2 — API-key providers | 8 (Jooble, USAJOBS, Adzuna, Reed, SerpApi, OpenWeb Ninja, Careerjet, TheirStack) |
| Phase 3 — ATS/company-based providers | 6 (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Teamtailor) |
| Providers currently contributing jobs | 19 |
| Providers currently blocked | 1 (TheirStack — account plan lacks Jobs API access, HTTP 402) |
| Providers with a hard result-window cap already reached | 3 (USAJOBS 10,000; Bundesagentur 10,000; Reed ~9,000, near its ~9,900 ceiling) |
| Providers deliberately throttled for cost (metered/paid) | 3 (SerpApi 50/run, OpenWeb Ninja ~50/run, TheirStack 50/run when active) |
| Providers using company-curated lists rather than a global index | 6 (all Phase 3 ATS sources) |

**Observation:** the pipeline already exercises most providers close to their practical ceiling
— three sources are capped by the API's own result-window limit, and three more are
deliberately kept small to control metered-API cost. The six ATS providers, which supply the
majority of total volume, grow only by manually adding verified company slugs — there is no
query-based way to expand their reach. Full per-provider detail (auth, rate limits, filters) is
documented in `research/api_analysis.md` §§4 and 9.

---

## Key Findings

1. **Regional concentration:** the United States accounts for 51% of the dataset; Canada (2.2%)
   and Singapore/SEA (3.0%) are the weakest of the six primary target regions.
2. **Provider concentration:** SmartRecruiters alone supplies 41.8% of all jobs; the top three
   providers together supply 62.8%.
3. **Company concentration:** a single employer, Domino's, accounts for 15.7% of the entire
   dataset — more than any other company by an order of magnitude.
4. **Deduplication is correct:** 0 duplicate URLs remain; apparent title+company "duplicates"
   are legitimate multi-location postings, not aggregation errors.
5. **Freshness is moderate but degrading:** 54% of jobs were current (≤30 days) at collection,
   but 46% are stale and 14% are over a year old, with no refresh schedule or expiry logic to
   prevent further decay.
6. **Remote coverage is thin:** only 10.9% of jobs are remote, making location data quality
   important for the large majority of the dataset.
7. **18.2% of jobs have unclassifiable location text**, limiting the reliability of any
   region-based filter, count, or map feature.
8. **One provider (TheirStack) currently contributes zero jobs** due to an account/plan
   restriction unrelated to code.
9. **Company distribution is bimodal:** 58% of all 9,497 distinct companies contribute exactly
   one job each, while a handful of large multi-location employers dominate total volume.

---

## Recommendations

*(Summarized here for management visibility; full reasoning, effort estimates, and a
prioritized roadmap are in `research/api_analysis.md` §§6, 14, and 19.)*

1. **Broaden regional balance**, particularly Canada, UK resilience, and Singapore/SEA, by
   extending already-integrated providers (e.g., enabling additional country configurations on
   existing keyed sources) rather than adding entirely new integrations.
2. **Introduce a refresh schedule and expiry mechanism** so the freshness ratio stops degrading
   between runs and dead/closed postings are retired automatically.
3. **Grow the ATS company-slug lists** for under-represented regions to rebalance provider and
   regional concentration without new integration work.
4. **Do not deduplicate on title+company alone** — doing so would remove tens of thousands of
   legitimate multi-location jobs (e.g., Domino's, BoxLunch); any future duplicate-reduction
   effort should be scoped conservatively (URL normalization plus location-aware matching).
5. **Improve location-text normalization** to shrink the 18.2% unclassifiable bucket and make
   regional filtering and reporting more reliable.
6. **Revisit the TheirStack account/plan** to restore its contribution, or formally retire it
   from the active provider list if the plan restriction is permanent.
7. **Monitor concentration risk**: with 41.8% of jobs from one provider and 15.7% from one
   company, any change to SmartRecruiters' Domino's board would materially shift dataset-wide
   statistics — worth tracking as a data-quality signal in future runs.

---

## Recent Job Market Analysis (≤ 30 Days)

**Scope note:** every figure below is computed from the same **84,077-job** slice already
established in the Job Freshness section above (jobs posted within 30 days of the dataset's
2026-07-03 collection date — 54.0% of the full 155,794-job dataset). Jobs older than 30 days are
excluded entirely from this section. Categories and regions are computed directly from each job's
`title`/`location` text; provider is reconstructed from the job's URL host, consistent with the
methodology used throughout this report.

### 1. Job Category Distribution

Every recent job was classified into a business-friendly category using its title (and tags where
informative). The suggested taxonomy skews toward professional/technical roles; because this
dataset is heavily weighted toward retail, hospitality, food-service, and driving/logistics
postings (see Company Distribution below), a large share of recent jobs do not map cleanly onto
that taxonomy and are honestly reported as **Other** rather than forced into a poor-fitting bucket.

| Category | Recent Jobs | % of recent |
|---|---:|---:|
| Other | 44,858 | 53.4% |
| Supply Chain | 7,531 | 9.0% |
| Software Engineering | 5,571 | 6.6% |
| Customer Support | 5,264 | 6.3% |
| Healthcare | 3,505 | 4.2% |
| Sales | 2,888 | 3.4% |
| Executive | 1,570 | 1.9% |
| Education | 1,474 | 1.8% |
| Accounting | 1,224 | 1.5% |
| Project Management | 994 | 1.2% |
| Internship / Graduate | 911 | 1.1% |
| Manufacturing | 792 | 0.9% |
| Human Resources | 779 | 0.9% |
| Marketing | 755 | 0.9% |
| Product Management | 576 | 0.7% |
| Finance | 525 | 0.6% |
| DevOps / Cloud | 517 | 0.6% |
| Data Science / Analytics | 511 | 0.6% |
| Legal | 399 | 0.5% |
| Business Development | 392 | 0.5% |
| Cybersecurity | 374 | 0.4% |
| Administrative | 334 | 0.4% |
| Customer Success | 302 | 0.4% |
| AI / Machine Learning | 299 | 0.4% |
| Digital Marketing | 293 | 0.3% |
| Operations | 274 | 0.3% |
| Procurement | 272 | 0.3% |
| Recruiting | 250 | 0.3% |
| IT Support | 219 | 0.3% |
| UI / UX Design | 174 | 0.2% |
| Government | 102 | 0.1% |
| Pharmaceutical | 77 | 0.1% |
| Graphic Design | 71 | 0.1% |

![Recent Job Category Distribution](charts/recent_category_distribution.png)

**Top hiring categories:** excluding the Other catch-all, **Supply Chain** (9.0% — driven by
delivery-driver and warehouse/despatch roles), **Software Engineering** (6.6%), and **Customer
Support** (6.3%) are the three largest identifiable categories among recent postings, followed by
**Healthcare** (4.2%) and **Sales** (3.4%). Inspection of the Other bucket confirms it is
dominated by retail, hospitality, and food-service titles (e.g., "Barista," "Tesco Colleague,"
"Kitchen Porter," "Assistant Manager") that fall outside the given professional/technical taxonomy
— this is a data-composition finding, not a classification gap.

### 2. Recent Jobs by Region

| Region | Recent Jobs | % of recent |
|---|---:|---:|
| United States | 39,124 | 46.5% |
| Europe | 15,721 | 18.7% |
| Other | 14,372 | 17.1% |
| United Kingdom | 6,925 | 8.2% |
| LATAM | 2,886 | 3.4% |
| Singapore / Southeast Asia | 1,744 | 2.1% |
| India | 1,656 | 2.0% |
| Canada | 1,649 | 2.0% |

![Recent Jobs by Region](charts/recent_region_distribution.png)

**Strongest current hiring activity:** the United States dominates recent postings (46.5%),
followed by Europe (18.7%, still Germany-heavy via Bundesagentur) and the UK (8.2%, almost
entirely Reed, which is 96.2% fresh — see below). Canada, India, and Singapore/Southeast Asia
each sit at only ~2% of recent volume — consistent with the regional coverage gaps already
identified in `research/api_analysis.md`, and a reminder that these regions are thin in *both*
total volume and freshness.

### 3. Recent Jobs by Provider

| Provider | Recent Jobs | % of recent | Freshness rate (share of provider's own total that is recent) |
|---|---:|---:|---:|
| SmartRecruiters | 36,479 | 43.4% | 56.0% |
| Reed | 8,658 | 10.3% | 96.2% |
| Bundesagentur | 7,800 | 9.3% | 100.0% |
| USAJOBS | 6,138 | 7.3% | 61.4% |
| Other (SerpApi, OpenWeb Ninja, CareerJet, TheirStack, misc.) | 5,091 | 6.1% | 50.4% |
| Greenhouse | 5,013 | 6.0% | 33.6% |
| Jooble | 2,973 | 3.5% | 95.1% |
| Himalayas | 2,964 | 3.5% | 100.0% |
| Lever | 2,653 | 3.2% | 14.9% |
| Ashby | 1,688 | 2.0% | 32.6% |
| Adzuna | 1,467 | 1.7% | 73.3% |
| Workable | 1,232 | 1.5% | 29.6% |
| Arbeitnow | 930 | 1.1% | 100.0% |
| The Muse | 615 | 0.7% | 30.8% |
| Teamtailor | 176 | 0.2% | 38.6% |
| Jobicy | 100 | 0.1% | 100.0% |
| RemoteOK | 100 | 0.1% | 100.0% |

![Recent Jobs by Provider](charts/recent_provider_distribution.png)

**Freshest-contributing providers:** by share of recent volume, SmartRecruiters (43.4%), Reed
(10.3%), and Bundesagentur (9.3%) contribute the most fresh jobs in absolute terms. By
**freshness rate** — the more diagnostic metric, showing what fraction of a provider's *own*
total inventory is recent — five providers are effectively 100% fresh: **Bundesagentur,
Himalayas, Arbeitnow, RemoteOK, and Jobicy**, all of which are newest-first, single-snapshot, or
short-window APIs by construction. **Reed (96.2%)** and **Jooble (95.1%)** are also excellent. At
the other end, **Lever (14.9%)**, **Workable (29.6%)**, **The Muse (30.8%)**, **Ashby (32.6%)**,
and **Greenhouse (33.6%)** have the lowest freshness rates — consistent with the earlier finding
that ATS boards return every currently open requisition, including long-standing evergreen roles,
regardless of when the pipeline last ran.

### 4. Recent Jobs by Company

| Rank | Company | Recent Jobs | % of recent |
|---:|---|---:|---:|
| 1 | Domino's | 20,620 | 24.5% |
| 2 | AccorHotel | 3,397 | 4.0% |
| 3 | AECOM | 2,297 | 2.7% |
| 4 | Bosch Group | 1,900 | 2.3% |
| 5 | Veterans Health Administration | 1,675 | 2.0% |
| 6 | Anduril Industries | 817 | 1.0% |
| 7 | Northwestern Memorial Healthcare | 751 | 0.9% |
| 8 | Reed | 689 | 0.8% |
| 9 | SpaceX | 681 | 0.8% |
| 10 | Delivery Hero | 599 | 0.7% |
| 11 | eFinancialCareers | 514 | 0.6% |
| 12 | Primark | 454 | 0.5% |
| 13 | ASSYSTEM | 417 | 0.5% |
| 14 | Tesco | 396 | 0.5% |
| 15 | AUREA GmbH | 341 | 0.4% |
| 16 | Boyd Gaming | 335 | 0.4% |
| 17 | Munson Healthcare | 328 | 0.4% |
| 18 | NielsenIQ | 324 | 0.4% |
| 19 | Hays Specialist Recruitment Limited | 320 | 0.4% |
| 20 | Continental | 309 | 0.4% |

![Top 20 Companies — Recent Openings](charts/recent_top_companies.png)

**Concentration:** recent hiring is **more concentrated than the dataset as a whole**. The top 10
companies account for 39.8% of all recent postings (vs. 37.8% dataset-wide), and Domino's alone
is 24.5% of every recent job — up from 15.7% dataset-wide — because Domino's postings refresh
very frequently (each store-level requisition is re-surfaced often), while many other large
employers' boards (e.g., Lever- and Greenhouse-hosted companies) contain a larger share of older,
still-open listings. There are 8,999 distinct companies among recent postings (vs. 9,497
dataset-wide), and the same bimodal pattern holds: a handful of very large, frequently-refreshed
employers alongside a long tail of single-posting companies.

### 5. Fresh Job Recommendations

- **APIs producing the freshest data:** Bundesagentur, Himalayas, Arbeitnow, RemoteOK, and Jobicy
  are effectively 100% fresh, because each either returns only newest-first results within a small
  window (Himalayas, Arbeitnow) or is a small, frequently-turning-over snapshot by construction
  (RemoteOK, Jobicy). Reed (96.2%) and Jooble (95.1%) are close behind.
- **Providers that mostly return older jobs:** Lever (14.9% fresh), Workable (29.6%), The Muse
  (30.8%), Ashby (32.6%), and Greenhouse (33.6%) skew toward stale inventory — all five are
  full-board ATS/API fetches that return every currently open requisition regardless of posting
  age, so a large share of what they return was already old at the time of the most recent run.
- **Providers that should be refreshed more frequently:** the same five low-freshness-rate
  providers (Lever, Workable, The Muse, Ashby, Greenhouse) benefit least from *more frequent runs
  alone*, since re-running them mainly re-fetches the same long-lived postings — for these, the
  fix is date-aware filtering or incremental sync (below), not just a tighter schedule.
- **Providers that should be synchronized daily:** the high-freshness-rate, high-volume providers
  — SmartRecruiters, Reed, Bundesagentur, USAJOBS, Jooble — justify a daily (or more frequent)
  sync, since their own APIs are already turning over quickly and a daily run would capture that
  turnover instead of losing it between longer intervals.
- **Providers that would benefit from incremental synchronization:** USAJOBS (`DatePosted`),
  Adzuna (`max_days_old`), Jooble (`datecreatedfrom`), Bundesagentur (`veroeffentlichtseit`), and
  TheirStack (`posted_at_max_age_days`, already partially used) all expose a genuine date-filter
  parameter today that is either unused or only partly used — these are the cheapest wins for
  incremental sync, since the capability already exists in the API (see
  `research/api_analysis.md`, Section 17).

### 6. Engineering Recommendations (Freshness-Focused)

- **Date filtering:** turn on the date filters already supported by USAJOBS, Adzuna, Bundesagentur,
  Jooble, and TheirStack to exclude stale postings at ingest time rather than after the fact —
  directly reduces the low freshness rates seen in this section without any new integration.
- **Incremental synchronization:** persist a per-job `first_seen`/`last_seen` watermark (using
  `createdAt`/`publishedAt`/`releasedDate`, already returned by every ATS provider) so runs can
  detect and retire postings that silently disappeared, rather than re-fetching a full board every
  time. This is the single biggest lever for the low-freshness ATS providers (Lever, Workable, The
  Muse, Ashby, Greenhouse), none of which expose a request-side date filter — the only path to
  "freshness" for these is diffing what changed between runs.
- **Region splitting:** partitioning broad, single-query providers (Adzuna, Bundesagentur, USAJOBS,
  Reed) by country/region multiplies effective coverage *and* lets each partition be scheduled and
  filtered independently by recency — a region that refreshes faster (e.g., UK via Reed) need not
  wait on a slower one.
- **Keyword searches:** replacing wildcard queries (Jooble, Careerjet, SerpApi, OpenWeb Ninja) with
  real, targeted keywords tends to surface different, often more recent, postings than a generic
  broad browse, and reduces duplication with other aggregators at the same time.
- **Company-based searches:** for the six ATS providers (Greenhouse, Lever, Ashby, SmartRecruiters,
  Workable, Teamtailor), freshness cannot be improved via query parameters — there are none — so
  the lever is exclusively adding/pruning company slugs and, more importantly, diffing each
  company's board run-over-run to detect closed postings.
- **Category searches:** partitioning The Muse, USAJOBS, and Himalayas by category alongside date
  ordering would let each category-specific query surface its own newest postings rather than
  being crowded out by a single large unfiltered result set.

**Estimated freshness improvement:** applying date filters and incremental sync to the five
providers identified above (USAJOBS, Adzuna, Bundesagentur, Jooble, TheirStack once restored) and
introducing run-over-run diffing for the five low-freshness ATS providers (Lever, Workable, The
Muse, Ashby, Greenhouse) would directly target the ~46,000 jobs in this dataset that are currently
older than 30 days despite coming from providers capable of returning newer results. A realistic
outcome is raising the **overall ≤30-day-fresh share from the current 54.0% into the high-60s to
low-70s percent range**, without adding a single new provider — the ceiling is bounded by how much
genuinely new inventory each provider's underlying job market produces per period, not by anything
in this pipeline.
