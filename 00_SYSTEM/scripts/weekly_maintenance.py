#!/usr/bin/env python3
"""
LitigationOS Weekly Maintenance Script
=======================================
Run:  python 00_SYSTEM/scripts/weekly_maintenance.py [--full | --quick]

Performs read-only health checks across all LitigationOS subsystems:
  1. Drive health     2. Database health    3. Deadline monitor
  4. Filing readiness  5. Agent fleet        6. Backup verification
  7. Intelligence gaps  8. Report generation

Safe to run anytime — no writes except the final report file.
"""
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

import argparse
import ctypes
import datetime
import os
import pathlib
import sqlite3
import textwrap
import time


# ── Constants ────────────────────────────────────────────────────────────────
LITIGATIONOS_ROOT = pathlib.Path(r"C:\Users\andre\LitigationOS")
DB_PATH = LITIGATIONOS_ROOT / "litigation_context.db"
REPORT_PATH = LITIGATIONOS_ROOT / "00_SYSTEM" / "WEEKLY_HEALTH_REPORT.md"

DRIVES = ["C:", "D:", "F:", "G:", "H:", "I:"]

GOLDEN_SET_LOCATIONS = [
    pathlib.Path(r"D:\THIS_IS_THE_ONE"),
    LITIGATIONOS_ROOT / "GOLDEN_SET",
    pathlib.Path(r"G:\GOLDEN_SET_BACKUP"),
]

AGENTS_DIR = pathlib.Path.home() / ".copilot" / "agents"
SKILLS_DIR = pathlib.Path.home() / ".copilot" / "skills"
AGENT_REGISTRY = LITIGATIONOS_ROOT / "00_SYSTEM" / "AGENT_REGISTRY.md"

KEY_TABLES = [
    "evidence_quotes",
    "extracted_harms",
    "deadlines",
    "omega_filing_readiness",
    "omega_intelligence_gaps",
    "documents",
    "atoms",
    "authority_chains",
    "judicial_findings",
    "claims",
]

DB_PRAGMAS = [
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
]


