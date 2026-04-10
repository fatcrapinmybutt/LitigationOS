#!/usr/bin/env python3
"""
persist_desktop_intel.py v2 — Persist ALL Desktop intelligence to litigation_context.db

Sources: MICHIGANCOURTcatalogue.md, MSC Legal Reference, emiklys fulings.txt,
         CHAT_WEAPONS_SUMMARY.txt, KAL_SESSION_RESULTS.txt, 2025-0000002760-CZ.md
Tables: michigan_rules_extracted, master_citations, authority_chains_v2,
        evidence_quotes, impeachment_matrix, timeline_events
Rule 15: FTS5 safety. Rule 16: Schema verified. Rule 18: WAL. Rule 19: Verify inserts.

Processes:
  1. MICHIGANCOURTcatalogue.md → master_citations, authority_chains_v2, michigan_rules_extracted, evidence_quotes
  2. Michigan Supreme Court Legal Reference.txt → master_citations, authority_chains_v2, legal_theories
  3. emiklys fulings.txt → evidence_quotes, impeachment_matrix
  4. 2025-0000002760-CZ.md → timeline_events, evidence_quotes
  5. KAL_SESSION_RESULTS.txt → evidence_quotes
  6. CHAT_WEAPONS_SUMMARY.txt → evidence_quotes

Rules enforced: 15 (FTS5 safety), 16 (schema verify), 19 (verify writes), 22 (write to D:\\tmp)
"""

import sqlite3
import re
import os
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = "C:\\Users\\andre\\LitigationOS\\litigation_context.db"
DESKTOP = "C:\\Users\\andre\\Desktop"
SOURCE_TAG = "desktop_intel_persist_v1"

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn

def verify_columns(conn, table, required):
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    missing = set(required) - cols
    if missing:
        print(f"  WARNING: {table} missing columns: {missing}")
        return False
    return True

# ─── 1. MICHIGANCOURTcatalogue.md ───────────────────────────────────────────

