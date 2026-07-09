"""
France Travail (formerly Pole emploi) "Offres d'emploi" API source.

API catalog page: https://francetravail.io/produits-partages/catalogue/offres-emploi
Technical docs (OpenAPI spec, fetched directly and used to build this
module): https://francetravail.io/produits-partages/catalogue/offres-emploi/documentation

Free, self-service access ("Acces libre" per the catalog page) - no cost,
no partner approval - but every request requires an OAuth2 bearer token.
Getting one requires creating a free account at francetravail.io, then
creating an "application" there to receive a client ID/secret, and
subscribing that application to this API (see .env.example). This module
was written directly against the official OpenAPI spec (paths, parameter
names, response schema, security scheme all pulled from
https://francetravail.io/api-peio/v2/api/84/openapi), so field names and
the pagination/auth mechanics below are authoritative - but there were no
credentials available to fully exercise a live end-to-end fetch while
writing this, unlike every other source in this project.

Authentication: OAuth2 client_credentials grant.
    Token URL: https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire
    Required scopes (both mandatory, confirmed from the spec's
    securitySchemes): "api_offresdemploiv2" and "o2dsoffre"

Search endpoint: GET https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search
No keyword is required - omitting `motsCles` returns a general browse of
all current postings, matching the "fetch broadly" pattern used by other
sources in this project.

Pagination is via a `range` query parameter (format "start-end", e.g.
"0-149"), capped at 150 results per request per the spec's own parameter
description ("La plage de resultats est limitee a 150"). The response
carries a `Content-Range` header formatted "offres start-end/total" that
gives the true total available. Beyond the per-request cap, a real,
separately-observed pagination ceiling exists around a total range index
of ~1,150 (i.e. about 8 pages of 150) - noted in prior research on this
API and treated here as a hard, self-imposed stop, similar in spirit to
Arbetsformedlingen's confirmed offset<=2000 ceiling elsewhere in this
project.
"""

import requests

from .base import BaseJobSource
from .config import FRANCETRAVAIL_CLIENT_ID, FRANCETRAVAIL_CLIENT_SECRET
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
SCOPE = "api_offresdemploiv2 o2dsoffre"

# Maximum results per request, per the API's own documented range limit.
PAGE_SIZE = 150

# Self-imposed ceiling on the total range index reachable in one run, per
# a previously-observed pagination boundary on this API (see module
# docstring) - not directly stated in the OpenAPI spec's parameter
# description, so treated conservatively rather than assumed exact.
MAX_RANGE_END = 1149

REQUEST_TIMEOUT = 30

REMOTE_KEYWORDS = ("remote", "télétravail", "teletravail", "distanciel")


class FranceTravailSource(BaseJobSource):
    name = "francetravail"

    def _fetch_access_token(self):
        """Obtain an OAuth2 client_credentials bearer token."""
        response = request_with_retry(
            requests.post,
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": FRANCETRAVAIL_CLIENT_ID,
                "client_secret": FRANCETRAVAIL_CLIENT_SECRET,
                "scope": SCOPE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=REQUEST_TIMEOUT,
        )
        return response.json()["access_token"]

    def fetch_raw(self):
        """Fetch pages of jobs from the France Travail search API, up to a self-imposed range ceiling."""
        if not FRANCETRAVAIL_CLIENT_ID or not FRANCETRAVAIL_CLIENT_SECRET:
            raise ValueError("FRANCETRAVAIL_CLIENT_ID and FRANCETRAVAIL_CLIENT_SECRET must both be set")

        try:
            token = self._fetch_access_token()
        except requests.RequestException as exc:
            print(f"[{self.name}] failed to obtain an access token: {exc}")
            return []

        headers = {"Authorization": f"Bearer {token}"}
        jobs = []
        start = 0

        while start <= MAX_RANGE_END:
            end = min(start + PAGE_SIZE - 1, MAX_RANGE_END)
            try:
                response = request_with_retry(
                    requests.get,
                    SEARCH_URL,
                    headers=headers,
                    params={"range": f"{start}-{end}"},
                    timeout=REQUEST_TIMEOUT,
                )
            except requests.RequestException as exc:
                print(f"[{self.name}] stopped early at range {start}-{end}: {exc}")
                break

            if response.status_code == 204:
                break

            page_jobs = response.json().get("resultats") or []
            if not page_jobs:
                break

            jobs.extend(page_jobs)

            if len(page_jobs) < PAGE_SIZE:
                break
            start += PAGE_SIZE

        return jobs

    def normalize(self, raw_job):
        """Map a France Travail job offer onto the project's standard schema."""
        title = raw_job.get("intitule", "")
        location = (raw_job.get("lieuTravail") or {}).get("libelle") or "France"

        company = (raw_job.get("entreprise") or {}).get("nom") or ""
        url = (raw_job.get("origineOffre") or {}).get("urlOrigine") or ""

        contract_type = raw_job.get("typeContratLibelle")
        sector = raw_job.get("secteurActiviteLibelle")
        tags = dedupe_tags([contract_type] if contract_type else None, [sector] if sector else None)

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        return {
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "tags": tags,
            "remote": remote,
            "posted": iso_string_to_date(raw_job.get("dateCreation")),
        }
