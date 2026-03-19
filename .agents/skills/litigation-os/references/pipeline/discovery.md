# Discovery Phases (1-4)

## Phase 1: Inventory — Full Recursive File Catalog

**Script:** `phase1_inventory.py`

- `os.walk()` with `\\?\` long-path prefix (handles 29-level depth on Windows)
- Stream SHA-256 hashing (64KB chunks — handles 99 GB without memory pressure)
- SQLite backend (not CSV) — indexed queries for all subsequent phases
- Skip list: .pyc, .class, .dll, .exe, java-1.8.0-openjdk*, __pycache__, tesseract-main/
- Progress: report every 10K files

**SQLite Schema:**
```sql
CREATE TABLE files (
  id INTEGER PRIMARY KEY, file_path TEXT NOT NULL, file_name TEXT NOT NULL,
  extension TEXT, size_bytes INTEGER, modified_time TEXT, sha256 TEXT,
  depth INTEGER, parent_dir TEXT, top_bucket TEXT, is_legal_content INTEGER DEFAULT 0,
  UNIQUE(file_path)
);
```

**Output:** `cyclepacks/CYCLE_{ts}/inventory.db` + `inventory_stats.json`

## Phase 2: Dedup — Hash-Cluster Canonical Election

**Script:** `phase2_dedup.py`

1. `SELECT sha256, COUNT(*) FROM files GROUP BY sha256 HAVING cnt > 1`
2. Score each path in cluster:
   - Depth penalty: lower depth = higher score
   - Bucket priority: LITIGATIONOS_MASTER > SCANNED_EVIDENCE > extracts > discovery
   - Path preference: court_orders/ > CORE_PDFS/ > sources/
3. Mark canonical: `UPDATE files SET is_canonical=1`

**Expected:** 50-70% reduction → ~120-200K canonical files

## Phase 3: Classify — Multi-Pass Legal Relevance

**Script:** `phase3_classify.py` (extends brain_builder.py scoring)

**Three passes:**

1. **Extension + Path Pattern**: Map extensions to categories (LEGAL_DOC, LEGAL_TEXT, STRUCTURED_DATA, etc.)
2. **Content Signals**: Reuse brain_builder.py regex patterns (MCL, MCR, case cites, persons, violations)
3. **MEEK Lane Assignment**: Match content signals to MEEK1-5 lane indicators

**Adds to SQLite:**
```sql
ALTER TABLE files ADD COLUMN category TEXT;
ALTER TABLE files ADD COLUMN priority TEXT;      -- HIGH/MEDIUM/LOW/SKIP
ALTER TABLE files ADD COLUMN meek_lanes TEXT;    -- comma-separated
ALTER TABLE files ADD COLUMN content_score REAL;
```

## Phase 4: Extract — Multi-Engine Text + Atom Generation

### 4A: PDF Extraction
- Primary: `pymupdf` (fitz) — already a dependency
- Fallback: Tesseract OCR for scanned pages
- Output: `extracts/{sha256}.txt` + `extraction_log.jsonl`

### 4B: DOCX Extraction
- `python-docx` (already used by j_docx_pipeline.py)
- Extracts: text + tables + headers/footers

### 4C: Structured Data (JSON/JSONL/CSV)
- Parse for embedded legal content, authority references, timeline data

### 4D: Atomize (extends compile_filings.py + consolidate_evidence.py)
- Generates 5 atom stores: fact, citation, event, person, contradiction
- All atoms carry evidence posture tags per BRAIN_SPEC
- See [atom-formats.md](../brain-spec/atom-formats.md) for schemas

### 4E: Archive Extraction (ZIP/RAR)
- Enumerate and extract legal documents from archives
- Feed extracted files back through 4A-4D
