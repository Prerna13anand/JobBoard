"""
Greenhouse Job Board API source.

API docs: https://developers.greenhouse.io/job-board.html

Endpoint: GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
No authentication is required for this endpoint. `content=true` is passed
to also receive `departments` (used for tags) and the full job
description - this costs nothing extra and needs no auth either.

Greenhouse is company-based rather than a single global index: each
company runs its own job board under its own "board token" (slug). The
list of companies to fetch is COMPANY_SLUGS below - adding a new company
later only requires adding its slug to that list; fetch_raw() already
iterates over it automatically, no logic changes needed.

The API returns a company's entire job list in a single response - no
page/offset/cursor params are documented or needed, confirmed live (one
request returned all jobs for every company tested here, largest being
491). So, like RemoteOK/Jobicy, this is a single-shot fetch per company
rather than a paginated one.

Each company is fetched independently, and a failure fetching one company
(bad slug, network error, etc.) is caught and logged so the remaining
companies still get processed - the same per-item fault isolation already
used for per-page failures in bundesagentur.py, applied per-company here.

`company_name` is provided directly by the API, so no manual slug-to-
display-name mapping is needed. There is no dedicated remote flag, so -
as with Jooble/Bundesagentur/Adzuna/Reed/CareerJet - remote-friendly
postings are detected via keyword.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://boards-api.greenhouse.io/v1/boards"

# Company board tokens to fetch. Every slug below was confirmed live
# against the real API before being added (many other well-known names,
# e.g. "doordash", "notion", "shopify", "salesforce", "openai", no longer
# run a public Greenhouse board under an obvious slug, or 404 outright).
# Add a new company by adding its slug here; no other code changes are
# needed - fetch_raw() iterates over this list automatically.
COMPANY_SLUGS = [
    # Original set
    "stripe",
    "airbnb",
    "coinbase",
    "robinhood",
    "pinterest",
    "cloudflare",
    "figma",
    "gitlab",
    "asana",
    "affirm",
    "reddit",
    "discord",

    # AI
    "databricks",
    "anthropic",
    "scaleai",
    "cresta",
    "deepmind",
    "labelbox",
    "stabilityai",
    "assemblyai",
    "fireworksai",
    "galileo",
    "youcom",
    "worldlabs",
    "imbue",

    # SaaS
    "intercom",
    "smartsheet",
    "wrike",
    "airtable",
    "mixpanel",
    "webflow",
    "typeform",
    "calendly",
    "hubspot",
    "surveymonkey",
    "klaviyo",
    "cultureamp",
    "lattice",

    # FinTech
    "brex",
    "block",
    "ripple",
    "upstart",
    "gusto",
    "chime",
    "mercury",
    "betterment",
    "marqeta",
    "gemini",
    "current",
    "remote",

    # Cybersecurity
    "netskope",
    "onetrust",
    "abnormalsecurity",
    "tanium",
    "cybereason",
    "orcasecurity",
    "zscaler",
    "knowbe4",
    "axonius",
    "huntress",
    "bitwarden",
    "expel",

    # Cloud
    "mongodb",
    "elastic",
    "vercel",
    "fastly",
    "cockroachlabs",
    "honeycomb",
    "netlify",
    "planetscale",

    # Healthcare
    "cloverhealth",
    "komodohealth",
    "mavenclinic",
    "omadahealth",
    "flatironhealth",
    "doximity",
    "elationhealth",
    "talkspace",
    "collectivehealth",
    "parsleyhealth",
    "cerebral",
    "calm",
    "particlehealth",

    # Gaming
    "roblox",
    "riotgames",
    "scopely",
    "epicgames",
    "twitch",
    "krafton",
    "wooga",
    "singularity6",

    # E-commerce
    "instacart",
    "flexport",
    "faire",
    "stockx",
    "narvar",
    "poshmark",
    "grailed",
    "attentive",
    "aftership",
    "yotpo",
    "postscript",
    "route",
    "extend",

    # Enterprise Software
    "datadog",
    "okta",
    "anaplan",
    "newrelic",
    "hackerrank",
    "pagerduty",
    "sumologic",
    "checkr",
    "greenhouse",

    # Robotics
    "agilityrobotics",
    "nuro",
    "figure",
    "aurorainnovation",
    "pathrobotics",
    "locusrobotics",
    "diligentrobotics",
    "apptronik",
    "formic",

    # Aerospace
    "rocketlab",
    "astranis",
    "planetlabs",
    "vardaspace",

    # Automotive
    "lucidmotors",

    # Banking / FinTech (expansion)
    "sofi",
    "n26",
    "monzo",
    "creditkarma",
    "public",
    "highnote",
    "lithic",
    "billtrust",
    "melio",

    # Insurance
    "oscar",
    "coalition",
    "pieinsurance",
    "openly",
    "ethos",
    "root",
    "atbay",

    # Biotech / Pharmaceuticals
    "ginkgobioworks",
    "generatebiomedicines",
    "altoslabs",
    "colossalbiosciences",
    "formbio",

    # Cybersecurity (expansion)
    "chainguard",

    # Cloud Infrastructure / DevTools
    "fivetran",
    "postman",
    "launchdarkly",
    "hightouch",
    "circleci",
    "warp",

    # Telecommunications
    "twilio",
    "dialpad",
    "vonage",
    "bandwidth",

    # Energy
    "watershed",

    # Logistics / Supply Chain
    "fourkites",
    "flexe",
    "samsara",

    # Retail / E-commerce (expansion)
    "glossier",
    "brooklinen",
    "renttherunway",

    # Hospitality / Travel
    "tripactions",
    "vacasa",

    # Education / EdTech
    "duolingo",
    "khanacademy",
    "coursera",
    "udemy",
    "outschool",
    "codeorg",
    "masterclass",
    "degreed",
    "coursehero",

    # Media / Entertainment / Gaming (expansion)
    "buzzfeed",
    "voxmedia",
    "naughtydog",
    "insomniac",
    "bungie",

    # Advertising / Marketing
    "braze",
    "taboola",
    "iterable",
    "customerio",
    "movableink",
    "listrak",

    # Consulting
    "thoughtworks",

    # Real Estate / Construction
    "urbancompass",
    "rxr",
    "entera",
    "turbotenant",
    "ingenious",
    "butlr",
    "housebuyersofamerica",
    "hover",

    # Non-profit
    "givedirectly",
    "donorschoose",

    # Aerospace / Defense / Space (large-volume expansion)
    "spacex",
    "andurilindustries",
    "axon",
    "k2spacecorporation",
    "muonspace",
    "aevexaerospace",
    "altentechnologyusa",
    "defenseunicorns",
    "freeformfuturecorp",
    "divergent",

    # AI (large-volume expansion)
    "xai",
    "gleanwork",
    "snorkelai",
    "agencywithin",
    "remesh",
    "loop",

    # Enterprise Software / Data Platforms (large-volume expansion)
    "datavant2",
    "alphasense",
    "torq",
    "merge",
    "lucidsoftware",
    "intrinsicrobotics",
    "mithril",

    # Gaming / Media / Entertainment (large-volume expansion)
    "sonyinteractiveentertainmentglobal",
    "hasbro",
    "neteasegames",
    "gsgcareers",
    "eleventhhourgames",
    "penninteractive",
    "mrbeastyoutube",
    "axs",

    # FinTech / Banking (large-volume expansion)
    "nubank",
    "branch",
    "enova",
    "pathward",
    "opploans",
    "splashfinancial",
    "creditunionofcolorado",

    # Insurance (large-volume expansion)
    "amwins",
    "ethoslife",
    "nextinsurance66",
    "slideinsurance",
    "sureify",

    # Healthcare / Biotech / Pharmaceuticals (large-volume expansion)
    "khealthcareers",
    "oura",
    "upwardhealth",
    "bridgebio",
    "legendcareers",
    "xairatherapeutics",
    "aspectbiosystems",
    "epicbio",
    "nuvalent",
    "smarterdx",

    # Retail / E-commerce (large-volume expansion)
    "quince",
    "residenthome",
    "vtex",
    "brilliantearth",
    "babylist",
    "weedmaps77",

    # Logistics / Supply Chain (large-volume expansion)
    "yqn",
    "shipbobinc",
    "itslogisticsllc",
    "gatherai",

    # Consulting / Professional Services (large-volume expansion)
    "teneo",
    "careerteam",
    "versaterm",
    "lts",
    "cooksys",
    "perform-careers",

    # Education / EdTech (large-volume expansion)
    "zetacharterschools",
    "perscholashires",
    "unitedcharterschools",
    "relaygraduateschoolofeducation",
    "furtherearlycareer",

    # Other (SaaS holding companies, wellness)
    "saasgroup",
    "levelaccess",
    "future",
]

REQUEST_TIMEOUT = 30

# Greenhouse has no dedicated remote flag, so - as with Jooble/Bundesagentur/
# Adzuna/Reed/CareerJet - remote-friendly postings are detected via keyword.
REMOTE_KEYWORDS = ("remote",)


class GreenhouseSource(BaseJobSource):
    name = "greenhouse"

    def fetch_raw(self):
        """Fetch every configured company's full job list from the Greenhouse Job Board API."""
        jobs = []

        for slug in COMPANY_SLUGS:
            try:
                response = request_with_retry(
                    requests.get,
                    f"{API_URL}/{slug}/jobs",
                    params={"content": "true"},
                    timeout=REQUEST_TIMEOUT,
                )
                payload = response.json()
            except requests.RequestException as exc:
                print(f"[{self.name}] skipped company '{slug}': {exc}")
                continue

            jobs.extend(payload.get("jobs", []))

        return jobs

    def normalize(self, raw_job):
        """Map a Greenhouse job record onto the project's standard schema."""
        title = raw_job.get("title", "")
        location = (raw_job.get("location") or {}).get("name") or "Unknown"

        departments = raw_job.get("departments") or []
        tags = dedupe_tags([department["name"] for department in departments if department.get("name")])

        haystack = f"{title} {location}".lower()
        remote = any(keyword in haystack for keyword in REMOTE_KEYWORDS)

        posted = iso_string_to_date(raw_job.get("first_published") or raw_job.get("updated_at"))

        return {
            "title": title,
            "company": raw_job.get("company_name", ""),
            "location": location,
            "url": raw_job.get("absolute_url", ""),
            "tags": tags,
            "remote": remote,
            "posted": posted,
        }
