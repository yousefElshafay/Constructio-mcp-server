from datetime import UTC, datetime


def now_iso() -> str:
    """Returns current UTC time in ISO 8601 format."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_iso(dt: datetime | str | None) -> str | None:
    """Converts datetime or string to ISO 8601 string, or None."""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
