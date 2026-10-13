DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM raw_ingestion_runs
        WHERE status = 'processed'
          AND record_count IS NOT NULL
          AND record_count <> processed_records
    ) THEN
        RAISE EXCEPTION 'A processed ingestion run has a record-count mismatch.';
    END IF;
END $$;

WITH run_errors AS (
    SELECT
        raw_ingestion_run_id,
        COUNT(*) AS error_records
    FROM raw_ingestion_record_errors
    GROUP BY raw_ingestion_run_id
)
SELECT
    runs.status,
    COUNT(*) AS runs,
    COALESCE(SUM(runs.record_count), 0) AS downloaded_records,
    COALESCE(SUM(runs.processed_records), 0) AS processed_records,
    COALESCE(SUM(run_errors.error_records), 0) AS error_records
FROM raw_ingestion_runs AS runs
LEFT JOIN run_errors ON run_errors.raw_ingestion_run_id = runs.id
GROUP BY runs.status
ORDER BY runs.status;
