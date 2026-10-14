{{ config(materialized='view') }}

select
    posting.id as job_posting_id,
    posting.source_id,
    posting.source_job_id,
    posting.company_id,
    posting.role_id,
    posting.seniority_level_id as seniority_id,
    posting.raw_advertisement::text as raw_advertisement_json,
    posting.source_url,
    posting.source_published_at,
    posting.source_updated_at,
    posting.retrieved_at,
    posting.last_seen_at,
    posting.status,
    posting.normalization_version,
    posting.content_fingerprint,
    posting.created_at,
    posting.updated_at
from {{ source('operational', 'job_postings') }} as posting
