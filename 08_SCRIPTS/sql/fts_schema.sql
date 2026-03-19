CREATE TABLE IF NOT EXISTS fileatoms(
  atom_id TEXT PRIMARY KEY,
  source_path_norm TEXT NOT NULL,
  bytes_size INTEGER NOT NULL,
  mtime_utc TEXT NOT NULL,
  ctime_utc TEXT,
  file_id TEXT,
  volume_serial TEXT,
  ext TEXT,
  kind TEXT,
  lane TEXT,
  case_id TEXT,
  discovered_at_utc TEXT,
  truth_tag TEXT,
  identity_key TEXT,
  labels_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_fileatoms_lane_case ON fileatoms(lane, case_id);

CREATE TABLE IF NOT EXISTS extractions(
  atom_id TEXT NOT NULL,
  extractor TEXT NOT NULL,
  extracted_at_utc TEXT NOT NULL,
  text_path TEXT NOT NULL,
  char_count INTEGER NOT NULL,
  warnings_json TEXT,
  PRIMARY KEY(atom_id, extractor, extracted_at_utc)
);

CREATE TABLE IF NOT EXISTS quotes(
  quote_id TEXT PRIMARY KEY,
  atom_id TEXT NOT NULL,
  text TEXT NOT NULL,
  start_pos INTEGER NOT NULL,
  end_pos INTEGER NOT NULL,
  truth_tag TEXT,
  pinpoint_scheme TEXT,
  pinpoint_value TEXT,
  page_hint INTEGER,
  lane TEXT,
  case_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_quotes_lane_case ON quotes(lane, case_id);

CREATE VIRTUAL TABLE IF NOT EXISTS corpus_fts USING fts5(
  quote_id UNINDEXED,
  atom_id UNINDEXED,
  lane,
  case_id,
  text
);

CREATE TABLE IF NOT EXISTS events(
  event_id TEXT PRIMARY KEY,
  atom_id TEXT NOT NULL,
  action TEXT NOT NULL,
  actor TEXT,
  object TEXT,
  when_event_raw TEXT,
  when_event_utc TEXT,
  when_recorded_utc TEXT,
  truth_tag TEXT,
  support_quote_ids_json TEXT,
  lane TEXT,
  case_id TEXT
);

CREATE TABLE IF NOT EXISTS packs(
  pack_id TEXT PRIMARY KEY,
  purpose TEXT,
  created_at_utc TEXT,
  scope_json TEXT,
  query TEXT,
  quote_ids_json TEXT,
  event_ids_json TEXT,
  notes_json TEXT
);
