# THE MANBEARPIG LitigationOS -- Agent Skill Modules
"""
MANBEARPIG Local Model Skill Registry
======================================
40 Michigan-first litigation intelligence skills with lazy loading.
Plus 16 EPOCH v4.0/v5.0 core engines (loaded from parent directory).
Pure SQLite, no external APIs, zero-dependency startup.

Usage:
    from skills import SKILL_REGISTRY, load_skill, list_skills, get_skill_class
    from skills import SkillBase
    skill_mod = load_skill('adversary_war_room')
    cls = get_skill_class('adversary_war_room')  # AdversaryWarRoom
"""

import importlib
import logging
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ── Common placeholder patterns that indicate unfinished output ──────
_PLACEHOLDER_PATTERNS = [
    r'\[DATE\]', r'\[NAME\]', r'\[CASE NUMBER\]', r'\[ADDRESS\]',
    r'\[PHONE\]', r'\[EMAIL\]', r'\[CITY\]', r'\[STATE\]', r'\[ZIP\]',
    r'\[COURT\]', r'\[JUDGE\]', r'\[SPECIFY[^\]]*\]', r'\[STATE FACTS\]',
    r'\[ISSUE \d+\]', r'\[SWORN STATEMENT[^\]]*\]',
    r'\[APPLICATION OF LAW TO FACTS\]', r'\[QUESTION PRESENTED[^\]]*\]',
    r'\[DOCUMENT BEING RESPONDED TO\]', r'\[FOC RECOMMENDATION[^\]]*\]',
    r'\[ORDER PROVISION[^\]]*\]', r'\[MATTER TO BE HEARD\]',
    r'\[FIRST ARGUMENT HEADING\]', r'\[Cases will be auto-populated[^\]]*\]',
    r'\[MCR references will be auto-populated[^\]]*\]',
    r'\[MCL references will be auto-populated[^\]]*\]',
    r'\[Detailed factual recitation[^\]]*\]',
    r'\[IRAC[^\]]*\]', r'\[Apply IRAC[^\]]*\]',
    r'\[Address on file\]', r'\[Address on file with the Court\]',
    r'\[City, State ZIP\]',
]
_PLACEHOLDER_RE = re.compile('|'.join(_PLACEHOLDER_PATTERNS), re.IGNORECASE)

# ── Citation pattern for MCR/MCL/MRE references ─────────────────────
_CITATION_RE = re.compile(
    r'(MCR|MCL|MRE)\s+(\d+(?:\.\d+)+(?:\([A-Za-z0-9]+\))*)'
)


