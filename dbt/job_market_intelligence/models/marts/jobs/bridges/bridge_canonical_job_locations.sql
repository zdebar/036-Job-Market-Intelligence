{{ config(materialized='table') }}

select
    canonical_jobs.canonical_job_id,
    locations.location_id,
    location.location_name
from {{ ref('fct_active_canonical_jobs') }} as canonical_jobs
join {{ ref('stg_job_posting_locations') }} as locations
    on locations.job_posting_id = canonical_jobs.primary_job_posting_id
left join {{ ref('dim_location') }} as location
    on location.location_id = locations.location_id
