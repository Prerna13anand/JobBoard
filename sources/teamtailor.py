"""
Teamtailor public jobs RSS feed source.

Docs referenced: https://docs.teamtailor.com/ (Web API), plus live inspection
of real Teamtailor-hosted career sites.

Teamtailor's documented Web API (`GET https://api.teamtailor.com/v1/jobs`,
or the regional `api.na.teamtailor.com` / `api.au.teamtailor.com`
variants) requires a per-company API key in an `Authorization: Token ...`
header - even the "Public" key tier is a credential only the company
itself can generate in its own account settings, so this project (a
third-party aggregator with no relationship to any of these companies)
cannot use it. That's the recruiting/hiring-workflow-adjacent API this
task explicitly says to ignore.

What every Teamtailor-hosted career site *does* expose with no key, no
login, and no account needed is a public RSS feed:

    GET https://{company_subdomain}.teamtailor.com/jobs.rss

Confirmed live by inspecting a real career site's HTML head
(`<link rel="alternate" type="application/rss+xml" ... href="/jobs.rss" />`)
and then fetching it directly - it returns every currently published job
in a single response, full HTML description included, no auth. This is
the same public surface Teamtailor's own career-site widget uses to
render its job list, so it's the "public job board capability" this
source relies on.

Teamtailor is company-based rather than a single global index: each
company publishes its postings under its own subdomain. Most companies
use a plain `{slug}.teamtailor.com` host, but some (confirmed live, e.g.
Rooted Talent Solutions, THE/STUDIO) are provisioned on Teamtailor's
North-America data stack and are only reachable at
`{slug}.na.teamtailor.com` - a plain `{slug}.teamtailor.com` 404s for
those. So COMPANY_SLUGS below stores each company's full subdomain
(including the `.na` suffix where required, e.g.
"rootedtalentsolutions.na") rather than assuming one uniform pattern -
adding a new company later only requires adding its subdomain to that
list; fetch_raw() already iterates over it automatically, no logic
changes needed.

The feed returns a company's entire published job list in a single
response - no page/offset/cursor params are documented or exist,
confirmed live (one request returned every job for every company tested
here, largest being 95). So, like Greenhouse/Ashby/Workable, this is a
single-shot fetch per company rather than a paginated one.

Each company is fetched independently, and a failure fetching or parsing
one company's feed (bad subdomain, network error, malformed XML) is
caught and logged so the remaining companies still get processed - the
same per-company fault isolation used in greenhouse.py/ashby.py.

The RSS channel carries a `<title>` with the company's real display name
(confirmed live it's often different from the URL subdomain, e.g.
subdomain "winid" -> channel title "Actual Talent") - so, like Workable's
account-level `name` field, no manual slug-to-display-name mapping is
needed; fetch_raw() just tags every job in a company's feed with that
channel title.

Each item's `<remoteStatus>` is a genuine field (confirmed live values:
"none", "hybrid", "fully", and occasionally "temporary" for a contract
type miscategorized into this field on at least one company's feed) - so,
like Ashby's `isRemote`, `remote` is read directly from it (True only for
"fully") rather than a keyword heuristic.

`<pubDate>` is RFC 822 format (e.g. "Thu, 02 Jul 2026 15:46:44 +0200"),
not ISO 8601, so the project's existing `iso_string_to_date` util (which
expects ISO 8601) doesn't apply here - `email.utils.parsedate_to_datetime`
(Python standard library) is used locally in this module instead, to
avoid changing shared utils.py for a format only this source produces.

Every company subdomain below was confirmed live against the real feed
before being added: ~35 candidate subdomains were tried this session
(sourced from real teamtailor.com career-site links surfaced via search,
not guessed) and only the 25 that returned HTTP 200 with at least one
published job were kept.
"""

import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, request_with_retry

API_URL = "https://{}.teamtailor.com/jobs.rss"

