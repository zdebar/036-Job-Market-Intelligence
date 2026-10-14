{{ config(materialized='table') }}

select
    company_id,
    company_name
from {{ ref('stg_companies') }}
