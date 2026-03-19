PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS ingest_runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  roots_json TEXT NOT NULL,
  stats_json TEXT,
  log_path TEXT
);

CREATE TABLE IF NOT EXISTS documents (
  doc_id TEXT PRIMARY KEY,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  ext TEXT,
  mime TEXT,
  original_path TEXT,
  stored_object_path TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(sha256);

CREATE TABLE IF NOT EXISTS extractions (
  extraction_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL,
  method TEXT NOT NULL,
  quality_score REAL,
  needs_ocr INTEGER NOT NULL DEFAULT 0,
  pages_json TEXT,
  fulltext_path TEXT,
  sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(doc_id) REFERENCES documents(doc_id)
);
CREATE INDEX IF NOT EXISTS idx_extractions_doc_id ON extractions(doc_id);

CREATE TABLE IF NOT EXISTS forms (
  form_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL,
  extraction_id TEXT,
  jurisdiction_guess TEXT,
  court_level_guess TEXT,
  family_guess TEXT,
  form_code_guess TEXT,
  title_guess TEXT,
  revision_guess TEXT,
  doctype_guess TEXT,
  detected_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(doc_id) REFERENCES documents(doc_id),
  FOREIGN KEY(extraction_id) REFERENCES extractions(extraction_id)
);
CREATE INDEX IF NOT EXISTS idx_forms_doc_id ON forms(doc_id);
CREATE INDEX IF NOT EXISTS idx_forms_code ON forms(form_code_guess);

CREATE TABLE IF NOT EXISTS form_instructions (
  instr_id TEXT PRIMARY KEY,
  form_id TEXT NOT NULL,
  instruction_fulltext_path TEXT NOT NULL,
  instruction_sha256 TEXT NOT NULL,
  spans_json_path TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(form_id) REFERENCES forms(form_id)
);

CREATE TABLE IF NOT EXISTS form_specs (
  spec_id TEXT PRIMARY KEY,
  form_id TEXT NOT NULL,
  spec_json_path TEXT NOT NULL,
  spec_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(form_id) REFERENCES forms(form_id)
);

CREATE TABLE IF NOT EXISTS compliance_profiles (
  profile_id TEXT PRIMARY KEY,
  form_id TEXT NOT NULL,
  profile_json_path TEXT NOT NULL,
  profile_sha256 TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  FOREIGN KEY(form_id) REFERENCES forms(form_id)
);

CREATE TABLE IF NOT EXISTS akn_templates (
  akn_id TEXT PRIMARY KEY,
  form_id TEXT NOT NULL,
  template_xml_path TEXT NOT NULL,
  template_sha256 TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  generator_version TEXT NOT NULL,
  validation_json TEXT,
  FOREIGN KEY(form_id) REFERENCES forms(form_id)
);

CREATE TABLE IF NOT EXISTS stack_manifests (
  stack_id TEXT PRIMARY KEY,
  form_id TEXT NOT NULL,
  case_id TEXT,
  stack_root TEXT NOT NULL,
  manifest_json_path TEXT NOT NULL,
  manifest_sha256 TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  FOREIGN KEY(form_id) REFERENCES forms(form_id)
);

CREATE TABLE IF NOT EXISTS rulebanks (
  rulebank_id TEXT PRIMARY KEY,
  jurisdiction TEXT NOT NULL,
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  loaded_at TEXT NOT NULL
);
