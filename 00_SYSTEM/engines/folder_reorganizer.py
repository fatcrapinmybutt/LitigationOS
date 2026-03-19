#!/usr/bin/env python3
"""
LITIGATIONOS FOLDER REORGANIZATION v1.0
Consolidates 55 top-level folders → 15 visible folders.
NO DELETIONS. Uses shutil.move (safe, same-drive = instant rename).

Target structure:
  00_SYSTEM/          - engines, DB, scripts
  01_CASE_FILES/      - case documents + data
  02_EVIDENCE/        - all evidence
  03_AUTHORITIES/     - legal authorities, caselaw, forms
  04_COURT_FILINGS/   - filed/draft court documents
  05_ANALYSIS/        - analysis reports, timelines
  06_ADVERSARY/       - adversary materials
  07_DATABASES/       - DB exports, CSV data
  08_TOOLS/           - apps, tools, extensions, compilers
  09_DOCUMENTS/       - general documents, specs, prompts
  10_ARCHIVES/        - archives + all UNPACKED content
  11_CONFIG/          - configuration files
  12_PROJECTS/        - project files, schematics
  THIS_IS_THE_ONE/    - critical final filing versions (stays)
  [hidden: .agents, .copilot, .github, .vscode — untouched]
"""
import os
import shutil
import time
from datetime import datetime

LOS = r'C:\Users\andre\LitigationOS'

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)

log("=" * 70)
log("  LITIGATIONOS REORGANIZATION v1.0")
log(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
log("=" * 70)

# Track moves
moved = 0
failed = 0
skipped = 0

def safe_move(src, dest_parent, dest_name=None):
    """Move src folder into dest_parent. If dest_name conflicts, merge."""
    global moved, failed, skipped
    
    if not os.path.exists(src):
        log(f"  [SKIP] Source not found: {src}")
        skipped += 1
        return
    
    os.makedirs(dest_parent, exist_ok=True)
    
    name = dest_name or os.path.basename(src)
    dest = os.path.join(dest_parent, name)
    
    if os.path.exists(dest):
        # Merge: move contents of src into existing dest
        log(f"  [MERGE] {os.path.basename(src)} → {os.path.relpath(dest, LOS)}")
        try:
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dest, item)
                if os.path.exists(d):
                    # Conflict — rename with suffix
                    base, ext = os.path.splitext(item)
                    d = os.path.join(dest, f"{base}_merged{ext}")
                try:
                    shutil.move(s, d)
                    moved += 1
                except Exception as e:
                    log(f"    [FAIL] {item}: {e}")
                    failed += 1
            # Remove empty src
            try:
                os.rmdir(src)
            except:
                pass
        except Exception as e:
            log(f"    [FAIL] Merge failed: {e}")
            failed += 1
    else:
        # Simple move (same drive = instant rename)
        try:
            shutil.move(src, dest)
            moved += 1
            log(f"  [MOVE] {os.path.basename(src)} → {os.path.relpath(dest, LOS)}")
        except Exception as e:
            log(f"  [FAIL] {os.path.basename(src)}: {e}")
            failed += 1

# ============================================================
# PHASE 1: Absorb all 28 UNPACKED folders into 10_ARCHIVES/_UNPACKED/
# ============================================================
log("\n[PHASE 1] Moving UNPACKED folders → 10_ARCHIVES/_UNPACKED/")

unpacked_dest = os.path.join(LOS, '10_ARCHIVES', '_UNPACKED')
os.makedirs(unpacked_dest, exist_ok=True)

