"""
Multi-Brain Universe — Database Schema Creator
Creates 5 core brain databases + cross-brain index for LitigationOS
"""
import sqlite3
import os
import sys

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

BRAIN_DIR = os.path.dirname(os.path.abspath(__file__))

PRAGMAS = """
PRAGMA busy_timeout = 120000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
"""

def create_brain(name, schema_sql):
    db_path = os.path.join(BRAIN_DIR, f"{name}.db")
    print(f"Creating {name} at {db_path}...")
    conn = sqlite3.connect(db_path)
    conn.executescript(PRAGMAS)
    conn.executescript(schema_sql)
    conn.commit()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    print(f"  Created {len(tables)} tables: {', '.join(t[0] for t in tables)}")
    conn.close()
    print(f"  \u2705 {name} created successfully")


# ═══════════════════════════════════════════════════════════
# BRAIN 1: AUTHORITY BRAIN — Pure canonical law (READ-ONLY after ingestion)
# ═══════════════════════════════════════════════════════════
AUTHORITY_SCHEMA = """
-- Court Rules (MCR)
CREATE TABLE IF NOT EXISTS court_rules (
    rule_id TEXT PRIMARY KEY,
    rule_number TEXT NOT NULL,
    rule_title TEXT,
    rule_text TEXT NOT NULL,
    chapter TEXT,
    subchapter TEXT,
    effective_date TEXT,
    amended_date TEXT,
    source_url TEXT,
    source_type TEXT DEFAULT 'government',
    trust_level TEXT DEFAULT 'canonical',
    sha256 TEXT,
    extraction_timestamp TEXT DEFAULT (datetime('now')),
    UNIQUE(rule_number)
);
CREATE VIRTUAL TABLE IF NOT EXISTS court_rules_fts USING fts5(
    rule_number, rule_title, rule_text, content=court_rules, content_rowid=rowid
);

-- Statutes (MCL)
CREATE TABLE IF NOT EXISTS statutes (
    statute_id TEXT PRIMARY KEY,
    statute_number TEXT NOT NULL,
    statute_title TEXT,
    statute_text TEXT NOT NULL,
    chapter TEXT,
    act_name TEXT,
    effective_date TEXT,
    amended_date TEXT,
    source_url TEXT,
    source_type TEXT DEFAULT 'government',
    trust_level TEXT DEFAULT 'canonical',
    sha256 TEXT,
    extraction_timestamp TEXT DEFAULT (datetime('now')),
    UNIQUE(statute_number)
);
CREATE VIRTUAL TABLE IF NOT EXISTS statutes_fts USING fts5(
    statute_number, statute_title, statute_text, content=statutes, content_rowid=rowid
);

-- Case Law
CREATE TABLE IF NOT EXISTS case_law (
    case_id TEXT PRIMARY KEY,
    case_name TEXT NOT NULL,
    citation TEXT NOT NULL,
    court TEXT,
    jurisdiction TEXT,
    date_decided TEXT,
    judge TEXT,
    holding TEXT,
    full_text TEXT,
    headnotes TEXT,
    key_quotes TEXT,
    topics TEXT,
    cited_by_count INTEGER DEFAULT 0,
    overruled INTEGER DEFAULT 0,
    distinguished INTEGER DEFAULT 0,
    source_url TEXT,
    source_type TEXT,
    trust_level TEXT DEFAULT 'canonical',
    sha256 TEXT,
    extraction_timestamp TEXT DEFAULT (datetime('now')),
    UNIQUE(citation)
);
CREATE VIRTUAL TABLE IF NOT EXISTS case_law_fts USING fts5(
    case_name, citation, holding, full_text, headnotes, key_quotes, content=case_law, content_rowid=rowid
);

-- Constitutional Provisions
CREATE TABLE IF NOT EXISTS constitutional_provisions (
    provision_id TEXT PRIMARY KEY,
    constitution TEXT NOT NULL,
    article TEXT,
    section TEXT,
    amendment TEXT,
    clause TEXT,
    provision_text TEXT NOT NULL,
    interpretation_notes TEXT,
    source_url TEXT,
    trust_level TEXT DEFAULT 'canonical',
    sha256 TEXT,
    extraction_timestamp TEXT DEFAULT (datetime('now'))
);

-- Rules of Evidence (MRE / FRE)
CREATE TABLE IF NOT EXISTS evidence_rules (
    rule_id TEXT PRIMARY KEY,
    rule_number TEXT NOT NULL,
    rule_title TEXT,
    rule_text TEXT NOT NULL,
    rule_set TEXT NOT NULL,
    effective_date TEXT,
    source_url TEXT,
    trust_level TEXT DEFAULT 'canonical',
    sha256 TEXT,
    extraction_timestamp TEXT DEFAULT (datetime('now')),
    UNIQUE(rule_number, rule_set)
);
CREATE VIRTUAL TABLE IF NOT EXISTS evidence_rules_fts USING fts5(
    rule_number, rule_title, rule_text, content=evidence_rules, content_rowid=rowid
);

-- SCAO Forms & Procedures
CREATE TABLE IF NOT EXISTS scao_forms (
    form_id TEXT PRIMARY KEY,
    form_number TEXT NOT NULL,
    form_title TEXT,
    form_type TEXT,
    court_type TEXT,
    case_type TEXT,
    required_for TEXT,
    filing_fee TEXT,
    instructions TEXT,
    download_url TEXT,
    source_type TEXT DEFAULT 'government',
    trust_level TEXT DEFAULT 'canonical',
    sha256 TEXT,
    extraction_timestamp TEXT DEFAULT (datetime('now')),
    UNIQUE(form_number)
);

-- Benchbook Entries
CREATE TABLE IF NOT EXISTS benchbook_entries (
    entry_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    benchbook_name TEXT,
    section TEXT,
    entry_text TEXT NOT NULL,
    applicable_rules TEXT,
    applicable_statutes TEXT,
    source_url TEXT,
    trust_level TEXT DEFAULT 'canonical',
    sha256 TEXT,
    extraction_timestamp TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS benchbook_fts USING fts5(
    topic, entry_text, applicable_rules, content=benchbook_entries, content_rowid=rowid
);

-- Authority Citations Network
CREATE TABLE IF NOT EXISTS authority_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_id TEXT NOT NULL,
    cited_id TEXT NOT NULL,
    citing_type TEXT NOT NULL,
    cited_type TEXT NOT NULL,
    citation_context TEXT,
    relationship TEXT DEFAULT 'cites',
    extraction_timestamp TEXT DEFAULT (datetime('now')),
    UNIQUE(citing_id, cited_id)
);
CREATE INDEX IF NOT EXISTS idx_auth_citing ON authority_citations(citing_id);
CREATE INDEX IF NOT EXISTS idx_auth_cited ON authority_citations(cited_id);

-- Provenance tracking for this brain
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_table TEXT NOT NULL,
    record_id TEXT NOT NULL,
    source_file TEXT,
    source_page INTEGER,
    source_line INTEGER,
    source_url TEXT,
    source_type TEXT,
    extraction_method TEXT,
    extraction_confidence REAL DEFAULT 1.0,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now')),
    UNIQUE(record_table, record_id, source_file)
);
CREATE INDEX IF NOT EXISTS idx_prov_record ON provenance(record_table, record_id);

-- Brain metadata
CREATE TABLE IF NOT EXISTS brain_meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
INSERT OR REPLACE INTO brain_meta (key, value) VALUES
    ('brain_name', 'authority'),
    ('brain_version', '1.0'),
    ('trust_level', 'canonical'),
    ('update_policy', 'read_only_after_ingestion'),
    ('created_at', datetime('now'));
"""

