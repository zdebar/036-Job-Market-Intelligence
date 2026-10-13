"""Small parsing helpers shared by source adapters."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def optional_text(value: Any) -> str | None:
    """Return stripped text or ``None`` for an empty value."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_datetime(value: Any) -> datetime | None:
    """Parse ISO-8601 strings and Unix seconds/milliseconds."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if abs(timestamp) > 10_000_000_000:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp, tz=UTC)

    text = optional_text(value)
    if text is None:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
