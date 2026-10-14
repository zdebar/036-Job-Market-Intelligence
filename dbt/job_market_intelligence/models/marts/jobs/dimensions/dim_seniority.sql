{{ config(materialized='table') }}

select
    seniority_id,
    seniority_name,
    sort_order
from {{ ref('stg_seniority_levels') }}