# ═══════════════════════════════════════════════════════════
# BRAIN 2: NARRATIVE BRAIN — Chronological evidence (APPEND-ONLY)
# ═══════════════════════════════════════════════════════════
NARRATIVE_SCHEMA = """
-- Master Timeline Events
CREATE TABLE IF NOT EXISTS timeline_events (
    event_id TEXT PRIMARY KEY,
    event_date TEXT,
    event_date_precision TEXT DEFAULT 'day',
    event_type TEXT NOT NULL,
    event_description TEXT NOT NULL,
    actors TEXT,
    location TEXT,
    case_lane TEXT,
    case_number TEXT,
    significance TEXT,
    source_file TEXT,
    source_page INTEGER,
    source_type TEXT,
    extraction_confidence REAL DEFAULT 1.0,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS timeline_fts USING fts5(
    event_date, event_type, event_description, actors, location, content=timeline_events, content_rowid=rowid
);
CREATE INDEX IF NOT EXISTS idx_timeline_date ON timeline_events(event_date);
CREATE INDEX IF NOT EXISTS idx_timeline_lane ON timeline_events(case_lane);

-- Document Extractions (verbatim text from source documents)
CREATE TABLE IF NOT EXISTS document_extractions (
    extraction_id TEXT PRIMARY KEY,
    source_file TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_page INTEGER,
    source_line_start INTEGER,
    source_line_end INTEGER,
    extracted_text TEXT NOT NULL,
    document_type TEXT,
    document_date TEXT,
    case_lane TEXT,
    case_number TEXT,
    extraction_method TEXT,
    extraction_confidence REAL DEFAULT 1.0,
    word_count INTEGER,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS extractions_fts USING fts5(
    source_file, extracted_text, document_type, content=document_extractions, content_rowid=rowid
);
CREATE INDEX IF NOT EXISTS idx_extract_file ON document_extractions(source_file);
CREATE INDEX IF NOT EXISTS idx_extract_lane ON document_extractions(case_lane);
CREATE INDEX IF NOT EXISTS idx_extract_type ON document_extractions(document_type);

-- Court Orders (verbatim text of orders received)
CREATE TABLE IF NOT EXISTS court_orders (
    order_id TEXT PRIMARY KEY,
    order_date TEXT,
    court TEXT,
    judge TEXT,
    case_number TEXT,
    case_lane TEXT,
    order_type TEXT,
    order_text TEXT NOT NULL,
    key_rulings TEXT,
    relief_granted TEXT,
    relief_denied TEXT,
    source_file TEXT,
    source_page INTEGER,
    extraction_confidence REAL DEFAULT 1.0,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS orders_fts USING fts5(
    order_type, order_text, key_rulings, content=court_orders, content_rowid=rowid
);

-- Police Reports
CREATE TABLE IF NOT EXISTS police_reports (
    report_id TEXT PRIMARY KEY,
    report_number TEXT,
    report_date TEXT,
    department TEXT DEFAULT 'NSPD',
    officer TEXT,
    incident_type TEXT,
    report_text TEXT NOT NULL,
    subjects TEXT,
    location TEXT,
    case_lane TEXT,
    source_file TEXT,
    source_page INTEGER,
    extraction_confidence REAL DEFAULT 1.0,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS police_fts USING fts5(
    report_number, incident_type, report_text, subjects, content=police_reports, content_rowid=rowid
);

-- Testimony & Transcript Extracts
CREATE TABLE IF NOT EXISTS testimony (
    testimony_id TEXT PRIMARY KEY,
    hearing_date TEXT,
    court TEXT,
    case_number TEXT,
    case_lane TEXT,
    witness TEXT,
    examiner TEXT,
    testimony_text TEXT NOT NULL,
    testimony_type TEXT,
    page_number INTEGER,
    line_numbers TEXT,
    key_admissions TEXT,
    source_file TEXT,
    extraction_confidence REAL DEFAULT 1.0,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS testimony_fts USING fts5(
    witness, testimony_text, key_admissions, content=testimony, content_rowid=rowid
);

-- Communications (emails, messages, ChatGPT context)
CREATE TABLE IF NOT EXISTS communications (
    comm_id TEXT PRIMARY KEY,
    comm_date TEXT,
    comm_type TEXT NOT NULL,
    sender TEXT,
    recipient TEXT,
    subject TEXT,
    body TEXT NOT NULL,
    case_lane TEXT,
    relevance_score REAL,
    source_file TEXT,
    source_type TEXT,
    extraction_confidence REAL DEFAULT 1.0,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS communications_fts USING fts5(
    comm_type, sender, recipient, subject, body, content=communications, content_rowid=rowid
);

-- Photo/Image Evidence Metadata
CREATE TABLE IF NOT EXISTS image_evidence (
    image_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    image_date TEXT,
    image_type TEXT,
    description TEXT,
    ocr_text TEXT,
    case_lane TEXT,
    relevance TEXT,
    bates_number TEXT,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now'))
);

-- Provenance tracking
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_table TEXT NOT NULL,
    record_id TEXT NOT NULL,
    source_file TEXT,
    source_page INTEGER,
    source_line INTEGER,
    source_url TEXT,
    source_type TEXT,
    extraction_method TEXT,
    extraction_confidence REAL DEFAULT 1.0,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now')),
    UNIQUE(record_table, record_id, source_file)
);
CREATE INDEX IF NOT EXISTS idx_prov_record ON provenance(record_table, record_id);

-- Brain metadata
CREATE TABLE IF NOT EXISTS brain_meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
INSERT OR REPLACE INTO brain_meta (key, value) VALUES
    ('brain_name', 'narrative'),
    ('brain_version', '1.0'),
    ('trust_level', 'evidential'),
    ('update_policy', 'append_only'),
    ('created_at', datetime('now'));
"""

