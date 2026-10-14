select
    job_posting_id,
    skill_id
from {{ ref('fct_active_job_posting_skill_requirements') }}
group by
    job_posting_id,
    skill_id
having count(*) > 1
