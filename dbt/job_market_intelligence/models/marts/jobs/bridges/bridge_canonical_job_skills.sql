{{ config(materialized='table') }}

select *
from {{ ref('fct_active_canonical_job_skill_requirements') }}
