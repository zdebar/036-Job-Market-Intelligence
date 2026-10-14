select
    canonical_job_id,
    skill_id
from {{ ref('fct_active_canonical_job_skill_requirements') }}
group by
    canonical_job_id,
    skill_id
having count(*) > 1
