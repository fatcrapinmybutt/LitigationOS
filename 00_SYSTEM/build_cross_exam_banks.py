"""
BUILD CROSS-EXAMINATION QUESTION BANKS
Sources: impeachment_matrix, contradiction_map, judicial_violations, evidence_quotes
Targets: Emily A. Watson, Hon. Jenny L. McNeill
Output: 04_ANALYSIS/CROSS_EXAM_BANKS/{WATSON,MCNEILL,COMBINED}_CROSS_EXAM.md
"""
import sqlite3
import os
import re
import textwrap
from datetime import date, datetime
from collections import defaultdict

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUT_DIR = r"C:\Users\andre\LitigationOS\04_ANALYSIS\CROSS_EXAM_BANKS"
os.makedirs(OUT_DIR, exist_ok=True)

SEPARATION_DAYS = (date.today() - date(2025, 7, 29)).days

def get_conn():
    conn = sqlite3.connect(DB, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.row_factory = sqlite3.Row
    return conn

def clean_text(s, maxlen=300):
    if not s:
        return ""
    s = re.sub(r'\s+', ' ', str(s)).strip()
    s = s.replace("Lincoln David Watson", "L.D.W.").replace("Lincoln", "L.D.W.")
    if len(s) > maxlen:
        s = s[:maxlen] + "..."
    return s

def short_source(path):
    if not path:
        return "DB record"
    path = str(path)
    if len(path) > 80:
        parts = path.replace("\\", "/").split("/")
        return "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
    return path

def severity_to_int(sev):
    if isinstance(sev, (int, float)):
        return int(sev)
    mapping = {"critical": 10, "high": 8, "medium": 5, "low": 3}
    return mapping.get(str(sev).lower().strip(), 5)

# ==============================================================================
# DATA EXTRACTION
# ==============================================================================
conn = get_conn()

print("Extracting Watson impeachment data...")
watson_impeachment = conn.execute("""
    SELECT id, category, evidence_summary, source_file, quote_text,
           impeachment_value, cross_exam_question, filing_relevance, event_date
    FROM impeachment_matrix
    WHERE (evidence_summary LIKE '%Watson%' OR evidence_summary LIKE '%Emily%'
           OR quote_text LIKE '%Watson%' OR quote_text LIKE '%Emily%'
           OR evidence_summary LIKE '%mother%filed%' OR evidence_summary LIKE '%mother%alleged%'
           OR category IN ('FALSE_ALLEGATIONS','PPO_WEAPONIZATION','WITHHOLDING',
                           'ALIENATION','ALIENATION_PATTERN','THIRD_PARTY_INTERFERENCE',
                           'RECANTATION_CONTRADICTION','TESTIMONY_VS_DOCUMENT',
                           'CREDIBILITY_FALSE_CLAIM','EVIDENCE_FABRICATION',
                           'Emily recanted previous claims','Emily admitted nothing physical occurred',
                           'Emily made false allegations','Parental alienation behavior',
                           'Emily withheld parenting time','Blocked phone contact',
                           'Refused visitation','Child coaching allegations',
                           'BIRTHDAY_DENIAL','HOLIDAY_ALIENATION','HOLIDAY_PATTERN',
                           'COMMUNICATION_STONEWALLING','HEALTH_PORTAL_BLOCK',
                           'IS_LINCOLN_ALIVE','Fabricated claims','Denied parental contact',
                           'ALBERT_PREMEDITATED','EX_PARTE_FRAUD'))
    ORDER BY impeachment_value DESC
    LIMIT 200
""").fetchall()
print(f"  Watson impeachment rows: {len(watson_impeachment)}")

print("Extracting Watson contradictions...")
watson_contradictions = conn.execute("""
    SELECT id, claim_id, source_a, source_b, contradiction_text, severity, lane
    FROM contradiction_map
    WHERE (contradiction_text LIKE '%Watson%' OR contradiction_text LIKE '%Emily%'
           OR contradiction_text LIKE '%mother%' OR contradiction_text LIKE '%Albert%')
      AND lane IN ('A','D','E')
    ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END
    LIMIT 100
""").fetchall()
print(f"  Watson contradiction rows: {len(watson_contradictions)}")

print("Extracting Watson evidence quotes...")
watson_evidence = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category, lane, relevance_score, filing_refs
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND (category IN ('ppo','custody','police','witness','communication')
           OR quote_text LIKE '%recant%' OR quote_text LIKE '%nothing was physical%'
           OR quote_text LIKE '%meth%' OR quote_text LIKE '%arsenic%'
           OR quote_text LIKE '%false%alleg%' OR quote_text LIKE '%suicid%'
           OR quote_text LIKE '%withhold%parent%')
      AND (quote_text LIKE '%Watson%' OR quote_text LIKE '%Emily%' OR quote_text LIKE '%mother%'
           OR quote_text LIKE '%Randall%' OR quote_text LIKE '%Albert%')
    ORDER BY relevance_score DESC
    LIMIT 150
""").fetchall()
print(f"  Watson evidence rows: {len(watson_evidence)}")

print("Extracting McNeill impeachment data...")
mcneill_impeachment = conn.execute("""
    SELECT id, category, evidence_summary, source_file, quote_text,
           impeachment_value, cross_exam_question, filing_relevance, event_date
    FROM impeachment_matrix
    WHERE (evidence_summary LIKE '%McNeill%' OR evidence_summary LIKE '%judge%'
           OR quote_text LIKE '%McNeill%' OR quote_text LIKE '%judicial%'
           OR category LIKE 'JUDICIAL_%' OR category LIKE 'MCNEILL_%'
           OR category LIKE 'FIVE_%' OR category LIKE 'EX_PARTE_%'
           OR category LIKE 'NO_HEARING%' OR category LIKE 'DENIAL_%'
           OR category LIKE 'BENCHBOOK_%'
           OR category IN ('ex_parte','ex_parte_five_orders','ex_parte_rate_anomaly',
                           'contempt_as_retaliation','denial_access_to_courts',
                           'secret_evaluation','evidence_suppression',
                           'unauthorized_practice_of_medicine','premeditation',
                           'Ex parte proceedings without notice',
                           'Judge Jenny L. McNeill','false_allegations',
                           'ex_parte_violation','selective_enforcement',
                           'HEALTHWEST_REJECTION','HEALTHWEST_EMPLOYMENT_EVAL',
                           'FOC_DOUBLE_STANDARD'))
    ORDER BY impeachment_value DESC
    LIMIT 200
""").fetchall()
print(f"  McNeill impeachment rows: {len(mcneill_impeachment)}")

print("Extracting McNeill judicial violations...")
mcneill_violations = conn.execute("""
    SELECT id, violation_type, description, date_occurred, mcr_rule, canon,
           source_file, source_quote, severity, lane
    FROM judicial_violations
    WHERE severity >= 7
    ORDER BY severity DESC
    LIMIT 100
""").fetchall()
print(f"  McNeill judicial violations: {len(mcneill_violations)}")

print("Extracting McNeill contradictions...")
mcneill_contradictions = conn.execute("""
    SELECT id, claim_id, source_a, source_b, contradiction_text, severity, lane
    FROM contradiction_map
    WHERE (contradiction_text LIKE '%McNeill%' OR contradiction_text LIKE '%judge%'
           OR contradiction_text LIKE '%ex parte%' OR contradiction_text LIKE '%contempt%'
           OR contradiction_text LIKE '%hearing%' OR contradiction_text LIKE '%HealthWest%')
      AND lane IN ('A','D','E','F')
    ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END
    LIMIT 100
""").fetchall()
print(f"  McNeill contradiction rows: {len(mcneill_contradictions)}")

print("Extracting McNeill evidence quotes...")
mcneill_evidence = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category, lane, relevance_score, filing_refs
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND category IN ('judicial','judicial_violation','due_process','benchbook','procedural')
      AND (quote_text LIKE '%McNeill%' OR quote_text LIKE '%ex parte%'
           OR quote_text LIKE '%contempt%' OR quote_text LIKE '%shut%mouth%'
           OR quote_text LIKE '%do not file%' OR quote_text LIKE '%HealthWest%'
           OR quote_text LIKE '%medication%' OR quote_text LIKE '%Five Orders%'
           OR quote_text LIKE '%Berry%' OR quote_text LIKE '%Ladas%')
    ORDER BY relevance_score DESC
    LIMIT 150
""").fetchall()
print(f"  McNeill evidence rows: {len(mcneill_evidence)}")

