"""
LEXICON Query Engine — Unified API for Michigan Legal Intelligence

Combines LEXICON (knowledge base) + ORACLE (reasoning) into a single
query interface for use by agents, tools, and the MCP server.

Usage:
    from lexicon.lexicon_engine import LexiconEngine
    engine = LexiconEngine()
    
    # "What do I need to file a custody modification?"
    roadmap = engine.filing_roadmap("motion_to_modify_custody", "14th_circuit_family", lane="A")
    
    # "When is my response brief due if the hearing is April 15?"
    deadlines = engine.compute_deadlines("motion_filing", hearing_date="2026-04-15")
    
    # "Is this recording admissible?"
    rules = engine.evidence_check("authentication", "audio_recording")
    
    # "What canons did McNeill violate?"
    violations = engine.canon_analysis(canons=[2, 3, 5])
    
    # Free-text legal question
    answer = engine.ask("How do I disqualify a judge in Michigan?")
"""

import sys
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# Add parent paths for imports
_engines_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_engines_dir))
sys.path.insert(0, str(_engines_dir / "lexicon"))
sys.path.insert(0, str(_engines_dir / "oracle"))

from lexicon.lexicon_db import LexiconDB
try:
    from oracle.oracle_engine import Oracle
    from oracle.deadlines import DeadlineCalculator, MichiganCalendar
    HAS_ORACLE = True
except ImportError:
    HAS_ORACLE = False


