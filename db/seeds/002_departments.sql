-- Provisional canonical departments for the first extraction and normalization pass.
-- Source-specific labels are mapped to these broader categories in config/normalization.

INSERT INTO departments (name)
VALUES
    ('Engineering'),
    ('Data & Analytics'),
    ('Go-to-Market'),
    ('Customer Success'),
    ('Operations'),
    ('Finance & Legal'),
    ('Asset Management'),
    ('Security & Compliance')
ON CONFLICT (name) DO NOTHING;
