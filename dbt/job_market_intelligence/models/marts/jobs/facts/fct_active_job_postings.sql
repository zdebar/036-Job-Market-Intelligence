{{ config(materialized='table') }}

select *
from {{ ref('fct_job_postings') }}
where status = 'active'
