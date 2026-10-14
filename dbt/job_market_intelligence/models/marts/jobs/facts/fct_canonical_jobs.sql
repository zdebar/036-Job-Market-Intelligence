{{ config(materialized='table') }}

select
    canonical.canonical_job_id,
    primary_posting.job_posting_id as primary_job_posting_id,
    case
        when coalesce(counts.active_posting_count, 0) > 0 then 'active'
        else 'inactive'
    end as status,
    coalesce(counts.posting_count, 0) as posting_count,
    coalesce(counts.active_posting_count, 0) as active_posting_count,
    coalesce(counts.source_count, 0) as source_count,
    counts.first_seen_at,
    counts.last_seen_at,
    primary_posting.company_id,
    primary_posting.role_id,
    primary_posting.source_id,
    primary_posting.seniority_id,
    primary_posting.source_published_at,
    primary_posting.source_url,
    primary_posting.salary_min,
    primary_posting.salary_max,
    primary_posting.salary_currency,
    primary_posting.salary_period
from {{ ref('stg_canonical_jobs') }} as canonical
left join {{ ref('int_canonical_job_posting_counts') }} as counts
    on counts.canonical_job_id = canonical.canonical_job_id
left join {{ ref('int_primary_job_postings') }} as primary_posting
    on primary_posting.canonical_job_id = canonical.canonical_job_id
