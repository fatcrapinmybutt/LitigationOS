#!/usr/bin/env python3
"""
build_authority_guides.py — LitigationOS Authority Reference Generator
Generates 6 comprehensive Michigan authority reference documents from litigation_context.db.
Pigors v. Watson consolidated litigation support.
"""

import sqlite3
import os
import re
import textwrap
from datetime import datetime
from pathlib import Path

DB_PATH = r"C:\Users\andre\litigation_context.db"
OUTPUT_DIR = r"C:\Users\andre\LitigationOS\02_AUTHORITY"
GENERATED_TAG = f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by LitigationOS build_authority_guides.py"

# MCR rules directly relevant to our case lanes
CASE_RELEVANT_MCR = {
    '1.109': 'Filing standards — all filings',
    '2.003': 'Judicial disqualification — Lane E',
    '2.105': 'Service of process — all filings',
    '2.107': 'Service and filing — all filings',
    '2.113': 'Form of pleadings — all filings',
    '2.114': 'Signatures/verification — all filings',
    '2.116': 'Summary disposition — Lane A',
    '2.119': 'Motion practice — all lanes',
    '2.302': 'Discovery — Lane A',
    '2.310': 'Depositions — Lane A',
    '2.313': 'Motion to compel — Lane A',
    '2.507': 'Conduct of trials — Lane A',
    '2.613': 'Findings by court — Lane A/F',
    '3.206': 'Initiating domestic case — Lane A',
    '3.207': 'Ex parte/temporary orders — Lane A',
    '3.208': 'Friend of the Court — Lane A',
    '3.210': 'Hearings — Lane A',
    '3.211': 'Child custody jurisdiction — Lane A',
    '3.310': 'Injunctions/PPO — Lane D',
    '3.606': 'Contempt — Lane A/D',
    '3.707': 'PPO proceedings — Lane D',
    '7.101': 'Court of Appeals jurisdiction — Lane F',
    '7.204': 'Claim of appeal — Lane F',
    '7.205': 'Application for leave — Lane F',
    '7.208': 'Filing requirements — Lane F',
    '7.210': 'Record on appeal — Lane F',
    '7.211': 'Motions in COA — Lane F',
    '7.212': 'Briefs — Lane F',
    '7.215': 'Publication of opinions — Lane F',
    '9.200': 'JTC construction — Lane E',
    '9.202': 'Standards of judicial conduct — Lane E',
    '9.210': 'JTC organization — Lane E',
    '9.220': 'JTC preliminary investigation — Lane E',
    '9.224': 'JTC complaint — Lane E',
    '9.233': 'JTC public hearing — Lane E',
    '9.251': 'JTC Supreme Court review — Lane E',
}

# MCR chapter names
MCR_CHAPTERS = {
    '1': 'General Provisions',
    '2': 'Civil Procedure',
    '3': 'Special Proceedings & Family Law',
    '4': 'District Court',
    '5': 'Probate Court',
    '6': 'Criminal Procedure',
    '7': 'Appellate Rules',
    '8': 'Administrative Rules',
    '9': 'Professional Discipline & Judicial Tenure',
}


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def write_file(filename, content):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✓ Written: {filename} ({len(content):,} chars)")


def truncate(text, maxlen=200):
    if not text:
        return ""
    text = text.strip().replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text[:maxlen] + "..." if len(text) > maxlen else text


def make_one_line_summary(title, full_text):
    """Generate a 1-line summary from title and first sentence of full_text."""
    if not full_text or len(full_text.strip()) < 10:
        return title or "No description available"
    # Take first meaningful sentence
    text = full_text.strip().replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    # Skip preamble junk
    for prefix in ['MCL - Section', 'Skip to content', 'Michigan Legislature']:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    # Find first sentence
    match = re.search(r'[.!;]', text[:300])
    if match:
        summary = text[:match.end()].strip()
    else:
        summary = text[:200].strip()
    return summary if len(summary) > 5 else (title or "No description available")


# ============================================================
# 1. MCR COMPLETE INDEX
# ============================================================
def build_mcr_complete_index(conn):
    print("Building MCR_COMPLETE_INDEX.md...")
    c = conn.cursor()

    # Get all MCR rules with titles
    c.execute("""
        SELECT rule_number, title, chapter, full_text, summary
        FROM auth_rules
        WHERE rule_type = 'MCR'
          AND title IS NOT NULL AND title != ''
          AND title != ('MCR ' || rule_number)
        ORDER BY rule_number
    """)
    rules_with_titles = c.fetchall()

    # Also get rules that only have generic titles but have full_text
    c.execute("""
        SELECT rule_number, title, chapter, full_text, summary
        FROM auth_rules
        WHERE rule_type = 'MCR'
          AND (title IS NULL OR title = '' OR title = ('MCR ' || rule_number))
          AND full_text IS NOT NULL AND length(full_text) > 50
        ORDER BY rule_number
    """)
    rules_with_text_only = c.fetchall()

    # Organize by chapter
    chapters = {}
    for row in list(rules_with_titles) + list(rules_with_text_only):
        rn = row['rule_number']
        ch_num = rn.split('.')[0] if '.' in rn else '0'
        ch_name = MCR_CHAPTERS.get(ch_num, row['chapter'] or 'Other')
        key = f"{ch_num}|{ch_name}"
        if key not in chapters:
            chapters[key] = []
        chapters[key].append(row)

    lines = []
    lines.append(f"# MCR COMPLETE INDEX — Michigan Court Rules")
    lines.append(f"### Pigors v. Watson | {GENERATED_TAG}")
    lines.append(f"### 🔴 = Directly used in our case\n")
    lines.append(f"**Total MCR rules indexed:** {len(rules_with_titles) + len(rules_with_text_only)}\n")
    lines.append("---\n")

    # Table of contents
    lines.append("## Table of Contents\n")
    for key in sorted(chapters.keys()):
        ch_num, ch_name = key.split('|', 1)
        lines.append(f"- [Chapter {ch_num}: {ch_name}](#chapter-{ch_num}-{ch_name.lower().replace(' ', '-').replace('&', '').replace('/', '')})")
    lines.append("\n---\n")

    for key in sorted(chapters.keys()):
        ch_num, ch_name = key.split('|', 1)
        rules = sorted(chapters[key], key=lambda r: r['rule_number'])
        lines.append(f"## Chapter {ch_num}: {ch_name}")
        lines.append(f"**{len(rules)} rules indexed**\n")
        lines.append("| MCR | Title | Summary | Case Use |")
        lines.append("|-----|-------|---------|----------|")

        for row in rules:
            rn = row['rule_number']
            title = row['title'] or ""
            # Clean title
            if title.startswith('MCR '):
                title = title.replace(f'MCR {rn}', '').strip()
            if not title or len(title) < 3:
                title = "(see full text)"

            summary = make_one_line_summary(title, row['full_text'])
            summary = truncate(summary, 120)

            # Check if case-relevant
            case_use = ""
            if rn in CASE_RELEVANT_MCR:
                case_use = f"🔴 {CASE_RELEVANT_MCR[rn]}"

            # Escape pipe chars
            title = title.replace('|', '/')
            summary = summary.replace('|', '/')

            lines.append(f"| **MCR {rn}** | {title[:80]} | {summary} | {case_use} |")

        lines.append("")

    # Appendix: Case-relevant rules quick reference
    lines.append("\n---\n## Appendix: Case-Relevant MCR Quick Reference\n")
    lines.append("| MCR | Case Application |")
    lines.append("|-----|-----------------|")
    for rn in sorted(CASE_RELEVANT_MCR.keys()):
        lines.append(f"| **MCR {rn}** | {CASE_RELEVANT_MCR[rn]} |")

    write_file("MCR_COMPLETE_INDEX.md", "\n".join(lines))


