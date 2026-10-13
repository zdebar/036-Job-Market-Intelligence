# Database Foundation

## Objective

Set up a reproducible local PostgreSQL database with versioned schema changes
and seed data.

## Decisions

- PostgreSQL 16 runs locally through Docker Compose.
- Host port `15433` is used to avoid the PostgreSQL port collision.
- Database connection settings are read from the local `.env` file through
  `DATABASE_URL`; `.env.example` documents the required variables.
- The initial schema is stored in `db/migrations/001_initial.sql`. It is a
  squashed version of the required migrations from project 035.
- Seed data is stored separately in `db/seeds/001_job_offers.sql`.
- Migration and seed files are applied by the Python runner:

  ```text
  uv run db-migrate
  uv run db-seed
  ```

- The runner creates `database_changelog` in PostgreSQL. It records applied
  files and checksums; it is bookkeeping, not the source of the schema.
- Applied SQL files are immutable. A schema change requires a new migration
  file instead of editing an already applied file.
- Each SQL file is executed in its own transaction. A PostgreSQL advisory lock
  prevents concurrent migration or seed runs.
- `psycopg` is used for the database connection and SQL execution.
- The same migration files will be used later when the database is moved to
  Azure PostgreSQL.

## Result

The project has a reproducible local PostgreSQL database, controlled schema
initialization, repeatable seed execution, and a migration history stored in
the database.
