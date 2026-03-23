---
name: OMEGA-FLATTEN
description: "Drive organization system: flatten drives into ≤30 file-type folders, then deep litigation analysis, content-based dedup, and evidence forging. Beyond apex-omega-elite."
---

# OMEGA-FLATTEN v1.0 — Drive Organization System

## Mission
Flatten entire drives into ≤30 file-type folders, then perform deep judicial/litigation analysis of every file, content-based deduplication, and evidence forging — creating court-ready intelligence from raw chaos.

## Architecture: 5-Phase Pipeline

```
Phase 1: SCAN    → Walk entire drive, classify every file by type
Phase 2: ORGANIZE → Move files into ≤30 type-based folders
Phase 3: ANALYZE  → Deep litigation analysis (MEEK lanes, entities, evidence value)
Phase 4: DEDUP    → Content-based deduplication (peek inside, not just hash)
Phase 5: FORGE    → Condense, merge, synthesize into court-ready intelligence
```

## The 30-Folder Taxonomy

| # | Folder | Purpose | Extensions |
|---|--------|---------|------------|
| 1 | `_INDEX` | Master index, flatten.db, manifests, reports | (system) |
| 2 | `_DEDUP` | Duplicate files (content-based dedup) | (system) |
| 3 | `_UNKNOWN` | Unclassified files | (fallback) |
| 4 | `PDF` | PDF documents | .pdf |
| 5 | `DOCX` | Word documents | .docx .doc .rtf .odt |
| 6 | `MD` | Markdown files | .md .markdown .mdx .rst |
| 7 | `TXT` | Plain text | .txt .text .asc |
| 8 | `HTML` | Web files | .html .htm .css .mhtml |
| 9 | `JSON` | JSON/JSONL data | .json .jsonl .geojson |
| 10 | `CSV` | Tabular data | .csv .tsv .xlsx .xls |
| 11 | `XML` | XML files | .xml .xsl .xsd .rss .plist |
| 12 | `IMG` | Images | .png .jpg .jpeg .gif .bmp .tiff .webp .svg |
| 13 | `VIDEO` | Video files | .mp4 .avi .mov .mkv .wmv |
| 14 | `AUDIO` | Audio files | .mp3 .wav .m4a .flac .ogg |
| 15 | `MEDIA` | Design media | .psd .ai .sketch .fig |
| 16 | `PY` | Python code | .py .pyw .pyi |
| 17 | `CODE` | Other source code | .js .ts .go .java .c .cpp .rs .sh .ps1 .sql |
| 18 | `DB` | Databases | .db .sqlite .sqlite3 .mdb |
| 19 | `DATA` | Binary data | .dat .bin .parquet .pkl .h5 |
| 20 | `EMAIL` | Email files | .eml .msg .mbox .pst |
| 21 | `PPTX` | Presentations | .pptx .ppt .key |
| 22 | `CONFIG` | Config files | .ini .yaml .yml .toml .env .cfg |
| 23 | `LOG` | Log files | .log |
| 24 | `ARCHIVE` | Compressed archives | .zip .rar .7z .tar .gz .iso |
| 25 | `EXE` | Executables | .exe .msi .dll .sys |
| 26 | `FONT` | Fonts | .ttf .otf .woff .woff2 |
| 27 | `CERT` | Certificates/keys | .pem .crt .key .cer |
| 28 | `BACKUP` | Backup files | .bak .old .orig .swp |
| 29 | `TEMP` | Temporary files | .tmp .cache .temp |
| 30 | `LEGAL` | Legal docs (content-detected) | (by MEEK signal analysis) |

## Usage

```powershell
# Flatten a drive (all phases)
python 00_SYSTEM\tools\drive_flattener\cli.py D --phase all

# Scan only (inventory without moving)
python 00_SYSTEM\tools\drive_flattener\cli.py D --phase scan --dry-run

# Organize only (move files into folders)
python 00_SYSTEM\tools\drive_flattener\cli.py D --phase organize

# Analyze only (deep litigation analysis)
python 00_SYSTEM\tools\drive_flattener\cli.py D --phase analyze

# Dedup only (content-based deduplication)
python 00_SYSTEM\tools\drive_flattener\cli.py D --phase dedup --dry-run

# Forge only (synthesize intelligence)
python 00_SYSTEM\tools\drive_flattener\cli.py D --phase forge

# Resume from checkpoint
python 00_SYSTEM\tools\drive_flattener\cli.py D --phase all --resume

# Limit processing (for testing)
python 00_SYSTEM\tools\drive_flattener\cli.py D --phase scan --limit 1000
```

## Execution Order (Recommended)
1. **D: drive first** — 24GB, 230K files (medium, good test)
2. **F: drive** — 23.5MB, 2.1K files (tiny, quick win)
3. **J: drive** — 5.7GB, 4.7K files (small, high-value MI Court Rules)
4. **I: drive last** — 1.2TB, 564K files (massive, needs full day)

## Database
Each drive gets its own `{drive}:\_INDEX\flatten.db` with:
- `flat_files` — master file index (every file)
- `dedup_clusters` — duplicate groups
- `dedup_members` — cluster membership
- `scan_sessions` — scan history
- `file_analysis` — deep per-file analysis
- `forge_outputs` — synthesized outputs

## MEEK Lane Detection
Files are automatically tagged with litigation case lanes:
- **MEEK1** (Lane B): Shady Oaks / Housing — keywords: shady oaks, eviction, habitability
- **MEEK2** (Lane A): Watson Custody — keywords: custody, parenting time, watson, MCL 722
- **MEEK3** (Lane D): PPO — keywords: ppo, personal protection, stalking
- **MEEK4** (Lane E): Judicial Misconduct — keywords: mcneill, disqualif, jtc, bias
- **MEEK5** (Lane F): Appellate — keywords: court of appeals, coa, appellate, msc

## Critical Rules
- **NO HARD DELETIONS** — duplicates move to `_DEDUP`, never deleted
- **CONTENT-BASED DEDUP** — peek inside files, don't rely solely on hashing
- **Checkpoint every 500 files** — crash-safe, resumable
- **Manifest tracks all moves** — reversible via `_INDEX\MOVE_MANIFEST.json`
- **Permission errors → skip + log** — never crash on access denied

## Outputs Per Drive
After full flatten, each drive contains:
```
{drive}:\
├── _INDEX\
│   ├── flatten.db              # Master database
│   ├── MOVE_MANIFEST.json      # Old path → new path mapping
│   ├── DEDUP_REPORT.md         # Deduplication analysis
│   ├── DRIVE_ANALYSIS_REPORT.md # Comprehensive drive report
│   ├── EVIDENCE_BY_LANE.json   # Evidence grouped by MEEK lane
│   ├── ENTITY_INDEX.json       # All extracted entities
│   ├── TIMELINE.csv            # Extracted timeline events
│   └── TOP_EVIDENCE.md         # Top 50 highest-value files
├── _DEDUP\                     # Duplicates (preserving folder structure)
├── PDF\
├── DOCX\
├── MD\
├── ... (27 more type folders)
└── _UNKNOWN\                   # Unclassified
```

## Integration with LitigationOS
- High-value files (litigation_score ≥ 7) auto-suggested for `litigation_context.db` ingestion
- MEEK lane assignments feed into the 6-lane case routing system
- Entity extractions enrich the evidence_quotes and narrative_context tables
- Timeline events merge into case_timeline
- Forge outputs become exhibit candidates
