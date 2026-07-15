# Job Aggregation Platform — Final Project Report (Manager Version)

**Internal Engineering Report · Data Platform**

| | |
|---|---|
| **Prepared for** | Engineering Manager |
| **Prepared by** | Reuben Jacob |
| **Report date** | July 15, 2026 |
| **Data snapshot as of** | July 10, 2026 |
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

- **46 providers implemented**; **41 currently contributing live data** to PostgreSQL.
- **184,506 unique job records** stored, deduplicated by URL/hash, with per-provider run history.
- **Offline country and work-arrangement normalization** — no paid geocoding service used.
- The remaining **222 researched providers** were not implemented for specific, documented reasons: no public API, enterprise/partner-only access, wrong data-flow direction (employer-posting tools, not read APIs), deprecated services, or a registration/verification step not yet completed.
- The platform reflects **one complete backfill run**, not yet a recurring schedule — it is ready for operational hardening, not further architecture, before production use.

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
| 41 of 46 providers contributing live data | Partially Completed | 5 non-contributing for external reasons (billing, missing credentials, one zero-result run) — Section 3 |
| Employment-type capture | Partially Completed | Present for 24 of 46 providers; absent for the rest |
| Country resolution long tail | Partially Completed | Multi-country case solved; ~1,565 distinct unresolved single-place values remain |
| Credentialed-provider setup | Partially Completed | 2 of 12 credentialed providers (Trade Me, CareerOneStop) lack credentials in this environment |
| 6 real, accessible candidate providers (Saramin, VDAB, CBOP, Work24, GOV.UK Find a Job, Job-Room Switzerland) | Partially Completed | Registration/verification step outstanding, not rejected |
| Standardized job-category taxonomy | Not Started | No cross-provider taxonomy exists in the data (Section 5, item 11) |
| Salary / visa-sponsorship capture | Not Started | No schema field; no provider exposes it in a usable form |
| Scheduled/automated recurring syncs | Not Started | Every run to date has been a single manual invocation |
| Inline normalization at insert time | Not Started | Currently a separate, manually-triggered migration script |
| Provider-run health alerting | Not Started | No automated flag for a source dropping to 0 jobs |
| Dashboard/analytics UI | Not Started | Static search frontend only |
| Expired-job / posting-removal detection | Not Started | Requires a second ingestion run to diff against; none has occurred |

---

## 3. Implemented APIs

### 3.1 Lifecycle summary

| Stage | Count |
|---|---:|
| Providers researched (API Catalog sheet, `job_api.xlsx`) | 268 |
| Providers shortlisted for close audit (Sheet1, `job_api.xlsx`) | 86 |
| Providers implemented (`sources/*.py`, registered in `sources/__init__.py`) | 46 |
| Providers currently contributing live data | 41 |
| Providers implemented but not currently contributing | 5 |
| Providers researched but not implemented | 222 |

### 3.2 Why 5 implemented providers are not currently live

| Provider | Reason |
|---|---|
| TheirStack | Account's billing plan does not include Jobs API access (HTTP 402) |
| Trade Me Jobs | Built, but no production credentials configured; also requires Trade Me's approval process |
| CareerOneStop | Built, but no credentials configured (`CAREERONESTOP_USER_ID`/`API_TOKEN`) |
| Fantastic.jobs | Credentialed, but returned 0 jobs in the latest run — most plausibly a trial-window/account-tier issue, not confirmed |
| Arbeitnow | Free, no-auth API that previously worked (931 jobs in earlier testing); returned 0 jobs in the latest run — cause not confirmed |

### 3.3 Volume concentration

| Provider | Jobs Stored | % of Total |
|---|---:|---:|
| SmartRecruiters | 65,392 | 35.4% |
| Greenhouse | 22,715 | 12.3% |
| Lever | 17,980 | 9.7% |
| NHS Jobs | 10,843 | 5.9% |
| USAJOBS | 10,000 | 5.4% |
| Bundesagentur für Arbeit | 9,896 | 5.4% |
| Reed | 8,994 | 4.9% |
| NAV Arbeidsplassen | 5,394 | 2.9% |
| Ashby | 5,252 | 2.8% |
| Workable | 4,137 | 2.2% |

Top 3 providers supply 57.4% of all 184,506 stored jobs — volume is concentrated in ATS boards, not evenly spread across all 46 sources.

---


## 4. Complete Provider Research (268 Providers)

Every provider researched in this project (`job_api.xlsx` API Catalog sheet, 268 rows), split into **Implemented (46)** and **Not Implemented (222)**. Pricing model and payment terms are this project's own verified classification of each provider's published terms — where nothing could be confirmed, the cell reads "Not publicly available." Reference is a documented URL/domain found in this project's research notes.


### 4.1 Implemented Providers (46)

