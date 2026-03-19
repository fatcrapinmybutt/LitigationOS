#!/usr/bin/env python3
"""
Enhanced Judicial Analysis Engine — OMEGA Module
Performs deep judicial profiling, legal action discovery, and MCR/MCL rule audit.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# ═══════════════════════════════════════════════════════════════════════════════
# Section 1: Judicial Profiling — McNeill Deep Analysis
# ═══════════════════════════════════════════════════════════════════════════════

def judicial_profiling(conn):
    """Deep analysis of Judge McNeill's violation patterns."""
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    profile = {}

    # --- 1a. Violation patterns: group by type, severity, frequency ---
    cur.execute("""
        SELECT canon_number AS type, severity,
               COUNT(*) AS freq
        FROM judicial_violations
        WHERE judge_name LIKE '%McNeill%'
        GROUP BY canon_number, severity
        ORDER BY freq DESC
    """)
    type_severity = cur.fetchall()

    type_totals = defaultdict(int)
    severity_totals = defaultdict(int)
    type_severity_map = defaultdict(lambda: defaultdict(int))
    for vtype, sev, cnt in type_severity:
        type_totals[vtype] += cnt
        severity_totals[sev] += cnt
        type_severity_map[vtype][sev] = cnt

    profile["violation_by_type"] = dict(type_totals)
    profile["violation_by_severity"] = dict(severity_totals)
    profile["type_severity_matrix"] = {k: dict(v) for k, v in type_severity_map.items()}

    total_violations = sum(type_totals.values())
    profile["total_violations"] = total_violations

    # --- 1b. Ex parte order analysis ---
    cur.execute("""
        SELECT COUNT(*) FROM judicial_violations
        WHERE judge_name LIKE '%McNeill%'
          AND (canon_number LIKE '%EX_PARTE%'
               OR violation_description LIKE '%ex parte%'
               OR canon_number LIKE '%2950%')
    """)
    ex_parte_count = cur.fetchone()[0]
    profile["ex_parte_violations"] = ex_parte_count

    cur.execute("""
        SELECT canon_number, severity, COUNT(*) as cnt
        FROM judicial_violations
        WHERE judge_name LIKE '%McNeill%'
          AND (canon_number LIKE '%EX_PARTE%'
               OR violation_description LIKE '%ex parte%'
               OR canon_number LIKE '%2950%')
        GROUP BY canon_number, severity
        ORDER BY cnt DESC
    """)
    profile["ex_parte_breakdown"] = [
        {"type": r[0], "severity": r[1], "count": r[2]} for r in cur.fetchall()
    ]

    # --- 1c. Bias indicators ---
    cur.execute("""
        SELECT COUNT(*) FROM judicial_violations
        WHERE judge_name LIKE '%McNeill%'
          AND (violation_description LIKE '%bias%'
               OR violation_description LIKE '%favor%'
               OR violation_description LIKE '%one-sided%'
               OR violation_description LIKE '%prejudic%'
               OR canon_number LIKE '%Disqualification%'
               OR canon_number LIKE '%CREDIBILITY%')
    """)
    bias_count = cur.fetchone()[0]
    profile["bias_indicator_count"] = bias_count

    # --- 1d. Procedural shortcut detection ---
    cur.execute("""
        SELECT COUNT(*) FROM judicial_violations
        WHERE judge_name LIKE '%McNeill%'
          AND (violation_description LIKE '%due process%'
               OR violation_description LIKE '%notice%'
               OR violation_description LIKE '%hearing%'
               OR canon_number LIKE '%PROCEDURAL%'
               OR canon_number LIKE '%2.107%'
               OR canon_number LIKE '%2.612%'
               OR canon_number LIKE '%3.207%')
    """)
    procedural_shortcut_count = cur.fetchone()[0]
    profile["procedural_shortcut_count"] = procedural_shortcut_count

    # --- 1e. Judicial misconduct score (0-100) ---
    #  Weighted formula:
    #    critical=4, high=3, medium=2, low=1   max theoretical ~4500
    #    ex_parte factor  (up to +15)
    #    bias factor      (up to +10)
    #    procedural factor(up to +10)
    weighted = (severity_totals.get("critical", 0) * 4
                + severity_totals.get("high", 0) * 3
                + severity_totals.get("medium", 0) * 2
                + severity_totals.get("low", 0) * 1)
    # Normalize weighted to 0-65 range (cap at 3000)
    base_score = min(weighted / 3000 * 65, 65)
    ex_parte_bonus = min(ex_parte_count / total_violations * 15, 15) if total_violations else 0
    bias_bonus = min(bias_count / total_violations * 10, 10) if total_violations else 0
    proc_bonus = min(procedural_shortcut_count / total_violations * 10, 10) if total_violations else 0
    misconduct_score = round(min(base_score + ex_parte_bonus + bias_bonus + proc_bonus, 100), 1)
    profile["misconduct_score"] = misconduct_score

    return profile


