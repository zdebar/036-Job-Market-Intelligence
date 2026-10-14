# dbt Mart Schema Reference

This document describes the currently implemented dbt marts for the Job Market
Intelligence project. It is a schema and usage reference for analysts, Power BI
authors, and contributors changing the dbt project.

The reference is based on the SQL models under
`dbt/job_market_intelligence/models/marts/jobs/` and the model properties in
`models/marts/jobs/schema.yml`. Update this document when a mart's columns,
grain, filtering rules, or relationships change.

## 1. Physical configuration

| Property | Current value |
|---|---|
| dbt project | `dbt/job_market_intelligence/` |
| Target schema | `analytics` by default |
| Mart materialization | `table` |
| Mart domain | `jobs` |
| BI consumer | Power BI |
| Source layer | Operational PostgreSQL tables through staging models |
| Transformation layers | Staging -> intermediate -> marts |
| Compensation target | CZK per month |
| Compensation policy | `config/compensation.toml` |

The mart models are persisted tables. Staging and intermediate models are
views. The default project configuration is in
[`dbt_project.yml`](../dbt/job_market_intelligence/dbt_project.yml).

Run dbt commands from the repository root. The project-local `profiles.yml` in
the root directory is then selected before any user-level profile.

## 2. Design principles

The mart layer contains two related analytical hubs:

1. source postings, represented by `fct_job_postings` and
   `fct_active_job_postings`;
2. canonical logical opportunities, represented by `fct_canonical_jobs` and
   `fct_active_canonical_jobs`.

The `fct_active_*` models are the normal Power BI entry points. They exclude
rows whose `status` is not `active`. The non-active-filtered facts retain
inactive history for auditing and historical analysis.

Relationship models are separate so that a posting or canonical job can have
many locations, departments, work modes, or skills without multiplying rows in
the main fact. Skill and employment-option facts also expose relationship
attributes in a convenient tabular form.

## 3. High-level relationship map

```text
                                dim_company
                                     |
dim_source ---- fct_active_job_postings ---- dim_role
                    |       |      |
                    |       |      +-- bridge_job_posting_locations -- dim_location
                    |       |      +-- bridge_job_posting_departments -- dim_department
                    |       |      +-- bridge_job_posting_work_modes -- dim_work_mode
                    |       |      +-- bridge_job_posting_skills -- dim_skill
                    |       |      +-- fct_active_job_posting_skill_requirements
                    |       |      +-- fct_active_job_posting_employment_options
                    |       |
                    |       +-- dim_seniority
                    |
                    +-- fct_active_canonical_jobs
                              |       |
                              |       +-- bridge_canonical_job_locations -- dim_location
                              |       +-- bridge_canonical_job_departments -- dim_department
                              |       +-- bridge_canonical_job_work_modes -- dim_work_mode
                              |       +-- bridge_canonical_job_skills -- dim_skill
                              |       +-- fct_active_canonical_job_skill_requirements
                              |       +-- fct_active_canonical_job_employment_options
                              |
                              +-- dim_company, dim_role, dim_source,
                                  dim_seniority
```

The diagram shows the principal relationships, not every possible BI
relationship. `dim_skill`, `dim_location`, and the other dimensions can be
shared by both the posting and canonical-job parts of the model.

## 4. Model catalog

### Dimensions

| Model | Grain | Purpose |
|---|---|---|
| `dim_company` | One row per normalized company | Company labels and filtering |
| `dim_department` | One row per normalized department | Department labels and filtering |
| `dim_employment_relation` | One row per employment relation | Employment type labels |
| `dim_location` | One row per normalized work location | Location labels and filtering |
| `dim_proficiency_level` | One row per skill proficiency level | Skill-level labels and sort order |
| `dim_requirement_type` | One row per skill requirement type | Required/preferred classification |
| `dim_role` | One row per normalized job role | Role labels and filtering |
| `dim_seniority` | One row per seniority level | Seniority labels and sort order |
| `dim_skill` | One row per normalized skill | Skill labels and filtering |
| `dim_source` | One row per source board | Source identity and labels |
| `dim_work_mode` | One row per work mode | Remote/hybrid/on-site style labels |
| `dim_workload` | One row per workload | Full-time/part-time style labels |

