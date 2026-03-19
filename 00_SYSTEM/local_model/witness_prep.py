"""
Witness Prep — LitigationOS 2026
Cross-examination outlines, deposition questions, impeachment packets,
and credibility analysis for Pigors v. Watson witnesses.
"""

import json
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")

MRE_901_FOUNDATIONS = {
    "document": [
        "I'm showing you what has been marked as Exhibit {exhibit}. Do you recognize this document?",
        "What is this document?",
        "How are you familiar with it?",
        "Is this a fair and accurate copy of the original?",
        "Was this document created in the ordinary course of business?",
    ],
    "photograph": [
        "I'm showing you what has been marked as Exhibit {exhibit}. Do you recognize this?",
        "What does this photograph depict?",
        "How are you familiar with the scene shown?",
        "Does this photograph fairly and accurately depict the scene as it appeared on [date]?",
    ],
    "recording": [
        "I'm showing you what has been marked as Exhibit {exhibit}. Can you identify this recording?",
        "Were you present when this recording was made?",
        "Does this recording fairly and accurately capture what occurred?",
        "Has this recording been altered or edited in any way?",
    ],
    "text_message": [
        "I'm showing you what has been marked as Exhibit {exhibit}. Do you recognize these messages?",
        "What phone number or account is associated with these messages?",
        "Did you send/receive these messages?",
        "Is this a complete and accurate copy of the message exchange?",
    ],
    "email": [
        "I'm showing you what has been marked as Exhibit {exhibit}. Do you recognize this email?",
        "Is this your email address shown in the From/To field?",
        "Did you send/receive this email on or about the date shown?",
        "Is this a fair and accurate copy of the email as sent/received?",
    ],
}


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")
    conn.row_factory = sqlite3.Row
    return conn