# ═══════════════════════════════════════════════════════════════════════════════
# Section 2: Legal Action Discovery
# ═══════════════════════════════════════════════════════════════════════════════

FORUMS = {
    "MSC": {
        "name": "Michigan Supreme Court",
        "filings": [
            ("Emergency Application for Leave to Appeal", "MCR 7.306(B)(1)", "Immediate relief from ongoing harm"),
            ("Complaint for Superintending Control", "Const 1963 Art 6 §4", "Systemic lower-court failure"),
            ("Petition for Habeas Corpus", "MCR 3.303", "Unlawful custody deprivation"),
            ("Writ of Mandamus", "MCR 3.305", "Compel lower court to perform duty"),
        ],
    },
    "COA": {
        "name": "Michigan Court of Appeals",
        "filings": [
            ("Appeal Brief (Case 366810)", "MCR 7.212", "Appeal existing COA case"),
            ("Motion for Peremptory Reversal", "MCR 7.211(C)(4)", "Clear legal error below"),
            ("Emergency Motion for Stay", "MCR 7.209", "Prevent irreparable harm during appeal"),
        ],
    },
    "14TH": {
        "name": "14th Circuit Court",
        "filings": [
            ("Motion to Vacate Ex Parte Orders", "MCR 2.612(C)", "Set aside void/voidable orders"),
            ("Motion for Disqualification", "MCR 2.003(D)", "Judicial bias/prejudice"),
            ("Emergency Motion to Restore Parenting Time", "MCR 3.207(B)", "Best interest of child"),
            ("Motion for Contempt/Sanctions", "MCR 3.606", "Violation of court orders"),
        ],
    },
    "JTC": {
        "name": "Judicial Tenure Commission",
        "filings": [
            ("Formal Complaint (Multi-Count)", "Const 1963 Art 6 §30", "Judicial misconduct/disability"),
            ("Request for Investigation", "JTC Rules", "Pattern of canon violations"),
        ],
    },
    "USDC": {
        "name": "US District Court (Western MI)",
        "filings": [
            ("42 USC §1983 — Civil Rights (Multi-Count)", "42 USC §1983", "Constitutional rights violations"),
            ("§1983 Injunctive Relief", "42 USC §1983", "Prospective relief against state actors"),
            ("Bivens Action", "Bivens v. Six Unknown Agents", "Federal constitutional tort"),
        ],
    },
    "BAR": {
        "name": "State Bar of Michigan",
        "filings": [
            ("Attorney Grievance — Berry", "MRPC 3.3/3.4/8.4", "Attorney misconduct"),
            ("Attorney Grievance — Barnes", "MRPC 1.1/1.3/3.3", "Attorney misconduct"),
            ("Attorney Grievance — Martini", "MRPC 1.4/3.3/8.4", "Attorney misconduct"),
        ],
    },
}


