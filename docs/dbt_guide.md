# dbt Overview

This is a general introduction to dbt for analytics engineering. It explains
what dbt does, how a dbt project is structured, how models form a dependency
graph, and how to build tested and documented datasets for BI tools.

dbt is most useful when a warehouse or database already contains raw or
operational data and the main problem is making that data trustworthy,
consistent, reusable, and understandable for analysis.

## 1. What dbt is

dbt is a transformation framework. You write SQL models and configuration;
dbt compiles the project, determines dependencies, executes transformations in
the correct order, runs tests, and generates documentation and lineage.

```text
raw or operational data
        |
        v
source declarations
        |
        v
staging models
        |
        v
intermediate models
        |
        v
analytical marts
        |
        v
BI, dashboards, exports, and metrics
```

dbt does not normally fetch data from an API, replace an application service,
or provide a general-purpose orchestration platform. It starts at the point
where data is available in the target database.

## 2. The dbt mental model

### 2.1 A model is a relation definition

A model is usually a SQL file. The query describes the rows and columns that
dbt should create as a view, table, incremental table, or another supported
relation.

```sql
-- models/staging/stg_orders.sql
select
    order_id,
    customer_id,
    cast(created_at as timestamp) as created_at,
    lower(status) as status
from {{ source('commerce', 'orders') }}
```

dbt replaces Jinja expressions such as `source()` and `ref()`, compiles the SQL,
and sends the resulting SQL to the database.

### 2.2 The project is a directed acyclic graph

`ref()` creates a dependency edge:

```sql
from {{ ref('stg_orders') }}
```

The result is a directed acyclic graph (DAG). dbt can then:

- build parents before children;
- select ancestors and descendants;
- show lineage;
- identify downstream impact of a change;
- run independent branches in parallel where supported.

Do not use hard-coded database and schema names when a `source()` or `ref()`
can express the dependency. Hard-coded names hide lineage and make environments
harder to change.

## 3. dbt versus other parts of a data platform

| Responsibility | Typical owner |
|---|---|
| Extract data from APIs or files | Ingestion tool or application |
| Store raw data | Database, object storage, or loading tool |
| Define operational tables | Application migrations |
| Transform data for analysis | dbt |
| Schedule and monitor workflows | Orchestrator |
| Visualize and explore data | Power BI or another BI tool |

The boundaries vary by organization. The important principle is to assign each
responsibility deliberately and avoid duplicating the same business rule in
multiple layers.

## 4. Project structure

A common dbt project looks like this:

```text
analytics_project/
  dbt_project.yml
  packages.yml
  models/
    staging/
      sources.yml
      stg_orders.sql
      schema.yml
    intermediate/
      int_customer_orders.sql
      schema.yml
    marts/
      core/
        dim_customers.sql
        fct_orders.sql
        schema.yml
  macros/
  tests/
  snapshots/
  seeds/
  analyses/
  README.md
```

The exact folders are a convention, not a requirement. A model should be
placed where its purpose is clear and where its dependencies match the layer.

## 5. Important configuration files

### `dbt_project.yml`

The project manifest. It defines the project name, model paths, clean targets,
default materializations, variables, and folder-level configuration.

### `profiles.yml`

Connection and target configuration. This project keeps a project-local
`profiles.yml` in the repository root. dbt finds it before the user-level
`%USERPROFILE%\\.dbt\\profiles.yml` when commands are run from the repository
root. Keep credentials out of Git and use environment variables or a secret
manager.

Do not copy this project's profile into the user-level dbt directory. That
directory is global and can contain configuration for unrelated projects.

### `packages.yml`

Optional dependencies on dbt packages. Review package compatibility, licenses,
and the generated lock file when using packages.

### YAML property files

Files such as `schema.yml` document models, columns, sources, tests, exposures,
and metrics. The filename is not important; its location and YAML structure
are.

### SQL model files

The transformation logic. Keep SQL readable and use `source()` and `ref()` to
make dependencies explicit.

## 6. Sources and staging

Declare raw or operational relations as sources:

```yaml
version: 2

sources:
  - name: commerce
    schema: raw
    tables:
      - name: orders
        description: Orders loaded from the commerce system.
        columns:
          - name: order_id
            data_tests:
              - not_null
              - unique
```

Use them in SQL with:

```sql
from {{ source('commerce', 'orders') }}
```

Staging models normally represent one source table or one source concept. They
should usually:

- rename columns to a consistent convention;
- cast data types;
- normalize simple values;
- remove clearly unusable technical records when that rule is stable;
- preserve source-level detail needed downstream;
- avoid complex business joins.

Staging is a boundary between source-specific structure and the project's
common vocabulary. It is not a place to build a final dashboard table.

## 7. Intermediate models

Intermediate models prepare reusable concepts that are too complex for staging
but are not yet final consumer-facing datasets.

Typical work includes:

