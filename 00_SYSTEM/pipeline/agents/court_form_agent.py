"""
COURT FORM AGENT (F06) — Michigan Court Form Intelligence Engine

Searches the court_forms.db for applicable court forms for any filing type,
validates form requirements, and generates auto-filled form data packages.

Capabilities:
  - Search forms by filing type, lane, court level, or series
  - Map required/optional forms to filing packages
  - Auto-fill form fields from party_data and litigation_context.db
  - Generate filing checklists with form status (filled/needs-input/missing)
  - Validate completeness before filing

v1.0 — Initial release
"""
import json
import os
import sqlite3
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .agent_models import (
    AgentResult, AgentStats, FatalAgentError, SkipItemError,
    MASTER_INDEX_DB
)

# Safe import of base class
try:
    from .agent_base import Agent9999
except ImportError:
    from agent_base import Agent9999


COURT_FORMS_DB = Path(os.environ.get(
    "COURT_FORMS_DB",
    r"C:\Users\andre\LitigationOS\court_forms.db"
))

LITIGATION_DB = Path(os.environ.get(
    "LITIGATION_DB",
    r"C:\Users\andre\LitigationOS\litigation_context.db"
))

# Filing type aliases for flexible lookup
FILING_ALIASES = {
    "F1": "emergency_tro",
    "F2": "civil_complaint_housing",
    "F3": "disqualification",
    "F4": "federal_1983",
    "F5": "msc_original_action",
    "F6": "jtc_complaint",
    "F7": "custody_modification",
    "F8": "ppo_termination",
    "F9": "coa_appeal_brief",
    "F10": "coa_emergency_motion",
    "tro": "emergency_tro",
    "shady_oaks": "civil_complaint_housing",
    "disqualification": "disqualification",
    "1983": "federal_1983",
    "federal": "federal_1983",
    "msc": "msc_original_action",
    "supreme_court": "msc_original_action",
    "jtc": "jtc_complaint",
    "custody": "custody_modification",
    "ppo": "ppo_termination",
    "coa_brief": "coa_appeal_brief",
    "coa_emergency": "coa_emergency_motion",
    "appeal": "coa_appeal_brief",
}


