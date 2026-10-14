{{ config(materialized='view') }}

select
    job_posting_id,
    salary_min,
    salary_max,
    salary_currency,
    salary_period,
    salary_min_czk_month,
    salary_max_czk_month
from {{ source('operational', 'job_posting_compensations') }}
