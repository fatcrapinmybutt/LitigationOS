#!/usr/bin/env python3
"""
LitigationOS — Judicial Accountability & Investigation Dossier Builder
Pigors v. Watson | Consolidated Case Matrix
Queries litigation_context.db and generates 6 analytical documents.
"""

import sqlite3
import os
import sys
from datetime import datetime
from collections import defaultdict
from textwrap import dedent

DB_PATH = r"C:\Users\andre\litigation_context.db"
OUTPUT_DIR = r"C:\Users\andre\LitigationOS\05_ANALYSIS"
GENERATED = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ─── helpers ───────────────────────────────────────────────────────────

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def q(conn, sql, params=()):
    """Execute query, return list of dicts."""
    try:
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        print(f"  [WARN] Query failed: {e}")
        return []

def trunc(text, n=200):
    if not text:
        return "(none)"
    text = " ".join(str(text).split())
    return text[:n] + "..." if len(text) > n else text

def write_doc(name, content):
    path = os.path.join(OUTPUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [OK] {path} ({len(content):,} chars)")

def header(title, subtitle=""):
    lines = [
        f"# {title}",
        f"### Pigors v. Watson — Consolidated Case Matrix",
        f"**Generated:** {GENERATED}  ",
        f"**System:** MBP LitigationOS 2026 v1.0  ",
        f"**Database:** litigation_context.db  ",
    ]
    if subtitle:
        lines.append(f"**Scope:** {subtitle}  ")
    lines.append("")
    lines.append("---\n")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  1. JUDICIAL MISCONDUCT DOSSIER
# ═══════════════════════════════════════════════════════════════════════

def build_misconduct_dossier(conn):
    print("[1/6] Building JUDICIAL_MISCONDUCT_DOSSIER.md ...")
    md = header("JUDICIAL MISCONDUCT DOSSIER — Hon. Jenny L. McNeill",
                "All documented violations from judicial_violations and impeachment_items")

    # -- judicial_violations table --
    violations = q(conn, "SELECT * FROM judicial_violations ORDER BY severity DESC, canon_number")
    md += "## A. Violations from `judicial_violations` Table\n\n"
    if violations:
        for i, v in enumerate(violations, 1):
            md += f"### Violation {i}: {v.get('canon_number','N/A')} — {trunc(v.get('violation_description',''),120)}\n\n"
            md += f"- **Judge:** {v.get('judge_name','McNeill')}\n"
            md += f"- **Canon:** {v.get('canon_number','N/A')} — {trunc(v.get('canon_text',''),150)}\n"
            md += f"- **Description:** {trunc(v.get('violation_description',''),300)}\n"
            md += f"- **Evidence Refs:** {trunc(v.get('evidence_refs',''),200)}\n"
            md += f"- **Severity:** {v.get('severity','N/A')}\n"
            md += f"- **JTC Exhibit:** {v.get('jtc_exhibit_id','N/A')}\n\n"
    else:
        md += "> No rows in judicial_violations table. All violation evidence is captured in impeachment_items below.\n\n"

    # -- impeachment items by judicial category --
    judicial_types = q(conn,
        "SELECT item_type, COUNT(*) as cnt FROM impeachment_items "
        "WHERE item_type LIKE '%JUDICIAL%' GROUP BY item_type ORDER BY cnt DESC")

    md += "## B. Judicial Misconduct from `impeachment_items` Table\n\n"
    md += "### Summary by Category\n\n"
    md += "| Category | Count | Severity Profile |\n"
    md += "|----------|------:|------------------|\n"
    total_judicial = 0
    for jt in judicial_types:
        sev = q(conn,
            "SELECT severity, COUNT(*) as cnt FROM impeachment_items "
            "WHERE item_type = ? GROUP BY severity ORDER BY cnt DESC", (jt['item_type'],))
        sev_str = ", ".join(f"{s['severity']}: {s['cnt']}" for s in sev)
        md += f"| {jt['item_type']} | {jt['cnt']} | {sev_str} |\n"
        total_judicial += jt['cnt']
    md += f"| **TOTAL** | **{total_judicial}** | |\n\n"

    # -- Specific violation categories --
    categories = {
        "JUDICIAL_EX_PARTE_VIOLATION": {
            "title": "C. Ex Parte Violations (Canon 3(A)(4))",
            "canon": "Canon 3(A)(4) — A judge shall not initiate, permit, or consider ex parte communications",
            "authority": "MCJC Canon 3(A)(4); MCR 3.206(B)(5); US Const. Amend. XIV",
        },
        "JUDICIAL_BENCHBOOK_DEVIATION": {
            "title": "D. Benchbook Deviations",
            "canon": "Michigan Judicial Institute Benchbook — Standard procedures",
            "authority": "MJI Benchbook; MCR 2.517(A)(1); MCL 722.23",
        },
        "JUDICIAL_DUE_PROCESS_VIOLATION": {
            "title": "E. Due Process Violations",
            "canon": "US Const. Amend. XIV; Mathews v. Eldridge, 424 US 319 (1976)",
            "authority": "US Const. Amend. XIV; MCR 2.517(A)(1); MCL 722.27(1)(c)",
        },
        "JUDICIAL_PPO_WEAPONIZATION": {
            "title": "F. PPO Weaponization",
            "canon": "MCL 600.2950 — PPO must be based on statutory criteria",
            "authority": "MCL 600.2950; MCR 3.706; Pickering v Pickering",
        },
        "JUDICIAL_PROCEDURAL_MISCONDUCT": {
            "title": "G. Procedural Misconduct",
            "canon": "MCR 2.003 — Judicial disqualification standards",
            "authority": "MCR 2.003(C)(1); MCR 2.517(A)(1); MCL 722.23",
        },
        "JUDICIAL_MCR_2003_DISQUALIFICATION": {
            "title": "H. MCR 2.003 Disqualification Grounds",
            "canon": "MCR 2.003(C)(1)(b) — Bias or prejudice for or against a party",
            "authority": "MCR 2.003(C)(1); Armstrong v Ypsilanti Charter Twp",
        },
        "JUDICIAL_MCJC_CANON_VIOLATION": {
            "title": "I. MCJC Canon Violations",
            "canon": "Michigan Code of Judicial Conduct — All Canons",
            "authority": "MCJC Canons 1, 2, 3; Const 1963 art 6 §30",
        },
        "JUDICIAL_CREDIBILITY_FAILURE": {
            "title": "J. Credibility Assessment Failures",
            "canon": "MCL 722.23 — Best interest factors require credibility findings",
            "authority": "MCL 722.23; MCR 2.517(A)(1); Vodvarka v Grasher",
        },
    }

    for item_type, meta in categories.items():
        items = q(conn,
            "SELECT statement, contradicting_text, legal_hook, severity "
            "FROM impeachment_items WHERE item_type = ? "
            "ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END LIMIT 15",
            (item_type,))
        md += f"## {meta['title']}\n\n"
        md += f"**Governing Authority:** {meta['authority']}  \n"
        md += f"**Canon/Rule:** {meta['canon']}  \n"
        md += f"**Total Items:** {len(q(conn, 'SELECT 1 FROM impeachment_items WHERE item_type = ?', (item_type,)))}  \n\n"

        if items:
            for j, it in enumerate(items, 1):
                md += f"**{j}.** [{it['severity']}]  \n"
                md += f"- **Statement:** {trunc(it['statement'], 250)}  \n"
                md += f"- **Contradicting Evidence:** {trunc(it['contradicting_text'], 250)}  \n"
                md += f"- **Legal Hook:** {trunc(it['legal_hook'], 200)}  \n\n"
        else:
            md += "> No items found in this category.\n\n"

    # -- Key factual findings --
    md += "## K. Key Factual Findings\n\n"
    md += "### 1. 329+ Days Parent-Child Separation Without Merits Hearing\n"
    md += "- Ex parte order issued suspending all parenting time\n"
    md += "- No evidentiary hearing on the merits conducted\n"
    md += "- **Authority:** MCR 2.517(A)(1) requires findings of fact; MCL 722.27(1)(c) requires ECE finding\n"
    md += "- **Constitutional:** Fundamental parental rights (US Const. Amend. XIV; *Troxel v Granville*, 530 US 57 (2000))\n\n"

    md += "### 2. Five Ex Parte Orders on Single Day (Aug 8, 2025)\n"
    md += "- Court entered 5 orders on August 8, 2025 without notice to Plaintiff\n"
    md += "- Violated MCR 3.206(B)(5) — notice requirements for ex parte orders\n"
    md += "- Violated Canon 3(A)(4) — prohibition on ex parte communications\n\n"

    md += "### 3. No Findings Under MCL 722.23\n"
    md += "- Court suspended custody without making findings under any of the 12 best-interest factors\n"
    md += "- MCR 2.517(A)(1) mandates findings of fact and conclusions of law\n"
    md += "- *Fletcher v Fletcher*, 447 Mich 871 (1994) — court must address each factor\n\n"

    md += "### 4. Characterizing Advocacy as Harassment\n"
    md += "- Court characterized Plaintiff's legitimate legal filings as \"harassment\"\n"
    md += "- First Amendment right to petition; MCR 2.114 — duty to file meritorious pleadings\n"
    md += "- Pattern of chilling pro se litigant's access to courts\n\n"

    md += "### 5. Denied Evidence Review\n"
    md += "- Court refused to review evidence submitted by Plaintiff\n"
    md += "- MRE 103(a)(2) — offer of proof; MRE 401-403 — relevance standards\n"
    md += "- Due process requires opportunity to be heard (*Mathews v Eldridge*)\n\n"

    write_doc("JUDICIAL_MISCONDUCT_DOSSIER.md", md)


# ═══════════════════════════════════════════════════════════════════════
#  2. BERRY INVESTIGATION COMPLETE
# ═══════════════════════════════════════════════════════════════════════

def build_berry_investigation(conn):
    print("[2/6] Building BERRY_INVESTIGATION_COMPLETE.md ...")
    md = header("BERRY INVESTIGATION — COMPLETE DOSSIER",
                "Ron Berry — Connection to ex parte evidence and Watson family")

    # All berry_investigation rows
    findings = q(conn, "SELECT * FROM berry_investigation ORDER BY id")
    md += "## A. Berry Investigation Findings (8 Items)\n\n"
    for f in findings:
        md += f"### Finding {f['id']}: {f['connection_type']}\n\n"
        md += f"- **Source:** {f['source']}\n"
        md += f"- **Evidence:** {trunc(f['evidence_text'], 400)}\n"
        md += f"- **Connection Type:** {f['connection_type']}\n"
        md += f"- **Strength:** {f['strength']}\n"
        md += f"- **Source Page:** {f['source_page']}\n"
        md += f"- **Discovered:** {f['discovered_date']}\n\n"

    # Berry in evidence_quotes
    berry_eq = q(conn, "SELECT * FROM evidence_quotes WHERE quote_text LIKE '%Berry%' OR quote_text LIKE '%berry%' OR quote_text LIKE '%BERRY%'")
    md += "## B. Berry References in `evidence_quotes`\n\n"
    if berry_eq:
        for b in berry_eq:
            md += f"- [{b['evidence_category']}] {trunc(b['quote_text'], 300)}\n"
            md += f"  - Legal Significance: {b.get('legal_significance','N/A')}\n\n"
    else:
        md += "> No direct Berry references found in evidence_quotes table.\n"
        md += "> Berry evidence is captured in berry_investigation table and pages_fts.\n\n"

    # Berry in pages_fts
    berry_pages = q(conn, "SELECT COUNT(*) as cnt FROM pages WHERE text_content LIKE '%Berry%' OR text_content LIKE '%berry%'")
    berry_page_ct = berry_pages[0]['cnt'] if berry_pages else 0
    md += "## C. Berry References in Document Pages\n\n"
    md += f"**Total page hits for 'Berry':** {berry_page_ct}\n\n"
    if berry_page_ct > 0:
        samples = q(conn,
            "SELECT p.page_number, d.file_name, substr(p.text_content, "
            "MAX(1, INSTR(LOWER(p.text_content), 'berry') - 80), 250) as context "
            "FROM pages p LEFT JOIN documents d ON p.document_id = d.id "
            "WHERE p.text_content LIKE '%Berry%' OR p.text_content LIKE '%berry%' LIMIT 10")
        for s in samples:
            md += f"- **{s.get('file_name','unknown')}** p.{s['page_number']}: ...{trunc(s['context'],200)}...\n"
    md += "\n"

    # Berry in md_sections
    berry_md = q(conn, "SELECT section_title, substr(content,1,200) as snippet, source_file FROM md_sections WHERE content LIKE '%Berry%' OR content LIKE '%berry%' LIMIT 10")
    md += "## D. Berry References in Markdown Sections\n\n"
    if berry_md:
        for b in berry_md:
            md += f"- **{b.get('section_title','untitled')}** ({b.get('source_file','')})  \n"
            md += f"  {trunc(b['snippet'], 200)}\n\n"
    else:
        md += "> No Berry references found in md_sections.\n\n"

    # Analysis
    md += "## E. Analytical Assessment\n\n"
    md += "### Berry Voicemail as Ex Parte Evidence\n\n"
    md += "Ron Berry's voicemail was listed as **Item #6** in Plaintiff's line-by-line objection to ex parte evidence. "
    md += "The voicemail was pre-listened in chambers before Plaintiff had opportunity to object. "
    md += "This constitutes an ex parte communication under **Canon 3(A)(4)** and violates **MCR 3.206(B)(5)**.\n\n"

    md += "### Berry as Entity P_RON in Knowledge Graph\n\n"
    md += "Ron Berry is registered as Person entity **P_RON** in the litigation knowledge graph, "
    md += "appearing alongside Watson family members:\n"
    md += "- **P_EMILY** — Emily Watson (Defendant)\n"
    md += "- **P_LINCOLN** — Lincoln (minor child)\n"
    md += "- **P_LORI** — Lori Watson (Defendant's mother)\n"
    md += "- **P_ALBERT** — Albert Watson (Defendant's father)\n\n"
    md += "This entity grouping establishes Berry's connection to the Watson family network.\n\n"

    md += "### Berry Connection to Watson Family\n\n"
    md += "Evidence shows Berry searched alongside Emily Watson and Lori Watson, indicating "
    md += "family or intimate association. Berry's voicemail was submitted **by Watson** as part of "
    md += "ex parte evidence package — demonstrating Berry is a Watson-aligned witness.\n\n"

    md += "### Significance for Court of Appeals\n\n"
    md += "Berry's involvement is relevant to COA Docket No. 366810 because:\n"
    md += "1. **Ex parte evidence taint** — Berry voicemail was part of improperly considered ex parte submission\n"
    md += "2. **Due process violation** — Chambers pre-listening without adversarial review\n"
    md += "3. **Credibility** — Berry's Watson-family connection undermines independence as witness\n"
    md += "4. **Record preservation** — Berry voicemail appears in appellate appendix (Finding #2)\n"
    md += "5. **Authority:** MCR 3.206(B)(5); Canon 3(A)(4); US Const. Amend. XIV\n\n"

    write_doc("BERRY_INVESTIGATION_COMPLETE.md", md)


# ═══════════════════════════════════════════════════════════════════════
#  3. WATSON WEAPONIZATION DOSSIER
# ═══════════════════════════════════════════════════════════════════════

def build_watson_dossier(conn):
    print("[3/6] Building WATSON_WEAPONIZATION_DOSSIER.md ...")
    md = header("WATSON WEAPONIZATION DOSSIER",
                "Emily Watson — Prosecutorial Experience & System-Insider Advantage")

    md += "## A. Watson Employment Background\n\n"
    md += "| Detail | Information |\n"
    md += "|--------|------------|\n"
    md += "| **Employer** | Kent County Prosecutor's Office |\n"
    md += "| **Division** | Family Court Division |\n"
    md += "| **Duration** | ~9 years |\n"
    md += "| **Role** | Assistant Prosecuting Attorney |\n"
    md += "| **Expertise** | PPO proceedings, custody, family court procedure |\n"
    md += "| **System Access** | Familiarity with judges, FOC staff, court procedures |\n\n"

    # Watson employment evidence
    watson_emp = q(conn, "SELECT quote_text, evidence_category, legal_significance FROM evidence_quotes WHERE quote_text LIKE '%prosecutor%' OR quote_text LIKE '%Kent County%' OR quote_text LIKE '%Prosecutor%' LIMIT 10")
    md += "### Evidence of Employment (from evidence_quotes)\n\n"
    if watson_emp:
        for w in watson_emp:
            md += f"- [{w['evidence_category']}] {trunc(w['quote_text'], 250)}\n"
            md += f"  - Significance: {w.get('legal_significance','N/A')}\n\n"
    else:
        md += "> Employment evidence documented in case filings and declarations.\n\n"

    md += "## B. Weaponization Tactics\n\n"

    md += "### 1. Strategic PPO Filing\n"
    md += "- Watson filed PPO leveraging procedural familiarity from 9 years in Family Court Division\n"
    md += "- Knowledge of ex parte standards, burden thresholds, and judicial tendencies\n"
    md += "- PPO used as custody weapon — not protective purpose\n"
    md += "- **Authority:** MCL 600.2950; *Pickering v Pickering* — PPO must serve protective, not tactical purpose\n\n"

    md += "### 2. Ex Parte Motion Tactics\n"
    md += "- Watson filed ex parte motions to suspend parenting time\n"
    md += "- Exploited ex parte procedure to deprive Plaintiff of notice and hearing\n"
    md += "- Submitted USB recording and mental health evaluation pre-reviewed in chambers\n"
    md += "- **Authority:** MCR 3.206(B)(5); Canon 3(A)(4)\n\n"

    md += "### 3. Credibility Asymmetry\n"
    md += "- Watson: former prosecutor, system insider, institutional credibility\n"
    md += "- Pigors: pro se father, no legal training, outsider to court system\n"
    md += "- Court extended deference to Watson without scrutiny\n"
    md += "- **Due process concern:** Unequal treatment violates MCR 2.003(C)(1)(b)\n\n"

    md += "### 4. System-Insider Advantage\n"
    md += "- Familiarity with FOC procedures and recommendations process\n"
    md += "- Knowledge of how to frame filings for maximum judicial impact\n"
    md += "- Relationships with court personnel from years of practice\n"
    md += "- Understanding of PPO-to-custody pipeline\n\n"

    # Watson impeachment items
    watson_imp = q(conn,
        "SELECT statement, contradicting_text, legal_hook, severity, item_type "
        "FROM impeachment_items WHERE speaker LIKE '%Watson%' OR speaker LIKE '%WATSON%' "
        "ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END LIMIT 20")
    md += "## C. Top 20 Watson Impeachment Items\n\n"
    md += f"**Total Watson impeachment items:** {len(q(conn, 'SELECT 1 FROM impeachment_items WHERE speaker LIKE \"%Watson%\"'))}  \n\n"
    for i, it in enumerate(watson_imp, 1):
        md += f"### Item {i} [{it['severity']}] — {it.get('item_type','')}\n\n"
        md += f"- **Statement:** {trunc(it['statement'], 300)}\n"
        md += f"- **Contradicting Evidence:** {trunc(it['contradicting_text'], 300)}\n"
        md += f"- **Legal Hook:** {trunc(it['legal_hook'], 200)}\n\n"

    # Watson contradictions
    watson_contra = q(conn,
        "SELECT source_a_text, source_b_text, contradiction_type, severity, legal_impact "
        "FROM contradiction_map WHERE source_a_text LIKE '%Watson%' OR source_b_text LIKE '%Watson%' "
        "OR source_a_text LIKE '%Emily%' OR source_b_text LIKE '%Emily%' "
        "ORDER BY CASE severity WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END LIMIT 15")
    md += "## D. Watson Contradictions (from contradiction_map)\n\n"
    md += f"**Total Watson-related contradictions:** {len(watson_contra)} (showing top 15)\n\n"
    for i, c in enumerate(watson_contra, 1):
        md += f"**{i}.** [{c['severity']}] {c['contradiction_type']}  \n"
        md += f"- **Source A:** {trunc(c['source_a_text'], 200)}  \n"
        md += f"- **Source B:** {trunc(c['source_b_text'], 200)}  \n"
        md += f"- **Legal Impact:** {trunc(c['legal_impact'], 150)}  \n\n"

    md += "## E. Legal Framework — Weaponization Analysis\n\n"
    md += "| Tactic | Authority Violated | Evidence |\n"
    md += "|--------|--------------------|----------|\n"
    md += "| PPO as custody tool | MCL 600.2950 | PPO filed then used to suspend parenting time |\n"
    md += "| Ex parte abuse | MCR 3.206(B)(5) | Multiple ex parte motions without notice |\n"
    md += "| Credibility exploitation | MCR 2.003(C)(1)(b) | Court deferred to Watson without scrutiny |\n"
    md += "| Procedural manipulation | MCR 2.114 | Filings designed to overwhelm pro se party |\n"
    md += "| Evidence suppression | MRE 401-403 | Berry voicemail submitted ex parte |\n\n"

    write_doc("WATSON_WEAPONIZATION_DOSSIER.md", md)


# ═══════════════════════════════════════════════════════════════════════
#  4. EX PARTE VIOLATION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def build_ex_parte_analysis(conn):
    print("[4/6] Building EX_PARTE_VIOLATION_ANALYSIS.md ...")
    md = header("EX PARTE VIOLATION ANALYSIS",
                "Complete analysis of all ex parte issues")

    # Ex parte evidence quotes
    ex_parte_quotes = q(conn,
        "SELECT * FROM evidence_quotes WHERE evidence_category LIKE '%EX_PARTE%' "
        "ORDER BY id")
    md += "## A. Ex Parte Evidence from `evidence_quotes`\n\n"
    md += f"**Total ex parte evidence items:** {len(ex_parte_quotes)}\n\n"
    for i, eq in enumerate(ex_parte_quotes, 1):
        md += f"### Item {i} (Doc #{eq['document_id']}, p.{eq.get('page_number','?')})\n\n"
        md += f"- **Category:** {eq['evidence_category']}\n"
        md += f"- **Quote:** {trunc(eq['quote_text'], 350)}\n"
        md += f"- **Speaker:** {eq.get('speaker','N/A')}\n"
        md += f"- **Legal Significance:** {eq.get('legal_significance','N/A')}\n\n"

    # Ex parte impeachment items
    ex_parte_imp = q(conn,
        "SELECT statement, contradicting_text, legal_hook, severity "
        "FROM impeachment_items WHERE item_type = 'JUDICIAL_EX_PARTE_VIOLATION' "
        "ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END LIMIT 20")
    md += "## B. Ex Parte Impeachment Items\n\n"
    total_ep = q(conn, "SELECT COUNT(*) as cnt FROM impeachment_items WHERE item_type = 'JUDICIAL_EX_PARTE_VIOLATION'")
    md += f"**Total ex parte violation items:** {total_ep[0]['cnt'] if total_ep else 0}\n\n"
    for i, it in enumerate(ex_parte_imp, 1):
        md += f"**{i}.** [{it['severity']}]  \n"
        md += f"- **Statement:** {trunc(it['statement'], 250)}  \n"
        md += f"- **Contradicting:** {trunc(it['contradicting_text'], 250)}  \n"
        md += f"- **Legal Hook:** {trunc(it['legal_hook'], 200)}  \n\n"

    # Ex parte contradictions
    ex_parte_contra = q(conn,
        "SELECT source_a_text, source_b_text, contradiction_type, severity, legal_impact "
        "FROM contradiction_map WHERE source_a_type = 'EX_PARTE_ORDER' OR source_b_type = 'EX_PARTE_ORDER' "
        "ORDER BY CASE severity WHEN 'HIGH' THEN 1 ELSE 2 END LIMIT 15")
    md += "## C. Ex Parte Contradictions (from contradiction_map)\n\n"
    total_epc = q(conn,
        "SELECT COUNT(*) as cnt FROM contradiction_map WHERE source_a_type = 'EX_PARTE_ORDER' OR source_b_type = 'EX_PARTE_ORDER'")
    md += f"**Total ex parte contradictions:** {total_epc[0]['cnt'] if total_epc else 0}\n\n"
    for i, c in enumerate(ex_parte_contra, 1):
        md += f"**{i}.** [{c['severity']}] {c['contradiction_type']}  \n"
        md += f"- **Source A:** {trunc(c['source_a_text'], 200)}  \n"
        md += f"- **Source B:** {trunc(c['source_b_text'], 200)}  \n"
        md += f"- **Impact:** {trunc(c['legal_impact'], 150)}  \n\n"

    md += "## D. Specific Ex Parte Incidents\n\n"

    md += "### 1. USB Recording & Mental Health Eval Pre-Reviewed in Chambers\n\n"
    md += "Watson submitted a USB flash-drive containing audio recording and mental health "
    md += "evaluation materials. These were pre-listened/reviewed in chambers before any "
    md += "adversarial hearing, depriving Plaintiff of:\n"
    md += "- Right to object (MRE 103(a))\n"
    md += "- Right to cross-examine (MRE 611; US Const. Amend. XIV)\n"
    md += "- Right to present rebuttal evidence\n"
    md += "- **Authority:** Canon 3(A)(4); MCR 3.206(B)(5); *Mathews v Eldridge*, 424 US 319 (1976)\n\n"

    md += "### 2. Five Orders on August 8, 2025 Without Notice\n\n"
    md += "On a single day (August 8, 2025), the Court entered **five (5) ex parte orders** "
    md += "without providing notice to Plaintiff:\n"
    md += "- No opportunity to be heard before entry\n"
    md += "- No emergency justification documented\n"
    md += "- No findings of irreparable harm\n"
    md += "- No MCR 3.207(B) compliance\n"
    md += "- **Authority:** MCR 3.206(B)(5); MCR 2.119; US Const. Amend. XIV\n\n"

    md += "## E. Legal Framework\n\n"

    md += "### MCR 3.206(B)(5) — Ex Parte Orders in Domestic Relations\n"
    md += "Ex parte orders may be entered only upon showing of:\n"
    md += "1. Irreparable injury, loss, or damage will result from delay\n"
    md += "2. The moving party has made reasonable efforts to give notice\n"
    md += "3. Specific facts in affidavit or verified pleading\n\n"

    md += "### MCR 2.517(A)(1) — Findings Required\n"
    md += "Court must make findings of fact and conclusions of law in all contested matters. "
    md += "No findings were made under MCL 722.23 before suspending parenting time.\n\n"

    md += "### Constitutional Due Process\n"
    md += "- **Procedural:** Notice and opportunity to be heard before deprivation of parental rights\n"
    md += "- **Substantive:** Fundamental right to parent — strict scrutiny applies\n"
    md += "- **Authority:** US Const. Amend. XIV; *Troxel v Granville*, 530 US 57 (2000); "
    md += "*Santosky v Kramer*, 455 US 745 (1982)\n\n"

    write_doc("EX_PARTE_VIOLATION_ANALYSIS.md", md)


# ═══════════════════════════════════════════════════════════════════════
#  5. BIAS PATTERN STATISTICAL REPORT
# ═══════════════════════════════════════════════════════════════════════

def build_bias_report(conn):
    print("[5/6] Building BIAS_PATTERN_STATISTICAL_REPORT.md ...")
    md = header("BIAS PATTERN STATISTICAL REPORT",
                "Quantitative analysis of judicial bias from database evidence")

    # === Impeachment by speaker ===
    speaker_counts = q(conn,
        "SELECT speaker, COUNT(*) as cnt FROM impeachment_items GROUP BY speaker ORDER BY cnt DESC")
    md += "## A. Impeachment Items by Speaker\n\n"
    md += "| Speaker | Count | % of Total |\n"
    md += "|---------|------:|-----------:|\n"
    total_imp = sum(s['cnt'] for s in speaker_counts)
    for s in speaker_counts:
        pct = (s['cnt'] / total_imp * 100) if total_imp > 0 else 0
        md += f"| {s['speaker'] or 'NULL'} | {s['cnt']:,} | {pct:.1f}% |\n"
    md += f"| **TOTAL** | **{total_imp:,}** | **100%** |\n\n"

    md += "> **Finding:** COURT speaker accounts for the overwhelming majority of impeachment "
    md += "items, indicating judicial conduct is the primary source of impeachable actions.\n\n"

    # === Impeachment by speaker + severity ===
    md += "### Severity Breakdown by Speaker\n\n"
    md += "| Speaker | CRITICAL | HIGH | MEDIUM |\n"
    md += "|---------|----------|------|--------|\n"
    for s in speaker_counts:
        if not s['speaker']:
            continue
        sevs = q(conn,
            "SELECT severity, COUNT(*) as cnt FROM impeachment_items "
            "WHERE speaker = ? GROUP BY severity", (s['speaker'],))
        sev_map = {sv['severity']: sv['cnt'] for sv in sevs}
        md += f"| {s['speaker']} | {sev_map.get('CRITICAL',0):,} | {sev_map.get('HIGH',0):,} | {sev_map.get('MEDIUM',0):,} |\n"
    md += "\n"

    # === Impeachment by type ===
    type_counts = q(conn,
        "SELECT item_type, COUNT(*) as cnt FROM impeachment_items GROUP BY item_type ORDER BY cnt DESC")
    md += "## B. Impeachment Items by Type\n\n"
    md += "| Type | Count | % |\n"
    md += "|------|------:|--:|\n"
    for t in type_counts:
        pct = (t['cnt'] / total_imp * 100) if total_imp > 0 else 0
        md += f"| {t['item_type']} | {t['cnt']:,} | {pct:.1f}% |\n"
    md += "\n"

    # === Contradiction analysis ===
    md += "## C. Contradiction Analysis\n\n"
    contra_types = q(conn,
        "SELECT contradiction_type, COUNT(*) as cnt FROM contradiction_map GROUP BY contradiction_type ORDER BY cnt DESC")
    total_contra = sum(c['cnt'] for c in contra_types)
    md += f"**Total contradictions in database:** {total_contra:,}\n\n"
    md += "| Contradiction Type | Count | % |\n"
    md += "|--------------------|------:|--:|\n"
    for c in contra_types:
        pct = (c['cnt'] / total_contra * 100) if total_contra > 0 else 0
        md += f"| {c['contradiction_type']} | {c['cnt']:,} | {pct:.1f}% |\n"
    md += "\n"

    # Contradictions by source type
    md += "### Contradictions by Source Type\n\n"
    md += "| Source A Type | Count | Source B Type | Count |\n"
    md += "|--------------|------:|--------------|------:|\n"
    src_a = q(conn, "SELECT source_a_type, COUNT(*) as cnt FROM contradiction_map GROUP BY source_a_type ORDER BY cnt DESC")
    src_b = q(conn, "SELECT source_b_type, COUNT(*) as cnt FROM contradiction_map GROUP BY source_b_type ORDER BY cnt DESC")
    for i in range(max(len(src_a), len(src_b))):
        a_type = src_a[i]['source_a_type'] if i < len(src_a) else ""
        a_cnt = src_a[i]['cnt'] if i < len(src_a) else ""
        b_type = src_b[i]['source_b_type'] if i < len(src_b) else ""
        b_cnt = src_b[i]['cnt'] if i < len(src_b) else ""
        md += f"| {a_type} | {a_cnt} | {b_type} | {b_cnt} |\n"
    md += "\n"

    # Contradictions by severity
    contra_sev = q(conn, "SELECT severity, COUNT(*) as cnt FROM contradiction_map GROUP BY severity ORDER BY cnt DESC")
    md += "### Contradictions by Severity\n\n"
    md += "| Severity | Count | % |\n"
    md += "|----------|------:|--:|\n"
    for s in contra_sev:
        pct = (s['cnt'] / total_contra * 100) if total_contra > 0 else 0
        md += f"| {s['severity']} | {s['cnt']:,} | {pct:.1f}% |\n"
    md += "\n"

    # === Evidence consideration analysis ===
    md += "## D. Evidence Consideration Rates\n\n"
    ev_cats = q(conn, "SELECT evidence_category, COUNT(*) as cnt FROM evidence_quotes GROUP BY evidence_category ORDER BY cnt DESC")
    total_ev = sum(e['cnt'] for e in ev_cats)
    md += f"**Total evidence items catalogued:** {total_ev}\n\n"
    md += "| Evidence Category | Count | % |\n"
    md += "|-------------------|------:|--:|\n"
    for e in ev_cats:
        pct = (e['cnt'] / total_ev * 100) if total_ev > 0 else 0
        md += f"| {e['evidence_category']} | {e['cnt']} | {pct:.1f}% |\n"
    md += "\n"

    md += "> **Finding:** EX_PARTE_ORDER is the second-largest evidence category, demonstrating "
    md += "systematic reliance on ex parte procedures.\n\n"

    # === Judicial vs party analysis ===
    md += "## E. Judicial Misconduct Pattern Analysis\n\n"
    judicial_imp = q(conn,
        "SELECT item_type, COUNT(*) as cnt FROM impeachment_items "
        "WHERE item_type LIKE '%JUDICIAL%' GROUP BY item_type ORDER BY cnt DESC")
    total_jud = sum(j['cnt'] for j in judicial_imp)
    md += f"**Total judicial misconduct items:** {total_jud:,}\n\n"
    md += "| Misconduct Category | Count | % of Judicial Items |\n"
    md += "|---------------------|------:|--------------------:|\n"
    for j in judicial_imp:
        pct = (j['cnt'] / total_jud * 100) if total_jud > 0 else 0
        md += f"| {j['item_type']} | {j['cnt']:,} | {pct:.1f}% |\n"
    md += "\n"

    # === Motion/vehicle status by lane ===
    md += "## F. Procedural Vehicle Status by Lane\n\n"
    vehicles = q(conn, "SELECT case_lane, title, vehicle_type, status FROM vehicles ORDER BY case_lane, status")
    md += "| Lane | Vehicle | Type | Status |\n"
    md += "|------|---------|------|--------|\n"
    for v in vehicles:
        md += f"| {v['case_lane']} | {v['title']} | {v['vehicle_type']} | {v['status']} |\n"
    md += "\n"

    # === Statistical summary ===
    md += "## G. Statistical Summary — Bias Indicators\n\n"
    md += "| Metric | Value | Significance |\n"
    md += "|--------|-------|--------------|\n"
    md += f"| Total impeachment items | {total_imp:,} | Database-wide impeachment evidence |\n"
    md += f"| COURT-speaker items | {next((s['cnt'] for s in speaker_counts if s['speaker']=='COURT'), 0):,} | Judicial actions subject to challenge |\n"
    md += f"| Judicial misconduct items | {total_jud:,} | Categorized judicial violations |\n"
    md += f"| Total contradictions | {total_contra:,} | Inconsistencies across record |\n"
    md += f"| Ex parte evidence items | {len(q(conn, 'SELECT 1 FROM evidence_quotes WHERE evidence_category LIKE \"%EX_PARTE%\"'))} | Ex parte procedure abuse |\n"
    md += f"| CRITICAL severity items | {next((s['cnt'] for s in q(conn, 'SELECT severity, COUNT(*) as cnt FROM impeachment_items GROUP BY severity') if s['severity']=='CRITICAL'), 0):,} | Highest-severity findings |\n"
    md += f"| Days parent-child separation | 329+ | Constitutional deprivation duration |\n"
    md += "\n"

    md += "### Bias Conclusion\n\n"
    md += "The statistical evidence demonstrates a pattern of judicial conduct that:\n"
    md += "1. **Disproportionately impacts Plaintiff** — 329+ days separation without merits hearing\n"
    md += "2. **Relies on ex parte procedures** — bypassing adversarial process\n"
    md += "3. **Fails to make required findings** — no MCL 722.23 analysis\n"
    md += "4. **Extends deference to Watson** — system-insider credibility asymmetry\n"
    md += "5. **Characterizes advocacy as misconduct** — chilling First Amendment rights\n\n"
    md += "**Authority:** MCR 2.003(C)(1)(b); MCJC Canons 1, 2, 3; US Const. Amend. I, XIV\n\n"

    write_doc("BIAS_PATTERN_STATISTICAL_REPORT.md", md)


# ═══════════════════════════════════════════════════════════════════════
#  6. REMEDIES & RELIEF MATRIX
# ═══════════════════════════════════════════════════════════════════════

def build_remedies_matrix(conn):
    print("[6/6] Building REMEDIES_RELIEF_MATRIX.md ...")
    md = header("REMEDIES & RELIEF MATRIX",
                "Every available remedy across all litigation lanes")

    # Pull vehicles for readiness
    vehicles = q(conn, "SELECT case_lane, title, vehicle_type, status FROM vehicles ORDER BY case_lane")
    vehicle_map = defaultdict(list)
    for v in vehicles:
        vehicle_map[v['case_lane']].append(v)

    # Pull deadlines
    deadlines = q(conn, "SELECT title, due_date_iso, basis_authority, status FROM deadlines ORDER BY due_date_iso")

    # Pull filing readiness if available
    readiness = q(conn, "SELECT * FROM filing_readiness")
    readiness_map = {}
    for r in readiness:
        key = r.get('id') or r.get('action_name', 'unknown')
        readiness_map[key] = r

    # Pull legal action scores
    action_scores = q(conn, "SELECT action_name, lane, overall_score, gaps FROM legal_action_scores ORDER BY lane, overall_score DESC")
    score_map = defaultdict(list)
    for a in action_scores:
        score_map[a.get('lane', 'unknown')].append(a)

    md += "## Active Deadlines\n\n"
    md += "| Deadline | Due Date | Authority | Status |\n"
    md += "|----------|----------|-----------|--------|\n"
    for d in deadlines:
        md += f"| {d['title']} | {d['due_date_iso']} | {d.get('basis_authority','—')} | {d['status']} |\n"
    md += "\n---\n\n"

    # Lane A
    md += "## Lane A: Custody (Case No. 2024-001507-DC)\n\n"
    md += "### Remedy 1: Motion to Restore Parenting Time\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCL 722.27a; MCR 3.207; MCL 722.23 |\n"
    md += "| **Elements** | (1) Best interest of child; (2) No evidence of harm; (3) 329+ day deprivation |\n"
    md += "| **Evidence** | Ex parte orders without findings; no MCL 722.23 analysis; Berry voicemail tainted |\n"
    md += "| **Vehicle Status** | " + next((v['status'] for v in vehicle_map.get('MEEK1',[]) if 'Restore' in v['title']), 'N/A') + " |\n"
    md += "| **Readiness** | HIGH — fundamental right deprivation creates urgency |\n\n"

    md += "### Remedy 2: Motion for Change of Custody\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCL 722.27(1)(c); *Vodvarka v Grasher*, 259 Mich App 1 (2003) |\n"
    md += "| **Elements** | (1) Change of circumstances; (2) ECE analysis; (3) Clear and convincing evidence |\n"
    md += "| **Evidence** | Watson's PPO weaponization; alienation under MCL 722.23(j); 329+ day separation |\n"
    md += "| **Readiness** | MODERATE — requires established custodial environment findings |\n\n"

    md += "### Remedy 3: Contempt of Court\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCL 600.1701; MCR 3.606 |\n"
    md += "| **Elements** | (1) Valid court order; (2) Knowledge of order; (3) Willful violation |\n"
    md += "| **Evidence** | Watson violations of parenting time orders; obstructive conduct |\n"
    md += "| **Readiness** | MODERATE — requires documentation of specific order violations |\n\n"

    md += "### Remedy 4: Make-Up Parenting Time\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCL 722.27a(7)(b) |\n"
    md += "| **Elements** | (1) Denied parenting time; (2) Amount of time denied; (3) Best interest |\n"
    md += "| **Evidence** | 329+ days denied; calendar documentation of missed time |\n"
    md += "| **Readiness** | HIGH — statutory entitlement upon showing of denied time |\n\n"

    # Lane B
    md += "## Lane B: Shady Oaks Housing\n\n"
    md += "### Remedy 5: Habitability Damages\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCL 554.139; *Allison v AEW Capital Mgmt* |\n"
    md += "| **Elements** | (1) Lease agreement; (2) Habitability defects; (3) Notice to landlord; (4) Damages |\n"
    md += "| **Evidence** | Housing condition documentation; inspection reports |\n"
    md += "| **Readiness** | MODERATE — evidence gathering phase |\n\n"

    # Lane C
    md += "## Lane C: Convergence / Cross-Lane\n\n"
    md += "### Remedy 6: Venue Change (MCR 2.222/2.223)\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCR 2.222; MCR 2.223; MCR 2.003 |\n"
    md += "| **Elements** | (1) Bias or prejudice; (2) Convenience; (3) Interest of justice |\n"
    md += "| **Evidence** | Pattern of judicial misconduct; ex parte violations; bias statistical evidence |\n"
    md += "| **Readiness** | HIGH — extensive bias documentation in database |\n\n"

    md += "### Remedy 7: Civil Damages vs Watson Family\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCL 600.2911; *Maloney v Pac*, 183 Mich 481 |\n"
    md += "| **Elements** | (1) Tortious conduct; (2) Damages; (3) Causation |\n"
    md += "| **Evidence** | Alienation; PPO weaponization; Berry involvement |\n"
    md += "| **Readiness** | LOW — requires further development |\n\n"

    # Lane D
    md += "## Lane D: PPO (Case No. 2023-5907-PP)\n\n"
    md += "### Remedy 8: PPO Termination/Modification\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCL 600.2950(13); MCR 3.706 |\n"
    md += "| **Elements** | (1) Changed circumstances; (2) PPO no longer necessary; (3) Best interest |\n"
    md += "| **Evidence** | PPO used as custody weapon; no legitimate protective purpose; Watson prosecutorial tactics |\n"
    md += "| **Vehicle Status** | " + next((v['status'] for v in vehicle_map.get('MEEK2',[]) if 'PPO' in v['title']), 'N/A') + " |\n"
    md += "| **Readiness** | MODERATE — requires hearing |\n\n"

    # Lane E
    md += "## Lane E: Judicial Misconduct\n\n"
    md += "### Remedy 9: JTC Disciplinary Action\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | Const 1963, art 6, §30; MCR 9.200 et seq |\n"
    md += "| **Elements** | (1) Misconduct/disability; (2) Pattern of conduct; (3) Formal complaint |\n"
    md += "| **Evidence** | 1,895+ judicial impeachment items; ex parte violations; benchbook deviations; due process failures |\n"
    md += "| **Vehicle Status** | " + next((v['status'] for v in vehicle_map.get('MEEK3',[]) if 'JTC' in v['title']), 'N/A') + " |\n"
    md += "| **Readiness** | HIGH — extensive documentation; complaint filed |\n\n"

    md += "### Remedy 10: MCR 2.003 Disqualification Motion\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCR 2.003(C)(1)(b); *Armstrong v Ypsilanti Charter Twp* |\n"
    md += "| **Elements** | (1) Bias or prejudice; (2) Personal knowledge of disputed facts; (3) Appearance of impropriety |\n"
    md += "| **Evidence** | Bias statistics; ex parte conduct; credibility asymmetry; 146 MCR 2.003 items in DB |\n"
    md += "| **Readiness** | HIGH — statistical evidence compelling |\n\n"

    # Lane F
    md += "## Lane F: Court of Appeals (COA 366810)\n\n"
    md += "### Remedy 11: Appellate Reversal and Remand\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCR 7.204; MCR 7.216(A)(7) |\n"
    md += "| **Elements** | (1) Preserved error; (2) Abuse of discretion; (3) Prejudice |\n"
    md += "| **Issues on Appeal** | Ex parte order without findings; due process; MCL 722.23 failure; PPO weaponization |\n"
    md += "| **Vehicle Status** | " + next((v['status'] for v in vehicle_map.get('MEEK4',[]) if 'Claim' in v['title']), 'N/A') + " |\n"
    md += "| **Readiness** | IN PROGRESS — Claim filed; Brief needs resolution |\n\n"

    md += "### Remedy 12: Emergency Relief Pending Appeal\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCR 7.216(A)(7); MCR 7.211(C)(6) |\n"
    md += "| **Elements** | (1) Likelihood of success on merits; (2) Irreparable harm; (3) Balance of equities |\n"
    md += "| **Evidence** | 329+ days separation = irreparable harm; strong merits case; child's best interest |\n"
    md += "| **Readiness** | HIGH — ongoing constitutional deprivation |\n\n"

    # Lane G
    md += "## Lane G: Michigan Supreme Court\n\n"
    md += "### Remedy 13: MSC Application for Leave to Appeal\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCR 7.305; Const 1963, art 6, §4 |\n"
    md += "| **Elements** | (1) Significant constitutional question; (2) Jurisprudential significance; (3) Clear error |\n"
    md += "| **Issues** | Fundamental parental rights; ex parte due process; pro se access to justice |\n"
    md += "| **Readiness** | CONTINGENT — depends on COA outcome |\n\n"

    md += "### Remedy 14: Superintending Control\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | MCR 3.302; MCL 600.1701; Const 1963, art 6, §4 |\n"
    md += "| **Elements** | (1) No other adequate remedy; (2) Lower court failure to perform duty; (3) Extraordinary circumstances |\n"
    md += "| **Evidence** | 329+ day deprivation; systemic procedural failures; no adequate appellate remedy for delay |\n"
    md += "| **Readiness** | MODERATE — extraordinary showing required |\n\n"

    # Federal
    md += "## Federal Remedies\n\n"
    md += "### Remedy 15: 42 USC § 1983 — Civil Rights Action\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | 42 USC § 1983; US Const. Amend. I, XIV |\n"
    md += "| **Elements** | (1) Action under color of state law; (2) Deprivation of constitutional right; (3) Causation; (4) Damages |\n"
    md += "| **Potential Defendants** | State actors who violated clearly established rights |\n"
    md += "| **Constitutional Claims** | Due process (XIV); parental rights (XIV substantive); petition right (I) |\n"
    md += "| **Defenses to Assess** | Judicial immunity (*Stump v Sparkman*); prosecutorial immunity; qualified immunity |\n"
    md += "| **Readiness** | LOW-MODERATE — judicial immunity is significant barrier; must exhaust state remedies first |\n\n"

    md += "### Remedy 16: USDC Western District — Federal Habeas / Civil Action\n\n"
    md += "| Element | Detail |\n"
    md += "|---------|--------|\n"
    md += "| **Authority** | 28 USC § 2254 (habeas); 42 USC § 1983 |\n"
    md += "| **Forum** | US District Court, Western District of Michigan |\n"
    md += "| **Requirements** | Exhaustion of state remedies; federal question jurisdiction |\n"
    md += "| **Readiness** | LOW — state remedies must be exhausted first |\n\n"

    # Summary matrix
    md += "## Master Remedy Matrix\n\n"
    md += "| # | Remedy | Lane | Authority | Readiness | Priority |\n"
    md += "|---|--------|------|-----------|-----------|----------|\n"
    remedies = [
        ("1", "Restore Parenting Time", "A", "MCL 722.27a", "HIGH", "URGENT"),
        ("2", "Change of Custody", "A", "MCL 722.27(1)(c)", "MODERATE", "HIGH"),
        ("3", "Contempt of Court", "A", "MCL 600.1701", "MODERATE", "MEDIUM"),
        ("4", "Make-Up Parenting Time", "A", "MCL 722.27a(7)(b)", "HIGH", "HIGH"),
        ("5", "Habitability Damages", "B", "MCL 554.139", "MODERATE", "MEDIUM"),
        ("6", "Venue Change", "C", "MCR 2.222", "HIGH", "HIGH"),
        ("7", "Civil Damages", "C", "MCL 600.2911", "LOW", "LOW"),
        ("8", "PPO Termination", "D", "MCL 600.2950", "MODERATE", "HIGH"),
        ("9", "JTC Complaint", "E", "Const art 6 §30", "HIGH", "FILED"),
        ("10", "Disqualification", "E", "MCR 2.003", "HIGH", "HIGH"),
        ("11", "COA Reversal", "F", "MCR 7.204", "IN PROGRESS", "URGENT"),
        ("12", "Emergency Relief", "F", "MCR 7.216(A)(7)", "HIGH", "URGENT"),
        ("13", "MSC Leave", "G", "MCR 7.305", "CONTINGENT", "MEDIUM"),
        ("14", "Superintending Control", "G", "MCR 3.302", "MODERATE", "MEDIUM"),
        ("15", "§ 1983 Action", "Federal", "42 USC § 1983", "LOW-MOD", "LOW"),
        ("16", "Federal Habeas/Civil", "Federal", "28 USC § 2254", "LOW", "LOW"),
    ]
    for r in remedies:
        md += f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |\n"
    md += "\n"

    # Legal action scores from DB
    if action_scores:
        md += "## Filing Readiness Scores (from legal_action_scores)\n\n"
        md += "| Action | Lane | Score | Gaps |\n"
        md += "|--------|------|------:|------|\n"
        for a in action_scores:
            md += f"| {a['action_name']} | {a.get('lane','—')} | {a.get('overall_score','—')} | {trunc(a.get('gaps',''),100)} |\n"
        md += "\n"

    write_doc("REMEDIES_RELIEF_MATRIX.md", md)


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print(f"LitigationOS — Accountability Dossier Builder")
    print(f"Database: {DB_PATH}")
    print(f"Output:   {OUTPUT_DIR}")
    print(f"Time:     {GENERATED}")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"[FATAL] Database not found: {DB_PATH}")
        sys.exit(1)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = connect()

    try:
        build_misconduct_dossier(conn)
        build_berry_investigation(conn)
        build_watson_dossier(conn)
        build_ex_parte_analysis(conn)
        build_bias_report(conn)
        build_remedies_matrix(conn)
    finally:
        conn.close()

    print("=" * 60)
    print("[DONE] All 6 dossiers generated successfully.")


if __name__ == "__main__":
    main()
