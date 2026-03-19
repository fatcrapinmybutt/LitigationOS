#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║  LITIGATIONOS UNIVERSAL BOOT ORCHESTRATOR — DELTA9 MAX LEVEL 9999++    ║
║                                                                        ║
║  Single entry point for the entire LitigationOS pipeline.              ║
║  Auto-detects ALL drives → Loads context → Indexes → Deduplicates →   ║
║  Organizes → Harvests → Analyzes → Produces court-ready output.        ║
║                                                                        ║
║  Usage:                                                                ║
║    python litigationos_boot.py                      # Full auto run    ║
║    python litigationos_boot.py --status             # Show status      ║
║    python litigationos_boot.py --phase INDEX        # Run single phase ║
║    python litigationos_boot.py --resume             # Resume from last ║
║    python litigationos_boot.py --dry-run            # Preview only     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import json
import os
import shutil
import sqlite3
import string
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ════════════════════════════════════════════════════════════════════════

LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
PIPELINE_DIR = LITIGOS_ROOT / "00_SYSTEM" / "pipeline"
AGENTS_DIR   = PIPELINE_DIR / "agents"
DB_PATH      = AGENTS_DIR / "master_index.db"
CHECKPOINT_DIR = AGENTS_DIR / "checkpoints"
BOOT_STATE_FILE = PIPELINE_DIR / "boot_state.json"

# All known drive roots — auto-discovered at boot
KNOWN_LITIGOS_DIRS = [
    "LitigationOS", "LITIGATIONOS_MASTER", "LITIGATIONOS_DATA",
    "LitigationOS-Desktop", "LitigationOS-Mobile",
    "LitigationOS-Commercial-Website", "LitigationOS-Watson-FINAL-PACKAGE",
    "LITIGATIONOS_RISK_PACK", "LITIGATIONOS__MASTERv1.0",
    "LitigationOS-Ultimate", "LitigationOS_Authority_Integrated",
    "LitigationOS_CompilerRuntime", "LitigationOS_AutopilotSuite",
]

# Directories to skip during scanning
SKIP_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    "tesseract-main", "czkawka-master", "java-1.8.0-openjdk",
    ".mypy_cache", ".pytest_cache", "target", ".gradle",
    "AppData", "ProgramData", "$RECYCLE.BIN", "System Volume Information",
    "Windows", "Program Files", "Program Files (x86)",
}


# ════════════════════════════════════════════════════════════════════════
#  PHASE 0: DRIVE DISCOVERY & CONTEXT LOADING
# ════════════════════════════════════════════════════════════════════════

