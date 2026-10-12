BEGIN;

-- Squashed initial schema based on migrations 001-006 from 035-Job-Data.
-- This file represents the final schema for a fresh 036 database.

CREATE TABLE sources (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    source_key TEXT NOT NULL UNIQUE
);

CREATE TABLE companies (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE roles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE skills (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE seniority_levels (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    sort_order SMALLINT NOT NULL UNIQUE
);

CREATE TABLE proficiency_levels (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    sort_order SMALLINT NOT NULL UNIQUE
);

CREATE TABLE requirement_types (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    sort_order SMALLINT NOT NULL UNIQUE
);

CREATE TABLE employment_relations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE workloads (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE work_modes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE locations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE job_postings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES sources(id),
    source_job_id TEXT NOT NULL,
    company_id BIGINT REFERENCES companies(id),
    role_id BIGINT REFERENCES roles(id),
    seniority_level_id BIGINT REFERENCES seniority_levels(id),
    raw_advertisement JSONB NOT NULL,
    content_fingerprint TEXT,
    source_url TEXT,
    source_published_at TIMESTAMPTZ,
    source_updated_at TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    normalization_version TEXT NOT NULL DEFAULT 'v1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_id, source_job_id),
    CHECK (status IN ('active', 'inactive', 'unknown')),
    CHECK (
        content_fingerprint IS NULL
        OR content_fingerprint ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE job_posting_locations (
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    location_id BIGINT NOT NULL REFERENCES locations(id),
    PRIMARY KEY (job_posting_id, location_id)
);

CREATE TABLE job_posting_work_modes (
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    work_mode_id BIGINT NOT NULL REFERENCES work_modes(id),
    PRIMARY KEY (job_posting_id, work_mode_id)
);

CREATE TABLE job_posting_employment_options (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    employment_relation_id BIGINT REFERENCES employment_relations(id),
    workload_id BIGINT REFERENCES workloads(id),
    hours_min NUMERIC(7, 2),
    hours_max NUMERIC(7, 2),
    hours_period TEXT,
    CHECK (hours_min IS NULL OR hours_min >= 0),
    CHECK (hours_max IS NULL OR hours_max >= 0),
    CHECK (
        hours_min IS NULL
        OR hours_max IS NULL
        OR hours_max >= hours_min
    ),
    CHECK (
        hours_period IS NULL
        OR hours_period IN ('day', 'week', 'month', 'year')
    ),
    CONSTRAINT job_posting_employment_options_hours_minimum_check
        CHECK (
            hours_min IS NULL
            OR hours_min <= CASE hours_period
                WHEN 'day' THEN 24
                WHEN 'week' THEN 168
                WHEN 'month' THEN 744
                WHEN 'year' THEN 8784
                ELSE 8784
            END
        ),
    CONSTRAINT job_posting_employment_options_hours_maximum_check
        CHECK (
            hours_max IS NULL
            OR hours_max <= CASE hours_period
                WHEN 'day' THEN 24
                WHEN 'week' THEN 168
                WHEN 'month' THEN 744
                WHEN 'year' THEN 8784
                ELSE 8784
            END
        )
);

CREATE TABLE job_skill_requirements (
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    skill_id BIGINT NOT NULL REFERENCES skills(id),
    proficiency_level_id BIGINT REFERENCES proficiency_levels(id),
    requirement_type_id BIGINT REFERENCES requirement_types(id),
    priority SMALLINT,
    PRIMARY KEY (job_posting_id, skill_id),
    CHECK (priority IS NULL OR priority BETWEEN 1 AND 5)
);

CREATE TABLE job_posting_compensations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    salary_min NUMERIC(12, 2),
    salary_max NUMERIC(12, 2),
    salary_currency TEXT,
    salary_period TEXT,
    CHECK (salary_min IS NOT NULL OR salary_max IS NOT NULL),
    CHECK (salary_min IS NULL OR salary_min >= 0),
    CHECK (salary_max IS NULL OR salary_max >= 0),
    CHECK (
        salary_min IS NULL
        OR salary_max IS NULL
        OR salary_max >= salary_min
    ),
    CHECK (
        salary_currency IS NULL
        OR salary_currency ~ '^[A-Z]{3}$'
    ),
    CHECK (
        salary_period IS NULL
        OR salary_period IN ('hour', 'day', 'week', 'month', 'year', 'project')
    ),
    UNIQUE (job_posting_id)
);

CREATE TABLE canonical_jobs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE job_posting_sources (
    canonical_job_id BIGINT NOT NULL REFERENCES canonical_jobs(id) ON DELETE CASCADE,
    job_posting_id BIGINT NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    match_method TEXT NOT NULL DEFAULT 'new_canonical_job',
    matched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    selection_rank INTEGER,
    PRIMARY KEY (canonical_job_id, job_posting_id),
    UNIQUE (job_posting_id),
    CHECK (
        match_method IN (
            'new_canonical_job',
            'algorithmic_match',
            'llm_match',
            'manual_match'
        )
    ),
    CHECK (selection_rank IS NULL OR selection_rank >= 1)
);

CREATE TABLE raw_ingestion_runs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    raw_path TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ,
    record_count INTEGER,
    payload_sha256 TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    processed_records INTEGER NOT NULL DEFAULT 0,
    parser_version TEXT,
    error_message TEXT,
    processing_started_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_id, run_id),
    CHECK (status IN ('pending', 'processing', 'processed', 'partial', 'failed')),
    CHECK (record_count IS NULL OR record_count >= 0),
    CHECK (processed_records >= 0)
);

CREATE TABLE raw_ingestion_record_errors (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    raw_ingestion_run_id BIGINT NOT NULL REFERENCES raw_ingestion_runs(id) ON DELETE CASCADE,
    source_job_id TEXT,
    stage TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX job_postings_source_id_idx ON job_postings (source_id);
CREATE INDEX job_postings_company_id_idx ON job_postings (company_id);
CREATE INDEX job_postings_role_id_idx ON job_postings (role_id);
CREATE INDEX job_postings_last_seen_at_idx ON job_postings (last_seen_at);
CREATE INDEX job_postings_content_fingerprint_idx
    ON job_postings (content_fingerprint);
CREATE INDEX job_posting_locations_location_id_idx
    ON job_posting_locations (location_id);
CREATE INDEX job_posting_work_modes_work_mode_id_idx
    ON job_posting_work_modes (work_mode_id);
CREATE INDEX job_posting_employment_options_relation_id_idx
    ON job_posting_employment_options (employment_relation_id);
CREATE INDEX job_skill_requirements_skill_id_idx
    ON job_skill_requirements (skill_id);
CREATE INDEX job_posting_sources_canonical_job_id_idx
    ON job_posting_sources (canonical_job_id);
CREATE UNIQUE INDEX job_posting_sources_canonical_rank_idx
    ON job_posting_sources (canonical_job_id, selection_rank)
    WHERE selection_rank IS NOT NULL;
CREATE INDEX raw_ingestion_runs_status_idx
    ON raw_ingestion_runs (status);
CREATE INDEX raw_ingestion_runs_source_id_idx
    ON raw_ingestion_runs (source_id);
CREATE INDEX raw_ingestion_record_errors_run_id_idx
    ON raw_ingestion_record_errors (raw_ingestion_run_id);

COMMIT;
