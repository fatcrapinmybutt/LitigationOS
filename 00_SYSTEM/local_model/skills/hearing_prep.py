"""
THE MANBEARPIG — EPOCH v8.0 — Hearing Preparation Engine
Court appearance preparation with DB-backed evidence and judicial intelligence
Supports: motion hearings, evidentiary hearings, oral argument, emergency hearings
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"


class HearingPrepEngine:
    """Generates comprehensive hearing preparation packages."""

    def __init__(self):
        self.db_path = DB_PATH
        self.objection_types = {
            "hearsay": {
                "rule": "MRE 801, 802",
                "phrase": "Objection, hearsay. The statement is an out-of-court statement offered for the truth of the matter asserted under MRE 801(c).",
                "exceptions": {
                    "present_sense": "MRE 803(1)",
                    "excited_utterance": "MRE 803(2)",
                    "state_of_mind": "MRE 803(3)",
                    "business_records": "MRE 803(6)",
                    "public_records": "MRE 803(8)",
                    "statement_against_interest": "MRE 804(b)(3)",
                    "prior_inconsistent": "MRE 801(d)(1)(A)"
                }
            },
            "relevance": {
                "rule": "MRE 401, 402",
                "phrase": "Objection, relevance. This evidence does not tend to make any fact of consequence more or less probable under MRE 401."
            },
            "prejudicial": {
                "rule": "MRE 403",
                "phrase": "Objection under MRE 403. The probative value of this evidence is substantially outweighed by the danger of unfair prejudice."
            },
            "foundation": {
                "rule": "MRE 901",
                "phrase": "Objection, lack of foundation. No proper authentication or identification under MRE 901."
            },
            "speculation": {
                "rule": "MRE 602",
                "phrase": "Objection, speculation. The witness lacks personal knowledge under MRE 602."
            },
            "leading": {
                "rule": "MRE 611(c)",
                "phrase": "Objection, leading. Counsel is suggesting the answer to the witness on direct examination."
            },
            "best_evidence": {
                "rule": "MRE 1002",
                "phrase": "Objection, best evidence rule. The original writing is required to prove its content under MRE 1002."
            },
            "character": {
                "rule": "MRE 404",
                "phrase": "Objection. This is inadmissible character evidence under MRE 404(a)."
            },
            "privilege": {
                "rule": "MRE 501",
                "phrase": "Objection, privileged. This communication is protected under [attorney-client/spousal/therapist-patient] privilege."
            },
            "cumulative": {
                "rule": "MRE 403, 611(a)",
                "phrase": "Objection, cumulative. This evidence has already been established and is needlessly cumulative under MRE 403."
            }
        }
        self.preservation_phrases = [
            "Your Honor, for the record, I object to [X] on the grounds of [Y] and request that my objection be noted for appellate purposes.",
            "Your Honor, I request that the record reflect that I was not provided notice of this [motion/hearing/order] in violation of MCR 2.119(C)(1).",
            "Your Honor, for purposes of preserving the record, I note that I have not been permitted to [present evidence/cross-examine/respond] in violation of my due process rights.",
            "Your Honor, I request a brief statement of reasons for the Court's ruling pursuant to MCR 2.517(A)(1) to preserve the issue for appeal.",
            "Your Honor, I respectfully note my continuing objection to [X] for the record without the need to re-state it each time.",
            "Your Honor, I move for reconsideration under MCR 2.119(F) and request that my motion toll the time for appeal under MCR 7.204(A)(1)."
        ]
        self.courtroom_etiquette = {
            "addressing_judge": "Your Honor",
            "addressing_opposing": "Counsel" or "Ms. Barnes",
            "standing": "Stand when addressing the court",
            "speaking": "Do not interrupt — wait for the judge to finish",
            "documents": "Hand documents to the clerk, not the judge",
            "recording": "Michigan courts allow recording — MCR 8.115",
            "witnesses": "Address witnesses by name, not 'you'"
        }

    def _query_db(self, sql, params=None):
        """Safe DB query."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sql, params or [])
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            return [{"error": str(e)}]

    def prep_motion_hearing(self, params=None):
        """Full motion hearing preparation package."""
        params = params or {}
        motion_type = params.get("motion_type", "emergency_restore_parenting_time")
        hearing_date = params.get("hearing_date", datetime.now().strftime("%Y-%m-%d"))

        # Get McNeill-specific intel
        mcneill_violations = self._query_db(
            "SELECT * FROM judicial_violations WHERE judge LIKE '%McNeill%' "
            "ORDER BY severity DESC LIMIT 15"
        )

        # Get relevant evidence
        evidence = self._query_db(
            "SELECT quote_text, source_file FROM evidence_quotes "
            "WHERE quote_text LIKE ? LIMIT 20",
            [f"%{motion_type.replace('_', ' ')}%"]
        )

        # Get strongest impeachment items
        impeachment = self._query_db(
            "SELECT * FROM impeachment_items ORDER BY strength_score DESC LIMIT 10"
        )

        result = {
            "method": "prep_motion_hearing",
            "motion_type": motion_type,
            "hearing_date": hearing_date,
            "opening_statement": {
                "time": "30 seconds max",
                "template": (
                    "Your Honor, Andrew Pigors, appearing pro se. "
                    "I am here on my [motion type]. The core issue is straightforward: "
                    "[one sentence summary]. I have [X] exhibits to present. "
                    "I respectfully request the Court's consideration."
                )
            },
            "argument_structure": [
                {"priority": 1, "point": "State the legal standard — cite specific MCR/MCL"},
                {"priority": 2, "point": "Apply the standard to the facts — reference specific exhibits"},
                {"priority": 3, "point": "Address opposing arguments preemptively"},
                {"priority": 4, "point": "State the requested relief clearly"}
            ],
            "anticipated_opposition": [
                {"argument": "PPO violations show unfitness", "rebuttal": "PPO violations do not equate to parental unfitness. MCL 722.27a(3) requires a best-interest analysis. No BIF hearing has occurred."},
                {"argument": "Child is safe with mother", "rebuttal": "Safety is not the standard. MCL 722.23 requires analysis of ALL 12 factors. Factor (j) — willingness to facilitate relationship — has not been assessed."},
                {"argument": "Father's filings are excessive", "rebuttal": "A parent has a constitutional right to petition the court. Boddie v. Connecticut, 401 U.S. 371 (1971). Restricting access violates Due Process."}
            ],
            "exhibit_checklist": [
                "Copies of motion (3 copies: court, opposing party, self)",
                "Proposed order (MCR 2.119(A)(2))",
                "Certificate of Service (MCR 2.107)",
                "Supporting affidavit if facts outside record",
                "Relevant court orders being challenged",
                "Timeline exhibit (one page, key dates)"
            ],
            "mcneill_patterns": {
                "known_violations": len(mcneill_violations),
                "key_patterns": [
                    "Pattern: Muting/silencing plaintiff — COUNTER: 'Your Honor, I respectfully request the opportunity to be heard. Due process requires that I be allowed to present my position.'",
                    "Pattern: Same-day ex parte orders — COUNTER: 'Your Honor, I note for the record that I did not receive notice of [X]. MCR 3.207(C)(2) requires verified pleading and immediate hearing.'",
                    "Pattern: Accepting unsworn testimony — COUNTER: 'Objection. The opposing party's statements are not sworn testimony and are inadmissible under MRE 602 and 603.'",
                    "Pattern: Refusing to view evidence — COUNTER: 'Your Honor, I offer Exhibit [X] for the record pursuant to MRE 103(a)(2). I request the Court state its reasons for exclusion.'"
                ]
            },
            "preservation_script": self.preservation_phrases,
            "closing": "Your Honor, for all the reasons stated, I respectfully request that the Court grant my motion. Thank you."
        }
        return result

    def prep_evidentiary_hearing(self, params=None):
        """Evidentiary hearing with witness/exhibit prep."""
        params = params or {}

        # Get contradiction evidence for cross-examination
        contradictions = self._query_db(
            "SELECT * FROM contradiction_map ORDER BY severity DESC LIMIT 20"
        )

        return {
            "method": "prep_evidentiary_hearing",
            "witness_examination": {
                "direct_examination": {
                    "rules": "MRE 611(a) — Court controls mode and order",
                    "tips": [
                        "Use open-ended questions: Who, What, When, Where, How",
                        "Do NOT lead your own witnesses (MRE 611(c))",
                        "Lay foundation before introducing exhibits (MRE 901)",
                        "Keep answers short and factual"
                    ]
                },
                "cross_examination": {
                    "rules": "MRE 611(b) — Limited to scope of direct + credibility",
                    "tips": [
                        "Use leading questions — you SHOULD lead on cross",
                        "Ask questions you know the answer to",
                        "Use prior inconsistent statements (MRE 613)",
                        "Impeach with contradiction_map evidence"
                    ],
                    "contradictions_available": len(contradictions),
                    "strongest_contradictions": contradictions[:5]
                }
            },
            "exhibit_foundation": {
                "self_authenticating": {
                    "rule": "MRE 902",
                    "types": ["Certified court records (902(4))", "Official publications (902(5))", "Business records with certification (902(11))"]
                },
                "authentication_required": {
                    "rule": "MRE 901",
                    "method": "Testimony of witness with knowledge (901(b)(1))",
                    "script": "Your Honor, I offer what has been marked as Exhibit [X]. [Describe document]. I can authenticate this as [basis]. I move for admission."
                }
            },
            "hearsay_exceptions": {
                "likely_applicable": [
                    "MRE 803(6) — Business records (court filings, FOC records)",
                    "MRE 803(8) — Public records (court orders, police reports)",
                    "MRE 801(d)(2) — Opposing party statements (Watson's prior statements)",
                    "MRE 803(3) — State of mind (Watson's intent statements)"
                ]
            },
            "objection_quick_card": self.objection_types
        }

    def prep_oral_argument(self, params=None):
        """Appellate oral argument preparation (COA/MSC)."""
        params = params or {}
        case_number = params.get("case_number", "366810")

        return {
            "method": "prep_oral_argument",
            "case": case_number,
            "format": {
                "time": "15 minutes per side — MCR 7.214(A)",
                "structure": "2 min intro → 10 min argument → 3 min reserve for rebuttal",
                "dress": "Business professional",
                "podium": "Stand at podium, address panel as 'May it please the Court'"
            },
            "argument_outline": [
                {"time": "0:00-2:00", "content": "Introduction and roadmap: 'This case presents [X] issues. The trial court [did X] in violation of [Y].'"},
                {"time": "2:00-5:00", "content": "Issue 1 — strongest issue first. Standard of review. Record cite. Why reversal required."},
                {"time": "5:00-8:00", "content": "Issue 2 — supporting issue. Connect to Issue 1."},
                {"time": "8:00-10:00", "content": "Issue 3 — any remaining issues briefly."},
                {"time": "10:00-12:00", "content": "Address plain error standard (Carines) — explain why each error is plain and affected substantial rights."},
                {"time": "12:00-12:30", "content": "Conclusion: state requested relief clearly."},
                {"time": "RESERVE", "content": "3 minutes for rebuttal — address ONLY new points raised by appellee."}
            ],
            "hot_bench_questions": [
                {"q": "Counsel, you didn't preserve these issues below. Why shouldn't we apply forfeiture?", "a": "Your Honor, we acknowledge the preservation issue and have briefed plain error under People v. Carines, 460 Mich 750. The errors are plain because they violate established law, and they affected substantial rights because they resulted in complete severance of the parent-child relationship."},
                {"q": "What about the PPO violations?", "a": "Your Honor, PPO violations — even those resulting in incarceration — do not constitute legal grounds to permanently sever parenting time without a best-interest hearing. In re Sanders, 495 Mich 394 (2014)."},
                {"q": "Wasn't the trial court exercising discretion?", "a": "Your Honor, discretion has limits. An ex parte order suspending all parenting time without verified pleading or hearing exceeds the bounds of MCR 3.207(C)(2). That is not discretion — that is a procedural violation."},
                {"q": "What remedy are you seeking?", "a": "Reversal of the ex parte orders, remand for a proper best-interest hearing under MCL 722.23, and restoration of parenting time pending that hearing."}
            ],
            "record_citations": "Prepare a one-page quick-reference with: order dates, transcript pages, exhibit numbers for each issue. Have it at the podium."
        }

    def prep_emergency_hearing(self, params=None):
        """Emergency motion hearing preparation."""
        separation_start = datetime(2025, 8, 8)
        days = (datetime.now() - separation_start).days

        return {
            "method": "prep_emergency_hearing",
            "framework": {
                "irreparable_harm": {
                    "standard": "MCR 3.310(B) — Immediate and irreparable injury",
                    "argument": f"Every day of separation causes irreparable harm to the parent-child bond. {days} days have elapsed. Developmental psychology establishes that prolonged separation causes lasting attachment damage. This harm cannot be remedied by monetary damages."
                },
                "likelihood_of_success": {
                    "standard": "Demonstrate probable success on merits",
                    "argument": "The ex parte orders violated MCR 3.207(C)(2) — no verified pleading, no immediate hearing. Under Vodvarka v. Grasmeyer, 259 Mich App 499 (2003), modification of established custodial environment requires clear and convincing evidence. No such showing was made."
                },
                "balance_of_harms": {
                    "standard": "Harm to movant outweighs harm to opposing party",
                    "argument": "Restoration of parenting time returns the status quo ante. The child benefits from a relationship with both parents. MCL 722.23(j) presumes willingness to facilitate the parent-child relationship serves the child's interest."
                },
                "public_interest": {
                    "standard": "Public interest favors relief",
                    "argument": "Michigan public policy favors maintaining parent-child relationships. MCL 722.27a(1) states that parenting time shall be granted 'to permit frequent and continuing contact.' The public interest is served by enforcing this legislative mandate."
                }
            },
            "separation_days": days,
            "key_phrase": f"Your Honor, my child and I have been separated for {days} days — since August 8, 2025 — without a best-interest hearing. I am asking this Court to restore what Michigan law presumes: that a child benefits from a relationship with both parents."
        }

    def generate_objection_card(self, params=None):
        """Quick-reference objection card for courtroom use — print this."""
        card = {
            "method": "generate_objection_card",
            "title": "OBJECTION QUICK REFERENCE — Andrew Pigors",
            "format": "Print on index card or single sheet",
            "objections": {}
        }
        for name, obj in self.objection_types.items():
            card["objections"][name] = {
                "rule": obj["rule"],
                "say": obj["phrase"]
            }
        card["general_tips"] = [
            "Stand when objecting",
            "State: 'Objection, [ground]' — keep it brief",
            "If overruled: 'Noted for the record, Your Honor'",
            "If opposing counsel objects to your evidence: be ready to state the exception",
            "ALWAYS get a ruling on the record before moving on"
        ]
        return card

    def mcneill_tactical_brief(self, params=None):
        """Judge-specific tactical briefing from judicial_violations DB."""
        violations = self._query_db(
            "SELECT violation_type, description, date, severity "
            "FROM judicial_violations WHERE judge LIKE '%McNeill%' "
            "ORDER BY date DESC LIMIT 30"
        )

        # Categorize
        categories = {}
        for v in violations:
            vtype = v.get("violation_type", "unknown")
            if vtype not in categories:
                categories[vtype] = []
            categories[vtype].append(v)

        return {
            "method": "mcneill_tactical_brief",
            "total_violations": len(violations),
            "categories": {k: len(v) for k, v in categories.items()},
            "top_patterns": [
                {
                    "pattern": "Ex parte orders without notice",
                    "frequency": "24+ documented instances",
                    "counter": "File written objection to EVERY ex parte order. State on record: 'I did not receive notice. MCR 3.207(C)(2) was not followed.'",
                    "preserve": "MCR 2.517 — request findings of fact"
                },
                {
                    "pattern": "Muting/silencing plaintiff",
                    "counter": "Calmly state: 'Your Honor, I respectfully request the opportunity to be heard. I have not yet presented my position.' If cut off, say: 'For the record, I was not permitted to complete my argument.'",
                    "preserve": "Note in post-hearing motion"
                },
                {
                    "pattern": "Accepting unverified allegations",
                    "counter": "Object: 'The opposing party has not provided sworn testimony or verified pleading as required by MCR 3.207(C)(2) and MRE 603.'",
                    "preserve": "MRE 103(a)(1) — timely objection"
                },
                {
                    "pattern": "Refusing to review exculpatory evidence",
                    "counter": "Offer into record: 'Your Honor, I offer Exhibit [X] pursuant to MRE 103(a)(2). If the Court declines to admit it, I request it be made part of the record as an offer of proof.'",
                    "preserve": "MRE 103(a)(2) — offer of proof"
                }
            ],
            "critical_reminders": [
                "RECORD EVERYTHING — Michigan allows recording (MCR 8.115)",
                "Bring a court reporter if possible — MCR 8.108",
                "File written objection within 7 days if oral objection overruled",
                "Every ruling you disagree with: 'Noted for the record, Your Honor'",
                "If denied any right: 'I preserve this issue for appellate review'"
            ]
        }

    def preservation_script(self, params=None):
        """Script for preserving issues on the record."""
        return {
            "method": "preservation_script",
            "purpose": "Say these phrases ON THE RECORD to preserve issues for appeal",
            "phrases": self.preservation_phrases,
            "when_to_use": {
                "denied_motion": "Your Honor, I respectfully note my objection to the denial of my motion for the record and preserve this issue for appeal.",
                "evidence_excluded": "Your Honor, I make an offer of proof under MRE 103(a)(2). The excluded evidence would show [X]. I preserve this ruling for appellate review.",
                "not_allowed_to_speak": "Your Honor, for the record, I was not permitted to [argue/present evidence/cross-examine]. I preserve this as a due process objection.",
                "ex_parte_order": "Your Honor, I object to this order on the grounds that it was entered without notice to me in violation of MCR 3.207(C)(2) and the Due Process Clause of the Fourteenth Amendment.",
                "adverse_ruling": "Your Honor, I respectfully disagree with the Court's ruling and preserve my objection for appellate review under MCR 7.204."
            },
            "magic_words": [
                "'For the record' — signals appellate preservation",
                "'I object' — required to preserve evidentiary issues (MRE 103)",
                "'I preserve this for appeal' — explicit preservation",
                "'Offer of proof' — preserves excluded evidence (MRE 103(a)(2))",
                "'Request findings of fact' — MCR 2.517 — forces judge to explain ruling"
            ]
        }

    def pro_se_courtroom_checklist(self, params=None):
        """Complete courtroom preparation checklist for pro se litigant."""
        return {
            "method": "pro_se_courtroom_checklist",
            "before_hearing": [
                "Print 3 copies of ALL documents (court, opposing, self)",
                "Organize exhibits in numbered order with tabs",
                "Prepare one-page argument outline (not a script — bullet points)",
                "Print objection quick-reference card",
                "Print preservation phrases card",
                "Charge phone for recording (MCR 8.115 allows)",
                "Arrive 30 minutes early",
                "Dress professionally — business attire"
            ],
            "bring_to_court": [
                "Photo ID",
                "3 copies of all filed documents",
                "Proposed order (MCR 2.119(A)(2))",
                "Certificate of Service",
                "Exhibits — organized, tabbed, numbered",
                "Pen and notepad",
                "Objection card",
                "Preservation phrases card",
                "Timeline one-pager"
            ],
            "in_courtroom": [
                "Stand when judge enters/exits",
                "Address judge as 'Your Honor'",
                "Stand when speaking",
                "Do not interrupt anyone",
                "Hand documents to clerk, not judge",
                "State your name for the record when speaking",
                "Object IMMEDIATELY — waiver if you wait",
                "Take notes on everything judge says"
            ],
            "after_hearing": [
                "Request copy of any orders entered",
                "Note the date and time for deadline calculation",
                "File written objection within 7 days if needed",
                "Calculate appeal deadline (21 days — MCR 7.204(A)(1))",
                "Document everything that happened while fresh",
                "Save any recordings"
            ],
            "etiquette": self.courtroom_etiquette
        }
