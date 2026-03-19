"""
DELTA99 Ω∞ — Response Warfare Engine
======================================
Auto-drafts response filings when adversary files anything.
Pre-builds response templates for all known Watson/Berry patterns.
Generates: responses to motions, replies to briefs, objections to proposed orders.

Depends on: d99-nuclear-assembler, d99-counter-intel
"""
import sys
import sqlite3
import json
import re
import time
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB, LITIGOS_ROOT

WARFARE_DB = Path(__file__).parent / "response_warfare.db"
OUTPUT_DIR = LITIGOS_ROOT / "06_FILINGS" / "RESPONSE_WARFARE"

# ── Response Templates ─────────────────────────────────────────────
RESPONSE_TYPES = {
    "motion_to_dismiss": {
        "title": "RESPONSE IN OPPOSITION TO MOTION TO DISMISS",
        "sections": ["jurisdiction", "factual_background", "argument", "conclusion"],
        "deadline_days": 14,
    },
    "emergency_motion": {
        "title": "RESPONSE TO EMERGENCY MOTION",
        "sections": ["no_true_emergency", "factual_rebuttal", "procedural_defects", "requested_relief"],
        "deadline_days": 7,
    },
    "motion_for_contempt": {
        "title": "RESPONSE TO MOTION FOR CONTEMPT",
        "sections": ["compliance_evidence", "factual_rebuttal", "impossibility_defense", "counter_motion"],
        "deadline_days": 14,
    },
    "ppo_motion": {
        "title": "RESPONSE TO MOTION REGARDING PERSONAL PROTECTION ORDER",
        "sections": ["factual_rebuttal", "mcl_600_2950_analysis", "false_allegations", "counter_evidence"],
        "deadline_days": 14,
    },
    "custody_modification": {
        "title": "RESPONSE TO MOTION FOR CUSTODY MODIFICATION",
        "sections": ["best_interest_factors", "factual_rebuttal", "proper_cause", "evidence"],
        "deadline_days": 21,
    },
    "ex_parte_order": {
        "title": "MOTION TO SET ASIDE EX PARTE ORDER",
        "sections": ["procedural_void", "due_process", "factual_deficiency", "requested_relief"],
        "deadline_days": 21,
    },
    "foc_recommendation": {
        "title": "OBJECTION TO FOC RECOMMENDATION",
        "sections": ["factual_errors", "legal_standard", "proper_recommendation", "requested_relief"],
        "deadline_days": 21,
    },
}

# ── Standard Legal Arguments (pre-built) ──────────────────────────
STANDARD_ARGUMENTS = {
    "no_true_emergency": """The opposing party's motion fails to demonstrate a true emergency
requiring ex parte relief. Under MCR 3.207(B), emergency motions require a showing that
(1) immediate and irreparable injury, loss, or damage will result, (2) the delay required
for notice is impracticable, and (3) the movant has made a good faith effort to give notice.
None of these requirements are met here.""",

    "procedural_void": """The order was entered without notice or opportunity to be heard in
violation of MCR 2.119(A) and the Due Process Clause of the Fourteenth Amendment.
An order entered without jurisdiction over a party or proper notice is void ab initio
and may be set aside at any time. Bowie v Arder, 441 Mich 23 (1992).""",

    "due_process": """Plaintiff's fundamental right to due process includes notice and an
opportunity to be heard before deprivation of liberty or property interests. Mathews v
Eldridge, 424 US 319 (1976). The parental liberty interest is a fundamental constitutional
right. Troxel v Granville, 530 US 57 (2000).""",

    "best_interest_standard": """Under MCL 722.23, the court must consider all statutory
best-interest factors when making custody determinations. The record demonstrates that
9 of 12 factors favor Father, including Factor (j) (willingness to facilitate relationship
with other parent), which is among the most important. Ireland v Smith, 451 Mich 457 (1996).""",

    "false_allegations_pattern": """The opposing party has a documented pattern of filing
unsubstantiated allegations timed to court proceedings. This pattern constitutes abuse
of process and should be considered under MCL 722.23(j) as evidence of unwillingness
to facilitate the parent-child relationship.""",
}


