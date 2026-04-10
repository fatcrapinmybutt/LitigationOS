-- ============================================================================
-- Michigan Court Filing Framework — Reusable Case Database Schema
-- ============================================================================
-- Case-agnostic SQLite schema for any litigation case.
-- Usage:  sqlite3 my_case.db < filing_db_schema.sql
-- Pragmas are applied by init_case_db.py at connection time.
-- ============================================================================

-- ── Case Information ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS case_info (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_number     TEXT    NOT NULL,
    court           TEXT    NOT NULL,
    judge           TEXT,
    judge_bar       TEXT,
    division        TEXT,                          -- family, civil, criminal
    lane            TEXT,                          -- user-defined lane label
    status          TEXT    DEFAULT 'active',      -- active, closed, dismissed, appealed
    filed_date      TEXT,
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now'))
);

-- ── Parties ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parties (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER REFERENCES case_info(id),
    name            TEXT    NOT NULL,
    role            TEXT    NOT NULL,               -- plaintiff, defendant, judge,
                                                    -- attorney, witness, intervenor,
                                                    -- guardian_ad_litem, foc, agency
    side            TEXT,                           -- plaintiff_side, defendant_side, neutral
    address         TEXT,
    city            TEXT,
    state           TEXT    DEFAULT 'MI',
    zip             TEXT,
    phone           TEXT,
    email           TEXT,
    bar_number      TEXT,
    firm            TEXT,
    represented_by  INTEGER REFERENCES parties(id), -- attorney representing this party
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ── Evidence Items ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER REFERENCES case_info(id),
    file_path       TEXT,
    filename        TEXT,
    description     TEXT,
    category        TEXT,                           -- document, photo, video, audio,
                                                    -- financial, communication, record
    subcategory     TEXT,                           -- email, text_message, court_order, etc.
    source          TEXT,                           -- party/agency that produced it
    date_collected  TEXT,
    date_of_content TEXT,                           -- date the evidence pertains to
    ocr_text        TEXT,
    content_hash    TEXT    UNIQUE,                 -- SHA-256 for dedup
    page_count      INTEGER,
    bates_start     TEXT,
    bates_end       TEXT,
    exhibit_label   TEXT,                           -- "Exhibit A", etc.
    admitted        INTEGER DEFAULT 0,              -- 0=not offered, 1=admitted, -1=excluded
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ── Timeline Events ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS timeline_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER REFERENCES case_info(id),
    event_date      TEXT    NOT NULL,
    event_time      TEXT,
    event           TEXT    NOT NULL,
    actors          TEXT,                           -- comma-separated names
    category        TEXT,                           -- filing, hearing, order, incident,
                                                    -- communication, police, medical
    source          TEXT,                           -- document/evidence proving this
    evidence_id     INTEGER REFERENCES evidence_items(id),
    lane            TEXT,
    significance    TEXT,                           -- routine, important, critical
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ── Fraud / Misconduct Indicators ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fraud_indicators (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER REFERENCES case_info(id),
    indicator_type  TEXT    NOT NULL,               -- fraud, perjury, forgery,
                                                    -- concealment, misrepresentation,
                                                    -- judicial_misconduct, ethical_violation
    description     TEXT    NOT NULL,
    severity        TEXT    DEFAULT 'medium',       -- low, medium, high, critical
    actor           TEXT,                           -- person responsible
    evidence_ref    TEXT,                           -- evidence_items.id or description
    evidence_id     INTEGER REFERENCES evidence_items(id),
    source          TEXT,
    date_discovered TEXT,
    status          TEXT    DEFAULT 'open',         -- open, verified, disputed, resolved
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ── Dollar Amounts ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dollar_amounts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER REFERENCES case_info(id),
    amount          REAL    NOT NULL,
    description     TEXT    NOT NULL,
    date            TEXT,
    source          TEXT,
    category        TEXT,                           -- rent, utility, repair, damage,
                                                    -- fee, penalty, loss, income
    evidence_id     INTEGER REFERENCES evidence_items(id),
    verified        INTEGER DEFAULT 0,
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ── Entity Registry ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS entity_registry (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id             INTEGER REFERENCES case_info(id),
    name                TEXT    NOT NULL,
    entity_type         TEXT    NOT NULL,           -- LLC, corporation, individual,
                                                    -- agency, trust, partnership
    parent_entity_id    INTEGER REFERENCES entity_registry(id),
    state               TEXT,
    registration_number TEXT,
    registered_agent    TEXT,
    address             TEXT,
    status              TEXT,                       -- active, dissolved, revoked, unknown
    notes               TEXT,
    created_at          TEXT    DEFAULT (datetime('now'))
);

-- ── Filing Vehicles ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS filing_vehicles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER REFERENCES case_info(id),
    name            TEXT    NOT NULL,               -- "Motion to Compel Discovery"
    vehicle_type    TEXT,                           -- motion, complaint, brief, petition,
                                                    -- application, response, reply, notice
    court           TEXT    NOT NULL,
    authority       TEXT,                           -- "MCR 2.313" etc.
    fee             REAL    DEFAULT 0.0,
    deadline_rule   TEXT,                           -- reference to deadline constants
    deadline_date   TEXT,
    status          TEXT    DEFAULT 'planned',      -- planned, drafting, qa, filed, served
    priority        INTEGER DEFAULT 5,             -- 1=highest, 10=lowest
    lane            TEXT,
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now'))
);

-- ── Filing Requirements ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS filing_requirements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id      INTEGER NOT NULL REFERENCES filing_vehicles(id),
    section         TEXT,                           -- "caption", "body", "exhibits", etc.
    requirement     TEXT    NOT NULL,
    authority       TEXT,                           -- MCR/MCL citation
    mandatory       INTEGER DEFAULT 1,             -- 1=required, 0=recommended
    satisfied       INTEGER DEFAULT 0,
    notes           TEXT
);