# Specific high-value records
print("Extracting specific high-value records...")
specific_watson = conn.execute("""
    SELECT id, category, evidence_summary, quote_text, impeachment_value, 
           cross_exam_question, filing_relevance, source_file
    FROM impeachment_matrix
    WHERE category IN ('RECANTATION_CONTRADICTION','ALBERT_PREMEDITATED',
                       'IS_LINCOLN_ALIVE','BIRTHDAY_DENIAL','HOLIDAY_ALIENATION')
    ORDER BY impeachment_value DESC
""").fetchall()
print(f"  Specific Watson high-value: {len(specific_watson)}")

specific_mcneill = conn.execute("""
    SELECT id, category, evidence_summary, quote_text, impeachment_value,
           cross_exam_question, filing_relevance, source_file
    FROM impeachment_matrix
    WHERE category IN ('MCNEILL_MEDICATION','MCNEILL_SHUT_MOUTH','FIVE_EXPARTE_ONE_DAY',
                       'ex_parte_five_orders','secret_evaluation','evidence_suppression',
                       'contempt_as_retaliation','denial_access_to_courts',
                       'unauthorized_practice_of_medicine','ex_parte_usb_listening')
    ORDER BY impeachment_value DESC
""").fetchall()
print(f"  Specific McNeill high-value: {len(specific_mcneill)}")

specific_jv = conn.execute("""
    SELECT id, violation_type, description, source_quote, severity, mcr_rule, canon, source_file
    FROM judicial_violations
    WHERE violation_type IN (
        'ex_parte_usb_listening','MCR 2.625','MCL 722.27a(9)','MCL 722.23',
        'Canon 3(B)(7)','Denial of Access to Courts','Contempt for Protected Speech',
        'Cross-Examination of Witnesses','Forced Medication Discussion',
        'Five Ex Parte Orders Pattern','Medication Conditioning',
        'Predetermined Custody Outcome','Retaliation — Contempt for Objecting',
        'Same-Day Ex Parte Signing','Two-Track Evidence System',
        'Evidence Suppression — Pages Returned','FOC Coordination Sanctioned',
        'Canon 3(A)(4)','Canon 3(B)(5)','MCR 2.003(C)(1)(b)',
        'MCR 2.119(E)','MCR 2.119(F)','MCR 2.517(A)(1)',
        'MCR 3.207(B)(1)','MCR 3.207(C)(5)','MCR 3.224(D) Timing Violation',
        'unauthorized_practice_of_medicine','structural_corruption',
        'undisclosed_conflict','denial_access_to_courts',
        'contempt_as_retaliation','secret_evaluation','judge_as_advocate',
        'stigmatizing_language','ex_parte_usb_listening'
    )
    ORDER BY severity DESC
""").fetchall()
print(f"  Specific judicial violations: {len(specific_jv)}")

conn.close()
print("All data extracted.\n")

# ==============================================================================
# QUESTION BANK CONSTRUCTION
# ==============================================================================

