#!/usr/bin/env python3
"""Accountability Campaign — JTC, State Bar, media strategy, and legislative advocacy tracker."""
import sys, sqlite3, json
from datetime import datetime
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ── JTC Complaint Tracker ──────────────────────────────────────────────────

def jtc_status(conn):
    """Judicial Tenure Commission complaint tracker for Judge McNeill."""
    cur = conn.execute(
        "SELECT COUNT(*) as cnt FROM judicial_violations WHERE judge_name LIKE '%McNeill%'")
    total = cur.fetchone()["cnt"]

    cur = conn.execute(
        "SELECT canon_number, COUNT(*) as cnt FROM judicial_violations "
        "WHERE judge_name LIKE '%McNeill%' GROUP BY canon_number ORDER BY cnt DESC")
    canons = cur.fetchall()

    cur = conn.execute(
        "SELECT severity, COUNT(*) as cnt FROM judicial_violations "
        "WHERE judge_name LIKE '%McNeill%' AND severity IS NOT NULL "
        "GROUP BY severity ORDER BY cnt DESC")
    severities = cur.fetchall()

    # Constitutional violations involving McNeill
    cur = conn.execute(
        "SELECT amendment, violation_type, COUNT(*) as cnt FROM constitutional_violations "
        "WHERE actors LIKE '%McNeill%' GROUP BY amendment, violation_type ORDER BY cnt DESC")
    const_v = cur.fetchall()

    return {
        "target": "Hon. Jenny L. McNeill",
        "total_violations": total,
        "canons_violated": [(r["canon_number"], r["cnt"]) for r in canons],
        "severity_breakdown": [(r["severity"], r["cnt"]) for r in severities],
        "constitutional_violations": [(r["amendment"], r["violation_type"], r["cnt"]) for r in const_v],
        "filing_status": "EVIDENCE COMPILED — ready for formal complaint",
        "venue": "Michigan Judicial Tenure Commission",
    }

# ── State Bar Complaint Tracker ────────────────────────────────────────────

def bar_status(conn, respondent):
    """State Bar complaint tracker for a specific respondent attorney."""
    cur = conn.execute(
        "SELECT violation_type, COUNT(*) as cnt FROM actor_violations "
        "WHERE actor=? GROUP BY violation_type ORDER BY cnt DESC", (respondent,))
    violations = cur.fetchall()

    cur = conn.execute(
        "SELECT severity, COUNT(*) as cnt FROM actor_violations "
        "WHERE actor=? AND severity IS NOT NULL "
        "GROUP BY severity ORDER BY cnt DESC", (respondent,))
    severities = cur.fetchall()

    cur = conn.execute(
        "SELECT COUNT(*) as cnt FROM actor_violations WHERE actor=?", (respondent,))
    total = cur.fetchone()["cnt"]

    # Berry-specific ethics violations
    ethics_count = 0
    if respondent == "Berry":
        cur = conn.execute("SELECT COUNT(*) as cnt FROM berry_ethics_violations")
        ethics_count = cur.fetchone()["cnt"]

    # Evidence strength heuristic
    if total > 100:
        strength = "VERY STRONG"
    elif total > 30:
        strength = "STRONG"
    elif total > 10:
        strength = "MODERATE"
    else:
        strength = "DEVELOPING"

    return {
        "respondent": respondent,
        "total_violations": total,
        "ethics_violations": ethics_count,
        "violation_types": [(r["violation_type"], r["cnt"]) for r in violations[:10]],
        "severity_breakdown": [(r["severity"], r["cnt"]) for r in severities],
        "evidence_strength": strength,
        "filing_status": "EVIDENCE COMPILED" if total > 20 else "GATHERING EVIDENCE",
        "venue": "Attorney Grievance Commission (Michigan)",
    }

# ── Media Strategy ─────────────────────────────────────────────────────────

