# SQL Analytics

## Goal

Validate that the normalized PostgreSQL schema supports useful job-market
analysis before introducing dbt or Power BI.

## Deliverables

- Read-only reports in `sql/reports/`.
- Data-quality checks in `sql/quality/`.
- Lightweight local runners for both.

Reports cover postings by company, source, role, department, skill, work mode,
location, and freshness, plus posting detail.

Quality checks cover ingestion counts, record errors, normalization coverage,
bridge integrity, posting completeness, canonical links, and posting ranking.

## Decisions

- Use explicit SQL and normalized tables as the primary source.
- Keep `raw_advertisement` for detail and debugging only.
- Do not change the operational schema for individual reports.
- Defer dbt models and the Power BI semantic model to phase 06.
- Canonical matching and ranking are operational processing concerns; SQL
  checks validate their persisted results.

## Done when

- Reports and checks run successfully against the local database.
- The SQL provides a sound input for phase 06 staging models.
