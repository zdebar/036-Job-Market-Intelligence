{{ config(materialized='table') }}

select *
from {{ ref('fct_canonical_jobs') }}
where status = 'active'
