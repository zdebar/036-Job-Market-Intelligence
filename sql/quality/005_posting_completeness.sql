SELECT
    COUNT(*) AS total_postings,
    COUNT(*) FILTER (WHERE source_url IS NULL OR source_url = '') AS missing_source_url,
    COUNT(*) FILTER (WHERE raw_advertisement IS NULL) AS missing_raw_advertisement,
    COUNT(*) FILTER (
        WHERE content_fingerprint IS NULL OR content_fingerprint = ''
    ) AS missing_fingerprint,
    COUNT(*) FILTER (WHERE last_seen_at IS NULL) AS missing_last_seen_at
FROM job_postings;
