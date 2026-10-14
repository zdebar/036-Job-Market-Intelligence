{{ config(materialized='table') }}

select
    postings.job_posting_id,
    postings.canonical_job_id,
    options.employment_option_id,
    options.employment_relation_id,
    employment_relations.employment_relation_name,
    options.workload_id,
    workloads.workload_name,
    options.hours_min,
    options.hours_max,
    options.hours_period
from {{ ref('fct_active_job_postings') }} as postings
join {{ ref('stg_job_posting_employment_options') }} as options
    on options.job_posting_id = postings.job_posting_id
left join {{ ref('dim_employment_relation') }} as employment_relations
    on employment_relations.employment_relation_id = options.employment_relation_id
left join {{ ref('dim_workload') }} as workloads
    on workloads.workload_id = options.workload_id