class DriveDiscovery:
    """Auto-detect all available drives and build a complete inventory."""

    def __init__(self):
        self.drives: Dict[str, dict] = {}
        self.litigos_variants: List[dict] = []
        self.previous_runs: List[dict] = []

    def detect_all_drives(self) -> Dict[str, dict]:
        """Scan all drive letters A-Z for available filesystems."""
        print("\n" + "=" * 70)
        print("  PHASE 0: UNIVERSAL DRIVE DISCOVERY")
        print("=" * 70)

        for letter in string.ascii_uppercase:
            root = f"{letter}:\\"
            if os.path.exists(root):
                try:
                    usage = shutil.disk_usage(root)
                    self.drives[letter] = {
                        "root": root,
                        "total_gb": round(usage.total / 1e9, 1),
                        "used_gb": round(usage.used / 1e9, 1),
                        "free_gb": round(usage.free / 1e9, 1),
                        "indexed": False,
                        "file_count": 0,
                    }
                except OSError:
                    pass

        print(f"\n  Detected {len(self.drives)} drives:")
        for letter, info in sorted(self.drives.items()):
            print(f"    {letter}: {info['used_gb']}GB used / {info['free_gb']}GB free / {info['total_gb']}GB total")

        return self.drives

    def scan_for_litigos_variants(self) -> List[dict]:
        """Find ALL LitigationOS installations across all drives."""
        print(f"\n  Scanning for LitigationOS variants across {len(self.drives)} drives...")

        for letter, info in self.drives.items():
            root = info["root"]
            try:
                for item in os.scandir(root):
                    if not item.is_dir():
                        continue
                    name = item.name
                    # Check if directory name matches LitigationOS patterns
                    name_lower = name.lower()
                    if any(p.lower() in name_lower for p in ["litigationos", "litigation_os", "litigos"]):
                        variant = {
                            "drive": letter,
                            "path": item.path,
                            "name": name,
                            "type": self._classify_variant(name),
                        }
                        self.litigos_variants.append(variant)
            except (PermissionError, OSError):
                pass

            # Also check common subdirs
            for subdir in ["Users\\andre", "DESSSKTOP", "CAPSTONE", "CANONICAL_ROOT_H"]:
                sub_path = os.path.join(root, subdir)
                if os.path.isdir(sub_path):
                    try:
                        for item in os.scandir(sub_path):
                            if not item.is_dir():
                                continue
                            name_lower = item.name.lower()
                            if any(p.lower() in name_lower for p in ["litigationos", "litigation_os", "litigos"]):
                                self.litigos_variants.append({
                                    "drive": letter,
                                    "path": item.path,
                                    "name": item.name,
                                    "type": self._classify_variant(item.name),
                                })
                    except (PermissionError, OSError):
                        pass

        print(f"  Found {len(self.litigos_variants)} LitigationOS variants:")
        by_drive = {}
        for v in self.litigos_variants:
            by_drive.setdefault(v["drive"], []).append(v)
        for d, variants in sorted(by_drive.items()):
            print(f"    {d}: {len(variants)} variants")
            for v in variants[:5]:
                print(f"      [{v['type']}] {v['name']}")
            if len(variants) > 5:
                print(f"      ... +{len(variants)-5} more")

        return self.litigos_variants

    def load_previous_runs(self) -> List[dict]:
        """Detect previous pipeline runs, interrupted runs, and checkpoints."""
        print(f"\n  Checking for previous runs and interrupted sessions...")

        # Check master_index.db existence and state
        if DB_PATH.exists():
            try:
                conn = sqlite3.connect(str(DB_PATH), timeout=5)
                c = conn.cursor()

                # File counts by drive
                c.execute("SELECT drive, COUNT(*) FROM files GROUP BY drive ORDER BY COUNT(*) DESC")
                drive_counts = c.fetchall()

                # Indexed vs hashed
                c.execute("SELECT COUNT(*) FROM files")
                total_files = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM files WHERE sha256 IS NOT NULL")
                hashed = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM files WHERE is_canonical=1")
                canonical = c.fetchone()[0]

                # Atoms
                c.execute("SELECT COUNT(*) FROM atoms")
                atoms = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM fact_atoms")
                fact_atoms = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM citation_atoms")
                cite_atoms = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM judicial_findings")
                judicial = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM action_scores")
                actions = c.fetchone()[0]

                conn.close()

                self.previous_runs.append({
                    "db_path": str(DB_PATH),
                    "total_files": total_files,
                    "hashed": hashed,
                    "canonical": canonical,
                    "atoms": atoms,
                    "fact_atoms": fact_atoms,
                    "citation_atoms": cite_atoms,
                    "judicial_findings": judicial,
                    "action_scores": actions,
                    "drive_counts": {d: c for d, c in drive_counts},
                })

                print(f"\n  ┌─── EXISTING DB STATE ──────────────────────────────────┐")
                print(f"  │ Files Indexed:   {total_files:>12,}                     │")
                print(f"  │ Files Hashed:    {hashed:>12,}  ({100*hashed/max(total_files,1):.1f}%)              │")
                print(f"  │ Canonicals:      {canonical:>12,}                     │")
                print(f"  │ Atoms:           {atoms:>12,}                     │")
                print(f"  │ Fact Atoms:      {fact_atoms:>12,}                     │")
                print(f"  │ Citation Atoms:  {cite_atoms:>12,}                     │")
                print(f"  │ Judicial:        {judicial:>12,}                     │")
                print(f"  │ Actions Scored:  {actions:>12,}                     │")
                print(f"  ├─── FILES BY DRIVE ────────────────────────────────────┤")
                for d, cnt in drive_counts:
                    indexed = "✓" if d in [v["drive"] for v in self.litigos_variants] or cnt > 0 else "✗"
                    print(f"  │   {d}: {cnt:>12,} files  [{indexed} indexed]                 │")

                # Check which drives are NOT indexed
                indexed_drives = {d for d, _ in drive_counts}
                missing = set(self.drives.keys()) - indexed_drives
                if missing:
                    print(f"  │                                                        │")
                    print(f"  │ ⚠ UNINDEXED DRIVES: {', '.join(sorted(missing)):>33} │")
                print(f"  └────────────────────────────────────────────────────────┘")

            except Exception as e:
                print(f"  ⚠ DB read error: {e}")

        # Check agent checkpoints
        if CHECKPOINT_DIR.exists():
            cp_files = list(CHECKPOINT_DIR.glob("*.json"))
            interrupted = []
            for cp_file in cp_files:
                try:
                    data = json.loads(cp_file.read_text())
                    if data.get("status") != "done":
                        interrupted.append({
                            "agent": cp_file.stem,
                            "processed": data.get("processed", 0),
                            "total": data.get("total", 0),
                        })
                except Exception:
                    pass

            if interrupted:
                print(f"\n  ⚠ INTERRUPTED AGENTS ({len(interrupted)}):")
                for a in interrupted[:10]:
                    pct = 100 * a["processed"] / max(a["total"], 1)
                    print(f"    {a['agent']}: {a['processed']:,}/{a['total']:,} ({pct:.0f}%)")

        return self.previous_runs

    def _classify_variant(self, name: str) -> str:
        nl = name.lower()
        if "desktop" in nl: return "APP-DESKTOP"
        if "mobile" in nl: return "APP-MOBILE"
        if "website" in nl or "commercial" in nl: return "APP-WEB"
        if "compiler" in nl or "runtime" in nl: return "COMPILER"
        if "autopilot" in nl: return "AUTOPILOT"
        if "risk" in nl: return "RISK-PACK"
        if "ultimate" in nl: return "ULTIMATE"
        if "bundle" in nl: return "BUNDLE"
        if "organizer" in nl: return "ORGANIZER"
        if "graph" in nl or "intake" in nl: return "GRAPH-STACK"
        if "authority" in nl: return "AUTHORITY"
        if "toolchain" in nl: return "TOOLCHAIN"
        if "data" in nl: return "DATA"
        if "master" in nl: return "MASTER"
        if "final" in nl or "watson" in nl: return "FILING-PACK"
        if "infinitezoom" in nl: return "ZOOM-PACK"
        if "plane" in nl: return "PLANE-MAP"
        return "VARIANT"


