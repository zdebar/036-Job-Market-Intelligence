import os
import uuid
from collections.abc import Generator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv

from job_market_intelligence.processing.database import ProcessingRepository
from job_market_intelligence.processing.fingerprint import content_fingerprint
from job_market_intelligence.processing.models import (
    CompensationOption,
    ParsedJobPosting,
)

PROJECT_ROOT = Path(__file__).parents[1]


def _connection() -> psycopg.Connection:
    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not configured")
    try:
        return psycopg.connect(database_url)
    except psycopg.OperationalError as error:
        pytest.skip(f"Local PostgreSQL is not available: {error}")


@pytest.fixture
def repository() -> Generator[ProcessingRepository, None, None]:
    connection = _connection()
    try:
        yield ProcessingRepository(connection)
    finally:
        connection.rollback()
        connection.close()


def _posting(
    source_job_id: str,
    updated_at: datetime,
    description: str = "Build data pipelines with Python and SQL.",
) -> ParsedJobPosting:
    return ParsedJobPosting(
        source_job_id=source_job_id,
        company_name="Ataccama",
        role_name="Data Engineer",
        seniority_level_name=None,
        source_url=f"https://jobs.example/{source_job_id}",
        source_published_at=updated_at,
        source_updated_at=updated_at,
        raw_advertisement={"description": description},
        content_fingerprint=content_fingerprint(description),
        locations=("Prague, Czechia",),
    )


def test_persists_czk_month_compensation(repository: ProcessingRepository) -> None:
    retrieved_at = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid.uuid4().hex
    record = replace(
        _posting(f"test-compensation-{suffix}", retrieved_at),
        compensation_options=(
            CompensationOption(
                salary_min=Decimal(1200),
                salary_max=Decimal(1800),
                salary_currency="EUR",
                salary_period="year",
            ),
        ),
    )

    posting_id = repository.upsert_job_posting(
        source_key="lever_ataccama",
        record=record,
        retrieved_at=retrieved_at,
    )
    row = repository.connection.execute(
        """
        SELECT salary_min_czk_month, salary_max_czk_month
        FROM job_posting_compensations
        WHERE job_posting_id = %s
        """,
        (posting_id,),
    ).fetchone()

    assert row == (Decimal("2437.50"), Decimal("3656.25"))


def test_cross_source_postings_share_canonical_and_rank(
    repository: ProcessingRepository,
) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    older = now - timedelta(days=1)
    suffix = uuid.uuid4().hex
    first_id = f"test-lever-{suffix}"
    second_id = f"test-greenhouse-{suffix}"

    first_posting_id = repository.upsert_job_posting(
        source_key="lever_ataccama",
        record=_posting(first_id, older),
        retrieved_at=older,
    )
    second_posting_id = repository.upsert_job_posting(
        source_key="greenhouse_mews",
        record=_posting(second_id, now),
        retrieved_at=now,
    )

    rows = repository.connection.execute(
        """
        SELECT canonical_job_id, job_posting_id, selection_rank
        FROM job_posting_sources
        WHERE job_posting_id IN (%s, %s)
        ORDER BY selection_rank
        """,
        (first_posting_id, second_posting_id),
    ).fetchall()

    assert len(rows) == 2
    assert rows[0][0] == rows[1][0]
    assert rows[0][1] == second_posting_id
    assert rows[0][2] == 1
    assert rows[1][1] == first_posting_id
    assert rows[1][2] == 2

    repository.mark_missing_postings_inactive(
        source_key="lever_ataccama",
        retrieved_at=now,
    )
    inactive_rank = repository.connection.execute(
        "SELECT selection_rank FROM job_posting_sources WHERE job_posting_id = %s",
        (first_posting_id,),
    ).fetchone()
    active_rank = repository.connection.execute(
        "SELECT selection_rank FROM job_posting_sources WHERE job_posting_id = %s",
        (second_posting_id,),
    ).fetchone()

    assert inactive_rank == (None,)
    assert active_rank == (1,)


def test_existing_canonical_link_is_preserved_when_posting_changes(
    repository: ProcessingRepository,
) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid.uuid4().hex
    source_job_id = f"test-existing-{suffix}"

    posting_id = repository.upsert_job_posting(
        source_key="lever_ataccama",
        record=_posting(source_job_id, now),
        retrieved_at=now,
    )
    original_link = repository.connection.execute(
        """
        SELECT canonical_job_id
        FROM job_posting_sources
        WHERE job_posting_id = %s
        """,
        (posting_id,),
    ).fetchone()

    later = now + timedelta(days=1)
    repository.upsert_job_posting(
        source_key="lever_ataccama",
        record=_posting(
            source_job_id,
            later,
            description="A completely changed advertisement.",
        ),
        retrieved_at=later,
    )
    current_link = repository.connection.execute(
        """
        SELECT canonical_job_id
        FROM job_posting_sources
        WHERE job_posting_id = %s
        """,
        (posting_id,),
    ).fetchone()

    assert original_link is not None
    assert current_link == original_link
