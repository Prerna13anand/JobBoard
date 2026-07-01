# Job Board Aggregator

## Project Overview

This project aggregates job postings from multiple public job APIs into a single, normalized dataset and presents them through a fast, searchable frontend. A modular Python pipeline fetches jobs from each source, maps them onto one common schema, deduplicates and validates the result, and writes it to `jobs.json`. A plain HTML/CSS/JavaScript frontend loads that dataset and lets users search, filter, and sort the listings entirely client-side.

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

- [Arbeitnow](https://www.arbeitnow.com/api/job-board-api)
- [Himalayas](https://himalayas.app/jobs/api)
- [RemoteOK](https://remoteok.com/api)
- [Jobicy](https://jobicy.com/api/v2/remote-jobs)
- [The Muse](https://www.themuse.com/api/public/jobs)
- [Bundesagentur für Arbeit](https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs) (German Federal Employment Agency)

The source architecture is modular: each provider is a self-contained module implementing a shared interface, so additional providers such as Greenhouse, Lever, Jooble, Adzuna, Reed, and others can be added later without changing the aggregation pipeline or the frontend.

## Project Structure

```
JobBoard/
├── sources/                 # One module per job API/ATS integration
│   ├── __init__.py          # Source registry
│   ├── base.py               # Shared BaseJobSource interface
│   ├── utils.py               # Shared normalization helpers
│   ├── arbeitnow.py
│   ├── himalayas.py
│   ├── remoteok.py
│   ├── jobicy.py
│   ├── themuse.py
│   └── bundesagentur.py
├── jobs.py                  # Aggregation entry point (fetch, normalize, dedupe, save)
├── jobs.json                # Aggregated, normalized job dataset (generated)
├── index.html                # Frontend page shell
├── script.js                 # Frontend logic (fetch, filter, sort, render)
├── style.css                  # Frontend styling
├── requirements.txt           # Python dependencies
├── aggregation_summary.md      # Phase 1 aggregation report
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

## Future Improvements

- Greenhouse integration
- Lever integration
- API-key providers
- Searchable location dropdown
- Pagination / virtualization for extremely large datasets

## Project Status

Phase 1 (backend aggregation) and Frontend Milestones 2–5 are complete.
