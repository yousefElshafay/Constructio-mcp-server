from datetime import UTC, datetime
from typing import Any


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def to_iso(value: Any, fallback: str | None = None) -> str:
    if isinstance(value, datetime):
        dt_value = value.astimezone(UTC).replace(microsecond=0)
        return dt_value.isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        return value
    return fallback or now_iso()
