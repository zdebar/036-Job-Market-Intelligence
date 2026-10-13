"""Common extraction and normalization support for provider parsers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

from job_market_intelligence.processing.extraction import extract_hours
from job_market_intelligence.processing.models import (
    EmploymentOption,
    SkillRequirement,
)
from job_market_intelligence.processing.normalization import (
    NormalizationDictionaries,
)
from job_market_intelligence.processing.utils import optional_text
from job_market_intelligence.processing.validation import HoursValidationRules


class ParserSupport:
    """Reusable configuration-backed helpers shared by all source parsers."""

    def __init__(self, project_root: Path) -> None:
        self.normalization = NormalizationDictionaries.from_project_root(project_root)
        self.hours_rules = HoursValidationRules.from_file(
            project_root / "config" / "validation.toml"
        )

    @staticmethod
    def text_value(value: Any) -> str | None:
        """Return text for scalar provider values."""
        if isinstance(value, Mapping):
            for key in ("name", "value", "text", "label", "title"):
                text = optional_text(value.get(key))
                if text:
                    return text
            return None
        return optional_text(value)

    def company_name(self, value: Any, fallback: str | None = None) -> str:
        text = self.text_value(value) or fallback
        if not text:
            raise ValueError("Company name is missing")
        return self.normalization.companies.find_first(text) or text

    def role_name(self, text: str) -> str | None:
        return self.normalization.roles.find_first(text)

    def seniority_level(self, text: str) -> str | None:
        return self.normalization.seniority_levels.find_first(text)

    def departments(self, values: Iterable[Any]) -> tuple[str, ...]:
        result: list[str] = []
        for value in values:
            text = self.text_value(value)
            if text:
                result.extend(self.normalization.departments.find_all(text))
        return tuple(dict.fromkeys(result))

    def locations(self, values: Iterable[Any]) -> tuple[str, ...]:
        result: list[str] = []
        for value in values:
            text = self.text_value(value)
            if text:
                result.extend(self.normalization.locations.find_non_overlapping(text))
        return tuple(dict.fromkeys(result))

    def work_modes(self, values: Iterable[Any]) -> tuple[str, ...]:
        text = " | ".join(
            value for value in (self.text_value(item) for item in values) if value
        )
        if not text:
            return ()
        return self.normalization.work_modes.find_all(text)

    def skills(self, text: str) -> tuple[SkillRequirement, ...]:
        return tuple(
            SkillRequirement(name=name)
            for name in self.normalization.skills.find_non_overlapping(text)
        )

    def employment_options(self, text: str) -> tuple[EmploymentOption, ...]:
        relation = self.normalization.employment_relations.find_first(text)
        workload = self.normalization.workloads.find_first(text)
        hours_min, hours_max, hours_period = extract_hours(text)
        if hours_period is None and hours_min is not None:
            hours_period = "week"
        self.hours_rules.validate(hours_min, hours_max, hours_period)
        if not any((relation, workload, hours_min, hours_max)):
            return ()
        return (
            EmploymentOption(
                employment_relation_name=relation,
                workload_name=workload,
                hours_min=hours_min,
                hours_max=hours_max,
                hours_period=hours_period,
            ),
        )

    @staticmethod
    def compensation(
        value: Mapping[str, Any] | None,
    ) -> tuple[Decimal | None, Decimal | None, str | None, str | None]:
        if not value:
            return None, None, None, None
        minimum = value.get("min", value.get("minimum", value.get("salaryMin")))
        maximum = value.get("max", value.get("maximum", value.get("salaryMax")))
        currency = optional_text(value.get("currency", value.get("salaryCurrency")))
        period = optional_text(value.get("period", value.get("salaryPeriod")))
        return (
            _decimal(minimum),
            _decimal(maximum),
            currency.upper() if currency else None,
            period.casefold() if period else None,
        )


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value).replace(",", "."))


def flatten_text(value: Any) -> str:
    """Flatten nested provider values into searchable text."""
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)
