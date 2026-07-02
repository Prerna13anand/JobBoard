# Job Board Aggregator

## Project Overview

This project aggregates job postings from multiple public job APIs into a single, normalized dataset and presents them through a fast, searchable frontend. A modular Python pipeline fetches jobs from each source, maps them onto one common schema, deduplicates and validates the result, and writes it to `jobs.json`. A plain HTML/CSS/JavaScript frontend loads that dataset and lets users search, filter, and sort the listings entirely client-side.

The project now aggregates jobs from every Phase 1 (no-auth) and Phase 2 (API-key) provider it integrates - 14 sources in total - through the same modular pipeline and the same common schema.

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

### Phase 1 - No-auth providers

- [Arbeitnow](https://www.arbeitnow.com/api/job-board-api)
- [Himalayas](https://himalayas.app/jobs/api)
- [RemoteOK](https://remoteok.com/api)
- [Jobicy](https://jobicy.com/api/v2/remote-jobs)
- [The Muse](https://www.themuse.com/api/public/jobs)
- [Bundesagentur für Arbeit](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs) (German Federal Employment Agency)

### Phase 2 - API-key providers

- [Jooble](https://jooble.org/api/about)
- [USAJOBS](https://developer.usajobs.gov/) (U.S. federal government job postings)
- [Adzuna](https://developer.adzuna.com/)
- [Reed](https://www.reed.co.uk/developers) (UK job board)
- [SerpApi](https://serpapi.com/google-jobs-api) (Google Jobs)
- [OpenWeb Ninja](https://www.openwebninja.com/api/jsearch) (JSearch)
- [CareerJet](https://www.careerjet.com/partners/api/)
- [TheirStack](https://theirstack.com/en/docs/api-reference/jobs/search_jobs_v1)

The source architecture is modular: each provider is a self-contained module implementing a shared interface, so additional providers such as Greenhouse, Lever, and others can be added later without changing the aggregation pipeline or the frontend.

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
│   └── theirstack.py          # Phase 2
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

`.env` (git-ignored, never committed) holds credentials for the Phase 2 providers, loaded automatically via `python-dotenv` when `jobs.py` runs. None are required to run the project - each corresponds to one optional Phase 2 source.

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

Each Phase 2 source was also tested in isolation with real API requests against its live endpoint (using credentials from `.env`), verifying successful fetches, correct normalization against the shared schema, and graceful skipping when its credentials are missing, before being run through the full aggregation pipeline.

## Future Improvements

- Greenhouse integration
- Lever integration
- Searchable location dropdown
- Pagination / virtualization for extremely large datasets

## Project Status

Phase 1 (no-auth providers) and Phase 2 (API-key providers) backend aggregation are complete, alongside Frontend Milestones 2–5.
