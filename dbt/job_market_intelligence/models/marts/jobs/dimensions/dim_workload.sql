{{ config(materialized='table') }}

select
    workload_id,
    workload_name
from {{ ref('stg_workloads') }}
