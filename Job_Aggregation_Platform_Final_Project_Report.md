# Job Aggregation Platform — Final Project Report

**Internal Engineering Report · Data Platform**

| | |
|---|---|
| **Prepared for** | Engineering Manager |
| **Prepared by** | Reuben Jacob |
| **Report date** | July 16, 2026 |
| **Data snapshot as of** | Latest verified execution of all 46 providers (an earlier baseline collection preceded it — Section 3.2) |
| **Companion document** | `Final_Project_Report_v2.md` (full technical detail, methodology, and evidence trail) |

This is a condensed version of `Final_Project_Report_v2.md`, written for a single reading in approximately 15–20 minutes. No technical finding has been removed — long narrative explanations have been replaced with tables, and repeated explanations have been cut. All figures are sourced from this project's PostgreSQL database, source code, and `job_api.xlsx` research workbook (API Catalog and Sheet1). Where a fact could not be verified from these sources, this report states **"Not publicly available"** or **"Not verified during this project"** rather than estimating.

---

## Contents

1. [Project Overview](#1-project-overview)
2. [Project Status](#2-project-status)
3. [Implemented APIs](#3-implemented-apis)
4. [Complete Provider Research (268 Providers)](#4-complete-provider-research-268-providers)
5. [Internship Requirement Coverage](#5-internship-requirement-coverage)
6. [Final Recommendations](#6-final-recommendations)

---

## 1. Project Overview

**Purpose.** Build a single, de-duplicated, queryable dataset of job postings, sourced from as many legitimately accessible providers as possible, normalized into one schema with country and remote/hybrid/on-site classification, and persisted in a real database rather than a flat file.

**Scope.** The project researched **268 job-related APIs, ATS platforms, and job boards** (government labour agencies, commercial aggregators, ATS platforms, and job boards), narrowed that list to an **86-provider shortlist** for close audit, and built **46 working integrations** against a shared `sources/` interface (`BaseJobSource`). Every researched provider — implemented or not — is documented with a specific, evidence-based reason (Section 4).

**Final outcome.**

- **46 providers implemented**; **41 have contributed live data** to PostgreSQL across an initial baseline collection and a later verification re-run; **40 of 46 were confirmed working in the latest re-run** (Section 3.2).
- **241,564 unique job records** stored, deduplicated by URL/hash, with per-provider run history.
- **Offline country and work-arrangement normalization** — no paid geocoding service used.
- The remaining **222 researched providers** were not implemented for specific, documented reasons: no public API, enterprise/partner-only access, wrong data-flow direction (employer-posting tools, not read APIs), deprecated services, or a registration/verification step not yet completed.
- The platform has been run twice as a **manual, one-off collection** (an initial baseline, then a verification re-run) — not yet on a recurring automated schedule. It is ready for operational hardening, not further architecture, before production use.

---

## 2. Project Status

| Area | Status | Detail |
|---|---|---|
| Provider research (268 researched, 86 shortlisted) | Completed | Every provider carries a documented reason for its outcome (Section 4) |
| 46 provider integrations (shared `BaseJobSource` interface) | Completed | One module per provider under `sources/` |
| PostgreSQL persistence (`jobs`, `provider_runs` tables) | Completed | Upsert-on-`dedup_key`, idempotent schema |
| Deduplication (URL/hash-based) | Completed | 0 cross-provider duplicate URLs remaining |
| Offline country normalization | Completed | Multi-country/region text forced to `NULL` rather than guessed |
| Work-arrangement classification (remote/hybrid/on-site) | Completed | Derived from location text and provider-native flags |
| `jobs.json` static export + frontend search/filter | Completed | Unchanged since Milestone 2 |
| Per-source fault isolation | Completed | One broken provider cannot halt a run |
| 40 of 46 providers confirmed working in the latest re-run | Partially Completed | 6 did not contribute in the latest run — billing, missing credentials, quota exhaustion, and one IP-allowlist regression (CareerJet, previously live) — Section 3 |
| Employment-type capture | Partially Completed | Present for 24 of 46 providers; absent for the rest |
| Country resolution long tail | Partially Completed | Multi-country case solved; ~1,565 distinct unresolved single-place values remain |
| Credentialed-provider setup | Partially Completed | 2 of 12 credentialed providers lack credentials in this environment — Trade Me pending its approval process; CareerOneStop's registration is geographically restricted (geo-blocked) from this environment |
| 6 real, accessible candidate providers (Saramin, VDAB, CBOP, Work24, GOV.UK Find a Job, Job-Room Switzerland) | Partially Completed | Registration/verification step outstanding, not rejected |

---

## 3. Implemented APIs

### 3.1 Lifecycle summary

| Stage | Count |
|---|---:|
| Providers researched (API Catalog sheet, `job_api.xlsx`) | 268 |
| Providers shortlisted for close audit (Sheet1, `job_api.xlsx`) | 86 |
| Providers implemented (`sources/*.py`, registered in `sources/__init__.py`) | 46 |
| Providers that have ever contributed live data (across both runs) | 41 |
| Providers confirmed working in the latest re-run | 40 |
| Providers that did not contribute in the latest re-run | 6 |
| Providers researched but not implemented | 222 |

### 3.2 Implemented Providers Currently Not Contributing

Re-verified by re-running `jobs.py` end-to-end and, for the failures below, independently re-testing each provider's `fetch_raw()` in isolation to confirm the cause. All reasons below are taken directly from the actual HTTP response received — none are assumed.

| Provider | Reason |
|---|---|
| TheirStack | Account's billing plan does not include Jobs API access (HTTP 402 Payment Required). |
| Trade Me Jobs | Requires a New Zealand or Australian Trade Me membership together with Trade Me developer application approval. Production credentials could not be obtained from outside the supported regions. |
| CareerOneStop | The integration has already been implemented in the codebase. However, CareerOneStop account registration is geographically restricted and could not be completed from India, so the required API credentials could not be obtained for testing. |
| Fantastic.jobs | **Cause confirmed.** Credentialed, but the API key has exhausted its metered quota — the live response body reads *"API Key has exceeded the allowed limit for 'jobs' meter"* (HTTP 403). This is a billing/quota limit, not an account or trial-eligibility problem. |
| Arbeitnow | The provider enforces a strict request-rate limit. Consecutive pagination requests trigger HTTP 429 responses. A small delay or exponential backoff between requests should resolve the issue. |
| CareerJet | The provider currently rejects requests because the server IP is not authorized. CareerJet requires the calling server's IP address to be allowlisted on its partner dashboard, and this environment's IP is not on that list. Historical data remains stored from a period when access was working; no new jobs are currently being retrieved. |

**Also observed, but not a contribution gap:** A temporary server-side gateway timeout was observed during one execution of OpenWebNinja. An immediate retry succeeded, indicating a transient provider-side issue rather than an implementation problem. OpenWebNinja remains counted among the working providers on the strength of that retry.

### 3.3 Volume concentration

| Provider | Jobs Stored | % of Total |
|---|---:|---:|
| SmartRecruiters | 73,946 | 30.6% |
| Greenhouse | 24,785 | 10.3% |
| Bundesagentur für Arbeit | 19,864 | 8.2% |
| Lever | 18,665 | 7.7% |
| Reed | 17,868 | 7.4% |
| NHS Jobs | 14,932 | 6.2% |
| USAJOBS | 13,230 | 5.5% |
| NAV Arbeidsplassen | 8,640 | 3.6% |
| Ashby | 5,622 | 2.3% |
| Himalayas | 5,253 | 2.2% |
| Workable | 4,497 | 1.9% |
| Workday | 4,475 | 1.9% |
| Arbetsförmedlingen | 4,196 | 1.7% |
| Adzuna | 4,000 | 1.7% |
| EURES | 3,681 | 1.5% |
| RemoteJobs.org | 3,000 | 1.2% |
| France Travail | 2,288 | 0.9% |
| The Muse | 2,202 | 0.9% |
| CareerJet | 1,996 | 0.8% |
| Jooble | 1,816 | 0.8% |
| Taiwan Ministry of Labor | 1,629 | 0.7% |
| Get on Board | 1,113 | 0.5% |
| Findwork.dev | 1,094 | 0.5% |
| Mustakbil.com | 576 | 0.2% |
| Teamtailor | 546 | 0.2% |
| Recruitee (Tellent) | 430 | 0.2% |
| MyJobMag | 200 | 0.1% |
| Jobicy | 200 | 0.1% |
| RemoteOK | 200 | 0.1% |
| We Work Remotely | 150 | 0.1% |
| SerpApi (Google Jobs) | 100 | <0.1% |
| 4dayweek.io | 98 | <0.1% |
| Freshersworld | 60 | <0.1% |
| OpenWebNinja (JSearch) | 49 | <0.1% |
| Remotive | 42 | <0.1% |
| MyCareersFuture | 38 | <0.1% |
| Working Nomads | 35 | <0.1% |
| Jobspresso | 20 | <0.1% |
| NoDesk | 20 | <0.1% |
| Hasjob | 7 | <0.1% |
| HK Gov Vacancies | 1 | <0.1% |
| TheirStack | 0 | 0.0% |
| Trade Me Jobs | 0 | 0.0% |
| CareerOneStop | 0 | 0.0% |
| Fantastic.jobs | 0 | 0.0% |
| Arbeitnow | 0 | 0.0% |

The top providers contribute nearly half of all stored jobs. Most job volume comes from ATS platforms and government job boards rather than being evenly distributed across all providers.

---


## 4. Complete Provider Research (268 Providers)

Tables 4.1 and 4.2 below satisfy the internship requirement to document the number of jobs available or retrieved for each API, alongside every provider's pricing, reference, and implementation status.

Every provider researched in this project (`job_api.xlsx` API Catalog sheet, 268 rows), split into **Implemented (46)** and **Not Implemented (222)**. Pricing model and payment terms are this project's own verified classification of each provider's published terms — where nothing could be confirmed, the cell reads "Not publicly available." Reference is a documented URL/domain found in this project's research notes.


### 4.1 Implemented Providers (46)

<table style="width:100%; table-layout:fixed; border-collapse:collapse; font-size:8pt; line-height:1.35;">
<colgroup>
<col style="width:11%;">
<col style="width:10%;">
<col style="width:9%;">
<col style="width:13%;">
<col style="width:11%;">
<col style="width:8%;">
<col style="width:38%;">
</colgroup>
<thead><tr>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Provider</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Pricing Model</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Payment After<br>Free Tier</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Official<br>Reference</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Jobs Retrieved<br>(Current Impl.)</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Status</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Implementation Notes</th>
</tr></thead>
<tbody>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">SmartRecruiters</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://developers.smartrecruiters.com/docs/posting-api">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">73,946 stored<br>(65,457 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> 100 curated companies only, not a global index.<br>&bull; <strong>Expansion:</strong> Add more verified company slugs.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Greenhouse</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://developers.greenhouse.io/job-board.html">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">24,785 stored<br>(23,026 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> 276 curated companies; single-shot fetch per company. 3 companies (particlehealth, creditkarma, loop) returned HTTP 404 in the latest re-run — each is skipped individually (fault isolation confirmed working) without affecting the other 273.<br>&bull; <strong>Expansion:</strong> Add more verified company slugs; prune or re-verify the 3 companies now returning 404.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Lever</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://github.com/lever/postings-api">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">18,665 stored<br>(15,686 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> 162 curated companies; single-shot fetch per company. In the latest re-run, 1 company (sprucesystems) returned HTTP 404 and 1 (boxlunch, a large multi-location employer) failed with a reset connection — both isolated to that company only (fault isolation confirmed working), but the boxlunch drop explains most of this run's fetched-count decrease versus the earlier baseline run.<br>&bull; <strong>Expansion:</strong> Add more verified company slugs; re-verify sprucesystems' board still exists and re-run to confirm boxlunch's failure was transient.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">NHS Jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://www.nhsbsa.nhs.uk/about-nhs-jobs/nhs-jobs-integration-and-benefits">Official Documentation (No Pricing Page)</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">14,932 stored<br>(12,466 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Undocumented endpoint; could change without notice.<br>&bull; <strong>Expansion:</strong> Monitor for endpoint changes; no code change needed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">USAJOBS</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free registration</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://developer.usajobs.gov">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">13,230 stored<br>(10,000 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Hard 10,000-result API ceiling; no retry/error handling in fetch loop.<br>&bull; <strong>Expansion:</strong> Partition by JobCategoryCode/LocationName; add shared retry helper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Bundesagentur für Arbeit</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth-style public key</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://www.arbeitsagentur.de/jobsuche">Free Public API</a> (undocumented; no official arbeitsagentur.de API docs exist)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">19,864 stored<br>(10,000 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Hard 10,000-result API ceiling (page x size).<br>&bull; <strong>Expansion:</strong> Partition query by location/keyword params.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Reed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free registration</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://reed.co.uk/developers/jobseeker">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">17,868 stored<br>(9,000 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> ~9,900 result-window boundary (HTTP 500 beyond); no shared retry helper.<br>&bull; <strong>Expansion:</strong> Raise page cap toward boundary; add shared retry helper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">NAV Arbeidsplassen</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth-style public token</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://navikt.github.io/pam-stilling-feed">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">8,640 stored<br>(13,743 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Change-feed, not a current-postings search; drives high dup rate.<br>&bull; <strong>Expansion:</strong> Increase lookback window or page cap.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Ashby</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://developers.ashbyhq.com/docs/public-job-posting-api">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">5,622 stored<br>(5,326 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> 102 curated companies only.<br>&bull; <strong>Expansion:</strong> Add slugs; enable <code>includeCompensation=true</code> for salary data.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Workable</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://help.workable.com/hc/en-us/articles/115012801727-How-to-embed-jobs-on-your-website-job-widget">Official Documentation (No Pricing Page)</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">4,497 stored<br>(8,018 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> 89 curated companies; public widget API only, not full ATS.<br>&bull; <strong>Expansion:</strong> Add more verified company slugs.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Workday</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://www.workday.com">Free Public API</a> (no fixed docs URL; keyless, per-tenant endpoint)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">4,475 stored<br>(2,997 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Self-capped at 200 jobs/tenant; large tenants under-sampled.<br>&bull; <strong>Expansion:</strong> Raise per-tenant page cap; add more tenants.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Himalayas</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://himalayas.app/docs/remote-jobs-api">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">5,253 stored<br>(3,000 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Self-capped at 3,000 of 90,000+; fixed page size (limit ignored).<br>&bull; <strong>Expansion:</strong> Raise page cap; use richer <code>/jobs/api/search</code> endpoint.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Arbetsförmedlingen</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobsearch.api.jobtechdev.se">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">4,196 stored<br>(2,100 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Hard offset ≤2,000 ceiling (~2,100 of 40,000 reachable).<br>&bull; <strong>Expansion:</strong> None found; add in-loop error handling for resilience.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Adzuna</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free tier + paid metered</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://developer.adzuna.com/docs/search">Official Documentation (No Pricing Page)</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">4,000 stored<br>(2,000 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Self-capped at 2,000/run; single-country (<code>us</code>) only.<br>&bull; <strong>Expansion:</strong> Raise page cap; query additional Adzuna country indexes.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">The Muse</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://themuse.com/developers/api/v2">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">2,202 stored<br>(2,000 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Hard 100-page ceiling (HTTP 400) without an API key.<br>&bull; <strong>Expansion:</strong> Add an API key to raise the ceiling.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">CareerJet</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free registration</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://careerjet.com/partners/api">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">1,996 stored<br>(0 fetched in latest re-run — failed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Blocked — IP allowlist</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> The provider currently rejects requests because the server IP is not authorized — CareerJet requires the calling server's IP to be allowlisted on its partner dashboard, and this environment's IP is not on that list. Historical data remains stored from a period when access was working.<br>&bull; <strong>Expansion:</strong> Re-add the current IP to the CareerJet partner dashboard allowlist, then re-run.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">EURES</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://eures.europa.eu">Free Public API</a> (undocumented)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">3,681 stored<br>(2,000 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Hard ~10,000-result ceiling; self-capped at 2,000/run.<br>&bull; <strong>Expansion:</strong> Raise page cap toward the ~10,000 ceiling.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">RemoteJobs.org</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://remotejobs.org/api-access">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">3,000 stored<br>(1,500 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Real rate limiting observed (HTTP 429 ~page 23).<br>&bull; <strong>Expansion:</strong> None beyond current handling; partial results already preserved.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">France Travail</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free self-service</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://francetravail.io/produits-partages/catalogue/offres-emploi">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">2,288 stored<br>(1,150 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Self-capped range ceiling (1,150), inherited from prior research.<br>&bull; <strong>Expansion:</strong> Re-confirm true ceiling; raise if larger window confirmed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jooble</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free registration</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jooble.org/api/about">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">1,816 stored<br>(1,112 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Usable window ~1,100-1,200 jobs vs. much larger reported totals; no in-loop retry.<br>&bull; <strong>Expansion:</strong> Add in-loop error handling.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Get on Board</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://getonbrd.com/api-doc.html">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">1,113 stored<br>(1,271 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> None significant; paid Private API tier unused by design.<br>&bull; <strong>Expansion:</strong> None identified; already fetches to each filter's total_pages.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Taiwan Ministry of Labor</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth open data</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://data.gov.tw/en/datasets/44062">Free Public API</a> (data.gov.tw #44062)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">1,629 stored<br>(1,000 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Hard 1,000-record cap; no working offset/page param found.<br>&bull; <strong>Expansion:</strong> None found; no further page accessible.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Findwork.dev</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free registration</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://findwork.dev/developers">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">1,094 stored<br>(1,000 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Real rate limiting observed (HTTP 429 ~page 11).<br>&bull; <strong>Expansion:</strong> None beyond current handling; partial results already preserved.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Mustakbil.com</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://rss.mustakbil.com/jobs-rss">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">576 stored<br>(500 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination exists; fixed 500-item feed.<br>&bull; <strong>Expansion:</strong> None found.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Teamtailor</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://docs.teamtailor.com">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">546 stored<br>(500 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> 25 curated companies; public RSS only, not credentialed Web API.<br>&bull; <strong>Expansion:</strong> Add more verified subdomains.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Recruitee (Tellent)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://docs.recruitee.com/reference/intro-to-careers-site-api">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">430 stored<br>(405 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> 21 curated companies; no pagination metadata in payload.<br>&bull; <strong>Expansion:</strong> Add more verified subdomains.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">RemoteOK</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://remoteok.com/api">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">200 stored<br>(100 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination exists; fixed ~100-job snapshot.<br>&bull; <strong>Expansion:</strong> None found.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">MyJobMag</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://www.myjobmag.com/feeds/">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">200 stored<br>(100 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination (robots.txt blocks query strings); fixed 100 items.<br>&bull; <strong>Expansion:</strong> Add other MyJobMag country feeds (Ghana/Kenya/SA/UK).</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobicy</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobi.cy/apidocs">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">200 stored<br>(100 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination; hard 100-job cap on <code>count</code>.<br>&bull; <strong>Expansion:</strong> None found.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">We Work Remotely</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://weworkremotely.com/remote-jobs.rss">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">150 stored<br>(99 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination; fixed ~100-item feed.<br>&bull; <strong>Expansion:</strong> Add per-category feeds for broader coverage.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">4dayweek.io</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://4dayweek.io/feed">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">98 stored<br>(50 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination; richer <code>/api/jobs</code> endpoint blocked by robots.txt.<br>&bull; <strong>Expansion:</strong> None; richer endpoint deliberately excluded.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">SerpApi (Google Jobs)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free tier + paid metered</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://serpapi.com/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">100 stored<br>(50 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Metered API; self-capped at 50 jobs/run to conserve quota.<br>&bull; <strong>Expansion:</strong> Raise page cap if a larger quota is approved.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">OpenWebNinja (JSearch)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free tier + paid metered</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://openwebninja.com/api/jsearch">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">49 stored<br>(0 fetched in the latest re-run — see note)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Metered API; self-capped at 5 pages to conserve quota. One scheduled run hit an HTTP 504 Gateway Timeout after exhausting its retries; an isolated retry moments later succeeded (48 jobs), confirming this was a transient server-side error, not an account/quota problem.<br>&bull; <strong>Expansion:</strong> Raise page cap if a larger quota is approved.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Working Nomads</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://www.workingnomads.com/api/exposed_jobs/">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">35 stored<br>(30 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination; fixed ~36-job snapshot; no RSS alternative found.<br>&bull; <strong>Expansion:</strong> None found.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Remotive</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://remotive.com/remote-jobs/api">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">42 stored<br>(38 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination; filter params confirmed non-functional.<br>&bull; <strong>Expansion:</strong> None found.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Freshersworld</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://freshersworld.com/feed">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">60 stored<br>(30 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination; rolling ~30-item window.<br>&bull; <strong>Expansion:</strong> None found.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobspresso</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobspresso.co/jobs/feed">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">20 stored<br>(20 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Deeper pagination exists but blocked by robots.txt.<br>&bull; <strong>Expansion:</strong> None; deeper pagination deliberately unused.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">MyCareersFuture</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://api.mycareersfuture.gov.sg">Free Public API</a> (undocumented)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">38 stored<br>(2,000 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Needs review</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> <code>limit</code> param ignored (fixed 20/page); self-capped at 2,000/run.<br>&bull; <strong>Expansion:</strong> Raise page cap; no hard API ceiling found.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">NoDesk</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://nodesk.co/remote-jobs">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">20 stored<br>(10 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination; fixed 10-item feed.<br>&bull; <strong>Expansion:</strong> None found.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Hasjob</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public feed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://hasjob.co/feed">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">7 stored<br>(7 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> No pagination; inherently small volume (community board).<br>&bull; <strong>Expansion:</strong> None found.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">HK Gov Vacancies</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth open data</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://data.gov.hk/en-data/dataset/hk-csb-csb-gov-vacancies">Free Public API</a> (data.gov.hk)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">1 stored<br>(54 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Needs review</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Static dataset; no per-posting URL (collapses on dedup).<br>&bull; <strong>Expansion:</strong> Use a non-URL dedup key to reduce duplicate collapse.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">TheirStack</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Per-credit metered (1 credit/job)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://theirstack.com/en/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">0 stored<br>(0 fetched in latest re-run — still blocked)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Blocked — billing</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Bills per job returned; blocked by account billing (HTTP 402), re-confirmed unchanged in the latest re-run.<br>&bull; <strong>Expansion:</strong> Resolve billing; then raise job cap and add retry helper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Trade Me Jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free (registered app)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://developer.trademe.co.nz/api-reference/search-methods/jobs-search">Official Documentation (No Pricing Page)</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">0 stored<br>(0 fetched in latest re-run — still uncredentialed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Built, uncredentialed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Built from API spec only, unexercised live; `TRADEME_CONSUMER_KEY`/`SECRET` still unset in this environment.<br>&bull; <strong>Expansion:</strong> Provision consumer key/secret; complete production approval.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">CareerOneStop</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free registration</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://careeronestop.org/Developers/WebAPI/web-api.aspx">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">0 stored<br>(0 fetched in latest re-run — still uncredentialed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Built, uncredentialed</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Hard ~750-result ceiling; access/registration was geographically restricted (geo-blocked) from this environment, preventing successful API registration and testing — re-confirmed unchanged in the latest re-run (`CAREERONESTOP_USER_ID`/`API_TOKEN` still unset).<br>&bull; <strong>Expansion:</strong> Retry registration from an unrestricted network/region to obtain a user ID/API token.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Fantastic.jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free trial → paid metered (~$1/1,000 jobs)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, after trial ends</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://fantastic.jobs/api">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">0 stored<br>(0 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Blocked — quota exceeded</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> Cause now confirmed: HTTP 403, body "API Key has exceeded the allowed limit for 'jobs' meter" — the account's metered quota is exhausted, not an expired trial or bad key.<br>&bull; <strong>Expansion:</strong> Upgrade the plan or wait for quota reset; add <code>/v1/active-jb</code> sibling endpoint.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Arbeitnow</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No-auth public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://arbeitnow.com/api/job-board-api">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">0 stored<br>(0 fetched in latest re-run)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Blocked — rate limited</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">&bull; <strong>Limitation:</strong> The provider enforces a strict request-rate limit; consecutive pagination requests trigger HTTP 429 responses.<br>&bull; <strong>Expansion:</strong> Add a small delay or exponential backoff between page requests in <code>arbeitnow.py</code>'s own loop (it does not currently use the shared <code>request_with_retry</code> helper).</td>
</tr>
</tbody></table>

### 4.2 Not Implemented Providers (222)

Grouped by research classification at the time of this project. **Registration/Approval Required** and **Needs Live Verification** providers have a real, plausible access path (Section 6, Recommendations); **Not Viable** providers were rejected on structural grounds (no public API, enterprise-only, wrong data-flow direction, deprecated, or a dataset rather than a live API).

#### Registration/Approval Required (4)

<table style="width:100%; table-layout:fixed; border-collapse:collapse; font-size:8pt; line-height:1.35;">
<colgroup>
<col style="width:15%;">
<col style="width:13%;">
<col style="width:11%;">
<col style="width:12%;">
<col style="width:11%;">
<col style="width:38%;">
</colgroup>
<thead><tr>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Provider</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Pricing Model</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Payment After<br>Free Tier</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Official<br>Reference</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Approx. Jobs<br>Available</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Reason Not Implemented</th>
</tr></thead>
<tbody>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">CBOP - Centralna Baza Ofert Pracy (Poland public employment offices)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://praca.gov.pl">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large - national public employment office coverage</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Poland's national public-employment-office job database. Real SOAP web service returning batches of up to 1,000 live offers per file, but capped at 20 calls/cycle and only reachable during a 17:00-07:00 window -…</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Saramin Open API (사람인 오픈 API)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (partner-gated access; pricing undisclosed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://saramin.co.kr">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Unknown - Saramin is one of Korea's largest commercial job boards but no public…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">One of Korea's largest commercial job boards. Real documented API, but gated behind an application/approval step, explicitly labeled beta with a 500-calls/day cap - usable, just slower to unlock and rate-constrained.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">VDAB Vacature API (Belgium - Flanders public employment service)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free, but partner/approval access required (no self-serve signup)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No, once approved, but partner/approval access is itself the…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large - Flanders regional coverage</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Flanders' public employment service vacancy API - free but requires an application form and an exploratory onboarding meeting with VDAB before credentials are issued. Real read API, just a slower registration path than…</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Work24 (formerly Worknet/워크넷) Job Listings Open API - Korea Employment Information Service</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large - South Korea's national public employment portal (renamed 고용24 in…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">South Korea's national public job bank, verified live on data.go.kr with real-time XML/JSON updates and a free key. Caveat: license text restricts use to non-commercial, attributed, unmodified use - confirm terms with…</td>
</tr>
</tbody></table>

#### Needs Live Verification (4)

<table style="width:100%; table-layout:fixed; border-collapse:collapse; font-size:8pt; line-height:1.35;">
<colgroup>
<col style="width:15%;">
<col style="width:13%;">
<col style="width:11%;">
<col style="width:12%;">
<col style="width:11%;">
<col style="width:38%;">
</colgroup>
<thead><tr>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Provider</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Pricing Model</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Payment After<br>Free Tier</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Official<br>Reference</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Approx. Jobs<br>Available</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Reason Not Implemented</th>
</tr></thead>
<tbody>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">GOV.UK Find a Job (DWP)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">UK's national government job service; no confirmed public read/search API for third parties was found - only an employer-side SFTP bulk-upload path for posting vacancies. Worth one more direct check with DWP given its…</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Job-Room Jobs API (SECO, Switzerland)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free, but partner/approval access required (no self-serve signup)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No, once approved, but partner/approval access is itself the…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Switzerland's biggest job platform, but the API is built primarily for employers/ATS submitting ads under a reporting-obligation rule - whether third-party aggregators can get read-only access is unconfirmed in the…</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JobsPikr</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Unknown (volume not published)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Commercial aggregator (incl. Naukri/Monster-sourced India feeds) with a real API and docs, but pricing is custom/quote-based rather than a published self-serve rate - confirm actual signup process and cost before…</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Portal del Empleo / Servicio Nacional de Empleo (STPS Mexico)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Mexico's national employment service publishes datasets on the CKAN-based datos.gob.mx open-data platform, but a live, current-vacancy-specific API endpoint for the job board itself was not directly confirmed - may…</td>
</tr>
</tbody></table>

#### Not Viable at Research Time (214)

<table style="width:100%; table-layout:fixed; border-collapse:collapse; font-size:8pt; line-height:1.35;">
<colgroup>
<col style="width:15%;">
<col style="width:13%;">
<col style="width:11%;">
<col style="width:12%;">
<col style="width:11%;">
<col style="width:38%;">
</colgroup>
<thead><tr>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Provider</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Pricing Model</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Payment After<br>Free Tier</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Official<br>Reference</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Approx. Jobs<br>Available</th>
<th style="text-align:left; vertical-align:bottom; padding:4px 5px; border-bottom:1.5px solid #333; background:#eef1f5;">Reason Not Implemented</th>
</tr></thead>
<tbody>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">104 Job Bank (104人力銀行)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://104.com.tw">104.com.tw</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">~1.1 million (110萬, Feb 2026)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">1111 Job Bank (1111人力銀行)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://1111.com.tw">1111.com.tw</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">51job (前程无忧 / Qiancheng Wuyou)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://51job.com">51job.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">AMS eJob-Room (Austria public employment service)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">APEC (Association Pour l'Emploi des Cadres, France)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">APS Jobs (Australian Public Service careers)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://apsjobs.gov.au">apsjobs.gov.au</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Moderate</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Adecco India</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Agencia Publica de Empleo SENA (APE)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://edu.co">edu.co</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">AllJobs.co.il</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://AllJobs.co.il">AllJobs.co.il</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Apideck</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://apideck.com/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid middleware re-wrapping ATSs (Greenhouse, Lever, Workday) already integrated directly for free.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Apify</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://apify.com/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic web-scraping infrastructure, not a job-specific API — would require building a custom scraper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Apna</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Large, blue-collar (board size; no public access)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API for third-party aggregators.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Appcast</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://appcast.io/how-programmatic-recruitment-advertising-improves-cost-per-hire/">appcast.io/how-programmatic-recruitment-advertising-improves-cost-per-hire/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Aura (by Aura Intelligence)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Proprietary workforce database spanning 20M+ companies (billions of data points;…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">BMET / Ami Probashi (Bangladesh Overseas Employment)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://amiprobashi.com">amiprobashi.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">BOSS Zhipin (Kanzhun Limited, NASDAQ: BZ)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://zhipin.com">zhipin.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">BambooHR</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A - per-tenant only, no aggregate feed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise-only access — gated behind sales/partner approval, no self-serve path.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Bayt.com</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://Bayt.com">Bayt.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Bdjobs.com</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Bolsa Nacional de Empleo (BNE / SENCE, Chile)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Bossjob</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://bossjob.com">bossjob.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Bright Data</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://brightdata.com/products/web-scraper/jobs-scraper">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">116.8M+ records (general Jobs dataset); LinkedIn Jobs dataset specifically 62.4M+</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic web-scraping infrastructure, not a job-specific API — would require building a custom scraper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">BrighterMonday</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://brightermonday.co.ke">brightermonday.co.ke</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Broadbean (Veritone Hire)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://broadbean.com/product-suite/job-distribution-platform/">broadbean.com/product-suite/job-distribution-platform/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Built In</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (tech/startup; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Bumeran</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">CEIPAL</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://ceipal.com/pricing">ceipal.com/pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">CV-Library</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">CWJobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://CWJobs.co.uk">CWJobs.co.uk</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">12,000+ jobs (per cwjobs.co.uk About Us page)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">CareerBuilder</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (partner-gated access; pricing undisclosed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://careerbuilder.com/">careerbuilder.com/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">CareerBuilder / Monster (Talent Network distribution)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://careerbuilder.com/talent-network">careerbuilder.com/talent-network</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">CareerLink Vietnam</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">CareerOne (Australia)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (partner-gated access; pricing undisclosed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://careerone.com.au">careerone.com.au</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">100,000+ (live jobs)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Feed-ingest/distribution network only — no public read endpoint for consumers.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Careers24</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://careers24.com">careers24.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Careers@Gov</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Small (SG public sector; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Catho Developer API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (partner-gated access; pricing undisclosed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">China MOHRSS National Public Employment Service Platform (全国公共招聘服务平台)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Civil Service Jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Claro Analytics (WilsonHCG)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://claroanalytics.com/">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Real-time job-postings and 500M+ global talent profiles</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Cliclavoro / Ministero del Lavoro Open Data (Italy)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Computrabajo</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Coresignal</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">399M+ multi-source records (incl. India)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise-tier data vendor sold via sales contact; no published self-serve price.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Cutshort</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Small (tech; board size not public)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Darwinbox</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A - per-tenant only, no aggregate feed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise-only access — gated behind sales/partner approval, no self-serve path.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Datapeople (by Payscale)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://datapeople.io/">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A (analyzes customer job postings, not a broad aggregation…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Dice</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (tech niche; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Diffbot</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://diffbot.com/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic web-scraping infrastructure, not a job-specific API — would require building a custom scraper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Draup</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://draup.com/">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Global labor-market and job-postings data (aggregated multi-source)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Drushim</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://Drushim.co.il">Drushim.co.il</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Egypt Ministry of Labour (formerly Ministry of Manpower) Job Portal</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://labour.gov.eg">labour.gov.eg</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Elempleo</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Very large (CO; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Eluta</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Employment Services of South Africa (ESSA) - Dept. of Employment and Labour</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://labour.gov.za">labour.gov.za</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Forasna</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://forasna.com/employer/pricing">forasna.com/employer/pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Foundit (Monster India)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">~800k+ (board size; no public access)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API for third-party aggregators.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Freshteam</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A - per-tenant only, no aggregate feed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise-only access — gated behind sales/partner approval, no self-serve path.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Glassdoor Jobs API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://glassdoor.com/developer/index.htm">glassdoor.com/developer/index.htm</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Glints</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Google Cloud Talent Solution (Job Search API)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://google.com/talent-solution/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A (you populate it with your own jobs; not an aggregation…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Hosted ML search engine for your own postings — not a source of third-party listings.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Google for Jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://schema.org">schema.org</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Unknown (indexes open web)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Greenwich.HR (WageScape)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://amazon.com/marketplace/pp/prodview-t5fvgfurgypxg">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">~5M new US jobs/month; ~70% of all open US jobs; 1.5M+ hiring organizations</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">GreytHR</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A - HRMS/payroll only, no job feed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">GulfTalent</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://gulftalent.com">gulftalent.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Gupy Public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://gupy.io">gupy.io</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">~90,000 job vacancies published monthly on the Gupy R&amp;S platform (official figure)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">HackerEarth Jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Small (board size not public)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">HasData</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://hasdata.com/prices">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic web-scraping infrastructure, not a job-specific API — would require building a custom scraper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Hello Work Job Information API (ハローワーク求人情報提供サービス, MHLW)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large - nationwide public employment service covering hundreds of thousands…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Real, documented API, but registration is restricted to licensed placement businesses/governments — a generic aggregator doesn't qualify.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">HelloWork ATS Partner API (France)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free, but partner/approval access required (no self-serve signup)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No, once approved, but partner/approval access is itself the…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Hired.com (LHH Recruitment Solutions)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://Hired.com">Hired.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">0</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Hirist</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (tech; board size not public)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Hong Kong Labour Department Interactive Employment Service (iES, jobs.gov.hk)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://www.jobs.gov">www.jobs.gov</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Horsefly Analytics</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://horseflyanalytics.com/">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">1 trillion+ data points; millions of job postings; supply/demand across 60+ countries</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">IEFPOnline / netEmprego (Portugal public employment service)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">5,913 ofertas de emprego (live count)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Indeed Hiring Lab</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://indeed.com">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A (publishes indices/aggregates, e.g. Job Postings Index, Wage…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Indeed's research arm — publishes aggregate labor-market indices, not individual job records.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Indeed India</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Huge (not accessible - partner-only)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise partner-only access; not available to a generic aggregator.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Indeed PLUS Job Distribution API (Recruit Holdings, Japan)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (partner-gated access; pricing undisclosed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large - aggregates postings across Japan's major job boards distributed via…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">InfoJobs (Spain)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">68,383 ofertas (live count, Spain, as of July 2026)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Instahyre</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (tech; board size not public)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Internshala</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Large (intern/fresher; board size not public)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Israeli Employment Service (Sherut HaTaasuka / taasuka.gov.il)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://taasuka.gov.il">taasuka.gov.il</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JSearch (RapidAPI, by OpenWeb Ninja)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic B2B data vendor, not a dedicated job board — paid, overlaps with sources already integrated.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jadarat (Saudi National Employment Portal / HRDF)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Job Bank (ESDC) feed / Open Gov dataset</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Very large (100,000+)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Live feed needs ESDC partner approval; fallback open dataset lacks employer names and apply URLs.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Job Market Finland / Tyomarkkinatori (TE-palvelut, Finland)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JobKorea</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">~209,637 (live listings)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JobStreet / JobsDB (SEEK group)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Very large if accessible (not public)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">SEEK-group flagship boards for SEA — enterprise partner-only, no self-serve path.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JobThai</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobthai.com">jobthai.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">~121,000 active jobs (121,337 shown live on jobthai.com)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobberman</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobberman.com">jobberman.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobcase (MaxRecruit)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobcase.com/products/maxrecruit">jobcase.com/products/maxrecruit</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobcase Platform API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobcase.com/">jobcase.com/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobg8</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobg8.com/Faq.aspx?contentid=10874">jobg8.com/Faq.aspx?contentid=10874</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobillico</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobindex (Denmark)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">33,600 jobs (live) / 30,000+ job ads</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JobisJob (LIFULL Connect)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobboardfinder.com/jobboard-jobisjob-usa">jobboardfinder.com/jobboard-jobisjob-usa</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">~9,000,000 (monthly, cross-country)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobnet.dk (Denmark public employment portal)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobrapido</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobrapido.com">jobrapido.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobs.cz</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (CZ/SK; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise-only access — gated behind sales/partner approval, no self-serve path.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JobsDB Hong Kong (SEEK Group) / CTgoodjobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://hk.jobs">hk.jobs</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">~32,700 (JobsDB HK) / ~32,000 (CTgoodjobs)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JobsEQ (Chmura Economics &amp; Analytics)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://chmura.com/jobseq">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Real-time job-posting dataset with international coverage</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JobsIreland.ie (Ireland public employment service)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">4,806 vacancies (live count)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jobsite</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://Jobsite.co.uk">Jobsite.co.uk</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">280,000+ live job adverts (per jobsite.co.uk About Us page)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JoinVision (JobCloud HR Tech)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://crunchbase.com/organization/joinvision">crunchbase.com/organization/joinvision</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Jora (Australia)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jora.com">jora.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Joveo</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://joveo.com/programmatic-job-advertising-platform/">joveo.com/programmatic-job-advertising-platform/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">JustRemote</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://justremote.co/remote-jobs">justremote.co/remote-jobs</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">2,000+ hidden remote jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Kalibrr</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Karir.com</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Keka</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A - HRMS/payroll only, no job feed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Kelly Services India</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Kemnaker Karirhub (SIAPkerja)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free, but partner/approval access required (no self-serve signup)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No, once approved, but partner/approval access is itself the…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Kombo.dev</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://kombo.dev/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid middleware re-wrapping ATSs (Greenhouse, Lever, Workday) already integrated directly for free.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Ladders</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (niche; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Lensa</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://lensa.com/">lensa.com/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Lightcast (formerly Emsi Burning Glass) Job Postings API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://lightcast.dev/apis/job-postings">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Billions of postings aggregated from 160,000+ sources (18B+ labor-market data points)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Lightcast Jobs Canada</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid labor-market-intelligence product sold via sales process, not self-serve.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">LinkUp</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://linkup.com">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Millions of postings indexed daily from 80,000+ employer websites</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">LinkedIn Jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Huge (not accessible - partner-only)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise partner program only — no self-serve developer signup.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">MOHRE UAE Federal Careers / iRecruitment Portal</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://mohre.gov.ae">mohre.gov.ae</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">MP Rojgar</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (state-level; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">MahaJobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (state-level; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">ManpowerGroup India</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Mantiks</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://mantiks.io/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic B2B data vendor, not a dedicated job board — paid, overlaps with sources already integrated.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Merge.dev</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://merge.dev/pricing/unified">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid middleware re-wrapping ATSs (Greenhouse, Lever, Workday) already integrated directly for free.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Mitula (LIFULL Connect / Adzuna)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://lifullconnect.com/brands/mitula/">lifullconnect.com/brands/mitula/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Monster</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://monster.com/solutions/talent-management/partner-with-monster/">monster.com/solutions/talent-management/partner-with-monster/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">NAVTTC National Employment Exchange Tool (NEXT / jobs.gov.pk)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">NEAIMS - National Employment Authority Kenya</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">National Career Service (NCS)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://data.gov.in">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Large in aggregate</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Periodic bulk open-government dataset, not a live per-job search API — stale snapshots only.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">National Directorate of Employment (NDE) Nigeria</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://nde.gov.ng">nde.gov.ng</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">National Job Portal (NJP) - Pakistan</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://njp.gov.pk">njp.gov.pk</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Small-to-moderate</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">National Job Portal - Bangladesh (jobs.gov.bd)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobs.gov.bd">jobs.gov.bd</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Naukri</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">~1M+ (board size; no public access)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API; any access is undocumented/grey-area and India-IP-restricted.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Naukrigulf</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://naukrigulf.com">naukrigulf.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Nexxt (formerly Beyond.com)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://Beyond.com">Beyond.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Nimble (Nimbleway)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://nimbleway.com/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic web-scraping infrastructure, not a job-specific API — would require building a custom scraper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">OCC Mundial</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">137,925 active vacancies ("vacantes activas en occ.com.mx", as of Oct 18, 2024);…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Outsourcely</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://outsourcely.com">outsourcely.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Oxylabs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://oxylabs.io/products/scraper-api/web/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic web-scraping infrastructure, not a job-specific API — would require building a custom scraper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">PandoLogic (pandoIQ) / Veritone Hire</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://pandologic.com/solutions/programmatic-advertising-pandoiq/">pandologic.com/solutions/programmatic-advertising-pandoiq/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Pangian</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://pangian.com/feed/?post_type=job_listing">pangian.com/feed/?post_type=job_listing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Varies (curated remote listings)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Site redirects to a static shutdown notice — service confirmed discontinued, not merely credential-gated.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">People Data Labs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://peopledatalabs.com/docs/job-posting-data-overview">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic B2B data vendor, not a dedicated job board — paid, overlaps with sources already integrated.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">PhilJobNet (DOLE Bureau of Local Employment)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://philjobnet.gov.ph">philjobnet.gov.ph</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Piloterr</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://piloterr.com/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic web-scraping infrastructure, not a job-specific API — would require building a custom scraper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Pnet</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://pnet.co.za">pnet.co.za</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Portal Empleo Argentina (Ministerio de Capital Humano / ex-Trabajo)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Pracuj.pl (Poland)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">762,827 job offers published in 2025</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">PredictLeads</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://predictleads.com/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">270M+ records since 2018; ~9.8M active jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic B2B data vendor, not a dedicated job board — paid, overlaps with sources already integrated.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Profesia</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (CZ/SK; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise-only access — gated behind sales/partner approval, no self-serve path.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Public Service Commission of Sri Lanka (psc.gov.lk)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://psc.gov.lk">psc.gov.lk</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Quess Corp</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Radancy</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://radancy.com/en/programmatic-adtech/">radancy.com/en/programmatic-adtech/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Randstad India</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">1,394 jobs (live count on official site)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Recruit CRM</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A - per-tenant only, no aggregate feed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise-only access — gated behind sales/partner approval, no self-serve path.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Recruitics</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://recruitics.com/programmatic-job-advertising">recruitics.com/programmatic-job-advertising</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Remote First Jobs (Dynamite Jobs)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://remotefirstjobs.com/rss">remotefirstjobs.com/rss</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Varies (curated remote-first listings)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Blocked by an active Cloudflare JS challenge on every path — a technical barrier, not a credentials gate.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Remote.co</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://remote.co/feed">remote.co/feed</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Revelio Labs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://reveliolabs.com">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">1.1B+ workforce profiles plus job postings, transitions, sentiment, layoffs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Rikunabi / Mynavi (Recruit Co. / Mynavi Corporation)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Rojgar Sangam (UP)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (state-level; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Rozee.pk</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">SEEK (SEEK.com.au / SEEK.co.nz)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free, but partner/approval access required (no self-serve signup)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No, once approved, but partner/approval access is itself the…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://SEEK.com.au">SEEK.com.au</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Feed-ingest/distribution network only — no public read endpoint for consumers.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">SEPE Open Data Portal (Spain public employment service)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Publishes only static statistical open-data files — no live REST API for current vacancies.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">SINE Aberto (Sistema Nacional de Emprego / Ministerio do Trabalho e Emprego)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://dados.gov.br/dataset/sine-aberto">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Suspended since Oct 2022 pending LGPD compliance review — no active API currently.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">ScraperAPI</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://scraperapi.com/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic web-scraping infrastructure, not a job-specific API — would require building a custom scraper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Scrapingdog</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://scrapingdog.com/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic web-scraping infrastructure, not a job-specific API — would require building a custom scraper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Shine</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (board size; no public access)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">SmartDreamers</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://smartdreamers.com/pricing">smartdreamers.com/pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Snagajob</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://snagajob.com/">snagajob.com/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">StepStone</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://stepstone.com">stepstone.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Superset</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (campus; per-institution, not aggregatable)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise-only access — gated behind sales/partner approval, no self-serve path.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Talent.com</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://Talent.com">Talent.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">40 million+ jobs (global figure stated on talent.com homepage)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">TalentNeuron (Gartner)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://talentneuron.com/solutions/platform">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Real-time labor data covering ~90% of world GDP; 40TB normalized data, 3B+ profiles,…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Talroo</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://talroo.com/pro/">talroo.com/pro/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Millions (per Talroo publisher marketing)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">TeamLease</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">23,082+ active job vacancies (live count on official site)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Techmap.io</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://jobdatafeeds.com">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">292M+ available jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic B2B data vendor, not a dedicated job board — paid, overlaps with sources already integrated.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Telangana T-Jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (state-level; not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Textkernel Jobfeed / Market IQ</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://textkernel.com/products-solutions/labour-market-insights/market-iq/">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Large multi-country vacancy corpus (millions of postings, deduplicated/enriched)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Thailand Department of Employment - Smart Job Center (ไทยมีงานทำ)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">The Burning Glass Institute</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://burningglassinstitute.org/">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A (research using Lightcast and other data))</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise labor-market-intelligence SaaS sold via sales contract, not a self-serve jobs feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">TimesJobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (board size; no public access)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">TopCV</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">TotalJobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://Totaljobs.com">Totaljobs.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Triplebyte</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free, but partner/approval access required (no self-serve signup)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No, once approved, but partner/approval access is itself the…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://triplebyte.com/">triplebyte.com/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Trovit (LIFULL Connect / Adzuna)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://trovit.com/feed-in-jobs/">trovit.com/feed-in-jobs/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">UWV Open Match Data (Netherlands)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A - aggregated statistics only, not individual postings)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Publishes aggregate labor-market statistics only — no individual job postings or per-job ID.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Unified.to</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid middleware re-wrapping ATSs (Greenhouse, Lever, Workday) already integrated directly for free.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Unstop</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (campus/intern; not a job-listing API)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Upward.net (a Jobcase company)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://upward.net/employers">upward.net/employers</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Vagas for Business API (Vagas.com.br)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (partner-gated access; pricing undisclosed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://Vagas.com">Vagas.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">VietnamWorks Open API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (partner-gated access; pricing undisclosed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://vietnamworks.com">Enterprise Contact / Pricing</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Partner access required — gated to approved commercial partners, not open registration.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">WUZZUF</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://wuzzuf.net">wuzzuf.net</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Welcome to the Jungle</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Wellfound</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (startup roles; board size not public)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">WhatJobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://whatjobs.com/job-aggregators">whatjobs.com/job-aggregators</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Work and Income / Find a Job (MSD, New Zealand)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://workandincome.gov">workandincome.gov</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Work at a Startup (Y Combinator)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://workatastartup.com">workatastartup.com</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Unknown (thousands across 1,000+ YC companies)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">WorkIndia</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Large, blue-collar (board size; no public access)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Workato</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://workato.com/pricing">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid middleware re-wrapping ATSs (Greenhouse, Lever, Workday) already integrated directly for free.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Workforce Australia</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://workforceaustralia.gov.au">Free Public API</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">API is write/management-only (employers post via OAuth2) — no read/search endpoint exists.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Workopolis</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">WowJobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Xing Jobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">XpressJobs (xpress.jobs)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">ZipAlerts (ZipRecruiter TrafficBoost)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (fee is for employers posting jobs on this platform, not…</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable to data access (see Pricing Model column)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://zipalerts.com/">zipalerts.com/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">ZipRecruiter API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Large (not quantified)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise-only access — gated behind sales/partner approval, no self-serve path.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Zoho Recruit</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, enterprise/sales pricing, no self-serve free tier</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available (N/A - per-tenant only, no aggregate feed)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Enterprise-only access — gated behind sales/partner approval, no self-serve path.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">ZonaJobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://zonajobs.com.ar">zonajobs.com.ar</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Zyte (formerly Scrapinghub)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free Tier + Pay-as-you-go</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, beyond the free tier/quota</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://zyte.com/zyte-api/pricing.html">Pricing Page</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Generic web-scraping infrastructure, not a job-specific API — would require building a custom scraper.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">data.gov.in OGD platform</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Free</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Varies (per-resource)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">General-purpose open-government-data portal (33 sectors), not jobs-specific — static datasets, not a live feed.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">eQuest</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Paid (metered/flat; see Cost Details column source for exact terms)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Yes, paid from the outset, no free tier documented</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://equest.com/">equest.com/</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Advertiser-side distribution network — built for employers to push jobs out, not for aggregators to pull data in.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">iimjobs</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Medium (management roles; board size not public)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">jobs.ch (Switzerland)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">45,825 jobs (live)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">karriere.at (Austria)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;"><a href="https://github.com/karriereat">github.com/karriereat</a></td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">13,400+ jobs (live)</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
<tr style="border-bottom:0.75px solid #ccc;">
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">topjobs.lk</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not applicable, no public API</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Not publicly available</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">Potentially large</td>
<td style="text-align:left; vertical-align:top; padding:4px 5px; word-wrap:break-word; overflow-wrap:break-word;">No public API — site requires jobseeker/employer login; no developer access documented.</td>
</tr>
</tbody></table>

## 5. Internship Requirement Coverage

### 6. Pricing model (Free / Free Trial / Pay-as-you-go / Subscription / Enterprise)

| Pricing Model (Implemented Providers) | Count | Providers |
|---|---:|---|
| Free (no cost, ever) | 41 | 40 fully free/no-auth or free-registration providers, plus Trade Me Jobs (free, but approval-gated) |
| Free Trial (time-limited, then paid) | 1 | Fantastic.jobs (7-day trial, then metered) |
| Pay-as-you-go / Metered (has a paid, usage-based component) | 5 | Adzuna, SerpApi, OpenWebNinja, TheirStack, Fantastic.jobs |
| Subscription (flat recurring fee) | 0 | Not used by any implemented provider |
| Enterprise (sales-negotiated contract) | 0 | Not used by any implemented provider — 15 enterprise-only candidates were identified in research and not implemented (Section 4.2) |

Full per-provider pricing model is in Section 4.1. The 222 not-implemented providers' pricing (where verifiable) is in Section 4.2.

### 7. Payment required after free tier

41 of the 46 implemented providers are free with no paid tier. The 5 providers below are the ones that will incur a cost once their free allowance runs out — 2 of the 5 (TheirStack, Fantastic.jobs) have already hit that point in this project's own account.

| Provider | Pricing Model | Payment After Free Tier | Official Pricing Page |
|---|---|---|---|
| Adzuna | Free tier, then paid metered access | Yes — once the free daily call allowance is exceeded | [developer.adzuna.com/docs/search](https://developer.adzuna.com/docs/search) (no separate public pricing page; commercial terms via the developer docs) |
| SerpApi (Google Jobs) | Free plan (250 searches/month), then paid metered plans | Yes — beyond 250 searches/month | [serpapi.com/pricing](https://serpapi.com/pricing) |
| OpenWebNinja (JSearch) | Free plan (~200 requests/month), then paid metered plans | Yes — beyond the free monthly request quota | [openwebninja.com/api/jsearch](https://openwebninja.com/api/jsearch) |
| TheirStack | Per-credit metered (bills 1 credit per job returned) | Yes — an active paid plan is required; this project's account is currently blocked (HTTP 402 — Section 3.2) | [theirstack.com/en/pricing](https://theirstack.com/en/pricing) |
| Fantastic.jobs | Free 7-day trial (no credit card), then paid metered (~$1 per 1,000 jobs) | Yes — after the trial/quota ends; this project's key has already exceeded its quota (Section 3.2) | [fantastic.jobs/api](https://fantastic.jobs/api) |

### 8. Pricing / documentation links

All 46 implemented providers have an official reference URL, quoted directly from source code (Section 4.1). Of the 222 not-implemented providers, a documented reference (domain or URL) was found in this project's research for **166 of 268 providers overall**; for the remainder, the reference cell reads "Not publicly available" rather than a guessed link (Section 4.2).

### 9. Number of jobs

| Metric | Value |
|---|---:|
| Total unique jobs stored (PostgreSQL, cumulative across both runs) | 241,564 |
| Total jobs fetched, all providers, pre-dedup (latest re-run) | 197,945 |
| New jobs added in the latest re-run | 57,058 |
| Distinct companies represented | 28,640 |

Top providers by volume are in Section 3.3. Approximate job counts for not-implemented providers (where publicly known) are in Section 4.2.

### 10. Region coverage

| Region | Dedicated Providers | Notes |
|---|---:|---|
| United States | 4 | USAJOBS, CareerOneStop, Findwork.dev, Adzuna |
| Canada | 0 | No dedicated source; incidental coverage only via global ATS boards |
| United Kingdom | 2 | Reed, NHS Jobs |
| Europe (non-UK) | 5 | Bundesagentur für Arbeit, Arbetsförmedlingen, France Travail, EURES, NAV Arbeidsplassen |
| India | 2 | Freshersworld, Hasjob |
| LATAM | 1 | Get on Board |
| APAC | 4 | MyCareersFuture, Taiwan MOL, HK Gov Vacancies, Trade Me |
| Africa | 1 | MyJobMag |
| Middle East | 0 | No single-country dedicated source (Mustakbil spans 20+ countries, counted as global) |
| Global / Remote / Multi-country | 27 | All 6 ATS platforms plus 21 aggregator/remote-board providers |

Resulting job distribution is US-heavy (47.3%), then UK (14.3%) and Germany (6.9%) — a sourcing-mix effect from which countries have dense curated ATS company lists, not a normalization defect. Canada remains the clearest unresolved regional gap.

### 11. Job categories

**No standardized, cross-provider job category exists in this dataset, and this cannot be supported without inventing one.**

Verified directly against all 46 providers' `normalize()` implementations:

- **0 of 46** providers expose a job-category field that means the same thing across providers.
- **23 of 46** expose a provider-specific department, team, business-unit, occupation, or function field (e.g. SmartRecruiters' `function`, Taiwan Ministry of Labor's occupation code, USAJOBS's federal job series) — each proprietary to that one provider.
- **23 of 46** expose no category-like field at all (confirmed in code, e.g. Reed's module comment: "no job-category/employment-type field at all").

Evidence that these fields cannot be merged: the stored tag "Engineering" comes from SmartRecruiters' `function` field (6,797 jobs), Greenhouse's `departments` field (1,154 jobs), and Ashby's `department`/`team` field (1,136 jobs) — three structurally unrelated fields that happen to use the same English word. Treating them as one taxonomy would silently merge unrelated data. This project's schema stores all of this in a single free-text `tags` array; a real crosswalk would require manually mapping each provider's raw values, which has not been done.

### 12. Data quality

| Dimension | Finding |
|---|---|
| Missing fields | Confirmed per-provider in code — e.g. Reed exposes no employment-type field at all; no provider exposes usable salary data |
| Company info | 43 of 46 providers give a direct company-name field; 3 derive it (Ashby, Lever, Workday) |
| Duplicate rate (latest re-run) | 8.0% — 15,865 of 197,945 fetched jobs were exact-URL duplicates within that run (item 14) |
| Stale postings | 9.2% of stored jobs are over 1 year old |

### 13. Job freshness

In plain terms: this project has collected jobs from all 46 providers by hand, on two separate occasions so far — not yet on an automatic, recurring schedule. That means we can describe how old the postings looked *at the moment we collected them*, but we cannot yet say how quickly postings actually go stale or get taken down, because answering that requires comparing many collections spread out over time, and continuous monitoring hasn't started.

**What we can say today, from the latest collection:**

- 99.8% of stored jobs have a posting date recorded.
- Half of all stored postings were listed within the last 16 days.
- 63.4% of stored jobs were posted within the last 30 days.
- 9.2% of stored jobs are more than a year old (mostly on a small number of boards, such as some government portals, that keep long-running postings visible).

**What we cannot say yet, and why:** how often a typical posting is removed or filled, and whether a job is still open by the time it's shown, both require repeated collections compared against each other over time. With only two manual collections done so far, close together in time, there isn't yet enough history to measure that.

### 14. Duplicate analysis

Duplicate jobs are removed automatically by comparing each job's web address (URL) — if two postings share the same address, only one is kept. This works well for duplicates from the *same* provider, but not when two *different* providers list the same job under two different addresses (e.g., a company's own careers page vs. an aggregator's copy of it) — that kind of duplicate is harder to catch and isn't currently measured.

Where duplicates are likely or unlikely, by provider category:

**ATS Providers**
- Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Teamtailor, Recruitee, Workable

Reason: Each is queried directly against one specific company's own job board, so overlap between these eight is unlikely — no company is deliberately queried through two ATS platforms at once. The real risk is one of these companies' jobs also showing up via an aggregator below, under a different link.

**Aggregators**
- Adzuna, CareerJet, Reed, Jooble

Reason: These collect postings from many outside sources, which can include companies already pulled in directly through the ATS providers above — so the same job can plausibly appear twice, under two different addresses.

**Government Providers**
- USAJOBS, Bundesagentur für Arbeit, EURES, France Travail

Reason: These generally publish their own postings, so duplicates are less common — except EURES, which itself gathers postings from national agencies including Bundesagentur, so the same government job can legitimately appear on both.

**Niche & Remote Job Boards**
- Himalayas, RemoteOK, We Work Remotely, Hasjob, NoDesk, MyJobMag

Reason: Small, narrowly-scoped boards; no evidence of overlap with any of the categories above.

**How this is handled today:** every job's web address is checked before it's stored, so a repeated address is never stored twice — whether the repeat happens within one collection run or across multiple runs. What isn't caught yet is the same job listed under two different addresses by two different providers; catching that would mean comparing job title, company, and location instead of just the address, which hasn't been built.

### 15. Rate limits

In practical terms, some providers will slow us down or temporarily cut us off if we ask for data too quickly or too often. What that means for how this pipeline should be run:

- **Providers with a fixed data ceiling** (USAJOBS, Bundesagentur für Arbeit, Reed) — these cap how many results they'll ever return, no matter how often we ask. Running the collection more often won't retrieve more from them. No delay is needed, and these are safe to run alongside everything else.
- **Providers that actively throttle requests** (RemoteJobs.org, Findwork.dev, and — newly confirmed in the latest re-run — Arbeitnow) — these return a "too many requests" error if asked too fast. A short pause-and-retry already handles this for RemoteJobs.org and Findwork.dev; Arbeitnow's own request loop has no pause built in yet and needs one added (Section 3.2). None of these three should be run as two copies of themselves at once, but each can run alongside other, different providers without issue.
- **Providers with a paid monthly quota** (SerpApi, OpenWebNinja, TheirStack, Fantastic.jobs) — every collection run uses up part of a monthly allowance. Running these on the same schedule as the free providers would burn through that allowance quickly, so they should run less often (e.g., weekly rather than daily). Fantastic.jobs has already run out of its current quota (Section 3.2).
- **Everything else (the no-registration majority)** — no published limit, though a couple of providers turned out to have an unpublished ceiling only found through testing (e.g. Reed's ~9,900-result limit). The existing automatic pause-and-retry behavior is sufficient protection; no other change is needed.

**Bottom line for scheduling:** the paid/metered providers should run less often to conserve quota; the actively-throttled providers need a delay between requests (already in place for two of the three, still missing for Arbeitnow); everything else can run as often as needed and in parallel.

### 16. Response time & reliability

**No formal benchmarking was performed.** The points below are observations from the latest re-run and the project's source code, not controlled or repeated measurements.

- **Fast (well under a minute):** NAV Arbeidsplassen, USAJOBS, Reed, Workable, Jooble, SerpApi, and most of the small no-registration boards (Jobicy, RemoteOK, MyJobMag, NoDesk, Hasjob, and similar) — each is a single request or a small, fixed number of pages.
- **Slower (several minutes or more):** SmartRecruiters (~9.4 min, but also by far the highest-volume provider), Greenhouse (~3.7 min), Bundesagentur (~2.3 min, includes its own retry logic), Workday (~4.2 min). **Lever was the slowest provider observed — about 42 minutes in the latest re-run, versus about 14.5 minutes in the earlier baseline run** — per-company pagination across 160+ companies, made worse this run by a dropped connection to one large company that triggered extra retries.
- **Needing retries:** most providers (36 of 46) already call a shared helper that automatically retries a failed request after a short pause; a few (e.g. Bundesagentur) use their own custom retry logic instead.
- **Requiring authentication:** 15 of 46 providers need an API key, OAuth, or similar credential (Section 17) — this adds a failure mode (an expired, missing, or over-quota credential) on top of ordinary network issues, and is exactly what's currently blocking CareerOneStop, Trade Me, TheirStack, and Fantastic.jobs (Section 3.2).
- **Returned zero jobs in the latest re-run:** CareerOneStop (no credentials), Trade Me (no credentials), TheirStack (billing block), Fantastic.jobs (quota exceeded), Arbeitnow (rate-limited mid-run), and CareerJet (its allowed-IP list on the provider's side no longer includes this environment) — all six now have a specific, confirmed cause rather than a guess (Section 3.2).
- **Stable:** the 40 providers that completed the latest re-run successfully — including Greenhouse and Lever, where a handful of individual company-level errors were isolated to those companies only, without affecting the rest of the run, confirming the project's per-provider fault isolation works as intended.

### 17. Authentication

| Auth Type | Count (of 46) |
|---|---:|
| None (no auth required) | 31 |
| API key (registered) | 10 |
| Public non-secret key/token (no registration) | 2 |
| OAuth | 2 |
| HTTP Basic | 1 |

Representative providers for each type:

- **No authentication:** Greenhouse, Lever, Ashby, SmartRecruiters, Himalayas, RemoteOK, and 25 others.
- **API key (registered):** Adzuna, Reed, USAJOBS, SerpApi, Findwork.dev, Jooble, OpenWebNinja, TheirStack, Fantastic.jobs, CareerOneStop.
- **Public non-secret key/token (no registration):** Bundesagentur für Arbeit, NAV Arbeidsplassen.
- **OAuth:** France Travail (OAuth2 client credentials), Trade Me Jobs (OAuth 1.0a).
- **HTTP Basic:** CareerJet.

The implemented providers table (Section 4.1) identifies the authentication mechanism used by each individual provider.

### 18. Filtering capabilities

| Provider | Filtering Available |
|---|---|
| SmartRecruiters | Company, offset/limit |
| Greenhouse | Company only |
| Lever | Company, offset/limit |
| NHS Jobs | Keyword |
| USAJOBS | Page/ResultsPerPage only (no keyword/filter params implemented) |
| Bundesagentur für Arbeit | Keyword, location |
| Reed | Pagination only (no keyword/filter params implemented) |
| NAV Arbeidsplassen | Modified-since cursor |
| Ashby | Company only |
| Workable | Company only |

Filtering capability was verified for the ten highest-volume providers; it was **not independently documented for the other 36 implemented providers** in this report. No provider was found to expose salary, experience-level, or visa-sponsorship filtering.

### 19. Must Have / Should Have / Nice to Have

| Priority | Item |
|---|---|
| Must Have | Move normalization inline into the save path |
| Must Have | Scheduled, automated recurring syncs |
| Must Have | Resolve the 6 non-contributing providers (credentials, billing, quota, and one IP-allowlist regression — Section 3.2) |
| Should Have | Reporting dashboard on top of PostgreSQL |
| Should Have | Better location enrichment (~1,565 distinct unresolved country values) |
| Should Have | Normalized employment-type field; a department/occupation crosswalk table |
| Should Have | Dedicated Canada, broader APAC, and Middle East sources |
| Should Have | Provider-run health alerting |
| Should Have | Complete the 6 deferred candidate providers (Saramin, VDAB, CBOP, Work24, GOV.UK Find a Job, Job-Room Switzerland) |
| Nice to Have | Funding-stage/company-size enrichment |
| Nice to Have | Salary capture where a source exposes it |
| Nice to Have | Historical trend tracking across multiple runs |
| Nice to Have | Periodic re-verification of the 268-provider research catalog |

### 20. Production recommendations

Summarized here; full detail in Section 6. Before production reliance: close the 5-provider contribution gap, add provider-run health alerting, move normalization inline, and put the pipeline on a recurring schedule.

---

## 6. Final Recommendations

**Current readiness.** The platform is functionally complete for a first release: 46 providers integrated, 241,564 deduplicated jobs stored in PostgreSQL, offline country/work-arrangement normalization applied, and full fault isolation so one broken provider cannot take down a run. It has been run twice as a **manual, one-off collection**, not an ongoing sync.

**Remaining work, in priority order:**

1. Resolve the 6 providers that did not contribute in the latest re-run, now that each has a confirmed, specific cause (Section 3.2): provision missing credentials (Trade Me), retry CareerOneStop's registration from a network/region that is not geo-blocked, resolve TheirStack's billing block, upgrade or renew Fantastic.jobs' plan (its quota is exhausted), add a delay/backoff to Arbeitnow's pagination loop, and re-add this environment's current IP to CareerJet's partner-dashboard allowlist.
2. Pursue the two highest-value deferred candidate providers — Saramin and VDAB — both real APIs blocked only by a registration/onboarding step.
3. Add provider-run health alerting before scheduling recurring syncs, so a source silently dropping to 0 — or, as seen with CareerJet, silently breaking between runs — doesn't go unnoticed.
4. Move country/work-arrangement normalization inline into the ingestion path, replacing the current manual migration script.
5. Investigate the two low-yield sources (HK Gov Vacancies, MyCareersFuture) before relying on either for APAC coverage.

**Production readiness.** Not yet production-scheduled. Recommended before relying on this pipeline for ongoing reporting: (a) resolve the 6-provider gap above, (b) add health alerting, (c) put the pipeline on a recurring cron/schedule, (d) confirm secrets handling carries through to the deployment target, (e) extend automated test coverage from country normalization to the full aggregation/dedup pipeline.

**Next steps.** Treat the items above as a scoped, well-understood backlog rather than unknowns — none of them block the current dataset from being useful today. The full technical detail, evidence, and provider-by-provider reasoning behind every recommendation is in `Final_Project_Report_v2.md`.

---

*Job Aggregation Platform — Final Project Report · Report date July 16, 2026 · Condensed from `Final_Project_Report_v2.md` for a single 15–20 minute engineering-manager review. No technical finding was removed; long narrative sections were replaced with tables, and repeated explanations were cut. All 46 implemented providers were independently re-executed end-to-end (a live re-run of `jobs.py`, plus isolated re-tests of each failing provider) to verify current status, job counts, and root causes before this update — see Section 3.2 for what changed. The Implemented Providers table (Section 4.1) was re-verified against `sources/*.py` and the latest re-run's output; all 46 providers' Official Reference links were previously re-checked live against each provider's own domain and were not re-checked again in this update, per instruction. Source of truth: PostgreSQL (`jobs`, `provider_runs`), this repository's source code, the latest re-run's live output, and `job_api.xlsx` (API Catalog, Sheet1 sheets). Where a fact could not be verified, this report states "Not publicly available" or "Not verified during this project" rather than estimating.*