| Provider | Pricing Model | Payment After Free Tier | Official Reference | Approx. Jobs (Stored / Fetched) | Status |
|---|---|---|---|---|---|
| SmartRecruiters | No-auth public API | No | developers.smartrecruiters.com/docs/posting-api | 65,392 stored (65,394 fetched) | Live |
| Greenhouse | No-auth public API | No | developers.greenhouse.io/job-board.html | 22,715 stored (22,715 fetched) | Live |
| Lever | No-auth public API | No | github.com/lever/postings-api | 17,980 stored (17,980 fetched) | Live |
| NHS Jobs | No-auth public feed | No | jobs.nhs.uk/api/v1/search_xml | 10,843 stored (13,011 fetched) | Live |
| USAJOBS | Free registration | No | developer.usajobs.gov | 10,000 stored (10,000 fetched) | Live |
| Bundesagentur für Arbeit | No-auth-style public key | No | github.com/bundesAPI/jobsuche-api | 9,896 stored (10,000 fetched) | Live |
| Reed | Free registration | No | reed.co.uk/developers/jobseeker | 8,994 stored (9,000 fetched) | Live |
| NAV Arbeidsplassen | No-auth-style public token | No | navikt.github.io/pam-stilling-feed | 5,394 stored (12,478 fetched) | Live |
| Ashby | No-auth public API | No | developers.ashbyhq.com/docs/public-job-posting-api | 5,252 stored (5,252 fetched) | Live |
| Workable | No-auth public API | No | apply.workable.com (public widget surface) | 4,137 stored (7,627 fetched) | Live |
| Workday | No-auth public API | No | (keyless endpoint, templated per tenant — no fixed docs URL found) | 2,997 stored (2,998 fetched) | Live |
| Himalayas | No-auth public API | No | himalayas.app/jobs/api | 2,253 stored (3,000 fetched) | Live |
| Arbetsförmedlingen | No-auth public API | No | jobsearch.api.jobtechdev.se | 2,096 stored (2,100 fetched) | Live |
| Adzuna | Free tier + paid metered | Yes, beyond free tier/quota | developer.adzuna.com/docs/search | 2,000 stored (2,000 fetched) | Live |
| The Muse | No-auth public tier | No | themuse.com/developers/api/v2 | 2,000 stored (2,000 fetched) | Live |
| CareerJet | Free registration | No | careerjet.com/partners/api | 1,996 stored (2,000 fetched) | Live |
| EURES | No-auth public feed | No | europa.eu/eures (no official public docs) | 1,681 stored (2,000 fetched) | Live |
| RemoteJobs.org | No-auth public API | No | remotejobs.org (in-response docs link 404s) | 1,500 stored (1,500 fetched) | Live |
| France Travail | Free self-service | No | francetravail.io/produits-partages/catalogue/offres-emploi | 1,146 stored (1,150 fetched) | Live |
| Jooble | Free registration | No | jooble.org/api | 1,137 stored (1,137 fetched) | Live |
| Get on Board | No-auth public tier | No | getonbrd.com/api-doc.html | 1,011 stored (1,261 fetched) | Live |
| Taiwan Ministry of Labor | No-auth open data | No | free.taiwanjobs.gov.tw (data.gov.tw dataset 44062) | 1,000 stored (1,000 fetched) | Live |
| Findwork.dev | Free registration | No | findwork.dev/developers | 1,000 stored (1,000 fetched) | Live |
| Mustakbil.com | No-auth public feed | No | rss.mustakbil.com/jobs-rss | 500 stored (500 fetched) | Live |
| Teamtailor | No-auth public feed | No | docs.teamtailor.com | 494 stored (494 fetched) | Live |
| Recruitee (Tellent) | No-auth public API | No | docs.recruitee.com/reference/intro-to-careers-site-api | 394 stored (394 fetched) | Live |
| RemoteOK | No-auth public API | No | remoteok.com/api | 100 stored (100 fetched) | Live |
| MyJobMag | No-auth public feed | No | myjobmag.com/feeds | 100 stored (100 fetched) | Live |
| Jobicy | No-auth public API | No | jobi.cy/apidocs | 100 stored (100 fetched) | Live |
| We Work Remotely | No-auth public feed | No | weworkremotely.com/remote-jobs.rss | 99 stored (100 fetched) | Live |
| 4dayweek.io | No-auth public feed | No | 4dayweek.io/feed | 50 stored (50 fetched) | Live |
| SerpApi (Google Jobs) | Free tier + paid metered | Yes, beyond free tier/quota | serpapi.com/google-jobs-api | 50 stored (50 fetched) | Live |
| OpenWebNinja (JSearch) | Free tier + paid metered | Yes, beyond free tier/quota | openwebninja.com/api/jsearch | 49 stored (49 fetched) | Live |
| Working Nomads | No-auth public API | No | workingnomads.com/jobs | 33 stored (33 fetched) | Live |
| Remotive | No-auth public API | No | remotive.com/api-jobs | 30 stored (30 fetched) | Live |
| Freshersworld | No-auth public feed | No | freshersworld.com/feed | 30 stored (30 fetched) | Live |
| Jobspresso | No-auth public feed | No | jobspresso.co/jobs/feed | 20 stored (20 fetched) | Live |
| MyCareersFuture | No-auth public API | No | api.mycareersfuture.gov.sg (no public docs found) | 20 stored (2,000 fetched) | Needs review |
| NoDesk | No-auth public feed | No | nodesk.co/remote-jobs | 10 stored (10 fetched) | Live |
| Hasjob | No-auth public feed | No | hasjob.co/feed | 6 stored (6 fetched) | Live |
| HK Gov Vacancies | No-auth open data | No | csb.gov.hk/datagovhk/gov-vacancies (data.gov.hk) | 1 stored (58 fetched) | Needs review |
| TheirStack | Per-credit metered (1 credit/job) | Yes | theirstack.com | 0 stored (0 fetched) | Blocked — billing |
| Trade Me Jobs | Free (registered app) | No | developer.trademe.co.nz | 0 stored (0 fetched) | Built, uncredentialed |
| CareerOneStop | Free registration | No | careeronestop.org/Developers/WebAPI/web-api.aspx | 0 stored (0 fetched) | Built, uncredentialed |
| Fantastic.jobs | Free trial → paid metered (~$1/1,000 jobs) | Yes, after trial ends | developer.fantastic.jobs | 0 stored (0 fetched) | Credentialed, 0 result |
| Arbeitnow | No-auth public API | No | arbeitnow.com/api/job-board-api | 0 stored (0 fetched) | 0 in latest run |

