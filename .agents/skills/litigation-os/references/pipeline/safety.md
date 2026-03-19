# Phase 0: Safety System — Snapshot + Rollback + Validation

## Iron Rule

**Nothing in LITIGATIONOS_MASTER gets modified until a verified backup exists.**

No snapshot.lock = no pipeline. No exceptions.

## Pre-Flight Snapshot (safety.py)

```bash
python tooling/safety.py --target C:\Users\andre\scans
```

1. **SHA-256 MANIFEST** of entire LITIGATIONOS_MASTER/ (every file + hash + size + mtime)
   → `backups/SNAPSHOT_{ts}/manifest.sha256.json`

2. **FULL COPY** of all files that any phase will modify:
   - SYNTHESIS_DATA.json, SYNTHESIS_STATS.md
   - MASTER_*.csv (all 5)
   - authority_shards_all.jsonl, EC_AUTHORITY_MAP.jsonl, KNOWLEDGE_ALL.jsonl
   - neo4j_nodes.csv, neo4j_edges.csv
   - lexos_bible/brains/brain_*.json (all 50)
   → `backups/SNAPSHOT_{ts}/originals/`

3. **INTEGRITY CHECK** — SHA-256 of every copy verified against manifest
   → If ANY mismatch: ABORT, print error, exit non-zero

4. **SNAPSHOT LOCK** — `backups/SNAPSHOT_{ts}/snapshot.lock`
   → Pipeline refuses to run without a valid lock

## Rollback (rollback.py)

```bash
# Full revert
python tooling/rollback.py --snapshot SNAPSHOT_20260221_123456

# Per-phase revert
python tooling/rollback.py --snapshot SNAPSHOT_20260221_123456 --phase 7b
```

**Full revert:**
1. Restores every file from originals/ to its original location
2. Verifies every restored file matches manifest SHA-256
3. Removes NEW files created by the pipeline
4. Reports: "Restored N files, removed M new files, verified K checksums"

**Per-phase revert** uses `touchlog_phase{N}.jsonl` to identify only files modified by that phase.

## Per-Phase Safety Guards

| Guard | Implementation | When |
|-------|---------------|------|
| Read-only source | `scans/` never written to | Always |
| Copy-before-modify | Backup master file before update | Phases 5, 7, 8, 10 |
| Dry-run mode | `--dry-run` logs without writing | Always available |
| Touch log | Every write logged with SHA-256 before/after | Every phase |
| Atomic writes | Write `.tmp` → verify → `os.replace()` | Phases 7B, 7C |
| Size sanity | Warn if output >2x or <0.5x original | Phases 5, 7B |
| No-delete policy | Pipeline NEVER deletes source files | Always |
| Abort hook | Ctrl+C writes partial checkpoint | Orchestrator |

## Post-Run Validation (validate.py)

```bash
python tooling/validate.py --snapshot SNAPSHOT_20260221_123456
```

1. Re-hash every file in original manifest
2. Flag: modified files (expected — master CSVs, brains)
3. Flag: deleted files (SHOULD BE ZERO)
4. Flag: new files (expected — atoms, deltas)
5. Verify: all modified files have backup in snapshot
6. Verify: all new files are in cyclepacks/ or known merge targets
7. Output: `validation_report.json` with PASS/WARN/FAIL
