-- ============================================================================
-- LitigationOS Product Database Schema
-- SQLite - Normalized, Jurisdiction-Extensible
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Jurisdiction plugin system
CREATE TABLE jurisdictions (
    id TEXT PRIMARY KEY,              -- e.g., 'MI', 'OH', 'NY'
    name TEXT NOT NULL,
    state_code TEXT,
    rules_version TEXT,
    enabled INTEGER DEFAULT 1
);

-- Court directory
CREATE TABLE courts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction_id TEXT REFERENCES jurisdictions(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL,               -- 'circuit', 'district', 'probate', 'coa', 'supreme', 'federal_district', 'federal_circuit'
    county TEXT,
    address TEXT,
    phone TEXT,
    efiling_url TEXT,
    local_rules_url TEXT
);

-- Cases
CREATE TABLE cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_number TEXT,
    court_id INTEGER REFERENCES courts(id),
    case_type TEXT,                   -- 'family', 'civil', 'criminal', 'appellate', 'federal'
    title TEXT NOT NULL,              -- e.g., 'Pigors v. Watson'
    filed_date TEXT,
    status TEXT DEFAULT 'active',     -- 'active', 'closed', 'appealed', 'settled'
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Parties
CREATE TABLE parties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role TEXT NOT NULL,               -- 'plaintiff', 'defendant', 'respondent', 'petitioner', 'intervenor', 'judge', 'attorney'
    party_type TEXT,                  -- 'individual', 'corporation', 'government', 'organization'
    bar_number TEXT,
    email TEXT,
    phone TEXT,
    address TEXT
);

-- Claims/Counts
CREATE TABLE claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    count_number INTEGER,
    title TEXT NOT NULL,              -- e.g., 'Count I: Intentional Infliction of Emotional Distress'
    legal_basis TEXT,                 -- e.g., 'MCL 600.2911'
    against_party_id INTEGER REFERENCES parties(id),
    status TEXT DEFAULT 'active',
    damages_sought REAL,
    notes TEXT
);

-- Court Rules (per jurisdiction)
CREATE TABLE court_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction_id TEXT REFERENCES jurisdictions(id),
    rule_number TEXT NOT NULL,        -- e.g., 'MCR 2.113', 'FRCP 12(b)(6)'
    title TEXT,
    full_text TEXT,
    category TEXT,                    -- 'format', 'motion', 'discovery', 'evidence', 'appeal', 'service'
    effective_date TEXT,
    source_url TEXT
);

-- Filings
CREATE TABLE filings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    filing_type TEXT,                 -- 'complaint', 'motion', 'brief', 'response', 'reply', 'order', 'notice'
    status TEXT DEFAULT 'draft',      -- 'draft', 'review', 'ready', 'filed', 'served'
    file_path TEXT,
    filed_date TEXT,
    served_date TEXT,
    compliance_score REAL,
    word_count INTEGER,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Deadlines
CREATE TABLE deadlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    filing_id INTEGER REFERENCES filings(id),
    title TEXT NOT NULL,
    due_date TEXT NOT NULL,
    rule_basis TEXT,                  -- e.g., 'MCR 7.212(A)(1)(a) - 56 days from claim of appeal'
    status TEXT DEFAULT 'pending',    -- 'pending', 'extended', 'met', 'missed'
    priority TEXT DEFAULT 'normal',   -- 'critical', 'high', 'normal', 'low'
    reminder_days INTEGER DEFAULT 7,
    notes TEXT
);

-- Evidence
CREATE TABLE evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    bates_number TEXT UNIQUE,         -- e.g., 'PIGORS-0001'
    title TEXT NOT NULL,
    description TEXT,
    file_path TEXT,
    file_type TEXT,                   -- 'pdf', 'image', 'text', 'email', 'screenshot', 'document'
    source TEXT,                      -- where it came from
    date_created TEXT,                -- when evidence was created (not when imported)
    date_imported TEXT DEFAULT (datetime('now')),
    authentication_method TEXT,       -- 'self_auth_902', 'witness_901', 'certification', 'stipulation'
    foundation_witness TEXT,
    relevance_score REAL,
    tags TEXT,                        -- JSON array of tags
    notes TEXT
);

