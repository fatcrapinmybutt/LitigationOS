"""
DELTA9 CHECKPOINT 18: Export harvested data into per-case folder structure.
Offloads fact_atoms, citation_atoms, judicial_findings, action_scores, and 
filing manifests into Lane A / Lane B / Lane C subfolders.
"""
import sqlite3, json, os, csv
from datetime import datetime
from pathlib import Path

DB = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db")
CASE_ROOT = Path(r"C:\Users\andre\LitigationOS\01_CASE_FILES")
CKPT_ROOT = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\checkpoints")
TS = datetime.now().strftime("%Y%m%d_%H%M%S")

LANES = {
    "A": {
        "dir": "LANE_A_WATSON_CUSTODY",
        "judges": ["McNeill"],
        "action_prefix": "A",
        "desc": "Watson/Custody - 2024-001507-DC, 2023-5907-PP"
    },
    "B": {
        "dir": "LANE_B_SHADY_OAKS_HOUSING", 
        "judges": ["Hoopes"],
        "action_prefix": "B",
        "desc": "Shady Oaks/Housing - 2025-002760-CZ"
    },
    "C": {
        "dir": "LANE_C_CONVERGENCE_COUNTY",
        "judges": ["McNeill", "Hoopes"],
        "action_prefix": "C",
        "desc": "Convergence/County - 14th Circuit, Muskegon County"
    }
}

def ensure_dirs():
    """Create lane folder structure."""
    for lane_id, cfg in LANES.items():
        base = CASE_ROOT / cfg["dir"]
        for sub in ["evidence", "citations", "judicial", "analysis", "filings"]:
            d = base / sub
            d.mkdir(parents=True, exist_ok=True)
            print(f"  [OK] {d}")

def export_fact_atoms(db):
    """Export fact_atoms per lane."""
    print("\n=== EXPORTING FACT ATOMS ===")
    # Get all fact atoms with their file's meek_lane
    rows = db.execute("""
        SELECT fa.id, fa.file_id, fa.atom_type, fa.content, fa.confidence,
               fa.source_page, f.meek_lane, f.full_path
        FROM fact_atoms fa
        LEFT JOIN files f ON fa.file_id = f.id
    """).fetchall()
    
    cols = ["id", "file_id", "atom_type", "content", "confidence", "source_page", "meek_lane", "source_path"]
    
    lane_data = {"A": [], "B": [], "C": [], "UNCLASSIFIED": []}
    for r in rows:
        lane = r[6] if r[6] in lane_data else "UNCLASSIFIED"
        lane_data[lane].append(dict(zip(cols, r)))
    
    for lane_id, cfg in LANES.items():
        out = CASE_ROOT / cfg["dir"] / "evidence" / f"fact_atoms_{TS}.jsonl"
        data = lane_data.get(lane_id, [])
        with open(out, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  Lane {lane_id}: {len(data)} fact atoms -> {out.name}")
    
    # Unclassified go to Lane C (convergence catches all)
    unc = lane_data.get("UNCLASSIFIED", [])
    if unc:
        out = CASE_ROOT / LANES["C"]["dir"] / "evidence" / f"fact_atoms_unclassified_{TS}.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            for item in unc:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  Unclassified: {len(unc)} fact atoms -> convergence")

def export_citation_atoms(db):
    """Export citation_atoms per lane (sampled - full set too large for JSONL)."""
    print("\n=== EXPORTING CITATION ATOMS ===")
    
    total = db.execute("SELECT COUNT(*) FROM citation_atoms").fetchone()[0]
    print(f"  Total citation atoms: {total:,}")
    
    # Export citation summary stats per type, per lane
    for lane_id, cfg in LANES.items():
        # Get citations linked to files in this lane
        stats = db.execute("""
            SELECT ca.citation_type, COUNT(*) as cnt
            FROM citation_atoms ca
            JOIN files f ON ca.file_id = f.id
            WHERE f.meek_lane = ?
            GROUP BY ca.citation_type
            ORDER BY cnt DESC
        """, (lane_id,)).fetchall()
        
        out = CASE_ROOT / cfg["dir"] / "citations" / f"citation_summary_{TS}.json"
        summary = {
            "lane": lane_id,
            "description": cfg["desc"],
            "exported_at": TS,
            "total_citations": sum(s[1] for s in stats),
            "by_type": {s[0]: s[1] for s in stats}
        }
        with open(out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"  Lane {lane_id}: {summary['total_citations']:,} citations -> {out.name}")
        
        # Export unique citation texts (deduplicated)
        unique_cites = db.execute("""
            SELECT DISTINCT ca.citation_type, ca.citation_text
            FROM citation_atoms ca
            JOIN files f ON ca.file_id = f.id
            WHERE f.meek_lane = ?
            ORDER BY ca.citation_type, ca.citation_text
        """, (lane_id,)).fetchall()
        
        out2 = CASE_ROOT / cfg["dir"] / "citations" / f"unique_citations_{TS}.jsonl"
        with open(out2, "w", encoding="utf-8") as f:
            for ct, txt in unique_cites:
                f.write(json.dumps({"type": ct, "text": txt}) + "\n")
        print(f"  Lane {lane_id}: {len(unique_cites)} unique citation texts")

