-- MI Appellate DocForge V8 (FTS-first; no SHA)
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS fileatoms(
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
  labels_json TEXT NOT NULL DEFAULT '[]',
  truth_tag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quotes(
  quote_id TEXT PRIMARY KEY,
  atom_id TEXT NOT NULL REFERENCES fileatoms(atom_id),
  text TEXT NOT NULL,
  truth_tag TEXT NOT NULL,
  pinpoint_scheme TEXT,
  pinpoint_value TEXT,
  start_char INTEGER,
  end_char INTEGER,
  actors_json TEXT NOT NULL DEFAULT '[]',
  tags_json TEXT NOT NULL DEFAULT '[]'
);

CREATE VIRTUAL TABLE IF NOT EXISTS corpus_fts USING fts5(
  quote_id,
  atom_id,
  lane,
  case_id,
  text,
  tokenize='unicode61'
);

CREATE TABLE IF NOT EXISTS events(
  event_id TEXT PRIMARY KEY,
  when_event_utc TEXT,
  when_recorded_utc TEXT,
  lane TEXT NOT NULL,
  case_id TEXT,
  actor TEXT,
  action TEXT NOT NULL,
  object TEXT,
  support_quote_ids_json TEXT NOT NULL DEFAULT '[]',
  truth_tag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS authority_triples(
  proposition_id TEXT PRIMARY KEY,
  proposition_text TEXT NOT NULL,
  authority_family TEXT NOT NULL,
  citation_stub TEXT NOT NULL,
  pinpoint TEXT,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS packs(
  pack_id TEXT PRIMARY KEY,
  purpose TEXT NOT NULL,
  lane TEXT NOT NULL,
  case_id TEXT,
  created_at_utc TEXT NOT NULL,
  scope_json TEXT NOT NULL,
  quote_ids_json TEXT NOT NULL,
  event_ids_json TEXT NOT NULL,
  authority_triples_json TEXT NOT NULL,
  acquisition_tasks_json TEXT NOT NULL,
  synthesis_instructions TEXT NOT NULL
);
