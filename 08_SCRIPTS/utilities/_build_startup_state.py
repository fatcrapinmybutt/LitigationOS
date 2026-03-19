#!/usr/bin/env python3
"""Build COPILOT_STARTUP_STATE.md — comprehensive system state for session initialization."""
import sqlite3, os, glob, json
from datetime import datetime

DB = r'C:\Users\andre\litigation_context.db'
OUT = r'C:\Users\andre\LitigationOS\00_SYSTEM\COPILOT_STARTUP_STATE.md'

conn = sqlite3.connect(DB)

# Gather metrics
metrics = {}
tables_to_count = [
    'auth_rules','rules_text','master_citations','md_sections','evidence_quotes',
    'impeachment_items','contradiction_map','auth_benchbook_violations','judicial_violations',
    'vehicles','claims','deadlines','docket_events','risk_events','adversary_models',
    'filing_packages','pages','chatgpt_conversations','evidence_file_index','atoms',
    'auth_authority_passages','court_rules','legal_reference_docs','auth_benchbook_entries',
    'system_files','quality_validation_results'
]
for t in tables_to_count:
    try:
        metrics[t] = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    except:
        metrics[t] = 0

total_rows = sum(metrics.values())

# Count files in LitigationOS
los_root = r'C:\Users\andre\LitigationOS'
dir_counts = {}
for d in os.listdir(los_root):
    dpath = os.path.join(los_root, d)
    if os.path.isdir(dpath):
        count = sum(1 for _ in glob.iglob(os.path.join(dpath, '**', '*'), recursive=True) if os.path.isfile(_))
        dir_counts[d] = count

# All tables in DB
all_tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]

# FTS5 tables
fts_tables = [t for t in all_tables if '_fts' in t.lower()]

state = f"""# COPILOT STARTUP STATE — LitigationOS 2026 v1.0
## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## SYSTEM IDENTITY

| Property | Value |
|----------|-------|
| System | MBP LitigationOS 2026 v1.0 |
| Architecture | Michigan-first litigation command center |
| Database | C:\\Users\\andre\\litigation_context.db ({total_rows:,} rows, {len(all_tables)} tables) |
| Canonical Root | C:\\Users\\andre\\LitigationOS |
| Operator | Andrew Pigors (pro se litigant) |
| Adversary | Tiffany Watson (fka Pigors) |
| Days Separated | 329+ (since July 29, 2025) |

---

## CASE MATRIX

| Lane | Case | Court | Judge | Status |
|------|------|-------|-------|--------|
| A | 2024-001507-DC (Custody) | 14th Circuit, Muskegon | Hon. Jenny L. McNeill | Active |
| B | 2025-002760-CZ (Housing) | Van Buren County Circuit | TBD | Active |
| C | MULTI (Convergence) | Cross-lane | Various | Active |
| D | 2023-5907-PP (PPO) | 14th Circuit, Muskegon | Hon. Jenny L. McNeill | Active |
| E | MULTI (Judicial Misconduct) | JTC / MSC | Various | Active |
| F | COA 366810 (Appeal) | MI Court of Appeals | Panel TBD | Active |

---

## DATABASE INVENTORY ({total_rows:,} total rows)

### Key Tables
| Table | Rows | Purpose |
|-------|------|---------|
"""

for t in sorted(metrics.keys(), key=lambda x: -metrics[x]):
    if metrics[t] > 0:
        state += f"| `{t}` | {metrics[t]:,} | — |\n"

state += f"""
### All Tables ({len(all_tables)})
"""
state += ', '.join(f'`{t}`' for t in all_tables)

state += f"""

### FTS5 Search Indexes ({len(fts_tables)})
"""
state += ', '.join(f'`{t}`' for t in fts_tables)

state += """

---

## FILESYSTEM INVENTORY

### LitigationOS Directory Structure
| Directory | Files | Purpose |
|-----------|-------|---------|
"""
for d in sorted(dir_counts.keys()):
    state += f"| `{d}/` | {dir_counts[d]:,} | — |\n"