# ═══════════════════════════════════════════════════════════
# BRAIN 3: ENTITY BRAIN — Parties, relationships (VERSIONED)
# ═══════════════════════════════════════════════════════════
ENTITY_SCHEMA = """
-- Parties (all persons/entities in the litigation)
CREATE TABLE IF NOT EXISTS parties (
    party_id TEXT PRIMARY KEY,
    legal_name TEXT NOT NULL,
    display_name TEXT,
    party_type TEXT NOT NULL,
    role TEXT,
    case_lanes TEXT,
    case_numbers TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    phone TEXT,
    email TEXT,
    bar_number TEXT,
    employer TEXT,
    notes TEXT,
    is_defendant INTEGER DEFAULT 0,
    is_plaintiff INTEGER DEFAULT 0,
    is_witness INTEGER DEFAULT 0,
    is_judge INTEGER DEFAULT 0,
    damages_range_low REAL,
    damages_range_high REAL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Corporate Structures (for veil piercing)
CREATE TABLE IF NOT EXISTS corporate_structures (
    structure_id TEXT PRIMARY KEY,
    parent_entity TEXT NOT NULL,
    child_entity TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    jurisdiction TEXT,
    formation_date TEXT,
    dissolution_date TEXT,
    registered_agent TEXT,
    notes TEXT,
    source_file TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (parent_entity) REFERENCES parties(party_id),
    FOREIGN KEY (child_entity) REFERENCES parties(party_id)
);
CREATE INDEX IF NOT EXISTS idx_corp_parent ON corporate_structures(parent_entity);
CREATE INDEX IF NOT EXISTS idx_corp_child ON corporate_structures(child_entity);

-- Party Relationships (non-corporate)
CREATE TABLE IF NOT EXISTS relationships (
    rel_id TEXT PRIMARY KEY,
    party_a TEXT NOT NULL,
    party_b TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    description TEXT,
    start_date TEXT,
    end_date TEXT,
    case_lanes TEXT,
    source_file TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (party_a) REFERENCES parties(party_id),
    FOREIGN KEY (party_b) REFERENCES parties(party_id)
);
CREATE INDEX IF NOT EXISTS idx_rel_a ON relationships(party_a);
CREATE INDEX IF NOT EXISTS idx_rel_b ON relationships(party_b);

-- Judge Profiles
CREATE TABLE IF NOT EXISTS judge_profiles (
    judge_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    court TEXT,
    division TEXT,
    appointed_date TEXT,
    rulings_count INTEGER DEFAULT 0,
    reversal_rate REAL,
    ex_parte_rate REAL,
    bias_score REAL,
    ruling_patterns TEXT,
    known_tendencies TEXT,
    disciplinary_history TEXT,
    source_files TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (judge_id) REFERENCES parties(party_id)
);

-- Witness Profiles
CREATE TABLE IF NOT EXISTS witness_profiles (
    witness_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    relationship_to_case TEXT,
    expected_testimony TEXT,
    credibility_score REAL,
    credibility_factors TEXT,
    prior_inconsistencies TEXT,
    impeachment_material TEXT,
    case_lanes TEXT,
    source_files TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (witness_id) REFERENCES parties(party_id)
);

-- Provenance
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_table TEXT NOT NULL,
    record_id TEXT NOT NULL,
    source_file TEXT,
    source_page INTEGER,
    source_url TEXT,
    source_type TEXT,
    extraction_method TEXT,
    extraction_confidence REAL DEFAULT 1.0,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now')),
    UNIQUE(record_table, record_id, source_file)
);
CREATE INDEX IF NOT EXISTS idx_prov_record ON provenance(record_table, record_id);

-- Brain metadata
CREATE TABLE IF NOT EXISTS brain_meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
INSERT OR REPLACE INTO brain_meta (key, value) VALUES
    ('brain_name', 'entity'),
    ('brain_version', '1.0'),
    ('trust_level', 'versioned'),
    ('update_policy', 'versioned_updates'),
    ('created_at', datetime('now'));
"""

