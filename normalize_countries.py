"""
Standalone, offline migration: improves the `country` column already stored
in PostgreSQL's `jobs` table, using only the `location` text already on each
row.

This does NOT re-fetch any provider, does NOT modify jobs.py, and makes NO
network requests of any kind - every lookup is backed by local data from
three offline libraries:

    pycountry          - canonical ISO 3166-1 country names/codes
    country_converter   - a large, regex-based table of country name
                          spellings/abbreviations/aliases (also used to
                          produce one consistent "friendly" name per country,
                          e.g. "United States" rather than pycountry's formal
                          ISO name "United States of America")
    geonamescache        - ~32k world cities (name + ISO2 country code +
                          population, used to disambiguate same-named
                          cities in different countries) plus US states and
                          US counties, all bundled as local data - nothing
                          is downloaded at runtime

Install (already added to requirements.txt):

    pip install pycountry country_converter geonamescache

Resolution strategy per location, in priority order (highest confidence
first - a row only falls through to a lower tier if nothing in a higher
tier matched any part of its location text):

    0. Exclusion check: if the location is a placeholder like "Remote",
       "Anywhere", "Worldwide", "Hybrid", "Distributed", etc. (with no
       other identifying text), the country is set to NULL - there is
       nothing to normalize, not "unknown data quality".
    0.5. Multi-country/region check: if the location names 2+ distinct real
       countries (e.g. "Germany, France, Netherlands") or a multi-country
       region/continent (e.g. "Europe", "EMEA", "APAC", "LATAM", "North
       America" - see REGION_TERMS), country is set to NULL - there is
       genuinely no single right country, so none is guessed. This is
       different from tier 0: the *location* is preserved exactly as-is
       either way (this script never touches the location column, only
       country/work_arrangement) - only the single-country guess is
       withheld. See is_ambiguous_multi_country().
    1. Full country names/native-language names/common abbreviations
       (pycountry exact names + a small hand-curated native-name alias
       table + country_converter's regex table), searched across the whole
       location string and each comma/semicolon/pipe/dash-separated segment.
    2. Unambiguous ISO 3166-1 alpha-2/alpha-3 codes appearing as an
       isolated token (e.g. "FR-Paris", "GB-London", "IND-BLR-...").
       26 two-letter codes are excluded here because they collide with a US
       state postal code (computed by cross-referencing geonamescache's US
       states against pycountry - see AMBIGUOUS_ISO2/_compute_ambiguous_iso2;
       a first hand-written pass at this list only caught 11 of the 26 and
       even mislabeled a couple, e.g. GA collides with Gabon, not Georgia)
       - those are deferred to tier 4 below rather than guessed here.
    3. City name lookup (geonamescache), case-insensitive exact match on
       a segment/word, disambiguated by picking the most populous city
       when a name exists in multiple countries (e.g. "London" -> UK over
       London, Ontario; "Paris" -> France over Paris, Texas).
    4. US state postal codes/full names and US county names -> "United
       States". This is the lowest-confidence tier and only fires if
       nothing else in the location resolved - it exists because this
       project's providers are heavily US-ATS-dominated (Greenhouse/Lever/
       SmartRecruiters/Workday all commonly give bare state codes).

    Many real countries double as small US town names (Lebanon, Jersey,
    Grenada, Angola, Mexico, Malta, Peru, Brazil, Nederland, Georgia, ...)
    or as loose substrings of one (Cook Islands' country_converter regex is
    just the bare word "cook", matching "Cookeville"/"Cook County";
    similarly Jordan/"South Jordan", Panama/"Panama City"). Tier 1 defers
    any country match whenever a US state-code segment is *also* present
    elsewhere in the same location (e.g. "Lebanon, TN" or "Jersey City,
    NJ") - if "United States" itself resolves from another segment, that
    wins; otherwise the location is left unresolved rather than guessing
    the country. Tier 4 separately excludes AMBIGUOUS_STATE_TOKENS (the 26
    codes above, plus "Georgia" the full name) from its own "United States"
    default - a bare "Georgia" or "TN" with nothing else to go on stays
    NULL/unknown, since the text alone genuinely can't tell state from
    country. Compound locations resolve fine regardless - "Atlanta,
    Georgia" or "Los Angeles, CA" hit the real city in tier 3 long before
    tier 4 is ever consulted.

    If nothing matches at any tier, the row is left as "Unknown" (country
    stays NULL) rather than guessing.

Work-arrangement tagging: independent of country resolution, every row is
also tagged with a `work_arrangement` of 'remote' / 'hybrid' / 'onsite' (or
NULL) via classify_work_arrangement() - a simple word/phrase search over the
location text. This is deliberately not mutually exclusive with country:
"Remote - US" gets both work_arrangement='remote' and country='United
States'; "Remote (United States | Canada)" gets work_arrangement='remote'
with country left NULL (ambiguous between two countries). This is what lets
placeholder locations like "Remote"/"Hybrid"/"Worldwide" stay filterable
even though they correctly have no country.

Update rule: a row is only written if its country or work_arrangement
actually changes - existing correct values are never rewritten, and
locations this script can't resolve never overwrite whatever is already
stored (no regressions). The one exception is placeholder/ambiguous-multi-
country locations (tier 0 and the multi-country check): those are always
forced to NULL, since they should never carry a single guessed country.

Usage:
    python normalize_countries.py            # apply updates
    python normalize_countries.py --dry-run   # report only, no writes
"""

import argparse
import re
import sys
import unicodedata
from collections import Counter

import country_converter as coco
import pandas as pd
import psycopg2.extras
import pycountry
from geonamescache import GeonamesCache

import database

SAMPLE_SIZE = 10
TOP_UNKNOWN_COUNT = 20

