from decimal import Decimal
from pathlib import Path

from job_market_intelligence.processing.compensation import CompensationNormalization

PROJECT_ROOT = Path(__file__).parents[1]


def _normalizer() -> CompensationNormalization:
    return CompensationNormalization.from_file(
        PROJECT_ROOT / "config" / "compensation.toml"
    )


def test_normalizes_eur_year_to_czk_month() -> None:
    result = _normalizer().normalize(Decimal(1200), Decimal(1800), "EUR", "year")

    assert result.salary_min_czk_month == Decimal("2437.50")
    assert result.salary_max_czk_month == Decimal("3656.25")
    assert _normalizer().rate_date.isoformat() == "2026-10-13"


def test_czk_month_is_normalized_without_conversion() -> None:
    result = _normalizer().normalize(Decimal(50000), Decimal(70000), "CZK", "month")

    assert result.salary_min_czk_month == Decimal("50000.00")
    assert result.salary_max_czk_month == Decimal("70000.00")


def test_missing_bound_is_partial() -> None:
    result = _normalizer().normalize(Decimal(100), None, "USD", "hour")

    assert result.salary_min_czk_month == Decimal("377658.67")
    assert result.salary_max_czk_month is None


def test_unknown_currency_is_not_comparable() -> None:
    result = _normalizer().normalize(Decimal(100), Decimal(200), "XXX", "month")

    assert result.salary_min_czk_month is None
    assert result.salary_max_czk_month is None