# ============================================================
# 2. MCL CUSTODY GUIDE
# ============================================================
def build_mcl_custody_guide(conn):
    print("Building MCL_CUSTODY_GUIDE.md...")
    c = conn.cursor()

    # Get MCL custody rules from auth_rules
    c.execute("""
        SELECT rule_number, title, full_text FROM auth_rules
        WHERE rule_type = 'MCL' AND rule_number LIKE '722%'
        ORDER BY rule_number
    """)
    mcl_rules = {r['rule_number']: r for r in c.fetchall()}

    # Get benchbook entries for custody/parenting
    c.execute("SELECT section, title, content FROM auth_benchbook_entries ORDER BY section")
    benchbook = c.fetchall()

    # Get legal_reference_docs for MCL 722
    c.execute("""
        SELECT heading, body FROM legal_reference_docs
        WHERE body LIKE '%722.23%' OR body LIKE '%722.27%' OR heading LIKE '%custody%' OR heading LIKE '%722%'
    """)
    ref_docs = c.fetchall()

    # Get pages with MCL 722.23 content for best interest factors
    c.execute("""
        SELECT text_content FROM pages
        WHERE text_content LIKE '%722.23%'
          AND (text_content LIKE '%best interest%' OR text_content LIKE '%factor%')
        LIMIT 10
    """)
    pages_722 = c.fetchall()

    # Get evidence quotes related to custody
    c.execute("""
        SELECT quote_text, speaker, legal_significance, evidence_category
        FROM evidence_quotes
        WHERE evidence_category IN ('CUSTODY_ORDER', 'TRANSCRIPT')
          AND (legal_significance LIKE '%custody%' OR legal_significance LIKE '%best interest%'
               OR legal_significance LIKE '%parenting%' OR quote_text LIKE '%722%')
        LIMIT 20
    """)
    custody_evidence = c.fetchall()

    # Get master_citations for MCL 722
    c.execute("""
        SELECT DISTINCT citation, context FROM master_citations
        WHERE citation LIKE 'MCL 722%'
        ORDER BY citation
    """)
    mcl_cites = c.fetchall()

    lines = []
    lines.append(f"# MCL CUSTODY GUIDE — Child Custody Act (MCL 722.21–722.31)")
    lines.append(f"### Pigors v. Watson | Case No. 2024-001507-DC | {GENERATED_TAG}")
    lines.append(f"### **329+ days parent-child separation** — This guide is litigation-critical.\n")
    lines.append("---\n")

    # TOC
    lines.append("## Table of Contents\n")
    lines.append("1. [Overview of Child Custody Act](#1-overview)")
    lines.append("2. [MCL 722.23 — Best Interest Factors (a)–(l)](#2-best-interest-factors)")
    lines.append("3. [MCL 722.27 — Custody Modification & ECE](#3-custody-modification)")
    lines.append("4. [MCL 722.27a — Parenting Time](#4-parenting-time)")
    lines.append("5. [MCL 722.27a(9) — Mandatory Remedies](#5-mandatory-remedies)")
    lines.append("6. [Benchbook Guidance](#6-benchbook-guidance)")
    lines.append("7. [Application to Our Facts](#7-application-to-facts)")
    lines.append("8. [Citations Index](#8-citations-index)")
    lines.append("\n---\n")

    # Section 1: Overview
    lines.append("## 1. Overview of Child Custody Act {#1-overview}\n")
    lines.append("The Michigan Child Custody Act (MCL 722.21–722.31) governs all custody and parenting time disputes in Michigan family courts.\n")
    lines.append("### Key Sections\n")
    lines.append("| MCL Section | Subject | Relevance |")
    lines.append("|-------------|---------|-----------|")
    custody_sections = {
        '722.21': ('Scope', 'Applicability of the Act'),
        '722.22': ('Definitions', 'Key terms: child, custody dispute'),
        '722.23': ('Best Interest Factors', '🔴 CRITICAL — 12 factors for all custody decisions'),
        '722.24': ('Guardian ad Litem', 'GAL appointment authority'),
        '722.25': ('Grandparent custody', 'Third-party standing'),
        '722.26': ('Custody orders', 'Form and content requirements'),
        '722.26a': ('Joint custody', 'Presumptions and standards'),
        '722.27': ('Custody modification', '🔴 CRITICAL — ECE, change of circumstances'),
        '722.27a': ('Parenting time', '🔴 CRITICAL — Cannot deny without endangerment finding'),
        '722.27b': ('Parenting time makeup', 'Compensation for denied time'),
        '722.28': ('Mediation', 'Dispute resolution requirements'),
        '722.29': ('Support', 'Support in custody context'),
        '722.30': ('Attorney fees', 'Fee shifting authority'),
        '722.31': ('Domicile change', '100-mile rule / change of domicile'),
    }
    for sec, (subj, rel) in custody_sections.items():
        lines.append(f"| **MCL {sec}** | {subj} | {rel} |")
    lines.append("")

    # Section 2: Best Interest Factors
    lines.append("\n## 2. MCL 722.23 — Best Interest Factors (a)–(l) {#2-best-interest-factors}\n")
    lines.append("> **\"As used in this act, 'best interests of the child' means the sum total of the following factors to be considered, evaluated, and determined by the court.\"** — MCL 722.23\n")

    factors = [
        ('(a)', 'Love, affection, and other emotional ties', 'The love, affection, and other emotional ties existing between the parties involved and the child.', 'Andrew maintained consistent, loving relationship until separation. 329+ days of forced separation undermines this factor analysis.'),
        ('(b)', 'Capacity to provide love, affection, guidance', 'The capacity and disposition of the parties involved to give the child love, affection, and guidance and to continue the education and raising of the child in his or her religion or creed, if any.', 'Andrew demonstrated capacity through daily caregiving before separation.'),
        ('(c)', 'Capacity to provide food, clothing, medical care', 'The capacity and disposition of the parties involved to provide the child with food, clothing, medical care or other remedial care, and other material needs.', 'Andrew maintained stable housing and employment. Material needs always met.'),
        ('(d)', 'Length of time in stable environment', 'The length of time the child has lived in a stable, satisfactory environment, and the desirability of maintaining continuity.', 'Child lived with Andrew in stable environment prior to ex parte order disruption.'),
        ('(e)', 'Permanence of family unit', 'The permanence, as a family unit, of the existing or proposed custodial home or homes.', 'Both homes should be evaluated for stability and permanence.'),
        ('(f)', 'Moral fitness', 'The moral fitness of the parties involved.', 'Review evidence of both parties\' conduct and fitness.'),
        ('(g)', 'Mental and physical health', 'The mental and physical health of the parties involved.', 'No disqualifying health issues for Andrew.'),
        ('(h)', 'Home, school, community record', 'The home, school, and community record of the child.', 'Child\'s age (1-3) limits school record; community ties to both parents.'),
        ('(i)', 'Reasonable preference of child', 'The reasonable preference of the child, if the court considers the child to be of sufficient age to express preference.', 'Child too young to express preference (under 3).'),
        ('(j)', 'Willingness to facilitate relationship (ANTI-ALIENATION)', 'The willingness and ability of each of the parties to facilitate and encourage a close and continuing parent-child relationship between the child and the other parent or the child and the parents.', '🔴 CRITICAL — Factor J directly addresses alienation. Watson\'s conduct of 329+ day separation is strong evidence of Factor J violation.'),
        ('(k)', 'Domestic violence', 'Domestic violence, regardless of whether the violence was directed against or witnessed by the child.', 'PPO proceedings (Lane D) must be evaluated in context.'),
        ('(l)', 'Other relevant factors', 'Any other factor considered by the court to be relevant to a particular child custody dispute.', 'Court must state on record any additional factors considered.'),
    ]

    for letter, name, text, application in factors:
        lines.append(f"### Factor {letter}: {name}\n")
        lines.append(f"**Statutory Text:** {text}\n")
        lines.append(f"**Application to Our Case:** {application}\n")

    # Section 3: Custody Modification & ECE
    lines.append("\n## 3. MCL 722.27 — Custody Modification & ECE {#3-custody-modification}\n")
    lines.append("### Established Custodial Environment (ECE) — MCL 722.27(1)(c)\n")
    lines.append("> An established custodial environment exists if \"over an appreciable time the child naturally looks to the custodian in that environment for guidance, discipline, the necessities of life, and parental comfort.\"\n")
    lines.append("**Burden of Proof:**")
    lines.append("- If a proposed change would alter the ECE → **clear and convincing evidence** required")
    lines.append("- If no ECE change → **preponderance of the evidence** standard\n")
    lines.append("### Change of Circumstances — Vodvarka v Grasher Standard\n")
    lines.append("Before modifying custody, the moving party must show either:")
    lines.append("1. **Proper cause** — an appropriate ground that has or could have a significant effect on the child's life")
    lines.append("2. **Change of circumstances** — conditions that have changed since the last custody order that affect the child's well-being\n")
    lines.append("*Vodvarka v Grasher*, 259 Mich App 1 (2003) — Threshold must be met before court re-evaluates best interest factors.\n")

    # Get benchbook entries for ECE
    for bb in benchbook:
        if 'custodial' in (bb['title'] or '').lower() or 'modification' in (bb['title'] or '').lower():
            lines.append(f"### Benchbook: {bb['title']}\n")
            lines.append(f"{bb['content']}\n")

    # Section 4: Parenting Time
    lines.append("\n## 4. MCL 722.27a — Parenting Time {#4-parenting-time}\n")

    pt_rule = mcl_rules.get('722.27a')
    if pt_rule and pt_rule['full_text']:
        ft = pt_rule['full_text'][:2000]
        lines.append(f"**Statutory Text (excerpt):**\n```\n{ft}\n```\n")

    lines.append("### Key Principles\n")
    lines.append("1. **Presumption of reasonable parenting time** — MCL 722.27a(1): \"Parenting time shall be granted in accordance with the best interests of the child.\"")
    lines.append("2. **Cannot deny without endangerment** — Parenting time may only be denied or restricted if it would endanger the child's physical, mental, or emotional health.")
    lines.append("3. **Frequency and duration** — Must be sufficient to preserve and foster the parent-child bond.")
    lines.append("4. **Specific parenting time** — If parties cannot agree, court must establish specific schedule.\n")

    for bb in benchbook:
        if 'parenting' in (bb['title'] or '').lower() or 'eldred' in (bb['title'] or '').lower():
            lines.append(f"### Benchbook: {bb['title']}\n")
            lines.append(f"{bb['content']}\n")

    # Section 5: Mandatory Remedies
    lines.append("\n## 5. MCL 722.27a(9) — Mandatory Remedies {#5-mandatory-remedies}\n")
    lines.append("> When parenting time has been wrongfully denied, MCL 722.27a(9) provides **mandatory** remedies:\n")
    lines.append("1. **Makeup parenting time** of the same type as denied (not just additional time)")
    lines.append("2. **Economic sanctions** — reimbursement for expenses incurred due to wrongful denial")
    lines.append("3. **Modification of parenting time** — the court may modify the existing order")
    lines.append("4. **Contempt** — the offending party may be found in contempt")
    lines.append("5. **Attorney fees and costs** — the court shall order payment\n")
    lines.append("**Application:** With 329+ days of denied parenting time, Andrew is entitled to ALL of these remedies. The statute uses \"shall\" — mandatory, not discretionary.\n")

    # Section 6: Benchbook
    lines.append("\n## 6. Benchbook Guidance {#6-benchbook-guidance}\n")
    for bb in benchbook:
        lines.append(f"### {bb['section']}: {bb['title']}\n")
        lines.append(f"{bb['content']}\n")

    # Section 7: Application
    lines.append("\n## 7. Application to Our Facts {#7-application-to-facts}\n")

    # Pull relevant evidence
    if custody_evidence:
        lines.append("### Key Evidence Quotes\n")
        for eq in custody_evidence[:15]:
            lines.append(f"- **[{eq['evidence_category']}]** ({eq['speaker'] or 'Unknown'}): \"{truncate(eq['quote_text'], 150)}\"")
            if eq['legal_significance']:
                lines.append(f"  - *Legal significance:* {truncate(eq['legal_significance'], 120)}")
        lines.append("")

    # Pull ref doc content
    if ref_docs:
        lines.append("### Authority Reference Analysis\n")
        for rd in ref_docs[:5]:
            lines.append(f"#### {rd['heading']}\n")
            body = rd['body'] or ""
            lines.append(f"{body[:1500]}\n")

    # Section 8: Citations Index
    lines.append("\n## 8. Citations Index {#8-citations-index}\n")
    lines.append("### MCL 722 Citations Found in Case Record\n")
    lines.append("| Citation | Context |")
    lines.append("|----------|---------|")
    for cite in mcl_cites:
        ctx = truncate(cite['context'] or '', 100).replace('|', '/')
        lines.append(f"| {cite['citation']} | {ctx} |")

    write_file("MCL_CUSTODY_GUIDE.md", "\n".join(lines))


