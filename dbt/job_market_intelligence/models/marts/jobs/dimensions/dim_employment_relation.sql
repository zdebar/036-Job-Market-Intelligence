{{ config(materialized='table') }}

select
    employment_relation_id,
    employment_relation_name
from {{ ref('stg_employment_relations') }}