### Facts

| Model | Grain | Population |
|---|---|---|
| `fct_job_postings` | One row per source job posting | Active and inactive history |
| `fct_active_job_postings` | One row per source job posting | Active only |
| `fct_canonical_jobs` | One row per logical job opportunity | Active and inactive history |
| `fct_active_canonical_jobs` | One row per logical job opportunity | Active only |
| `fct_active_job_posting_skill_requirements` | One row per active posting and skill | Active only |
| `fct_active_canonical_job_skill_requirements` | One row per active canonical job and skill | Primary active posting only |
| `fct_active_job_posting_employment_options` | One row per employment option belonging to an active posting | Active only |
| `fct_active_canonical_job_employment_options` | One row per employment option from a canonical job's primary active posting | Active only |

### Bridges

| Model | Grain |
|---|---|
| `bridge_job_posting_locations` | One row per active posting and location |
| `bridge_job_posting_departments` | One row per active posting and department |
| `bridge_job_posting_work_modes` | One row per active posting and work mode |
| `bridge_job_posting_skills` | One row per active posting and skill |
| `bridge_canonical_job_locations` | One row per canonical job and primary-posting location |
| `bridge_canonical_job_departments` | One row per canonical job and primary-posting department |
| `bridge_canonical_job_work_modes` | One row per canonical job and primary-posting work mode |
| `bridge_canonical_job_skills` | One row per canonical job and primary-posting skill |

## 5. Dimensions

All dimension keys are sourced from the normalized operational lookup tables.
The declared key in each dimension is not null and unique.

### `dim_company`

Grain: one row per normalized company.

| Column | Logical type | Description |
|---|---|---|
| `company_id` | `BIGINT` | Dimension key |
| `company_name` | `TEXT` | Normalized company name |

### `dim_department`

Grain: one row per normalized department.

| Column | Logical type | Description |
|---|---|---|
| `department_id` | `BIGINT` | Dimension key |
| `department_name` | `TEXT` | Normalized department name |

### `dim_employment_relation`

Grain: one row per employment relation.

| Column | Logical type | Description |
|---|---|---|
| `employment_relation_id` | `BIGINT` | Dimension key |
| `employment_relation_name` | `TEXT` | Employment relation label |

### `dim_location`

Grain: one row per normalized work location.

| Column | Logical type | Description |
|---|---|---|
| `location_id` | `BIGINT` | Dimension key |
| `location_name` | `TEXT` | Normalized location label |

### `dim_proficiency_level`

Grain: one row per skill proficiency level.

| Column | Logical type | Description |
|---|---|---|
| `proficiency_level_id` | `BIGINT` | Dimension key |
| `proficiency_level_name` | `TEXT` | Display label |
| `sort_order` | `SMALLINT` | Business ordering of levels |

### `dim_requirement_type`

Grain: one row per skill requirement type.

| Column | Logical type | Description |
|---|---|---|
| `requirement_type_id` | `BIGINT` | Dimension key |
| `requirement_type_name` | `TEXT` | Display label, for example required or preferred |
| `sort_order` | `SMALLINT` | Business ordering of requirement types |

### `dim_role`

Grain: one row per normalized job role.

| Column | Logical type | Description |
|---|---|---|
| `role_id` | `BIGINT` | Dimension key |
| `role_name` | `TEXT` | Normalized role label |

### `dim_seniority`

Grain: one row per seniority level.

| Column | Logical type | Description |
|---|---|---|
| `seniority_id` | `BIGINT` | Dimension key |
| `seniority_name` | `TEXT` | Display label |
| `sort_order` | `SMALLINT` | Business ordering of seniority levels |

### `dim_skill`

Grain: one row per normalized skill.

| Column | Logical type | Description |
|---|---|---|
| `skill_id` | `BIGINT` | Dimension key |
| `skill_name` | `TEXT` | Normalized skill label |

### `dim_source`

