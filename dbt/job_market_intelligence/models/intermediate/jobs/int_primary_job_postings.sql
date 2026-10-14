{{ config(materialized='view') }}

select *
from {{ ref('int_job_postings_enriched') }}
where selection_rank = 1