def _init_db() -> sqlite3.Connection:
    WARFARE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(WARFARE_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS response_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_filing TEXT DEFAULT '',
            response_type TEXT NOT NULL,
            title TEXT DEFAULT '',
            content TEXT DEFAULT '',
            output_path TEXT DEFAULT '',
            status TEXT DEFAULT 'draft',
            deadline TEXT DEFAULT '',
            generated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS response_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            argument_key TEXT NOT NULL UNIQUE,
            argument_text TEXT NOT NULL,
            applicable_to TEXT DEFAULT '[]',
            usage_count INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    return conn


def _pull_supporting_evidence(central: sqlite3.Connection,
                              keywords: list[str]) -> list[str]:
    """Pull evidence quotes supporting the response."""
    evidence = []
    for kw in keywords[:3]:
        try:
            rows = central.execute("""
                SELECT quote_text FROM evidence_quotes_fts
                WHERE evidence_quotes_fts MATCH ? LIMIT 5
            """, (kw,)).fetchall()
            for r in rows:
                evidence.append(str(r[0])[:300])
        except sqlite3.Error:
            pass
    return evidence


def generate_response(response_type: str, trigger_filing: str = "",
                      adversary_args: list[str] = None) -> dict:
    """Generate a complete response filing."""
    start = time.time()
    wdb = _init_db()

    rtype = RESPONSE_TYPES.get(response_type)
    if not rtype:
        return {"error": f"Unknown response type: {response_type}"}

    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    # Build filing
    title = rtype["title"]
    deadline = (datetime.now() + timedelta(days=rtype["deadline_days"])).strftime("%Y-%m-%d")

    content_parts = []
    content_parts.append(f"STATE OF MICHIGAN")
    content_parts.append(f"IN THE 14TH CIRCUIT COURT")
    content_parts.append(f"COUNTY OF MUSKEGON\n")
    content_parts.append(f"Case No. 2024-001507-DC")
    content_parts.append(f"Hon. Jenny L. McNeill\n")
    content_parts.append(f"{'=' * 50}")
    content_parts.append(f"{title}")
    content_parts.append(f"{'=' * 50}\n")

    if trigger_filing:
        content_parts.append(f"NOW COMES Plaintiff, Andrew J. Pigors, pro se, and in response")
        content_parts.append(f"to Defendant's {trigger_filing}, states as follows:\n")

    # Generate sections using pre-built arguments
    for section in rtype["sections"]:
        content_parts.append(f"\n{'─' * 40}")
        content_parts.append(f"  {section.upper().replace('_', ' ')}")
        content_parts.append(f"{'─' * 40}\n")

        if section in STANDARD_ARGUMENTS:
            content_parts.append(STANDARD_ARGUMENTS[section])
        else:
            content_parts.append(f"[{section.upper()} — To be completed with case-specific facts]\n")

    # Add supporting evidence
    evidence = _pull_supporting_evidence(central, [response_type, "watson", "custody"])
    if evidence:
        content_parts.append(f"\n{'─' * 40}")
        content_parts.append(f"  SUPPORTING EVIDENCE")
        content_parts.append(f"{'─' * 40}\n")
        for i, ev in enumerate(evidence[:5], 1):
            content_parts.append(f"  {i}. {ev}\n")

    # Certificate of Service
    content_parts.append(f"\n{'─' * 40}")
    content_parts.append(f"  CERTIFICATE OF SERVICE")
    content_parts.append(f"{'─' * 40}\n")
    content_parts.append(f"I certify that on [DATE], I served this {title}")
    content_parts.append(f"upon all parties by [METHOD].\n")
    content_parts.append(f"                    ________________________________")
    content_parts.append(f"                    Andrew J. Pigors, Pro Se")

    full_content = "\n".join(content_parts)

    # Write to file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_type = response_type.replace("_", "-")
    output_file = OUTPUT_DIR / f"response_{safe_type}_{ts}.txt"
    output_file.write_text(full_content, encoding="utf-8")

    # Persist
    wdb.execute("""
        INSERT INTO response_drafts
        (trigger_filing, response_type, title, content, output_path, deadline)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (trigger_filing, response_type, title,
          full_content[:10000], str(output_file), deadline))
    wdb.commit()

    central.close()
    wdb.close()

    return {
        "type": response_type,
        "title": title,
        "trigger": trigger_filing,
        "deadline": deadline,
        "sections": len(rtype["sections"]),
        "evidence_cited": len(evidence),
        "output": str(output_file),
        "content_length": len(full_content),
        "duration_s": round(time.time() - start, 2),
    }


def generate_all_templates() -> dict:
    """Pre-generate response templates for all known types."""
    results = []
    for rtype in RESPONSE_TYPES:
        result = generate_response(rtype, trigger_filing=f"[Anticipated {rtype}]")
        results.append(result)
    return {
        "templates_generated": len(results),
        "types": [r["type"] for r in results],
        "results": results,
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        print(json.dumps(generate_all_templates(), indent=2, default=str))
    elif len(sys.argv) > 1:
        print(json.dumps(generate_response(sys.argv[1]), indent=2, default=str))
    else:
        print(f"Usage: python response_warfare.py <type>|all")
        print(f"Types: {', '.join(RESPONSE_TYPES.keys())}")
