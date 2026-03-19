"""
OMEGA Phase 11: Legal Action Discovery
Implement Six Case Lane model. Score evidence strength for all 79 actions
(A1-A35, B1-B14, C1-C7, D1-D7, E1-E8, F1-F8) against atom stores filtered
by MEEK lane.
"""
import json
import re
import sys
import time
from pathlib import Path

from config import (
    SCANS_ROOT, MASTER_ROOT, MEEK_SIGNALS,
    LANE_A_CASES, LANE_B_CASES, LANE_D_CASES, LANE_E_CASES, LANE_F_CASES,
    POSTURE_TAGS,
    get_cyclepack_dir, report_progress, CYCLE_TS,
)
from safety import write_phase_checkpoint, is_phase_done

# ── Posture Weights ──────────────────────────────────────────────────
POSTURE_WEIGHT = {
    "SWORN_FACT": 3.0,
    "RECORD_FACT": 2.5,
    "EVIDENCE_FACT": 2.0,
    "ALLEGATION": 1.0,
    "INFERENCE": 0.5,
}

# ═══════════════════════════════════════════════════════════════════════
# Full 79-Action Matrix — Six Case Lane Model
# Lane A: Family Court (2024-001507-DC, 2023-5907-PP) — 35 actions
# Lane B: Civil Rights (2025-002760-CZ) — 14 actions
# Lane C: Oversight / Regulatory — 7 actions
# Lane D: PPO / Protection Orders — 7 actions
# Lane E: Judicial Misconduct / JTC — 8 actions
# Lane F: Appellate (COA / MSC) — 8 actions
# ═══════════════════════════════════════════════════════════════════════
ACTION_MATRIX = [
    # ── LANE A: Family Court Actions (A1-A35) ────────────────────────
    {"id": "A1",  "lane": "A", "title": "Emergency Motion to Restore Parenting Time",
     "meek": ["MEEK2", "MEEK3"], "authority": "MCL 722.27a; MCR 3.207",
     "keywords": ["parenting time", "custody", "restore", "visitation", "emergency"]},
    {"id": "A2",  "lane": "A", "title": "Motion for Judicial Disqualification",
     "meek": ["MEEK4"], "authority": "MCR 2.003(C); Canon 3",
     "keywords": ["disqualif", "recuse", "bias", "impartial", "MCR 2.003"]},
    {"id": "A3",  "lane": "A", "title": "Motion to Set Aside Ex Parte Orders",
     "meek": ["MEEK4", "MEEK2"], "authority": "MCR 2.612; MCR 3.207(A)",
     "keywords": ["ex parte", "set aside", "void", "without notice"]},
    {"id": "A4",  "lane": "A", "title": "Motion for De Novo Hearing on FOC Recommendation",
     "meek": ["MEEK2"], "authority": "MCL 552.507(5); MCR 3.210(C)(7)",
     "keywords": ["de novo", "FOC", "recommendation", "referee", "objection"]},
    {"id": "A5",  "lane": "A", "title": "Motion to Compel Discovery",
     "meek": ["MEEK2"], "authority": "MCR 2.313; MCR 3.206(C)",
     "keywords": ["discovery", "compel", "interrogator", "deposition", "produce"]},
    {"id": "A6",  "lane": "A", "title": "Motion for Contempt — Custody Order Violation",
     "meek": ["MEEK2", "MEEK3"], "authority": "MCL 600.1701; MCR 3.208",
     "keywords": ["contempt", "violat", "custody order", "non-compliance"]},
    {"id": "A7",  "lane": "A", "title": "Motion for Contempt — PPO Violation",
     "meek": ["MEEK3"], "authority": "MCL 600.2950(23); MCR 3.708",
     "keywords": ["contempt", "PPO", "protection order", "violat"]},
    {"id": "A8",  "lane": "A", "title": "Motion to Modify Custody",
     "meek": ["MEEK2"], "authority": "MCL 722.27; MCR 3.210",
     "keywords": ["modify", "custody", "change custody", "proper cause", "best interest"]},
    {"id": "A9",  "lane": "A", "title": "Motion for Psychological Evaluation",
     "meek": ["MEEK2"], "authority": "MCL 722.27(1)(c); MCR 3.210(B)",
     "keywords": ["psychological", "evaluation", "assessment", "mental health", "fitness"]},
    {"id": "A10", "lane": "A", "title": "Motion to Appoint Guardian ad Litem",
     "meek": ["MEEK2"], "authority": "MCL 722.24; MCR 3.204",
     "keywords": ["guardian ad litem", "GAL", "child advocate", "child representative"]},
    {"id": "A11", "lane": "A", "title": "Motion for Best Interest Hearing",
     "meek": ["MEEK2"], "authority": "MCL 722.23; MCL 722.27",
     "keywords": ["best interest", "factor", "MCL 722.23", "hearing"]},
    {"id": "A12", "lane": "A", "title": "Motion for Make-Up Parenting Time",
     "meek": ["MEEK2"], "authority": "MCL 722.27a(7)(c)",
     "keywords": ["make-up", "makeup", "compensatory", "parenting time", "denied time"]},
    {"id": "A13", "lane": "A", "title": "Motion to Enforce Parenting Time Order",
     "meek": ["MEEK2"], "authority": "MCL 722.27a(7); MCR 3.208",
     "keywords": ["enforce", "parenting time", "order", "compliance", "violat"]},
    {"id": "A14", "lane": "A", "title": "Objection to FOC Recommendation",
     "meek": ["MEEK2"], "authority": "MCR 3.210(C)(7); MCL 552.507(5)",
     "keywords": ["objection", "FOC", "recommendation", "referee"]},
    {"id": "A15", "lane": "A", "title": "Motion to Strike Improper FOC Report",
     "meek": ["MEEK2"], "authority": "MCR 2.116(C)(8); MCR 3.210",
     "keywords": ["strike", "FOC", "report", "improper", "deficient"]},
    {"id": "A16", "lane": "A", "title": "Motion for Child Support Modification",
     "meek": ["MEEK2"], "authority": "MCL 552.517; MCR 3.211",
     "keywords": ["child support", "modify", "support", "income", "deviation"]},
    {"id": "A17", "lane": "A", "title": "Motion for Attorney Fees",
     "meek": ["MEEK2"], "authority": "MCL 722.27a(7)(a); MCR 3.206(D)",
     "keywords": ["attorney fees", "costs", "sanctions", "fee shifting"]},
    {"id": "A18", "lane": "A", "title": "Motion for Specific Findings of Fact",
     "meek": ["MEEK2"], "authority": "MCR 2.517; MCR 3.210",
     "keywords": ["findings of fact", "specific findings", "conclusions of law"]},
    {"id": "A19", "lane": "A", "title": "Motion to Seal Records",
     "meek": ["MEEK2"], "authority": "MCR 8.119(I)",
     "keywords": ["seal", "protective order", "confidential", "privacy"]},
    {"id": "A20", "lane": "A", "title": "Motion for Stay Pending Appeal",
     "meek": ["MEEK2", "MEEK5"], "authority": "MCR 7.209; MCR 2.614",
     "keywords": ["stay", "pending appeal", "bond", "supersedeas"]},
    {"id": "A21", "lane": "A", "title": "Motion to Consolidate Cases",
     "meek": ["MEEK2", "MEEK3"], "authority": "MCR 2.505(A)",
     "keywords": ["consolidate", "join", "related cases", "common issues"]},
    {"id": "A22", "lane": "A", "title": "Motion for Protective Order — Discovery",
     "meek": ["MEEK2"], "authority": "MCR 2.302(C)",
     "keywords": ["protective order", "discovery", "privilege", "confidential"]},
    {"id": "A23", "lane": "A", "title": "Motion to Quash Subpoena",
     "meek": ["MEEK2"], "authority": "MCR 2.506(H)",
     "keywords": ["quash", "subpoena", "undue burden", "relevance"]},
    {"id": "A24", "lane": "A", "title": "Motion for Evidentiary Hearing",
     "meek": ["MEEK2", "MEEK4"], "authority": "MCR 2.119; MRE 104",
     "keywords": ["evidentiary", "hearing", "evidence", "testimony", "live witness"]},
    {"id": "A25", "lane": "A", "title": "Motion to Reconsider Custody Order",
     "meek": ["MEEK2"], "authority": "MCR 2.119(F)",
     "keywords": ["reconsider", "rehear", "palpable error", "custody"]},
    {"id": "A26", "lane": "A", "title": "Motion Regarding Parental Alienation",
     "meek": ["MEEK2"], "authority": "MCL 722.23(j); MCL 722.23(l)",
     "keywords": ["alienation", "parental alienation", "interfere", "relationship"]},
    {"id": "A27", "lane": "A", "title": "Motion to Compel Compliance with Court Orders",
     "meek": ["MEEK2", "MEEK3"], "authority": "MCL 600.1701; MCR 3.208",
     "keywords": ["comply", "compliance", "court order", "enforce"]},
    {"id": "A28", "lane": "A", "title": "Motion for Emergency Temporary Orders",
     "meek": ["MEEK2", "MEEK3"], "authority": "MCR 3.207(B)",
     "keywords": ["emergency", "temporary", "immediate", "danger", "harm"]},
    {"id": "A29", "lane": "A", "title": "Motion for Transcript Production",
     "meek": ["MEEK2", "MEEK5"], "authority": "MCR 7.210(B)",
     "keywords": ["transcript", "court reporter", "record", "production"]},
    {"id": "A30", "lane": "A", "title": "Motion to Correct Court Record",
     "meek": ["MEEK2"], "authority": "MCR 2.612; MCR 8.119",
     "keywords": ["correct", "record", "clerical", "error", "nunc pro tunc"]},
    {"id": "A31", "lane": "A", "title": "Motion for Default Judgment",
     "meek": ["MEEK2"], "authority": "MCR 2.603",
     "keywords": ["default", "failure to appear", "failure to respond"]},
    {"id": "A32", "lane": "A", "title": "Motion to Intervene",
     "meek": ["MEEK2"], "authority": "MCR 2.209",
     "keywords": ["intervene", "intervention", "third party", "interested party"]},
    {"id": "A33", "lane": "A", "title": "Motion for Summary Disposition",
     "meek": ["MEEK2"], "authority": "MCR 2.116",
     "keywords": ["summary disposition", "no genuine issue", "matter of law"]},
    {"id": "A34", "lane": "A", "title": "Petition for Personal Protection Order",
     "meek": ["MEEK3"], "authority": "MCL 600.2950; MCR 3.706",
     "keywords": ["PPO", "personal protection", "stalking", "harassment", "domestic violence"]},
    {"id": "A35", "lane": "A", "title": "Motion to Terminate PPO",
     "meek": ["MEEK3"], "authority": "MCL 600.2950(8); MCR 3.707",
     "keywords": ["terminate", "PPO", "modify PPO", "dissolve"]},

    # ── LANE B: Civil Rights Actions (B1-B14) ────────────────────────
    {"id": "B1",  "lane": "B", "title": "42 USC §1983 — Due Process Violation",
     "meek": ["MEEK4"], "authority": "42 USC §1983; 14th Amendment",
     "keywords": ["due process", "1983", "civil rights", "deprivation", "under color of law"]},
    {"id": "B2",  "lane": "B", "title": "42 USC §1983 — Equal Protection",
     "meek": ["MEEK4"], "authority": "42 USC §1983; 14th Amendment",
     "keywords": ["equal protection", "discrimination", "class of one", "disparate"]},
    {"id": "B3",  "lane": "B", "title": "42 USC §1985 — Conspiracy to Deprive Rights",
     "meek": ["MEEK4"], "authority": "42 USC §1985(3)",
     "keywords": ["conspiracy", "1985", "deprive rights", "concerted action"]},
    {"id": "B4",  "lane": "B", "title": "42 USC §1986 — Neglect to Prevent Conspiracy",
     "meek": ["MEEK4"], "authority": "42 USC §1986",
     "keywords": ["neglect", "1986", "prevent", "knowledge of conspiracy"]},
    {"id": "B5",  "lane": "B", "title": "Monell Claim — Municipal Liability",
     "meek": ["MEEK4"], "authority": "Monell v Dept of Social Services, 436 US 658",
     "keywords": ["Monell", "municipal", "policy", "custom", "practice", "official capacity"]},
    {"id": "B6",  "lane": "B", "title": "Bivens Action — Federal Officials",
     "meek": ["MEEK4"], "authority": "Bivens v Six Unknown Named Agents, 403 US 388",
     "keywords": ["Bivens", "federal", "constitutional", "individual capacity"]},
    {"id": "B7",  "lane": "B", "title": "First Amendment Retaliation",
     "meek": ["MEEK4"], "authority": "42 USC §1983; First Amendment",
     "keywords": ["retaliation", "first amendment", "petition", "speech", "filing"]},
    {"id": "B8",  "lane": "B", "title": "Fourth Amendment — Unreasonable Seizure of Children",
     "meek": ["MEEK2", "MEEK4"], "authority": "42 USC §1983; Fourth Amendment",
     "keywords": ["seizure", "children", "fourth amendment", "unreasonable", "removal"]},
    {"id": "B9",  "lane": "B", "title": "Substantive Due Process — Parental Liberty",
     "meek": ["MEEK2", "MEEK4"], "authority": "Troxel v Granville, 530 US 57",
     "keywords": ["parental liberty", "substantive due process", "fundamental right", "Troxel"]},
    {"id": "B10", "lane": "B", "title": "Procedural Due Process — Notice and Hearing",
     "meek": ["MEEK4"], "authority": "Mathews v Eldridge, 424 US 319",
     "keywords": ["notice", "hearing", "procedural due process", "opportunity to be heard"]},
    {"id": "B11", "lane": "B", "title": "State Law — Intentional Infliction of Emotional Distress",
     "meek": ["MEEK4"], "authority": "MCL 600.2913; Roberts v Auto-Owners, 422 Mich 594",
     "keywords": ["emotional distress", "IIED", "outrageous", "extreme conduct"]},
    {"id": "B12", "lane": "B", "title": "State Law — Abuse of Process",
     "meek": ["MEEK4"], "authority": "Friedman v Dozorc, 412 Mich 1",
     "keywords": ["abuse of process", "improper purpose", "ulterior motive"]},
    {"id": "B13", "lane": "B", "title": "State Law — Fraud on the Court",
     "meek": ["MEEK4"], "authority": "MCR 2.612(C)(1)(c)",
     "keywords": ["fraud", "fraud on court", "misrepresent", "perjury", "fabricat"]},
    {"id": "B14", "lane": "B", "title": "State Law — Governmental Immunity Exception",
     "meek": ["MEEK4"], "authority": "MCL 691.1407(2)",
     "keywords": ["governmental immunity", "gross negligence", "ministerial", "discretionary"]},

    # ── LANE C: Oversight / Regulatory Actions (C1-C7) ───────────────
    {"id": "C1",  "lane": "C", "title": "JTC Complaint — Judicial Misconduct",
     "meek": ["MEEK4"], "authority": "MCR 9.104; MCR 9.205",
     "keywords": ["JTC", "judicial tenure", "misconduct", "complaint", "discipline"]},
    {"id": "C2",  "lane": "C", "title": "Attorney Grievance — Attorney Misconduct",
     "meek": ["MEEK4"], "authority": "MCR 9.104; MRPC 3.3; MRPC 8.4",
     "keywords": ["grievance", "attorney misconduct", "bar complaint", "MRPC"]},
    {"id": "C3",  "lane": "C", "title": "MSC Complaint for Superintending Control",
     "meek": ["MEEK4", "MEEK5"], "authority": "MCR 7.304; Const 1963 Art 6 §4",
     "keywords": ["superintending control", "MSC", "extraordinary writ", "mandamus"]},
    {"id": "C4",  "lane": "C", "title": "COA Application for Leave to Appeal",
     "meek": ["MEEK5"], "authority": "MCR 7.205; MCR 7.203",
     "keywords": ["leave to appeal", "COA", "appellate", "application"]},
    {"id": "C5",  "lane": "C", "title": "COA Emergency Application",
     "meek": ["MEEK5"], "authority": "MCR 7.205(F); MCR 7.211(C)(6)",
     "keywords": ["emergency", "COA", "expedited", "immediate relief", "irreparable"]},
    {"id": "C6",  "lane": "C", "title": "FOIA Request — Government Records",
     "meek": ["MEEK4"], "authority": "MCL 15.231; FOIA",
     "keywords": ["FOIA", "public record", "freedom of information", "disclosure"]},
    {"id": "C7",  "lane": "C", "title": "OIG/DHHS Complaint — Agency Misconduct",
     "meek": ["MEEK4"], "authority": "MCL 400.1 et seq.",
     "keywords": ["OIG", "DHHS", "CPS", "agency", "investigation", "complaint"]},

    # ── LANE D: PPO / Protection Orders (D1-D7) ─────────────────────
    {"id": "D1",  "lane": "D", "title": "Motion to Enforce PPO",
     "meek": ["MEEK3"], "authority": "MCL 600.2950(23); MCR 3.708",
     "keywords": ["enforce", "PPO", "protection order", "compliance", "violat"]},
    {"id": "D2",  "lane": "D", "title": "Motion for Contempt (PPO Violation)",
     "meek": ["MEEK3"], "authority": "MCL 600.1701; MCR 3.708",
     "keywords": ["contempt", "PPO", "violation", "protection order", "willful"]},
    {"id": "D3",  "lane": "D", "title": "Motion to Modify PPO",
     "meek": ["MEEK3"], "authority": "MCL 600.2950(8); MCR 3.707",
     "keywords": ["modify", "PPO", "change terms", "protection order", "amend"]},
    {"id": "D4",  "lane": "D", "title": "Motion to Extend PPO",
     "meek": ["MEEK3"], "authority": "MCL 600.2950(11); MCR 3.706",
     "keywords": ["extend", "PPO", "renewal", "expiration", "continuing threat"]},
    {"id": "D5",  "lane": "D", "title": "PPO Violation Criminal Complaint",
     "meek": ["MEEK3"], "authority": "MCL 600.2950(23); MCL 764.15b",
     "keywords": ["criminal", "PPO violation", "arrest", "police report", "warrant"]},
    {"id": "D6",  "lane": "D", "title": "Motion for Bond Conditions",
     "meek": ["MEEK3"], "authority": "MCL 765.6; MCR 6.106",
     "keywords": ["bond", "conditions", "bail", "pretrial", "release conditions"]},
    {"id": "D7",  "lane": "D", "title": "Emergency Ex Parte PPO Petition",
     "meek": ["MEEK3"], "authority": "MCL 600.2950; MCR 3.706",
     "keywords": ["emergency", "ex parte", "PPO", "immediate danger", "petition"]},

    # ── LANE E: Judicial Misconduct / JTC (E1-E8) ───────────────────
    {"id": "E1",  "lane": "E", "title": "Motion for Disqualification (MCR 2.003)",
     "meek": ["MEEK4"], "authority": "MCR 2.003(C); Canon 3",
     "keywords": ["disqualif", "recuse", "bias", "impartial", "MCR 2.003"]},
    {"id": "E2",  "lane": "E", "title": "JTC Formal Complaint",
     "meek": ["MEEK4"], "authority": "MCR 9.104; MCR 9.205",
     "keywords": ["JTC", "judicial tenure", "misconduct", "discipline", "complaint"]},
    {"id": "E3",  "lane": "E", "title": "Motion for Peremptory Disqualification",
     "meek": ["MEEK4"], "authority": "MCR 2.003(B); MCL 600.1428",
     "keywords": ["peremptory", "disqualif", "challenge", "automatic"]},
    {"id": "E4",  "lane": "E", "title": "Ex Parte Contact Documentation",
     "meek": ["MEEK4"], "authority": "Canon 3(A)(4); MCR 2.003",
     "keywords": ["ex parte", "contact", "communication", "improper", "one-sided"]},
    {"id": "E5",  "lane": "E", "title": "Canon Violation Brief",
     "meek": ["MEEK4"], "authority": "MI Code of Judicial Conduct; Canon 1-7",
     "keywords": ["canon", "judicial conduct", "violation", "ethics", "demeanor"]},
    {"id": "E6",  "lane": "E", "title": "Pattern of Bias Memorandum",
     "meek": ["MEEK4"], "authority": "MCR 2.003(C)(1); Canon 3",
     "keywords": ["pattern", "bias", "prejudice", "systematic", "disparity"]},
    {"id": "E7",  "lane": "E", "title": "Motion for New Trial (Judicial Bias)",
     "meek": ["MEEK4"], "authority": "MCR 2.611; MCR 2.003",
     "keywords": ["new trial", "bias", "prejudice", "fair trial", "judicial error"]},
    {"id": "E8",  "lane": "E", "title": "Complaint to State Bar (Attorney Misconduct)",
     "meek": ["MEEK4"], "authority": "MCR 9.104; MRPC 3.3; MRPC 8.4",
     "keywords": ["state bar", "attorney misconduct", "grievance", "MRPC", "ethics"]},

    # ── LANE F: Appellate — COA / MSC (F1-F8) ───────────────────────
    {"id": "F1",  "lane": "F", "title": "Claim of Appeal (COA)",
     "meek": ["MEEK5"], "authority": "MCR 7.203; MCR 7.204",
     "keywords": ["claim of appeal", "COA", "final order", "appeal as of right"]},
    {"id": "F2",  "lane": "F", "title": "Application for Leave to Appeal (COA)",
     "meek": ["MEEK5"], "authority": "MCR 7.205; MCR 7.203",
     "keywords": ["leave to appeal", "COA", "application", "appellate"]},
    {"id": "F3",  "lane": "F", "title": "Application for Leave to Appeal (MSC)",
     "meek": ["MEEK5"], "authority": "MCR 7.303; MCR 7.305",
     "keywords": ["MSC", "supreme court", "leave to appeal", "significant question"]},
    {"id": "F4",  "lane": "F", "title": "Interlocutory Appeal",
     "meek": ["MEEK5"], "authority": "MCR 7.203(B); MCR 7.205",
     "keywords": ["interlocutory", "non-final", "leave to appeal", "interim order"]},
    {"id": "F5",  "lane": "F", "title": "MSC Original Action (Superintending Control)",
     "meek": ["MEEK5"], "authority": "MCR 7.304; MCR 7.305; Const 1963 Art 6 §4",
     "keywords": ["superintending control", "MSC", "extraordinary writ", "mandamus"]},
    {"id": "F6",  "lane": "F", "title": "Motion for Immediate Consideration",
     "meek": ["MEEK5"], "authority": "MCR 7.211(C)(6); MCR 7.305(C)(6)",
     "keywords": ["immediate consideration", "expedite", "urgent", "emergency"]},
    {"id": "F7",  "lane": "F", "title": "Motion for Stay Pending Appeal",
     "meek": ["MEEK5"], "authority": "MCR 7.209; MCR 2.614",
     "keywords": ["stay", "pending appeal", "bond", "supersedeas", "irreparable"]},
    {"id": "F8",  "lane": "F", "title": "Brief on Appeal",
     "meek": ["MEEK5"], "authority": "MCR 7.212; MCR 7.305",
     "keywords": ["brief", "appeal", "argument", "standard of review", "issues presented"]},
]