Grain: one row per source board.

| Column | Logical type | Description |
|---|---|---|
| `source_id` | `BIGINT` | Dimension key |
| `source_key` | `TEXT` | Stable source identifier |
| `source_name` | `TEXT` | Display name of the source |

### `dim_work_mode`

Grain: one row per work mode.

| Column | Logical type | Description |
|---|---|---|
| `work_mode_id` | `BIGINT` | Dimension key |
| `work_mode_name` | `TEXT` | Display label |

### `dim_workload`

Grain: one row per workload.

| Column | Logical type | Description |
|---|---|---|
| `workload_id` | `BIGINT` | Dimension key |
| `workload_name` | `TEXT` | Display label |

## 6. Posting facts

### `fct_job_postings`

Grain: one row per source job posting, including inactive history. The model
inherits the source-posting columns from `int_job_postings_enriched`.

| Column | Logical type | Description |
|---|---|---|
| `job_posting_id` | `BIGINT` | Source-posting fact key; not null and unique |
| `source_id` | `BIGINT` | Source board key |
| `source_job_id` | `TEXT` | Provider's job identifier |
| `company_id` | `BIGINT` | Company dimension key; may be null |
| `role_id` | `BIGINT` | Role dimension key; may be null |
| `seniority_id` | `BIGINT` | Seniority dimension key; may be null |
| `raw_advertisement_json` | `TEXT` | Original advertisement JSON cast to text |
| `source_url` | `TEXT` | Original job URL |
| `source_published_at` | `TIMESTAMPTZ` | Publication time reported by the source |
| `source_updated_at` | `TIMESTAMPTZ` | Source-reported update time |
| `retrieved_at` | `TIMESTAMPTZ` | Time the source record was retrieved |
| `last_seen_at` | `TIMESTAMPTZ` | Most recent observation of the posting |
| `status` | `TEXT` | `active`, `inactive`, or `unknown` |
| `normalization_version` | `TEXT` | Version of processing/normalization rules |
| `content_fingerprint` | `TEXT` | Content hash when available |
| `created_at` | `TIMESTAMPTZ` | Operational record creation time |
| `updated_at` | `TIMESTAMPTZ` | Operational record update time |
| `canonical_job_id` | `BIGINT` | Logical-job key when matched |
| `match_method` | `TEXT` | Method used to associate the canonical job |
| `matched_at` | `TIMESTAMPTZ` | Time of canonical matching |
| `selection_rank` | `INTEGER` | Rank used when selecting a primary posting |
| `salary_min` | `NUMERIC(12,2)` | Lower salary bound |
| `salary_max` | `NUMERIC(12,2)` | Upper salary bound |
| `salary_currency` | `TEXT` | Three-letter currency code when available |
| `salary_period` | `TEXT` | Salary period such as month or year |
| `salary_min_czk_month` | `NUMERIC(12,2)` | Lower bound converted to CZK per month |
| `salary_max_czk_month` | `NUMERIC(12,2)` | Upper bound converted to CZK per month |

### `fct_active_job_postings`

Grain: one row per active source job posting. It has the same columns as
`fct_job_postings` and applies `status = 'active'`.

Use this as the main Power BI fact when the analysis is about individual source
postings. It preserves provider-level detail and includes the canonical-job
association when one exists.

## 7. Canonical-job facts

### `fct_canonical_jobs`

Grain: one row per logical job opportunity, including inactive history.

