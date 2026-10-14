{{ config(materialized='table') }}

select
    postings.job_posting_id,
    departments.department_id,
    department.department_name
from {{ ref('fct_active_job_postings') }} as postings
join {{ ref('stg_job_posting_departments') }} as departments
    on departments.job_posting_id = postings.job_posting_id
left join {{ ref('dim_department') }} as department
    on department.department_id = departments.department_id