class LexiconEngine:
    """Unified Michigan Legal Intelligence Query Engine."""

    def __init__(self, lexicon_db_path: Optional[str] = None):
        self.lexicon = LexiconDB(db_path=lexicon_db_path)
        if HAS_ORACLE:
            self.oracle = Oracle()
            self.calendar = MichiganCalendar()
            self.deadlines = DeadlineCalculator()
        else:
            self.oracle = None
            self.calendar = None
            self.deadlines = None

    # ─── High-Level Query Methods ─────────────────────────────

    def ask(self, question: str) -> Dict[str, Any]:
        """Answer a free-text legal question using LEXICON + ORACLE.
        
        Routes to the most appropriate handler based on keywords.
        """
        q = question.lower()

        # Filing / procedural questions
        filing_keywords = ["file", "filing", "motion", "petition", "application", "complaint"]
        if any(kw in q for kw in filing_keywords):
            filing_type = self._detect_filing_type(q)
            court = self._detect_court(q)
            if filing_type:
                return {
                    "type": "filing_guidance",
                    "filing_type": filing_type,
                    "court": court,
                    "roadmap": self.filing_roadmap(filing_type, court) if self.oracle else None,
                    "rules": self.lexicon.search(question, limit=10),
                    "checklist": self.oracle.get_checklist(filing_type) if self.oracle else None
                }

        # Deadline questions
        deadline_keywords = ["deadline", "when", "due", "days", "time limit", "how long"]
        if any(kw in q for kw in deadline_keywords):
            return {
                "type": "deadline_info",
                "deadlines": self.lexicon.get_deadlines(),
                "rules": self.lexicon.search(question, limit=5)
            }

        # Evidence questions
        evidence_keywords = ["evidence", "admissible", "hearsay", "authenticate", "witness", "exhibit"]
        if any(kw in q for kw in evidence_keywords):
            return {
                "type": "evidence_guidance",
                "rules": self.lexicon.search(question, source="MRE", limit=10),
                "decision_trees": self._get_relevant_evidence_trees(q)
            }

        # Judicial conduct / JTC questions
        judicial_keywords = ["canon", "jtc", "misconduct", "bias", "recuse", "disqualify"]
        if any(kw in q for kw in judicial_keywords):
            return {
                "type": "judicial_conduct",
                "rules": self.lexicon.search(question, limit=10),
                "canon_violations": self.lexicon.get_canon_violations(),
                "disqualification_rules": [
                    self.lexicon.get_rule("MCR-2.003"),
                    self.lexicon.get_rule("MCL-600.916")
                ]
            }

        # FOC questions
        foc_keywords = ["foc", "friend of the court", "recommendation", "objection", "enforcement"]
        if any(kw in q for kw in foc_keywords):
            return {
                "type": "foc_guidance",
                "rules": self.lexicon.search(question, source="FOC", limit=10),
                "deadlines": self.lexicon.get_deadlines(trigger_event="foc_recommendation")
            }

        # Default: full-text search
        return {
            "type": "search_results",
            "rules": self.lexicon.search(question, limit=15)
        }

    def filing_roadmap(self, filing_type: str, court: str = None,
                       lane: str = None, hearing_date: str = None) -> Dict:
        """Complete procedural roadmap for a filing type."""
        result = {
            "filing_type": filing_type,
            "court": court or "general",
            "lane": lane,
            "requirements": self.lexicon.get_filing_requirements(filing_type, court),
            "applicable_rules": [],
            "cross_references": []
        }

        # Get primary rules for this filing type
        rules = self.lexicon.search(filing_type.replace("_", " "), limit=10)
        result["applicable_rules"] = rules

        # Get cross-references for each rule
        for rule in rules:
            refs = self.lexicon.get_cross_refs(rule["rule_id"])
            result["cross_references"].extend(refs)

        # Add ORACLE enrichment
        if self.oracle:
            result["checklist"] = self.oracle.get_checklist(filing_type, court)
            result["forms"] = self.oracle.get_forms_required(filing_type, court)
            result["service"] = self.oracle.get_service_requirements(filing_type, court or "14th_circuit_family")
            result["risks"] = self.oracle.analyze_filing_risks(filing_type, court or "14th_circuit_family", lane or "A")

            if hearing_date:
                ref_date = date.fromisoformat(hearing_date) if isinstance(hearing_date, str) else hearing_date
                result["computed_deadlines"] = self.deadlines.motion_deadlines(ref_date)

        if lane and self.oracle:
            result["lane_info"] = self.oracle.get_lane_info(lane)

        return result

    def compute_deadlines(self, trigger_event: str,
                          hearing_date: str = None,
                          judgment_date: str = None,
                          order_date: str = None) -> List[Dict]:
        """Compute deadlines for a trigger event."""
        if not self.deadlines:
            return self.lexicon.get_deadlines(trigger_event=trigger_event)

        if trigger_event == "motion_filing" and hearing_date:
            ref = date.fromisoformat(hearing_date) if isinstance(hearing_date, str) else hearing_date
            return self.deadlines.motion_deadlines(ref)
        elif trigger_event == "appeal_of_right" and judgment_date:
            ref = date.fromisoformat(judgment_date) if isinstance(judgment_date, str) else judgment_date
            return self.deadlines.appeal_of_right_timeline(ref)
        elif trigger_event == "coa_leave" and order_date:
            ref = date.fromisoformat(order_date) if isinstance(order_date, str) else order_date
            return self.deadlines.leave_to_appeal_coa_timeline(ref)
        elif trigger_event == "foc_recommendation" and order_date:
            ref = date.fromisoformat(order_date) if isinstance(order_date, str) else order_date
            return self.deadlines.foc_objection_timeline(ref)
        else:
            return self.lexicon.get_deadlines(trigger_event=trigger_event)

    def evidence_check(self, category: str, evidence_type: str = None) -> Dict:
        """Check evidence admissibility rules for a category."""
        rules = self.lexicon.get_evidence_rules_by_category(category)

        # Also search for evidence_type if provided
        search_results = []
        if evidence_type:
            search_results = self.lexicon.search(
                f"{evidence_type} {category}", source="MRE", limit=5
            )

        return {
            "category": category,
            "evidence_type": evidence_type,
            "rules": rules,
            "related_rules": search_results
        }

    def canon_analysis(self, canons: List[int] = None) -> Dict:
        """Analyze judicial canon violations."""
        violations = []
        rules = []

        if canons:
            for c in canons:
                violations.extend(self.lexicon.get_canon_violations(canon_number=c))
                rule = self.lexicon.get_rule(f"CANON-{c}")
                if rule:
                    rules.append(rule)
        else:
            violations = self.lexicon.get_canon_violations()
            rules = self.lexicon.get_rules_by_source("CANON")

        return {
            "canons_analyzed": canons or list(range(1, 8)),
            "violations": violations,
            "rules": rules,
            "disqualification_rules": [
                self.lexicon.get_rule("MCR-2.003"),
                self.lexicon.get_rule("MCL-600.916")
            ]
        }

    def lane_rules(self, lane: str) -> Dict:
        """Get all rules applicable to a case lane."""
        rules = self.lexicon.get_rules_for_lane(lane)
        lane_info = self.oracle.get_lane_info(lane) if self.oracle else {"lane": lane}

        # Group by source
        by_source = {}
        for r in rules:
            src = r.get("source", "UNKNOWN")
            by_source.setdefault(src, []).append(r)

        return {
            "lane": lane,
            "info": lane_info,
            "total_rules": len(rules),
            "by_source": {k: len(v) for k, v in by_source.items()},
            "rules": rules
        }

    def get_stats(self) -> Dict:
        """Get complete LEXICON + ORACLE statistics."""
        stats = self.lexicon.get_stats()
        stats["oracle_available"] = HAS_ORACLE
        stats["engine_version"] = "1.0.0"
        return stats

    # ─── Private Helpers ──────────────────────────────────────

    def _detect_filing_type(self, q: str) -> Optional[str]:
        """Detect filing type from natural language."""
        patterns = {
            "motion_to_modify_custody": ["custody", "modify custody", "change custody", "parenting time"],
            "motion_to_disqualify_judge": ["disqualify", "recuse", "recusal", "disqualification"],
            "motion_to_vacate_order": ["vacate", "vacatur", "set aside", "relief from"],
            "motion_for_contempt": ["contempt", "violation of order", "enforce order"],
            "application_for_leave": ["appeal", "leave to appeal", "coa", "appellate"],
            "ppo_modification": ["ppo", "protection order", "personal protection"],
            "motion_for_summary_disposition": ["summary disposition", "summary judgment", "dismiss"],
            "foc_objection": ["foc objection", "friend of court", "recommendation"],
        }
        for filing_type, keywords in patterns.items():
            if any(kw in q for kw in keywords):
                return filing_type
        return None

    def _detect_court(self, q: str) -> Optional[str]:
        """Detect court from natural language."""
        if any(kw in q for kw in ["coa", "court of appeals", "appellate"]):
            return "michigan_coa"
        if any(kw in q for kw in ["msc", "supreme court"]):
            return "michigan_msc"
        if any(kw in q for kw in ["civil", "housing", "shady oaks"]):
            return "14th_circuit_civil"
        if any(kw in q for kw in ["family", "custody", "ppo", "foc"]):
            return "14th_circuit_family"
        return None

    def _get_relevant_evidence_trees(self, q: str) -> List[Dict]:
        """Get evidence decision trees relevant to the question."""
        categories = []
        if any(kw in q for kw in ["hearsay", "out of court", "statement"]):
            categories.append("hearsay_exception")
        if any(kw in q for kw in ["authentic", "foundation", "genuine"]):
            categories.append("authentication")
        if any(kw in q for kw in ["impeach", "credib", "inconsistent", "bias"]):
            categories.append("impeachment")
        if any(kw in q for kw in ["business record", "public record", "police"]):
            categories.append("hearsay_exception")

        results = []
        for cat in set(categories):
            results.extend(self.lexicon.get_evidence_rules_by_category(cat))
        return results


