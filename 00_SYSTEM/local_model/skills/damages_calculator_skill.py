#!/usr/bin/env python3
"""
MBP LitigationOS — Damages Calculator Skill Wrapper (m44)
==========================================================
Skill wrapper around engines/damages_calculator.py (d34).
Adds forum-specific views, time-series damages, and court-ready
exhibit generation.

Engine: engines.damages_calculator.DamagesCalculator
Authority:
    42 USC § 1983, 42 USC § 1988, Troxel v Granville 530 US 57 (2000),
    Carey v Piphus 435 US 247 (1978), MCL 600.2910, MCL 600.6304

Usage:
    from skills.damages_calculator_skill import DamagesCalculatorSkill
    skill = DamagesCalculatorSkill()
    summary = skill.calculate_all_damages()
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
    if "skills" in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

# Import the engine
try:
    from engines.damages_calculator import DamagesCalculator
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engines"))
    from damages_calculator import DamagesCalculator

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

SEPARATION_START = date(2025, 8, 8)

FORUM_MAPPING = {
    "14th_circuit": {
        "name": "14th Circuit Court, Muskegon",
        "case": "2024-001507-DC",
        "categories": ["separation", "economic", "emotional_distress"],
        "note": "Compensatory only — no §1983 in state court",
    },
    "coa": {
        "name": "Michigan Court of Appeals (366810)",
        "case": "COA 366810",
        "categories": ["separation", "economic"],
        "note": "Appellate — damages inform reversal urgency",
    },
    "msc": {
        "name": "Michigan Supreme Court",
        "case": "MSC Original Action",
        "categories": ["separation", "constitutional"],
        "note": "Equitable relief primary; damages secondary",
    },
    "federal": {
        "name": "USDC Western District MI",
        "case": "42 USC §1983",
        "categories": ["separation", "constitutional", "economic", "emotional_distress"],
        "note": "Full range including punitive + §1988 costs",
    },
    "jtc": {
        "name": "Judicial Tenure Commission",
        "case": "JTC Complaint",
        "categories": ["separation"],
        "note": "Demonstrates harm magnitude — no monetary recovery",
    },
}


def _get_db() -> Optional[sqlite3.Connection]:
    try:
        conn = sqlite3.connect(DB_PATH, timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


class DamagesCalculatorSkill:
    """Skill wrapper providing forum-specific, time-series, and exhibit views."""

    def __init__(self):
        self.engine = DamagesCalculator()

    def calculate_all_damages(self) -> Dict[str, Any]:
        """Run all damage calculations via the engine and return unified summary."""
        return self.engine.generate_damages_summary()

    def damages_by_forum(self, court: str) -> Dict[str, Any]:
        """Return damages relevant to a specific forum.

        Args:
            court: One of '14th_circuit', 'coa', 'msc', 'federal', 'jtc'
        """
        forum = FORUM_MAPPING.get(court)
        if not forum:
            return {
                "error": f"Unknown court: {court}",
                "available": list(FORUM_MAPPING.keys()),
            }

        summary = self.engine.generate_damages_summary()
        categories = summary.get("categories", {})

        # Filter to relevant categories
        relevant = {}
        for cat_key in forum["categories"]:
            for k, v in categories.items():
                if cat_key.lower() in k.lower():
                    relevant[k] = v

        return {
            "forum": forum["name"],
            "case": forum["case"],
            "note": forum["note"],
            "days_separated": summary.get("days_separated", 0),
            "applicable_categories": relevant,
            "grand_total_range": summary.get("grand_total_range", {}),
        }

    def damages_timeline(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Damages accrued over time with monthly breakpoints.

        Default range: separation start to today.
        """
        start_date = date.fromisoformat(start) if start else SEPARATION_START
        end_date = date.fromisoformat(end) if end else date.today()

        # Build monthly accrual (separation damages grow daily)
        timeline = []
        current = start_date.replace(day=1)
        # Base daily rate from engine (tiered — use average)
        base_daily = 300.0  # conservative midpoint

        cumulative = 0.0
        while current <= end_date:
            month_end = (current.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            if month_end > end_date:
                month_end = end_date
            if current < SEPARATION_START:
                days_in_month = 0
            else:
                eff_start = max(current, SEPARATION_START)
                days_in_month = max(0, (month_end - eff_start).days + 1)

            month_accrual = days_in_month * base_daily
            cumulative += month_accrual

            timeline.append({
                "month": current.strftime("%Y-%m"),
                "days_accruing": days_in_month,
                "monthly_accrual": round(month_accrual, 2),
                "cumulative": round(cumulative, 2),
            })

            # Next month
            current = (month_end + timedelta(days=1))
            if current.day != 1:
                current = current.replace(day=1)

        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "total_days": max(0, (end_date - SEPARATION_START).days),
            "base_daily_rate": base_daily,
            "total_separation_damages": round(cumulative, 2),
            "monthly_timeline": timeline,
            "note": "Separation damages only; constitutional/economic/emotional separate",
        }

    def generate_damages_exhibit(self) -> Dict[str, Any]:
        """Generate court-ready damages exhibit in markdown format."""
        summary = self.engine.generate_damages_summary()
        days = summary.get("days_separated", 0)
        categories = summary.get("categories", {})
        grand = summary.get("grand_total_range", {})

        lines = [
            "# EXHIBIT ___: DAMAGES SUMMARY",
            "",
            f"**Case:** Pigors v. Watson, No. 2024-001507-DC",
            f"**Prepared:** {date.today().strftime('%B %d, %Y')}",
            f"**Days of Parent-Child Separation:** {days} (since August 8, 2025)",
            "",
            "---",
            "",
            "## I. DAMAGE CATEGORIES",
            "",
        ]

        cat_num = 1
        for name, data in categories.items():
            if isinstance(data, dict):
                low = data.get("low", 0)
                high = data.get("high", 0)
                lines.append(f"### {cat_num}. {name}")
                lines.append(f"- **Low estimate:** ${low:,.0f}")
                lines.append(f"- **High estimate:** ${high:,.0f}")
                lines.append("")
            else:
                lines.append(f"### {cat_num}. {name}: {data}")
                lines.append("")
            cat_num += 1

        lines.extend([
            "---",
            "",
            "## II. TOTAL DAMAGES RANGE",
            "",
            f"- **Compensatory:** ${summary.get('compensatory_range', {}).get('low', 0):,.0f} "
            f"— ${summary.get('compensatory_range', {}).get('high', 0):,.0f}",
            f"- **Punitive (federal only):** ${summary.get('punitive_range', {}).get('low', 0):,.0f} "
            f"— ${summary.get('punitive_range', {}).get('high', 0):,.0f}",
            f"- **GRAND TOTAL:** {grand.get('formatted', 'N/A')}",
            "",
            "---",
            "",
            "## III. AUTHORITY",
            "",
            "- 42 USC § 1983 — Civil rights deprivation",
            "- 42 USC § 1988 — Attorney fees / pro se costs",
            "- *Troxel v. Granville*, 530 U.S. 57 (2000) — fundamental parental right",
            "- *Carey v. Piphus*, 435 U.S. 247 (1978) — procedural due process damages",
            "- *Memphis Community School Dist. v. Stachura*, 477 U.S. 299 (1986)",
            "- MCL 600.2910 — Civil conspiracy",
            "- MCL 600.6304 — Joint and several liability",
            "",
            "---",
            "",
            f"*Generated by LitigationOS on {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        ])

        md_text = "\n".join(lines)

        return {
            "exhibit_markdown": md_text,
            "char_count": len(md_text),
            "line_count": len(lines),
            "categories": len(categories),
            "days_separated": days,
            "grand_total": grand.get("formatted", "N/A"),
        }


# ── JSON-RPC dispatch ─────────────────────────────────────────────────

def handle_rpc(method: str, params: Dict[str, Any] = None) -> Dict:
    params = params or {}
    skill = DamagesCalculatorSkill()
    dispatch = {
        "calculate_all_damages": skill.calculate_all_damages,
        "damages_by_forum": skill.damages_by_forum,
        "damages_timeline": skill.damages_timeline,
        "generate_damages_exhibit": skill.generate_damages_exhibit,
    }
    fn = dispatch.get(method)
    if not fn:
        return {"error": f"Unknown method: {method}", "available": list(dispatch.keys())}
    try:
        result = fn(**params)
        return {"result": result, "method": method, "status": "ok"}
    except Exception as e:
        return {"error": str(e), "method": method}


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    skill = DamagesCalculatorSkill()
    print("=== Damages Calculator Skill (m44) ===\n")

    summary = skill.calculate_all_damages()
    print(f"Days separated: {summary.get('days_separated', 'N/A')}")
    print(f"Grand total: {summary.get('grand_total_range', {}).get('formatted', 'N/A')}")

    federal = skill.damages_by_forum("federal")
    print(f"\nFederal forum: {federal.get('forum', 'N/A')}")
    print(f"Applicable categories: {len(federal.get('applicable_categories', {}))}")

    exhibit = skill.generate_damages_exhibit()
    print(f"\nExhibit: {exhibit['line_count']} lines, {exhibit['char_count']} chars")

    print("\n[OK] Damages Calculator Skill operational")
