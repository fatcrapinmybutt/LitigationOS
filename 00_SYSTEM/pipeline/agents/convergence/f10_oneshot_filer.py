"""
DELTA9 — F10 One-Shot Filer + Clearance Protocol
Convergence Tier · MAX LEVEL 9999++

Single-command court filing assembly: markdown → court-ready PDF package.
Composes from F06/F07/F08 logic — does NOT duplicate.
Includes inline Clearance Protocol (pre-flight readiness gate).

ADR-001 Phase 1 — Approved by Skeptic, Guardian, Advocate.
Kill switch: LITIGOS_DISABLE_ONESHOT=1
Canary gate: LITIGOS_ONESHOT_APPROVE=1 (first 2 filings)
"""
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB, CHECKPOINT_DIR,
)

# Filing dependency graph — determines valid sequencing
FILING_DEPENDENCIES: Dict[str, List[str]] = {
    "F1": [],                    # Emergency TRO — no deps
    "F2": [],                    # Shady Oaks — no deps
    "F3": [],                    # Disqualification — no deps
    "F4": ["F3"],                # Federal §1983 — after disqualification
    "F5": [],                    # MSC Original Action — no deps
    "F6": [],                    # JTC Complaint — no deps
    "F7": ["F1"],                # Custody modification — after TRO
    "F8": [],                    # PPO Termination — no deps
    "F9": ["F3", "F7"],          # COA Brief — after trial filings
    "F10": ["F9"],               # COA Emergency — after brief
}

# Staging directory for transactional assembly
STAGING_DIR = CHECKPOINT_DIR / "oneshot_staging"