unpacked_folders = [
    '20260302_014913_v3_1_SCAO_LIVE_DISCOVERY_EXPANSION_v3_1_plus_queue_UNPACKED',
    '20260302_1959_LITIGATIONOS_PIPERUNNER_EXECUTION_BUNDLE_UNPACKED',
    '20260302_2000_RUN_EVERYTHING_EXECUTABLES_UNPACKED',
    '20260302_2023_FORGE_RUNNER_PACK_UNPACKED',
    '20260302_2059_FORGE_FULLSPECTRUM_v5_UNPACKED',
    '20260302_2110_MI_SCAO_LIVE_DISCOVERY_CONTINUATION_v4_1_UNPACKED',
    '20260302_2300_MI_SCAO_LIVE_DISCOVERY_CONTINUATION_v4_2_UNPACKED',
    '20260303_0129_SCAO_LIVE_DISCOVERY_MEEK2_MEEK3_WINPACK_SEED_compiled_v2_UNPACKED',
    'CYCLEPACK_06_ADVERSARY_20260303_011222_UNPACKED',
    'CYCLEPACK_07_DATABASES_013443_UNPACKED',
    'CYCLEPACK_07_DATABASES_ADV2_20260303_015325_UNPACKED',
    'FORGE_FULLSPECTRUM_YAML_v4_UNPACKED',
    'GO_TO_WORK_WORKPACK_07DB_20260303_022353_UNPACKED',
    'INGEST_LitigationOS_20260302_run2_UNPACKED',
    'INGEST_LitigationOS_VECTOR_CASCADE_v20260303_run3_UNPACKED',
    'LitigationOS_ChatGPTExport_PartialParse_20260302_195853_UNPACKED',
    'LitigationOS_CourtInjection_v7_Pack_20260302_210825_UNPACKED',
    'LitigationOS_Execution_Run_EXEC_20260302_192501_UNPACKED',
    'LitigationOS_FactLedger_v2_20260302_201424_UNPACKED',
    'LitigationOS_FactLedger_v3_Convergence_20260302_202520_UNPACKED',
    'LitigationOS_FactLedger_v6_VerifiedPins_20260302_204913_UNPACKED',
    'LitigationOS_SCHEM_EXEC_20260302_193827_UNPACKED',
    'LitigationOS_USER_CANON_MERGE_v5_20260302_203743_UNPACKED',
    'MI_SCAO_LOCAL_INGEST_VECTOR_CASCADE_20260302_run1_UNPACKED',
    'MI_WEB_PIN_FOOTERS_TOP_FORMS_v20260302_UNPACKED',
    'QUOTELOCK_DEEP_07_DATABASES_20260303_020332_UNPACKED',
    'RUN6_INGEST_ALL_v20260302_RESULTS_ONLY_UNPACKED',
    'SCHEMATICS_UNPACKED',
]

for folder in unpacked_folders:
    safe_move(os.path.join(LOS, folder), unpacked_dest)

# ============================================================
# PHASE 2: Absorb straggler root folders
# ============================================================
log("\n[PHASE 2] Moving straggler folders")

# MI_AUTHORITY_FORMS → 03_AUTHORITIES
safe_move(os.path.join(LOS, 'MI_AUTHORITY_FORMS_PACKET_PLAYBOOK_DELTA999_v20260302'),
          os.path.join(LOS, '03_AUTHORITIES'))

# LITIGATIONOS_DATA → 01_CASE_FILES
safe_move(os.path.join(LOS, 'LITIGATIONOS_DATA'),
          os.path.join(LOS, '01_CASE_FILES'))

# ============================================================
# PHASE 3: Merge overlapping numbered folders
# ============================================================
log("\n[PHASE 3] Merging overlapping folders")

# 01_DATA → merge into 01_CASE_FILES/_DATA
safe_move(os.path.join(LOS, '01_DATA'),
          os.path.join(LOS, '01_CASE_FILES'), '_DATA')

# 12_TOOLS → merge into 08_TOOLS (rename 08_APPS first)
apps_dir = os.path.join(LOS, '08_APPS')
tools_dir = os.path.join(LOS, '08_TOOLS')
if os.path.exists(apps_dir) and not os.path.exists(tools_dir):
    log("  [RENAME] 08_APPS → 08_TOOLS")
    try:
        os.rename(apps_dir, tools_dir)
        moved += 1
    except Exception as e:
        log(f"  [FAIL] Rename 08_APPS: {e}")
        tools_dir = apps_dir  # fallback