def legal_action_discovery(conn, profile):
    """Cross-reference forums with evidence strength; calculate readiness."""
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    # Get omega_scores for cross-referencing
    cur.execute("SELECT action_id, name, forum, total_score, tier FROM omega_scores")
    omega_map = {}
    for aid, name, forum, score, tier in cur.fetchall():
        omega_map[forum] = omega_map.get(forum, [])
        omega_map[forum].append({"action_id": aid, "name": name, "score": score, "tier": tier})

    # Count supporting evidence per category
    cur.execute("""
        SELECT evidence_category, COUNT(*) FROM evidence_quotes
        GROUP BY evidence_category
    """)
    evidence_counts = dict(cur.fetchall())
    total_evidence = sum(evidence_counts.values())

    # Count supported claims
    cur.execute("SELECT COUNT(*) FROM claims WHERE status='supported'")
    supported_claims = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM claims")
    total_claims = cur.fetchone()[0]
    claim_support_ratio = supported_claims / total_claims if total_claims else 0

    # Create omega_legal_actions table
    cur.execute("DROP TABLE IF EXISTS omega_legal_actions")
    cur.execute("""
        CREATE TABLE omega_legal_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forum TEXT NOT NULL,
            forum_name TEXT,
            filing_name TEXT NOT NULL,
            authority TEXT,
            description TEXT,
            omega_score INTEGER,
            omega_tier TEXT,
            evidence_strength INTEGER,
            readiness_score INTEGER,
            readiness_label TEXT,
            violation_support INTEGER,
            created_at TEXT
        )
    """)

    results = []
    for forum_code, forum_info in FORUMS.items():
        # Get best omega score for this forum
        forum_scores = omega_map.get(forum_code, [])
        best_omega = max((s["score"] for s in forum_scores), default=0)
        best_tier = next((s["tier"] for s in forum_scores if s["score"] == best_omega), "UNSCORED")

        # Evidence strength: based on violation count + evidence volume
        violation_count = profile["total_violations"]
        ev_strength = min(int((violation_count / 1200) * 50 + (total_evidence / 320000) * 50), 100)

        for filing_name, authority, desc in forum_info["filings"]:
            # Readiness: composite of omega score, evidence, claim support
            omega_component = best_omega * 0.4
            evidence_component = ev_strength * 0.3
            claim_component = claim_support_ratio * 100 * 0.3
            readiness = round(min(omega_component + evidence_component + claim_component, 100))

            if readiness >= 80:
                label = "READY TO FILE"
            elif readiness >= 60:
                label = "NEAR READY"
            elif readiness >= 40:
                label = "IN PROGRESS"
            else:
                label = "NEEDS WORK"

            cur.execute("""
                INSERT INTO omega_legal_actions
                (forum, forum_name, filing_name, authority, description,
                 omega_score, omega_tier, evidence_strength, readiness_score,
                 readiness_label, violation_support, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (forum_code, forum_info["name"], filing_name, authority, desc,
                  best_omega, best_tier, ev_strength, readiness,
                  label, violation_count, now))

            results.append({
                "forum": forum_code,
                "filing": filing_name,
                "authority": authority,
                "omega_score": best_omega,
                "evidence_strength": ev_strength,
                "readiness": readiness,
                "label": label,
            })

    conn.commit()
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Section 3: Rule Audit — MCR/MCL Compliance
# ═══════════════════════════════════════════════════════════════════════════════

RULE_REQUIREMENTS = {
    "msc-emergency-app": {
        "name": "MSC Emergency Application",
        "rule": "MCR 7.306(B)(1)",
        "procedures": [
            "File application for leave to appeal with emergency designation",
            "Include motion for immediate consideration",
            "Attach lower court orders being challenged",
            "Include proof of service on all parties",
        ],
        "service": "Personal service or registered mail on all parties; file proof of service",
        "timing": "No fixed deadline — file ASAP; court may act within 21 days",
        "fees": "Filing fee ~$375; fee waiver available via MCR 2.002",
    },
    "msc-superintending": {
        "name": "MSC Superintending Control",
        "rule": "Const 1963 Art 6 §4; MCR 3.302",
        "procedures": [
            "File complaint for superintending control",
            "Demonstrate no adequate legal remedy exists",
            "Show lower court acted beyond jurisdiction or failed mandatory duty",
            "Attach all relevant orders and transcripts",
        ],
        "service": "Service on respondent judge and all parties per MCR 2.105",
        "timing": "No statutory deadline; file when pattern documented",
        "fees": "Filing fee ~$375; fee waiver via MCR 2.002",
    },
    "msc-habeas": {
        "name": "MSC Habeas Corpus",
        "rule": "MCR 3.303; Const 1963 Art 1 §12",
        "procedures": [
            "File petition for writ of habeas corpus",
            "Demonstrate unlawful restraint/deprivation of custody",
            "Show exhaustion of other remedies or explain why impractical",
            "Attach supporting affidavits and evidence",
        ],
        "service": "Service on custodian and opposing party",
        "timing": "Immediate — no fixed deadline for filing",
        "fees": "Filing fee ~$375; fee waiver via MCR 2.002",
    },
    "jtc-formal-complaint": {
        "name": "JTC Formal Complaint (9-Count)",
        "rule": "Const 1963 Art 6 §30; MCR 9.200 et seq.",
        "procedures": [
            "Draft formal written complaint with specific canon violations",
            "Identify each count with dates, actions, and evidence",
            "Attach documentary evidence and sworn statements",
            "Mail to JTC — 3034 W. Grand Blvd, Suite 8-450, Detroit, MI 48202",
        ],
        "service": "File directly with JTC; they handle service on judge",
        "timing": "No statute of limitations for JTC complaints",
        "fees": "No filing fee",
    },
    "usdc-1983-5count": {
        "name": "USDC §1983 (5 Counts)",
        "rule": "42 USC §1983; 28 USC §1343",
        "procedures": [
            "File complaint in US District Court (W.D. Michigan)",
            "Plead deprivation of constitutional rights under color of state law",
            "Identify each defendant and their role",
            "Plead exhaustion of state remedies or Pullman/Younger exceptions",
            "Include demand for damages and injunctive relief",
        ],
        "service": "Federal Rules of Civil Procedure Rule 4 — summons and complaint",
        "timing": "3-year statute of limitations (MCL 600.5805(2) borrowed for §1983)",
        "fees": "Filing fee $405; IFP motion available under 28 USC §1915",
    },
    "14th-vacate-exparte": {
        "name": "Vacate Ex Parte Orders",
        "rule": "MCR 2.612(C)(1); MCR 3.207",
        "procedures": [
            "File motion to set aside void/voidable ex parte orders",
            "Cite MCR 2.612(C)(1)(a)-(f) grounds",
            "Identify each order by date and docket entry",
            "Request evidentiary hearing on contested facts",
        ],
        "service": "Service on opposing counsel per MCR 2.107; 9-day notice period",
        "timing": "Reasonable time; within 1 year for most grounds",
        "fees": "Motion filing fee ~$20; fee waiver via MCR 2.002",
    },
    "14th-disqualification": {
        "name": "Disqualification Motion",
        "rule": "MCR 2.003(D)",
        "procedures": [
            "File motion and affidavit of disqualification",
            "Specify grounds: personal bias, ex parte contacts, appearance of impropriety",
            "Chief judge decides if challenged judge does not recuse",
            "Appeal denial to COA under MCR 7.203",
        ],
        "service": "Serve on all parties and file with court",
        "timing": "File promptly after discovering grounds",
        "fees": "Motion filing fee ~$20",
    },
    "coa-appeal-366810": {
        "name": "COA Appeal 366810 Brief",
        "rule": "MCR 7.212; MCR 7.211",
        "procedures": [
            "File appellant's brief per MCR 7.212 format requirements",
            "Include statement of jurisdiction, questions presented, facts, argument",
            "Attach appendix with relevant orders, opinions, transcripts",
            "File within deadline set by court scheduling order",
        ],
        "service": "Serve on appellee counsel and file proof of service",
        "timing": "Per COA scheduling order; typically 56 days after claim of appeal",
        "fees": "Included in original appeal filing fee",
    },
    "bar-berry": {
        "name": "State Bar Complaint — Berry",
        "rule": "MRPC 3.3/3.4/8.4; MCR 9.100 et seq.",
        "procedures": [
            "File grievance with Attorney Grievance Commission",
            "Detail specific MRPC violations with dates and evidence",
            "Attach documentary proof of misconduct",
            "Mail to AGC — 535 Griswold, Suite 1700, Detroit, MI 48226",
        ],
        "service": "AGC handles service on respondent attorney",
        "timing": "No statute of limitations for attorney grievances",
        "fees": "No filing fee",
    },
}


def rule_audit(conn):
    """For top OMEGA actions, list procedural requirements, service, timing, fees."""
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cur.execute("DROP TABLE IF EXISTS omega_rule_audit")
    cur.execute("""
        CREATE TABLE omega_rule_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id TEXT NOT NULL,
            action_name TEXT,
            rule_citation TEXT,
            procedures TEXT,
            service_requirements TEXT,
            timing_window TEXT,
            fees TEXT,
            omega_score INTEGER,
            omega_tier TEXT,
            created_at TEXT
        )
    """)

    # Get top OMEGA actions
    cur.execute("""
        SELECT action_id, name, total_score, tier
        FROM omega_scores
        ORDER BY total_score DESC
    """)
    actions = cur.fetchall()

    audit_results = []
    for action_id, name, score, tier in actions:
        reqs = RULE_REQUIREMENTS.get(action_id)
        if not reqs:
            continue
        cur.execute("""
            INSERT INTO omega_rule_audit
            (action_id, action_name, rule_citation, procedures,
             service_requirements, timing_window, fees,
             omega_score, omega_tier, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (action_id, reqs["name"], reqs["rule"],
              json.dumps(reqs["procedures"]),
              reqs["service"], reqs["timing"], reqs["fees"],
              score, tier, now))

        audit_results.append({
            "action_id": action_id,
            "name": reqs["name"],
            "rule": reqs["rule"],
            "steps": len(reqs["procedures"]),
            "score": score,
            "tier": tier,
        })

    conn.commit()
    return audit_results


