#!/usr/bin/env python3
"""
MBP LitigationOS -- Motion Generator Skill
============================================
Generate complete, court-ready motions with IRAC structure, evidence,
authority citations, and MCR 2.113-compliant formatting.
Case: Pigors v. Watson, 14th Circuit Muskegon, Judge McNeill.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent if 'skills' in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


# ── Case caption ──────────────────────────────────────────────────────

CASE_CAPTION = """
================================================================================
STATE OF MICHIGAN
IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW PIGORS,                         Case No. 2024-001507-DC
    Plaintiff,                         Hon. Jenny L. McNeill

v.

TIFFANY WATSON (fka PIGORS),
    Defendant.
________________________________________________________________________________
""".strip()

SIGNATURE_BLOCK = """
Respectfully submitted,

______________________________
Andrew Pigors, Pro Se Plaintiff
Muskegon, Michigan
Date: {date}
""".strip()

CERTIFICATE_OF_SERVICE = """
CERTIFICATE OF SERVICE

I, Andrew Pigors, certify that on {date}, I served a copy of the
foregoing document on the following party(ies) by:
  [ ] First-class U.S. mail, postage prepaid
  [ ] Personal delivery
  [ ] Electronic service (email / MiFILE)

    Tiffany Watson (fka Pigors)
    c/o address on file with the Court

______________________________
Andrew Pigors
""".strip()


def _today_str() -> str:
    """Return today's date formatted for filings."""
    return datetime.now().strftime("%B %d, %Y")


