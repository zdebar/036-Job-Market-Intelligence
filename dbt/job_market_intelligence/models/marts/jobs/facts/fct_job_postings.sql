{{ config(materialized='table') }}

select *
from {{ ref('int_job_postings_enriched') }}
