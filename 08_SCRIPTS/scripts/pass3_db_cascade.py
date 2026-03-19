"""PASS 3: Database Consolidation + Cascade Architecture."""
import sqlite3, os, json, shutil
from datetime import datetime

INVENTORY_DB = r"I:\DRIVE_ORG\drive_inventory.db"
LOG = r"I:\DRIVE_ORG\operations.log"
MAIN_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
CASCADE_OUT = r"I:\DRIVE_ORG\db_cascade.json"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def catalog_db(path):
    """Open a DB and catalog its tables/row counts."""
    try:
        uri = f"file:{path}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("PRAGMA query_only = ON")
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        result = {}
        for (tname,) in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM [{tname}]").fetchone()[0]
                result[tname] = count
            except:
                result[tname] = -1
        conn.close()
        return result
    except Exception as e:
        return {"ERROR": str(e)}

def run():
    log("=" * 60)
    log("PASS 3: DATABASE CONSOLIDATION + CASCADE")
    log("=" * 60)
    
    inv = sqlite3.connect(INVENTORY_DB)
    
    # Find all DB files > 1MB
    dbs = inv.execute("""
        SELECT path, size, drive FROM files 
        WHERE classification = 'DATABASE' AND size > 1000000
        AND path NOT LIKE '%session-state%'
        AND path NOT LIKE '%session-store%'
        AND path NOT LIKE '%drive_inventory%'
        ORDER BY size DESC
    """).fetchall()
    
    log(f"Found {len(dbs)} databases > 1MB")
    
    catalog = []
    for path, size, drive in dbs:
        log(f"  Cataloging: {os.path.basename(path)} ({size/1024/1024:.1f}MB) [{drive}]")
        tables = catalog_db(path)
        
        is_main = (path.lower() == MAIN_DB.lower())
        
        entry = {
            "path": path,
            "size_mb": round(size/1024/1024, 1),
            "drive": drive,
            "is_main": is_main,
            "table_count": len(tables),
            "tables": tables,
            "total_rows": sum(v for v in tables.values() if v > 0)
        }
        catalog.append(entry)
    
    # Classify into tiers
    tier1 = []  # Brain (main DB)
    tier2 = []  # Operational (inventory, warchest)
    tier3 = []  # Reference (authority stores, manifests)
    tier4 = []  # Archive/Redundant
    
    main_tables = set()
    
    for db in catalog:
        if "ERROR" in db["tables"]:
            tier4.append(db)
            continue
        
        if db["is_main"]:
            tier1.append(db)
            main_tables = set(db["tables"].keys())
            continue
        
        fname = os.path.basename(db["path"]).lower()
        
        # Check if this DB has tables that overlap with main
        db_tables = set(db["tables"].keys())
        overlap = db_tables & main_tables
        unique = db_tables - main_tables
        
        db["overlap_tables"] = list(overlap)
        db["unique_tables"] = list(unique)
        db["overlap_pct"] = round(len(overlap) / max(len(db_tables), 1) * 100)
        
        if "warchest" in fname or "pinnacle" in fname:
            if db["table_count"] > 5:
                tier2.append(db)
            else:
                tier4.append(db)
        elif "authority" in fname:
            tier3.append(db)
        elif "manifest" in fname or "catalog" in fname or "index" in fname:
            tier3.append(db)
        elif db["overlap_pct"] > 80:
            tier4.append(db)  # Mostly redundant
        elif len(unique) > 3:
            tier3.append(db)  # Has unique data
        else:
            tier4.append(db)
    
    # Output cascade
    cascade = {
        "generated": datetime.now().isoformat(),
        "tier1_brain": [{
            "path": d["path"], "size_mb": d["size_mb"],
            "tables": d["table_count"], "rows": d["total_rows"]
        } for d in tier1],
        "tier2_operational": [{
            "path": d["path"], "size_mb": d["size_mb"],
            "tables": d["table_count"], "rows": d["total_rows"],
            "unique_tables": d.get("unique_tables", [])
        } for d in tier2],
        "tier3_reference": [{
            "path": d["path"], "size_mb": d["size_mb"],
            "tables": d["table_count"], "rows": d["total_rows"],
            "unique_tables": d.get("unique_tables", [])
        } for d in tier3],
        "tier4_archive": [{
            "path": d["path"], "size_mb": d["size_mb"],
            "tables": d["table_count"]
        } for d in tier4]
    }
    
    with open(CASCADE_OUT, "w") as f:
        json.dump(cascade, f, indent=2)
    
    log(f"\nCASCADE ARCHITECTURE:")
    log(f"  Tier 1 (Brain): {len(tier1)} DBs — {sum(d['size_mb'] for d in tier1):.0f}MB")
    log(f"  Tier 2 (Operational): {len(tier2)} DBs — {sum(d['size_mb'] for d in tier2):.0f}MB")
    log(f"  Tier 3 (Reference): {len(tier3)} DBs — {sum(d['size_mb'] for d in tier3):.0f}MB")
    log(f"  Tier 4 (Archive/Redundant): {len(tier4)} DBs — {sum(d['size_mb'] for d in tier4):.0f}MB")
    
    # Report unique data in satellites
    log(f"\nUNIQUE DATA IN SATELLITES:")
    for db in tier2 + tier3:
        if db.get("unique_tables"):
            log(f"  {os.path.basename(db['path'])}: {len(db['unique_tables'])} unique tables")
            for t in db["unique_tables"][:5]:
                log(f"    - {t}: {db['tables'].get(t, '?')} rows")
    
    inv.close()
    log(f"\nPASS 3 COMPLETE — Cascade written to {CASCADE_OUT}")

if __name__ == "__main__":
    run()