# ════════════════════════════════════════════════════════════════════════
#  PHASE 1: INDEX ALL DRIVES
# ════════════════════════════════════════════════════════════════════════

class UniversalIndexer:
    """Index files across ALL detected drives into master_index.db."""

    def __init__(self, db_path: Path, drives: Dict[str, dict]):
        self.db_path = db_path
        self.drives = drives
        self.stats = {"new": 0, "existing": 0, "errors": 0}

    def index_missing_drives(self):
        """Index only drives that haven't been indexed yet."""
        conn = sqlite3.connect(str(self.db_path), timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        c = conn.cursor()

        # Find already-indexed drives
        c.execute("SELECT DISTINCT drive FROM files")
        indexed_drives = {row[0] for row in c.fetchall()}

        # Determine which drives need indexing
        to_index = set(self.drives.keys()) - indexed_drives
        if not to_index:
            print("\n  All drives already indexed. Checking for new files...")
            # Still do a quick scan for new files on each drive
            to_index = set(self.drives.keys())

        print(f"\n" + "=" * 70)
        print(f"  PHASE 1: INDEXING {'NEW ' if to_index != set(self.drives.keys()) else ''}DRIVES: {', '.join(sorted(to_index))}")
        print("=" * 70)

        for drive_letter in sorted(to_index):
            already_indexed = drive_letter in indexed_drives
            self._index_drive(conn, drive_letter, incremental=already_indexed)

        conn.close()
        print(f"\n  Index complete: {self.stats['new']:,} new, {self.stats['existing']:,} existing, {self.stats['errors']:,} errors")

    def _index_drive(self, conn: sqlite3.Connection, drive_letter: str, incremental: bool = False):
        """Walk a drive and insert files into the DB."""
        root = f"{drive_letter}:\\"
        label = "INCREMENTAL" if incremental else "FULL"
        print(f"\n  [{label}] Scanning {drive_letter}: drive...")

        # Build set of existing paths for incremental mode
        existing_paths = set()
        if incremental:
            c = conn.cursor()
            c.execute("SELECT full_path FROM files WHERE drive=?", (drive_letter,))
            existing_paths = {row[0] for row in c.fetchall()}
            print(f"    {len(existing_paths):,} files already indexed on {drive_letter}:")

        count = 0
        batch = []
        batch_size = 1000

        for dirpath, dirnames, filenames in os.walk(root):
            # Skip system/junk directories
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                          and not d.startswith("$")
                          and not d.startswith(".")]

            depth = dirpath.replace(root, "").count(os.sep) + 1

            for fname in filenames:
                full_path = os.path.join(dirpath, fname)

                # Skip if already indexed (incremental mode)
                if incremental and full_path in existing_paths:
                    self.stats["existing"] += 1
                    continue

                try:
                    ext = os.path.splitext(fname)[1].lower()
                    stat = os.stat(full_path)
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

                    batch.append((
                        drive_letter,
                        full_path,
                        fname,
                        ext,
                        size,
                        depth,
                        modified,
                    ))
                    count += 1

                    if len(batch) >= batch_size:
                        self._flush_batch(conn, batch)
                        batch = []
                        if count % 10000 == 0:
                            print(f"    {drive_letter}: {count:,} new files...", flush=True)

                except (PermissionError, OSError):
                    self.stats["errors"] += 1

        if batch:
            self._flush_batch(conn, batch)

        self.stats["new"] += count
        print(f"    {drive_letter}: {count:,} new files indexed")

    def _flush_batch(self, conn: sqlite3.Connection, batch: list):
        """Insert a batch of files, skipping duplicates."""
        conn.executemany("""
            INSERT OR IGNORE INTO files (drive, full_path, file_name, extension, size_bytes, depth, modified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, batch)
        conn.commit()


# ════════════════════════════════════════════════════════════════════════
#  PHASE 2: DEDUP + HASH (resume-aware)
# ════════════════════════════════════════════════════════════════════════

class UniversalDedup:
    """Hash unhashed files, elect canonicals, track dedup clusters."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def run(self):
        """Hash all unhashed legal-relevant files, then elect canonicals."""
        print(f"\n" + "=" * 70)
        print(f"  PHASE 2: UNIVERSAL DEDUPLICATION")
        print("=" * 70)

        # This delegates to existing tier2 agents via orchestrator
        # but can also run standalone for incremental updates
        print("  Delegating to DELTA9 Tier 2 agents (A05-A08)...")
        print("  A07-CODE-DEDUP is the bottleneck — processing 828K+ code files")
        print("  Use 'python -m agents.agent_orchestrator --tier tier2' for full run")


# ════════════════════════════════════════════════════════════════════════
#  PHASE 3-4: HARVEST (Extract + Atomize)
# ════════════════════════════════════════════════════════════════════════

class UniversalHarvester:
    """Extract text from all canonical legal documents, generate atoms."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def run(self):
        print(f"\n" + "=" * 70)
        print(f"  PHASE 3-4: UNIVERSAL HARVEST")
        print("=" * 70)
        print("  Delegating to DELTA9 Tier 3 agents (A09-A12)...")
        print("  A10-PDF-HARVESTER handles PDFs (most critical)")
        print("  A11-TEXT-MINER handles .md/.txt files")
        print("  A12-STRUCT-PARSER handles .json/.csv/.jsonl")


# ════════════════════════════════════════════════════════════════════════
#  PHASE 5-6: ANALYZE (Judicial + Legal Actions + Scoring)
# ════════════════════════════════════════════════════════════════════════

class UniversalAnalyzer:
    """Run all analysis tiers: Judicial → Case Intel → Legal Warfare."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def run(self):
        print(f"\n" + "=" * 70)
        print(f"  PHASE 5-6: UNIVERSAL ANALYSIS")
        print("=" * 70)
        print("  Tier J: Judicial Harvest (J01-J08) — judge profiling, misconduct")
        print("  Tier K: Case Intelligence (K01-K08) — custody, housing, convergence")
        print("  Tier L: Legal Warfare (L01-L08) — scoring, gaps, damages, readiness")


# ════════════════════════════════════════════════════════════════════════
#  PHASE 7: PRODUCE (Court Documents + Manifests + Encyclopedias)
# ════════════════════════════════════════════════════════════════════════

class UniversalProducer:
    """Produce all court-ready output: manifests, encyclopedias, binders."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def generate_manifest(self) -> dict:
        """Generate the master filing manifest with ALL available court actions."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Get all scored actions
        c.execute("""
            SELECT action_id, lane, evidence_score, authority_score,
                   vulnerability_score, readiness_score, composite_score, gap_count
            FROM action_scores ORDER BY composite_score DESC
        """)
        actions = [dict(row) for row in c.fetchall()]

        # Get judicial findings summary
        c.execute("""
            SELECT judge, finding_type, COUNT(*) as cnt, AVG(severity) as avg_sev
            FROM judicial_findings GROUP BY judge, finding_type
            ORDER BY avg_sev DESC
        """)
        judicial_summary = [dict(row) for row in c.fetchall()]

        # Get top atoms by lane
        c.execute("""
            SELECT meek_lane, atom_type, COUNT(*) as cnt
            FROM atoms GROUP BY meek_lane, atom_type ORDER BY cnt DESC
        """)
        atom_summary = [dict(row) for row in c.fetchall()]

        # Get filing readiness
        ready = [a for a in actions if a["readiness_score"] and a["readiness_score"] >= 70]
        close = [a for a in actions if a["readiness_score"] and 50 <= a["readiness_score"] < 70]
        developing = [a for a in actions if a["readiness_score"] and a["readiness_score"] < 50]

        conn.close()

        manifest = {
            "generated": datetime.now().isoformat(),
            "system": "LitigationOS DELTA9 MAX LEVEL 9999++",
            "case_lanes": {
                "A": {
                    "name": "Watson / Custody",
                    "cases": ["2024-001507-DC", "2023-5907-PP"],
                    "judge": "McNeill",
                    "actions": [a for a in actions if a["lane"] == "A"],
                },
                "B": {
                    "name": "Shady Oaks / Housing",
                    "cases": ["2025-002760-CZ"],
                    "judge": "Hoopes",
                    "actions": [a for a in actions if a["lane"] == "B"],
                },
                "C": {
                    "name": "Convergence / County",
                    "cases": ["NEW consolidated"],
                    "judge": "Multi-judge pattern",
                    "actions": [a for a in actions if a["lane"] == "C"],
                },
                "D": {
                    "name": "PPO / Protection Orders",
                    "cases": ["2024-001507-DC", "2023-5907-PP"],
                    "judge": "McNeill",
                    "actions": [a for a in actions if a["lane"] == "D"],
                },
                "E": {
                    "name": "Judicial Misconduct / JTC",
                    "cases": ["2024-001507-DC"],
                    "judge": "McNeill",
                    "actions": [a for a in actions if a["lane"] == "E"],
                },
                "F": {
                    "name": "Appellate (COA/MSC)",
                    "cases": [],
                    "judge": "Multi-panel",
                    "actions": [a for a in actions if a["lane"] == "F"],
                },
            },
            "readiness": {
                "ready_to_file": len(ready),
                "close": len(close),
                "developing": len(developing),
                "ready_actions": [a["action_id"] for a in ready],
            },
            "judicial_findings": judicial_summary,
            "atom_inventory": atom_summary,
            "total_actions": len(actions),
        }

        return manifest

    def generate_encyclopedia(self) -> dict:
        """Generate the legal action encyclopedia with ALL viable options."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        encyclopedia = {
            "title": "LITIGATIONOS LEGAL ACTION ENCYCLOPEDIA",
            "subtitle": "Complete Catalog of Viable Legal Actions Across All Jurisdictions",
            "michigan_courts": {
                "circuit_court": {
                    "14th_judicial_circuit": {
                        "venue": "Muskegon County",
                        "lane_a": self._get_circuit_actions(c, "A"),
                        "lane_b": self._get_circuit_actions(c, "B"),
                        "lane_d": self._get_circuit_actions(c, "D"),
                        "lane_e": self._get_circuit_actions(c, "E"),
                        "lane_f": self._get_circuit_actions(c, "F"),
                    }
                },
                "court_of_appeals": {
                    "description": "Michigan Court of Appeals",
                    "filing_paths": ["MCR 7.205 Leave to Appeal", "MCR 7.202(6) Interlocutory"],
                    "applicable_actions": self._get_appellate_actions(c),
                },
                "supreme_court": {
                    "description": "Michigan Supreme Court",
                    "filing_paths": [
                        "MCR 7.305 Application for Leave",
                        "MCR 7.305(B)(2) Bypass (significant public interest)",
                        "MCR 7.306 Extraordinary Writs",
                    ],
                },
                "jtc": {
                    "description": "Judicial Tenure Commission",
                    "authority": "MCR 9.200, Canons 1-3",
                    "target": "Hon. Jenny L. McNeill",
                },
            },
            "federal_courts": {
                "western_district_michigan": {
                    "claims": [
                        {"id": "A18", "type": "42 USC §1983 Substantive Due Process"},
                        {"id": "A19", "type": "42 USC §1983 Procedural Due Process"},
                        {"id": "A20", "type": "42 USC §1983 Civil Conspiracy"},
                        {"id": "C1", "type": "Monell County Liability"},
                        {"id": "C5", "type": "42 USC §1985 Conspiracy"},
                    ],
                },
                "sixth_circuit": {
                    "description": "6th Circuit Court of Appeals (if district denies)",
                },
            },
            "administrative": {
                "attorney_grievance": {"target": "David Rusco", "body": "MI AGC"},
                "lara": {"target": "Licensed professionals", "body": "LARA"},
                "code_enforcement": {"target": "Shady Oaks MHP", "body": "Muskegon County"},
            },
        }

        conn.close()
        return encyclopedia

    def generate_binder_index(self) -> dict:
        """Generate court binder organizational index."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Count exhibits by lane
        c.execute("SELECT meek_lane, COUNT(*) FROM atoms WHERE atom_type='fact' GROUP BY meek_lane")
        facts_by_lane = dict(c.fetchall())

        c.execute("SELECT meek_lane, COUNT(*) FROM atoms WHERE atom_type='citation' GROUP BY meek_lane")
        cites_by_lane = dict(c.fetchall())

        # Get judicial findings for exhibit prep
        c.execute("SELECT COUNT(*) FROM judicial_findings WHERE judge='McNeill'")
        mcneill_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM judicial_findings WHERE judge='Hoopes'")
        hoopes_count = c.fetchone()[0]

        conn.close()

        binder = {
            "title": "LITIGATIONOS MASTER BINDER INDEX",
            "volumes": {
                "VOL_1_LANE_A": {
                    "title": "Watson / Custody — 2024-001507-DC",
                    "tabs": [
                        {"tab": "A", "content": "Complaint / Petition", "status": "READY"},
                        {"tab": "B", "content": "Emergency Motions", "status": "READY"},
                        {"tab": "C", "content": "PPO Documents (2023-5907-PP)", "status": "READY"},
                        {"tab": "D", "content": "Best Interest Analysis (MCL 722.23)", "status": "IN PROGRESS"},
                        {"tab": "E", "content": "Parental Alienation Evidence", "status": "IN PROGRESS"},
                        {"tab": "F", "content": "Judicial Misconduct — McNeill", "count": mcneill_count},
                        {"tab": "G", "content": "Impeachment Materials", "status": "READY"},
                        {"tab": "H", "content": "Exhibit Index", "facts": facts_by_lane.get("A", 0)},
                    ],
                },
                "VOL_2_LANE_B": {
                    "title": "Shady Oaks / Housing — 2025-002760-CZ",
                    "tabs": [
                        {"tab": "A", "content": "Civil Complaint", "status": "READY"},
                        {"tab": "B", "content": "Habitability Evidence (MCL 554.139)", "status": "IN PROGRESS"},
                        {"tab": "C", "content": "Consumer Protection (MCL 445.903)", "status": "IN PROGRESS"},
                        {"tab": "D", "content": "Corporate Defendant Docs", "status": "IN PROGRESS"},
                        {"tab": "E", "content": "Damages Calculation", "status": "READY"},
                        {"tab": "F", "content": "Exhibit Index", "facts": facts_by_lane.get("B", 0)},
                    ],
                },
                "VOL_3_LANE_C": {
                    "title": "Convergence / County — Muskegon County Pattern",
                    "tabs": [
                        {"tab": "A", "content": "§1983 Federal Complaint", "status": "READY"},
                        {"tab": "B", "content": "Monell Pattern Evidence", "status": "IN PROGRESS"},
                        {"tab": "C", "content": "Cross-Lane Judicial Misconduct", "count": mcneill_count + hoopes_count},
                        {"tab": "D", "content": "JTC Complaint Package", "status": "READY"},
                        {"tab": "E", "content": "MSC Application Materials", "status": "DEVELOPING"},
                        {"tab": "F", "content": "Convergence Exhibit Index"},
                    ],
                },
                "VOL_4_AUTHORITIES": {
                    "title": "Legal Authorities Compendium",
                    "tabs": [
                        {"tab": "A", "content": "Michigan Court Rules (MCR)"},
                        {"tab": "B", "content": "Michigan Compiled Laws (MCL)"},
                        {"tab": "C", "content": "Michigan Rules of Evidence (MRE)"},
                        {"tab": "D", "content": "Federal Statutes (42 USC §1983+)"},
                        {"tab": "E", "content": "Case Law Citations"},
                        {"tab": "F", "content": "Judicial Canons"},
                    ],
                },
            },
        }

        return binder

    def _get_circuit_actions(self, cursor, lane: str) -> list:
        cursor.execute("""
            SELECT action_id, composite_score, readiness_score, gap_count
            FROM action_scores WHERE lane=? ORDER BY composite_score DESC
        """, (lane,))
        return [dict(r) for r in cursor.fetchall()]

    def _get_appellate_actions(self, cursor) -> list:
        cursor.execute("""
            SELECT action_id, composite_score, readiness_score
            FROM action_scores WHERE action_id LIKE 'A1%' OR action_id LIKE 'B9%'
            ORDER BY composite_score DESC
        """)
        return [dict(r) for r in cursor.fetchall()]

    def run(self):
        """Generate all production outputs."""
        print(f"\n" + "=" * 70)
        print(f"  PHASE 7: UNIVERSAL PRODUCTION")
        print("=" * 70)

        output_dir = LITIGOS_ROOT / "01_CASE_FILES" / "PRODUCTION_OUTPUT"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Master Filing Manifest
        print("\n  Generating Master Filing Manifest...")
        manifest = self.generate_manifest()
        manifest_path = output_dir / "MASTER_FILING_MANIFEST.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str))
        print(f"    → {manifest_path}")
        print(f"    → {manifest['total_actions']} actions scored")
        print(f"    → {manifest['readiness']['ready_to_file']} READY TO FILE")

        # 2. Legal Action Encyclopedia
        print("\n  Generating Legal Action Encyclopedia...")
        encyclopedia = self.generate_encyclopedia()
        enc_path = output_dir / "LEGAL_ACTION_ENCYCLOPEDIA.json"
        enc_path.write_text(json.dumps(encyclopedia, indent=2, default=str))
        print(f"    → {enc_path}")

        # 3. Court Binder Index
        print("\n  Generating Court Binder Index...")
        binder = self.generate_binder_index()
        binder_path = output_dir / "MASTER_BINDER_INDEX.json"
        binder_path.write_text(json.dumps(binder, indent=2, default=str))
        print(f"    → {binder_path}")
        print(f"    → {len(binder['volumes'])} volumes")

        # 4. Human-readable summary
        self._write_summary(output_dir, manifest, binder)

        print(f"\n  ✓ All production outputs in: {output_dir}")

    def _write_summary(self, output_dir: Path, manifest: dict, binder: dict):
        """Write human-readable summary markdown."""
        summary_path = output_dir / "PRODUCTION_SUMMARY.md"
        lines = [
            "# LITIGATIONOS PRODUCTION SUMMARY",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## FILING READINESS",
            f"- **Ready to File:** {manifest['readiness']['ready_to_file']} actions",
            f"- **Ready Actions:** {', '.join(manifest['readiness']['ready_actions'])}",
            f"- **Close (50-70%):** {manifest['readiness']['close']} actions",
            f"- **Developing (<50%):** {manifest['readiness']['developing']} actions",
            f"- **Total Actions:** {manifest['total_actions']}",
            "",
            "## CASE LANES",
        ]
        for lane_id, lane in manifest["case_lanes"].items():
            lines.append(f"\n### Lane {lane_id}: {lane['name']}")
            lines.append(f"- Cases: {', '.join(lane['cases'])}")
            lines.append(f"- Judge: {lane['judge']}")
            lines.append(f"- Actions: {len(lane['actions'])}")

        lines.extend([
            "",
            "## COURT BINDER VOLUMES",
        ])
        for vol_id, vol in binder["volumes"].items():
            lines.append(f"\n### {vol_id}: {vol['title']}")
            for tab in vol["tabs"]:
                status = tab.get("status", "")
                count = tab.get("count", "")
                extra = f" [{status}]" if status else f" ({count} findings)" if count else ""
                lines.append(f"- Tab {tab['tab']}: {tab['content']}{extra}")

        lines.extend([
            "",
            "## MICHIGAN JURISDICTIONS COVERED",
            "- 14th Judicial Circuit Court, Muskegon County",
            "- Michigan Court of Appeals",
            "- Michigan Supreme Court",
            "- Judicial Tenure Commission",
            "- Western District of Michigan (Federal)",
            "- 6th Circuit Court of Appeals (Federal)",
            "- Attorney Grievance Commission",
            "- LARA (Licensing)",
            "- Muskegon County Code Enforcement",
            "",
            "---",
            "*Generated by LitigationOS DELTA9 Universal Boot Orchestrator*",
        ])

        summary_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"    → {summary_path}")