| Column | Logical type | Description |
|---|---|---|
| `canonical_job_id` | `BIGINT` | Logical-job key; not null and unique |
| `primary_job_posting_id` | `BIGINT` | Selected representative posting; may be null for incomplete historical rows |
| `status` | `TEXT` | Active when at least one active posting exists |
| `posting_count` | `BIGINT` | Total source postings associated with the logical job |
| `active_posting_count` | `BIGINT` | Active source postings associated with the logical job |
| `source_count` | `BIGINT` | Number of distinct source boards represented |
| `first_seen_at` | `TIMESTAMPTZ` | Earliest observed posting timestamp |
| `last_seen_at` | `TIMESTAMPTZ` | Latest observed posting timestamp |
| `company_id` | `BIGINT` | Company from the primary posting |
| `role_id` | `BIGINT` | Role from the primary posting |
| `source_id` | `BIGINT` | Source of the primary posting |
| `seniority_id` | `BIGINT` | Seniority from the primary posting |
| `source_published_at` | `TIMESTAMPTZ` | Publication time of the primary posting |
| `source_url` | `TEXT` | URL of the primary posting |
| `salary_min` | `NUMERIC(12,2)` | Salary lower bound from the primary posting |
| `salary_max` | `NUMERIC(12,2)` | Salary upper bound from the primary posting |
| `salary_currency` | `TEXT` | Currency from the primary posting |
| `salary_period` | `TEXT` | Salary period from the primary posting |
| `salary_min_czk_month` | `NUMERIC(12,2)` | Lower bound converted to CZK per month |
| `salary_max_czk_month` | `NUMERIC(12,2)` | Upper bound converted to CZK per month |

The canonical fact intentionally represents a logical opportunity rather than
every source advertisement. Counts and descriptive attributes are derived from
all associated postings, while the selected primary posting supplies the
representative descriptive and salary fields.

### Compensation policy

The source salary fields are intentionally preserved because they are needed
for traceability. The normalized fields are calculated during processing and
are available in the posting and canonical facts for Power BI measures. If a
rate or period is unavailable, the normalized fields remain null instead of
being presented as a comparable zero.

The configured rate date and all conversion factors are maintained in
[`config/compensation.toml`](../config/compensation.toml). Updating that file
affects newly processed or explicitly reprocessed records. Existing derived
values are kept stable until a deliberate historical backfill is run.

### `fct_active_canonical_jobs`

Grain: one row per active logical job opportunity. It has the same columns as
`fct_canonical_jobs` and applies `status = 'active'`.

Use this as the main Power BI fact when cross-source duplicates should count as
one logical opportunity. Its `primary_job_posting_id` drives the canonical-job
bridge models and the canonical skill/employment-option facts.

## 8. Skill requirement facts

### `fct_active_job_posting_skill_requirements`

Grain: one row per active source posting and skill. The grain is tested by the
`job_posting_id + skill_id` combination.

| Column | Logical type | Description |
|---|---|---|
| `job_posting_id` | `BIGINT` | Active posting key |
| `canonical_job_id` | `BIGINT` | Associated logical-job key; may be null |
| `skill_id` | `BIGINT` | Skill dimension key |
| `skill_name` | `TEXT` | Skill label denormalized for convenience |
| `proficiency_level_id` | `BIGINT` | Proficiency dimension key; may be null |
| `proficiency_level_name` | `TEXT` | Proficiency label |
| `requirement_type_id` | `BIGINT` | Requirement-type dimension key; may be null |
| `requirement_type_name` | `TEXT` | Requirement-type label |
| `priority` | `SMALLINT` | Source priority when supplied |

This is the preferred detailed table for a Power BI visual that needs one row
per posting-skill pair and the skill parameters in the same row.

### `fct_active_canonical_job_skill_requirements`

Grain: one row per active canonical job and skill from the primary active
posting. The grain is tested by the `canonical_job_id + skill_id` combination.

| Column | Logical type | Description |
|---|---|---|
| `canonical_job_id` | `BIGINT` | Active logical-job key |
| `job_posting_id` | `BIGINT` | Primary active source-posting key |
| `skill_id` | `BIGINT` | Skill dimension key |
| `skill_name` | `TEXT` | Skill label denormalized for convenience |
| `proficiency_level_id` | `BIGINT` | Proficiency dimension key; may be null |
| `proficiency_level_name` | `TEXT` | Proficiency label |
| `requirement_type_id` | `BIGINT` | Requirement-type dimension key; may be null |
| `requirement_type_name` | `TEXT` | Requirement-type label |
| `priority` | `SMALLINT` | Source priority when supplied |

This model avoids counting the same logical job once for every source posting.
It describes the skill requirements of the selected primary posting.

