# -*- coding: utf-8 -*-
"""
FILING FACTORY v1.0 — Complete Court-Ready Package Generator
═══════════════════════════════════════════════════════════════

The central engine that produces COMPLETE filing packages:
  Motion/Complaint/Brief → Court Forms → Affidavits → Exhibits
  → Proof of Service → Cover Pages → TOC → TOA → Fee Waiver

Input:  filing_type + lane + evidence_refs
Output: Complete court-ready package directory with all documents

Architecture:
  FilingFactory orchestrates 6 sub-engines:
    1. DocumentEngine    — Main filing body (motion/complaint/brief)
    2. CourtFormEngine   — Required SCAO forms (auto-filled)
    3. AffidavitEngine   — Verification affidavits with exhibit refs
    4. ExhibitEngine     — Exhibit cover pages, Bates stamps, index
    5. CitationEngine    — Authority validation + format checking
    6. QualityGate       — Pre-filing QA (GO/NO-GO)

Dependencies:
  - court_forms.db (39 forms, 31 mappings)
  - litigation_context.db (master evidence/claims)
  - databases/*.db (10 jurisdiction/knowledge DBs)
"""
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path(r"C:\Users\andre\LitigationOS")
DATABASES_DIR = BASE_DIR / "databases"
COURT_FORMS_DB = BASE_DIR / "court_forms.db"
LITIGATION_DB = BASE_DIR / "litigation_context.db"
OUTPUT_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# Immutable party data — NEVER modify, NEVER fabricate
PARTY_DATA = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17",
        "city": "North Muskegon",
        "state": "Michigan",
        "zip": "49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
        "pro_se": True,
        "bar_number": None,
    },
    "defendant": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive",
        "city": "Norton Shores",
        "state": "Michigan",
        "zip": "49441",
        "phone": None,
        "email": None,
    },
    "child": {
        "initials": "L.D.W.",
        "dob": "2022-11-09",
        "note": "Initials ONLY per MCR 8.119(H)",
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "bar_number": "P-58235",
        "court": "14th Circuit Court, Family Division",
        "county": "Muskegon",
    },
}

# Case lane definitions
CASE_LANES = {
    "A": {"name": "Custody", "case_number": "2024-001507-DC", "court": "14th Circuit Family"},
    "B": {"name": "Housing", "case_number": "2025-002760-CZ", "court": "14th Circuit Civil"},
    "C": {"name": "Convergence", "case_number": "Multi-lane", "court": "Multiple"},
    "D": {"name": "PPO", "case_number": "2023-5907-PP", "court": "14th Circuit Family"},
    "E": {"name": "Judicial Misconduct", "case_number": "JTC-TBD", "court": "JTC"},
    "F": {"name": "Appellate", "case_number": "COA 366810", "court": "Michigan Court of Appeals"},
}

# Filing type registry — maps filing ID to metadata
FILING_REGISTRY = {
    "F1":  {"name": "Emergency TRO", "lane": "B", "court": "circuit", "type": "motion"},
    "F2":  {"name": "Shady Oaks Complaint", "lane": "B", "court": "circuit", "type": "complaint"},
    "F3":  {"name": "Disqualification MCR 2.003", "lane": "A", "court": "circuit", "type": "motion"},
    "F4":  {"name": "Federal §1983 Complaint", "lane": "C", "court": "federal", "type": "complaint"},
    "F5":  {"name": "MSC Original Action", "lane": "E", "court": "supreme", "type": "complaint"},
    "F6":  {"name": "JTC Complaint", "lane": "E", "court": "jtc", "type": "complaint"},
    "F7":  {"name": "Custody Modification", "lane": "A", "court": "circuit_family", "type": "motion"},
    "F8":  {"name": "PPO Termination", "lane": "D", "court": "circuit", "type": "motion"},
    "F9":  {"name": "COA Brief on Appeal", "lane": "F", "court": "appellate", "type": "brief"},
    "F10": {"name": "COA Emergency Motion", "lane": "F", "court": "appellate", "type": "motion"},
}

# Dynamic day calculation — NEVER hardcode
def days_since(start_date_str: str) -> int:
    """Calculate days from a date string to today."""
    start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    return (date.today() - start).days

def separation_days() -> int:
    """Days since Jul 29, 2025 parental separation."""
    return days_since("2025-07-29")


# ═══════════════════════════════════════════════════════════════
# DATABASE ACCESS LAYER
# ═══════════════════════════════════════════════════════════════

