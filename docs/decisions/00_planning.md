# Planning

## Project objective

Build a data platform for collecting, structuring, and analyzing job postings.

The project is intended to serve as:

- a practical Data/AI Engineering project,
- a portfolio example,
- a tool for labor market analysis.

## Basic data flow

```text
sources
→ ingestion
→ raw storage
→ extraction and normalization
→ PostgreSQL
→ data quality and SQL analytics
→ dbt Gold
→ Power BI
→ Azure
```

## Main technologies

| Technology                | Role                                   |
| ------------------------- | -------------------------------------- |
| Git and GitHub            | Version control, collaboration, and CI/CD |
| Python and uv             | Application, parsing, and environment management |
| httpx                     | HTTP communication with sources        |
| Docker and Docker Compose | Local service runtime                 |
| PostgreSQL               | Operational and analytical database    |
| SQL migrations           | Database schema change management      |
| pytest and Ruff          | Testing, linting, and formatting       |
| dbt                      | Analytical transformation layer        |
| Power BI                 | Dashboards and analytics presentation  |
| Azure                    | Cloud storage, execution, and monitoring |
| LLM API                  | Later AI extraction                    |

## Main phases

| Phase | Status | Name                            | Outcome                                              |
| ----- | ------ | ------------------------------- | ---------------------------------------------------- |
| 0     | [x]    | Planning                        | Objectives, terminology, scope, and decisions        |
| 1     | [x]    | Project foundation              | Git, Python, uv, tests, linting, and basic structure |
| 2     | [x]    | Database foundation             | PostgreSQL, Docker, migrations, and seed data        |
| 3     | [ ]    | Basic ingestion                 | Data download and raw storage                        |
| 4     | [ ]    | Extraction and normalization    | Conversion of source data to a common format         |
| 5     | [ ]    | SQL analytics and data modeling | First useful queries and reports                     |
| 6     | [ ]    | Data modeling / dbt             | Staging, facts, dimensions, bridges, and Gold views  |
| 7     | [ ]    | Dashboard                       | Power BI dashboard on the analytical layer           |
| 8     | [ ]    | Cloud foundation                | Azure Storage, Azure PostgreSQL, and secrets         |
| 9     | [ ]    | Cloud orchestration             | Automated runs, retries, logging, and monitoring     |

## Optional phases

| Phase | Status | Name                  | Outcome                                      |
| ----- | ------ | --------------------- | -------------------------------------------- |
| 10    | [ ]    | AI extraction         | LLM extraction and validation of structured data |
| 11    | [ ]    | Optional technologies | Databricks, PySpark, embeddings, and semantic search |


## Principles

- Start locally and move functional parts to Azure later.
- Raw data is immutable and can be reprocessed.
- Each phase must first have a clear outcome and a test.
- Add new technologies only when they serve a clear purpose in the project.
- Use `035` only as a reference; adopt code incrementally as needed.
- AI, Databricks, and semantic search are extensions, not requirements for the basic platform.