## 9. Employment-option facts

### `fct_active_job_posting_employment_options`

Grain: one row per employment option belonging to an active source posting.

| Column | Logical type | Description |
|---|---|---|
| `job_posting_id` | `BIGINT` | Active posting key |
| `canonical_job_id` | `BIGINT` | Associated logical-job key; may be null |
| `employment_option_id` | `BIGINT` | Employment-option key; not null and unique |
| `employment_relation_id` | `BIGINT` | Employment-relation dimension key |
| `employment_relation_name` | `TEXT` | Employment-relation label |
| `workload_id` | `BIGINT` | Workload dimension key |
| `workload_name` | `TEXT` | Workload label |
| `hours_min` | `NUMERIC(7,2)` | Lower hours bound |
| `hours_max` | `NUMERIC(7,2)` | Upper hours bound |
| `hours_period` | `TEXT` | Period for the hours values |

### `fct_active_canonical_job_employment_options`

Grain: one row per employment option from the primary active posting of an
active canonical job.

| Column | Logical type | Description |
|---|---|---|
| `canonical_job_id` | `BIGINT` | Active logical-job key |
| `job_posting_id` | `BIGINT` | Primary active source-posting key |
| `employment_option_id` | `BIGINT` | Employment-option key; not null and unique |
| `employment_relation_id` | `BIGINT` | Employment-relation dimension key |
| `employment_relation_name` | `TEXT` | Employment-relation label |
| `workload_id` | `BIGINT` | Workload dimension key |
| `workload_name` | `TEXT` | Workload label |
| `hours_min` | `NUMERIC(7,2)` | Lower hours bound |
| `hours_max` | `NUMERIC(7,2)` | Upper hours bound |
| `hours_period` | `TEXT` | Period for the hours values |

## 10. Posting bridges

Posting bridges contain only active postings. Dimension labels are included in
the bridge SQL for convenient inspection and simple exports.

### `bridge_job_posting_locations`

Grain: one row per active posting and location.

| Column | Logical type | Description |
|---|---|---|
| `job_posting_id` | `BIGINT` | Active posting key |
| `location_id` | `BIGINT` | Location dimension key |
| `location_name` | `TEXT` | Location label |

### `bridge_job_posting_departments`

Grain: one row per active posting and department.

| Column | Logical type | Description |
|---|---|---|
| `job_posting_id` | `BIGINT` | Active posting key |
| `department_id` | `BIGINT` | Department dimension key |
| `department_name` | `TEXT` | Department label |

### `bridge_job_posting_work_modes`

Grain: one row per active posting and work mode.

| Column | Logical type | Description |
|---|---|---|
| `job_posting_id` | `BIGINT` | Active posting key |
| `work_mode_id` | `BIGINT` | Work-mode dimension key |
| `work_mode_name` | `TEXT` | Work-mode label |

### `bridge_job_posting_skills`

Grain: one row per active posting and skill. This model currently exposes the
same columns as `fct_active_job_posting_skill_requirements`:

```text
job_posting_id
canonical_job_id
skill_id
skill_name
proficiency_level_id
proficiency_level_name
requirement_type_id
requirement_type_name
priority
```

It is currently implemented as a direct projection of the skill-requirement
fact so the relationship-oriented name is available to BI consumers.

## 11. Canonical-job bridges

Canonical-job bridges use the primary active posting selected for each active
canonical job.

### `bridge_canonical_job_locations`

Grain: one row per canonical job and primary-posting location.

| Column | Logical type | Description |
|---|---|---|
| `canonical_job_id` | `BIGINT` | Active logical-job key |
| `location_id` | `BIGINT` | Location dimension key |
| `location_name` | `TEXT` | Location label |

### `bridge_canonical_job_departments`

Grain: one row per canonical job and primary-posting department.

| Column | Logical type | Description |
|---|---|---|
| `canonical_job_id` | `BIGINT` | Active logical-job key |
| `department_id` | `BIGINT` | Department dimension key |
| `department_name` | `TEXT` | Department label |

