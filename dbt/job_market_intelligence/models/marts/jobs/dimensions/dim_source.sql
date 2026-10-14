{{ config(materialized='table') }}

select
    source_id,
    source_key,
    source_name
from {{ ref('stg_sources') }}
