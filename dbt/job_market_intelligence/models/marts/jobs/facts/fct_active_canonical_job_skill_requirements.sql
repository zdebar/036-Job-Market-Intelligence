{{ config(materialized='table') }}

select
    canonical_jobs.canonical_job_id,
    canonical_jobs.primary_job_posting_id as job_posting_id,
    requirements.skill_id,
    skills.skill_name,
    requirements.proficiency_level_id,
    proficiency.proficiency_level_name,
    requirements.requirement_type_id,
    requirement_types.requirement_type_name,
    requirements.priority
from {{ ref('fct_active_canonical_jobs') }} as canonical_jobs
join {{ ref('stg_job_skill_requirements') }} as requirements
    on requirements.job_posting_id = canonical_jobs.primary_job_posting_id
left join {{ ref('dim_skill') }} as skills
    on skills.skill_id = requirements.skill_id
left join {{ ref('dim_proficiency_level') }} as proficiency
    on proficiency.proficiency_level_id = requirements.proficiency_level_id
left join {{ ref('dim_requirement_type') }} as requirement_types
    on requirement_types.requirement_type_id = requirements.requirement_type_id
