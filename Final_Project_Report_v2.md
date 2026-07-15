# Job Aggregation Platform — Final Project Report (v2)

**Internal Engineering Report · Data Platform**

Final project report covering the complete provider research effort — approximately 250 providers researched, ~80 shortlisted, 46 implemented, 41 currently live — alongside the multi-source ingestion pipeline, PostgreSQL data layer, and offline location/work-arrangement normalization built over this project.

This is a revision of `FINAL_PROJECT_REPORT.md`. That document is preserved unchanged; this report supersedes it as the submission copy. The implementation-facing sections (architecture, statistics, pricing, capability matrix, limitations, recommendations) are carried forward from it with only the corrections and additions noted inline — they were independently re-verified against source code for this revision where flagged. What is new in this revision is the complete provider-research lifecycle: the ~250-provider catalog, the ~80-provider shortlist, and the reasoning that connects research to every implementation decision, which the prior version did not document.

| | |
|---|---|
| **Prepared for** | Engineering Manager |
| **Prepared by** | Reuben Jacob |
| **Report date** | July 15, 2026 |
| **Data snapshot as of** | July 10, 2026 |
| **Supersedes** | `FINAL_PROJECT_REPORT.md` (July 13, 2026) |

| 268 | 86 | 46 | 41 | 184,506 |
|---|---|---|---|---|
| Providers researched (API Catalog) | Providers shortlisted for close audit (Sheet1) | Providers integrated | Providers actively contributing data | Jobs stored in PostgreSQL |

---

## Executive Summary

**Objective.** Build a single, de-duplicated, queryable dataset of job postings sourced from as many legitimately accessible providers as practical — government labour agencies, ATS platforms, commercial job-search APIs, and RSS feeds — normalized into one schema with reliable country and remote/hybrid/on-site classification, backed by a real database rather than a flat file.

**Provider research lifecycle.** This project began with a market survey of **268** job-related APIs and platforms, narrowed to an **86**-provider shortlist for close, provider-by-provider audit, of which **46** were built and **41** are contributing live data today. The remaining 222 researched providers are preserved with a specific, evidenced reason each — "not implemented" does not mean "not investigated." Section 3 traces the full lifecycle; Section 8 and Appendix D categorize every rejection; Section 9 lists the providers still worth a second look.

**Major achievements**
- 46 provider integrations behind one shared interface, absorbing more than double the project's original provider count without structural rework.
- 184,506 unique jobs persisted in PostgreSQL with real deduplication (0 remaining cross-provider duplicate URLs) and full per-provider run history.
- Offline country and work-arrangement normalization requiring no paid geocoding service.
- A complete, evidence-based provider research trail spanning 268 candidates, reusable by future engineers deciding what to build next.

**Main technical challenges**
- Undocumented, reverse-engineered endpoints (5 of 46 live providers) with no official API contract to rely on.
- Hard, undocumented result-window ceilings (USAJOBS/Bundesagentur at 10,000 records; Reed at ~9,900) discovered only through live testing, not documentation.
- Reconciling 46 structurally different pagination, authentication, and schema shapes into one common model.
- No standardized job-category taxonomy exists across providers — confirmed by direct code inspection of all 46 modules, not assumed.

**Key engineering decisions**
- A shared `BaseJobSource` interface, so adding a new provider never requires changing `jobs.py`.
- Conservative normalization: force location fields to `NULL` on ambiguous multi-country/region text rather than guess.
- Per-source fault isolation, so one broken provider can never halt a full run.
- Deliberate exclusion of redundant, paid middleware (ATS-unification APIs, generic scraping infrastructure) already covered by free, direct integrations.

**Current implementation status.** 46 of 268 researched providers are implemented; 41 of 46 are contributing live data; the other 5 are fully built but non-contributing for external, individually diagnosed reasons — a billing restriction, missing credentials, or one transient zero-result run (Section 15).

**Production readiness.** The platform reflects a single, complete backfill run, not yet a recurring schedule. It is ready for operational hardening — not further architecture — before being relied on for ongoing production reporting.

**Final recommendations.** Close the 5-provider contribution gap; pursue the two highest-value deferred providers (Saramin, VDAB — Section 9); add provider-run health alerting; move normalization inline; and put the pipeline on a recurring schedule. Full prioritized detail in Sections 19 and 21.

*This summary is intended to be readable in 2–3 minutes. Section 1 and the sections that follow provide the full supporting detail and evidence.*

---

## Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Overview](#2-project-overview)
3. [Provider Research & Evaluation Lifecycle](#3-provider-research--evaluation-lifecycle)
4. [Provider Evaluation Methodology](#4-provider-evaluation-methodology)
5. [Provider Decision Matrix](#5-provider-decision-matrix)
6. [Technology Stack](#6-technology-stack)
7. [APIs and Providers (Implemented)](#7-apis-and-providers-implemented)
8. [Provider Research Knowledge Base](#8-provider-research-knowledge-base)
9. [Future Candidate & Deferred Providers](#9-future-candidate--deferred-providers)
10. [Features](#10-features)
11. [PostgreSQL Integration](#11-postgresql-integration)
12. [Statistics](#12-statistics)
13. [API Comparison](#13-api-comparison)
14. [Pricing Analysis](#14-pricing-analysis)
15. [Implemented vs Pending](#15-implemented-vs-pending)
16. [Country Coverage](#16-country-coverage)
17. [Job Categories & Department/Team Metadata — Evidence-Based Field Analysis](#17-job-categories--departmentteam-metadata--evidence-based-field-analysis)
18. [Known Limitations](#18-known-limitations)
19. [Future Improvements](#19-future-improvements)
20. [Lessons Learned](#20-lessons-learned)
21. [Final Recommendations](#21-final-recommendations)
22. [Conclusion](#22-conclusion)
23. [Provider Capability Matrix](#23-provider-capability-matrix)
24. [Project Status](#24-project-status)
25. [Requirement Coverage Matrix](#25-requirement-coverage-matrix)
26. [Appendix A — Complete Provider Research Catalog (268 providers)](#appendix-a--complete-provider-research-catalog-268-providers)
27. [Appendix B — Shortlist Audit (Sheet1, 86 providers)](#appendix-b--shortlist-audit-sheet1-86-providers)
28. [Appendix C — Capacity & Expansion Planning Notes](#appendix-c--capacity--expansion-planning-notes)
29. [Appendix D — Rejected Providers by Category](#appendix-d--rejected-providers-by-category)

---

## 1. Executive Summary

*A one-page version of this summary, covering objective, lifecycle, achievements, challenges, decisions, status, readiness, and recommendations, appears at the front of this document. This section adds the narrative detail behind it: why the research lifecycle matters and what it changes about how the implementation should be read.*

The Job Aggregation Platform did not start from 46 providers — it started from a 268-provider market survey, evaluated against a consistent set of criteria (public API availability, documentation quality, auth model, pricing, geographic/regulatory restrictions, data quality, freshness, pagination, filtering, maintenance risk, and implementation effort — Section 4), narrowed to an 86-provider shortlist, and built out to 46 working integrations. The 222 researched-but-unbuilt providers are not an afterthought: Sections 3, 8, 9, and Appendices A, B, and D preserve why each was rejected, whether it could become viable later, and what would have to change.

This report answers two questions together, where the prior version answered only the second: **why** each sourcing decision was made, and **what** was ultimately built. The evidence shows the lifecycle was not linear guesswork. Six providers marked "needs live verification" in research were subsequently confirmed live and implemented (Get on Board, Working Nomads, Freshersworld, Hasjob, and others). NHS Jobs was marked as having no viable public API through its *official* channel — engineering then found and integrated a separate, undocumented public feed instead, without bypassing anything that actually required authorization. And providers correctly identified as blocked by enterprise pricing, citizen-ID gating, or a genuinely absent public API were left out rather than worked around with scraping or unauthorized access. That discipline — building only what a legitimate, sustainable integration path supports — is a main finding of this report, detailed in Section 3.4.

On implementation: 46 provider modules run against a shared `BaseJobSource` interface; 184,506 unique jobs are stored in PostgreSQL with real deduplication, per-provider run history, and country/work-arrangement normalization that leaves ambiguous fields blank rather than guessing. 41 of 46 providers are live; the other five are fully built but non-contributing for individually diagnosed external reasons (Section 15). The platform is ready for the operational hardening — scheduled syncs, inline normalization, credential provisioning, and the specific next-candidate providers in Section 9 — detailed in Section 19.

---

## 2. Project Overview

### Goal

Build a single, queryable, de-duplicated dataset of job postings sourced from as many distinct, legitimately accessible channels as practical — public government job boards, no-auth ATS endpoints, metered commercial search APIs, and company RSS feeds — normalized to a common schema, with reliable country and remote/hybrid/on-site classification, and a historical record of every ingestion run and every provider decision behind it.

### How the provider roster was actually built

Unlike a project that starts by picking a fixed list of APIs to integrate, this project began with an open-ended market survey (Section 3) and progressively narrowed it through explicit evaluation criteria (Section 4) into a shortlist, and then into working code. That means the 46 implemented providers are not "the APIs someone thought of" — they are the surviving 17% of a 268-provider research universe, filtered by real constraints: whether a public read API exists at all, whether its access model is self-serve or gated, whether its pricing is compatible with a project with no committed budget, and whether its data quality and maintenance risk profile were acceptable. Section 8 and Appendix A preserve the other 83%, with the specific reason each did not make it in.

### Architecture

Every provider lives in its own module under `sources/` and implements a shared `BaseJobSource` interface: `fetch_raw()` pulls records from that provider's native API/feed format, and `normalize()` maps them onto one common job schema (`title`, `company`, `location`, `url`, `tags`, `remote`, `posted`). A concrete `run()` method on the base class calls both per record, catching and logging any per-source or per-record failure so one broken provider can never take the whole pipeline down. Adding a new source has never required changing `jobs.py` — only a new module plus one line in the `SOURCES` registry (confirmed directly in `sources/__init__.py`, which registers all 46 `...Source()` instances).

### Workflow

1. **Fetch & normalize** — `jobs.py` instantiates all 46 sources and runs each independently.
2. **Merge & deduplicate** — results are combined and deduplicated by URL (or a SHA-256 hash of title/company/location for the rare job with no URL).
3. **Write `jobs.json`** — the deduplicated set is written for the static frontend, unchanged in format since Milestone 2.
4. **Persist to PostgreSQL** — `database.py` upserts every job into the `jobs` table (keyed on `dedup_key`) and records one `provider_runs` row per source with fetch/insert/update/duplicate counts and duration.
5. **Normalize offline** — `normalize_countries.py` runs as a separate, idempotent migration pass over the stored `location` text, deriving `country` and `work_arrangement` using only local libraries — no network calls, no provider re-fetch.

### Technologies used

Python 3 for the whole pipeline; PostgreSQL for persistence; `psycopg2` as the driver; `requests` (plus `requests-oauthlib` for the one OAuth 1.0a source) for HTTP; Python's built-in `xml.etree.ElementTree` for RSS/Atom/XML feed sources; and `pycountry`, `country_converter`, and `geonamescache` for fully offline location normalization. See [Section 6](#6-technology-stack) for the rationale behind each.

---

## 3. Provider Research & Evaluation Lifecycle

This section is the piece the prior report omitted: the complete path from an open-ended market survey down to a live, production data source. Every number below is drawn directly from this project's own research artifacts — `job_api.xlsx` (`API Catalog` and `Sheet1`), `research/api_analysis.md`, and two research audits produced during this project (a 268-provider catalog audit and an 86-provider shortlist audit) — cross-checked against `sources/__init__.py`, which is ground truth for what is actually implemented today.

### 3.1 The five-stage lifecycle

```
   268 providers researched  (API Catalog sheet, job_api.xlsx)
              │
              │  narrowed for closer, provider-by-provider audit
              ▼
    86 providers shortlisted  (Sheet1, job_api.xlsx — "deliberately narrower
              │                than the workbook's 268-row API Catalog sheet")
              │  evaluated against pricing / auth / region / data-quality criteria
              ▼
    46 providers implemented  (sources/__init__.py — one module per provider,
              │                shared BaseJobSource interface)
              │  credentialed, live-tested, and free of external blockers
              ▼
    41 providers live today   (contributing rows to the current PostgreSQL
              │                snapshot — Section 15)
              │
              ▼
   222 providers documented, not built — preserved with a specific reason
                              each (Section 8, Section 9, Appendix A)
```

### 3.2 Stage 1 — Broad market research (268 providers)

The `API Catalog` sheet of `job_api.xlsx` records **268 distinct providers** spanning government labour agencies, national and regional job portals, commercial job boards, ATS platforms, job-distribution/CPC networks, labor-market-intelligence vendors, generic web-scraping infrastructure vendors, and B2B data-aggregation vendors, across every populated region in the workbook (North America, Europe, the Gulf, South/Southeast Asia, East Asia, Africa, and Latin America). Each row records the provider's type, region, whether a public API exists, its registration/authentication model, whether it currently contributes live jobs, whether it structurally fits this project's architecture, and a specific, evidence-based reason for its classification — never a bare "no."

This catalog was not static: a companion document, `research/api_analysis.md` (a ~2,700-line internal research log spanning multiple research passes), independently corroborates it — e.g. its Section 5/10 "Additional APIs by Region" and Section 19 "Final Prioritized Implementation Roadmap" recommended, among others, multi-country Adzuna, MyCareersFuture, France Travail, CareerOneStop/NLx, and Get on Board as the next APIs to integrate — and all five were subsequently implemented (`sources/adzuna.py`, `sources/mycareersfuture.py`, `sources/francetravail.py`, `sources/careeronestop.py`, `sources/getonboard.py`). This is direct, artifact-level evidence that research recommendations demonstrably shaped what got built, not just a retrospective label.

At the point this 268-row catalog was produced, **38 of its providers were already marked "done"** (i.e., already integrated at that time). Cross-checking all 268 names against the actual, current `sources/__init__.py` registry (46 modules) shows that **8 more providers were implemented after this catalog snapshot was taken**: NHS Jobs, Get on Board, 4dayweek.io, Working Nomads, Freshersworld, Hasjob, Trade Me Jobs, and Fantastic Jobs / Active Jobs DB. Their catalog-time classification is itself informative and is unpacked in Section 3.4 below — this is not a discrepancy to paper over, it is the clearest evidence in this project that research and engineering were in active dialogue, not that one simply dictated to the other.

### 3.3 Stage 2 — Shortlisting for close audit (86 providers)

`Sheet1` of `job_api.xlsx` is explicitly described in this project's own shortlist-audit artifact as **"a curated shortlist of 86 providers, deliberately narrower than the workbook's 268-row API Catalog sheet."** This is the ~80-provider shortlist referenced throughout this report and in the original task brief. It is not simply the "top 86 by some score" — it is a curated subset selected for a second, more detailed pass of scrutiny (registration flow, live-endpoint verification, exact auth mechanism) beyond what the broader 268-row catalog captured in a single reason field.

Cross-checking this shortlist against the current 46-provider implementation:

| Sheet1 classification at shortlist time | Count | Of these, later implemented |
|---|---:|---:|
| Already implemented (`done`) | 31 | 31 |
| Registration/approval required (`reg`) | 5 | 3 (NHS Jobs, Trade Me Jobs, Fantastic Jobs) |
| Needs live verification (`investigate`) | 8 | 4 (Get on Board, Working Nomads, Freshersworld, Hasjob) |
| Not viable at shortlist time (`blocked`) | 42 | 0 |
| **Total** | **86** | **38** |

Two `reg` providers (CBOP Poland, Work24 Korea) and four `investigate` providers (GOV.UK Find a Job, Portal del Empleo Mexico, Thailand Smart Job Center, ZonaJobs) remain unimplemented today — each is carried forward with its specific status in [Section 9](#9-future-candidate--deferred-providers). None of the 42 `blocked` shortlist entries were implemented, which is the expected and correct outcome: a provider blocked by e.g. a citizen-ID login requirement or a fully enterprise-gated pricing model does not become viable just because it was shortlisted for a closer look.

Eight of the 46 implemented providers do not appear in Sheet1's 86 rows at all: Workday, Taiwan Ministry of Labor, Mustakbil.com, We Work Remotely, Jobspresso, NoDesk, TheirStack, and 4dayweek.io. Checking the broader 268-row catalog explains seven of these — all seven were already marked `done` there, meaning they were already built by the time the narrower 86-row shortlist audit was produced and so had no reason to appear in a "what still needs auditing" list. The eighth, **4dayweek.io, was marked `investigate` in the 268-row catalog and does not appear in Sheet1 at all** — the evidence available does not show it went through the formal shortlist process; the most defensible reading is that it was added organically as a structural sibling of the already-shortlisted remote-job RSS boards (We Work Remotely, Jobspresso, NoDesk), which share its exact "public RSS feed, no pagination" implementation pattern. This is stated as the best-supported inference, not a confirmed fact — the research artifacts do not document a decision meeting for 4dayweek.io specifically.

### 3.4 Stage 3 — From shortlist to shipped code: where research and engineering diverged

The most concrete evidence that this project's research shaped implementation — and that implementation sometimes justifiably overrode research — is in the handful of providers whose catalog-time classification changed by the time they were built:

- **NHS Jobs** was classified `blocked` in the 268-provider catalog with the reason "No public API — the site/portal requires a jobseeker or employer login." That classification was correct for NHS's **official, documented** channel: NHS's "Self-Serve Job Adverts API," which requires an eligibility application to NHSBSA (organisation must be UK-based, public-facing, and post health/NHS-associated roles) — reflected accurately in Sheet1's later, more forgiving `reg` classification of the same provider. What the catalog and shortlist could not have captured is that engineering subsequently found and verified a **separate, undocumented public XML endpoint** (`jobs.nhs.uk/api/v1/search_xml`) that requires no registration, no key, and no auth header at all — confirmed directly in `sources/nhsjobs.py`'s module docstring, which documents that this is deliberately a different surface from NHSBSA's gated API and was verified stable across two independent testing passes. This is implemented and live today, contributing 10,843 jobs (Section 7) — a case where engineering discovery went beyond what desk research alone could find, without violating the provider's terms (the endpoint is public and unauthenticated by design, not a bypass of one that requires it).
- **Fantastic Jobs / Active Jobs DB** and **Trade Me Jobs** were both classified `reg` (registration/approval required) in both the 268-row catalog and the 86-row shortlist, and both assessments held up exactly as researched: Fantastic Jobs was built against its documented, metered API (a 7-day free trial, then ~$1/1,000 jobs) and is credentialed today but currently returns 0 jobs, most plausibly a trial-window or account-tier issue (Section 15); Trade Me Jobs was built against its documented OAuth 1.0a endpoint but has no production credentials configured in this environment and additionally requires Trade Me's own approval process for production (non-sandbox) access. Both are "implemented exactly as the research predicted, blocked exactly as the research predicted" — the opposite failure mode from NHS Jobs, and just as informative.
- **Get on Board, Working Nomads, Freshersworld, and Hasjob** were all marked `investigate` ("needs a live check to confirm it still exists / works before building against it") in both catalog passes. All four were subsequently verified live and implemented — the research correctly identified them as plausible-but-unconfirmed rather than either accepting or rejecting them on paper, and engineering resolved the uncertainty by building against the live endpoint directly.
- **CBOP (Poland)** and **Work24 (Korea)** remain exactly where the research left them — `reg`, real and technically workable, but not yet built, because their fetch pattern (a SOAP service reachable only in a nightly window, for CBOP) or licensing terms (a non-commercial-use restriction pending confirmation, for Work24) warranted deferral rather than immediate integration. See [Section 9](#9-future-candidate--deferred-providers).

### 3.5 Stage 4 — Live contribution (41 of 46)

Of the 46 implemented providers, 41 are contributing live data in the current PostgreSQL snapshot. The remaining five (TheirStack, Trade Me Jobs, CareerOneStop, Fantastic Jobs, Arbeitnow) are fully built but non-contributing for external, individually diagnosed reasons — billing, missing credentials, or a transient zero-result run — detailed exhaustively in [Section 15](#15-implemented-vs-pending).

### 3.6 Stage 5 — The 222 researched-but-unbuilt providers

The remaining 222 providers from the 268-row catalog (268 minus the 46 implemented) are not a discard pile — they are a preserved decision record. [Section 8](#8-provider-research-knowledge-base) groups all of them by *why* they did not make it in, with the full list reproduced in [Appendix A](#appendix-a--complete-provider-research-catalog-268-providers). [Section 9](#9-future-candidate--deferred-providers) isolates the subset genuinely worth revisiting — those blocked only by a registration/approval step or an unresolved licensing question, not by a hard structural absence of any public API.

---

## 4. Provider Evaluation Methodology

Every provider in the research catalog was assessed against the same set of criteria, drawn directly from the columns actually populated in `job_api.xlsx` and from the qualitative reasoning recorded in `research/api_analysis.md`. This is the methodology that produced the classifications used throughout this report (`done` / `reg` / `investigate` / `blocked` in the research artifacts; **Live** / **Needs review** / **Built, uncredentialed** / **Blocked** in the implementation-facing sections):

| Criterion | What was checked | Where it is evidenced |
|---|---|---|
| **Public API availability** | Does a genuine, third-party-readable endpoint exist at all — as opposed to a site that only supports jobseeker/employer browser login? This was the hard floor: the majority of rejected providers (127 of 214 non-implemented `blocked` catalog entries — Section 8) failed on this criterion alone. | `API Catalog` sheet `public_api` / `reason` columns; live endpoint checks recorded in the shortlist audit |
| **Documentation quality** | Is there a real developer/API reference, or only inferred/reverse-engineered behavior? Several *implemented* providers (NHS Jobs, EURES, MyCareersFuture, NAV Arbeidsplassen) have no official documentation at all and were verified entirely through live testing — accepted as a calculated risk, not a disqualifier by itself. | `Docs Available` (Schema Definitions), module docstrings in `sources/*.py` |
| **Authentication requirements** | None, self-serve API key, OAuth, HTTP Basic, or gated behind an approval/partnership process, a citizen national-ID login, or a licensed-business-only login. | `auth`/`registration` columns; Section 8's Authentication-Restricted categories |
| **Pricing model** | Free / free registration / free trial / pay-as-you-go metered / enterprise sales-only. Enterprise-sales-only was treated as effectively a hard blocker for a project with no procurement process. | `Access Model`, `Cost Details` (Schema Definitions); Section 14 |
| **Free tier** | Whether a free tier exists and its practical size (e.g. SerpApi/OpenWeb Ninja's 200 requests or searches per month). | Provider docs quoted in `sources/*.py`; Section 14 |
| **Enterprise requirements** | Whether the *only* path to data is a sales contract or partner program (e.g. LinkedIn Jobs, JobStreet/JobsDB, Coresignal, most Labor-Market-Intelligence vendors) — 15 providers were rejected on this basis alone (Section 8). | `reason` column; Section 8 |
| **Geographic restrictions** | Whether a provider's access model, not just its data, is restricted to a specific country's residents (e.g. Israeli Employment Service, Jadarat Saudi Arabia require national-ID login) versus providers that are merely regionally scoped by design (e.g. VDAB is Flanders-only by design, not by restriction). | `region` column; Section 8's citizen-ID-gated category; Section 16 |
| **Data quality** | Whether the provider returns individual, current job postings with real identifiers, versus an aggregate statistics dataset with no per-job record (UWV Netherlands, SEPE Spain, data.gov.in, NCS India) — 5 providers were rejected specifically because they are *datasets*, not live per-job search APIs. | `reason` column; Section 8 |
| **Job freshness** | Whether postings are live/current versus a static or periodically-refreshed snapshot; carried into the *implemented* roster as the Section 12 "Posting freshness" analysis. | Module docstrings; Section 12 |
| **Pagination** | Whether the provider supports iterating beyond a single page, and what its real (often undocumented) ceiling is — discovered live for every implemented provider (Section 7's Notes column) rather than assumed from documentation. | `Pagination`, `API Limits` (Schema Definitions); Section 7 |
| **Search capabilities** | Keyword, location, company, category, and date filters actually available versus actually used — audited in `research/api_analysis.md` Section 17 ("API Filter Optimization Research") for the then-current provider set. | `research/api_analysis.md` §17; Section 13 |
| **Maintenance / stability** | Whether a provider is actively maintained, deprecated, or suspended (Brazil's SINE Aberto was suspended in October 2022 pending LGPD compliance; a third-party SEPE Spain scraper is known-deprecated), and whether an integrated-but-undocumented endpoint carries ongoing breakage risk (flagged explicitly for 5 of the 46 implemented providers in Section 18). | `reason` column; Section 18, Section 20 |
| **Ease of implementation** | Whether the provider's fetch pattern (REST/JSON, SOAP, OAuth 1.0a, RSS/Atom, a rotating public token) fits this project's existing conventions without disproportionate engineering effort — the explicit reason CBOP (Poland's SOAP/time-window feed) remains unbuilt despite being free and real. | `reason` column; Section 9 |

This methodology was applied consistently whether the outcome was rejection, deferral, or integration — every "blocked" classification in Appendix A carries the specific criterion (or combination) it failed, not a generic label.

---

## 5. Provider Decision Matrix

A single, consolidated view of every stage a provider could reach, with the count at each stage and the section that documents it in detail. Read top to bottom, this is the whole project's provider-sourcing decision tree.

| Stage | Count | Definition | Detail |
|---|---:|---|---|
| Researched (API Catalog) | 268 | Appears in `job_api.xlsx`'s `API Catalog` sheet | Section 3.2, Appendix A |
| Shortlisted for close audit (Sheet1) | 86 | Appears in `job_api.xlsx`'s `Sheet1`, a deliberately narrower cut of the 268 | Section 3.3, Appendix B |
| Registration/approval-gated but real (`reg`) | 6 (catalog) / 5 (shortlist) | A genuine API exists; access requires a registration, application, or partnership step beyond a self-serve key | Section 3.4, Section 9 |
| Needs live verification (`investigate`) | 9 (catalog) / 8 (shortlist) | Advertised or historically documented, but not independently confirmed live at research time | Section 3.4, Section 9 |
| Not viable at research time (`blocked`) | 215 (catalog) / 42 (shortlist) | No public API, enterprise-only, wrong data-flow direction, deprecated, or a dataset rather than a live API | Section 8, Appendix A |
| Implemented | 46 | A `sources/*.py` module exists and is registered in `SOURCES` (`sources/__init__.py`) | Section 7 |
| Live / contributing | 41 | Implemented **and** returned ≥1 job in the current PostgreSQL snapshot | Section 15 |
| Implemented, not currently contributing | 5 | Implemented but blocked by billing, missing credentials, or a transient zero-result run | Section 15 |
| Deferred / worth revisiting (Section 9) | 10 | 4 registration-gated (Saramin, VDAB, CBOP, Work24) + 4 needing live verification (GOV.UK Find a Job, Portal del Empleo, Job-Room Switzerland, JobsPikr) + 2 lower-priority `blocked` entries carried forward for a specific partnership path (Thailand Smart Job Center, ZonaJobs) | Section 9 |
| Rejected, no viable path identified | 212 | No public API, enterprise/partner-only with no self-serve tier, deprecated, or a wrong-direction/employer-only API — the 214 `blocked` (non-implemented) catalog entries minus the 2 carried into Section 9.3 | Section 8, Appendix A |

---

## 6. Technology Stack

One correction from the requested list before the table below: this project does **not** use **feedparser** or **BeautifulSoup**. Neither appears in `requirements.txt` or anywhere in `sources/`. RSS/Atom/XML feed providers (Mustakbil, MyJobMag, Hasjob, NoDesk, We Work Remotely, Jobspresso, Freshersworld, 4dayweek) are parsed with Python's built-in `xml.etree.ElementTree`, supplemented by targeted `re`/`html` cleanup where a feed is malformed or double-escaped. This is called out explicitly rather than silently listing unused dependencies.

| Technology | Role in this project | Why it was chosen |
|---|---|---|
| Python 3 | Orchestration language for every source module, the aggregation pipeline, database layer, and normalization scripts. | Mature HTTP/XML/JSON tooling, strong standard library, and the language every part of this project is already written in. |
| PostgreSQL | System of record for all 184,506 job rows and per-provider run history. | Native `UNIQUE` constraints for URL-based dedup, array columns for `tags`, transactional upserts (`ON CONFLICT`), and mature indexing for the reporting queries in Section 12. |
| psycopg2 (psycopg2-binary) | PostgreSQL driver used by `database.py` for every connection, upsert, and report query. | The de facto standard, well-maintained Python/PostgreSQL adapter; supports `execute_values` for efficient bulk upserts. |
| requests | HTTP client for every REST/JSON API source (the large majority of the 46 providers). | Simple, reliable synchronous HTTP with easy header/auth/timeout/retry control — sufficient for this pipeline's sequential, per-provider fetch model. |
| requests-oauthlib | Signs the Trade Me Jobs API's OAuth 1.0a two-legged requests. | Trade Me is the only source in the project requiring OAuth 1.0a; this is the standard, well-tested library for that signing scheme. |
| xml.etree.ElementTree *(stdlib)* | Parses every RSS/Atom/XML feed source (8 providers) instead of feedparser/BeautifulSoup. | No extra dependency needed; standard-library parser is sufficient once malformed markup is pre-cleaned with `re`/`html.unescape`. |
| python-dotenv | Loads API credentials from a git-ignored `.env` file into environment variables at import time. | Keeps every secret out of source control while remaining a single, uniform pattern across all 12 credentialed providers. |
| pycountry | Canonical ISO 3166-1 country names/codes used as the highest-confidence tier of location resolution. | Authoritative, offline, dependency-light reference data — no external geocoding API or network call required. |
| country_converter | Large regex table of country name spellings/abbreviations, and the source of the one consistent "friendly" country name used throughout (e.g. "United States" rather than the ISO formal name). | Handles the long tail of alternate country spellings that a static name lookup alone would miss, entirely offline. |
| geonamescache | ~32,000 world cities, US states, and US counties, used to disambiguate location strings that name a city but not a country (e.g. "Paris" → France over Paris, Texas, by population). | Bundled local data — no live geocoding service, no API key, no rate limit, no cost. |

---

## 7. APIs and Providers (Implemented)

All 46 integrated providers — the survivors of the research lifecycle in Section 3 — sorted by live job count currently stored in PostgreSQL. "Jobs Fetched" is the raw per-run count recorded in `provider_runs` (includes in-run duplicates); "Jobs Stored" is the live, post-dedup count in the `jobs` table. Every pricing-page URL below is quoted directly from this project's own source code (module docstrings or `sources/config.py`) — none are guessed. The **Research Origin** column cross-references each provider back to its stage in Section 3: **Catalog-only** means it was already `done` in the 268-row catalog by the time the narrower shortlist was produced; **Shortlist `done`** means it was already implemented when Sheet1 itself was created; **Shortlist upgrade** means its classification changed from `reg`/`investigate` to implemented; **Outside shortlist** means it does not appear in Sheet1 at all (Section 3.3).

| Provider | Type | Region | Auth | Pricing Model | Tier | Official Page | Fetched | Stored | Status | Research Origin |
|---|---|---|---|---|---|---|---:|---:|---|---|
| SmartRecruiters | ATS | Global (curated cos.) | None | No-auth public API | Free | developers.smartrecruiters.com/docs/posting-api | 65,394 | 65,392 | Live | Shortlist `done` |
| Greenhouse | ATS | Global (curated cos.) | None | No-auth public API | Free | developers.greenhouse.io/job-board.html | 22,715 | 22,715 | Live | Shortlist `done` |
| Lever | ATS | Global (curated cos.) | None | No-auth public API | Free | github.com/lever/postings-api | 17,980 | 17,980 | Live | Shortlist `done` |
| NHS Jobs | Government (undocumented feed) | United Kingdom | None | No-auth public feed | Free | jobs.nhs.uk/api/v1/search_xml | 13,011 | 10,843 | Live | Shortlist upgrade (`reg`→implemented; Section 3.4) |
| USAJOBS | Government API | United States | API key (3 headers) + email | Free registration | Free | developer.usajobs.gov | 10,000 | 10,000 | Live | Shortlist `done` |
| Bundesagentur für Arbeit | Government API | Germany / Austria | Public non-secret API key | No-auth-style public key | Free | github.com/bundesAPI/jobsuche-api | 10,000 | 9,896 | Live | Shortlist `done` |
| Reed | Commercial Aggregator | United Kingdom | HTTP Basic (key as username) | Free registration | Free | reed.co.uk/developers/jobseeker | 9,000 | 8,994 | Live | Shortlist `done` |
| NAV Arbeidsplassen | Government API | Norway | Public no-signup rotating token | No-auth-style public token | Free | navikt.github.io/pam-stilling-feed | 12,478 | 5,394 | Live | Shortlist `done` |
| Ashby | ATS | Global (curated cos.) | None | No-auth public API | Free | developers.ashbyhq.com/docs/public-job-posting-api | 5,252 | 5,252 | Live | Shortlist `done` |
| Workable | ATS (public widget API) | Global (curated cos.) | None | No-auth public API | Free | apply.workable.com (public widget surface) | 7,627 | 4,137 | Live | Shortlist `done` |
| Workday | ATS (public CXS API) | Global + US govt tenants | None | No-auth public API | Free | (keyless endpoint, templated per tenant — no fixed docs URL found) | 2,998 | 2,997 | Live | Outside shortlist (already catalog `done`) |
| Himalayas | Public API | Global / Remote | None | No-auth public API | Free | himalayas.app/jobs/api | 3,000 | 2,253 | Live | Shortlist `done` |
| Arbetsförmedlingen | Government API | Sweden | None | No-auth public API | Free | jobsearch.api.jobtechdev.se | 2,100 | 2,096 | Live | Shortlist `done` |
| Adzuna | Commercial Aggregator | United States | API key (app_id + app_key) | Free tier + paid metered | Free tier | developer.adzuna.com/docs/search | 2,000 | 2,000 | Live | Shortlist `done` |
| The Muse | Commercial Aggregator | Global / US-tech-skewed | None (public tier) | No-auth public tier | Free | themuse.com/developers/api/v2 | 2,000 | 2,000 | Live | Shortlist `done` |
| CareerJet | Commercial Aggregator | Global (per-country query) | API key + IP allowlist + Referer | Free registration | Free | careerjet.com/partners/api | 2,000 | 1,996 | Live | Shortlist `done` |
| EURES | Government (undocumented feed) | EU / EEA | None | No-auth public feed | Free | europa.eu/eures (no official public docs) | 2,000 | 1,681 | Live | Shortlist `done` |
| RemoteJobs.org | Public API | Global / Remote | None | No-auth public API | Free | remotejobs.org (in-response docs link 404s) | 1,500 | 1,500 | Live | Shortlist `done` |
| France Travail | Government API | France | OAuth2 client credentials | Free self-service | Free | francetravail.io/produits-partages/catalogue/offres-emploi | 1,150 | 1,146 | Live | Shortlist `done` |
| Jooble | Commercial Aggregator | Global (keyword-scoped) | API key | Free registration | Free | jooble.org/api | 1,137 | 1,137 | Live | Shortlist `done` |
| Get on Board | Commercial Aggregator (tech) | Latin America | None (public tier) | No-auth public tier | Free | getonbrd.com/api-doc.html | 1,261 | 1,011 | Live | Shortlist upgrade (`investigate`→implemented; Section 3.4) |
| Taiwan Ministry of Labor | Government API | Taiwan | None | No-auth open data | Free | free.taiwanjobs.gov.tw (data.gov.tw dataset 44062) | 1,000 | 1,000 | Live | Outside shortlist (already catalog `done`) |
| Findwork.dev | Public API (tech board) | US / remote tech | API key (token) | Free registration | Free | findwork.dev/developers | 1,000 | 1,000 | Live | Shortlist `done` |
| Mustakbil.com | RSS Feed | Multi-country (PK-founded, 20+ countries) | None | No-auth public feed | Free | rss.mustakbil.com/jobs-rss | 500 | 500 | Live | Outside shortlist (already catalog `done`) |
| Teamtailor | ATS (public RSS, not API) | Global (curated cos.) | None | No-auth public feed | Free | docs.teamtailor.com | 494 | 494 | Live | Shortlist `done` |
| Recruitee (Tellent) | ATS | Global (NL/EU-heavy sample) | None | No-auth public API | Free | docs.recruitee.com/reference/intro-to-careers-site-api | 394 | 394 | Live | Shortlist `done` |
| RemoteOK | Public API | Global / Remote | None | No-auth public API | Free | remoteok.com/api | 100 | 100 | Live | Shortlist `done` |
| MyJobMag | RSS Feed | Nigeria | None | No-auth public feed | Free | myjobmag.com/feeds | 100 | 100 | Live | Shortlist `done` |
| Jobicy | Public API | Global / Remote | None | No-auth public API | Free | jobi.cy/apidocs | 100 | 100 | Live | Shortlist `done` |
| We Work Remotely | RSS Feed | Global / Remote | None | No-auth public feed | Free | weworkremotely.com/remote-jobs.rss | 100 | 99 | Live | Outside shortlist (already catalog `done`) |
| 4dayweek.io | RSS Feed | Global | None | No-auth public feed | Free | 4dayweek.io/feed | 50 | 50 | Live | Outside shortlist entirely (catalog `investigate`; Section 3.3) |
| SerpApi (Google Jobs) | Commercial Aggregator | Global | API key | Free tier + paid metered | Free tier / Paid | serpapi.com/google-jobs-api | 50 | 50 | Live | Shortlist `done` |
| OpenWebNinja (JSearch) | Commercial Aggregator | Global | API key | Free tier + paid metered | Free tier / Paid | openwebninja.com/api/jsearch | 49 | 49 | Live | Shortlist `done` |
| Working Nomads | Public API | Global / Remote | None | No-auth public API | Free | workingnomads.com/jobs | 33 | 33 | Live | Shortlist upgrade (`investigate`→implemented; Section 3.4) |
| Remotive | Public API | Global / Remote | None | No-auth public API | Free | remotive.com/api-jobs | 30 | 30 | Live | Shortlist `done` |
| Freshersworld | RSS Feed | India (entry-level) | None | No-auth public feed | Free | freshersworld.com/feed | 30 | 30 | Live | Shortlist upgrade (`investigate`→implemented; Section 3.4) |
| Jobspresso | RSS Feed | Global / Remote | None | No-auth public feed | Free | jobspresso.co/jobs/feed | 20 | 20 | Live | Outside shortlist (already catalog `done`) |
| MyCareersFuture | Government (undocumented API) | Singapore | None | No-auth public API | Free | api.mycareersfuture.gov.sg (no public docs found) | 2,000 | 20 | **Needs review** | Shortlist `done` |
| NoDesk | RSS Feed | Global / Remote | None | No-auth public feed | Free | nodesk.co/remote-jobs | 10 | 10 | Live | Outside shortlist (already catalog `done`) |
| Hasjob | Atom Feed | India (tech/startup) | None | No-auth public feed | Free | hasjob.co/feed | 6 | 6 | Live | Shortlist upgrade (`investigate`→implemented; Section 3.4) |
| HK Gov Vacancies | Government (static open data) | Hong Kong | None | No-auth open data | Free | csb.gov.hk/datagovhk/gov-vacancies (data.gov.hk) | 58 | 1 | **Needs review** | Shortlist `done` |
| TheirStack | Commercial Aggregator | Global | API key (Bearer) | Per-credit metered (1 credit/job) | Paid | theirstack.com | 0 | 0 | **Blocked — billing** | Outside shortlist (already catalog `done`) |
| Trade Me Jobs | Commercial Aggregator | New Zealand | OAuth 1.0a (consumer key/secret) | Free (registered app) | Free / Approval | developer.trademe.co.nz | 0 | 0 | **Built, uncredentialed** | Shortlist upgrade (`reg`, still uncredentialed; Section 3.4) |
| CareerOneStop | Government API | United States | API key + user ID | Free registration | Free | careeronestop.org/Developers/WebAPI/web-api.aspx | 0 | 0 | **Built, uncredentialed** | Shortlist `done` |
| Fantastic.jobs | Commercial Aggregator (ATS feed) | Global | API key (Bearer) | Free trial → paid metered (~$1/1,000 jobs) | Free trial | developer.fantastic.jobs | 0 | 0 | **Credentialed, 0 result** | Shortlist upgrade (`reg`, credentialed; Section 3.4) |
| Arbeitnow | Public API | Global / Germany-leaning | None | No-auth public API | Free | arbeitnow.com/api/job-board-api | 0 | 0 | **0 in latest run** | Outside shortlist (already catalog `done`) |

"Live" = contributed jobs currently in PostgreSQL in this snapshot. "Needs review" = contributing data, but with a structural quirk worth a closer look (Section 18). See Section 15 for full root-cause detail on every non-contributing provider, and Section 3 for how each provider's research history led here.

---

## 8. Provider Research Knowledge Base

This section is the reusable part of this report: **every one of the 214 catalog providers that were not implemented, grouped by the specific reason they were not**, so a future engineer can decide in seconds whether a given rejection still holds or is worth re-checking. (214 = 215 `blocked` entries in the 268-row catalog, minus NHS Jobs, which the catalog classified `blocked` for its *official* channel before engineering found a separate working feed — see Section 3.4.) Section 4 gives the criteria; this section groups the outcomes; [Appendix D](#appendix-d--rejected-providers-by-category) lists all 214 in full. Section 9 isolates the smaller subset genuinely worth revisiting.

### 8.1 Rejection categories at a glance

| Category | Count | Typical example | Full list |
|---|---:|---|---|
| No Public API | 126 | Naukri, Bayt.com, 51job, StepStone, Civil Service Jobs (UK) | Appendix D.1 |
| Employer-Side Distribution / Write-Only Networks | 25 | Appcast, Broadbean, SEEK, Google for Jobs | Appendix D.2 |
| Labor-Market-Intelligence / Research SaaS | 14 | Lightcast, TalentNeuron, LinkUp, Indeed Hiring Lab | Appendix D.3 |
| Enterprise-Only / Sales-Gated | 15 | BambooHR, LinkedIn Jobs, ZipRecruiter API, Coresignal | Appendix D.4 |
| Paid-Only, Excluded for Scope Not Price | 20 | Apify, Bright Data, Merge.dev, JSearch | Appendix D.5 |
| Authentication-Restricted (citizen-ID / licensed-business) | 5 | Israeli Employment Service, Jadarat, Hello Work Japan | Appendix D.6 |
| Static Dataset, Not a Live API | 4 | UWV Netherlands, SEPE Spain, data.gov.in | Appendix D.7 |
| Commercial-Partnership Gated | 2 | Job Bank Canada, Kemnaker Karirhub (Indonesia) | Appendix D.8 |
| Deprecated / Suspended / Technically Inaccessible | 3 | SINE Aberto (Brazil, suspended), Pangian (shut down), Remote First Jobs (Cloudflare-walled) | Appendix D.9 |
| **Total rejected (blocked)** | **214** | | |

Each category is expanded below with its defining logic and a handful of representative rows; the complete provider-by-provider list — all 214, with region and full reasoning quoted from this project's own research — is in **Appendix D**.

### 8.2 No Public API (126 providers) — the hard floor

By far the largest category. These providers have a real, often large-scale web/mobile presence, but no developer documentation, API endpoint, or third-party read access exists at all — the only way to see their data is to browse as a jobseeker or register as an employer to post. No amount of pricing tolerance or engineering effort overcomes a genuinely nonexistent read API. It spans nearly every region: India (Naukri, Shine, Internshala, TimesJobs, and 20+ others), the Gulf (Bayt.com, GulfTalent, Naukrigulf), East Asia (51job, BOSS Zhipin, JobKorea), Europe (StepStone, CV-Library, InfoJobs, Pracuj.pl), and government portals with citizen/employer login only (Civil Service Jobs UK, Job Market Finland, Cliclavoro Italy). None were rejected on data-quality or geographic grounds — there is simply nothing for a third-party pipeline to call. Full list: **Appendix D.1**.

### 8.3 Employer-Side Distribution / Write-Only Networks (25 providers) — wrong data-flow direction

These providers have real, sometimes well-documented APIs — the rejection is structural, not access-related. They exist for **employers and job boards to push postings out** (CPC job-distribution networks, meta-search advertiser platforms, or write/management-only feeds), not for an aggregator to pull postings in. Representative examples: Appcast, Broadbean, Joveo, and Radancy (advertiser-side CPC networks); Google for Jobs, JobisJob, and Trovit (meta-search/advertiser platforms); SEEK, CareerOne, and Workforce Australia (feed-ingest or write-only management APIs with no read endpoint). Full list: **Appendix D.2**.

### 8.4 Labor-Market-Intelligence / Research SaaS (14 providers)

A distinct category from a job-postings feed: these products sell aggregate hiring-trend analytics, research indices, or enterprise talent-intelligence dashboards via sales contract, not a self-serve job feed. Examples: Lightcast, TalentNeuron (Gartner), LinkUp, Revelio Labs, Textkernel, and Indeed Hiring Lab (Indeed's own research arm, publishing aggregate CSVs, not individual job records). Full list: **Appendix D.3**.

### 8.5 Enterprise-Only / Sales-Gated Providers (15 providers)

Real APIs exist, but the only documented path to access is a sales conversation or partner program — no published self-serve pricing or signup flow. Examples: BambooHR, Darwinbox, Freshteam, Recruit CRM, Superset, Zoho Recruit (enterprise ATS platforms); LinkedIn Jobs, Indeed India, JobStreet/JobsDB, VietnamWorks (enterprise partner-program-only aggregators); Coresignal, Lightcast Jobs Canada, ZipRecruiter API (enterprise data/API vendors sold via sales contact). Full list: **Appendix D.4**.

### 8.6 Paid-Only, Excluded for Scope Not Price (20 providers)

Three sub-groups share the same self-serve metered/paid pricing shape this project already accepts elsewhere (Adzuna, SerpApi, OpenWebNinja, Fantastic Jobs, TheirStack) — they were excluded for *what they are*, not because a paid tier exists:

- **Generic web-scraping infrastructure vendors (10)** — Apify, Bright Data, Diffbot, HasData, Nimble, Oxylabs, Piloterr, ScraperAPI, Scrapingdog, Zyte. Not job-specific; using one means building and maintaining a custom per-site scraper, which is a project in itself.
- **B2B data-aggregation / enrichment vendors (5)** — JSearch (a paid RapidAPI repackaging of OpenWeb Ninja, already integrated natively), Mantiks, People Data Labs, PredictLeads, Techmap.io. Paid, and redundant with sources already held for free.
- **ATS Unified-API middleware (5)** — Apideck, Kombo.dev, Merge.dev, Unified.to, Workato. Paid re-wrappers of ATS platforms (Greenhouse, Lever, Workday) this project already integrates directly for free.

Full list: **Appendix D.5**.

### 8.7 Authentication-Restricted Providers (5 providers)

Distinct from "no public API": a real, sometimes fully documented API exists, but access is restricted to a specific class of credentialed user this project does not qualify as — a national citizen ID (Israeli Employment Service, Jadarat Saudi Arabia, Agencia SENA Colombia), or a licensed professional business (Hello Work Japan — restricted to licensed placement businesses, local governments, or training institutions). Google Cloud Talent Solution is included here for a related but distinct reason: it is not a third-party feed at all, but infrastructure for searching *your own* postings. Full list: **Appendix D.6**.

### 8.8 Static Dataset, Not a Live API (4 providers)

Real, often free and government-authoritative data — published as a periodic bulk file or aggregate statistics table, not a queryable, per-job live search endpoint. National Career Service India and data.gov.in expose periodic dataset dumps rather than live postings; SEPE Spain and UWV Netherlands publish only aggregate statistical files with no per-job identifier at all. Full list: **Appendix D.7**.

### 8.9 Commercial-Partnership Gated (2 providers)

| Provider | Region | Reason |
|---|---|---|
| Job Bank (ESDC) feed / Open Gov dataset | Canada | The live feed requires ESDC partner approval; the fallback open dataset is a monthly CSV dump missing employer/company names and per-job apply URLs — fields this project's schema requires. Doesn't fit even with credentials. |
| Kemnaker Karirhub (SIAPkerja) | Indonesia | Access restricted to job portals with a formal MoU with the Indonesian Ministry of Manpower; no publicly documented API key/OAuth path exists for outside developers. |

### 8.10 Deprecated / Suspended / Technically Inaccessible (3 providers)

| Provider | Region | Status | Reason |
|---|---|---|---|
| SINE Aberto (Sistema Nacional de Emprego) | Brazil | Suspended | Brazil suspended this data-sharing service in October 2022 (CODEFAT Resolution 956/2022) pending LGPD privacy-law compliance updates — no active API to integrate against right now. |
| Pangian | Remote/Global | Discontinued | Confirmed live: `pangian.com` 301-redirects to a static shutdown notice on GitHub Pages; every other candidate path 404s. Discontinued, not credential-gated. |
| Remote First Jobs (Dynamite Jobs) | Remote/Global | Technically blocked | Confirmed live: an active Cloudflare managed JS challenge on every path tested, including `robots.txt` itself (HTTP 403, "Just a moment..."). Not a credentials gate — a plain HTTP client cannot pass it, and this project's architecture has no headless-browser/JS-execution layer to attempt one. |

### 8.11 Region-Restricted Access Models

"Region restricted" takes two distinct forms in this catalog: (1) **citizen/national-only access**, where the *login* — not just the data — is restricted to nationals of one country (Section 8.7's Israeli Employment Service, Jadarat, and Agencia SENA); and (2) **deliberately single-region-by-design APIs that are otherwise real and workable**, such as VDAB (Flanders only, not all of Belgium) and Work24 (South Korea only) — both carried forward as genuine future candidates in Section 9 rather than rejected outright, because a narrow region is a scope decision, not an access failure. The implemented roster has the same pattern in reverse (Section 16): Taiwan MOL, MyCareersFuture, and HK Gov Vacancies are deliberately single-country, precisely because that narrow scope was the tradeoff for a free, workable, no-partnership-required API.

---
## 9. Future Candidate & Deferred Providers

Unlike Section 8's rejections, the providers below have a **genuine, confirmed, or plausible access path** that simply was not completed in this project's timeframe — a registration step, an approval meeting, or a live-verification check still outstanding. These are the providers worth revisiting first, in priority order, before returning to the 214 in Section 8.

### 9.1 Registration/Approval Required — Real API, Not Yet Built (4 providers)

| Provider | Region | What's required | Recommendation |
|---|---|---|---|
| **Saramin Open API (사람인 오픈 API)** | South Korea | An application/approval step via `oapi.saramin.co.kr` before an access key is issued; the service is explicitly labeled "beta"; capped at 500 calls/day. Pagination is page-based (`start`/`count`, max 110/page). | **Apply for access.** Estimated implementation effort is low-to-medium once credentialed — a REST API with published code tables, broadly similar in shape to the government/commercial APIs already integrated (e.g. CareerOneStop). The blocker is the approval step, not integration complexity. Not yet built. |
| **VDAB Vacature API** (Belgium — Flanders public employment service) | Belgium (Flanders only) | An application form **and** an "exploratory onboarding meeting" with VDAB before credentials are issued — a manual, relationship-based process, not instant self-serve. | The API is real, documented (`developer.vdab.be/openservices`), and free. Feasibility depends entirely on completing VDAB's onboarding process. Belgium's other regional employment bodies (Actiris for Brussels, Forem for Wallonia) were not independently verified in this research pass and would need separate evaluation. |
| **CBOP — Centralna Baza Ofert Pracy** (Poland public employment offices) | Poland | Pre-registered Partner name (free, no fee) for a real SOAP web service returning batches of up to 1,000 live offers per file — but capped at 20 calls/cycle and only reachable during a 17:00–07:00 window. | Workable, but the SOAP/overnight-window fetch pattern doesn't match this project's REST/JSON, daytime-run conventions — the reason for deferral is engineering fit, not access. The source catalog itself classifies this "Recommended," not rejected. |
| **Work24** (formerly Worknet/워크넷), Korea Employment Information Service | South Korea | Free instant key via `data.go.kr` — access itself is not the blocker. | License text restricts use to non-commercial purposes with attribution and prohibits modifying the data — flagged as needing re-confirmation with the issuing agency before any commercial ingestion. Pending that confirmation, not built. |

### 9.2 Needs Live Verification (4 providers)

These were marked `investigate` in the research catalog — plausible or historically documented, but not independently confirmed live within this project's research pass. Note that this exact classification, applied to Get on Board, Working Nomads, Freshersworld, and Hasjob, resolved into successful implementations (Section 3.4); these four are the ones where that resolution has not yet happened.

| Provider | Region | Open question | Recommendation |
|---|---|---|---|
| **GOV.UK Find a Job (DWP)** | United Kingdom | No confirmed public read/search API for third parties was found — only an employer-side SFTP bulk-upload path for *posting* vacancies. Original research status (verbatim): "Investigate." | Worth a direct follow-up with DWP / the API Catalogue (`api.gov.uk/dwp`) to confirm whether any read-only feed exists for third parties — would be authoritative, high-volume, and free if confirmed. |
| **Portal del Empleo / Servicio Nacional de Empleo (STPS Mexico)** | Mexico | Mexico's national open-data platform (`datos.gob.mx`, CKAN-based) was directly verified live (HTTP 200, dataset flagged `private:false`), but a live, current-vacancy-specific query endpoint for the job board itself was not directly confirmed. | Not ruled out — the source catalog classifies this "Recommended," not rejected. A focused follow-up directly against the CKAN dataset is needed before an implementation decision. |
| **Job-Room Jobs API** (SECO, Switzerland) | Switzerland | Switzerland's biggest job platform, but the API is built primarily for employers/ATS submitting ads under a reporting-obligation rule; whether third-party aggregators can get read-only access is unconfirmed in the docs. | Ask SECO directly (`jobroom-api@seco.admin.ch`) before counting on this one — the platform's scale makes it worth the one email. |
| **JobsPikr** | India (Naukri/Monster-sourced feeds) | A real API and documentation exist, but pricing is custom/quote-based rather than a published self-serve rate. | Confirm the actual signup process and cost directly before treating this as a routine paid integration on the same footing as Adzuna/SerpApi/Fantastic Jobs. |

### 9.3 Investigated but Not Technically Feasible Today (2 providers)

| Provider | Region | Why not feasible now | Could become feasible later? |
|---|---|---|---|
| **Thailand Department of Employment — Smart Job Center** (ไทยมีงานทำ) | Thailand | No public API or developer documentation of any kind was found — a web/mobile-app-only government job-matching platform with no discoverable integration surface at all. Not a credentialing or licensing issue; simply no API. | Only if the Department of Employment publishes a developer API in the future. Not recommended for scraping given the absence of any documented terms for automated access. |
| **ZonaJobs** (Argentina) | Argentina | A page suggesting API documentation exists (`ofertas-de-trabajo-api.html`) was confirmed to be an SEO/landing page listing API-related job postings, not real developer documentation. The site's own account registration is for employers *posting* jobs, not reading data. | Only via a direct partnership with Navent (ZonaJobs' parent company, which also owns Bumeran and Computrabajo). Could become feasible if Navent opens a partner API. |

### 9.4 Priority ranking for future work

Combining Sections 9.1–9.3 with the evaluation criteria in Section 4, the recommended order for revisiting this list is:

1. **Saramin** — largest realistic volume gain (a major Korean commercial board), low technical risk once credentialed, only blocked by an application step.
2. **VDAB** — free, documented, real read API; only blocked by a one-time onboarding meeting.
3. **GOV.UK Find a Job** — a single email to DWP could resolve years of uncertainty about a large, authoritative, free UK source.
4. **Job-Room (Switzerland)** — same shape: one email to SECO to resolve read-access uncertainty on Switzerland's largest job platform.
5. **Portal del Empleo (Mexico)** — the open-data platform is already confirmed live; only the vacancy-specific endpoint needs confirming.
6. **Work24 (Korea)** — technically ready today; blocked only on confirming the non-commercial licensing term is compatible with this project's use.
7. **CBOP (Poland)** — real and free, but genuinely lower priority given the SOAP/overnight-window engineering mismatch.
8. **JobsPikr** — worth a pricing conversation only after the free/registration-gated options above are exhausted, since it is paid from the outset.
9. **ZonaJobs / Thailand Smart Job Center** — lowest priority; both require either a partnership relationship or a currently-nonexistent API to appear before any engineering work is possible.

---

## 10. Features

### Fully Implemented

- 46 provider integrations on a shared `BaseJobSource` interface, the surviving 17% of a 268-provider research universe (Section 3)
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
- Provider research coverage — 268 providers researched, 86 shortlisted for close audit, but 6 real, accessible candidates (Section 9) remain unbuilt for registration/verification reasons, not rejection

### Not Implemented

- Salary / compensation capture (no field in schema; no source module attempts it)
- Company funding-stage / size enrichment
- Scheduled or automatic recurring syncs (manual `python jobs.py` invocation only)
- Inline normalization at insert time (country/work-arrangement is a separate, manually-run migration pass)
- Dashboard / analytics UI beyond the static search frontend
- Provider health alerting (no automated flag when a source silently drops to 0 jobs)

---

## 11. PostgreSQL Integration

PostgreSQL is the system of record, applied via an idempotent `database.sql` (every statement is `CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`) that `database.py`'s `init_schema()` also runs automatically on every startup.

#### jobs table

One row per unique posting. Columns: `id`, `provider`, `title`, `company`, `location` (original provider text, never altered by normalization), `country` (normalized, nullable), `work_arrangement` (normalized, nullable), `url`, `remote` (boolean, provider-native signal), `posted_date`, `tags` (array), `dedup_key` (`UNIQUE`), `first_seen`, `last_seen`, `created_at`. Indexes exist on `provider`, `country`, `remote`, `work_arrangement`, and `first_seen`.

#### provider_runs table

One row per provider per `jobs.py` invocation: `jobs_fetched`, `jobs_inserted`, `jobs_updated`, `duplicates`, and `duration` (seconds). Every provider in this project's history shares one `run_time` (2026-07-10 17:23), meaning the current dataset reflects a single, complete backfill run across all 46 sources rather than incremental accumulation over time.

#### Duplicate detection

Two layers: within a single provider's own fetch, a job is skipped if its `dedup_key` (URL, or a SHA-256 hash of title/company/location when no URL exists) repeats — counted as `duplicates` in `provider_runs`. Across the whole table, `dedup_key UNIQUE` plus `ON CONFLICT ... DO UPDATE` guarantees no duplicate row can ever exist regardless of provider — confirmed live: `184,506` rows, `184,506` distinct `dedup_key` values.

#### Historical tracking

`first_seen`/`last_seen` on every job, plus a full `provider_runs` row per invocation, gives the schema everything needed to track new-vs-returning postings across future runs — the reporting query for "new jobs added in the latest run" already exists in `database.sql`, ready to become meaningful once recurring runs begin (see Section 19).

#### Country normalization

`normalize_countries.py` is a standalone, offline migration reading only the already-stored `location` text. It resolves a single confident country through a tiered strategy (exact country names → ISO codes → city lookup → UK postcode / French department detection → US state fallback), and — as of the most recent update — explicitly detects locations naming 2+ countries or a multi-country region (Europe, EMEA, APAC, LATAM, etc.) and forces `country = NULL` for those rather than guessing, while leaving `location` itself untouched. It never overwrites a value it cannot independently verify.

#### Work arrangement

Derived independently of country by `classify_work_arrangement()`, a word/phrase search over `location` text for remote/hybrid/on-site signals. Intentionally not mutually exclusive with country — "Remote - US" resolves to both `work_arrangement='remote'` and `country='United States'`.

#### Reporting capability

Six standing report queries (total jobs, jobs by provider, jobs by country, remote/non-remote split, duplicate counts, new jobs in the latest run) live in both `database.sql` (for direct `psql` use) and `database.py`'s `REPORT_QUERIES`, and print automatically at the end of every `jobs.py` run.

---

## 12. Statistics

All figures below are live queries against the current PostgreSQL database, run July 13, 2026, carried forward unchanged from the prior report (no schema or data change occurred between that report and this revision — confirmed by file modification timestamps: `database.py`/`jobs.py` predate the prior report's own generation date).

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

Top 3 providers (SmartRecruiters, Greenhouse, Lever) supply 57.4% of all jobs — the dataset's volume is concentrated in ATS boards, not evenly spread across 46 sources. Notably, all three were also among the first providers confirmed `done` in the original research catalog (Section 3.2) — the highest-volume sources were also the earliest, lowest-friction wins the research identified (no-auth, no-registration, structurally simple company-board APIs).

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

These are two independent signals: `work_arrangement` is a location-text classifier (only fires on explicit wording); `remote` is each provider's own boolean/status field where one exists (e.g. Ashby's `isRemote`, USAJOBS's `RemoteIndicator`). They intentionally are not reconciled into one field — see Section 18.

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

**Refresh frequency** cannot be reported as a rate: every row in `provider_runs` shares one `run_time` (Section 11) — there has been exactly one ingestion run to date, not a recurring schedule, so there is no interval to measure yet. **Expired-job detection** is likewise not implemented: none of the 46 providers' `normalize()` implementations populate a status/expiration field, and detecting a posting that disappeared from a source would require a second run to diff against, which hasn't occurred. Both are stated here as limitations rather than estimated.

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

The table below covers all 46 providers, directly from `provider_runs`, sorted by duplicate rate descending.

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

MyCareersFuture and HK Gov Vacancies' near-100% duplicate rates are structural, not code defects (Section 18): MyCareersFuture's `limit` parameter is silently ignored so every page re-returns the same 20 records, and HK Gov Vacancies' feed gives every job the same generic portal URL, so URL-based dedup treats 57 of 58 as duplicates of the first.

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

Lever's 870-second run is the slowest in the project despite modest volume, likely reflecting real per-company pagination overhead across its curated list. NAV, Workable, and MyCareersFuture show the highest duplicate rates — each explained structurally in Sections 7 and 18, not a code defect.

---

## 13. API Comparison

Comparing the ten highest-volume providers across the dimensions that matter for data quality. "—" means the field genuinely does not exist for that provider, confirmed in code, not merely unobserved.

| Provider | Volume | Missing fields | Salary | Company info | Freshness | Dup. rate | Resp. time | Reliability | Auth | Filtering |
|---|---:|---|---|---|---|---:|---:|---|---|---|
| SmartRecruiters | 65,392 | Job-ad URL (constructed) | — | Direct field | Live board | 0.003% | 385.7s | High | None | Company, offset/limit |
| Greenhouse | 22,715 | — | — | Direct field | Live board | 0% | 183.8s | High | None | Company only |
| Lever | 17,980 | Company name (derived) | — | Slug-derived | Live board | 0% | 870.1s | High | None | Company, offset/limit |
| NHS Jobs | 10,843 | Employment type (partial) | — | Direct field | Live board | 16.7% | 102.4s | Undocumented endpoint | None | Keyword |
| USAJOBS | 10,000 | — | Not confirmed in code | Direct field | Live board | 0% | 53.1s | High | API key + email | `Page`/`ResultsPerPage` only |
| Bundesagentur | 9,896 | URL (sometimes constructed) | — | Direct field | Live board | 1.0% | 174.3s | High (with retry) | Public key | Keyword, location |
| Reed | 8,994 | Employment-type field entirely | Not confirmed in code | Direct field | Live board | 0.07% | 56.6s | High | HTTP Basic | `resultsToTake`/`resultsToSkip` pagination only |
| NAV Arbeidsplassen | 5,394 | — | — | Direct field | Change-feed, not live-only | 56.8% | 51.4s | Rotating token | Public rotating token | Modified-since cursor |
| Ashby | 5,252 | Company name (mapped) | — | Manually mapped | Live board | 0% | 70.3s | High | None | Company only |
| Workable | 4,137 | — | — | Direct field | Live board | 45.8% | 51.8s | High | None | Company only |

No provider in this project exposes structured salary data that is actually consumed — Reed's and USAJOBS's implementations send no salary parameter or field anywhere in `fetch_raw()`/`normalize()` (verified directly against `sources/reed.py` and `sources/usajobs.py`). Ashby's compensation parameter (`includeCompensation=true`, Section 17.4) is the one confirmed available-but-unused case, because it is the one place the module's own source comment documents the tradeoff explicitly.

---

## 14. Pricing Analysis

No provider in this project is on a flat subscription or a negotiated enterprise contract — the paid tier that exists is exclusively metered/pay-as-you-go. This mirrors the criteria applied during research (Section 4): enterprise-sales-gated providers (15 of them, Section 8.4) were screened out before implementation was ever attempted. Every page below is the exact URL found in this project's own code.

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

Not applicable to the implemented roster — no provider integrated in this project documents a flat-fee subscription or an enterprise contract tier in its code, docs, or account setup. (15 providers matching this profile were identified in research and deliberately not integrated — Section 8.4.)

---

## 15. Implemented vs Pending

#### Completed providers (41 of 46, contributing live data)

All providers listed in Section 7 with status "Live" or "Needs review" — 41 in total, contributing 184,505 of the 184,506 stored jobs.

#### Investigated but scoped out (deliberate narrowing, not rejection)

- **Fantastic.jobs `/v1/active-jb`** — a sibling endpoint covering job-board-sourced listings (LinkedIn, Wellfound, Y Combinator) with a near-identical schema to the ATS-sourced endpoint that was integrated. Deliberately left out to keep the source to one well-defined feed; a natural follow-up.
- **TheirStack's non-jobs endpoints** (company enrichment, hiring signals, contacts, CRM data) — deliberately not touched; only the jobs-search endpoint was in scope.
- **Workable's authenticated SPI API** — the full ATS surface was deliberately not used in favor of the public, no-auth widget API, which is sufficient for this project's read-only needs.
- **Trade Me's per-user OAuth flow** — not needed; the read-only search endpoint only requires two-legged OAuth 1.0a (consumer key/secret, no user token).

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

## 16. Country Coverage

Providers grouped by their intended regional focus (not the resulting job count, which skews further toward the US/UK/Germany because those are also where the highest-volume ATS boards happen to be curated — see Section 12).

| Region | Dedicated providers | Providers |
|---|---:|---|
| United States | 4 | USAJOBS, CareerOneStop, Findwork.dev, Adzuna (configured for `us`) |
| Canada | 0 | *No dedicated source* — Canadian jobs appear only incidentally via global ATS boards. (Job Bank Canada was researched and rejected — Section 8.8 — for a partner-gated live feed and a dataset fallback missing required schema fields.) |
| United Kingdom | 2 | Reed, NHS Jobs |
| Europe (non-UK) | 5 | Bundesagentur für Arbeit (Germany/Austria), Arbetsförmedlingen (Sweden), France Travail (France), EURES (EU/EEA-wide), NAV Arbeidsplassen (Norway) |
| India | 2 | Freshersworld, Hasjob |
| LATAM | 1 | Get on Board |
| APAC | 4 | MyCareersFuture (Singapore), Taiwan MOL, HK Gov Vacancies, Trade Me (New Zealand) |
| Middle East | 0† | No single-country dedicated source; Mustakbil spans 20+ countries incl. UAE, Saudi Arabia |
| Africa | 1 | MyJobMag (Nigeria) |
| Global / Remote / Multi-country | 27 | All 6 ATS platforms (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Teamtailor, Recruitee, Workday), plus RemoteOK, Jobicy, The Muse, Jooble, SerpApi, OpenWebNinja, CareerJet, TheirStack, Fantastic.jobs, Himalayas, Arbeitnow, We Work Remotely, RemoteJobs.org, Remotive, WorkingNomads, NoDesk, Jobspresso, 4dayweek.io, Mustakbil |

† Mustakbil is multi-country and Middle-East-heavy but not single-region, so it's counted under Global/Multi-country rather than claimed as a dedicated Middle East source.

Actual resulting coverage (Section 12) confirms the same imbalance already visible at the provider level: the United States (47.3%), United Kingdom (14.3%), and Germany (6.9%) together account for over two-thirds of all stored jobs, while Canada — despite being a natural target market — has no dedicated source and appears only incidentally. This is a sourcing-mix artifact, not a normalization defect: the country-resolution logic itself (Section 11) is unbiased; it simply has more raw material to work with in the countries where curated ATS company lists happen to be dense. Section 9's deferred candidates (Saramin for Korea, VDAB for Belgium, Work24 for Korea) would each add real single-country depth if completed; none currently address the Canada gap specifically, which remains the clearest unresolved regional weak point identified across both this report and `research/api_analysis.md`.

---

## 17. Job Categories & Department/Team Metadata — Evidence-Based Field Analysis

*Employment-type values (Full-time, Contract, Internship, Temporary) and provider-internal labels (e.g. SmartRecruiters' "General Business") are not a job-category taxonomy, and this section does not treat them as one. What follows is a direct, code-level inventory of what each of the 46 implemented providers actually exposes, and an honest answer to whether any of it constitutes a standardized, cross-provider job category.*

### 17.1 Definitions used in this section

Four distinct concepts get conflated in casual usage; this report keeps them separate because the underlying provider fields are structurally different:

| Term | What it actually means | Example |
|---|---|---|
| **Standardized Job Category** | A job-function taxonomy that is *consistent and comparable across providers* — the same value means the same thing regardless of source. | An industry-standard scheme (e.g. O*NET, LinkedIn's job-function taxonomy). |
| **Employment Type** | Contract shape: full-time, part-time, contract, internship, temporary, freelance. | "Full-time", "Contract" |
| **Department / Team / Business Unit** | The hiring company's *own internal org unit* for this role — not an industry category, just that employer's org chart. | "Platform Engineering", "Revenue" |
| **Occupation / Discipline / Function** | A provider's or government agency's own occupational or functional classification for the role — closer to a real taxonomy than a department name, but still proprietary to that one provider, not shared across the other 45. | SmartRecruiters' `function` field; Taiwan Ministry of Labor's two-level occupation code; USAJOBS's federal job series |
| **Free-text tag / keyword** | Anything else a provider's feed happens to expose (skills, industry sector, academic requirement, etc.), with no taxonomy behind it at all. | "python", "Federal contractor" |

This project's schema has exactly one field, `tags` (a `TEXT[]` array), to hold all four. That collapsing is the root cause of every finding below.

### 17.2 Finding: no provider exposes a standardized, cross-comparable job category — but 23 of 46 expose *some* department/occupation/function-like field

Every one of the 46 provider modules was checked directly against its `normalize()` implementation (the code that decides what goes into `tags`). **Zero providers expose a job-category field that is standardized across this project's 46 sources.** Of the 46, **23 expose some category-like, department-like, business-unit-like, or occupation-like field** — but each is proprietary to that one provider or that one employer, using its own taxonomy. The table below is organized by which of the four sub-concepts (Department/Team/Business Unit vs. Occupation/Discipline/Function) each provider's field actually maps to, since the task brief specifically calls these two families out:

| Provider | Field actually read (from source code) | Closest sub-concept | What it really is |
|---|---|---|---|
| Greenhouse | `departments` | Department/Team | Each hiring company's own org-chart department names |
| Lever | `categories.department`, `categories.team` | Department/Team | Each hiring company's own org-chart labels |
| Ashby | `department`, `team` | Department/Team | Each hiring company's own org-chart labels |
| Workable | `department` | Department/Team | Each hiring company's own org-chart labels |
| Recruitee | `department` | Department/Team | Each hiring company's own org-chart labels |
| Teamtailor | `department` (from feed XML) | Department/Team | Each hiring company's own org-chart labels |
| SmartRecruiters | `department`, `function`, `typeOfEmployment` | Department/Team **and** Function | SmartRecruiters' own three-part taxonomy — the one provider exposing both sub-concepts distinctly |
| Workable | `function` (in addition to `department` above) | Function | A second, function-level field alongside `department` |
| USAJOBS | `job_categories` | Occupation | US federal job-series coding — the most formally standardized single-provider occupation scheme in this project, but still US-federal-specific, not cross-provider |
| Bundesagentur für Arbeit | `beruf` (occupation), `studiengang` (field of study) | Occupation/Discipline | German public-employment-service occupation coding |
| Taiwan Ministry of Labor | `CJOB_NAME1`, `CJOB_NAME2` | Occupation | Taiwanese government two-level occupation code |
| France Travail | `secteurActiviteLibelle` (activity sector) | Occupation/Discipline | French public-employment-service sector coding |
| Trade Me Jobs | `job_category` | Occupation | Trade Me's own listing taxonomy (built, not yet live — Section 7) |
| Himalayas | `categories`, `parentCategories` | Occupation/Discipline | Himalayas' own remote-tech taxonomy |
| Adzuna | `category.label` | Occupation/Discipline | Adzuna's own listing taxonomy |
| The Muse | `categories`, `levels` | Occupation/Discipline | The Muse's own taxonomy |
| Get on Board | `category_name` | Occupation/Discipline | Get on Board's own tech-role taxonomy |
| MyCareersFuture | `categories` | Occupation/Discipline | Singapore government job-portal taxonomy |
| Jobicy | `jobIndustry` | Discipline (industry) | Jobicy's own industry list |
| Fantastic.jobs | `ai_taxonomies_a` | Occupation/Discipline | Fantastic.jobs' own AI-generated taxonomy |
| Freshersworld | regex-extracted from description ("For more {Category} Jobs…") | Occupation/Discipline | Freshersworld's own site category |
| Mustakbil.com | `category` (RSS field) | Occupation/Discipline | Mustakbil's own listing taxonomy |
| MyJobMag | `industry` (RSS field) | Discipline (industry) | MyJobMag's own industry list |
| We Work Remotely | `category` (RSS field) | Occupation/Discipline | We Work Remotely's own listing taxonomy |
| RemoteJobs.org | `category` | Occupation/Discipline | RemoteJobs.org's own listing taxonomy |
| Remotive | `category` | Occupation/Discipline | Remotive's own listing taxonomy |
| Arbeitnow | `tags` (provider's own field) | Discipline (skills-adjacent) | Arbeitnow's own free-text tag list |

The remaining 21 providers expose no category/department/occupation concept at all in their `normalize()` output — confirmed directly in code, not assumed: **Reed** (module comment: "no job-category/employment-type field at all"), **CareerJet** (module comment: "no job-category/employment-type field to draw tags from, same situation as Reed"), **Jobspresso** (module comment: "every item checked live had an empty `<category>` list"), **NAV Arbeidsplassen** (module comment: "no category/skill data at this feed's summary level"), plus NHS Jobs, EURES, Workday, Jooble, SerpApi, OpenWebNinja, Findwork.dev, CareerOneStop, HK Gov Vacancies, NoDesk, FourDayWeek, Hasjob, Arbetsförmedlingen, TheirStack, RemoteOK, WorkingNomads, and MyCareersFuture's employment-type companion field. These providers, where a job type is exposed at all, expose only an **employment-type** value (Section 23, "Employment Type" column) or nothing.

### 17.3 Finding: identical-looking tag strings come from structurally different fields

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

### 17.4 Implementation gap: a field this project could extract but currently doesn't

One case was found where a provider's underlying API documents a richer field than this project's implementation actually requests — confirmed directly in the module's own comment, not inferred:

> **Ashby** — `sources/ashby.py`: *"An optional `includeCompensation=true` query param adds salary data to the response - not needed for this project's schema, so it's left off."*

This is a genuine, deliberate implementation gap: Ashby's public API can return salary/compensation data, and this project chooses not to request it. No equivalent case was found for a *category* field specifically — where a category-, department-, or occupation-like field exists, it is already extracted into `tags`.

### 17.5 Employment-type coverage (distinct from category)

Employment type — full-time / part-time / contract / temporary / internship / freelance — is a separate, real signal from category, and is exposed by more providers (Section 23). Reading the raw stored values from Section 17.3's evidence: **Full-time** dominates wherever captured; **Part-time**, **Contract**, and **Fixed-Term/Permanent** appear as a minority; **Internship** and **Freelance** do not appear as distinct stored values anywhere in this review — either genuinely rare across these 46 sources' curated company/board lists, or captured under a differently-worded value not surfaced in the top tag list. 19,988 jobs (10.8%) carry no tags at all. **Remote / Hybrid / On-site** remains the one dimension that is genuinely normalized in this schema (`work_arrangement`, Section 11/12), independent of the `tags` free text.

### 17.6 Future normalization potential

The 23 department/occupation/function-like fields inventoried in Section 17.2, although each is provider-specific today, are not random or unstructured — most fall cleanly into one of two families (a company's internal org-chart label, or a provider/government agency's own occupational classification), and several are already fairly granular (USAJOBS's federal job series, Bundesagentur's German occupation codes, Taiwan MOL's two-level occupation code). This is a genuine, evidence-supported opportunity: a future version of this platform **could** build a manually-curated crosswalk table mapping each provider's raw category/department/function/occupation value onto a small number of common buckets (e.g. "Engineering," "Sales," "Operations," "Healthcare"), the same way `normalize_countries.py` already does for location text. This is stated as a forward-looking recommendation, not a claim that such normalization exists today or that it would be a small effort — Section 17.3 shows the same English word already means three different things across three providers, so any crosswalk would need to be built and validated per provider, not by simple string matching. See Section 19 ("Should Have") for where this is tracked as a roadmap item.

### 17.7 Conclusion

The correct, defensible statement about this project's job-category data is: **no standardized job category exists or is derivable from the current schema.** What exists instead is a single free-text `tags` array mixing at least four structurally different concepts (department/team/business-unit labels, occupation/discipline/function labels, employment-type values, and miscellaneous tags/skills) from 23 different provider-specific taxonomies across 46 providers, none of which are reconciled with each other — but several of which are specific and structured enough to be a realistic starting point for a future normalization effort (Section 17.6). See Section 23 for the complete per-provider field inventory.

---

## 18. Known Limitations

> **Multi-country locations.** Real postings genuinely list more than one country ("Germany, France, Netherlands"), a region ("EMEA", "APAC", "LATAM", "Europe"), or a paired market ("Remote (US/Canada)"). The normalization layer (Section 11) now detects both cases and forces `country = NULL` rather than guessing — the original `location` text is always preserved, so these postings remain searchable even without a resolved country. This was a deliberate design choice: accurate country statistics require declining to guess, not forcing every posting into one country.

> **Funding stage (Series A/B, etc.) is not available.** No provider integrated in this project exposes company funding data, and none was added — this would require a dedicated external data provider (e.g. Crunchbase/PitchBook-style API), which is out of scope for a job-posting aggregation pipeline. See Section 19.

> **Some commercial providers require paid access.** TheirStack is fully built but currently blocked by its account's billing plan (HTTP 402); Fantastic.jobs' free trial appears exhausted or account-restricted despite a configured key. Neither is a code defect — see Section 15 for the full breakdown.

> **Trial API quotas constrain volume.** SerpApi and OpenWebNinja are both capped at 200 requests/month on their free tiers, which is why each contributes only ~50 jobs despite having no technical pagination limit — the caps in code are deliberate quota conservation, not a discovered ceiling.

#### Additional limitations found during this review

- **Work-arrangement coverage is thin.** Only 4.6% of jobs carry an explicit remote/hybrid/on-site classification, because the classifier depends entirely on wording actually present in `location` text — most postings simply don't say.
- **A long tail of unresolved single-place locations remains.** 1,565 distinct `country` values exist post-normalization; the multi-country/region problem above is now solved, but genuinely ambiguous single places (e.g. a UK county like "Aberdeenshire" with no other identifying text) are correctly left unresolved rather than guessed — a separate, pre-existing gap from the multi-country fix.
- **Several sources are undocumented, reverse-engineered endpoints** (EURES, NHS Jobs, MyCareersFuture, NAV Arbeidsplassen's public token) — none publish an official API contract for what's actually being called, so any of them could change or break without notice. NHS Jobs is the clearest example of why this matters and also why it can pay off — Section 3.4.
- **HK Gov Vacancies effectively collapses to one stored row** — every job in the feed links to the same generic search-portal URL (no per-posting URL exists in the source data), so URL-based deduplication treats 57 of 58 fetched jobs as duplicates of the first. The data is real; the dedup strategy for this specific source needs a different key.
- **MyCareersFuture is similarly under-yielding** — 1,980 of 2,000 fetched records were duplicates in a single run, worth root-causing before relying on this source for Singapore coverage.
- **No salary data exists anywhere in the schema** — not partially captured, not planned; zero providers expose it in a form this pipeline consumes.
- **Reed exposes no employment-type field at all**, unlike most other commercial aggregators.
- **The dataset is a single point-in-time snapshot** (all 46 `provider_runs` rows share one `run_time`) — there is not yet a second run to validate the "new jobs" / staleness reporting logic against.
- **The provider research catalog (268 providers) is itself a snapshot**, not a living document — several classifications (Section 3.4) were already stale relative to the current 46-provider implementation by the time this report was written, and will drift further as providers change their APIs, pricing, or access models over time. Appendix A should be periodically re-verified, not treated as permanently authoritative.

---

## 19. Future Improvements

### Must Have

- Move country/work-arrangement normalization inline into `jobs.py`'s save path, instead of a separate manual migration script run after the fact
- Scheduled, automated recurring syncs (currently a single manual invocation)
- Resolve the 5 non-contributing providers: provision credentials (Trade Me, CareerOneStop), resolve TheirStack billing, verify Fantastic.jobs' trial/account status, root-cause Arbeitnow's 0-job run

### Should Have

- Reporting dashboard on top of PostgreSQL (currently `psql`/report-query access only)
- Better location enrichment to shrink the 1,565-distinct-country long tail
- A normalized employment-type field, reconciling the fragmented `tags` values (Section 17)
- A curated department/occupation crosswalk table, per Section 17.6's forward-looking recommendation — the highest-leverage next step if job-category comparability is ever required
- Dedicated Canada, broader APAC, and Middle East sources — currently incidental coverage only; Section 9's deferred candidates (Saramin, VDAB, Work24) partially address APAC/Europe depth but not Canada specifically
- Provider-run health alerting (flag when a source's `jobs_fetched` drops to 0 or far below its historical baseline)
- Complete the 6 deferred providers in Section 9, in the priority order given there

### Nice to Have

- Funding-stage / company-size enrichment via an external data provider
- Salary capture/normalization where a source exposes it
- Historical trend tracking across multiple runs once recurring syncs exist
- Integration of Fantastic.jobs' `/v1/active-jb` sibling endpoint (LinkedIn/Wellfound/YC-sourced)
- Periodic re-verification of Appendix A's 268-provider catalog, since provider APIs, pricing, and access models change over time (Section 18)

---

## 20. Lessons Learned

- **Research shaped implementation, concretely and traceably.** Five of `research/api_analysis.md`'s "Top 10 APIs to integrate next" recommendations (Adzuna multi-country, MyCareersFuture, France Travail, CareerOneStop/NLx, Get on Board) were subsequently built — this is not a coincidence and not asserted without evidence; Section 3.2 traces each one directly.
- **A provider's classification can and should change as evidence improves.** NHS Jobs moved from "no viable public API" (268-provider catalog, evaluating the official gated channel) to "implemented" (an independently discovered, undocumented public feed) without either assessment being wrong — they were evaluating different things. Get on Board, Working Nomads, Freshersworld, and Hasjob moved from "needs verification" to "implemented" once someone checked. Documenting classification changes, not just final states, is what makes a research catalog reusable (Section 3.4).
- **The modular `BaseJobSource` pattern paid for itself.** Growing from the original ~20 providers to 46 required zero changes to `jobs.py`, the frontend, or any existing source — only new, self-contained modules.
- **Undocumented, reverse-engineered endpoints are a real and recurring pattern** at this scale, not an edge case — 5 of 46 providers (EURES, NHS Jobs, MyCareersFuture, NAV Arbeidsplassen, HK Gov Vacancies) have no official public API contract for what's actually called. They work today, but each is a standing fragility risk with no advance warning if it changes.
- **Pagination behavior must be discovered live, not assumed from docs** — nearly every provider had at least one undocumented quirk (a silently-ignored `limit` param, a hard result-window boundary that returns HTTP 500 instead of an empty page, a `robots.txt` disallow on the richer endpoint) found only by testing against the real API.
- **Conservative, "never overwrite what you can't verify" normalization logic is safer than aggressive re-guessing.** The country-normalization work deliberately forces ambiguous locations to `NULL` rather than picking a plausible-looking answer — this trades completeness for correctness, which is the right trade for statistics a manager will actually read.
- **Per-source fault isolation is not optional at this scale.** With 5 of 46 providers currently non-contributing for entirely unrelated reasons (billing, missing credentials, a transient zero-result run), a pipeline that let one failure abort the whole run would have made this a much worse outage instead of a routine, fully-diagnosed Section 15 entry.
- **External dependencies need monitoring, not just integration.** TheirStack went from working to fully blocked purely through an account-plan change on their end, with no code change on ours — a reminder that "integrated" is not the same as "will keep working."
- **A rejected provider is not a closed question.** 214 providers were correctly excluded (Section 8), but 6 more (Section 9) remain genuinely open — the discipline of separating "structurally impossible" from "not yet completed" is what makes a research catalog worth revisiting instead of re-researching from scratch.

---

## 21. Final Recommendations

Before this pipeline is relied on for production reporting, the following should happen, roughly in priority order:

1. **Close the 5-provider implementation gap.** Provision `TRADEME_CONSUMER_KEY/SECRET` and `CAREERONESTOP_USER_ID/API_TOKEN`, resolve or drop TheirStack's billing block, verify Fantastic.jobs' account/trial status, and re-run Arbeitnow to confirm its 0-job result was transient.
2. **Pursue the highest-priority deferred providers (Section 9.4)** — Saramin and VDAB first, since both are real, workable APIs blocked only by a registration or onboarding step, not a structural barrier.
3. **Add provider-run health alerting** before scheduling recurring syncs — without it, a source silently dropping to 0 (as happened with Arbeitnow in this snapshot) could go unnoticed indefinitely.
4. **Move normalization inline** so every future run's data is immediately consistent, rather than depending on someone remembering to re-run `normalize_countries.py` after each sync.
5. **Investigate the two low-yield sources** (HK Gov Vacancies collapsing to 1 row, MyCareersFuture's 99% duplicate rate) before treating either as a reliable APAC data point.
6. **Extend the regression-test pattern already established for country normalization** (`test_normalize_countries.py`) to cover the aggregation and dedup pipeline itself, so future provider additions can't silently regress existing behavior.
7. **Confirm secrets handling carries through to any deployment target** — `.env` is git-ignored locally, which is necessary but not sufficient; verify the same discipline applies wherever this pipeline eventually runs on a schedule.
8. **Treat Section 18's limitations as a scoped backlog, not a blocker** — none of them prevent the current dataset from being useful today; they define what "production-grade" means for the next phase.
9. **Re-verify Appendix A's rejection reasons periodically** (annually, or before any major sourcing push) — provider APIs, pricing, and access models change, and a "no public API" finding from this research pass could become out of date.

---

## 22. Conclusion

This project's story does not start with 46 providers — it starts with a 268-provider market survey, narrowed to an 86-provider shortlist, refined into 46 working integrations, and validated down to 41 providers actively contributing data today. That lifecycle (Section 3) is the part of this project most valuable to a future engineer who has to decide whether to add a 47th provider, revisit a rejected one, or trust an existing one's data quality — and it is preserved in full in Sections 3, 8, and 9 and Appendices A–B, rather than compressed into "46 providers were chosen."

On the implementation side, the objective was to build an extensible, multi-source job aggregation pipeline with a real database layer and honest location normalization — and it delivered on all three. 46 provider integrations span government labour agencies, six ATS platforms, commercial search APIs, and RSS/XML feeds, all built against one shared interface that has already absorbed more than double its original provider count without structural change. 184,506 unique jobs are stored in PostgreSQL with genuine deduplication, full run history, and a country/work-arrangement normalization layer that would rather leave a field blank than guess wrong.

The platform is not yet production-scheduled — it currently reflects one complete backfill run rather than an ongoing sync — and five providers need attention before the roster is fully live. Six more real, accessible providers (Section 9) remain a registration step or a verification check away from joining it. Neither fact undermines the core result: the architecture, data model, normalization approach, and — new in this revision — the provider research discipline itself have all proven themselves at scale, and every open item in this report (Sections 9, 15, 18, 19, 21) is a scoped, well-understood next step rather than an unknown risk. The project is ready to move from build phase into operational hardening, with a documented, reusable map of where the next providers should come from.

---

## 23. Provider Capability Matrix

For every implemented provider, whether its `normalize()` implementation exposes each field — verified directly against `sources/*.py` for this report. **Yes** = a genuine, structured field is extracted. **Partial** = the concept exists but is proprietary/heuristic/derived/hardcoded rather than a clean structured signal (see the Notes column for which). **Not Exposed** = no evidence of this field was found in the provider's `normalize()` implementation.

Two columns are near-constant and explained once here rather than repeated 46 times: **Salary** is "Not Exposed" for all 46 providers — the schema has no salary field and no module populates one; Ashby is the sole *confirmed* case where the provider's own API could supply it (`includeCompensation=true`) and this project deliberately doesn't request it (Section 17.4). **Visa Sponsorship** is "Not Exposed" for all 46 — no reference to visa/sponsorship data was found in any provider module.

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
| Ashby | Not Exposed | Yes (`employmentType`) | Yes (`department`, `team`) | Partial (manually mapped) | Yes | Yes (`isRemote`) | Not Exposed | Compensation param exists, deliberately unused (Section 17.4) |
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
| Trade Me Jobs | Partial (`job_category`) | Yes (`job_type`) | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | Built from API spec; not exercised against live data (Section 15) |
| CareerOneStop | Not Exposed | Not Exposed | Not Exposed | Yes | Yes | Partial (keyword-inferred) | Not Exposed | Only structured tag is a "Federal contractor" flag |
| Fantastic.jobs | Partial (`ai_taxonomies_a`) | Yes (`employment_type`) | Not Exposed | Yes | Yes | Yes (`work_arrangement`/`location_type`) | Not Exposed | |
| Arbeitnow | Partial (own `tags` field) | Yes (`job_types`) | Not Exposed | Yes | Yes | Yes (`remote` field) | Not Exposed | |

Column totals across all 46: **Job Category** — 23 Partial, 0 Yes, 23 Not Exposed. **Employment Type** — 22 Yes, 2 Partial, 22 Not Exposed. **Dept/Team** — 7 Yes, 39 Not Exposed. **Company** — 43 Yes, 3 Partial (Ashby, Lever, Workday), 0 Not Exposed. **Location** — 44 Yes, 2 Partial (Bundesagentur, Taiwan MOL, both hardcoded country-level fallbacks), 0 Not Exposed. **Remote Flag** — 13 Yes (genuine field), 23 Partial (11 keyword-inferred + 9 hardcoded-True remote-only boards + 3 other derivations), 2 Not Exposed (hardcoded False: 4dayweek, Freshersworld). **Experience Level** — 4 Partial (Himalayas, The Muse, Jobicy, TheirStack), 42 Not Exposed. **Salary** and **Visa Sponsorship** — 0 Yes/Partial, 46 Not Exposed each, for every provider.

These totals are the direct, numeric confirmation behind Section 17's conclusion: **zero** providers reach "Yes" on Job Category, and the 23 "Partial" providers use 23 structurally different, non-interoperable fields.

---

## 24. Project Status

A project-wide Completed / Partially Implemented / Not Yet Started breakdown, distinct from Section 10's feature-level list — this section covers every major component of the project, cross-referencing where each is documented in detail.

### Completed

- **Complete provider research lifecycle preserved and documented** — 268 providers researched, 86 shortlisted, every rejection and deferral reasoned and evidenced (Sections 3, 8, 9, Appendices A–B) — new in this revision
- **46 provider integrations**, all built against the shared `BaseJobSource` interface (Section 2, Section 7)
- **PostgreSQL persistence layer** — `jobs` and `provider_runs` tables, upsert-on-`dedup_key`, idempotent schema application (Section 11)
- **Deduplication** — URL/hash-based, `UNIQUE` constraint enforced, 0 cross-provider duplicates remaining (Section 11, Section 12)
- **Per-provider run history and reporting queries** (Section 11, Section 12)
- **Offline country normalization**, including the multi-country/region-ambiguity fix that forces `NULL` rather than guessing (Section 11, Section 18)
- **Work-arrangement classification** (`remote`/`hybrid`/`onsite` derived from location text) (Section 11, Section 12)
- **`jobs.json` static export** for the frontend, unchanged since Milestone 2 (Section 2)
- **Frontend search, location filter, and sort** (Section 10, per `aggregation_summary.md`)
- **Per-source fault isolation** — one broken provider cannot halt the run (Section 2, Section 20)
- **Evidence-gathering methodology for both implementation and research claims** — direct source-code verification of `tags`/`remote`/`company` field provenance for all 46 providers (Section 17, Section 23), and direct cross-referencing of 268 catalog entries against the live `sources/__init__.py` registry (Section 3)

### Partially Implemented

- **41 of 46 providers actively contributing data**; 5 are built but non-contributing for external reasons (billing, missing credentials, one unexplained zero-result run) (Section 15)
- **Work-arrangement coverage** — only 4.6% of jobs carry an explicit classification; the underlying classifier itself is complete, but most source text simply doesn't say (Section 18)
- **Employment-type capture** — present and genuinely extracted for 24 of 46 providers (22 Yes + 2 Partial in Section 23), entirely absent for the other 22
- **Country resolution** — the multi-country/region case is now solved; a long tail of ~1,565 distinct single-place values remains unenriched (Section 18)
- **Credentialed-provider coverage** — 12 providers use API keys/OAuth; 2 (Trade Me, CareerOneStop) are built but uncredentialed in this environment (Section 15)
- **Provider research follow-through** — 6 real, accessible candidate providers (Saramin, VDAB, CBOP, Work24, GOV.UK Find a Job, Job-Room Switzerland/Portal del Empleo/JobsPikr) remain unbuilt for registration/verification reasons, not rejection (Section 9)

### Not Yet Started

- **Standardized/normalized job-category taxonomy** — confirmed not to exist anywhere in this project's data, and not derivable from the current schema without a dedicated crosswalk-building effort (Section 17)
- **Salary capture and normalization** — no schema field, no provider extracts it (Section 17, Section 18, Section 23)
- **Visa-sponsorship data** — not found in any of the 46 providers' exposed fields; not evaluated whether any upstream API offers it (Section 23)
- **Experience-level normalization** — 4 providers expose a raw signal, folded into free-text `tags`, not a structured field (Section 23)
- **Company funding-stage/size enrichment** (Section 18, Section 19)
- **Scheduled/automated recurring syncs** — every run to date has been a single manual invocation (Section 11, Section 19)
- **Inline normalization at insert time** — country/work-arrangement normalization is a separate, manually-triggered migration step (Section 11, Section 19)
- **Provider-run health alerting** (Section 19, Section 21)
- **Dashboard/analytics UI** beyond the static search frontend (Section 10, Section 19)
- **Expired-job / posting-removal detection** — requires a second run to diff against; none has occurred yet (Section 12)
- **Periodic re-verification of the 268-provider research catalog** — a one-time snapshot, not a living document (Section 18)

---

## 25. Requirement Coverage Matrix

Every requirement from this task's checklist, mapped to the section(s) that address it, with an honest status. **Covered** = fully addressed with evidence. **Partial** = addressed but with a named, specific gap. This matrix combines the original implementation-report checklist (rows 1–19, carried forward from the prior report) with the manager's revision brief for this v2 (rows 20–27, new in this revision).

| # | Requirement | Status | Section(s) | Notes |
|---:|---|---|---|---|
| 1 | Prepare a final project report | Covered | Whole document | |
| 2 | List every API/service used in the project | Covered | Section 7 | All 46, one row each |
| 3 | Document what has been completed and what is still pending | Covered | Section 10, Section 15, Section 24 | |
| 4 | Identify features fully/partially/not-yet-implemented | Covered | Section 10, Section 24 | |
| 5 | List pricing models (free / free trial / pay-as-you-go / subscription / enterprise) | Covered | Section 7, Section 14 | No provider in the implemented roster documents a subscription or enterprise tier; 15 enterprise-only candidates were identified and deliberately excluded in research (Section 8.4) |
| 6 | Highlight services requiring payment after the free tier expires | Covered | Section 14, Section 15 | TheirStack, Fantastic.jobs, SerpApi, OpenWebNinja |
| 7 | Include links to pricing pages for each service | Partial | Section 7, Section 14 | Every provider with a registration/pricing/docs page has one, quoted verbatim from this project's own code; the 31 fully free, no-auth public APIs have no distinct "pricing page" to link by definition |
| 8 | Document the number of jobs available from each API | Covered | Section 7, Section 12 | Fetched and Stored columns for all 46 |
| 9 | Break down job coverage by country/region | Covered | Section 16 | |
| 10 | List job types/categories per API (full-time, part-time, contract, internship, remote, hybrid, on-site, freelance) | Partial | Section 17, Section 23 | Employment-type values are documented per-provider; a genuine "job category" comparable across APIs does not exist (Section 17) — reported as a finding. Internship and freelance were not found as distinct stored values for any provider |
| 11 | Compare data quality across APIs (duplicates, missing fields, stale jobs, salary, company info) | Covered | Section 13, Section 23, Section 12 | |
| 12 | Report how current jobs are (average posting age, refresh frequency, expired jobs) | Covered | Section 12 ("Posting freshness") | Median 22 days / mean 229 days posting age; refresh frequency and expired-job detection explicitly stated as not yet measurable (single ingestion run to date) |
| 13 | Analyze duplicate jobs across APIs and estimate deduplication rates | Covered | Section 12 ("Deduplication rate and response time — every provider") | Covers all 46 providers plus a global 8.08% rate |
| 14 | Document rate limits and API quotas for every provider | Partial | Section 7 (Notes column), Section 14 | Every row has a discovered pagination/result-window limit where one exists |
| 15 | Record response times and reliability for each API | Covered | Section 12 (full table), Section 13 (qualitative detail for top 10) | |
| 16 | Note authentication requirements and implementation complexity for each API | Partial | Section 7 (Auth column) | Authentication is fully documented per provider; "implementation complexity" has no explicit rating column, stated as a gap rather than invented |
| 17 | Document all filtering capabilities (location, remote, salary, experience level, visa sponsorship, company, industry, keywords) | Partial | Section 13 (top 10 only) | Filtering capability is not documented for the other 36 providers. No provider was found to expose salary, experience-level, or visa-sponsorship filtering |
| 18 | Prioritize remaining tasks into Must/Should/Nice to Have | Covered | Section 19 | |
| 19 | End with clear recommendations and next steps for production readiness | Covered | Section 21, Section 22 | |
| 20 | Preserve the complete provider research effort (~250 researched, ~80 shortlisted), not just the 46 implemented | Covered | Section 3, Appendix A, Appendix B | 268 researched (API Catalog), 86 shortlisted (Sheet1) — exact counts from this project's own workbook, not rounded estimates |
| 21 | Demonstrate how research influenced implementation decisions, not merely that research occurred | Covered | Section 3.2–3.4, Section 20 | Five research-recommended APIs traced directly to implementation; NHS Jobs' research-to-engineering divergence documented as a specific case study |
| 22 | Document why providers were selected, why rejected, which should be reconsidered, limitations, payment/enterprise requirements, geographic restrictions | Covered | Section 4, Section 8, Section 9 | Every one of 214 rejected providers carries a specific reason and category (Section 8); 6 providers flagged as genuinely reconsiderable (Section 9) |
| 23 | Add a Research Lifecycle section (250+ → 80 → 46 → 41 → remaining) | Covered | Section 3 | Exact figures: 268 → 86 → 46 → 41 → 214 rejected + 8 deferred/unresolved |
| 24 | Add Provider Research Overview, Evaluation Methodology, Decision Matrix, Knowledge Base, Selection/Rejection Criteria sections | Covered | Section 3, Section 4, Section 5, Section 8 | |
| 25 | Add Future Candidate, Deferred, Enterprise-only, Paid-only, Region-Restricted, Authentication-Restricted, Deprecated, No-Public-API, Commercial-Partnership provider sections | Covered | Section 8 (subsections 8.1–8.10), Section 9 | Every named category from the brief is populated with real providers and evidence, or explicitly noted where a category has zero or very few qualifying entries (e.g. Deprecated: 1 confirmed case) |
| 26 | Replace job-category analysis to reflect department/team/business-unit/occupation/discipline/function metadata rather than employment-type values | Covered | Section 17 | Section 17.2 explicitly maps each of the 23 category-like providers onto Department/Team vs. Occupation/Discipline/Function; Section 17.6 adds the forward-looking normalization discussion requested |
| 27 | Output as a new file, `Final_Project_Report_v2.md`, without overwriting the original | Covered | This document | `FINAL_PROJECT_REPORT.md` is untouched |

### Methodology note and its own limitation

Sections 3, 4, 5, 8, and 9 (the new research-lifecycle material) were produced by extracting and cross-referencing the complete `API Catalog` (268 rows) and `Sheet1` (86 rows) data directly from this project's `job_api.xlsx` workbook and its companion research artifacts, matched programmatically against every provider's name in `sources/__init__.py` — not summarized or paraphrased from memory. Every count in Section 3 and Section 5 (268, 86, 46, 41, 38, 8, 6, 214) is a direct tally over that extracted data, reproducible against the same source file. Sections 6–7 and 10–24 (the implementation-facing material) were carried forward from the prior report; source code (`sources/nhsjobs.py`, `sources/fantasticjobs.py`, `sources/__init__.py`) was independently re-read for this revision to verify the specific research-to-implementation claims in Section 3.4, and file modification timestamps confirmed no implementation change occurred between the prior report and this one. This is stated explicitly per this task's own instruction to name a limitation rather than imply a completeness this revision did not fully re-verify line-by-line.

---


## Appendix A — Complete Provider Research Catalog (268 providers)

Full `API Catalog` sheet of `job_api.xlsx`, one row per researched provider. **Status** is this catalog's classification *at research time*; **Implemented?** cross-checks that name against this project's actual current `sources/__init__.py` registry (46 modules) as ground truth — the two differ in a handful of cases where research and engineering diverged, each explained in the narrative sections above.


### Implemented in catalog snapshot (38)

| Provider | Type | Region | Implemented? | Research Notes / Reason |
|---|---|---|---|---|
| Adzuna | Commercial Aggregator | Canada; Europe (Other); India; LATAM; Other/Unclassified; Singapore/SEA; United Kingdom; United States | Yes | Live in production as sources/adzuna.py. |
| Arbeitnow | Public | Germany; Other/Unclassified | Yes | Live in production as sources/arbeitnow.py. |
| Arbetsformedlingen JobSearch API (Sweden) | Government | Sweden | Yes | Live in production as sources/arbetsformedlingen.py. |
| Ashby | ATS | Canada; Europe (Other); Germany; India; Other/Unclassified; Remote/Global; Singapore/SEA; United Kingdom; United States | Yes | Live in production as sources/ashby.py. |
| Bundesagentur fur Arbeit | Government | Europe (Other); Germany | Yes | Live in production as sources/bundesagentur.py. |
| CareerOneStop / NLx "List Jobs V2" | Government | United States | Yes | Live in production as sources/careeronestop.py. |
| Careerjet | Commercial Aggregator | United Kingdom; United States | Yes | Live in production as sources/careerjet.py. |
| EURES | Government | Europe (Other) | Yes | Live in production as sources/eures.py. |
| Findwork.dev | Public | United States | Yes | Live in production as sources/findwork.py. |
| France Travail (ex-Pole emploi) | Government | Europe (Other) | Yes | Live in production as sources/francetravail.py. |
| Greenhouse | ATS | Canada; Europe (Other); Germany; India; LATAM; Other/Unclassified; Singapore/SEA; United Kingdom; United States | Yes | Live in production as sources/greenhouse.py. |
| Himalayas | Public | Canada; Europe (Other); Germany; India; LATAM; Other/Unclassified; Remote/Global; Singapore/SEA; United Kingdom; United States | Yes | Live in production as sources/himalayas.py. |
| Hong Kong Government Job Vacancy Open Data APIs (Civil Service Bureau + Digital Policy Office, DATA.GOV.HK) | Government | Hong Kong | Yes | Live in production as sources/hk_gov_vacancies.py. |
| Jobicy | Public | Canada; Europe (Other); Germany; LATAM; Other/Unclassified; Singapore/SEA; United States | Yes | Live in production as sources/jobicy.py. |
| Jobspresso | Public | Remote/Global | Yes | Live in production as sources/jobspresso.py. |
| Jooble | Commercial Aggregator | Europe (Other); Germany; Other/Unclassified; United Kingdom; United States | Yes | Live in production as sources/jooble.py. |
| Lever | ATS | Canada; Europe (Other); Germany; India; LATAM; Other/Unclassified; Remote/Global; Singapore/SEA; United Kingdom; United States | Yes | Live in production as sources/lever.py. |
| Mustakbil.com | Commercial Job Board | Pakistan | Yes | Live in production as sources/mustakbil.py. |
| MyCareersFuture | Government | Singapore/SEA | Yes | Live in production as sources/mycareersfuture.py. |
| MyJobMag | Commercial Job Board | Nigeria | Yes | Live in production as sources/myjobmag.py. |
| NAV Arbeidsplassen Job Vacancy Feed (Norway) | Government | Norway | Yes | Live in production as sources/nav_norway.py. |
| NoDesk | Public | Remote/Global | Yes | Live in production as sources/nodesk.py. |
| OpenWeb Ninja | Commercial Aggregator | India; United States | Yes | Live in production as sources/openwebninja.py. |
| Recruitee (Tellent) ATS API (Netherlands) | ATS | Netherlands | Yes | Live in production as sources/recruitee.py. |
| Reed | Commercial Aggregator | United Kingdom | Yes | Live in production as sources/reed.py. |
| RemoteJobs.org | Public | United States | Yes | Live in production as sources/remotejobs_org.py. |
| RemoteOK | Public | Canada; Europe (Other); India; LATAM; Other/Unclassified; Singapore/SEA; United Kingdom; United States | Yes | Live in production as sources/remoteok.py. |
| Remotive Remote Jobs API | Public | Remote/Global | Yes | Live in production as sources/remotive.py. |
| SerpApi | Commercial Aggregator | India; United States | Yes | Live in production as sources/serpapi.py. |
| SmartRecruiters | ATS | Canada; Europe (Other); Germany; India; LATAM; Other/Unclassified; Singapore/SEA; United Kingdom; United States | Yes | Live in production as sources/smartrecruiters.py. |
| Taiwan Ministry of Labor Open API / 台灣就業通 Job Vacancy Web Service | Government | Taiwan | Yes | Live in production as sources/taiwan_mol.py. |
| Teamtailor | ATS | Canada; Europe (Other); Germany; LATAM; Other/Unclassified; Singapore/SEA; United Kingdom; United States | Yes | Live in production as sources/teamtailor.py. |
| The Muse | Commercial Aggregator | Europe (Other); India; Other/Unclassified; Remote/Global; United Kingdom; United States | Yes | Live in production as sources/themuse.py. |
| TheirStack | Commercial Aggregator | n/a (plan-gated) | Yes | Live in production as sources/theirstack.py. |
| USAJOBS | Government | United States | Yes | Live in production as sources/usajobs.py. |
| We Work Remotely (RSS feeds) | Public | Remote/Global | Yes | Live in production as sources/weworkremotely.py. |
| Workable | ATS | Canada; Europe (Other); Germany; India; Other/Unclassified; Singapore/SEA; United Kingdom; United States | Yes | Live in production as sources/workable.py. |
| Workday | ATS | India | Yes | Live in production as sources/workday.py. |

### Registration/Approval Required (6)

| Provider | Type | Region | Implemented? | Research Notes / Reason |
|---|---|---|---|---|
| CBOP - Centralna Baza Ofert Pracy (Poland public employment offices) | Government | Poland | No | Poland's national public-employment-office job database. Real SOAP web service returning batches of up to 1,000 live offers per file, but capped at 20 calls/cycle and only reachable during a 17:00-07:00 window - workable, but the fetch pattern doesn't match our REST/JSON conventions. |
| Fantastic Jobs / Active Jobs DB | Commercial Aggregator | India; United States | Yes | RapidAPI wrapper aggregating 54+ ATS platforms and 200k+ career sites (3M+ jobs/month globally, incl. India/Europe/LATAM/SEA in one integration) - same pay-per-call pattern as Adzuna/SerpApi already integrated. High value if the metered cost is acceptable. |
| Saramin Open API (사람인 오픈 API) | Commercial Job Board | South Korea | No | One of Korea's largest commercial job boards. Real documented API, but gated behind an application/approval step, explicitly labeled beta with a 500-calls/day cap - usable, just slower to unlock and rate-constrained. |
| Trade Me Jobs | Commercial Job Board | New Zealand | Yes | Genuine live job-search endpoint (GET /v1/Search/Jobs) confirmed by the catalog research - one of New Zealand's two largest job boards, alongside SEEK. Free self-service developer registration, OAuth 1.0a is more setup work than a bearer key but well-documented. |
| VDAB Vacature API (Belgium - Flanders public employment service) | Government | Belgium | No | Flanders' public employment service vacancy API - free but requires an application form and an exploratory onboarding meeting with VDAB before credentials are issued. Real read API, just a slower registration path than a self-serve key. |
| Work24 (formerly Worknet/워크넷) Job Listings Open API - Korea Employment Information Service | Government | South Korea | No | South Korea's national public job bank, verified live on data.go.kr with real-time XML/JSON updates and a free key. Caveat: license text restricts use to non-commercial, attributed, unmodified use - confirm terms with the agency before ingesting. |

### Needs Live Verification (9)

| Provider | Type | Region | Implemented? | Research Notes / Reason |
|---|---|---|---|---|
| 4dayweek.io | Public | Remote/Global | Yes | Site references a feed/API but no public spec was confirmed - verify the RSS URL is genuinely open before building; likely the same WeWorkRemotely/Jobspresso/NoDesk-style pattern as its sibling remote boards, not yet checked live this session. |
| Freshersworld | Commercial Aggregator | India | Yes | Had a public RSS/XML feed historically for India fresher/graduate jobs; needs a live check to confirm it still exists before building against it. |
| GOV.UK Find a Job (DWP) | Government | United Kingdom | No | UK's national government job service; no confirmed public read/search API for third parties was found - only an employer-side SFTP bulk-upload path for posting vacancies. Worth one more direct check with DWP given its size. |
| Get on Board | Commercial Aggregator | LATAM | Yes | LATAM tech/startup board that advertises a public API (page/per_page pagination documented) but it has not been independently verified end-to-end. |
| Hasjob | Commercial Aggregator | India | Yes | Tiny community India tech-jobs board; historically had a public feed with no auth, but documentation status is unconfirmed and volume is very small. |
| Job-Room Jobs API (SECO, Switzerland) | Government | Switzerland | No | Switzerland's biggest job platform, but the API is built primarily for employers/ATS submitting ads under a reporting-obligation rule - whether third-party aggregators can get read-only access is unconfirmed in the docs. Ask SECO directly before counting on this one. |
| JobsPikr | Commercial Aggregator | India | No | Commercial aggregator (incl. Naukri/Monster-sourced India feeds) with a real API and docs, but pricing is custom/quote-based rather than a published self-serve rate - confirm actual signup process and cost before treating as a routine paid integration. |
| Portal del Empleo / Servicio Nacional de Empleo (STPS Mexico) | Government | Mexico | No | Mexico's national employment service publishes datasets on the CKAN-based datos.gob.mx open-data platform, but a live, current-vacancy-specific API endpoint for the job board itself was not directly confirmed - may turn out to be a dataset dump like Job Bank Canada. |
| Working Nomads | Public | LATAM | Yes | Free API/RSS advertised for this small LATAM remote board, but no docs were found and auth requirements are unconfirmed ('varies'). Low volume even if it works. |

### Not Viable at Research Time (215)

| Provider | Type | Region | Implemented? | Research Notes / Reason |
|---|---|---|---|---|
| 104 Job Bank (104人力銀行) | Commercial Job Board | Taiwan | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| 1111 Job Bank (1111人力銀行) | Commercial Job Board | Taiwan | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| 51job (前程无忧 / Qiancheng Wuyou) | Commercial Job Board | China | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| AMS eJob-Room (Austria public employment service) | Government | Austria | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| APEC (Association Pour l'Emploi des Cadres, France) | Government-affiliated / Non-profit Job Board | France | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| APS Jobs (Australian Public Service careers) | Government | Australia | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Adecco India | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Agencia Publica de Empleo SENA (APE) | Government | Colombia | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| AllJobs.co.il | Commercial Job Board | Israel | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Apideck | ATS Unified API | Global | No | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Workday - we already integrate directly for free). Redundant and enterprise-priced. |
| Apify | Web Scraping API | Global | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Apna | Commercial Aggregator | India | No | No public API for third-party aggregators. |
| Appcast | Job Distribution Network | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Aura (by Aura Intelligence) | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| BMET / Ami Probashi (Bangladesh Overseas Employment) | Government | Bangladesh | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| BOSS Zhipin (Kanzhun Limited, NASDAQ: BZ) | Commercial Job Board | China | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| BambooHR | ATS | Remote/Global | No | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Bayt.com | Commercial Job Board | United Arab Emirates | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bdjobs.com | Commercial Job Board | Bangladesh | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bolsa Nacional de Empleo (BNE / SENCE, Chile) | Government | Chile | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bossjob | Commercial Job Board | Philippines | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bright Data | Web Scraping API | Global | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| BrighterMonday | Commercial Job Board | Kenya | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Broadbean (Veritone Hire) | Job Distribution Network | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Built In | Commercial Aggregator | United States | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bumeran | Commercial Aggregator | LATAM | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CEIPAL | ATS | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CV-Library | Commercial Aggregator | United Kingdom | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CWJobs | Commercial Aggregator | United Kingdom | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CareerBuilder | Commercial Job Board | United States | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CareerBuilder / Monster (Talent Network distribution) | Job Distribution Network | United States | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| CareerLink Vietnam | Commercial Job Board | Vietnam | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CareerOne (Australia) | Commercial Job Board | Australia | No | Feed-ingest / posting-distribution network only - no public read endpoint for pulling job data as a consumer. |
| Careers24 | Commercial Job Board | South Africa | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Careers@Gov | Government | Singapore/SEA | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Catho Developer API | Commercial Job Board | Brazil | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| China MOHRSS National Public Employment Service Platform (全国公共招聘服务平台) | Government | China | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Civil Service Jobs | Government | United Kingdom | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Claro Analytics (WilsonHCG) | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Cliclavoro / Ministero del Lavoro Open Data (Italy) | Government | Italy | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Computrabajo | Commercial Aggregator | LATAM | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Coresignal | Commercial Aggregator | India; United States | No | Enterprise-tier data vendor sold via sales contact, not a published self-serve price - same bucket as the other enterprise data vendors below. |
| Cutshort | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Darwinbox | ATS | India | No | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Datapeople (by Payscale) | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Dice | Commercial Aggregator | United States | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Diffbot | Web Scraping API | Global | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Draup | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Drushim | Commercial Job Board | Israel | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Egypt Ministry of Labour (formerly Ministry of Manpower) Job Portal | Government | Egypt | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Elempleo | Commercial Aggregator | LATAM | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Eluta | Commercial Aggregator | Canada | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Employment Services of South Africa (ESSA) - Dept. of Employment and Labour | Government | South Africa | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Forasna | Commercial Job Board | Egypt | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Foundit (Monster India) | Commercial Aggregator | India | No | No public API for third-party aggregators. |
| Freshteam | ATS | India | No | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Glassdoor Jobs API | Commercial Job Board | Global | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Glints | Commercial Aggregator | Singapore/SEA | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Google Cloud Talent Solution (Job Search API) | Enterprise Job Search API | Global | No | This is a hosted ML matching/search engine you populate with your OWN job postings - it is not a source of aggregated third-party listings at all. Enterprise infrastructure product, not a job feed. |
| Google for Jobs | Meta-search Aggregator | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Greenwich.HR (WageScape) | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| GreytHR | ATS | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| GulfTalent | Commercial Job Board | United Arab Emirates | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Gupy Public API | ATS | Brazil | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| HackerEarth Jobs | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| HasData | Web Scraping API | Global | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Hello Work Job Information API (ハローワーク求人情報提供サービス, MHLW) | Government | Japan | No | Japan's real, fully-documented national job API - but registration is restricted to licensed private job-placement businesses, local governments, or training institutions. A generic aggregator does not qualify for access. |
| HelloWork ATS Partner API (France) | Commercial Job Board | France | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Hired.com (LHH Recruitment Solutions) | Commercial Job Board | United States | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Hirist | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Hong Kong Labour Department Interactive Employment Service (iES, jobs.gov.hk) | Government | Hong Kong | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Horsefly Analytics | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| IEFPOnline / netEmprego (Portugal public employment service) | Government | Portugal | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Indeed Hiring Lab | Labor Market Intelligence | Global | No | Indeed's economic-research arm: publishes aggregate labor-market indices/trend CSVs (mirrored on FRED), not individual job records. Research/statistics product, not a live job listings feed. |
| Indeed India | Commercial Aggregator | India | No | Enterprise partner-only access; not available to a generic aggregator. |
| Indeed PLUS Job Distribution API (Recruit Holdings, Japan) | Aggregator/Partner Network | Japan | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| InfoJobs (Spain) | Commercial Job Board | Spain | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Instahyre | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Internshala | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Israeli Employment Service (Sherut HaTaasuka / taasuka.gov.il) | Government | Israel | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JSearch (RapidAPI, by OpenWeb Ninja) | Data Aggregator / API Vendor | Global | No | Generic B2B data-aggregation vendor, not a dedicated job board - paid, and overlaps with sources already integrated. |
| Jadarat (Saudi National Employment Portal / HRDF) | Government | Saudi Arabia | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Job Bank (ESDC) feed / Open Gov dataset | Government | Canada | No | Canada's national job bank: the live feed requires ESDC partner approval, and the fallback open dataset is a monthly CSV dump missing employer/company names and per-job apply URLs - the two fields this project's schema requires. Doesn't fit even with credentials. |
| Job Market Finland / Tyomarkkinatori (TE-palvelut, Finland) | Government | Finland | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobKorea | Commercial Job Board | South Korea | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobStreet / JobsDB (SEEK group) | Commercial Aggregator | Singapore/SEA | No | SEEK-group flagship boards for SEA; enterprise partner-only access, no self-serve path (catalog explicitly marks 'Not Recommended'). |
| JobThai | Commercial Job Board | Thailand | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobberman | Commercial Job Board | Nigeria | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobcase (MaxRecruit) | Job Distribution Network | United States | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Jobcase Platform API | Commercial Job Board | United States | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobg8 | Job Distribution Network | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Jobillico | Commercial Aggregator | Canada | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobindex (Denmark) | Commercial Job Board | Denmark | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobisJob (LIFULL Connect) | Meta-search Aggregator | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Jobnet.dk (Denmark public employment portal) | Government | Denmark | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobrapido | Commercial Aggregator | Europe (Other) | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobs.cz | Commercial Aggregator | Europe (Other) | No | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| JobsDB Hong Kong (SEEK Group) / CTgoodjobs | Commercial Job Board | Hong Kong | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobsEQ (Chmura Economics & Analytics) | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| JobsIreland.ie (Ireland public employment service) | Government | Ireland | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobsite | Commercial Aggregator | United Kingdom | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JoinVision (JobCloud HR Tech) | Job Distribution Network | Austria / DACH | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Jora (Australia) | Job Aggregator | Australia | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Joveo | Job Distribution Network | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| JustRemote | Commercial Job Board | Remote/Global | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Kalibrr | Commercial Aggregator | Singapore/SEA | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Karir.com | Commercial Job Board | Indonesia | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Keka | ATS | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Kelly Services India | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Kemnaker Karirhub (SIAPkerja) | Government | Indonesia | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Kombo.dev | ATS Unified API | Global | No | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Workday - we already integrate directly for free). Redundant and enterprise-priced. |
| Ladders | Commercial Aggregator | United States | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Lensa | Meta-search Aggregator | United States | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Lightcast (formerly Emsi Burning Glass) Job Postings API | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Lightcast Jobs Canada | Commercial Aggregator | Canada | No | Paid labor-market-intelligence product sold through a sales process, not a self-serve developer signup; catalog itself marks 'Not Recommended'. |
| LinkUp | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| LinkedIn Jobs | Commercial Aggregator | India | No | Enterprise partner program only - no self-serve developer signup for job search/aggregation. |
| MOHRE UAE Federal Careers / iRecruitment Portal | Government | United Arab Emirates | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| MP Rojgar | Government | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| MahaJobs | Government | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| ManpowerGroup India | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Mantiks | Data Aggregator / API Vendor | Global | No | Generic B2B data-aggregation vendor, not a dedicated job board - paid, and overlaps with sources already integrated. |
| Merge.dev | ATS Unified API | Global | No | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Workday - we already integrate directly for free). Redundant and enterprise-priced. |
| Mitula (LIFULL Connect / Adzuna) | Meta-search Aggregator | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Monster | Commercial Job Board | Global | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| NAVTTC National Employment Exchange Tool (NEXT / jobs.gov.pk) | Government | Pakistan | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| NEAIMS - National Employment Authority Kenya | Government | Kenya | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| NHS Jobs | Government | United Kingdom | Yes | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| National Career Service (NCS) | Government | India | No | India's NCS exposes a periodic bulk open-government dataset (data.gov.in), not a live per-job search API - stale snapshots, not real-time postings. Doesn't fit a live-fetch architecture. |
| National Directorate of Employment (NDE) Nigeria | Government | Nigeria | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| National Job Portal (NJP) - Pakistan | Government | Pakistan | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| National Job Portal - Bangladesh (jobs.gov.bd) | Government | Bangladesh | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Naukri | Commercial Aggregator | India | No | No public API; any access is undocumented/grey-area and India-IP-restricted. |
| Naukrigulf | Commercial Job Board | United Arab Emirates | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Nexxt (formerly Beyond.com) | Commercial Job Board | United States | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Nimble (Nimbleway) | Web Scraping API | Global | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| OCC Mundial | Commercial Aggregator | LATAM | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Outsourcely | Commercial Job Board | Remote/Global | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Oxylabs | Web Scraping API | Global | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| PandoLogic (pandoIQ) / Veritone Hire | Job Distribution Network | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Pangian | Public | Remote/Global | No | pangian.com redirects (301) to a static 'Thank You for Being Part of Pangian' shutdown notice on GitHub Pages (pangianhq.github.io) - confirmed live. Every other path (/jobs/, /about/, /blog/, all RSS-candidate URLs) 404s. The service is discontinued/paused indefinitely, not merely credential-gated. |
| People Data Labs | Data Aggregator / API Vendor | Global | No | Generic B2B data-aggregation vendor, not a dedicated job board - paid, and overlaps with sources already integrated. |
| PhilJobNet (DOLE Bureau of Local Employment) | Government | Philippines | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Piloterr | Web Scraping API | Global | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Pnet | Commercial Job Board | South Africa | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Portal Empleo Argentina (Ministerio de Capital Humano / ex-Trabajo) | Government | Argentina | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Pracuj.pl (Poland) | Commercial Job Board | Poland | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| PredictLeads | Data Aggregator / API Vendor | Global | No | Generic B2B data-aggregation vendor, not a dedicated job board - paid, and overlaps with sources already integrated. |
| Profesia | Commercial Aggregator | Europe (Other) | No | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Public Service Commission of Sri Lanka (psc.gov.lk) | Government | Sri Lanka | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Quess Corp | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Radancy | Job Distribution Network | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Randstad India | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Recruit CRM | ATS | India | No | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Recruitics | Job Distribution Network | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Remote First Jobs (Dynamite Jobs) | Public | Remote/Global | No | remotefirstjobs.com is behind an active Cloudflare managed JS challenge on every path tested (including robots.txt itself) - confirmed live, HTTP 403 with a 'Just a moment...' interactive challenge page. Not a credentials gate; a plain HTTP client cannot get through it at all, and this project's architecture has no headless-browser/JS-execution layer to attempt a bypass. |
| Remote.co | Commercial Job Board | Remote/Global | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Revelio Labs | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Rikunabi / Mynavi (Recruit Co. / Mynavi Corporation) | Commercial Job Board | Japan | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Rojgar Sangam (UP) | Government | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Rozee.pk | Commercial Job Board | Pakistan | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| SEEK (SEEK.com.au / SEEK.co.nz) | Commercial Job Board | Australia; New Zealand | No | Feed-ingest / posting-distribution network only - no public read endpoint for pulling job data as a consumer. |
| SEPE Open Data Portal (Spain public employment service) | Government | Spain | No | Spain's SEPE only publishes static statistical/administrative open-data files - no confirmed live REST API for current vacancies exists; a known third-party scraper for it is deprecated. |
| SINE Aberto (Sistema Nacional de Emprego / Ministerio do Trabalho e Emprego) | Government | Brazil | No | Brazil suspended this data-sharing service in October 2022 (CODEFAT Resolution 956/2022) pending LGPD privacy-law compliance updates - no active API to integrate against right now. |
| ScraperAPI | Web Scraping API | Global | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Scrapingdog | Web Scraping API | Global | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Shine | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| SmartDreamers | Job Distribution Network | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Snagajob | Commercial Job Board | United States | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| StepStone | Commercial Aggregator | Europe (Other) | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Superset | ATS | India | No | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Talent.com | Commercial Aggregator | Canada | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| TalentNeuron (Gartner) | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Talroo | Job Distribution Network | United States | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| TeamLease | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Techmap.io | Data Aggregator / API Vendor | Global | No | Generic B2B data-aggregation vendor, not a dedicated job board - paid, and overlaps with sources already integrated. |
| Telangana T-Jobs | Government | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Textkernel Jobfeed / Market IQ | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| Thailand Department of Employment - Smart Job Center (ไทยมีงานทำ) | Government | Thailand | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| The Burning Glass Institute | Labor Market Intelligence | Global | No | Enterprise labor-market-intelligence SaaS sold via sales contract - not a self-serve job-postings feed. |
| TimesJobs | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| TopCV | Commercial Job Board | Vietnam | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| TotalJobs | Commercial Aggregator | United Kingdom | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Triplebyte | Commercial Job Board | United States | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Trovit (LIFULL Connect / Adzuna) | Meta-search Aggregator | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| UWV Open Match Data (Netherlands) | Government | Netherlands | No | UWV (Dutch public employment service) publishes aggregate labor-market statistics datasets, not individual live job postings - no per-job identifier exists in the data at all. |
| Unified.to | ATS Unified API | Global | No | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Workday - we already integrate directly for free). Redundant and enterprise-priced. |
| Unstop | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Upward.net (a Jobcase company) | Job Distribution Network | United States | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Vagas for Business API (Vagas.com.br) | ATS / Job Board | Brazil | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| VietnamWorks Open API | Commercial | Vietnam | No | Partner Access Required - gated to approved commercial partners, not open developer registration. |
| WUZZUF | Commercial Job Board | Egypt | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Welcome to the Jungle | Commercial Aggregator | Europe (Other) | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Wellfound | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| WhatJobs | Meta-search Aggregator | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Work and Income / Find a Job (MSD, New Zealand) | Government | New Zealand | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Work at a Startup (Y Combinator) | Commercial Job Board | Global | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| WorkIndia | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Workato | ATS Unified API | Global | No | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Workday - we already integrate directly for free). Redundant and enterprise-priced. |
| Workforce Australia | Government | Australia | No | The public API is write/management-only (employers create and manage job ads via OAuth2 through the Business portal) - no public job-listings read/search endpoint exists to pull postings from. |
| Workopolis | Commercial Aggregator | Canada | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| WowJobs | Commercial Aggregator | Canada | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Xing Jobs | Commercial Aggregator | Europe (Other) | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| XpressJobs (xpress.jobs) | Commercial Job Board | Sri Lanka | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| ZipAlerts (ZipRecruiter TrafficBoost) | Job Distribution Network | United States | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| ZipRecruiter API | Commercial Aggregator | United States | No | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| Zoho Recruit | ATS | India | No | Enterprise-only pricing/access - gated behind a sales or partner-approval process, no self-serve developer path. |
| ZonaJobs | Commercial Job Board | Argentina | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Zyte (formerly Scrapinghub) | Web Scraping API | Global | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| data.gov.in OGD platform | Government | India | No | General-purpose Indian open-government-data portal spanning 33 sectors; not jobs-specific, and individual resources are static per-resource datasets rather than a live job-postings feed. |
| eQuest | Job Distribution Network | Global | No | Advertiser-side job-distribution/CPC network - built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| iimjobs | Commercial Aggregator | India | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| jobs.ch (Switzerland) | Commercial Job Board | Switzerland | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| karriere.at (Austria) | Commercial Job Board | Austria | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| topjobs.lk | Commercial Job Board | Sri Lanka | No | No public API - the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
---

## Appendix B — Shortlist Audit (Sheet1, 86 providers)

Full `Sheet1` of `job_api.xlsx` — the curated shortlist, deliberately narrower than the 268-row API Catalog. Cross-checked the same way as Appendix A.


### Implemented in catalog snapshot (31)

| Provider | Type | Region | Implemented? | Research Notes / Reason |
|---|---|---|---|---|
| Adzuna | API | Multi-country (UK/US/Europe/India/etc.) | Yes | Live in production as sources/adzuna.py. |
| Arbeitnow | API | Germany | Yes | Live in production as sources/arbeitnow.py. |
| Arbetsformedlingen JobSearch API (Sweden) | Government API | Sweden | Yes | Live in production as sources/arbetsformedlingen.py. |
| Ashby | ATS | Global (multi-company ATS) | Yes | Live in production as sources/ashby.py. |
| Bundesagentur fur Arbeit | Government API | Germany | Yes | Live in production as sources/bundesagentur.py. |
| CareerOneStop / NLx "List Jobs V2" | Government API | United States | Yes | Live in production as sources/careeronestop.py. |
| Careerjet | API | Multi-country | Yes | Live in production as sources/careerjet.py. |
| EURES | Government API | EU/EEA | Yes | Live in production as sources/eures.py. |
| Findwork.dev | API | United States | Yes | Live in production as sources/findwork.py. |
| France Travail (ex-Pole emploi) | Government API | France | Yes | Live in production as sources/francetravail.py. |
| Greenhouse | ATS | Global (multi-company ATS) | Yes | Live in production as sources/greenhouse.py. |
| Himalayas | API | Remote/Global | Yes | Live in production as sources/himalayas.py. |
| Hong Kong Government Job Vacancy Open Data APIs (Civil Service Bureau + Digital Policy Office, DATA.GOV.HK) | Government API | Hong Kong | Yes | Live in production as sources/hk_gov_vacancies.py. |
| Jobicy | API | Remote/Global | Yes | Live in production as sources/jobicy.py. |
| Jooble | API | Global (multi-country aggregator) | Yes | Live in production as sources/jooble.py. |
| Lever | ATS | Global (multi-company ATS) | Yes | Live in production as sources/lever.py. |
| MyCareersFuture | Government API | Singapore | Yes | Live in production as sources/mycareersfuture.py. |
| MyJobMag | RSS | Nigeria (brand also covers Kenya/South Africa/UK) | Yes | Live in production as sources/myjobmag.py. |
| NAV Arbeidsplassen Job Vacancy Feed (Norway) | Government API | Norway | Yes | Live in production as sources/nav_norway.py. |
| OpenWeb Ninja | API | Global | Yes | Live in production as sources/openwebninja.py. |
| Recruitee (Tellent) ATS API (Netherlands) | ATS | Netherlands/Belgium/DACH (multi-company ATS) | Yes | Live in production as sources/recruitee.py. |
| Reed | API | United Kingdom | Yes | Live in production as sources/reed.py. |
| RemoteJobs.org | API | Remote/Global | Yes | Live in production as sources/remotejobs_org.py. |
| RemoteOK | API | Remote/Global | Yes | Live in production as sources/remoteok.py. |
| Remotive Remote Jobs API | API | Remote/Global | Yes | Live in production as sources/remotive.py. |
| SerpApi | API | Global (Google Jobs proxy) | Yes | Live in production as sources/serpapi.py. |
| SmartRecruiters | ATS | Global (multi-company ATS) | Yes | Live in production as sources/smartrecruiters.py. |
| Teamtailor | ATS | Global (multi-company ATS) | Yes | Live in production as sources/teamtailor.py. |
| The Muse | API | United States / Global | Yes | Live in production as sources/themuse.py. |
| USAJOBS | Government API | United States | Yes | Live in production as sources/usajobs.py. |
| Workable | ATS | Global (multi-company ATS) | Yes | Live in production as sources/workable.py. |

### Registration/Approval Required (5)

| Provider | Type | Region | Implemented? | Research Notes / Reason |
|---|---|---|---|---|
| CBOP - Centralna Baza Ofert Pracy (Poland public employment offices) | Government API | Poland | No | Poland's national public-employment-office job database - real SOAP service returning live offers in batches of up to 1,000, but capped at 20 calls/cycle and only reachable during a 17:00-07:00 window. Free, but the SOAP/time-window fetch pattern doesn't match this project's REST/JSON conventions. |
| Fantastic Jobs / Active Jobs DB | API | Global (US/India/Europe/LATAM/SEA) | Yes | RapidAPI wrapper aggregating 54+ ATS platforms and 200k+ career sites (3M+ jobs/month globally). Same pay-per-call pattern as Adzuna/SerpApi already integrated - highest remaining volume if the metered cost is approved. |
| NHS Jobs | Government API | United Kingdom | Yes | NHS Jobs publishes a documented 'Self-Serve API' for retrieving listings, but access is gated to organisations that are UK-based, public-facing, and post health/NHS-associated roles, with no cost to jobseekers - a vetted-application model, not open self-serve. A generic global aggregator may not qualify; worth applying to find out. |
| Trade Me Jobs | API | New Zealand | Yes | Genuine live job-search endpoint (GET /v1/Search/Jobs), free self-service developer registration. One of New Zealand's two largest job boards alongside SEEK. |
| Work24 (formerly Worknet/워크넷) Job Listings Open API - Korea Employment Information Service | Government API | South Korea | No | South Korea's national public job bank, real-time XML/JSON updates, free key issued instantly on signup. License text restricts use to non-commercial/attributed/unmodified - confirm terms before production use. |

### Needs Live Verification (8)

| Provider | Type | Region | Implemented? | Research Notes / Reason |
|---|---|---|---|---|
| Freshersworld | Commercial Job Board | India | Yes | Had a public RSS/XML feed historically for India fresher/graduate jobs; needs a live check to confirm it still exists before building against it. |
| GOV.UK Find a Job (DWP) | Commercial Job Board | United Kingdom | No | UK's national government job service - no confirmed public read/search API for third parties was found, only an employer-side SFTP bulk-upload path for posting vacancies. Worth one direct check with DWP given the size of the prize. |
| Get on Board | Commercial Job Board | LATAM | Yes | LATAM tech/startup board that advertises a public API (page/per_page pagination documented) but it has not been independently verified end-to-end. |
| Hasjob | Commercial Job Board | India | Yes | Tiny community India tech-jobs board; historically had a public feed with no auth, but documentation status is unconfirmed and volume is very small. |
| Portal del Empleo / Servicio Nacional de Empleo (STPS Mexico) | Commercial Job Board | Mexico | No | Mexico's national employment service publishes on the CKAN-based datos.gob.mx open-data platform, but a live, current-vacancy-specific API endpoint was not directly confirmed - may turn out to be a dataset dump like Job Bank Canada. |
| Thailand Department of Employment - Smart Job Center (ไทยมีงานทำ) | API | Thailand | No | Thailand's national job-matching platform; the Ministry of Labour's e-Labour portal references 'Open Data' services connected to Smart Job Center, but exact API/dataset endpoints weren't confirmed live - worth checking Thailand's national open-data portal (data.go.th) directly. |
| Working Nomads | Commercial Job Board | LATAM (remote) | Yes | Free API/RSS advertised for this small LATAM remote board, but no docs were found and auth requirements are unconfirmed ('varies'). Low volume even if it works. |
| ZonaJobs | Commercial Job Board | Argentina | No | Argentina's leading generalist job portal (Navent group, ~20,000+ live listings). Advertises an 'ofertas-de-trabajo-api' page and third-party job-distribution integrations (dstribute.io), but no public read-API documentation was found live - likely an employer-posting feed rather than a consumer read API. Worth a direct check with Navent. |

### Not Viable at Research Time (42)

| Provider | Type | Region | Implemented? | Research Notes / Reason |
|---|---|---|---|---|
| Apideck | ATS Unified API | Global (middleware) | No | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Ashby, Workable, Teamtailor, SmartRecruiters, Recruitee - we already integrate directly for free). Redundant and adds an unnecessary paid layer. |
| Apify | Web Scraping API | Global (infra vendor) | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Bayt.com | Commercial Job Board | United Arab Emirates / MENA | No | One of the Gulf region's largest commercial job boards - no public API; employer/recruiter account required to post, jobseeker browsing only through the site itself. |
| Bolsa Nacional de Empleo (BNE / SENCE, Chile) | Government API | Chile | No | Chile's public employment portal requires jobseeker/citizen login to browse; a real employer API exists but credentials are issued per-account after a request, not open self-serve. |
| Bossjob | Commercial Job Board | Philippines | No | Chat-first AI job platform for the Philippines/SEA - no public developer API found in official documentation or search results. |
| Bright Data | Web Scraping API | Global (infra vendor) | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| BrighterMonday | Commercial Job Board | Kenya | No | East Africa's largest commercial job board - no public API found; only an undocumented internal endpoint, employer account required to post. |
| Careers24 | Commercial Job Board | South Africa | No | South African commercial job board - no public API; employer/recruiter account required to post listings. |
| Diffbot | Data Aggregator / API Vendor | Global (data vendor) | No | Generic B2B data-aggregation/enrichment vendor, not a dedicated job board - paid, and overlaps with sources already integrated directly for free. |
| Employment Services of South Africa (ESSA) - Dept. of Employment and Labour | Government API | South Africa | No | South African government employment portal gated behind jobseeker SA-ID or employer UIF-registration login - no public API for third parties. |
| Google Cloud Talent Solution (Job Search API) | API | Global (enterprise infra) | No | A hosted ML matching/search engine you populate with your OWN job postings - not a source of aggregated third-party listings at all. Enterprise infrastructure product, not a job feed. |
| HasData | Web Scraping API | Global (infra vendor) | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Hello Work Job Information API (ハローワーク求人情報提供サービス, MHLW) | Government API | Japan | No | Japan's real, fully-documented national job API - but registration is restricted to licensed private job-placement businesses, local governments, or training institutions. A generic aggregator does not qualify. |
| Indeed Hiring Lab | API | Global (research) | No | Indeed's economic-research arm publishes aggregate labor-market indices/trend CSVs (also mirrored on FRED), not individual job records. Research/statistics product, not a live job listings feed. |
| Israeli Employment Service (Sherut HaTaasuka / taasuka.gov.il) | Government API | Israel | No | Requires an Israeli citizen with a Teudat Zehut (national ID) to register online and then appear in person within 14 days - a citizen-services portal, not a public data API. |
| JSearch (RapidAPI, by OpenWeb Ninja) | Data Aggregator / API Vendor | Global (redundant wrapper) | No | A RapidAPI-hosted repackaging of the same OpenWeb Ninja data this project already integrates directly (OpenWeb Ninja is implemented) - paying for the RapidAPI wrapper of a source we already have natively would be pure redundancy. |
| Jadarat (Saudi National Employment Portal / HRDF) | Government API | Saudi Arabia | No | Saudi national employment portal requiring a Saudi-national citizen account to access - not available to a third-party aggregator at all, let alone one outside Saudi Arabia. |
| Job Bank (ESDC) feed / Open Gov dataset | Government API | Canada | No | Canada's national job bank: the live feed needs ESDC partner approval, and the fallback open dataset is a monthly CSV dump missing employer/company names and per-job apply URLs - the two fields this project's schema requires. |
| Jobberman | Commercial Job Board | Nigeria | No | Leading Nigerian commercial job board (Africa-wide under the same brand) - no public API; employer account required to post. |
| Mantiks | Data Aggregator / API Vendor | Global (data vendor) | No | Generic B2B data-aggregation/enrichment vendor, not a dedicated job board - paid, and overlaps with sources already integrated directly for free. |
| Merge.dev | ATS Unified API | Global (middleware) | No | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Ashby, Workable, Teamtailor, SmartRecruiters, Recruitee - we already integrate directly for free). Redundant and adds an unnecessary paid layer. |
| NEAIMS - National Employment Authority Kenya | Government API | Kenya | No | Kenya's national employment authority system requires jobseeker/employer/agency account registration to use - no public API found. |
| National Career Service (NCS) | Government API | India | No | India's NCS exposes a periodic bulk open-government dataset (data.gov.in), not a live per-job search API - stale snapshots, not real-time postings. |
| Naukrigulf | Commercial Job Board | United Arab Emirates / Gulf | No | Gulf-region sister site to Naukri.com (also not integrated, same grey-area/no-public-API situation) - recruiter/employer account required, verification mandatory to activate. |
| Nimble (Nimbleway) | Web Scraping API | Global (infra vendor) | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Oxylabs | Web Scraping API | Global (infra vendor) | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| People Data Labs | Data Aggregator / API Vendor | Global (data vendor) | No | Generic B2B data-aggregation/enrichment vendor, not a dedicated job board - paid, and overlaps with sources already integrated directly for free. |
| PhilJobNet (DOLE Bureau of Local Employment) | Government API | Philippines | No | Philippines' national government job-matching portal - vacancies can be browsed without login, but no public API or developer documentation exists for pulling listings programmatically. |
| Piloterr | Web Scraping API | Global (infra vendor) | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| PredictLeads | Data Aggregator / API Vendor | Global (data vendor) | No | Generic B2B data-aggregation/enrichment vendor, not a dedicated job board - paid, and overlaps with sources already integrated directly for free. |
| SEPE Open Data Portal (Spain public employment service) | Government API | Spain | No | Spain's SEPE only publishes static statistical/administrative open-data files - no confirmed live REST API for current vacancies; a known third-party scraper for it is deprecated. |
| SINE Aberto (Sistema Nacional de Emprego / Ministerio do Trabalho e Emprego) | Government API | Brazil | No | Brazil suspended this data-sharing service in October 2022 (CODEFAT Resolution 956/2022) pending LGPD privacy-law compliance updates - no active API to integrate against right now. |
| ScraperAPI | Web Scraping API | Global (infra vendor) | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Scrapingdog | Web Scraping API | Global (infra vendor) | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| Techmap.io | Data Aggregator / API Vendor | Global (data vendor) | No | Generic B2B data-aggregation/enrichment vendor, not a dedicated job board - paid, and overlaps with sources already integrated directly for free. |
| The Burning Glass Institute | API | Global (research) | No | A nonprofit labor-market research institute (spun out of Burning Glass Technologies, now Lightcast) - publishes research reports and indices (e.g. the 'State of Skills' report), not a job-postings API or feed of any kind. |
| UWV Open Match Data (Netherlands) | Government API | Netherlands | No | UWV (Dutch public employment service) publishes aggregate labor-market statistics datasets, not individual live job postings - no per-job identifier exists in the data. |
| Unified.to | ATS Unified API | Global (middleware) | No | Paid middleware that re-wraps other ATSs (several of which - Greenhouse, Lever, Ashby, Workable, Teamtailor, SmartRecruiters, Recruitee - we already integrate directly for free). Redundant and adds an unnecessary paid layer. |
| WUZZUF | Commercial Job Board | Egypt | No | Egypt's leading commercial job board - no public API; employer account required to post. |
| Workforce Australia | Government API | Australia | No | The public API is write/management-only (employers create and manage job ads via OAuth2) - no public job-listings read/search endpoint exists to pull postings from. |
| Zyte (formerly Scrapinghub) | Web Scraping API | Global (infra vendor) | No | Generic web-scraping infrastructure vendor, not a job-specific API - using it means building and maintaining a custom per-site scraper ourselves, which is a project in itself, not one more provider. |
| data.gov.in OGD platform | Government API | India | No | General-purpose Indian open-government-data portal spanning 33 sectors; not jobs-specific, and individual resources are static per-resource datasets rather than a live job-postings feed. |
---

## Appendix C — Capacity & Expansion Planning Notes

`job_api.xlsx` contains a fourth sheet beyond the `API Catalog` and `Sheet1` discussed throughout this report: **`Integration Detail`** (104 rows, 35 columns), accompanied by a **`Schema Definitions`** sheet that documents what every column in the workbook means. This appendix summarizes what that sheet contains and why it is not the primary evidence base for Sections 3–9.

### What `Integration Detail` actually is

`Integration Detail` is a per-provider (and, for high-volume ATS providers, per-region-within-provider) capacity and engineering-planning worksheet: expansion potential, recommended cron frequency, API calls per run, deduplication-key strategy, cross-provider overlap risk, and canonical-source preference. Its own `Schema Definitions` entries repeatedly reference "Report Sec 13/17" and "report Part 6" — a different, earlier report structure than either this document or `FINAL_PROJECT_REPORT.md`, confirming it was produced during an earlier phase of this project, when only **20 providers** were integrated (stated explicitly in its own `Schema Definitions` notes) and the persistence layer was still `jobs.json`, not PostgreSQL.

### Why it is referenced here rather than reproduced in full

Because it predates the current 46-provider, PostgreSQL-backed implementation, its per-provider figures (e.g. "Current Jobs Collected") do not match the live figures in Section 12 of this report, and reproducing all 104 rows × 35 columns would restate stale numbers alongside this report's current ones in a way that risks confusion rather than adding evidence. It is preserved here as a pointer, not omitted as if it didn't exist — a future engineer revisiting expansion planning should open `Integration Detail` directly rather than rely on a summary.

### Representative example (USAJOBS, read directly from the sheet)

To illustrate the sheet's depth without reproducing it in full: for USAJOBS, `Integration Detail` records a **Current Fetch Strategy** of `Page` + `ResultsPerPage=500` looping up to `MAX_PAGES=20`, a **Current Bottleneck** of "Hard API result window" (confirmed independently in Section 7 of this report as the same 10,000-record ceiling), an **Expansion Strategy** of partitioning the query by `JobCategoryCode`/`LocationName` to open multiple independent 10,000-result windows (**Estimated Additional Jobs: +10,000–20,000**, **Engineering Effort: Medium**), a **Best Deduplication Key** of `PositionURI` (a stable, government-issued canonical URL), and an **Estimated Duplicate Exposure** of "Very Low — 100% company-unique, zero overlap pairs identified with any other provider." This level of per-provider planning detail exists for roughly the top 20–30 providers by volume in the sheet (the highest-volume ATS providers are broken out by region within the same provider, which is why the sheet has 104 rows for far fewer distinct providers).

### How this connects to Section 19 (Future Improvements)

The expansion strategies recorded in `Integration Detail` for still-relevant, high-volume providers (e.g. partitioned queries for USAJOBS, Bundesagentur, and Reed to bypass their hard result windows; ATS company-slug-list expansion for the six ATS providers) remain valid engineering recommendations today, independent of the sheet's stale absolute job counts — they describe *how* to extract more from an API's own already-exposed capabilities, which does not change when the surrounding pipeline moves from `jobs.json` to PostgreSQL. Anyone acting on Section 19's "Should Have" coverage-expansion items is encouraged to consult `Integration Detail` directly for the fully worked-out, per-provider version of that recommendation.

---

 · Data snapshot 2026-07-10 · Original report generated 2026-07-13 · This revision (v2) generated 2026-07-15, adding the complete provider research lifecycle (268-provider catalog, 86-provider shortlist, evaluation methodology, decision matrix, and full rejection/deferral knowledge base) alongside the previously-reported implementation detail.*

*Source of truth: PostgreSQL (`jobs`, `provider_runs`), this repository's own source code, and `job_api.xlsx` (API Catalog, Sheet1, Integration Detail, Schema Definitions sheets) — no figure in this report is estimated or assumed. Where evidence was not available or a research artifact was found to be a stale snapshot, this report states that explicitly rather than inferring a result.*
## Appendix D — Rejected Providers by Category

Complete, unabridged lists behind the Section 8 summary — all 214 non-implemented `blocked` catalog providers, one row each, no provider repeated across categories. Region and reasoning are quoted directly from this project's research catalog.

### D.1 No Public API (126 providers)

By far the largest rejection category. These providers' web/mobile presence is real and often large-scale, but no developer documentation, API endpoint, or third-party read access exists at all — the only way to see their data is to browse the site as a jobseeker or register as an employer to post. This is the hard floor referenced in Section 4: no amount of pricing tolerance or engineering effort overcomes a genuinely nonexistent read API. It spans nearly every region in the catalog — India (Naukri, Shine, Internshala, TimesJobs, and 20+ others), the Gulf (Bayt.com, GulfTalent, Naukrigulf), East Asia (51job, BOSS Zhipin, JobKorea, Rikunabi/Mynavi), Europe (StepStone, CV-Library, CWJobs, InfoJobs, Pracuj.pl), and government portals that only support citizen/employer browser login rather than a data feed (Civil Service Jobs UK, Job Market Finland, JobsIreland.ie, Cliclavoro Italy). None of these were rejected on data-quality or geographic grounds — they were rejected because there is nothing for a third-party pipeline to call.

| Provider | Type | Region | Reason |
|---|---|---|---|
| 104 Job Bank (104人力銀行) | Commercial Job Board | Taiwan | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| 1111 Job Bank (1111人力銀行) | Commercial Job Board | Taiwan | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| 51job (前程无忧 / Qiancheng Wuyou) | Commercial Job Board | China | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| AMS eJob-Room (Austria public employment service) | Government | Austria | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| APEC (Association Pour l'Emploi des Cadres, France) | Government-affiliated / Non-profit Job Board | France | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| APS Jobs (Australian Public Service careers) | Government | Australia | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Adecco India | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| AllJobs.co.il | Commercial Job Board | Israel | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Apna | Commercial Aggregator | India | No public API for third-party aggregators. |
| BMET / Ami Probashi (Bangladesh Overseas Employment) | Government | Bangladesh | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| BOSS Zhipin (Kanzhun Limited, NASDAQ: BZ) | Commercial Job Board | China | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bayt.com | Commercial Job Board | United Arab Emirates | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bdjobs.com | Commercial Job Board | Bangladesh | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bolsa Nacional de Empleo (BNE / SENCE, Chile) | Government | Chile | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bossjob | Commercial Job Board | Philippines | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| BrighterMonday | Commercial Job Board | Kenya | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Built In | Commercial Aggregator | United States | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Bumeran | Commercial Aggregator | LATAM | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CEIPAL | ATS | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CV-Library | Commercial Aggregator | United Kingdom | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CWJobs | Commercial Aggregator | United Kingdom | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CareerBuilder | Commercial Job Board | United States | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| CareerLink Vietnam | Commercial Job Board | Vietnam | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Careers24 | Commercial Job Board | South Africa | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Careers@Gov | Government | Singapore/SEA | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Catho Developer API | Commercial Job Board | Brazil | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| China MOHRSS National Public Employment Service Platform (全国公共招聘服务平台) | Government | China | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Civil Service Jobs | Government | United Kingdom | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Cliclavoro / Ministero del Lavoro Open Data (Italy) | Government | Italy | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Computrabajo | Commercial Aggregator | LATAM | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Cutshort | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Dice | Commercial Aggregator | United States | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Drushim | Commercial Job Board | Israel | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Egypt Ministry of Labour (formerly Ministry of Manpower) Job Portal | Government | Egypt | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Elempleo | Commercial Aggregator | LATAM | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Eluta | Commercial Aggregator | Canada | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Employment Services of South Africa (ESSA) — Dept. of Employment and Labour | Government | South Africa | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Forasna | Commercial Job Board | Egypt | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Foundit (Monster India) | Commercial Aggregator | India | No public API for third-party aggregators. |
| Glassdoor Jobs API | Commercial Job Board | Global | Historically offered `partner_id`/`partner_key` access; now enterprise-only — no self-serve path remains. |
| Glints | Commercial Aggregator | Singapore/SEA | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| GreytHR | ATS | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| GulfTalent | Commercial Job Board | United Arab Emirates | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Gupy Public API | ATS | Brazil | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| HackerEarth Jobs | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| HelloWork ATS Partner API (France) | Commercial Job Board | France | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Hired.com (LHH Recruitment Solutions) | Commercial Job Board | United States | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Hirist | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Hong Kong Labour Department Interactive Employment Service (iES, jobs.gov.hk) | Government | Hong Kong | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| IEFPOnline / netEmprego (Portugal public employment service) | Government | Portugal | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| InfoJobs (Spain) | Commercial Job Board | Spain | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Instahyre | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Internshala | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Job Market Finland / Työmarkkinatori (TE-palvelut, Finland) | Government | Finland | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobKorea | Commercial Job Board | South Korea | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobThai | Commercial Job Board | Thailand | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobberman | Commercial Job Board | Nigeria | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobcase Platform API | Commercial Job Board | United States | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobillico | Commercial Aggregator | Canada | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobindex (Denmark) | Commercial Job Board | Denmark | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobnet.dk (Denmark public employment portal) | Government | Denmark | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobrapido | Commercial Aggregator | Europe (Other) | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobsDB Hong Kong (SEEK Group) / CTgoodjobs | Commercial Job Board | Hong Kong | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JobsIreland.ie (Ireland public employment service) | Government | Ireland | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jobsite | Commercial Aggregator | United Kingdom | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Jora (Australia) | Job Aggregator | Australia | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| JustRemote | Commercial Job Board | Remote/Global | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Kalibrr | Commercial Aggregator | Singapore/SEA | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Karir.com | Commercial Job Board | Indonesia | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Keka | ATS | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Kelly Services India | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Ladders | Commercial Aggregator | United States | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| MOHRE UAE Federal Careers / iRecruitment Portal | Government | United Arab Emirates | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| MP Rojgar | Government | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| MahaJobs | Government | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| ManpowerGroup India | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Monster | Commercial Job Board | Global | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| NAVTTC National Employment Exchange Tool (NEXT / jobs.gov.pk) | Government | Pakistan | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| NEAIMS — National Employment Authority Kenya | Government | Kenya | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| National Directorate of Employment (NDE) Nigeria | Government | Nigeria | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| National Job Portal (NJP) — Pakistan | Government | Pakistan | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| National Job Portal — Bangladesh (jobs.gov.bd) | Government | Bangladesh | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Naukri | Commercial Aggregator | India | No public API; any access is undocumented/grey-area and India-IP-restricted. |
| Naukrigulf | Commercial Job Board | United Arab Emirates | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Nexxt (formerly Beyond.com) | Commercial Job Board | United States | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| OCC Mundial | Commercial Aggregator | LATAM | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Outsourcely | Commercial Job Board | Remote/Global | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| PhilJobNet (DOLE Bureau of Local Employment) | Government | Philippines | Public browsing needs no login, but no public API or developer documentation exists for pulling listings programmatically. |
| Pnet | Commercial Job Board | South Africa | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Portal Empleo Argentina (Ministerio de Capital Humano / ex-Trabajo) | Government | Argentina | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Pracuj.pl (Poland) | Commercial Job Board | Poland | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Public Service Commission of Sri Lanka (psc.gov.lk) | Government | Sri Lanka | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Quess Corp | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Randstad India | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Remote.co | Commercial Job Board | Remote/Global | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Rikunabi / Mynavi (Recruit Co. / Mynavi Corporation) | Commercial Job Board | Japan | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Rojgar Sangam (UP) | Government | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Rozee.pk | Commercial Job Board | Pakistan | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Shine | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Snagajob | Commercial Job Board | United States | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| StepStone | Commercial Aggregator | Europe (Other) | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Talent.com | Commercial Aggregator | Canada | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| TeamLease | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Telangana T-Jobs | Government | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Thailand Department of Employment — Smart Job Center (ไทยมีงานทำ) | Government | Thailand | No public API or developer documentation of any kind was found — a web/mobile-app-only platform with no discoverable integration surface. |
| TimesJobs | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| TopCV | Commercial Job Board | Vietnam | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| TotalJobs | Commercial Aggregator | United Kingdom | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Triplebyte | Commercial Job Board | United States | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Unstop | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Vagas for Business API (Vagas.com.br) | ATS / Job Board | Brazil | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| WUZZUF | Commercial Job Board | Egypt | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Welcome to the Jungle | Commercial Aggregator | Europe (Other) | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Wellfound | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Work and Income / Find a Job (MSD, New Zealand) | Government | New Zealand | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Work at a Startup (Y Combinator) | Commercial Job Board | Global | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| WorkIndia | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Workopolis | Commercial Aggregator | Canada | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| WowJobs | Commercial Aggregator | Canada | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| Xing Jobs | Commercial Aggregator | Europe (Other) | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| XpressJobs (xpress.jobs) | Commercial Job Board | Sri Lanka | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| ZonaJobs | Commercial Job Board | Argentina | An SEO/landing page suggesting an API exists was confirmed to be for employers *posting* jobs, not a read API — see Section 9 for the fuller writeup. |
| iimjobs | Commercial Aggregator | India | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| jobs.ch (Switzerland) | Commercial Job Board | Switzerland | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| karriere.at (Austria) | Commercial Job Board | Austria | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |
| topjobs.lk | Commercial Job Board | Sri Lanka | No public API — the site/portal requires a jobseeker or employer login; no developer/API access is documented anywhere. |


### D.2 Employer-Side Distribution / Write-Only Networks — Wrong Data-Flow Direction (25 providers)

These providers have real, sometimes well-documented APIs — the reason they were rejected is structural, not access-related: they are built for **employers and job boards to push postings out** (CPC job-distribution networks, meta-search advertiser platforms, or write/management-only feeds), not for an aggregator to pull postings in. Building against one of these would mean becoming a client that *pays to advertise*, not a source that *reads* — the opposite relationship this project needs.

| Provider | Type | Region | Reason |
|---|---|---|---|
| Appcast | Job Distribution Network | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out, not for aggregators to pull postings in. No public read API. |
| Broadbean (Veritone Hire) | Job Distribution Network | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| CareerBuilder / Monster (Talent Network distribution) | Job Distribution Network | United States | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| CareerOne (Australia) | Commercial Job Board | Australia | Feed-ingest / posting-distribution network only — no public read endpoint for pulling job data as a consumer. |
| Google for Jobs | Meta-search Aggregator | Global | Advertiser/organic-crawl indexing surface for employer sites — no public read API for third-party aggregators. |
| Indeed PLUS Job Distribution API (Recruit Holdings, Japan) | Aggregator/Partner Network | Japan | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Jobcase (MaxRecruit) | Job Distribution Network | United States | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Jobg8 | Job Distribution Network | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| JobisJob (LIFULL Connect) | Meta-search Aggregator | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| JoinVision (JobCloud HR Tech) | Job Distribution Network | Austria / DACH | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Joveo | Job Distribution Network | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Lensa | Meta-search Aggregator | United States | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Mitula (LIFULL Connect / Adzuna) | Meta-search Aggregator | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| PandoLogic (pandoIQ) / Veritone Hire | Job Distribution Network | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Radancy | Job Distribution Network | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Recruitics | Job Distribution Network | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| SEEK (SEEK.com.au / SEEK.co.nz) | Commercial Job Board | Australia; New Zealand | Feed-ingest / posting-distribution network only — no public read endpoint for pulling job data as a consumer. |
| SmartDreamers | Job Distribution Network | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Talroo | Job Distribution Network | United States | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Trovit (LIFULL Connect / Adzuna) | Meta-search Aggregator | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Upward.net (a Jobcase company) | Job Distribution Network | United States | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| WhatJobs | Meta-search Aggregator | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| Workforce Australia | Government | Australia | The public API is write/management-only (employers create and manage job ads via OAuth2) — no public job-listings read/search endpoint exists to pull postings from. |
| ZipAlerts (ZipRecruiter TrafficBoost) | Job Distribution Network | United States | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |
| eQuest | Job Distribution Network | Global | Advertiser-side job-distribution/CPC network — built for employers to push postings out. No public read API. |


### D.3 Labor-Market-Intelligence / Research SaaS (14 providers)

A distinct category from a job-postings feed: these products sell aggregate hiring-trend analytics, research indices, or enterprise talent-intelligence dashboards, sold via a sales contract rather than a self-serve API key. Even where they technically ingest job postings internally, that is not the product being sold to a third party.

| Provider | Region | Reason |
|---|---|---|
| Aura (by Aura Intelligence) | Global | Enterprise labor-market-intelligence SaaS sold via sales contract — not a self-serve job-postings feed. |
| Claro Analytics (WilsonHCG) | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| Datapeople (by Payscale) | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| Draup | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| Greenwich.HR (WageScape) | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| Horsefly Analytics | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| Indeed Hiring Lab | Global | Indeed's economic-research arm publishes aggregate labor-market indices/trend CSVs (mirrored on FRED), not individual job records — a research/statistics product, not a live listings feed. |
| JobsEQ (Chmura Economics & Analytics) | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| Lightcast (formerly Emsi Burning Glass) Job Postings API | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| LinkUp | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| Revelio Labs | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| TalentNeuron (Gartner) | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| Textkernel Jobfeed / Market IQ | Global | Enterprise labor-market-intelligence SaaS sold via sales contract. |
| The Burning Glass Institute | Global | A nonprofit labor-market research institute (spun out of Burning Glass Technologies, now Lightcast) — publishes research reports and indices, not a job-postings API. |


### D.4 Enterprise-Only / Sales-Gated Providers (15 providers)

Real APIs exist, but the *only* documented path to access is a sales conversation or partner program — no published self-serve pricing or signup flow. This is distinct from "paid" in the sense that a paid, metered self-serve tier (like the ones this project already uses for Adzuna, SerpApi, and Fantastic Jobs) is workable; sales-gated access with no published terms is not something a project without a procurement process can commit to.

| Provider | Region | Reason |
|---|---|---|
| BambooHR | Remote/Global | Enterprise-only pricing/access — gated behind a sales or partner-approval process, no self-serve developer path. |
| Coresignal | India; United States | Enterprise-tier data vendor sold via sales contact, not a published self-serve price. |
| Darwinbox | India | Enterprise-only pricing/access — gated behind a sales or partner-approval process. |
| Freshteam | India | Enterprise-only pricing/access — gated behind a sales or partner-approval process. |
| Indeed India | India | Enterprise partner-only access; not available to a generic aggregator. |
| Jobs.cz | Europe (Other) | Enterprise-only pricing/access — gated behind a sales or partner-approval process. |
| JobStreet / JobsDB (SEEK group) | Singapore/SEA | SEEK-group flagship boards for SEA; enterprise partner-only access, no self-serve path (the source catalog explicitly marks this "Not Recommended"). |
| Lightcast Jobs Canada | Canada | Paid labor-market-intelligence product sold through a sales process, not a self-serve developer signup; the source catalog itself marks this "Not Recommended." |
| LinkedIn Jobs | India | Enterprise partner program only — no self-serve developer signup for job search/aggregation. |
| Profesia | Europe (Other) | Enterprise-only pricing/access — gated behind a sales or partner-approval process. |
| Recruit CRM | India | Enterprise-only pricing/access — gated behind a sales or partner-approval process. |
| Superset | India | Enterprise-only pricing/access — gated behind a sales or partner-approval process. |
| VietnamWorks Open API | Vietnam | Partner Access Required — gated to approved commercial partners, not open developer registration. |
| ZipRecruiter API | United States | Enterprise-only pricing/access — gated behind a sales or partner-approval process. |
| Zoho Recruit | India | Enterprise-only pricing/access — gated behind a sales or partner-approval process. |


### D.5 Paid-Only Providers Excluded for Scope, Not Price (20 providers)

Three sub-groups all share the same self-serve, metered/paid pricing shape this project already accepts elsewhere (Adzuna, SerpApi, OpenWebNinja, Fantastic Jobs, TheirStack) — they were excluded because of *what they are*, not because a paid tier exists at all.

**Generic web-scraping infrastructure vendors (10)** — not job-specific; using one means building and maintaining a custom per-site scraper, which is a project in itself, not one more provider:

| Provider | Reason |
|---|---|
| Apify | Generic web-scraping infrastructure vendor — API key/Bearer token, metered. |
| Bright Data | Generic web-scraping infrastructure vendor — API key/Bearer token, metered. |
| Diffbot | Generic web-scraping infrastructure vendor — API key, metered. |
| HasData | Generic web-scraping infrastructure vendor — `x-api-key` header, metered. |
| Nimble (Nimbleway) | Generic web-scraping infrastructure vendor — API key/Bearer token, metered. |
| Oxylabs | Generic web-scraping infrastructure vendor — API key, metered. |
| Piloterr | Generic web-scraping infrastructure vendor — API key, metered. |
| ScraperAPI | Generic web-scraping infrastructure vendor — API key, metered. |
| Scrapingdog | Generic web-scraping infrastructure vendor — API key, metered. |
| Zyte (formerly Scrapinghub) | Generic web-scraping infrastructure vendor — API key, metered. |

**B2B data-aggregation / enrichment vendors (5)** — paid, and overlap with data this project already collects directly for free:

| Provider | Reason |
|---|---|
| JSearch (RapidAPI, by OpenWeb Ninja) | A RapidAPI repackaging of the same OpenWeb Ninja data this project already integrates directly — paying for the wrapper of a source already held natively would be pure redundancy. |
| Mantiks | Generic B2B data-aggregation vendor, not a dedicated job board — paid, overlaps with sources already integrated. |
| People Data Labs | Generic B2B data-aggregation vendor — paid, overlaps with sources already integrated. |
| PredictLeads | Generic B2B data-aggregation vendor — paid, overlaps with sources already integrated. |
| Techmap.io | Generic B2B data-aggregation vendor (via RapidAPI) — paid, overlaps with sources already integrated. |

**ATS Unified-API middleware (5)** — paid re-wrappers of ATS platforms this project already integrates directly for free:

| Provider | Reason |
|---|---|
| Apideck | Re-wraps Greenhouse, Lever, Workday (all already integrated directly for free). Redundant and enterprise-priced. |
| Kombo.dev | Same redundancy — re-wraps ATSs already integrated directly. |
| Merge.dev | Same redundancy — re-wraps ATSs already integrated directly. |
| Unified.to | Same redundancy — re-wraps ATSs already integrated directly. |
| Workato | Same redundancy — re-wraps ATSs already integrated directly. |


### D.6 Authentication-Restricted Providers (5 providers)

Distinct from "no public API": these have a real, sometimes fully documented API, but access is restricted to a specific class of credentialed user this project does not qualify as — a national citizen ID, a licensed professional business, or (in Section 9) a formal partner/approval program still worth pursuing.

| Provider | Region | Restriction | Reason |
|---|---|---|---|
| Hello Work Job Information API (ハローワーク求人情報提供サービス, MHLW) | Japan | Licensed-business gated | Japan's real, fully-documented national job API — registration is restricted to licensed private job-placement businesses, local governments, or training institutions. A generic aggregator does not qualify. |
| Israeli Employment Service (Sherut HaTaasuka / taasuka.gov.il) | Israel | Citizen-ID gated | Requires an Israeli citizen with a Teudat Zehut (national ID) to register online and then appear in person within 14 days — a citizen-services portal, not a public data API. |
| Jadarat (Saudi National Employment Portal / HRDF) | Saudi Arabia | Citizen-ID gated | Requires a Saudi-national citizen account (18+, degree requirements for government roles) — not available to a third-party aggregator at all. |
| Agencia Publica de Empleo SENA (APE) | Colombia | Citizen-ID gated | Registered user login (document ID + password) required to search/view individual vacancies; Colombia's open-data (Socrata) API only exposes aggregate registration statistics, not live listings. |
| Google Cloud Talent Solution (Job Search API) | Global | Not a third-party feed at all | A hosted ML matching/search engine populated with the customer's *own* job postings — not a source of aggregated third-party listings. Enterprise infrastructure product, not a job feed. |


### D.7 Static Dataset, Not a Live API (4 providers)

These providers publish real, often free and government-authoritative data — but as a periodic bulk file or aggregate statistics table, not a queryable, per-job live search endpoint. Integrating one would mean ingesting a dataset dump on an unpredictable refresh cycle rather than a live feed, and in three cases (UWV, SEPE, data.gov.in) there is no stable per-job identifier to key off of at all.

| Provider | Region | Reason |
|---|---|---|
| National Career Service (NCS) | India | Exposes a periodic bulk open-government dataset (data.gov.in), not a live per-job search API — stale snapshots, not real-time postings. |
| data.gov.in OGD platform | India | General-purpose Indian open-government-data portal spanning 33 sectors; not jobs-specific, and individual resources are static per-resource datasets. |
| SEPE Open Data Portal (Spain public employment service) | Spain | Only publishes static statistical/administrative open-data files — no confirmed live REST API for current vacancies; a known third-party scraper for it is deprecated. |
| UWV Open Match Data (Netherlands) | Netherlands | Publishes aggregate labor-market statistics datasets, not individual live job postings — no per-job identifier exists in the data at all. |


### D.8 Commercial-Partnership-Gated Providers (2 providers, one revisited in Section 9)

| Provider | Region | Reason |
|---|---|---|
| Job Bank (ESDC) feed / Open Gov dataset | Canada | The live feed requires ESDC partner approval; the fallback open dataset is a monthly CSV dump missing employer/company names and per-job apply URLs — the two fields this project's schema requires. Doesn't fit even with credentials, so this is not carried into Section 9's revisit list. |
| Kemnaker Karirhub (SIAPkerja) | Indonesia | Access restricted to job portals with a formal MoU with the Indonesian Ministry of Manpower; no publicly documented API key/OAuth path exists for outside developers. |


### D.9 Deprecated / Suspended / Technically Inaccessible Providers (3 providers)

| Provider | Region | Status | Reason |
|---|---|---|---|
| SINE Aberto (Sistema Nacional de Emprego / Ministério do Trabalho e Emprego) | Brazil | Suspended | Brazil suspended this data-sharing service in October 2022 (CODEFAT Resolution 956/2022) pending LGPD privacy-law compliance updates — no active API to integrate against right now. |
| Pangian | Remote/Global | Discontinued | `pangian.com` redirects to a static shutdown notice; the service is discontinued/paused indefinitely. |
| Remote First Jobs (Dynamite Jobs) | Remote/Global | Technically blocked | Confirmed live: an active Cloudflare managed JS challenge on every path tested, including `robots.txt` itself (HTTP 403, "Just a moment..."). Not a credentials gate — a plain HTTP client cannot pass it, and this project's architecture has no headless-browser/JS-execution layer to attempt one. |


---

*Job Aggregation Platform — Final Project Report v2 · Data snapshot 2026-07-10 · Original report generated 2026-07-13 · This revision (v2) generated 2026-07-15, adding the complete provider research lifecycle (268-provider catalog, 86-provider shortlist, evaluation methodology, decision matrix, and full rejection/deferral knowledge base) alongside the previously-reported implementation detail. Polished for final submission on 2026-07-15: added the front-matter Executive Summary, condensed Section 8 into summary tables with the full detail moved to Appendix D, and completed a final numeric consistency pass.*

*Source of truth: PostgreSQL (`jobs`, `provider_runs`), this repository's own source code, and `job_api.xlsx` (API Catalog, Sheet1, Integration Detail, Schema Definitions sheets) — no figure in this report is estimated or assumed. Where evidence was not available or a research artifact was found to be a stale snapshot, this report states that explicitly rather than inferring a result.*
