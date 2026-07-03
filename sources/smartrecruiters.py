"""
SmartRecruiters Posting API source.

API docs: https://developers.smartrecruiters.com/docs/posting-api

Endpoint: GET https://api.smartrecruiters.com/v1/companies/{company_identifier}/postings
The official docs list this endpoint as requiring an API key or OAuth,
but confirmed live: it returns real data with no auth header at all (it's
the same publicly-embeddable endpoint SmartRecruiters' own career-site
widgets use - CORS is wide open, `access-control-allow-origin: *`). This
is a different endpoint from the partner `/feed/publications` Job Board
API, which does require an `X-SmartToken` header - this project only uses
the public, no-auth one.

SmartRecruiters is company-based rather than a single global index: each
company publishes its postings under its own "company identifier" (slug).
The list of companies to fetch is COMPANY_SLUGS below - adding a new
company later only requires adding its slug to that list; fetch_raw()
already iterates over it automatically, no logic changes needed.

Unlike Greenhouse/Lever/Ashby, an unknown or empty company identifier
does not 404 - it returns HTTP 200 with `totalFound: 0` (confirmed live
with a nonsense identifier). So "verified" here means both HTTP 200 *and*
totalFound > 0 - every slug below was checked against both before being
added.

Pagination is real and required: `offset` + `limit` (default/max used
here: 100 per page, confirmed live), unlike Greenhouse/Ashby's single-shot
responses - some companies here have thousands of postings (Domino's:
24,445; Bosch Group: 4,647). Confirmed live that consecutive pages return
disjoint job IDs (no overlap/skip). Each page failure is caught and
logged, stopping pagination for just that company while keeping whatever
pages it already fetched - the same per-page fault isolation used in
bundesagentur.py/lever.py - and the remaining companies are still
processed regardless.

Each job carries a `company: {identifier, name}` object directly (unlike
Lever/Ashby, which have no company field at all) - so, like Greenhouse's
`company_name`, no manual slug-to-display-name mapping is needed.

There is no dedicated public job-ad URL field in the list response (only
an internal API `ref` URL). Confirmed live that
`https://jobs.smartrecruiters.com/{company_identifier}/{posting_id}`
resolves the public job ad correctly without needing the title-slug
suffix real career-site links use, so that's what's built here.

`location.remote` is a genuine boolean (distinct from `location.hybrid`),
confirmed via live data, so - like Lever's `workplaceType` - `remote` is
read directly from it rather than a keyword heuristic.

Every company slug below was confirmed live against the real API before
being added: ~200 candidate identifiers were tried this session (sourced
from real careers.smartrecruiters.com/jobs.smartrecruiters.com links, not
guessed) and only the 100 that returned HTTP 200 with totalFound > 0 were
kept.
"""

import requests

from .base import BaseJobSource
from .utils import dedupe_tags, iso_string_to_date, request_with_retry

API_URL = "https://api.smartrecruiters.com/v1/companies"

