# FRESH-START MEGA-PROMPT — LitigationOS OMEGA UNIFICATION
> **Load this at the start of a new Copilot CLI session to restore full context.**
> Generated: 2026-04-08 | Session 42+ | Separation Day 253

---

## IMMEDIATE CONTEXT RESTORE

Before doing ANY work, execute these steps IN ORDER:

```
Step 1: Read this file completely
Step 2: Read 04_ANALYSIS/SESSION_OFFLOAD_20260408.md (full session history)
Step 3: Read 04_ANALYSIS/WIZTREE_DRIVE_AUDIT.md (drive audit findings)
Step 4: Read 04_ANALYSIS/convergence_report.md (system health: 95.2/100)
Step 5: Query intel_dashboard for live DB stats
Step 6: Query separation_counter for current day count
Step 7: Report readiness to user
```

---

## THE MISSION

You are continuing a hyper-comprehensive plan to:

1. **EMERGENCY SPACE RECOVERY** — C: SSD has only ~8-10 GB free of 238 GB. 70+ GB is recoverable.
2. **DRIVE ORGANIZATION** — 2.35M files across 6 drives need canonical structure. 38 files violate MCR 8.119(H).
3. **DEDUPLICATION** — Content-based (peek inside documents, NOT hash-only). 5 duplicate mbp_brain.db, I: has 42.85 GB duplicate DBs.
4. **EVIDENCE INGESTION** — Final harvest from 19,811 PDFs, 65,526 TXTs, 12,270 DOCXs. MEEK lane routing.
5. **DATABASE CONSOLIDATION** — Brain sync (narrative_brain 93K events → central 18K), WAL checkpoint (147 MB), ANALYZE.
6. **THEMANBEARPIG.exe REBUILD** — Fix spec file paths/icon/console, wire all engines, build v22+ on D: drive.
7. **FULL SYSTEM INTEGRATION** — All databases, KRAKEN, engines, daemons, API unified as one system.

---

## EXECUTION PLAN (6 Phases)

### Phase 1: EMERGENCY C: Drive Space Recovery
**Priority: P0 — Must run FIRST. C: is choking.**

Actions (in order of impact):
1. **Git gc --aggressive** — 22 GB git objects → ~4-6 GB (recover ~16 GB)
2. **Archive duplicate DBs from C:\06_DATA\** — dup_file_catalog.db (232MB), dup_document_fulltext.db (19.8MB), dup_drive_inventory.db (477MB) → `11_ARCHIVES/`
3. **Archive old mbp_brain.db copies** from Desktop builds (~2.3 GB across 5 copies)
4. **Clean VS Code .BROWSE.VC.DB files** — 4 copies totaling ~4.2 GB
5. **Clean pip cache** — `pip cache purge`
6. **Archive duplicate master_index.db** — 3.24 GB copy exists on both C: and I:
7. **Ask user** about hibernation disable (8.76 GB) and pagefile reduction (3.6 GB)

Expected recovery: **30-50 GB** (conservative), up to 70 GB (aggressive with user approval)

### Phase 2: Cross-Drive Organization & Dedup
1. **I: drive** — Archive 42.85 GB of duplicate DBs (keep 1 latest backup on J:)
2. **J: drive** — Inspect 53.10 GB CHK files (FOUND.000/001/002), archive or delete with user approval
3. **G: drive** — Archive stale litigation_context.db
4. **Fix 38 MCR 8.119(H) violations** — rename files with child's full name in path
5. **Content-based dedup sweep** — peek inside, don't just hash. Move dupes to I: dedup folder.
6. **Zero-byte file cleanup** — 11,296 zero-byte files identified → archive

### Phase 3: Evidence Ingestion Sweep
1. **KRAKEN multi-round harvest** from drives with focus on un-ingested files
2. **MEEK lane routing** during ingestion (E→D→F→C→A→B priority)
3. **Persist HIGH findings** to evidence_quotes, timeline_events, impeachment_matrix
4. **Target**: 19,811 PDFs + 65,526 TXTs + 12,270 DOCXs across all drives

### Phase 4: Database Consolidation
1. **Brain sync** — narrative_brain (93K timeline_events) → central (18K) — sync TO central
2. **Entity brain sync** — entity_brain (17K parties) → central (27) — sync TO central
3. **WAL checkpoint** — 147 MB WAL file on main DB → PRAGMA wal_checkpoint(TRUNCATE)
4. **ANALYZE all DBs** — refresh query planner statistics
5. **FTS5 rebuild** where needed — evidence_fts, timeline_fts
6. **Archive duplicate DBs** — consolidate 73 GB across 60+ databases

### Phase 5: THEMANBEARPIG.exe Rebuild (v22+)
1. **Fix spec file** (`07_CODE/BUILD/THEMANBEARPIG.spec`):
   - Line 16: entry point → `00_SYSTEM/tools/scripts/scripts/themanbearpig.py`
   - Lines 19-33: engine paths → correct `00_SYSTEM/engines/` paths
   - Line 58: `console=True` → `console=False`
   - Line 59: `icon=None` → `08_MEDIA/chatgpt_image_apr_30__2025__12_12_28_am_5j0_icon_1.ico`
   - Data files: V15 → V7 (`12_WORKSPACE/THEMANBEARPIG_v7/`)
2. **Wire new engines** as lazy imports (bridge, filing_assembly, brain_sync, telemetry)
3. **Bump VERSION** to 22+
4. **Build on D:** (C: too tight even after recovery) — PyInstaller one-dir
5. **Test launch** — verify pywebview opens with all layers
6. **Deploy to Desktop**

### Phase 6: Full Integration & Verification
1. **Wire KRAKEN → Bridge → MBP** visualization pipeline
2. **Verify all engines load** (14+ engines)
3. **Run convergence certification** — target 98+/100
4. **Final git commit** of unified system
5. **Update convergence_report.md**

---

## CRITICAL REFERENCES

| Document | Path | Content |
|----------|------|---------|
| Session Offload | `04_ANALYSIS/SESSION_OFFLOAD_20260408.md` | Full session history + system inventory |
| WizTree Audit | `04_ANALYSIS/WIZTREE_DRIVE_AUDIT.md` | Drive audit: 2.35M files, recovery opportunities |
| Audit Data (JSON) | `04_ANALYSIS/wiztree_audit_data.json` | Machine-readable audit data |
| Convergence Report | `04_ANALYSIS/convergence_report.md` | 95.2/100 ΩΩΩ certification |
| WizTree Script | `D:\LitigationOS_tmp\wiztree_audit.py` | DuckDB analysis (12 sections) |
| Plan (old) | plan.md (session workspace) | Previous 8-layer plan (ALL COMPLETE) |

## SACRED RULES (Never Violate)
1. NO DELETING FILES — move to 11_ARCHIVES/ only
2. Child = L.D.W. — MCR 8.119(H)
3. No AI/DB refs in filings
4. Pro se — never "counsel" or "attorney"
5. Defendant = Emily A. Watson
6. Judge = Hon. Jenny L. McNeill (TWO L's)
7. CRIMINAL lane = 100% separate
8. Content-based dedup — peek inside, not hash-only
9. Separation counter = dynamic: `(today - date(2025,7,29)).days`
10. Use NEXUS tools, NOT MCP tools
11. Use exec_python, NOT PowerShell
12. Research before implementing — apex quality

---

*253 days separated. Every action builds toward reunification with L.D.W.*