def build_watson_questions():
    """Build cross-examination question bank for Emily A. Watson."""
    questions = []
    seen_ids = set()
    qnum = 0

    # --- Category mapping for MRE basis ---
    mre_map = {
        "RECANTATION_CONTRADICTION": "MRE 613(b) — Prior Inconsistent Statement",
        "FALSE_ALLEGATIONS": "MRE 608(b) — Character for Truthfulness; MRE 404(b) — Pattern",
        "PPO_WEAPONIZATION": "MRE 404(b) — Pattern of Conduct; MRE 613(b) — Prior Inconsistent",
        "WITHHOLDING": "MRE 404(b) — Pattern of Conduct",
        "ALIENATION": "MRE 404(b) — Pattern of Conduct",
        "ALIENATION_PATTERN": "MRE 404(b) — Pattern of Conduct; MCL 722.23(j)",
        "THIRD_PARTY_INTERFERENCE": "MRE 404(b) — Pattern; MRE 801(d)(2) — Admission by Party-Opponent",
        "TESTIMONY_VS_DOCUMENT": "MRE 613(b) — Prior Inconsistent Statement; MRE 1006 — Summaries",
        "CREDIBILITY": "MRE 608(b) — Character for Truthfulness",
        "CREDIBILITY_FALSE_CLAIM": "MRE 608(b) — Character for Truthfulness",
        "CREDIBILITY_FORENSIC": "MRE 608(b) — Character for Truthfulness; MRE 702 — Expert Testimony",
        "PRIOR_INCONSISTENT_STATEMENT": "MRE 613(b) — Prior Inconsistent Statement",
        "TIMELINE_CONTRADICTION": "MRE 613(b) — Prior Inconsistent Statement; MRE 611(b) — Cross",
        "TIMELINE_SEQUENCE_ANOMALY": "MRE 613(b) — Prior Inconsistent Statement",
        "EVIDENCE_FABRICATION": "MRE 608(b) — Character; MRE 404(b) — Fraud Pattern",
        "FINANCIAL": "MRE 608(b) — Bias/Interest; MRE 611(b) — Cross",
        "CROSS_SPEAKER_CONTRADICTION": "MRE 613(b) — Prior Inconsistent Statement",
        "COMMUNICATION_STONEWALLING": "MRE 404(b) — Pattern of Alienation",
        "BIRTHDAY_DENIAL": "MRE 404(b) — Pattern of Alienation; MCL 722.23(j)",
        "HOLIDAY_ALIENATION": "MRE 404(b) — Pattern; MCL 722.23(j)",
        "HOLIDAY_PATTERN": "MRE 404(b) — Pattern; MCL 722.23(j)",
        "HEALTH_PORTAL_BLOCK": "MRE 404(b) — Pattern of Alienation",
        "IS_LINCOLN_ALIVE": "MRE 608(b) — Character for Truthfulness",
        "ALBERT_PREMEDITATED": "MRE 801(d)(2)(E) — Co-Conspirator Statement; MRE 404(b)",
        "EX_PARTE_FRAUD": "MRE 608(b) — Character; MRE 404(b) — Fraud Pattern",
    }
    default_mre = "MRE 611(b) — Scope of Cross-Examination"

    # --- Filing relevance mapping ---
    filing_map = {
        "FALSE_ALLEGATIONS": "Emergency Motion, Custody Mod, MSC Application, §1983 Complaint",
        "PPO_WEAPONIZATION": "PPO Termination (Lane D), MSC Application, §1983 Complaint",
        "WITHHOLDING": "Emergency Motion (Lane A), Contempt Motion, §1983 Complaint",
        "ALIENATION": "Custody Modification (Lane A), MSC Application",
        "ALIENATION_PATTERN": "Custody Modification (Lane A), MCL 722.23(j) Brief",
        "RECANTATION_CONTRADICTION": "PPO Termination, Custody Mod, MSC Application",
        "CREDIBILITY": "All filings — general credibility attack",
        "THIRD_PARTY_INTERFERENCE": "§1983 Complaint (Lane C), MSC Application",
        "TESTIMONY_VS_DOCUMENT": "COA Brief (366810), MSC Application",
        "FINANCIAL": "Custody Modification, Support Modification",
        "BIRTHDAY_DENIAL": "Emergency Motion, Contempt, MCL 722.23(j)",
        "HOLIDAY_ALIENATION": "Custody Modification, MCL 722.23(j)",
        "ALBERT_PREMEDITATED": "§1983 Conspiracy, MSC Application, Emergency Motion",
        "EX_PARTE_FRAUD": "MSC Application, §1983 Complaint, PPO Termination",
    }
    default_filing = "Custody Modification (Lane A), COA Brief (366810)"

    # --- TIER 1: Specific high-value impeachment records ---
    for r in specific_watson:
        if r['id'] in seen_ids:
            continue
        seen_ids.add(r['id'])
        qnum += 1
        cat = r['category']
        summary = clean_text(r['evidence_summary'], 400)
        quote = clean_text(r['quote_text'], 400)
        val = r['impeachment_value'] if r['impeachment_value'] else 8
        existing_q = clean_text(r['cross_exam_question'], 300)
        src = short_source(r['source_file'])
        mre = mre_map.get(cat, default_mre)
        filing = filing_map.get(cat, r['filing_relevance'] or default_filing)

        # Build question components
        if "recant" in cat.lower() or "recant" in summary.lower():
            setup = '"Nothing was physical" — Emily Watson, NSPD report, Oct 13, 2023'
            pin = '"Ms. Watson, you told police on October 13, 2023 that nothing was physical between you and Mr. Pigors, correct?"'
            confront = '"But isn\'t it true that just TWO DAYS LATER, on October 15, 2023, you filed a PPO alleging physical abuse — the very conduct you told police never happened?"'
        elif "albert" in cat.lower() or "premeditat" in summary.lower():
            setup = '"They want this documented so Emily can go tomorrow to get an Ex Parte order for full custody of her son" — Albert Watson to NSPD, NS2505044, Aug 7, 2025'
            pin = '"Your father, Albert Watson, called police on August 7, 2025, correct?"'
            confront = '"And isn\'t it true he told police that your family wanted the call documented specifically so YOU could go the next day to get an ex parte custody order — which is exactly what happened on August 8?"'
        elif "birthday" in cat.lower():
            setup = 'Father sent birthday messages to L.D.W. via court-approved AppClose platform'
            pin = '"You are aware that the court approved AppClose as a communication platform for Mr. Pigors and L.D.W., correct?"'
            confront = '"But isn\'t it true you reported Mr. Pigors\' birthday messages to his own child as contempt violations, resulting in 45 days of jail time for a father wishing his son happy birthday?"'
        elif "alive" in cat.lower():
            setup = 'Father denied all information about child\'s wellbeing for 230+ days'
            pin = f'"Ms. Watson, it has been {SEPARATION_DAYS} days since Mr. Pigors has had any contact with L.D.W., correct?"'
            confront = '"In all that time, have you provided Mr. Pigors with ANY information about his son\'s health, education, or wellbeing — even a single photograph, report card, or doctor\'s update?"'
        elif "holiday" in cat.lower():
            setup = 'Court order specifies holiday parenting time schedule'
            pin = '"You are aware of the parenting time provisions in the court order, correct?"'
            confront = '"But isn\'t it true you denied Mr. Pigors access to L.D.W. on [holiday], in direct violation of the court\'s parenting time order?"'
        else:
            setup = quote if quote else summary
            pin = existing_q if existing_q else f'"You are aware of this {cat.lower().replace("_"," ")} evidence, correct?"'
            confront = f'"But isn\'t it true that the evidence contradicts your position on {cat.lower().replace("_"," ")}?"'

        title = cat.replace("_", " ").title()
        questions.append({
            "num": qnum, "title": title, "target": "Emily A. Watson",
            "topic": cat, "value": val, "setup": setup, "source": src,
            "pin": pin, "confront": confront, "exhibit": f"Impeachment Matrix ID {r['id']}",
            "filing": filing, "mre": mre, "db_id": r['id'], "table": "impeachment_matrix"
        })

    # --- TIER 2: High-value Watson impeachment (impeachment_value >= 7) ---
    for r in watson_impeachment:
        if r['id'] in seen_ids:
            continue
        if r['impeachment_value'] and r['impeachment_value'] < 7:
            continue
        seen_ids.add(r['id'])
        qnum += 1
        cat = r['category']
        summary = clean_text(r['evidence_summary'], 400)
        quote = clean_text(r['quote_text'], 400)
        val = r['impeachment_value'] if r['impeachment_value'] else 7
        existing_q = clean_text(r['cross_exam_question'], 300)
        src = short_source(r['source_file'])
        mre = mre_map.get(cat, default_mre)
        filing = filing_map.get(cat, r['filing_relevance'] or default_filing)

        setup = quote if quote else summary
        pin = existing_q if existing_q else f'"You made this statement, correct?"'
        confront = f'"But isn\'t it true that the documentary evidence contradicts this?"'

        title = cat.replace("_", " ").title()[:60]
        questions.append({
            "num": qnum, "title": title, "target": "Emily A. Watson",
            "topic": cat, "value": val, "setup": setup, "source": src,
            "pin": pin, "confront": confront, "exhibit": f"Impeachment Matrix ID {r['id']}",
            "filing": filing, "mre": mre, "db_id": r['id'], "table": "impeachment_matrix"
        })

    # --- TIER 3: Watson contradictions (critical/high) ---
    for r in watson_contradictions:
        sev = severity_to_int(r['severity'])
        if sev < 7:
            continue
        key = f"contradiction_{r['id']}"
        if key in seen_ids:
            continue
        seen_ids.add(key)
        qnum += 1
        text = clean_text(r['contradiction_text'], 500)

        # Extract the two sides of the contradiction
        parts = text.split(" vs ")
        side_a = parts[0] if parts else text
        side_b = parts[1] if len(parts) > 1 else ""

        setup = f'"{side_a[:250]}"'
        pin = '"You made this statement, correct?"'
        confront = f'"But isn\'t it true that {side_b[:250]}?"' if side_b else '"But the documentary record shows otherwise, correct?"'

        questions.append({
            "num": qnum, "title": f"Contradiction — {r['claim_id'][:40]}",
            "target": "Emily A. Watson", "topic": "CONTRADICTION",
            "value": sev, "setup": setup, "source": f"contradiction_map ID {r['id']}",
            "pin": pin, "confront": confront,
            "exhibit": f"Source A: {r['source_a']}, Source B: {r['source_b']}",
            "filing": "COA Brief (366810), Custody Modification",
            "mre": "MRE 613(b) — Prior Inconsistent Statement",
            "db_id": r['id'], "table": "contradiction_map"
        })

    # --- TIER 4: Key evidence quotes with cross-exam potential ---
    key_patterns = [
        ("recant", "Recantation", 9, "MRE 613(b) — Prior Inconsistent Statement"),
        ("nothing was physical", "Recantation — Physical Abuse", 10, "MRE 613(b) — Prior Inconsistent Statement"),
        ("meth", "Substance Abuse Projection", 9, "MRE 608(b) — Character; MRE 404(b) — Pattern"),
        ("arsenic", "False Arsenic Allegation", 9, "MRE 608(b) — Character for Truthfulness"),
        ("suicid", "False Suicidal Allegation", 8, "MRE 608(b) — Character for Truthfulness"),
        ("withhold", "Parenting Time Withholding", 8, "MRE 404(b) — Pattern; MCL 722.23(j)"),
        ("false%alleg", "False Allegations Pattern", 8, "MRE 404(b) — Pattern; MRE 608(b)"),
        ("Randall", "Officer Randall — Meth Admission", 9, "MRE 608(b) — Character; MRE 803(8) — Public Record"),
    ]
    for r in watson_evidence:
        qt = str(r['quote_text']).lower()
        for pattern, title, base_val, mre_basis in key_patterns:
            if pattern.replace("%", "") in qt:
                eid = f"evidence_{r['id']}_{pattern}"
                if eid in seen_ids:
                    continue
                seen_ids.add(eid)
                qnum += 1
                quote = clean_text(r['quote_text'], 400)
                src = short_source(r['source_file'])
                page = r['page_number']

                questions.append({
                    "num": qnum, "title": title,
                    "target": "Emily A. Watson", "topic": title.upper().replace(" ", "_"),
                    "value": base_val, "setup": f'"{quote}"',
                    "source": f"{src}" + (f", p. {page}" if page else ""),
                    "pin": '"You are aware of this evidence, correct?"',
                    "confront": f'"Isn\'t it true this contradicts your sworn testimony?"',
                    "exhibit": f"Evidence ID {r['id']}, Category: {r['category']}",
                    "filing": "Emergency Motion, Custody Mod, COA Brief",
                    "mre": mre_basis,
                    "db_id": r['id'], "table": "evidence_quotes"
                })
                break  # One match per evidence row

    # Sort by impeachment value descending
    questions.sort(key=lambda q: q['value'], reverse=True)

    # Renumber
    for i, q in enumerate(questions, 1):
        q['num'] = i

    return questions