### 4.2 Not Implemented Providers (222)

Grouped by research classification at the time of this project. **Registration/Approval Required** and **Needs Live Verification** providers have a real, plausible access path (Section 6, Recommendations); **Not Viable** providers were rejected on structural grounds (no public API, enterprise-only, wrong data-flow direction, deprecated, or a dataset rather than a live API).


#### Registration/Approval Required (4)

| Provider | Pricing Model | Payment After Free Tier | Official Reference | Approx. Jobs Available | Reason Not Implemented |
|---|---|---|---|---|---|
| CBOP - Centralna Baza Ofert Pracy (Poland public employment offices) | Free | No | praca.gov.pl | Potentially large - national public employment office coverage | Poland's national public-employment-office job database. Real SOAP web service returning batches of up to 1,000 live offers per file, but capped at 20 calls/cycle and only reachable during a 17:00-07:00 window -… |
| Saramin Open API (사람인 오픈 API) | Not publicly available (partner-gated access; pricing undisclosed) | Not publicly available | saramin.co.kr | Unknown - Saramin is one of Korea's largest commercial job boards but no public… | One of Korea's largest commercial job boards. Real documented API, but gated behind an application/approval step, explicitly labeled beta with a 500-calls/day cap - usable, just slower to unlock and rate-constrained. |
| VDAB Vacature API (Belgium - Flanders public employment service) | Free, but partner/approval access required (no self-serve signup) | No, once approved, but partner/approval access is itself the… | Not publicly available | Potentially large - Flanders regional coverage | Flanders' public employment service vacancy API - free but requires an application form and an exploratory onboarding meeting with VDAB before credentials are issued. Real read API, just a slower registration path than… |
| Work24 (formerly Worknet/워크넷) Job Listings Open API - Korea Employment Information Service | Free | No | Not publicly available | Potentially large - South Korea's national public employment portal (renamed 고용24 in… | South Korea's national public job bank, verified live on data.go.kr with real-time XML/JSON updates and a free key. Caveat: license text restricts use to non-commercial, attributed, unmodified use - confirm terms with… |

#### Needs Live Verification (4)

| Provider | Pricing Model | Payment After Free Tier | Official Reference | Approx. Jobs Available | Reason Not Implemented |
|---|---|---|---|---|---|
| GOV.UK Find a Job (DWP) | Free | No | Not publicly available | Potentially large | UK's national government job service; no confirmed public read/search API for third parties was found - only an employer-side SFTP bulk-upload path for posting vacancies. Worth one more direct check with DWP given its… |
| Job-Room Jobs API (SECO, Switzerland) | Free, but partner/approval access required (no self-serve signup) | No, once approved, but partner/approval access is itself the… | Not publicly available | Potentially large | Switzerland's biggest job platform, but the API is built primarily for employers/ATS submitting ads under a reporting-obligation rule - whether third-party aggregators can get read-only access is unconfirmed in the… |
| JobsPikr | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | Not publicly available | Unknown (volume not published) | Commercial aggregator (incl. Naukri/Monster-sourced India feeds) with a real API and docs, but pricing is custom/quote-based rather than a published self-serve rate - confirm actual signup process and cost before… |
| Portal del Empleo / Servicio Nacional de Empleo (STPS Mexico) | Free | No | Not publicly available | Potentially large | Mexico's national employment service publishes datasets on the CKAN-based datos.gob.mx open-data platform, but a live, current-vacancy-specific API endpoint for the job board itself was not directly confirmed - may… |

#### Not Viable at Research Time (214)

