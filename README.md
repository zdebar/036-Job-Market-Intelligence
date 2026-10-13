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
