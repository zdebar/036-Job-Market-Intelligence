{{ config(materialized='table') }}

select
    role_id,
    role_name
from {{ ref('stg_roles') }}
