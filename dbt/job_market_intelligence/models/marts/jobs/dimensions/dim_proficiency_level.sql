{{ config(materialized='table') }}

select
    proficiency_level_id,
    proficiency_level_name,
    sort_order
from {{ ref('stg_proficiency_levels') }}