-- ── Court Format Specifications ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS format_specs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    court           TEXT    NOT NULL,               -- "circuit", "coa", "msc", "wdmi", "district"
    spec_name       TEXT    NOT NULL,
    spec_value      TEXT    NOT NULL,
    authority       TEXT,                           -- MCR/LCivR citation
    UNIQUE(court, spec_name)
);

-- ── Court Forms ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS court_forms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    form_number     TEXT    NOT NULL,               -- "MC 01", "SCAO TF-5"
    form_name       TEXT    NOT NULL,
    vehicle_id      INTEGER REFERENCES filing_vehicles(id),
    court           TEXT,
    mandatory       INTEGER DEFAULT 1,
    url             TEXT,
    notes           TEXT
);

-- ── Service Log ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS service_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id      INTEGER REFERENCES filing_vehicles(id),
    party_served    TEXT    NOT NULL,
    address         TEXT,
    method          TEXT    NOT NULL,               -- electronic, personal, mail, ECF
    date_served     TEXT    NOT NULL,
    proof_filed     INTEGER DEFAULT 0,
    confirmation    TEXT,                           -- tracking number, receipt, etc.
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ── Deadlines ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS deadlines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id      INTEGER REFERENCES filing_vehicles(id),
    case_id         INTEGER REFERENCES case_info(id),
    deadline_date   TEXT    NOT NULL,
    trigger_event   TEXT,                           -- "motion_served", "order_entered", etc.
    trigger_date    TEXT,
    rule            TEXT,                           -- "MCR 2.119(C)(1)" etc.
    days            INTEGER,                        -- number of days from trigger
    status          TEXT    DEFAULT 'pending',      -- pending, met, missed, extended
    urgency         TEXT    DEFAULT 'normal',       -- normal, urgent, critical, expired
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ── Filing Packages (Assembly Pipeline) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS filing_packages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id      INTEGER NOT NULL REFERENCES filing_vehicles(id),
    phase           TEXT    NOT NULL,               -- EVIDENCE, AUTHORITY, DRAFT,
                                                    -- QA, ASSEMBLE, SUBMIT, CONFIRM
    readiness_score INTEGER DEFAULT 0,             -- 0-100
    assigned_to     TEXT,
    started_at      TEXT,
    completed_at    TEXT,
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now'))
);

-- ── Claims ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS claims (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         INTEGER REFERENCES case_info(id),
    claim_type      TEXT    NOT NULL,               -- negligence, fraud, breach_of_contract,
                                                    -- constitutional, statutory, equitable
    description     TEXT    NOT NULL,
    authority       TEXT,                           -- MCL/USC citation
    elements        TEXT,                           -- JSON array of required legal elements
    lane            TEXT,
    status          TEXT    DEFAULT 'developing',   -- developing, ready, filed, adjudicated
    damages_low     REAL,
    damages_high    REAL,
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT    DEFAULT (datetime('now'))
);

-- ── FTS5 Full-Text Search Indexes ───────────────────────────────────────────

CREATE VIRTUAL TABLE IF NOT EXISTS evidence_fts USING fts5(
    description,
    ocr_text,
    filename,
    notes,
    content=evidence_items,
    content_rowid=id,
    tokenize='porter unicode61'
);

