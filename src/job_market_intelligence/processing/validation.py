"""Validation rules for extracted job attributes."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from job_market_intelligence.ingestion.config import load_toml


@dataclass(frozen=True)
class HoursValidationRules:
    """Maximum accepted hours by period."""

    maximums: dict[str, Decimal]

    @classmethod
    def from_file(cls, path: Path) -> HoursValidationRules:
        config = load_toml(path)
        values = config.get("hours", {})
        if not isinstance(values, dict):
            raise TypeError(f"Expected an [hours] section in {path}")
        return cls(
            maximums={
                period.removeprefix("max_"): Decimal(str(value))
                for period, value in values.items()
                if str(period).startswith("max_")
            }
        )

    def validate(
        self,
        hours_min: Decimal | None,
        hours_max: Decimal | None,
        period: str | None,
    ) -> None:
        """Raise ``ValueError`` when the hours range is invalid."""
        if hours_min is not None and hours_min < 0:
            raise ValueError("Minimum hours cannot be negative")
        if hours_max is not None and hours_max < 0:
            raise ValueError("Maximum hours cannot be negative")
        if hours_min is not None and hours_max is not None and hours_max < hours_min:
            raise ValueError("Maximum hours cannot be lower than minimum hours")
        if period in self.maximums:
            maximum = self.maximums[period]
            if hours_min is not None and hours_min > maximum:
                raise ValueError(f"Minimum hours exceed the {period} limit")
            if hours_max is not None and hours_max > maximum:
                raise ValueError(f"Maximum hours exceed the {period} limit")


def decimal_value(value: Any) -> Decimal | None:
    """Convert a numeric value to ``Decimal`` without accepting invalid text."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace(",", ".").strip())
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Invalid decimal value: {value!r}") from error
