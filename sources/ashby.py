"""
Ashby Job Posting API source.

API docs: https://developers.ashbyhq.com/docs/public-job-posting-api

Endpoint: GET https://api.ashbyhq.com/posting-api/job-board/{board_name}
No authentication is required for this endpoint (confirmed live). An
optional `includeCompensation=true` query param adds salary data to the
response - not needed for this project's schema, so it's left off.

Ashby is company-based rather than a single global index: each company
publishes its postings under its own "board name" (slug), same shape as
Greenhouse/Lever. The list of companies to fetch is COMPANY_BOARDS below -
adding a new company later only requires adding its slug/name pair to that
dict; fetch_raw() already iterates over it automatically, no logic changes
needed.

Like Greenhouse, the API returns a company's entire job list in a single
response - no page/offset/cursor params are documented or exist, confirmed
live (one request returned every job for every company tested here,
largest being 593). So this is a single-shot fetch per company.

Each company is fetched independently, and a failure fetching one company
(bad slug, network error, etc.) is caught and logged so the remaining
companies still get processed - the same per-company fault isolation used
in greenhouse.py.

Unlike Greenhouse (which returns `company_name` per job), Ashby's job
objects carry no company display name at all - the same gap Lever has.
So fetch_raw() tags each raw job with the board slug it came from, and
COMPANY_BOARDS maps that slug directly to a display name (rather than
deriving one via string transforms like lever.py's _company_name_from_slug,
since Ashby slugs are inconsistently stylized - e.g. "elevenlabs" ->
"ElevenLabs", "moderntreasury" -> "Modern Treasury" - and no mechanical
rule gets both right).

`isRemote` is a genuine boolean field on every job (confirmed via live
data across every company tested here), so - like Lever's `workplaceType`
- `remote` is read directly from it rather than a keyword heuristic.

Every company slug below was confirmed live against the real API before
being added: ~350 candidate slugs were tried this session and only the
102 that returned HTTP 200 with at least one active job were kept. Ashby's
customer base skews toward growth-stage AI/SaaS/FinTech companies rather
than large traditional enterprises, so coverage is thinner in categories
like manufacturing, logistics, and consulting, where no large-volume
public Ashby board could be verified live.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://api.ashbyhq.com/posting-api/job-board"

# Company board slugs mapped to display names. Every slug below was
# confirmed live against the real API before being added. Add a new
# company by adding a "slug": "Display Name" entry here; no other code
# changes are needed - fetch_raw() iterates over this dict automatically.
COMPANY_BOARDS = {
    # AI
    "harvey": "Harvey",
    "sierra": "Sierra",
    "cohere": "Cohere",
    "langchain": "LangChain",
    "cerebras": "Cerebras",
    "perplexity": "Perplexity",
    "synthesia": "Synthesia",
    "deepgram": "Deepgram",
    "character": "Character.AI",
    "extropic": "Extropic",
    "poolside": "Poolside",
    "cartesia": "Cartesia",
    "pika": "Pika",
    "ideogram": "Ideogram",
    "bland": "Bland",
    "vapi": "Vapi",
    "tavus": "Tavus",
    "writer": "Writer",
    "braintrust": "Braintrust",
    "mercor": "Mercor",
    "replit": "Replit",
    "cursor": "Cursor",
    "elevenlabs": "ElevenLabs",

    # SaaS
    "notion": "Notion",
    "linear": "Linear",
    "attio": "Attio",
    "miro": "Miro",
    "zapier": "Zapier",
    "posthog": "PostHog",
    "sanity": "Sanity",
    "gitbook": "GitBook",
    "vitally": "Vitally",
    "metaview": "Metaview",
    "orb": "Orb",
    "workos": "WorkOS",
    "knock": "Knock",
    "resend": "Resend",
    "doppler": "Doppler",
    "hightouch": "Hightouch",
    "replo": "Replo",
    "zip": "Zip",
    "runway": "Runway",
    "ashby": "Ashby",

    # Cloud
    "supabase": "Supabase",
    "render": "Render",
    "railway": "Railway",
    "modal": "Modal",
    "baseten": "Baseten",
    "pinecone": "Pinecone",
    "airbyte": "Airbyte",
    "temporal": "Temporal",
    "neon": "Neon",
    "confluent": "Confluent",
    "snowflake": "Snowflake",

    # Cybersecurity
    "socket": "Socket",
    "semgrep": "Semgrep",
    "1password": "1Password",
    "vanta": "Vanta",
    "drata": "Drata",
    "materialsecurity": "Material Security",
    "stytch": "Stytch",
    "hackerone": "HackerOne",
    "persona": "Persona",

    # FinTech
    "ramp": "Ramp",
    "airwallex": "Airwallex",
    "wealthsimple": "Wealthsimple",
    "column": "Column",
    "unit": "Unit",
    "highbeam": "Highbeam",
    "moderntreasury": "Modern Treasury",
    "parafin": "Parafin",
    "sardine": "Sardine",
    "novo": "Novo",
    "float": "Float",
    "synctera": "Synctera",
    "middesk": "Middesk",

    # Banking
    "cedar": "Cedar",
    "levels": "Levels",

    # Insurance
    "lemonade": "Lemonade",
    "coverdash": "Coverdash",

    # Healthcare
    "headway": "Headway",
    "abridge": "Abridge",
    "overjet": "Overjet",
    "eightsleep": "Eight Sleep",
    "superpower": "Superpower",

    # Retail
    "vetcove": "Vetcove",

    # Manufacturing / Defense / Robotics
    "saronic": "Saronic",
    "skydio": "Skydio",
    "serverobotics": "Serve Robotics",
    "improbable": "Improbable",

    # Logistics
    "genies": "Genies",

    # Education
    "handshake": "Handshake",
    "multiverse": "Multiverse",
    "speak": "Speak",

    # Media
    "substack": "Substack",

    # Other (crypto / web3)
    "alchemy": "Alchemy",
    "uniswap": "Uniswap Labs",
    "opensea": "OpenSea",
    "mystenlabs": "Mysten Labs",
    "dune": "Dune",

    # Other (telecom)
    "hiya": "Hiya",

    # Other (SaaS - misc)
    "tempo": "Tempo",
}

REQUEST_TIMEOUT = 30


class AshbySource(BaseJobSource):
    name = "ashby"

    def fetch_raw(self):
        """Fetch every configured company's full job list from the Ashby Job Posting API."""
        jobs = []

        for slug in COMPANY_BOARDS:
            try:
                response = request_with_retry(
                    requests.get,
                    f"{API_URL}/{slug}",
                    timeout=REQUEST_TIMEOUT,
                )
                payload = response.json()
            except requests.RequestException as exc:
                print(f"[{self.name}] skipped company '{slug}': {exc}")
                continue

            # Ashby's job objects don't carry a company display name, so
            # the board slug is stashed on each raw record for
            # normalize() to look up in COMPANY_BOARDS.
            page_jobs = payload.get("jobs", [])
            for job in page_jobs:
                job["_company_slug"] = slug
            jobs.extend(page_jobs)

        return jobs

    def normalize(self, raw_job):
        """Map an Ashby job record onto the project's standard schema."""
        tags = dedupe_tags(
            [raw_job["department"]] if raw_job.get("department") else None,
            [raw_job["team"]] if raw_job.get("team") else None,
            [raw_job["employmentType"]] if raw_job.get("employmentType") else None,
        )

        posted = iso_string_to_date(raw_job.get("publishedAt"))

        return {
            "title": raw_job.get("title", ""),
            "company": COMPANY_BOARDS.get(raw_job.get("_company_slug", ""), ""),
            "location": raw_job.get("location") or "Unknown",
            "url": raw_job.get("jobUrl", ""),
            "tags": tags,
            "remote": bool(raw_job.get("isRemote")),
            "posted": posted,
        }
