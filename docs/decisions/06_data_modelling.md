# Decision 06: Data Modelling with dbt

## Decision

Use dbt to build an analytical layer over the operational PostgreSQL schema.
The project follows the dbt staging/intermediate/marts structure. Staging and
intermediate models are views; marts are persisted tables in the `analytics`
schema for Power BI consumption.

dbt does not perform ingestion, extraction, normalization, or canonical-job
matching. Those steps are completed by the application before dbt runs.

## Models

- staging views: thin, source-conformed views over operational tables;
- intermediate views: reusable posting enrichment and canonical-job counts;
- dimensions: company, role, source, seniority, department, skill, location,
  work mode, proficiency, requirement type, employment relation, and workload;
- facts: complete posting and canonical-job facts plus active Power BI facts;
- bridges: active posting and canonical-job relationships for skills, locations,
  work modes, and departments;
- relationship facts: active skills with proficiency, requirement type, and
  priority, plus employment and workload options.

## Grain and canonical jobs

- `fct_job_postings` has one row per source posting;
- `fct_canonical_jobs` has one row per logical job opportunity;
- a canonical job uses the active posting with `selection_rank = 1` as its
  current representation;
- inactive postings remain linked to their canonical job but are not primary;
- many-to-many attributes are exposed through bridge and relationship fact
  tables, not JSON arrays;
- inactive postings remain available in complete facts but are excluded from
  the active reporting contract.

## Scope

Included:

- reusable dbt models and source declarations;
- model-level and relationship tests;
- PostgreSQL profile configuration for local development;
- departments added to the model from `job_posting_departments`;
- all operational reads routed through staging models;
- active Power BI facts separated from complete audit/history facts.

Deferred:

- snapshots and historical primary-posting changes;
- incremental materialization;
- slowly changing dimensions;
- dashboard-specific aggregate models;
- dbt v2 migration until a PostgreSQL adapter is available for this project.
