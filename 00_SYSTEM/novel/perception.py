"""
NOVEL Engine — Perception Layer v2
Deep analysis of the REAL system state by querying litigation_context.db,
scanning the filesystem, and analyzing the agent/skill/tool fleet.

This replaces hardcoded gap lists with genuine intelligence —
the engine discovers reality instead of assuming it.

Three perception modes:
  DatabasePerception  — queries the real 166-table litigation DB
  FleetPerception     — analyzes agents, skills, tools for coverage gaps
  FilesystemPerception — scans drives for orphaned/unprocessed files
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
from typing import Optional

os.environ["PYTHONUTF8"] = "1"

REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
MAIN_DB = REPO_ROOT / "litigation_context.db"
DARWIN_DB = REPO_ROOT / "00_SYSTEM" / "darwin" / "darwin.db"


def _safe_connect(db_path: Path) -> Optional[sqlite3.Connection]:
    """Connect with WAL mode and busy timeout. Returns None if DB doesn't exist."""
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.row_factory = sqlite3.Row
    return conn


class DatabasePerception:
    """
    Queries litigation_context.db to understand the REAL state of the case.
    Finds data gaps, stale records, orphaned evidence, missing linkages,
    and opportunities that hardcoded lists can never discover.
    """

    def __init__(self, db_path: Path = MAIN_DB):
        self.db_path = db_path

    def perceive(self) -> dict:
        """Full perception scan — returns a complete picture of DB state."""
        conn = _safe_connect(self.db_path)
        if not conn:
            return {"error": f"Database not found: {self.db_path}"}
        try:
            tables = self._get_all_tables(conn)
            return {
                "table_census": self._census_tables(conn, tables),
                "evidence_intelligence": self._perceive_evidence(conn, tables),
                "filing_intelligence": self._perceive_filings(conn, tables),
                "deadline_intelligence": self._perceive_deadlines(conn, tables),
                "authority_intelligence": self._perceive_authorities(conn, tables),
                "data_quality": self._perceive_quality(conn, tables),
                "orphan_detection": self._perceive_orphans(conn, tables),
                "cross_reference_gaps": self._perceive_cross_refs(conn, tables),
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            conn.close()

    def _get_all_tables(self, conn) -> set:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return set(r[0] for r in rows)

    def _table_cols(self, conn, table: str) -> list:
        return [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]

    def _safe_count(self, conn, table: str) -> int:
        try:
            return conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        except Exception:
            return -1

    # ────────────────────────────────────────────────────────────
    # TABLE CENSUS — which tables are empty, small, large, broken
    # ────────────────────────────────────────────────────────────

    def _census_tables(self, conn, tables: set) -> dict:
        empty, small, large, broken = [], [], [], []
        total_rows = 0

        for table in sorted(tables):
            count = self._safe_count(conn, table)
            if count < 0:
                broken.append(table)
            elif count == 0:
                empty.append(table)
            else:
                total_rows += count
                if count < 10:
                    small.append({"table": table, "rows": count})
                elif count > 10000:
                    large.append({"table": table, "rows": count})

        return {
            "total_tables": len(tables),
            "total_rows": total_rows,
            "empty_count": len(empty),
            "empty_tables": empty[:30],
            "small_count": len(small),
            "large_count": len(large),
            "large_tables": sorted(large, key=lambda x: -x["rows"])[:15],
            "broken_count": len(broken),
        }

    # ────────────────────────────────────────────────────────────
    # EVIDENCE INTELLIGENCE — what evidence exists, what's linked
    # ────────────────────────────────────────────────────────────

    def _perceive_evidence(self, conn, tables: set) -> dict:
        intel = {"total": 0, "unlinked": 0, "by_lane": {}, "by_type": {},
                 "strongest": [], "weakest_claims": [], "gaps": []}

        if "evidence_quotes" not in tables:
            intel["gaps"].append("evidence_quotes table missing")
            return intel

        cols = self._table_cols(conn, "evidence_quotes")
        intel["total"] = self._safe_count(conn, "evidence_quotes")

        # Unlinked evidence (no claim assignment)
        if "claim_id" in cols:
            row = conn.execute(
                "SELECT COUNT(*) FROM evidence_quotes WHERE claim_id IS NULL OR claim_id = ''"
            ).fetchone()
            intel["unlinked"] = row[0]
            if intel["total"] > 0:
                intel["link_rate"] = round(
                    (intel["total"] - intel["unlinked"]) / intel["total"] * 100, 1
                )

        # Distribution by lane
        lane_col = "lane" if "lane" in cols else "vehicle_name" if "vehicle_name" in cols else None
        if lane_col:
            rows = conn.execute(f'''
                SELECT "{lane_col}", COUNT(*) as cnt FROM evidence_quotes
                GROUP BY "{lane_col}" ORDER BY cnt DESC
            ''').fetchall()
            intel["by_lane"] = {r[0] or "UNASSIGNED": r[1] for r in rows}

        # Evidence strength distribution
        if "score" in cols or "strength" in cols:
            score_col = "score" if "score" in cols else "strength"
            try:
                row = conn.execute(f'''
                    SELECT 
                        AVG(CAST("{score_col}" AS REAL)) as avg_score,
                        MIN(CAST("{score_col}" AS REAL)) as min_score,
                        MAX(CAST("{score_col}" AS REAL)) as max_score
                    FROM evidence_quotes 
                    WHERE "{score_col}" IS NOT NULL AND "{score_col}" != ''
                ''').fetchone()
                if row and row[0] is not None:
                    intel["avg_strength"] = round(row[0], 3)
                    intel["strength_range"] = [round(row[1], 3), round(row[2], 3)]
            except Exception:
                pass

        return intel

    # ────────────────────────────────────────────────────────────
    # FILING INTELLIGENCE — readiness, blockers, coverage
    # ────────────────────────────────────────────────────────────

    def _perceive_filings(self, conn, tables: set) -> dict:
        intel = {"total": 0, "ready": 0, "blocked": 0, "items": [], "gaps": []}

        if "filing_readiness" not in tables:
            intel["gaps"].append("filing_readiness table missing")
            return intel

        cols = self._table_cols(conn, "filing_readiness")
        intel["total"] = self._safe_count(conn, "filing_readiness")

        status_col = "status" if "status" in cols else None
        vehicle_col = "vehicle_name" if "vehicle_name" in cols else None

        if status_col:
            rows = conn.execute(
                f'SELECT "{status_col}", COUNT(*) FROM filing_readiness GROUP BY "{status_col}"'
            ).fetchall()
            intel["by_status"] = {r[0] or "unknown": r[1] for r in rows}

        if vehicle_col and status_col:
            rows = conn.execute(f'''
                SELECT "{vehicle_col}", "{status_col}" FROM filing_readiness
                WHERE "{status_col}" NOT IN ('complete', 'filed')
                ORDER BY "{vehicle_col}"
            ''').fetchall()
            intel["not_ready"] = [{"vehicle": r[0], "status": r[1]} for r in rows]
            intel["blocked"] = len(intel["not_ready"])

        return intel

    # ────────────────────────────────────────────────────────────
    # DEADLINE INTELLIGENCE — overdue, urgent, approaching
    # ────────────────────────────────────────────────────────────

    def _perceive_deadlines(self, conn, tables: set) -> dict:
        intel = {"overdue": [], "urgent_7d": [], "upcoming_30d": [], "total": 0, "gaps": []}

        if "deadlines" not in tables:
            intel["gaps"].append("deadlines table missing")
            return intel

        cols = self._table_cols(conn, "deadlines")
        intel["total"] = self._safe_count(conn, "deadlines")

        date_col = next(
            (c for c in ["due_date_iso", "deadline_date", "due_date"] if c in cols), None
        )
        if not date_col:
            intel["gaps"].append("No date column found in deadlines")
            return intel

        status_col = "status" if "status" in cols else None
        desc_col = next((c for c in ["description", "title", "name", "detail"] if c in cols), None)

        today = datetime.now().strftime("%Y-%m-%d")
        d7 = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        d30 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            where_active = f'AND "{status_col}" NOT IN (\'done\', \'filed\', \'complete\')' if status_col else ""

            # Overdue
            rows = conn.execute(f'''
                SELECT * FROM deadlines
                WHERE "{date_col}" < ? AND "{date_col}" IS NOT NULL AND "{date_col}" != ''
                {where_active}
                ORDER BY "{date_col}" ASC LIMIT 20
            ''', (today,)).fetchall()
            intel["overdue"] = [dict(r) for r in rows]

            # Urgent (next 7 days)
            rows = conn.execute(f'''
                SELECT * FROM deadlines
                WHERE "{date_col}" >= ? AND "{date_col}" <= ?
                {where_active}
                ORDER BY "{date_col}" ASC LIMIT 20
            ''', (today, d7)).fetchall()
            intel["urgent_7d"] = [dict(r) for r in rows]

            # Upcoming (next 30 days)
            rows = conn.execute(f'''
                SELECT * FROM deadlines
                WHERE "{date_col}" > ? AND "{date_col}" <= ?
                {where_active}
                ORDER BY "{date_col}" ASC LIMIT 20
            ''', (d7, d30)).fetchall()
            intel["upcoming_30d"] = [dict(r) for r in rows]

        except Exception as e:
            intel["gaps"].append(f"Query error: {str(e)[:100]}")

        intel["overdue_count"] = len(intel["overdue"])
        intel["urgent_count"] = len(intel["urgent_7d"])
        return intel

    # ────────────────────────────────────────────────────────────
    # AUTHORITY INTELLIGENCE — citations, coverage, strength
    # ────────────────────────────────────────────────────────────

    def _perceive_authorities(self, conn, tables: set) -> dict:
        intel = {"total": 0, "by_type": {}, "gaps": []}

        ami = "authority_master_index" if "authority_master_index" in tables else None
        if not ami:
            intel["gaps"].append("authority_master_index missing")
            return intel

        cols = self._table_cols(conn, ami)
        intel["total"] = self._safe_count(conn, ami)

        if "type" in cols:
            rows = conn.execute(f'SELECT type, COUNT(*) FROM {ami} GROUP BY type').fetchall()
            intel["by_type"] = {r[0] or "unknown": r[1] for r in rows}

        if "lanes" in cols:
            rows = conn.execute(f'SELECT lanes, COUNT(*) FROM {ami} GROUP BY lanes ORDER BY COUNT(*) DESC LIMIT 10').fetchall()
            intel["by_lane"] = {r[0] or "unassigned": r[1] for r in rows}

        return intel

    # ────────────────────────────────────────────────────────────
    # DATA QUALITY — hallucination residue, placeholder orphans
    # ────────────────────────────────────────────────────────────

    def _perceive_quality(self, conn, tables: set) -> dict:
        quality = {"hallucinations": [], "placeholder_issues": [], "score": 1.0}

        hallucination_patterns = [
            "Jane Berry", "Patricia Berry", "91% alienation",
            "Tiffany Watson", "Lincoln David Watson", "Ron Berry Esq",
            "P35878",
        ]

        check_tables = [t for t in [
            "evidence_quotes", "claims", "narrative_context",
            "critical_facts", "false_allegations", "police_reports",
        ] if t in tables]

        found_count = 0
        for table in check_tables:
            cols = self._table_cols(conn, table)
            text_cols = [c for c in cols if any(
                kw in c.lower()
                for kw in ["text", "content", "desc", "quote", "fact", "narrative", "detail", "body"]
            )]
            for col in text_cols[:3]:
                for pattern in hallucination_patterns:
                    try:
                        count = conn.execute(
                            f'SELECT COUNT(*) FROM "{table}" WHERE "{col}" LIKE ?',
                            (f"%{pattern}%",)
                        ).fetchone()[0]
                        if count > 0:
                            quality["hallucinations"].append({
                                "table": table, "column": col,
                                "pattern": pattern, "count": count,
                            })
                            found_count += count
                    except Exception:
                        pass

        quality["score"] = max(0.0, 1.0 - (found_count * 0.05))
        return quality

    # ────────────────────────────────────────────────────────────
    # ORPHAN DETECTION — records pointing to nothing
    # ────────────────────────────────────────────────────────────

    def _perceive_orphans(self, conn, tables: set) -> dict:
        orphans = {"issues": []}

        # Evidence quotes referencing non-existent claims
        if "evidence_quotes" in tables and "claims" in tables:
            eq_cols = self._table_cols(conn, "evidence_quotes")
            cl_cols = self._table_cols(conn, "claims")
            claim_id_col = "claim_id" if "claim_id" in eq_cols else None
            cl_id_col = "claim_id" if "claim_id" in cl_cols else "id" if "id" in cl_cols else None

            if claim_id_col and cl_id_col:
                try:
                    count = conn.execute(f'''
                        SELECT COUNT(*) FROM evidence_quotes eq
                        WHERE eq."{claim_id_col}" IS NOT NULL
                          AND eq."{claim_id_col}" != ''
                          AND eq."{claim_id_col}" NOT IN (
                              SELECT "{cl_id_col}" FROM claims
                          )
                    ''').fetchone()[0]
                    if count > 0:
                        orphans["issues"].append({
                            "type": "orphaned_evidence",
                            "desc": f"{count} evidence quotes reference non-existent claims",
                            "severity": 0.7,
                        })
                except Exception:
                    pass

        return orphans

    # ────────────────────────────────────────────────────────────
    # CROSS-REFERENCE GAPS — what should connect but doesn't
    # ────────────────────────────────────────────────────────────

    def _perceive_cross_refs(self, conn, tables: set) -> dict:
        gaps = []

        expected_links = [
            ("evidence_quotes", "claim_id", "claims", "Evidence→Claims linkage"),
            ("deadlines", "vehicle_name", "filing_readiness", "Deadlines→Filings linkage"),
            ("judicial_violations", "authority", "authority_master_index", "Judicial→Authority linkage"),
        ]

        for src_table, src_col, dst_table, desc in expected_links:
            if src_table not in tables or dst_table not in tables:
                gaps.append({"link": desc, "status": "missing_table", "severity": 0.6})
                continue

            src_cols = self._table_cols(conn, src_table)
            if src_col not in src_cols:
                gaps.append({"link": desc, "status": "missing_column", "severity": 0.5})
                continue

            try:
                null_count = conn.execute(
                    f'SELECT COUNT(*) FROM "{src_table}" WHERE "{src_col}" IS NULL OR "{src_col}" = \'\''
                ).fetchone()[0]
                total = self._safe_count(conn, src_table)
                if total > 0 and null_count / total > 0.5:
                    gaps.append({
                        "link": desc,
                        "status": "weak",
                        "null_rate": round(null_count / total * 100, 1),
                        "severity": 0.7,
                    })
            except Exception:
                pass

        return {"gaps": gaps}


class FleetPerception:
    """
    Analyzes the agent/skill/tool fleet to find capability gaps,
    redundancies, and optimization opportunities.
    """

    DIRS = {
        "agents": REPO_ROOT / ".agents" / "agents",
        "skills": REPO_ROOT / ".agents" / "skills",
        "tools": REPO_ROOT / "00_SYSTEM" / "tools",
        "pipeline": REPO_ROOT / "00_SYSTEM" / "pipeline",
        "scripts": REPO_ROOT / "00_SYSTEM" / "scripts",
        "mcp": REPO_ROOT / "00_SYSTEM" / "mcp_server",
    }

    DOMAIN_KEYWORDS = {
        "evidence": ["evidence", "exhibit", "bates", "chain_of_custody", "authenticate"],
        "filing": ["filing", "motion", "brief", "petition", "complaint", "pleading"],
        "deadline": ["deadline", "calendar", "schedule", "docket", "timeline"],
        "judicial": ["judicial", "judge", "mcneill", "recusal", "disqualif", "jtc", "misconduct"],
        "appellate": ["appell", "coa", "msc", "appeal", "certiorari"],
        "custody": ["custody", "parenting", "child", "best_interest", "foc"],
        "housing": ["housing", "shady_oaks", "evict", "title", "property", "landlord"],
        "ppo": ["ppo", "protection_order", "contempt", "restrain"],
        "criminal": ["criminal", "self_defense", "misdemeanor", "arraign"],
        "discovery": ["discovery", "foia", "subpoena", "interrogator", "deposition"],
        "research": ["research", "citation", "authority", "case_law", "statute"],
        "automation": ["automat", "pipeline", "workflow", "orchestrat", "daemon"],
    }

    def perceive(self) -> dict:
        inventory = self._build_inventory()
        coverage = self._analyze_coverage(inventory)
        redundancy = self._find_redundancies(inventory)
        return {
            "inventory": {k: len(v) for k, v in inventory.items()},
            "coverage": coverage,
            "redundancy": redundancy,
            "darwin_state": self._perceive_darwin(),
        }

    def _build_inventory(self) -> dict:
        inv = {}
        for category, path in self.DIRS.items():
            items = []
            if path.exists():
                for f in path.iterdir():
                    if f.name.startswith(".") or f.name == "__pycache__":
                        continue
                    if f.is_file() and f.suffix in (".py", ".md"):
                        items.append(f.stem)
                    elif f.is_dir():
                        items.append(f.name)
            inv[category] = items
        return inv

    def _analyze_coverage(self, inventory: dict) -> dict:
        """Map every component to domains and find gaps."""
        domain_coverage = {d: {"components": [], "count": 0} for d in self.DOMAIN_KEYWORDS}
        all_names = []
        for items in inventory.values():
            all_names.extend(items)

        for name in all_names:
            name_lower = name.lower().replace("-", "_")
            for domain, keywords in self.DOMAIN_KEYWORDS.items():
                if any(kw in name_lower for kw in keywords):
                    domain_coverage[domain]["components"].append(name)
                    domain_coverage[domain]["count"] += 1

        gaps = []
        for domain, info in domain_coverage.items():
            if info["count"] == 0:
                gaps.append({"domain": domain, "severity": "CRITICAL", "score": 1.0})
            elif info["count"] < 3:
                gaps.append({"domain": domain, "severity": "WEAK", "score": 0.6})

        return {"domains": {d: v["count"] for d, v in domain_coverage.items()}, "gaps": gaps}

    def _find_redundancies(self, inventory: dict) -> list:
        """Find components that overlap significantly."""
        redundancies = []
        all_items = []
        for category, items in inventory.items():
            for item in items:
                all_items.append((item, category))

        # Group by similar names
        from collections import defaultdict
        groups = defaultdict(list)
        for name, cat in all_items:
            base = name.lower().replace("-", "_").replace("omega_", "").replace("omega-", "")
            for key_word in ["evidence", "filing", "deadline", "judicial", "custody", "research"]:
                if key_word in base:
                    groups[key_word].append((name, cat))
                    break

        for keyword, items in groups.items():
            if len(items) > 5:
                redundancies.append({
                    "domain": keyword,
                    "count": len(items),
                    "components": [f"{n} ({c})" for n, c in items[:8]],
                })

        return redundancies

    def _perceive_darwin(self) -> dict:
        """Check DARWIN engine state for agent evolution data."""
        if not DARWIN_DB.exists():
            return {"status": "not_initialized"}

        conn = _safe_connect(DARWIN_DB)
        if not conn:
            return {"status": "connection_failed"}

        try:
            tables = set(r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall())

            result = {"status": "active", "tables": list(tables)}

            if "genomes" in tables:
                row = conn.execute("SELECT COUNT(*), MAX(generation) FROM genomes").fetchone()
                result["genome_count"] = row[0]
                result["max_generation"] = row[1]

            if "evolution_log" in tables:
                result["evolution_events"] = self._safe_count_ext(conn, "evolution_log")

            return result
        finally:
            conn.close()

    @staticmethod
    def _safe_count_ext(conn, table):
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception:
            return 0


class FilesystemPerception:
    """
    Scans the actual filesystem for unprocessed files, orphaned outputs,
    and structural issues.
    """

    SCAN_DIRS = {
        "filings": REPO_ROOT / "01_FILINGS",
        "evidence": REPO_ROOT / "02_EVIDENCE",
        "generated": REPO_ROOT / "GENERATED_FILINGS",
        "tools": REPO_ROOT / "00_SYSTEM" / "tools",
        "temp": REPO_ROOT / "temp",
    }

    def perceive(self) -> dict:
        result = {}
        for name, path in self.SCAN_DIRS.items():
            if path.exists():
                result[name] = self._scan_directory(path)
            else:
                result[name] = {"exists": False}

        result["repo_health"] = self._check_repo_health()
        return result

    def _scan_directory(self, path: Path) -> dict:
        files = []
        total_size = 0
        by_ext = Counter()

        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.name.startswith("."):
                    files.append(str(f.relative_to(REPO_ROOT)))
                    total_size += f.stat().st_size
                    by_ext[f.suffix.lower()] += 1
        except PermissionError:
            pass

        return {
            "exists": True,
            "file_count": len(files),
            "total_size_mb": round(total_size / (1024 * 1024), 1),
            "by_extension": dict(by_ext.most_common(10)),
        }

    def _check_repo_health(self) -> dict:
        issues = []

        # Check for stale temp files
        temp_dir = REPO_ROOT / "temp"
        if temp_dir.exists():
            old_files = []
            cutoff = datetime.now() - timedelta(days=7)
            for f in temp_dir.iterdir():
                if f.is_file():
                    try:
                        mtime = datetime.fromtimestamp(f.stat().st_mtime)
                        if mtime < cutoff:
                            old_files.append(f.name)
                    except Exception:
                        pass
            if old_files:
                issues.append({
                    "type": "stale_temp_files",
                    "count": len(old_files),
                    "severity": 0.3,
                })

        # Check for shadow modules in repo root
        shadow_names = [
            "json.py", "typing.py", "tokenize.py", "numpy.py", "pandas.py",
            "csv.py", "re.py", "os.py", "sys.py", "collections.py",
        ]
        found_shadows = [n for n in shadow_names if (REPO_ROOT / n).exists()]
        if found_shadows:
            issues.append({
                "type": "shadow_modules",
                "count": len(found_shadows),
                "names": found_shadows,
                "severity": 0.8,
            })

        return {"issues": issues}


# ─── Unified Perception API ──────────────────────────────────────────────

class PerceptionEngine:
    """
    Unified perception across all three layers.
    Returns a single coherent picture of the entire system.
    """

    def __init__(self):
        self.db = DatabasePerception()
        self.fleet = FleetPerception()
        self.fs = FilesystemPerception()

    def full_perception(self) -> dict:
        """Run all three perception layers and synthesize."""
        db_state = self.db.perceive()
        fleet_state = self.fleet.perceive()
        fs_state = self.fs.perceive()

        # Synthesize into actionable intelligence
        synthesis = self._synthesize(db_state, fleet_state, fs_state)

        return {
            "database": db_state,
            "fleet": fleet_state,
            "filesystem": fs_state,
            "synthesis": synthesis,
            "timestamp": datetime.now().isoformat(),
        }

    def _synthesize(self, db: dict, fleet: dict, fs: dict) -> dict:
        """Cross-reference all three perception layers to find the highest-value opportunities."""
        opportunities = []

        # DB gaps that fleet can't address
        db_evidence = db.get("evidence_intelligence", {})
        if db_evidence.get("unlinked", 0) > 100:
            opportunities.append({
                "type": "evidence_linkage",
                "priority": "CRITICAL",
                "desc": f"{db_evidence['unlinked']} evidence items have no claim linkage — "
                        f"a tool to auto-link evidence to claims would immediately strengthen the case",
                "invention_type": "tool",
                "domains": ["evidence_processing", "pattern_recognition"],
            })

        # Overdue deadlines with no matching agent
        deadline_state = db.get("deadline_intelligence", {})
        if deadline_state.get("overdue_count", 0) > 0:
            opportunities.append({
                "type": "deadline_response",
                "priority": "CRITICAL",
                "desc": f"{deadline_state['overdue_count']} overdue deadlines — "
                        f"need automatic deadline monitoring and response generation",
                "invention_type": "tool",
                "domains": ["deadline_management", "filing_generation"],
            })

        # Domain coverage gaps in fleet
        for gap in fleet.get("coverage", {}).get("gaps", []):
            opportunities.append({
                "type": "fleet_gap",
                "priority": gap.get("severity", "WEAK"),
                "desc": f"No components cover the '{gap['domain']}' domain — "
                        f"need agents/tools/skills for this area",
                "invention_type": "agent",
                "domains": [gap["domain"]],
            })

        # Data quality issues
        quality = db.get("data_quality", {})
        if quality.get("hallucinations"):
            opportunities.append({
                "type": "data_decontamination",
                "priority": "CRITICAL",
                "desc": f"{len(quality['hallucinations'])} hallucination residue entries found — "
                        f"need automated decontamination sweep tool",
                "invention_type": "tool",
                "domains": ["quality_assurance"],
            })

        # Sort by priority
        priority_order = {"CRITICAL": 0, "WEAK": 1, "LOW": 2}
        opportunities.sort(key=lambda x: priority_order.get(x["priority"], 99))

        return {
            "opportunity_count": len(opportunities),
            "critical_count": sum(1 for o in opportunities if o["priority"] == "CRITICAL"),
            "opportunities": opportunities,
        }

    def quick_report(self) -> str:
        """Generate a human-readable perception report."""
        p = self.full_perception()
        lines = []
        lines.append("╔══════════════════════════════════════════════════════════════╗")
        lines.append("║           NOVEL v2 — PERCEPTION ENGINE REPORT               ║")
        lines.append("╠══════════════════════════════════════════════════════════════╣")

        # DB state
        census = p["database"].get("table_census", {})
        lines.append(f"║  DATABASE: {census.get('total_tables', '?')} tables, "
                     f"{census.get('total_rows', '?'):,} rows, "
                     f"{census.get('empty_count', '?')} empty")

        # Evidence
        ev = p["database"].get("evidence_intelligence", {})
        lines.append(f"║  EVIDENCE: {ev.get('total', 0):,} items, "
                     f"{ev.get('unlinked', 0):,} unlinked "
                     f"({ev.get('link_rate', '?')}% linked)")

        # Deadlines
        dl = p["database"].get("deadline_intelligence", {})
        lines.append(f"║  DEADLINES: {dl.get('overdue_count', 0)} overdue, "
                     f"{dl.get('urgent_count', 0)} urgent (7d)")

        # Fleet
        inv = p["fleet"].get("inventory", {})
        lines.append(f"║  FLEET: {inv.get('agents', 0)} agents, "
                     f"{inv.get('skills', 0)} skills, "
                     f"{inv.get('tools', 0)} tools")

        # Quality
        q = p["database"].get("data_quality", {})
        h_count = len(q.get("hallucinations", []))
        quality_emoji = "✅" if h_count == 0 else "⚠️"
        lines.append(f"║  QUALITY: {quality_emoji} score={q.get('score', '?')}, "
                     f"hallucination residue={h_count}")

        # Synthesis
        syn = p.get("synthesis", {})
        lines.append(f"║  OPPORTUNITIES: {syn.get('opportunity_count', 0)} found, "
                     f"{syn.get('critical_count', 0)} critical")

        lines.append("╠══════════════════════════════════════════════════════════════╣")

        for opp in syn.get("opportunities", [])[:8]:
            icon = "🔴" if opp["priority"] == "CRITICAL" else "🟡"
            desc = opp["desc"][:56]
            lines.append(f"║  {icon} {desc}")

        lines.append("╚══════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)
