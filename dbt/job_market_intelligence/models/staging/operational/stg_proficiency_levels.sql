{{ config(materialized='view') }}

select
    id as proficiency_level_id,
    name as proficiency_level_name,
    sort_order
from {{ source('operational', 'proficiency_levels') }}