def export_judicial_findings(db):
    """Export judicial_findings per lane."""
    print("\n=== EXPORTING JUDICIAL FINDINGS ===")
    
    for lane_id, cfg in LANES.items():
        judges = cfg["judges"]
        placeholders = ",".join("?" * len(judges))
        rows = db.execute(f"""
            SELECT id, judge, finding_type, description, severity, 
                   source_file_id, canon_ref, mcr_ref, confidence, agent_id
            FROM judicial_findings
            WHERE judge IN ({placeholders})
            ORDER BY severity DESC
        """, judges).fetchall()
        
        cols = ["id", "judge", "finding_type", "description", "severity",
                "source_file_id", "canon_ref", "mcr_ref", "confidence", "agent_id"]
        
        out = CASE_ROOT / cfg["dir"] / "judicial" / f"judicial_findings_{TS}.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(dict(zip(cols, r)), ensure_ascii=False) + "\n")
        
        # Summary stats
        summary = {
            "lane": lane_id,
            "judges": judges,
            "total_findings": len(rows),
            "by_type": {},
            "by_severity": {"critical_8plus": 0, "high_6plus": 0, "medium_4plus": 0, "low": 0}
        }
        for r in rows:
            ft = r[2] or "unknown"
            summary["by_type"][ft] = summary["by_type"].get(ft, 0) + 1
            sev = r[4] or 0
            if sev >= 8: summary["by_severity"]["critical_8plus"] += 1
            elif sev >= 6: summary["by_severity"]["high_6plus"] += 1
            elif sev >= 4: summary["by_severity"]["medium_4plus"] += 1
            else: summary["by_severity"]["low"] += 1
        
        out2 = CASE_ROOT / cfg["dir"] / "judicial" / f"judicial_summary_{TS}.json"
        with open(out2, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"  Lane {lane_id} ({', '.join(judges)}): {len(rows)} findings -> {out.name}")

def export_action_scores(db):
    """Export action_scores per lane."""
    print("\n=== EXPORTING ACTION SCORES ===")
    
    for lane_id, cfg in LANES.items():
        rows = db.execute("""
            SELECT action_id, lane, evidence_score, authority_score,
                   vulnerability_score, readiness_score, composite_score,
                   gap_count, updated_by, damages_json
            FROM action_scores
            WHERE lane = ?
            ORDER BY composite_score DESC
        """, (lane_id,)).fetchall()
        
        cols = ["action_id", "lane", "evidence_score", "authority_score",
                "vulnerability_score", "readiness_score", "composite_score",
                "gap_count", "updated_by", "damages_json"]
        
        actions = []
        for r in rows:
            d = dict(zip(cols, r))
            if d["damages_json"]:
                try:
                    d["damages"] = json.loads(d["damages_json"])
                except:
                    pass
            actions.append(d)
        
        out = CASE_ROOT / cfg["dir"] / "analysis" / f"action_scores_{TS}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump({
                "lane": lane_id,
                "description": cfg["desc"],
                "exported_at": TS,
                "total_actions": len(actions),
                "ready_to_file": sum(1 for a in actions if (a.get("composite_score") or 0) >= 70),
                "actions": actions
            }, f, indent=2, ensure_ascii=False)
        
        ready = sum(1 for a in actions if (a.get("composite_score") or 0) >= 70)
        print(f"  Lane {lane_id}: {len(actions)} actions, {ready} ready-to-file -> {out.name}")

def export_filing_manifests(db):
    """Copy filing checkpoint JSONs per lane."""
    print("\n=== EXPORTING FILING MANIFESTS ===")
    
    for lane_id, cfg in LANES.items():
        prefix = cfg["action_prefix"]
        count = 0
        for f in CKPT_ROOT.iterdir():
            if f.name.startswith(f"filing_{prefix}") and f.name.endswith(".json"):
                try:
                    data = json.load(open(f))
                    dest = CASE_ROOT / cfg["dir"] / "filings" / f.name
                    with open(dest, "w") as out:
                        json.dump(data, out, indent=2)
                    count += 1
                except:
                    pass
        print(f"  Lane {lane_id}: {count} filing manifests copied")

