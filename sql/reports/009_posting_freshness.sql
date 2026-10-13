SELECT
    jp.status,
    COUNT(*) AS postings,
    MIN(jp.last_seen_at) AS earliest_last_seen_at,
    MAX(jp.last_seen_at) AS latest_last_seen_at,
    COUNT(*) FILTER (WHERE jp.last_seen_at >= CURRENT_TIMESTAMP - INTERVAL '7 days')
        AS seen_in_last_7_days
FROM job_postings AS jp
GROUP BY jp.status
ORDER BY jp.status;