-- Triggers to keep evidence FTS in sync
CREATE TRIGGER IF NOT EXISTS evidence_ai AFTER INSERT ON evidence_items BEGIN
    INSERT INTO evidence_fts(rowid, description, ocr_text, filename, notes)
    VALUES (new.id, new.description, new.ocr_text, new.filename, new.notes);
END;

CREATE TRIGGER IF NOT EXISTS evidence_ad AFTER DELETE ON evidence_items BEGIN
    INSERT INTO evidence_fts(evidence_fts, rowid, description, ocr_text, filename, notes)
    VALUES ('delete', old.id, old.description, old.ocr_text, old.filename, old.notes);
END;

CREATE TRIGGER IF NOT EXISTS evidence_au AFTER UPDATE ON evidence_items BEGIN
    INSERT INTO evidence_fts(evidence_fts, rowid, description, ocr_text, filename, notes)
    VALUES ('delete', old.id, old.description, old.ocr_text, old.filename, old.notes);
    INSERT INTO evidence_fts(rowid, description, ocr_text, filename, notes)
    VALUES (new.id, new.description, new.ocr_text, new.filename, new.notes);
END;

CREATE VIRTUAL TABLE IF NOT EXISTS timeline_fts USING fts5(
    event,
    actors,
    source,
    notes,
    content=timeline_events,
    content_rowid=id,
    tokenize='porter unicode61'
);

-- Triggers to keep timeline FTS in sync
CREATE TRIGGER IF NOT EXISTS timeline_ai AFTER INSERT ON timeline_events BEGIN
    INSERT INTO timeline_fts(rowid, event, actors, source, notes)
    VALUES (new.id, new.event, new.actors, new.source, new.notes);
END;

CREATE TRIGGER IF NOT EXISTS timeline_ad AFTER DELETE ON timeline_events BEGIN
    INSERT INTO timeline_fts(timeline_fts, rowid, event, actors, source, notes)
    VALUES ('delete', old.id, old.event, old.actors, old.source, old.notes);
END;

CREATE TRIGGER IF NOT EXISTS timeline_au AFTER UPDATE ON timeline_events BEGIN
    INSERT INTO timeline_fts(timeline_fts, rowid, event, actors, source, notes)
    VALUES ('delete', old.id, old.event, old.actors, old.source, old.notes);
    INSERT INTO timeline_fts(rowid, event, actors, source, notes)
    VALUES (new.id, new.event, new.actors, new.source, new.notes);
END;

-- ── Performance Indexes ─────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_evidence_case      ON evidence_items(case_id);
CREATE INDEX IF NOT EXISTS idx_evidence_category   ON evidence_items(category);
CREATE INDEX IF NOT EXISTS idx_evidence_hash       ON evidence_items(content_hash);
CREATE INDEX IF NOT EXISTS idx_timeline_date       ON timeline_events(event_date);
CREATE INDEX IF NOT EXISTS idx_timeline_case       ON timeline_events(case_id);
CREATE INDEX IF NOT EXISTS idx_timeline_category   ON timeline_events(category);
CREATE INDEX IF NOT EXISTS idx_fraud_case          ON fraud_indicators(case_id);
CREATE INDEX IF NOT EXISTS idx_fraud_severity      ON fraud_indicators(severity);
CREATE INDEX IF NOT EXISTS idx_amounts_case        ON dollar_amounts(case_id);
CREATE INDEX IF NOT EXISTS idx_amounts_category    ON dollar_amounts(category);
CREATE INDEX IF NOT EXISTS idx_vehicles_case       ON filing_vehicles(case_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_status     ON filing_vehicles(status);
CREATE INDEX IF NOT EXISTS idx_deadlines_date      ON deadlines(deadline_date);
CREATE INDEX IF NOT EXISTS idx_deadlines_status    ON deadlines(status);
CREATE INDEX IF NOT EXISTS idx_packages_vehicle    ON filing_packages(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_packages_phase      ON filing_packages(phase);
CREATE INDEX IF NOT EXISTS idx_claims_case         ON claims(case_id);
CREATE INDEX IF NOT EXISTS idx_claims_lane         ON claims(lane);
CREATE INDEX IF NOT EXISTS idx_parties_case        ON parties(case_id);
CREATE INDEX IF NOT EXISTS idx_parties_role        ON parties(role);
CREATE INDEX IF NOT EXISTS idx_service_vehicle     ON service_log(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_entities_case       ON entity_registry(case_id);
CREATE INDEX IF NOT EXISTS idx_entities_type       ON entity_registry(entity_type);
CREATE INDEX IF NOT EXISTS idx_forms_vehicle       ON court_forms(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_requirements_vehicle ON filing_requirements(vehicle_id);