def build_mcneill_questions():
    """Build cross-examination question bank for Hon. Jenny L. McNeill."""
    questions = []
    seen_ids = set()
    qnum = 0

    mre_map = {
        "JUDICIAL_EX_PARTE_VIOLATION": "MCR 2.003(C)(1)(b) — Bias; Canon 3(B)(7) — Ex Parte",
        "JUDICIAL_DUE_PROCESS_VIOLATION": "US Const. Amend. XIV; MCR 2.003(C)(1)(b)",
        "JUDICIAL_PROCEDURAL_MISCONDUCT": "MCR 2.003(C)(1)(b) — Bias; Benchbook §4-§5",
        "JUDICIAL_MCJC_CANON_VIOLATION": "MCJC Canon 2, 3 — Judicial Conduct",
        "JUDICIAL_MCR_2003_DISQUALIFICATION": "MCR 2.003(C)(1) — Disqualification Grounds",
        "JUDICIAL_CREDIBILITY_FAILURE": "MCR 2.003(C)(1)(b) — Demonstrable Bias",
        "JUDICIAL_PPO_WEAPONIZATION": "MCR 3.707; MCL 600.2950 — PPO Standards",
        "JUDICIAL_BENCHBOOK_DEVIATION": "Michigan Judicial Benchbook §4.6, §5.4",
        "FIVE_EXPARTE_ONE_DAY": "MCR 3.207(B)(1); Canon 3(B)(7); US Const. Amend. XIV",
        "MCNEILL_MEDICATION": "MCL 333.16215 — Unauthorized Practice of Medicine",
        "MCNEILL_SHUT_MOUTH": "US Const. Amend. I; MCR 2.003(C)(1)(b) — Bias",
        "NO_HEARING": "MCR 2.119(E)(3); US Const. Amend. XIV — Due Process",
        "DENIAL_WITHOUT_HEARING": "MCR 2.119(E)(3); US Const. Amend. XIV",
        "EX_PARTE_COMMUNICATION": "Canon 3(B)(7); MCR 2.003(C)(1)(b)",
        "BENCHBOOK_VIOLATION": "Michigan Judicial Benchbook — Applicable Section",
    }
    default_mre = "MCR 2.003(C)(1)(b) — Bias or Prejudice"

    filing_map = {
        "JUDICIAL_EX_PARTE_VIOLATION": "JTC Complaint (Lane E), MSC Application, §1983 Complaint",
        "JUDICIAL_DUE_PROCESS_VIOLATION": "§1983 Complaint (Lane C), MSC Superintending Control",
        "JUDICIAL_PROCEDURAL_MISCONDUCT": "MCR 2.003 Disqualification, JTC Complaint",
        "JUDICIAL_MCJC_CANON_VIOLATION": "JTC Complaint (Lane E), MSC Application",
        "JUDICIAL_MCR_2003_DISQUALIFICATION": "MCR 2.003 Disqualification Motion",
        "FIVE_EXPARTE_ONE_DAY": "MSC Superintending Control, §1983 Complaint, JTC Complaint",
        "MCNEILL_MEDICATION": "§1983 Complaint, JTC Complaint, MSC Application",
        "MCNEILL_SHUT_MOUTH": "§1983 Complaint, JTC Complaint, COA Brief (366810)",
        "NO_HEARING": "COA Brief (366810), MSC Application",
    }
    default_filing = "JTC Complaint (Lane E), MCR 2.003 Disqualification"

    # --- TIER 1: Specific named judicial violations ---
    for r in specific_jv:
        key = f"jv_{r['id']}"
        if key in seen_ids:
            continue
        seen_ids.add(key)
        qnum += 1
        vtype = r['violation_type']
        desc = clean_text(r['description'], 400)
        quote = clean_text(r['source_quote'], 400)
        sev = r['severity']
        mcr = r['mcr_rule'] or ""
        canon = r['canon'] or ""
        src = short_source(r['source_file'])

        # Build specific questions by violation type
        if vtype == "ex_parte_usb_listening":
            setup = '"Yes, I had my staff listen to it" — Judge McNeill, re: USB recording submitted ex parte'
            pin = '"Your Honor, you admitted on the record that you had your staff listen to a USB recording that was submitted without notice to Mr. Pigors, correct?"'
            confront = '"And isn\'t it true that Canon 3(B)(7) prohibits a judge from considering ex parte communications, including evidence submitted without notice to all parties?"'
            title = "Ex Parte USB Listening Admission"
        elif vtype == "MCR 2.625":
            setup = '"Do not file any more, I will not look at it" — Judge McNeill to father'
            pin = '"You told Mr. Pigors not to file any more motions and that you would not look at them, correct?"'
            confront = '"Isn\'t it true that MCR 2.625 provides NO authority for a blanket filing ban, and that denying a party\'s right to petition the court violates the First Amendment and Michigan Constitution art. 1, § 3?"'
            title = "Unconstitutional Filing Ban"
        elif vtype == "MCL 722.27a(9)":
            setup = '27+ documented court order violations by Emily Watson — zero enforcement'
            pin = '"You are aware of the documented instances where Emily A. Watson violated parenting time orders, correct?"'
            confront = '"But isn\'t it true that MCL 722.27a(9) MANDATES enforcement of parenting time orders, and you failed to enforce a single one of these documented violations?"'
            title = "Failure to Enforce Parenting Time"
        elif vtype == "MCL 722.23":
            setup = 'Complete custody change ordered with ZERO written best-interest findings'
            pin = '"When you changed custody from joint to sole maternal custody, you made written findings on each of the 12 statutory best-interest factors, correct?"'
            confront = '"Isn\'t it true that you made ZERO written findings on ANY of the 12 MCL 722.23 factors, despite MCR 2.517(A)(1) requiring findings of fact in contested matters?"'
            title = "Zero Best-Interest Factor Findings"
        elif vtype == "Canon 3(B)(7)":
            setup = 'Ex parte communications: USB receipt, staff review, secret evaluation, Emily Watson communications'
            pin = '"You are aware that Canon 3(B)(7) of the Michigan Code of Judicial Conduct prohibits ex parte communications, correct?"'
            confront = '"But isn\'t it true that you received and reviewed a USB recording ex parte, had staff evaluate it without notice, and communicated with Emily Watson\'s representatives outside of formal proceedings?"'
            title = "Canon 3(B)(7) Ex Parte Violations"
        elif "Contempt for Protected Speech" in vtype:
            setup = 'Father sentenced to jail for objecting to unauthorized medication discussion'
            pin = '"You held Mr. Pigors in contempt during a hearing, correct?"'
            confront = '"Isn\'t it true that his \'contempt\' was objecting when you and Emily Watson discussed requiring prescription medication as a condition for him to see his son — a discussion neither of you was medically qualified to conduct?"'
            title = "Contempt for Protected Speech"
        elif "Forced Medication" in vtype or "Medication" in vtype:
            setup = 'Judge discussed requiring prescription medication as "the only way" father could see child'
            pin = '"During the hearing, you discussed with Emily Watson that prescription medication would be required for Mr. Pigors to see L.D.W., correct?"'
            confront = '"Isn\'t it true that conditioning a parent\'s constitutional right to see their child on medication compliance constitutes unauthorized practice of medicine under MCL 333.16215 and violates substantive due process?"'
            title = "Unauthorized Medication Conditioning"
        elif "Five Ex Parte" in vtype:
            setup = 'FIVE separate ex parte orders signed Aug 8-9, 2025 — zero notice to father'
            pin = '"On August 8 and 9, 2025, you signed five separate orders affecting Mr. Pigors\' parental rights, correct?"'
            confront = '"And isn\'t it true that Mr. Pigors received ZERO notice of any of these five orders before they were entered — completely eliminating his parenting time without any opportunity to be heard?"'
            title = "Five Ex Parte Orders — One Day"
        elif "Predetermined" in vtype:
            setup = 'Custody outcome decided before evidence was fully presented'
            pin = '"You entered a final custody order in this case, correct?"'
            confront = '"Isn\'t it true that the outcome was predetermined, given that you excluded the HealthWest evaluation showing father was fit while simultaneously accepting mother\'s unverified allegations?"'
            title = "Predetermined Custody Outcome"
        elif "Evidence Suppression" in vtype:
            setup = 'HealthWest evaluation: Father deemed fit (LOCUS 12) — excluded from record'
            pin = '"A HealthWest evaluation was completed for Mr. Pigors, correct?"'
            confront = '"And isn\'t it true that this evaluation found Mr. Pigors mentally fit with a LOCUS score of 12 — the lowest risk level — yet you excluded this favorable evidence from the record while accepting unverified allegations against him?"'
            title = "HealthWest Evaluation Suppression"
        elif "FOC Coordination" in vtype:
            setup = 'FOC operates from 990 Terrace St — same address as judge\'s spouse\'s office'
            pin = '"Your spouse, Cavan Berry, maintains an office at 990 Terrace Street in Muskegon, correct?"'
            confront = '"And isn\'t it true that the Friend of the Court — the very agency making custody recommendations in this case — operates from that same address at 990 Terrace Street?"'
            title = "FOC/Judicial Spouse Address Overlap"
        elif "Retaliation" in vtype:
            setup = 'Contempt sentence imposed after father objected to unauthorized discussion'
            pin = '"You sentenced Mr. Pigors to jail after he spoke during a hearing, correct?"'
            confront = '"Isn\'t it true that his \'offense\' was objecting when you told him to \'shut his mouth\' — and you then sentenced him for exercising his right to object to an unauthorized medication discussion?"'
            title = "Retaliatory Contempt"
        elif "Two-Track" in vtype:
            setup = 'Father\'s evidence systematically excluded while mother\'s allegations accepted at face value'
            pin = '"You considered evidence from both parties in this case, correct?"'
            confront = '"But isn\'t it true that you operated a two-track evidence system — accepting Emily Watson\'s allegations without verification while systematically excluding Mr. Pigors\' documented evidence including police reports, the HealthWest evaluation, and AppClose records?"'
            title = "Two-Track Evidence System"
        elif "Cross-Examination" in vtype:
            setup = 'Judge cross-examined witnesses herself during hearing'
            pin = '"During hearings in this case, you asked questions of witnesses, correct?"'
            confront = '"Isn\'t it true that you crossed the line from neutral arbiter to advocate by actively cross-examining witnesses — a function reserved for the parties — demonstrating the appearance of bias prohibited by Canon 2(A)?"'
            title = "Judge as Advocate — Cross-Examining Witnesses"
        elif "structural_corruption" in vtype or "undisclosed_conflict" in vtype:
            setup = 'McNeill, Hoopes, and Ladas-Hoopes were law partners at Ladas, Hoopes & McNeill'
            pin = '"Before taking the bench, you practiced law with Kenneth Hoopes and Maria Ladas-Hoopes at the firm Ladas, Hoopes & McNeill, correct?"'
            confront = '"And isn\'t it true that Judge Hoopes is now the Chief Judge who would hear any disqualification appeal, and Judge Ladas-Hoopes presides in the 60th District Court where Mr. Pigors also has matters — meaning the entire local judiciary is controlled by your former law partners?"'
            title = "Judicial Cartel — Former Law Partners"
        else:
            setup = quote if quote else desc
            pin = f'"This {vtype.replace("_"," ")} is documented in the record, correct?"'
            confront = '"But isn\'t it true this violates established judicial standards?"'
            title = vtype.replace("_", " ").title()[:60]

        mre = f"{mcr}; {canon}" if mcr and canon else (mcr or canon or default_mre)
        filing = filing_map.get(vtype, default_filing)

        questions.append({
            "num": qnum, "title": title, "target": "Hon. Jenny L. McNeill",
            "topic": vtype, "value": sev, "setup": setup,
            "source": src, "pin": pin, "confront": confront,
            "exhibit": f"Judicial Violations ID {r['id']}",
            "filing": filing, "mre": mre, "db_id": r['id'], "table": "judicial_violations"
        })

    # --- TIER 2: Specific high-value McNeill impeachment records ---
    for r in specific_mcneill:
        key = f"imp_{r['id']}"
        if key in seen_ids:
            continue
        seen_ids.add(key)
        qnum += 1
        cat = r['category']
        summary = clean_text(r['evidence_summary'], 400)
        val = r['impeachment_value'] if r['impeachment_value'] else 9
        src = short_source(r['source_file'])
        mre = mre_map.get(cat, default_mre)
        filing = filing_map.get(cat, r['filing_relevance'] or default_filing)

        setup = summary
        pin = '"This is documented in the court record, correct?"'
        confront = '"But isn\'t it true this violates the judicial standards you swore to uphold?"'

        title = cat.replace("_", " ").title()[:60]
        questions.append({
            "num": qnum, "title": title, "target": "Hon. Jenny L. McNeill",
            "topic": cat, "value": val, "setup": setup, "source": src,
            "pin": pin, "confront": confront, "exhibit": f"Impeachment Matrix ID {r['id']}",
            "filing": filing, "mre": mre, "db_id": r['id'], "table": "impeachment_matrix"
        })

    # --- TIER 3: High-value McNeill impeachment (value >= 7) ---
    for r in mcneill_impeachment:
        key = f"imp_{r['id']}"
        if key in seen_ids:
            continue
        if r['impeachment_value'] and r['impeachment_value'] < 7:
            continue
        seen_ids.add(key)
        qnum += 1
        cat = r['category']
        summary = clean_text(r['evidence_summary'], 400)
        val = r['impeachment_value'] if r['impeachment_value'] else 7
        existing_q = clean_text(r['cross_exam_question'], 300)
        src = short_source(r['source_file'])
        mre = mre_map.get(cat, default_mre)
        filing = filing_map.get(cat, r['filing_relevance'] or default_filing)

        setup = summary
        pin = existing_q if existing_q else '"This is in the record, correct?"'
        confront = '"Doesn\'t this demonstrate a pattern of bias against Mr. Pigors?"'

        title = cat.replace("_", " ").title()[:60]
        questions.append({
            "num": qnum, "title": title, "target": "Hon. Jenny L. McNeill",
            "topic": cat, "value": val, "setup": setup, "source": src,
            "pin": pin, "confront": confront, "exhibit": f"Impeachment Matrix ID {r['id']}",
            "filing": filing, "mre": mre, "db_id": r['id'], "table": "impeachment_matrix"
        })

    # --- TIER 4: High-severity judicial violations ---
    for r in mcneill_violations:
        key = f"jv_{r['id']}"
        if key in seen_ids:
            continue
        if r['severity'] < 8:
            continue
        seen_ids.add(key)
        qnum += 1
        desc = clean_text(r['description'], 400)
        quote = clean_text(r['source_quote'], 400)
        src = short_source(r['source_file'])
        mcr = r['mcr_rule'] or ""
        canon = r['canon'] or ""

        setup = quote if quote else desc
        pin = '"This is documented, correct?"'
        confront = '"Doesn\'t this violate the standards of judicial conduct?"'

        mre_basis = f"{mcr}; {canon}" if mcr and canon else (mcr or canon or default_mre)
        title = r['violation_type'].replace("_", " ").title()[:60]

        questions.append({
            "num": qnum, "title": title, "target": "Hon. Jenny L. McNeill",
            "topic": r['violation_type'], "value": r['severity'],
            "setup": setup, "source": src, "pin": pin, "confront": confront,
            "exhibit": f"Judicial Violations ID {r['id']}",
            "filing": default_filing, "mre": mre_basis,
            "db_id": r['id'], "table": "judicial_violations"
        })

    # --- TIER 5: McNeill contradictions ---
    for r in mcneill_contradictions:
        sev = severity_to_int(r['severity'])
        if sev < 7:
            continue
        key = f"mc_contradiction_{r['id']}"
        if key in seen_ids:
            continue
        seen_ids.add(key)
        qnum += 1
        text = clean_text(r['contradiction_text'], 500)
        parts = text.split(" vs ")
        side_a = parts[0] if parts else text
        side_b = parts[1] if len(parts) > 1 else ""

        questions.append({
            "num": qnum, "title": f"Court Contradiction — {r['claim_id'][:40]}",
            "target": "Hon. Jenny L. McNeill", "topic": "JUDICIAL_CONTRADICTION",
            "value": sev, "setup": f'"{side_a[:250]}"',
            "source": f"contradiction_map ID {r['id']}",
            "pin": '"This is part of the court record, correct?"',
            "confront": f'"But isn\'t it true that {side_b[:250]}?"' if side_b else '"The record contradicts this, doesn\'t it?"',
            "exhibit": f"Source A: {r['source_a']}, Source B: {r['source_b']}",
            "filing": "COA Brief (366810), MSC Application, JTC Complaint",
            "mre": "MCR 2.003(C)(1)(b) — Demonstrable Bias",
            "db_id": r['id'], "table": "contradiction_map"
        })

    # Sort by impeachment value descending
    questions.sort(key=lambda q: q['value'], reverse=True)
    for i, q in enumerate(questions, 1):
        q['num'] = i

    return questions


