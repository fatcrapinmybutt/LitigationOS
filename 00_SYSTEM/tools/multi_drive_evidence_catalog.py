#!/usr/bin/env python3
"""Tool #263: MULTI-DRIVE EVIDENCE CATALOG
Catalogs evidence files across ALL user drives into a unified DB table
`multi_drive_catalog`. Builds a comprehensive searchable index.
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


# ── Category detection ──────────────────────────────────────────────
def detect_category(filepath, ext):
    fp = s(filepath)
    if ext == 'dir':
        return 'unknown'
    if any(k in fp for k in ['evidence', 'exhibit', 'proof', 'ex_', 'bates']):
        return 'evidence'
    if any(k in fp for k in ['motion', 'complaint', 'brief', 'petition', 'order',
                              'affidavit', 'cc379', 'cc385', 'mc-230']):
        return 'filing'
    if any(k in fp for k in ['authority', 'canon', 'mcl', 'mcr', 'statute', 'caselaw']):
        return 'authority'
    if any(k in fp for k in ['email', 'letter', 'noreply', 'appclose', 'correspondence']):
        return 'correspondence'
    if any(k in fp for k in ['income', 'financial', 'tax', 'support', 'foc']):
        return 'financial'
    if any(k in fp for k in ['police', 'nspd', 'ns25', 'dispatch']):
        return 'police'
    if any(k in fp for k in ['transcript', 'hearing', 'deposition']):
        return 'transcript'
    if ext in ('mp4', 'jpg', 'png', 'jpeg', 'gif'):
        return 'photo_video'
    if ext in ('zip', '7z', 'rar'):
        return 'archive'
    if ext in ('py', 'js', 'ps1', 'cypher', 'cmd', 'bat', 'sh'):
        return 'code'
    if any(k in fp for k in ['report', 'audit', 'analysis', 'dashboard']):
        return 'report'
    if any(k in fp for k in ['config']):
        return 'config'
    return 'unknown'


# ── Lane detection ──────────────────────────────────────────────────
def detect_lane(filepath):
    fp = s(filepath)
    lanes = []
    if any(k in fp for k in ['custody', 'parenting', 'child', 'ldw', '001507']):
        lanes.append('A')
    if any(k in fp for k in ['shady oaks', 'shady_oaks', 'housing', 'eviction', '002760', 'sewer']):
        lanes.append('B')
    if any(k in fp for k in ['ppo', 'protection', '5907', 'contempt', 'show cause',
                              'terminate_ppo', 'modify_ppo', 'terminatevacate']):
        lanes.append('D')
    if any(k in fp for k in ['mcneill', 'judicial', 'misconduct', 'jtc', 'canon', 'bias',
                              'disqualif', 'recusal']):
        lanes.append('E')
    if any(k in fp for k in ['coa', 'appeal', 'appellate', 'msc', 'superintending']):
        lanes.append('F')
    if any(k in fp for k in ['convergence', 'multi-lane', 'cross']):
        lanes.append('C')
    if not lanes:
        # Default based on filing patterns
        if any(k in fp for k in ['pigors', 'watson']):
            lanes.append('A')
    return ','.join(lanes) if lanes else 'A'


# ── Evidence value ──────────────────────────────────────────────────
def detect_value(filepath, ext, category):
    fp = s(filepath)
    # LOW: code, config, README, duplicates
    if ext in ('py', 'js', 'ps1', 'cypher', 'cmd', 'bat', 'sh'):
        return 'LOW'
    if 'readme' in fp or 'config' in fp:
        return 'LOW'
    if re.search(r'\(\d+\)', fp):  # duplicates like (1), (2)
        return 'LOW'
    # HIGH: docx filings, pdf court docs, key encyclopedias, exhibits, transcripts, affidavits
    if ext == 'docx' and category in ('filing', 'evidence'):
        return 'HIGH'
    if ext == 'pdf':
        return 'HIGH'
    if ext == 'md' and any(k in fp for k in ['encyclopedia', 'dossier', 'impeachment',
                                               'narrative', 'evidentiary', 'master']):
        return 'HIGH'
    if category in ('evidence', 'transcript'):
        return 'HIGH'
    if category == 'filing' and ext in ('docx', 'pdf'):
        return 'HIGH'
    if 'affidavit' in fp:
        return 'HIGH'
    # MEDIUM: csv, json data, evidence photos, police reports
    if ext in ('csv', 'json'):
        return 'MEDIUM'
    if category in ('photo_video', 'police'):
        return 'MEDIUM'
    if category == 'report':
        return 'MEDIUM'
    return 'MEDIUM'


# ── Perpetrator relevance ───────────────────────────────────────────
def detect_perpetrators(filepath):
    fp = s(filepath)
    perps = []
    if any(k in fp for k in ['emily', 'watson']):
        perps.append('emily')
    if any(k in fp for k in ['berry', 'ronald']):
        perps.append('berry')
    if any(k in fp for k in ['mcneill', 'judge']):
        perps.append('mcneill')
    if any(k in fp for k in ['rusco', 'foc']):
        perps.append('rusco')
    if any(k in fp for k in ['barnes', 'p55406']):
        perps.append('barnes')
    if any(k in fp for k in ['albert', 'cody', 'lori']):
        perps.append('watson_family')
    return ','.join(perps) if perps else ''


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
    print("TOOL #263: MULTI-DRIVE EVIDENCE CATALOG")
    print("=" * 70)

    # Create table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS multi_drive_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drive TEXT,
            file_path TEXT UNIQUE,
            filename TEXT,
            extension TEXT,
            category TEXT,
            case_lane TEXT,
            evidence_value TEXT,
            perpetrator_relevance TEXT,
            ingested INTEGER DEFAULT 0,
            scan_date TEXT
        )
    """)
    conn.commit()

    # Verify table schema
    cols = [r[1] for r in conn.execute("PRAGMA table_info(multi_drive_catalog)").fetchall()]
    print(f"  Table columns: {cols}")

    scan_date = datetime.now().isoformat()

    # ── Hard-coded file lists ───────────────────────────────────────
    files = []

    # VIDEOS FOLDER
    videos = [
        r"C:\Users\andre\Videos\20220723_211931.mp4",
        r"C:\Users\andre\Videos\20230605_183910.mp4",
        r"C:\Users\andre\Videos\20230506_080114.mp4",
        r"C:\Users\andre\Videos\20230218_103914.mp4",
        r"C:\Users\andre\Videos\20231028_193610.mp4",
        r"C:\Users\andre\Videos\CHATGPT_CHRONOLOGICAL_ENCYCLOPEDIA.md",
        r"C:\Users\andre\Videos\SHADY_OAKS_ENCYCLOPEDIA.md",
        r"C:\Users\andre\Videos\MASTER_DATED_FACTS_INDEX.md",
        r"C:\Users\andre\Videos\MASTER_LITIGATION_ENCYCLOPEDIA_v2.md",
        r"C:\Users\andre\Videos\MASTER_LITIGATION_ENCYCLOPEDIA.md",
        r"C:\Users\andre\Videos\EVIDENTIARY_NARRATIVE_MCNEILL.md",
        r"C:\Users\andre\Videos\EVIDENTIARY_NARRATIVE_SHADY_OAKS.md",
        r"C:\Users\andre\Videos\MEGA_HARVEST_REPORT.md",
        r"C:\Users\andre\Videos\EVIDENCE_MINING_CYCLE6.md",
        r"C:\Users\andre\Videos\EVIDENCE_MINING_CYCLE1.md",
        r"C:\Users\andre\Videos\JUDICIAL_DOSSIER_MCNEILL.md",
        r"C:\Users\andre\Videos\IMPEACHMENT_PACKAGES.md",
        r"C:\Users\andre\Videos\FILING_PRIORITY_DASHBOARD.md",
    ]
    files.extend(videos)

    # DESKTOP KEY files
    desktop = [
        r"C:\Users\andre\Desktop\COMPREHENSIVE_CLAIM_RESEARCH.md",
        r"C:\Users\andre\Desktop\COMPREHENSIVE_JUDICIAL_ANALYSIS.md",
        r"C:\Users\andre\Desktop\MASTER_LITIGATION_ENCYCLOPEDIA.md",
        r"C:\Users\andre\Desktop\05_MSC_ORIGINAL_ACTION.md",
        r"C:\Users\andre\Desktop\SESSION_STATE_SAVE.md",
        r"C:\Users\andre\Desktop\AUTHORITY_INVENTORY.txt",
        r"C:\Users\andre\Desktop\AUTHORITY_INVENTORY_COMPLETE.txt",
    ]
    files.extend(desktop)

    # F:\ DRIVE — Filing documents
    f_filings = [
        r"F:\Hearing_Brief_Ex_Parte_PT_Pigors_v_Watson_v6.docx",
        r"F:\Hearing_Brief_Ex_Parte_PT_Pigors_v_Watson_v5.docx",
        r"F:\Hearing_Brief_Ex_Parte_PT_Pigors_v_Watson_v4.docx",
        r"F:\Hearing_Brief_Ex_Parte_PT_Pigors_v_Watson_v3.docx",
        r"F:\Pigors_ExParte_PT_Hearing_Brief_vFinal.docx",
        r"F:\Supervisory_Order_MCR_7.206_Pigors_v_Watson.docx",
        r"F:\Verified_Affidavit_Linked_FINAL.docx",
        r"F:\MOTION_CUSTODY_EmergencyPT_SHORT.docx",
        r"F:\Affidavit_Exhibit_A_CUSTODY_WEAVED_MEEK4.docx",
        r"F:\MOTION_PPO_TerminateVacateSanctions_SHORT.docx",
        r"F:\Affidavit_Exhibit_A_PPO_WEAVED_MEEK4.docx",
        r"F:\Motion_Disqualify_and_Refer_Chief_Judge_v1.1.docx",
        r"F:\Motion_to_Rescind_Suspension_Pigors_v_Watson.docx",
        r"F:\Proposed_Order_ParentingTime_Reinstatement.docx",
        r"F:\Affidavit_Pigors_Disqualification_v1.1.docx",
        r"F:\Canon_Violation_Brief_Pigors_v_Watson.docx",
        r"F:\Pigors_JTC_Structural_DueProcess_Canon_Narrative_v1.docx",
        r"F:\2025-10-29_COA_Brief_in_Support_v2.docx",
        r"F:\Pigors_COA_Application_Leave_ExParte_PT_Suspension_v1.docx",
        r"F:\2025-10-29_COA_Complaint_Superintending_Control_v2.docx",
        r"F:\2025-10-29_JTC_Verified_Complaint_Captioned_Signed_Notarized_v6.docx",
        r"F:\2025-10-29_MSC_ExParte_Addendum_Captioned_Signed_Notarized_v6.docx",
        r"F:\Pigors_Hearing_Record_Building_Playbook_v1.docx",
        r"F:\Pigors_WDMI_1983_Framing_Memo_v1.docx",
        r"F:\Pigors_Parental_Alienation_Pattern_Memo_v1.docx",
        r"F:\CC379_Motion_Modify_Terminate_PPO_2023-5907-PP_2025-09-26.docx",
        r"F:\CC385_Order_Modify_Terminate_PPO_2023-5907-PP_2025-09-26.docx",
        r"F:\Verified_Complaint_ShadyOaks.docx",
        r"F:\MC-230_Emergency_TRO_Motion.docx",
    ]
    # Exhibits A through M
    for letter in 'ABCDEFGHIJKLM':
        f_filings.append(f"F:\\Exhibit_{letter}.docx")
    files.extend(f_filings)

    # F:\ DRIVE — Data/evidence files
    f_data = [
        r"F:\CLAIMS.json",
        r"F:\REFUTATION_MATRIX.csv",
        r"F:\EXHIBIT_MATRIX_FULL.csv",
        r"F:\circuit court docket mcneill custody.txt",
        r"F:\KNOWLEDGE_ALL.md",
        r"F:\ETERNAL_SUPERGRAPH_MASTER.json",
    ]
    files.extend(f_data)

    # F:\ DRIVE — Directories
    f_dirs = [
        r"F:\extracts", r"F:\01_FILINGS", r"F:\02_EVIDENCE",
        r"F:\03_LEGAL_DOCS", r"F:\04_CASE_DATA", r"F:\05_LEGAL_RESEARCH",
        r"F:\06_ARCHIVES", r"F:\06_TRANSCRIPTS", r"F:\07_CORRESPONDENCE",
        r"F:\Evidence", r"F:\exhibits", r"F:\federal",
        r"F:\shadyfiles", r"F:\shadynfiles2",
    ]

    # ── Build rows ──────────────────────────────────────────────────
    rows = []
    stats = {"total": 0, "by_category": {}, "by_lane": {}, "by_value": {}, "by_drive": {}}

    def process_entry(fpath, is_dir=False):
        filename = os.path.basename(fpath)
        drive = fpath[0] if len(fpath) >= 2 and fpath[1] == ':' else '?'
        ext = 'dir' if is_dir else (filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'none')
        category = detect_category(fpath, ext) if not is_dir else 'unknown'
        lane = detect_lane(fpath)
        value = detect_value(fpath, ext, category) if not is_dir else 'LOW'
        perps = detect_perpetrators(fpath)

        stats["total"] += 1
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        stats["by_lane"][lane] = stats["by_lane"].get(lane, 0) + 1
        stats["by_value"][value] = stats["by_value"].get(value, 0) + 1
        stats["by_drive"][drive] = stats["by_drive"].get(drive, 0) + 1

        return (drive, fpath, filename, ext, category, lane, value, perps, 0, scan_date)

    for fp in files:
        rows.append(process_entry(fp))
    for fp in f_dirs:
        rows.append(process_entry(fp, is_dir=True))

    # ── Insert into DB ──────────────────────────────────────────────
    conn.executemany("""
        INSERT OR REPLACE INTO multi_drive_catalog
        (drive, file_path, filename, extension, category, case_lane, evidence_value,
         perpetrator_relevance, ingested, scan_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()

    total_in_db = conn.execute("SELECT COUNT(*) FROM multi_drive_catalog").fetchone()[0]

    # ── Summary statistics ──────────────────────────────────────────
    print(f"\n  Cataloged {stats['total']} entries ({total_in_db} total in DB)")
    print(f"\n  By Drive:")
    for d, c in sorted(stats["by_drive"].items()):
        print(f"    {d}: → {c} files")
    print(f"\n  By Category:")
    for cat, c in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        print(f"    {cat}: {c}")
    print(f"\n  By Evidence Value:")
    for v, c in sorted(stats["by_value"].items()):
        print(f"    {v}: {c}")
    print(f"\n  By Case Lane:")
    for lane, c in sorted(stats["by_lane"].items()):
        print(f"    {lane}: {c}")

    # HIGH value items
    high_items = safe_query(conn,
        "SELECT file_path, category, case_lane FROM multi_drive_catalog WHERE evidence_value='HIGH' ORDER BY category")
    print(f"\n  HIGH-VALUE Evidence ({len(high_items)} items):")
    for r in high_items[:30]:
        print(f"    [{r[1]:15s}] [{r[2]:5s}] {r[0]}")
    if len(high_items) > 30:
        print(f"    ... and {len(high_items) - 30} more")

    # Perpetrator-linked items
    perp_items = safe_query(conn,
        "SELECT perpetrator_relevance, COUNT(*) FROM multi_drive_catalog WHERE perpetrator_relevance != '' GROUP BY perpetrator_relevance ORDER BY COUNT(*) DESC")
    if perp_items:
        print(f"\n  Perpetrator-Linked Files:")
        for r in perp_items:
            print(f"    {r[0]}: {r[1]} files")

    # ── Generate reports ────────────────────────────────────────────
    report_data = {
        "tool": "#263 Multi-Drive Evidence Catalog",
        "generated": scan_date,
        "total_entries": stats["total"],
        "total_in_db": total_in_db,
        "by_drive": stats["by_drive"],
        "by_category": stats["by_category"],
        "by_value": stats["by_value"],
        "by_lane": stats["by_lane"],
        "high_value_count": len(high_items),
        "high_value_items": [{"path": r[0], "category": r[1], "lane": r[2]} for r in high_items],
        "perpetrator_links": {r[0]: r[1] for r in perp_items} if perp_items else {}
    }

    json_path = os.path.join(report_dir, "tool_263_multi_drive_catalog.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    md_lines = [
        "# Tool #263: Multi-Drive Evidence Catalog",
        f"Generated: {scan_date}",
        "",
        f"## Summary",
        f"- **Total entries cataloged**: {stats['total']}",
        f"- **Total in DB**: {total_in_db}",
        "",
        "## By Drive",
    ]
    for d, c in sorted(stats["by_drive"].items()):
        md_lines.append(f"- **{d}:\\** → {c} files")
    md_lines.append("")
    md_lines.append("## By Category")
    md_lines.append("| Category | Count |")
    md_lines.append("|----------|-------|")
    for cat, c in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        md_lines.append(f"| {cat} | {c} |")
    md_lines.append("")
    md_lines.append("## By Evidence Value")
    md_lines.append("| Value | Count |")
    md_lines.append("|-------|-------|")
    for v, c in sorted(stats["by_value"].items()):
        md_lines.append(f"| {v} | {c} |")
    md_lines.append("")
    md_lines.append("## By Case Lane")
    md_lines.append("| Lane | Count |")
    md_lines.append("|------|-------|")
    for lane, c in sorted(stats["by_lane"].items()):
        md_lines.append(f"| {lane} | {c} |")
    md_lines.append("")
    md_lines.append("## HIGH-Value Evidence Files")
    md_lines.append("| Path | Category | Lane |")
    md_lines.append("|------|----------|------|")
    for r in high_items:
        md_lines.append(f"| `{r[0]}` | {r[1]} | {r[2]} |")
    md_lines.append("")
    if perp_items:
        md_lines.append("## Perpetrator-Linked Files")
        md_lines.append("| Perpetrator(s) | Count |")
        md_lines.append("|----------------|-------|")
        for r in perp_items:
            md_lines.append(f"| {r[0]} | {r[1]} |")

    md_path = os.path.join(report_dir, "tool_263_multi_drive_catalog.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"\n  Reports written:")
    print(f"    {json_path}")
    print(f"    {md_path}")

    conn.close()
    print("\n" + "=" * 70)
    print("TOOL #263 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
