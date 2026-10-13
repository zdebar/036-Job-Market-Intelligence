# Processing

## Goal

Convert immutable raw API responses into validated, normalized database records
and assign cross-source postings to canonical jobs.

## Flow

```text
raw response
    -> source adapter
    -> extraction and normalization
    -> validation
    -> posting upsert
    -> canonical assignment
    -> primary-posting ranking
    -> source lifecycle update
```

## Decisions

- A source posting is identified by `(source_id, source_job_id)`.
- Repeated downloads update the existing posting and preserve its canonical
  link.
- `content_fingerprint` is a SHA-256 hash of normalized advertisement text.
- New postings are matched only within the same company.
- One exact fingerprint candidate is an `algorithmic_match`.
- Otherwise, one candidate with the same role, locations, and compatible known
  seniority is an `algorithmic_match`.
- Ambiguous or missing matches create a new `canonical_job`.
- Existing canonical links are not automatically moved after a posting update.
- Ranking uses `source_updated_at`, then `retrieved_at`, completeness, and
  posting ID as a stable tie-breaker.
- Active postings receive `selection_rank`; inactive postings receive `NULL`.
- Postings missing from a successful complete source run become inactive.
  Partial and failed runs do not deactivate postings.
- LLM and manual matching remain reserved for later use.

## Result

Processing produces queryable normalized records, preserves the original raw
advertisement, and maintains canonical-job links and primary-posting ranking.

Run it with:

```powershell
uv run job-market-parse
```

Use `--reprocess-processed` to backfill existing processed runs after a
processing change.
