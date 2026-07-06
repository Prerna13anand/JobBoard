# Job API/ATS Catalog — Schema Definition

Source: `final_project_report.pdf` (Job Aggregation Platform Final Project Report, July 6, 2026), backed by `research/api_analysis.md` and `reports/analytics_summary.md`.

Grain: **one row per (API/ATS, Region) pair.** An API that serves multiple regions (e.g. Adzuna, SmartRecruiters) appears as multiple rows — one per region it has a meaningful presence in — so each row can be filtered/sorted independently by region.

## Columns

| # | Column | Type | Definition | Source |
|---|--------|------|------------|--------|
| 1 | **API/ATS Name** | Text | Name of the provider (e.g. "Adzuna", "Greenhouse", "USAJOBS"). Repeats across rows for multi-region providers. | Report §5, §24 |
| 2 | **Region** | Text (single value) | The specific region this row describes: United States, Canada, United Kingdom, Germany, Europe (Other), India, Singapore/SEA, LATAM, Remote/Global, or Other/Unclassified. | Report §6, §24 Part 2 (Provider × Region Matrix) |
| 3 | **Type** | Categorical | The provider's structural category: `Public`, `Government`, `Commercial Aggregator`, or `ATS`. Distinct from pricing — describes *what kind* of source it is. | Report §9, §16, §24 Part 1 |
| 4 | **Access Model** | Categorical | Pricing tier: `Free`, `Free tier + Paid (metered)`, `Paid`, or `Enterprise`. | Report §16, §24 Part 1 |
| 5 | **Cost Details** | Free text | Specific pricing where known, e.g. "Free (no auth)", "Free tier / paid metered", "~$1 per 1,000 jobs", "Paid, from $49/mo". Blank/"—" if not applicable (fully free) or unpublished. | Report §16 |
| 6 | **Auth Required** | Text | Whether the API requires authentication and the method: e.g. "No", "Yes (API key)", "Yes (OAuth2)", "Yes (HTTP Basic)", "Yes (Bearer token)". | Report §24 Part 1 |
| 7 | **Primary Industry/Category** | Text (top skew) | The dominant job category/industry this provider's postings skew toward in this region, e.g. "Tech/AI-SaaS", "Government/Healthcare", "Retail/Operations", "Sales". Reflects which companies use that source, not a strict industry taxonomy — treat as a skew signal, not an exhaustive tag. | Report §24 Part 3 (Provider × Category Matrix) |
| 8 | **Remote %** | Percentage | Share of this provider's jobs marked remote (dataset-wide figure, not region-specific unless noted). | Report §24 Part 1 |
| 9 | **Freshness (≤30 days %)** | Percentage | Share of this provider's jobs that were posted within 30 days of the 2026-07-03 collection date — the "how current is this source" filter. | Report §7, §24 Part 1 |
| 10 | **Estimated Jobs (this region)** | Number | Job count estimated as (provider's total jobs) × (region's share of that provider's jobs), per the Provider × Region Matrix. Rounded; treat as directional, not exact. | Derived: Report §24 Part 1 × Part 2 |
| 11 | **% of Provider's Total Jobs** | Percentage | What share of this provider's overall job volume comes from this region (row-normalized in the source matrix: High ≥40%, Medium 15–39%, Low 5–14%, Minimal 1–4%, None <1%). | Report §24 Part 2 |
| 12 | **Limitations / Rate Limits** | Free text | Pagination caps, result-window ceilings, or query quotas, e.g. "Hard 10,000 result window", "Free-tier daily cap; ≤50/page", "Budget-bound: ~2,500/mo". | Report §12, §16, §17 |
| 13 | **Docs Available** | Yes/No | Whether the provider publishes usable API documentation. | Report §16 |

## Notes on interpretation

- **Region rows with ~0% share are omitted.** A provider only gets a row for a region if it has a non-trivial (>0%) presence there, per the Provider × Region Matrix — otherwise the sheet would carry hundreds of meaningless zero-rows.
- **"Estimated Jobs (this region)"** is a derived figure (total × row %), not a directly reported per-region count for most providers — exceptions are the four single-region anchors (USAJOBS/US, Bundesagentur/Germany, Reed/UK — each ~100% one region) where the total *is* the regional count.
- **Primary Industry/Category** is a skew, not a hard filter boundary — e.g. Greenhouse is tagged "Tech/AI-SaaS" because its curated company list is AI/SaaS-heavy, not because the API itself restricts to tech postings.
- Scope is the **20 currently-integrated providers only** (not the ~15 additional recommended-but-unintegrated APIs from Report §16/§18).

## Filterable dimensions this schema supports

Region · Industry/Category skew · Freshness (recent vs. stale) · Type (public/government/commercial/ATS) · Access Model (free/paid) · Remote-friendliness · Cost structure
