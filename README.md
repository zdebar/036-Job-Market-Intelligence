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

Seed files are tracked as well and must use a numbered filename, for example:

`002_more_reference_data.sql`.

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
