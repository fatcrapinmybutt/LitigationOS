#!/usr/bin/env python3
"""Tool #264: DESKTOP FILING CONSOLIDATOR
Scans and indexes ALL court filing versions found on Desktop and F: drive
into `desktop_filing_versions` table. Cross-references versions and identifies
the latest version of each filing.
"""
import sys, os, json, sqlite3, re
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except:
        return []


# ── Filing type detection ───────────────────────────────────────────
def detect_filing_type(filepath):
    fp = s(filepath)
    if 'affidavit' in fp:
        return 'affidavit'
    if 'motion' in fp or 'mc-230' in fp:
        return 'motion'
    if 'brief' in fp:
        return 'brief'
    if 'complaint' in fp:
        return 'complaint'
    if 'order' in fp or 'cc385' in fp:
        return 'order'
    if 'exhibit' in fp:
        return 'exhibit'
    if 'petition' in fp or 'application' in fp:
        return 'petition'
    if 'memo' in fp or 'playbook' in fp or 'narrative' in fp:
        return 'brief'
    return 'filing'


# ── Case lane detection ────────────────────────────────────────────
def detect_lane(filepath):
    fp = s(filepath)
    if any(k in fp for k in ['ppo', '5907', 'cc379', 'cc385', 'terminatevacate',
                              'terminate_ppo', 'modify_ppo', 'protection']):
        return 'D'
    if any(k in fp for k in ['mcneill', 'jtc', 'judicial', 'misconduct', 'canon',
                              'disqualif', 'recusal', 'bias']):
        return 'E'
    if any(k in fp for k in ['coa', 'appeal', 'appellate', 'msc', 'superintending',
                              'supervisory']):
        return 'F'
    if any(k in fp for k in ['shady', 'housing', 'eviction', '002760', 'tro']):
        return 'B'
    if any(k in fp for k in ['custody', 'parenting', '001507', 'emergencypt']):
        return 'A'
    if any(k in fp for k in ['1983', 'federal', 'wdmi']):
        return 'F'
    return 'A'


# ── Version extraction ──────────────────────────────────────────────
def extract_version(filepath):
    fn = os.path.basename(filepath)
    # Patterns: v6, v5, v1.1, vFinal, _v2, _v1
    m = re.search(r'[_\s]v(\d+(?:\.\d+)?)', fn, re.IGNORECASE)
    if m:
        return f"v{m.group(1)}"
    m = re.search(r'vFinal', fn, re.IGNORECASE)
    if m:
        return 'vFinal'
    m = re.search(r'_SHORT', fn)
    if m:
        return 'SHORT'
    return 'v1'


# ── Filing group ID ─────────────────────────────────────────────────
def filing_group_id(filepath):
    """Group related filing versions under the same filing_id."""
    fn = s(os.path.basename(filepath))
    # Remove version suffixes for grouping
    fn = re.sub(r'[_\s]v\d+(\.\d+)?', '', fn)
    fn = re.sub(r'vfinal', '', fn)
    fn = re.sub(r'_short', '', fn)
    fn = re.sub(r'\.docx$|\.pdf$|\.md$|\.txt$', '', fn)
    fn = re.sub(r'[_\s]+$', '', fn)
    return fn.strip()


