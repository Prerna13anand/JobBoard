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