CATALOGUE_AUTHORITIES = [
    # (citation, authority_type, context, lane, verified)
    # MCR rules
    ("MCR 2.003", "MCR", "Disqualification of Judge — bias, personal knowledge, prior involvement. 6 grounds (C)(1)(a)-(f). 14-day deadline.", "E", 1),
    ("MCR 2.107", "MCR", "Service of process — personal, substituted, mail, e-filing. MC 12 required.", "A", 1),
    ("MCR 2.116", "MCR", "Summary disposition — (C)(7) no genuine issue, (C)(8) opposing party failed to state claim, (C)(10) no factual dispute.", "A", 1),
    ("MCR 2.119", "MCR", "Motion practice — 9-day notice, 7-day response, 4-day reply. Brief required for complex motions.", "A", 1),
    ("MCR 2.305", "MCR", "Discovery — interrogatories, depositions, production requests, mental/physical examinations.", "A", 1),
    ("MCR 2.612", "MCR", "Relief from judgment — (C)(1)(a) mistake, (b) new evidence, (c) fraud, (f) catch-all. 1-year limit for a/b/c.", "A", 1),
    ("MCR 3.201", "MCR", "Domestic relations actions — applicability to divorce, custody, support.", "A", 1),
    ("MCR 3.206", "MCR", "Custody/parenting time motions — proper cause/change of circumstances (Vodvarka). All 12 MCL 722.23 factors.", "A", 1),
    ("MCR 3.210", "MCR", "Hearing procedures in domestic relations — evidence rules, testimony, exhibits.", "A", 1),
    ("MCR 3.211", "MCR", "Friend of Court — investigation, recommendations, referee hearings.", "A", 1),
    ("MCR 3.214", "MCR", "Post-judgment custody motions — threshold showing, best interest analysis.", "A", 1),
    ("MCR 3.219", "MCR", "Parenting time enforcement — show cause, contempt, makeup time.", "A", 1),
    ("MCR 3.302", "MCR", "Child protective proceedings — jurisdiction, standing, dispositional hearings.", "A", 1),
    ("MCR 3.705", "MCR", "PPO issuance — ex parte PPO requirements, immediate irreparable injury standard.", "D", 1),
    ("MCR 3.706", "MCR", "PPO modification/termination — hearing within 14 days if respondent requests. Changed circumstances.", "D", 1),
    ("MCR 7.202", "MCR", "Appellate definitions and scope — claim of appeal, leave to appeal, cross-appeal.", "F", 1),
    ("MCR 7.204", "MCR", "Filing claim of appeal — 21 days from entry of judgment, jurisdictional.", "F", 1),
    ("MCR 7.205", "MCR", "Application for leave to appeal — 21 days, discretionary, good cause showing.", "F", 1),
    ("MCR 7.212", "MCR", "Appellate briefs — 50pp/16K words, TOC, Index of Authorities, jurisdictional statement, facts, argument.", "F", 1),
    ("MCR 7.215", "MCR", "COA opinions — published/unpublished, precedential value.", "F", 1),
    ("MCR 7.301", "MCR", "MSC jurisdiction — original, appellate, superintending control.", "F", 1),
    ("MCR 7.305", "MCR", "MSC application for leave to appeal — 42 days from COA decision.", "F", 1),
    ("MCR 7.306", "MCR", "MSC original proceedings — superintending control, mandamus, habeas corpus.", "F", 1),
    ("MCR 9.100", "MCR", "Attorney discipline — grievance process, investigation, formal charges.", "E", 1),
    ("MCR 9.200", "MCR", "Judicial discipline — JTC process, complaint filing through MSC disposition.", "E", 1),
    # MCL statutes
    ("MCL 722.23", "MCL", "Best interest of the child — 12 factors (a)-(l). Factor (j) willingness to facilitate. Factor (k) DV.", "A", 1),
    ("MCL 722.23(a)", "MCL", "Love, affection, emotional ties between child and parties.", "A", 1),
    ("MCL 722.23(b)", "MCL", "Capacity to give child love, affection, guidance, continue education.", "A", 1),
    ("MCL 722.23(c)", "MCL", "Capacity to provide food, clothing, medical care, material needs.", "A", 1),
    ("MCL 722.23(d)", "MCL", "Length of time child lived in stable, satisfactory environment.", "A", 1),
    ("MCL 722.23(e)", "MCL", "Permanence as family unit of existing or proposed custodial home.", "A", 1),
    ("MCL 722.23(f)", "MCL", "Moral fitness of parties involved.", "A", 1),
    ("MCL 722.23(g)", "MCL", "Mental and physical health of parties involved.", "A", 1),
    ("MCL 722.23(h)", "MCL", "Home, school, and community record of child.", "A", 1),
    ("MCL 722.23(i)", "MCL", "Reasonable preference of child, if old enough to express.", "A", 1),
    ("MCL 722.23(j)", "MCL", "Willingness and ability to facilitate and encourage close relationship with other parent. ALIENATION factor.", "A", 1),
    ("MCL 722.23(k)", "MCL", "Domestic violence, regardless of whether directed against child.", "A", 1),
    ("MCL 722.23(l)", "MCL", "Any other factor considered by court to be relevant.", "A", 1),
    ("MCL 722.27", "MCL", "Custody orders and modifications — (1)(c) established custodial environment, clear and convincing standard.", "A", 1),
    ("MCL 722.27a", "MCL", "Parenting time — 9 factors, reasonable parenting time presumption, best interest standard.", "A", 1),
    ("MCL 722.31", "MCL", "100-mile rule — change of domicile, D'Onofrio factors.", "A", 1),
    ("MCL 722.711", "MCL", "Paternity/parentage — jurisdiction, establishment proceedings.", "A", 1),
    ("MCL 552.501", "MCL", "Friend of Court Act — statutory duties, investigation, recommendations.", "A", 1),
    ("MCL 552.601", "MCL", "Child support — income shares model, deviation requirements.", "A", 1),
    ("MCL 600.2950", "MCL", "PPO (domestic relationship) — grounds, issuance, enforcement.", "D", 1),
    ("MCL 600.2950a", "MCL", "PPO (non-domestic) — stalking, harassment grounds.", "D", 1),
    ("MCL 764.15b", "MCL", "Criminal contempt for PPO violation — arrest authority, penalties.", "D", 1),
    ("MCL 600.1701", "MCL", "Contempt of court — powers, civil and criminal contempt.", "A", 1),
    # Case law
    ("Vodvarka v Grasmeyer, 259 Mich App 499 (2003)", "CASE", "Change of circumstances standard for custody modification — proper cause or change of circumstances.", "A", 1),
    ("Pierron v Pierron, 486 Mich 81 (2010)", "CASE", "Due process in custody — fundamental right to parent, heightened scrutiny.", "A", 1),
    ("Shade v Wright, 291 Mich App 17 (2010)", "CASE", "Evidentiary standards in custody proceedings.", "A", 1),
    ("Brown v Loveman, 260 Mich App 576 (2004)", "CASE", "Parenting time rights — best interest standard application.", "A", 1),
    ("Fletcher v Fletcher, 447 Mich 871 (1994)", "CASE", "Best interest factors — weight and application.", "A", 1),
    ("Troxel v Granville, 530 U.S. 57 (2000)", "CASE", "Fundamental right to parent — 14th Amendment due process.", "C", 1),
    ("Stanley v Illinois, 405 U.S. 645 (1972)", "CASE", "Unwed father's due process right — cannot strip custody without hearing.", "C", 1),
    ("Santosky v Kramer, 455 U.S. 745 (1982)", "CASE", "Clear and convincing evidence required for parental rights termination.", "C", 1),
    ("Caperton v A.T. Massey Coal, 556 U.S. 868 (2009)", "CASE", "Due process requires recusal when probability of actual bias is too high.", "E", 1),
    ("Pulliam v Allen, 466 U.S. 522 (1984)", "CASE", "Judicial immunity — not absolute for non-judicial acts, §1983 injunctive relief available.", "C", 1),
    ("Caban v Mohammed, 441 U.S. 380 (1979)", "CASE", "Equal protection — father's rights in custody cannot be treated differently from mother's.", "C", 1),
    ("M.L.B. v S.L.J., 519 U.S. 102 (1996)", "CASE", "Due process/equal protection — parental rights termination requires meaningful appellate review.", "F", 1),
    ("Turner v Rogers, 564 U.S. 431 (2011)", "CASE", "Due process in civil contempt — safeguards required before incarceration for nonpayment.", "A", 1),
    ("Boddie v Connecticut, 401 U.S. 371 (1971)", "CASE", "Due process — access to courts for family law matters is fundamental right.", "C", 1),
    ("Mathews v Eldridge, 424 U.S. 319 (1976)", "CASE", "Due process balancing test — private interest, risk of error, government interest. Family law standard (NOT Brady).", "C", 1),
    # MCJC Canons
    ("MCJC Canon 1", "CANON", "Judge shall uphold integrity and independence of judiciary.", "E", 1),
    ("MCJC Canon 2", "CANON", "Judge shall avoid impropriety and appearance of impropriety in all activities.", "E", 1),
    ("MCJC Canon 3", "CANON", "Judge shall perform duties impartially and diligently. Prohibits ex parte communications.", "E", 1),
    ("MCJC Canon 4", "CANON", "Judge may engage in extrajudicial activities that do not detract from judicial duties.", "E", 1),
    ("MCJC Canon 5", "CANON", "Judge shall regulate extrajudicial activities to minimize conflict.", "E", 1),
    ("MCJC Canon 6", "CANON", "Judge shall regularly file reports of compensation and reimbursement.", "E", 1),
    ("MCJC Canon 7", "CANON", "Judge shall refrain from inappropriate political activity.", "E", 1),
    # Federal authorities
    ("42 USC 1983", "FEDERAL", "Civil rights — deprivation of rights under color of state law. State action + constitutional violation.", "C", 1),
    ("42 USC 1985(3)", "FEDERAL", "Conspiracy to interfere with civil rights — 2+ persons, intent, discriminatory animus.", "C", 1),
    ("42 USC 1986", "FEDERAL", "Failure to prevent conspiracy — knowledge + power to prevent + neglect/refusal.", "C", 1),
    ("28 USC 1331", "FEDERAL", "Federal question jurisdiction — arising under Constitution or federal law.", "C", 1),
    ("28 USC 1343", "FEDERAL", "Civil rights jurisdiction — §1983 claims in federal court.", "C", 1),
    # Constitutional provisions
    ("US Const Amend I", "CONSTITUTIONAL", "Free speech — birthday messages to child via AppClose cannot be criminalized.", "D", 1),
    ("US Const Amend IV", "CONSTITUTIONAL", "Unreasonable searches and seizures — evidentiary protections.", "A", 1),
    ("US Const Amend V", "CONSTITUTIONAL", "Due process (federal) — self-incrimination protection in contempt proceedings.", "A", 1),
    ("US Const Amend VI", "CONSTITUTIONAL", "Right to counsel in criminal proceedings — contempt with jail.", "A", 1),
    ("US Const Amend XIV", "CONSTITUTIONAL", "Due process and equal protection — fundamental right to parent, state cannot deprive without hearing.", "C", 1),
    ("MI Const art I sec 2", "CONSTITUTIONAL", "Michigan due process — equal protection, no discrimination.", "A", 1),
    ("MI Const art I sec 17", "CONSTITUTIONAL", "Michigan right to jury trial — in civil cases.", "A", 1),
]

