"""Extraction of structured values from provider text."""

from __future__ import annotations

import re
from decimal import Decimal

from job_market_intelligence.processing.validation import decimal_value

HOURS_PATTERN = re.compile(
    r"(?P<minimum>\d+(?:[.,]\d+)?)?\s*(?:-|–|to)?\s*"
    r"(?P<maximum>\d+(?:[.,]\d+)?)?\s*(?:hours?|hodin?)\s*"
    r"(?:per\s+(?P<period>day|week|month|year)|/(?P<slash_period>day|week|month|year))?",
    flags=re.IGNORECASE,
)


def normalize_hours_period(value: str | None) -> str | None:
    """Normalize an hours period to the database vocabulary."""
    if not value:
        return None
    return value.casefold().removesuffix("s")


def extract_hours(
    text: str,
) -> tuple[Decimal | None, Decimal | None, str | None]:
    """Extract the first hours range from text."""
    match = HOURS_PATTERN.search(text)
    if not match:
        return None, None, None

    minimum = decimal_value(match.group("minimum"))
    maximum = decimal_value(match.group("maximum"))
    if minimum is None and maximum is not None:
        minimum = maximum
    if maximum is None and minimum is not None:
        maximum = minimum
    period = normalize_hours_period(
        match.group("period") or match.group("slash_period")
    )
    return minimum, maximum, period
