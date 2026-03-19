#!/usr/bin/env python3
"""
APEX Evidence-to-Element Mapper
================================
For each cause of action, lists required elements and maps available evidence.
Critical for complaint construction per litigation-lawsuit-forge Phase 3.

Maps evidence from litigation_context.db to the legal elements required
for each cause of action under Michigan law. Identifies gaps and suggests
evidence acquisition strategies.

Shadow-programmed: APEX_LLM_ENABLED gates neural features.
NEVER crashes — all methods try/except with fallbacks.
Never sets CWD to repo root (shadow modules).
Uses Path(__file__).parent for paths.
DB: busy_timeout=60000, journal_mode=WAL, cache_size=-32000.
Thread-safe, UTF-8 safe, logging, type hints.
"""

import json
import logging
import os
import re
import sqlite3
import sys
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── APEX Shadow Programming ────────────────────────────────────────
APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
DEFAULT_DB = os.environ.get(
    "LITIGATION_DB_PATH",
    str(_MODULE_DIR.parent.parent.parent / "litigation_context.db"),
)

# ── Lane → Case Number mapping ─────────────────────────────────────
LANE_CASES: Dict[str, List[str]] = {
    "A": ["2024-001507-DC", "2023-5907-PP"],
    "B": ["2025-002760-CZ"],
    "C": [],
    "D": ["2024-001507-DC", "2023-5907-PP"],
    "E": ["2024-001507-DC"],
    "F": ["366810"],
}