# ============================================================
# 3. MRE ADMISSIBILITY GUIDE
# ============================================================
def build_mre_guide(conn):
    print("Building MRE_ADMISSIBILITY_GUIDE.md...")
    c = conn.cursor()

    # Get all MRE rules
    c.execute("""
        SELECT rule_number, title, full_text FROM auth_rules
        WHERE rule_type = 'MRE'
        ORDER BY CAST(rule_number AS INTEGER)
    """)
    mre_rules = c.fetchall()

    # Get evidence quotes for exhibit mapping
    c.execute("""
        SELECT id, evidence_category, quote_text, speaker, legal_significance
        FROM evidence_quotes
        ORDER BY evidence_category, id
    """)
    exhibits = c.fetchall()

    lines = []
    lines.append(f"# MRE ADMISSIBILITY GUIDE — Michigan Rules of Evidence")
    lines.append(f"### Pigors v. Watson | {GENERATED_TAG}")
    lines.append(f"### Evidence Authentication & Admissibility Reference\n")
    lines.append("---\n")

    # TOC
    lines.append("## Table of Contents\n")
    lines.append("1. [Article IV: Relevance (MRE 401–403)](#article-iv-relevance)")
    lines.append("2. [Article VIII: Hearsay (MRE 801–807)](#article-viii-hearsay)")
    lines.append("3. [Article IX: Authentication (MRE 901–902)](#article-ix-authentication)")
    lines.append("4. [Complete MRE Index](#complete-mre-index)")
    lines.append("5. [Exhibit Authentication Map](#exhibit-authentication-map)")
    lines.append("6. [Authentication Decision Flowchart](#authentication-flowchart)")
    lines.append("\n---\n")

    # Group rules by article
    relevance_rules = [r for r in mre_rules if r['rule_number'] in ('401', '402', '403')]
    hearsay_rules = [r for r in mre_rules if r['rule_number'].startswith('80')]
    auth_rules_mre = [r for r in mre_rules if r['rule_number'].startswith('90')]

    # Article IV: Relevance
    lines.append("## Article IV: Relevance (MRE 401–403) {#article-iv-relevance}\n")
    for r in relevance_rules:
        lines.append(f"### MRE {r['rule_number']}: {r['title']}\n")
        if r['full_text']:
            lines.append(f"```\n{r['full_text'][:2000]}\n```\n")
        else:
            lines.append(f"*Title:* {r['title']}\n")

    lines.append("### Relevance Application to Our Case\n")
    lines.append("| Evidence Type | MRE 401 Test | MRE 403 Concerns |")
    lines.append("|---------------|-------------|-------------------|")
    lines.append("| Custody orders | Directly relevant to custody dispute | None — central to case |")
    lines.append("| Ex parte orders | Relevant to procedural due process | Prejudice if context omitted |")
    lines.append("| Transcripts | Relevant to judicial conduct/statements | Volume — select key passages |")
    lines.append("| PPO records | Relevant to DV allegations | Risk of unfair prejudice if unsubstantiated |")
    lines.append("| Communications | Relevant to Factor J (alienation) | Privacy concerns — redact non-relevant |")
    lines.append("")

    # Article VIII: Hearsay
    lines.append("## Article VIII: Hearsay (MRE 801–807) {#article-viii-hearsay}\n")
    for r in hearsay_rules:
        lines.append(f"### MRE {r['rule_number']}: {r['title']}\n")
        if r['full_text']:
            ft = r['full_text'][:3000]
            lines.append(f"```\n{ft}\n```\n")
        else:
            lines.append(f"*Title:* {r['title']}\n")

    lines.append("### Hearsay Exceptions Most Relevant to Our Case\n")
    lines.append("| Exception | MRE | Application |")
    lines.append("|-----------|-----|-------------|")
    lines.append("| Party-opponent statements | MRE 801(d)(2) | Watson's own statements admissible against her |")
    lines.append("| Excited utterance | MRE 803(2) | Statements made under stress of event |")
    lines.append("| Then-existing condition | MRE 803(3) | State of mind, emotion, intent |")
    lines.append("| Records of regularly conducted activity | MRE 803(6) | FOC records, court documents |")
    lines.append("| Public records | MRE 803(8) | Court orders, police reports, DHHS records |")
    lines.append("| Former testimony | MRE 804(b)(1) | Prior hearing transcripts |")
    lines.append("| Statement against interest | MRE 804(b)(3) | Watson's admissions against interest |")
    lines.append("")

    # Article IX: Authentication
    lines.append("## Article IX: Authentication (MRE 901–902) {#article-ix-authentication}\n")
    for r in auth_rules_mre:
        lines.append(f"### MRE {r['rule_number']}: {r['title']}\n")
        if r['full_text']:
            ft = r['full_text'][:3000]
            lines.append(f"```\n{ft}\n```\n")
        else:
            lines.append(f"*Title:* {r['title']}\n")

    lines.append("### Authentication Methods Summary\n")
    lines.append("| Method | MRE | Use For |")
    lines.append("|--------|-----|---------|")
    lines.append("| Testimony of witness with knowledge | 901(b)(1) | Personal observations, communications |")
    lines.append("| Distinctive characteristics | 901(b)(4) | Texts, emails, social media by content/style |")
    lines.append("| Public records | 901(b)(7) | Court filings, government records |")
    lines.append("| Certified copies | 902(1)-(4) | Self-authenticating public records |")
    lines.append("| Official publications | 902(5) | Statutes, regulations |")
    lines.append("| Business records | 902(11)-(12) | Certified business records |")
    lines.append("")

    # Complete MRE Index
    lines.append("## Complete MRE Index {#complete-mre-index}\n")
    lines.append("| MRE | Title | Key Points |")
    lines.append("|-----|-------|------------|")
    for r in mre_rules:
        title = (r['title'] or '').replace('|', '/')
        summary = make_one_line_summary(r['title'], r['full_text']).replace('|', '/')
        lines.append(f"| **MRE {r['rule_number']}** | {title[:60]} | {truncate(summary, 100)} |")
    lines.append("")

    # Exhibit Authentication Map
    lines.append("## Exhibit Authentication Map {#exhibit-authentication-map}\n")
    lines.append("### Evidence Inventory by Category\n")

    categories = {}
    for ex in exhibits:
        cat = ex['evidence_category'] or 'UNCATEGORIZED'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ex)

    auth_method_map = {
        'CUSTODY_ORDER': ('MRE 902(1)-(4)', 'Self-authenticating certified court record'),
        'EX_PARTE_ORDER': ('MRE 902(1)-(4)', 'Self-authenticating certified court record'),
        'JUDGE_ORDER': ('MRE 902(1)-(4)', 'Self-authenticating certified court record'),
        'TRANSCRIPT': ('MRE 901(b)(1), 803(b)(1)', 'Court reporter certification + former testimony exception'),
        'PPO': ('MRE 902(1)-(4)', 'Self-authenticating certified court record'),
    }

    lines.append("| Category | Count | Authentication Method | MRE Basis | Hearsay Exception |")
    lines.append("|----------|-------|----------------------|-----------|-------------------|")
    for cat, items in sorted(categories.items()):
        method_info = auth_method_map.get(cat, ('MRE 901(b)(1)', 'Testimony of witness with knowledge'))
        lines.append(f"| **{cat}** | {len(items)} | {method_info[1]} | {method_info[0]} | MRE 803(8) Public Records |")
    lines.append("")

    lines.append(f"\n**Total evidence items:** {len(exhibits)}\n")

    # Authentication Flowchart
    lines.append("## Authentication Decision Flowchart {#authentication-flowchart}\n")
    lines.append("```")
    lines.append("Is the document a certified public record?")
    lines.append("  ├── YES → Self-authenticating under MRE 902(1)-(4)")
    lines.append("  │         No further foundation needed")
    lines.append("  └── NO → Can a witness with knowledge authenticate?")
    lines.append("            ├── YES → MRE 901(b)(1) — Testimony of witness")
    lines.append("            └── NO → Does it have distinctive characteristics?")
    lines.append("                      ├── YES → MRE 901(b)(4) — Content, patterns")
    lines.append("                      └── NO → Is it a business record with certification?")
    lines.append("                                ├── YES → MRE 902(11)-(12)")
    lines.append("                                └── NO → Consider other 901(b) methods")
    lines.append("```\n")

    write_file("MRE_ADMISSIBILITY_GUIDE.md", "\n".join(lines))


