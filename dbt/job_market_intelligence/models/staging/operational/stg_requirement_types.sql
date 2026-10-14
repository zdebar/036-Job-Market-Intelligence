{{ config(materialized='view') }}

select
    id as requirement_type_id,
    name as requirement_type_name,
    sort_order
from {{ source('operational', 'requirement_types') }}