class EvidenceElementMapper:
    """Maps available evidence to required legal elements for each cause of action.

    For each cause of action (COA), maintains the list of required legal elements
    under Michigan law, searches the litigation DB for evidence supporting each
    element, and reports gaps with acquisition suggestions.
    """

    # Required elements per cause of action (Michigan law)
    ELEMENTS: Dict[str, List[str]] = {
        "negligence": ["duty", "breach", "causation", "damages"],
        "fraud": [
            "misrepresentation", "material_fact", "knowledge_of_falsity",
            "intent_to_induce", "reliance", "damages",
        ],
        "breach_of_contract": ["valid_contract", "breach", "damages"],
        "civil_rights_1983": ["person", "under_color_of_law", "deprivation_of_right"],
        "due_process_violation": [
            "liberty_or_property_interest", "state_action", "inadequate_process",
        ],
        "parental_alienation": [
            "interference_pattern", "impact_on_child", "intent_or_recklessness",
        ],
        "habitability_breach": [
            "residential_lease", "defective_condition", "notice_to_landlord",
            "failure_to_repair",
        ],
        "truth_in_renting": ["residential_lease", "prohibited_clause", "tenant_harm"],
        "consumer_protection": ["trade_or_commerce", "unfair_practice", "injury"],
        "judicial_misconduct": [
            "judicial_officer", "misconduct_act", "impact_on_proceedings",
        ],
        "contempt": ["valid_court_order", "knowledge_of_order", "willful_violation"],
        "conspiracy_1983": ["agreement", "deprivation_of_rights", "overt_act"],
    }

    # Keywords for searching evidence related to each element
    _ELEMENT_KEYWORDS: Dict[str, List[str]] = {
        "duty": ["duty", "obligation", "responsibility", "standard of care", "owed"],
        "breach": ["breach", "violated", "failed to", "failure", "did not comply"],
        "causation": ["caused", "because", "result of", "led to", "proximate"],
        "damages": ["damage", "harm", "injury", "loss", "suffered", "economic"],
        "misrepresentation": ["misrepresent", "false statement", "told", "claimed", "lied"],
        "material_fact": ["material", "significant", "important fact", "relied upon"],
        "knowledge_of_falsity": ["knew", "knowledge", "aware", "intentional", "knowingly"],
        "intent_to_induce": ["induce", "persuade", "cause to act", "relied"],
        "reliance": ["relied", "reliance", "trusted", "acted upon", "belief"],
        "valid_contract": ["contract", "agreement", "lease", "signed", "executed"],
        "person": ["person", "individual", "official", "employee", "agent"],
        "under_color_of_law": ["color of law", "official capacity", "state action", "government"],
        "deprivation_of_right": ["deprived", "denied", "violated right", "constitutional"],
        "liberty_or_property_interest": ["liberty", "property", "parental right", "fundamental"],
        "state_action": ["state action", "government", "court", "judge", "official"],
        "inadequate_process": ["no hearing", "no notice", "denied opportunity", "ex parte"],
        "interference_pattern": ["interfere", "alienat", "denied parenting", "obstruct", "pattern"],
        "impact_on_child": ["child", "children", "emotional", "psychological", "relationship"],
        "intent_or_recklessness": ["intentional", "reckless", "willful", "deliberate"],
        "residential_lease": ["lease", "rental", "tenant", "residential", "apartment"],
        "defective_condition": ["defect", "mold", "water", "broken", "unsafe", "code violation"],
        "notice_to_landlord": ["notice", "notified", "complained", "reported", "told landlord"],
        "failure_to_repair": ["failed to repair", "did not fix", "refused", "neglected"],
        "prohibited_clause": ["prohibited", "illegal clause", "waiver", "truth in renting"],
        "tenant_harm": ["harm", "damage", "loss", "injury", "suffered", "tenant"],
        "trade_or_commerce": ["trade", "commerce", "business", "consumer", "marketplace"],
        "unfair_practice": ["unfair", "deceptive", "unconscionable", "predatory"],
        "injury": ["injury", "harm", "damage", "suffered"],
        "judicial_officer": ["judge", "judicial officer", "McNeill", "magistrate", "referee"],
        "misconduct_act": ["misconduct", "bias", "ex parte", "violated canon", "improper"],
        "impact_on_proceedings": ["proceedings", "ruling", "order", "denied", "prejudiced"],
        "valid_court_order": ["court order", "order", "judgment", "decree", "stipulation"],
        "knowledge_of_order": ["knew", "served", "aware of order", "notified"],
        "willful_violation": ["willful", "deliberate", "violated", "disobeyed", "contempt"],
        "agreement": ["agreement", "conspir", "coordinated", "agreed", "concerted"],
        "deprivation_of_rights": ["deprived", "rights", "denied", "violated", "constitutional"],
        "overt_act": ["acted", "overt act", "carried out", "implemented", "executed"],
    }

    # Suggestions for evidence acquisition per element type
    _ACQUISITION_SUGGESTIONS: Dict[str, List[str]] = {
        "duty": ["Look for statutes, regulations, or policies establishing duty"],
        "breach": ["Gather records showing non-compliance, violation reports"],
        "causation": ["Timeline analysis, expert testimony, logical chain of events"],
        "damages": ["Financial records, medical records, testimony of harm"],
        "misrepresentation": ["Written/verbal statements, emails, text messages"],
        "reliance": ["Actions taken based on misrepresentation, changed position"],
        "valid_contract": ["Original signed lease/contract, amendments, receipts"],
        "under_color_of_law": ["Court records, official orders, government employment records"],
        "deprivation_of_right": ["Constitutional analysis, case law comparison, timeline"],
        "inadequate_process": ["Hearing transcripts, notice records, court docket"],
        "interference_pattern": ["Communication records, visitation logs, third-party testimony"],
        "impact_on_child": ["School records, therapist notes, behavioral observations"],
        "defective_condition": ["Photos, inspection reports, building code citations"],
        "notice_to_landlord": ["Written complaints, emails, certified mail receipts"],
        "failure_to_repair": ["Follow-up correspondence, condition photos over time"],
        "misconduct_act": ["Transcript excerpts, judicial canons, comparison orders"],
        "willful_violation": ["Proof of knowledge + proof of non-compliance timeline"],
        "agreement": ["Communications between parties, parallel actions, witness statements"],
        "overt_act": ["Specific actions taken in furtherance of conspiracy"],
    }

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path
        self._lock = threading.Lock()

    # ── DB Connection ──────────────────────────────────────────────

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        """Open a read-only WAL connection."""
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=30)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.warning("[EvidenceMapper] DB connect failed: %s", e)
            return None

    # ── Public API ─────────────────────────────────────────────────

    def map_evidence(self, cause_of_action: str, lane: str = None) -> dict:
        """Map available evidence to required elements for a cause of action.

        Args:
            cause_of_action: Key from ELEMENTS dict (e.g., "negligence", "civil_rights_1983")
            lane: Optional case lane (A-F) to scope evidence search

        Returns:
            {
                cause_of_action: str,
                lane: str,
                elements: [{name: str, status: str, evidence: [...], confidence: float}],
                gaps: [str],
                overall_strength: int (0-100),
                total_evidence_pieces: int,
            }
        """
        try:
            coa_key = cause_of_action.lower().replace(" ", "_")
            elements = self.ELEMENTS.get(coa_key)
            if elements is None:
                return {
                    "cause_of_action": cause_of_action,
                    "lane": lane,
                    "elements": [],
                    "gaps": [f"Unknown cause of action: {cause_of_action}"],
                    "overall_strength": 0,
                    "total_evidence_pieces": 0,
                    "available_causes": list(self.ELEMENTS.keys()),
                }

            element_results: List[Dict] = []
            gaps: List[str] = []
            total_evidence = 0

            for element in elements:
                evidence_items = self._search_evidence_for_element(element, lane)
                total_evidence += len(evidence_items)

                if len(evidence_items) >= 3:
                    status = "strong"
                    confidence = min(1.0, 0.6 + len(evidence_items) * 0.1)
                elif len(evidence_items) >= 1:
                    status = "partial"
                    confidence = 0.3 + len(evidence_items) * 0.15
                else:
                    status = "gap"
                    confidence = 0.0
                    gaps.append(element)

                element_results.append({
                    "name": element,
                    "status": status,
                    "evidence": evidence_items[:5],  # Top 5 per element
                    "confidence": round(min(1.0, confidence), 2),
                })

            # Overall strength: percentage of elements with at least partial support
            supported = sum(1 for e in element_results if e["status"] != "gap")
            overall_strength = int(100 * supported / len(elements)) if elements else 0

            return {
                "cause_of_action": coa_key,
                "lane": lane,
                "elements": element_results,
                "gaps": gaps,
                "overall_strength": overall_strength,
                "total_evidence_pieces": total_evidence,
            }
        except Exception as e:
            logger.error("[EvidenceMapper] map_evidence failed: %s", e, exc_info=True)
            return {
                "cause_of_action": cause_of_action,
                "lane": lane,
                "elements": [],
                "gaps": [f"Error: {e}"],
                "overall_strength": 0,
                "total_evidence_pieces": 0,
            }

    def find_gaps(self, cause_of_action: str, lane: str = None) -> list:
        """Identify elements without sufficient evidence support.

        Returns list of {element: str, suggestions: [str]} dicts.
        """
        try:
            mapping = self.map_evidence(cause_of_action, lane)
            gap_details: List[Dict] = []
            for gap_name in mapping.get("gaps", []):
                suggestions = self._ACQUISITION_SUGGESTIONS.get(gap_name, [
                    f"Search for evidence supporting the '{gap_name}' element"
                ])
                gap_details.append({
                    "element": gap_name,
                    "suggestions": suggestions,
                })
            return gap_details
        except Exception as e:
            logger.error("[EvidenceMapper] find_gaps failed: %s", e)
            return [{"element": "error", "suggestions": [str(e)]}]

    def suggest_evidence(self, element: str, lane: str = None) -> list:
        """Suggest potential evidence sources for an unsupported element.

        Returns list of suggestion strings.
        """
        try:
            suggestions: List[str] = []

            # Get standard suggestions
            standard = self._ACQUISITION_SUGGESTIONS.get(element, [])
            suggestions.extend(standard)

            # Search DB for potentially relevant documents
            keywords = self._ELEMENT_KEYWORDS.get(element, [element])
            conn = self._get_conn()
            if conn is not None:
                try:
                    fts_query = " OR ".join(f'"{kw}"' for kw in keywords[:5])
                    try:
                        rows = conn.execute(
                            "SELECT quote_text FROM evidence_quotes_fts "
                            "WHERE evidence_quotes_fts MATCH ? ORDER BY rank LIMIT 5",
                            (fts_query,)
                        ).fetchall()
                        for row in rows:
                            if row[0]:
                                suggestions.append(f"Potential source: {str(row[0])[:100]}...")
                    except Exception:
                        pass
                finally:
                    conn.close()

            if not suggestions:
                suggestions.append(f"Search for evidence supporting '{element}' element")

            return suggestions
        except Exception as e:
            logger.warning("[EvidenceMapper] suggest_evidence failed: %s", e)
            return [f"Evidence suggestion error: {e}"]

    # ── Internal Helpers ───────────────────────────────────────────

    def _search_evidence_for_element(self, element: str, lane: Optional[str]) -> List[Dict]:
        """Search litigation DB for evidence supporting a specific element."""
        conn = self._get_conn()
        if conn is None:
            return []

        try:
            keywords = self._ELEMENT_KEYWORDS.get(element, [element])
            results: List[Dict] = []

            # FTS5 search across evidence tables
            fts_query = " OR ".join(f'"{kw}"' for kw in keywords[:6])
            fts_tables = [
                ("evidence_quotes_fts", "quote_text"),
                ("auth_rules_fts", "full_text"),
            ]

            for fts_table, text_col in fts_tables:
                try:
                    rows = conn.execute(
                        f"SELECT {text_col}, rank FROM {fts_table} "
                        f"WHERE {fts_table} MATCH ? ORDER BY rank LIMIT 10",
                        (fts_query,)
                    ).fetchall()
                    for row in rows:
                        if row[0]:
                            text = str(row[0])
                            # Lane filtering
                            if lane and not self._text_matches_lane(text, lane):
                                continue
                            results.append({
                                "text": text[:200],
                                "source": fts_table,
                                "relevance": abs(float(row[1])) if row[1] else 0.0,
                            })
                except Exception:
                    continue

            # Sort by relevance (FTS5 rank is negative, closer to 0 = better)
            results.sort(key=lambda r: r.get("relevance", 0), reverse=True)
            return results[:10]
        except Exception as e:
            logger.debug("[EvidenceMapper] Evidence search for '%s' failed: %s", element, e)
            return []
        finally:
            conn.close()

    @staticmethod
    def _text_matches_lane(text: str, lane: str) -> bool:
        """Check if text is relevant to a specific case lane."""
        lane_keywords: Dict[str, List[str]] = {
            "A": ["custody", "parenting", "watson", "001507", "5907"],
            "B": ["housing", "shady", "002760", "tenant", "habitability"],
            "C": ["convergence", "cross-lane", "conspiracy"],
            "D": ["ppo", "protection order", "stalking"],
            "E": ["misconduct", "jtc", "mcneill", "judicial tenure"],
            "F": ["appellate", "coa", "366810", "appeal"],
        }
        keywords = lane_keywords.get(lane.upper(), [])
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)

    # ── Status & Self-Test ─────────────────────────────────────────

    def status(self) -> Dict:
        """Return engine status."""
        return {
            "engine": "APEX-EvidenceElementMapper",
            "apex_llm_enabled": APEX_LLM_ENABLED,
            "causes_of_action": len(self.ELEMENTS),
            "total_elements": sum(len(v) for v in self.ELEMENTS.values()),
            "element_keywords": len(self._ELEMENT_KEYWORDS),
            "db_path": self.db_path,
            "db_available": os.path.exists(self.db_path),
        }

    def self_test(self) -> Dict:
        """Run self-test with sample mappings."""
        results = {"tests": [], "status": "pass"}
        try:
            # Test 1: Map evidence for negligence
            mapping = self.map_evidence("negligence")
            results["tests"].append({
                "name": "map_negligence",
                "pass": len(mapping["elements"]) == 4,
                "element_count": len(mapping["elements"]),
                "strength": mapping["overall_strength"],
            })

            # Test 2: Map evidence for civil_rights_1983
            mapping2 = self.map_evidence("civil_rights_1983", lane="E")
            results["tests"].append({
                "name": "map_1983_lane_E",
                "pass": len(mapping2["elements"]) == 3,
                "element_count": len(mapping2["elements"]),
                "strength": mapping2["overall_strength"],
            })

            # Test 3: Find gaps
            gaps = self.find_gaps("fraud")
            results["tests"].append({
                "name": "find_gaps_fraud",
                "pass": isinstance(gaps, list),
                "gap_count": len(gaps),
            })

            # Test 4: Unknown COA
            unknown = self.map_evidence("nonexistent_cause")
            results["tests"].append({
                "name": "unknown_coa",
                "pass": unknown["overall_strength"] == 0 and len(unknown.get("available_causes", [])) > 0,
            })

            # Test 5: Suggest evidence
            suggestions = self.suggest_evidence("duty", "A")
            results["tests"].append({
                "name": "suggest_evidence",
                "pass": len(suggestions) > 0,
                "count": len(suggestions),
            })

            results["status"] = "pass" if all(t["pass"] for t in results["tests"]) else "partial"
        except Exception as e:
            results["status"] = "fail"
            results["error"] = str(e)
        return results


# ── CLI Entry Point ────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    mapper = EvidenceElementMapper()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "--self-test":
        print(json.dumps(mapper.self_test(), indent=2, default=str))
    elif cmd == "--status":
        print(json.dumps(mapper.status(), indent=2, default=str))
    elif cmd == "--map":
        coa = sys.argv[2] if len(sys.argv) > 2 else "negligence"
        lane = sys.argv[3] if len(sys.argv) > 3 else None
        result = mapper.map_evidence(coa, lane)
        print(json.dumps(result, indent=2, default=str))
    elif cmd == "--gaps":
        coa = sys.argv[2] if len(sys.argv) > 2 else "negligence"
        lane = sys.argv[3] if len(sys.argv) > 3 else None
        gaps = mapper.find_gaps(coa, lane)
        print(json.dumps(gaps, indent=2, default=str))
    elif cmd not in ("status", "--status"):
        coa = cmd
        lane = sys.argv[2] if len(sys.argv) > 2 else None
        result = mapper.map_evidence(coa, lane)
        print(json.dumps(result, indent=2, default=str))
    else:
        print(json.dumps(mapper.status(), indent=2, default=str))