def media_strategy(conn, adversaries):
    """Outline media strategy (when legally appropriate)."""
    strategies = []

    # Count total documented violations
    cur = conn.execute("SELECT COUNT(*) as cnt FROM actor_violations")
    total_violations = cur.fetchone()["cnt"]

    cur = conn.execute("SELECT COUNT(*) as cnt FROM judicial_violations")
    judicial_v = cur.fetchone()["cnt"]

    strategies.append({
        "channel": "Public Records / FOIA",
        "status": "AVAILABLE",
        "note": "All court filings are public record; FOIA for government communications",
    })
    strategies.append({
        "channel": "Investigative Journalism",
        "status": "WHEN LEGALLY APPROPRIATE",
        "note": f"Systemic pattern: {total_violations:,} actor violations + {judicial_v:,} judicial violations documented",
    })
    strategies.append({
        "channel": "Advocacy Organizations",
        "status": "AVAILABLE",
        "note": "Family court reform organizations, parental rights groups",
    })
    strategies.append({
        "channel": "Social Media / Public Awareness",
        "status": "AFTER FILINGS COMPLETE",
        "note": "Document systemic issues without prejudicing pending matters",
    })
    return strategies

# ── Legislative Advocacy ───────────────────────────────────────────────────

def legislative_advocacy(conn):
    """Identify systemic issues from violation patterns for legislative advocacy."""
    issues = []

    # Ex parte patterns
    cur = conn.execute(
        "SELECT COUNT(*) as cnt FROM actor_violations WHERE violation_type LIKE '%ex_parte%'")
    ex_parte = cur.fetchone()["cnt"]
    if ex_parte > 0:
        issues.append({
            "issue": "Ex Parte Order Abuse",
            "count": ex_parte,
            "reform": "Mandatory notice + hearing before custody modifications; time limits on ex parte orders",
            "model_legislation": "Require 72-hour hearing after any ex parte custody order",
        })

    # Due process violations
    cur = conn.execute(
        "SELECT COUNT(*) as cnt FROM constitutional_violations "
        "WHERE amendment LIKE '%14th%' AND violation_type LIKE '%DUE_PROCESS%'")
    dp = cur.fetchone()["cnt"]
    if dp > 0:
        issues.append({
            "issue": "Due Process Violations in Family Court",
            "count": dp,
            "reform": "Recorded hearings mandatory; written findings required for all custody changes",
            "model_legislation": "Family Court Transparency Act — require transcripts + findings of fact",
        })

    # Parental alienation as weapon
    cur = conn.execute(
        "SELECT COUNT(*) as cnt FROM actor_violations "
        "WHERE violation_type LIKE '%alienat%' OR description LIKE '%alienat%'")
    alien = cur.fetchone()["cnt"]
    if alien > 0:
        issues.append({
            "issue": "Weaponized Alienation Claims",
            "count": alien,
            "reform": "Evidence-based standards for alienation findings; prohibition on unsubstantiated claims",
            "model_legislation": "Require peer-reviewed methodology for any alienation determination",
        })

    # Judicial accountability gaps
    cur = conn.execute(
        "SELECT COUNT(DISTINCT judge_name) as cnt FROM judicial_violations")
    judges = cur.fetchone()["cnt"]
    issues.append({
        "issue": "Judicial Accountability Gaps",
        "count": judges,
        "reform": "Strengthen JTC enforcement; mandatory recusal standards; public complaint tracking",
        "model_legislation": "Judicial Accountability Act — public database of JTC complaints + outcomes",
    })

    return issues

# ── Save to Database ───────────────────────────────────────────────────────

def save_accountability(conn, jtc, bar_data, media, legislative):
    """Save all accountability data to omega_accountability table."""
    conn.execute("DROP TABLE IF EXISTS omega_accountability")
    conn.execute("""
        CREATE TABLE omega_accountability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            target TEXT,
            metric TEXT NOT NULL,
            value_num REAL,
            value_text TEXT,
            ts TEXT DEFAULT (datetime('now'))
        )
    """)

    def ins(cat, target, metric, vn=None, vt=None):
        conn.execute(
            "INSERT INTO omega_accountability (category, target, metric, value_num, value_text) "
            "VALUES (?,?,?,?,?)", (cat, target, metric, vn, vt))

    # JTC data
    ins("jtc", jtc["target"], "total_violations", jtc["total_violations"])
    ins("jtc", jtc["target"], "filing_status", vt=jtc["filing_status"])
    for canon, cnt in jtc["canons_violated"]:
        ins("jtc", jtc["target"], f"canon_{canon}", cnt)
    for amend, vtype, cnt in jtc["constitutional_violations"]:
        ins("jtc", jtc["target"], f"constitutional_{amend}_{vtype}", cnt)

    # Bar data
    for bd in bar_data:
        ins("bar", bd["respondent"], "total_violations", bd["total_violations"])
        ins("bar", bd["respondent"], "ethics_violations", bd["ethics_violations"])
        ins("bar", bd["respondent"], "evidence_strength", vt=bd["evidence_strength"])
        ins("bar", bd["respondent"], "filing_status", vt=bd["filing_status"])
        for vtype, cnt in bd["violation_types"]:
            ins("bar", bd["respondent"], f"violation_{vtype}", cnt)

    # Media
    for m in media:
        ins("media", None, m["channel"], vt=f"[{m['status']}] {m['note']}")

    # Legislative
    for leg in legislative:
        ins("legislative", None, leg["issue"], leg["count"], leg["reform"])

    conn.commit()

