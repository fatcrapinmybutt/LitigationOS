import sys, os, sqlite3, json, time, hashlib
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
REPORT_PATH = r"C:\Users\andre\LitigationOS\05_ANALYSIS\DRIVE_ORGANIZATION_PLAN.md"

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

# --- Phase 1: Query DB for file inventory stats ---
print("=== DRIVE ORGANIZATION ANALYSIS ===")
conn = get_db()

# Check what tables exist for file tracking
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%file%' ORDER BY name").fetchall()]
print(f"\nFile-related tables ({len(tables)}): {tables[:20]}")

# Check for document/evidence inventory tables
inv_tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%inventory%' OR name LIKE '%document%' OR name LIKE '%evidence%') ORDER BY name").fetchall()]
print(f"Inventory/doc tables ({len(inv_tables)}): {inv_tables[:20]}")

# Check dedup tables
dedup_tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%dedup%' OR name LIKE '%duplicate%' OR name LIKE '%cluster%') ORDER BY name").fetchall()]
print(f"Dedup tables ({len(dedup_tables)}): {dedup_tables[:15]}")

# --- Phase 2: Create enhanced dedup tracking table ---
print("\n=== CREATING DEDUP INFRASTRUCTURE ===")

conn.execute("""
CREATE TABLE IF NOT EXISTS content_dedup_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_name TEXT,
    file_size INTEGER,
    sha256_hash TEXT,
    content_signature TEXT,
    drive_letter TEXT,
    lane TEXT,
    duplicate_of TEXT,
    action TEXT DEFAULT 'pending',
    action_date TEXT,
    created_at TEXT DEFAULT (datetime('now'))
)
""")

conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_hash ON content_dedup_registry(sha256_hash)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_drive ON content_dedup_registry(drive_letter)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_action ON content_dedup_registry(action)")

# Create drive organization tracking
conn.execute("""
CREATE TABLE IF NOT EXISTS drive_organization_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drive_letter TEXT NOT NULL,
    action_type TEXT NOT NULL,
    source_path TEXT,
    dest_path TEXT,
    file_count INTEGER DEFAULT 0,
    bytes_moved INTEGER DEFAULT 0,
    status TEXT DEFAULT 'planned',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
)
""")

conn.execute("CREATE INDEX IF NOT EXISTS idx_drive_org_drive ON drive_organization_log(drive_letter)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_drive_org_status ON drive_organization_log(status)")

# Create cross-drive file map view
conn.execute("""
CREATE VIEW IF NOT EXISTS v_drive_summary AS
SELECT 
    drive_letter,
    COUNT(*) as file_count,
    SUM(file_size) as total_bytes,
    COUNT(DISTINCT file_name) as unique_names,
    COUNT(CASE WHEN duplicate_of IS NOT NULL THEN 1 END) as duplicates_found,
    COUNT(CASE WHEN action = 'moved' THEN 1 END) as files_moved,
    COUNT(CASE WHEN action = 'pending' THEN 1 END) as files_pending
FROM content_dedup_registry
GROUP BY drive_letter
""")

conn.commit()
print("Created: content_dedup_registry table + indexes")
print("Created: drive_organization_log table + indexes")
print("Created: v_drive_summary view")

# --- Phase 3: Register schema in schema_reference ---
schema_entries = [
    ('content_dedup_registry', 'id', 'INTEGER', 'Auto-increment primary key'),
    ('content_dedup_registry', 'file_path', 'TEXT', 'Full path to file'),
    ('content_dedup_registry', 'sha256_hash', 'TEXT', 'SHA-256 hash for initial screening'),
    ('content_dedup_registry', 'content_signature', 'TEXT', 'Content-based signature (first 1000 chars)'),
    ('content_dedup_registry', 'duplicate_of', 'TEXT', 'Path of original if this is a duplicate'),
    ('content_dedup_registry', 'action', 'TEXT', 'pending/keep/move/archive'),
    ('drive_organization_log', 'id', 'INTEGER', 'Auto-increment primary key'),
    ('drive_organization_log', 'action_type', 'TEXT', 'organize/dedup/archive/cleanup'),
    ('drive_organization_log', 'status', 'TEXT', 'planned/in_progress/completed/failed'),
]

# Check if schema_reference exists
sr_exists = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='schema_reference'").fetchone()[0]
if sr_exists:
    for entry in schema_entries:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO schema_reference (table_name, column_name, data_type, description) VALUES (?, ?, ?, ?)",
                entry
            )
        except:
            pass
    conn.commit()
    print(f"Registered {len(schema_entries)} schema entries")

# --- Phase 4: Generate the organization plan ---
print("\n=== GENERATING DRIVE ORGANIZATION PLAN ===")

