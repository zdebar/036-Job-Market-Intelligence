{{ config(materialized='table') }}

select
    work_mode_id,
    work_mode_name
from {{ ref('stg_work_modes') }}