def _load_atom_store(cycle_dir: Path, store_name: str) -> list[dict]:
    """Load atoms from JSONL files."""
    atoms: list[dict] = []
    fname = f"{store_name}.jsonl"
    for candidate in (cycle_dir / fname, cycle_dir / "atoms" / fname):
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line:
                    try:
                        atoms.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            break
    return atoms


def _atoms_match_meek(atom: dict, meek_lanes: list[str]) -> bool:
    """Check if atom's meek_lane matches any of the action's target lanes."""
    atom_lane = atom.get("meek_lane", "")
    if atom_lane and atom_lane in meek_lanes:
        return True
    # Also check text against MEEK signal patterns
    text = atom.get("text", "") or atom.get("content", "")
    for lane_id in meek_lanes:
        pattern = MEEK_SIGNALS.get(lane_id)
        if pattern and pattern.search(text):
            return True
    return False


def _atoms_match_keywords(atom: dict, keywords: list[str]) -> bool:
    """Check if atom text matches action keywords."""
    text = ((atom.get("text", "") or "") + " " + (atom.get("content", "") or "")).lower()
    return any(kw.lower() in text for kw in keywords)


def _score_evidence(fact_count: int, citation_count: int, person_count: int,
                    posture_scores: float) -> float:
    """(fact_atoms×3 + citation_atoms×2 + person_atoms×1) × posture_weight."""
    raw = fact_count * 3 + citation_count * 2 + person_count * 1
    return round(raw * max(posture_scores, 0.5), 2)