TT_NAMESPACE = {"tt": "https://teamtailor.com/locations"}

REQUEST_TIMEOUT = 30

# Company subdomains to fetch (region suffix included where the company's
# feed only resolves under it, e.g. "rootedtalentsolutions.na"). Every
# entry below was confirmed live against the real RSS feed before being
# added. Add a new company by adding its subdomain here; no other code
# changes are needed - fetch_raw() iterates over this list automatically.
COMPANY_SLUGS = [
    "winid",
    "luminorbank",
    "nordictalent",
    "recruitgo",
    "niryu",
    "tmgchicago",
    "polestar",
    "rootedtalentsolutions.na",
    "oatly",
    "career",
    "zinkworks",
    "parcellab",
    "cyberone-security",
    "thestudio.na",
    "howhowltd",
    "gigroup-",
    "upstart13",
    "tise1-amby",
    "dolead",
    "softonic",
    "royalpharmaceuticalsociety",
    "pixiongames",
    "tixtrack",
    "providentineurope",
    "doconomy",
]


def _rfc822_to_iso_date(date_string):
    """Convert an RFC 822 date string (RSS pubDate format) to "YYYY-MM-DD"."""
    if not date_string:
        return ""

    try:
        return parsedate_to_datetime(date_string).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


class TeamtailorSource(BaseJobSource):
    name = "teamtailor"

    def fetch_raw(self):
        """Fetch every configured company's published jobs.rss feed."""
        jobs = []

        for slug in COMPANY_SLUGS:
            try:
                response = request_with_retry(
                    requests.get,
                    API_URL.format(slug),
                    timeout=REQUEST_TIMEOUT,
                )
                root = ET.fromstring(response.content)
            except (requests.RequestException, ET.ParseError) as exc:
                print(f"[{self.name}] skipped company '{slug}': {exc}")
                continue

            channel = root.find("channel")
            if channel is None:
                continue

            # The company display name lives at the channel level, not per
            # item, so it's stashed on each raw record for normalize().
            title_el = channel.find("title")
            company_name = title_el.text if title_el is not None and title_el.text else ""

            for item in channel.findall("item"):
                item.set("_company_name", company_name)
                jobs.append(item)

        return jobs

    def normalize(self, raw_job):
        """Map a Teamtailor RSS <item> element onto the project's standard schema."""
        title_el = raw_job.find("title")
        link_el = raw_job.find("link")
        remote_el = raw_job.find("remoteStatus")
        pubdate_el = raw_job.find("pubDate")

        department_el = raw_job.find("tt:department", TT_NAMESPACE)
        role_el = raw_job.find("tt:role", TT_NAMESPACE)
        division_el = raw_job.find("tt:division", TT_NAMESPACE)

        locations_el = raw_job.find("tt:locations", TT_NAMESPACE)
        first_location = locations_el.find("tt:location", TT_NAMESPACE) if locations_el is not None else None
        city = ""
        country = ""
        if first_location is not None:
            city_el = first_location.find("tt:city", TT_NAMESPACE)
            country_el = first_location.find("tt:country", TT_NAMESPACE)
            city = city_el.text if city_el is not None and city_el.text else ""
            country = country_el.text if country_el is not None and country_el.text else ""
        location = ", ".join(part for part in (city, country) if part) or "Unknown"

        tags = dedupe_tags(
            [department_el.text] if department_el is not None and department_el.text else None,
            [role_el.text] if role_el is not None and role_el.text else None,
            [division_el.text] if division_el is not None and division_el.text else None,
        )

        return {
            "title": title_el.text if title_el is not None and title_el.text else "",
            "company": raw_job.get("_company_name", ""),
            "location": location,
            "url": link_el.text if link_el is not None and link_el.text else "",
            "tags": tags,
            "remote": remote_el is not None and remote_el.text == "fully",
            "posted": _rfc822_to_iso_date(pubdate_el.text if pubdate_el is not None else None),
        }
