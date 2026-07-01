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

from .arbeitnow import ArbeitnowSource
from .bundesagentur import BundesagenturSource
from .himalayas import HimalayasSource
from .jobicy import JobicySource
from .remoteok import RemoteOKSource
from .themuse import TheMuseSource

# All active job sources. jobs.py loops over this list to build the full
# aggregated job listing.
SOURCES = [
    ArbeitnowSource(),
    HimalayasSource(),
    RemoteOKSource(),
    JobicySource(),
    TheMuseSource(),
    BundesagenturSource(),
]
