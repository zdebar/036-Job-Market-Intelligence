-- These views are managed by dbt and are recreated by the next dbt build.
DROP VIEW IF EXISTS analytics_intermediate.int_canonical_job_posting_counts;
DROP VIEW IF EXISTS analytics_intermediate.int_primary_job_postings;
DROP VIEW IF EXISTS analytics_intermediate.int_job_postings_enriched;
DROP VIEW IF EXISTS analytics_staging.stg_job_posting_compensations;

ALTER TABLE job_posting_compensations
    DROP COLUMN IF EXISTS salary_fx_rate,
    DROP COLUMN IF EXISTS salary_fx_rate_date,
    DROP COLUMN IF EXISTS salary_normalization_status;