# ============================================================
# 4. PROTECTIVE AUTHORITIES
# ============================================================
def build_protective_authorities(conn):
    print("Building PROTECTIVE_AUTHORITIES.md...")
    c = conn.cursor()

    lines = []
    lines.append(f"# PROTECTIVE AUTHORITIES — Legal Shields for Andrew & Lincoln")
    lines.append(f"### Pigors v. Watson | {GENERATED_TAG}")
    lines.append(f"### Authorities that PROTECT parental rights and require reunification\n")
    lines.append("---\n")

    # 1. Constitutional
    lines.append("## I. CONSTITUTIONAL PROTECTIONS\n")
    lines.append("### A. 14th Amendment — Due Process Clause\n")
    lines.append("> \"No State shall ... deprive any person of life, liberty, or property, without due process of law.\"\n")
    lines.append("**Fundamental Right:** The U.S. Supreme Court has repeatedly held that parents have a **fundamental liberty interest** in the care, custody, and control of their children. This is protected under both substantive and procedural due process.\n")
    lines.append("**Procedural Due Process Requirements:**")
    lines.append("1. **Notice** — Adequate notice before any deprivation of parental rights")
    lines.append("2. **Hearing** — Meaningful opportunity to be heard before a neutral decision-maker")
    lines.append("3. **Standard of proof** — Clear and convincing evidence for termination/severe restriction\n")
    lines.append("**Application:** Andrew was deprived of parenting time via ex parte orders without adequate prior notice or opportunity to be heard. 329+ days of separation without a full evidentiary hearing violates procedural due process.\n")

    lines.append("### B. Troxel v. Granville, 530 U.S. 57 (2000)\n")
    lines.append("> \"The liberty interest at issue in this case — the interest of parents in the care, custody, and control of their children — is perhaps the oldest of the fundamental liberty interests recognized by this Court.\"\n")
    lines.append("**Holdings:**")
    lines.append("1. Parents have a fundamental right to make decisions about their children")
    lines.append("2. A fit parent's decisions must be given **special weight**")
    lines.append("3. Courts cannot override fit parent's decisions without showing harm to child")
    lines.append("4. Due process requires individualized consideration, not blanket presumptions\n")
    lines.append("**Application:** Andrew is a fit parent. No finding of unfitness has been made. The prolonged separation overrides his fundamental rights without constitutionally adequate justification.\n")

    # 2. MCL 722.27a
    lines.append("## II. MICHIGAN STATUTORY PROTECTIONS\n")
    lines.append("### A. MCL 722.27a — Parenting Time Rights\n")

    c.execute("SELECT full_text FROM auth_rules WHERE rule_number = '722.27a'")
    row = c.fetchone()
    if row and row['full_text'] and len(row['full_text']) > 100:
        lines.append(f"**Full Statutory Text:**\n```\n{row['full_text'][:3000]}\n```\n")

    lines.append("**Key Protections:**")
    lines.append("1. Parenting time **shall be granted** in accordance with best interests (mandatory)")
    lines.append("2. Cannot restrict parenting time without **endangerment finding** on the record")
    lines.append("3. Court must consider frequency and duration sufficient to preserve parent-child bond")
    lines.append("4. Specific schedule required when parties cannot agree\n")
    lines.append("**Application:** No endangerment finding was made before restricting Andrew's parenting time. The \"shall\" language makes this mandatory, not discretionary.\n")

    # 3. MCL 722.27a(9) mandatory remedies
    lines.append("### B. MCL 722.27a(9) — Mandatory Remedies for Denied Parenting Time\n")
    lines.append("When parenting time is wrongfully denied, the court **SHALL** order:\n")
    lines.append("1. ✅ **Makeup parenting time** — same type and duration as denied")
    lines.append("2. ✅ **Economic sanctions** — reimburse expenses from wrongful denial")
    lines.append("3. ✅ **Modification of parenting time order** — adjust to prevent future denial")
    lines.append("4. ✅ **Contempt** — hold offending party in contempt of court")
    lines.append("5. ✅ **Attorney fees and costs** — mandatory cost shifting\n")
    lines.append("**Application:** 329+ days of denied parenting time triggers ALL mandatory remedies. \"Shall\" = mandatory. Court has no discretion to deny these remedies once wrongful denial is established.\n")

    # 4. MCL 722.23(j) - Factor J
    lines.append("### C. MCL 722.23(j) — Factor J (Anti-Alienation)\n")
    lines.append("> Factor (j): \"The willingness and ability of each of the parties to facilitate and encourage a close and continuing parent-child relationship between the child and the other parent or the child and the parents.\"\n")
    lines.append("**This is the anti-alienation factor.** Courts weigh whether each parent actively supports the child's relationship with the other parent.\n")
    lines.append("**Application:** Watson's conduct in maintaining 329+ days of separation, failing to facilitate contact, and opposing parenting time restoration is direct evidence of Factor J violation. This factor alone can be dispositive in custody modification.\n")

    # 5. MCR 3.207 — post-deprivation hearing
    lines.append("## III. MICHIGAN COURT RULE PROTECTIONS\n")
    lines.append("### A. MCR 3.207 — Ex Parte Orders & Hearing Requirements\n")

    c.execute("SELECT full_text FROM auth_rules WHERE rule_number = '3.207'")
    row = c.fetchone()
    if row and row['full_text']:
        lines.append(f"**Rule Text (excerpt):**\n```\n{row['full_text'][:2000]}\n```\n")

    lines.append("**Key Protection:** MCR 3.207(B)(6) — When ex parte orders affect custody or parenting time, the court MUST hold a hearing within 14 days. The party affected must receive notice and opportunity to be heard.\n")
    lines.append("**Application:** Ex parte orders restricting Andrew's parenting time must be followed by prompt hearing. Failure to hold timely hearing = due process violation.\n")

    # 6. MCR 3.210 — Hearings
    c.execute("SELECT full_text FROM auth_rules WHERE rule_number = '3.210'")
    row = c.fetchone()
    lines.append("### B. MCR 3.210 — Hearing Requirements\n")
    if row and row['full_text']:
        lines.append(f"**Rule Text (excerpt):**\n```\n{row['full_text'][:1500]}\n```\n")
    lines.append("**Protection:** Requires evidentiary hearings before custody/parenting time modifications. Court must make findings on the record.\n")

    # 7. Case Law
    lines.append("## IV. PROTECTIVE CASE LAW\n")
    lines.append("### A. Harvey v Harvey, 470 Mich 186 (2004)\n")
    lines.append("**Holding:** Parenting time is an independent right governed by best interests. Courts must evaluate parenting time separately from custody and apply the statutory factors.\n")
    lines.append("**Application:** Andrew's parenting time rights exist independently and cannot be eliminated as a collateral consequence of other proceedings.\n")

    lines.append("### B. Vodvarka v Grasher, 259 Mich App 1 (2003)\n")
    lines.append("**Holding:** Before modifying custody, the moving party must demonstrate either **proper cause** or a **change of circumstances** sufficient to warrant re-evaluation of best interest factors. This is a threshold requirement.\n")
    lines.append("**Application:** Any modification away from Andrew's custodial rights must clear the Vodvarka threshold. The burden falls on the party seeking modification.\n")

    lines.append("### C. Eldred v Ziny, 246 Mich App 142 (2001)\n")
    lines.append("**Holding:** \"Endangerment\" for purposes of restricting parenting time must be more than theoretical — requires evidence of significant risk to child's physical, mental, or emotional health.\n")
    lines.append("**Application:** No evidence of endangerment from Andrew's parenting. Theoretical or speculative risk is insufficient to restrict parenting time.\n")

    # Benchbook support
    lines.append("## V. BENCHBOOK SUPPORT\n")
    c.execute("SELECT section, title, content FROM auth_benchbook_entries WHERE title LIKE '%parenting%' OR title LIKE '%presumption%' OR title LIKE '%endangerment%'")
    for bb in c.fetchall():
        lines.append(f"### {bb['section']}: {bb['title']}\n")
        lines.append(f"{bb['content']}\n")

    # Summary
    lines.append("## VI. SUMMARY — AUTHORITY SHIELD\n")
    lines.append("| Authority | Protection | Strength |")
    lines.append("|-----------|-----------|----------|")
    lines.append("| U.S. Const. Amend. XIV | Fundamental parental liberty interest | ⚡ Constitutional — highest |")
    lines.append("| Troxel v Granville | Fit parent presumption | ⚡ SCOTUS binding |")
    lines.append("| MCL 722.27a | Parenting time SHALL be granted | 🔴 Mandatory statutory |")
    lines.append("| MCL 722.27a(9) | 5 mandatory remedies for denied time | 🔴 Mandatory statutory |")
    lines.append("| MCL 722.23(j) | Anti-alienation factor | 🔴 Statutory factor |")
    lines.append("| MCR 3.207(B)(6) | Post-deprivation hearing required | 🔴 Court rule |")
    lines.append("| Harvey v Harvey | Independent parenting time right | 📕 MI Supreme Court |")
    lines.append("| Vodvarka v Grasher | Threshold for modification | 📕 MI Court of Appeals |")
    lines.append("| Eldred v Ziny | Endangerment must be real, not speculative | 📕 MI Court of Appeals |")

    write_file("PROTECTIVE_AUTHORITIES.md", "\n".join(lines))