def export_atoms(db):
    """Export intel atoms per lane."""
    print("\n=== EXPORTING INTEL ATOMS ===")
    
    for lane_id, cfg in LANES.items():
        rows = db.execute("""
            SELECT id, atom_type, source_file_id, meek_lane, content,
                   confidence, posture, created_by
            FROM atoms
            WHERE meek_lane = ?
            ORDER BY confidence DESC
        """, (lane_id,)).fetchall()
        
        cols = ["id", "atom_type", "source_file_id", "meek_lane", "content",
                "confidence", "posture", "created_by"]
        
        out = CASE_ROOT / cfg["dir"] / "evidence" / f"intel_atoms_{TS}.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(dict(zip(cols, r)), ensure_ascii=False) + "\n")
        print(f"  Lane {lane_id}: {len(rows)} intel atoms")

def write_checkpoint_meta(db):
    """Write master checkpoint metadata."""
    print("\n=== WRITING CHECKPOINT METADATA ===")
    
    meta = {
        "checkpoint": 18,
        "title": "Case-Organized Harvest Export",
        "timestamp": TS,
        "db_stats": {
            "total_files": db.execute("SELECT COUNT(*) FROM files").fetchone()[0],
            "hashed": db.execute("SELECT COUNT(*) FROM files WHERE sha256 IS NOT NULL").fetchone()[0],
            "canonical": db.execute("SELECT COUNT(*) FROM files WHERE is_canonical=1").fetchone()[0],
            "fact_atoms": db.execute("SELECT COUNT(*) FROM fact_atoms").fetchone()[0],
            "citation_atoms": db.execute("SELECT COUNT(*) FROM citation_atoms").fetchone()[0],
            "intel_atoms": db.execute("SELECT COUNT(*) FROM atoms").fetchone()[0],
            "judicial_findings": db.execute("SELECT COUNT(*) FROM judicial_findings").fetchone()[0],
            "action_scores": db.execute("SELECT COUNT(*) FROM action_scores").fetchone()[0],
            "pdfs_processed": db.execute("SELECT COUNT(*) FROM files WHERE extension='.pdf' AND processed=1").fetchone()[0],
        },
        "tier_status": {
            "tier1_recon": "COMPLETE",
            "tier2_dedup": "A05/A06/A08 DONE, A07 at ~198K/900K",
            "tier3_flatten": "COMPLETE (A09 6274/6274)",
            "tierJ_judicial": "J01/J03/J04/J05/J06 DONE, J02/J07 running, J08 needs fix",
            "tierK_case_intel": "COMPLETE",
            "tierL_legal_warfare": "COMPLETE - 7 ready to file",
            "convergence": "COMPLETE (F01-F06)",
            "A10_pdf_harvest": "RUNNING (446/4210)"
        },
        "active_shells": ["tier2-v4 (A07)", "tierj-v4 (J02/J07/J08)", "pdf-harvest (A10)"],
        "known_issues": [
            "J08-IMPEACH: atoms table missing 'title' column",
            "A07-CODE-DEDUP: 198K/900K (multi-hour)",
            "Many D:\\ PDFs are corrupt (scanned images)"
        ]
    }
    
    # Write to case files root
    out = CASE_ROOT / f"CHECKPOINT_18_{TS}.json"
    with open(out, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  Checkpoint metadata -> {out}")
    
    # Also write per-lane summary cards
    for lane_id, cfg in LANES.items():
        lane_meta = {
            "lane": lane_id,
            "description": cfg["desc"],
            "checkpoint": 18,
            "exported_at": TS
        }
        out = CASE_ROOT / cfg["dir"] / f"LANE_STATUS_{TS}.json"
        with open(out, "w") as f:
            json.dump(lane_meta, f, indent=2)

def main():
    print("=" * 60)
    print("DELTA9 CHECKPOINT 18: CASE-ORGANIZED HARVEST EXPORT")
    print("=" * 60)
    
    print("\n--- Creating folder structure ---")
    ensure_dirs()
    
    db = sqlite3.connect(str(DB), timeout=5)
    db.execute("PRAGMA query_only = ON")
    db.execute("PRAGMA busy_timeout = 5000")
    
    try:
        export_fact_atoms(db)
        export_citation_atoms(db)
        export_judicial_findings(db)
        export_action_scores(db)
        export_filing_manifests(db)
        export_atoms(db)
        write_checkpoint_meta(db)
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("CHECKPOINT 18 EXPORT COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
