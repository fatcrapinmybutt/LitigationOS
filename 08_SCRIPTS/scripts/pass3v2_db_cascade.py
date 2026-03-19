"""PASS 3 v2: Fast DB cascade - skip giant backup DBs, use signal_timeout."""
import sqlite3, os, json
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

def catalog_db(path, timeout=30):
    """Open a DB and catalog tables. Skip row counts for huge DBs."""
    try:
        uri = f"file:{path}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True, timeout=timeout)
        conn.execute("PRAGMA query_only = ON")
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        result = {}
        size = os.path.getsize(path)
        for (tname,) in tables:
            if size > 500_000_000:  # >500MB: skip row counts
                result[tname] = -1
            else:
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
    log("PASS 3 v2: DATABASE CONSOLIDATION + CASCADE")
    log("=" * 60)
    
    inv = sqlite3.connect(INVENTORY_DB)
    
    dbs = inv.execute("""
        SELECT path, size, drive FROM files 
        WHERE classification = 'DATABASE' AND size > 1000000
        AND path NOT LIKE '%session-state%'
        AND path NOT LIKE '%session-store%'
        AND path NOT LIKE '%drive_inventory%'
        AND path NOT LIKE '%DEDUP_ARCHIVE%'
        ORDER BY size DESC
    """).fetchall()
    
    log(f"Found {len(dbs)} databases > 1MB")
    
    # Known schema for main DB (skip cataloging)
    MAIN_DB_INFO = {
        "path": MAIN_DB,
        "size_mb": 7990.1,
        "drive": "C_LitigationOS",
        "is_main": True,
        "table_count": 376,
        "total_rows": 700000,
        "tables": {}  # Known from prior analysis
    }
    
    catalog = [MAIN_DB_INFO]
    main_tables_known = set()  # We'll populate from smaller DBs comparison
    
    # Get main DB table names only (fast)
    try:
        uri = f"file:{MAIN_DB}?mode=ro&immutable=1"
        mc = sqlite3.connect(uri, uri=True)
        mc.execute("PRAGMA query_only = ON")
        main_tables_known = set(r[0] for r in mc.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
        mc.close()
        MAIN_DB_INFO["tables"] = {t: -1 for t in main_tables_known}
        log(f"  Main DB: {len(main_tables_known)} tables")
    except Exception as e:
        log(f"  Main DB table list error: {e}")
    
    for path, size, drive in dbs:
        if path.lower() == MAIN_DB.lower():
            continue
        
        fname = os.path.basename(path)
        
        # Skip known backup of main (exact copy)
        if "backup" in fname.lower() and size > 5_000_000_000:
            catalog.append({
                "path": path, "size_mb": round(size/1024/1024, 1),
                "drive": drive, "is_main": False,
                "table_count": 376, "total_rows": 700000,
                "tables": {"_BACKUP_OF_MAIN": -1},
                "overlap_pct": 100, "unique_tables": [], "overlap_tables": []
            })
            log(f"  SKIP (backup): {fname} ({size/1024/1024:.0f}MB)")
            continue
        
        log(f"  Cataloging: {fname} ({size/1024/1024:.1f}MB) [{drive}]")
        tables = catalog_db(path, timeout=15)
        
        db_tables = set(tables.keys()) - {"ERROR"}
        overlap = db_tables & main_tables_known
        unique = db_tables - main_tables_known
        
        entry = {
            "path": path,
            "size_mb": round(size/1024/1024, 1),
            "drive": drive,
            "is_main": False,
            "table_count": len(tables),
            "tables": tables,
            "total_rows": sum(v for v in tables.values() if isinstance(v, int) and v > 0),
            "overlap_tables": list(overlap)[:10],
            "unique_tables": list(unique),
            "overlap_pct": round(len(overlap) / max(len(db_tables), 1) * 100)
        }
        catalog.append(entry)
    
    # Classify into tiers
    tier1, tier2, tier3, tier4 = [], [], [], []
    
    for db in catalog:
        if db.get("is_main"):
            tier1.append(db)
            continue
        
        if "ERROR" in db.get("tables", {}):
            tier4.append(db)
            continue
        
        fname = os.path.basename(db["path"]).lower()
        overlap_pct = db.get("overlap_pct", 0)
        unique = db.get("unique_tables", [])
        
        if "_BACKUP_OF_MAIN" in db.get("tables", {}):
            tier4.append(db)
        elif "warchest" in fname or "pinnacle" in fname:
            tier2.append(db) if db["table_count"] > 3 else tier4.append(db)
        elif "authority" in fname and len(unique) > 0:
            tier3.append(db)
        elif "master_index" in fname or "file_catalog" in fname:
            tier3.append(db)
        elif "manifest" in fname or "catalog" in fname:
            tier3.append(db)
        elif overlap_pct > 80:
            tier4.append(db)
        elif len(unique) > 2:
            tier3.append(db)
        else:
            tier4.append(db)
    
    cascade = {
        "generated": datetime.now().isoformat(),
        "tier1_brain": [{"path": d["path"], "size_mb": d["size_mb"], "tables": d["table_count"]} for d in tier1],
        "tier2_operational": [{"path": d["path"], "size_mb": d["size_mb"], "tables": d["table_count"], "unique_tables": d.get("unique_tables", [])} for d in tier2],
        "tier3_reference": [{"path": d["path"], "size_mb": d["size_mb"], "tables": d["table_count"], "unique_tables": d.get("unique_tables", [])} for d in tier3],
        "tier4_archive": [{"path": d["path"], "size_mb": d["size_mb"], "tables": d["table_count"]} for d in tier4],
        "stats": {
            "total_dbs": len(catalog),
            "total_size_gb": round(sum(d["size_mb"] for d in catalog)/1024, 1),
            "tier4_deletable_gb": round(sum(d["size_mb"] for d in tier4)/1024, 1)
        }
    }
    
    with open(CASCADE_OUT, "w") as f:
        json.dump(cascade, f, indent=2)
    
    log(f"\nCASCADE ARCHITECTURE:")
    log(f"  Tier 1 (Brain): {len(tier1)} — {sum(d['size_mb'] for d in tier1):.0f}MB")
    log(f"  Tier 2 (Operational): {len(tier2)} — {sum(d['size_mb'] for d in tier2):.0f}MB")
    log(f"  Tier 3 (Reference): {len(tier3)} — {sum(d['size_mb'] for d in tier3):.0f}MB")
    log(f"  Tier 4 (Archive): {len(tier4)} — {sum(d['size_mb'] for d in tier4):.0f}MB")
    
    log(f"\nUNIQUE DATA IN SATELLITES:")
    for db in tier2 + tier3:
        unique = db.get("unique_tables", [])
        if unique:
            log(f"  {os.path.basename(db['path'])}: {len(unique)} unique tables")
            for t in unique[:5]:
                rows = db["tables"].get(t, "?")
                log(f"    - {t}: {rows} rows")
    
    log(f"\nARCHIVE/REDUNDANT (safe to delete after verification):")
    for db in tier4[:15]:
        log(f"  {db['size_mb']:.0f}MB | {os.path.basename(db['path'])}")
    
    inv.close()
    log(f"\nPASS 3 COMPLETE — {CASCADE_OUT}")

if __name__ == "__main__":
    run()