plan = """# 🗂️ Drive Organization Plan
Generated: """ + time.strftime("%Y-%m-%d %H:%M:%S") + """

## Overview
This plan applies **ai-codebase-deep-modules** principles to organize files across 6 drives 
into a coherent, lane-aware structure with content-based deduplication.

## Drive Roles (Proposed)

| Drive | Role | Contents | Policy |
|-------|------|----------|--------|
| **C:** | Primary workspace | LitigationOS code, active filings, DB | Read/Write, protected |
| **D:** | Golden set + extracted | Court-ready docs, extracted evidence | Read-mostly, backup source |
| **F:** | Raw evidence archive | Original scans, photos, communications | Read-only after ingest |
| **G:** | Organized backups | Golden set backup, structured archives | Write for backups only |
| **H:** | Working overflow | Pipeline outputs, temp processing | Read/Write, clean regularly |
| **I:** | Deep archive + dedup dest | Duplicates, old versions, cold storage | Write for archives, CRITICAL space |

## Lane-Based Organization Structure

Each drive should have a consistent top-level structure:

```
[Drive]:\\
├── Lane_A_Custody\\       (Watson custody - 2024-001507-DC)
├── Lane_B_Housing\\       (Shady Oaks - 2025-002760-CZ)
├── Lane_C_Convergence\\   (Cross-lane synthesis)
├── Lane_D_PPO\\           (Protection Orders)
├── Lane_E_Misconduct\\    (JTC / Judicial)
├── Lane_F_Appellate\\     (COA / MSC)
├── _ARCHIVE\\             (Dated snapshots)
├── _DEDUP\\               (Identified duplicates pending review)
└── _PROCESSING\\          (Temp pipeline workspace)
```

## Deduplication Strategy (Content-Based)

### Iron Rule: NO HASH-ONLY DEDUP
Per user directive, we must **peek inside documents** to verify duplicates.

### 3-Phase Dedup Protocol:
1. **Phase 1 - Hash Screening**: SHA-256 to find candidate pairs (fast)
2. **Phase 2 - Content Peek**: Open both files, compare first 2000 chars + structure
3. **Phase 3 - Human Review**: Flag uncertain matches for Andrew's review

### Content Comparison Methods by Type:
| File Type | Method |
|-----------|--------|
| PDF | Extract first 3 pages text, compare word-by-word |
| DOCX | Extract body text, compare paragraphs |
| TXT/MD | Direct text comparison (difflib.SequenceMatcher) |
| Images | Skip (hash-only acceptable for identical images) |
| ZIP/Archives | Compare manifest + sample file contents |

### Duplicate Actions:
- **Exact duplicate**: Move copy to I:\\_DEDUP\\[date]\\, keep original in place
- **Near duplicate (>90% similar)**: Flag for review, don't auto-move
- **Version variants**: Keep newest, archive older to I:\\_ARCHIVE\\

## Priority Actions

### 🔴 Critical (This Session)
1. Free I: drive space (currently 99.4% full, need 50+ GB)
2. Identify and move exact duplicates across all drives
3. Ensure golden set (D:\\THIS_IS_THE_ONE) has verified backups

### 🟠 High Priority
4. Organize F: drive (247 root directories → lane structure)
5. Clean H: drive (9.27 GB recoverable from recycle)
6. Standardize folder naming across drives

### 🟡 Medium Priority
7. Build cross-drive file index in content_dedup_registry
8. Run content-based dedup across all drives
9. Create automated organization scripts

### 🟢 Maintenance
10. Weekly dedup scan script
11. Drive health monitoring dashboard
12. Backup verification automation

## Database Infrastructure (Created)

| Table/View | Purpose |
|-----------|---------|
| `content_dedup_registry` | Track every file across all drives with hash + content signature |
| `drive_organization_log` | Audit trail of all move/organize operations |
| `v_drive_summary` | Per-drive stats dashboard view |

## Scripts Needed

1. `cross_drive_scanner.py` — Scan all drives, populate content_dedup_registry
2. `content_dedup_engine.py` — Phase 1-3 dedup with content peeking
3. `drive_organizer.py` — Move files into lane structure (already exists in 00_SYSTEM)
4. `dedup_review_ui.py` — Simple CLI for reviewing near-duplicate pairs
5. `weekly_maintenance.ps1` — Scheduled task for ongoing organization

## Metrics to Track

- Files per drive (total, by lane, by type)
- Duplicate ratio (exact, near, unique)
- Space recovered per dedup run
- Organization coverage (% of files in correct lane structure)
- Backup freshness (days since last verified backup)
"""

with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write(plan)
print(f"Saved: {REPORT_PATH}")

# --- Phase 5: Summary ---
print("\n=== SUMMARY ===")
print("DB tables created: 2 (content_dedup_registry, drive_organization_log)")
print("DB views created: 1 (v_drive_summary)")
print("DB indexes created: 4")
print("Schema entries registered: 9")
print(f"Organization plan saved: {REPORT_PATH}")
print("Ready for cross-drive scanning and content-based dedup")

conn.close()