# ═══════════════════════════════════════════════════════════
# BRAIN 4: CLAIMS BRAIN — Causes of action, elements (VERSIONED)
# ═══════════════════════════════════════════════════════════
CLAIMS_SCHEMA = """
-- Causes of Action
CREATE TABLE IF NOT EXISTS causes_of_action (
    claim_id TEXT PRIMARY KEY,
    claim_name TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    case_lane TEXT NOT NULL,
    case_number TEXT,
    defendants TEXT,
    statute TEXT,
    elements TEXT NOT NULL,
    elements_met TEXT,
    evidence_strength TEXT,
    damages_low REAL,
    damages_high REAL,
    treble_eligible INTEGER DEFAULT 0,
    sol_expiry TEXT,
    sol_status TEXT DEFAULT 'green',
    filing_readiness INTEGER DEFAULT 0,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_claims_lane ON causes_of_action(case_lane);

-- Claim Elements (each element of each cause of action)
CREATE TABLE IF NOT EXISTS claim_elements (
    element_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    element_number INTEGER NOT NULL,
    element_description TEXT NOT NULL,
    element_met INTEGER DEFAULT 0,
    evidence_ids TEXT,
    evidence_strength TEXT DEFAULT 'unknown',
    authority TEXT,
    notes TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (claim_id) REFERENCES causes_of_action(claim_id)
);
CREATE INDEX IF NOT EXISTS idx_elem_claim ON claim_elements(claim_id);

-- Evidence-to-Claim Mapping
CREATE TABLE IF NOT EXISTS evidence_claim_map (
    map_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL,
    element_id TEXT,
    evidence_type TEXT NOT NULL,
    evidence_description TEXT NOT NULL,
    evidence_source TEXT,
    evidence_date TEXT,
    evidence_strength TEXT DEFAULT 'moderate',
    bates_number TEXT,
    case_lane TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (claim_id) REFERENCES causes_of_action(claim_id)
);
CREATE INDEX IF NOT EXISTS idx_ecm_claim ON evidence_claim_map(claim_id);
CREATE INDEX IF NOT EXISTS idx_ecm_lane ON evidence_claim_map(case_lane);

-- Damages Calculations
CREATE TABLE IF NOT EXISTS damages (
    damage_id TEXT PRIMARY KEY,
    claim_id TEXT,
    case_lane TEXT NOT NULL,
    damage_type TEXT NOT NULL,
    damage_category TEXT NOT NULL,
    amount_low REAL,
    amount_high REAL,
    treble_multiplier REAL DEFAULT 1.0,
    calculation_basis TEXT,
    evidence_sources TEXT,
    statute_authority TEXT,
    notes TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (claim_id) REFERENCES causes_of_action(claim_id)
);

-- Discovery Tracking
CREATE TABLE IF NOT EXISTS discovery_items (
    discovery_id TEXT PRIMARY KEY,
    item_type TEXT NOT NULL,
    description TEXT NOT NULL,
    target_party TEXT,
    case_lane TEXT,
    case_number TEXT,
    status TEXT DEFAULT 'needed',
    date_requested TEXT,
    date_due TEXT,
    date_received TEXT,
    response_status TEXT,
    linked_claims TEXT,
    notes TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_disc_lane ON discovery_items(case_lane);
CREATE INDEX IF NOT EXISTS idx_disc_status ON discovery_items(status);

-- SOL Tracking
CREATE TABLE IF NOT EXISTS sol_tracker (
    sol_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    case_lane TEXT,
    statute TEXT,
    sol_period TEXT,
    accrual_date TEXT,
    expiry_date TEXT,
    status TEXT DEFAULT 'green',
    tolling_applicable INTEGER DEFAULT 0,
    tolling_basis TEXT,
    days_remaining INTEGER,
    notes TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (claim_id) REFERENCES causes_of_action(claim_id)
);

-- Provenance
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_table TEXT NOT NULL,
    record_id TEXT NOT NULL,
    source_file TEXT,
    source_page INTEGER,
    source_url TEXT,
    source_type TEXT,
    extraction_method TEXT,
    extraction_confidence REAL DEFAULT 1.0,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now')),
    UNIQUE(record_table, record_id, source_file)
);
CREATE INDEX IF NOT EXISTS idx_prov_record ON provenance(record_table, record_id);

-- Brain metadata
CREATE TABLE IF NOT EXISTS brain_meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
INSERT OR REPLACE INTO brain_meta (key, value) VALUES
    ('brain_name', 'claims'),
    ('brain_version', '1.0'),
    ('trust_level', 'versioned'),
    ('update_policy', 'versioned_updates'),
    ('created_at', datetime('now'));
"""