# ============================================================
# 5. ACCOUNTABILITY AUTHORITIES
# ============================================================
def build_accountability_authorities(conn):
    print("Building ACCOUNTABILITY_AUTHORITIES.md...")
    c = conn.cursor()

    lines = []
    lines.append(f"# ACCOUNTABILITY AUTHORITIES — Holding Judge & Opposition Accountable")
    lines.append(f"### Pigors v. Watson | {GENERATED_TAG}")
    lines.append(f"### Authorities for judicial disqualification, contempt, and civil rights enforcement\n")
    lines.append("---\n")

    # TOC
    lines.append("## Table of Contents\n")
    lines.append("1. [MCR 2.003 — Judicial Disqualification](#1-mcr-2003)")
    lines.append("2. [MCR 9.200 — JTC Procedure](#2-mcr-9200)")
    lines.append("3. [Michigan Code of Judicial Conduct (Canons 1–7)](#3-judicial-conduct)")
    lines.append("4. [MCR 3.606 / MCL 600.1701 — Contempt](#4-contempt)")
    lines.append("5. [MCL 600.2911 — Tortious Interference](#5-tortious-interference)")
    lines.append("6. [42 USC § 1983 — Federal Civil Rights](#6-section-1983)")
    lines.append("7. [Benchbook Violations Inventory](#7-benchbook-violations)")
    lines.append("\n---\n")

    # 1. MCR 2.003
    lines.append("## 1. MCR 2.003 — Judicial Disqualification {#1-mcr-2003}\n")
    c.execute("SELECT full_text FROM auth_rules WHERE rule_number = '2.003'")
    row = c.fetchone()
    if row and row['full_text']:
        lines.append(f"**Full Rule Text:**\n```\n{row['full_text']}\n```\n")

    lines.append("### Key Grounds for Disqualification\n")
    lines.append("| Ground | MCR 2.003(C)(1) | Application |")
    lines.append("|--------|-----------------|-------------|")
    lines.append("| (a) Personal bias | Judge has personal bias/prejudice | Pattern of one-sided rulings |")
    lines.append("| (b) Personal knowledge | Judge has personal knowledge of disputed facts | Ex parte communications |")
    lines.append("| (c) Prior involvement | Judge previously involved as lawyer/witness | N/A |")
    lines.append("| (d) Financial interest | Judge has financial interest | N/A |")
    lines.append("| (e) Related to party | Judge related to party/attorney | Check connections |")
    lines.append("")
    lines.append("**Procedure:** Motion filed under MCR 2.003(D). If denied, the decision is reviewable on appeal.\n")
    lines.append("**Application to Hon. Jenny L. McNeill:** Pattern of procedural irregularities, ex parte order issuance without adequate findings, and 329+ days of separation without meaningful hearing create grounds for disqualification motion.\n")

    # 2. MCR 9.200 — JTC Procedure
    lines.append("## 2. MCR 9.200 — Judicial Tenure Commission Procedure {#2-mcr-9200}\n")

    jtc_rules = []
    c.execute("""
        SELECT rule_number, title, full_text FROM auth_rules
        WHERE rule_type = 'MCR' AND rule_number LIKE '9.2%'
          AND title IS NOT NULL AND title != '' AND title NOT LIKE 'MCR 9.%'
        ORDER BY rule_number
    """)
    jtc_rules = c.fetchall()

    lines.append("### JTC Procedure Overview\n")
    lines.append("| MCR | Title | Key Requirement |")
    lines.append("|-----|-------|-----------------|")
    for r in jtc_rules:
        title = (r['title'] or '').replace('|', '/')
        # Extract first sentence of full_text for key requirement
        key_req = make_one_line_summary(r['title'], r['full_text']).replace('|', '/')
        lines.append(f"| **MCR {r['rule_number']}** | {title[:60]} | {truncate(key_req, 100)} |")
    lines.append("")

    # Show key JTC rules with full text
    for rn in ['9.202', '9.210', '9.220', '9.224', '9.233', '9.251']:
        c.execute("SELECT title, full_text FROM auth_rules WHERE rule_number = ?", (rn,))
        row = c.fetchone()
        if row and row['full_text'] and len(row['full_text']) > 50:
            lines.append(f"### MCR {rn}: {row['title']}\n")
            lines.append(f"```\n{row['full_text'][:2000]}\n```\n")

    lines.append("### JTC Complaint Filing Checklist\n")
    lines.append("1. ☐ Identify specific canon/rule violations with dates")
    lines.append("2. ☐ Gather supporting evidence (transcripts, orders, docket entries)")
    lines.append("3. ☐ Document pattern of conduct (not isolated incidents)")
    lines.append("4. ☐ File written complaint with JTC (MCR 9.220)")
    lines.append("5. ☐ JTC conducts preliminary investigation")
    lines.append("6. ☐ If probable cause found → formal complaint (MCR 9.224)")
    lines.append("7. ☐ Public hearing before master (MCR 9.233)")
    lines.append("8. ☐ Commission decision (MCR 9.244)")
    lines.append("9. ☐ Supreme Court review (MCR 9.251)\n")

    # 3. Canons of Judicial Conduct
    lines.append("## 3. Michigan Code of Judicial Conduct (Canons 1–7) {#3-judicial-conduct}\n")

    canons = {
        'Canon 1': ('Independence and Integrity', 'A judge should uphold the integrity and independence of the judiciary. An independent and honorable judiciary is indispensable to justice in our society.'),
        'Canon 2': ('Avoiding Impropriety', 'A judge should avoid impropriety and the appearance of impropriety in all activities. (A) Public confidence. (B) No outside influence on judicial conduct.'),
        'Canon 3': ('Impartial Performance', 'A judge should perform the duties of the office impartially and diligently. (A)(1) Adjudicative responsibilities. (A)(4) No ex parte communications. (A)(5) No bias.'),
        'Canon 4': ('Extra-judicial Activities', 'A judge should so conduct extra-judicial activities as to minimize the risk of conflict with judicial obligations.'),
        'Canon 5': ('Regulation of Political Activity', 'A judge should regulate political activity to minimize the risk of conflict with judicial obligations.'),
        'Canon 6': ('Compensation and Reimbursement', 'A judge may receive compensation and reimbursement of expenses for allowed extra-judicial activities.'),
        'Canon 7': ('Pro Tempore Judges', 'A judge pro tempore should comply with this Code.'),
    }

    for canon, (title, desc) in canons.items():
        lines.append(f"### {canon}: {title}\n")
        lines.append(f"{desc}\n")

    # Get benchbook violations by canon
    c.execute("""
        SELECT rule, COUNT(*) as cnt, GROUP_CONCAT(substr(explanation, 1, 120), ' | ') as explanations
        FROM auth_benchbook_violations
        WHERE rule LIKE 'Canon%'
        GROUP BY rule
        ORDER BY cnt DESC
    """)
    canon_violations = c.fetchall()

    if canon_violations:
        lines.append("### Documented Canon Violations in Our Case\n")
        lines.append("| Canon | Violation Count | Sample Explanations |")
        lines.append("|-------|----------------|---------------------|")
        for v in canon_violations:
            expl = truncate(v['explanations'] or '', 150).replace('|', '/')
            lines.append(f"| **{v['rule']}** | {v['cnt']} | {expl} |")
        lines.append("")

    # 4. Contempt
    lines.append("## 4. Contempt of Court — MCR 3.606 / MCL 600.1701 {#4-contempt}\n")

    c.execute("SELECT full_text FROM auth_rules WHERE rule_number = '3.606'")
    row = c.fetchone()
    if row and row['full_text']:
        lines.append(f"### MCR 3.606 — Contempts Outside Immediate Presence of Court\n")
        lines.append(f"```\n{row['full_text'][:3000]}\n```\n")

    lines.append("### Contempt Authority Summary\n")
    lines.append("| Type | Authority | Standard | Remedy |")
    lines.append("|------|-----------|----------|--------|")
    lines.append("| Civil contempt | MCR 3.606, MCL 600.1701 | Willful disobedience of court order | Coercive — compliance |")
    lines.append("| Criminal contempt | MCL 600.1701 | Willful obstruction of justice | Punitive — fine/jail |")
    lines.append("| Parenting time contempt | MCL 722.27a(9) | Wrongful denial of parenting time | Mandatory remedies |")
    lines.append("")
    lines.append("**Application against Watson:** Denial of court-ordered parenting time for 329+ days constitutes prima facie civil contempt. MCL 722.27a(9) provides mandatory remedies.\n")
    lines.append("**Application against Court:** Failure to enforce existing orders or hold timely hearings may constitute constructive denial of rights.\n")

    # 5. Tortious Interference
    lines.append("## 5. MCL 600.2911 — Tortious Interference with Parental Relationship {#5-tortious-interference}\n")
    lines.append("### Elements of Tortious Interference\n")
    lines.append("1. **Existence of parental relationship** — Andrew is biological father with legal custody rights")
    lines.append("2. **Defendant's knowledge of relationship** — Watson clearly knew of the relationship")
    lines.append("3. **Intentional interference** — Deliberate actions to prevent parenting time")
    lines.append("4. **Causation** — Watson's actions directly caused 329+ days of separation")
    lines.append("5. **Damages** — Psychological harm to child and parent, economic losses\n")
    lines.append("**Statutory Basis:** MCL 600.2911 authorizes civil action for interference with parental relationship.\n")
    lines.append("**Application:** Watson's sustained campaign of parenting time denial, combined with court manipulation, satisfies all elements of tortious interference.\n")

    # 6. 42 USC 1983
    lines.append("## 6. 42 USC § 1983 — Federal Civil Rights {#6-section-1983}\n")
    lines.append("> \"Every person who, under color of any statute, ordinance, regulation, custom, or usage, of any State ... subjects, or causes to be subjected, any citizen of the United States ... to the deprivation of any rights, privileges, or immunities secured by the Constitution and laws, shall be liable to the party injured in an action at law.\"\n")
    lines.append("### Elements for § 1983 Claim\n")
    lines.append("1. **Action under color of state law** — Judge acting in official capacity")
    lines.append("2. **Deprivation of constitutional right** — 14th Amendment due process (parental rights)")
    lines.append("3. **Causation** — Judge's orders directly caused deprivation")
    lines.append("4. **Damages** — 329+ days separation, psychological harm, economic loss\n")
    lines.append("### Judicial Immunity Considerations\n")
    lines.append("- **General rule:** Judges have absolute immunity for judicial acts")
    lines.append("- **Exception 1:** Acts not taken in judicial capacity (administrative acts)")
    lines.append("- **Exception 2:** Acts taken in complete absence of all jurisdiction")
    lines.append("- **Exception 3:** Injunctive/declaratory relief still available under § 1983")
    lines.append("- *Pulliam v Allen*, 466 U.S. 522 (1984) — Declaratory/injunctive relief against judges\n")
    lines.append("**Filing:** USDC Western District of Michigan. Must exhaust state remedies first for Rooker-Feldman doctrine.\n")

    # 7. Benchbook Violations
    lines.append("## 7. Benchbook Violations Inventory {#7-benchbook-violations}\n")

    c.execute("""
        SELECT rule, COUNT(*) as cnt,
               AVG(severity) as avg_severity,
               GROUP_CONCAT(substr(matching_text, 1, 80), ' || ') as samples
        FROM auth_benchbook_violations
        GROUP BY rule
        ORDER BY cnt DESC
    """)
    all_violations = c.fetchall()

    if all_violations:
        lines.append(f"**Total documented violations:** {sum(v['cnt'] for v in all_violations)}\n")
        lines.append("| Rule/Canon | Count | Avg Severity | Sample Evidence |")
        lines.append("|------------|-------|-------------|-----------------|")
        for v in all_violations:
            sev = f"{v['avg_severity']:.1f}" if v['avg_severity'] else "N/A"
            samples = truncate(v['samples'] or '', 120).replace('|', '/')
            lines.append(f"| **{v['rule']}** | {v['cnt']} | {sev} | {samples} |")
    lines.append("")

    write_file("ACCOUNTABILITY_AUTHORITIES.md", "\n".join(lines))


