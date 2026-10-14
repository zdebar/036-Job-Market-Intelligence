{{ config(materialized='view') }}

select
    id as location_id,
    name as location_name
from {{ source('operational', 'locations') }}