def _compute_posture_weight(atoms: list[dict]) -> float:
    """Average posture weight across matched atoms."""
    if not atoms:
        return 0.5
    total = 0.0
    for a in atoms:
        posture = a.get("posture", "ALLEGATION")
        total += POSTURE_WEIGHT.get(posture, 1.0)
    return total / len(atoms)


def _identify_gaps(action: dict, fact_count: int, citation_count: int,
                   event_count: int) -> list[str]:
    """Identify what's missing for an action to be filing-ready."""
    gaps = []
    if fact_count == 0:
        gaps.append("No supporting fact atoms found")
    elif fact_count < 3:
        gaps.append(f"Only {fact_count} fact atoms — need stronger factual foundation")
    if citation_count == 0:
        gaps.append(f"No citation atoms matching {action['authority']}")
    if event_count == 0:
        gaps.append("No event atoms with dates — timeline gap")
    if fact_count > 0 and citation_count == 0:
        gaps.append("Facts exist but no legal authority links — need authority chain")
    return gaps


def run_legal_action_discovery(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase11"):
        print("[PHASE11] Already complete, skipping", file=sys.stderr)
        return

    print("[PHASE11] Legal Action Discovery starting...", file=sys.stderr)
    start = time.time()

    # Load atom stores
    fact_atoms = _load_atom_store(cycle_dir, "fact_atoms")
    citation_atoms = _load_atom_store(cycle_dir, "citation_atoms")
    event_atoms = _load_atom_store(cycle_dir, "event_atoms")
    person_atoms = _load_atom_store(cycle_dir, "person_atoms")

    print(f"[PHASE11] Atoms: facts={len(fact_atoms)}, citations={len(citation_atoms)}, "
          f"events={len(event_atoms)}, persons={len(person_atoms)}", file=sys.stderr)

    # ── Score each action ────────────────────────────────────────────
    results: list[dict] = []
    lane_a_results: list[dict] = []
    lane_b_results: list[dict] = []
    lane_c_results: list[dict] = []
    lane_d_results: list[dict] = []
    lane_e_results: list[dict] = []
    lane_f_results: list[dict] = []
    evidence_gaps: list[dict] = []

    for idx, action in enumerate(ACTION_MATRIX):
        meek_lanes = action["meek"]
        keywords = action["keywords"]

        # Filter atoms by MEEK lane + keyword match
        matched_facts = [a for a in fact_atoms
                         if _atoms_match_meek(a, meek_lanes) and _atoms_match_keywords(a, keywords)]
        matched_citations = [a for a in citation_atoms
                             if _atoms_match_meek(a, meek_lanes) and _atoms_match_keywords(a, keywords)]
        matched_events = [a for a in event_atoms
                          if _atoms_match_meek(a, meek_lanes) and _atoms_match_keywords(a, keywords)]
        matched_persons = [a for a in person_atoms
                           if _atoms_match_meek(a, meek_lanes) and _atoms_match_keywords(a, keywords)]

        all_matched = matched_facts + matched_citations + matched_events + matched_persons
        posture_weight = _compute_posture_weight(all_matched)

        evidence_score = _score_evidence(
            len(matched_facts), len(matched_citations), len(matched_persons), posture_weight)

        # Readiness assessment
        gaps = _identify_gaps(action, len(matched_facts), len(matched_citations), len(matched_events))
        if not gaps:
            readiness = "READY"
        elif len(gaps) <= 1 and len(matched_facts) >= 2:
            readiness = "NEAR_READY"
        elif matched_facts or matched_citations:
            readiness = "PARTIAL"
        else:
            readiness = "INSUFFICIENT"

        entry = {
            "action_id": action["id"],
            "lane": action["lane"],
            "title": action["title"],
            "authority": action["authority"],
            "meek_lanes": meek_lanes,
            "evidence_counts": {
                "fact_atoms": len(matched_facts),
                "citation_atoms": len(matched_citations),
                "event_atoms": len(matched_events),
                "person_atoms": len(matched_persons),
                "total": len(all_matched),
            },
            "posture_weight": round(posture_weight, 2),
            "evidence_score": evidence_score,
            "readiness": readiness,
            "gaps": gaps,
        }
        results.append(entry)

        # Lane-specific scorecards
        lane_entry = {
            "action_id": action["id"],
            "title": action["title"],
            "evidence_score": evidence_score,
            "readiness": readiness,
            "total_atoms": len(all_matched),
            "gap_count": len(gaps),
        }
        if action["lane"] == "A":
            lane_a_results.append(lane_entry)
        elif action["lane"] == "B":
            lane_b_results.append(lane_entry)
        elif action["lane"] == "C":
            lane_c_results.append(lane_entry)
        elif action["lane"] == "D":
            lane_d_results.append(lane_entry)
        elif action["lane"] == "E":
            lane_e_results.append(lane_entry)
        else:
            lane_f_results.append(lane_entry)

        # Evidence gaps
        if gaps:
            evidence_gaps.append({
                "action_id": action["id"],
                "title": action["title"],
                "lane": action["lane"],
                "readiness": readiness,
                "evidence_score": evidence_score,
                "gaps": gaps,
            })

        if (idx + 1) % 10 == 0 or idx + 1 == len(ACTION_MATRIX):
            report_progress("phase11", idx + 1, len(ACTION_MATRIX))

    # Sort by evidence score
    results.sort(key=lambda r: r["evidence_score"], reverse=True)
    top_20 = results[:20]

    elapsed = round(time.time() - start, 1)

    # Lane summaries
    def _lane_summary(lane_results: list[dict]) -> dict:
        return {
            "total_actions": len(lane_results),
            "ready": sum(1 for r in lane_results if r["readiness"] == "READY"),
            "near_ready": sum(1 for r in lane_results if r["readiness"] == "NEAR_READY"),
            "partial": sum(1 for r in lane_results if r["readiness"] == "PARTIAL"),
            "insufficient": sum(1 for r in lane_results if r["readiness"] == "INSUFFICIENT"),
            "avg_score": round(
                sum(r["evidence_score"] for r in lane_results) / max(len(lane_results), 1), 2),
            "actions": sorted(lane_results, key=lambda r: r["evidence_score"], reverse=True),
        }

    lane_a_scorecard = {"lane": "A", "cases": list(LANE_A_CASES), "summary": _lane_summary(lane_a_results)}
    lane_b_scorecard = {"lane": "B", "cases": list(LANE_B_CASES), "summary": _lane_summary(lane_b_results)}
    lane_c_scorecard = {"lane": "C", "cases": ["Oversight/Regulatory"], "summary": _lane_summary(lane_c_results)}
    lane_d_scorecard = {"lane": "D", "cases": list(LANE_D_CASES), "summary": _lane_summary(lane_d_results)}
    lane_e_scorecard = {"lane": "E", "cases": list(LANE_E_CASES), "summary": _lane_summary(lane_e_results)}
    lane_f_scorecard = {"lane": "F", "cases": list(LANE_F_CASES) or ["Appellate/COA/MSC"], "summary": _lane_summary(lane_f_results)}

    # ── Write outputs ────────────────────────────────────────────────
    if not dry_run:
        cycle_dir.mkdir(parents=True, exist_ok=True)

        (cycle_dir / "legal_action_matrix.json").write_text(
            json.dumps({"actions": results, "total": len(results), "elapsed_seconds": elapsed},
                       indent=2), encoding="utf-8")

        (cycle_dir / "lane_a_scorecard.json").write_text(
            json.dumps(lane_a_scorecard, indent=2), encoding="utf-8")
        (cycle_dir / "lane_b_scorecard.json").write_text(
            json.dumps(lane_b_scorecard, indent=2), encoding="utf-8")
        (cycle_dir / "lane_c_scorecard.json").write_text(
            json.dumps(lane_c_scorecard, indent=2), encoding="utf-8")
        (cycle_dir / "lane_d_scorecard.json").write_text(
            json.dumps(lane_d_scorecard, indent=2), encoding="utf-8")
        (cycle_dir / "lane_e_scorecard.json").write_text(
            json.dumps(lane_e_scorecard, indent=2), encoding="utf-8")
        (cycle_dir / "lane_f_scorecard.json").write_text(
            json.dumps(lane_f_scorecard, indent=2), encoding="utf-8")

        (cycle_dir / "top_20_actions.json").write_text(
            json.dumps({"top_20": top_20}, indent=2), encoding="utf-8")

        with open(cycle_dir / "evidence_gaps_per_action.jsonl", "w", encoding="utf-8") as f:
            for gap in evidence_gaps:
                f.write(json.dumps(gap) + "\n")

        print(f"[PHASE11] Outputs written to {cycle_dir}", file=sys.stderr)
        write_phase_checkpoint(cycle_dir, "phase11", {
            "status": "done",
            "total_actions": len(results),
            "ready": sum(1 for r in results if r["readiness"] == "READY"),
            "near_ready": sum(1 for r in results if r["readiness"] == "NEAR_READY"),
            "partial": sum(1 for r in results if r["readiness"] == "PARTIAL"),
            "insufficient": sum(1 for r in results if r["readiness"] == "INSUFFICIENT"),
            "top_score": results[0]["evidence_score"] if results else 0,
            "elapsed": f"{elapsed:.0f}s",
        })
    else:
        ready_count = sum(1 for r in results if r["readiness"] == "READY")
        print(f"[PHASE11] DRY RUN — {len(results)} actions scored, {ready_count} ready", file=sys.stderr)

    ready_count = sum(1 for r in results if r["readiness"] in ("READY", "NEAR_READY"))
    print(f"[PHASE11] Complete in {elapsed:.0f}s — "
          f"{len(results)} actions, {ready_count} ready/near-ready, "
          f"top score {results[0]['evidence_score'] if results else 0}",
          file=sys.stderr)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 11: Legal Action Discovery")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_legal_action_discovery(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
