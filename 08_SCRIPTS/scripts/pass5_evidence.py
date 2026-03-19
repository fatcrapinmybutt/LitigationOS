"""PASS 5: Evidence Integrity + Gap Analysis for Delta99 packages."""
import os, json, re, sqlite3
from datetime import datetime

DELTA99 = r"I:\LitigationOS_Delta99"
MAIN_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
LOG = r"I:\DRIVE_ORG\operations.log"
INVENTORY_DB = r"I:\DRIVE_ORG\drive_inventory.db"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def extract_exhibit_refs(text):
    """Extract exhibit references from filing text."""
    refs = set()
    # Match Exhibit A, Exhibit 1, Ex. A-1, etc
    for m in re.finditer(r'(?:Exhibit|Ex\.?)\s+([A-Z0-9][\w-]*)', text, re.IGNORECASE):
        refs.add(m.group(1).upper())
    return refs

def find_exhibit_files(pkg_dir):
    """Find actual exhibit files in a package directory."""
    exhibit_files = {}
    for root, dirs, files in os.walk(pkg_dir):
        for f in files:
            fl = f.lower()
            if 'exhibit' in fl or fl.startswith('ex_') or fl.startswith('ex-'):
                path = os.path.join(root, f)
                exhibit_files[f] = {"path": path, "size": os.path.getsize(path)}
    return exhibit_files

def run():
    log("=" * 60)
    log("PASS 5: EVIDENCE INTEGRITY + GAP ANALYSIS")
    log("=" * 60)
    
    # Get exhibit authentication data from main DB
    try:
        uri = f"file:{MAIN_DB}?mode=ro&immutable=1"
        db = sqlite3.connect(uri, uri=True)
        db.execute("PRAGMA query_only = ON")
        auth_count = db.execute("SELECT COUNT(*) FROM exhibit_authentication").fetchone()[0]
        log(f"  Exhibit authentication entries: {auth_count:,}")
    except:
        auth_count = 0
        log("  WARNING: Could not access exhibit_authentication")
    
    # Get evidence files from inventory
    inv = sqlite3.connect(INVENTORY_DB)
    evidence_files = inv.execute("""
        SELECT path, filename, size FROM files 
        WHERE classification = 'EVIDENCE'
        AND (extension IN ('pdf', 'png', 'jpg', 'jpeg', 'tif', 'tiff'))
        ORDER BY filename
    """).fetchall()
    log(f"  Evidence files in inventory: {len(evidence_files):,}")
    
    # Build evidence lookup
    evidence_lookup = {}
    for path, fname, size in evidence_files:
        key = fname.lower()
        if key not in evidence_lookup:
            evidence_lookup[key] = []
        evidence_lookup[key].append({"path": path, "size": size})
    
    # Process each package
    packages = sorted([d for d in os.listdir(DELTA99) if d.startswith("PKG") and os.path.isdir(os.path.join(DELTA99, d))])
    
    overall = {
        "generated": datetime.now().isoformat(),
        "packages": {},
        "total_cited_exhibits": 0,
        "total_physical_files": 0,
        "total_gaps": 0
    }
    
    for pkg in packages:
        pkg_dir = os.path.join(DELTA99, pkg)
        log(f"\n  {pkg}:")
        
        # Read all text files in package
        all_text = ""
        file_count = 0
        for f in os.listdir(pkg_dir):
            fp = os.path.join(pkg_dir, f)
            if os.path.isfile(fp) and f.endswith(('.md', '.txt', '.json', '.csv')):
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                        all_text += fh.read() + "\n"
                    file_count += 1
                except:
                    pass
        
        # Extract exhibit references
        cited_exhibits = extract_exhibit_refs(all_text)
        physical_files = find_exhibit_files(pkg_dir)
        
        # Check for EXHIBITS_INDEX
        exhibits_index_path = os.path.join(pkg_dir, "EXHIBITS_INDEX.md")
        has_index = os.path.exists(exhibits_index_path)
        
        # Gap analysis
        gaps = []
        for ex in cited_exhibits:
            # Check if any physical file matches
            found = False
            for fname in physical_files:
                if ex.lower() in fname.lower():
                    found = True
                    break
            if not found:
                gaps.append(ex)
        
        pkg_info = {
            "files": file_count,
            "cited_exhibits": sorted(cited_exhibits),
            "physical_files": list(physical_files.keys()),
            "has_exhibit_index": has_index,
            "gaps": gaps,
            "status": "COMPLETE" if len(gaps) == 0 else f"GAPS: {len(gaps)}"
        }
        overall["packages"][pkg] = pkg_info
        overall["total_cited_exhibits"] += len(cited_exhibits)
        overall["total_physical_files"] += len(physical_files)
        overall["total_gaps"] += len(gaps)
        
        log(f"    Files: {file_count} | Cited: {len(cited_exhibits)} | Physical: {len(physical_files)} | Gaps: {len(gaps)} | {pkg_info['status']}")
    
    # Write evidence map
    map_path = os.path.join(DELTA99, "EVIDENCE_MAP.json")
    with open(map_path, "w") as f:
        json.dump(overall, f, indent=2)
    
    log(f"\n{'='*60}")
    log(f"PASS 5 COMPLETE")
    log(f"  Total cited exhibits: {overall['total_cited_exhibits']}")
    log(f"  Total physical files: {overall['total_physical_files']}")
    log(f"  Total gaps: {overall['total_gaps']}")
    log(f"  Evidence map: {map_path}")
    log(f"{'='*60}")
    
    try:
        db.close()
    except:
        pass
    inv.close()

if __name__ == "__main__":
    run()
