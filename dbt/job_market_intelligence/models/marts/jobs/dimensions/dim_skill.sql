{{ config(materialized='table') }}

select
    skill_id,
    skill_name
from {{ ref('stg_skills') }}
