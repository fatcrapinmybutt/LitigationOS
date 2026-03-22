---
description: Hardware topology, drive layout, and database centralization architecture for LitigationOS. Apply when performing file operations, database migrations, backup scripts, or storage-tier decisions.
applyTo: "**/*.{py,ps1,sh,sql,md}"
---

# Infrastructure Memory

Drive hardware map, storage tiering rules, and database centralization patterns for a 6-drive litigation corpus.

## Drive Hardware Map

| Drive | Device | Type | Size | Filesystem | Performance | Role |
|-------|--------|------|------|-----------|-------------|------|
| **C:\** | WDC PC SN530 | NVMe SSD | 238 GB | NTFS | ⚡ Fast | Primary OS + active databases |
| **D:\** | EAGT | USB | 466 GB | — | Slow | DB archives |
| **F:\** | Memorex | USB Flash | 58 GB | — | Slow | Backups, index files |
| **G:\** | Memorex | USB Flash | 58 GB | — | Slow | Evidence |
| **I:\** | Generic SD/MMC | SD Card | ~30 GB | — | Slow | Sorted evidence, dedup target |
| **J:\** | General UDisk | USB Removable | 1953 GB | **exFAT** | Slow | Centralization target (1.94 TB free) |

**C:\ is the only SSD.** All other drives are USB mass storage or flash — 10-100× slower random I/O. Keep all active/hot databases and WAL-mode files exclusively on C:\. All other drives are suitable only for sequential reads, archives, and cold reference queries.

**J:\ is exFAT** — no file locking, no symlinks, no junctions, no NTFS streams. WAL mode is unsafe here. Use `PRAGMA journal_mode=DELETE` or `immutable=1` for any SQLite database on J:\.

## Database Centralization Architecture

70+ databases (~37 GB) scattered across 6 drives, consolidated into a 3-tier hybrid:

```
TIER 1: HOT (~1.5 GB) — C:\Users\andre\LitigationOS\ (NVMe SSD, NTFS)
  WAL mode, fast reads/writes, reliable file locking
  ├── litigation_context.db       422 MB   central hub
  ├── mcr_rules.db                3.7 MB   court rules
  ├── court_forms.db              0.1 MB   SCAO forms
  ├── 00_SYSTEM/brains/*.db       685 MB   AI brains (interpretation, narrative, authority)
  ├── 00_SYSTEM/file_catalog.db   233 MB   file catalog
  ├── 09_DATA/authority_master.db  83 MB   authorities
  ├── 09_DATA/ec.db                29 MB   evidence chains
  └── 09_DATA/litigation_lite.db   50 MB   lite queries

TIER 2: WARM (~3.2 GB) — J:\LitigationOS_CENTRAL\DATABASES\ (USB, exFAT)
  DELETE journal mode, infrequent cold queries only
  ├── MANIFESTS/    drive_I_manifest (1.4 GB), omega_dedup (592 MB), etc.
  ├── OCR/          ocr_master.db (231 MB)
  ├── TOOLS/        script_forge.db (211 MB)
  └── REFERENCE/    flatten_manifest (511 MB), consolidation_plan (13 MB)

TIER 3: ARCHIVE (~33 GB) — J:\LitigationOS_CENTRAL\ARCHIVE\ (USB, exFAT)
  Read-only (immutable=1), never written to
  ├── Backups from I:\ (v0.9.0 11.7 GB, v12.1.1 8.0 GB)
  ├── Backups from F:\ (v0.9.0 4.1 GB)
  └── Archives from D:\ (master_index 3.3 GB, cross_brain 1.2 GB, etc.)
```

## File Copy Protocol for Large Databases

When migrating databases between drives, use chunked copy with SHA-256 verification:

```python
import hashlib, shutil

def copy_with_verify(src: str, dst: str, chunk_size: int = 1024 * 1024) -> str:
    """Copy file with streaming SHA-256 verification. Returns hex digest."""
    sha = hashlib.sha256()
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        while chunk := fsrc.read(chunk_size):
            sha.update(chunk)
            fdst.write(chunk)
    return sha.hexdigest()
```

Generate a manifest (JSON) with source path, destination path, file size, SHA-256, and copy timestamp for every migrated database. Store manifest at `J:\LitigationOS_CENTRAL\MANIFEST.json`.

## No-Delete Policy

LitigationOS enforces **append-only evidence** and **no hard deletions**. When consolidating or deduplicating:
- **COPY** files to the target location — never move
- Original files remain in place on their source drives
- Duplicates go to `I:\` dedup folder, never deleted
- Content-based dedup only — peek inside documents, do not rely solely on file hashing