class CourtFormAgent(Agent9999):
    """Michigan Court Form Intelligence Engine.

    Searches court_forms.db for applicable forms, maps them to filing
    packages, and generates auto-filled field data for each form.
    """

    AGENT_ID = "F06"
    AGENT_NAME = "CourtFormAgent"
    TIER = "F"  # Filing/convergence tier

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._forms_conn: Optional[sqlite3.Connection] = None
        self._lit_conn: Optional[sqlite3.Connection] = None
        self._party_cache: Dict[str, str] = {}

    def _open_forms_db(self) -> sqlite3.Connection:
        """Open court_forms.db with standard pragmas."""
        if self._forms_conn is not None:
            return self._forms_conn
        if not COURT_FORMS_DB.exists():
            raise FatalAgentError(f"Court forms DB not found: {COURT_FORMS_DB}")
        conn = sqlite3.connect(str(COURT_FORMS_DB), timeout=60)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        self._forms_conn = conn
        return conn

    def _open_litigation_db(self) -> Optional[sqlite3.Connection]:
        """Open litigation_context.db for cross-referencing."""
        if self._lit_conn is not None:
            return self._lit_conn
        if not LITIGATION_DB.exists():
            self.log_warning("litigation_context.db not found — auto-fill limited")
            return None
        conn = sqlite3.connect(str(LITIGATION_DB), timeout=60)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        self._lit_conn = conn
        return conn

    def _load_party_data(self) -> Dict[str, str]:
        """Load all party data for auto-fill."""
        if self._party_cache:
            return self._party_cache
        conn = self._open_forms_db()
        rows = conn.execute("SELECT key, value FROM party_data").fetchall()
        self._party_cache = {r["key"]: r["value"] for r in rows}
        return self._party_cache

    # ──────────────────────────────────────────────────────────
    # CORE: Search forms for a filing type
    # ──────────────────────────────────────────────────────────

    def search_forms_for_filing(self, filing_type: str) -> Dict[str, Any]:
        """Find all required and optional forms for a filing type.

        Args:
            filing_type: Filing identifier (e.g. "F7", "custody", "custody_modification")

        Returns:
            Dict with 'required', 'optional', 'package_info', 'checklist'
        """
        resolved = FILING_ALIASES.get(filing_type, filing_type)
        conn = self._open_forms_db()

        # Get package info
        pkg = conn.execute(
            "SELECT * FROM filing_packages WHERE filing_type = ?",
            (resolved,)
        ).fetchone()

        # Get form mappings
        mappings = conn.execute("""
            SELECT fm.*, cf.form_number, cf.form_name, cf.form_series, 
                   cf.court_level, cf.description, cf.url, cf.mcr_reference,
                   cf.fillable
            FROM form_filing_map fm
            JOIN court_forms cf ON fm.form_id = cf.form_id
            WHERE fm.filing_type = ?
            ORDER BY fm.order_in_package
        """, (resolved,)).fetchall()

        required = []
        optional = []
        for m in mappings:
            form_info = {
                "form_id": m["form_id"],
                "form_number": m["form_number"],
                "form_name": m["form_name"],
                "series": m["form_series"],
                "court_level": m["court_level"],
                "description": m["description"],
                "url": m["url"],
                "mcr_reference": m["mcr_reference"],
                "fillable": bool(m["fillable"]),
                "order": m["order_in_package"],
                "notes": m["notes"],
            }
            if m["required"]:
                required.append(form_info)
            else:
                optional.append(form_info)

        result = {
            "filing_type": resolved,
            "filing_alias": filing_type,
            "required_forms": required,
            "optional_forms": optional,
            "total_required": len(required),
            "total_optional": len(optional),
        }

        if pkg:
            result["package"] = {
                "name": pkg["package_name"],
                "lane": pkg["lane"],
                "court": pkg["court"],
                "case_number": pkg["case_number"],
                "description": pkg["description"],
            }

        return result

    # ──────────────────────────────────────────────────────────
    # AUTO-FILL: Generate field values for a form
    # ──────────────────────────────────────────────────────────

    def auto_fill_form(self, form_id: str, case_number: str = None) -> Dict[str, Any]:
        """Auto-fill form fields from party_data and litigation DB.

        Args:
            form_id: Form identifier (e.g. "MC-20", "FOC-115")
            case_number: Optional case number override

        Returns:
            Dict with filled fields, missing fields, and completion %
        """
        conn = self._open_forms_db()
        party = self._load_party_data()

        fields = conn.execute(
            "SELECT * FROM form_fields WHERE form_id = ? ORDER BY section, field_name",
            (form_id,)
        ).fetchall()

        if not fields:
            return {
                "form_id": form_id,
                "message": "No field definitions found — form may need manual entry",
                "filled": {},
                "missing": [],
                "completion_pct": 0.0,
            }

        filled = {}
        missing = []
        needs_andrew = []

        for f in fields:
            field_name = f["field_name"]
            auto_source = f["auto_fill_source"]
            auto_value = f["auto_fill_value"]
            notes = f["notes"] or ""

            # Priority: explicit value > party data lookup > None
            value = None
            source_desc = None

            if auto_value:
                value = auto_value
                source_desc = "pre-filled constant"
            elif auto_source and auto_source in party:
                value = party[auto_source]
                source_desc = f"party_data[{auto_source}]"
            elif case_number and field_name == "case_number":
                value = case_number
                source_desc = "case_number parameter"

            if value:
                filled[field_name] = {
                    "label": f["field_label"],
                    "value": value,
                    "source": source_desc,
                    "type": f["field_type"],
                    "section": f["section"],
                }
            elif "ANDREW_REQUIRED" in notes:
                needs_andrew.append({
                    "field": field_name,
                    "label": f["field_label"],
                    "type": f["field_type"],
                    "section": f["section"],
                    "notes": notes,
                })
            elif f["field_type"] == "signature":
                needs_andrew.append({
                    "field": field_name,
                    "label": f["field_label"],
                    "type": "signature",
                    "section": f["section"],
                    "notes": "Physical signature required",
                })
            else:
                missing.append({
                    "field": field_name,
                    "label": f["field_label"],
                    "type": f["field_type"],
                    "section": f["section"],
                    "notes": notes,
                })

        total = len(fields)
        filled_count = len(filled)
        completion = round((filled_count / total) * 100, 1) if total > 0 else 0.0

        return {
            "form_id": form_id,
            "total_fields": total,
            "filled_count": filled_count,
            "completion_pct": completion,
            "filled": filled,
            "needs_andrew_input": needs_andrew,
            "missing": missing,
            "ready_to_file": len(needs_andrew) == 0 and len(missing) == 0,
        }

    # ──────────────────────────────────────────────────────────
    # CHECKLIST: Full filing package readiness
    # ──────────────────────────────────────────────────────────

    def generate_filing_checklist(self, filing_type: str) -> Dict[str, Any]:
        """Generate a complete filing checklist with form status.

        Returns a structured checklist showing:
          - Each form: found/not-found, auto-fill %, fields needing input
          - Overall readiness score
          - Blocking items (Andrew must do)
        """
        forms = self.search_forms_for_filing(filing_type)
        checklist_items = []
        blockers = []
        total_fields = 0
        filled_fields = 0

        for form_list, is_required in [
            (forms["required_forms"], True),
            (forms["optional_forms"], False),
        ]:
            for form in form_list:
                fill_result = self.auto_fill_form(form["form_id"])
                total_fields += fill_result.get("total_fields", 0)
                filled_fields += fill_result.get("filled_count", 0)

                item = {
                    "form_id": form["form_id"],
                    "form_name": form["form_name"],
                    "form_number": form["form_number"],
                    "required": is_required,
                    "fillable": form["fillable"],
                    "completion_pct": fill_result.get("completion_pct", 0),
                    "needs_andrew": fill_result.get("needs_andrew_input", []),
                    "missing": fill_result.get("missing", []),
                    "url": form["url"],
                    "mcr_reference": form["mcr_reference"],
                    "notes": form["notes"],
                }
                checklist_items.append(item)

                # Track blockers
                for need in fill_result.get("needs_andrew_input", []):
                    blockers.append({
                        "form": form["form_name"],
                        "field": need["label"],
                        "type": need["type"],
                        "notes": need.get("notes", ""),
                    })

        overall_completion = (
            round((filled_fields / total_fields) * 100, 1)
            if total_fields > 0 else 0.0
        )

        return {
            "filing_type": filing_type,
            "package": forms.get("package", {}),
            "checklist": checklist_items,
            "total_forms": len(checklist_items),
            "overall_completion_pct": overall_completion,
            "total_fields": total_fields,
            "filled_fields": filled_fields,
            "blockers": blockers,
            "blocker_count": len(blockers),
            "ready_to_file": len(blockers) == 0,
        }

    # ──────────────────────────────────────────────────────────
    # SEARCH: Find forms by various criteria
    # ──────────────────────────────────────────────────────────

    def search_forms(
        self,
        query: str = None,
        series: str = None,
        court_level: str = None,
        lane: str = None,
        division: str = None,
    ) -> List[Dict[str, Any]]:
        """Search court forms by multiple criteria.

        Args:
            query: Free-text search (matches form_name, description, mcr_reference)
            series: Form series filter (MC, CC, FOC, COA, MSC, FED, JTC)
            court_level: Court level (circuit, coa, msc, federal, jtc)
            lane: Case lane (A, B, C, D, E, F)
            division: Division (family, civil, criminal, appellate)

        Returns:
            List of matching forms
        """
        conn = self._open_forms_db()
        conditions = []
        params = []

        if query:
            conditions.append(
                "(form_name LIKE ? OR description LIKE ? OR mcr_reference LIKE ? OR form_number LIKE ?)"
            )
            q = f"%{query}%"
            params.extend([q, q, q, q])

        if series:
            conditions.append("form_series = ?")
            params.append(series.upper())

        if court_level:
            conditions.append("court_level = ?")
            params.append(court_level.lower())

        if lane:
            conditions.append("filing_lanes LIKE ?")
            params.append(f"%{lane.upper()}%")

        if division:
            conditions.append("division = ?")
            params.append(division.lower())

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM court_forms WHERE {where} ORDER BY form_series, form_number"

        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ──────────────────────────────────────────────────────────
    # BULK: All 10 filings status
    # ──────────────────────────────────────────────────────────

    def all_filings_form_status(self) -> Dict[str, Any]:
        """Get form readiness for all 10 filings at once."""
        results = {}
        for alias in ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"]:
            try:
                checklist = self.generate_filing_checklist(alias)
                results[alias] = {
                    "name": checklist.get("package", {}).get("name", alias),
                    "total_forms": checklist["total_forms"],
                    "completion_pct": checklist["overall_completion_pct"],
                    "blockers": checklist["blocker_count"],
                    "ready": checklist["ready_to_file"],
                }
            except Exception as e:
                results[alias] = {"error": str(e)}
        return results

    # ──────────────────────────────────────────────────────────
    # Agent9999 CONTRACT
    # ──────────────────────────────────────────────────────────

    def run(self, filing_types: List[str] = None, **kwargs) -> AgentResult:
        """Run the court form agent.

        If filing_types provided, generates checklists for those filings.
        Otherwise, generates status for all 10 filings.
        """
        start = time.time()
        stats = AgentStats(agent_id=self.AGENT_ID)

        try:
            self._open_forms_db()
            findings = {}

            if filing_types:
                for ft in filing_types:
                    stats.items_processed += 1
                    try:
                        checklist = self.generate_filing_checklist(ft)
                        findings[ft] = checklist
                        stats.items_success += 1
                    except Exception as e:
                        stats.items_failed += 1
                        findings[ft] = {"error": str(e)}
            else:
                findings = self.all_filings_form_status()
                stats.items_processed = 10
                stats.items_success = sum(
                    1 for v in findings.values() if "error" not in v
                )
                stats.items_failed = sum(
                    1 for v in findings.values() if "error" in v
                )

            stats.runtime_seconds = round(time.time() - start, 2)

            return AgentResult(
                agent_id=self.AGENT_ID,
                status="SUCCESS",
                stats=stats,
                output=findings,
            )

        except Exception as e:
            stats.runtime_seconds = round(time.time() - start, 2)
            return AgentResult(
                agent_id=self.AGENT_ID,
                status="FATAL",
                stats=stats,
                error=str(e),
            )

        finally:
            if self._forms_conn:
                self._forms_conn.close()
                self._forms_conn = None
            if self._lit_conn:
                self._lit_conn.close()
                self._lit_conn = None

    # Convenience alias
    def process_item(self, item: Any) -> Any:
        """Not used — this agent runs in batch via run()."""
        return None