class MotionGenerator:
    """Generate court-ready motions for Pigors v. Watson."""

    # ── Case number lookup ────────────────────────────────────────────
    CASE_NUMBERS = {
        "custody": "2024-001507-DC",
        "ppo": "2023-5907-PP",
        "coa": "366810",
        "default": "2024-001507-DC",
    }

    MOTION_TYPES = {
        "emergency_restore_pt": {
            "title": "EMERGENCY MOTION TO RESTORE PARENTING TIME",
            "authority": "MCL 722.27a; MCR 2.119(B)",
            "evidence_keywords": [
                "parenting time", "visitation", "custody", "contact",
                "separation", "child", "overnight", "denied",
            ],
            "authority_keywords": ["722.27a", "2.119", "parenting time", "emergency"],
        },
        "disqualify": {
            "title": "MOTION FOR DISQUALIFICATION",
            "authority": "MCR 2.003(C)(1)",
            "evidence_keywords": [
                "bias", "prejudice", "impartial", "ex parte",
                "disqualif", "recus", "misconduct",
            ],
            "authority_keywords": ["2.003", "disqualif", "bias", "recus"],
        },
        "contempt": {
            "title": "MOTION FOR CONTEMPT",
            "authority": "MCR 3.606; MCL 600.1701",
            "evidence_keywords": [
                "contempt", "violat", "disobey", "failed to comply",
                "refused", "willful", "court order",
            ],
            "authority_keywords": ["3.606", "600.1701", "contempt"],
        },
        "compel_discovery": {
            "title": "MOTION TO COMPEL DISCOVERY",
            "authority": "MCR 2.313(A)",
            "evidence_keywords": [
                "discovery", "interrogat", "document request", "deposition",
                "refused to answer", "failed to produce", "subpoena",
            ],
            "authority_keywords": ["2.313", "discovery", "compel"],
        },
        "vacate_order": {
            "title": "MOTION TO SET ASIDE ORDER",
            "authority": "MCR 2.612",
            "evidence_keywords": [
                "void", "ex parte", "no notice", "no hearing",
                "defective", "vacate", "set aside",
            ],
            "authority_keywords": ["2.612", "set aside", "vacate", "void"],
        },
        "reconsideration": {
            "title": "MOTION FOR RECONSIDERATION",
            "authority": "MCR 2.119(F)",
            "evidence_keywords": [
                "error", "overlooked", "palpable", "new evidence",
                "misapprehend", "reconsider",
            ],
            "authority_keywords": ["2.119", "reconsideration", "palpable"],
        },
        "summary_disposition": {
            "title": "MOTION FOR SUMMARY DISPOSITION",
            "authority": "MCR 2.116(C)(10)",
            "evidence_keywords": [
                "no genuine issue", "material fact", "undisputed",
                "entitled to judgment", "summary",
            ],
            "authority_keywords": ["2.116", "summary disposition"],
        },
        "dissolve_ppo": {
            "title": "MOTION TO DISSOLVE PPO",
            "authority": "MCL 600.2950(12)",
            "evidence_keywords": [
                "ppo", "personal protection", "restraining", "no-contact",
                "dissolve", "modify", "terminate",
            ],
            "authority_keywords": ["600.2950", "ppo", "personal protection"],
        },
    }

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _conn(self) -> Optional[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    # ── Gather evidence ───────────────────────────────────────────────

    def gather_evidence_for_motion(
        self, motion_type: str, limit: int = 20
    ) -> List[Dict]:
        """Search evidence_quotes for evidence supporting this motion type."""
        mtype = self.MOTION_TYPES.get(motion_type)
        if not mtype:
            return []

        conn = self._conn()
        if not conn:
            return []

        results: List[Dict] = []
        keywords = mtype.get("evidence_keywords", [])

        # FTS search first
        try:
            fts_query = " OR ".join(keywords[:5])
            rows = conn.execute(
                "SELECT quote_text, speaker, legal_significance, evidence_category "
                "FROM evidence_quotes "
                "WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts "
                "WHERE evidence_quotes_fts MATCH ?) LIMIT ?",
                (fts_query, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "quote": r["quote_text"],
                    "speaker": r["speaker"],
                    "significance": r["legal_significance"],
                    "category": r["evidence_category"],
                    "source": "evidence_quotes_fts",
                })
        except Exception:
            pass

        # LIKE fallback for remaining slots
        if len(results) < limit:
            remaining = limit - len(results)
            for kw in keywords:
                if len(results) >= limit:
                    break
                try:
                    rows = conn.execute(
                        "SELECT quote_text, speaker, legal_significance, "
                        "evidence_category "
                        "FROM evidence_quotes "
                        "WHERE quote_text LIKE ? LIMIT ?",
                        (f"%{kw}%", remaining),
                    ).fetchall()
                    seen = {r["quote"][:80] for r in results}
                    for r in rows:
                        if r["quote_text"][:80] not in seen:
                            results.append({
                                "quote": r["quote_text"],
                                "speaker": r["speaker"],
                                "significance": r["legal_significance"],
                                "category": r["evidence_category"],
                                "source": "evidence_quotes_like",
                            })
                            seen.add(r["quote_text"][:80])
                except Exception:
                    pass

        conn.close()
        return results[:limit]

    # ── Gather authority ──────────────────────────────────────────────

    def gather_authority_for_motion(
        self, motion_type: str, limit: int = 10
    ) -> List[Dict]:
        """Search auth_rules for governing authority for this motion type."""
        mtype = self.MOTION_TYPES.get(motion_type)
        if not mtype:
            return []

        conn = self._conn()
        if not conn:
            return []

        results: List[Dict] = []
        keywords = mtype.get("authority_keywords", [])

        # auth_rules search
        for kw in keywords:
            if len(results) >= limit:
                break
            try:
                rows = conn.execute(
                    "SELECT rule_number, title, substr(full_text, 1, 800) as text "
                    "FROM auth_rules "
                    "WHERE rule_number LIKE ? OR title LIKE ? OR full_text LIKE ? "
                    "LIMIT ?",
                    (f"%{kw}%", f"%{kw}%", f"%{kw}%", limit),
                ).fetchall()
                seen = {r["authority"][:40] for r in results if "authority" in r}
                for r in rows:
                    if r["rule_number"][:40] not in seen:
                        results.append({
                            "authority": r["rule_number"],
                            "title": r["title"],
                            "text": r["text"],
                            "source": "auth_rules",
                        })
                        seen.add(r["rule_number"][:40])
            except Exception:
                pass

        # rules_text (statutes) search
        for kw in keywords:
            if len(results) >= limit:
                break
            try:
                rows = conn.execute(
                    "SELECT rule, chapter, substr(context, 1, 600) as text "
                    "FROM rules_text "
                    "WHERE rule LIKE ? OR context LIKE ? LIMIT ?",
                    (f"%{kw}%", f"%{kw}%", min(limit, 5)),
                ).fetchall()
                for r in rows:
                    results.append({
                        "authority": r["rule"],
                        "title": r["chapter"],
                        "text": r["text"],
                        "source": "rules_text",
                    })
            except Exception:
                pass

        conn.close()
        return results[:limit]

    # ── Generate complete motion ──────────────────────────────────────

    def generate_motion(
        self, motion_type: str, custom_facts: str = None
    ) -> Dict:
        """
        Generate a complete motion with caption, IRAC arguments, evidence,
        authority, relief, signature, and certificate of service.
        Returns: {text, authority_count, evidence_count, word_count}.
        """
        mtype = self.MOTION_TYPES.get(motion_type)
        if not mtype:
            available = ", ".join(self.MOTION_TYPES.keys())
            return {
                "text": f"ERROR: Unknown motion type '{motion_type}'. "
                        f"Available: {available}",
                "authority_count": 0,
                "evidence_count": 0,
                "word_count": 0,
            }

        evidence = self.gather_evidence_for_motion(motion_type)
        authority = self.gather_authority_for_motion(motion_type)

        # Build numbered factual paragraphs
        fact_paragraphs = []
        para_num = 1

        fact_paragraphs.append(
            f"  {para_num}. Plaintiff Andrew Pigors is the father of the minor "
            f"child and brings this motion pro se."
        )
        para_num += 1

        fact_paragraphs.append(
            f"  {para_num}. As of the date of this filing, Plaintiff has been "
            f"separated from his child for more than 329 days."
        )
        para_num += 1

        if custom_facts:
            for line in custom_facts.strip().split("\n"):
                line = line.strip()
                if line:
                    fact_paragraphs.append(f"  {para_num}. {line}")
                    para_num += 1

        for ev in evidence[:10]:
            speaker = ev.get("speaker") or "Record"
            quote = (ev.get("quote") or "")[:300]
            if quote:
                fact_paragraphs.append(
                    f"  {para_num}. {speaker} stated: \"{quote}\""
                )
                para_num += 1

        facts_block = "\n\n".join(fact_paragraphs)

        # Build IRAC argument
        auth_citations = []
        for a in authority:
            auth_citations.append(
                f"  - {a['authority']}: {a['title'] or ''}\n"
                f"    {(a['text'] or '')[:300]}"
            )
        auth_block = "\n".join(auth_citations) if auth_citations else (
            "  [Authority search returned no results — manual citation required]"
        )

        evid_citations = []
        for ev in evidence[:8]:
            sig = ev.get("significance") or "relevant to motion"
            evid_citations.append(
                f"  - [{ev.get('speaker') or 'Record'}]: "
                f"{(ev.get('quote') or '')[:200]} "
                f"(Significance: {sig})"
            )
        evid_block = "\n".join(evid_citations) if evid_citations else (
            "  [No matching evidence — supplement from record]"
        )

        # Relief section — motion-type specific
        relief = self._build_relief(motion_type)

        motion_text = f"""
{CASE_CAPTION}

{mtype['title']}
________________________________________________________________________________

NOW COMES Plaintiff Andrew Pigors, appearing pro se, and respectfully moves
this Honorable Court for the relief described herein, pursuant to
{mtype['authority']}, and in support states as follows:

STATEMENT OF FACTS

{facts_block}

ARGUMENT

I. ISSUE

  Whether Plaintiff is entitled to relief under {mtype['authority']} based on
  the facts and circumstances set forth above, including the ongoing 329+ day
  separation of parent and child.

II. RULE

  The governing authority for this motion is {mtype['authority']}.

  Applicable Authority:
{auth_block}

III. APPLICATION

  The facts of this case establish that relief is warranted. The evidence
  from the record demonstrates:

{evid_block}

  The 329+ day parent-child separation is directly relevant to this motion
  and constitutes an ongoing deprivation of fundamental parental rights
  protected by the Fourteenth Amendment. See Troxel v Granville, 530 US
  57 (2000); MCL 722.27a(7).

IV. CONCLUSION

  For the foregoing reasons, Plaintiff is entitled to the relief requested.

RELIEF REQUESTED

{relief}

{SIGNATURE_BLOCK.format(date=_today_str())}

{CERTIFICATE_OF_SERVICE.format(date=_today_str())}
""".strip()

        word_count = len(motion_text.split())

        # ── Post-generation validation ────────────────────────────────
        validation = self.verify_citations(motion_text)
        irac_check = self._check_irac(motion_text)

        return {
            "text": motion_text,
            "authority_count": len(authority),
            "evidence_count": len(evidence),
            "word_count": word_count,
            "motion_type": motion_type,
            "title": mtype["title"],
            "citation_validation": validation,
            "irac_check": irac_check,
        }

    # ── Citation Verification ────────────────────────────────────────

    def verify_citations(self, text: str) -> Dict:
        """Extract all MCR/MCL/MRE citations from text and verify each
        against auth_rules and rules_text tables in the DB.
        Returns: {verified: [...], unverified: [...], total: int}."""
        import re
        cite_re = re.compile(r'(MCR|MCL|MRE)\s+(\d+(?:\.\d+)+(?:\([A-Za-z0-9]+\))*)')
        citations = cite_re.findall(text)
        verified, unverified = [], []

        conn = self._conn()
        if not conn:
            return {"verified": [], "unverified": [f"{t} {n}" for t, n in citations],
                    "total": len(citations)}

        for cite_type, cite_num in citations:
            base_num = cite_num.split("(")[0]
            full_cite = f"{cite_type} {cite_num}"
            found = False
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM auth_rules "
                    "WHERE rule_number LIKE ?", (f"%{base_num}%",)
                ).fetchone()
                if row and row["cnt"] > 0:
                    found = True
            except Exception:
                pass
            if not found:
                try:
                    row2 = conn.execute(
                        "SELECT COUNT(*) as cnt FROM rules_text "
                        "WHERE rule LIKE ?", (f"%{base_num}%",)
                    ).fetchone()
                    if row2 and row2["cnt"] > 0:
                        found = True
                except Exception:
                    pass
            (verified if found else unverified).append(full_cite)

        conn.close()
        return {"verified": verified, "unverified": list(set(unverified)),
                "total": len(citations)}

    # ── IRAC Enforcement Check ────────────────────────────────────────

    @staticmethod
    def _check_irac(text: str) -> Dict:
        """Check that the document contains all four IRAC sections.
        Returns: {complete: bool, present: [...], missing: [...]}."""
        sections = {
            "ISSUE": bool(re.search(r'\bI\.\s*ISSUE\b', text)),
            "RULE": bool(re.search(r'\bII\.\s*RULE\b', text)),
            "APPLICATION": bool(re.search(r'\bIII\.\s*APPLICATION\b', text)),
            "CONCLUSION": bool(re.search(r'\bIV\.\s*CONCLUSION\b', text)),
        }
        present = [k for k, v in sections.items() if v]
        missing = [k for k, v in sections.items() if not v]
        return {"complete": len(missing) == 0, "present": present, "missing": missing}

    # ── Build relief section ──────────────────────────────────────────

    @staticmethod
    def _build_relief(motion_type: str) -> str:
        """Build motion-type-specific relief requested section."""
        relief_map = {
            "emergency_restore_pt": (
                "  WHEREFORE, Plaintiff respectfully requests that this Court:\n"
                "    1. Enter an emergency order restoring Plaintiff's parenting\n"
                "       time immediately per MCL 722.27a;\n"
                "    2. Order make-up parenting time for the 329+ days lost;\n"
                "    3. Order Defendant to comply with all parenting time provisions;\n"
                "    4. Award Plaintiff costs and attorney fees per MCL 722.27a(6);\n"
                "    5. Grant such other relief as this Court deems just."
            ),
            "disqualify": (
                "  WHEREFORE, Plaintiff respectfully requests that this Court:\n"
                "    1. Disqualify the Honorable Jenny L. McNeill per MCR 2.003(C)(1);\n"
                "    2. Assign this case to a new judge;\n"
                "    3. Vacate all orders entered by the disqualified judge;\n"
                "    4. Grant such other relief as this Court deems just."
            ),
            "contempt": (
                "  WHEREFORE, Plaintiff respectfully requests that this Court:\n"
                "    1. Find Defendant in contempt of court per MCR 3.606;\n"
                "    2. Order Defendant to purge the contempt by complying;\n"
                "    3. Award Plaintiff make-up parenting time;\n"
                "    4. Award costs and attorney fees per MCR 3.606(A);\n"
                "    5. Grant such other relief as this Court deems just."
            ),
            "compel_discovery": (
                "  WHEREFORE, Plaintiff respectfully requests that this Court:\n"
                "    1. Compel Defendant to fully respond to discovery per MCR 2.313;\n"
                "    2. Order responses within 14 days;\n"
                "    3. Award costs of this motion per MCR 2.313(A)(5);\n"
                "    4. Grant such other relief as this Court deems just."
            ),
            "vacate_order": (
                "  WHEREFORE, Plaintiff respectfully requests that this Court:\n"
                "    1. Set aside the challenged order per MCR 2.612;\n"
                "    2. Restore the status quo ante;\n"
                "    3. Conduct a de novo hearing on the merits;\n"
                "    4. Grant such other relief as this Court deems just."
            ),
            "reconsideration": (
                "  WHEREFORE, Plaintiff respectfully requests that this Court:\n"
                "    1. Reconsider and correct the order per MCR 2.119(F);\n"
                "    2. Modify the order consistent with the law and facts;\n"
                "    3. Grant such other relief as this Court deems just."
            ),
            "summary_disposition": (
                "  WHEREFORE, Plaintiff respectfully requests that this Court:\n"
                "    1. Grant summary disposition in Plaintiff's favor per\n"
                "       MCR 2.116(C)(10);\n"
                "    2. Enter judgment consistent with the relief sought;\n"
                "    3. Grant such other relief as this Court deems just."
            ),
            "dissolve_ppo": (
                "  WHEREFORE, Plaintiff respectfully requests that this Court:\n"
                "    1. Dissolve the Personal Protection Order per MCL 600.2950(12);\n"
                "    2. Restore Plaintiff's rights;\n"
                "    3. Grant such other relief as this Court deems just."
            ),
        }
        return relief_map.get(motion_type, (
            "  WHEREFORE, Plaintiff respectfully requests that this Court grant\n"
            "  such relief as is just and equitable."
        ))

    # ── Brief in support ──────────────────────────────────────────────

    def generate_brief_in_support(self, motion_type: str) -> str:
        """Generate a brief in support of the motion with full IRAC analysis."""
        mtype = self.MOTION_TYPES.get(motion_type)
        if not mtype:
            return f"ERROR: Unknown motion type '{motion_type}'."

        evidence = self.gather_evidence_for_motion(motion_type, limit=15)
        authority = self.gather_authority_for_motion(motion_type, limit=10)

        auth_block = ""
        for i, a in enumerate(authority, 1):
            auth_block += (
                f"\n  {i}. {a['authority']} — {a.get('title', '')}\n"
                f"     {(a.get('text') or '')[:400]}\n"
            )
        if not auth_block:
            auth_block = "\n  [No matching authority — manual citation required]\n"

        evid_block = ""
        for i, ev in enumerate(evidence, 1):
            evid_block += (
                f"\n  {i}. [{ev.get('speaker') or 'Record'}]: "
                f"{(ev.get('quote') or '')[:250]}\n"
                f"     Legal significance: {ev.get('significance', 'N/A')}\n"
            )
        if not evid_block:
            evid_block = "\n  [No matching evidence — supplement from record]\n"

        brief = f"""
{CASE_CAPTION}

BRIEF IN SUPPORT OF {mtype['title']}
________________________________________________________________________________

TABLE OF AUTHORITIES
{auth_block}

STATEMENT OF QUESTIONS PRESENTED

  1. Whether Plaintiff is entitled to relief under {mtype['authority']}.

  2. Whether the ongoing 329+ day parent-child separation constitutes a
     deprivation of fundamental constitutional rights requiring immediate
     judicial intervention.

STATEMENT OF FACTS

  Plaintiff Andrew Pigors is the father of the minor child in this custody
  matter. Plaintiff has been denied meaningful contact with his child for
  more than 329 consecutive days. Plaintiff brings this action pro se.

  The evidence from the record establishes:
{evid_block}

ARGUMENT

I. ISSUE

  Whether the trial court should grant {mtype['title'].lower()} under
  {mtype['authority']} where the record demonstrates that Plaintiff has
  been deprived of his parenting time for 329+ days without the required
  statutory findings.

II. RULE

  {mtype['authority']} governs this motion.

  The applicable legal standards are:
{auth_block}

  Additionally, MCL 722.23(a)-(l) requires the court to evaluate all
  best interest factors before modifying custody or parenting time.
  MCL 722.27a(7) prohibits restricting parenting time without a finding
  that the child's physical, mental, or emotional health would be
  endangered.

III. APPLICATION

  Applying the governing standards to the facts of this case, Plaintiff
  has demonstrated entitlement to the relief sought. The evidence
  establishes that:

  A. The 329+ day separation is unsupported by any finding of
     endangerment per MCL 722.27a(3).

  B. Plaintiff's fundamental parental rights under the Fourteenth
     Amendment have been infringed without due process.

  C. The record contains substantial evidence supporting Plaintiff's
     position as set forth in the evidence cited above.

IV. CONCLUSION

  For the foregoing reasons, Plaintiff respectfully requests that this
  Honorable Court grant the relief requested in the accompanying motion.

{SIGNATURE_BLOCK.format(date=_today_str())}

{CERTIFICATE_OF_SERVICE.format(date=_today_str())}
""".strip()

        return brief

    # ── List available motions ────────────────────────────────────────

    def list_available_motions(self) -> List[Dict]:
        """List all available motion types with readiness scores."""
        results: List[Dict] = []
        for key, mtype in self.MOTION_TYPES.items():
            evidence = self.gather_evidence_for_motion(key, limit=5)
            authority = self.gather_authority_for_motion(key, limit=5)

            evidence_score = min(len(evidence) / 5.0, 1.0)
            authority_score = min(len(authority) / 3.0, 1.0)
            overall = (evidence_score * 0.5) + (authority_score * 0.5)

            results.append({
                "motion_type": key,
                "title": mtype["title"],
                "authority": mtype["authority"],
                "evidence_count": len(evidence),
                "authority_count": len(authority),
                "evidence_score": round(evidence_score, 2),
                "authority_score": round(authority_score, 2),
                "readiness_score": round(overall, 2),
                "ready": overall >= 0.5,
            })

        results.sort(key=lambda x: x["readiness_score"], reverse=True)
        return results


