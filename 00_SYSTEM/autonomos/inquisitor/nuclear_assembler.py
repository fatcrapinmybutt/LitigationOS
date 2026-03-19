"""
DELTA99 Ω∞ — Nuclear Filing Assembler
=======================================
Assembles complete, court-ready filing packages from DB intelligence.
Pulls authority chains, evidence quotes, claims, and auto-generates:
caption → body → index of authorities → certificate of service → exhibit index.

Depends on: d99-citation-validator (validates all citations before assembly)
"""
import sys
import sqlite3
import json
import time
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB, LITIGOS_ROOT

ASSEMBLER_DB = Path(__file__).parent / "nuclear_assembler.db"
OUTPUT_DIR = LITIGOS_ROOT / "06_FILINGS" / "NUCLEAR_ASSEMBLED"

# ── Michigan Court Formatting ──────────────────────────────────────
CAPTION_TEMPLATE = """STATE OF MICHIGAN
IN THE {court}
COUNTY OF MUSKEGON

ANDREW J. PIGORS,
    Plaintiff/Petitioner,                    Case No. {case_no}

v.                                           Hon. {judge}

EMILY A. WATSON,
    Defendant/Respondent.
{separator}
{attorney_block}
"""

ATTORNEY_BLOCK = """ANDREW J. PIGORS, Pro Se
[ADDRESS]
[PHONE]
[EMAIL]"""

CERTIFICATE_OF_SERVICE = """
CERTIFICATE OF SERVICE

I hereby certify that on {date}, I served a true copy of the foregoing
{document_name} upon the following by {service_method}:

{parties}

                                        ________________________________
                                        Andrew J. Pigors, Pro Se
                                        Date: {date}
"""

# ── Court Configurations ───────────────────────────────────────────
COURTS = {
    "14th_circuit": {"name": "14TH CIRCUIT COURT", "case": "2024-001507-DC", "judge": "Jenny L. McNeill"},
    "COA": {"name": "COURT OF APPEALS", "case": "366810", "judge": "Panel TBD"},
    "MSC": {"name": "SUPREME COURT", "case": "TBD", "judge": ""},
    "USDC": {"name": "UNITED STATES DISTRICT COURT\nWESTERN DISTRICT OF MICHIGAN", "case": "TBD", "judge": "TBD"},
    "JTC": {"name": "JUDICIAL TENURE COMMISSION", "case": "N/A", "judge": "N/A"},
}