# ---------------------------------------------------------------------------
# Placeholder / non-geographic locations - always normalized to NULL.
# ---------------------------------------------------------------------------
PLACEHOLDER_LOCATIONS = {
    "", "-", "remote", "anywhere", "worldwide", "hybrid", "global",
    "flexible", "flexible remote", "distributed", "unknown", "n a", "na",
    "tbd", "various", "various locations", "multiple", "multiple locations",
    "any", "any city", "not specified", "location negotiable after selection",
    "islandwide", "nationwide", "central", "global remote", "remote job",
    "full time", "full-time", "in office", "in-office", "on site", "onsite",
    "flex", "flexible location", "flexible / remote", "wfh", "work from home",
}

# ---------------------------------------------------------------------------
# Work-arrangement classification - independent of country. A remote/hybrid/
# onsite qualifier and a real country are not mutually exclusive ("Remote -
# US" has both), so this is checked separately, as a substring/word search
# rather than a whole-string placeholder match. First match wins; checked in
# this order (most to least specific) so "Hybrid - Remote" (rare) reads as
# remote, matching the stronger claim.
# ---------------------------------------------------------------------------
_WORK_ARRANGEMENT_PATTERNS = [
    ("remote", re.compile(
        r"\b(remote|anywhere|worldwide|distributed|work[\s-]?from[\s-]?home|wfh|flexible|islandwide)\b",
        re.IGNORECASE,
    )),
    ("hybrid", re.compile(r"\bhybrid\b", re.IGNORECASE)),
    ("onsite", re.compile(r"\b(on[\s-]?site|in[\s-]?office)\b", re.IGNORECASE)),
]


def classify_work_arrangement(location):
    """Best-effort remote/hybrid/onsite tag derived from location text, independent
    of country resolution (e.g. "Remote (United States | Canada)" has no single
    resolvable country, but is still clearly "remote"; "Remote - US" is both
    "remote" and resolves country to United States)."""
    if not location:
        return None
    text = _strip_accents(location)
    for label, pattern in _WORK_ARRANGEMENT_PATTERNS:
        if pattern.search(text):
            return label
    return None


# A large share of this dataset's remaining unresolved locations turned out
# to be UK addresses ("Frimley, GU16 7UJ", "Cambridge Bio Medical Campus,
# CB2 0AY") or bare postcodes (bad/missing town names, e.g. "EC1A1BB") for
# towns too small for geonamescache's ~32k cities. UK postcodes are a
# distinctive, unambiguous format (1-2 letters, a digit, an optional
# letter/digit, then a digit and 2 letters, e.g. "GU16 7UJ" or "M2 5DB",
# space optional) not used anywhere else, so matching one anywhere in a
# candidate is treated as a confident "United Kingdom".
_UK_POSTCODE_RE = re.compile(r"^[A-Z]{1,2}[0-9][A-Z0-9]?\s*[0-9][A-Z]{2}$")


def _is_uk_postcode(candidate):
    return bool(_UK_POSTCODE_RE.match(candidate.strip().upper()))


# Another large share of remaining unresolved locations turned out to be
# French addresses given as "{INSEE department code} - {commune}" (e.g.
# "83 - COGOLIN", "01 - MONTLUEL"), including several where the "commune"
# is literally the department's own name ("01 - Ain", "02 - Aisne") -
# confirming this is the official 2-digit (01-95, mainland) or 3-digit
# (971-976, overseas) INSEE numbering, not a coincidence. Checked directly
# against the DB: every single distinct code appearing in this dataset
# (1,119 rows) is a genuine valid department number, so this is treated as
# a confident "France" the same way a UK postcode is treated as "United
# Kingdom".
_FRENCH_DEPT_RE = re.compile(r"^(0[1-9]|[1-8][0-9]|9[0-5]|97[1-6])\s*-\s*\S")


def _is_french_department_code(candidate):
    return bool(_FRENCH_DEPT_RE.match(candidate.strip()))

# ---------------------------------------------------------------------------
# Native-language / short-form country aliases not reliably covered by
# country_converter's (English-centric) regex table.
# ---------------------------------------------------------------------------
NATIVE_ALIASES = {
    "deutschland": "Germany", "duitsland": "Germany",
    "espana": "Spain", "belgie": "Belgium", "belgique": "Belgium",
    "nederland": "Netherlands", "holland": "Netherlands",
    "norge": "Norway", "sverige": "Sweden", "suomi": "Finland",
    "osterreich": "Austria", "schweiz": "Switzerland", "suisse": "Switzerland",
    "svizzera": "Switzerland", "polska": "Poland", "danmark": "Denmark",
    "italia": "Italy", "brasil": "Brazil", "mexico city": "Mexico",
    "us": "United States", "usa": "United States", "u s": "United States",
    "uk": "United Kingdom", "u k": "United Kingdom",
    "uae": "United Arab Emirates", "prc": "China",
}

# Subset of NATIVE_ALIASES safe to check against bare individual words (see
# the early pass in _resolve_country_uncached, used for separator-less text
# like "US Remote"). Deliberately excludes full native-language place names
# like "nederland"/"deutschland"/"brasil": those are exactly as prone to the
# same-named-US-town problem as any other country name (Nederland, TX is a
# real town), so they're only resolved through the main tiered/candidate
# pipeline below, where the US-state-context deferral applies.
_SAFE_BARE_WORD_ALIASES = {"us", "usa", "u s", "uk", "u k", "uae"}

# Specific named places not present at all in geonamescache (usually because
# they're too new/small for its ~32k-city dataset) - resolved directly
# rather than through the city lookup tier.
MANUAL_PLACE_ALIASES = {
    "king abdullah economic city": "Saudi Arabia",
}

# US unincorporated territories: each has its own pycountry/ISO entry, but
# for the multi-country ambiguity check they should count as "United
# States", not a separate country - a job list like "Albany, NY, ...,
# San Juan, Puerto Rico, ..., Washington, DC" is an ordinary list of US
# offices, not a US-and-Puerto-Rico multi-country listing.
US_TERRITORIES = {
    "Puerto Rico", "Guam", "American Samoa",
    "Northern Mariana Islands", "Virgin Islands, U.S.",
}

