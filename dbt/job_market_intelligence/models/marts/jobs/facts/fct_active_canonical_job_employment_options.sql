{{ config(materialized='table') }}

select
    canonical_jobs.canonical_job_id,
    canonical_jobs.primary_job_posting_id as job_posting_id,
    options.employment_option_id,
    options.employment_relation_id,
    employment_relations.employment_relation_name,
    options.workload_id,
    workloads.workload_name,
    options.hours_min,
    options.hours_max,
    options.hours_period
from {{ ref('fct_active_canonical_jobs') }} as canonical_jobs
join {{ ref('stg_job_posting_employment_options') }} as options
    on options.job_posting_id = canonical_jobs.primary_job_posting_id
left join {{ ref('dim_employment_relation') }} as employment_relations
    on employment_relations.employment_relation_id = options.employment_relation_id
left join {{ ref('dim_workload') }} as workloads
    on workloads.workload_id = options.workload_id