class DBAccess:
    """Unified access to all 11+ databases with WAL mode and busy timeout."""
    
    PRAGMAS = """
        PRAGMA busy_timeout=60000;
        PRAGMA journal_mode=WAL;
        PRAGMA cache_size=-32000;
        PRAGMA temp_store=MEMORY;
        PRAGMA synchronous=NORMAL;
    """
    
    def __init__(self):
        self._connections: Dict[str, sqlite3.Connection] = {}
    
    def get_conn(self, db_path: Path) -> sqlite3.Connection:
        key = str(db_path)
        if key not in self._connections:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            conn.executescript(self.PRAGMAS)
            self._connections[key] = conn
        return self._connections[key]
    
    def close_all(self):
        for conn in self._connections.values():
            try:
                conn.close()
            except Exception:
                pass
        self._connections.clear()
    
    @property
    def litigation(self) -> sqlite3.Connection:
        return self.get_conn(LITIGATION_DB)
    
    @property
    def court_forms(self) -> sqlite3.Connection:
        return self.get_conn(COURT_FORMS_DB)
    
    def jurisdiction(self, name: str) -> sqlite3.Connection:
        return self.get_conn(DATABASES_DIR / f"jurisdiction_{name}.db")
    
    def knowledge(self, name: str) -> sqlite3.Connection:
        return self.get_conn(DATABASES_DIR / f"{name}.db")
    
    def query(self, db_path: Path, sql: str, params: tuple = ()) -> List[dict]:
        conn = self.get_conn(db_path)
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    
    def cross_query(self, sql_map: Dict[str, Tuple[Path, str, tuple]]) -> Dict[str, List[dict]]:
        """Execute queries across multiple DBs in one call."""
        results = {}
        for key, (db_path, sql, params) in sql_map.items():
            try:
                results[key] = self.query(db_path, sql, params)
            except Exception as e:
                results[key] = [{"error": str(e)}]
        return results


# ═══════════════════════════════════════════════════════════════
# CITATION ENGINE
# ═══════════════════════════════════════════════════════════════

class CitationEngine:
    """Validates and formats legal citations."""
    
    # Michigan citation patterns
    MICHIGAN_CASE_PATTERN = re.compile(
        r'(?P<name>[A-Z][a-zA-Z\s&\',.-]+)\s+v\s+(?P<opponent>[A-Z][a-zA-Z\s&\',.-]+),?\s*'
        r'(?P<volume>\d+)\s+(?P<reporter>Mich(?:\s+App)?|NW2d|NW\.?2d)\s+(?P<page>\d+)'
        r'(?:\s*\((?P<year>\d{4})\))?'
    )
    FEDERAL_CASE_PATTERN = re.compile(
        r'(?P<name>[A-Z][a-zA-Z\s&\',.-]+)\s+v\s+(?P<opponent>[A-Z][a-zA-Z\s&\',.-]+),?\s*'
        r'(?P<volume>\d+)\s+(?P<reporter>US|S\.?\s*Ct\.?|F\.?\s*(?:2d|3d|4th)?|F\.?\s*Supp\.?\s*(?:2d|3d)?)\s+(?P<page>\d+)'
        r'(?:\s*\((?P<year>\d{4})\))?'
    )
    MCL_PATTERN = re.compile(r'MCL\s+(\d+\.\d+[a-z]?(?:\(\d+\))?)')
    MCR_PATTERN = re.compile(r'MCR\s+(\d+\.\d+(?:\([A-Z]\)(?:\(\d+\))?)?)')
    USC_PATTERN = re.compile(r'(\d+)\s+USC\s+[§]?\s*(\d+[a-z]?)')
    
    # Known fabricated citations — REJECT on sight
    KNOWN_FABRICATIONS = {
        "McCraney v Ford Motor Co",
        "MCL 600.2145",  # misapplied for right to counsel
        "Patricia Berry",
        "Jane Berry",
    }
    
    def __init__(self, db: DBAccess):
        self.db = db
        self._known_cache: Optional[Dict[str, dict]] = None
    
    def _load_known_citations(self):
        if self._known_cache is not None:
            return
        try:
            rows = self.db.query(LITIGATION_DB,
                "SELECT * FROM known_citations", ())
            self._known_cache = {r.get("citation", ""): r for r in rows}
        except Exception:
            self._known_cache = {}
    
    def validate_citation(self, citation_text: str) -> Dict[str, Any]:
        """Validate a single citation. Returns {valid, format, issues, authority_type}."""
        result = {"text": citation_text, "valid": True, "issues": [], "authority_type": "unknown"}
        
        # Check fabrication list
        for fab in self.KNOWN_FABRICATIONS:
            if fab.lower() in citation_text.lower():
                result["valid"] = False
                result["issues"].append(f"FABRICATED CITATION: '{fab}' is a known hallucination")
                return result
        
        # Detect type
        if self.MCL_PATTERN.search(citation_text):
            result["authority_type"] = "michigan_statute"
        elif self.MCR_PATTERN.search(citation_text):
            result["authority_type"] = "michigan_court_rule"
        elif self.USC_PATTERN.search(citation_text):
            result["authority_type"] = "federal_statute"
        elif self.MICHIGAN_CASE_PATTERN.search(citation_text):
            result["authority_type"] = "michigan_case"
        elif self.FEDERAL_CASE_PATTERN.search(citation_text):
            result["authority_type"] = "federal_case"
        
        # Check against known citations DB
        self._load_known_citations()
        if self._known_cache:
            for key, data in self._known_cache.items():
                if key and key.lower() in citation_text.lower():
                    status = data.get("status", "unknown")
                    if status == "hallucinated":
                        result["valid"] = False
                        result["issues"].append(f"DB flagged as HALLUCINATED: {key}")
                    elif status == "verified":
                        result["db_verified"] = True
                    break
        
        return result
    
    def scan_document(self, text: str) -> List[Dict[str, Any]]:
        """Scan a document for all citations and validate each."""
        citations = []
        # Find all case citations
        for pattern in [self.MICHIGAN_CASE_PATTERN, self.FEDERAL_CASE_PATTERN]:
            for m in pattern.finditer(text):
                citations.append(self.validate_citation(m.group()))
        # Find statute citations
        for pattern in [self.MCL_PATTERN, self.MCR_PATTERN, self.USC_PATTERN]:
            for m in pattern.finditer(text):
                citations.append(self.validate_citation(m.group()))
        return citations


