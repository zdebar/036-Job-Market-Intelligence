{{ config(materialized='table') }}

select
    canonical_jobs.canonical_job_id,
    departments.department_id,
    department.department_name
from {{ ref('fct_active_canonical_jobs') }} as canonical_jobs
join {{ ref('stg_job_posting_departments') }} as departments
    on departments.job_posting_id = canonical_jobs.primary_job_posting_id
left join {{ ref('dim_department') }} as department
    on department.department_id = departments.department_id
