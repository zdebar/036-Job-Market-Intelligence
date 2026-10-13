WITH issues AS (
    SELECT
        'missing_canonical_link' AS issue,
        COUNT(*)::BIGINT AS issue_count
    FROM job_postings AS postings
    LEFT JOIN job_posting_sources AS links
        ON links.job_posting_id = postings.id
    WHERE links.job_posting_id IS NULL

    UNION ALL

    SELECT
        'canonical_without_posting',
        COUNT(*)::BIGINT
    FROM canonical_jobs AS canonical
    LEFT JOIN job_posting_sources AS links
        ON links.canonical_job_id = canonical.id
    WHERE links.canonical_job_id IS NULL

    UNION ALL

    SELECT
        'duplicate_fingerprint_across_canonicals',
        COUNT(*)::BIGINT
    FROM (
        SELECT postings.company_id, postings.content_fingerprint
        FROM job_postings AS postings
        JOIN job_posting_sources AS links
            ON links.job_posting_id = postings.id
        WHERE postings.content_fingerprint IS NOT NULL
        GROUP BY postings.company_id, postings.content_fingerprint
        HAVING COUNT(DISTINCT links.canonical_job_id) > 1
    ) AS duplicates
)
SELECT issue, issue_count
FROM issues
WHERE issue_count > 0
ORDER BY issue;