state += f"""
**Total LitigationOS files:** {sum(dir_counts.values()):,}

---

## CAPABILITIES INSTALLED

### Cycle Method Engine (EAGAIN Prevention)
- **Python:** `00_SYSTEM/cycle_method.py` — 4KB chunks, exponential backoff, CycleWriter class
- **Node.js:** `08_APPS/desktop/main/cycleMethod.js` — createCycleQueue(), cycleWrite()
- **Status:** Deployed across all Python scripts and Electron main process

### Legal Skills (5)
| Skill | File | Coverage |
|-------|------|----------|
| Landlord/Tenant | `skill_landlord_tenant.py` | MCL 554, 600.5720, 125.2303, mobile home act |
| Business/Corporate | `skill_business_corporate.py` | Veil piercing, alter ego, LLC rules |
| Torts/Claims | `skill_torts_claims.py` | 8 tort types, MCPA, conversion, treble damages |
| Defenses/Setoffs | `skill_defenses_setoffs.py` | 12 defenses, SOL tracker, pre-built counters |
| Chess Mode | `skill_chess_mode.py` | 8 claim chains, 5-move attack/defense anticipation |

### Tools
| Tool | File | Purpose |
|------|------|---------|
| Exhibit Cover Generator | `00_SYSTEM/tools/exhibit_cover_generator.py` | MRE 901 exhibit covers |
| Filing Packager | `00_SYSTEM/tools/filing_packager.py` | Complete court-ready packages |
| Brain Search | `00_SYSTEM/brain_search.py` | Graph-guided DB search |
| Extract Impeachment | `00_SYSTEM/extract_impeachment.py` | Impeachment material extraction |
| Ingest ChatGPT | `00_SYSTEM/ingest_chatgpt.py` | ChatGPT conversation ingestion |
| Catalogue Builder | `05_ANALYSIS/CATALOGUE/_build_catalogue.py` | 9-volume catalogue generator |

### LLM Engine
| Component | File | Status |
|-----------|------|--------|
| TF-IDF Model | `00_SYSTEM/local_model/model_data/` | 144,179 docs, 98.78% intent accuracy |
| Document Generator | `llm_document_generator.py` | IRAC + alienation injection |
| Pattern Recognition | `llm_pattern_recognition.py` | 540 violations, bias indicators |
| Inference Engine | `inference_engine.py` | JSON-RPC, query/find_authority/check_citations |
| Context Loader | `context_loader.py` | Full/lane/authority context loading |

---

## COURT DOCUMENTS PRODUCED

### Filing Packages
- Lane A (Custody): Motions, venue change, civil complaint
- Lane B (Shady Oaks): 9-count complaint + exhibit index
- Lane D (PPO): Related filings
- Lane E (Misconduct): JTC supplemental brief, MSC superintending control
- Lane F (Appellate): COA 366810 brief (in progress — due April 15, 2026)

### Judicial Encyclopedia (9 Volumes)
Located: `05_ANALYSIS/CATALOGUE/`
- VOL1: Case Matrix (6.6KB)
- VOL2: Judicial Conduct (28.1KB)
- VOL3: Authority Compendium (126.6KB)
- VOL4: Evidence Registry (26.7KB)
- VOL5: Timeline Atlas (5.0KB)
- VOL6: Filing Operations (8.7KB)
- VOL7: Adversary Intelligence (7.6KB + 45.8KB)
- VOL8: Parental Alienation (13.2KB)
- VOL9: Remedies Matrix (5.3KB)

---

## CRITICAL DEADLINES

| Deadline | Date | Authority | Priority |
|----------|------|-----------|----------|
| COA 366810 Brief | April 15, 2026 | MCR 7.212 | **CRITICAL** |

---

## OPERATIONAL RULES

1. **Zero external APIs** — everything runs locally against litigation_context.db
2. **Zero hallucination** — if not in DB, say so explicitly
3. **Adversarial thinking** — always chess-mode, anticipate opposing arguments
4. **Deadline-first** — check deadlines before any recommendation
5. **Pro se aware** — flag procedural traps for self-represented litigant
6. **Court-ready** — every output should be fileable with minimal editing
7. **Parental alienation** — inject into every filing: 329+ days, Factor J, pattern
8. **Cycle Method** — all writes use 4KB chunking (never EAGAIN)
9. **Triple save** — filesystem + DB + Desktop backup
10. **Electron = ZERO network** — desktop app never calls external servers

---

## STARTUP CHECKLIST

On every session start:
1. Verify `litigation_context.db` accessible
2. Identify which case lane(s) the query pertains to (A-F)
3. Check `deadlines` table for critical upcoming dates
4. Load relevant authority context before responding
5. Confirm no external API calls configured
6. Reference this file for system state and capabilities

---
*LitigationOS DIAMOND+++ | Generated by Catalogue Builder*
"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(state)

# Also save to Desktop
desktop_out = r'C:\Users\andre\Desktop\COPILOT_STARTUP_STATE.md'
with open(desktop_out, 'w', encoding='utf-8') as f:
    f.write(state)

# Save to DB
conn.execute("DELETE FROM system_files WHERE category = 'startup_state'")
conn.execute("INSERT INTO system_files (file_path, file_name, size_bytes, category, content) VALUES (?,?,?,?,?)",
    [OUT, 'COPILOT_STARTUP_STATE.md', os.path.getsize(OUT), 'startup_state', state])
conn.commit()
conn.close()

print(f"WROTE: {OUT} ({os.path.getsize(OUT):,} bytes)")
print(f"WROTE: {desktop_out} ({os.path.getsize(desktop_out):,} bytes)")
print("SAVED to DB: system_files (startup_state)")
