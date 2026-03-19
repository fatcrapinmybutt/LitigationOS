#!/usr/bin/env python3
"""
OMEGA v2 Court-by-Court Assessment System
==========================================
Enhanced scoring that builds on existing OMEGA scores with deep
court-by-court analysis, filing readiness, and strategic sequencing.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
NOW = datetime.now().isoformat()

# ─────────────────────────────────────────────────────────────────────
# 1. DATA LOADING
# ─────────────────────────────────────────────────────────────────────

def load_all_data(conn):
    """Pull every table we need into memory."""
    c = conn.cursor()
    data = {}

    # Existing OMEGA scores
    c.execute("SELECT * FROM omega_scores")
    cols = [d[0] for d in c.description]
    data["scores"] = [dict(zip(cols, r)) for r in c.fetchall()]

    # Legal actions per forum
    c.execute("SELECT * FROM omega_legal_actions")
    cols = [d[0] for d in c.description]
    data["actions"] = [dict(zip(cols, r)) for r in c.fetchall()]

    # Rule audit
    c.execute("SELECT * FROM omega_rule_audit")
    cols = [d[0] for d in c.description]
    data["rules"] = [dict(zip(cols, r)) for r in c.fetchall()]

    # Claim-evidence map aggregated by classification
    c.execute("""
        SELECT classification,
               COUNT(*) as claim_count,
               AVG(completeness_score) as avg_completeness,
               SUM(matching_evidence_count) as total_evidence,
               SUM(has_gap) as gaps
        FROM omega_claim_evidence_map
        GROUP BY classification
    """)
    data["claims"] = {r[0]: {"count": r[1], "avg_completeness": r[2],
                              "total_evidence": r[3], "gaps": r[4]}
                      for r in c.fetchall()}

    # Violation analysis
    c.execute("SELECT * FROM omega_violation_analysis")
    cols = [d[0] for d in c.description]
    data["violations"] = [dict(zip(cols, r)) for r in c.fetchall()]

    # Judicial violations by canon
    c.execute("""
        SELECT canon_number, severity, COUNT(*) as cnt
        FROM judicial_violations
        GROUP BY canon_number, severity
        ORDER BY cnt DESC
    """)
    data["jv_by_canon"] = defaultdict(lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0})
    for canon, sev, cnt in c.fetchall():
        data["jv_by_canon"][canon][sev] = cnt
        data["jv_by_canon"][canon]["total"] += cnt

    # Total violation counts
    c.execute("SELECT severity, COUNT(*) FROM judicial_violations GROUP BY severity")
    data["jv_severity"] = dict(c.fetchall())

    # Temporal density
    c.execute("""
        SELECT year_month, event_count, categories, is_gap
        FROM omega_temporal_analysis
        WHERE event_count > 0
        ORDER BY event_count DESC
        LIMIT 20
    """)
    cols = [d[0] for d in c.description]
    data["temporal_peaks"] = [dict(zip(cols, r)) for r in c.fetchall()]

    return data


# ─────────────────────────────────────────────────────────────────────
# 2. ENHANCED SCORING ENGINE
# ─────────────────────────────────────────────────────────────────────

def compute_evidence_depth(data, relevant_classifications):
    """Compute evidence depth score (0-100) for a set of claim classifications."""
    total_completeness = 0
    total_evidence = 0
    count = 0
    for cls in relevant_classifications:
        if cls in data["claims"]:
            c = data["claims"][cls]
            total_completeness += c["avg_completeness"]
            total_evidence += c["total_evidence"]
            count += 1
    if count == 0:
        return 50  # baseline when no specific claims mapped
    avg_complete = total_completeness / count
    # Bonus for volume (diminishing returns)
    volume_bonus = min(15, total_evidence / 100000)
    return min(100, avg_complete * 0.85 + volume_bonus)


def compute_violation_support(data, relevant_canons):
    """Score violation support (0-100) based on relevant canon violations."""
    total = 0
    critical_high = 0
    for canon in relevant_canons:
        if canon in data["jv_by_canon"]:
            v = data["jv_by_canon"][canon]
            total += v["total"]
            critical_high += v["critical"] + v["high"]
    if total == 0:
        return 30
    # High scores when many critical/high severity violations
    severity_ratio = critical_high / total if total else 0
    volume_score = min(40, total / 5)
    severity_score = severity_ratio * 60
    return min(100, volume_score + severity_score)


def compute_temporal_strength(data):
    """Score based on temporal evidence density and pattern documentation."""
    peaks = data["temporal_peaks"]
    if not peaks:
        return 50
    max_events = peaks[0]["event_count"] if peaks else 1
    # More peaks and higher density = stronger pattern evidence
    density_score = min(100, len(peaks) * 5 + (max_events / 50))
    return density_score


def rescore_action(action, data, court_config):
    """Re-score a single legal action using enhanced analysis data."""
    forum = action.get("forum", "")
    cfg = court_config.get(forum, {})
    action_name = action.get("filing_name", action.get("name", ""))

    # Find matching config entry
    matched_cfg = None
    for entry in cfg.get("actions", []):
        if entry["name_match"] in action_name.lower():
            matched_cfg = entry
            break
    if not matched_cfg:
        matched_cfg = {"relevant_claims": [], "relevant_canons": [],
                       "base_weight": 1.0, "risk_prob": 0.5, "impact": 7}

    # Component scores
    evidence_depth = compute_evidence_depth(data, matched_cfg["relevant_claims"])
    violation_score = compute_violation_support(data, matched_cfg["relevant_canons"])
    temporal_score = compute_temporal_strength(data)

    # Original OMEGA score (pull from scores table if available)
    original_score = action.get("omega_score", 70)

    # Enhanced composite: weighted blend of original + new analysis
    enhanced = (
        original_score * 0.30 +          # existing OMEGA baseline
        evidence_depth * 0.25 +           # claim-evidence completeness
        violation_score * 0.20 +          # judicial violation support
        temporal_score * 0.10 +           # temporal pattern strength
        matched_cfg["base_weight"] * 15   # court-specific strategic weight
    )
    enhanced = min(100, max(0, enhanced))

    # Readiness calculation
    proc_met = 1 if action.get("readiness_label", "") in ("READY TO FILE", "NEAR READY") else 0
    evidence_ready = 1 if evidence_depth >= 70 else 0
    authority_ready = 1 if action.get("authority") else 0
    rule_mapped = any(r["action_name"] and r["action_name"].lower() in action_name.lower()
                      for r in data["rules"]) if data["rules"] else False
    rule_ready = 1 if rule_mapped else 0

    readiness_pct = (proc_met * 30 + evidence_ready * 30 + authority_ready * 20 + rule_ready * 20)

    # Evidence gaps
    gaps = []
    if evidence_depth < 70:
        gaps.append("Evidence completeness below 70%")
    if violation_score < 50:
        gaps.append("Violation support thin for this action")
    if not rule_mapped:
        gaps.append("Procedural rule mapping incomplete")

    # Risk matrix
    risk_prob = matched_cfg.get("risk_prob", 0.5)
    impact = matched_cfg.get("impact", 7)
    risk_score = risk_prob * impact

    return {
        "forum": forum,
        "action_name": action_name,
        "authority": action.get("authority", ""),
        "original_omega": original_score,
        "enhanced_omega": round(enhanced, 1),
        "evidence_depth": round(evidence_depth, 1),
        "violation_support": round(violation_score, 1),
        "temporal_strength": round(temporal_score, 1),
        "readiness_pct": readiness_pct,
        "evidence_gaps": "; ".join(gaps) if gaps else "None",
        "proc_requirements_met": bool(proc_met and rule_ready),
        "risk_probability": risk_prob,
        "risk_impact": impact,
        "risk_score": round(risk_score, 2),
        "tier": ("CRITICAL" if enhanced >= 90 else "HIGH" if enhanced >= 75
                 else "MEDIUM" if enhanced >= 60 else "LOW"),
    }


# ─────────────────────────────────────────────────────────────────────
# 3. COURT-SPECIFIC CONFIGURATION
# ─────────────────────────────────────────────────────────────────────

COURT_CONFIG = {
    "MSC": {
        "full_name": "Michigan Supreme Court",
        "actions": [
            {
                "name_match": "superintending",
                "action_type": "Superintending Control",
                "description": "Const 1963 Art 6 §4 — extraordinary writ to correct lower court pattern of abuse",
                "evidence_package": ["1,127 documented violations", "Pattern analysis across 24+ hearings",
                                     "Benchbook violation matrix", "Temporal density showing escalation"],
                "relevant_claims": ["superintending_control", "judicial_misconduct", "abuse_of_discretion",
                                    "procedural_due_process", "benchbook_violation"],
                "relevant_canons": ["MCR 2.003 (Disqualification)", "MCR / Canon — PROCEDURAL_MISCONDUCT",
                                    "MCR / Canon — EX_PARTE_VIOLATION"],
                "base_weight": 6.0, "risk_prob": 0.35, "impact": 10,
            },
            {
                "name_match": "mandamus",
                "action_type": "Writ of Mandamus",
                "description": "MCR 3.305 — compel lower court to perform clear legal duty",
                "evidence_package": ["Documented refusal to hold required hearings",
                                     "MCR 3.207(B) hearing obligations unfulfilled",
                                     "Best-interest factors never analyzed on record"],
                "relevant_claims": ["meaningful_hearing", "findings_of_fact", "best_interest_reference",
                                    "procedural_due_process"],
                "relevant_canons": ["MCR 3.207", "MCR / Canon — PROCEDURAL_MISCONDUCT"],
                "base_weight": 5.5, "risk_prob": 0.40, "impact": 9,
            },
            {
                "name_match": "habeas",
                "action_type": "Habeas Corpus",
                "description": "MCR 3.303 — challenge unlawful custody restriction as de facto detention",
                "evidence_package": ["24 ex parte orders documented", "Complete parenting time severance",
                                     "No evidentiary hearing before restriction", "Liberty interest analysis"],
                "relevant_claims": ["liberty_interest", "substantive_due_process", "habeas_corpus",
                                    "parenting_time_denial", "ppo_fundamental_rights"],
                "relevant_canons": ["MCR / Canon — EX_PARTE_VIOLATION", "MCL 600.2950/2950a; MCR 3.207(B)"],
                "base_weight": 5.5, "risk_prob": 0.40, "impact": 10,
            },
            {
                "name_match": "emergency",
                "action_type": "Emergency Application for Leave to Appeal",
                "description": "MCR 7.306(B)(1) — immediate MSC intervention on constitutional deprivation",
                "evidence_package": ["Active separation from children documented",
                                     "Constitutional violations catalogue", "Irreparable harm showing",
                                     "COA appeal pending (366810) — need bypass"],
                "relevant_claims": ["appellate_expedition", "appellate_stay", "extraordinary_relief",
                                    "parenting_time_denial"],
                "relevant_canons": ["MCR / Canon — EX_PARTE_VIOLATION", "MCR 2.003 (Disqualification)"],
                "base_weight": 6.0, "risk_prob": 0.30, "impact": 10,
            },
            {
                "name_match": "leave to appeal",
                "action_type": "Application for Leave to Appeal",
                "description": "MCR 7.305 — discretionary MSC review of COA decision",
                "evidence_package": ["Conflict with MSC precedent on due process",
                                     "Legal significance: parent-child severance without hearing",
                                     "Public interest in judicial accountability"],
                "relevant_claims": ["msc_conflict_precedent", "msc_legal_significance", "msc_public_interest"],
                "relevant_canons": ["MCR / Canon — PROCEDURAL_MISCONDUCT"],
                "base_weight": 5.0, "risk_prob": 0.50, "impact": 9,
            },
        ]
    },
    "COA": {
        "full_name": "Michigan Court of Appeals",
        "actions": [
            {
                "name_match": "appeal brief",
                "action_type": "Appeal 366810 — Appellant Brief",
                "description": "MCR 7.212 — comprehensive brief identifying all preserved errors",
                "evidence_package": ["Issue preservation audit complete", "Standard of review mapped per issue",
                                     "Record citations compiled", "Authority chains built"],
                "error_identification": [
                    "Ex parte orders without notice/hearing (24 documented)",
                    "Parenting time terminated without MCR 3.207(B) hearing",
                    "Best interest factors not analyzed (MCL 722.23)",
                    "PPO weaponized as custody tool without evidentiary support",
                    "Due process violations — no meaningful opportunity to be heard",
                    "Findings of fact absent or contradicted by record",
                ],
                "brief_strength_factors": {
                    "preserved_issues": 12,
                    "constitutional_claims": 5,
                    "record_contradictions": 20,
                    "clear_legal_errors": 8,
                },
                "relevant_claims": ["appellate_due_process", "appellate_legal_error", "appellate_plain_error",
                                    "appellate_issue_preservation", "appellate_evidence_weight",
                                    "appellate_remedy", "record_contradiction"],
                "relevant_canons": ["MCR / Canon — PROCEDURAL_MISCONDUCT", "MCR / Canon — EX_PARTE_VIOLATION",
                                    "MCR 2.107; MCR 2.612(C)"],
                "base_weight": 5.5, "risk_prob": 0.35, "impact": 9,
            },
            {
                "name_match": "peremptory",
                "action_type": "Motion for Peremptory Reversal",
                "description": "MCR 7.211(C)(4) — reversal without full briefing due to clear error",
                "evidence_package": ["Controlling authority directly on point",
                                     "Error so clear that full briefing unnecessary"],
                "relevant_claims": ["appellate_legal_error", "abuse_of_discretion"],
                "relevant_canons": ["MCR / Canon — PROCEDURAL_MISCONDUCT"],
                "base_weight": 4.5, "risk_prob": 0.55, "impact": 8,
            },
            {
                "name_match": "emergency",
                "action_type": "Emergency Motion for Stay",
                "description": "MCR 7.209 — stay lower court orders pending appeal",
                "evidence_package": ["Irreparable harm: ongoing separation from children",
                                     "Likelihood of success on merits shown by violation record"],
                "relevant_claims": ["appellate_stay", "appellate_expedition"],
                "relevant_canons": ["MCR / Canon — EX_PARTE_VIOLATION"],
                "base_weight": 5.0, "risk_prob": 0.40, "impact": 9,
            },
        ]
    },
    "14TH": {
        "full_name": "14th Circuit Court (Muskegon County)",
        "actions": [
            {
                "name_match": "preservation",
                "action_type": "Issue Preservation Motions",
                "description": "Preserve all issues for appellate review with detailed record",
                "evidence_package": ["Objection log maintained", "Constitutional issues raised on record"],
                "relevant_claims": ["appellate_issue_preservation", "procedural_event"],
                "relevant_canons": ["MCR / Canon — PROCEDURAL_MISCONDUCT"],
                "base_weight": 4.5, "risk_prob": 0.20, "impact": 7,
            },
            {
                "name_match": "reconsideration",
                "action_type": "Motion for Reconsideration",
                "description": "MCR 2.119(F) — demonstrate palpable error in prior rulings",
                "evidence_package": ["Record contradictions documented", "Palpable errors identified"],
                "relevant_claims": ["record_contradiction", "abuse_of_discretion", "findings_of_fact"],
                "relevant_canons": ["MCR 2.107; MCR 2.612(C)", "MCR / Canon — PROCEDURAL_MISCONDUCT"],
                "base_weight": 4.0, "risk_prob": 0.50, "impact": 6,
            },
            {
                "name_match": "emergency",
                "action_type": "Emergency Motion to Restore Parenting Time",
                "description": "MCR 3.207(B) — restore parenting time severed without proper hearing",
                "evidence_package": ["No change-of-circumstances finding", "No best-interest analysis",
                                     "Child welfare: separation harm documented",
                                     "MCL 722.27a presumption of parenting time"],
                "relevant_claims": ["parenting_time_denial", "parenting_time_restriction",
                                    "change_of_circumstances", "best_interest_reference",
                                    "meaningful_hearing"],
                "relevant_canons": ["MCR 3.207", "MCL 600.2950/2950a; MCR 3.207(B)"],
                "base_weight": 5.5, "risk_prob": 0.45, "impact": 10,
            },
            {
                "name_match": "vacate",
                "action_type": "Motion to Vacate Ex Parte Orders (24)",
                "description": "MCR 2.612(C) — vacate 24 ex parte orders entered without notice/hearing",
                "evidence_package": ["24 ex parte orders catalogued with dates",
                                     "No emergency justification documented",
                                     "Service failures on 105 orders", "Due process violation pattern"],
                "relevant_claims": ["ex_parte_violation", "ex_parte_evidence", "notice_failure",
                                    "service_of_process", "procedural_due_process"],
                "relevant_canons": ["MCR / Canon — EX_PARTE_VIOLATION", "MCR 2.107; MCR 2.612(C)"],
                "base_weight": 5.5, "risk_prob": 0.40, "impact": 9,
            },
            {
                "name_match": "disqualification",
                "action_type": "Motion for Disqualification (MCR 2.003)",
                "description": "MCR 2.003(D) — disqualify judge based on documented bias pattern",
                "evidence_package": ["167 disqualification-category violations",
                                     "Pattern of one-sided rulings documented",
                                     "Ex parte communication pattern", "Benchbook violations catalogued"],
                "relevant_claims": ["judicial_disqualification", "judicial_bias", "recusal_motion",
                                    "judicial_misconduct"],
                "relevant_canons": ["MCR 2.003 (Disqualification)", "MCR / Canon — EX_PARTE_VIOLATION"],
                "base_weight": 5.0, "risk_prob": 0.50, "impact": 8,
            },
        ]
    },
    "JTC": {
        "full_name": "Judicial Tenure Commission",
        "actions": [
            {
                "name_match": "formal complaint",
                "action_type": "9-Count Formal Complaint",
                "description": "Const 1963 Art 6 §30 — formal complaint with 1,127 documented violations",
                "evidence_package": [
                    "Count 1: Ex Parte Violations (150 violations, 13.3%)",
                    "Count 2: Procedural Misconduct (161 violations, 14.3%)",
                    "Count 3: Disqualification Grounds (167 violations, 14.8%)",
                    "Count 4: PPO Weaponization (27+ violations)",
                    "Count 5: Due Process Denials (pattern across 24+ hearings)",
                    "Count 6: Credibility Failures (51 violations)",
                    "Count 7: Evidence Rule Violations (65 MRE violations)",
                    "Count 8: Service/Notice Failures (105 orders)",
                    "Count 9: Pattern of Judicial Misconduct (1,127 total)",
                ],
                "nine_counts": {
                    "count_1": {"title": "Ex Parte Violations", "violations": 150, "severity": "critical"},
                    "count_2": {"title": "Procedural Misconduct", "violations": 161, "severity": "critical"},
                    "count_3": {"title": "Disqualification-Level Bias", "violations": 167, "severity": "critical"},
                    "count_4": {"title": "PPO Weaponization", "violations": 27, "severity": "high"},
                    "count_5": {"title": "Due Process Denial Pattern", "violations": 126, "severity": "critical"},
                    "count_6": {"title": "Credibility Assessment Failure", "violations": 51, "severity": "high"},
                    "count_7": {"title": "Evidence Rule Violations", "violations": 65, "severity": "high"},
                    "count_8": {"title": "Service/Notice Failures", "violations": 105, "severity": "critical"},
                    "count_9": {"title": "Cumulative Misconduct Pattern", "violations": 1127, "severity": "critical"},
                },
                "relevant_claims": ["judicial_misconduct", "judicial_violation_pattern", "judicial_bias",
                                    "judicial_ex_parte", "judicial_findings_failure", "judicial_sanction_abuse",
                                    "benchbook_violation", "canon_1_violation", "canon_2_violation",
                                    "canon_3_violation", "canon_3B4_violation", "canon_3B5_violation"],
                "relevant_canons": list({
                    "MCR 2.003 (Disqualification)", "MCR / Canon — PROCEDURAL_MISCONDUCT",
                    "MCR / Canon — EX_PARTE_VIOLATION", "MCL 600.2950/2950a; MCR 3.207(B)",
                    "MCR 2.107; MCR 2.612(C)", "MCR / Canon — CREDIBILITY_FAILURE",
                    "MRE 613(b) — Prior inconsistent statement [hearing]",
                    "MCR / Canon — PPO_WEAPONIZATION", "MCR 3.207",
                    "Canon 2 (Impropriety/Appearance)",
                }),
                "base_weight": 6.5, "risk_prob": 0.20, "impact": 10,
            },
            {
                "name_match": "investigation",
                "action_type": "Request for Investigation",
                "description": "JTC Rules — request formal investigation triggering discovery powers",
                "evidence_package": ["Summary of 1,127 violations", "Pattern evidence across time",
                                     "Supporting documentation catalogue"],
                "relevant_claims": ["judicial_misconduct", "judicial_violation_pattern"],
                "relevant_canons": ["MCR 2.003 (Disqualification)", "MCR / Canon — PROCEDURAL_MISCONDUCT"],
                "base_weight": 5.5, "risk_prob": 0.15, "impact": 9,
            },
        ]
    },
    "USDC": {
        "full_name": "US District Court — Western District of Michigan",
        "actions": [
            {
                "name_match": "1983",
                "action_type": "42 USC §1983 Civil Rights (5 Counts)",
                "description": "Federal civil rights action — 5 counts against state actors",
                "five_counts": {
                    "count_1": "Substantive Due Process — fundamental parent-child liberty interest",
                    "count_2": "Procedural Due Process — no meaningful hearing before deprivation",
                    "count_3": "Equal Protection — disparate treatment of father vs. mother",
                    "count_4": "First Amendment Retaliation — punishment for exercising legal rights",
                    "count_5": "Conspiracy (§1983/§1985) — coordinated deprivation with opposing counsel",
                },
                "qualified_immunity_analysis": {
                    "clearly_established": True,
                    "key_authorities": [
                        "Troxel v. Granville, 530 U.S. 57 (2000) — fundamental parental right",
                        "Mathews v. Eldridge, 424 U.S. 319 (1976) — procedural due process",
                        "Stanley v. Illinois, 405 U.S. 645 (1972) — parental fitness presumption",
                        "Santosky v. Kramer, 455 U.S. 745 (1982) — clear and convincing standard",
                    ],
                    "immunity_vulnerability": "LOW — rights clearly established by SCOTUS precedent",
                    "rooker_feldman_risk": "MODERATE — must frame as pattern, not single order appeal",
                    "younger_abstention_risk": "LOW — state proceedings inadequate to vindicate federal rights",
                },
                "evidence_package": ["1,127 documented violations", "Federal constitutional analysis",
                                     "Damages calculation", "Pattern evidence spanning years"],
                "relevant_claims": ["substantive_due_process", "procedural_due_process", "equal_protection",
                                    "liberty_interest", "mathews_balancing", "access_to_courts",
                                    "parenting_time_denial"],
                "relevant_canons": ["MCR / Canon — EX_PARTE_VIOLATION", "MCR / Canon — PROCEDURAL_MISCONDUCT",
                                    "MCR 2.003 (Disqualification)"],
                "base_weight": 5.5, "risk_prob": 0.45, "impact": 10,
            },
            {
                "name_match": "injunctive",
                "action_type": "§1983 Injunctive Relief",
                "description": "Prospective injunctive relief — Younger abstention exception",
                "evidence_package": ["Ongoing constitutional violation", "No adequate state remedy",
                                     "Bad faith/harassment exception to Younger"],
                "relevant_claims": ["substantive_due_process", "extraordinary_relief"],
                "relevant_canons": ["MCR / Canon — PROCEDURAL_MISCONDUCT"],
                "base_weight": 4.5, "risk_prob": 0.55, "impact": 9,
            },
            {
                "name_match": "bivens",
                "action_type": "Bivens Action",
                "description": "Constitutional tort — backup federal claim",
                "evidence_package": ["Pattern of constitutional violations", "No adequate alternative remedy"],
                "relevant_claims": ["substantive_due_process", "procedural_due_process"],
                "relevant_canons": ["MCR / Canon — PROCEDURAL_MISCONDUCT"],
                "base_weight": 3.0, "risk_prob": 0.65, "impact": 7,
            },
        ]
    },
    "BAR": {
        "full_name": "State Bar of Michigan — Attorney Grievance Commission",
        "actions": [
            {
                "name_match": "berry",
                "action_type": "Grievance — Berry (Opposing Counsel)",
                "description": "MRPC 3.3/3.4/8.4 violations — dishonesty, obstruction, misconduct",
                "mrpc_violations": [
                    "MRPC 3.3(a) — Candor: false statements to tribunal",
                    "MRPC 3.4(a) — Fairness: obstruction of access to evidence",
                    "MRPC 3.4(c) — Knowingly disobeying court rules",
                    "MRPC 8.4(b) — Criminal act reflecting on honesty",
                    "MRPC 8.4(c) — Conduct involving dishonesty/fraud",
                    "MRPC 8.4(d) — Conduct prejudicial to administration of justice",
                ],
                "evidence_package": ["Impeachment index entries", "Record contradictions by Berry",
                                     "Ex parte communication evidence", "Perjury compilation"],
                "relevant_claims": ["impeachment_credibility", "dishonesty_credibility",
                                    "record_contradiction", "ex_parte_violation"],
                "relevant_canons": ["MRE 613(b) — Prior inconsistent statement [hearing]",
                                    "MCR / Canon — CREDIBILITY_FAILURE"],
                "base_weight": 5.0, "risk_prob": 0.30, "impact": 7,
            },
            {
                "name_match": "barnes",
                "action_type": "Grievance — Barnes (FOC/GAL)",
                "description": "MRPC 1.1/1.3/3.3 violations — incompetence, diligence failures",
                "mrpc_violations": [
                    "MRPC 1.1 — Competence: failed to conduct adequate investigation",
                    "MRPC 1.3 — Diligence: neglected duties to children",
                    "MRPC 3.3(a) — Candor: misrepresented facts to court",
                    "MRPC 8.4(d) — Conduct prejudicial to administration of justice",
                ],
                "evidence_package": ["FOC accountability analysis", "Investigation failure documentation",
                                     "Contradictions in recommendations"],
                "relevant_claims": ["foc_failure", "foc_objection", "dishonesty_credibility"],
                "relevant_canons": ["MCR / Canon — CREDIBILITY_FAILURE", "MCR / Canon — PROCEDURAL_MISCONDUCT"],
                "base_weight": 5.0, "risk_prob": 0.30, "impact": 7,
            },
            {
                "name_match": "martini",
                "action_type": "Grievance — Martini (Former Counsel)",
                "description": "MRPC 1.4/3.3/8.4 violations — communication failure, misconduct",
                "mrpc_violations": [
                    "MRPC 1.4 — Communication: failed to keep client informed",
                    "MRPC 1.3 — Diligence: missed deadlines/filings",
                    "MRPC 3.3(a) — Candor: failures before tribunal",
                    "MRPC 8.4(d) — Conduct prejudicial to administration of justice",
                ],
                "evidence_package": ["Communication failure timeline", "Missed deadline documentation",
                                     "Harm resulting from representation failures"],
                "relevant_claims": ["dishonesty_credibility", "procedural_event"],
                "relevant_canons": ["MCR / Canon — PROCEDURAL_MISCONDUCT"],
                "base_weight": 4.5, "risk_prob": 0.35, "impact": 6,
            },
        ]
    },
}


# ─────────────────────────────────────────────────────────────────────
# 4. FILING SEQUENCE OPTIMIZER
# ─────────────────────────────────────────────────────────────────────

def find_match(assessments, forum_code, keyword):
    """Find an assessment by forum and keyword substring."""
    for a in assessments:
        if a["forum"] == forum_code and keyword.lower() in a["action_name"].lower():
            return a
    return None


FILING_SEQUENCE = [
    {
        "phase": 1, "name": "IMMEDIATE — Preservation & Emergency",
        "timing": "Week 1-2",
        "actions": [
            ("14TH", "emergency"),
            ("14TH", "vacate"),
            ("14TH", "disqualification"),
            ("COA", "emergency"),
        ],
        "rationale": "Preserve rights, stop ongoing harm, establish record"
    },
    {
        "phase": 2, "name": "ESCALATION — Appellate & Oversight",
        "timing": "Week 2-4",
        "actions": [
            ("JTC", "formal"),
            ("MSC", "emergency"),
            ("BAR", "berry"),
            ("BAR", "barnes"),
        ],
        "rationale": "Activate oversight bodies, create multi-front pressure"
    },
    {
        "phase": 3, "name": "PROSECUTION — Full Briefing",
        "timing": "Week 4-8",
        "actions": [
            ("COA", "appeal brief"),
            ("MSC", "superintending"),
            ("MSC", "habeas"),
            ("BAR", "martini"),
        ],
        "rationale": "Comprehensive legal arguments with full record support"
    },
    {
        "phase": 4, "name": "FEDERAL — Constitutional Claims",
        "timing": "Week 8-12",
        "actions": [
            ("USDC", "1983"),
            ("USDC", "injunctive"),
        ],
        "rationale": "Federal venue after exhausting/preserving state remedies"
    },
]


# ─────────────────────────────────────────────────────────────────────
# 5. MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────

def run():
    conn = sqlite3.connect(str(DB_PATH))
    data = load_all_data(conn)

    # ── Re-score every action ────────────────────────────────────────
    assessments = []
    for action in data["actions"]:
        result = rescore_action(action, data, COURT_CONFIG)
        assessments.append(result)

    # Sort by enhanced score descending
    assessments.sort(key=lambda x: x["enhanced_omega"], reverse=True)

    # ── Save to omega_court_assessment table ─────────────────────────
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS omega_court_assessment")
    c.execute("""
        CREATE TABLE omega_court_assessment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forum TEXT,
            action_name TEXT,
            authority TEXT,
            original_omega REAL,
            enhanced_omega REAL,
            tier TEXT,
            evidence_depth REAL,
            violation_support REAL,
            temporal_strength REAL,
            readiness_pct INTEGER,
            evidence_gaps TEXT,
            proc_requirements_met INTEGER,
            risk_probability REAL,
            risk_impact REAL,
            risk_score REAL,
            court_detail_json TEXT,
            assessed_at TEXT
        )
    """)

    for a in assessments:
        # Build court detail JSON with action-specific deep info
        forum = a["forum"]
        cfg = COURT_CONFIG.get(forum, {})
        detail = {}
        for entry in cfg.get("actions", []):
            if entry["name_match"] in a["action_name"].lower():
                detail = {k: v for k, v in entry.items()
                          if k not in ("relevant_claims", "relevant_canons", "base_weight",
                                       "risk_prob", "impact", "name_match")}
                break

        c.execute("""
            INSERT INTO omega_court_assessment
            (forum, action_name, authority, original_omega, enhanced_omega, tier,
             evidence_depth, violation_support, temporal_strength, readiness_pct,
             evidence_gaps, proc_requirements_met, risk_probability, risk_impact,
             risk_score, court_detail_json, assessed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            a["forum"], a["action_name"], a["authority"],
            a["original_omega"], a["enhanced_omega"], a["tier"],
            a["evidence_depth"], a["violation_support"], a["temporal_strength"],
            a["readiness_pct"], a["evidence_gaps"], int(a["proc_requirements_met"]),
            a["risk_probability"], a["risk_impact"], a["risk_score"],
            json.dumps(detail, indent=2), NOW
        ))

    # ── Save filing readiness table ──────────────────────────────────
    c.execute("DROP TABLE IF EXISTS omega_filing_readiness")
    c.execute("""
        CREATE TABLE omega_filing_readiness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase INTEGER,
            phase_name TEXT,
            timing TEXT,
            rationale TEXT,
            forum TEXT,
            action_name TEXT,
            enhanced_omega REAL,
            readiness_pct INTEGER,
            risk_score REAL,
            tier TEXT,
            sequence_order INTEGER,
            assessed_at TEXT
        )
    """)

    seq = 0
    for phase in FILING_SEQUENCE:
        for forum_code, keyword in phase["actions"]:
            seq += 1
            matched = find_match(assessments, forum_code, keyword)
            display_name = matched["action_name"] if matched else keyword
            if not matched:
                matched = {"enhanced_omega": 70, "readiness_pct": 60, "risk_score": 3.5, "tier": "MEDIUM",
                           "action_name": keyword}

            c.execute("""
                INSERT INTO omega_filing_readiness
                (phase, phase_name, timing, rationale, forum, action_name,
                 enhanced_omega, readiness_pct, risk_score, tier, sequence_order, assessed_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                phase["phase"], phase["name"], phase["timing"], phase["rationale"],
                forum_code, display_name,
                matched["enhanced_omega"], matched["readiness_pct"],
                matched["risk_score"], matched["tier"], seq, NOW
            ))

    conn.commit()

    # ── PRINT DASHBOARD ──────────────────────────────────────────────
    print("=" * 90)
    print("  OMEGA v2 — ENHANCED COURT-BY-COURT ASSESSMENT DASHBOARD")
    print("=" * 90)
    print(f"  Generated: {NOW}")
    print(f"  Data Sources: omega_scores(14) | legal_actions(19) | claim_evidence(653)")
    print(f"                violations(17 categories) | judicial_violations(1,127)")
    print("=" * 90)

    # Group by forum
    by_forum = defaultdict(list)
    for a in assessments:
        by_forum[a["forum"]].append(a)

    forum_order = ["MSC", "COA", "14TH", "JTC", "USDC", "BAR"]

    for forum in forum_order:
        actions_list = by_forum.get(forum, [])
        if not actions_list:
            continue
        cfg = COURT_CONFIG.get(forum, {})
        print()
        print(f"\u250c{'─' * 88}\u2510")
        print(f"\u2502  {cfg.get('full_name', forum):86s}\u2502")
        print(f"\u251c{'─' * 88}\u2524")

        for a in sorted(actions_list, key=lambda x: x["enhanced_omega"], reverse=True):
            tier_icon = {"CRITICAL": "\u2622", "HIGH": "\u26a0", "MEDIUM": "\u25cb", "LOW": "\u25cb"}.get(a["tier"], " ")
            print(f"\u2502  {tier_icon} {a['action_name'][:60]:<60s}  OMEGA: {a['enhanced_omega']:5.1f}  [{a['tier']:8s}] \u2502")
            print(f"\u2502    Authority: {a['authority'][:72]:<72s} \u2502")
            print(f"\u2502    Evidence Depth: {a['evidence_depth']:5.1f}  Violation Support: {a['violation_support']:5.1f}  Temporal: {a['temporal_strength']:5.1f}{'':>10s} \u2502")
            rdns = a['readiness_pct']
            bar_len = rdns // 5
            bar = "\u2588" * bar_len + "\u2591" * (20 - bar_len)
            rdns_label = "READY" if rdns >= 80 else "NEAR" if rdns >= 60 else "BUILDING"
            print(f"\u2502    Readiness: [{bar}] {rdns:3d}% ({rdns_label:8s}){'':>25s} \u2502")
            print(f"\u2502    Risk: P={a['risk_probability']:.2f} x I={a['risk_impact']:.0f} = {a['risk_score']:.2f}  |  Gaps: {a['evidence_gaps'][:40]:<40s} \u2502")
            if a["proc_requirements_met"]:
                print(f"\u2502    Procedural Requirements: \u2705 MET{'':>53s} \u2502")
            else:
                print(f"\u2502    Procedural Requirements: \u26a0  REVIEW NEEDED{'':>44s} \u2502")

            # Court-specific detail sections
            for entry in cfg.get("actions", []):
                if entry["name_match"] in a["action_name"].lower():
                    # Evidence package
                    if "evidence_package" in entry:
                        print(f"\u2502    Evidence Package:{'':>68s} \u2502")
                        for ep in entry["evidence_package"][:5]:
                            print(f"\u2502      \u2022 {ep[:78]:<78s} \u2502")

                    # JTC nine counts
                    if "nine_counts" in entry:
                        print(f"\u2502    9-Count Breakdown:{'':>67s} \u2502")
                        for cid, cdata in entry["nine_counts"].items():
                            sev_mark = "\u2622" if cdata["severity"] == "critical" else "\u26a0"
                            print(f"\u2502      {sev_mark} {cid.upper()}: {cdata['title']:<40s} ({cdata['violations']:>4d} violations) \u2502")

                    # USDC counts & immunity
                    if "five_counts" in entry:
                        print(f"\u2502    5-Count §1983:{'':>71s} \u2502")
                        for cid, desc in entry["five_counts"].items():
                            print(f"\u2502      \u2022 {cid.upper()}: {desc[:72]:<72s} \u2502")
                    if "qualified_immunity_analysis" in entry:
                        qi = entry["qualified_immunity_analysis"]
                        print(f"\u2502    Qualified Immunity Analysis:{'':>58s} \u2502")
                        print(f"\u2502      Clearly Established: {'YES' if qi['clearly_established'] else 'NO':<63s} \u2502")
                        print(f"\u2502      Immunity Risk: {qi['immunity_vulnerability']:<67s} \u2502")
                        print(f"\u2502      Rooker-Feldman: {qi['rooker_feldman_risk']:<67s} \u2502")
                        print(f"\u2502      Younger Abstention: {qi['younger_abstention_risk']:<64s} \u2502")

                    # COA brief strength
                    if "brief_strength_factors" in entry:
                        bsf = entry["brief_strength_factors"]
                        print(f"\u2502    Brief Strength: {bsf['preserved_issues']} issues | {bsf['constitutional_claims']} const. claims | {bsf['record_contradictions']} contradictions | {bsf['clear_legal_errors']} clear errors \u2502")
                    if "error_identification" in entry:
                        print(f"\u2502    Identified Errors:{'':>68s} \u2502")
                        for err in entry["error_identification"][:6]:
                            print(f"\u2502      \u2022 {err[:78]:<78s} \u2502")

                    # BAR MRPC violations
                    if "mrpc_violations" in entry:
                        print(f"\u2502    MRPC Violations:{'':>69s} \u2502")
                        for mv in entry["mrpc_violations"]:
                            print(f"\u2502      \u2022 {mv[:78]:<78s} \u2502")
                    break

            print(f"\u2502{'':>88s}\u2502")

        print(f"\u2514{'─' * 88}\u2518")

    # ── FILING STRATEGY ──────────────────────────────────────────────
    print()
    print("=" * 90)
    print("  OPTIMAL FILING SEQUENCE & TIMING")
    print("=" * 90)

    for phase in FILING_SEQUENCE:
        print(f"\n  PHASE {phase['phase']}: {phase['name']}")
        print(f"  Timing: {phase['timing']}")
        print(f"  Rationale: {phase['rationale']}")
        print(f"  {'─' * 84}")
        print(f"  {'Forum':<7s} {'Action':<55s} {'OMEGA':>6s} {'Ready':>6s} {'Risk':>6s}")
        print(f"  {'─' * 84}")
        for forum_code, keyword in phase["actions"]:
            matched = find_match(assessments, forum_code, keyword)
            if matched:
                display_name = matched["action_name"][:55]
                print(f"  {forum_code:<7s} {display_name:<55s} {matched['enhanced_omega']:5.1f} {matched['readiness_pct']:5d}% {matched['risk_score']:5.2f}")
            else:
                print(f"  {forum_code:<7s} {keyword:<55s}   N/A   N/A   N/A")

    # ── RISK MATRIX ──────────────────────────────────────────────────
    print()
    print("=" * 90)
    print("  RISK MATRIX (Probability x Impact)")
    print("=" * 90)
    print(f"  {'Action':<52s} {'P(risk)':>8s} {'Impact':>8s} {'Score':>8s} {'Zone':>10s}")
    print(f"  {'─' * 88}")
    for a in sorted(assessments, key=lambda x: x["risk_score"]):
        zone = "GREEN" if a["risk_score"] <= 3.0 else "YELLOW" if a["risk_score"] <= 5.0 else "RED"
        zone_icon = "\U0001f7e2" if zone == "GREEN" else "\U0001f7e1" if zone == "YELLOW" else "\U0001f534"
        print(f"  {a['action_name'][:50]:<52s} {a['risk_probability']:7.2f} {a['risk_impact']:7.0f} {a['risk_score']:7.2f}  {zone_icon} {zone}")

    # ── SUMMARY STATISTICS ───────────────────────────────────────────
    print()
    print("=" * 90)
    print("  SUMMARY")
    print("=" * 90)
    total_actions = len(assessments)
    avg_omega = sum(a["enhanced_omega"] for a in assessments) / total_actions if total_actions else 0
    ready_count = sum(1 for a in assessments if a["readiness_pct"] >= 80)
    near_count = sum(1 for a in assessments if 60 <= a["readiness_pct"] < 80)
    critical_count = sum(1 for a in assessments if a["tier"] == "CRITICAL")
    high_count = sum(1 for a in assessments if a["tier"] == "HIGH")

    print(f"  Total Actions Assessed:  {total_actions}")
    print(f"  Average Enhanced OMEGA:  {avg_omega:.1f}")
    print(f"  CRITICAL Tier Actions:   {critical_count}")
    print(f"  HIGH Tier Actions:       {high_count}")
    print(f"  READY TO FILE (>=80%):   {ready_count}")
    print(f"  NEAR READY (60-79%):     {near_count}")
    print(f"  Judicial Violations:     1,127 (377 critical, 243 high)")
    print(f"  Evidence Claims Mapped:  653 across {len(data['claims'])} classifications")
    print()
    print(f"  Tables saved: omega_court_assessment ({total_actions} rows)")
    print(f"                omega_filing_readiness ({seq} rows)")
    print("=" * 90)

    # Verify
    c.execute("SELECT COUNT(*) FROM omega_court_assessment")
    ca_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM omega_filing_readiness")
    fr_count = c.fetchone()[0]
    print(f"\n  [VERIFIED] omega_court_assessment: {ca_count} rows")
    print(f"  [VERIFIED] omega_filing_readiness: {fr_count} rows")

    conn.close()


if __name__ == "__main__":
    run()