### `bridge_canonical_job_work_modes`

Grain: one row per canonical job and primary-posting work mode.

| Column | Logical type | Description |
|---|---|---|
| `canonical_job_id` | `BIGINT` | Active logical-job key |
| `work_mode_id` | `BIGINT` | Work-mode dimension key |
| `work_mode_name` | `TEXT` | Work-mode label |

### `bridge_canonical_job_skills`

Grain: one row per canonical job and primary-posting skill. This model currently
exposes the same columns as `fct_active_canonical_job_skill_requirements`:

```text
canonical_job_id
job_posting_id
skill_id
skill_name
proficiency_level_id
proficiency_level_name
requirement_type_id
requirement_type_name
priority
```

## 12. Recommended Power BI usage

### Choose one primary fact

Use one of these as the central fact for a report:

| Question | Central model |
|---|---|
| How many source advertisements are active? | `fct_active_job_postings` |
| How many logical opportunities are active? | `fct_active_canonical_jobs` |
| How did the source inventory change over time? | `fct_job_postings` |
| Which skills are attached to each source posting? | `fct_active_job_posting_skill_requirements` |
| Which skills describe each logical opportunity? | `fct_active_canonical_job_skill_requirements` |

Do not combine `fct_active_job_postings` and `fct_active_canonical_jobs` as two
unrelated facts in the same report and then count both without a deliberate
metric definition. One logical job can have several source postings.

### Use dimensions for labels and slicing

Use `dim_company`, `dim_role`, `dim_source`, `dim_seniority`, and the other
dimensions as reusable lookup/filter tables. Use bridge models when the
relationship is multi-valued. Do not join locations, skills, departments, and
work modes directly into one wide job table; that creates a Cartesian-like
product of combinations for jobs with multiple values in several categories.

### Use detailed relationship facts when parameters matter

The skill-requirement facts are intentionally denormalized with skill,
proficiency, and requirement labels. They are suitable for a detailed table
visual or a skill-focused report. The bridge models provide a relationship
surface for model navigation and filtering.

Power BI relationship directions and many-to-many behavior must be configured
deliberately. Avoid enabling bidirectional filtering everywhere; it can create
ambiguous paths and unexpected counts. If a report needs a job-grain table
filtered by a skill, use an explicit measure or a dedicated job-grain aggregate
when the relationship design would otherwise be ambiguous.

## 13. Data-quality contract

The current dbt properties and tests enforce or check the following:

- dimension keys are not null and unique;
- `fct_job_postings.job_posting_id` is not null and unique;
- `fct_active_job_postings.job_posting_id` is not null and unique;
- `fct_canonical_jobs.canonical_job_id` is not null and unique;
- `fct_active_canonical_jobs.canonical_job_id` is not null and unique;
- skill IDs relate to `dim_skill` in both skill-requirement facts;
- posting bridge keys relate to `fct_active_job_postings`;
- canonical bridge keys relate to `fct_active_canonical_jobs`;
- custom tests protect the posting-skill and canonical-job-skill composite grains;
- employment-option IDs are not null and unique in both employment-option facts.

Run the complete mart build and tests with:

```powershell
uv run dbt build --project-dir dbt/job_market_intelligence
```

## 14. Change checklist

When changing a mart, update all of the following where applicable:

1. the model SQL;
2. the model description and column tests in `models/marts/jobs/schema.yml`;
3. this schema reference;
4. custom grain tests under `dbt/job_market_intelligence/tests/`;
5. the Power BI relationship or semantic model documentation;
6. downstream reports affected by column, filter, or grain changes.

Before merging, verify the model grain, row counts, uniqueness, relationship
paths, active/inactive behavior, and the effect on measures.

## 15. Related documentation

- [General dbt overview](dbt_guide.md)
- [General data modelling overview](data_modelling_guide.md)
- [dbt project README](../dbt/job_market_intelligence/README.md)
- [Mart model properties](../dbt/job_market_intelligence/models/marts/jobs/schema.yml)
- [dbt project configuration](../dbt/job_market_intelligence/dbt_project.yml)
