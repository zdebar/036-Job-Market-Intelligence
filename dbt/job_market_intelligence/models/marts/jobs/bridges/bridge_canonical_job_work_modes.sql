{{ config(materialized='table') }}

select
    canonical_jobs.canonical_job_id,
    work_modes.work_mode_id,
    work_mode.work_mode_name
from {{ ref('fct_active_canonical_jobs') }} as canonical_jobs
join {{ ref('stg_job_posting_work_modes') }} as work_modes
    on work_modes.job_posting_id = canonical_jobs.primary_job_posting_id
left join {{ ref('dim_work_mode') }} as work_mode
    on work_mode.work_mode_id = work_modes.work_mode_id