# ═══════════════════════════════════════════════════════════
# BRAIN 5: INTERPRETATION BRAIN — AI analysis (VERSIONED, AI-GENERATED)
# ═══════════════════════════════════════════════════════════
INTERPRETATION_SCHEMA = """
-- Legal Arguments (AI-drafted)
CREATE TABLE IF NOT EXISTS legal_arguments (
    argument_id TEXT PRIMARY KEY,
    claim_id TEXT,
    case_lane TEXT,
    argument_type TEXT NOT NULL,
    argument_text TEXT NOT NULL,
    supporting_authorities TEXT,
    supporting_evidence TEXT,
    counter_arguments TEXT,
    strength_score REAL,
    ai_model TEXT,
    ai_confidence REAL,
    version INTEGER DEFAULT 1,
    superseded_by TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS arguments_fts USING fts5(
    argument_type, argument_text, supporting_authorities, content=legal_arguments, content_rowid=rowid
);

-- Strategic Analysis
CREATE TABLE IF NOT EXISTS strategy_analysis (
    analysis_id TEXT PRIMARY KEY,
    case_lane TEXT,
    analysis_type TEXT NOT NULL,
    analysis_text TEXT NOT NULL,
    risk_score REAL,
    success_probability REAL,
    recommended_actions TEXT,
    ai_model TEXT,
    ai_confidence REAL,
    version INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Impeachment Analysis
CREATE TABLE IF NOT EXISTS impeachment_analysis (
    impeachment_id TEXT PRIMARY KEY,
    target_party TEXT NOT NULL,
    impeachment_type TEXT NOT NULL,
    description TEXT NOT NULL,
    prior_statement TEXT,
    contradicting_evidence TEXT,
    severity TEXT DEFAULT 'moderate',
    case_lane TEXT,
    source_references TEXT,
    ai_model TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS impeachment_fts USING fts5(
    target_party, impeachment_type, description, prior_statement, content=impeachment_analysis, content_rowid=rowid
);

-- Risk Assessments
CREATE TABLE IF NOT EXISTS risk_assessments (
    risk_id TEXT PRIMARY KEY,
    case_lane TEXT,
    filing_name TEXT,
    risk_category TEXT NOT NULL,
    risk_description TEXT NOT NULL,
    risk_level TEXT DEFAULT 'medium',
    mitigation TEXT,
    ai_model TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Brief Drafts (AI-generated sections)
CREATE TABLE IF NOT EXISTS brief_drafts (
    draft_id TEXT PRIMARY KEY,
    filing_name TEXT,
    section_name TEXT NOT NULL,
    draft_text TEXT NOT NULL,
    case_lane TEXT,
    word_count INTEGER,
    citation_count INTEGER,
    ai_model TEXT,
    ai_confidence REAL,
    version INTEGER DEFAULT 1,
    superseded_by TEXT,
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS drafts_fts USING fts5(
    filing_name, section_name, draft_text, content=brief_drafts, content_rowid=rowid
);

-- Citation Validation Results
CREATE TABLE IF NOT EXISTS citation_validations (
    validation_id TEXT PRIMARY KEY,
    citation TEXT NOT NULL,
    citation_type TEXT,
    filing_source TEXT,
    is_valid INTEGER,
    current_status TEXT,
    validation_method TEXT,
    validation_notes TEXT,
    alternative_citation TEXT,
    ai_model TEXT,
    validated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cv_citation ON citation_validations(citation);

-- Authority Application Analysis (how law applies to facts)
CREATE TABLE IF NOT EXISTS authority_applications (
    application_id TEXT PRIMARY KEY,
    authority_id TEXT NOT NULL,
    authority_type TEXT NOT NULL,
    claim_id TEXT,
    case_lane TEXT,
    application_text TEXT NOT NULL,
    relevance_score REAL,
    binding_level TEXT,
    distinguishable INTEGER DEFAULT 0,
    distinguishing_factors TEXT,
    ai_model TEXT,
    version INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS applications_fts USING fts5(
    authority_type, application_text, content=authority_applications, content_rowid=rowid
);

-- Provenance
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_table TEXT NOT NULL,
    record_id TEXT NOT NULL,
    source_file TEXT,
    ai_model TEXT,
    ai_confidence REAL,
    input_context TEXT,
    sha256 TEXT,
    extracted_at TEXT DEFAULT (datetime('now')),
    UNIQUE(record_table, record_id, source_file)
);
CREATE INDEX IF NOT EXISTS idx_prov_record ON provenance(record_table, record_id);

-- Brain metadata
CREATE TABLE IF NOT EXISTS brain_meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
INSERT OR REPLACE INTO brain_meta (key, value) VALUES
    ('brain_name', 'interpretation'),
    ('brain_version', '1.0'),
    ('trust_level', 'ai_generated'),
    ('update_policy', 'versioned_never_overwrite'),
    ('created_at', datetime('now'));
"""