# ═══════════════════════════════════════════════════════════════
# AFFIDAVIT ENGINE
# ═══════════════════════════════════════════════════════════════

class AffidavitEngine:
    """Generates MCR 2.114-compliant affidavits with exhibit references."""
    
    VERIFICATION_BLOCK = """
## VERIFICATION

I, {name}, declare under penalty of perjury pursuant to MCL 600.1561 and 
28 USC § 1746 that the foregoing statements are true and correct to the 
best of my knowledge, information, and belief.

Dated: {date}

_________________________________
{name}
{address}
{city}, {state} {zip}
{phone}
"""

    NOTARY_BLOCK = """
## NOTARIZATION

STATE OF MICHIGAN  )
                   ) ss.
COUNTY OF MUSKEGON )

Subscribed and sworn to before me this _____ day of _____________, 20___.

_________________________________
Notary Public, Muskegon County, Michigan
My Commission Expires: _______________
"""

    EXHIBIT_COVER = """
---

# EXHIBIT {letter}

**{title}**

{description}

---
*Attached to the {filing_type} of Andrew James Pigors*  
*Case No. {case_number}*  
*{court}*

---
"""

    def generate_affidavit(self, filing_id: str, statements: List[Dict[str, str]],
                           exhibits: List[Dict[str, str]]) -> str:
        """Generate a complete affidavit with numbered paragraphs and exhibit refs.
        
        Args:
            filing_id: e.g., "F3" for Disqualification
            statements: List of {"text": "...", "exhibit_ref": "A"} dicts
            exhibits: List of {"letter": "A", "title": "...", "description": "..."} dicts
        """
        filing = FILING_REGISTRY.get(filing_id, {})
        lane_id = filing.get("lane", "A")
        lane = CASE_LANES.get(lane_id, {})
        
        lines = []
        lines.append(f"# AFFIDAVIT OF {PARTY_DATA['plaintiff']['name'].upper()}")
        lines.append("")
        lines.append(f"**In Support of {filing.get('name', 'Filing')}**")
        lines.append(f"**Case No. {lane.get('case_number', '[CASE NUMBER]')}**")
        lines.append(f"**{lane.get('court', '[COURT]')}**")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"I, {PARTY_DATA['plaintiff']['name']}, being duly sworn, depose and state:")
        lines.append("")
        
        for i, stmt in enumerate(statements, 1):
            text = stmt["text"]
            ref = stmt.get("exhibit_ref")
            if ref:
                text += f" (See **Exhibit {ref}**, attached hereto and incorporated by reference.)"
            lines.append(f"{i}. {text}")
            lines.append("")
        
        # Exhibit list
        if exhibits:
            lines.append("---")
            lines.append("")
            lines.append("## EXHIBIT INDEX")
            lines.append("")
            for ex in exhibits:
                lines.append(f"- **Exhibit {ex['letter']}**: {ex['title']}")
            lines.append("")
        
        # Verification
        lines.append(self.VERIFICATION_BLOCK.format(
            name=PARTY_DATA["plaintiff"]["name"],
            date="________________, 2026",
            address=PARTY_DATA["plaintiff"]["address"],
            city=PARTY_DATA["plaintiff"]["city"],
            state=PARTY_DATA["plaintiff"]["state"],
            zip=PARTY_DATA["plaintiff"]["zip"],
            phone=PARTY_DATA["plaintiff"]["phone"],
        ))
        
        # Notary
        lines.append(self.NOTARY_BLOCK)
        
        return "\n".join(lines)
    
    def generate_exhibit_cover(self, letter: str, title: str, description: str,
                                filing_id: str) -> str:
        """Generate exhibit cover page."""
        filing = FILING_REGISTRY.get(filing_id, {})
        lane_id = filing.get("lane", "A")
        lane = CASE_LANES.get(lane_id, {})
        return self.EXHIBIT_COVER.format(
            letter=letter,
            title=title,
            description=description,
            filing_type=filing.get("name", "Filing"),
            case_number=lane.get("case_number", "[CASE NUMBER]"),
            court=lane.get("court", "[COURT]"),
        )


# ═══════════════════════════════════════════════════════════════
# COURT FORM ENGINE
# ═══════════════════════════════════════════════════════════════

