"""
Auto-pilot: Monitors A07, then runs K → L → F tiers sequentially.
Launch this and walk away — everything queues up behind A07.

v2.0: Deadline Autopilot extension (ADR-001 Phase 2)
  - deadline_driven_priority(): MCR-aware filing prioritization
  - Filing dependency graph enforcement
  - Recommendation engine: FILE NOW / PREPARE / DEFER / BLOCKED
  Kill switch: LITIGOS_DISABLE_DEADLINE_AUTOPILOT=1
"""
import sys, os, time, json
from datetime import datetime, timedelta
sys.path.insert(0, '.')
os.chdir(r'C:\Users\andre\LitigationOS\00_SYSTEM\pipeline')

from agents.agent_orchestrator import run_tier

TIERS = [
    ("tierK", "K-TIER ANALYSIS", 4),
    ("tierL", "L-TIER SCORING", 4),
    ("convergence", "CONVERGENCE F01-F06", 2),
]

def wait_for_a07():
    """Poll A07 checkpoint until done."""
    cp_path = 'agents/checkpoints/A07-CODE-DEDUP.checkpoint.json'
    while True:
        try:
            d = json.load(open(cp_path))
            p = d.get('processed', 0)
            t = d.get('total', 857028)
            pct = 100 * p / max(t, 1)
            print(f'[AUTOPILOT] A07: {p:,}/{t:,} ({pct:.1f}%)', flush=True)
            if p >= t - 10:  # within 10 of done
                print('[AUTOPILOT] A07 appears complete!', flush=True)
                return
        except Exception as e:
            print(f'[AUTOPILOT] A07 check error: {e}', flush=True)
        time.sleep(60)  # check every 60s

def run_tier_safe(tier_name, label, workers):
    """Run a tier with full error handling."""
    print(f'\n{"="*60}', flush=True)
    print(f'[AUTOPILOT] === {label} ===', flush=True)
    print(f'{"="*60}', flush=True)
    try:
        results = run_tier(tier_name, max_workers=workers)
        for r in results:
            s = r.stats
            status_icon = "✓" if r.status == "SUCCESS" else "✗"
            print(f'  {status_icon} {r.agent_id}: {r.status} '
                  f'[{s.processed}/{s.total} done, {s.skipped} skip, {s.errored} err]',
                  flush=True)
            if r.error:
                print(f'    ERR: {str(r.error)[:200]}', flush=True)
        return results
    except Exception as e:
        print(f'[AUTOPILOT] {label} FAILED: {e}', flush=True)
        return []

if __name__ == '__main__':
    print('[AUTOPILOT] Waiting for A07 to complete before launching K → L → F...', flush=True)
    wait_for_a07()

    # Small delay to let A07 finalize and release DB
    time.sleep(5)

    for tier_name, label, workers in TIERS:
        run_tier_safe(tier_name, label, workers)

    # Final DB stats
    import sqlite3
    db = sqlite3.connect('agents/master_index.db', timeout=30)
    db.execute('PRAGMA busy_timeout=30000')
    print('\n' + '='*60, flush=True)
    print('[AUTOPILOT] === FINAL STATUS ===', flush=True)
    for label, q in [
        ('Files', 'SELECT COUNT(*) FROM files'),
        ('Canonical', 'SELECT COUNT(*) FROM files WHERE is_canonical=1'),
        ('fact_atoms', 'SELECT COUNT(*) FROM fact_atoms'),
        ('citation_atoms', 'SELECT COUNT(*) FROM citation_atoms'),
        ('atoms', 'SELECT COUNT(*) FROM atoms'),
        ('judicial', 'SELECT COUNT(*) FROM judicial_findings'),
        ('action_scores', 'SELECT COUNT(*) FROM action_scores'),
        ('Ready to file', "SELECT COUNT(*) FROM action_scores WHERE readiness_score >= 0.7"),
    ]:
        try:
            val = db.execute(q).fetchone()[0]
            print(f'  {label}: {val:,}', flush=True)
        except:
            pass
    db.close()
    print('\n[AUTOPILOT] ALL TIERS COMPLETE', flush=True)

    # Run deadline priority analysis if not disabled
    if os.environ.get('LITIGOS_DISABLE_DEADLINE_AUTOPILOT', '0') != '1':
        print('\n' + '='*60, flush=True)
        print('[AUTOPILOT] === DEADLINE PRIORITY ANALYSIS ===', flush=True)
        priorities = deadline_driven_priority()
        for p in priorities:
            icon = {"FILE NOW": "🔴", "PREPARE": "🟡", "DEFER": "🟢", "BLOCKED": "⛔"}.get(p["recommendation"], "❓")
            print(f'  {icon} {p["filing_id"]}: {p["recommendation"]} '
                  f'({p["days_remaining"]}d, urgency={p["urgency"]}, '
                  f'score={p["readiness_score"]:.2f})', flush=True)
            if p.get("blockers"):
                print(f'      Blocked by: {", ".join(p["blockers"])}', flush=True)

        # Write report
        report_path = 'agents/checkpoints/deadline_priority_report.json'
        with open(report_path, 'w') as f:
            json.dump(priorities, f, indent=2, default=str)
        print(f'\n[AUTOPILOT] Priority report → {report_path}', flush=True)


