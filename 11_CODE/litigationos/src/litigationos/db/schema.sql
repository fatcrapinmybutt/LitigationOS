-- LitigationOS Product Database Schema
-- Auto-generated from Pydantic models + DEVELOPER.md + seed.py references

-- Jurisdiction plugin registry
CREATE TABLE IF NOT EXISTS jurisdictions (
    id TEXT PRIMARY KEY,          -- e.g., 'MI'
    name TEXT NOT NULL,           -- e.g., 'Michigan'
    state_code TEXT,
    rules_version TEXT,
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Court directory
CREATE TABLE IF NOT EXISTS courts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction_id TEXT REFERENCES jurisdictions(id),
    name TEXT NOT NULL,
    type TEXT,                    -- 'circuit', 'district', 'coa', 'supreme', 'federal'
    county TEXT,
    address TEXT,
    phone TEXT,
    efiling_url TEXT,
    local_rules_url TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Top-level case container
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_number TEXT,
    court_id INTEGER REFERENCES courts(id),
    case_type TEXT,               -- 'family', 'civil', 'criminal', 'appellate', 'federal'
    title TEXT NOT NULL,
    filed_date TEXT,
    status TEXT DEFAULT 'active', -- 'active', 'closed', 'appealed', 'settled'
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Parties involved in a case
CREATE TABLE IF NOT EXISTS parties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL REFERENCES cases(id),
    name TEXT NOT NULL,
    role TEXT NOT NULL,           -- 'plaintiff', 'defendant', 'respondent', 'petitioner', 'intervenor', 'judge', 'attorney'
    party_type TEXT,              -- 'individual', 'corporation', 'government', 'organization'
    bar_number TEXT,
    email TEXT,
    phone TEXT,
    address TEXT
);

-- Legal claims/counts within a case
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL REFERENCES cases(id),
    count_number INTEGER,
    title TEXT NOT NULL,          -- e.g., 'Count I: IIED'
    legal_basis TEXT,             -- e.g., 'MCL 600.2911'
    against_party_id INTEGER REFERENCES parties(id),
    status TEXT DEFAULT 'active',
    damages_sought REAL,
    notes TEXT
);

-- Court rules per jurisdiction
CREATE TABLE IF NOT EXISTS court_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction_id TEXT REFERENCES jurisdictions(id),
    rule_number TEXT NOT NULL,    -- e.g., 'MCR 2.119'
    title TEXT,
    full_text TEXT,
    category TEXT,                -- e.g., 'civil_procedure', 'appellate', 'evidence'
    effective_date TEXT,
    notes TEXT
);

-- Court filings with status tracking
CREATE TABLE IF NOT EXISTS filings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL REFERENCES cases(id),
    title TEXT NOT NULL,
    filing_type TEXT,             -- 'complaint', 'motion', 'brief', 'response', 'reply', 'order', 'notice'
    status TEXT DEFAULT 'draft',  -- 'draft', 'review', 'ready', 'filed', 'served'
    file_path TEXT,
    filed_date TEXT,
    served_date TEXT,
    compliance_score REAL,
    word_count INTEGER,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Calculated and manual deadlines
CREATE TABLE IF NOT EXISTS deadlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL REFERENCES cases(id),
    filing_id INTEGER REFERENCES filings(id),
    title TEXT NOT NULL,
    due_date TEXT NOT NULL,
    rule_basis TEXT,              -- e.g., 'MCR 7.212(A)(1)(a) - 56 days from claim of appeal'
    status TEXT DEFAULT 'pending', -- 'pending', 'extended', 'met', 'missed'
    priority TEXT DEFAULT 'normal', -- 'critical', 'high', 'normal', 'low'
    reminder_days INTEGER DEFAULT 7,
    notes TEXT
);

-- Evidence items with Bates numbers
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL REFERENCES cases(id),
    bates_number TEXT,            -- e.g., 'PIGORS-0001'
    title TEXT NOT NULL,
    description TEXT,
    file_path TEXT,
    file_type TEXT,               -- 'pdf', 'image', 'text', 'email', 'screenshot', 'document'
    source TEXT,
    date_created TEXT,
    date_imported TEXT DEFAULT (datetime('now')),
    authentication_method TEXT,   -- 'self_auth_902', 'witness_901', 'certification', 'stipulation'
    foundation_witness TEXT,
    relevance_score REAL,
    tags TEXT,                    -- JSON array of tags
    notes TEXT
);

-- Jinja2 document templates
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction_id TEXT REFERENCES jurisdictions(id),
    name TEXT NOT NULL,
    template_type TEXT,           -- 'motion', 'brief', 'complaint', 'order', 'service', 'affidavit'
    content TEXT NOT NULL,        -- Jinja2 template content
    variables TEXT,               -- JSON schema of required variables
    court_rule TEXT,              -- MCR/FRCP rule this template follows
    notes TEXT
);

-- Generated documents
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id INTEGER REFERENCES filings(id),
    template_id INTEGER REFERENCES templates(id),
    title TEXT NOT NULL,
    content TEXT,                 -- Markdown content
    output_path TEXT,             -- Generated DOCX/PDF path
    format TEXT DEFAULT 'md',     -- 'md', 'docx', 'pdf'
    variables TEXT,               -- JSON of template variables used
    created_at TEXT DEFAULT (datetime('now'))
);