| Provider | Pricing Model | Payment After Free Tier | Official Reference | Approx. Jobs Available | Reason Not Implemented |
|---|---|---|---|---|---|
| 104 Job Bank (104人力銀行) | Not applicable, no public API | Not applicable, no public API | 104.com.tw | ~1.1 million (110萬, Feb 2026) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| 1111 Job Bank (1111人力銀行) | Not applicable, no public API | Not applicable, no public API | 1111.com.tw | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| 51job (前程无忧 / Qiancheng Wuyou) | Not applicable, no public API | Not applicable, no public API | 51job.com | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| AMS eJob-Room (Austria public employment service) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| APEC (Association Pour l'Emploi des Cadres, France) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| APS Jobs (Australian Public Service careers) | Not applicable, no public API | Not applicable, no public API | apsjobs.gov.au | Moderate | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Adecco India | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Agencia Publica de Empleo SENA (APE) | Not applicable, no public API | Not applicable, no public API | edu.co | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| AllJobs.co.il | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | AllJobs.co.il | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Apideck | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | apideck.com/pricing | Not publicly available | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Workday - we already integrate directly for free). Redundant and enterprise-priced. |
| Apify | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | apify.com/pricing | Not publicly available | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Apna | Not applicable, no public API | Not applicable, no public API | Not publicly available | Large, blue-collar (board size; no public access) | No public API for third-party aggregators. |
| Appcast | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | appcast.io/how-programmatic-recruitment-advertising-improves-cost-per-hire/ | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Aura (by Aura Intelligence) | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Proprietary workforce database spanning 20M+ companies (billions of data points;… | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| BMET / Ami Probashi (Bangladesh Overseas Employment) | Not applicable, no public API | Not applicable, no public API | amiprobashi.com | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| BOSS Zhipin (Kanzhun Limited, NASDAQ: BZ) | Not applicable, no public API | Not applicable, no public API | zhipin.com | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| BambooHR | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Not publicly available (N/A - per-tenant only, no aggregate feed) | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Bayt.com | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | Bayt.com | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bdjobs.com | Not applicable, no public API | Not applicable, no public API | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bolsa Nacional de Empleo (BNE / SENCE, Chile) | Free | No | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bossjob | Free | No | bossjob.com | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bright Data | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | brightdata.com/products/web-scraper/jobs-scraper | 116.8M+ records (general Jobs dataset); LinkedIn Jobs dataset specifically 62.4M+ | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| BrighterMonday | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | brightermonday.co.ke | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Broadbean (Veritone Hire) | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | broadbean.com/product-suite/job-distribution-platform/ | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Built In | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (tech/startup; not quantified) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bumeran | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CEIPAL | Not publicly available | Not publicly available | ceipal.com/pricing | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CV-Library | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CWJobs | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | CWJobs.co.uk | 12,000+ jobs (per cwjobs.co.uk About Us page) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CareerBuilder | Not publicly available (partner-gated access; pricing undisclosed) | Not publicly available | careerbuilder.com/ | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CareerBuilder / Monster (Talent Network distribution) | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | careerbuilder.com/talent-network | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| CareerLink Vietnam | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CareerOne (Australia) | Not publicly available (partner-gated access; pricing undisclosed) | Not publicly available | careerone.com.au | 100,000+ (live jobs) | Feed-ingest / posting-distribution network only - no public read endpoint for pulling job data as a consumer. |
| Careers24 | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | careers24.com | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Careers@Gov | Not applicable, no public API | Not applicable, no public API | Not publicly available | Small (SG public sector; not quantified) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Catho Developer API | Not publicly available (partner-gated access; pricing undisclosed) | Not publicly available | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| China MOHRSS National Public Employment Service Platform (全国公共招聘服务平台) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Civil Service Jobs | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (not quantified) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Claro Analytics (WilsonHCG) | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | claroanalytics.com/ | Real-time job-postings and 500M+ global talent profiles | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Cliclavoro / Ministero del Lavoro Open Data (Italy) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Computrabajo | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Coresignal | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | 399M+ multi-source records (incl. India) | Enterprise-tier data vendor sold via sales contact, not a published self-serve price - same bucket as the other enterprise data vendors below. |
| Cutshort | Not applicable, no public API | Not applicable, no public API | Not publicly available | Small (tech; board size not public) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Darwinbox | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Not publicly available (N/A - per-tenant only, no aggregate feed) | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Datapeople (by Payscale) | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | datapeople.io/ | Not publicly available (N/A (analyzes customer job postings, not a broad aggregation… | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Dice | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (tech niche; not quantified) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Diffbot | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | diffbot.com/pricing | Not publicly available | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Draup | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | draup.com/ | Global labor-market and job-postings data (aggregated multi-source) | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Drushim | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | Drushim.co.il | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Egypt Ministry of Labour (formerly Ministry of Manpower) Job Portal | Not applicable, no public API | Not applicable, no public API | labour.gov.eg | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Elempleo | Not applicable, no public API | Not applicable, no public API | Not publicly available | Very large (CO; not quantified) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Eluta | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Employment Services of South Africa (ESSA) - Dept. of Employment and Labour | Free | No | labour.gov.za | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Forasna | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | forasna.com/employer/pricing | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Foundit (Monster India) | Not applicable, no public API | Not applicable, no public API | Not publicly available | ~800k+ (board size; no public access) | No public API for third-party aggregators. |
| Freshteam | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Not publicly available (N/A - per-tenant only, no aggregate feed) | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Glassdoor Jobs API | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | glassdoor.com/developer/index.htm | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Glints | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Google Cloud Talent Solution (Job Search API) | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | google.com/talent-solution/pricing | Not publicly available (N/A (you populate it with your own jobs; not an aggregation… | This is a hosted ML matching/search engine you populate with your OWN job postings - it is not a source of aggregated third-party listings at all. Enterprise infrastructure product, not a job feed. |
| Google for Jobs | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | schema.org | Unknown (indexes open web) | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Greenwich.HR (WageScape) | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | amazon.com/marketplace/pp/prodview-t5fvgfurgypxg | ~5M new US jobs/month; ~70% of all open US jobs; 1.5M+ hiring organizations | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| GreytHR | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Not publicly available (N/A - HRMS/payroll only, no job feed) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| GulfTalent | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | gulftalent.com | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Gupy Public API | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | gupy.io | ~90,000 job vacancies published monthly on the Gupy R&S platform (official figure) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| HackerEarth Jobs | Not applicable, no public API | Not applicable, no public API | Not publicly available | Small (board size not public) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| HasData | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | hasdata.com/prices | Not publicly available | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Hello Work Job Information API (ハローワーク求人情報提供サービス, MHLW) | Free | No | Not publicly available | Potentially large - nationwide public employment service covering hundreds of thousands… | Japan's real, fully-documented national job API - but registration is restricted to licensed private job-placement businesses, local governments, or training institutions. A generic aggregator does not qualify for… |
| HelloWork ATS Partner API (France) | Free, but partner/approval access required (no self-serve signup) | No, once approved, but partner/approval access is itself the… | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Hired.com (LHH Recruitment Solutions) | Not applicable, no public API | Not applicable, no public API | Hired.com | 0 | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Hirist | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (tech; board size not public) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Hong Kong Labour Department Interactive Employment Service (iES, jobs.gov.hk) | Not applicable, no public API | Not applicable, no public API | www.jobs.gov | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Horsefly Analytics | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | horseflyanalytics.com/ | 1 trillion+ data points; millions of job postings; supply/demand across 60+ countries | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| IEFPOnline / netEmprego (Portugal public employment service) | Not applicable, no public API | Not applicable, no public API | Not publicly available | 5,913 ofertas de emprego (live count) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Indeed Hiring Lab | Free | No | indeed.com | Not publicly available (N/A (publishes indices/aggregates, e.g. Job Postings Index, Wage… | Indeed's economic-research arm: publishes aggregate labor-market indices/trend CSVs (mirrored on FRED), not individual job records. Research/statistics product, not a live job listings feed. |
| Indeed India | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Huge (not accessible - partner-only) | Enterprise partner-only access; not available to a generic aggregator. |
| Indeed PLUS Job Distribution API (Recruit Holdings, Japan) | Not publicly available (partner-gated access; pricing undisclosed) | Not publicly available | Not publicly available | Potentially large - aggregates postings across Japan's major job boards distributed via… | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| InfoJobs (Spain) | Not applicable, no public API | Not applicable, no public API | Not publicly available | 68,383 ofertas (live count, Spain, as of July 2026) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Instahyre | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (tech; board size not public) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Internshala | Not applicable, no public API | Not applicable, no public API | Not publicly available | Large (intern/fresher; board size not public) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Israeli Employment Service (Sherut HaTaasuka / taasuka.gov.il) | Free | No | taasuka.gov.il | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JSearch (RapidAPI, by OpenWeb Ninja) | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch | Not publicly available | Generic B2B data-aggregation vendor, not a dedicated job board - paid, and overlaps with sources already integrated. |
| Jadarat (Saudi National Employment Portal / HRDF) | Free | No | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Job Bank (ESDC) feed / Open Gov dataset | Free | No | Not publicly available | Very large (100,000+) | Canada's national job bank: the live feed requires ESDC partner approval, and the fallback open dataset is a monthly CSV dump missing employer/company names and per-job apply URLs - the two fields this project's schema… |
| Job Market Finland / Tyomarkkinatori (TE-palvelut, Finland) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobKorea | Not applicable, no public API | Not applicable, no public API | Not publicly available | ~209,637 (live listings) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobStreet / JobsDB (SEEK group) | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Very large if accessible (not public) | SEEK-group flagship boards for SEA; enterprise partner-only access, no self-serve path (catalog explicitly marks 'Not Recommended'). |
| JobThai | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | jobthai.com | ~121,000 active jobs (121,337 shown live on jobthai.com) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobberman | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | jobberman.com | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobcase (MaxRecruit) | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | jobcase.com/products/maxrecruit | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Jobcase Platform API | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | jobcase.com/ | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobg8 | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | jobg8.com/Faq.aspx?contentid=10874 | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Jobillico | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobindex (Denmark) | Not applicable, no public API | Not applicable, no public API | Not publicly available | 33,600 jobs (live) / 30,000+ job ads | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobisJob (LIFULL Connect) | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | jobboardfinder.com/jobboard-jobisjob-usa | ~9,000,000 (monthly, cross-country) | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Jobnet.dk (Denmark public employment portal) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobrapido | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | jobrapido.com | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobs.cz | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Medium (CZ/SK; not quantified) | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| JobsDB Hong Kong (SEEK Group) / CTgoodjobs | Not applicable, no public API | Not applicable, no public API | hk.jobs | ~32,700 (JobsDB HK) / ~32,000 (CTgoodjobs) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobsEQ (Chmura Economics & Analytics) | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | chmura.com/jobseq | Real-time job-posting dataset with international coverage | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| JobsIreland.ie (Ireland public employment service) | Not applicable, no public API | Not applicable, no public API | Not publicly available | 4,806 vacancies (live count) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobsite | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Jobsite.co.uk | 280,000+ live job adverts (per jobsite.co.uk About Us page) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JoinVision (JobCloud HR Tech) | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | crunchbase.com/organization/joinvision | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Jora (Australia) | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | jora.com | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Joveo | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | joveo.com/programmatic-job-advertising-platform/ | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| JustRemote | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | justremote.co/remote-jobs | 2,000+ hidden remote jobs | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Kalibrr | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Karir.com | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Keka | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Not publicly available (N/A - HRMS/payroll only, no job feed) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Kelly Services India | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Kemnaker Karirhub (SIAPkerja) | Free, but partner/approval access required (no self-serve signup) | No, once approved, but partner/approval access is itself the… | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Kombo.dev | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | kombo.dev/pricing | Not publicly available | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Workday - we already integrate directly for free). Redundant and enterprise-priced. |
| Ladders | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (niche; not quantified) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Lensa | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | lensa.com/ | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Lightcast (formerly Emsi Burning Glass) Job Postings API | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | lightcast.dev/apis/job-postings | Billions of postings aggregated from 160,000+ sources (18B+ labor-market data points) | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Lightcast Jobs Canada | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | Not publicly available | Not publicly available | Paid labor-market-intelligence product sold through a sales process, not a self-serve developer signup; catalog itself marks 'Not Recommended'. |
| LinkUp | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | linkup.com | Millions of postings indexed daily from 80,000+ employer websites | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| LinkedIn Jobs | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Huge (not accessible - partner-only) | Enterprise partner program only - no self-serve developer signup for job search/aggregation. |
| MOHRE UAE Federal Careers / iRecruitment Portal | Not applicable, no public API | Not applicable, no public API | mohre.gov.ae | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| MP Rojgar | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (state-level; not quantified) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| MahaJobs | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (state-level; not quantified) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| ManpowerGroup India | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Mantiks | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | mantiks.io/pricing | Not publicly available | Generic B2B data-aggregation vendor, not a dedicated job board - paid, and overlaps with sources already integrated. |
| Merge.dev | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | merge.dev/pricing/unified | Not publicly available | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Workday - we already integrate directly for free). Redundant and enterprise-priced. |
| Mitula (LIFULL Connect / Adzuna) | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | lifullconnect.com/brands/mitula/ | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Monster | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | monster.com/solutions/talent-management/partner-with-monster/ | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| NAVTTC National Employment Exchange Tool (NEXT / jobs.gov.pk) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| NEAIMS - National Employment Authority Kenya | Free | No | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| National Career Service (NCS) | Free | No | data.gov.in | Large in aggregate | India's NCS exposes a periodic bulk open-government dataset (data.gov.in), not a live per-job search API - stale snapshots, not real-time postings. Doesn't fit a live-fetch architecture. |
| National Directorate of Employment (NDE) Nigeria | Not applicable, no public API | Not applicable, no public API | nde.gov.ng | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| National Job Portal (NJP) - Pakistan | Not applicable, no public API | Not applicable, no public API | njp.gov.pk | Small-to-moderate | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| National Job Portal - Bangladesh (jobs.gov.bd) | Not applicable, no public API | Not applicable, no public API | jobs.gov.bd | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Naukri | Not applicable, no public API | Not applicable, no public API | Not publicly available | ~1M+ (board size; no public access) | No public API; any access is undocumented/grey-area and India-IP-restricted. |
| Naukrigulf | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | naukrigulf.com | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Nexxt (formerly Beyond.com) | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | Beyond.com | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Nimble (Nimbleway) | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | nimbleway.com/pricing | Not publicly available | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| OCC Mundial | Not applicable, no public API | Not applicable, no public API | Not publicly available | 137,925 active vacancies ("vacantes activas en occ.com.mx", as of Oct 18, 2024);… | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Outsourcely | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | outsourcely.com | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Oxylabs | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | oxylabs.io/products/scraper-api/web/pricing | Not publicly available | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| PandoLogic (pandoIQ) / Veritone Hire | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | pandologic.com/solutions/programmatic-advertising-pandoiq/ | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Pangian | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | pangian.com/feed/?post_type=job_listing | Varies (curated remote listings) | pangian.com redirects (301) to a static 'Thank You for Being Part of Pangian' shutdown notice on GitHub Pages (pangianhq.github.io) - confirmed live. Every other path (/jobs/, /about/, /blog/, all RSS-candidate URLs)… |
| People Data Labs | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | peopledatalabs.com/docs/job-posting-data-overview | Not publicly available | Generic B2B data-aggregation vendor, not a dedicated job board - paid, and overlaps with sources already integrated. |
| PhilJobNet (DOLE Bureau of Local Employment) | Free | No | philjobnet.gov.ph | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Piloterr | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | piloterr.com/pricing | Not publicly available | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Pnet | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | pnet.co.za | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Portal Empleo Argentina (Ministerio de Capital Humano / ex-Trabajo) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Pracuj.pl (Poland) | Not applicable, no public API | Not applicable, no public API | Not publicly available | 762,827 job offers published in 2025 | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| PredictLeads | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | predictleads.com/pricing | 270M+ records since 2018; ~9.8M active jobs | Generic B2B data-aggregation vendor, not a dedicated job board - paid, and overlaps with sources already integrated. |
| Profesia | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Medium (CZ/SK; not quantified) | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Public Service Commission of Sri Lanka (psc.gov.lk) | Not applicable, no public API | Not applicable, no public API | psc.gov.lk | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Quess Corp | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Radancy | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | radancy.com/en/programmatic-adtech/ | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Randstad India | Not applicable, no public API | Not applicable, no public API | Not publicly available | 1,394 jobs (live count on official site) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Recruit CRM | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Not publicly available (N/A - per-tenant only, no aggregate feed) | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Recruitics | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | recruitics.com/programmatic-job-advertising | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Remote First Jobs (Dynamite Jobs) | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | remotefirstjobs.com/rss | Varies (curated remote-first listings) | remotefirstjobs.com is behind an active Cloudflare managed JS challenge on every path tested (including robots.txt itself) - confirmed live, HTTP 403 with a 'Just a moment...' interactive challenge page. Not a… |
| Remote.co | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | remote.co/feed | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Revelio Labs | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | reveliolabs.com | 1.1B+ workforce profiles plus job postings, transitions, sentiment, layoffs | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Rikunabi / Mynavi (Recruit Co. / Mynavi Corporation) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Rojgar Sangam (UP) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (state-level; not quantified) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Rozee.pk | Not applicable, no public API | Not applicable, no public API | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| SEEK (SEEK.com.au / SEEK.co.nz) | Free, but partner/approval access required (no self-serve signup) | No, once approved, but partner/approval access is itself the… | SEEK.com.au | Potentially large | Feed-ingest / posting-distribution network only - no public read endpoint for pulling job data as a consumer. |
| SEPE Open Data Portal (Spain public employment service) | Free | No | Not publicly available | Not publicly available | Spain's SEPE only publishes static statistical/administrative open-data files - no confirmed live REST API for current vacancies exists; a known third-party scraper for it is deprecated. |
| SINE Aberto (Sistema Nacional de Emprego / Ministerio do Trabalho e Emprego) | Free | No | dados.gov.br/dataset/sine-aberto | Potentially large | Brazil suspended this data-sharing service in October 2022 (CODEFAT Resolution 956/2022) pending LGPD privacy-law compliance updates - no active API to integrate against right now. |
| ScraperAPI | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | scraperapi.com/pricing | Not publicly available | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Scrapingdog | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | scrapingdog.com/pricing | Not publicly available | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Shine | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (board size; no public access) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| SmartDreamers | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | smartdreamers.com/pricing | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Snagajob | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | snagajob.com/ | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| StepStone | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | stepstone.com | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Superset | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Medium (campus; per-institution, not aggregatable) | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Talent.com | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Talent.com | 40 million+ jobs (global figure stated on talent.com homepage) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| TalentNeuron (Gartner) | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | talentneuron.com/solutions/platform | Real-time labor data covering ~90% of world GDP; 40TB normalized data, 3B+ profiles,… | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Talroo | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | talroo.com/pro/ | Millions (per Talroo publisher marketing) | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| TeamLease | Not applicable, no public API | Not applicable, no public API | Not publicly available | 23,082+ active job vacancies (live count on official site) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Techmap.io | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | jobdatafeeds.com | 292M+ available jobs | Generic B2B data-aggregation vendor, not a dedicated job board - paid, and overlaps with sources already integrated. |
| Telangana T-Jobs | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (state-level; not quantified) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Textkernel Jobfeed / Market IQ | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | textkernel.com/products-solutions/labour-market-insights/market-iq/ | Large multi-country vacancy corpus (millions of postings, deduplicated/enriched) | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Thailand Department of Employment - Smart Job Center (ไทยมีงานทำ) | Free | No | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| The Burning Glass Institute | Free | No | burningglassinstitute.org/ | Not publicly available (N/A (research using Lightcast and other data)) | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| TimesJobs | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (board size; no public access) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| TopCV | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| TotalJobs | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Totaljobs.com | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Triplebyte | Free, but partner/approval access required (no self-serve signup) | No, once approved, but partner/approval access is itself the… | triplebyte.com/ | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Trovit (LIFULL Connect / Adzuna) | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | trovit.com/feed-in-jobs/ | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| UWV Open Match Data (Netherlands) | Free | No | Not publicly available | Not publicly available (N/A - aggregated statistics only, not individual postings) | UWV (Dutch public employment service) publishes aggregate labor-market statistics datasets, not individual live job postings - no per-job identifier exists in the data at all. |
| Unified.to | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | Not publicly available | Not publicly available | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Workday - we already integrate directly for free). Redundant and enterprise-priced. |
| Unstop | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (campus/intern; not a job-listing API) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Upward.net (a Jobcase company) | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | upward.net/employers | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Vagas for Business API (Vagas.com.br) | Not publicly available (partner-gated access; pricing undisclosed) | Not publicly available | Vagas.com | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| VietnamWorks Open API | Not publicly available (partner-gated access; pricing undisclosed) | Not publicly available | vietnamworks.com | Potentially large | Partner Access Required - gated to approved commercial partners, not open developer registration. |
| WUZZUF | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | wuzzuf.net | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Welcome to the Jungle | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Wellfound | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (startup roles; board size not public) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| WhatJobs | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | whatjobs.com/job-aggregators | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Work and Income / Find a Job (MSD, New Zealand) | Not applicable, no public API | Not applicable, no public API | workandincome.gov | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Work at a Startup (Y Combinator) | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | workatastartup.com | Unknown (thousands across 1,000+ YC companies) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| WorkIndia | Not applicable, no public API | Not applicable, no public API | Not publicly available | Large, blue-collar (board size; no public access) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Workato | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | workato.com/pricing | Not publicly available | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Workday - we already integrate directly for free). Redundant and enterprise-priced. |
| Workforce Australia | Free | No | workforceaustralia.gov.au | Potentially large | The public API is write/management-only (employers create and manage job ads via OAuth2 through the Business portal) - no public job-listings read/search endpoint exists to pull postings from. |
| Workopolis | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| WowJobs | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Xing Jobs | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| XpressJobs (xpress.jobs) | Not applicable, no public API | Not applicable, no public API | Not publicly available | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| ZipAlerts (ZipRecruiter TrafficBoost) | Not applicable to data access (fee is for employers posting jobs on this platform, not… | Not applicable to data access (see Pricing Model column) | zipalerts.com/ | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| ZipRecruiter API | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Large (not quantified) | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Zoho Recruit | Enterprise | Yes, enterprise/sales pricing, no self-serve free tier | Not publicly available | Not publicly available (N/A - per-tenant only, no aggregate feed) | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| ZonaJobs | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | zonajobs.com.ar | Not publicly available | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Zyte (formerly Scrapinghub) | Free Tier + Pay-as-you-go | Yes, beyond the free tier/quota | zyte.com/zyte-api/pricing.html | Not publicly available | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| data.gov.in OGD platform | Free | No | Not publicly available | Varies (per-resource) | General-purpose Indian open-government-data portal spanning 33 sectors; not jobs-specific, and individual resources are static per-resource datasets rather than a live job-postings feed. |
| eQuest | Paid (metered/flat; see Cost Details column source for exact terms) | Yes, paid from the outset, no free tier documented | equest.com/ | Not publicly available | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| iimjobs | Not applicable, no public API | Not applicable, no public API | Not publicly available | Medium (management roles; board size not public) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| jobs.ch (Switzerland) | Not applicable, no public API | Not applicable, no public API | Not publicly available | 45,825 jobs (live) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| karriere.at (Austria) | Not applicable, no public API | Not applicable, no public API | github.com/karriereat | 13,400+ jobs (live) | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| topjobs.lk | Not applicable, no public API | Not applicable, no public API | Not publicly available | Potentially large | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |

---

## 5. Internship Requirement Coverage

### 2. Final project report

This document, together with the companion technical report `Final_Project_Report_v2.md`, is the final project report.

### 3. APIs/services used

46 providers implemented (Section 3); 268 researched in total (Section 4).

### 4. Completed vs. pending

See the [Project Status table](#2-project-status) (Section 2).

### 5. Fully / partially / not started

See the [Project Status table](#2-project-status) (Section 2).

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

| Answer | Count (of 46 implemented) |
|---|---:|
| No (free with no paid tier) | 41 |
| Yes, beyond a free tier/quota, or after a trial | 5 |

### 8. Pricing / documentation links

All 46 implemented providers have an official reference URL, quoted directly from source code (Section 4.1). Of the 222 not-implemented providers, a documented reference (domain or URL) was found in this project's research for **166 of 268 providers overall**; for the remainder, the reference cell reads "Not publicly available" rather than a guessed link (Section 4.2).

### 9. Number of jobs

| Metric | Value |
|---|---:|
| Total unique jobs stored (PostgreSQL) | 184,506 |
| Total jobs fetched, all providers, pre-dedup | 200,727 |
| Distinct companies represented | 18,367 |

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
| Duplicate rate | 8.08% overall (see item 14 below) |
| Stale postings | 11.9% of stored jobs are over 1 year old |

### 13. Job freshness

| Metric | Value |
|---|---:|
| Jobs with a posted date recorded | 184,129 of 184,506 (99.8%) |
| Median posting age | 22 days |
| Mean posting age | 229 days (skewed by a long tail of old postings on some boards) |
| Posted within 30 days of snapshot | 108,003 (58.6%) |
| Older than 1 year | 21,915 (11.9%) |

Refresh frequency and expired-job detection are **not verified during this project** — the dataset reflects one ingestion run, not a recurring schedule, so there is no interval or diff to measure yet.

### 14. Duplicate analysis

| Metric | Value |
|---|---:|
| Total in-run duplicates skipped (all providers) | 16,221 |
| Total fetched, pre-dedup | 200,727 |
| Overall deduplication rate | 8.08% |
| Cross-provider duplicate URLs remaining | 0 |

Highest duplicate rates: MyCareersFuture (99.0%, `limit` param silently ignored by the provider), HK Gov Vacancies (98.3%, every job shares one generic portal URL), NAV Arbeidsplassen (56.8%, a change-feed rather than a current-postings search), Workable (45.8%, the same job posted to multiple cities, correctly collapsed).

### 15. Rate limits

| Limit type | Examples |
|---|---|
| Hard result-window ceiling | USAJOBS and Bundesagentur für Arbeit (10,000 records); Reed (~9,900, returns HTTP 500 beyond it) |
| Monthly quota | SerpApi and OpenWebNinja (200 requests/month free tier) |
| Per-job billing | TheirStack (1 credit per job returned) |

The examples above are the limits discovered and documented during implementation (`Final_Project_Report_v2.md`, Section 7); not all 46 providers' rate limits were independently re-verified for this report.

### 16. Response time & reliability

| Provider | Duration (s) | Reliability |
|---|---:|---|
| SmartRecruiters | 385.7 | High |
| Lever | 870.1 | High (slowest run despite modest volume — per-company pagination overhead) |
| Greenhouse | 183.8 | High |
| NHS Jobs | 102.4 | Undocumented endpoint (no official API contract) |
| USAJOBS | 53.1 | High |
| Bundesagentur für Arbeit | 174.3 | High (with retry logic) |
| Reed | 56.6 | High |
| NAV Arbeidsplassen | 51.4 | Rotating token (no fixed key) |
| Ashby | 70.3 | High |
| Workable | 51.8 | High |

Full duration/reliability figures for all 46 providers exist in the underlying `provider_runs` table; only the ten highest-volume providers are shown here for brevity.

### 17. Authentication

| Auth Type | Count (of 46) |
|---|---:|
| None (no auth required) | 31 |
| API key (registered) | 10 |
| Public non-secret key/token (no registration) | 2 |
| OAuth | 2 |
| HTTP Basic | 1 |

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
| Must Have | Resolve the 5 non-contributing providers (credentials, billing, root-cause) |
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

**Current readiness.** The platform is functionally complete for a first release: 46 providers integrated, 184,506 deduplicated jobs stored in PostgreSQL, offline country/work-arrangement normalization applied, and full fault isolation so one broken provider cannot take down a run. It reflects **one complete backfill run**, not an ongoing sync.

**Remaining work, in priority order:**

1. Provision missing credentials (Trade Me, CareerOneStop), resolve TheirStack's billing block, verify Fantastic.jobs' trial/account status, and re-run Arbeitnow to confirm its 0-job result was transient.
2. Pursue the two highest-value deferred candidate providers — Saramin and VDAB — both real APIs blocked only by a registration/onboarding step.
3. Add provider-run health alerting before scheduling recurring syncs, so a source silently dropping to 0 doesn't go unnoticed.
4. Move country/work-arrangement normalization inline into the ingestion path, replacing the current manual migration script.
5. Investigate the two low-yield sources (HK Gov Vacancies, MyCareersFuture) before relying on either for APAC coverage.

**Production readiness.** Not yet production-scheduled. Recommended before relying on this pipeline for ongoing reporting: (a) resolve the 5-provider gap above, (b) add health alerting, (c) put the pipeline on a recurring cron/schedule, (d) confirm secrets handling carries through to the deployment target, (e) extend automated test coverage from country normalization to the full aggregation/dedup pipeline.

**Next steps.** Treat the items above as a scoped, well-understood backlog rather than unknowns — none of them block the current dataset from being useful today. The full technical detail, evidence, and provider-by-provider reasoning behind every recommendation is in `Final_Project_Report_v2.md`.

---

*Job Aggregation Platform — Final Project Report (Manager Version) · Data snapshot 2026-07-10 · Report date July 15, 2026 · Condensed from `Final_Project_Report_v2.md` for a single 15–20 minute engineering-manager review. No technical finding was removed; long narrative sections were replaced with tables, and repeated explanations were cut. Source of truth: PostgreSQL (`jobs`, `provider_runs`), this repository's source code, and `job_api.xlsx` (API Catalog, Sheet1 sheets). Where a fact could not be verified, this report states "Not publicly available" or "Not verified during this project" rather than estimating.*