safe_move(os.path.join(LOS, '12_TOOLS'), tools_dir, '_TOOLS')
safe_move(os.path.join(LOS, '14_EXTENSIONS'), tools_dir, '_EXTENSIONS')
safe_move(os.path.join(LOS, '15_COMPILER_PACKS'), tools_dir, '_COMPILER_PACKS')

# 16_DOCUMENTS → rename to 09_DOCUMENTS
docs_dir = os.path.join(LOS, '09_DOCUMENTS')
if os.path.exists(os.path.join(LOS, '16_DOCUMENTS')) and not os.path.exists(docs_dir):
    # First move 09_SPECS into 16_DOCUMENTS, then rename
    safe_move(os.path.join(LOS, '09_SPECS'),
              os.path.join(LOS, '16_DOCUMENTS'), '_SPECS')
    log("  [RENAME] 16_DOCUMENTS → 09_DOCUMENTS")
    try:
        os.rename(os.path.join(LOS, '16_DOCUMENTS'), docs_dir)
        moved += 1
    except Exception as e:
        log(f"  [FAIL] Rename 16_DOCUMENTS: {e}")

# 17_CONFIG → rename to 11_CONFIG
config_dir = os.path.join(LOS, '11_CONFIG')
if os.path.exists(os.path.join(LOS, '17_CONFIG')) and not os.path.exists(config_dir):
    # Move 11_PROMPTS into 17_CONFIG first
    safe_move(os.path.join(LOS, '11_PROMPTS'),
              os.path.join(LOS, '17_CONFIG'), '_PROMPTS')
    log("  [RENAME] 17_CONFIG → 11_CONFIG")
    try:
        os.rename(os.path.join(LOS, '17_CONFIG'), config_dir)
        moved += 1
    except Exception as e:
        log(f"  [FAIL] Rename 17_CONFIG: {e}")

# 13_PROJECTS → rename to 12_PROJECTS
proj_dir = os.path.join(LOS, '12_PROJECTS')
if os.path.exists(os.path.join(LOS, '13_PROJECTS')) and not os.path.exists(proj_dir):
    log("  [RENAME] 13_PROJECTS → 12_PROJECTS")
    try:
        os.rename(os.path.join(LOS, '13_PROJECTS'), proj_dir)
        moved += 1
    except Exception as e:
        log(f"  [FAIL] Rename 13_PROJECTS: {e}")

# ============================================================
# PHASE 4: Verify final structure
# ============================================================
log("\n[PHASE 4] Final structure verification")

final_dirs = []
for item in sorted(os.listdir(LOS)):
    path = os.path.join(LOS, item)
    if os.path.isdir(path):
        hidden = item.startswith('.')
        final_dirs.append((item, hidden))

visible = [d for d, h in final_dirs if not h]
hidden = [d for d, h in final_dirs if h]

log(f"\n  VISIBLE FOLDERS: {len(visible)}")
for d in visible:
    path = os.path.join(LOS, d)
    try:
        files = sum(1 for _ in os.scandir(path) if _.is_file())
        dirs = sum(1 for _ in os.scandir(path) if _.is_dir())
    except:
        files = dirs = 0
    log(f"    {d:50s} ({files}f, {dirs}d)")

log(f"\n  HIDDEN FOLDERS: {len(hidden)}")
for d in hidden:
    log(f"    {d}")

# Write log
log_path = os.path.join(LOS, '00_SYSTEM', 'REORG_LOG.txt')
with open(log_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))

log(f"\n{'='*70}")
log(f"  REORGANIZATION COMPLETE")
log(f"  Moves: {moved} | Failed: {failed} | Skipped: {skipped}")
log(f"  Visible folders: {len(visible)} | Hidden: {len(hidden)}")
log(f"  Log: {log_path}")
log(f"{'='*70}")
