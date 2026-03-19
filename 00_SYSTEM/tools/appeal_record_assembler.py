#!/usr/bin/env python3
"""
Tool #61 — Appeal Record Assembler
======================================
Assembles the lower court record for COA appeal (366810).
Per MCR 7.210, the record on appeal includes:
1. Original papers filed in lower court
2. Transcript of proceedings (or settled statement)
3. Exhibits admitted into evidence
4. Register of actions (docket)

This tool compiles everything available in the DB and filing packages
into a structured record index for COA submission.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

def get_docket_events(conn):
    """Try to get docket events from various tables."""
    events = []
    
    for table in ['docket_events', 'timeline_events', 'case_events', 'case_timeline']:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if not cols:
                continue
            
            # Find date and description columns
            date_col = next((c for c in cols if 'date' in c.lower()), None)
            desc_col = next((c for c in cols if any(t in c.lower() for t in ['description', 'event', 'action', 'text', 'detail'])), None)
            
            if date_col and desc_col:
                rows = conn.execute(f"SELECT {date_col}, {desc_col} FROM {table} ORDER BY {date_col} LIMIT 200").fetchall()
                for row in rows:
                    events.append({'date': str(row[0]), 'description': str(row[1]), 'source': table})
        except:
            continue
    
    return events

def get_judicial_orders(conn):
    """Get documented judicial orders/violations."""
    orders = []
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(judicial_violations)").fetchall()]
        date_col = next((c for c in cols if 'date' in c.lower()), cols[0] if cols else None)
        desc_col = next((c for c in cols if any(t in c.lower() for t in ['violation', 'description', 'finding', 'text'])), cols[1] if len(cols) > 1 else None)
        
        if date_col and desc_col:
            rows = conn.execute(f"""
                SELECT {date_col}, {desc_col} 
                FROM judicial_violations 
                ORDER BY {date_col} 
                LIMIT 100
            """).fetchall()
            for row in rows:
                orders.append({'date': str(row[0]), 'description': str(row[1][:200])})
    except:
        pass
    return orders

def scan_existing_documents():
    """Scan filing packages for documents that form the record."""
    docs = []
    
    # Scan all PKG directories
    for pkg_dir in sorted(PKG_BASE.glob("PKG_F*")):
        for md_file in sorted(pkg_dir.glob("*.md")):
            if '.bak.' in md_file.name:
                continue
            size = md_file.stat().st_size
            docs.append({
                'filing': pkg_dir.name.split('_')[1],
                'file': md_file.name,
                'size': size,
                'path': str(md_file),
            })
    
    # Scan PDF output
    pdf_dir = PKG_BASE / "PDF_OUTPUT"
    if pdf_dir.exists():
        for pdf in sorted(pdf_dir.rglob("*.pdf")):
            docs.append({
                'filing': pdf.parent.name,
                'file': pdf.name,
                'size': pdf.stat().st_size,
                'path': str(pdf),
            })
    
    return docs

def main():
    print("=" * 70)
    print("APPEAL RECORD ASSEMBLER — Tool #61")
    print(f"COA Case No. 366810")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    
    # Gather components
    docket = get_docket_events(conn)
    orders = get_judicial_orders(conn)
    docs = scan_existing_documents()
    conn.close()
    
    # Categorize documents
    lower_court = [d for d in docs if d['filing'] in ['F1','F2','F3','F7']]
    appellate = [d for d in docs if d['filing'] in ['F8','F9']]
    other = [d for d in docs if d['filing'] not in ['F1','F2','F3','F7','F8','F9']]
    pdfs = [d for d in docs if d['file'].endswith('.pdf')]
    
    print(f"\n📋 Docket events found: {len(docket)}")
    print(f"⚖️  Judicial orders/violations: {len(orders)}")
    print(f"📄 Lower court documents: {len(lower_court)}")
    print(f"📑 Appellate documents: {len(appellate)}")
    print(f"📎 PDFs available: {len(pdfs)}")
    
    # Generate record index
    lines = [
        "# APPEAL RECORD INDEX",
        "## COA Case No. 366810",
        f"### Pigors v. Watson",
        f"### Lower Court: 14th Circuit Court, Case No. 2024-001507-DC",
        f"*Assembled: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "---\n",
        "## MCR 7.210 Record Requirements",
        "The record on appeal consists of:",
        "1. **Original papers filed in the trial court** (§7.210(A)(1))",
        "2. **Transcript of testimony** or settled statement (§7.210(A)(2) / §7.210(B))",
        "3. **Exhibits** admitted or offered for admission (§7.210(A)(3))",
        "4. **Register of actions** maintained by clerk (§7.210(A)(4))\n",
        "---\n",
        "## Part 1: Lower Court Papers (MCR 7.210(A)(1))",
        "| # | Filing | Document | Size |",
        "|---|--------|----------|------|",
    ]
    
    for i, doc in enumerate(lower_court, 1):
        size_str = f"{doc['size']//1024}KB" if doc['size'] > 1024 else f"{doc['size']}B"
        lines.append(f"| {i} | {doc['filing']} | {doc['file']} | {size_str} |")
    
    lines.extend([
        "",
        "## Part 2: Transcript / Settled Statement (MCR 7.210(B))",
        "",
    ])
    
    # Check for settled statement
    settled = PKG_BASE / "PKG_F9_COA_APPEAL_BRIEF" / "01D_SETTLED_STATEMENT.md"
    if not settled.exists():
        for p in PKG_BASE.glob("PKG_F9_*"):
            s = p / "01D_SETTLED_STATEMENT.md"
            if s.exists():
                settled = s
                break
    
    if settled.exists():
        lines.extend([
            "✅ **Settled Statement prepared** (MCR 7.210(B)(2))",
            f"- File: `{settled.name}`",
            f"- Location: `{settled.parent.name}/`",
            "",
            "> **Andrew must:** Serve proposed settled statement on opposing party.",
            "> Opposing party has 14 days to object per MCR 7.210(B)(2)(b).",
            "> If no objection, statement is deemed accurate.",
        ])
    else:
        lines.extend([
            "⚠️ **No transcript or settled statement found**",
            "- Request transcript from court reporter, OR",
            "- Prepare settled statement per MCR 7.210(B)(2)",
        ])
    
    lines.extend([
        "",
        "## Part 3: Exhibits (MCR 7.210(A)(3))",
        "",
        "Exhibits are documented in each filing's exhibit index (03_EXHIBIT_INDEX.md).",
        "",
    ])
    
    exhibit_count = 0
    for pkg in sorted(PKG_BASE.glob("PKG_F*")):
        exhibit_file = pkg / "03_EXHIBIT_INDEX.md"
        if exhibit_file.exists():
            exhibit_count += 1
            lines.append(f"- ✅ {pkg.name}: `03_EXHIBIT_INDEX.md`")
    
    lines.extend([
        f"\n*{exhibit_count} exhibit indexes available*",
        "",
        "## Part 4: Register of Actions (MCR 7.210(A)(4))",
        "",
    ])
    
    if docket:
        lines.extend([
            f"**{len(docket)} docket events found in database:**",
            "| Date | Event | Source |",
            "|------|-------|--------|",
        ])
        for evt in docket[:50]:
            lines.append(f"| {evt['date']} | {evt['description'][:80]} | {evt['source']} |")
    else:
        lines.extend([
            "⚠️ **No docket events in database**",
            "",
            "> **Andrew must:** Request certified register of actions from 14th Circuit Court Clerk.",
            "> Address: 990 Terrace St, Muskegon, MI 49442",
            "> Phone: (231) 724-6241",
        ])
    
    lines.extend([
        "",
        "## Part 5: Judicial Violations (Supporting Record)",
        f"**{len(orders)} documented violations by Judge McNeill:**",
        "",
    ])
    
    if orders:
        for i, order in enumerate(orders[:20], 1):
            lines.append(f"{i}. [{order['date']}] {order['description']}")
    
    lines.extend([
        "",
        "---",
        "## PDF Documents Ready for Filing",
        f"**{len(pdfs)} court-ready PDFs available:**",
        "",
    ])
    
    pdf_by_filing = {}
    for pdf in pdfs:
        pdf_by_filing.setdefault(pdf['filing'], []).append(pdf['file'])
    
    for filing, files in sorted(pdf_by_filing.items()):
        lines.append(f"### {filing} ({len(files)} PDFs)")
        for f in files:
            lines.append(f"- `{f}`")
    
    lines.extend([
        "",
        "---",
        "## Filing Checklist for COA 366810",
        "- [ ] Claim of appeal (if not already filed)",
        "- [ ] Docketing statement",
        "- [ ] Proof of service on all parties",
        "- [ ] Appellant brief (F9: 01_MAIN_FILING.md → PDF)",
        "- [ ] Appendix with lower court record",
        "- [ ] Settled statement (served and finalized)",
        "- [ ] IFP application (if needed — see 09_IFP_APPLICATION.md)",
        "- [ ] Certificate of compliance (word count)",
        "",
        f"*Record assembled by Tool #61 — {len(docs)} documents indexed*",
    ])
    
    md_path = REPORTS_DIR / "APPEAL_RECORD_INDEX.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "appeal_record.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Appeal Record Assembler (#61)',
        'coa_case': '366810',
        'lower_court_case': '2024-001507-DC',
        'docket_events': len(docket),
        'judicial_orders': len(orders),
        'lower_court_docs': len(lower_court),
        'appellate_docs': len(appellate),
        'total_pdfs': len(pdfs),
        'exhibit_indexes': exhibit_count,
        'settled_statement': settled.exists() if settled else False,
    }, indent=2, default=str), encoding='utf-8')
    
    # Save to F9 package
    for pkg in PKG_BASE.glob("PKG_F9_*"):
        record_path = pkg / "10_APPEAL_RECORD_INDEX.md"
        record_path.write_text('\n'.join(lines), encoding='utf-8')
        print(f"\n✅ Record index saved to {pkg.name}/10_APPEAL_RECORD_INDEX.md")
    
    print(f"✅ Reports: {md_path.name}, {json_path.name}")
    print(f"📋 Record: {len(docket)} docket events, {len(orders)} violations, {len(docs)} documents, {len(pdfs)} PDFs")

if __name__ == '__main__':
    main()
