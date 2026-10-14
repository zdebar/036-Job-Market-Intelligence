{{ config(materialized='view') }}

select
    id as department_id,
    name as department_name
from {{ source('operational', 'departments') }}