# ── Helpers ──────────────────────────────────────────────────────────────────
def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fmt_bytes(n):
    """Human-readable byte size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def get_drive_space(drive_letter):
    """Return (free, total) in bytes using ctypes on Windows."""
    free = ctypes.c_ulonglong(0)
    total = ctypes.c_ulonglong(0)
    root = drive_letter + "\\"
    try:
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            root, ctypes.byref(free), ctypes.byref(total), None
        )
    except Exception:
        return None, None
    return free.value, total.value


def safe_db_connect(db_path):
    """Open DB with standard PRAGMAs; returns (conn, cursor) or (None, None)."""
    if not db_path.exists():
        return None, None
    conn = sqlite3.connect(str(db_path), timeout=120)
    cur = conn.cursor()
    for pragma in DB_PRAGMAS:
        cur.execute(pragma)
    return conn, cur


def quick_file_count(root, sample_limit=5000):
    """Fast file count — walks up to sample_limit entries then extrapolates."""
    count = 0
    try:
        for _dirpath, _dirnames, filenames in os.walk(root):
            count += len(filenames)
            if count >= sample_limit:
                return count, True
    except (PermissionError, OSError):
        pass
    return count, False


def largest_files(root, top_n=5, walk_limit=10000):
    """Find the top-N largest files under root (bounded walk)."""
    results = []
    visited = 0
    try:
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                fp = os.path.join(dirpath, fn)
                try:
                    sz = os.path.getsize(fp)
                    results.append((sz, fp))
                except (PermissionError, OSError):
                    continue
                visited += 1
                if visited >= walk_limit:
                    results.sort(reverse=True)
                    return results[:top_n], True
    except (PermissionError, OSError):
        pass
    results.sort(reverse=True)
    return results[:top_n], False


# ── Section 1: Drive Health ──────────────────────────────────────────────────
def check_drives(full_mode=False):
    lines = ["## 1. Drive Health Check\n"]
    alerts = []
    walk_limit = 50000 if full_mode else 10000

    for drive in DRIVES:
        root = drive + "\\"
        if not os.path.exists(root):
            lines.append(f"### {drive}  —  **NOT MOUNTED**\n")
            continue

        free, total = get_drive_space(drive)
        if total is None or total == 0:
            lines.append(f"### {drive}  —  **UNABLE TO READ**\n")
            continue

        used = total - free
        pct = (used / total) * 100
        status = "OK" if pct < 90 else "ALERT"
        if pct >= 90:
            alerts.append(f"{drive} is {pct:.1f}% full — free up space immediately")

        file_count, truncated = quick_file_count(root, sample_limit=5000 if not full_mode else 50000)
        count_label = f"~{file_count}+" if truncated else str(file_count)

        lines.append(f"### {drive}  —  {status}")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total | {fmt_bytes(total)} |")
        lines.append(f"| Used | {fmt_bytes(used)} ({pct:.1f}%) |")
        lines.append(f"| Free | {fmt_bytes(free)} |")
        lines.append(f"| Files (est.) | {count_label} |")
        lines.append("")

        if full_mode:
            big, _ = largest_files(root, top_n=5, walk_limit=walk_limit)
            if big:
                lines.append("**Largest files:**")
                for sz, fp in big:
                    lines.append(f"- `{fp}` — {fmt_bytes(sz)}")
                lines.append("")

    return "\n".join(lines), alerts


# ── Section 2: Database Health ───────────────────────────────────────────────
def check_database(full_mode=False):
    lines = ["## 2. Database Health\n"]
    alerts = []

    if not DB_PATH.exists():
        lines.append("**DATABASE NOT FOUND** at `{}`\n".format(DB_PATH))
        alerts.append("litigation_context.db is MISSING")
        return "\n".join(lines), alerts

    db_size = DB_PATH.stat().st_size
    lines.append(f"- **Path:** `{DB_PATH}`")
    lines.append(f"- **Size:** {fmt_bytes(db_size)}")
    lines.append(f"- **Modified:** {datetime.datetime.fromtimestamp(DB_PATH.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    conn, cur = safe_db_connect(DB_PATH)
    if conn is None:
        lines.append("**Could not connect to database.**\n")
        alerts.append("Cannot open litigation_context.db")
        return "\n".join(lines), alerts

    try:
        # Table count
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cur.fetchone()[0]
        lines.append(f"- **Tables:** {table_count}")

        # Integrity check
        if full_mode:
            lines.append("- **Integrity check:** running full check (may take minutes)...")
            cur.execute("PRAGMA integrity_check")
        else:
            cur.execute("PRAGMA quick_check")
        ic_result = cur.fetchone()[0]
        ic_status = "PASS" if ic_result == "ok" else f"FAIL: {ic_result}"
        lines.append(f"- **Integrity:** {ic_status}")
        if ic_result != "ok":
            alerts.append(f"Database integrity check FAILED: {ic_result}")
        lines.append("")

        # Key table row counts
        lines.append("### Key Table Row Counts\n")
        lines.append("| Table | Rows |")
        lines.append("|-------|------|")
        for tbl in KEY_TABLES:
            try:
                cur.execute(f"SELECT COUNT(*) FROM [{tbl}]")
                rows = cur.fetchone()[0]
                lines.append(f"| {tbl} | {rows:,} |")
            except sqlite3.OperationalError:
                lines.append(f"| {tbl} | *(table not found)* |")
        lines.append("")

        # Empty tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        all_tables = [r[0] for r in cur.fetchall()]
        empty_tables = []
        for tbl in all_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM [{tbl}]")
                if cur.fetchone()[0] == 0:
                    empty_tables.append(tbl)
            except sqlite3.OperationalError:
                continue
        if empty_tables:
            lines.append(f"### Empty Tables ({len(empty_tables)})\n")
            if len(empty_tables) <= 20 or full_mode:
                for t in empty_tables:
                    lines.append(f"- `{t}`")
            else:
                for t in empty_tables[:20]:
                    lines.append(f"- `{t}`")
                lines.append(f"- ...and {len(empty_tables) - 20} more")
            lines.append("")

        # Orphaned indexes
        cur.execute("""
            SELECT i.name, i.tbl_name FROM sqlite_master i
            WHERE i.type='index'
              AND i.tbl_name NOT IN (SELECT name FROM sqlite_master WHERE type='table')
        """)
        orphans = cur.fetchall()
        if orphans:
            lines.append(f"### Orphaned Indexes ({len(orphans)})\n")
            for idx_name, tbl_name in orphans:
                lines.append(f"- `{idx_name}` → missing table `{tbl_name}`")
            alerts.append(f"{len(orphans)} orphaned indexes found")
            lines.append("")

    finally:
        conn.close()

    return "\n".join(lines), alerts


# ── Section 3: Deadline Monitor ──────────────────────────────────────────────
def check_deadlines():
    lines = ["## 3. Deadline Monitor\n"]
    alerts = []

    conn, cur = safe_db_connect(DB_PATH)
    if conn is None:
        lines.append("*Database unavailable.*\n")
        return "\n".join(lines), alerts

    try:
        cur.execute("""
            SELECT deadline_id, title, due_date_iso, status, case_id, risk_if_missed
            FROM deadlines
            ORDER BY due_date_iso ASC
        """)
        rows = cur.fetchall()

        if not rows:
            lines.append("No deadlines found in database.\n")
            return "\n".join(lines), alerts

        today = datetime.date.today()
        overdue = []
        urgent = []
        upcoming = []

        for did, title, due_iso, status, case_id, risk in rows:
            try:
                due_date = datetime.date.fromisoformat(due_iso[:10])
            except (ValueError, TypeError):
                continue
            days_left = (due_date - today).days
            entry = {
                "id": did, "title": title, "due": due_iso[:10],
                "status": status or "unknown", "case": case_id or "",
                "risk": risk or "", "days": days_left,
            }
            if days_left < 0 and (status or "").lower() not in ("completed", "done", "filed"):
                overdue.append(entry)
            elif 0 <= days_left <= 7:
                urgent.append(entry)
            else:
                upcoming.append(entry)

        if overdue:
            lines.append(f"### OVERDUE ({len(overdue)})\n")
            lines.append("| Deadline | Due | Days Late | Status | Risk |")
            lines.append("|----------|-----|-----------|--------|------|")
            for e in overdue:
                lines.append(f"| {e['title'][:50]} | {e['due']} | {abs(e['days'])} | {e['status']} | {e['risk'][:40]} |")
            lines.append("")
            alerts.append(f"{len(overdue)} OVERDUE deadline(s) require immediate attention")

        if urgent:
            lines.append(f"### URGENT — Within 7 Days ({len(urgent)})\n")
            lines.append("| Deadline | Due | Days Left | Status |")
            lines.append("|----------|-----|-----------|--------|")
            for e in urgent:
                lines.append(f"| {e['title'][:50]} | {e['due']} | {e['days']} | {e['status']} |")
            lines.append("")
            alerts.append(f"{len(urgent)} deadline(s) due within 7 days")

        lines.append(f"**Total deadlines:** {len(rows)} | Overdue: {len(overdue)} | Urgent: {len(urgent)} | Upcoming: {len(upcoming)}\n")

    finally:
        conn.close()

    return "\n".join(lines), alerts


# ── Section 4: Filing Readiness ──────────────────────────────────────────────
def check_filing_readiness():
    lines = ["## 4. Filing Readiness\n"]
    alerts = []

    conn, cur = safe_db_connect(DB_PATH)
    if conn is None:
        lines.append("*Database unavailable.*\n")
        return "\n".join(lines), alerts

    try:
        cur.execute("""
            SELECT action_name, readiness_pct, tier, forum, phase_name, risk_score
            FROM omega_filing_readiness
            ORDER BY readiness_pct DESC
        """)
        rows = cur.fetchall()

        if not rows:
            lines.append("No filing readiness data found.\n")
            return "\n".join(lines), alerts

        complete = [(r[0], r[1], r[2], r[3]) for r in rows if (r[1] or 0) >= 100]
        high = [(r[0], r[1], r[2], r[3]) for r in rows if 80 <= (r[1] or 0) < 100]
        low = [(r[0], r[1], r[2], r[3]) for r in rows if (r[1] or 0) < 80]

        lines.append(f"**Total filings tracked:** {len(rows)}\n")
        lines.append(f"- Ready (100%): **{len(complete)}**")
        lines.append(f"- Near-ready (80-99%): **{len(high)}**")
        lines.append(f"- Needs work (<80%): **{len(low)}**")
        lines.append("")

        if high:
            lines.append("### Near-Ready Filings (80-99%) — Close the Gap\n")
            lines.append("| Filing | Readiness | Tier | Forum |")
            lines.append("|--------|-----------|------|-------|")
            for name, pct, tier, forum in high:
                lines.append(f"| {name[:50]} | {pct}% | {tier or '-'} | {forum or '-'} |")
            lines.append("")
            alerts.append(f"{len(high)} filing(s) at 80-99% — push these to 100%")

        if low:
            lines.append("### Filings Needing Work (<80%)\n")
            lines.append("| Filing | Readiness | Tier | Forum |")
            lines.append("|--------|-----------|------|-------|")
            for name, pct, tier, forum in low[:15]:
                lines.append(f"| {name[:50]} | {pct}% | {tier or '-'} | {forum or '-'} |")
            if len(low) > 15:
                lines.append(f"| ...and {len(low) - 15} more | | | |")
            lines.append("")

    finally:
        conn.close()

    return "\n".join(lines), alerts


# ── Section 5: Agent Fleet ───────────────────────────────────────────────────
def check_agent_fleet():
    lines = ["## 5. Agent Fleet Check\n"]
    alerts = []

    # Agents
    agent_count = 0
    stub_agents = []
    if AGENTS_DIR.exists():
        agent_files = list(AGENTS_DIR.glob("*.md"))
        agent_count = len(agent_files)
        for af in agent_files:
            try:
                if af.stat().st_size < 200:
                    stub_agents.append(af.name)
            except OSError:
                continue
    lines.append(f"- **Copilot agents:** {agent_count} (in `{AGENTS_DIR}`)")

    # Skills
    skill_count = 0
    if SKILLS_DIR.exists():
        skill_files = list(SKILLS_DIR.glob("*.md"))
        skill_count = len(skill_files)
    lines.append(f"- **Copilot skills:** {skill_count} (in `{SKILLS_DIR}`)")

    # Agent Registry
    if AGENT_REGISTRY.exists():
        reg_mtime = datetime.datetime.fromtimestamp(AGENT_REGISTRY.stat().st_mtime)
        age_days = (datetime.datetime.now() - reg_mtime).days
        freshness = "current" if age_days < 14 else f"**STALE** ({age_days} days old)"
        lines.append(f"- **AGENT_REGISTRY.md:** exists, {freshness}")
        if age_days >= 14:
            alerts.append(f"AGENT_REGISTRY.md is {age_days} days old — regenerate it")
    else:
        lines.append("- **AGENT_REGISTRY.md:** **MISSING**")
        alerts.append("AGENT_REGISTRY.md not found — create one")

    # Stubs
    if stub_agents:
        lines.append(f"\n### Stub Agents (<200 bytes) — {len(stub_agents)}\n")
        for sa in stub_agents:
            lines.append(f"- `{sa}`")
        alerts.append(f"{len(stub_agents)} agent(s) under 200 bytes — likely stubs")

    lines.append("")
    return "\n".join(lines), alerts


# ── Section 6: Backup Verification ───────────────────────────────────────────
def check_backups():
    lines = ["## 6. Backup Verification\n"]
    alerts = []

    lines.append("| Location | Exists | Files | Last Modified |")
    lines.append("|----------|--------|-------|---------------|")

    found_counts = []
    for loc in GOLDEN_SET_LOCATIONS:
        if loc.exists():
            try:
                fc, _ = quick_file_count(str(loc), sample_limit=50000)
                mtime = datetime.datetime.fromtimestamp(loc.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            except OSError:
                fc, mtime = "?", "?"
            lines.append(f"| `{loc}` | YES | {fc:,} | {mtime} |")
            found_counts.append((str(loc), fc))
        else:
            lines.append(f"| `{loc}` | **NO** | — | — |")
            alerts.append(f"Golden set MISSING at `{loc}`")
    lines.append("")

    # Cross-compare counts
    if len(found_counts) >= 2:
        counts = [c for _, c in found_counts]
        if max(counts) - min(counts) > 10:
            lines.append("**WARNING:** File counts differ significantly across golden set locations.\n")
            alerts.append("Golden set file counts differ — verify sync")

    return "\n".join(lines), alerts


# ── Section 7: Intelligence Gaps ─────────────────────────────────────────────
def check_intelligence_gaps():
    lines = ["## 7. Intelligence Gaps\n"]
    alerts = []

    conn, cur = safe_db_connect(DB_PATH)
    if conn is None:
        lines.append("*Database unavailable.*\n")
        return "\n".join(lines), alerts

    try:
        cur.execute("SELECT COUNT(*) FROM omega_intelligence_gaps")
        total = cur.fetchone()[0]
        lines.append(f"**Total gaps tracked:** {total}\n")

        if total == 0:
            lines.append("No intelligence gaps recorded.\n")
            return "\n".join(lines), alerts

        # By severity
        cur.execute("""
            SELECT gap_severity, COUNT(*) as cnt
            FROM omega_intelligence_gaps
            GROUP BY gap_severity
            ORDER BY cnt DESC
        """)
        sev_rows = cur.fetchall()
        if sev_rows:
            lines.append("### By Severity\n")
            lines.append("| Severity | Count |")
            lines.append("|----------|-------|")
            for sev, cnt in sev_rows:
                lines.append(f"| {sev or 'unclassified'} | {cnt} |")
            lines.append("")

        # By action
        cur.execute("""
            SELECT action_name, COUNT(*) as cnt
            FROM omega_intelligence_gaps
            GROUP BY action_name
            ORDER BY cnt DESC
            LIMIT 10
        """)
        act_rows = cur.fetchall()
        if act_rows:
            lines.append("### Top 10 Actions by Gap Count\n")
            lines.append("| Action | Gaps |")
            lines.append("|--------|------|")
            for action, cnt in act_rows:
                lines.append(f"| {(action or 'unknown')[:50]} | {cnt} |")
            lines.append("")

        # By category
        cur.execute("""
            SELECT claim_category, COUNT(*) as cnt
            FROM omega_intelligence_gaps
            GROUP BY claim_category
            ORDER BY cnt DESC
            LIMIT 10
        """)
        cat_rows = cur.fetchall()
        if cat_rows:
            lines.append("### Top 10 Categories by Gap Count\n")
            lines.append("| Category | Gaps |")
            lines.append("|----------|------|")
            for cat, cnt in cat_rows:
                lines.append(f"| {(cat or 'unknown')[:50]} | {cnt} |")
            lines.append("")

        high_sev = sum(c for s, c in sev_rows if s and s.lower() in ("critical", "high"))
        if high_sev > 0:
            alerts.append(f"{high_sev} high/critical intelligence gaps need research")

    finally:
        conn.close()

    return "\n".join(lines), alerts


# ── Section 8: Report Assembly ───────────────────────────────────────────────
def generate_quick_actions(all_alerts):
    """Rank alerts and produce top-5 recommended actions."""
    lines = ["## Quick Actions — Top Priorities\n"]

    # Priority keywords for sorting
    priority_keywords = ["OVERDUE", "MISSING", "FAIL", "90%", "critical"]

    def score(alert_text):
        s = 0
        lower = alert_text.lower()
        for kw in priority_keywords:
            if kw.lower() in lower:
                s += 10
        return s

    ranked = sorted(all_alerts, key=score, reverse=True)

    if not ranked:
        lines.append("All systems nominal. No urgent actions needed.\n")
        return "\n".join(lines)

    for i, action in enumerate(ranked[:5], 1):
        lines.append(f"{i}. {action}")
    lines.append("")

    if len(ranked) > 5:
        lines.append(f"*Plus {len(ranked) - 5} additional alerts — see sections above.*\n")

    return "\n".join(lines)


def build_report(full_mode=False):
    """Run all checks and assemble the final markdown report."""
    mode_label = "FULL" if full_mode else "QUICK"
    start = time.time()

    header = textwrap.dedent(f"""\
        # LitigationOS Weekly Health Report
        **Generated:** {now_iso()}
        **Mode:** {mode_label}
        **System:** Pigors v. Watson — LitigationOS Δ∞

        ---
    """)

    all_alerts = []
    sections = []

    print(f"[{now_iso()}] Starting {mode_label} maintenance scan...")

    # 1. Drives
    print("  [1/7] Checking drives...")
    text, alerts = check_drives(full_mode)
    sections.append(text)
    all_alerts.extend(alerts)

    # 2. Database
    print("  [2/7] Checking database...")
    text, alerts = check_database(full_mode)
    sections.append(text)
    all_alerts.extend(alerts)

    # 3. Deadlines
    print("  [3/7] Checking deadlines...")
    text, alerts = check_deadlines()
    sections.append(text)
    all_alerts.extend(alerts)

    # 4. Filing readiness
    print("  [4/7] Checking filing readiness...")
    text, alerts = check_filing_readiness()
    sections.append(text)
    all_alerts.extend(alerts)

    # 5. Agent fleet
    print("  [5/7] Checking agent fleet...")
    text, alerts = check_agent_fleet()
    sections.append(text)
    all_alerts.extend(alerts)

    # 6. Backups
    print("  [6/7] Verifying backups...")
    text, alerts = check_backups()
    sections.append(text)
    all_alerts.extend(alerts)

    # 7. Intelligence gaps
    print("  [7/7] Analyzing intelligence gaps...")
    text, alerts = check_intelligence_gaps()
    sections.append(text)
    all_alerts.extend(alerts)

    # Quick actions summary
    actions_section = generate_quick_actions(all_alerts)

    elapsed = time.time() - start

    footer = textwrap.dedent(f"""\
        ---
        ## Run Summary
        - **Alerts raised:** {len(all_alerts)}
        - **Elapsed:** {elapsed:.1f}s
        - **Report saved to:** `{REPORT_PATH}`
        - **Next run:** Schedule with `schtasks` (see weekly_maintenance.ps1)
    """)

    full_report = "\n".join([header, actions_section] + sections + [footer])
    return full_report


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS Weekly Maintenance — read-only health check"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--full", action="store_true",
                       help="Full scan (largest files, full integrity check)")
    group.add_argument("--quick", action="store_true",
                       help="Quick scan (sampling, quick_check)")
    parser.add_argument("--stdout-only", action="store_true",
                        help="Print report to stdout without writing file")
    args = parser.parse_args()

    full_mode = args.full  # default (no flag) = quick

    report = build_report(full_mode=full_mode)

    if not args.stdout_only:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report, encoding="utf-8")
        print(f"\n[{now_iso()}] Report saved to {REPORT_PATH}")

    print("\n" + report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
