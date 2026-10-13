"""Database persistence for normalized job postings."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from psycopg import Connection, sql
from psycopg.types.json import Jsonb

from job_market_intelligence.processing.models import (
    CompensationOption,
    EmploymentOption,
    ParsedJobPosting,
    RecordError,
    SkillRequirement,
)


class ProcessingRepository:
    """Persist one processing run using the 036 database schema."""

    def __init__(self, connection: Connection[Any]) -> None:
        self.connection = connection

    def register_raw_run(
        self,
        *,
        source_key: str,
        run_id: str,
        raw_path: str,
        retrieved_at: datetime | None,
        record_count: int | None,
        payload_sha256: str | None,
    ) -> tuple[int, str]:
        row = self.connection.execute(
            """
            INSERT INTO raw_ingestion_runs (
                source_id, run_id, raw_path, retrieved_at, record_count,
                payload_sha256, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            ON CONFLICT (source_id, run_id) DO UPDATE SET
                raw_path = EXCLUDED.raw_path,
                retrieved_at = EXCLUDED.retrieved_at,
                record_count = EXCLUDED.record_count,
                payload_sha256 = EXCLUDED.payload_sha256,
                status = CASE
                    WHEN raw_ingestion_runs.status = 'processed'
                    THEN raw_ingestion_runs.status
                    ELSE 'pending'
                END,
                updated_at = now()
            RETURNING id, status
            """,
            (
                source_key,
                run_id,
                raw_path,
                retrieved_at,
                record_count,
                payload_sha256,
            ),
        ).fetchone()
        if row is None:
            raise RuntimeError("Could not register raw ingestion run")
        return int(row[0]), str(row[1])

    def mark_processing(self, run_id: int) -> None:
        self.connection.execute(
            """
            UPDATE raw_ingestion_runs
            SET status = 'processing', processing_started_at = now(), updated_at = now()
            WHERE id = %s
            """,
            (run_id,),
        )

    def mark_processed(self, run_id: int, processed_records: int) -> None:
        self.connection.execute(
            """
            UPDATE raw_ingestion_runs
            SET status = 'processed', processed_records = %s,
                processed_at = now(), updated_at = now(), error_message = NULL
            WHERE id = %s
            """,
            (processed_records, run_id),
        )

    def mark_partial(self, run_id: int, processed_records: int) -> None:
        self.connection.execute(
            """
            UPDATE raw_ingestion_runs
            SET status = 'partial', processed_records = %s,
                processed_at = now(), updated_at = now()
            WHERE id = %s
            """,
            (processed_records, run_id),
        )

    def mark_failed(self, run_id: int, error_message: str) -> None:
        self.connection.execute(
            """
            UPDATE raw_ingestion_runs
            SET status = 'failed', error_message = %s, updated_at = now()
            WHERE id = %s
            """,
            (error_message[:4000], run_id),
        )

    def record_error(self, run_id: int, error: RecordError) -> None:
        self.connection.execute(
            """
            INSERT INTO raw_ingestion_record_errors (
                raw_ingestion_run_id, source_job_id, stage, error_type, error_message
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                run_id,
                error.source_job_id,
                error.stage,
                error.error_type,
                error.error_message[:4000],
            ),
        )

    def upsert_job_posting(
        self,
        *,
        source_key: str,
        record: ParsedJobPosting,
        retrieved_at: datetime,
    ) -> int:
        source_id = self._required_id("sources", "source_key", source_key)
        company_id = self._required_id("companies", "name", record.company_name)
        role_id = self._optional_id("roles", "name", record.role_name)
        seniority_id = self._optional_id(
            "seniority_levels", "name", record.seniority_level_name
        )
        row = self.connection.execute(
            """
            INSERT INTO job_postings (
                source_id, source_job_id, company_id, role_id, seniority_level_id,
                raw_advertisement, content_fingerprint, source_url,
                source_published_at, source_updated_at, retrieved_at, last_seen_at,
                status, normalization_version
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, 'active', 'v1'
            )
            ON CONFLICT (source_id, source_job_id) DO UPDATE SET
                company_id = EXCLUDED.company_id,
                role_id = EXCLUDED.role_id,
                seniority_level_id = EXCLUDED.seniority_level_id,
                raw_advertisement = EXCLUDED.raw_advertisement,
                content_fingerprint = EXCLUDED.content_fingerprint,
                source_url = EXCLUDED.source_url,
                source_published_at = EXCLUDED.source_published_at,
                source_updated_at = EXCLUDED.source_updated_at,
                retrieved_at = EXCLUDED.retrieved_at,
                last_seen_at = EXCLUDED.last_seen_at,
                status = 'active',
                normalization_version = EXCLUDED.normalization_version,
                updated_at = now()
            RETURNING id
            """,
            (
                source_id,
                record.source_job_id,
                company_id,
                role_id,
                seniority_id,
                Jsonb(record.raw_advertisement),
                record.content_fingerprint,
                record.source_url,
                record.source_published_at,
                record.source_updated_at,
                retrieved_at,
                retrieved_at,
            ),
        ).fetchone()
        if row is None:
            raise RuntimeError("Could not upsert job posting")
        posting_id = int(row[0])
        self._replace_child_records(posting_id, record)
        return posting_id

    def mark_missing_postings_inactive(
        self,
        *,
        source_key: str,
        retrieved_at: datetime,
    ) -> None:
        self.connection.execute(
            """
            UPDATE job_postings
            SET status = 'inactive', updated_at = now()
            WHERE source_id = (SELECT id FROM sources WHERE source_key = %s)
              AND status = 'active'
              AND last_seen_at < %s
            """,
            (source_key, retrieved_at),
        )

    def _replace_child_records(
        self,
        posting_id: int,
        record: ParsedJobPosting,
    ) -> None:
        self._clear_child_records(posting_id)
        self._insert_reference_links(
            posting_id,
            record.locations,
            relation_table="job_posting_locations",
            relation_column="location_id",
            reference_table="locations",
        )
        self._insert_reference_links(
            posting_id,
            record.departments,
            relation_table="job_posting_departments",
            relation_column="department_id",
            reference_table="departments",
        )
        self._insert_reference_links(
            posting_id,
            record.work_modes,
            relation_table="job_posting_work_modes",
            relation_column="work_mode_id",
            reference_table="work_modes",
        )
        self._insert_employment_options(posting_id, record.employment_options)
        self._insert_skill_requirements(posting_id, record.skill_requirements)
        self._insert_compensations(posting_id, record.compensation_options)

    def _clear_child_records(self, posting_id: int) -> None:
        for table in (
            "job_posting_locations",
            "job_posting_departments",
            "job_posting_work_modes",
            "job_posting_employment_options",
            "job_skill_requirements",
            "job_posting_compensations",
        ):
            self.connection.execute(
                sql.SQL("DELETE FROM {} WHERE job_posting_id = %s").format(
                    sql.Identifier(table)
                ),
                (posting_id,),
            )

    def _insert_reference_links(
        self,
        posting_id: int,
        names: Iterable[str],
        *,
        relation_table: str,
        relation_column: str,
        reference_table: str,
    ) -> None:
        for name in names:
            reference_id = self._optional_id(reference_table, "name", name)
            if reference_id is None:
                continue
            statement = sql.SQL(
                "INSERT INTO {} (job_posting_id, {}) VALUES (%s, %s)"
            ).format(sql.Identifier(relation_table), sql.Identifier(relation_column))
            self.connection.execute(statement, (posting_id, reference_id))

    def _insert_employment_options(
        self,
        posting_id: int,
        options: Iterable[EmploymentOption],
    ) -> None:
        for option in options:
            relation_id = self._optional_id(
                "employment_relations", "name", option.employment_relation_name
            )
            workload_id = self._optional_id("workloads", "name", option.workload_name)
            self.connection.execute(
                """
                INSERT INTO job_posting_employment_options (
                    job_posting_id, employment_relation_id, workload_id,
                    hours_min, hours_max, hours_period
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    posting_id,
                    relation_id,
                    workload_id,
                    option.hours_min,
                    option.hours_max,
                    option.hours_period,
                ),
            )

    def _insert_skill_requirements(
        self,
        posting_id: int,
        requirements: Iterable[SkillRequirement],
    ) -> None:
        for requirement in requirements:
            skill_id = self._optional_id("skills", "name", requirement.name)
            if skill_id is None:
                continue
            proficiency_id = self._optional_id(
                "proficiency_levels", "name", requirement.proficiency_level_name
            )
            requirement_type_id = self._optional_id(
                "requirement_types", "name", requirement.requirement_type_name
            )
            self.connection.execute(
                """
                INSERT INTO job_skill_requirements (
                    job_posting_id, skill_id, proficiency_level_id,
                    requirement_type_id, priority
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (job_posting_id, skill_id) DO UPDATE SET
                    proficiency_level_id = EXCLUDED.proficiency_level_id,
                    requirement_type_id = EXCLUDED.requirement_type_id,
                    priority = EXCLUDED.priority
                """,
                (
                    posting_id,
                    skill_id,
                    proficiency_id,
                    requirement_type_id,
                    requirement.priority,
                ),
            )

    def _insert_compensations(
        self,
        posting_id: int,
        compensations: Iterable[CompensationOption],
    ) -> None:
        for compensation in compensations:
            if compensation.salary_min is None and compensation.salary_max is None:
                continue
            self.connection.execute(
                """
                INSERT INTO job_posting_compensations (
                    job_posting_id, salary_min, salary_max,
                    salary_currency, salary_period
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    posting_id,
                    compensation.salary_min,
                    compensation.salary_max,
                    compensation.salary_currency,
                    compensation.salary_period,
                ),
            )

    def _required_id(self, table: str, column: str, value: str) -> int:
        identifier = self._optional_id(table, column, value)
        if identifier is None:
            raise ValueError(f"Reference value not found in {table}: {value}")
        return identifier

    def _optional_id(self, table: str, column: str, value: str | None) -> int | None:
        if value is None:
            return None
        statement = sql.SQL("SELECT id FROM {} WHERE {} = %s").format(
            sql.Identifier(table), sql.Identifier(column)
        )
        row = self.connection.execute(statement, (value,)).fetchone()
        return int(row[0]) if row else None


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(UTC)
