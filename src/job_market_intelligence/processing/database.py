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
        canonical_job_id = self._ensure_canonical_job(posting_id)
        self._refresh_canonical_job_ranking(canonical_job_id)
        return posting_id

    def mark_missing_postings_inactive(
        self,
        *,
        source_key: str,
        retrieved_at: datetime,
    ) -> int:
        result = self.connection.execute(
            """
            UPDATE job_postings
            SET status = 'inactive', updated_at = now()
            WHERE source_id = (SELECT id FROM sources WHERE source_key = %s)
              AND status = 'active'
              AND last_seen_at < %s
            RETURNING id
            """,
            (source_key, retrieved_at),
        )
        posting_ids = [int(row[0]) for row in result.fetchall()]
        canonical_ids: set[int] = set()
        for posting_id in posting_ids:
            row = self.connection.execute(
                """
                SELECT canonical_job_id
                FROM job_posting_sources
                WHERE job_posting_id = %s
                """,
                (posting_id,),
            ).fetchone()
            if row is not None:
                canonical_ids.add(int(row[0]))

        for canonical_id in canonical_ids:
            self._refresh_canonical_job_ranking(canonical_id)
        return len(posting_ids)

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

    def _ensure_canonical_job(self, posting_id: int) -> int:
        existing = self.connection.execute(
            """
            SELECT canonical_job_id
            FROM job_posting_sources
            WHERE job_posting_id = %s
            """,
            (posting_id,),
        ).fetchone()
        if existing is not None:
            return int(existing[0])

        canonical_id = self._find_canonical_match(posting_id)
        match_method = (
            "algorithmic_match" if canonical_id is not None else "new_canonical_job"
        )
        if canonical_id is None:
            row = self.connection.execute(
                "INSERT INTO canonical_jobs DEFAULT VALUES RETURNING id"
            ).fetchone()
            if row is None:
                raise RuntimeError(f"Could not create canonical job for {posting_id}")
            canonical_id = int(row[0])

        self.connection.execute(
            """
            INSERT INTO job_posting_sources (
                canonical_job_id, job_posting_id, match_method, matched_at
            )
            VALUES (%s, %s, %s, now())
            """,
            (canonical_id, posting_id, match_method),
        )
        return canonical_id

    def _find_canonical_match(self, posting_id: int) -> int | None:
        current = self.connection.execute(
            """
            SELECT company_id, role_id, seniority_level_id, content_fingerprint
            FROM job_postings
            WHERE id = %s
            """,
            (posting_id,),
        ).fetchone()
        if current is None:
            raise RuntimeError(f"Posting does not exist: {posting_id}")

        company_id, role_id, seniority_id, fingerprint = current
        if fingerprint:
            exact_matches = self._fingerprint_candidates(
                posting_id, int(company_id), str(fingerprint)
            )
            if len(exact_matches) == 1:
                return exact_matches[0]
            if exact_matches:
                return None

        if role_id is None or not self._has_locations(posting_id):
            return None

        fallback_matches = self._fallback_candidates(
            posting_id,
            int(company_id),
            int(role_id),
            int(seniority_id) if seniority_id is not None else None,
        )
        return fallback_matches[0] if len(fallback_matches) == 1 else None

    def _fingerprint_candidates(
        self,
        posting_id: int,
        company_id: int,
        fingerprint: str,
    ) -> list[int]:
        rows = self.connection.execute(
            """
            SELECT DISTINCT links.canonical_job_id
            FROM job_postings AS postings
            JOIN job_posting_sources AS links ON links.job_posting_id = postings.id
            WHERE postings.id <> %s
              AND postings.company_id = %s
              AND postings.content_fingerprint = %s
            """,
            (posting_id, company_id, fingerprint),
        ).fetchall()
        return [int(row[0]) for row in rows]

    def _fallback_candidates(
        self,
        posting_id: int,
        company_id: int,
        role_id: int,
        seniority_id: int | None,
    ) -> list[int]:
        rows = self.connection.execute(
            """
            SELECT DISTINCT links.canonical_job_id
            FROM job_postings AS postings
            JOIN job_posting_sources AS links ON links.job_posting_id = postings.id
            WHERE postings.id <> %s
              AND postings.company_id = %s
              AND postings.role_id = %s
              AND (
                  postings.seniority_level_id IS NULL
                  OR CAST(%s AS BIGINT) IS NULL
                  OR postings.seniority_level_id = CAST(%s AS BIGINT)
              )
              AND ARRAY(
                  SELECT location_id
                  FROM job_posting_locations
                  WHERE job_posting_id = postings.id
                  ORDER BY location_id
              ) = ARRAY(
                  SELECT location_id
                  FROM job_posting_locations
                  WHERE job_posting_id = %s
                  ORDER BY location_id
              )
            """,
            (
                posting_id,
                company_id,
                role_id,
                seniority_id,
                seniority_id,
                posting_id,
            ),
        ).fetchall()
        return [int(row[0]) for row in rows]

    def _has_locations(self, posting_id: int) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM job_posting_locations
            WHERE job_posting_id = %s
            LIMIT 1
            """,
            (posting_id,),
        ).fetchone()
        return row is not None

    def _refresh_canonical_job_ranking(self, canonical_id: int) -> None:
        self.connection.execute(
            """
            UPDATE job_posting_sources
            SET selection_rank = NULL
            WHERE canonical_job_id = %s
            """,
            (canonical_id,),
        )
        self.connection.execute(
            """
            WITH ranked AS (
                SELECT
                    links.job_posting_id,
                    ROW_NUMBER() OVER (
                        ORDER BY
                            COALESCE(
                                postings.source_updated_at,
                                postings.retrieved_at
                            ) DESC NULLS LAST,
                            (
                                CASE WHEN postings.role_id IS NOT NULL THEN 1 ELSE 0 END
                                + CASE WHEN postings.seniority_level_id IS NOT NULL THEN 1 ELSE 0 END
                                + CASE WHEN postings.source_url IS NOT NULL THEN 1 ELSE 0 END
                                + CASE WHEN EXISTS (
                                    SELECT 1
                                    FROM job_posting_locations AS locations
                                    WHERE locations.job_posting_id = postings.id
                                ) THEN 1 ELSE 0 END
                                + CASE WHEN EXISTS (
                                    SELECT 1
                                    FROM job_posting_work_modes AS work_modes
                                    WHERE work_modes.job_posting_id = postings.id
                                ) THEN 1 ELSE 0 END
                                + CASE WHEN EXISTS (
                                    SELECT 1
                                    FROM job_skill_requirements AS skills
                                    WHERE skills.job_posting_id = postings.id
                                ) THEN 1 ELSE 0 END
                                + CASE WHEN EXISTS (
                                    SELECT 1
                                    FROM job_posting_compensations AS compensation
                                    WHERE compensation.job_posting_id = postings.id
                                ) THEN 1 ELSE 0 END
                                + CASE WHEN EXISTS (
                                    SELECT 1
                                    FROM job_posting_employment_options AS employment
                                    WHERE employment.job_posting_id = postings.id
                                ) THEN 1 ELSE 0 END
                            ) DESC,
                            postings.id ASC
                    )::INTEGER AS selection_rank
                FROM job_posting_sources AS links
                JOIN job_postings AS postings
                    ON postings.id = links.job_posting_id
                WHERE links.canonical_job_id = %s
                  AND postings.status = 'active'
            )
            UPDATE job_posting_sources AS links
            SET selection_rank = ranked.selection_rank
            FROM ranked
            WHERE links.job_posting_id = ranked.job_posting_id
            """,
            (canonical_id,),
        )
        self.connection.execute(
            """
            UPDATE canonical_jobs
            SET updated_at = now()
            WHERE id = %s
            """,
            (canonical_id,),
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