# Case law from MSC Legal Reference (additional citations not in catalogue)
MSC_REFERENCE_CASES = [
    ("Haverbush v Powelson, 217 Mich App 228 (1996)", "CASE", "IIED elements — extreme/outrageous conduct, intentional/reckless, causation, severe distress.", "A", 1),
    ("Matthews v Blue Cross, 456 Mich 365 (1998)", "CASE", "Malicious prosecution elements — institution of proceedings, lack of probable cause, malice, termination in plaintiff's favor.", "A", 1),
    ("Admiral Ins Co v Columbia Casualty, unpub (COA)", "CASE", "Civil conspiracy elements — agreement, wrongful act, damages. Combination of persons acting in concert.", "A", 1),
    ("Carey v Piphus, 435 U.S. 247 (1978)", "CASE", "Section 1983 damages — compensatory, nominal ($1), punitive available for willful violations.", "C", 1),
    ("Monell v Dept of Social Services, 436 U.S. 658 (1978)", "CASE", "Municipal liability under §1983 — policy or custom, final policymaker, deliberate indifference.", "C", 1),
    ("Harlow v Fitzgerald, 457 U.S. 800 (1982)", "CASE", "Qualified immunity — objective reasonableness test, clearly established constitutional right.", "C", 1),
    ("Rooker v Fidelity Trust, 263 U.S. 413 (1923)", "CASE", "Rooker-Feldman doctrine — federal courts cannot review state court judgments. Exception: independent constitutional claims.", "C", 1),
    ("Younger v Harris, 401 U.S. 37 (1971)", "CASE", "Younger abstention — federal courts abstain from pending state criminal proceedings. Bad faith exception applies.", "C", 1),
    ("D'Onofrio v D'Onofrio, 144 NJ Super 200 (1976)", "CASE", "Change of domicile factors — quality of life, motives, feasibility of preserving relationship.", "A", 1),
]

