-- SaralAI Scheme Database Schema
-- SQLite database for storing government welfare scheme information

CREATE TABLE IF NOT EXISTS schemes (
    id              TEXT PRIMARY KEY,
    title_en        TEXT NOT NULL,
    title_hi        TEXT,
    title_kn        TEXT,
    ministry        TEXT,
    scope           TEXT CHECK (scope IN ('national', 'state')),
    state           TEXT,                          -- NULL if national
    category        TEXT NOT NULL,                 -- widow, disability, edu, etc.

    -- eligibility predicates (JSON array of {field, op, value})
    eligibility     TEXT NOT NULL,

    benefit_en      TEXT NOT NULL,
    benefit_hi      TEXT,
    benefit_kn      TEXT,

    documents       TEXT NOT NULL,                 -- JSON array of doc keys
    application_url TEXT,
    office_template TEXT,

    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schemes_category ON schemes(category);
CREATE INDEX IF NOT EXISTS idx_schemes_state    ON schemes(state);
CREATE INDEX IF NOT EXISTS idx_schemes_scope    ON schemes(scope);