# ==============================================================================
# FORMAT AND WRITE OUTPUT
# ==============================================================================

def format_question(q):
    """Format a single cross-exam question in the prescribed format."""
    lines = []
    lines.append(f"## Q{q['num']:03d}: {q['title']}")
    lines.append(f"**Target:** {q['target']}")
    lines.append(f"**Topic:** {q['topic']}")
    lines.append(f"**Impeachment Value:** {q['value']}/10")
    lines.append(f"**Setup (Commit):** {q['setup']}")
    lines.append(f"**Source:** {q['source']}")
    lines.append(f"**Pin Question:** {q['pin']}")
    lines.append(f"**Confrontation:** {q['confront']}")
    lines.append(f"**Exhibit:** {q['exhibit']}")
    lines.append(f"**Filing Relevance:** {q['filing']}")
    lines.append(f"**MRE Basis:** {q['mre']}")
    lines.append(f"**DB Record:** `{q['table']}` ID {q['db_id']}")
    lines.append("")
    return "\n".join(lines)


def write_watson_bank(questions):
    path = os.path.join(OUT_DIR, "WATSON_CROSS_EXAM.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# CROSS-EXAMINATION QUESTION BANK — EMILY A. WATSON\n\n")
        f.write(f"**Case:** Pigors v. Watson, No. 2024-001507-DC\n")
        f.write(f"**Court:** 14th Circuit Court, Muskegon County\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Total Questions:** {len(questions)}\n")
        f.write(f"**Separation Days:** {SEPARATION_DAYS} (since Jul 29, 2025)\n\n")
        f.write("---\n\n")

        # Table of Contents by topic
        f.write("## TABLE OF CONTENTS\n\n")
        topics = defaultdict(list)
        for q in questions:
            topics[q['topic']].append(q)
        f.write("| Topic | Questions | Avg Value |\n")
        f.write("|-------|-----------|----------|\n")
        for topic, qs in sorted(topics.items(), key=lambda x: -max(q['value'] for q in x[1])):
            avg = sum(q['value'] for q in qs) / len(qs)
            f.write(f"| {topic} | {len(qs)} | {avg:.1f}/10 |\n")
        f.write("\n---\n\n")

        # Tactical summary
        f.write("## TACTICAL SUMMARY\n\n")
        f.write("### Cross-Examination Strategy: COMMIT → PIN → CONFRONT\n\n")
        f.write("1. **COMMIT**: Lock the witness into their prior statement\n")
        f.write("2. **PIN**: Establish the specific date, context, and medium of the statement\n")
        f.write("3. **CONFRONT**: Present the contradicting evidence with exhibit reference\n")
        f.write("4. **EXHIBIT**: Mark and move to admit the contradicting document\n\n")
        f.write("### Key Impeachment Themes\n\n")
        f.write("- **Recantation Pattern**: Told police \"nothing was physical\" Oct 13, 2023 → Filed PPO alleging physical abuse Oct 15, 2023\n")
        f.write("- **False Allegations Escalation**: Suicidal → Arsenic → Assault → Drugs → Threats (all disproven)\n")
        f.write(f"- **Parenting Time Withholding**: {SEPARATION_DAYS} days since last contact with L.D.W.\n")
        f.write("- **Premeditated Ex Parte**: Albert Watson admitted to police the custody grab was planned (NS2505044)\n")
        f.write("- **Substance Abuse Projection**: Officer Randall documented Emily's meth use admission\n\n")
        f.write("---\n\n")

        # Questions grouped by value tier
        f.write("## CRITICAL QUESTIONS (Value 9-10)\n\n")
        for q in questions:
            if q['value'] >= 9:
                f.write(format_question(q))

        f.write("## HIGH-VALUE QUESTIONS (Value 7-8)\n\n")
        for q in questions:
            if 7 <= q['value'] <= 8:
                f.write(format_question(q))

        f.write("## SUPPORTING QUESTIONS (Value 5-6)\n\n")
        for q in questions:
            if q['value'] < 7:
                f.write(format_question(q))

    print(f"  Wrote {path} ({len(questions)} questions)")
    return path