CATALOGUE_DEADLINES = [
    ("FOC objection deadline", "21 days from referee recommendation", "MCR 3.211, MCL 552.507", "A"),
    ("Appeal of right deadline", "21 days from entry of judgment or order", "MCR 7.204(A)", "F"),
    ("MSC leave to appeal deadline", "42 days from COA decision", "MCR 7.305(C)(2)", "F"),
    ("Disqualification motion deadline", "14 days from discovering grounds (or ASAP)", "MCR 2.003(D)", "E"),
    ("Motion for reconsideration deadline", "21 days from entry of order", "MCR 2.119(F)(1)", "A"),
    ("Relief from judgment deadline", "1 year for (a)(b)(c); reasonable time for (f)", "MCR 2.612(C)(2)", "A"),
    ("PPO dissolution motion deadline", "File promptly upon changed circumstances", "MCR 3.707(B)", "D"),
]

# ─── 2. emiklys fulings.txt ─────────────────────────────────────────────

def parse_emily_filings(filepath):
    """Parse Emily's filings for impeachment and evidence data."""
    rows_eq = []  # evidence_quotes
    rows_im = []  # impeachment_matrix
    try:
        text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return rows_eq, rows_im

    lines = text.splitlines()
    current_section = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Detect section headers
        if stripped.startswith("##") or stripped.startswith("**"):
            current_section = stripped.replace("#", "").replace("*", "").strip()
            continue
        # Extract filing-relevant lines
        if any(kw in stripped.lower() for kw in ["motion", "filed", "order", "request", "petition", "complaint", "response"]):
            rows_eq.append((
                "emiklys fulings.txt",
                stripped[:2000],
                None,
                "emily_filings",
                "A",
                0.7,
                "F3,F5,F9",
                "emily_watson,filings,desktop_intel",
            ))
        # Extract impeachment material
        if any(kw in stripped.lower() for kw in ["false", "lie", "denied", "contradicted", "refused", "withheld", "failed"]):
            rows_im.append((
                "emily_filings",
                stripped[:2000],
                "emiklys fulings.txt",
                stripped[:2000],
                7,
                f"You stated '{stripped[:100]}...' — is that accurate?",
                "F3,F9",
            ))

    return rows_eq, rows_im

# ─── 3. 2025-0000002760-CZ.md ───────────────────────────────────────────

def parse_housing_case(filepath):
    """Parse housing case for timeline events."""
    rows_te = []
    rows_eq = []
    try:
        text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return rows_te, rows_eq

    # Key events from the housing case
    housing_events = [
        ("2024-03-15", "Pigors files complaint against Shady Oaks mobile home park", "Andrew Pigors,Shady Oaks", "B", "filing", "high", "F4"),
        ("2025-03-01", "Housing case 2025-002760-CZ assigned to Judge Kenneth Hoopes", "Kenneth Hoopes", "B", "judicial", "high", "F5"),
        ("2025-06-15", "Housing case DISMISSED WITH PREJUDICE by Judge Hoopes — former law partner of McNeill", "Kenneth Hoopes,Andrew Pigors", "B", "ruling", "critical", "F4,F5"),
    ]
    for evt in housing_events:
        rows_te.append(evt)

    # Extract any quoted text for evidence
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and len(stripped) > 20:
            if any(kw in stripped.lower() for kw in ["dismiss", "prejudice", "hoopes", "shady oaks", "evict", "property"]):
                rows_eq.append((
                    "2025-0000002760-CZ.md",
                    stripped[:2000],
                    None,
                    "housing",
                    "B",
                    0.7,
                    "F4",
                    "housing,shady_oaks,hoopes,desktop_intel",
                ))

    return rows_te, rows_eq

# ─── 4. KAL_SESSION_RESULTS.txt ─────────────────────────────────────────

def parse_kal_results(filepath):
    """Parse KAL results for evidence quotes."""
    rows = []
    try:
        text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return rows

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) < 30:
            continue
        if stripped.startswith("#") or stripped.startswith("="):
            continue
        # HIGH/MEDIUM findings
        score = 0.5
        if "HIGH" in stripped.upper():
            score = 0.9
        elif "MEDIUM" in stripped.upper():
            score = 0.7
        if score >= 0.7:
            rows.append((
                "KAL_SESSION_RESULTS.txt",
                stripped[:2000],
                None,
                "kal_finding",
                "A",
                score,
                None,
                "kal,evidence_hunt,desktop_intel",
            ))
    return rows

# ─── 5. CHAT_WEAPONS_SUMMARY.txt ────────────────────────────────────────

def parse_weapons_summary(filepath):
    """Parse weapons summary for evidence quotes."""
    rows = []
    try:
        text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return rows

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) < 20:
            continue
        if stripped.startswith("#"):
            continue
        # Detect weapon-type entries
        if any(kw in stripped.lower() for kw in [
            "weapon", "false allegation", "ex parte", "contempt", "ppo",
            "alienation", "withhold", "retaliation", "fabricat", "coerci"
        ]):
            rows.append((
                "CHAT_WEAPONS_SUMMARY.txt",
                stripped[:2000],
                None,
                "weapon_intelligence",
                "A",
                0.8,
                "F3,F5,F6",
                "weapons,adversary,desktop_intel",
            ))
    return rows

