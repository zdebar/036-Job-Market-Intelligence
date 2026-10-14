{{ config(materialized='table') }}

select
    requirement_type_id,
    requirement_type_name,
    sort_order
from {{ ref('stg_requirement_types') }}
