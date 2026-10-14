# Project documentation

This directory contains general technology overviews, data modelling guidance,
and architectural decision records for the project.

## General guides

- [Python overview](python_guide.md) — language fundamentals, functions,
  modules, typing, errors, I/O, testing, packaging, and reliable application
  design.
- [SQL overview](sql_guide.md) — relational concepts, queries, NULLs, joins,
  aggregation, window functions, transactions, constraints, safety, and
  performance.
- [dbt overview](dbt_guide.md) — transformation workflows, sources, models,
  DAGs, staging/intermediate/marts, materializations, tests, documentation,
  and deployment.
- [dbt mart schema reference](dbt_mart_schema.md) — current mart models,
  grains, columns, relationships, tests, and Power BI usage.
- [Data modelling overview](data_modelling_guide.md) — entities, keys, grain,
  normalization, facts, dimensions, bridges, history, BI relationships, and
  modelling procedures.

## Architectural decisions

- [00: Planning](decisions/00_planning.md)
- [01: Project foundation](decisions/01_project_foundation.md)
- [02: Database foundation](decisions/02_database_foundation.md)
- [03: Basic ingestion](decisions/03_basic_ingestion.md)
- [04: Processing](decisions/04_processing.md)
- [05: SQL analytics](decisions/05_SQL_analytics.md)
- [06: dbt data modelling](decisions/06_data_modelling.md)
