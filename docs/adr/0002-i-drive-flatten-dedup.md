# ADR-0002: I: Drive Flatten and Dedup Strategy

- **Status:** Accepted
- **Date:** 2026-03-06
- **Deciders:** Andrew Pigors

## Context

The I:\ drive serves as a primary evidence storage volume for LitigationOS. It has reached critical capacity:

- **Total size:** 465.7 GB
- **Free space:** Originally 4.45 GB (now ~18 GB after quick wins)
- **File count:** ~833,000 files across 20 top-level folders
- **Largest folders:** `05_EVIDENCE` (599K files, 219 GB), `12_ARCHIVES` (209K files, 115 GB)

The user's explicit requirements:
1. **Flatten all files to I:\ root** — zero subfolders, every file at the top level.
2. **Dedup signals:** "file name and size and date" — same name + same size = duplicate. Folder sizes are "a dead giveaway" for duplicate directory trees.
3. **No hard deletions** — duplicates must be moved, never deleted. This is litigation evidence subject to preservation obligations.

A previous session's scan identified **103,031 duplicate-name groups**, confirming massive redundancy across the nested folder structure.

## Decision Drivers

- Must recover significant free space on the critically full I:\ drive
- Must preserve all original evidence files (litigation hold — no deletions)
- Must use content-aware dedup, not just filename hashing
- Must be scriptable and repeatable (not manual GUI work for 833K files)
- Must produce an audit trail (manifest) for chain-of-custody compliance
- Must handle name collisions when flattening nested paths to a single directory

## Considered Options

### Option 1: Custom Python Script (`i_drive_flatten.py`) — **CHOSEN**

Purpose-built Python script with SQLite manifest, (name + size + date) dedup logic, flatten with collision handling, and `--dry-run` safety mode.

### Option 2: czkawka CLI Only

Rust-based duplicate finder with fast scanning and multiple dedup strategies.

### Option 3: AllDup

Windows GUI application for finding and managing duplicate files.

### Option 4: Manual Windows Explorer

Use Windows Explorer's search and manual file operations.

## Decision

Build a **custom Python flatten-and-dedup script** (`i_drive_flatten.py`) as the primary tool, with **czkawka CLI** as a companion tool for fast Rust-based size scanning and verification.

### Dedup Algorithm

```
For each file on I:\:
  1. Compute key = (filename, size_bytes)
  2. Group files by key
  3. Within each group:
     a. Keep the file with the oldest date_created (the original)
     b. Move all others to I:\__DEDUP_HOLDING\
  4. For the kept file, move to I:\ root
  5. On name collision at root: prepend parent folder name
     e.g., "report.pdf" from "05_EVIDENCE\custody\" → "custody_report.pdf"
```

### Manifest Schema

```sql
CREATE TABLE flatten_manifest (
    id INTEGER PRIMARY KEY,
    original_path TEXT NOT NULL,
    new_path TEXT,
    action TEXT NOT NULL,        -- 'kept', 'dedup_moved', 'flattened', 'collision_renamed'
    file_name TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    date_created TEXT,
    date_modified TEXT,
    sha256 TEXT,                  -- computed on-demand for verification
    dedup_group_id INTEGER,
    processed_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Rationale

### Why Custom Python (Option 1)

- **Exact match to requirements:** Implements the precise (name + size + date) dedup logic the user specified, with flatten-to-root behavior.
- **SQLite manifest:** Provides a queryable audit trail for every file operation — critical for litigation chain-of-custody.
- **--dry-run mode:** Can simulate the entire operation and produce a report before moving any files. Essential for 833K files.
- **Pipeline integration:** Written in Python, can be imported by other LitigationOS modules or called from the agent fleet.
- **Collision handling:** Custom logic to prepend parent folder names prevents data loss during flatten.

### Why Not czkawka Only (Option 2)

- czkawka excels at finding duplicates but cannot flatten a directory tree to root.
- No built-in SQLite manifest or custom collision-handling logic.
- However, czkawka is valuable as a companion tool: its Rust-based scanner is significantly faster than Python for initial size-based scanning of 833K files.

### Why Not AllDup (Option 3)

- GUI-focused tool — cannot be scripted or integrated into the pipeline.
- No flatten capability.
- No programmatic manifest output.

### Why Not Manual (Option 4)

- 833,000 files across 20 folders with 103K duplicate groups is physically impossible to handle manually.
- No audit trail, no reproducibility, high risk of accidental deletion.

## Consequences

### Positive

- **Significant space recovery:** 103K duplicate groups suggest potentially 50-100+ GB of recoverable space.
- **Clean flat structure:** Every evidence file accessible at I:\ root without navigating nested folders.
- **Full audit trail:** SQLite manifest records every operation — what was moved, where, why.
- **Reversible:** Duplicates moved to `I:\__DEDUP_HOLDING\`, not deleted. Can restore any file from the manifest.
- **Queryable inventory:** Manifest enables SQL queries like "show me all PDFs over 10 MB" or "find all files from 05_EVIDENCE."

### Negative

- **Explorer performance:** 800K+ files in a single root directory will slow Windows Explorer significantly. Consider using CLI tools (`fd`, `rg`, `dir`) instead of Explorer for navigation.
- **Scan duration:** Initial scan of 833K files will take ~10-15 minutes even with optimizations.
- **Name collisions:** Disambiguation by prepending parent folder names may create long or confusing filenames (e.g., `custody_2024_hearing_transcript_report.pdf`).
- **Temporary space needed:** Moving files requires temporary free space on I:\ during the operation.

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Accidental data loss | `--dry-run` first; no deletions ever; `__DEDUP_HOLDING` as safe harbor |
| Name collision creates ambiguity | Manifest records original path → always traceable |
| I:\ drive runs out of space during flatten | Process in batches; largest duplicates first |
| Power failure mid-operation | Manifest tracks `processed_at`; can resume from last checkpoint |

## Implementation Notes

### Execution Plan

```
Phase 1: Scan (read-only)
  - Walk entire I:\ tree
  - Build SQLite manifest with all 833K file entries
  - Identify duplicate groups by (name, size)
  - Report: total dupes, estimated space savings, collision count

Phase 2: Dry Run
  - Simulate all moves and renames
  - Output planned operations to manifest
  - User reviews before proceeding

Phase 3: Dedup (moves only)
  - Within each duplicate group, keep oldest file
  - Move others to I:\__DEDUP_HOLDING\{dedup_group_id}\
  - Update manifest with each move

Phase 4: Flatten (moves only)
  - Move all kept files from subfolders to I:\ root
  - Handle name collisions by prepending parent folder name
  - Update manifest

Phase 5: Verify
  - Confirm all files accounted for (manifest count = scan count)
  - Run czkawka as independent verification
  - Report final state
```

### File Layout After Completion

```
I:\
├── file1.pdf
├── file2.docx
├── custody_report.pdf          ← renamed from 05_EVIDENCE\custody\report.pdf
├── archives_report.pdf         ← renamed from 12_ARCHIVES\report.pdf
├── ...                         ← ~730K unique files at root
├── __DEDUP_HOLDING\            ← ~103K duplicate files preserved here
│   ├── group_00001\
│   ├── group_00002\
│   └── ...
└── __FLATTEN_MANIFEST.db       ← SQLite audit trail
```

### Companion Tool: czkawka

```powershell
# Fast Rust-based duplicate scan for verification
czkawka_cli dup -d I:\ -x hash -f results.txt
```

Used after the Python script completes to independently verify no duplicates remain in the flattened root.