# =========================================
# FILING DEPENDENCY GRAPH (ADR-001 Phase 2)
# =========================================
FILING_DEPENDENCIES = {
    "F1": [],                    # Emergency TRO — no deps
    "F2": [],                    # Shady Oaks — no deps
    "F3": [],                    # Disqualification — no deps
    "F4": ["F3"],                # Federal §1983 — after disqualification
    "F5": [],                    # MSC Original Action — no deps
    "F6": [],                    # JTC Complaint — no deps
    "F7": ["F1"],                # Custody modification — after TRO
    "F8": [],                    # PPO Termination — no deps
    "F9": ["F3", "F7"],          # COA Brief — after trial filings
    "F10": ["F9"],               # COA Emergency — after brief
}

# Lane mapping for filing IDs
FILING_LANE_MAP = {
    "F1": "A", "F2": "B", "F3": "E", "F4": "C",
    "F5": "E", "F6": "E", "F7": "A", "F8": "D",
    "F9": "F", "F10": "F",
}


def deadline_driven_priority(db_path: str = 'agents/master_index.db') -> list:
    """MCR-aware deadline priority engine.

    Returns filings sorted by urgency × readiness, with dependency enforcement.
    Kill switch: LITIGOS_DISABLE_DEADLINE_AUTOPILOT=1

    Returns list of dicts:
        filing_id, deadline, days_remaining, urgency, readiness_score,
        recommendation (FILE NOW|PREPARE|DEFER|BLOCKED), blockers
    """
    import sqlite3

    if os.environ.get('LITIGOS_DISABLE_DEADLINE_AUTOPILOT', '0') == '1':
        return []

    db = sqlite3.connect(db_path, timeout=30)
    db.execute('PRAGMA busy_timeout=30000')
    db.row_factory = sqlite3.Row

    # Gather deadline data
    deadlines = {}
    try:
        rows = db.execute("SELECT * FROM deadlines").fetchall()
        for r in rows:
            fid = dict(r).get("filing_id", dict(r).get("id", ""))
            due = dict(r).get("due_date", dict(r).get("deadline", ""))
            if fid and due:
                deadlines[str(fid)] = str(due)
    except Exception:
        pass

    # Fallback hardcoded deadlines (from F09 deadline_enforcer)
    fallback_deadlines = {
        "F1": "2026-03-01",   # Emergency Motion
        "F3": "2026-03-15",   # McNeill Disqualification
        "F9": "2026-04-15",   # COA Appellant Brief
        "F10": "2026-03-10",  # COA Record Appendix
    }
    for fid, dd in fallback_deadlines.items():
        if fid not in deadlines:
            deadlines[fid] = dd

    # Gather readiness scores
    readiness = {}
    try:
        rows = db.execute(
            "SELECT lane, MAX(composite_score) as best_score, "
            "MAX(readiness_score) as readiness "
            "FROM action_scores GROUP BY lane"
        ).fetchall()
        for r in rows:
            readiness[dict(r)["lane"]] = {
                "composite": float(dict(r)["best_score"] or 0),
                "readiness": float(dict(r)["readiness"] or 0),
            }
    except Exception:
        pass

    db.close()

    # Check which filings are "complete" (composite > 70)
    completed_filings = set()
    for fid, lane in FILING_LANE_MAP.items():
        r = readiness.get(lane, {})
        if r.get("composite", 0) >= 70:
            completed_filings.add(fid)

    # Build priority list
    now = datetime.now()
    priorities = []

    all_filings = set(list(FILING_DEPENDENCIES.keys()))
    for fid in sorted(all_filings):
        lane = FILING_LANE_MAP.get(fid, "A")
        r = readiness.get(lane, {})
        score = r.get("readiness", r.get("composite", 0) / 100.0)
        if score > 1.0:
            score = score / 100.0  # normalize if composite_score (0-100)

        # Parse deadline
        deadline_str = deadlines.get(fid, "")
        days_remaining = 999
        if deadline_str:
            try:
                dl = datetime.strptime(deadline_str[:10], "%Y-%m-%d")
                days_remaining = (dl - now).days
            except ValueError:
                pass

        # Urgency classification (matches F09)
        if days_remaining <= 0:
            urgency = "OVERDUE"
        elif days_remaining <= 3:
            urgency = "CRITICAL"
        elif days_remaining <= 7:
            urgency = "HIGH"
        elif days_remaining <= 21:
            urgency = "MEDIUM"
        else:
            urgency = "LOW"

        # Check dependency blockers
        deps = FILING_DEPENDENCIES.get(fid, [])
        blockers = [d for d in deps if d not in completed_filings]

        # Recommendation engine
        if blockers:
            recommendation = "BLOCKED"
        elif urgency in ("OVERDUE", "CRITICAL") and score >= 0.65:
            recommendation = "FILE NOW"
        elif urgency in ("OVERDUE", "CRITICAL") and score < 0.65:
            recommendation = "PREPARE"
        elif urgency == "HIGH" and score >= 0.65:
            recommendation = "PREPARE"
        elif urgency in ("MEDIUM", "LOW") and score >= 0.65:
            recommendation = "DEFER"
        else:
            recommendation = "DEFER"

        # Priority sort key: urgency weight * (1 + readiness)
        urgency_weight = {"OVERDUE": 100, "CRITICAL": 80, "HIGH": 60,
                          "MEDIUM": 30, "LOW": 10}.get(urgency, 0)
        priority_score = urgency_weight * (1 + score)

        priorities.append({
            "filing_id": fid,
            "lane": lane,
            "deadline": deadline_str or "No deadline set",
            "days_remaining": days_remaining,
            "urgency": urgency,
            "readiness_score": round(score, 3),
            "recommendation": recommendation,
            "blockers": blockers,
            "priority_score": round(priority_score, 1),
        })

    # Sort: highest priority first
    priorities.sort(key=lambda x: -x["priority_score"])
    return priorities


# CLI entry point for standalone deadline analysis
if __name__ == '__main__' and '--deadlines' in sys.argv:
    print('[AUTOPILOT] Deadline Priority Analysis (standalone mode)', flush=True)
    priorities = deadline_driven_priority()
    for p in priorities:
        icon = {"FILE NOW": "🔴", "PREPARE": "🟡", "DEFER": "🟢", "BLOCKED": "⛔"}.get(p["recommendation"], "❓")
        print(f'  {icon} {p["filing_id"]}: {p["recommendation"]} '
              f'({p["days_remaining"]}d, urgency={p["urgency"]}, '
              f'score={p["readiness_score"]:.2f})', flush=True)
    report_path = 'agents/checkpoints/deadline_priority_report.json'
    with open(report_path, 'w') as f:
        json.dump(priorities, f, indent=2, default=str)
    print(f'\nReport → {report_path}', flush=True)
    sys.exit(0)
