"""Typed records exchanged by extraction, normalization, and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class SkillRequirement:
    """A normalized skill mention."""

    name: str
    proficiency_level_name: str | None = None
    requirement_type_name: str | None = None
    priority: int | None = None


@dataclass(frozen=True)
class EmploymentOption:
    """Normalized employment relation and workload information."""

    employment_relation_name: str | None = None
    workload_name: str | None = None
    hours_min: Decimal | None = None
    hours_max: Decimal | None = None
    hours_period: str | None = None


@dataclass(frozen=True)
class CompensationOption:
    """Normalized compensation information."""

    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str | None = None
    salary_period: str | None = None


@dataclass(frozen=True)
class ParsedJobPosting:
    """One normalized job posting extracted from a provider payload."""

    source_job_id: str
    company_name: str
    role_name: str | None
    seniority_level_name: str | None
    source_url: str | None
    source_published_at: datetime | None
    source_updated_at: datetime | None
    raw_advertisement: dict[str, Any]
    content_fingerprint: str | None = None
    departments: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    work_modes: tuple[str, ...] = ()
    employment_options: tuple[EmploymentOption, ...] = ()
    compensation_options: tuple[CompensationOption, ...] = ()
    skill_requirements: tuple[SkillRequirement, ...] = ()


@dataclass(frozen=True)
class RecordError:
    """A record-level error that can be stored without stopping the run."""

    source_job_id: str | None
    stage: str
    error_type: str
    error_message: str


@dataclass(frozen=True)
class ParseResult:
    """Successful records and recoverable record errors from one raw response."""

    records: tuple[ParsedJobPosting, ...]
    errors: tuple[RecordError, ...]