# ============================================================
# 6. AUTHORITY MERMAID HIERARCHY
# ============================================================
def build_mermaid_hierarchy(conn):
    print("Building AUTHORITY_MERMAID_HIERARCHY.md...")
    c = conn.cursor()

    lines = []
    lines.append(f"# AUTHORITY MERMAID HIERARCHY — Visual Authority Maps")
    lines.append(f"### Pigors v. Watson | {GENERATED_TAG}")
    lines.append(f"### Interactive authority hierarchy diagrams\n")
    lines.append("---\n")

    # 1. Constitutional hierarchy
    lines.append("## 1. Authority Hierarchy: Constitution → Statutes → Court Rules → Case Law\n")
    lines.append("```mermaid")
    lines.append("graph TD")
    lines.append('    CONST["⚡ U.S. Constitution<br/>14th Amendment Due Process"]')
    lines.append('    SCOTUS["⚡ U.S. Supreme Court<br/>Troxel v Granville, 530 U.S. 57"]')
    lines.append('    MICONST["🏛️ Michigan Constitution<br/>Art. 6 - Judicial Branch"]')
    lines.append('    MCL["📜 Michigan Compiled Laws<br/>MCL 722.21-722.31 Child Custody Act<br/>MCL 600.2950 PPO<br/>MCL 600.1701 Contempt"]')
    lines.append('    MCR["📋 Michigan Court Rules<br/>MCR 2.xxx Civil Procedure<br/>MCR 3.xxx Special Proceedings<br/>MCR 7.xxx Appellate<br/>MCR 9.xxx Judicial Discipline"]')
    lines.append('    MRE["📖 Michigan Rules of Evidence<br/>MRE 401-403 Relevance<br/>MRE 801-807 Hearsay<br/>MRE 901-902 Authentication"]')
    lines.append('    MISCT["📕 MI Supreme Court<br/>Harvey v Harvey (2004)"]')
    lines.append('    MICOA["📗 MI Court of Appeals<br/>Vodvarka v Grasher (2003)<br/>Eldred v Ziny (2001)"]')
    lines.append('    BENCH["📘 Benchbooks<br/>Judicial Conduct Standards"]')
    lines.append('    SCAO["📝 SCAO Forms & Admin Orders"]')
    lines.append("")
    lines.append("    CONST --> SCOTUS")
    lines.append("    CONST --> MICONST")
    lines.append("    SCOTUS --> MISCT")
    lines.append("    MICONST --> MCL")
    lines.append("    MICONST --> MCR")
    lines.append("    MICONST --> MRE")
    lines.append("    MCL --> MISCT")
    lines.append("    MCR --> MISCT")
    lines.append("    MISCT --> MICOA")
    lines.append("    MCR --> SCAO")
    lines.append("    MISCT --> BENCH")
    lines.append("")
    lines.append('    style CONST fill:#ff6b6b,stroke:#c0392b,color:#fff')
    lines.append('    style SCOTUS fill:#ff6b6b,stroke:#c0392b,color:#fff')
    lines.append('    style MICONST fill:#e74c3c,stroke:#c0392b,color:#fff')
    lines.append('    style MCL fill:#3498db,stroke:#2980b9,color:#fff')
    lines.append('    style MCR fill:#2ecc71,stroke:#27ae60,color:#fff')
    lines.append('    style MRE fill:#9b59b6,stroke:#8e44ad,color:#fff')
    lines.append('    style MISCT fill:#f39c12,stroke:#e67e22,color:#fff')
    lines.append('    style MICOA fill:#f1c40f,stroke:#f39c12,color:#333')
    lines.append('    style BENCH fill:#1abc9c,stroke:#16a085,color:#fff')
    lines.append('    style SCAO fill:#95a5a6,stroke:#7f8c8d,color:#fff')
    lines.append("```\n")

    # 2. MCL 722 Custody Tree
    lines.append("## 2. MCL 722 — Child Custody Act Structure\n")
    lines.append("```mermaid")
    lines.append("graph TD")
    lines.append('    ROOT["📜 MCL 722 — Child Custody Act"]')
    lines.append('    S21["MCL 722.21<br/>Scope"]')
    lines.append('    S22["MCL 722.22<br/>Definitions"]')
    lines.append('    S23["🔴 MCL 722.23<br/>Best Interest Factors"]')
    lines.append('    S24["MCL 722.24<br/>Guardian ad Litem"]')
    lines.append('    S25["MCL 722.25<br/>Grandparent Custody"]')
    lines.append('    S26["MCL 722.26<br/>Custody Orders"]')
    lines.append('    S26A["MCL 722.26a<br/>Joint Custody"]')
    lines.append('    S27["🔴 MCL 722.27<br/>Modification / ECE"]')
    lines.append('    S27A["🔴 MCL 722.27a<br/>Parenting Time"]')
    lines.append('    S27B["MCL 722.27b<br/>Makeup Time"]')
    lines.append('    S28["MCL 722.28<br/>Mediation"]')
    lines.append('    S30["MCL 722.30<br/>Attorney Fees"]')
    lines.append('    S31["MCL 722.31<br/>Domicile Change"]')
    lines.append("")
    lines.append("    ROOT --> S21")
    lines.append("    ROOT --> S22")
    lines.append("    ROOT --> S23")
    lines.append("    ROOT --> S24")
    lines.append("    ROOT --> S25")
    lines.append("    ROOT --> S26")
    lines.append("    ROOT --> S26A")
    lines.append("    ROOT --> S27")
    lines.append("    ROOT --> S27A")
    lines.append("    ROOT --> S27B")
    lines.append("    ROOT --> S28")
    lines.append("    ROOT --> S30")
    lines.append("    ROOT --> S31")
    lines.append("")

    # Best Interest Factors subtree
    lines.append('    FA["(a) Love/affection"]')
    lines.append('    FB["(b) Capacity for guidance"]')
    lines.append('    FC["(c) Material needs"]')
    lines.append('    FD["(d) Stable environment"]')
    lines.append('    FE["(e) Family permanence"]')
    lines.append('    FF["(f) Moral fitness"]')
    lines.append('    FG["(g) Mental/physical health"]')
    lines.append('    FH["(h) Home/school/community"]')
    lines.append('    FI["(i) Child preference"]')
    lines.append('    FJ["🔴 (j) Factor J<br/>Anti-Alienation"]')
    lines.append('    FK["(k) Domestic violence"]')
    lines.append('    FL["(l) Other factors"]')
    lines.append("")
    lines.append("    S23 --> FA")
    lines.append("    S23 --> FB")
    lines.append("    S23 --> FC")
    lines.append("    S23 --> FD")
    lines.append("    S23 --> FE")
    lines.append("    S23 --> FF")
    lines.append("    S23 --> FG")
    lines.append("    S23 --> FH")
    lines.append("    S23 --> FI")
    lines.append("    S23 --> FJ")
    lines.append("    S23 --> FK")
    lines.append("    S23 --> FL")
    lines.append("")

    # Parenting time subtree
    lines.append('    PT1["PT Presumption"]')
    lines.append('    PT2["No deny w/o endangerment"]')
    lines.append('    PT3["Specific schedule"]')
    lines.append('    PT9["🔴 722.27a(9)<br/>MANDATORY REMEDIES"]')
    lines.append('    REM1["Makeup time"]')
    lines.append('    REM2["Economic sanctions"]')
    lines.append('    REM3["Order modification"]')
    lines.append('    REM4["Contempt"]')
    lines.append('    REM5["Attorney fees"]')
    lines.append("")
    lines.append("    S27A --> PT1")
    lines.append("    S27A --> PT2")
    lines.append("    S27A --> PT3")
    lines.append("    S27A --> PT9")
    lines.append("    PT9 --> REM1")
    lines.append("    PT9 --> REM2")
    lines.append("    PT9 --> REM3")
    lines.append("    PT9 --> REM4")
    lines.append("    PT9 --> REM5")
    lines.append("")

    # ECE subtree
    lines.append('    ECE["Established Custodial<br/>Environment"]')
    lines.append('    COC["Change of<br/>Circumstances"]')
    lines.append('    BUR1["Clear & convincing<br/>(if ECE changes)"]')
    lines.append('    BUR2["Preponderance<br/>(if no ECE change)"]')
    lines.append("")
    lines.append("    S27 --> ECE")
    lines.append("    S27 --> COC")
    lines.append("    ECE --> BUR1")
    lines.append("    ECE --> BUR2")
    lines.append("")

    lines.append('    style S23 fill:#ff6b6b,stroke:#c0392b,color:#fff')
    lines.append('    style S27 fill:#ff6b6b,stroke:#c0392b,color:#fff')
    lines.append('    style S27A fill:#ff6b6b,stroke:#c0392b,color:#fff')
    lines.append('    style FJ fill:#e74c3c,stroke:#c0392b,color:#fff')
    lines.append('    style PT9 fill:#e74c3c,stroke:#c0392b,color:#fff')
    lines.append("```\n")

    # 3. MRE Authentication Decision Flowchart
    lines.append("## 3. MRE Authentication Decision Flowchart\n")
    lines.append("```mermaid")
    lines.append("flowchart TD")
    lines.append('    START["📄 Evidence to Authenticate"]')
    lines.append('    Q1{"Is it a certified<br/>public record?"}')
    lines.append('    A1["✅ Self-Authenticating<br/>MRE 902(1)-(4)<br/>No foundation needed"]')
    lines.append('    Q2{"Is it a certified<br/>business record?"}')
    lines.append('    A2["✅ Self-Authenticating<br/>MRE 902(11)-(12)<br/>With custodian declaration"]')
    lines.append('    Q3{"Is it an official<br/>publication?"}')
    lines.append('    A3["✅ Self-Authenticating<br/>MRE 902(5)<br/>Published by authority"]')
    lines.append('    Q4{"Can a witness<br/>authenticate?"}')
    lines.append('    A4["✅ MRE 901(b)(1)<br/>Testimony of witness<br/>with knowledge"]')
    lines.append('    Q5{"Distinctive<br/>characteristics?"}')
    lines.append('    A5["✅ MRE 901(b)(4)<br/>Appearance, contents,<br/>substance, patterns"]')
    lines.append('    Q6{"Electronic / digital<br/>evidence?"}')
    lines.append('    A6["✅ MRE 901(b)(9)<br/>System or process<br/>description + testimony"]')
    lines.append('    FAIL["⚠️ Consider other<br/>901(b) methods or<br/>stipulation"]')
    lines.append("")
    lines.append("    START --> Q1")
    lines.append("    Q1 -->|YES| A1")
    lines.append("    Q1 -->|NO| Q2")
    lines.append("    Q2 -->|YES| A2")
    lines.append("    Q2 -->|NO| Q3")
    lines.append("    Q3 -->|YES| A3")
    lines.append("    Q3 -->|NO| Q4")
    lines.append("    Q4 -->|YES| A4")
    lines.append("    Q4 -->|NO| Q5")
    lines.append("    Q5 -->|YES| A5")
    lines.append("    Q5 -->|NO| Q6")
    lines.append("    Q6 -->|YES| A6")
    lines.append("    Q6 -->|NO| FAIL")
    lines.append("")
    lines.append('    style A1 fill:#2ecc71,stroke:#27ae60,color:#fff')
    lines.append('    style A2 fill:#2ecc71,stroke:#27ae60,color:#fff')
    lines.append('    style A3 fill:#2ecc71,stroke:#27ae60,color:#fff')
    lines.append('    style A4 fill:#3498db,stroke:#2980b9,color:#fff')
    lines.append('    style A5 fill:#3498db,stroke:#2980b9,color:#fff')
    lines.append('    style A6 fill:#9b59b6,stroke:#8e44ad,color:#fff')
    lines.append('    style FAIL fill:#e74c3c,stroke:#c0392b,color:#fff')
    lines.append("```\n")

    # 4. Filing Authority Map
    lines.append("## 4. Filing Authority Map — Which MCR Governs Which Filing\n")
    lines.append("```mermaid")
    lines.append("graph LR")
    lines.append('    subgraph "Lane A: Custody"')
    lines.append('        LA1["Motion to Restore PT<br/>MCR 3.208<br/>MCL 722.27a"]')
    lines.append('        LA2["Motion to Modify Custody<br/>MCR 3.210<br/>MCL 722.27"]')
    lines.append('        LA3["Motion to Compel Discovery<br/>MCR 2.313"]')
    lines.append('        LA4["Contempt Motion<br/>MCR 3.606<br/>MCL 600.1701"]')
    lines.append('        LA5["Summary Disposition<br/>MCR 2.116"]')
    lines.append("    end")
    lines.append("")
    lines.append('    subgraph "Lane D: PPO"')
    lines.append('        LD1["Motion to Dissolve PPO<br/>MCR 3.707<br/>MCL 600.2950"]')
    lines.append('        LD2["Response to PPO<br/>MCR 3.310"]')
    lines.append("    end")
    lines.append("")
    lines.append('    subgraph "Lane E: Judicial Misconduct"')
    lines.append('        LE1["Disqualification Motion<br/>MCR 2.003"]')
    lines.append('        LE2["JTC Complaint<br/>MCR 9.220-9.224"]')
    lines.append('        LE3["Judicial Conduct<br/>Canons 1-7"]')
    lines.append("    end")
    lines.append("")
    lines.append('    subgraph "Lane F: Appellate"')
    lines.append('        LF1["Claim of Appeal<br/>MCR 7.204"]')
    lines.append('        LF2["Leave Application<br/>MCR 7.205"]')
    lines.append('        LF3["Appellant Brief<br/>MCR 7.212"]')
    lines.append('        LF4["Record on Appeal<br/>MCR 7.210"]')
    lines.append('        LF5["Motions in COA<br/>MCR 7.211"]')
    lines.append("    end")
    lines.append("")
    lines.append('    subgraph "All Filings"')
    lines.append('        ALL1["Filing Standards<br/>MCR 1.109"]')
    lines.append('        ALL2["Service<br/>MCR 2.105/2.107"]')
    lines.append('        ALL3["Pleading Form<br/>MCR 2.113"]')
    lines.append('        ALL4["Signatures<br/>MCR 2.114"]')
    lines.append("    end")
    lines.append("")
    lines.append("    ALL1 -.-> LA1")
    lines.append("    ALL1 -.-> LD1")
    lines.append("    ALL1 -.-> LE1")
    lines.append("    ALL1 -.-> LF1")
    lines.append("    ALL2 -.-> LA1")
    lines.append("    ALL2 -.-> LD1")
    lines.append("    ALL2 -.-> LE1")
    lines.append("    ALL2 -.-> LF1")
    lines.append("")
    lines.append('    style LA1 fill:#3498db,stroke:#2980b9,color:#fff')
    lines.append('    style LA2 fill:#3498db,stroke:#2980b9,color:#fff')
    lines.append('    style LD1 fill:#e67e22,stroke:#d35400,color:#fff')
    lines.append('    style LE1 fill:#e74c3c,stroke:#c0392b,color:#fff')
    lines.append('    style LE2 fill:#e74c3c,stroke:#c0392b,color:#fff')
    lines.append('    style LF1 fill:#9b59b6,stroke:#8e44ad,color:#fff')
    lines.append('    style LF3 fill:#9b59b6,stroke:#8e44ad,color:#fff')
    lines.append("```\n")

    # 5. Case Lane Connectivity
    lines.append("## 5. Case Lane Cross-References\n")
    lines.append("```mermaid")
    lines.append("graph TD")
    lines.append('    A["🔵 Lane A<br/>Watson Custody<br/>2024-001507-DC"]')
    lines.append('    D["🟠 Lane D<br/>PPO<br/>2023-5907-PP"]')
    lines.append('    E["🔴 Lane E<br/>Judicial Misconduct"]')
    lines.append('    F["🟣 Lane F<br/>COA 366810"]')
    lines.append('    FED["⚡ Federal<br/>42 USC 1983<br/>USDC W.D. Mich"]')
    lines.append("")
    lines.append('    A -->|"Ex parte orders<br/>created basis"| D')
    lines.append('    A -->|"Procedural violations<br/>fuel complaints"| E')
    lines.append('    A -->|"Appeal of right<br/>from final orders"| F')
    lines.append('    D -->|"PPO affects<br/>custody factors"| A')
    lines.append('    E -->|"Disqualification<br/>affects all lanes"| A')
    lines.append('    E -->|"Constitutional<br/>violations"| FED')
    lines.append('    F -->|"Reversal returns<br/>to trial court"| A')
    lines.append("")
    lines.append('    style A fill:#3498db,stroke:#2980b9,color:#fff')
    lines.append('    style D fill:#e67e22,stroke:#d35400,color:#fff')
    lines.append('    style E fill:#e74c3c,stroke:#c0392b,color:#fff')
    lines.append('    style F fill:#9b59b6,stroke:#8e44ad,color:#fff')
    lines.append('    style FED fill:#2c3e50,stroke:#1a252f,color:#fff')
    lines.append("```\n")

    write_file("AUTHORITY_MERMAID_HIERARCHY.md", "\n".join(lines))


# ============================================================
# MAIN
# ============================================================
def main():
    print(f"{'='*60}")
    print(f"LitigationOS Authority Reference Generator")
    print(f"Database: {DB_PATH}")
    print(f"Output:   {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = get_conn()

    try:
        build_mcr_complete_index(conn)
        build_mcl_custody_guide(conn)
        build_mre_guide(conn)
        build_protective_authorities(conn)
        build_accountability_authorities(conn)
        build_mermaid_hierarchy(conn)
    finally:
        conn.close()

    print(f"\n{'='*60}")
    print(f"✅ All 6 authority reference documents generated.")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
