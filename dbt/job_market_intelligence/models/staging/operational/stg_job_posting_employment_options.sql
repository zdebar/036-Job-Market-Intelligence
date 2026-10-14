{{ config(materialized='view') }}

select
    id as employment_option_id,
    job_posting_id,
    employment_relation_id,
    workload_id,
    hours_min,
    hours_max,
    hours_period
from {{ source('operational', 'job_posting_employment_options') }}
