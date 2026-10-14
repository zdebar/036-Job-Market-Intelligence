{{ config(materialized='view') }}

select
    postings.*,
    posting_source.canonical_job_id,
    posting_source.match_method,
    posting_source.matched_at,
    posting_source.selection_rank,
    compensation.salary_min,
    compensation.salary_max,
    compensation.salary_currency,
    compensation.salary_period
from {{ ref('stg_job_postings') }} as postings
left join {{ ref('stg_job_posting_sources') }} as posting_source
    on posting_source.job_posting_id = postings.job_posting_id
left join {{ ref('stg_job_posting_compensations') }} as compensation
    on compensation.job_posting_id = postings.job_posting_id