class CourtFormEngine:
    """Queries court_forms.db and auto-fills forms for filing packages."""
    
    def __init__(self, db: DBAccess):
        self.db = db
    
    def get_required_forms(self, filing_id: str) -> List[dict]:
        """Get all required court forms for a filing type."""
        filing = FILING_REGISTRY.get(filing_id, {})
        filing_type = filing.get("name", "")
        lane = filing.get("lane", "")
        
        try:
            rows = self.db.query(COURT_FORMS_DB, """
                SELECT cf.form_number, cf.form_name, cf.court_level, cf.url,
                       cf.fillable, cf.page_count, ffm.required, ffm.order_in_package
                FROM form_filing_map ffm
                JOIN court_forms cf ON ffm.form_id = cf.form_id
                WHERE ffm.lane = ? OR ffm.lane = 'ALL'
                ORDER BY ffm.required DESC, ffm.order_in_package
            """, (lane,))
            return rows
        except Exception:
            return []
    
    def get_auto_fill_data(self, form_number: str) -> Dict[str, str]:
        """Get auto-fill values for a specific form."""
        try:
            fields = self.db.query(COURT_FORMS_DB, """
                SELECT ff.field_name, ff.field_label, ff.auto_fill_source, 
                       ff.auto_fill_value, ff.required
                FROM form_fields ff
                JOIN court_forms cf ON ff.form_id = cf.form_id
                WHERE cf.form_number = ?
            """, (form_number,))
            
            result = {}
            for f in fields:
                source = f.get("auto_fill_source", "")
                value = f.get("auto_fill_value", "")
                
                if source == "party_data":
                    # Resolve from PARTY_DATA
                    parts = value.split(".")
                    data = PARTY_DATA
                    for p in parts:
                        if isinstance(data, dict):
                            data = data.get(p, "")
                    result[f["field_name"]] = str(data) if data else "[FILL]"
                elif source == "case_data":
                    result[f["field_name"]] = value or "[FILL]"
                elif source == "computed":
                    if value == "separation_days":
                        result[f["field_name"]] = str(separation_days())
                    elif value == "today":
                        result[f["field_name"]] = date.today().strftime("%B %d, %Y")
                    else:
                        result[f["field_name"]] = "[FILL]"
                else:
                    result[f["field_name"]] = value or "[FILL]"
            
            return result
        except Exception:
            return {}
    
    def generate_form_checklist(self, filing_id: str) -> str:
        """Generate a checklist of all forms needed for a filing."""
        forms = self.get_required_forms(filing_id)
        filing = FILING_REGISTRY.get(filing_id, {})
        
        lines = [f"# COURT FORM CHECKLIST — {filing.get('name', filing_id)}", ""]
        lines.append(f"**Case Lane:** {filing.get('lane', '?')} ({CASE_LANES.get(filing.get('lane', ''), {}).get('name', '')})")
        lines.append(f"**Case Number:** {CASE_LANES.get(filing.get('lane', ''), {}).get('case_number', '')}")
        lines.append("")
        
        required = [f for f in forms if f.get("required")]
        optional = [f for f in forms if not f.get("required")]
        
        if required:
            lines.append("## REQUIRED FORMS")
            for f in required:
                fill = self.get_auto_fill_data(f["form_number"])
                fill_count = sum(1 for v in fill.values() if v != "[FILL]")
                total = len(fill)
                status = "✅ AUTO-FILLED" if fill_count == total and total > 0 else f"⚠️ {fill_count}/{total} fields filled"
                lines.append(f"- [ ] **{f['form_number']}** — {f['form_name']} ({status})")
            lines.append("")
        
        if optional:
            lines.append("## OPTIONAL FORMS")
            for f in optional:
                lines.append(f"- [ ] {f['form_number']} — {f['form_name']}")
            lines.append("")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# QUALITY GATE
# ═══════════════════════════════════════════════════════════════

