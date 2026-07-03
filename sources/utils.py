"""Small helpers shared across job source implementations."""

import time
from datetime import datetime, timezone

import requests


def timestamp_to_iso_date(unix_timestamp):
    """Convert a Unix timestamp (seconds) to an ISO 8601 date string ("YYYY-MM-DD")."""
    if not unix_timestamp:
        return ""

    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc).strftime("%Y-%m-%d")


def iso_string_to_date(date_string):
    """Convert an ISO 8601 datetime string (e.g. "2026-07-01T02:13:51+00:00") to "YYYY-MM-DD"."""
    if not date_string:
        return ""

    try:
        return datetime.fromisoformat(date_string).strftime("%Y-%m-%d")
    except ValueError:
        # Best-effort fallback if the source ever sends a non-standard format.
        return date_string[:10]


def uk_date_to_iso(date_string):
    """Convert a UK-style "DD/MM/YYYY" date string to ISO "YYYY-MM-DD"."""
    if not date_string:
        return ""

    try:
        return datetime.strptime(date_string, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def dedupe_tags(*tag_lists):
    """Merge multiple tag lists into one, dropping empties and preserving order."""
    merged = []
    for tags in tag_lists:
        merged.extend(tags or [])
    return list(dict.fromkeys(merged))


# HTTP statuses worth retrying: rate limiting and server-side errors, all
# of which can plausibly succeed on a later attempt. Anything else (bad
# request, bad/missing credentials, not found, etc.) is a permanent
# problem retrying won't fix, so it's raised immediately instead.
_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def request_with_retry(method, url, *, max_attempts=3, backoff_seconds=2, **kwargs):
    """
    Call a `requests` method (e.g. `requests.get`, `requests.post`) with
    retries for transient failures only: connection errors, timeouts, and
    HTTP 429/500/502/503/504. Uses exponential backoff between attempts
    (2s, 4s, ... for the default backoff_seconds=2).

    Any other HTTP error status (400/401/402/403/404/etc.) is raised
    immediately without retrying. After the final attempt fails, the
    underlying exception is raised as-is, so a caller's existing
    try/except around the request keeps working unchanged.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            response = method(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status not in _RETRYABLE_STATUS_CODES or attempt == max_attempts:
                raise
        except (requests.ConnectionError, requests.Timeout):
            if attempt == max_attempts:
                raise

        time.sleep(backoff_seconds * (2 ** (attempt - 1)))