-- Templates (jurisdiction-aware)
CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction_id TEXT REFERENCES jurisdictions(id),
    name TEXT NOT NULL,
    template_type TEXT,               -- 'motion', 'brief', 'complaint', 'order', 'service', 'affidavit'
    content TEXT NOT NULL,            -- Jinja2 template
    variables TEXT,                   -- JSON schema of required variables
    court_rule TEXT,                  -- MCR/FRCP rule this template follows
    notes TEXT
);

-- Documents (generated from templates)
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id INTEGER REFERENCES filings(id),
    template_id INTEGER REFERENCES templates(id),
    title TEXT NOT NULL,
    content TEXT,                     -- markdown content
    output_path TEXT,                 -- generated DOCX/PDF path
    format TEXT DEFAULT 'md',         -- 'md', 'docx', 'pdf'
    variables TEXT,                   -- JSON of template variables used
    created_at TEXT DEFAULT (datetime('now'))
);

-- Timeline events
CREATE TABLE timeline_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    event_date TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    event_type TEXT,                  -- 'filing', 'hearing', 'order', 'communication', 'incident', 'deadline'
    evidence_ids TEXT,                -- JSON array of evidence IDs
    filing_id INTEGER REFERENCES filings(id),
    importance TEXT DEFAULT 'normal'  -- 'critical', 'high', 'normal', 'low'
);

-- User settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    category TEXT                     -- 'general', 'display', 'jurisdiction', 'ai', 'paths'
);

-- SCAO Forms (Michigan specific, loaded by jurisdiction plugin)
CREATE TABLE scao_forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jurisdiction_id TEXT REFERENCES jurisdictions(id),
    form_number TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    url TEXT,
    notes TEXT
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Courts
CREATE INDEX idx_courts_jurisdiction ON courts(jurisdiction_id);
CREATE INDEX idx_courts_type ON courts(type);
CREATE INDEX idx_courts_county ON courts(county);

