# 036 – Job Market Intelligence

A data platform for collecting and analyzing job postings.

## Technology

- Python
- uv
- PostgreSQL
- Docker
- pytest
- Ruff

## Local development

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Database

Create the local configuration from the prepared template and start PostgreSQL:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
```

Run migrations and seed data through the runner:

```powershell
uv run db-migrate
uv run db-seed
```

The runner records applied SQL files in the `database_changelog` table, so
repeated runs skip files that have already been applied. Do not modify an
applied migration; create a new file in `db/migrations/` for each new change.

## Basic ingestion

The ingestion adapters download complete Greenhouse, Lever, and Ashby board
responses and save them as immutable raw files. Configure boards in the
corresponding files under `config/sources/`, then preview the requests without
network access:

```powershell
uv run job-market-ingest --dry-run
```

Run the configured downloads with:

```powershell
uv run job-market-ingest
```

Each run creates a new directory under
`data/01_bronze/<source_key>/<date>/<run_id>/` containing `response.json` and
`metadata.json`. Raw data is ignored by Git and is not overwritten by later
runs.

## Extraction and normalization

Process stored raw responses into PostgreSQL with:

```powershell
uv run job-market-parse
```

To backfill existing processed runs after a processing change, explicitly
request reprocessing:

```powershell
uv run job-market-parse --reprocess-processed
```

Preview discovered raw runs without a database connection:

```powershell
uv run job-market-parse --dry-run
```

The processing runner is idempotent: a raw run recorded as `processed` is
skipped on later executions. Record-level failures are stored in
`raw_ingestion_record_errors` and do not discard the original raw response.
During persistence, new postings are assigned to a canonical job when an
unambiguous cross-source match exists. Active canonical postings receive a
deterministic primary-posting rank; postings missing from a successful full
source run become inactive.

## SQL analytics

Phase 05 contains read-only reports in `sql/reports/` and data-quality checks
in `sql/quality/`. Run all reports or checks with:

```powershell
uv run job-market-report
uv run job-market-quality
```

Run one SQL file by repeating the `--file` option when needed:

```powershell
uv run job-market-report --file 001_active_jobs_by_company.sql
uv run job-market-quality --file 003_normalization_coverage.sql
```

Reports use the normalized tables and bridge tables as their primary source.
The `raw_advertisement` JSONB column is retained for detail and debugging;
canonical-job matching is completed during processing, and the dbt semantic
layer is built in Phase 06.

## dbt analytical models

Phase 06 builds reusable analytical marts in the `analytics` schema. Staging
and intermediate models remain views, while the marts used by Power BI are
persisted tables. The dbt project is in `dbt/job_market_intelligence/`; setup
and profile instructions are in its README.

Run dbt commands from the repository root. The project-local `profiles.yml` in
the root directory is used before any user-level dbt profile.

```powershell
uv run dbt debug --project-dir dbt/job_market_intelligence
uv run dbt build --project-dir dbt/job_market_intelligence
```

## Project documentation

The general technology and data modelling guides are collected in
[`docs/README.md`](docs/README.md):

- [Python overview](docs/python_guide.md)
- [SQL overview](docs/sql_guide.md)
- [dbt overview](docs/dbt_guide.md)
- [Data modelling overview](docs/data_modelling_guide.md)
