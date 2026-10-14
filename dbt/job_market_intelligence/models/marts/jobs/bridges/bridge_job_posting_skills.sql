{{ config(materialized='table') }}

select *
from {{ ref('fct_active_job_posting_skill_requirements') }}
