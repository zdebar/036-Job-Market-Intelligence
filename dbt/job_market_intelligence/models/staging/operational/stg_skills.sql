{{ config(materialized='view') }}

select
    id as skill_id,
    name as skill_name
from {{ source('operational', 'skills') }}