-- Cases
CREATE INDEX idx_cases_court ON cases(court_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_case_number ON cases(case_number);
CREATE INDEX idx_cases_case_type ON cases(case_type);
CREATE INDEX idx_cases_filed_date ON cases(filed_date);

-- Parties
CREATE INDEX idx_parties_case ON parties(case_id);
CREATE INDEX idx_parties_role ON parties(role);
CREATE INDEX idx_parties_name ON parties(name);

-- Claims
CREATE INDEX idx_claims_case ON claims(case_id);
CREATE INDEX idx_claims_against_party ON claims(against_party_id);
CREATE INDEX idx_claims_status ON claims(status);

-- Court Rules
CREATE INDEX idx_court_rules_jurisdiction ON court_rules(jurisdiction_id);
CREATE INDEX idx_court_rules_category ON court_rules(category);
CREATE INDEX idx_court_rules_rule_number ON court_rules(rule_number);

-- Filings
CREATE INDEX idx_filings_case ON filings(case_id);
CREATE INDEX idx_filings_status ON filings(status);
CREATE INDEX idx_filings_type ON filings(filing_type);
CREATE INDEX idx_filings_filed_date ON filings(filed_date);

-- Deadlines
CREATE INDEX idx_deadlines_case ON deadlines(case_id);
CREATE INDEX idx_deadlines_filing ON deadlines(filing_id);
CREATE INDEX idx_deadlines_due_date ON deadlines(due_date);
CREATE INDEX idx_deadlines_status ON deadlines(status);
CREATE INDEX idx_deadlines_priority ON deadlines(priority);

-- Evidence
CREATE INDEX idx_evidence_case ON evidence(case_id);
CREATE INDEX idx_evidence_bates ON evidence(bates_number);
CREATE INDEX idx_evidence_file_type ON evidence(file_type);
CREATE INDEX idx_evidence_date_created ON evidence(date_created);

-- Documents
CREATE INDEX idx_documents_filing ON documents(filing_id);
CREATE INDEX idx_documents_template ON documents(template_id);

-- Templates
CREATE INDEX idx_templates_jurisdiction ON templates(jurisdiction_id);
CREATE INDEX idx_templates_type ON templates(template_type);

-- Timeline
CREATE INDEX idx_timeline_case ON timeline_events(case_id);
CREATE INDEX idx_timeline_date ON timeline_events(event_date);
CREATE INDEX idx_timeline_type ON timeline_events(event_type);
CREATE INDEX idx_timeline_filing ON timeline_events(filing_id);

-- Settings
CREATE INDEX idx_settings_category ON settings(category);

-- SCAO Forms
CREATE INDEX idx_scao_forms_jurisdiction ON scao_forms(jurisdiction_id);
CREATE INDEX idx_scao_forms_number ON scao_forms(form_number);
CREATE INDEX idx_scao_forms_category ON scao_forms(category);

-- ============================================================================
-- FULL-TEXT SEARCH (FTS5)
-- ============================================================================

-- Evidence full-text search
CREATE VIRTUAL TABLE evidence_fts USING fts5(
    title,
    description,
    source,
    tags,
    notes,
    content='evidence',
    content_rowid='id'
);

-- Triggers to keep evidence FTS in sync
CREATE TRIGGER evidence_ai AFTER INSERT ON evidence BEGIN
    INSERT INTO evidence_fts(rowid, title, description, source, tags, notes)
    VALUES (new.id, new.title, new.description, new.source, new.tags, new.notes);
END;

CREATE TRIGGER evidence_ad AFTER DELETE ON evidence BEGIN
    INSERT INTO evidence_fts(evidence_fts, rowid, title, description, source, tags, notes)
    VALUES ('delete', old.id, old.title, old.description, old.source, old.tags, old.notes);
END;

CREATE TRIGGER evidence_au AFTER UPDATE ON evidence BEGIN
    INSERT INTO evidence_fts(evidence_fts, rowid, title, description, source, tags, notes)
    VALUES ('delete', old.id, old.title, old.description, old.source, old.tags, old.notes);
    INSERT INTO evidence_fts(rowid, title, description, source, tags, notes)
    VALUES (new.id, new.title, new.description, new.source, new.tags, new.notes);
END;

-- Court rules full-text search
CREATE VIRTUAL TABLE court_rules_fts USING fts5(
    rule_number,
    title,
    full_text,
    category,
    content='court_rules',
    content_rowid='id'
);

-- Triggers to keep court_rules FTS in sync
CREATE TRIGGER court_rules_ai AFTER INSERT ON court_rules BEGIN
    INSERT INTO court_rules_fts(rowid, rule_number, title, full_text, category)
    VALUES (new.id, new.rule_number, new.title, new.full_text, new.category);
END;

CREATE TRIGGER court_rules_ad AFTER DELETE ON court_rules BEGIN
    INSERT INTO court_rules_fts(court_rules_fts, rowid, rule_number, title, full_text, category)
    VALUES ('delete', old.id, old.rule_number, old.title, old.full_text, old.category);
END;

CREATE TRIGGER court_rules_au AFTER UPDATE ON court_rules BEGIN
    INSERT INTO court_rules_fts(court_rules_fts, rowid, rule_number, title, full_text, category)
    VALUES ('delete', old.id, old.rule_number, old.title, old.full_text, old.category);
    INSERT INTO court_rules_fts(rowid, rule_number, title, full_text, category)
    VALUES (new.id, new.rule_number, new.title, new.full_text, new.category);
END;

-- ============================================================================
-- SEED: Default Michigan jurisdiction
-- ============================================================================

INSERT INTO jurisdictions (id, name, state_code, rules_version, enabled)
VALUES ('MI', 'Michigan', 'MI', '2024', 1);

INSERT INTO settings (key, value, category) VALUES
    ('default_jurisdiction', 'MI', 'jurisdiction'),
    ('theme', 'dark', 'display'),
    ('bates_prefix', 'EXHIBIT', 'general'),
    ('auto_save', '1', 'general'),
    ('ai_enabled', '0', 'ai'),
    ('ollama_model', 'llama3.2', 'ai'),
    ('ollama_url', 'http://localhost:11434', 'ai');
