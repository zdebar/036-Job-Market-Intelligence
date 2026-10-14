{{ config(materialized='view') }}

select
    id as employment_relation_id,
    name as employment_relation_name
from {{ source('operational', 'employment_relations') }}