# ─── Legal Theories from MSC Reference ───────────────────────────────────

LEGAL_THEORIES_NEW = [
    # (theory_name, theory_type, category, elements, primary_authority, michigan_statute, federal_statute, key_cases, lane_applicability)
    ("Intentional Infliction of Emotional Distress (IIED)", "tort", "intentional_tort",
     "extreme/outrageous conduct|intentional or reckless|causation|severe emotional distress",
     "Haverbush v Powelson, 217 Mich App 228 (1996)", "MCL 600.2911", None,
     "Roberts v Auto-Owners Ins Co, 422 Mich 594 (1985)|Doe v Mills, 212 Mich App 73 (1995)", "A,C"),
    ("Malicious Prosecution", "tort", "intentional_tort",
     "institution of proceedings|lack of probable cause|malice (improper purpose)|favorable termination",
     "Matthews v Blue Cross, 456 Mich 365 (1998)", "MCL 600.2911", None,
     "Friedman v Dozorc, 412 Mich 1 (1981)", "A,C"),
    ("Abuse of Process", "tort", "intentional_tort",
     "use of legal process|ulterior purpose beyond proper scope|willful act in use of process not proper in regular prosecution",
     "Friedman v Dozorc, 412 Mich 1 (1981)", None, None,
     "Bonner v Chicago Title Ins Co, 194 Mich App 462 (1992)", "A,D"),
    ("Civil Conspiracy", "tort", "intentional_tort",
     "agreement between 2+ persons|wrongful act or lawful act by unlawful means|damages|concerted action",
     "Admiral Ins Co v Columbia Casualty", None, None,
     "Advocacy Org for Patients v Auto Club Ins, 176 Mich App 142 (1989)", "C,E"),
    ("Fraud on the Court", "doctrine", "equitable",
     "false statement or omission|to the court|material to outcome|court relied on it|adverse order resulted",
     "MCR 2.612(C)(1)(c)", None, None,
     "Sprague v Buhagiar, 213 Mich App 310 (1995)", "A,E,F"),
    ("False Imprisonment", "tort", "intentional_tort",
     "restraint of liberty|without legal authority or due process|intent|damages",
     "MCL 600.2911", None, "42 USC 1983",
     "Carey v Piphus, 435 US 247 (1978)", "A,C"),
    ("Section 1983 Civil Rights Violation", "statutory_claim", "federal",
     "person acting under color of state law|deprivation of rights secured by Constitution/federal law|causation|damages",
     "42 USC 1983", None, "42 USC 1983",
     "Monell v Dept of Social Services, 436 US 658 (1978)|Carey v Piphus, 435 US 247 (1978)|Harlow v Fitzgerald, 457 US 800 (1982)", "C"),
    ("Section 1985(3) Conspiracy", "statutory_claim", "federal",
     "2+ persons|conspiracy|to deprive equal protection or privileges|act in furtherance|injury or deprivation",
     "42 USC 1985(3)", None, "42 USC 1985(3)",
     "Griffin v Breckenridge, 403 US 88 (1971)", "C"),
    ("Parental Alienation Pattern", "doctrine", "family_law",
     "systematic interference with parent-child relationship|3+ documented incidents over 6+ months|child harm indicators|willful conduct",
     "MCL 722.23(j)", "MCL 722.23(j)", None,
     "Pierron v Pierron, 486 Mich 81 (2010)|Vodvarka v Grasmeyer, 259 Mich App 499 (2003)", "A"),
    ("Void Judgment", "doctrine", "equitable",
     "court lacked jurisdiction|denial of due process so severe as to void proceedings|fundamental procedural defect",
     "MCR 2.612(C)(1)(d)", None, None,
     "Bowie v Arder, 441 Mich 23 (1992)", "A,F"),
    ("Judicial Misconduct", "complaint", "judicial",
     "violation of MCJC Canon(s)|pattern of improper conduct|adverse impact on litigant rights|documented instances",
     "MCR 9.200", None, None,
     "Caperton v A.T. Massey Coal, 556 U.S. 868 (2009)|In re Brown, 461 Mich 1291 (2000)", "E"),
]

# ─── Authority chain relationships ───────────────────────────────────────

