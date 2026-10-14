# dbt analytical models

This project builds the analytical layer for 036 from the operational
PostgreSQL schema. The project follows a staging, intermediate, and marts
layout:

- `staging/operational/`: source-conformed views with one source concept per
  model;
- `intermediate/jobs/`: reusable joins and canonical-job preparation views;
- `marts/jobs/`: Power BI-facing dimensions, facts, and relationship bridges.

Staging and intermediate models are views. Marts are persisted tables in the
`analytics` schema. The reporting-facing `fct_active_*` models exclude
inactive postings; the complete facts retain status and inactive history for
auditing and future analysis.

## Local setup

Install the dbt v1 PostgreSQL adapter and synchronize the environment:

```powershell
uv add --dev dbt-postgres
uv sync
```

The repository root contains the project-local `profiles.yml`. Run dbt from
the repository root so dbt finds this file before the user-level
`%USERPROFILE%\.dbt\profiles.yml`. The profile uses the local Docker defaults
from `.env.example`. If the values in `.env` differ, expose the corresponding
variables before running dbt.

Do not copy this profile to `%USERPROFILE%\.dbt\profiles.yml`. The user-level
profile may belong to another dbt project and must not control this project.

The repository also includes `.vscode/settings.json` with the dbt extension's
v1 compatibility mode enabled. This reduces diagnostic noise for this dbt v1
project, but it does not make the extension's language server run dbt v1.
Current versions of the dbt VS Code extension require a dbt v2 binary for the
language server, so do not point the machine-level `dbt.dbtPath` setting at
this project's `.venv\Scripts\dbt.exe`.

Run this PostgreSQL project through the locked v1 environment instead:

```powershell
uv run dbt debug --project-dir dbt/job_market_intelligence
uv run dbt build --project-dir dbt/job_market_intelligence
```

If the extension reports that PostgreSQL is unsupported, disable the dbt
extension for this workspace. This does not affect the project CLI or its
dbt builds.

## Commands

Run from the repository root:

```powershell
uv run dbt debug --project-dir dbt/job_market_intelligence
uv run dbt build --project-dir dbt/job_market_intelligence
```

`dbt build` creates or replaces the analytical tables and runs the declared
model and relationship tests.

## Power BI contract

The complete mart schema, grain, column, relationship, and Power BI reference
is documented in [`docs/dbt_mart_schema.md`](../../docs/dbt_mart_schema.md).

Use these marts as the normal Power BI entry points:

- `fct_active_job_postings`: one row per active source posting;
- `fct_active_canonical_jobs`: one row per active logical job opportunity;
- `dim_*`: reusable filter and label tables;
- `bridge_*`: one row per many-to-many relationship;
- `fct_active_*_skill_requirements`: skills with proficiency, requirement type,
  and priority already attached;
- `fct_active_*_employment_options`: employment and workload options already
  attached to the posting or canonical job.

Compensation marts preserve `salary_min`, `salary_max`,
`salary_currency`, and `salary_period`, and also expose
`salary_min_czk_month` and `salary_max_czk_month` for comparable reporting.
The conversion policy and rate snapshot are maintained in
`config/compensation.toml`; the operational derived columns are populated by
the processing layer before dbt reads them.

Power BI should use model relationships and dimensions for filtering. It
should not build a single wide table by joining skills, locations, work modes,
and departments together, because that multiplies rows. Relationship facts
are intentionally precomputed in dbt so the same business definitions are
reused across reports.
