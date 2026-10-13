# Extraction and Normalization

## Objective

Convert immutable raw API responses into validated, normalized records for
PostgreSQL.

## Decisions

- Source-specific adapters parse Greenhouse, Lever, and Ashby payloads.
- Shared models and helpers produce one normalized `ParsedJobPosting` shape.
- The original provider record remains unchanged in `raw_advertisement`.
- Posting identity is `(source_id, source_job_id)`; repeated runs update the
  existing posting.
- Normalize common fields: company, role, seniority, department, locations,
  work modes, employment, compensation, and skills.
- Store aliases and normalization rules in `config/normalization/`.
- Unknown values remain `NULL` where allowed. Invalid records are reported and
  are not inserted.
- Calculate `content_fingerprint` from normalized advertisement text.
- Department labels are mapped to a small provisional taxonomy and stored via
  the many-to-many `job_posting_departments` table. Unmatched labels remain in
  the raw JSON. Team labels remain in the raw JSON.
- LLM extraction and cross-source canonical matching are deferred.

## Flow

```text
raw response
    -> source adapter
    -> extraction and normalization
    -> validation
    -> PostgreSQL upsert
```

## Result

Raw job data can be reprocessed into consistent operational records without
losing provider-specific information.

Run the processing step with:

```powershell
uv run job-market-parse
```

Use `--dry-run` to list raw runs without connecting to PostgreSQL. Processed
runs are recorded in `raw_ingestion_runs` and are skipped on later runs.