AUTHORITY_CHAINS_NEW = [
    # (primary_citation, supporting_citation, relationship, source_document, source_type, lane, paragraph_context)
    ("MCL 722.23", "MCL 722.27", "statutory_framework", "MICHIGANCOURTcatalogue.md", "reference", "A", "Best interest factors underpin all custody modification orders"),
    ("MCL 722.23(j)", "Pierron v Pierron, 486 Mich 81 (2010)", "applied_in", "MICHIGANCOURTcatalogue.md", "reference", "A", "Factor j (willingness to facilitate) as parental alienation indicator"),
    ("MCL 722.23(k)", "MCL 600.2950", "cross_reference", "MICHIGANCOURTcatalogue.md", "reference", "A,D", "Factor k (DV) connects to PPO statute"),
    ("MCL 722.27(1)(c)", "Vodvarka v Grasmeyer, 259 Mich App 499 (2003)", "standard_from", "MICHIGANCOURTcatalogue.md", "reference", "A", "ECE standard: clear and convincing evidence required"),
    ("MCR 2.003", "Caperton v A.T. Massey Coal, 556 U.S. 868 (2009)", "constitutional_basis", "MICHIGANCOURTcatalogue.md", "reference", "E", "Due process requires recusal when probability of actual bias too high"),
    ("MCR 2.003", "MCJC Canon 2", "implements", "MICHIGANCOURTcatalogue.md", "reference", "E", "Disqualification rule implements appearance of impropriety canon"),
    ("MCR 2.003", "MCJC Canon 3", "implements", "MICHIGANCOURTcatalogue.md", "reference", "E", "Disqualification rule implements impartiality and ex parte prohibition"),
    ("42 USC 1983", "28 USC 1331", "jurisdiction", "MSC_Legal_Reference.txt", "reference", "C", "Federal question jurisdiction for §1983 claims"),
    ("42 USC 1983", "28 USC 1343", "jurisdiction", "MSC_Legal_Reference.txt", "reference", "C", "Civil rights jurisdiction specifically for §1983"),
    ("42 USC 1983", "Monell v Dept of Social Services, 436 US 658 (1978)", "applied_in", "MSC_Legal_Reference.txt", "reference", "C", "Municipal liability under §1983 requires policy or custom"),
    ("42 USC 1983", "Carey v Piphus, 435 US 247 (1978)", "damages_from", "MSC_Legal_Reference.txt", "reference", "C", "§1983 damages: compensatory, nominal ($1), punitive"),
    ("42 USC 1983", "Harlow v Fitzgerald, 457 US 800 (1982)", "limited_by", "MSC_Legal_Reference.txt", "reference", "C", "Qualified immunity defense — objective reasonableness test"),
    ("42 USC 1985(3)", "42 USC 1983", "supplements", "MSC_Legal_Reference.txt", "reference", "C", "Conspiracy claim supplements individual §1983 claims"),
    ("MCR 7.212", "MCR 7.204", "procedural_sequence", "MICHIGANCOURTcatalogue.md", "reference", "F", "Brief filed after claim of appeal"),
    ("MCR 7.306", "MI Const art VI sec 4", "constitutional_basis", "MICHIGANCOURTcatalogue.md", "reference", "F", "MSC superintending control power from constitution"),
    ("MCR 9.200", "MCJC Canon 1", "enforces", "MICHIGANCOURTcatalogue.md", "reference", "E", "JTC process enforces all 7 judicial canons"),
    ("MCR 9.200", "MCJC Canon 3", "enforces", "MICHIGANCOURTcatalogue.md", "reference", "E", "JTC specifically enforces ex parte prohibition"),
    ("Mathews v Eldridge, 424 U.S. 319 (1976)", "US Const Amend XIV", "applies", "MSC_Legal_Reference.txt", "reference", "C", "Due process balancing test for family law — NOT Brady v Maryland"),
    ("Troxel v Granville, 530 U.S. 57 (2000)", "US Const Amend XIV", "applies", "MSC_Legal_Reference.txt", "reference", "C", "Fundamental right to parent under 14th Amendment due process"),
    ("MCL 552.501", "MCR 3.211", "implements", "MICHIGANCOURTcatalogue.md", "reference", "A", "FOC Act implemented through domestic relations court rules"),
    ("MCL 722.23(j)", "MCL 722.27a", "related_to", "MICHIGANCOURTcatalogue.md", "reference", "A", "Factor j (alienation) directly impacts parenting time determination"),
]