# ---------------------------------------------------------------------------
# Multi-country region/continent names ("Europe", "EMEA", "APAC", ...) - none
# of these are real countries, so resolve_country() was already returning
# None for them, but they weren't being treated as *ambiguous* either (that
# status was reserved for locations naming 2+ real countries). The result:
# a bare "Europe" or "EMEA" location fell through to run()'s "can't verify,
# leave untouched" rule and kept whatever garbage country a previous,
# cruder guess had written (confirmed live in this project's database - e.g.
# "Europe" -> country="Europe" literally, "APAC" -> country="Uganda" from a
# real Ugandan town called Apac colliding in the city-lookup tier,
# "Remote - European Union" -> "United States" from "Union" matching a US
# county name). Treating a region mention as ambiguous (same as 2+ named
# countries) fixes all of these: it forces country to NULL and, unlike an
# unresolvable location, is allowed to *overwrite* a bad existing value -
# see is_ambiguous_multi_country() and its use in run().
#
# Split into two tiers by collision risk:
#   REGION_TERMS - matched only when a term is an entire segment/sub-segment
#     (after splitting on comma/semicolon/pipe/slash/parens/dash/"&" - see
#     _distinct_regions_mentioned) or an entire location. Safe for
#     multi-word phrases like "North America" and single words alike,
#     because the match is exact-equality, never substring.
#   WORD_LEVEL_REGION_TERMS - a stricter subset also matched against
#     individual whitespace-split words within an otherwise-unmatched
#     segment (e.g. "Americas Remote", "EMEA Remote" have no separator to
#     split on between the region word and "Remote"). Deliberately excludes
#     "africa"/"asia"/"oceania": bare continent words are collision-prone at
#     word level - "South Africa" would otherwise be misread as mentioning
#     region "Africa" (checked: every real hit for those three in this
#     dataset was already its own clean comma/paren-separated segment, so
#     segment-level matching alone catches them with no added risk).
# ---------------------------------------------------------------------------
REGION_TERMS = {
    "europe", "european union", "emea", "apac", "asia pacific", "apj",
    "latam", "anz", "mena", "nordics", "benelux",
    "americas", "north america", "south america", "central america",
    "asia", "africa", "oceania", "worldwide", "global",
}

WORD_LEVEL_REGION_TERMS = {
    "europe", "emea", "apac", "latam", "anz", "mena", "nordics",
    "benelux", "apj", "worldwide", "global", "americas",
}

_REGION_SUB_SPLIT_RE = re.compile(r"[&]|-|–|—")

_SPLIT_RE = re.compile(r"[,;/|]|&|-|–|—")
_LOOSE_SPLIT_RE = re.compile(r"\s+(?:or|and)\s+", re.IGNORECASE)
_PAREN_RE = re.compile(r"\(([^)]+)\)")
_NON_WORD_RE = re.compile(r"[^\w\s]+")
_WHITESPACE_RE = re.compile(r"\s+")


