# Job Board Aggregator

## Project Overview

This project aggregates job postings from multiple public job APIs into a single, normalized dataset and presents them through a fast, searchable frontend. A modular Python pipeline fetches jobs from each source, maps them onto one common schema, deduplicates and validates the result, and writes it to `jobs.json`. A plain HTML/CSS/JavaScript frontend loads that dataset and lets users search, filter, and sort the listings entirely client-side.

The project now aggregates jobs from every implemented provider - 20 sources in total, spanning no-auth public APIs, API-key-based job search APIs, and ATS (applicant tracking system) job board integrations - through the same modular pipeline and the same common schema. The latest full run produced 155,697 unique, normalized jobs in `jobs.json`.

## Features

- Aggregates jobs from multiple public APIs
- Normalizes all jobs into one common schema
- Deduplicates jobs
- Schema validation
- Responsive job board UI
- Live search
- Dynamic location filter
- Sort by Newest
- Sort by Title A–Z
- Debounced search
- Loading state
- Error state
- Job count
- Clear Filters

## APIs Used

### Public APIs

No authentication required.

- [Arbeitnow](https://www.arbeitnow.com/api/job-board-api)
- [Himalayas](https://himalayas.app/jobs/api)
- [RemoteOK](https://remoteok.com/api)
- [Jobicy](https://jobicy.com/api/v2/remote-jobs)
- [The Muse](https://www.themuse.com/api/public/jobs)
- [Bundesagentur für Arbeit](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs) (German Federal Employment Agency)

### API Key Providers

Require credentials configured via `.env` (see [Environment Variables](#environment-variables)).

- [Jooble](https://jooble.org/api/about)
- [USAJOBS](https://developer.usajobs.gov/) (U.S. federal government job postings)
- [Adzuna](https://developer.adzuna.com/)
- [Reed](https://www.reed.co.uk/developers) (UK job board)
- [SerpApi](https://serpapi.com/google-jobs-api) (Google Jobs)
- [OpenWeb Ninja](https://www.openwebninja.com/api/jsearch) (JSearch)
- [CareerJet](https://www.careerjet.com/partners/api/)
- [TheirStack](https://theirstack.com/en/docs/api-reference/jobs/search_jobs_v1)

### ATS Providers

Public, no-auth job board endpoints hosted by each applicant tracking system, fetched per company.

- [Greenhouse](https://developers.greenhouse.io/job-board.html)
- [Lever](https://github.com/lever/postings-api)
- [Ashby](https://developers.ashbyhq.com/docs/public-job-posting-api)
- [SmartRecruiters](https://developers.smartrecruiters.com/docs/posting-api)
- [Workable](https://help.workable.com/hc/en-us/articles/115012771647-Using-the-Workable-API-to-create-a-careers-page)
- [Teamtailor](https://docs.teamtailor.com/)

The source architecture is modular: each provider is a self-contained module implementing a shared interface, so additional providers can be added later without changing the aggregation pipeline or the frontend. Greenhouse, Lever, Ashby, SmartRecruiters, Workable, and Teamtailor were all added exactly this way.

## Project Structure

```
JobBoard/
├── sources/                 # One module per job API/ATS integration
│   ├── __init__.py          # Source registry
│   ├── base.py               # Shared BaseJobSource interface
│   ├── config.py              # Loads .env and exposes Phase 2 API credentials
│   ├── utils.py               # Shared normalization helpers
│   ├── arbeitnow.py           # Phase 1
│   ├── himalayas.py           # Phase 1
│   ├── remoteok.py            # Phase 1
│   ├── jobicy.py              # Phase 1
│   ├── themuse.py             # Phase 1
│   ├── bundesagentur.py       # Phase 1
│   ├── jooble.py              # Phase 2
│   ├── usajobs.py             # Phase 2
│   ├── adzuna.py              # Phase 2
│   ├── reed.py                # Phase 2
│   ├── serpapi.py             # Phase 2
│   ├── openwebninja.py        # Phase 2
│   ├── careerjet.py           # Phase 2
│   ├── theirstack.py          # Phase 2
│   ├── greenhouse.py          # Phase 3 (ATS)
│   ├── lever.py               # Phase 3 (ATS)
│   ├── ashby.py               # Phase 3 (ATS)
│   ├── smartrecruiters.py     # Phase 3 (ATS)
│   ├── workable.py            # Phase 3 (ATS)
│   └── teamtailor.py          # Phase 3 (ATS)
├── jobs.py                  # Aggregation entry point (fetch, normalize, dedupe, save)
├── jobs.json                # Aggregated, normalized job dataset (generated)
├── index.html                # Frontend page shell
├── script.js                 # Frontend logic (fetch, filter, sort, render)
├── style.css                  # Frontend styling
├── requirements.txt           # Python dependencies
├── .env.example                # Template for Phase 2 API credentials
├── aggregation_summary.md      # Aggregation report (Phase 1 + Phase 2)
└── README.md                    # This file
```

## Technologies Used

- Python 3
- HTML5
- CSS3
- Vanilla JavaScript
- Playwright (testing)

## Installation

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Phase 2 sources need API credentials. Copy the example environment file and fill in whichever credentials you have:

```bash
cp .env.example .env
```

Then edit `.env` with your values. See [Environment Variables](#environment-variables) below for what each one is for. Phase 1 sources need no configuration at all; any Phase 2 source with a missing or empty credential is skipped gracefully rather than causing an error.

## Environment Variables

`.env` (git-ignored, never committed) holds credentials for the Phase 2 providers, loaded automatically via `python-dotenv` when `jobs.py` runs. None are required to run the project - each corresponds to one optional Phase 2 source. The Phase 1 sources and all Phase 3 ATS providers (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Teamtailor) use public, no-auth endpoints and need no entry in `.env` at all.

| Variable | Used by |
|---|---|
| `USAJOBS_API_KEY` | USAJOBS |
| `USAJOBS_EMAIL` | USAJOBS |
| `ADZUNA_APP_ID` | Adzuna |
| `ADZUNA_APP_KEY` | Adzuna |
| `JOOBLE_API_KEY` | Jooble |
| `REED_API_KEY` | Reed |
| `SERPAPI_API_KEY` | SerpApi |
| `THEIRSTACK_API_KEY` | TheirStack |
| `OPENWEBNINJA_API_KEY` | OpenWeb Ninja |
| `CAREERJET_API_KEY` | CareerJet |

## Running the Backend

```bash
python jobs.py
```

This fetches jobs from every registered source, normalizes, deduplicates, and validates them, and writes the result to `jobs.json`.

## Running the Frontend

The frontend loads `jobs.json` via `fetch()`, which requires the page to be served over HTTP rather than opened directly as a `file://` URL.

```bash
python -m http.server 8000
```

Then open:

```
http://localhost:8000
```

## Job Schema

Every job, regardless of source, is normalized into the same schema:

```json
{
  "title": "",
  "company": "",
  "location": "",
  "url": "",
  "tags": [],
  "remote": true,
  "posted": ""
}
```

| Field      | Type      | Description                                  |
|------------|-----------|-----------------------------------------------|
| `title`    | string    | Job title                                     |
| `company`  | string    | Hiring company or organization                |
| `location` | string    | Human-readable location                       |
| `url`      | string    | Link to the original job posting              |
| `tags`     | string[]  | Categories, skills, or other descriptive tags |
| `remote`   | boolean   | Whether the position is remote                |
| `posted`   | string    | Posting date in `YYYY-MM-DD` format           |

## Testing

The frontend was manually tested throughout development and automatically tested using Playwright, covering search, location filtering, sorting, filter combinations, debounced input, Clear Filters, job count updates, loading state, error state, and console-error-free operation.

Every provider - Phase 1, Phase 2, and Phase 3 alike - was also tested in isolation with real API requests against its live endpoint before being wired into the registry: Phase 2 sources verified successful fetches, correct normalization, and graceful skipping when credentials are missing; Phase 3 ATS providers verified correct fetching and normalization against each company board confirmed live during research. All 20 sources were then verified together through the complete aggregation pipeline (`python jobs.py`), confirming successful fetch, normalization, deduplication, and schema validation end-to-end.

## Future Improvements

- Searchable location dropdown
- Pagination / virtualization for extremely large datasets

## Project Status

All provider integrations are complete: Phase 1 (no-auth providers), Phase 2 (API-key providers), and Phase 3 (ATS providers - Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Teamtailor), for 20 sources total, alongside Frontend Milestones 2–5.
