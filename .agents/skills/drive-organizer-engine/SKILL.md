---
name: drive-organizer-engine
description: "Consumes scanner manifests to deduplicate, consolidate, organize, and ingest files across all drives into a single LitigationOS master structure. Paired with drive-forensic-scanner. Use when: organize files, deduplicate, consolidate drives, clean filesystem, ingest evidence."
---

# Drive Organizer Engine

Reads SQLite manifests from the forensic scanner and executes a 6-stage pipeline:
1. Cross-Drive Dedup Analysis (SHA256 join across all manifests)
2. Smart Consolidation Plan (map files to correct 00-99 LitigationOS dirs)
3. Trash Cleanup (0-byte, .tmp, corrupt, __pycache__)
4. Execute Moves with rollback logging
5. Legal Document Ingestion into master_index.db
6. Verification and Report
