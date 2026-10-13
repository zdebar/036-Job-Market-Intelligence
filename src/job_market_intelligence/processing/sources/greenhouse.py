"""Greenhouse extraction and normalization."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from job_market_intelligence.processing.fingerprint import content_fingerprint
from job_market_intelligence.processing.models import (
    CompensationOption,
    ParsedJobPosting,
    ParseResult,
    RecordError,
)
from job_market_intelligence.processing.sources.common import (
    ParserSupport,
    flatten_text,
)
from job_market_intelligence.processing.utils import optional_text, parse_datetime


class GreenhouseParser:
    """Parse the Greenhouse board jobs response."""

    def __init__(self, project_root: Path) -> None:
        self.support = ParserSupport(project_root)

    def parse(
        self, payload: Mapping[str, Any], metadata: Mapping[str, Any]
    ) -> ParseResult:
        jobs = payload.get("jobs", [])
        if not isinstance(jobs, list):
            raise TypeError("Greenhouse payload does not contain a jobs list")
        records: list[ParsedJobPosting] = []
        errors: list[RecordError] = []
        for job in jobs:
            try:
                if not isinstance(job, Mapping):
                    raise TypeError("Greenhouse job is not an object")
                records.append(self._parse_job(job, metadata))
            except (TypeError, ValueError, KeyError) as error:
                errors.append(
                    RecordError(
                        source_job_id=optional_text(job.get("id"))
                        if isinstance(job, Mapping)
                        else None,
                        stage="extraction",
                        error_type=type(error).__name__,
                        error_message=str(error),
                    )
                )
        return ParseResult(records=tuple(records), errors=tuple(errors))

    def _parse_job(
        self,
        job: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> ParsedJobPosting:
        source_job_id = optional_text(job.get("id"))
        if not source_job_id:
            raise ValueError("Greenhouse job id is missing")
        title = optional_text(job.get("title")) or ""
        description = (
            optional_text(job.get("content"))
            or optional_text(job.get("description"))
            or ""
        )
        metadata_values = _greenhouse_metadata(job.get("metadata"))
        searchable_text = " ".join((title, description, *metadata_values))

        locations: list[Any] = []
        if job.get("location") is not None:
            locations.append(job["location"])
        offices = job.get("offices", [])
        if isinstance(offices, list):
            locations.extend(
                office.get("location")
                for office in offices
                if isinstance(office, Mapping) and office.get("location")
            )

        departments: list[Any] = []
        source_departments = job.get("departments", [])
        if isinstance(source_departments, list):
            departments.extend(source_departments)
        departments.extend(
            value for value in metadata_values if "department" in value.casefold()
        )

        company = self.support.company_name(
            metadata.get("company") or metadata.get("company_name")
        )
        return ParsedJobPosting(
            source_job_id=source_job_id,
            company_name=company,
            role_name=self.support.role_name(title),
            seniority_level_name=self.support.seniority_level(title),
            source_url=optional_text(job.get("absolute_url")),
            source_published_at=parse_datetime(
                job.get("first_published") or job.get("first_published_at")
            ),
            source_updated_at=parse_datetime(job.get("updated_at")),
            raw_advertisement=dict(job),
            content_fingerprint=content_fingerprint(description),
            departments=self.support.departments(departments),
            locations=self.support.locations(locations),
            work_modes=self.support.work_modes([*metadata_values, description]),
            employment_options=self.support.employment_options(searchable_text),
            compensation_options=_compensation_options(job),
            skill_requirements=self.support.skills(description),
        )


def _greenhouse_metadata(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        name = optional_text(item.get("name"))
        item_value = flatten_text(item.get("value"))
        if name and item_value:
            result.append(f"{name}: {item_value}")
        elif item_value:
            result.append(item_value)
    return result


def _compensation_options(job: Mapping[str, Any]) -> tuple[CompensationOption, ...]:
    value = job.get("pay_transparency") or job.get("compensation")
    if not isinstance(value, Mapping):
        return ()
    minimum = value.get("min", value.get("minimum"))
    maximum = value.get("max", value.get("maximum"))
    if minimum is None and maximum is None:
        return ()
    from job_market_intelligence.processing.sources.common import ParserSupport

    salary_min, salary_max, currency, period = ParserSupport.compensation(value)
    return (
        CompensationOption(
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            salary_period=period,
        ),
    )