# ── Dashboard ──────────────────────────────────────────────────────────────

def print_dashboard(jtc, bar_data, media, legislative):
    w = 80
    print("\n" + "=" * w)
    print("  OMEGA ACCOUNTABILITY CAMPAIGN DASHBOARD")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * w)

    # JTC Section
    print(f"\n  {'JTC COMPLAINT — ' + jtc['target']:^{w-4}}")
    print("  " + "-" * (w - 4))
    print(f"  Venue:              {jtc['venue']}")
    print(f"  Total violations:   {jtc['total_violations']:,}")
    print(f"  Filing status:      {jtc['filing_status']}")
    print(f"\n  Canon Violations:")
    for canon, cnt in jtc["canons_violated"][:10]:
        print(f"    {canon or 'Unspecified':<45} {cnt:>5}")
    if jtc["severity_breakdown"]:
        print(f"\n  Severity Breakdown:")
        for sev, cnt in jtc["severity_breakdown"]:
            print(f"    {sev or 'Unspecified':<20} {cnt:>5}")
    if jtc["constitutional_violations"]:
        print(f"\n  Constitutional Violations:")
        for amend, vtype, cnt in jtc["constitutional_violations"]:
            print(f"    {amend} — {vtype:<35} {cnt:>3}")

    # State Bar Section
    print(f"\n  {'STATE BAR COMPLAINTS':^{w-4}}")
    print("  " + "-" * (w - 4))
    for bd in bar_data:
        print(f"\n  ▸ Respondent: {bd['respondent']}")
        print(f"    Venue:            {bd['venue']}")
        print(f"    Total violations: {bd['total_violations']:,}")
        if bd["ethics_violations"]:
            print(f"    Ethics (MRPC):    {bd['ethics_violations']:,}")
        print(f"    Evidence strength:{bd['evidence_strength']}")
        print(f"    Filing status:    {bd['filing_status']}")
        print(f"    Top violation types:")
        for vtype, cnt in bd["violation_types"][:5]:
            print(f"      {vtype or '?':<35} {cnt:>5}")
        if bd["severity_breakdown"]:
            print(f"    Severity:")
            for sev, cnt in bd["severity_breakdown"][:5]:
                print(f"      {sev or 'Unspecified':<20} {cnt:>5}")

    # Media Strategy
    print(f"\n  {'MEDIA STRATEGY OUTLINE':^{w-4}}")
    print("  " + "-" * (w - 4))
    for m in media:
        print(f"  [{m['status']:<25}] {m['channel']}")
        print(f"    {m['note']}")

    # Legislative Advocacy
    print(f"\n  {'LEGISLATIVE ADVOCACY — SYSTEMIC ISSUES':^{w-4}}")
    print("  " + "-" * (w - 4))
    for leg in legislative:
        print(f"\n  ▸ {leg['issue']} ({leg['count']} instances)")
        print(f"    Reform:      {leg['reform']}")
        print(f"    Model bill:  {leg['model_legislation']}")

    print("\n" + "=" * w)
    print(f"  Data saved to omega_accountability table ({DB})")
    print("=" * w + "\n")

# ── Main ───────────────────────────────────────────────────────────────────

def main():
    conn = connect()

    jtc = jtc_status(conn)

    respondents = ["Berry", "Barnes", "Martini"]
    bar_data = [bar_status(conn, r) for r in respondents]

    media = media_strategy(conn, respondents)
    legislative = legislative_advocacy(conn)

    save_accountability(conn, jtc, bar_data, media, legislative)
    print_dashboard(jtc, bar_data, media, legislative)

    conn.close()

if __name__ == "__main__":
    main()