def _safe_print(text):
    """Print text that may contain characters this terminal's encoding can't display.

    Job locations round-trip through many languages (e.g. "Perú", "México");
    some terminals (notably Windows consoles stuck on a legacy codepage) can't
    encode those directly. The stored/resolved data is unaffected either way.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding))


def _repair_mojibake(text):
    """
    Repair UTF-8 text that was mistakenly double-encoded upstream (a small
    number of rows have e.g. "MÃ©xico" stored instead of "México" - the
    UTF-8 bytes for "é" got individually reinterpreted as Latin-1). Safe by
    construction: encode-as-latin1-then-decode-as-utf8 only succeeds when
    the text was genuinely double-encoded this way; for already-correct
    text it raises (a lone accented character doesn't round-trip through
    UTF-8 decoding) and the original is kept unchanged.
    """
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def _strip_accents(text):
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _normalize_key(text):
    """Lowercase, accent-stripped, punctuation-collapsed form used for dict lookups."""
    text = _strip_accents(text).lower()
    text = _NON_WORD_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _build_candidates(location):
    """
    Break a raw location string into the pieces worth resolving independently.

    Deliberately does NOT split on "and"/"or" - several real country names
    contain "and" (Trinidad and Tobago, Bosnia and Herzegovina, Antigua and
    Barbuda, Turks and Caicos Islands, ...), so splitting on it would corrupt
    them into two meaningless fragments. "X or Y" phrasing (e.g. "NY or
    Remote") is instead handled separately, only in the lowest-confidence US
    state/county tier where there's no real country name left to protect -
    see _build_loose_candidates().
    """
    candidates = [location]
    candidates.extend(p.strip() for p in _SPLIT_RE.split(location) if p.strip())
    candidates.extend(_PAREN_RE.findall(location))
    no_paren = _PAREN_RE.sub(" ", location).strip()
    if no_paren:
        candidates.append(no_paren)
    # dedupe while preserving order
    seen = set()
    ordered = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered


def _build_loose_candidates(text):
    """Extra candidates split on "or"/"and" and on individual words (e.g. "US Remote"
    -> "US"), used only by the tier-4 US state/county fallback - see the note on
    _build_candidates() for why this isn't used everywhere."""
    extra = [p.strip() for p in _LOOSE_SPLIT_RE.split(text) if p.strip()]
    extra.extend(text.split())
    return extra


# ---------------------------------------------------------------------------
# Reference data, built once at import time.
# ---------------------------------------------------------------------------

def _build_pycountry_name_lookup():
    """Exact-name lookup: pycountry name/official_name/common_name -> friendly name."""
    lookup = {}
    for country in pycountry.countries:
        friendly = coco.convert(country.alpha_2, src="ISO2", to="name_short", not_found=country.name)
        for attr in ("name", "official_name", "common_name"):
            value = getattr(country, attr, None)
            if value:
                lookup[_normalize_key(value)] = friendly
    return lookup


def _build_coco_regex():
    """One combined regex covering every country's alias/spelling patterns from country_converter."""
    cc = coco.CountryConverter()
    patterns, names = [], []
    for _, row in cc.data.iterrows():
        rx, name = row["regex"], row["name_short"]
        if pd.isna(rx) or pd.isna(name) or not str(rx).strip():
            continue
        # Convert any capturing group in the source regex to non-capturing so
        # group index i always lines up with names[i] in the combined regex.
        safe_rx = re.sub(r"\((?!\?)", "(?:", rx)
        patterns.append(f"({safe_rx})")
        names.append(name)
    combined = re.compile("|".join(patterns), re.IGNORECASE)
    return combined, names


def _compute_ambiguous_iso2(gc):
    """
    Every US state postal code that's *also* a real ISO 3166-1 alpha-2 country
    code - computed by cross-referencing geonamescache's US states against
    pycountry's country list, rather than hand-enumerated (a first pass at
    this by hand only caught 11 of the real 26: it's easy to miss non-obvious
    ones like IL/Israel, LA/Laos, MA/Morocco, MD/Moldova, TN/Tunisia,
    VA/Vatican City, AR/Argentina, KY/Cayman Islands, SC/Seychelles, and it's
    easy to get the collision wrong even for codes correctly flagged - e.g.
    GA collides with Gabon, not Georgia (Georgia the country's real code is
    GE); MT collides with Malta, not Montenegro (ME)).
    """
    country_codes = {c.alpha_2 for c in pycountry.countries}
    return {code for code in gc.get_us_states() if code in country_codes}


def _build_iso_code_lookup(ambiguous_iso2):
    """ISO 3166-1 alpha-2 (excluding US-state collisions) and alpha-3 -> friendly name."""
    alpha2, alpha3 = {}, {}
    for country in pycountry.countries:
        friendly = coco.convert(country.alpha_2, src="ISO2", to="name_short", not_found=country.name)
        if country.alpha_2 not in ambiguous_iso2:
            alpha2[country.alpha_2.lower()] = friendly
        alpha3[country.alpha_3.lower()] = friendly
    return alpha2, alpha3


# A few very common short forms/alternate or historical spellings that
# don't match geonamescache's canonical name for the same city - deliberately
# tiny and unambiguous, unlike the removed word-level fallback this replaces
# (see _build_city_lookup's docstring).
_CITY_NAME_ALIASES = {
    "new york": "new york city",
    "bangalore": "bengaluru",       # renamed 2014; "Bangalore" still common in job postings
    "gurgaon": "gurugram",          # renamed 2016
    "munchen": "munich",            # German spelling (accent-stripped from "München")
    "bombay": "mumbai",              # renamed 1995
    "calcutta": "kolkata",           # renamed 2001
    "madras": "chennai",             # renamed 1996
    "peking": "beijing",
    # Deliberately NOT "canton" -> "guangzhou": geonamescache has no
    # Guangzhou entry reachable under that name at all, but it does have
    # four real, populous US cities literally named Canton (OH, MI, GA,
    # MA) - the alias would only ever misidentify those, never help.
}


def _build_city_lookup(gc):
    """
    City name -> ISO2, keeping the most populous city for any name that repeats.

    Deliberately does NOT also check individual words of a multi-word
    candidate (e.g. treating "New York" as a match for "York" would return
    the wrong country: England, not the US) - only whole-segment/whole-word
    exact matches are trusted, plus the small manual _CITY_NAME_ALIASES
    table for the handful of very common names that don't match
    geonamescache's canonical spelling.
    """
    city_country, city_population = {}, {}
    for city in gc.get_cities().values():
        key = _normalize_key(city["name"])
        if not key:
            continue
        population = city.get("population") or 0
        if population > city_population.get(key, -1):
            city_population[key] = population
            city_country[key] = city["countrycode"]
    for alias, canonical in _CITY_NAME_ALIASES.items():
        if canonical in city_country:
            city_country[alias] = city_country[canonical]
    return city_country


def _build_us_lookup(gc):
    """US state codes/names and county names -> True (all imply "United States")."""
    us_tokens = set()
    for code, info in gc.get_us_states().items():
        us_tokens.add(_normalize_key(code))
        us_tokens.add(_normalize_key(info["name"]))
    us_tokens.add(_normalize_key("Washington DC"))
    us_tokens.add(_normalize_key("District of Columbia"))
    us_counties = {_normalize_key(c["name"]) for c in gc.get_us_counties()}
    return us_tokens, us_counties


print("Loading offline reference data (pycountry, country_converter, geonamescache)...")
_gc = GeonamesCache()
PYCOUNTRY_NAME_LOOKUP = _build_pycountry_name_lookup()
COCO_REGEX, COCO_NAMES = _build_coco_regex()
AMBIGUOUS_ISO2 = _compute_ambiguous_iso2(_gc)
ISO2_LOOKUP, ISO3_LOOKUP = _build_iso_code_lookup(AMBIGUOUS_ISO2)
# Built from pycountry's clean alpha_2, not country_converter's own "ISO2"
# column: that column is a plain code for almost every country, but for
# Greece and the United Kingdom specifically it's the *regex* "^GR$|^EL$" /
# "^GB$|^UK$" rather than "GR"/"GB" - using it directly here would silently
# make every UK/Greek city (e.g. geonamescache's plain "GB" country code for
# London) fail to resolve.
ISO2_TO_NAME = {
    country.alpha_2: coco.convert(country.alpha_2, src="ISO2", to="name_short", not_found=country.name)
    for country in pycountry.countries
}
CITY_COUNTRY = _build_city_lookup(_gc)
US_STATE_TOKENS, US_COUNTY_NAMES = _build_us_lookup(_gc)

# Bare tokens genuinely ambiguous between a US state and a real country, with
# no way to tell which from the text alone: the 26 two-letter postal-code
# collisions above, plus "Georgia" the full state name (which doesn't show
# up in AMBIGUOUS_ISO2 - that's a *code* collision with Gabon; Georgia the
# state vs. Georgia the country is a full-*name* collision instead). These
# are excluded from tier 4 entirely rather than defaulted to "United States" -
# a bare "Georgia" or "TN" with nothing else in the location stays NULL/
# unknown. Compound locations aren't affected - "Atlanta, Georgia" or
# "Nashville, TN" resolve confidently via the real city in tier 3 long
# before tier 4 would ever need to consider "Georgia"/"TN" at all.
AMBIGUOUS_STATE_TOKENS = {code.lower() for code in AMBIGUOUS_ISO2} | {"georgia"}

print(f"  {len(PYCOUNTRY_NAME_LOOKUP)} country name variants, {len(CITY_COUNTRY)} cities, "
      f"{len(US_STATE_TOKENS)} US state tokens, {len(US_COUNTY_NAMES)} US counties loaded, "
      f"{len(AMBIGUOUS_ISO2)} ambiguous US-state/country codes excluded.\n")


def _distinct_countries_mentioned(text):
    """
    Every distinct country independently matched across text's comma/semicolon/
    pipe-separated segments.

    Deliberately exact-match only (PYCOUNTRY_NAME_LOOKUP/NATIVE_ALIASES), NOT
    the loose COCO_REGEX substring search used elsewhere: a real list of
    countries ("Nigeria, South Africa") is made of segments that are each,
    in full, a real country name, so exact matching catches those just
    fine - but loose substring matching also flags plenty of ordinary city
    names that merely *contain* a country's name as a false "second
    country" ("Cookeville" contains "cook" -> Cook Islands; "South Jordan"
    contains "jordan"; "Panama City" contains "panama"), which would wrongly
    mark "Cookeville, TN, United States" as an ambiguous multi-country list
    instead of the single, ordinary US location it is.

    A second, similar false-positive class: many small US towns are
    literally named after a country (Lebanon TN/KY/PA/OH/OR/IN/MO, Grenada
    MS, Angola IN, Mexico MO, Malta NY, Peru IN/IL, Brazil IN, Nederland
    TX, ...) - all of these exact-match a real country name too. If the
    same location also has a US state-code segment (e.g. "TN") *and*
    "United States" itself among the matches, that combination is far more
    likely this same-named-town pattern than a genuine multi-country
    listing, so it's treated as non-ambiguous (empty result) rather than
    flagging e.g. "Lebanon, TN, United States" as Lebanon-and-US.

    That suppression only fires when "United States" is the *only* other
    match besides the state-code-adjacent one (len(found) == 2): a genuine
    "we hire in every country" listing often coincidentally includes both
    "Georgia" (which is also a US state name) and "United States" among
    100+ entries, and that must still count as ambiguous, not get wiped
    out by this same rule.

    Splits on "/" and parentheses too (not just comma/semicolon/pipe), so a
    parenthetical shorthand like "Remote (US/Canada)" still splits "US" and
    "Canada" into their own segments instead of being trapped inside one
    "or Remote (US/Canada)" chunk that matches neither exactly.

    US territories (see US_TERRITORIES) count as "United States" here, not
    as their own distinct country - a list of US office cities that happens
    to include "San Juan, Puerto Rico" is not a multi-country listing.
    """
    found = set()
    has_state_code = False
    for segment in re.split(r"[,;|/()]", text):
        segment = segment.strip()
        if not segment:
            continue
        key = _normalize_key(segment)
        if key in US_STATE_TOKENS:
            has_state_code = True
        if key in US_STATE_TOKENS or key in US_COUNTY_NAMES:
            continue
        name = PYCOUNTRY_NAME_LOOKUP.get(key) or NATIVE_ALIASES.get(key)
        if name:
            found.add("United States" if name in US_TERRITORIES else name)
            continue
        # Whole segment didn't resolve as-is - try its internal dash-
        # separated parts too (e.g. "CA - Canada; US - United States", where
        # each half of "CA - Canada" is its own segment only after a further
        # split on "-"). Deliberately only attempted here, as a fallback
        # after the whole-segment match already failed: trying it
        # unconditionally would corrupt genuine hyphenated country names
        # ("Guinea-Bissau", "Timor-Leste") into meaningless halves, and
        # could double-count a country matched as a whole. This fallback's
        # hits are also excluded from has_state_code below - "CA" here is
        # standing in for Canada (spelled out right next to it), not
        # California, so it must not trigger the same-named-US-town
        # suppression that a bare top-level "TN"/"CA" segment would.
        for sub in _REGION_SUB_SPLIT_RE.split(segment):
            sub = sub.strip()
            if not sub:
                continue
            sub_key = _normalize_key(sub)
            if sub_key in US_STATE_TOKENS or sub_key in US_COUNTY_NAMES:
                continue
            sub_name = PYCOUNTRY_NAME_LOOKUP.get(sub_key) or NATIVE_ALIASES.get(sub_key)
            if sub_name:
                found.add("United States" if sub_name in US_TERRITORIES else sub_name)
    if has_state_code and "United States" in found and len(found) == 2:
        return set()
    return found


def _distinct_regions_mentioned(text):
    """
    Every distinct multi-country region/continent term (see REGION_TERMS)
    found in text, checked the same segment-by-segment way as
    _distinct_countries_mentioned - any hit here means the location can't
    resolve to a single country, so resolve_country() treats a non-empty
    result exactly like 2+ named countries (see its use in
    _resolve_country_uncached).

    A segment that's already a real, complete country name (e.g. "South
    Africa") is skipped entirely rather than checked for embedded region
    words - otherwise "South Africa" would be misread as mentioning region
    "Africa" merely because "Africa" is its second word.
    """
    found = set()
    for segment in re.split(r"[,;|/()]", text):
        segment = segment.strip()
        if not segment:
            continue
        key = _normalize_key(segment)
        if key in PYCOUNTRY_NAME_LOOKUP or key in NATIVE_ALIASES:
            continue
        if key in REGION_TERMS:
            found.add(key)
            continue
        for sub in _REGION_SUB_SPLIT_RE.split(segment):
            sub_key = _normalize_key(sub.strip())
            if sub_key in REGION_TERMS:
                found.add(sub_key)
        for word in segment.split():
            word_key = _normalize_key(word)
            if word_key in WORD_LEVEL_REGION_TERMS:
                found.add(word_key)
    return found


_resolve_cache = {}
_ambiguous_multi_country = set()


def is_ambiguous_bare_location(location):
    """True if the *entire* location (not just one segment of it) is a bare
    state/country collision token - "Georgia" or "CA" alone, with nothing
    else to disambiguate it. Distinct from is_ambiguous_multi_country: this
    location isn't unresolvable because it's unfamiliar text, it's
    unresolvable because it's a specific, known "could be either" case - so
    like the multi-country case, run() forces it to NULL rather than
    leaving behind whatever single guess a previous pass landed on.
    Compound locations aren't affected ("Atlanta, Georgia" resolves via the
    real city "Atlanta" regardless of "Georgia"'s own ambiguity)."""
    return _normalize_key(location) in AMBIGUOUS_STATE_TOKENS


def is_ambiguous_multi_country(location):
    """True if a location lists 2+ distinct countries (e.g. "Nigeria, South Africa"; a
    "countries we hire in" list) OR names a multi-country region/continent (e.g.
    "Europe", "EMEA", "APAC" - see REGION_TERMS) - either way there's no single right
    country. resolve_country() returns None for these rather than arbitrarily picking
    one, and run() forces such rows to NULL rather than leaving whatever single country
    a *previous*, equally arbitrary (or plain wrong) value had landed on."""
    resolve_country(location)  # populates the cache/ambiguity set as a side effect
    return location in _ambiguous_multi_country


def resolve_country(location):
    """Best-effort, offline resolution of a free-text location to a country name (or None)."""
    if location is None:
        return None
    if location in _resolve_cache:
        return _resolve_cache[location]

    result = _resolve_country_uncached(location)
    _resolve_cache[location] = result
    return result


def _resolve_country_uncached(location):
    text = _repair_mojibake(location.strip())
    if not text:
        return None

    if _normalize_key(text) in PLACEHOLDER_LOCATIONS:
        return None

    # A location naming 2+ distinct countries (a "hiring in these countries"
    # list, not a single job's location) has no single right answer - flag it
    # rather than let regex-alternation order silently pick one arbitrarily.
    # Same treatment for a named multi-country region/continent ("Europe",
    # "EMEA", "APAC", ... - see REGION_TERMS): it's just as unresolvable to
    # one country as a 2+-country list is, even when it's the only "country-
    # like" text present.
    explicit_countries = _distinct_countries_mentioned(_strip_accents(text))
    regions_mentioned = _distinct_regions_mentioned(_strip_accents(text))
    if regions_mentioned or len(explicit_countries) >= 2:
        _ambiguous_multi_country.add(location)
        return None

    resolved, city_candidate = _resolve_tiers(text)

    # Final safety net, city-tier matches only: a location can explicitly
    # name exactly one *other* country (so the check above doesn't trigger -
    # there's only one exact match) while ALSO containing real city names
    # from a different country, e.g. "Bellevue, Washington; Chicago,
    # Illinois; Toronto, Ontario, Canada" - tier 3 happily resolves
    # "Bellevue" to United States without ever noticing "Canada" is spelled
    # out right there too. If a *city* match disagrees with an explicitly-
    # named country, this location genuinely spans 2+ real countries.
    #
    # But only when the matched city ISN'T itself the source of that
    # "explicit country" - "Lebanon, Pennsylvania" resolves via tier 3 with
    # city_candidate="Lebanon", and "Lebanon" is exactly the same word that
    # made explicit_countries={"Lebanon"} in the first place (a same-named-
    # town false positive, not a second location) - that must not be
    # second-guessed. Only a city match whose own name is unrelated to the
    # explicit country (like "Bellevue", nothing to do with "Canada") means
    # the explicit mention is describing a genuinely different place.
    if city_candidate and resolved and explicit_countries and resolved not in explicit_countries:
        if _normalize_key(city_candidate) not in PYCOUNTRY_NAME_LOOKUP:
            _ambiguous_multi_country.add(location)
            return None

    return resolved


def _resolve_tiers(text):
    """Returns (country, city_candidate) - city_candidate is the matched candidate
    string when the result came from tier 3's city lookup specifically, or None
    otherwise (see the caller, _resolve_country_uncached, for why that matters)."""
    candidates = _build_candidates(text)

    # Named places with no geonamescache entry at all (see MANUAL_PLACE_ALIASES).
    for candidate in candidates:
        key = _normalize_key(candidate)
        if key in MANUAL_PLACE_ALIASES:
            return MANUAL_PLACE_ALIASES[key], None

    # A UK postcode (see _is_uk_postcode) anywhere is a confident, unambiguous
    # "United Kingdom" - this covers small UK towns/villages too tiny for
    # geonamescache's ~32k cities (e.g. "Frimley, GU16 7UJ") as well as bare
    # postcodes with no usable town name at all (e.g. "EC1A1BB").
    for candidate in candidates:
        if _is_uk_postcode(candidate):
            return "United Kingdom", None

    # A French INSEE department code prefix (see _is_french_department_code)
    # is likewise a confident "France" - covers small French communes too
    # tiny for geonamescache (e.g. "83 - COGOLIN").
    if _is_french_department_code(text):
        return "France", None

    # _SAFE_BARE_WORD_ALIASES entries are short and unambiguous (no US state
    # shares these names) - safe to check against individual words too (not
    # just comma/dash-split candidates), which is what lets bare "US Remote"/
    # "Remote US" resolve without a separator to split on.
    for word in text.split():
        key = _normalize_key(word)
        if key in _SAFE_BARE_WORD_ALIASES:
            return NATIVE_ALIASES[key], None

    # Any country match is deferred rather than returned immediately when a
    # US state-code segment is *also* present somewhere in this same
    # location: plenty of real countries double as small US town names
    # (Lebanon, Jersey, Grenada, Angola, Mexico, Malta, Peru, Brazil,
    # Nederland, Georgia, ...) - e.g. "Lebanon, TN" or "Jersey City, NJ". If
    # another candidate in the same location resolves to something else
    # (most commonly "United States" itself), that wins; the weak match is
    # only used as a last resort if nothing better turns up anywhere below.
    has_state_code_context = any(
        _normalize_key(c) in US_STATE_TOKENS for c in candidates
    )
    weak_match = None

    def _accept(name):
        nonlocal weak_match
        # "United States" itself is never deferred - there's nothing it
        # could lose out to that would be a better answer. Every *other*
        # match is always deferred (not just the first): the same country
        # can legitimately match more than once for one location (e.g. both
        # the whole unsplit string and the "Jersey City" segment separately
        # match "Jersey"'s loose regex) - accepting the second occurrence
        # just because weak_match was already set would let this same
        # low-confidence guess win outright instead of leaving room for a
        # real city (e.g. "Boston") to resolve it correctly in tier 3.
        if name != "United States" and has_state_code_context:
            if weak_match is None:
                weak_match = name
            return None
        return name

    # Tier 1: full country names (pycountry exact, native aliases, coco regex).
    # Skips any candidate that's itself a recognized US state/county name
    # (e.g. "Georgia", "Cook County", "Switzerland County", "Lebanon
    # County") - several of country_converter's per-country regexes are
    # loose single-word substring matches (Cook Islands is just `\bcook`),
    # which would otherwise misread ordinary US county names as a mention of
    # an unrelated country. Tier 4 below resolves these correctly instead.
    for candidate in candidates:
        if _normalize_key(candidate) in US_STATE_TOKENS or _normalize_key(candidate) in US_COUNTY_NAMES:
            continue
        key = _normalize_key(candidate)
        if key in PYCOUNTRY_NAME_LOOKUP:
            accepted = _accept(PYCOUNTRY_NAME_LOOKUP[key])
            if accepted:
                return accepted, None
        if key in NATIVE_ALIASES:
            accepted = _accept(NATIVE_ALIASES[key])
            if accepted:
                return accepted, None

    for candidate in candidates:
        if _normalize_key(candidate) in US_STATE_TOKENS or _normalize_key(candidate) in US_COUNTY_NAMES:
            continue
        stripped = _strip_accents(candidate)
        match = COCO_REGEX.search(stripped)
        if match:
            idx = next(i for i, g in enumerate(match.groups()) if g is not None)
            accepted = _accept(COCO_NAMES[idx])
            if accepted:
                return accepted, None

    # Tier 2: unambiguous ISO alpha-2/alpha-3 codes as an isolated token.
    for candidate in candidates:
        key = _normalize_key(candidate)
        if key in ISO3_LOOKUP:
            return ISO3_LOOKUP[key], None
        if key in ISO2_LOOKUP:
            return ISO2_LOOKUP[key], None

    # Tier 3: city name lookup (population-weighted disambiguation). Whole
    # candidates only, deliberately no per-word fallback - see
    # _build_city_lookup's docstring for why (e.g. "New York" must not
    # resolve via the substring word "York", which is a real English city).
    # Returns the matched candidate itself too (see caller) since a city
    # match alone doesn't rule out a *different*, explicitly-named country
    # appearing elsewhere in the same location (e.g. "Bellevue, WA; Toronto,
    # Canada") - unless the matched city IS that "different country" name
    # (e.g. "Lebanon, Pennsylvania": the city itself is the coincidence).
    for candidate in candidates:
        key = _normalize_key(candidate)
        if key in CITY_COUNTRY:
            return ISO2_TO_NAME.get(CITY_COUNTRY[key]), candidate

    # Tier 4: US states (incl. the ambiguous codes deferred from tier 2) / counties.
    # Uses the extra "or"/"and"-split candidates too (e.g. "NY or Remote") -
    # safe here since tiers 1-3 already had a fair shot at any real country name.
    # Skips AMBIGUOUS_STATE_TOKENS (Georgia/CA/GA/IN/PA/DE/AZ/AL/CO/ID/MT/SD) -
    # those stay unresolved rather than being defaulted to "United States"
    # when nothing else in the location backs that reading up.
    for candidate in candidates + _build_loose_candidates(text):
        key = _normalize_key(candidate)
        if key in AMBIGUOUS_STATE_TOKENS:
            continue
        if key in US_STATE_TOKENS or key in US_COUNTY_NAMES:
            return "United States", None

    # Nothing confidently resolved - including any deferred Georgia/Jersey
    # match, which by itself isn't enough context either way (see
    # AMBIGUOUS_STATE_TOKENS above).
    return None, None


# ---------------------------------------------------------------------------
# Migration driver
# ---------------------------------------------------------------------------

def run(dry_run=False):
    conn = database.get_connection()
    try:
        # Ensures work_arrangement exists even on a database that was set up
        # before this column was added - safe/idempotent, see database.sql.
        database.init_schema(conn)

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, location, country, work_arrangement FROM jobs ORDER BY id")
            rows = cur.fetchall()

        total_rows = len(rows)
        updates = []          # (id, new_country, new_work_arrangement)
        samples = []          # (id, location, old_country, new_country)
        multi_country_samples = []   # (id, location, old_country) - region/multi-country rows specifically
        unknown_locations = Counter()
        final_unknown_count = 0
        multi_country_row_count = 0
        final_countries_seen = set()   # every non-NULL country this run leaves in place, computed
                                        # in-memory so the confirmation check below is accurate even
                                        # under --dry-run (where nothing is actually committed)

        for row in rows:
            location = row["location"] or ""
            old_country = row["country"]
            old_arrangement = row["work_arrangement"]
            resolved = resolve_country(location)
            arrangement = classify_work_arrangement(location)
            is_multi_country = is_ambiguous_multi_country(location)
            should_be_null = (
                _normalize_key(location) in PLACEHOLDER_LOCATIONS
                or is_multi_country
                or is_ambiguous_bare_location(location)
            )

            if is_multi_country:
                multi_country_row_count += 1
                if len(multi_country_samples) < SAMPLE_SIZE:
                    multi_country_samples.append((row["id"], location, old_country))

            if resolved is not None and (
                old_country is None or _normalize_key(old_country) != _normalize_key(resolved)
            ):
                # Missing or different from what we can now confidently derive.
                final_country = resolved
            elif resolved is None and should_be_null and old_country is not None:
                # A placeholder or ambiguous multi-country/region location
                # should never carry a single guessed country - note the
                # *location* column itself is never touched here or anywhere
                # else in this function, so the original text survives
                # unchanged regardless of what country ends up NULL.
                final_country = None
            else:
                # Either already correct, or unresolvable and left untouched
                # (never overwrite a value we can't independently verify).
                final_country = old_country if resolved is None else resolved

            country_changed = _normalize_key(final_country or "") != _normalize_key(old_country or "")
            arrangement_changed = arrangement != old_arrangement
            if country_changed or arrangement_changed:
                updates.append((row["id"], final_country, arrangement))
                if country_changed and len(samples) < SAMPLE_SIZE:
                    samples.append((row["id"], location, old_country, final_country))

            if final_country is None:
                unknown_locations[location] += 1
                final_unknown_count += 1
            else:
                final_countries_seen.add(final_country)

        if updates and not dry_run:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(
                    cur,
                    "UPDATE jobs AS j SET country = v.country, work_arrangement = v.work_arrangement "
                    "FROM (VALUES %s) AS v(id, country, work_arrangement) WHERE j.id = v.id",
                    updates,
                    template="(%s, %s, %s)",
                )
            conn.commit()
        else:
            conn.rollback()

        _safe_print("=" * 78)
        _safe_print("FINAL SUMMARY")
        _safe_print("=" * 78)
        _safe_print(f"Total rows processed: {total_rows}")
        _safe_print(f"Rows updated: {len(updates)}{' (dry run - not written)' if dry_run else ''}")
        _safe_print(f"Unknown locations (country left NULL): {final_unknown_count}")

        _safe_print(
            f"\nMulti-country / region locations detected: {multi_country_row_count} rows "
            f"across {len(_ambiguous_multi_country)} distinct location strings "
            f"(2+ named countries, e.g. \"Germany, France, Netherlands\", or a named "
            f"region/continent, e.g. \"Europe\", \"EMEA\", \"APAC\", \"LATAM\" - country "
            f"forced to NULL for all of these; original location text is never modified)."
        )

        _safe_print(f"\nTop {TOP_UNKNOWN_COUNT} remaining unknown location values:")
        for location, count in unknown_locations.most_common(TOP_UNKNOWN_COUNT):
            display = location if location else "(empty)"
            _safe_print(f"  {count:>6}  {display}")

        _safe_print(f"\nSample before/after corrections (first {len(samples)}):")
        for job_id, location, old, new in samples:
            _safe_print(f"  id={job_id}  location={location!r}  {old!r} -> {new!r}")

        _safe_print(
            f"\nSample preserved locations - multi-country/region rows "
            f"(first {len(multi_country_samples)}, location text kept exactly as-is, country -> NULL):"
        )
        for job_id, location, old in multi_country_samples:
            _safe_print(f"  id={job_id}  location={location!r}  (was country={old!r})")

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(country, 'Unknown') AS country, COUNT(*) AS job_count "
                "FROM jobs GROUP BY country ORDER BY job_count DESC LIMIT 25"
            )
            top_countries = cur.fetchall()
        _safe_print("\nTop 25 countries after normalization:")
        for country, count in top_countries:
            _safe_print(f"  {count:>6}  {country}")

        # Confirmation check, scoped to this run's actual change (region/
        # multi-country garbage specifically - NOT a general audit of every
        # country value's validity, which is a separate, pre-existing
        # concern unrelated to this migration - e.g. a single-place location
        # like "Aberdeenshire" that the resolver has never been able to
        # confidently place is left exactly as it was, same as before this
        # change, since it's neither a region term nor a multi-country
        # list). Checked from final_countries_seen (computed in-memory above
        # from every row's actual final_country) rather than re-querying the
        # database, so this is accurate under --dry-run too, where nothing
        # is committed.
        bad_countries = [
            c for c in final_countries_seen
            if _normalize_key(c) in REGION_TERMS or is_ambiguous_multi_country(c)
        ]
        if bad_countries:
            _safe_print(
                f"\nCONFIRMATION FAILED: {len(bad_countries)} distinct country value(s) "
                f"would still be region/multi-country text, not a single true country:"
            )
            for c in bad_countries:
                _safe_print(f"  {c!r}")
        else:
            _safe_print(
                f"\nConfirmed: none of the {len(final_countries_seen)} distinct country "
                f"values {'that would remain' if dry_run else 'now in the database'} is a "
                f"region/continent name (e.g. \"Europe\", \"EMEA\", \"APAC\") or an "
                f"ambiguous multi-country list - every row that named 2+ countries or a "
                f"named region now has country=NULL instead, with its original location "
                f"text preserved."
            )
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing to the database.")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
