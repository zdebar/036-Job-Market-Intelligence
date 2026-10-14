{{ config(materialized='view') }}

select
    id as workload_id,
    name as workload_name
from {{ source('operational', 'workloads') }}