# ─── CLI ──────────────────────────────────────────────────────

def main():
    import argparse

    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="LEXICON Engine — Michigan Legal Intelligence")
    sub = parser.add_subparsers(dest="command")

    sp = sub.add_parser("ask", help="Ask a legal question")
    sp.add_argument("question", nargs="+", help="Your question")

    sp = sub.add_parser("roadmap", help="Get filing roadmap")
    sp.add_argument("filing_type", help="Filing type")
    sp.add_argument("court", nargs="?", help="Court")
    sp.add_argument("--lane", help="Case lane (A-F)")
    sp.add_argument("--hearing", help="Hearing date (YYYY-MM-DD)")

    sp = sub.add_parser("deadlines", help="Compute deadlines")
    sp.add_argument("trigger", help="Trigger event")
    sp.add_argument("--hearing", help="Hearing date")
    sp.add_argument("--judgment", help="Judgment date")
    sp.add_argument("--order", help="Order date")

    sp = sub.add_parser("evidence", help="Evidence admissibility check")
    sp.add_argument("category", help="Category (hearsay_exception, authentication, etc.)")
    sp.add_argument("--type", dest="etype", help="Evidence type")

    sp = sub.add_parser("canons", help="Canon violation analysis")
    sp.add_argument("--canons", type=int, nargs="+", help="Canon numbers (1-7)")

    sp = sub.add_parser("lane", help="Rules for a case lane")
    sp.add_argument("lane_letter", help="Lane letter (A-F)")

    sub.add_parser("stats", help="Database statistics")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    engine = LexiconEngine()

    if args.command == "ask":
        question = " ".join(args.question)
        result = engine.ask(question)
        print(f"\nQuery type: {result['type']}")
        if "rules" in result and result["rules"]:
            print(f"\nRelevant rules ({len(result['rules'])}):")
            for r in result["rules"][:10]:
                if isinstance(r, dict) and r:
                    print(f"  [{r.get('source','')}] {r.get('rule_id','')} — {r.get('title','')}")
                    if r.get('summary'):
                        print(f"    {r['summary'][:120]}")
        if "canon_violations" in result and result["canon_violations"]:
            print(f"\nCanon violations ({len(result['canon_violations'])}):")
            for v in result["canon_violations"][:5]:
                print(f"  Canon {v.get('canon_number','?')}: {v.get('violation_type','')}")
        if "disqualification_rules" in result:
            disq = [r for r in result["disqualification_rules"] if r]
            if disq:
                print(f"\nDisqualification rules:")
                for r in disq:
                    print(f"  {r.get('rule_id','')} — {r.get('title','')}")
                    if r.get('summary'):
                        print(f"    {r['summary'][:150]}")
        if "checklist" in result and result["checklist"]:
            print(f"\nChecklist ({len(result['checklist'])} steps):")
            for item in result["checklist"][:5]:
                print(f"  Step {item['step']}: {item['action']}")
        if "decision_trees" in result and result["decision_trees"]:
            print(f"\nEvidence decision trees ({len(result['decision_trees'])}):")
            for t in result["decision_trees"][:3]:
                print(f"  {t.get('mre_number','')} — {t.get('rule_name','')}")
        if "deadlines" in result and result["deadlines"]:
            print(f"\nRelevant deadlines ({len(result['deadlines'])}):")
            for d in result["deadlines"][:5]:
                if isinstance(d, dict):
                    print(f"  {d.get('description', d.get('rule_id',''))}")

    elif args.command == "roadmap":
        result = engine.filing_roadmap(
            args.filing_type, args.court, lane=args.lane, hearing_date=args.hearing
        )
        print(f"\n{'='*60}")
        print(f"  FILING ROADMAP: {result['filing_type']}")
        print(f"{'='*60}")
        if result.get("lane_info"):
            li = result["lane_info"]
            print(f"  Lane: {li.get('lane')} — {li.get('description')}")
            print(f"  Case: {li.get('case_number')} | Court: {li.get('court')}")
        if result.get("checklist"):
            print(f"\n  Checklist:")
            for item in result["checklist"]:
                req = "REQUIRED" if item.get("required") else "optional"
                print(f"    Step {item['step']}: {item['action']}  [{req}]")
        if result.get("forms"):
            print(f"\n  Required Forms:")
            for f in result["forms"]:
                print(f"    {f.get('form_number','?')}: {f.get('title','')}")
        if result.get("risks"):
            print(f"\n  Risks:")
            for r in result["risks"]:
                print(f"    [{r.get('severity','')}] {r.get('risk','')}")
                print(f"      → {r.get('mitigation','')}")

    elif args.command == "deadlines":
        result = engine.compute_deadlines(
            args.trigger,
            hearing_date=args.hearing,
            judgment_date=args.judgment,
            order_date=args.order
        )
        print(f"\nDeadlines for '{args.trigger}':")
        for d in result:
            if isinstance(d, dict):
                print(f"  {d.get('date', d.get('computed_date', '?'))}: "
                      f"{d.get('event', d.get('description', ''))}")

    elif args.command == "evidence":
        result = engine.evidence_check(args.category, args.etype)
        print(f"\nEvidence rules for '{args.category}':")
        for r in result.get("rules", []):
            print(f"\n  {r.get('mre_number','')} — {r.get('rule_name','')}")
            print(f"    Applies: {r.get('applies_when','')[:100]}")

    elif args.command == "canons":
        result = engine.canon_analysis(args.canons)
        print(f"\nCanon analysis ({len(result['violations'])} violations):")
        for v in result["violations"]:
            print(f"\n  Canon {v.get('canon_number','?')}: {v.get('violation_type','')}")
            for e in v.get("elements", []):
                print(f"    • {e}")

    elif args.command == "lane":
        result = engine.lane_rules(args.lane_letter)
        print(f"\nLane {result['lane']}: {result['total_rules']} applicable rules")
        print(f"  By source: {result['by_source']}")
        for r in result["rules"][:15]:
            print(f"  [{r.get('source','')}] {r.get('rule_id','')} — {r.get('title','')}")

    elif args.command == "stats":
        stats = engine.get_stats()
        print("\nLEXICON + ORACLE Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
