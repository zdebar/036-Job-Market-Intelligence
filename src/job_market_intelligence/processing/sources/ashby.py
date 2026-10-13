"""Ashby extraction and normalization."""

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


class AshbyParser:
    """Parse Ashby's public job board response."""

    def __init__(self, project_root: Path) -> None:
        self.support = ParserSupport(project_root)

    def parse(
        self, payload: Mapping[str, Any], metadata: Mapping[str, Any]
    ) -> ParseResult:
        jobs = payload.get("jobs", [])
        if not isinstance(jobs, list):
            raise TypeError("Ashby payload does not contain a jobs list")
        records: list[ParsedJobPosting] = []
        errors: list[RecordError] = []
        for job in jobs:
            try:
                if not isinstance(job, Mapping):
                    raise TypeError("Ashby job is not an object")
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
        source_job_id = optional_text(job.get("id") or job.get("jobId"))
        if not source_job_id:
            raise ValueError("Ashby job id is missing")
        title = optional_text(job.get("title")) or ""
        description = (
            optional_text(job.get("descriptionPlain"))
            or optional_text(job.get("descriptionHtml"))
            or optional_text(job.get("description"))
            or ""
        )
        searchable_text = " ".join(
            (title, description, flatten_text(job.get("employmentType")))
        )
        locations = [job.get("location"), job.get("secondaryLocations")]
        workplace = [job.get("workplaceType")]
        if job.get("isRemote") is True:
            workplace.append("Remote")
        company = self.support.company_name(
            metadata.get("company") or metadata.get("company_name")
        )
        return ParsedJobPosting(
            source_job_id=source_job_id,
            company_name=company,
            role_name=self.support.role_name(title),
            seniority_level_name=self.support.seniority_level(title),
            source_url=optional_text(job.get("jobUrl") or job.get("applyUrl")),
            source_published_at=parse_datetime(job.get("publishedAt")),
            source_updated_at=parse_datetime(job.get("updatedAt")),
            raw_advertisement=dict(job),
            content_fingerprint=content_fingerprint(description),
            departments=self.support.departments([job.get("department")]),
            locations=self.support.locations(_flatten_values(locations)),
            work_modes=self.support.work_modes([*workplace, description]),
            employment_options=self.support.employment_options(searchable_text),
            compensation_options=_compensation_options(job),
            skill_requirements=self.support.skills(description),
        )


def _flatten_values(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    for value in values:
        if isinstance(value, list):
            result.extend(value)
        elif value is not None:
            result.append(value)
    return result


def _compensation_options(job: Mapping[str, Any]) -> tuple[CompensationOption, ...]:
    value = job.get("compensation") or job.get("compensationRange")
    if not isinstance(value, Mapping):
        return ()
    if isinstance(value.get("range"), Mapping):
        value = value["range"]
    from job_market_intelligence.processing.sources.common import ParserSupport

    salary_min, salary_max, currency, period = ParserSupport.compensation(value)
    if salary_min is None and salary_max is None:
        return ()
    return (
        CompensationOption(
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            salary_period=period,
        ),
    )
