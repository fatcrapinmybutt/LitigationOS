PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS fileatoms (
  atom_id TEXT PRIMARY KEY,
  source_path_norm TEXT NOT NULL,
  bytes_size INTEGER NOT NULL,
  mtime_utc TEXT NOT NULL,
  ctime_utc TEXT,
  file_id TEXT,
  volume_serial TEXT,
  ext TEXT NOT NULL,
  kind TEXT NOT NULL,
  lane TEXT NOT NULL,
  case_id TEXT,
  discovered_at_utc TEXT NOT NULL,
  truth_tag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS extractions (
  atom_id TEXT NOT NULL,
  extractor TEXT NOT NULL,
  extracted_at_utc TEXT NOT NULL,
  text_path TEXT NOT NULL,
  char_count INTEGER NOT NULL,
  warnings_json TEXT NOT NULL,
  PRIMARY KEY (atom_id, extracted_at_utc)
);

CREATE TABLE IF NOT EXISTS quotes (
  quote_id TEXT PRIMARY KEY,
  atom_id TEXT NOT NULL,
  text TEXT NOT NULL,
  start_pos INTEGER NOT NULL,
  end_pos INTEGER NOT NULL,
  pinpoint_scheme TEXT,
  pinpoint_value TEXT,
  truth_tag TEXT NOT NULL,
  relevance REAL NOT NULL DEFAULT 0.0
);

CREATE VIRTUAL TABLE IF NOT EXISTS quotes_fts USING fts5(
  quote_id UNINDEXED,
  atom_id UNINDEXED,
  lane UNINDEXED,
  case_id UNINDEXED,
  text,
  tokenize='unicode61'
);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  lane TEXT NOT NULL,
  case_id TEXT,
  actor TEXT,
  action TEXT NOT NULL,
  obj TEXT,
  when_event_utc TEXT,
  when_recorded_utc TEXT,
  support_quotes_json TEXT NOT NULL,
  truth_tag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS packs (
  pack_id TEXT PRIMARY KEY,
  purpose TEXT NOT NULL,
  scope_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  query_text TEXT NOT NULL,
  pack_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fileatoms_lane_case ON fileatoms(lane, case_id);
CREATE INDEX IF NOT EXISTS idx_quotes_atom ON quotes(atom_id);
CREATE INDEX IF NOT EXISTS idx_events_lane_case ON events(lane, case_id);