class QualityGate:
    """Pre-filing quality assurance — GO/NO-GO decision."""
    
    KNOWN_HALLUCINATIONS = [
        "Jane Berry", "Patricia Berry", "SBN P35878",
        "nine (9) separate police investigations",
        "9 CPS investigations", "91% alienation score",
        "584 consecutive days", "569 days",
        "McCraney v Ford Motor", "MCL 600.2145",
    ]
    
    def __init__(self, db: DBAccess, citation_engine: CitationEngine):
        self.db = db
        self.citation_engine = citation_engine
    
    def check_hallucinations(self, text: str) -> List[str]:
        """Scan for known hallucinated content."""
        found = []
        for h in self.KNOWN_HALLUCINATIONS:
            if h.lower() in text.lower():
                found.append(f"🔴 HALLUCINATION DETECTED: '{h}'")
        return found
    
    def check_party_names(self, text: str) -> List[str]:
        """Verify party names are correct."""
        issues = []
        # Check for wrong names
        wrong_names = {
            "Emily Ann": "Should be 'Emily A. Watson'",
            "Emily M.": "Should be 'Emily A. Watson'",
            "Amy McNeill": "Should be 'Jenny L. McNeill'",
            "Patricia Berry": "NEVER EXISTED — hallucination",
            "Jane Berry": "NEVER EXISTED — hallucination",
        }
        for wrong, fix in wrong_names.items():
            if wrong in text:
                issues.append(f"🔴 WRONG NAME: '{wrong}' — {fix}")
        
        # Check child's name not exposed
        # We can't check for the actual name but we ensure L.D.W. is used
        if "L.D.W." not in text and "child" in text.lower():
            issues.append("⚠️ Verify child referred to as 'L.D.W.' per MCR 8.119(H)")
        
        return issues
    
    def check_required_sections(self, text: str, filing_type: str) -> List[str]:
        """Check that required sections exist for filing type."""
        issues = []
        common_sections = {
            "complaint": ["JURISDICTION", "PARTIES", "FACTS", "CAUSES OF ACTION", "PRAYER FOR RELIEF", "VERIFICATION"],
            "motion": ["STATEMENT OF FACTS", "ARGUMENT", "RELIEF REQUESTED", "VERIFICATION"],
            "brief": ["STATEMENT OF JURISDICTION", "STATEMENT OF QUESTIONS", "STATEMENT OF FACTS", "ARGUMENT", "RELIEF REQUESTED"],
        }
        required = common_sections.get(filing_type, [])
        text_upper = text.upper()
        for section in required:
            if section not in text_upper:
                issues.append(f"⚠️ MISSING SECTION: '{section}' (required for {filing_type})")
        return issues
    
    def check_dates_consistent(self, text: str) -> List[str]:
        """Check for hardcoded day counts that should be dynamic."""
        issues = []
        bad_patterns = [
            (r'\b584\s+(?:consecutive\s+)?days?\b', "584 days is WRONG — calculate dynamically"),
            (r'\b569\s+days?\b', "569 days is WRONG — calculate dynamically"),
        ]
        for pattern, msg in bad_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"🔴 HARDCODED DATE: {msg}")
        return issues
    
    def full_audit(self, text: str, filing_id: str) -> Dict[str, Any]:
        """Run complete QA audit on a filing."""
        filing = FILING_REGISTRY.get(filing_id, {})
        filing_type = filing.get("type", "unknown")
        
        hallucinations = self.check_hallucinations(text)
        party_issues = self.check_party_names(text)
        section_issues = self.check_required_sections(text, filing_type)
        date_issues = self.check_dates_consistent(text)
        citation_results = self.citation_engine.scan_document(text)
        
        bad_citations = [c for c in citation_results if not c.get("valid")]
        
        all_issues = hallucinations + party_issues + section_issues + date_issues
        for bc in bad_citations:
            all_issues.append(f"🔴 BAD CITATION: {bc['text']} — {'; '.join(bc['issues'])}")
        
        blocker_count = sum(1 for i in all_issues if "🔴" in i)
        warning_count = sum(1 for i in all_issues if "⚠️" in i)
        
        go_no_go = "GO" if blocker_count == 0 else "NO-GO"
        
        return {
            "filing_id": filing_id,
            "filing_name": filing.get("name", filing_id),
            "go_no_go": go_no_go,
            "blockers": blocker_count,
            "warnings": warning_count,
            "total_citations": len(citation_results),
            "valid_citations": len(citation_results) - len(bad_citations),
            "issues": all_issues,
        }


# ═══════════════════════════════════════════════════════════════
# FILING FACTORY — MASTER ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