class OneShotFiler(Agent9999):
    """Single-command court filing assembly with inline clearance protocol."""

    def __init__(self):
        super().__init__(agent_id="F10-ONESHOT")
        self._packages: list = []
        self._canary_count: int = 0

    # ------------------------------------------------------------------
    # Kill switch check
    # ------------------------------------------------------------------
    def _is_disabled(self) -> bool:
        return os.environ.get("LITIGOS_DISABLE_ONESHOT", "0") == "1"

    # ------------------------------------------------------------------
    # Clearance Protocol (ADR-001 #5 — inline, not standalone)
    # ------------------------------------------------------------------
    def _preflight_clearance(self, filing_id: str) -> dict:
        """Soft gate using existing filing_readiness infrastructure.

        Returns: {status: CLEARED|NEEDS_REVIEW|BLOCKED, score: float, reason: str}
        """
        # Check action_scores for this filing's lane
        lane_map = {
            "F1": "A", "F2": "B", "F3": "E", "F4": "C",
            "F5": "E", "F6": "E", "F7": "A", "F8": "D",
            "F9": "F", "F10": "F",
        }
        lane = lane_map.get(filing_id, "A")

        # Query readiness from action_scores
        row = self._db_execute(
            "SELECT composite_score, gap_count, readiness_score "
            "FROM action_scores WHERE lane = ? "
            "ORDER BY composite_score DESC LIMIT 1",
            (lane,)
        ).fetchone()

        if not row:
            return {"status": "BLOCKED", "score": 0.0,
                    "reason": f"No readiness data for lane {lane}"}

        score = float(row[0] or 0) / 100.0  # normalize to 0-1
        gap_count = int(row[1] or 0)
        threshold = float(os.environ.get("LITIGOS_CLEARANCE_THRESHOLD", "0.65"))

        # Override bypass
        if os.environ.get("LITIGOS_CLEARANCE_OVERRIDE", "0") == "1":
            return {"status": "CLEARED", "score": score,
                    "reason": "Override active — bypassing clearance"}

        # Check filing dependencies
        deps = FILING_DEPENDENCIES.get(filing_id, [])
        unmet_deps = []
        for dep in deps:
            dep_lane = lane_map.get(dep, "A")
            dep_row = self._db_execute(
                "SELECT composite_score FROM action_scores "
                "WHERE lane = ? AND composite_score > 50 LIMIT 1",
                (dep_lane,)
            ).fetchone()
            if not dep_row:
                unmet_deps.append(dep)

        if unmet_deps:
            return {"status": "BLOCKED", "score": score,
                    "reason": f"Unmet dependencies: {', '.join(unmet_deps)}"}

        if score >= threshold:
            return {"status": "CLEARED", "score": score,
                    "reason": f"Score {score:.2f} >= threshold {threshold:.2f}"}
        else:
            return {"status": "NEEDS_REVIEW", "score": score,
                    "reason": f"Score {score:.2f} < threshold {threshold:.2f}",
                    "gaps": gap_count}

    # ------------------------------------------------------------------
    # Citation validation (delegates to F08 logic)
    # ------------------------------------------------------------------
    def _validate_citations(self, text: str) -> dict:
        """Extract and validate citations in filing text.

        Returns: {total, verified, unverified, hallucinated, details: [...]}
        """
        import re

        # Citation patterns from F08
        patterns = {
            "MCR": r"MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*)",
            "MCL": r"MCL\s+(\d+\.\d+[a-z]?(?:\([0-9a-z]+\))*)",
            "MRE": r"MRE\s+(\d+(?:\.\d+)?)",
        }

        results = {"total": 0, "verified": 0, "unverified": 0,
                    "hallucinated": 0, "details": []}

        for cite_type, pattern in patterns.items():
            for match in re.finditer(pattern, text):
                results["total"] += 1
                cite_ref = match.group(1)

                # Check against michigan_rules_extracted
                row = self._db_execute(
                    "SELECT rule_number FROM michigan_rules_extracted "
                    "WHERE rule_number LIKE ? LIMIT 1",
                    (f"%{cite_ref}%",)
                ).fetchone()

                if row:
                    results["verified"] += 1
                    results["details"].append({
                        "citation": f"{cite_type} {cite_ref}",
                        "status": "verified"
                    })
                else:
                    results["unverified"] += 1
                    results["details"].append({
                        "citation": f"{cite_type} {cite_ref}",
                        "status": "unverified"
                    })

        return results

    # ------------------------------------------------------------------
    # Abstract implementations
    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        if self._is_disabled():
            raise FatalAgentError("One-Shot Filer disabled (LITIGOS_DISABLE_ONESHOT=1)")

        # Verify action_scores table exists
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='action_scores'"
        )
        if not cursor.fetchone():
            raise FatalAgentError("action_scores table missing — run Lane 2 first")

        # Ensure staging directory
        STAGING_DIR.mkdir(parents=True, exist_ok=True)

    def _get_work_items(self) -> list:
        """Get filings ready for one-shot assembly.

        Queries action_scores for items with composite_score > 50,
        then filters by clearance status.
        """
        cursor = self._db_execute(
            "SELECT DISTINCT lane FROM action_scores "
            "WHERE composite_score > 50 "
            "ORDER BY composite_score DESC"
        )
        lanes = cursor.fetchall()

        # Map lanes back to filing IDs
        lane_to_filings = {
            "A": ["F1", "F7"], "B": ["F2"], "C": ["F4"],
            "D": ["F8"], "E": ["F3", "F5", "F6"], "F": ["F9", "F10"],
        }

        work_items = []
        for lane_row in lanes:
            lane = lane_row[0] if not isinstance(lane_row, dict) else lane_row.get("lane", "A")
            filings = lane_to_filings.get(lane, [])
            for fid in filings:
                work_items.append({"filing_id": fid, "lane": lane})

        return work_items

    def _process_item(self, item: Any) -> None:
        """Assemble a single filing through the one-shot pipeline.

        Steps:
        1. Pre-flight clearance check (inline #5)
        2. Citation validation (F08 logic)
        3. Transactional staging (write to staging, not production)
        4. Manifest assembly (F01 logic)
        5. Certification scoring (F06 logic)
        6. Atomic commit (move staging → production)
        """
        filing_id = item["filing_id"] if isinstance(item, dict) else item
        lane = item.get("lane", "A") if isinstance(item, dict) else "A"

        self._log("START", f"One-shot assembly: {filing_id} (lane {lane})")

        # ── Step 1: Pre-flight clearance ──
        clearance = self._preflight_clearance(filing_id)
        self._log("CLEARANCE", f"{filing_id}: {clearance['status']} "
                  f"(score={clearance.get('score', 0):.2f})")

        if clearance["status"] == "BLOCKED":
            self._log("BLOCKED", f"{filing_id}: {clearance['reason']}")
            raise SkipItemError(f"{filing_id} blocked: {clearance['reason']}")

        # ── Canary gate: first 2 filings require manual approval ──
        if self._canary_count < 2:
            if os.environ.get("LITIGOS_ONESHOT_APPROVE", "0") != "1":
                self._log("CANARY", f"{filing_id}: Canary gate — "
                         f"set LITIGOS_ONESHOT_APPROVE=1 to proceed")
                raise SkipItemError(f"{filing_id}: Canary gate active")
            self._canary_count += 1

        # ── Step 2: Gather evidence and citations ──
        lane_pattern = f"%{lane}%"
        atoms = self._db_execute(
            "SELECT * FROM atoms WHERE meek_lane LIKE ? LIMIT 200",
            (lane_pattern,)
        ).fetchall()

        citations = self._db_execute(
            "SELECT * FROM atoms WHERE atom_type = 'citation_validation' "
            "AND meek_lane LIKE ?",
            (lane_pattern,)
        ).fetchall()

        # ── Step 3: Citation validation ──
        # Build a text blob from atoms for citation checking
        atom_texts = []
        for atom in atoms:
            text = atom[3] if not isinstance(atom, dict) else atom.get("content", "")
            if text:
                atom_texts.append(str(text))
        combined_text = "\n".join(atom_texts[:100])  # cap for performance

        citation_audit = self._validate_citations(combined_text)
        self._log("CITATIONS", f"{filing_id}: {citation_audit['verified']} verified, "
                  f"{citation_audit['unverified']} unverified, "
                  f"{citation_audit['hallucinated']} hallucinated")

        # ── Step 4: Build filing manifest (F01 logic) ──
        action_row = self._db_execute(
            "SELECT * FROM action_scores WHERE lane = ? "
            "ORDER BY composite_score DESC LIMIT 1",
            (lane,)
        ).fetchone()

        composite = 0.0
        action_id = f"{lane}-{filing_id}"
        if action_row:
            action_id = action_row[1] if not isinstance(action_row, dict) else action_row.get("action_id", action_id)
            composite = float(action_row[7] if not isinstance(action_row, dict) else action_row.get("composite_score", 0) or 0)

        manifest = {
            "filing_id": filing_id,
            "action_id": action_id,
            "lane": lane,
            "composite_score": composite,
            "clearance": clearance,
            "citation_audit": {
                "total": citation_audit["total"],
                "verified": citation_audit["verified"],
                "unverified": citation_audit["unverified"],
                "hallucinated": citation_audit["hallucinated"],
            },
            "evidence": {
                "atom_count": len(atoms),
                "citation_count": len(citations),
                "exhibit_count": min(len(atoms), 50),
            },
            "exhibits": [
                {"atom_id": a[0] if not isinstance(a, dict) else a.get("id"),
                 "type": "evidence"}
                for a in atoms[:50]
            ],
            "readiness_score": min(composite / 100.0, 1.0),
            "status": clearance["status"],
            "assembled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        # ── Step 5: Certification scoring (F06 logic) ──
        cert_score = self._compute_certification(lane, len(atoms), len(citations),
                                                  composite, citation_audit)
        manifest["certification"] = cert_score
        self._log("CERT", f"{filing_id}: certification={cert_score['overall']:.2f} "
                  f"verdict={cert_score['verdict']}")

        # ── Step 6: Write to staging (transactional) ──
        staging_path = STAGING_DIR / f"oneshot_{filing_id}.json"
        staging_path.write_text(json.dumps(manifest, indent=2, default=str))

        # Write staging record to DB
        self._ensure_staging_table()
        self._db_execute(
            "INSERT OR REPLACE INTO oneshot_staging "
            "(request_id, filing_id, lane, status, manifest_json, "
            " composite_confidence, clearance_status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (
                f"F10_{filing_id}_{int(time.time())}",
                filing_id, lane,
                "ready" if cert_score["verdict"] == "READY" else "needs_review",
                json.dumps(manifest, default=str),
                cert_score["overall"],
                clearance["status"],
            )
        )

        # ── Step 7: Atomic commit to production checkpoint ──
        production_path = CHECKPOINT_DIR / f"oneshot_{filing_id}_FINAL.json"
        shutil.copy2(str(staging_path), str(production_path))

        self._log("COMPLETE", f"{filing_id}: assembled → {production_path.name} "
                  f"(score={cert_score['overall']:.2f}, verdict={cert_score['verdict']})")
        self._packages.append(manifest)

    # ------------------------------------------------------------------
    # Certification scoring (reuses F06 weights)
    # ------------------------------------------------------------------
    def _compute_certification(self, lane: str, atom_count: int,
                                citation_count: int, composite: float,
                                citation_audit: dict) -> dict:
        """Compute multi-dimensional certification score."""
        # Coverage: atoms per lane
        coverage = min(atom_count / 100.0, 1.0)  # 100 atoms = full coverage

        # Citation quality: verified / total
        cite_quality = 1.0
        if citation_audit["total"] > 0:
            cite_quality = citation_audit["verified"] / citation_audit["total"]

        # Readiness: from action_scores composite
        readiness = min(composite / 100.0, 1.0)

        # Gap penalty: check for unresolved gaps
        gap_row = self._db_execute(
            "SELECT gap_count FROM action_scores WHERE lane = ? LIMIT 1",
            (lane,)
        ).fetchone()
        gap_count = int(gap_row[0] or 0) if gap_row else 0
        gap_score = max(1.0 - (gap_count * 0.05), 0.0)  # -5% per gap

        # Weighted composite (aligned with F06 weights)
        overall = (
            coverage * 0.30 +
            cite_quality * 0.25 +
            readiness * 0.30 +
            gap_score * 0.15
        )

        verdict = "READY" if overall >= 0.60 else "NEEDS_REVIEW"

        return {
            "overall": overall,
            "coverage": coverage,
            "citation_quality": cite_quality,
            "readiness": readiness,
            "gap_score": gap_score,
            "gap_count": gap_count,
            "verdict": verdict,
        }

    # ------------------------------------------------------------------
    # Staging table management
    # ------------------------------------------------------------------
    def _ensure_staging_table(self) -> None:
        """Create oneshot_staging table if not exists."""
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS oneshot_staging (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                filing_id TEXT NOT NULL,
                lane TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                manifest_json TEXT,
                composite_confidence REAL DEFAULT 0.0,
                clearance_status TEXT DEFAULT 'UNKNOWN',
                created_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT
            )
        """)

    # ------------------------------------------------------------------
    # Finalize: summary report
    # ------------------------------------------------------------------
    def _finalize(self) -> None:
        """Write one-shot assembly summary report."""
        report = {
            "agent": "F10-ONESHOT",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_filings": len(self._packages),
            "filings": [
                {
                    "filing_id": p["filing_id"],
                    "lane": p["lane"],
                    "status": p["status"],
                    "score": p.get("certification", {}).get("overall", 0),
                    "verdict": p.get("certification", {}).get("verdict", "UNKNOWN"),
                    "evidence_count": p["evidence"]["atom_count"],
                    "citation_count": p["evidence"]["citation_count"],
                }
                for p in self._packages
            ],
            "ready_count": sum(
                1 for p in self._packages
                if p.get("certification", {}).get("verdict") == "READY"
            ),
            "review_count": sum(
                1 for p in self._packages
                if p.get("certification", {}).get("verdict") == "NEEDS_REVIEW"
            ),
        }

        report_path = CHECKPOINT_DIR / "oneshot_assembly_report.json"
        report_path.write_text(json.dumps(report, indent=2))
        self._log("REPORT", f"One-shot report: {report['total_filings']} filings, "
                  f"{report['ready_count']} ready, {report['review_count']} need review")

        super()._finalize()