class SkillBase:
    """Base class providing shared validation, DB query, and quality utilities
    for all LitigationOS skills. Skills may inherit from this or use it standalone."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    # ── Output Validation ────────────────────────────────────────────

    def validate_output(self, text: str) -> Dict[str, Any]:
        """Validate generated text for placeholders and unverified citations.

        Returns:
            {
                "score": int (0-100),
                "issues": [str],
                "placeholder_count": int,
                "unverified_citations": [str],
                "total_citations": int,
            }
        """
        issues: List[str] = []
        score = 100

        # 1. Check for placeholder patterns
        placeholders = _PLACEHOLDER_RE.findall(text)
        if placeholders:
            deduped = list(set(placeholders))
            issues.append(
                f"Found {len(placeholders)} placeholder(s): "
                f"{', '.join(deduped[:8])}"
            )
            score -= len(placeholders) * 5

        # 2. Check for unverified citations
        citations = _CITATION_RE.findall(text)
        unverified: List[str] = []
        conn = self._get_conn()
        if conn and citations:
            for cite_type, cite_num in citations:
                # Normalize: strip sub-rules for DB lookup
                base_num = re.split(r'\(', cite_num)[0]
                try:
                    row = conn.execute(
                        "SELECT COUNT(*) as cnt FROM auth_rules "
                        "WHERE rule_number LIKE ?",
                        (f"%{base_num}%",),
                    ).fetchone()
                    if row["cnt"] == 0:
                        # Fallback: check rules_text
                        row2 = conn.execute(
                            "SELECT COUNT(*) as cnt FROM rules_text "
                            "WHERE rule LIKE ?",
                            (f"%{base_num}%",),
                        ).fetchone()
                        if row2["cnt"] == 0:
                            unverified.append(f"{cite_type} {cite_num}")
                except Exception:
                    pass
            if conn:
                conn.close()

        if unverified:
            issues.append(
                f"{len(unverified)} unverified citation(s): "
                f"{', '.join(unverified[:5])}"
            )
            score -= len(unverified) * 3

        # 3. Structural checks
        if "CERTIFICATE OF SERVICE" not in text:
            if any(kw in text.upper() for kw in ["MOTION", "BRIEF", "RESPONSE", "OBJECTION"]):
                issues.append("Missing Certificate of Service (MCR 2.107)")
                score -= 15
        if "Respectfully submitted" not in text and "IT IS SO ORDERED" not in text:
            if any(kw in text.upper() for kw in ["MOTION", "BRIEF", "RESPONSE"]):
                issues.append("Missing signature block")
                score -= 10

        return {
            "score": max(0, min(100, score)),
            "issues": issues,
            "placeholder_count": len(placeholders),
            "unverified_citations": unverified,
            "total_citations": len(citations),
        }

    # ── DB Convenience: Authority Search ─────────────────────────────

    def get_db_authority(self, topic: str, limit: int = 5) -> List[Dict]:
        """Query auth_rules_fts for authority on a topic. Falls back to LIKE."""
        conn = self._get_conn()
        if not conn:
            return []
        results: List[Dict] = []
        try:
            rows = conn.execute(
                "SELECT rule_number, title, substr(full_text, 1, 600) as text "
                "FROM auth_rules WHERE rowid IN "
                "(SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?) "
                "LIMIT ?",
                (topic, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "rule_number": r["rule_number"],
                    "title": r["title"],
                    "text": r["text"],
                })
        except Exception:
            # FTS fallback to LIKE
            try:
                rows = conn.execute(
                    "SELECT rule_number, title, substr(full_text, 1, 600) as text "
                    "FROM auth_rules WHERE rule_number LIKE ? "
                    "OR title LIKE ? OR full_text LIKE ? LIMIT ?",
                    (f"%{topic}%", f"%{topic}%", f"%{topic}%", limit),
                ).fetchall()
                for r in rows:
                    results.append({
                        "rule_number": r["rule_number"],
                        "title": r["title"],
                        "text": r["text"],
                    })
            except Exception:
                pass
        finally:
            conn.close()
        return results

    # ── DB Convenience: Evidence Search ──────────────────────────────

    def get_evidence(self, topic: str, limit: int = 5) -> List[Dict]:
        """Query evidence_quotes_fts for evidence on a topic. Falls back to LIKE."""
        conn = self._get_conn()
        if not conn:
            return []
        results: List[Dict] = []
        try:
            rows = conn.execute(
                "SELECT quote_text, speaker, legal_significance, evidence_category "
                "FROM evidence_quotes WHERE rowid IN "
                "(SELECT rowid FROM evidence_quotes_fts "
                "WHERE evidence_quotes_fts MATCH ?) LIMIT ?",
                (topic, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "quote_text": r["quote_text"],
                    "speaker": r["speaker"],
                    "legal_significance": r["legal_significance"],
                    "evidence_category": r["evidence_category"],
                })
        except Exception:
            try:
                rows = conn.execute(
                    "SELECT quote_text, speaker, legal_significance, evidence_category "
                    "FROM evidence_quotes WHERE quote_text LIKE ? "
                    "OR legal_significance LIKE ? LIMIT ?",
                    (f"%{topic}%", f"%{topic}%", limit),
                ).fetchall()
                for r in rows:
                    results.append({
                        "quote_text": r["quote_text"],
                        "speaker": r["speaker"],
                        "legal_significance": r["legal_significance"],
                        "evidence_category": r["evidence_category"],
                    })
            except Exception:
                pass
        finally:
            conn.close()
        return results

# ── Skill Registry: name → module filename (without .py) ────────────────────
SKILL_REGISTRY: Dict[str, str] = {
    # ── Existing 8 core skills ──────────────────────────────────────────────
    "authority_search":          "authority_search",
    "cite_check":                "cite_check",
    "contradiction_finder":      "contradiction_finder",
    "deadline_calculator":       "deadline_calculator",
    "factor_analysis":           "factor_analysis",
    "impeachment_engine":        "impeachment_engine",
    "precedent_matcher":         "precedent_matcher",
    "timeline_builder":          "timeline_builder",
    # ── New 16 skills ───────────────────────────────────────────────────────
    "jtc_complaint_generator":   "jtc_complaint_generator",
    "filing_package_generator":  "filing_package_generator",
    "adversary_war_room":        "adversary_war_room",
    "motion_generator":          "motion_generator",
    "order_analyzer":            "order_analyzer",
    "alienation_analyzer":       "alienation_analyzer",
    "forensic_analyzer":         "forensic_analyzer",
    "weaponization_tracker":     "weaponization_tracker",
    "evidence_clusterer":        "evidence_clusterer",
    "case_strength_scorer":      "case_strength_scorer",
    "narrative_builder":         "narrative_builder",
    "appellate_brief_builder":   "appellate_brief_builder",
    "authority_graph_navigator": "authority_graph_navigator",
    "citation_network":          "citation_network",
    "chronology_engine":         "chronology_engine",
    "discovery_engine":          "discovery_engine",
    "pro_se_trap_detector":      "pro_se_trap_detector",
    "response_drafter":          "response_drafter",
    # ── EPOCH v8.0 multi-forum skills ───────────────────────────────────
    "service_tracker":           "service_tracker",
    "multi_forum_compliance":    "multi_forum_compliance",
    # ── EPOCH v8.0 federal + hearing skills ─────────────────────────────
    "federal_jurisdiction":      "federal_jurisdiction",
    "hearing_prep":              "hearing_prep",
    # ── EPOCH v8.0 appellate filing compliance ───────────────────────────
    "appendix_builder":          "appendix_builder",
    "certificate_of_service":    "certificate_of_service",
    # ── EPOCH v8.0 appellate document compliance ─────────────────────────
    "appellate_validator":       "appellate_validator",
    "index_of_authorities":      "index_of_authorities",
    # ── EPOCH v8.1 document generation pipeline ──────────────────────────
    "caption_engine":            "caption_engine",
    "mifile_checker":            "mifile_checker",
    "proposed_order_generator":  "proposed_order_generator",
    "scao_forms_library":        "scao_forms_library",
    "timeline_generator":        "timeline_generator",
    # ── EPOCH v8.1 MSC fleet intelligence ─────────────────────────────────
    "msc_fleet_engine":          "msc_fleet_engine",
    # ── EPOCH v8.2 pre-filing and deadline skills ─────────────────────────
    "pre_filing_validator":      "pre_filing_validator",
    "deadline_monitor":          "deadline_monitor",
    # ── EPOCH v8.5 harm intelligence ──────────────────────────────────────
    "chat_harm_intelligence":    "chat_harm_intelligence",
    "adversary_accountability":  "adversary_accountability",
    # ── EPOCH v8.5 shell management & watchdog ────────────────────────────
    "shell_management":          "shell_management",
    # ── EPOCH v8.6 MANBEARPIG skills (m41-m47) ─────────────────────────────
    "harm_search_optimizer":     "harm_search_optimizer",
    "timeline_visualization":    "timeline_visualization",
    "damages_calculator_skill":  "damages_calculator_skill",
    "scao_form_filler":          "scao_form_filler",
    "adversary_wargame_v2":      "adversary_wargame_v2",
}

# ── Class name mapping (skills that export a primary class) ─────────────────
CLASS_REGISTRY: Dict[str, str] = {
    "factor_analysis":           "FactorAnalysis",
    "impeachment_engine":        "ImpeachmentEngine",
    "precedent_matcher":         "PrecedentMatcher",
    "jtc_complaint_generator":   "JTCComplaintGenerator",
    "filing_package_generator":  "FilingPackageGenerator",
    "adversary_war_room":        "AdversaryWarRoom",
    "motion_generator":          "MotionGenerator",
    "order_analyzer":            "OrderAnalyzer",
    "alienation_analyzer":       "AlienationAnalyzer",
    "forensic_analyzer":         "ForensicAnalyzer",
    "weaponization_tracker":     "WeaponizationTracker",
    "evidence_clusterer":        "EvidenceClusterer",
    "case_strength_scorer":      "CaseStrengthScorer",
    "narrative_builder":         "NarrativeBuilder",
    "appellate_brief_builder":   "AppellateBriefBuilder",
    "authority_graph_navigator": "AuthorityGraphNavigator",
    "citation_network":          "CitationNetwork",
    "chronology_engine":         "ChronologyEngine",
    "discovery_engine":          "DiscoveryEngine",
    "pro_se_trap_detector":      "ProSeTrapDetector",
    "response_drafter":          "ResponseDrafter",
    "service_tracker":           "ServiceTracker",
    "multi_forum_compliance":    "MultiForumCompliance",
    "federal_jurisdiction":      "FederalJurisdictionEngine",
    "hearing_prep":              "HearingPrepEngine",
    "appendix_builder":          "AppendixBuilder",
    "certificate_of_service":    "CertificateOfService",
    "appellate_validator":       "AppellateValidator",
    "index_of_authorities":      "IndexOfAuthorities",
    "pre_filing_validator":      "PreFilingValidator",
    "deadline_monitor":          "DeadlineMonitor",
    # ── EPOCH v8.6 ──────────────────────────────────────────────────────
    "harm_search_optimizer":     "HarmSearchOptimizer",
    "timeline_visualization":    "TimelineVisualization",
    "damages_calculator_skill":  "DamagesCalculatorSkill",
    "scao_form_filler":          "SCAOFormFiller",
    "adversary_wargame_v2":      "AdversaryWargameV2",
}

# ── Lazy-load cache ─────────────────────────────────────────────────────────
_loaded: Dict[str, Any] = {}


def list_skills() -> List[str]:
    """Return sorted list of registered skill names."""
    return sorted(SKILL_REGISTRY.keys())


def load_skill(name: str) -> Any:
    """Dynamically import and return a skill module by registry name.

    Raises KeyError if the skill name is unknown.
    Raises ImportError if the module cannot be loaded.
    """
    if name not in SKILL_REGISTRY:
        raise KeyError(
            f"Unknown skill: '{name}'. Available: {list_skills()}"
        )
    if name not in _loaded:
        module_name = SKILL_REGISTRY[name]
        try:
            module = importlib.import_module(f".{module_name}", package=__name__)
            _loaded[name] = module
            logger.info("Loaded skill: %s (module: %s)", name, module_name)
        except Exception as exc:
            logger.error("Failed to load skill '%s': %s", name, exc)
            raise
    return _loaded[name]


def get_skill_class(name: str) -> Optional[Any]:
    """Load a skill module and return its primary class, or None if no class is registered."""
    try:
        module = load_skill(name)
        class_name = CLASS_REGISTRY.get(name)
        if class_name:
            return getattr(module, class_name, None)
        return None
    except Exception as exc:
        logger.error("Failed to get class for skill '%s': %s", name, exc)
        return None


def unload_skill(name: str) -> bool:
    """Remove a skill from the cache, forcing re-import on next load."""
    if name in _loaded:
        del _loaded[name]
        logger.info("Unloaded skill: %s", name)
        return True
    return False


def get_skill_status() -> Dict[str, str]:
    """Check which skills can be loaded successfully.

    Returns dict mapping skill name → 'OK' or 'ERROR: <message>'.
    """
    results: Dict[str, str] = {}
    for name in sorted(SKILL_REGISTRY.keys()):
        try:
            load_skill(name)
            results[name] = "OK"
        except Exception as exc:
            results[name] = f"ERROR: {exc}"
    return results


def check_db_connectivity() -> Dict[str, Any]:
    """Test database connectivity (shared by all skills)."""
    import sqlite3
    info: Dict[str, Any] = {
        "path": DB_PATH,
        "exists": os.path.isfile(DB_PATH),
        "accessible": False,
        "table_count": 0,
        "error": None,
    }
    if not info["exists"]:
        info["error"] = "Database file not found"
        return info
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        )
        info["table_count"] = cursor.fetchone()[0]
        info["accessible"] = True
        conn.close()
    except Exception as exc:
        info["error"] = str(exc)
    return info


def get_full_health() -> Dict[str, Any]:
    """Comprehensive health report: DB + all skills."""
    return {
        "database": check_db_connectivity(),
        "skill_count": len(SKILL_REGISTRY),
        "skills_with_classes": len(CLASS_REGISTRY),
        "skill_status": get_skill_status(),
    }

# === EPOCH v8.5: Chat Harm Intelligence (26,409 harms from 51,868 messages) ===
from .chat_harm_intelligence import METHODS as chat_harm_methods
from .adversary_accountability import METHODS as adversary_methods

CHAT_HARM_SKILLS = {
    'harm_search': chat_harm_methods['harm_search'],
    'adversary_profile': chat_harm_methods['adversary_profile'],
    'harm_to_filing_map': chat_harm_methods['harm_to_filing_map'],
    'chat_evidence_extract': chat_harm_methods['chat_evidence_extract'],
    'harm_statistics': chat_harm_methods['harm_statistics'],
    'get_accountability': adversary_methods['get_accountability'],
    'all_adversaries': adversary_methods['all_adversaries'],
}
