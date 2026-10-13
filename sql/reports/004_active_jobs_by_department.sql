SELECT
    d.name AS department,
    COUNT(DISTINCT jpd.job_posting_id) AS active_postings
FROM job_posting_departments AS jpd
JOIN departments AS d ON d.id = jpd.department_id
JOIN job_postings AS jp ON jp.id = jpd.job_posting_id
WHERE jp.status = 'active'
GROUP BY d.id, d.name
ORDER BY active_postings DESC, department;
