DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM raw_ingestion_record_errors) THEN
        RAISE EXCEPTION 'Raw ingestion contains record-level errors.';
    END IF;
END $$;

SELECT
    COALESCE(stage, '[unknown stage]') AS stage,
    COUNT(*) AS errors
FROM raw_ingestion_record_errors
GROUP BY stage
ORDER BY stage;
