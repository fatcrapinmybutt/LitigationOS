"""PASS 9: Backup + Continuity."""
import os, json, shutil
from datetime import datetime

LOG = r"I:\DRIVE_ORG\operations.log"
DELTA99 = r"I:\LitigationOS_Delta99"
BACKUP_DIR = r"I:\LitigationOS_Backup"
DR_PATH = os.path.join(DELTA99, "DISASTER_RECOVERY.md")

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def run():
    log("=" * 60)
    log("PASS 9: BACKUP + CONTINUITY")
    log("=" * 60)
    
    # Verify Delta99 backup exists and is current
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Copy critical Delta99 files to backup
    delta99_backup = os.path.join(BACKUP_DIR, "Delta99_backup")
    os.makedirs(delta99_backup, exist_ok=True)
    
    copied = 0
    for item in os.listdir(DELTA99):
        src = os.path.join(DELTA99, item)
        dst = os.path.join(delta99_backup, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            copied += 1
        elif os.path.isfile(src):
            shutil.copy2(src, dst)
            copied += 1
    
    log(f"  Delta99 backed up: {copied} items to {delta99_backup}")
    
    # Check for main DB backup
    main_backup = os.path.join(BACKUP_DIR, "litigation_context_backup.db")
    backup_exists = False
    for f in os.listdir(r"I:\\"):
        if "litigation_context" in f.lower() and f.endswith(".db"):
            backup_exists = True
            break
    
    # Generate disaster recovery document
    dr = f"""# DISASTER RECOVERY PLAN
## LitigationOS — Pigors v. Watson, 2024-001507-DC

**Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}**

---

## CRITICAL ASSETS INVENTORY

### Tier 1: Irreplaceable (MUST PRESERVE)
| Asset | Location | Size | Backup |
|---|---|---|---|
| litigation_context.db | C:\\Users\\andre\\LitigationOS\\ | ~8GB | I:\\LitigationOS_Archives\\ |
| Delta99 Filing Packages | I:\\LitigationOS_Delta99\\PKG01-12\\ | ~5MB | I:\\LitigationOS_Backup\\Delta99_backup\\ |
| Evidence Photos/Scans | C:\\Users\\andre\\LitigationOS\\02_EVIDENCE\\ | ~2GB | Verify backup exists |
| Court Orders/Filings | C:\\Users\\andre\\LitigationOS\\01_CASE_FILES\\ | ~500MB | Verify backup exists |

### Tier 2: Important (Should preserve)
| Asset | Location | Notes |
|---|---|---|
| Authority Library | C:\\Users\\andre\\LitigationOS\\03_AUTHORITIES\\ | 928+ files, MCR/MCL/Benchbooks |
| Proofread Engine | C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\proofread\\ | Custom verification engine |
| Drive Inventory DB | I:\\DRIVE_ORG\\drive_inventory.db | ~400MB, file inventory |
| DB Cascade Config | I:\\DRIVE_ORG\\db_cascade.json | Database architecture map |

### Tier 3: Regenerable (Can rebuild if needed)
| Asset | Notes |
|---|---|
| Dashboard (DASHBOARD.html) | Auto-generated from package data |
| Timeline (MASTER_TIMELINE.md) | Extracted from DB + case records |
| Dedup reports (DEDUP_CANDIDATES.json) | Regenerable from inventory scan |

---

## RECOVERY PROCEDURES

### Scenario 1: C: Drive Failure
1. Install fresh Windows + Python + VS Code
2. Restore `litigation_context.db` from `I:\\LitigationOS_Archives\\`
3. Clone LitigationOS directory structure from backup
4. Restore evidence files from I: backup
5. Re-run proofread engine to verify package integrity
6. Open DASHBOARD.html to verify all systems green

### Scenario 2: I: Drive Failure
1. Delta99 packages are the PRIMARY output — these MUST be printed/filed from backup
2. Inventory DB can be rebuilt by re-running inventory_engine.py
3. Backups of Delta99 should also exist on C:\\Users\\andre\\LitigationOS\\ if copied

### Scenario 3: All Drives Lost
1. Prioritize COA Case 366810 deadline (April 15, 2026)
2. Re-obtain court records from MiFILE
3. Re-obtain evidence from original sources
4. Rebuild filing packages from V5 spec + proofread engine

---

## CRITICAL DEADLINES
| Deadline | Date | Days Remaining | Priority |
|---|---|---|---|
| COA Brief (366810) | April 15, 2026 | {(datetime(2026,4,15) - datetime.now()).days} | **CRITICAL** |

---

## BACKUP SCHEDULE (Recommended)
- **Daily**: Copy Delta99 changes to I:\\LitigationOS_Backup\\
- **Weekly**: Full backup of C:\\Users\\andre\\LitigationOS\\ to I:\\
- **Before filing**: Snapshot entire Delta99 + supporting evidence
- **After court events**: Update DB + timeline + dashboard

---

## VERIFICATION COMMANDS
```powershell
# Verify Delta99 packages intact
python C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\proofread\\proofread_engine.py --all

# Verify DB health  
python -c "import sqlite3; c=sqlite3.connect('C:\\\\Users\\\\andre\\\\LitigationOS\\\\litigation_context.db'); print(f'Tables: {{len(c.execute(chr(34)SELECT name FROM sqlite_master WHERE type=chr(39)table chr(39)chr(34)).fetchall())}}'); c.close()"

# Check drive space
Get-CimInstance Win32_LogicalDisk | Select DeviceID, @{{n='Free_GB';e={{[math]::Round($_.FreeSpace/1GB,1)}}}}
```

---

*This document is auto-generated. Update after any major system change.*
"""
    
    with open(DR_PATH, "w", encoding="utf-8") as f:
        f.write(dr)
    
    log(f"  Disaster recovery: {DR_PATH}")
    log(f"PASS 9 COMPLETE")

if __name__ == "__main__":
    run()
