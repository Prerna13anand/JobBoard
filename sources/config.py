"""
Centralized credential configuration for Phase 2 (API-key-based) job sources.

None of the Phase 1 sources (Arbeitnow, Himalayas, RemoteOK, Jobicy, The
Muse, Bundesagentur fur Arbeit) need an API key. This module exists so
that every Phase 2 source added from here on reads its credentials from
environment variables - populated from a local .env file via
python-dotenv, if one exists - instead of hardcoding secrets in source
code.

Usage in a future source module:

    from .config import ADZUNA_APP_ID, ADZUNA_APP_KEY

Setup: copy .env.example to .env and fill in whichever credentials you
have. .env is git-ignored and must never be committed.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# USAJOBS - https://developer.usajobs.gov/
USAJOBS_API_KEY = os.getenv("USAJOBS_API_KEY")
USAJOBS_EMAIL = os.getenv("USAJOBS_EMAIL")

# Adzuna - https://developer.adzuna.com/
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Jooble - https://jooble.org/api/about
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")

# Reed - https://www.reed.co.uk/developers
REED_API_KEY = os.getenv("REED_API_KEY")

# SerpApi - https://serpapi.com/
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# TheirStack - https://theirstack.com/
THEIRSTACK_API_KEY = os.getenv("THEIRSTACK_API_KEY")

# OpenWebNinja - https://www.openwebninja.com/
OPENWEBNINJA_API_KEY = os.getenv("OPENWEBNINJA_API_KEY")

# CareerJet - https://www.careerjet.com/partners/api/
CAREERJET_API_KEY = os.getenv("CAREERJET_API_KEY")

# CareerOneStop / NLx - https://www.careeronestop.org/Developers/WebAPI/web-api.aspx
CAREERONESTOP_USER_ID = os.getenv("CAREERONESTOP_USER_ID")
CAREERONESTOP_API_TOKEN = os.getenv("CAREERONESTOP_API_TOKEN")

# Findwork.dev - https://findwork.dev/developers/
FINDWORK_API_KEY = os.getenv("FINDWORK_API_KEY")

# France Travail - https://francetravail.io/produits-partages/catalogue/offres-emploi
FRANCETRAVAIL_CLIENT_ID = os.getenv("FRANCETRAVAIL_CLIENT_ID")
FRANCETRAVAIL_CLIENT_SECRET = os.getenv("FRANCETRAVAIL_CLIENT_SECRET")

# Trade Me Jobs - https://developer.trademe.co.nz/
TRADEME_CONSUMER_KEY = os.getenv("TRADEME_CONSUMER_KEY")
TRADEME_CONSUMER_SECRET = os.getenv("TRADEME_CONSUMER_SECRET")

# Fantastic.jobs - https://developer.fantastic.jobs/
FANTASTICJOBS_API_KEY = os.getenv("FANTASTICJOBS_API_KEY")
