"""Small helpers shared across job source implementations."""

from datetime import datetime, timezone


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


def dedupe_tags(*tag_lists):
    """Merge multiple tag lists into one, dropping empties and preserving order."""
    merged = []
    for tags in tag_lists:
        merged.extend(tags or [])
    return list(dict.fromkeys(merged))