def write_mcneill_bank(questions):
    path = os.path.join(OUT_DIR, "MCNEILL_CROSS_EXAM.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# CROSS-EXAMINATION QUESTION BANK — HON. JENNY L. McNEILL\n\n")
        f.write(f"**Case:** Pigors v. Watson, No. 2024-001507-DC\n")
        f.write(f"**Court:** 14th Circuit Court, Muskegon County\n")
        f.write(f"**Use:** JTC Complaint (Lane E), MCR 2.003 Disqualification, MSC Application, §1983 Complaint, COA Brief (366810)\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Total Questions:** {len(questions)}\n")
        f.write(f"**Separation Days:** {SEPARATION_DAYS} (since Jul 29, 2025)\n\n")
        f.write("⚠️ **NOTE**: These questions are framed for JTC proceedings, MSC applications, §1983 depositions,\n")
        f.write("and appellate briefing. A sitting judge cannot be directly cross-examined in their own court.\n")
        f.write("Use these as: (1) JTC complaint exhibits, (2) MSC factual assertions, (3) §1983 deposition questions,\n")
        f.write("(4) COA brief argument points, (5) MCR 2.003 affidavit support.\n\n")
        f.write("---\n\n")

        # Table of Contents
        f.write("## TABLE OF CONTENTS\n\n")
        topics = defaultdict(list)
        for q in questions:
            topics[q['topic']].append(q)
        f.write("| Topic | Questions | Avg Value |\n")
        f.write("|-------|-----------|----------|\n")
        for topic, qs in sorted(topics.items(), key=lambda x: -max(q['value'] for q in x[1])):
            avg = sum(q['value'] for q in qs) / len(qs)
            f.write(f"| {topic} | {len(qs)} | {avg:.1f}/10 |\n")
        f.write("\n---\n\n")

        # Tactical summary
        f.write("## TACTICAL SUMMARY\n\n")
        f.write("### Judicial Misconduct Pattern Categories\n\n")
        f.write("1. **Ex Parte Violations (3,697 documented)**: Orders entered without notice or hearing\n")
        f.write("2. **Five Orders Day (Aug 8-9, 2025)**: FIVE ex parte orders, zero notice, complete parenting time elimination\n")
        f.write("3. **Contempt Abuse (59 days jail)**: Birthday messages = contempt; objecting = contempt\n")
        f.write("4. **Filing Ban**: \"Do not file anymore, I will not look at it\" — denial of access to courts\n")
        f.write("5. **Medication Coercion**: Discussed Rx as \"the only way\" father could see son\n")
        f.write("6. **Evidence Suppression**: HealthWest eval (LOCUS 12, fit parent) excluded from record\n")
        f.write("7. **Structural Conflicts**: Spouse (Cavan Berry) at same address as FOC; former partners are Chief Judge and District Judge\n")
        f.write("8. **Two-Track Evidence**: Mother's allegations accepted at face value; father's evidence excluded\n\n")
        f.write("### Three-Court Judicial Cartel\n\n")
        f.write("- **Hon. Jenny L. McNeill** — 14th Circuit (custody/PPO judge)\n")
        f.write("- **Hon. Kenneth Hoopes** — 14th Circuit Chief Judge (McNeill's former law partner)\n")
        f.write("- **Hon. Maria Ladas-Hoopes** — 60th District (Hoopes' wife, McNeill's former partner)\n")
        f.write("- All three: former partners at **Ladas, Hoopes & McNeill**, 435 Whitehall Rd\n\n")
        f.write("---\n\n")

        # Questions grouped by value tier
        f.write("## CRITICAL QUESTIONS (Value 9-10)\n\n")
        for q in questions:
            if q['value'] >= 9:
                f.write(format_question(q))

        f.write("## HIGH-VALUE QUESTIONS (Value 7-8)\n\n")
        for q in questions:
            if 7 <= q['value'] <= 8:
                f.write(format_question(q))

        f.write("## SUPPORTING QUESTIONS (Value 5-6)\n\n")
        for q in questions:
            if q['value'] < 7:
                f.write(format_question(q))

    print(f"  Wrote {path} ({len(questions)} questions)")
    return path


