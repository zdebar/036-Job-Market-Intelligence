{{ config(materialized='view') }}

select
    id as work_mode_id,
    name as work_mode_name
from {{ source('operational', 'work_modes') }}