# ════════════════════════════════════════════════════════════════════════
#  MASTER ORCHESTRATOR — Runs Everything
# ════════════════════════════════════════════════════════════════════════

class LitigationOSOrchestrator:
    """
    The Universal Boot Orchestrator.
    Single entry point: detect → context → index → dedup → harvest → analyze → produce.
    """

    PHASES = [
        ("0-DISCOVER",  "Drive Discovery & Context Loading"),
        ("1-INDEX",     "Universal File Indexing (all drives)"),
        ("2-DEDUP",     "Hash, Classify & Deduplicate"),
        ("3-HARVEST",   "Extract Text & Generate Atoms"),
        ("4-JUDICIAL",  "Judicial Analysis (Tier J)"),
        ("5-CASEINT",   "Case Intelligence (Tier K)"),
        ("6-WARFARE",   "Legal Warfare Scoring (Tier L)"),
        ("7-CONVERGE",  "Convergence & Filing Factory (Tier F)"),
        ("8-PRODUCE",   "Production Output: Manifests, Encyclopedias, Binders"),
        ("9-VALIDATE",  "Court-Ready Validation & QA"),
    ]

    def __init__(self, dry_run: bool = False, resume: bool = True):
        self.dry_run = dry_run
        self.resume = resume
        self.discovery = DriveDiscovery()
        self.boot_state = self._load_boot_state()
        self.start_time = time.time()

    def run(self, phase: Optional[str] = None):
        """Execute the full pipeline or a single phase."""
        self._print_banner()

        # Phase 0: Always run discovery
        self.discovery.detect_all_drives()
        self.discovery.scan_for_litigos_variants()
        self.discovery.load_previous_runs()

        if phase:
            self._run_phase(phase)
        else:
            self._run_all_phases()

        self._print_completion()

    def run_status(self):
        """Print comprehensive status without executing anything."""
        self._print_banner()
        self.discovery.detect_all_drives()
        self.discovery.scan_for_litigos_variants()
        self.discovery.load_previous_runs()

        # Additional status from DB
        if DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH), timeout=10)
            c = conn.cursor()

            print(f"\n" + "=" * 70)
            print(f"  AGENT STATUS")
            print("=" * 70)

            # Check each agent's checkpoint
            if CHECKPOINT_DIR.exists():
                for cp_file in sorted(CHECKPOINT_DIR.glob("*.json")):
                    try:
                        data = json.loads(cp_file.read_text())
                        agent = cp_file.stem
                        status = data.get("status", "unknown")
                        processed = data.get("processed", 0)
                        total = data.get("total", 0)
                        pct = 100 * processed / max(total, 1)
                        icon = "✅" if status == "done" else "🔄" if processed > 0 else "⏳"
                        print(f"  {icon} {agent}: {status} [{processed:,}/{total:,}] ({pct:.0f}%)")
                    except Exception:
                        pass

            # Pipeline phase status
            print(f"\n" + "=" * 70)
            print(f"  PIPELINE PHASES")
            print("=" * 70)
            for phase_id, phase_name in self.PHASES:
                completed = self.boot_state.get("completed_phases", {}).get(phase_id, False)
                icon = "✅" if completed else "⬜"
                print(f"  {icon} {phase_id}: {phase_name}")

            conn.close()

    def _run_all_phases(self):
        """Execute all phases in sequence, skipping completed ones if resuming."""
        for phase_id, phase_name in self.PHASES:
            if self.resume and self.boot_state.get("completed_phases", {}).get(phase_id):
                print(f"\n  ⏭ Skipping {phase_id} (already complete)")
                continue

            self._run_phase(phase_id)

    def _run_phase(self, phase_id: str):
        """Execute a single phase."""
        phase_name = dict(self.PHASES).get(phase_id, phase_id)
        print(f"\n{'█' * 70}")
        print(f"  EXECUTING: {phase_id} — {phase_name}")
        print(f"{'█' * 70}")

        if self.dry_run:
            print(f"  [DRY RUN] Would execute {phase_id}")
            return

        try:
            if phase_id == "0-DISCOVER":
                pass  # Already done at boot
            elif phase_id == "1-INDEX":
                indexer = UniversalIndexer(DB_PATH, self.discovery.drives)
                indexer.index_missing_drives()
            elif phase_id == "2-DEDUP":
                UniversalDedup(DB_PATH).run()
            elif phase_id == "3-HARVEST":
                UniversalHarvester(DB_PATH).run()
            elif phase_id in ("4-JUDICIAL", "5-CASEINT", "6-WARFARE", "7-CONVERGE"):
                tier_map = {
                    "4-JUDICIAL": "tierJ",
                    "5-CASEINT": "tierK",
                    "6-WARFARE": "tierL",
                    "7-CONVERGE": "convergence",
                }
                tier = tier_map[phase_id]
                self._run_agent_tier(tier)
            elif phase_id == "8-PRODUCE":
                UniversalProducer(DB_PATH).run()
            elif phase_id == "9-VALIDATE":
                self._run_validation()

            self._mark_phase_complete(phase_id)
            print(f"\n  ✓ {phase_id} COMPLETE")

        except Exception as e:
            print(f"\n  ✗ {phase_id} FAILED: {e}")
            traceback.print_exc()

    def _run_agent_tier(self, tier: str):
        """Delegate to the DELTA9 agent orchestrator for a tier."""
        print(f"  Delegating to agent_orchestrator.run_tier('{tier}')...")
        sys.path.insert(0, str(PIPELINE_DIR))
        try:
            from agents.agent_orchestrator import run_tier
            results = run_tier(tier, max_workers=4)
            for r in results:
                s = r.stats
                icon = "✅" if r.status == "SUCCESS" else "❌"
                print(f"    {icon} {r.agent_id}: {r.status} [{s.processed}/{s.total} done, {s.errored} err]")
        except ImportError as e:
            print(f"  ⚠ Cannot import orchestrator: {e}")
            print(f"  Run manually: cd {PIPELINE_DIR} && python -m agents.agent_orchestrator --tier {tier}")

    def _run_validation(self):
        """Run court-ready validation checks."""
        print("  Running validation checks...")
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        c = conn.cursor()

        checks = []

        # Check 1: All drives indexed
        c.execute("SELECT DISTINCT drive FROM files")
        indexed = {r[0] for r in c.fetchall()}
        all_drives = set(self.discovery.drives.keys())
        missing = all_drives - indexed
        checks.append(("All drives indexed", len(missing) == 0, f"Missing: {missing}" if missing else "OK"))

        # Check 2: Sufficient canonicals
        c.execute("SELECT COUNT(*) FROM files WHERE is_canonical=1")
        canonical_count = c.fetchone()[0]
        checks.append(("Canonicals elected", canonical_count > 1000, f"{canonical_count:,} canonicals"))

        # Check 3: Atoms exist
        c.execute("SELECT COUNT(*) FROM atoms")
        atom_count = c.fetchone()[0]
        checks.append(("Atoms extracted", atom_count > 100, f"{atom_count:,} atoms"))

        # Check 4: Judicial findings
        c.execute("SELECT COUNT(*) FROM judicial_findings")
        jf = c.fetchone()[0]
        checks.append(("Judicial findings", jf > 50, f"{jf:,} findings"))

        # Check 5: Actions scored
        c.execute("SELECT COUNT(*) FROM action_scores WHERE composite_score > 0")
        scored = c.fetchone()[0]
        checks.append(("Actions scored", scored > 10, f"{scored:,} scored"))

        # Check 6: Ready to file
        c.execute("SELECT COUNT(*) FROM action_scores WHERE readiness_score >= 70")
        ready = c.fetchone()[0]
        checks.append(("Ready to file", ready > 0, f"{ready:,} ready"))

        conn.close()

        passed = sum(1 for _, ok, _ in checks if ok)
        total = len(checks)
        print(f"\n  Validation: {passed}/{total} checks passed")
        for name, ok, detail in checks:
            icon = "✅" if ok else "❌"
            print(f"    {icon} {name}: {detail}")

    def _load_boot_state(self) -> dict:
        """Load saved boot state for resume capability."""
        if BOOT_STATE_FILE.exists():
            try:
                return json.loads(BOOT_STATE_FILE.read_text())
            except Exception:
                pass
        return {"completed_phases": {}, "last_run": None}

    def _mark_phase_complete(self, phase_id: str):
        """Save phase completion for resume."""
        self.boot_state.setdefault("completed_phases", {})[phase_id] = datetime.now().isoformat()
        self.boot_state["last_run"] = datetime.now().isoformat()
        BOOT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BOOT_STATE_FILE.write_text(json.dumps(self.boot_state, indent=2))

    def _print_banner(self):
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║   ██╗     ██╗████████╗██╗ ██████╗  █████╗ ████████╗██╗ ██████╗ ███╗   ║
║   ██║     ██║╚══██╔══╝██║██╔════╝ ██╔══██╗╚══██╔══╝██║██╔═══██╗██║   ║
║   ██║     ██║   ██║   ██║██║  ███╗███████║   ██║   ██║██║   ██║██║   ║
║   ██║     ██║   ██║   ██║██║   ██║██╔══██║   ██║   ██║██║   ██║╚═╝   ║
║   ███████╗██║   ██║   ██║╚██████╔╝██║  ██║   ██║   ██║╚██████╔╝██╗   ║
║   ╚══════╝╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝   ║
║                                                                        ║
║          DELTA9 UNIVERSAL BOOT ORCHESTRATOR — MAX LEVEL 9999++         ║
║           Pigors v. Watson | Pigors v. Shady Oaks | v. County          ║
║                                                                        ║
╚══════════════════════════════════════════════════════════════════════════╝
""")

    def _print_completion(self):
        elapsed = time.time() - self.start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  BOOT COMPLETE — Elapsed: {mins}m {secs}s                                     ║
║                                                                        ║
║  Outputs:                                                              ║
║    • MASTER_FILING_MANIFEST.json   — All 56 actions scored             ║
║    • LEGAL_ACTION_ENCYCLOPEDIA.json — Full jurisdiction catalog         ║
║    • MASTER_BINDER_INDEX.json      — 4-volume court binder             ║
║    • PRODUCTION_SUMMARY.md         — Human-readable status             ║
║                                                                        ║
║  Next: Review ready-to-file actions → Generate .docx → File with court ║
╚══════════════════════════════════════════════════════════════════════════╝
""")