class FilingFactory:
    """Master orchestrator that produces complete court-ready filing packages."""
    
    def __init__(self):
        self.db = DBAccess()
        self.citations = CitationEngine(self.db)
        self.affidavits = AffidavitEngine()
        self.forms = CourtFormEngine(self.db)
        self.quality = QualityGate(self.db, self.citations)
    
    def generate_caption(self, filing_id: str) -> str:
        """Generate proper Michigan court caption."""
        filing = FILING_REGISTRY.get(filing_id, {})
        lane_id = filing.get("lane", "A")
        lane = CASE_LANES.get(lane_id, {})
        
        court = lane.get("court", "[COURT]")
        case_num = lane.get("case_number", "[CASE NUMBER]")
        judge = PARTY_DATA["judge"]["name"]
        
        caption = f"""STATE OF MICHIGAN
IN THE {court.upper()}
COUNTY OF MUSKEGON

{PARTY_DATA['plaintiff']['name'].upper()},
    Plaintiff,                              Case No. {case_num}

v.                                          {judge}

{PARTY_DATA['defendant']['name'].upper()},
    Defendant.
__________________________________________/
"""
        return caption
    
    def generate_signature_block(self) -> str:
        """Generate pro se signature block per MCR 2.114."""
        p = PARTY_DATA["plaintiff"]
        return f"""
Respectfully submitted,

Dated: _________________, 2026

_________________________________
{p['name']}
{p['address']}
{p['city']}, {p['state']} {p['zip']}
{p['phone']}
{p['email']}
Plaintiff, In Pro Per
"""
    
    def generate_certificate_of_service(self, filing_id: str) -> str:
        """Generate certificate of service."""
        return f"""
## CERTIFICATE OF SERVICE

I hereby certify that on _________________, 2026, I served a true copy of the 
foregoing document upon the following parties by [☐ first-class mail] [☐ e-filing 
via MiFILE] [☐ personal delivery]:

{PARTY_DATA['defendant']['name']}
{PARTY_DATA['defendant']['address']}
{PARTY_DATA['defendant']['city']}, {PARTY_DATA['defendant']['state']} {PARTY_DATA['defendant']['zip']}

_________________________________
{PARTY_DATA['plaintiff']['name']}
"""
    
    def audit_filing(self, filing_id: str, filing_text: str) -> Dict[str, Any]:
        """Run full QA audit on a filing."""
        return self.quality.full_audit(filing_text, filing_id)
    
    def audit_all_filings(self, filing_dir: Path = OUTPUT_BASE) -> Dict[str, Any]:
        """Audit all 10 canonical filings."""
        results = {}
        for fid in sorted(FILING_REGISTRY.keys()):
            num = fid.replace("F", "").zfill(2)
            fname = FILING_REGISTRY[fid]["name"].upper().replace(" ", "_")
            # Try common naming patterns
            candidates = list(filing_dir.glob(f"{num}_*.md"))
            if not candidates:
                results[fid] = {"filing_id": fid, "go_no_go": "MISSING", "issues": ["Filing file not found"]}
                continue
            text = candidates[0].read_text(encoding="utf-8", errors="replace")
            results[fid] = self.audit_filing(fid, text)
        return results
    
    def generate_package_manifest(self, filing_id: str) -> str:
        """Generate a complete package manifest for a filing."""
        filing = FILING_REGISTRY.get(filing_id, {})
        lane_id = filing.get("lane", "A")
        lane = CASE_LANES.get(lane_id, {})
        
        lines = []
        lines.append(f"# FILING PACKAGE MANIFEST — {filing.get('name', filing_id)}")
        lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        lines.append(f"**Case:** {lane.get('case_number', '')} ({lane.get('name', '')})")
        lines.append(f"**Court:** {lane.get('court', '')}")
        lines.append("")
        lines.append("## DOCUMENTS IN THIS PACKAGE")
        lines.append("")
        lines.append(f"1. **{filing.get('name', 'Main Document')}** — The primary filing")
        lines.append(f"2. **Affidavit of {PARTY_DATA['plaintiff']['name']}** — Verification under oath")
        lines.append(f"3. **Exhibit Index** — Tabbed exhibits referenced in affidavit")
        lines.append(f"4. **Certificate of Service** — Proof of service on opposing party")
        
        # Court forms
        forms = self.forms.get_required_forms(filing_id)
        if forms:
            for i, f in enumerate(forms, 5):
                req = "REQUIRED" if f.get("required") else "Optional"
                lines.append(f"{i}. **{f['form_number']} — {f['form_name']}** ({req})")
        
        lines.append("")
        lines.append("## FILING CHECKLIST")
        lines.append("")
        lines.append("- [ ] Main document reviewed and signed")
        lines.append("- [ ] Affidavit signed and notarized (if required)")
        lines.append("- [ ] All exhibits attached with cover pages")
        lines.append("- [ ] Certificate of service completed")
        lines.append("- [ ] Court forms filled and attached")
        lines.append("- [ ] Fee waiver MC 20 attached (if applicable)")
        lines.append("- [ ] E-filed via MiFILE OR filed in person at clerk's office")
        lines.append("")
        
        return "\n".join(lines)
    
    def generate_full_package(self, filing_id: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Generate a COMPLETE court-ready filing package.
        
        Creates a directory with:
          01_MAIN_FILING.md — The primary motion/complaint/brief
          02_AFFIDAVIT.md — Verification affidavit with exhibit refs
          03_EXHIBIT_INDEX.md — Tabbed exhibit index with cover pages
          04_CERTIFICATE_OF_SERVICE.md — Proof of service
          05_COURT_FORMS_CHECKLIST.md — Required forms with auto-fill data
          06_CAPTION.md — Standalone caption for each document
          PACKAGE_MANIFEST.md — Master checklist of everything
        
        Returns: dict with package_dir, file_count, qa_result, warnings
        """
        filing = FILING_REGISTRY.get(filing_id)
        if not filing:
            return {"error": f"Unknown filing ID: {filing_id}"}
        
        lane_id = filing.get("lane", "A")
        lane = CASE_LANES.get(lane_id, {})
        safe_name = filing["name"].upper().replace(" ", "_").replace("§", "S").replace(".", "")
        
        pkg_dir = (output_dir or OUTPUT_BASE) / f"PKG_{filing_id}_{safe_name}"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        files_created = []
        
        # 1. Find and copy main filing
        source_num = filing_id.replace("F", "").zfill(2)
        source_candidates = list(OUTPUT_BASE.glob(f"{source_num}_*.md"))
        main_text = ""
        if source_candidates:
            main_text = source_candidates[0].read_text(encoding="utf-8", errors="replace")
            main_path = pkg_dir / "01_MAIN_FILING.md"
            main_path.write_text(main_text, encoding="utf-8")
            files_created.append(str(main_path))
        
        # 2. Generate caption
        caption = self.generate_caption(filing_id)
        caption_path = pkg_dir / "06_CAPTION.md"
        caption_path.write_text(caption, encoding="utf-8")
        files_created.append(str(caption_path))
        
        # 3. Generate affidavit with exhibit references from the main filing
        exhibit_refs = self._extract_exhibit_refs(main_text)
        statements = self._build_affidavit_statements(filing_id, main_text)
        affidavit = self.affidavits.generate_affidavit(filing_id, statements, exhibit_refs)
        aff_path = pkg_dir / "02_AFFIDAVIT.md"
        aff_path.write_text(affidavit, encoding="utf-8")
        files_created.append(str(aff_path))
        
        # 4. Generate exhibit index with cover pages
        exhibit_index = self._build_exhibit_index(filing_id, exhibit_refs)
        ex_path = pkg_dir / "03_EXHIBIT_INDEX.md"
        ex_path.write_text(exhibit_index, encoding="utf-8")
        files_created.append(str(ex_path))
        
        # 5. Certificate of service
        cos = self.generate_certificate_of_service(filing_id)
        cos_path = pkg_dir / "04_CERTIFICATE_OF_SERVICE.md"
        cos_path.write_text(cos, encoding="utf-8")
        files_created.append(str(cos_path))
        
        # 6. Court forms checklist with auto-fill data
        forms_checklist = self.forms.generate_form_checklist(filing_id)
        forms_path = pkg_dir / "05_COURT_FORMS_CHECKLIST.md"
        forms_path.write_text(forms_checklist, encoding="utf-8")
        files_created.append(str(forms_path))
        
        # 7. Package manifest
        manifest = self.generate_package_manifest(filing_id)
        manifest_path = pkg_dir / "PACKAGE_MANIFEST.md"
        manifest_path.write_text(manifest, encoding="utf-8")
        files_created.append(str(manifest_path))
        
        # 8. Run QA audit on the main filing
        qa_result = {}
        if main_text:
            qa_result = self.audit_filing(filing_id, main_text)
        
        return {
            "filing_id": filing_id,
            "filing_name": filing["name"],
            "package_dir": str(pkg_dir),
            "files_created": len(files_created),
            "file_list": files_created,
            "qa_result": qa_result,
            "go_no_go": qa_result.get("go_no_go", "UNKNOWN"),
        }
    
    def generate_all_packages(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Generate complete packages for ALL 10 filings."""
        results = {}
        for fid in sorted(FILING_REGISTRY.keys()):
            results[fid] = self.generate_full_package(fid, output_dir)
        
        # Summary
        total_files = sum(r.get("files_created", 0) for r in results.values())
        go_count = sum(1 for r in results.values() if r.get("go_no_go") == "GO")
        
        return {
            "total_packages": len(results),
            "total_files": total_files,
            "go_count": go_count,
            "no_go_count": len(results) - go_count,
            "packages": results,
        }
    
    def _extract_exhibit_refs(self, text: str) -> List[Dict[str, str]]:
        """Extract exhibit references from filing text."""
        exhibits = []
        seen = set()
        # Match patterns like "Exhibit A", "Exhibit B — Title"
        pattern = re.compile(
            r'[Ee]xhibit\s+([A-Z](?:\d{0,2})?)(?:\s*[-—:]\s*([^\n.;]+))?'
        )
        for m in pattern.finditer(text):
            letter = m.group(1)
            if letter in seen:
                continue
            seen.add(letter)
            title = (m.group(2) or f"Exhibit {letter}").strip()
            exhibits.append({
                "letter": letter,
                "title": title,
                "description": f"Supporting evidence for the claims herein. See Exhibit {letter}.",
            })
        return exhibits
    
    def _build_affidavit_statements(self, filing_id: str, main_text: str) -> List[Dict[str, str]]:
        """Build affidavit statements from filing content and DB evidence."""
        statements = []
        filing = FILING_REGISTRY.get(filing_id, {})
        lane_id = filing.get("lane", "A")
        lane = CASE_LANES.get(lane_id, {})
        
        # Standard opening statements
        statements.append({
            "text": f"I am the Plaintiff in the above-captioned matter, Case No. "
                    f"{lane.get('case_number', '[CASE NUMBER]')}, pending before "
                    f"{PARTY_DATA['judge']['name']} in the {lane.get('court', '[COURT]')}.",
        })
        statements.append({
            "text": "I am over 18 years of age and competent to testify to the matters "
                    "herein based on my personal knowledge and experience.",
        })
        statements.append({
            "text": "I am the father of L.D.W. (minor child, initials used per "
                    "MCR 8.119(H)), born November 9, 2022.",
        })
        
        # Dynamic separation days
        sep = separation_days()
        statements.append({
            "text": f"As of the date of this affidavit, I have been separated from my "
                    f"son L.D.W. for {sep} consecutive days since July 29, 2025, when "
                    f"the Defendant unilaterally ceased all parenting time.",
        })
        
        # Filing-specific statements from DB
        try:
            rows = self.db.query(LITIGATION_DB,
                "SELECT quote_text, source_file FROM evidence_quotes "
                "WHERE claim_id LIKE ? LIMIT 10",
                (f"%{lane_id}%",))
            for i, row in enumerate(rows):
                quote = row.get("quote_text", "")
                source = row.get("source_file", "")
                if quote and len(quote) > 30:
                    letter = chr(65 + i)  # A, B, C...
                    statements.append({
                        "text": quote[:500],
                        "exhibit_ref": letter,
                    })
        except Exception:
            pass
        
        statements.append({
            "text": "The above statements are true and correct to the best of my knowledge, "
                    "information, and belief.",
        })
        
        return statements
    
    def _build_exhibit_index(self, filing_id: str, exhibits: List[Dict[str, str]]) -> str:
        """Build exhibit index with cover pages."""
        filing = FILING_REGISTRY.get(filing_id, {})
        lane_id = filing.get("lane", "A")
        lane = CASE_LANES.get(lane_id, {})
        
        lines = []
        lines.append(f"# EXHIBIT INDEX")
        lines.append(f"**{filing.get('name', '')}**")
        lines.append(f"**Case No. {lane.get('case_number', '')}**")
        lines.append("")
        lines.append("| Exhibit | Description | Pages |")
        lines.append("|---------|-------------|-------|")
        for ex in exhibits:
            lines.append(f"| **{ex['letter']}** | {ex['title']} | [___] |")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Generate individual cover pages
        for ex in exhibits:
            cover = self.affidavits.generate_exhibit_cover(
                ex["letter"], ex["title"], ex.get("description", ""),
                filing_id
            )
            lines.append(cover)
            lines.append("")
        
        return "\n".join(lines)

    def close(self):
        self.db.close_all()


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════

def main():
    """CLI for Filing Factory operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Filing Factory — Court-Ready Package Generator")
    sub = parser.add_subparsers(dest="command")
    
    # Audit command
    audit_p = sub.add_parser("audit", help="Audit all filings for quality issues")
    audit_p.add_argument("--filing", help="Specific filing ID (e.g., F3)")
    audit_p.add_argument("--dir", default=str(OUTPUT_BASE), help="Filing directory")
    
    # Manifest command
    manifest_p = sub.add_parser("manifest", help="Generate package manifest")
    manifest_p.add_argument("filing_id", help="Filing ID (e.g., F3)")
    
    # Forms command
    forms_p = sub.add_parser("forms", help="List required court forms")
    forms_p.add_argument("filing_id", help="Filing ID (e.g., F3)")
    
    # Caption command
    caption_p = sub.add_parser("caption", help="Generate court caption")
    caption_p.add_argument("filing_id", help="Filing ID (e.g., F3)")
    
    # Package command (NEW — end-to-end)
    package_p = sub.add_parser("package", help="Generate complete filing package")
    package_p.add_argument("filing_id", help="Filing ID (e.g., F3)")
    package_p.add_argument("--dir", default=str(OUTPUT_BASE), help="Output directory")
    
    # Package-all command (NEW — all 10 filings)
    package_all_p = sub.add_parser("package-all", help="Generate ALL 10 filing packages")
    package_all_p.add_argument("--dir", default=str(OUTPUT_BASE), help="Output directory")
    
    # Status command
    sub.add_parser("status", help="Show all filings status")
    
    args = parser.parse_args()
    factory = FilingFactory()
    
    try:
        if args.command == "audit":
            if args.filing:
                filing_path = Path(args.dir)
                candidates = list(filing_path.glob(f"{args.filing.replace('F', '').zfill(2)}_*.md"))
                if candidates:
                    text = candidates[0].read_text(encoding="utf-8", errors="replace")
                    result = factory.audit_filing(args.filing, text)
                    print(json.dumps(result, indent=2))
                else:
                    print(f"Filing {args.filing} not found in {args.dir}")
            else:
                results = factory.audit_all_filings(Path(args.dir))
                for fid, r in sorted(results.items()):
                    status = "✅ GO" if r["go_no_go"] == "GO" else "❌ NO-GO" if r["go_no_go"] == "NO-GO" else "⚠️ MISSING"
                    print(f"  {fid} {FILING_REGISTRY.get(fid, {}).get('name', ''):40s} {status}  ({r.get('blockers', 0)} blockers, {r.get('warnings', 0)} warnings)")
        
        elif args.command == "manifest":
            print(factory.generate_package_manifest(args.filing_id))
        
        elif args.command == "forms":
            print(factory.forms.generate_form_checklist(args.filing_id))
        
        elif args.command == "caption":
            print(factory.generate_caption(args.filing_id))
        
        elif args.command == "package":
            result = factory.generate_full_package(args.filing_id, Path(args.dir))
            print(f"📦 Package generated: {result.get('package_dir', 'ERROR')}")
            print(f"   Files: {result.get('files_created', 0)}")
            print(f"   QA: {result.get('go_no_go', 'UNKNOWN')}")
            if result.get('qa_result', {}).get('issues'):
                for issue in result['qa_result']['issues'][:5]:
                    print(f"   {issue}")
        
        elif args.command == "package-all":
            results = factory.generate_all_packages(Path(args.dir))
            print(f"📦 Generated {results['total_packages']} packages ({results['total_files']} files)")
            print(f"   GO: {results['go_count']} | NO-GO: {results['no_go_count']}")
            for fid, r in sorted(results.get('packages', {}).items()):
                status = "✅" if r.get("go_no_go") == "GO" else "❌"
                print(f"   {status} {fid}: {r.get('filing_name', '')} → {r.get('files_created', 0)} files")
        
        elif args.command == "status":
            print("FILING REGISTRY — 10 Filings Across 6 Lanes")
            print("=" * 70)
            for fid, meta in sorted(FILING_REGISTRY.items()):
                lane = CASE_LANES.get(meta["lane"], {})
                print(f"  {fid}: {meta['name']:40s} Lane {meta['lane']} ({lane.get('name', '')}) [{meta['type']}]")
        
        else:
            parser.print_help()
    finally:
        factory.close()


if __name__ == "__main__":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    main()