# Company identifiers to fetch. Every slug below was confirmed live
# against the real API (HTTP 200 and totalFound > 0) before being added.
# Add a new company by adding its identifier here; no other code changes
# are needed - fetch_raw() iterates over this list automatically.
COMPANY_SLUGS = [
    # Manufacturing
    "BoschGroup",
    "RobertBosch",
    "Continental",
    "ContinentalAG",
    "AveryDennison",
    "AveryDennison1",
    "westerndigital",
    "ASSYSTEM",
    "FortuneBrands",

    # Consulting
    "prosidianconsulting",
    "AvanceConsultingServices2",
    "PAConsulting",
    "KPFFConsultingEngineers",
    "DTRConsultingServices",
    "Deloitte6",
    "Accenture1",
    "talan",
    "ArchirodonGroup",
    "AECOM2",
    "version1",

    # Market Research
    "NielsenIQ",

    # Retail
    "Primark",
    "Salomon",
    "Shaws",
    "OptimumRetailDynamics",
    "ASOS",

    # Hospitality
    "AccorHotel",
    "AubergeCollection",
    "HillstoneRestaurantGroup",
    "Equinox",
    "SydneyAirport1",
    "Dominos",

    # Healthcare
    "northwesternmedicine",
    "siloamcareers",
    "MunsonHealthcare1",
    "HaltonHealthcare1",
    "SouthernMedicalRecruiters",
    "HealthPartners1",
    "PortsmouthHospitalsUniversityNHSTrust",
    "LegendBiotech",
    "GlobalPharmatek",
    "redcare-pharmacy",
    "EVERSANA1",
    "AHRCNYC1",

    # Media
    "NBCUniversal3",
    "IngramContentGroup1",
    "PulseMediaGroup",
    "ANPublishing1",
    "MassMedia1",
    "Nine",

    # Gaming
    "BoydGaming",
    "Evolution",
    "Gameloft",

    # Banking
    "standardbankgroup",
    "Wise",
    "Shawbrook",
    "EntCreditUnion1",
    "STCU1",
    "Vericast",
    "FinancialStaffingResourcesLtd",
    "Avaloq1",

    # Insurance
    "OUTsurance",
    "OTIPGroupofCompaniesOGC",
    "TheMastersWealthManagementGroupLLC",
    "NeilsonFinancialServices",

    # FinTech
    "Visa",
    "Versant3",

    # Logistics
    "DeliveryHero",
    "Grab",
    "DPDGroupUK1",
    "PSLogistics",
    "MIQLOGISTICS",
    "CulinaGroup1",

    # Education
    "ColumbiaUniversity1",
    "NazarbayevUniversity1",
    "ef-edtech",

    # SaaS / Technology
    "ServiceNow",
    "ifs1",
    "aristanetworks",
    "softwaremind",
    "sigmasoftware2",
    "insightsoftware",
    "Zen31",
    "technologynavigators",
    "JobsForHumanity",
    "brightspeed",
    "RocketInternet",

    # Energy
    "ContactEnergy",
    "EcoEnergySolutions",

    # Cybersecurity / IT Services
    "AreteTechnologiesInc",
    "PurpleBoxInc",
    "IDEALFORCELLC",
    "ComtechLLC2",
    "Pierpoint4",
    "BCforward3",

    # Luxury / Consumer Goods
    "LVMHPerfumesCosmetics",

    # Automotive
    "CooperAutoGroup",

    # Staffing
    "TheRecruitingDivision1",
    "JamesAStaleyCo",

    # Other (social media / telecom)
    "X",
]

PAGE_SIZE = 100
REQUEST_TIMEOUT = 30


class SmartRecruitersSource(BaseJobSource):
    name = "smartrecruiters"

    def fetch_raw(self):
        """Fetch every configured company's job postings from the SmartRecruiters Posting API."""
        jobs = []

        for slug in COMPANY_SLUGS:
            offset = 0

            while True:
                try:
                    response = request_with_retry(
                        requests.get,
                        f"{API_URL}/{slug}/postings",
                        params={"offset": offset, "limit": PAGE_SIZE},
                        timeout=REQUEST_TIMEOUT,
                    )
                    payload = response.json()
                except requests.RequestException as exc:
                    print(f"[{self.name}] skipped company '{slug}': {exc}")
                    break

                page_jobs = payload.get("content", [])
                if not page_jobs:
                    break

                jobs.extend(page_jobs)

                if len(page_jobs) < PAGE_SIZE:
                    break
                offset += PAGE_SIZE

        return jobs

    def normalize(self, raw_job):
        """Map a SmartRecruiters job record onto the project's standard schema."""
        company = raw_job.get("company") or {}
        location = raw_job.get("location") or {}

        department = raw_job.get("department") or {}
        function = raw_job.get("function") or {}
        employment = raw_job.get("typeOfEmployment") or {}
        tags = dedupe_tags(
            [department["label"]] if department.get("label") else None,
            [function["label"]] if function.get("label") else None,
            [employment["label"]] if employment.get("label") else None,
        )

        posted = iso_string_to_date(raw_job.get("releasedDate"))

        identifier = company.get("identifier", "")
        job_id = raw_job.get("id", "")
        url = f"https://jobs.smartrecruiters.com/{identifier}/{job_id}" if identifier and job_id else ""

        return {
            "title": raw_job.get("name", ""),
            "company": company.get("name", ""),
            "location": location.get("fullLocation") or "Unknown",
            "url": url,
            "tags": tags,
            "remote": bool(location.get("remote")),
            "posted": posted,
        }
