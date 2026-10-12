# 036 – Job Market Intelligence

Datová platforma pro sběr a analýzu pracovních nabídek.

## Technologie

- Python
- uv
- PostgreSQL
- Docker
- pytest
- Ruff

## Lokální vývoj

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Databáze

Vytvoř lokální konfiguraci z připravené šablony a spusť PostgreSQL:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
```

Migrace a seed spouštěj přes runner:

```powershell
uv run db-migrate
uv run db-seed
```

Runner eviduje aplikované SQL soubory v tabulce `database_changelog`, takže
opakované spuštění přeskočí již aplikované soubory. Již aplikovanou migraci
neupravuj; pro další změnu vytvoř nový soubor v `db/migrations/`.

Seed soubory jsou také evidované a musí mít číslovaný název, například
`002_more_reference_data.sql`.