- joining several staging models;
- deduplicating records;
- choosing a canonical record;
- preparing one row per entity;
- calculating reusable flags or classifications;
- aggregating a child table to a defined parent grain.

Intermediate models should have a clear purpose and grain. If a transformation
is used only once and is genuinely simple, a CTE may be enough. If it is reused
or needs its own tests and documentation, make it a model.

## 8. Marts

Marts are the stable datasets exposed to analysts, BI tools, and downstream
consumers. A mart should have:

- an explicit grain;
- names that reflect business meaning;
- stable keys;
- documented measures and dimensions;
- tests for important assumptions;
- only the columns needed by intended consumers, unless detail is deliberately
  part of the contract.

Common mart types are:

| Mart type | Meaning |
|---|---|
| Dimension | Descriptive entity such as customer, company, or skill |
| Fact | Event, transaction, snapshot, or measurable state |
| Bridge | Many-to-many relationship between entities |
| Aggregate | Precomputed summary at a stated grain |

Do not put every possible join into one giant mart. Prefer a small coherent
star schema or a small set of purpose-specific marts.

## 9. Grain in dbt models

The grain is what one row represents. Put it in the model description:

```text
One row per active job posting.
One row per job posting and required skill.
One row per company.
```

The grain controls joins, keys, tests, and measures. A model that starts with
one row per job and joins a many-to-many skill relation is no longer one row per
job unless the skill rows are aggregated or separated into a bridge.

Every model should answer:

1. What does one row represent?
2. Which columns identify that row?
3. Can the key be null or duplicated?
4. Which joins preserve the grain?
5. Which operations intentionally change the grain?

## 10. Materializations

Materialization controls how dbt creates a model in the database.

### View

A view stores the query definition. It is cheap to rebuild and usually reflects
current upstream data, but the query runs when consumers read it.

Use views for lightweight staging or intermediate logic.

### Table

A table stores the result physically. It is faster for repeated reads and can
shield consumers from expensive transformations, but it must be rebuilt to
refresh.

Use tables for important marts or expensive stable transformations.

### Incremental model

An incremental model processes only new or changed rows after an initial build.
It can reduce cost and runtime, but requires a reliable change strategy,
unique key, late-arriving-data policy, and backfill plan.

Do not choose incremental merely because a table is large. First define how
updates, deletes, corrections, and late events are handled.

### Ephemeral model

An ephemeral model is compiled into downstream SQL rather than created as a
database relation. It can be useful for small reusable expressions, but too many
ephemeral layers make compiled SQL difficult to inspect.

## 11. Tests and data quality

Tests express assumptions about data. Generic tests commonly include:

```yaml
columns:
  - name: order_id
    data_tests:
      - not_null
      - unique
  - name: customer_id
    data_tests:
      - relationships:
          to: ref('dim_customers')
          field: customer_id
```

Useful test categories:

- `not_null` for required keys and attributes;
- `unique` for a declared key;
- `relationships` for foreign-key-like integrity;
- `accepted_values` for controlled status values;
- singular SQL tests for business rules;
- source freshness for loading expectations.

A singular test should return violating rows. It passes when the result is
empty:

```sql
select
    customer_id,
    count(*) as row_count
from {{ ref('dim_customers') }}
group by customer_id
having count(*) > 1
```

Tests are guardrails, not decoration. A failed key or relationship test should
be investigated before the model is published.

## 12. Jinja and macros

Jinja generates SQL before execution. Keep Jinja simple and use it for
configuration, repetition, and adapter-aware behavior.

```sql
select
    order_id,
    {% if target.name == 'prod' %}
    created_at
    {% else %}
    cast(created_at as timestamp) as created_at
    {% endif %}
from {{ ref('stg_orders') }}
```

Macros are reusable Jinja functions:

```sql
{% macro safe_divide(numerator, denominator) %}
    {{ numerator }} / nullif({{ denominator }}, 0)
{% endmacro %}
```

Do not move all business logic into macros. A model should remain understandable
from its compiled SQL and its local context. Use macros when the same correct
pattern is repeated or when database adapter differences must be isolated.

## 13. Documentation and lineage

Document models and important columns with business meaning, not just their
SQL expression:

```yaml
models:
  - name: fct_orders
    description: "One row per order placed by a customer."
    columns:
      - name: order_id
        description: "Stable identifier of the order in the source system."
```

Generated documentation can show:

- source definitions;
- model descriptions;
- column descriptions;
- upstream and downstream lineage;
- test definitions and results;
- exposures such as dashboards.

Keep documentation close to the model so it changes with the transformation.

## 14. Seeds, snapshots, and exposures

### Seeds

Seeds are small, version-controlled CSV datasets such as mappings, codes, or
reference lists. They are not a replacement for loading large operational
tables.

### Snapshots

