"""Filing Priority & Sequencing Optimizer.

Analyzes all 10 filings across vulnerability, strength, urgency, and
dependencies to produce an optimal filing order.  Factors in:

- IRAC scores (claim strength)
- Opposition vulnerability (from opposition_analysis)
- Authority chain completeness
- Cross-filing dependencies (from filing_cross_reference)
- Court-specific deadlines
- Strategic sequencing (what filing strengthens the next)

Usage::

    opt = FilingPriorityOptimizer()
    order = opt.optimal_filing_order()
    report = opt.generate_strategy_report()
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# Filing metadata — courts, deadlines, strategic value
FILING_REGISTRY: dict[str, dict[str, Any]] = {
    "F1": {
        "name": "Emergency TRO",
        "court": "14th Circuit",
        "lane": "A",
        "urgency": 8,
        "strategic_notes": "Must file before F7 to establish immediate need",
    },
    "F2": {
        "name": "Shady Oaks Housing",
        "court": "14th Circuit",
        "lane": "B",
        "urgency": 4,
        "strategic_notes": "Independent lane — can file anytime",
    },
    "F3": {
        "name": "Judicial Disqualification",
        "court": "14th Circuit",
        "lane": "E",
        "urgency": 9,
        "strategic_notes": "MUST file before F7 — no point filing custody motion before biased judge",
    },
    "F4": {
        "name": "Federal §1983 Complaint",
        "court": "Federal WDMI",
        "lane": "A",
        "urgency": 7,
        "strategic_notes": "Parallel federal action — strengthens all state filings",
    },
    "F5": {
        "name": "MSC Bypass Application",
        "court": "Michigan Supreme Court",
        "lane": "F",
        "urgency": 6,
        "strategic_notes": "File after F9 COA brief to show appellate exhaustion",
    },
    "F6": {
        "name": "JTC Formal Complaint",
        "court": "JTC",
        "lane": "E",
        "urgency": 7,
        "strategic_notes": "Supports F3 disqualification — external validator of bias",
    },
    "F7": {
        "name": "Custody Modification",
        "court": "14th Circuit",
        "lane": "A",
        "urgency": 10,
        "strategic_notes": "Core filing — but file AFTER F3 succeeds or simultaneously",
    },
    "F8": {
        "name": "PPO Modification/Dismissal",
        "court": "14th Circuit",
        "lane": "D",
        "urgency": 6,
        "strategic_notes": "Supports custody narrative — PPO was weaponized",
    },
    "F9": {
        "name": "COA Appeal Brief",
        "court": "COA",
        "lane": "F",
        "urgency": 9,
        "strategic_notes": "Deadline-driven — must meet COA briefing schedule",
    },
    "F10": {
        "name": "COA Emergency Motion",
        "court": "COA",
        "lane": "F",
        "urgency": 10,
        "strategic_notes": "File simultaneously with F9 for immediate relief",
    },
}

# Strategic dependencies — filing A should come before filing B
FILING_DEPENDENCIES: list[tuple[str, str, str]] = [
    ("F3", "F7", "Disqualification must precede or accompany custody motion"),
    ("F6", "F3", "JTC complaint validates bias claim in disqualification"),
    ("F9", "F5", "COA brief should precede MSC bypass to show exhaustion"),
    ("F10", "F9", "Emergency motion filed with or after brief"),
    ("F1", "F7", "TRO establishes immediate need before custody hearing"),
    ("F4", "F3", "Federal complaint strengthens disqualification narrative"),
    ("F3", "F8", "Judge removal before PPO hearing in same court"),
]


class FilingPriorityOptimizer:
    """Analyze and optimize filing order across all 10 packages."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        logger.info("FilingPriorityOptimizer ready  db=%s", self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=60)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
        return conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone()[0] > 0

    def _get_irac_scores(self) -> dict[str, float]:
        """Pull IRAC strength scores from DB."""
        conn = self._connect()
        try:
            if not self._table_exists(conn, "irac_analysis"):
                return {}
            rows = conn.execute(
                "SELECT filing_id, score FROM irac_analysis WHERE filing_id IS NOT NULL"
            ).fetchall()
            return {r["filing_id"]: float(r["score"]) for r in rows}
        except Exception:
            return {}
        finally:
            conn.close()

    def _get_vulnerability_scores(self) -> dict[str, float]:
        """Pull opposition vulnerability scores from DB."""
        conn = self._connect()
        try:
            if not self._table_exists(conn, "filing_vulnerability_scores"):
                return {}
            rows = conn.execute(
                "SELECT filing_id, overall_vulnerability FROM filing_vulnerability_scores"
            ).fetchall()
            return {r["filing_id"]: float(r["overall_vulnerability"]) for r in rows}
        except Exception:
            return {}
        finally:
            conn.close()

    def _get_authority_completeness(self) -> dict[str, float]:
        """Pull authority chain completeness from DB."""
        conn = self._connect()
        try:
            if not self._table_exists(conn, "authority_chain_summary"):
                return {}
            rows = conn.execute(
                "SELECT filing_id, score FROM authority_chain_summary"
            ).fetchall()
            return {r["filing_id"]: float(r["score"]) for r in rows}
        except Exception:
            return {}
        finally:
            conn.close()

    def _get_exhibit_counts(self) -> dict[str, int]:
        """Pull exhibit counts per filing from DB."""
        conn = self._connect()
        try:
            if not self._table_exists(conn, "exhibit_binders"):
                return {}
            rows = conn.execute(
                "SELECT filing_id, COUNT(*) as cnt FROM exhibit_binders GROUP BY filing_id"
            ).fetchall()
            return {r["filing_id"]: r["cnt"] for r in rows}
        except Exception:
            return {}
        finally:
            conn.close()

    def score_filing(self, filing_id: str) -> dict[str, Any]:
        """Compute composite priority score for a single filing."""
        reg = FILING_REGISTRY.get(filing_id, {})
        irac = self._get_irac_scores()
        vuln = self._get_vulnerability_scores()
        auth = self._get_authority_completeness()
        exhibits = self._get_exhibit_counts()

        urgency = reg.get("urgency", 5)
        strength = irac.get(filing_id, 5.0)
        vulnerability = vuln.get(filing_id, 5.0)
        authority_score = auth.get(filing_id, 1.0)
        exhibit_count = exhibits.get(filing_id, 0)

        # Composite: high urgency + high strength + low vulnerability + complete authorities
        # Scale: 0-100
        composite = (
            urgency * 3.0                          # 0-30 (urgency weight)
            + strength * 2.0                       # 0-20 (legal strength)
            + (10 - vulnerability) * 2.0           # 0-20 (inverse vulnerability)
            + min(authority_score, 7) * 2.0        # 0-14 (authority completeness)
            + min(exhibit_count / 200, 1) * 16     # 0-16 (evidence depth)
        )

        return {
            "filing_id": filing_id,
            "name": reg.get("name", filing_id),
            "court": reg.get("court", "Unknown"),
            "lane": reg.get("lane", "?"),
            "urgency": urgency,
            "strength": strength,
            "vulnerability": vulnerability,
            "authority_score": authority_score,
            "exhibit_count": exhibit_count,
            "composite_score": round(composite, 1),
            "strategic_notes": reg.get("strategic_notes", ""),
        }

    def optimal_filing_order(self) -> list[dict[str, Any]]:
        """Return all filings sorted by optimal filing order.

        Considers: composite score, dependencies, strategic sequencing.
        """
        scored = [self.score_filing(fid) for fid in FILING_REGISTRY]
        scored.sort(key=lambda x: x["composite_score"], reverse=True)

        # Apply dependency adjustments — if A depends on B, B must come first
        order = [s["filing_id"] for s in scored]
        for dep_first, dep_after, _reason in FILING_DEPENDENCIES:
            if dep_first in order and dep_after in order:
                idx_first = order.index(dep_first)
                idx_after = order.index(dep_after)
                if idx_first > idx_after:
                    # Move dep_first before dep_after
                    order.remove(dep_first)
                    order.insert(idx_after, dep_first)

        # Rebuild scored list in new order
        score_map = {s["filing_id"]: s for s in scored}
        return [score_map[fid] for fid in order if fid in score_map]

    def generate_strategy_report(self) -> str:
        """Generate a human-readable filing strategy report."""
        order = self.optimal_filing_order()
        lines = [
            "# FILING PRIORITY & SEQUENCING REPORT",
            f"_Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}_\n",
            "## Optimal Filing Order\n",
            "| Priority | Filing | Court | Score | Urgency | Strength | Vuln | Exhibits |",
            "|----------|--------|-------|-------|---------|----------|------|----------|",
        ]
        for i, f in enumerate(order, 1):
            lines.append(
                f"| {i} | **{f['filing_id']}** {f['name']} | {f['court']} | "
                f"{f['composite_score']} | {f['urgency']}/10 | {f['strength']}/10 | "
                f"{f['vulnerability']}/10 | {f['exhibit_count']:,} |"
            )

        lines.append("\n## Strategic Dependencies\n")
        for dep_first, dep_after, reason in FILING_DEPENDENCIES:
            lines.append(f"- **{dep_first} → {dep_after}**: {reason}")

        lines.append("\n## Recommended Filing Waves\n")
        lines.append("### Wave 1 — Immediate (This Week)")
        lines.append("- F3 (Disqualification) + F6 (JTC) — remove biased judge")
        lines.append("- F10 (COA Emergency) + F9 (COA Brief) — appellate relief\n")
        lines.append("### Wave 2 — Following Week")
        lines.append("- F1 (TRO) + F7 (Custody Modification) — with new/replacement judge")
        lines.append("- F4 (§1983 Federal) — parallel federal action\n")
        lines.append("### Wave 3 — Strategic Follow-Up")
        lines.append("- F8 (PPO) — after custody posture established")
        lines.append("- F5 (MSC Bypass) — after COA briefing complete")
        lines.append("- F2 (Housing) — independent timeline\n")

        lines.append("\n## Per-Filing Notes\n")
        for f in order:
            lines.append(f"### {f['filing_id']} — {f['name']}")
            lines.append(f"- **Court:** {f['court']} | **Lane:** {f['lane']}")
            lines.append(f"- **Strategy:** {f['strategic_notes']}")
            lines.append("")

        return "\n".join(lines)
