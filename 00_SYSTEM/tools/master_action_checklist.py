#!/usr/bin/env python3
"""
Tool #68 — Master Action Checklist Generator
================================================
THE capstone document: a single, prioritized checklist of EVERYTHING
Andrew needs to do to file all 10 actions.

Pulls from ALL prior tools to create one unified action plan.
This is the "what do I do next?" document.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

def count_packages():
    """Count files in filing packages."""
    total = 0
    per_pkg = {}
    for pkg in sorted(PKG_BASE.glob("PKG_F*")):
        files = [f for f in pkg.iterdir() if f.suffix == '.md' and '.bak.' not in f.name]
        per_pkg[pkg.name] = len(files)
        total += len(files)
    return total, per_pkg

def count_pdfs():
    """Count generated PDFs."""
    pdf_dir = PKG_BASE / "PDF_OUTPUT"
    if not pdf_dir.exists():
        return 0
    return len(list(pdf_dir.rglob("*.pdf")))

def count_tools():
    """Count tools built."""
    return len(list((REPO / "00_SYSTEM" / "tools").glob("*.py")))

def count_reports():
    """Count reports generated."""
    return len(list(REPORTS_DIR.glob("*.md"))) + len(list(REPORTS_DIR.glob("*.json")))

def main():
    print("=" * 70)
    print("MASTER ACTION CHECKLIST — Tool #68")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)
    
    total_files, per_pkg = count_packages()
    pdf_count = count_pdfs()
    tool_count = count_tools()
    report_count = count_reports()
    
    lines = [
        "# 🎯 MASTER ACTION CHECKLIST",
        f"## Pigors v. Watson — All 10 Filings",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*{total_files} package files | {pdf_count} PDFs | {tool_count} tools | {report_count} reports*\n",
        "---\n",
        "# PHASE 1: PREPARATION (Before Any Filing)\n",
        "## 🔴 Critical — Do These First",
        "- [ ] **Register for MiFILE** — mifile.courts.michigan.gov/register",
        "      - Required for ALL state court filings (F1, F2, F3, F7)",
        "      - Takes 1-3 business days to process",
        "",
        "- [ ] **Register for PACER/CM-ECF** — pacer.uscourts.gov",
        "      - Required for federal court filing (F4)",
        "      - Takes 1-5 business days to process",
        "",
        "- [ ] **Review ALL 10 affidavits** — in each PKG_F*/02_AFFIDAVIT.md",
        "      - These are SWORN STATEMENTS — read every word carefully",
        "      - Correct any errors before signing",
        "      - Must be notarized OR signed under penalty of perjury",
        "      - ⚠️ FALSE statements = perjury (MCL 750.423)",
        "",
        "- [ ] **Call COA Clerk** — (517) 373-0786",
        "      - Confirm brief deadline for COA 366810",
        "      - This may be the most time-sensitive deadline",
        "",
        "## 🟡 High Priority — Complete Within 3 Days",
        "- [ ] **Gather financial information for IFP applications**",
        "      - Monthly income from ALL sources",
        "      - Monthly expenses (rent, utilities, food, medical, transportation)",
        "      - Bank account balances",
        "      - Vehicle value and loan balance",
        "      - List of dependents (L.D.W.)",
        "      - Government assistance received (SNAP, Medicaid, SSI, etc.)",
        "",
        "- [ ] **Complete MC 20 form** (Michigan fee waiver) — courts.michigan.gov/scao-forms",
        "      - One form for circuit court (covers F1, F2, F3, F7)",
        "      - One form for COA (covers F8, F9)",
        "      - One form for MSC (covers F5)",
        "",
        "- [ ] **Complete AO 240 form** (federal fee waiver) — uscourts.gov",
        "      - For F4 (§1983 federal complaint)",
        "",
        "- [ ] **Get Ronald Berry's current address**",
        "      - Needed for service if named in F4",
        "      - May be at Emily's address: 2160 Garland Drive, Norton Shores",
        "",
        "- [ ] **Get LARA registered agent addresses**",
        "      - Shady Oaks / Cricklewood registered agents for F2 housing claims",
        "      - Check: lara.michigan.gov/colaentitysearch",
        "",
        "- [ ] **Print all filings** (3 copies each: court + opposing party + yourself)",
        "      - PDFs ready at: Desktop\\LITIGATION_FILING_PACKAGE\\PDF_OUTPUT\\",
        f"      - {pdf_count} PDFs ready to print",
        "",
        "- [ ] **Buy supplies**",
        "      - Tab dividers (for exhibits)",
        "      - Manila envelopes (9x12, for mailing)",
        "      - Certified mail forms (USPS)",
        "      - Blue pen (for signing — never black, to distinguish originals)",
        "",
        "---\n",
        "# PHASE 2: WAVE 1 FILING (Day 1)\n",
        "## File F1 + F3 simultaneously\n",
        "- [ ] **Sign F1 affidavit** (notarize if possible)",
        "- [ ] **Sign F3 affidavit** (notarize if possible)",
        "- [ ] **E-file F1 via MiFILE** — Emergency Parenting Time Motion",
        "      - Include: MC 20 (IFP), motion, affidavit, exhibit index, cert of service",
        "- [ ] **E-file F3 via MiFILE** — Judicial Disqualification Motion",
        "      - Include: motion, brief, affidavit, cert of service",
        "- [ ] **Serve Emily Watson** — certified mail to 2160 Garland Drive, Norton Shores, MI 49441",
        "      - Send copies of F1 AND F3",
        "      - Keep certified mail receipt (green card)",
        "- [ ] **File proof of service** with court (use 04_CERTIFICATE_OF_SERVICE.md template)",
        "",
        "---\n",
        "# PHASE 3: WAVE 2 — FREE COMPLAINTS (Day 3)\n",
        "- [ ] **Mail F6 to JTC** — 3034 W Grand Blvd, Ste 8-450, Detroit, MI 48202",
        "      - Or email: jtc@jtc.courts.mi.gov",
        "      - FREE — no filing fee",
        "- [ ] **File F10 with AGC** — online at agcmi.com",
        "      - Or mail: 535 Griswold, Ste 1700, Detroit, MI 48226",
        "      - FREE — no filing fee",
        "",
        "---\n",
        "# PHASE 4: WAVE 3 — CORE LITIGATION (Day 7-8)\n",
        "- [ ] **Sign F2 affidavit**",
        "- [ ] **E-file F2 via MiFILE** — Fraud Upon the Court Complaint",
        "      - Request summons from clerk",
        "- [ ] **Arrange personal service** for F2 on Emily Watson",
        "      - Use process server (not yourself — MCR 2.103(A))",
        "      - 91 days to complete service (MCR 2.102(D))",
        "- [ ] **Sign F7 affidavit**",
        "- [ ] **E-file F7 via MiFILE** — Custody Modification Motion + Brief",
        "- [ ] **Serve Emily Watson** with F7 (certified mail)",
        "",
        "---\n",
        "# PHASE 5: WAVE 4 — BYPASS (Day 14-21)\n",
        "- [ ] **Sign F4 affidavit**",
        "- [ ] **File F4 via CM/ECF** — 42 USC §1983 Federal Complaint",
        "      - Include AO 240 (IFP) + complaint + affidavit",
        "      - If IFP granted, request US Marshals service",
        "- [ ] **Serve Michigan Attorney General** with F4 (certified mail to Lansing)",
        "- [ ] **Sign F5 affidavit**",  
        "- [ ] **File F5 via TrueFiling** — MSC Superintending Control",
        "      - Include MC 20 (IFP) + complaint + supporting docs",
        "- [ ] **Serve Emily Watson** with F5 (certified mail)",
        "",
        "---\n",
        "# PHASE 6: WAVE 5 — APPELLATE (Day 14-30)\n",
        "- [ ] **Serve settled statement** on Emily Watson (14 days before brief due)",
        "- [ ] **File F9 via TrueFiling** — COA 366810 Appeal Brief",
        "- [ ] **File F8 via TrueFiling** — COA Application for Leave (new)",
        "      - Include MC 20 (IFP)",
        "- [ ] **Serve Emily Watson** with F8 and F9 (first class mail)",
        "",
        "---\n",
        "# PHASE 7: POST-FILING MONITORING\n",
        "- [ ] Check MiFILE daily for court responses",
        "- [ ] Check PACER for federal court activity",
        "- [ ] Check TrueFiling for COA/MSC responses",
        "- [ ] Track all response deadlines (see DEADLINE_TRACKER.md)",
        "- [ ] Prepare for F1 emergency hearing (see 08_HEARING_PREP_KIT.md)",
        "- [ ] Prepare for F3 disqualification hearing (see 08_HEARING_PREP_KIT.md)",
        "- [ ] File replies to any motions to dismiss within 7 days (MCR 2.119(F))",
        "",
        "---\n",
        "# 💰 COST SUMMARY",
        "| Scenario | Total Cost |",
        "|----------|-----------|",
        "| Without IFP | $2,030 |",
        "| With IFP approved | $525 |",
        "| Savings | $1,505 (74%) |",
        "",
        "---\n",
        "# 📁 YOUR FILING PACKAGES",
        "All packages at: `Desktop\\LITIGATION_FILING_PACKAGE\\`\n",
        "| Package | Files | Status |",
        "|---------|-------|--------|",
    ]
    
    for pkg_name, count in sorted(per_pkg.items()):
        lines.append(f"| {pkg_name} | {count} files | ✅ Ready |")
    
    lines.extend([
        "",
        f"\n**Total: {total_files} package files + {pdf_count} court-ready PDFs**",
        "",
        "---",
        "# 📋 REFERENCE DOCUMENTS",
        "All in `00_SYSTEM/reports/`:",
        "- `MASTER_STRATEGY.md` — Overall strategy and filing order",
        "- `FILING_SEQUENCE.md` — 5-wave, 30-day filing plan",
        "- `DEADLINE_TRACKER.md` — All deadlines with urgency levels",
        "- `SERVICE_OF_PROCESS_GUIDE.md` — Who to serve, how, when",
        "- `LITIGATION_COST_ESTIMATE.md` — Cost breakdown with/without IFP",
        "- `IFP_APPLICATIONS.md` — Fee waiver instructions for each court",
        "- `PRO_SE_COURTROOM_PROTOCOL.md` — Courtroom behavior guide",
        "- `RESPONSE_ANTICIPATOR.md` — Expected opposition + rebuttals",
        "- `EVIDENCE_GAP_ANALYSIS.md` — Strength of evidence per claim",
        "- `SANCTIONS_RISK_REPORT.md` — Risk assessment (score: 360)",
        "- `CONVERGENCE_DASHBOARD.md` — Overall GO/NO-GO assessment",
        "- `APPEAL_RECORD_INDEX.md` — COA 366810 record compilation",
        "- `LAWSUIT_TARGET_HARVEST.md` — Evidence per target (15,636 items)",
        "",
        "---",
        f"*Generated by Tool #68 — Master Action Checklist*",
        f"*{tool_count} tools built | {total_files} files | {pdf_count} PDFs | {report_count} reports*",
    ])
    
    md_path = REPORTS_DIR / "MASTER_ACTION_CHECKLIST.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    # Also save to top level of filing package
    top_level = PKG_BASE / "00_MASTER_ACTION_CHECKLIST.md"
    top_level.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "master_checklist.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Master Action Checklist (#68)',
        'package_files': total_files,
        'pdfs': pdf_count,
        'tools': tool_count,
        'reports': report_count,
        'phases': 7,
        'packages': per_pkg,
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Master checklist generated")
    print(f"   {total_files} package files | {pdf_count} PDFs | {tool_count} tools | {report_count} reports")
    print(f"   Saved to: reports/ AND top of filing package")

if __name__ == '__main__':
    main()