class WitnessPrep:
    """Builds cross-examination outlines, impeachment packets, and deposition questions."""

    def get_impeachment_items(
        self, speaker: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query impeachment_items (~15,171 rows), optionally filtered by speaker."""
        conn = _get_db()
        try:
            if speaker:
                rows = conn.execute(
                    """SELECT * FROM impeachment_items
                       WHERE LOWER(speaker) LIKE ?
                       ORDER BY rowid LIMIT ?""",
                    (f"%{speaker.lower()}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM impeachment_items ORDER BY rowid LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_contradictions(
        self, speaker: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query contradiction_map (~10,558 rows), optionally filtered by speaker."""
        conn = _get_db()
        try:
            if speaker:
                rows = conn.execute(
                    """SELECT * FROM contradiction_map
                       WHERE LOWER(COALESCE(source_a_text,'') || ' ' || COALESCE(source_b_text,''))
                       LIKE ?
                       ORDER BY rowid LIMIT ?""",
                    (f"%{speaker.lower()}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM contradiction_map ORDER BY rowid LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def build_cross_exam_outline(self, witness: str) -> Dict[str, Any]:
        """Generate cross-examination outline from impeachment items for a specific witness."""
        items = self.get_impeachment_items(speaker=witness, limit=200)

        # Group by legal_hook or category
        topics: Dict[str, List[Dict]] = {}
        for item in items:
            hook = item.get("legal_hook") or item.get("impeachment_type") or "general"
            topics.setdefault(str(hook), []).append(item)

        outline_sections: List[Dict[str, Any]] = []
        for topic, topic_items in topics.items():
            questions: List[str] = []
            for it in topic_items[:10]:
                stmt = it.get("statement", "")
                contra = it.get("contradicting_text", "")
                if stmt:
                    questions.append(f"You previously stated: \"{stmt[:200]}\" — is that correct?")
                if contra:
                    questions.append(
                        f"But isn't it true that {contra[:200]}?"
                    )
            outline_sections.append({
                "topic": topic,
                "item_count": len(topic_items),
                "suggested_questions": questions,
            })

        return {
            "witness": witness,
            "type": "cross_examination_outline",
            "total_impeachment_items": len(items),
            "topic_count": len(outline_sections),
            "sections": outline_sections,
            "note": "Per MRE 613: extrinsic evidence of prior inconsistent statement admissible if witness given opportunity to explain.",
        }

    def build_deposition_questions(self, witness: str) -> Dict[str, Any]:
        """Generate deposition questions from contradictions for a specific witness."""
        contradictions = self.get_contradictions(speaker=witness, limit=100)

        questions: List[Dict[str, Any]] = []
        for i, c in enumerate(contradictions, 1):
            src_a = c.get("source_a_text", "")
            src_b = c.get("source_b_text", "")
            ctype = c.get("contradiction_type", "")
            questions.append({
                "question_number": i,
                "area": ctype,
                "lead_in": f"I'd like to direct your attention to the following: \"{src_a[:200]}\"",
                "follow_up": f"How do you reconcile that with: \"{src_b[:200]}\"?",
                "purpose": "Establish inconsistency for impeachment per MRE 613",
            })

        return {
            "witness": witness,
            "type": "deposition_questions",
            "total_contradictions": len(contradictions),
            "questions": questions,
        }

    def build_foundation_questions(self, exhibit: str) -> Dict[str, Any]:
        """Authentication foundation questions per MRE 901."""
        exhibit_type = "document"  # default
        exhibit_lower = exhibit.lower()
        if any(w in exhibit_lower for w in ["photo", "image", "picture"]):
            exhibit_type = "photograph"
        elif any(w in exhibit_lower for w in ["recording", "audio", "video"]):
            exhibit_type = "recording"
        elif any(w in exhibit_lower for w in ["text", "sms", "message"]):
            exhibit_type = "text_message"
        elif any(w in exhibit_lower for w in ["email", "e-mail"]):
            exhibit_type = "email"

        template = MRE_901_FOUNDATIONS.get(exhibit_type, MRE_901_FOUNDATIONS["document"])
        questions = [q.format(exhibit=exhibit) for q in template]

        return {
            "exhibit": exhibit,
            "exhibit_type": exhibit_type,
            "type": "foundation_questions",
            "authority": "MRE 901(a) — authentication as condition precedent to admissibility",
            "questions": questions,
            "procedure": [
                "1. Mark exhibit for identification",
                "2. Show exhibit to opposing counsel",
                "3. Ask foundation questions",
                "4. Move for admission: 'Your Honor, I move to admit Exhibit {exhibit} into evidence.'",
                "5. If objection, respond with foundation laid",
            ],
        }

    def build_impeachment_packet(self, witness: str) -> Dict[str, Any]:
        """Complete impeachment package: prior inconsistent statements, contradictions, credibility."""
        impeachment = self.get_impeachment_items(speaker=witness, limit=200)
        contradictions = self.get_contradictions(speaker=witness, limit=100)

        # Prior inconsistent statements
        prior_inconsistent: List[Dict] = []
        for item in impeachment:
            if item.get("statement") and item.get("contradicting_text"):
                prior_inconsistent.append({
                    "statement": item["statement"],
                    "contradicting_evidence": item["contradicting_text"],
                    "legal_hook": item.get("legal_hook", ""),
                })

        # Credibility issues
        credibility_issues: List[str] = []
        if len(prior_inconsistent) > 5:
            credibility_issues.append(
                f"Pattern of inconsistency: {len(prior_inconsistent)} prior inconsistent statements"
            )
        if len(contradictions) > 5:
            credibility_issues.append(
                f"Significant contradictions: {len(contradictions)} contradictions in record"
            )

        return {
            "witness": witness,
            "type": "impeachment_packet",
            "prior_inconsistent_statements": prior_inconsistent[:50],
            "contradictions": [dict(c) for c in contradictions[:50]],
            "credibility_issues": credibility_issues,
            "total_impeachment_items": len(impeachment),
            "total_contradictions": len(contradictions),
            "authority": [
                "MRE 607 — Any party may impeach a witness",
                "MRE 613 — Prior inconsistent statements",
                "MRE 616 — Bias of witness",
            ],
        }

    def get_witness_credibility_score(self, witness: str) -> Dict[str, Any]:
        """Score witness credibility based on contradictions/impeachment items."""
        impeachment = self.get_impeachment_items(speaker=witness, limit=500)
        contradictions = self.get_contradictions(speaker=witness, limit=500)

        imp_count = len(impeachment)
        contra_count = len(contradictions)

        # Lower score = less credible (more impeachment material)
        if imp_count == 0 and contra_count == 0:
            score = 90
            assessment = "HIGH — minimal impeachment material available"
        elif imp_count + contra_count <= 5:
            score = 70
            assessment = "MODERATE — some impeachment material exists"
        elif imp_count + contra_count <= 20:
            score = 45
            assessment = "LOW — significant impeachment material available"
        else:
            score = 20
            assessment = "VERY LOW — extensive impeachment material available"

        return {
            "witness": witness,
            "credibility_score": score,
            "assessment": assessment,
            "impeachment_items": imp_count,
            "contradictions": contra_count,
            "note": "Score reflects available impeachment material, not actual credibility determination (that is for the trier of fact).",
        }

    def list_witnesses(self) -> List[Dict[str, Any]]:
        """Get all unique speakers from impeachment_items."""
        conn = _get_db()
        try:
            rows = conn.execute(
                """SELECT speaker, COUNT(*) as item_count
                   FROM impeachment_items
                   WHERE speaker IS NOT NULL AND speaker != ''
                   GROUP BY speaker
                   ORDER BY item_count DESC"""
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def self_test() -> Dict[str, Any]:
    """Run self-test to verify DB connectivity and key witness prep methods."""
    results = {"status": "ok", "tests": {}}
    wp = WitnessPrep()

    # Test 1: DB connectivity
    try:
        conn = _get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        results["tests"]["db_connectivity"] = {"passed": True}
    except Exception as e:
        results["tests"]["db_connectivity"] = {"passed": False, "error": str(e)}

    # Test 2: list_witnesses
    try:
        witnesses = wp.list_witnesses()
        results["tests"]["list_witnesses"] = {
            "passed": isinstance(witnesses, list),
            "count": len(witnesses),
        }
    except Exception as e:
        results["tests"]["list_witnesses"] = {"passed": False, "error": str(e)}

    # Test 3: get_impeachment_items
    try:
        items = wp.get_impeachment_items(limit=5)
        results["tests"]["get_impeachment_items"] = {
            "passed": isinstance(items, list),
            "count": len(items),
        }
    except Exception as e:
        results["tests"]["get_impeachment_items"] = {"passed": False, "error": str(e)}

    results["status"] = (
        "ok" if all(t.get("passed") for t in results["tests"].values()) else "degraded"
    )
    return results


if __name__ == "__main__":
    wp = WitnessPrep()
    if len(sys.argv) < 2:
        print("Usage: witness_prep.py <command> [args]")
        print("Commands: witnesses | impeachment [witness] | contradictions [witness]")
        print("          cross <witness> | deposition <witness> | foundation <exhibit>")
        print("          packet <witness> | credibility <witness> | test")
        sys.exit(0)

    cmd = sys.argv[1]
    witness_arg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None

    commands_no_arg = {
        "witnesses": lambda: wp.list_witnesses(),
        "impeachment": lambda: wp.get_impeachment_items(speaker=witness_arg),
        "contradictions": lambda: wp.get_contradictions(speaker=witness_arg),
    }
    commands_with_arg = {
        "cross": lambda w: wp.build_cross_exam_outline(w),
        "deposition": lambda w: wp.build_deposition_questions(w),
        "foundation": lambda w: wp.build_foundation_questions(w),
        "packet": lambda w: wp.build_impeachment_packet(w),
        "credibility": lambda w: wp.get_witness_credibility_score(w),
    }

    if cmd == "test":
        result = self_test()
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0)

    if cmd in commands_no_arg:
        result = commands_no_arg[cmd]()
    elif cmd in commands_with_arg:
        if not witness_arg:
            print(f"Error: '{cmd}' requires a witness/exhibit name argument.")
            sys.exit(1)
        result = commands_with_arg[cmd](witness_arg)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

    print(json.dumps(result, indent=2, default=str))
