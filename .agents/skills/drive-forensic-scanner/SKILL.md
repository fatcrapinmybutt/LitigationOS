---
name: drive-forensic-scanner
description: "Deep forensic scanner for all drives. Fingerprints every file by content, detects duplicates via SHA256, classifies legal docs vs code vs evidence vs trash, maps project structures, finds corrupt/empty files, builds complete manifests. Use when: scan drives, organize files, find duplicates, audit filesystem."
---

# Drive Forensic Scanner

**Role**: Filesystem Intelligence Agent

Deep-scan drives to produce structured manifests of every file with:
- SHA256 hashing for dedup detection
- Content-type fingerprinting (magic bytes + extension + path analysis)
- Legal document classification (motions, briefs, evidence, court orders)
- Project structure detection (Python packages, Node apps, databases)
- Corrupt/empty/temp file detection
- Cross-drive duplicate mapping
- Size analysis and space recovery estimates

## Capabilities

- Parallel per-drive scanning via sub-agents
- SQLite manifest output for cross-drive queries  
- Trash detection (0-byte, .tmp, thumbs.db, desktop.ini, __pycache__)
- Legal content scoring (Michigan court patterns, case numbers, party names)
- Archive detection and contents listing
- Database inventory with table counts and sizes

## Usage

Deploy one agent per drive for parallel scanning. Each agent outputs to:
`C:\Users\andre\LitigationOS\00_SYSTEM\manifests\drive_{X}_manifest.db`

Then run cross-drive dedup query to find consolidation targets.