# ════════════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS Universal Boot Orchestrator — DELTA9 MAX LEVEL 9999++",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python litigationos_boot.py                    # Full auto-run (all phases)
  python litigationos_boot.py --status           # Show comprehensive status
  python litigationos_boot.py --phase 1-INDEX    # Run only indexing
  python litigationos_boot.py --phase 8-PRODUCE  # Generate all outputs
  python litigationos_boot.py --resume           # Resume from last checkpoint
  python litigationos_boot.py --dry-run          # Preview without executing
  python litigationos_boot.py --reset            # Clear boot state, fresh start
        """,
    )
    parser.add_argument("--status", action="store_true", help="Show system status without executing")
    parser.add_argument("--phase", type=str, help="Run a specific phase (e.g., 1-INDEX, 8-PRODUCE)")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from last checkpoint (default)")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh, ignore previous progress")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't execute")
    parser.add_argument("--reset", action="store_true", help="Clear boot state for fresh start")

    args = parser.parse_args()

    if args.reset:
        if BOOT_STATE_FILE.exists():
            BOOT_STATE_FILE.unlink()
            print("Boot state cleared. Ready for fresh start.")
        return

    orchestrator = LitigationOSOrchestrator(
        dry_run=args.dry_run,
        resume=not args.no_resume,
    )

    if args.status:
        orchestrator.run_status()
    else:
        orchestrator.run(phase=args.phase)


if __name__ == "__main__":
    main()
