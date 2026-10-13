DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM job_posting_locations AS bridge
        LEFT JOIN job_postings AS jp ON jp.id = bridge.job_posting_id
        WHERE jp.id IS NULL
    ) OR EXISTS (
        SELECT 1
        FROM job_posting_departments AS bridge
        LEFT JOIN job_postings AS jp ON jp.id = bridge.job_posting_id
        WHERE jp.id IS NULL
    ) OR EXISTS (
        SELECT 1
        FROM job_posting_work_modes AS bridge
        LEFT JOIN job_postings AS jp ON jp.id = bridge.job_posting_id
        WHERE jp.id IS NULL
    ) OR EXISTS (
        SELECT 1
        FROM job_skill_requirements AS bridge
        LEFT JOIN job_postings AS jp ON jp.id = bridge.job_posting_id
        WHERE jp.id IS NULL
    ) THEN
        RAISE EXCEPTION 'A bridge table contains an orphan posting reference.';
    END IF;
END $$;

SELECT bridge_name, orphan_rows
FROM (
    SELECT
        'job_posting_locations' AS bridge_name,
        COUNT(*) FILTER (WHERE jp.id IS NULL) AS orphan_rows
    FROM job_posting_locations AS bridge
    LEFT JOIN job_postings AS jp ON jp.id = bridge.job_posting_id
    UNION ALL
    SELECT
        'job_posting_departments',
        COUNT(*) FILTER (WHERE jp.id IS NULL)
    FROM job_posting_departments AS bridge
    LEFT JOIN job_postings AS jp ON jp.id = bridge.job_posting_id
    UNION ALL
    SELECT
        'job_posting_work_modes',
        COUNT(*) FILTER (WHERE jp.id IS NULL)
    FROM job_posting_work_modes AS bridge
    LEFT JOIN job_postings AS jp ON jp.id = bridge.job_posting_id
    UNION ALL
    SELECT
        'job_skill_requirements',
        COUNT(*) FILTER (WHERE jp.id IS NULL)
    FROM job_skill_requirements AS bridge
    LEFT JOIN job_postings AS jp ON jp.id = bridge.job_posting_id
) AS bridge_checks
ORDER BY bridge_name;
