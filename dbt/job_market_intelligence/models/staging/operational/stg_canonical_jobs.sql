{{ config(materialized='view') }}

select
    id as canonical_job_id,
    created_at,
    updated_at
from {{ source('operational', 'canonical_jobs') }}
