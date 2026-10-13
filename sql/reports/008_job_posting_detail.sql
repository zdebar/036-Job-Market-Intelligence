WITH posting_departments AS (
    SELECT
        jpd.job_posting_id,
        string_agg(d.name, ', ' ORDER BY d.name) AS departments
    FROM job_posting_departments AS jpd
    JOIN departments AS d ON d.id = jpd.department_id
    GROUP BY jpd.job_posting_id
), posting_locations AS (
    SELECT
        jpl.job_posting_id,
        string_agg(l.name, '; ' ORDER BY l.name) AS locations
    FROM job_posting_locations AS jpl
    JOIN locations AS l ON l.id = jpl.location_id
    GROUP BY jpl.job_posting_id
), posting_work_modes AS (
    SELECT
        jpwm.job_posting_id,
        string_agg(wm.name, ', ' ORDER BY wm.name) AS work_modes
    FROM job_posting_work_modes AS jpwm
    JOIN work_modes AS wm ON wm.id = jpwm.work_mode_id
    GROUP BY jpwm.job_posting_id
), posting_employment AS (
    SELECT
        jpeo.job_posting_id,
        string_agg(
            er.name || COALESCE(' (' || w.name || ')', ''),
            ', ' ORDER BY er.name, w.name
        ) AS employment_options
    FROM job_posting_employment_options AS jpeo
    JOIN employment_relations AS er ON er.id = jpeo.employment_relation_id
    LEFT JOIN workloads AS w ON w.id = jpeo.workload_id
    GROUP BY jpeo.job_posting_id
), posting_skills AS (
    SELECT
        jsr.job_posting_id,
        string_agg(s.name, ', ' ORDER BY s.name) AS skills
    FROM job_skill_requirements AS jsr
    JOIN skills AS s ON s.id = jsr.skill_id
    GROUP BY jsr.job_posting_id
)
SELECT
    jp.id,
    jp.source_job_id,
    s.name AS source,
    c.name AS company,
    r.name AS role,
    sl.name AS seniority,
    pd.departments,
    pl.locations,
    pwm.work_modes,
    pe.employment_options,
    pc.salary_min,
    pc.salary_max,
    pc.salary_currency,
    ps.skills,
    jp.status,
    jp.source_published_at,
    jp.last_seen_at,
    jp.source_url
FROM job_postings AS jp
JOIN sources AS s ON s.id = jp.source_id
LEFT JOIN companies AS c ON c.id = jp.company_id
LEFT JOIN roles AS r ON r.id = jp.role_id
LEFT JOIN seniority_levels AS sl ON sl.id = jp.seniority_level_id
LEFT JOIN posting_departments AS pd ON pd.job_posting_id = jp.id
LEFT JOIN posting_locations AS pl ON pl.job_posting_id = jp.id
LEFT JOIN posting_work_modes AS pwm ON pwm.job_posting_id = jp.id
LEFT JOIN posting_employment AS pe ON pe.job_posting_id = jp.id
LEFT JOIN posting_skills AS ps ON ps.job_posting_id = jp.id
LEFT JOIN job_posting_compensations AS pc ON pc.job_posting_id = jp.id
ORDER BY jp.last_seen_at DESC, jp.id;