Snapshots preserve historical versions of mutable source rows. They are useful
when the source overwrites records but the business needs to know what changed
over time. Define the change key, timestamp strategy, and deletion behavior.

### Exposures

Exposures describe downstream consumers such as dashboards, notebooks, or
reports. They make impact analysis more complete than a model-only DAG.

## 15. Environments and reproducibility

Keep local, CI, staging, and production targets separate. A developer should
not accidentally write to a production schema.

Use a lock file for package dependencies, keep the dbt version and adapter
compatible, and make the target database explicit in commands and logs.

The reproducibility contract is:

```text
same code + same source state + same configuration
    -> same intended result
```

If a model uses the current time, random values, unstable ordering, or an
external API during compilation, document the effect and consider whether the
result remains reproducible.

## 16. Development workflow

A normal workflow is:

```powershell
dbt debug
dbt parse
dbt compile --select model_name
dbt build --select model_name+
dbt docs generate
```

What the commands do:

| Command | Purpose |
|---|---|
| `dbt debug` | Check profile, adapter, and connection |
| `dbt parse` | Validate project structure without building models |
| `dbt compile` | Render Jinja and show executable SQL |
| `dbt run` | Build selected models |
| `dbt test` | Run selected tests |
| `dbt build` | Run selected models, tests, and related resources in order |
| `dbt ls` | List resources and inspect selectors |
| `dbt docs generate` | Generate documentation and lineage artifacts |
| `dbt clean` | Remove configured local build artifacts |

Use selectors deliberately:

```text
model_name       the model
model_name+      the model and descendants
+model_name      the model and ancestors
+model_name+     ancestors, model, and descendants
path:models/...  resources under a path
tag:finance      resources with a tag
```

## 17. CI and deployment

A useful CI pipeline should:

1. install the locked dbt environment;
2. validate the profile and adapter;
3. parse the project;
4. build representative models against a disposable or controlled database;
5. run tests and fail on critical violations;
6. publish run artifacts and logs where appropriate.

Production scheduling usually looks like:

```text
load source data -> dbt build -> publish/refresh BI consumers
```

Record the code version, target environment, selector, start and end time,
model outcomes, test outcomes, and failures. Treat a successful SQL execution
with failed data tests as an unsuccessful data product run.

## 18. Safe model change process

Before changing a model:

1. read its description and tests;
2. state its current grain;
3. inspect upstream and downstream dependencies;
4. identify BI or report consumers;
5. classify the change as additive, corrective, or breaking.

After changing it:

1. run `dbt parse`;
2. inspect compiled SQL;
3. run a targeted `dbt build` with descendants;
4. compare row counts, key uniqueness, null rates, and important measures;
5. update documentation and tests;
6. communicate column or grain changes to consumers.

Never use `DISTINCT` merely to make a failing uniqueness test pass. Find the
join or grain error first.

## 19. dbt and the BI semantic layer

dbt prepares reliable relations; a BI tool often adds relationships, measures,
security, and presentation. Decide where each rule belongs:

| Rule | Prefer |
|---|---|
| Source cleanup and type casting | Staging dbt model |
| Reusable business classification | Intermediate or mart model |
| Stable row-level measure | Fact model |
| Many-to-many relation | Bridge model |
| User-selected slicing | BI relationships and filters |
| Presentation formatting | BI layer |

Do not physically join every dimension attribute into every fact row just so a
BI tool can filter it. Preserve star-schema relationships unless denormalizing
is a deliberate performance or usability decision.

## 20. Common mistakes

- reading raw sources directly from every mart;
- using hard-coded relation names instead of `source()` and `ref()`;
- failing to state model grain;
- joining a many-to-many table into a one-row-per-entity model;
- using `DISTINCT` to hide row multiplication;
- creating an incremental model without a backfill strategy;
- putting all logic into macros;
- documenting columns without documenting business meaning;
- testing only that a query runs, not that its result is correct;
- allowing local targets to point at production;
- building a wide table that duplicates dimensions unnecessarily.

## 21. Review checklist

- Is the model's grain stated in its description?
- Are dependencies expressed with `source()` and `ref()`?
- Is the model in the correct layer?
- Are key, null, relationship, and business-rule tests present?
- Is the materialization appropriate for freshness and cost?
- Are joins safe at the declared grain?
- Are filters applied intentionally?
- Is the model documented for its consumers?
- Can it be rebuilt deterministically?
- Will downstream reports continue to work after the change?

## 22. Further reading

- [dbt documentation](https://docs.getdbt.com/)
- [How dbt projects are structured](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview)
- [Sources](https://docs.getdbt.com/docs/build/sources)
- [Models](https://docs.getdbt.com/docs/build/sql-models)
- [Tests](https://docs.getdbt.com/docs/build/data-tests)
- [Materializations](https://docs.getdbt.com/best-practices/materializations/1-guide-overview)
- [dbt commands](https://docs.getdbt.com/reference/dbt-commands)
