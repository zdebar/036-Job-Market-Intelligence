{{ config(materialized='table') }}

select
    postings.job_posting_id,
    locations.location_id,
    location.location_name
from {{ ref('fct_active_job_postings') }} as postings
join {{ ref('stg_job_posting_locations') }} as locations
    on locations.job_posting_id = postings.job_posting_id
left join {{ ref('dim_location') }} as location
    on location.location_id = locations.location_id
