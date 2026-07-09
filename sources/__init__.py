"""
Job source registry.

Every job API/ATS integration lives in its own module in this package and
exposes a subclass of `BaseJobSource` (see base.py). To add a new source in
a future milestone:

    1. Create sources/<new_source>.py with a class that subclasses BaseJobSource
       and implements `fetch_raw()` and `normalize(raw_job)`.
    2. Import it below and add an instance to SOURCES.

jobs.py never needs to change when a new source is added.
"""

from . import config  # noqa: F401 - loads .env on startup for Phase 2 (API-key) sources
from .adzuna import AdzunaSource
from .arbeitnow import ArbeitnowSource
from .arbetsformedlingen import ArbetsformedlingenSource
from .ashby import AshbySource
from .bundesagentur import BundesagenturSource
from .careerjet import CareerJetSource
from .careeronestop import CareerOneStopSource
from .eures import EuresSource
from .findwork import FindworkSource
from .francetravail import FranceTravailSource
from .greenhouse import GreenhouseSource
from .himalayas import HimalayasSource
from .hk_gov_vacancies import HKGovVacanciesSource
from .jobicy import JobicySource
from .jobspresso import JobspressoSource
from .jooble import JoobleSource
from .lever import LeverSource
from .mustakbil import MustakbilSource
from .mycareersfuture import MyCareersFutureSource
from .myjobmag import MyJobMagSource
from .nav_norway import NAVNorwaySource
from .nodesk import NoDeskSource
from .openwebninja import OpenWebNinjaSource
from .recruitee import RecruiteeSource
from .reed import ReedSource
from .remoteok import RemoteOKSource
from .remotejobs_org import RemoteJobsOrgSource
from .remotive import RemotiveSource
from .serpapi import SerpApiSource
from .smartrecruiters import SmartRecruitersSource
from .taiwan_mol import TaiwanMOLSource
from .teamtailor import TeamtailorSource
from .theirstack import TheirStackSource
from .themuse import TheMuseSource
from .usajobs import USAJobsSource
from .weworkremotely import WeWorkRemotelySource
from .workable import WorkableSource
from .workday import WorkdaySource

# All active job sources. jobs.py loops over this list to build the full
# aggregated job listing.
SOURCES = [
    ArbeitnowSource(),
    HimalayasSource(),
    RemoteOKSource(),
    JobicySource(),
    TheMuseSource(),
    BundesagenturSource(),
    RemotiveSource(),
    ArbetsformedlingenSource(),
    RemoteJobsOrgSource(),
    MyCareersFutureSource(),
    HKGovVacanciesSource(),
    TaiwanMOLSource(),
    NAVNorwaySource(),
    WeWorkRemotelySource(),
    JobspressoSource(),
    NoDeskSource(),
    MyJobMagSource(),
    MustakbilSource(),
    EuresSource(),
    JoobleSource(),
    USAJobsSource(),
    AdzunaSource(),
    ReedSource(),
    SerpApiSource(),
    OpenWebNinjaSource(),
    CareerJetSource(),
    CareerOneStopSource(),
    FindworkSource(),
    FranceTravailSource(),
    TheirStackSource(),
    GreenhouseSource(),
    LeverSource(),
    AshbySource(),
    SmartRecruitersSource(),
    WorkableSource(),
    TeamtailorSource(),
    RecruiteeSource(),
    WorkdaySource(),
]
