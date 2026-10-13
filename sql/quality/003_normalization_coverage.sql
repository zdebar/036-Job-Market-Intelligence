SELECT
    COUNT(*) AS total_postings,
    COUNT(*) FILTER (WHERE company_id IS NULL) AS missing_company,
    COUNT(*) FILTER (WHERE role_id IS NULL) AS missing_role,
    COUNT(*) FILTER (WHERE seniority_level_id IS NULL) AS missing_seniority,
    COUNT(*) FILTER (
        WHERE NOT EXISTS (
            SELECT 1
            FROM job_posting_departments AS jpd
            WHERE jpd.job_posting_id = jp.id
        )
    ) AS missing_department,
    COUNT(*) FILTER (
        WHERE NOT EXISTS (
            SELECT 1
            FROM job_posting_locations AS jpl
            WHERE jpl.job_posting_id = jp.id
        )
    ) AS missing_location,
    COUNT(*) FILTER (
        WHERE NOT EXISTS (
            SELECT 1
            FROM job_posting_work_modes AS jpwm
            WHERE jpwm.job_posting_id = jp.id
        )
    ) AS missing_work_mode
FROM job_postings AS jp;