def write_combined_index(watson_qs, mcneill_qs):
    path = os.path.join(OUT_DIR, "COMBINED_QUESTION_INDEX.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# COMBINED CROSS-EXAMINATION QUESTION INDEX\n\n")
        f.write(f"**Case:** Pigors v. Watson, No. 2024-001507-DC\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Watson Questions:** {len(watson_qs)}\n")
        f.write(f"**McNeill Questions:** {len(mcneill_qs)}\n")
        f.write(f"**Total Questions:** {len(watson_qs) + len(mcneill_qs)}\n")
        f.write(f"**Separation Days:** {SEPARATION_DAYS} (since Jul 29, 2025)\n\n")
        f.write("---\n\n")

        # Summary statistics
        f.write("## SUMMARY STATISTICS\n\n")

        f.write("### Emily A. Watson\n\n")
        f.write("| Metric | Count |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total questions | {len(watson_qs)} |\n")
        w_crit = sum(1 for q in watson_qs if q['value'] >= 9)
        w_high = sum(1 for q in watson_qs if 7 <= q['value'] <= 8)
        w_avg = sum(q['value'] for q in watson_qs) / max(len(watson_qs), 1)
        f.write(f"| Critical (9-10) | {w_crit} |\n")
        f.write(f"| High (7-8) | {w_high} |\n")
        f.write(f"| Average value | {w_avg:.1f}/10 |\n")
        w_topics = len(set(q['topic'] for q in watson_qs))
        f.write(f"| Unique topics | {w_topics} |\n\n")

        f.write("### Hon. Jenny L. McNeill\n\n")
        f.write("| Metric | Count |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total questions | {len(mcneill_qs)} |\n")
        m_crit = sum(1 for q in mcneill_qs if q['value'] >= 9)
        m_high = sum(1 for q in mcneill_qs if 7 <= q['value'] <= 8)
        m_avg = sum(q['value'] for q in mcneill_qs) / max(len(mcneill_qs), 1)
        f.write(f"| Critical (9-10) | {m_crit} |\n")
        f.write(f"| High (7-8) | {m_high} |\n")
        f.write(f"| Average value | {m_avg:.1f}/10 |\n")
        m_topics = len(set(q['topic'] for q in mcneill_qs))
        f.write(f"| Unique topics | {m_topics} |\n\n")

        f.write("---\n\n")

        # Data sources
        f.write("## DATA SOURCES\n\n")
        f.write("| Table | Description | Records Queried |\n")
        f.write("|-------|-------------|----------------|\n")
        w_imp = sum(1 for q in watson_qs if q['table'] == 'impeachment_matrix')
        w_con = sum(1 for q in watson_qs if q['table'] == 'contradiction_map')
        w_ev = sum(1 for q in watson_qs if q['table'] == 'evidence_quotes')
        m_imp = sum(1 for q in mcneill_qs if q['table'] == 'impeachment_matrix')
        m_jv = sum(1 for q in mcneill_qs if q['table'] == 'judicial_violations')
        m_con = sum(1 for q in mcneill_qs if q['table'] == 'contradiction_map')
        f.write(f"| `impeachment_matrix` (5,229 rows) | Impeachment ammunition | Watson: {w_imp}, McNeill: {m_imp} |\n")
        f.write(f"| `contradiction_map` (2,534 rows) | Documented contradictions | Watson: {w_con}, McNeill: {m_con} |\n")
        f.write(f"| `judicial_violations` (1,956 rows) | Judicial misconduct | McNeill: {m_jv} |\n")
        f.write(f"| `evidence_quotes` (175,223 rows) | Evidence with verbatim quotes | Watson: {w_ev} |\n\n")

        f.write("---\n\n")

        # Filing cross-reference
        f.write("## FILING CROSS-REFERENCE\n\n")
        f.write("### Questions by Filing Target\n\n")
        filing_counts = defaultdict(lambda: {"watson": 0, "mcneill": 0})
        for q in watson_qs:
            for f_ref in q['filing'].split(","):
                f_ref = f_ref.strip()
                if f_ref:
                    filing_counts[f_ref]["watson"] += 1
        for q in mcneill_qs:
            for f_ref in q['filing'].split(","):
                f_ref = f_ref.strip()
                if f_ref:
                    filing_counts[f_ref]["mcneill"] += 1

        f.write("| Filing | Watson Qs | McNeill Qs | Total |\n")
        f.write("|--------|-----------|------------|-------|\n")
        for filing, counts in sorted(filing_counts.items(), key=lambda x: -(x[1]["watson"] + x[1]["mcneill"])):
            total = counts["watson"] + counts["mcneill"]
            f.write(f"| {filing} | {counts['watson']} | {counts['mcneill']} | {total} |\n")
        f.write("\n---\n\n")

        # MRE cross-reference
        f.write("## MRE CROSS-REFERENCE\n\n")
        mre_counts = defaultdict(int)
        for q in watson_qs + mcneill_qs:
            mre_counts[q['mre']] += 1
        f.write("| MRE Basis | Question Count |\n")
        f.write("|-----------|---------------|\n")
        for mre, cnt in sorted(mre_counts.items(), key=lambda x: -x[1]):
            f.write(f"| {mre} | {cnt} |\n")
        f.write("\n---\n\n")

        # Master question index (compact)
        f.write("## MASTER QUESTION INDEX\n\n")
        f.write("### Watson Questions\n\n")
        f.write("| # | Title | Value | Topic | Table |\n")
        f.write("|---|-------|-------|-------|-------|\n")
        for q in watson_qs:
            f.write(f"| W-{q['num']:03d} | {q['title'][:50]} | {q['value']}/10 | {q['topic'][:30]} | {q['table']} |\n")

        f.write(f"\n### McNeill Questions\n\n")
        f.write("| # | Title | Value | Topic | Table |\n")
        f.write("|---|-------|-------|-------|-------|\n")
        for q in mcneill_qs:
            f.write(f"| M-{q['num']:03d} | {q['title'][:50]} | {q['value']}/10 | {q['topic'][:30]} | {q['table']} |\n")

        f.write(f"\n---\n\n")
        f.write(f"*Generated by LitigationOS Cross-Examination Engine*\n")
        f.write(f"*All questions traceable to litigation_context.db records*\n")
        f.write(f"*Child referenced as L.D.W. per MCR 8.119(H)*\n")

    print(f"  Wrote {path}")
    return path


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
print("Building Watson question bank...")
watson_questions = build_watson_questions()
print(f"  Watson questions built: {len(watson_questions)}")

print("Building McNeill question bank...")
mcneill_questions = build_mcneill_questions()
print(f"  McNeill questions built: {len(mcneill_questions)}")

print("\nWriting output files...")
watson_path = write_watson_bank(watson_questions)
mcneill_path = write_mcneill_bank(mcneill_questions)
combined_path = write_combined_index(watson_questions, mcneill_questions)

print(f"\n{'=' * 80}")
print(f"CROSS-EXAMINATION BANKS COMPLETE")
print(f"{'=' * 80}")
print(f"Watson questions:  {len(watson_questions)}")
print(f"McNeill questions: {len(mcneill_questions)}")
print(f"Total questions:   {len(watson_questions) + len(mcneill_questions)}")
print(f"\nOutput files:")
print(f"  {watson_path}")
print(f"  {mcneill_path}")
print(f"  {combined_path}")
print(f"\nSeparation days: {SEPARATION_DAYS}")