# ═══════════════════════════════════════════════════════════
# CROSS-BRAIN INDEX
# ═══════════════════════════════════════════════════════════
CROSS_BRAIN_SCHEMA = """
-- Cross-brain references
CREATE TABLE IF NOT EXISTS cross_references (
    ref_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_brain TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_brain TEXT NOT NULL,
    target_table TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(source_brain, source_id, target_brain, target_id, relationship_type)
);
CREATE INDEX IF NOT EXISTS idx_xref_source ON cross_references(source_brain, source_id);
CREATE INDEX IF NOT EXISTS idx_xref_target ON cross_references(target_brain, target_id);

-- Universal search index
CREATE VIRTUAL TABLE IF NOT EXISTS universal_search USING fts5(
    brain_name, table_name, record_id, searchable_text, record_type
);

-- Extraction queue (files to process)
CREATE TABLE IF NOT EXISTS extraction_queue (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending',
    target_brain TEXT,
    extraction_method TEXT,
    error_message TEXT,
    attempts INTEGER DEFAULT 0,
    queued_at TEXT DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT,
    UNIQUE(file_path)
);
CREATE INDEX IF NOT EXISTS idx_queue_status ON extraction_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_priority ON extraction_queue(priority);

-- Brain statistics
CREATE TABLE IF NOT EXISTS brain_stats (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brain_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    row_count INTEGER,
    last_ingestion TEXT,
    snapshot_at TEXT DEFAULT (datetime('now'))
);

-- Brain metadata
CREATE TABLE IF NOT EXISTS brain_meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
INSERT OR REPLACE INTO brain_meta (key, value) VALUES
    ('brain_name', 'cross_brain_index'),
    ('brain_version', '1.0'),
    ('trust_level', 'meta'),
    ('update_policy', 'auto_maintained'),
    ('created_at', datetime('now'));
"""


if __name__ == '__main__':
    os.makedirs(BRAIN_DIR, exist_ok=True)

    brains = [
        ('authority_brain', AUTHORITY_SCHEMA),
        ('narrative_brain', NARRATIVE_SCHEMA),
        ('entity_brain', ENTITY_SCHEMA),
        ('claims_brain', CLAIMS_SCHEMA),
        ('interpretation_brain', INTERPRETATION_SCHEMA),
        ('cross_brain_index', CROSS_BRAIN_SCHEMA),
    ]

    for name, schema in brains:
        create_brain(name, schema)

    print(f"\n\u2705 ALL {len(brains)} BRAIN DATABASES CREATED in {BRAIN_DIR}")
    print("Brain Universe is ONLINE.")