-- Chronological case events
CREATE TABLE IF NOT EXISTS timeline_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL REFERENCES cases(id),
    event_date TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    event_type TEXT,              -- 'filing', 'hearing', 'order', 'communication', 'incident', 'deadline'
    evidence_ids TEXT,            -- JSON array of evidence IDs
    filing_id INTEGER REFERENCES filings(id),
    importance TEXT DEFAULT 'normal' -- 'critical', 'high', 'normal', 'low'
);

-- Key-value application settings
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    category TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Michigan SCAO forms catalog
CREATE TABLE IF NOT EXISTS scao_forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_number TEXT NOT NULL,    -- e.g., 'MC 20', 'CC 375'
    title TEXT NOT NULL,
    category TEXT,                -- e.g., 'domestic', 'civil', 'criminal', 'probate'
    court_type TEXT,              -- 'circuit', 'district', 'probate', 'coa'
    url TEXT,
    notes TEXT
);

-- ── FTS5 Virtual Tables ──────────────────────────────────────────

CREATE VIRTUAL TABLE IF NOT EXISTS evidence_fts USING fts5(
    title, description, source, tags, notes,
    content='evidence',
    content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS court_rules_fts USING fts5(
    rule_number, title, full_text, category,
    content='court_rules',
    content_rowid='id'
);

-- ── FTS5 Sync Triggers ──────────────────────────────────────────

-- Evidence FTS triggers
CREATE TRIGGER IF NOT EXISTS evidence_ai AFTER INSERT ON evidence BEGIN
    INSERT INTO evidence_fts(rowid, title, description, source, tags, notes)
    VALUES (new.id, new.title, new.description, new.source, new.tags, new.notes);
END;

CREATE TRIGGER IF NOT EXISTS evidence_ad AFTER DELETE ON evidence BEGIN
    INSERT INTO evidence_fts(evidence_fts, rowid, title, description, source, tags, notes)
    VALUES ('delete', old.id, old.title, old.description, old.source, old.tags, old.notes);
END;

CREATE TRIGGER IF NOT EXISTS evidence_au AFTER UPDATE ON evidence BEGIN
    INSERT INTO evidence_fts(evidence_fts, rowid, title, description, source, tags, notes)
    VALUES ('delete', old.id, old.title, old.description, old.source, old.tags, old.notes);
    INSERT INTO evidence_fts(rowid, title, description, source, tags, notes)
    VALUES (new.id, new.title, new.description, new.source, new.tags, new.notes);
END;

-- Court rules FTS triggers
CREATE TRIGGER IF NOT EXISTS court_rules_ai AFTER INSERT ON court_rules BEGIN
    INSERT INTO court_rules_fts(rowid, rule_number, title, full_text, category)
    VALUES (new.id, new.rule_number, new.title, new.full_text, new.category);
END;

CREATE TRIGGER IF NOT EXISTS court_rules_ad AFTER DELETE ON court_rules BEGIN
    INSERT INTO court_rules_fts(court_rules_fts, rowid, rule_number, title, full_text, category)
    VALUES ('delete', old.id, old.rule_number, old.title, old.full_text, old.category);
END;

CREATE TRIGGER IF NOT EXISTS court_rules_au AFTER UPDATE ON court_rules BEGIN
    INSERT INTO court_rules_fts(court_rules_fts, rowid, rule_number, title, full_text, category)
    VALUES ('delete', old.id, old.rule_number, old.title, old.full_text, old.category);
    INSERT INTO court_rules_fts(rowid, rule_number, title, full_text, category)
    VALUES (new.id, new.rule_number, new.title, new.full_text, new.category);
END;

-- ── Indexes ──────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_cases_case_number ON cases(case_number);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_parties_case_id ON parties(case_id);
CREATE INDEX IF NOT EXISTS idx_parties_role ON parties(role);
CREATE INDEX IF NOT EXISTS idx_claims_case_id ON claims(case_id);
CREATE INDEX IF NOT EXISTS idx_filings_case_id ON filings(case_id);
CREATE INDEX IF NOT EXISTS idx_filings_case ON filings(case_id);
CREATE INDEX IF NOT EXISTS idx_filings_status ON filings(status);
CREATE INDEX IF NOT EXISTS idx_deadlines_case_id ON deadlines(case_id);
CREATE INDEX IF NOT EXISTS idx_deadlines_due_date ON deadlines(due_date);
CREATE INDEX IF NOT EXISTS idx_deadlines_status ON deadlines(status);
CREATE INDEX IF NOT EXISTS idx_evidence_case_id ON evidence(case_id);
CREATE INDEX IF NOT EXISTS idx_evidence_bates ON evidence(bates_number);
CREATE INDEX IF NOT EXISTS idx_timeline_case_id ON timeline_events(case_id);
CREATE INDEX IF NOT EXISTS idx_timeline_date ON timeline_events(event_date);
CREATE INDEX IF NOT EXISTS idx_court_rules_jurisdiction ON court_rules(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_court_rules_number ON court_rules(rule_number);