def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")

    print("=" * 70)
    print("TOOL #264: DESKTOP FILING CONSOLIDATOR")
    print("=" * 70)

    # Create table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS desktop_filing_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_id TEXT,
            title TEXT,
            file_path TEXT,
            drive TEXT,
            version TEXT,
            date_modified TEXT,
            size_bytes INTEGER,
            is_latest INTEGER DEFAULT 0,
            case_lane TEXT,
            filing_type TEXT,
            scan_date TEXT
        )
    """)
    conn.commit()

    cols = [r[1] for r in conn.execute("PRAGMA table_info(desktop_filing_versions)").fetchall()]
    print(f"  Table columns: {cols}")

    scan_date = datetime.now().isoformat()

    # ── Known filing paths ──────────────────────────────────────────

    # Desktop COURT_FILING_DRAFTS folder (5 draft motions)
    desktop_drafts = [
        (r"C:\Users\andre\Desktop\COURT_FILING_DRAFTS\Emergency_Motion_PT_Reinstatement.docx",
         "Emergency Motion PT Reinstatement"),
        (r"C:\Users\andre\Desktop\COURT_FILING_DRAFTS\Motion_Disqualification_McNeill.docx",
         "Motion Disqualification McNeill"),
        (r"C:\Users\andre\Desktop\COURT_FILING_DRAFTS\JTC_Verified_Complaint.docx",
         "JTC Verified Complaint"),
        (r"C:\Users\andre\Desktop\COURT_FILING_DRAFTS\Contempt_Motion_Watson.docx",
         "Contempt Motion Watson"),
        (r"C:\Users\andre\Desktop\COURT_FILING_DRAFTS\PPO_Modify_Terminate_Motion.docx",
         "PPO Modify Terminate Motion"),
    ]

    # Desktop LITIGATION_FILING_PACKAGE (PKG_F1-F10)
    desktop_pkg = []
    pkg_titles = {
        "F1": "Emergency Motion Custody PT",
        "F2": "Shady Oaks Housing Complaint",
        "F3": "Motion Disqualify McNeill",
        "F4": "Federal §1983 WDMI",
        "F5": "COA Application Leave to Appeal",
        "F6": "PPO Terminate/Modify CC379",
        "F7": "JTC Verified Complaint",
        "F8": "MSC Original Action",
        "F9": "Contempt Motion Watson",
        "F10": "Motion Rescind Suspension",
    }
    for fid, title in pkg_titles.items():
        desktop_pkg.append((
            f"C:\\Users\\andre\\Desktop\\LITIGATION_FILING_PACKAGE\\PKG_{fid}\\main_filing.docx",
            title, fid
        ))

    # F:\ Drive filings
    f_filings = [
        # Hearing briefs (versioned)
        (r"F:\Hearing_Brief_Ex_Parte_PT_Pigors_v_Watson_v3.docx", "Hearing Brief Ex Parte PT"),
        (r"F:\Hearing_Brief_Ex_Parte_PT_Pigors_v_Watson_v4.docx", "Hearing Brief Ex Parte PT"),
        (r"F:\Hearing_Brief_Ex_Parte_PT_Pigors_v_Watson_v5.docx", "Hearing Brief Ex Parte PT"),
        (r"F:\Hearing_Brief_Ex_Parte_PT_Pigors_v_Watson_v6.docx", "Hearing Brief Ex Parte PT"),
        (r"F:\Pigors_ExParte_PT_Hearing_Brief_vFinal.docx", "Hearing Brief Ex Parte PT"),
        # Motions
        (r"F:\MOTION_CUSTODY_EmergencyPT_SHORT.docx", "Emergency Custody Motion PT"),
        (r"F:\MOTION_PPO_TerminateVacateSanctions_SHORT.docx", "PPO Terminate Vacate Sanctions Motion"),
        (r"F:\Motion_Disqualify_and_Refer_Chief_Judge_v1.1.docx", "Motion Disqualify Refer Chief Judge"),
        (r"F:\Motion_to_Rescind_Suspension_Pigors_v_Watson.docx", "Motion Rescind Suspension"),
        (r"F:\MC-230_Emergency_TRO_Motion.docx", "Emergency TRO Motion MC-230"),
        (r"F:\CC379_Motion_Modify_Terminate_PPO_2023-5907-PP_2025-09-26.docx", "CC379 Motion Modify Terminate PPO"),
        # Affidavits
        (r"F:\Verified_Affidavit_Linked_FINAL.docx", "Verified Affidavit Linked"),
        (r"F:\Affidavit_Exhibit_A_CUSTODY_WEAVED_MEEK4.docx", "Affidavit Exhibit A Custody"),
        (r"F:\Affidavit_Exhibit_A_PPO_WEAVED_MEEK4.docx", "Affidavit Exhibit A PPO"),
        (r"F:\Affidavit_Pigors_Disqualification_v1.1.docx", "Affidavit Disqualification"),
        # Briefs / Narratives
        (r"F:\Canon_Violation_Brief_Pigors_v_Watson.docx", "Canon Violation Brief"),
        (r"F:\Pigors_JTC_Structural_DueProcess_Canon_Narrative_v1.docx", "JTC Due Process Canon Narrative"),
        (r"F:\Pigors_Hearing_Record_Building_Playbook_v1.docx", "Hearing Record Building Playbook"),
        (r"F:\Pigors_WDMI_1983_Framing_Memo_v1.docx", "WDMI §1983 Framing Memo"),
        (r"F:\Pigors_Parental_Alienation_Pattern_Memo_v1.docx", "Parental Alienation Pattern Memo"),
        # Orders
        (r"F:\Supervisory_Order_MCR_7.206_Pigors_v_Watson.docx", "Supervisory Order MCR 7.206"),
        (r"F:\Proposed_Order_ParentingTime_Reinstatement.docx", "Proposed Order PT Reinstatement"),
        (r"F:\CC385_Order_Modify_Terminate_PPO_2023-5907-PP_2025-09-26.docx", "CC385 Order Modify Terminate PPO"),
        # COA / MSC / JTC
        (r"F:\2025-10-29_COA_Brief_in_Support_v2.docx", "COA Brief in Support"),
        (r"F:\Pigors_COA_Application_Leave_ExParte_PT_Suspension_v1.docx", "COA Application Leave to Appeal"),
        (r"F:\2025-10-29_COA_Complaint_Superintending_Control_v2.docx", "COA Complaint Superintending Control"),
        (r"F:\2025-10-29_JTC_Verified_Complaint_Captioned_Signed_Notarized_v6.docx", "JTC Verified Complaint"),
        (r"F:\2025-10-29_MSC_ExParte_Addendum_Captioned_Signed_Notarized_v6.docx", "MSC ExParte Addendum"),
        # Shady Oaks
        (r"F:\Verified_Complaint_ShadyOaks.docx", "Verified Complaint Shady Oaks"),
        # Exhibits
    ]
    for letter in 'ABCDEFGHIJKLM':
        f_filings.append((f"F:\\Exhibit_{letter}.docx", f"Exhibit {letter}"))

    # ── Build rows ──────────────────────────────────────────────────
    rows = []
    filing_groups = {}  # group_id -> list of (path, version, title)

    def add_row(fpath, title, fid_override=None):
        fn = os.path.basename(fpath)
        drive = fpath[0]
        version = extract_version(fpath)
        ftype = detect_filing_type(fpath)
        lane = detect_lane(fpath)
        fid = fid_override or filing_group_id(fpath)

        # Try to get file size/date if file exists
        size = 0
        date_mod = ''
        if os.path.exists(fpath):
            try:
                st = os.stat(fpath)
                size = st.st_size
                date_mod = datetime.fromtimestamp(st.st_mtime).isoformat()
            except:
                pass

        row = (fid, title, fpath, drive, version, date_mod, size, 0, lane, ftype, scan_date)
        rows.append(row)

        # Track for latest-version detection
        if fid not in filing_groups:
            filing_groups[fid] = []
        filing_groups[fid].append((fpath, version, title, date_mod, size))

    # Process desktop drafts
    for fpath, title in desktop_drafts:
        add_row(fpath, title)

    # Process desktop PKG filings
    for fpath, title, fid in desktop_pkg:
        add_row(fpath, title, fid_override=f"PKG_{fid}")

    # Process F:\ filings
    for entry in f_filings:
        fpath, title = entry[0], entry[1]
        add_row(fpath, title)

    # ── Insert into DB ──────────────────────────────────────────────
    # Clear existing scan data to avoid stale entries
    conn.execute("DELETE FROM desktop_filing_versions WHERE scan_date != ''")
    conn.executemany("""
        INSERT INTO desktop_filing_versions
        (filing_id, title, file_path, drive, version, date_modified, size_bytes,
         is_latest, case_lane, filing_type, scan_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()

    # ── Determine latest versions ───────────────────────────────────
    VERSION_ORDER = {'vfinal': 1000, 'short': 500}

    def version_sort_key(v):
        vl = v.lower()
        if vl in VERSION_ORDER:
            return VERSION_ORDER[vl]
        m = re.match(r'v(\d+(?:\.\d+)?)', vl)
        if m:
            return float(m.group(1))
        return 0

    latest_map = {}
    for gid, entries in filing_groups.items():
        # Sort by version descending, then by date
        best = max(entries, key=lambda e: (version_sort_key(e[1]), e[3]))
        latest_map[gid] = best[0]  # file_path of the latest
        conn.execute(
            "UPDATE desktop_filing_versions SET is_latest=1 WHERE filing_id=? AND file_path=?",
            (gid, best[0])
        )
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM desktop_filing_versions").fetchone()[0]
    latest_count = conn.execute("SELECT COUNT(*) FROM desktop_filing_versions WHERE is_latest=1").fetchone()[0]
    unique_filings = len(filing_groups)

    # ── Summary output ──────────────────────────────────────────────
    print(f"\n  Total filing entries: {total}")
    print(f"  Unique filing groups: {unique_filings}")
    print(f"  Latest versions identified: {latest_count}")

    print(f"\n  Filing Version Matrix:")
    print(f"  {'Filing ID':<50s} {'Versions':>8s} {'Latest':>10s} {'Lane':>5s} {'Type':>10s}")
    print(f"  {'-'*50} {'-'*8} {'-'*10} {'-'*5} {'-'*10}")

    for gid in sorted(filing_groups.keys()):
        entries = filing_groups[gid]
        versions = sorted(set(e[1] for e in entries))
        latest_v = 'vFinal' if 'vFinal' in versions else max(versions, key=version_sort_key)
        lane = detect_lane(entries[0][0])
        ftype = detect_filing_type(entries[0][0])
        v_str = ','.join(versions)
        print(f"  {gid:<50s} {len(entries):>8d} {latest_v:>10s} {lane:>5s} {ftype:>10s}")

    # By lane
    lane_counts = safe_query(conn,
        "SELECT case_lane, COUNT(*), SUM(is_latest) FROM desktop_filing_versions GROUP BY case_lane ORDER BY case_lane")
    print(f"\n  By Case Lane:")
    for r in lane_counts:
        print(f"    Lane {r[0]}: {r[1]} versions, {r[2]} latest")

    # By type
    type_counts = safe_query(conn,
        "SELECT filing_type, COUNT(*) FROM desktop_filing_versions GROUP BY filing_type ORDER BY COUNT(*) DESC")
    print(f"\n  By Filing Type:")
    for r in type_counts:
        print(f"    {r[0]}: {r[1]}")

    # ── Generate reports ────────────────────────────────────────────
    report_data = {
        "tool": "#264 Desktop Filing Consolidator",
        "generated": scan_date,
        "total_entries": total,
        "unique_filings": unique_filings,
        "latest_versions": latest_count,
        "filing_groups": {},
        "by_lane": {r[0]: {"total": r[1], "latest": r[2]} for r in lane_counts},
        "by_type": {r[0]: r[1] for r in type_counts},
    }
    for gid, entries in filing_groups.items():
        report_data["filing_groups"][gid] = {
            "versions": [{"path": e[0], "version": e[1], "title": e[2],
                          "date": e[3], "size": e[4]} for e in entries],
            "latest_path": latest_map.get(gid, ''),
            "lane": detect_lane(entries[0][0]),
            "type": detect_filing_type(entries[0][0]),
        }

    json_path = os.path.join(report_dir, "tool_264_desktop_filing_versions.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    md_lines = [
        "# Tool #264: Desktop Filing Consolidator",
        f"Generated: {scan_date}",
        "",
        "## Summary",
        f"- **Total filing entries**: {total}",
        f"- **Unique filing groups**: {unique_filings}",
        f"- **Latest versions identified**: {latest_count}",
        "",
        "## Filing Version Matrix",
        "",
        "| Filing ID | Versions | Latest | Lane | Type |",
        "|-----------|----------|--------|------|------|",
    ]
    for gid in sorted(filing_groups.keys()):
        entries = filing_groups[gid]
        versions = sorted(set(e[1] for e in entries))
        latest_v = 'vFinal' if 'vFinal' in versions else max(versions, key=version_sort_key)
        lane = detect_lane(entries[0][0])
        ftype = detect_filing_type(entries[0][0])
        md_lines.append(f"| {gid} | {','.join(versions)} | {latest_v} | {lane} | {ftype} |")

    md_lines.append("")
    md_lines.append("## Version Details")
    md_lines.append("")
    for gid in sorted(filing_groups.keys()):
        entries = filing_groups[gid]
        md_lines.append(f"### {gid}")
        md_lines.append(f"- **Lane**: {detect_lane(entries[0][0])}")
        md_lines.append(f"- **Type**: {detect_filing_type(entries[0][0])}")
        md_lines.append(f"- **Latest**: `{latest_map.get(gid, 'unknown')}`")
        md_lines.append("")
        for e in entries:
            latest_marker = " ✅ LATEST" if e[0] == latest_map.get(gid) else ""
            md_lines.append(f"  - `{e[0]}` — {e[1]}{latest_marker}")
        md_lines.append("")

    md_lines.append("## By Case Lane")
    md_lines.append("| Lane | Total | Latest |")
    md_lines.append("|------|-------|--------|")
    for r in lane_counts:
        md_lines.append(f"| {r[0]} | {r[1]} | {r[2]} |")
    md_lines.append("")
    md_lines.append("## By Filing Type")
    md_lines.append("| Type | Count |")
    md_lines.append("|------|-------|")
    for r in type_counts:
        md_lines.append(f"| {r[0]} | {r[1]} |")

    md_path = os.path.join(report_dir, "tool_264_desktop_filing_versions.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"\n  Reports written:")
    print(f"    {json_path}")
    print(f"    {md_path}")

    conn.close()
    print("\n" + "=" * 70)
    print("TOOL #264 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
