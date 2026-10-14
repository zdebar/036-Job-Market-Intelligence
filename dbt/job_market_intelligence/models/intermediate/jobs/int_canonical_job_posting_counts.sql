{{ config(materialized='view') }}

select
    canonical_job_id,
    count(*) as posting_count,
    count(*) filter (where status = 'active') as active_posting_count,
    count(distinct source_id) as source_count,
    min(created_at) as first_seen_at,
    max(last_seen_at) as last_seen_at
from {{ ref('int_job_postings_enriched') }}
where canonical_job_id is not null
group by canonical_job_id
