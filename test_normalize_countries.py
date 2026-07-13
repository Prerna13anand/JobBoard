"""
Regression tests for normalize_countries.py.

Pure-function tests only - no database connection, no network calls, no
provider re-runs. Run with:

    python test_normalize_countries.py

Exits non-zero (and prints every failure) if any case regresses.
"""

import sys

import normalize_countries as nc


CASES = [
    # --- New behavior: multi-country / region locations must resolve to
    # None (and be flagged by is_ambiguous_multi_country) -----------------
    ("US/Canada", None, True),
    ("Canada & United States", None, True),
    ("Germany, France, Netherlands", None, True),
    ("Europe", None, True),
    ("EMEA", None, True),
    ("APAC", None, True),
    ("LATAM", None, True),
    ("Worldwide", None, False),  # placeholder tier, not multi-country tier
    ("Remote (US/Canada)", None, True),
    ("Remote (Europe)", None, True),
    ("Remote - Europe", None, True),
    ("Europe - Remote", None, True),
    ("Remote, Europe", None, True),
    ("Americas Remote", None, True),
    ("EMEA Remote", None, True),
    ("Remote - EMEA", None, True),
    ("North America", None, True),
    ("Remote (North America)", None, True),
    ("South America", None, True),
    ("Remote-North & South America", None, True),
    ("Remote - European Union", None, True),   # was wrongly "United States" before this fix
    ("CA - Canada; US - United States", None, True),  # was wrongly "United States" before this fix
    ("Canada, United States", None, True),
    ("Australia, Canada, India, United Kingdom, United States", None, True),
    ("EMEA,  LATAM,  Canada,  USA", None, True),
    ("Worldwide, North America, South America, Asia, Europe, Africa, Oceania", None, True),

    # --- Safety net: must NOT be misclassified as multi-country/region ----
    ("South Africa", "South Africa", False),
    ("Cape Town, WC, South Africa", "South Africa", False),
    ("Guinea-Bissau", "Guinea-Bissau", False),
    ("Bosnia and Herzegovina", "Bosnia and Herzegovina", False),
    ("Timor-Leste", "Timor-Leste", False),

    # --- Existing, already-correct behavior must be unchanged -------------
    ("Atlanta, GA", "United States", False),
    ("Atlanta, Georgia", "United States", False),
    ("Paris, France", "France", False),
    ("London, UK", "United Kingdom", False),
    ("Bangalore, India", "India", False),
    ("Lebanon, TN, United States", "United States", False),
    ("GB-London", "United Kingdom", False),
    ("Frimley, GU16 7UJ", "United Kingdom", False),   # UK postcode tier
    ("83 - COGOLIN", "France", False),                # French dept code tier
    ("Remote", None, False),                          # placeholder tier
    ("Georgia", None, False),                         # ambiguous bare state/country
    ("CA", None, False),                              # ambiguous bare state/country
]


def main():
    failures = []
    for location, expected_country, expected_ambiguous in CASES:
        nc._resolve_cache.clear()
        nc._ambiguous_multi_country.clear()
        resolved = nc.resolve_country(location)
        ambiguous = nc.is_ambiguous_multi_country(location)
        if resolved != expected_country or ambiguous != expected_ambiguous:
            failures.append(
                f"  {location!r}: expected (country={expected_country!r}, "
                f"ambiguous={expected_ambiguous}), got (country={resolved!r}, "
                f"ambiguous={ambiguous})"
            )

    # work_arrangement must stay independent of the country/ambiguity result
    wa_cases = [
        ("Remote (US/Canada)", "remote"),
        ("Remote (Europe)", "remote"),
        ("EMEA Remote", "remote"),
        ("Hybrid - EMEA", "hybrid"),
        ("Europe", None),
        ("Atlanta, GA", None),
    ]
    for location, expected in wa_cases:
        got = nc.classify_work_arrangement(location)
        if got != expected:
            failures.append(
                f"  work_arrangement({location!r}): expected {expected!r}, got {got!r}"
            )

    print(f"{len(CASES) + len(wa_cases)} cases checked, {len(failures)} failed.\n")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("All regression tests passed.")


if __name__ == "__main__":
    main()
