{{ config(materialized='view') }}

select
    job_posting_id,
    department_id
from {{ source('operational', 'job_posting_departments') }}
