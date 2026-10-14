"""Normalize compensation values for comparable analytical reporting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from job_market_intelligence.ingestion.config import load_toml


@dataclass(frozen=True)
class NormalizedCompensation:
    """Derived compensation values stored alongside the source values."""

    salary_min_czk_month: Decimal | None
    salary_max_czk_month: Decimal | None


@dataclass(frozen=True)
class CompensationNormalization:
    """Configured policy for converting compensation to CZK per month."""

    target_currency: str
    target_period: str
    rate_date: date
    exchange_rates: dict[str, Decimal]
    period_factors_to_month: dict[str, Decimal]

    @classmethod
    def from_file(cls, config_path: Path) -> CompensationNormalization:
        """Load and validate a compensation normalization configuration."""
        config = load_toml(config_path)
        target = _section(config, "target")
        fx = _section(config, "fx")
        rates = _section(fx, "rates")
        period_factors = _section(config, "period_factors_to_month")

        target_currency = _required_text(target, "currency").upper()
        target_period = _required_text(target, "period").lower()
        if (target_currency, target_period) != ("CZK", "month"):
            raise ValueError(
                "Compensation normalization currently supports only CZK per month"
            )

        rate_date_value = fx.get("rate_date")
        if isinstance(rate_date_value, datetime):
            rate_date = rate_date_value.date()
        elif isinstance(rate_date_value, date):
            rate_date = rate_date_value
        elif isinstance(rate_date_value, str):
            try:
                rate_date = date.fromisoformat(rate_date_value)
            except ValueError as error:
                raise ValueError("fx.rate_date must be an ISO date") from error
        else:
            raise TypeError("Missing or invalid fx.rate_date")

        exchange_rates = {
            str(currency).upper(): _decimal(value, f"fx.rates.{currency}")
            for currency, value in rates.items()
        }
        if target_currency not in exchange_rates:
            raise ValueError(
                f"Missing exchange rate for target currency {target_currency}"
            )
        if exchange_rates[target_currency] != Decimal(1):
            raise ValueError("The CZK target exchange rate must be exactly 1")

        factors = {
            str(period).lower(): _decimal(value, f"period_factors_to_month.{period}")
            for period, value in period_factors.items()
        }
        if target_period not in factors:
            raise ValueError(f"Missing period factor for target period {target_period}")

        return cls(
            target_currency=target_currency,
            target_period=target_period,
            rate_date=rate_date,
            exchange_rates=exchange_rates,
            period_factors_to_month=factors,
        )

    def normalize(
        self,
        salary_min: Decimal | None,
        salary_max: Decimal | None,
        salary_currency: str | None,
        salary_period: str | None,
    ) -> NormalizedCompensation:
        """Convert one source compensation option to CZK per month."""
        if salary_min is None and salary_max is None:
            return _not_comparable()
        if salary_min is not None and salary_min < 0:
            raise ValueError("salary_min cannot be negative")
        if salary_max is not None and salary_max < 0:
            raise ValueError("salary_max cannot be negative")
        if (
            salary_min is not None
            and salary_max is not None
            and salary_max < salary_min
        ):
            raise ValueError("salary_max cannot be lower than salary_min")

        currency = salary_currency.upper() if salary_currency else None
        period = salary_period.lower() if salary_period else None
        if (
            currency not in self.exchange_rates
            or period not in self.period_factors_to_month
        ):
            return _not_comparable()

        multiplier = (
            self.exchange_rates[currency] * self.period_factors_to_month[period]
        )
        return NormalizedCompensation(
            salary_min_czk_month=_quantize(salary_min * multiplier)
            if salary_min is not None
            else None,
            salary_max_czk_month=_quantize(salary_max * multiplier)
            if salary_max is not None
            else None,
        )


def _section(value: dict[str, Any], name: str) -> dict[str, Any]:
    section = value.get(name)
    if not isinstance(section, dict):
        raise TypeError(f"Configuration section '{name}' is missing or invalid")
    return section


def _required_text(section: dict[str, Any], name: str) -> str:
    value = section.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Configuration value '{name}' is missing or invalid")
    return value.strip()


def _decimal(value: Any, name: str) -> Decimal:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Configuration value '{name}' is not numeric") from error
    if decimal <= 0:
        raise ValueError(f"Configuration value '{name}' must be positive")
    return decimal


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _not_comparable() -> NormalizedCompensation:
    return NormalizedCompensation(
        salary_min_czk_month=None,
        salary_max_czk_month=None,
    )