# ═══════════════════════════════════════════════════════════════════════════════
# Section 4: Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

def print_dashboard(profile, legal_actions, audit_results):
    W = 80
    SEP = "=" * W
    THIN = "-" * W

    print(f"\n{SEP}")
    print("  OMEGA ENHANCED JUDICIAL ANALYSIS ENGINE — DASHBOARD")
    print(f"  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(SEP)

    # --- Judicial Profile ---
    print(f"\n{'─'*W}")
    print("  § 1  JUDICIAL PROFILING — Judge Jenny L. McNeill")
    print(f"{'─'*W}")
    print(f"  Total Documented Violations:  {profile['total_violations']}")
    print(f"  Misconduct Score:             {profile['misconduct_score']}/100", end="")
    ms = profile["misconduct_score"]
    if ms >= 80:
        print("  ██████████ EXTREME")
    elif ms >= 60:
        print("  ████████░░ SEVERE")
    elif ms >= 40:
        print("  ██████░░░░ HIGH")
    else:
        print("  ████░░░░░░ MODERATE")

    print(f"\n  Severity Distribution:")
    for sev in ["critical", "high", "medium", "low"]:
        cnt = profile["violation_by_severity"].get(sev, 0)
        pct = cnt / profile["total_violations"] * 100 if profile["total_violations"] else 0
        bar = "█" * int(pct / 2)
        print(f"    {sev.upper():10s}  {cnt:4d}  ({pct:5.1f}%)  {bar}")

    print(f"\n  Top Violation Types:")
    sorted_types = sorted(profile["violation_by_type"].items(), key=lambda x: -x[1])
    for vtype, cnt in sorted_types[:8]:
        pct = cnt / profile["total_violations"] * 100
        print(f"    {cnt:4d}  ({pct:5.1f}%)  {vtype}")

    print(f"\n  Key Indicators:")
    print(f"    Ex Parte Violations:       {profile['ex_parte_violations']:4d}")
    print(f"    Bias Indicators:           {profile['bias_indicator_count']:4d}")
    print(f"    Procedural Shortcuts:      {profile['procedural_shortcut_count']:4d}")

    if profile["ex_parte_breakdown"]:
        print(f"\n  Ex Parte Breakdown:")
        for item in profile["ex_parte_breakdown"][:5]:
            print(f"    {item['count']:4d}  [{item['severity']:8s}]  {item['type']}")

    # --- Legal Action Discovery ---
    print(f"\n{'─'*W}")
    print("  § 2  LEGAL ACTION DISCOVERY — 6 Forums")
    print(f"{'─'*W}")

    current_forum = None
    for la in sorted(legal_actions, key=lambda x: (-x["readiness"], x["forum"])):
        if la["forum"] != current_forum:
            current_forum = la["forum"]
            fname = FORUMS[current_forum]["name"]
            print(f"\n  [{current_forum}] {fname}")
            print(f"  {'Filing':<48s} {'Auth':>12s} {'Rdns':>5s} {'Status'}")
            print(f"  {'─'*48} {'─'*12} {'─'*5} {'─'*15}")
        status_icon = {"READY TO FILE": "✅", "NEAR READY": "🔶", "IN PROGRESS": "🔧", "NEEDS WORK": "⬜"}.get(la["label"], "?")
        print(f"  {la['filing']:<48s} {la['authority']:>12s} {la['readiness']:5d} {status_icon} {la['label']}")

    # --- Rule Audit ---
    print(f"\n{'─'*W}")
    print("  § 3  RULE AUDIT — MCR/MCL Compliance Requirements")
    print(f"{'─'*W}")

    for ar in audit_results:
        print(f"\n  [{ar['tier']}] {ar['name']}  (OMEGA {ar['score']})")
        print(f"    Rule: {ar['rule']}")
        print(f"    Procedural Steps: {ar['steps']}")

    # Lookup full details for top 3
    top3 = audit_results[:3]
    if top3:
        print(f"\n  Detailed Requirements for Top 3 Actions:")
        print(f"  {THIN}")
        for ar in top3:
            reqs = RULE_REQUIREMENTS.get(ar["action_id"], {})
            if not reqs:
                continue
            print(f"\n  ▶ {reqs['name']}  ({reqs['rule']})")
            for i, step in enumerate(reqs["procedures"], 1):
                print(f"    {i}. {step}")
            print(f"    Service: {reqs['service']}")
            print(f"    Timing:  {reqs['timing']}")
            print(f"    Fees:    {reqs['fees']}")

    # --- Summary ---
    print(f"\n{SEP}")
    print("  SUMMARY")
    print(SEP)
    ready = sum(1 for la in legal_actions if la["label"] == "READY TO FILE")
    near = sum(1 for la in legal_actions if la["label"] == "NEAR READY")
    print(f"  Violations cataloged:    {profile['total_violations']}")
    print(f"  Misconduct score:        {profile['misconduct_score']}/100")
    print(f"  Filings mapped:          {len(legal_actions)} across 6 forums")
    print(f"  Ready to file:           {ready}")
    print(f"  Near ready:              {near}")
    print(f"  Rule audits completed:   {len(audit_results)}")
    print(f"  Tables saved:            omega_legal_actions, omega_rule_audit")
    print(SEP)


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    print("Running judicial profiling...")
    profile = judicial_profiling(conn)

    print("Running legal action discovery...")
    legal_actions = legal_action_discovery(conn, profile)

    print("Running rule audit...")
    audit_results = rule_audit(conn)

    print_dashboard(profile, legal_actions, audit_results)

    conn.close()
    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