# ── Self-test ─────────────────────────────────────────────────────────

def self_test() -> Dict:
    """Run diagnostics on MotionGenerator skill."""
    results = {
        "skill": "motion_generator",
        "status": "ok",
        "tests": {},
    }
    gen = MotionGenerator()

    # Test DB connection
    conn = _get_db()
    results["tests"]["db_connection"] = "pass" if conn else "FAIL"
    if conn:
        conn.close()

    # Test gather_evidence
    try:
        evidence = gen.gather_evidence_for_motion("emergency_restore_pt", limit=5)
        results["tests"]["gather_evidence"] = f"pass ({len(evidence)} items)"
    except Exception as e:
        results["tests"]["gather_evidence"] = f"FAIL: {e}"

    # Test gather_authority
    try:
        authority = gen.gather_authority_for_motion("emergency_restore_pt", limit=5)
        results["tests"]["gather_authority"] = f"pass ({len(authority)} items)"
    except Exception as e:
        results["tests"]["gather_authority"] = f"FAIL: {e}"

    # Test generate_motion
    try:
        motion = gen.generate_motion("emergency_restore_pt")
        results["tests"]["generate_motion"] = (
            f"pass ({motion['word_count']} words, "
            f"{motion['authority_count']} auth, "
            f"{motion['evidence_count']} evid)"
        )
    except Exception as e:
        results["tests"]["generate_motion"] = f"FAIL: {e}"

    # Test generate_brief
    try:
        brief = gen.generate_brief_in_support("disqualify")
        results["tests"]["generate_brief"] = f"pass ({len(brief)} chars)"
    except Exception as e:
        results["tests"]["generate_brief"] = f"FAIL: {e}"

    # Test list_available_motions
    try:
        available = gen.list_available_motions()
        ready = sum(1 for m in available if m["ready"])
        results["tests"]["list_available"] = (
            f"pass ({len(available)} types, {ready} ready)"
        )
    except Exception as e:
        results["tests"]["list_available"] = f"FAIL: {e}"

    # Test invalid motion type
    try:
        bad = gen.generate_motion("nonexistent_type")
        results["tests"]["invalid_type_guard"] = (
            "pass" if "ERROR" in bad["text"] else "FAIL: no error returned"
        )
    except Exception as e:
        results["tests"]["invalid_type_guard"] = f"FAIL: {e}"

    # Overall status
    if any("FAIL" in str(v) for v in results["tests"].values()):
        results["status"] = "degraded"

    return results


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        gen = MotionGenerator()

        if cmd == "generate":
            mtype = sys.argv[2] if len(sys.argv) > 2 else "emergency_restore_pt"
            facts = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else None
            result = gen.generate_motion(mtype, custom_facts=facts)
            if result.get("text"):
                print(result["text"])
                print(f"\n--- {result['word_count']} words | "
                      f"{result['authority_count']} authorities | "
                      f"{result['evidence_count']} evidence items ---",
                      file=sys.stderr)
            else:
                cycle_json(result)
        elif cmd == "brief":
            mtype = sys.argv[2] if len(sys.argv) > 2 else "emergency_restore_pt"
            print(gen.generate_brief_in_support(mtype))
        elif cmd == "evidence":
            mtype = sys.argv[2] if len(sys.argv) > 2 else "emergency_restore_pt"
            cycle_json(gen.gather_evidence_for_motion(mtype))
        elif cmd == "authority":
            mtype = sys.argv[2] if len(sys.argv) > 2 else "emergency_restore_pt"
            cycle_json(gen.gather_authority_for_motion(mtype))
        elif cmd == "list":
            cycle_json(gen.list_available_motions())
        elif cmd == "test":
            cycle_json(self_test())
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print("Commands: generate, brief, evidence, authority, list, test")
    else:
        print("Motion Generator Skill — MBP LitigationOS")
        print("Usage:")
        print("  python motion_generator.py generate <type> [custom facts]")
        print("  python motion_generator.py brief <type>")
        print("  python motion_generator.py evidence <type>")
        print("  python motion_generator.py authority <type>")
        print("  python motion_generator.py list")
        print("  python motion_generator.py test")
        print(f"\nMotion types: {', '.join(MotionGenerator.MOTION_TYPES.keys())}")
