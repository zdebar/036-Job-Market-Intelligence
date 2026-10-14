ALTER TABLE job_posting_compensations
    ADD COLUMN salary_min_czk_month NUMERIC(12, 2),
    ADD COLUMN salary_max_czk_month NUMERIC(12, 2),
    ADD COLUMN salary_fx_rate NUMERIC(12, 6),
    ADD COLUMN salary_fx_rate_date DATE,
    ADD COLUMN salary_normalization_status TEXT NOT NULL DEFAULT 'not_comparable';

ALTER TABLE job_posting_compensations
    ADD CONSTRAINT job_posting_compensations_normalization_status_check
        CHECK (
            salary_normalization_status IN (
                'normalized', 'partial', 'not_comparable'
            )
        ),
    ADD CONSTRAINT job_posting_compensations_normalized_min_check
        CHECK (
            salary_min_czk_month IS NULL OR salary_min_czk_month >= 0
        ),
    ADD CONSTRAINT job_posting_compensations_normalized_max_check
        CHECK (
            salary_max_czk_month IS NULL OR salary_max_czk_month >= 0
        ),
    ADD CONSTRAINT job_posting_compensations_normalized_range_check
        CHECK (
            salary_min_czk_month IS NULL
            OR salary_max_czk_month IS NULL
            OR salary_max_czk_month >= salary_min_czk_month
        );