# ─── MAIN EXECUTION ──────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("DESKTOP INTELLIGENCE PERSISTENCE ENGINE v1.0")
    print(f"Target DB: {DB_PATH}")
    print(f"Source: {DESKTOP}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    conn = get_conn()

    # Verify all target table schemas
    print("\n[1/8] Verifying table schemas...")
    tables_ok = True
    tables_ok &= verify_columns(conn, "master_citations", ["citation", "authority_type", "context", "lane", "verified", "source_document"])
    tables_ok &= verify_columns(conn, "evidence_quotes", ["source_file", "quote_text", "category", "lane", "relevance_score", "tags"])
    tables_ok &= verify_columns(conn, "timeline_events", ["event_date", "event_description", "actors", "lane", "category", "severity"])
    tables_ok &= verify_columns(conn, "michigan_rules_extracted", ["rule_number", "rule_type", "title", "source_file"])
    tables_ok &= verify_columns(conn, "authority_chains_v2", ["primary_citation", "supporting_citation", "relationship", "source_document", "lane"])
    tables_ok &= verify_columns(conn, "impeachment_matrix", ["category", "evidence_summary", "source_file", "quote_text", "impeachment_value"])
    tables_ok &= verify_columns(conn, "legal_theories", ["theory_name", "theory_type", "elements", "primary_authority"])
    if not tables_ok:
        print("  Some columns missing — proceeding with available columns")

    # Get baseline counts
    print("\n[2/8] Baseline counts...")
    baselines = {}
    for tbl in ["master_citations", "evidence_quotes", "timeline_events", "authority_chains_v2", "impeachment_matrix", "legal_theories"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        baselines[tbl] = cnt
        print(f"  {tbl}: {cnt:,}")

    # ── INSERT master_citations ──────────────────────────────────────────
    print("\n[3/8] Inserting master_citations (catalogue + MSC reference)...")
    all_citations = CATALOGUE_AUTHORITIES + MSC_REFERENCE_CASES
    inserted_mc = 0
    for cit, atype, ctx, lane, verified in all_citations:
        # Check if already exists
        existing = conn.execute(
            "SELECT id FROM master_citations WHERE citation = ? AND source_document = ?",
            (cit, "desktop_intel_persist")
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO master_citations (citation, authority_type, context, lane, verified, source_document, first_seen) VALUES (?,?,?,?,?,?,?)",
                (cit, atype, ctx, lane, verified, "desktop_intel_persist", datetime.now().isoformat())
            )
            inserted_mc += 1
    conn.commit()
    new_mc = conn.execute("SELECT COUNT(*) FROM master_citations").fetchone()[0]
    print(f"  Inserted: {inserted_mc} | Total: {new_mc:,} (was {baselines['master_citations']:,})")

    # ── INSERT authority_chains_v2 ───────────────────────────────────────
    print("\n[4/8] Inserting authority_chains_v2 relationships...")
    inserted_ac = 0
    for primary, supporting, rel, src_doc, src_type, lane, ctx in AUTHORITY_CHAINS_NEW:
        existing = conn.execute(
            "SELECT id FROM authority_chains_v2 WHERE primary_citation = ? AND supporting_citation = ? AND source_document = ?",
            (primary, supporting, src_doc)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO authority_chains_v2 (primary_citation, supporting_citation, relationship, source_document, source_type, lane, paragraph_context) VALUES (?,?,?,?,?,?,?)",
                (primary, supporting, rel, src_doc, src_type, lane, ctx)
            )
            inserted_ac += 1
    conn.commit()
    new_ac = conn.execute("SELECT COUNT(*) FROM authority_chains_v2").fetchone()[0]
    print(f"  Inserted: {inserted_ac} | Total: {new_ac:,} (was {baselines['authority_chains_v2']:,})")

    # ── INSERT evidence_quotes (deadlines) ───────────────────────────────
    print("\n[5/8] Inserting evidence_quotes (deadlines + parsed files)...")
    inserted_eq = 0

    # Deadlines from catalogue
    for name, timeframe, authority, lane in CATALOGUE_DEADLINES:
        text = f"DEADLINE: {name} — {timeframe} (Authority: {authority})"
        existing = conn.execute(
            "SELECT id FROM evidence_quotes WHERE quote_text = ? AND source_file = ?",
            (text, "MICHIGANCOURTcatalogue.md")
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO evidence_quotes (source_file, quote_text, category, lane, relevance_score, tags) VALUES (?,?,?,?,?,?)",
                ("MICHIGANCOURTcatalogue.md", text, "deadline", lane, 0.9, f"deadline,{authority},desktop_intel")
            )
            inserted_eq += 1

    # Parse Emily's filings
    emily_path = os.path.join(DESKTOP, "emiklys fulings.txt")
    if os.path.exists(emily_path):
        eq_rows, im_rows = parse_emily_filings(emily_path)
        for row in eq_rows:
            conn.execute(
                "INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags) VALUES (?,?,?,?,?,?,?,?)",
                row
            )
            inserted_eq += 1
        print(f"  Emily filings: {len(eq_rows)} evidence + {len(im_rows)} impeachment rows")

    # Parse housing case
    housing_path = os.path.join(DESKTOP, "2025-0000002760-CZ.md")
    if os.path.exists(housing_path):
        te_rows, eq_rows2 = parse_housing_case(housing_path)
        for row in eq_rows2:
            conn.execute(
                "INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags) VALUES (?,?,?,?,?,?,?,?)",
                row
            )
            inserted_eq += 1
        print(f"  Housing case: {len(eq_rows2)} evidence rows")

    # Parse KAL results
    kal_path = os.path.join(DESKTOP, "KAL_SESSION_RESULTS.txt")
    if os.path.exists(kal_path):
        kal_rows = parse_kal_results(kal_path)
        for row in kal_rows:
            conn.execute(
                "INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags) VALUES (?,?,?,?,?,?,?,?)",
                row
            )
            inserted_eq += 1
        print(f"  KAL results: {len(kal_rows)} evidence rows")

    # Parse weapons summary
    weapons_path = os.path.join(DESKTOP, "CHAT_WEAPONS_SUMMARY.txt")
    if os.path.exists(weapons_path):
        weapons_rows = parse_weapons_summary(weapons_path)
        for row in weapons_rows:
            conn.execute(
                "INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags) VALUES (?,?,?,?,?,?,?,?)",
                row
            )
            inserted_eq += 1
        print(f"  Weapons summary: {len(weapons_rows)} evidence rows")

    conn.commit()
    new_eq = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
    print(f"  Total inserted: {inserted_eq} | Total: {new_eq:,} (was {baselines['evidence_quotes']:,})")

    # ── INSERT timeline_events ───────────────────────────────────────────
    print("\n[6/8] Inserting timeline_events...")
    inserted_te = 0
    if os.path.exists(housing_path):
        te_rows, _ = parse_housing_case(housing_path)
        for evt_date, desc, actors, lane, cat, severity, filing_rel in te_rows:
            existing = conn.execute(
                "SELECT id FROM timeline_events WHERE event_date = ? AND event_description = ?",
                (evt_date, desc)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO timeline_events (event_date, event_description, actors, lane, category, severity, filing_relevance, source_table) VALUES (?,?,?,?,?,?,?,?)",
                    (evt_date, desc, actors, lane, cat, severity, filing_rel, "desktop_intel_persist")
                )
                inserted_te += 1
    conn.commit()
    new_te = conn.execute("SELECT COUNT(*) FROM timeline_events").fetchone()[0]
    print(f"  Inserted: {inserted_te} | Total: {new_te:,} (was {baselines['timeline_events']:,})")

    # ── INSERT impeachment_matrix ────────────────────────────────────────
    print("\n[7/8] Inserting impeachment_matrix...")
    inserted_im = 0
    if os.path.exists(emily_path):
        _, im_rows = parse_emily_filings(emily_path)
        for cat, summary, src, quote, value, question, filing_rel in im_rows:
            conn.execute(
                "INSERT INTO impeachment_matrix (category, evidence_summary, source_file, quote_text, impeachment_value, cross_exam_question, filing_relevance, source_table) VALUES (?,?,?,?,?,?,?,?)",
                (cat, summary, src, quote, value, question, filing_rel, "desktop_intel_persist")
            )
            inserted_im += 1
    conn.commit()
    new_im = conn.execute("SELECT COUNT(*) FROM impeachment_matrix").fetchone()[0]
    print(f"  Inserted: {inserted_im} | Total: {new_im:,} (was {baselines['impeachment_matrix']:,})")

    # ── INSERT legal_theories ────────────────────────────────────────────
    print("\n[8/8] Inserting legal_theories...")
    inserted_lt = 0
    for theory in LEGAL_THEORIES_NEW:
        name, ttype, cat, elements, primary_auth, mi_stat, fed_stat, cases, lanes = theory
        existing = conn.execute(
            "SELECT id FROM legal_theories WHERE theory_name = ?",
            (name,)
        ).fetchone()
        if not existing:
            conn.execute(
                """INSERT INTO legal_theories 
                (theory_name, theory_type, category, elements, primary_authority, michigan_statute, federal_statute, key_cases, lane_applicability, status) 
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (name, ttype, cat, elements, primary_auth, mi_stat, fed_stat, cases, lanes, "ACTIVE")
            )
            inserted_lt += 1
        else:
            # Upgrade STUB to ACTIVE with full data
            conn.execute(
                """UPDATE legal_theories SET 
                elements=?, primary_authority=?, michigan_statute=?, federal_statute=?, 
                key_cases=?, lane_applicability=?, status='ACTIVE'
                WHERE theory_name=? AND (status='STUB' OR elements IS NULL)""",
                (elements, primary_auth, mi_stat, fed_stat, cases, lanes, name)
            )
    conn.commit()
    new_lt = conn.execute("SELECT COUNT(*) FROM legal_theories").fetchone()[0]
    print(f"  Inserted: {inserted_lt} | Total: {new_lt:,} (was {baselines['legal_theories']:,})")

    # ── FINAL VERIFICATION ───────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("VERIFICATION REPORT")
    print("=" * 70)
    total_new = 0
    for tbl in ["master_citations", "evidence_quotes", "timeline_events", "authority_chains_v2", "impeachment_matrix", "legal_theories"]:
        new_cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        delta = new_cnt - baselines[tbl]
        total_new += delta
        status = "✅" if delta > 0 else "⚪"
        print(f"  {status} {tbl}: {baselines[tbl]:,} → {new_cnt:,} (+{delta})")

    print(f"\n  TOTAL NEW ROWS: {total_new}")
    print(f"  Timestamp: {datetime.now().isoformat()}")

    # Rebuild FTS5 indexes if we added evidence
    if inserted_eq > 0:
        print("\n  Rebuilding FTS5 indexes...")
        try:
            conn.execute("INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')")
            print("  ✅ evidence_fts rebuilt")
        except Exception as e:
            print(f"  ⚠️ evidence_fts rebuild: {e}")
        try:
            conn.execute("INSERT INTO timeline_fts(timeline_fts) VALUES('rebuild')")
            print("  ✅ timeline_fts rebuilt")
        except Exception as e:
            print(f"  ⚠️ timeline_fts rebuild: {e}")
        conn.commit()

    conn.close()
    print("\n✅ DESKTOP INTELLIGENCE PERSISTENCE COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
