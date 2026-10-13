"""Lever extraction and normalization."""

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


class LeverParser:
    """Parse Lever's postings list response."""

    def __init__(self, project_root: Path) -> None:
        self.support = ParserSupport(project_root)

    def parse(
        self, payload: Mapping[str, Any] | list[Any], metadata: Mapping[str, Any]
    ) -> ParseResult:
        postings = (
            payload
            if isinstance(payload, list)
            else payload.get("postings", payload.get("jobs", []))
        )
        if not isinstance(postings, list):
            raise TypeError("Lever payload does not contain a postings list")
        records: list[ParsedJobPosting] = []
        errors: list[RecordError] = []
        for posting in postings:
            try:
                if not isinstance(posting, Mapping):
                    raise TypeError("Lever posting is not an object")
                records.append(self._parse_posting(posting, metadata))
            except (TypeError, ValueError, KeyError) as error:
                errors.append(
                    RecordError(
                        source_job_id=optional_text(posting.get("id"))
                        if isinstance(posting, Mapping)
                        else None,
                        stage="extraction",
                        error_type=type(error).__name__,
                        error_message=str(error),
                    )
                )
        return ParseResult(records=tuple(records), errors=tuple(errors))

    def _parse_posting(
        self,
        posting: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> ParsedJobPosting:
        source_job_id = optional_text(posting.get("id"))
        if not source_job_id:
            raise ValueError("Lever posting id is missing")
        categories = posting.get("categories")
        categories = categories if isinstance(categories, Mapping) else {}
        title = optional_text(posting.get("text")) or ""
        description = (
            optional_text(posting.get("descriptionPlain"))
            or optional_text(posting.get("description"))
            or optional_text(posting.get("descriptionHtml"))
            or ""
        )
        category_text = flatten_text(categories)
        searchable_text = f"{title} {description} {category_text}"
        location_values = [categories.get("location"), categories.get("allLocations")]
        department_values = [categories.get("department"), categories.get("team")]
        work_mode_values = [categories.get("workplaceType"), searchable_text]

        company = self.support.company_name(
            metadata.get("company") or metadata.get("company_name")
        )
        return ParsedJobPosting(
            source_job_id=source_job_id,
            company_name=company,
            role_name=self.support.role_name(title),
            seniority_level_name=self.support.seniority_level(title),
            source_url=optional_text(
                posting.get("hostedUrl") or posting.get("applyUrl")
            ),
            source_published_at=parse_datetime(posting.get("createdAt")),
            source_updated_at=parse_datetime(posting.get("updatedAt")),
            raw_advertisement=dict(posting),
            content_fingerprint=content_fingerprint(description),
            departments=self.support.departments(department_values),
            locations=self.support.locations(_flatten_values(location_values)),
            work_modes=self.support.work_modes(work_mode_values),
            employment_options=self.support.employment_options(searchable_text),
            compensation_options=_compensation_options(posting),
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


def _compensation_options(posting: Mapping[str, Any]) -> tuple[CompensationOption, ...]:
    value = posting.get("salaryRange") or posting.get("salary_range")
    if not isinstance(value, Mapping):
        return ()
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