def _init_db() -> sqlite3.Connection:
    ASSEMBLER_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ASSEMBLER_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS assembled_filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_name TEXT NOT NULL,
            forum TEXT NOT NULL,
            lane TEXT DEFAULT '',
            sections_count INTEGER DEFAULT 0,
            citations_count INTEGER DEFAULT 0,
            evidence_count INTEGER DEFAULT 0,
            output_path TEXT DEFAULT '',
            assembly_time_s REAL DEFAULT 0.0,
            assembled_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS filing_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_id INTEGER NOT NULL,
            section_order INTEGER DEFAULT 0,
            section_type TEXT NOT NULL,
            title TEXT DEFAULT '',
            content TEXT DEFAULT '',
            citations_used TEXT DEFAULT '[]',
            evidence_used TEXT DEFAULT '[]'
        );
    """)
    conn.commit()
    return conn


@dataclass
class FilingSection:
    section_type: str
    title: str
    content: str = ""
    citations: list = field(default_factory=list)
    evidence: list = field(default_factory=list)


def _generate_caption(court_key: str, document_title: str) -> str:
    court = COURTS.get(court_key, COURTS["14th_circuit"])
    sep = "/" * 45
    return CAPTION_TEMPLATE.format(
        court=court["name"], case_no=court["case"],
        judge=court["judge"], separator=sep,
        attorney_block=ATTORNEY_BLOCK
    ) + f"\n{document_title.upper()}\n{'=' * len(document_title)}\n"


def _pull_authority(central: sqlite3.Connection, vehicle: str) -> list[dict]:
    """Pull relevant authority for a filing vehicle."""
    authorities = []
    try:
        rows = central.execute("""
            SELECT rule_id, rule_text FROM auth_rules
            WHERE rule_text LIKE ? LIMIT 50
        """, (f"%{vehicle[:30]}%",)).fetchall()
        for r in rows:
            authorities.append({"id": str(r[0]), "text": str(r[1])[:500]})
    except sqlite3.Error:
        pass

    try:
        rows = central.execute("""
            SELECT rowid, citation_text FROM master_citations
            WHERE citation_text LIKE ? LIMIT 50
        """, (f"%{vehicle[:20]}%",)).fetchall()
        for r in rows:
            authorities.append({"id": f"mc_{r[0]}", "text": str(r[1])[:500]})
    except sqlite3.Error:
        pass
    return authorities


def _pull_evidence(central: sqlite3.Connection, lane: str, vehicle: str) -> list[dict]:
    """Pull evidence quotes relevant to this filing."""
    evidence = []
    search_terms = vehicle.replace("_", " ")
    try:
        rows = central.execute("""
            SELECT rowid, quote_text, source_file FROM evidence_quotes_fts
            WHERE evidence_quotes_fts MATCH ? LIMIT 30
        """, (search_terms[:50],)).fetchall()
        for r in rows:
            evidence.append({"id": str(r[0]), "text": str(r[1])[:500],
                             "source": str(r[2] or "")})
    except sqlite3.Error:
        try:
            rows = central.execute("""
                SELECT rowid, quote_text, source_file FROM evidence_quotes
                WHERE quote_text LIKE ? LIMIT 30
            """, (f"%{vehicle[:20]}%",)).fetchall()
            for r in rows:
                evidence.append({"id": str(r[0]), "text": str(r[1])[:500],
                                 "source": str(r[2] or "")})
        except sqlite3.Error:
            pass
    return evidence


def _pull_claims(central: sqlite3.Connection, vehicle: str) -> list[dict]:
    """Pull claims relevant to filing."""
    claims = []
    try:
        rows = central.execute("""
            SELECT claim_id, proposition, status FROM claims
            WHERE proposition LIKE ? AND status = 'supported'
            LIMIT 20
        """, (f"%{vehicle[:20]}%",)).fetchall()
        for r in rows:
            claims.append({"id": str(r[0]), "proposition": str(r[1])[:500]})
    except sqlite3.Error:
        pass
    return claims


def _generate_index_of_authorities(authorities: list[dict]) -> str:
    """Generate Index of Authorities section."""
    if not authorities:
        return "INDEX OF AUTHORITIES\n\n[No authorities compiled]\n"

    sections = {"statutes": [], "court_rules": [], "case_law": [], "other": []}
    for auth in authorities:
        text = auth["text"]
        if re.search(r'MCL\s+\d+', text, re.I):
            sections["statutes"].append(text[:200])
        elif re.search(r'MCR\s+\d+', text, re.I):
            sections["court_rules"].append(text[:200])
        elif re.search(r'\bv\b.*\d+\s+Mich', text, re.I):
            sections["case_law"].append(text[:200])
        else:
            sections["other"].append(text[:200])

    out = "INDEX OF AUTHORITIES\n\n"
    if sections["statutes"]:
        out += "STATUTES\n"
        for s in sorted(set(sections["statutes"])):
            out += f"  {s}\n"
    if sections["court_rules"]:
        out += "\nCOURT RULES\n"
        for s in sorted(set(sections["court_rules"])):
            out += f"  {s}\n"
    if sections["case_law"]:
        out += "\nCASE LAW\n"
        for s in sorted(set(sections["case_law"])):
            out += f"  {s}\n"
    return out


def _generate_cos(document_name: str) -> str:
    """Generate Certificate of Service."""
    return CERTIFICATE_OF_SERVICE.format(
        date="[DATE]",
        document_name=document_name,
        service_method="[first class mail / MiFILE / personal service]",
        parties="Emily A. Watson\n[ADDRESS]\n\n"
                "Friend of the Court\nPamela Rusco\n990 Terrace St\nMuskegon, MI 49442"
    )


def assemble_filing(vehicle_name: str, forum: str, lane: str = "A") -> dict:
    """Assemble a complete filing package."""
    start = time.time()
    adb = _init_db()
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    court_key = {"MSC": "MSC", "COA": "COA", "USDC": "USDC", "JTC": "JTC"}.get(forum, "14th_circuit")

    # Pull intelligence
    authorities = _pull_authority(central, vehicle_name)
    evidence = _pull_evidence(central, lane, vehicle_name)
    claims = _pull_claims(central, vehicle_name)

    # Build sections
    sections = []

    # 1. Caption
    sections.append(FilingSection(
        section_type="caption", title="Caption",
        content=_generate_caption(court_key, vehicle_name)
    ))

    # 2. Statement of Facts
    facts_content = "STATEMENT OF FACTS\n\n"
    for i, ev in enumerate(evidence[:15], 1):
        facts_content += f"{i}. {ev['text']}\n\n"
    if not evidence:
        facts_content += "[Evidence quotes to be inserted]\n"
    sections.append(FilingSection(
        section_type="facts", title="Statement of Facts",
        content=facts_content, evidence=[e["id"] for e in evidence[:15]]
    ))

    # 3. Argument
    arg_content = "ARGUMENT\n\n"
    for i, claim in enumerate(claims[:10], 1):
        arg_content += f"  {chr(64+i)}. {claim['proposition']}\n\n"
    if not claims:
        arg_content += "[Arguments to be inserted from claims database]\n"
    sections.append(FilingSection(
        section_type="argument", title="Argument",
        content=arg_content, citations=[a["id"] for a in authorities[:20]]
    ))

    # 4. Index of Authorities
    sections.append(FilingSection(
        section_type="ioa", title="Index of Authorities",
        content=_generate_index_of_authorities(authorities)
    ))

    # 5. Certificate of Service
    sections.append(FilingSection(
        section_type="cos", title="Certificate of Service",
        content=_generate_cos(vehicle_name)
    ))

    # 6. Exhibit Index
    exhibit_content = "EXHIBIT INDEX\n\n"
    for i, ev in enumerate(evidence[:20], 1):
        exhibit_content += f"Exhibit {i}: {ev['source'][:100]} — {ev['text'][:80]}\n"
    sections.append(FilingSection(
        section_type="exhibits", title="Exhibit Index",
        content=exhibit_content
    ))

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[^\w\-]', '_', vehicle_name)[:50]
    output_file = OUTPUT_DIR / f"{safe_name}_{ts}.txt"

    full_text = "\n\n".join(s.content for s in sections)
    output_file.write_text(full_text, encoding="utf-8")

    duration = round(time.time() - start, 2)

    # Persist
    filing_id = adb.execute("""
        INSERT INTO assembled_filings
        (filing_name, forum, lane, sections_count, citations_count,
         evidence_count, output_path, assembly_time_s)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (vehicle_name, forum, lane, len(sections),
          len(authorities), len(evidence), str(output_file), duration)).lastrowid

    for i, s in enumerate(sections):
        adb.execute("""
            INSERT INTO filing_sections
            (filing_id, section_order, section_type, title, content,
             citations_used, evidence_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (filing_id, i, s.section_type, s.title,
              s.content[:5000], json.dumps(s.citations), json.dumps(s.evidence)))

    adb.commit()
    central.close()
    adb.close()

    return {
        "filing": vehicle_name,
        "forum": forum,
        "sections": len(sections),
        "authorities": len(authorities),
        "evidence_quotes": len(evidence),
        "claims": len(claims),
        "output": str(output_file),
        "duration_s": duration,
    }


def assemble_all() -> dict:
    """Assemble all filings from filing_readiness table."""
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    results = []
    try:
        rows = central.execute("""
            SELECT action_name, forum FROM filing_readiness
            WHERE readiness_pct >= 50
            ORDER BY readiness_pct DESC
        """).fetchall()
    except sqlite3.Error:
        try:
            rows = central.execute("""
                SELECT filing_name, forum FROM omega_legal_actions
                ORDER BY omega_score DESC
            """).fetchall()
        except sqlite3.Error:
            rows = []

    central.close()

    for name, forum in rows:
        try:
            result = assemble_filing(str(name), str(forum or "14th_circuit"))
            results.append(result)
        except Exception as e:
            results.append({"filing": str(name), "error": str(e)})

    return {
        "assembled": len([r for r in results if "error" not in r]),
        "errors": len([r for r in results if "error" in r]),
        "results": results[:15],
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        print(json.dumps(assemble_all(), indent=2, default=str))
    elif len(sys.argv) > 2:
        print(json.dumps(assemble_filing(sys.argv[1], sys.argv[2]), indent=2, default=str))
    else:
        print("Usage: python nuclear_assembler.py <vehicle_name> <forum>|all")
