#!/usr/bin/env python3
"""
FRAUD UPON THE COURT / FRUIT OF THE POISONOUS TREE — Evidence Compilation v2
Fixed column names from schema discovery. Queries targeted specialty tables.
"""

import sys
import os
import sqlite3
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUTPUT_PATH = r"C:\Users\andre\LitigationOS\temp\FRAUD_EVIDENCE_COMPILATION.md"

PRAGMAS = """
PRAGMA busy_timeout=60000;
PRAGMA journal_mode=WAL;
PRAGMA cache_size=-32000;
PRAGMA temp_store=MEMORY;
PRAGMA synchronous=NORMAL;
"""

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(PRAGMAS)
    return conn

def safe_query(conn, label, sql, params=None):
    try:
        rows = conn.execute(sql, params or ()).fetchall()
        result = [dict(r) for r in rows]
        print(f"  [{label}] => {len(result)} rows")
        return result
    except Exception as e:
        print(f"  [{label}] ERROR: {e}")
        return []

def truncate(val, max_len=300):
    if val is None:
        return ""
    s = str(val)
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s

def format_items(rows, columns=None, max_items=50):
    if not rows:
        return "*No results found.*\n"
    if columns is None:
        columns = list(rows[0].keys())
    lines = []
    for i, row in enumerate(rows[:max_items], 1):
        lines.append(f"### Item {i}")
        for col in columns:
            val = row.get(col, "")
            lines.append(f"- **{col}**: {truncate(val)}")
        lines.append("")
    if len(rows) > max_items:
        lines.append(f"*... and {len(rows) - max_items} more results.*\n")
    return "\n".join(lines)

def format_table(rows, columns=None, max_rows=30):
    if not rows:
        return "*No results found.*\n"
    if columns is None:
        columns = list(rows[0].keys())
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, sep]
    for row in rows[:max_rows]:
        vals = [truncate(row.get(c, ""), 100).replace("|", "/").replace("\n", " ") for c in columns]
        lines.append("| " + " | ".join(vals) + " |")
    if len(rows) > max_rows:
        lines.append(f"\n*... {len(rows) - max_rows} more rows omitted.*")
    return "\n".join(lines)


def main():
    print(f"=== FRAUD EVIDENCE COMPILATION v2 ===")
    print(f"DB: {DB_PATH} ({os.path.getsize(DB_PATH) / (1024**3):.1f} GB)")
    print(f"Time: {datetime.now().isoformat()}\n")

    conn = get_connection()
    summary = {}
    sections = []

    # =================================================================
    # evidence_quotes correct columns:
    #   id, document_id, page_number, evidence_category, quote_text,
    #   quote_hash, quote_type, speaker, date_ref, legal_significance,
    #   created_at, source_type
    # =================================================================

    # === 1. FRAUD / PERJURY EVIDENCE ===
    print("=== 1. FRAUD / PERJURY EVIDENCE ===")
    
    # 1a. evidence_quotes — fraud keywords
    q1a = safe_query(conn, "eq_fraud",
        """SELECT quote_text, document_id, evidence_category, speaker, legal_significance
           FROM evidence_quotes 
           WHERE (quote_text LIKE '%perjur%' OR quote_text LIKE '%false%' 
                  OR quote_text LIKE '%fabricat%' OR quote_text LIKE '%lied%' 
                  OR quote_text LIKE '%lying%' OR quote_text LIKE '%fraud%'
                  OR quote_text LIKE '%misrepresent%' OR quote_text LIKE '%decei%')
           AND (quote_text LIKE '%Emily%' OR quote_text LIKE '%Watson%' 
                OR quote_text LIKE '%Berry%' OR quote_text LIKE '%Barnes%')
           LIMIT 50""")
    
    # 1b. watson_perjury_compilation — dedicated perjury table!
    q1b_cols = safe_query(conn, "perjury_schema", "PRAGMA table_info(watson_perjury_compilation)")
    perjury_col_names = [r['name'] for r in q1b_cols]
    print(f"  watson_perjury_compilation columns: {perjury_col_names}")
    
    q1b = safe_query(conn, "watson_perjury",
        "SELECT * FROM watson_perjury_compilation LIMIT 50")
    
    # 1c. contradiction_timeline
    q1c_cols = safe_query(conn, "contradict_schema", "PRAGMA table_info(contradiction_timeline)")
    print(f"  contradiction_timeline columns: {[r['name'] for r in q1c_cols]}")
    
    q1c = safe_query(conn, "contradictions",
        "SELECT * FROM contradiction_timeline LIMIT 30")
    
    summary["1a_EQ_Fraud_Perjury"] = len(q1a)
    summary["1b_Watson_Perjury_Compilation"] = len(q1b)
    summary["1c_Contradiction_Timeline"] = len(q1c)
    
    sect1 = "## 1. FRAUD / PERJURY EVIDENCE\n\n"
    sect1 += ("Evidence of false statements, perjury, fabrication, and fraud by Emily Watson, "
              "Ronald Berry, and Jennifer Barnes.\n\n"
              "**Filing Relevance:** F3 (court relied on fraud), F4 (§1983 — rights deprived through fraud), "
              "F5 (MSC — systemic fraud requires bypass)\n\n")
    
    body1 = ""
    if q1a:
        body1 += "### 1a. Evidence Quotes — Fraud/Perjury Keywords\n\n"
        body1 += format_items(q1a) + "\n"
    if q1b:
        body1 += "### 1b. Watson Perjury Compilation (Dedicated Table)\n\n"
        body1 += format_items(q1b) + "\n"
    if q1c:
        body1 += "### 1c. Contradiction Timeline\n\n"
        body1 += format_items(q1c) + "\n"
    if not body1:
        body1 = "*No fraud/perjury evidence found.*\n"
    sections.append((sect1, body1))

    # === 2. CONSPIRACY TIMELINE ===
    print("\n=== 2. CONSPIRACY TIMELINE ===")
    
    # 2a. conspiracy_timeline (dedicated table)
    q2a_cols = safe_query(conn, "ct_schema", "PRAGMA table_info(conspiracy_timeline)")
    ct_col_names = [r['name'] for r in q2a_cols]
    print(f"  conspiracy_timeline columns: {ct_col_names}")
    
    q2a = safe_query(conn, "conspiracy_tl",
        "SELECT * FROM conspiracy_timeline ORDER BY rowid LIMIT 40")
    
    # 2b. watson_family_conspiracy (dedicated table!)
    q2b_cols = safe_query(conn, "wfc_schema", "PRAGMA table_info(watson_family_conspiracy)")
    wfc_col_names = [r['name'] for r in q2b_cols]
    print(f"  watson_family_conspiracy columns: {wfc_col_names}")
    
    q2b = safe_query(conn, "watson_family_conspiracy",
        "SELECT * FROM watson_family_conspiracy LIMIT 40")
    
    # 2c. evidence_quotes — conspiracy keywords
    q2c = safe_query(conn, "eq_conspiracy",
        """SELECT quote_text, document_id, evidence_category, speaker, legal_significance
           FROM evidence_quotes 
           WHERE (quote_text LIKE '%conspir%' OR quote_text LIKE '%collud%' 
                  OR quote_text LIKE '%scheme%')
           LIMIT 30""")
    
    summary["2a_Conspiracy_Timeline"] = len(q2a)
    summary["2b_Watson_Family_Conspiracy"] = len(q2b)
    summary["2c_EQ_Conspiracy"] = len(q2c)
    
    sect2 = "## 2. CONSPIRACY TIMELINE\n\n"
    sect2 += ("Coordinated actions among Emily Watson, Ronald Berry, Jennifer Barnes, "
              "and Watson family (Albert Watson, Cody Watson, Lori Watson).\n\n"
              "**Filing Relevance:** F4 (§1983 conspiracy), F5 (MSC pattern of fraud)\n\n")
    
    body2 = ""
    if q2a:
        body2 += "### 2a. Conspiracy Timeline (Dedicated Table)\n\n"
        body2 += format_items(q2a) + "\n"
    if q2b:
        body2 += "### 2b. Watson Family Conspiracy (Dedicated Table)\n\n"
        body2 += format_items(q2b) + "\n"
    if q2c:
        body2 += "### 2c. Evidence Quotes — Conspiracy Keywords\n\n"
        body2 += format_items(q2c) + "\n"
    if not body2:
        body2 = "*No conspiracy evidence found.*\n"
    sections.append((sect2, body2))

    # === 3. JUDICIAL VIOLATIONS (McNeill) ===
    print("\n=== 3. JUDICIAL VIOLATIONS ===")
    
    # 3a. judicial_violations — CRITICAL severity
    q3a = safe_query(conn, "jv_critical",
        """SELECT violation_id, judge_name, canon_number, canon_text, 
                  violation_description, evidence_refs, severity, jtc_exhibit_id
           FROM judicial_violations 
           WHERE severity = 'CRITICAL' OR severity = 'critical' OR severity = 'HIGH'
           LIMIT 30""")
    
    jv_total = safe_query(conn, "jv_count", "SELECT COUNT(*) as c FROM judicial_violations")
    total_jv = jv_total[0]['c'] if jv_total else 0
    
    # 3b. judicial_dossier
    q3b_cols = safe_query(conn, "jd_schema", "PRAGMA table_info(judicial_dossier)")
    print(f"  judicial_dossier columns: {[r['name'] for r in q3b_cols]}")
    
    q3b = safe_query(conn, "judicial_dossier",
        "SELECT * FROM judicial_dossier LIMIT 30")
    
    # 3c. judicial_conflicts
    q3c_cols = safe_query(conn, "jc_schema", "PRAGMA table_info(judicial_conflicts)")
    print(f"  judicial_conflicts columns: {[r['name'] for r in q3c_cols]}")
    
    q3c = safe_query(conn, "judicial_conflicts",
        "SELECT * FROM judicial_conflicts LIMIT 20")
    
    # 3d. judicial_canons_matrix
    q3d = safe_query(conn, "canons_matrix",
        "SELECT * FROM judicial_canons_matrix LIMIT 20")
    
    # 3e. constitutional_violations
    q3e_cols = safe_query(conn, "cv_schema", "PRAGMA table_info(constitutional_violations)")
    print(f"  constitutional_violations columns: {[r['name'] for r in q3e_cols]}")
    
    q3e = safe_query(conn, "constitutional",
        "SELECT * FROM constitutional_violations LIMIT 20")
    
    summary["3a_JV_Critical"] = len(q3a)
    summary["3b_Judicial_Dossier"] = len(q3b)
    summary["3c_Judicial_Conflicts"] = len(q3c)
    summary["3d_Canons_Matrix"] = len(q3d)
    summary["3e_Constitutional"] = len(q3e)
    
    sect3 = f"## 3. JUDICIAL VIOLATIONS — Hon. Jenny L. McNeill\n\n"
    sect3 += f"Total violations in DB: **{total_jv}**\n\n"
    sect3 += ("**Filing Relevance:** F3 (MCR 2.003 disqualification), "
              "F5 (MSC superintending control)\n\n")
    
    body3 = ""
    if q3a:
        body3 += "### 3a. Critical/High Severity Violations\n\n"
        body3 += format_items(q3a) + "\n"
    if q3b:
        body3 += "### 3b. Judicial Dossier\n\n"
        body3 += format_items(q3b) + "\n"
    if q3c:
        body3 += "### 3c. Judicial Conflicts of Interest\n\n"
        body3 += format_items(q3c) + "\n"
    if q3d:
        body3 += "### 3d. Judicial Canons Matrix\n\n"
        body3 += format_items(q3d) + "\n"
    if q3e:
        body3 += "### 3e. Constitutional Violations\n\n"
        body3 += format_items(q3e) + "\n"
    sections.append((sect3, body3))

    # === 4. PPO FOUNDATION FRAUD ===
    print("\n=== 4. PPO FOUNDATION FRAUD ===")
    
    # 4a. evidence_quotes — PPO + fraud
    q4a = safe_query(conn, "eq_ppo_fraud",
        """SELECT quote_text, document_id, evidence_category, speaker, legal_significance
           FROM evidence_quotes 
           WHERE (quote_text LIKE '%PPO%' OR quote_text LIKE '%protection order%'
                  OR quote_text LIKE '%personal protection%')
           AND (quote_text LIKE '%false%' OR quote_text LIKE '%fabricat%' 
                OR quote_text LIKE '%straw%' OR quote_text LIKE '%stalk%'
                OR quote_text LIKE '%fraud%' OR quote_text LIKE '%perjur%')
           LIMIT 30""")
    
    # 4b. ppo_timeline_complete
    q4b_cols = safe_query(conn, "ppo_tl_schema", "PRAGMA table_info(ppo_timeline_complete)")
    print(f"  ppo_timeline_complete columns: {[r['name'] for r in q4b_cols]}")
    
    q4b = safe_query(conn, "ppo_timeline",
        "SELECT * FROM ppo_timeline_complete ORDER BY rowid LIMIT 30")
    
    # 4c. ppo_violations
    q4c_cols = safe_query(conn, "ppo_v_schema", "PRAGMA table_info(ppo_violations)")
    print(f"  ppo_violations columns: {[r['name'] for r in q4c_cols]}")
    
    q4c = safe_query(conn, "ppo_violations",
        "SELECT * FROM ppo_violations LIMIT 30")
    
    summary["4a_EQ_PPO_Fraud"] = len(q4a)
    summary["4b_PPO_Timeline"] = len(q4b)
    summary["4c_PPO_Violations"] = len(q4c)
    
    sect4 = "## 4. PPO FOUNDATION FRAUD — Fruit of the Poisonous Tree\n\n"
    sect4 += ("The initial PPO was obtained through false claims. ALL subsequent orders, "
              "custody changes, and restrictions flowing from that PPO are tainted fruit.\n\n"
              "**Filing Relevance:** F3 (court perpetuated fraud), F4 (§1983 rights violated "
              "through fraudulent PPO), F5 (MSC — entire proceeding tainted from root)\n\n")
    
    body4 = ""
    if q4a:
        body4 += "### 4a. Evidence Quotes — PPO Fraud\n\n"
        body4 += format_items(q4a) + "\n"
    if q4b:
        body4 += "### 4b. PPO Timeline (Complete)\n\n"
        body4 += format_items(q4b) + "\n"
    if q4c:
        body4 += "### 4c. PPO Violations\n\n"
        body4 += format_items(q4c) + "\n"
    if not body4:
        body4 = "*No PPO fraud evidence found.*\n"
    sections.append((sect4, body4))

    # === 5. EX-PARTE ORDER VIOLATIONS ===
    print("\n=== 5. EX-PARTE ORDER VIOLATIONS ===")
    
    q5a = safe_query(conn, "eq_exparte",
        """SELECT quote_text, document_id, evidence_category, speaker, legal_significance
           FROM evidence_quotes 
           WHERE (quote_text LIKE '%August 8%' OR quote_text LIKE '%August 2025%'
                  OR quote_text LIKE '%722.27a%' OR quote_text LIKE '%ex parte%'
                  OR quote_text LIKE '%ex-parte%' OR quote_text LIKE '%without notice%'
                  OR quote_text LIKE '%without hearing%')
           LIMIT 30""")
    
    # 5b. docket_events — August 2025
    q5b = safe_query(conn, "docket_aug2025",
        """SELECT event_id, case_id, event_date_iso, title, event_type, summary, truth_tag
           FROM docket_events 
           WHERE event_date_iso LIKE '2025-08%'
           LIMIT 20""")
    
    # 5c. docket_events — ex parte
    q5c = safe_query(conn, "docket_exparte",
        """SELECT event_id, case_id, event_date_iso, title, event_type, summary
           FROM docket_events 
           WHERE summary LIKE '%ex parte%' OR title LIKE '%ex parte%'
                 OR summary LIKE '%without notice%' OR summary LIKE '%722.27a%'
           LIMIT 20""")
    
    summary["5a_EQ_ExParte"] = len(q5a)
    summary["5b_Docket_Aug2025"] = len(q5b)
    summary["5c_Docket_ExParte"] = len(q5c)
    
    sect5 = "## 5. EX-PARTE ORDER VIOLATIONS — MCL 722.27a(3)\n\n"
    sect5 += ("The August 8, 2025 order modified custody/parenting time without the notice "
              "and hearing required by MCL 722.27a(3).\n\n"
              "**Filing Relevance:** F3 (judge violated statutory requirements), "
              "F4 (§1983 due process deprivation), F5 (MSC statutory violation)\n\n")
    
    body5 = ""
    if q5a:
        body5 += "### 5a. Evidence Quotes — Ex-Parte\n\n"
        body5 += format_items(q5a) + "\n"
    if q5b:
        body5 += "### 5b. Docket Events — August 2025\n\n"
        body5 += format_items(q5b) + "\n"
    if q5c:
        body5 += "### 5c. Docket Events — Ex-Parte References\n\n"
        body5 += format_items(q5c) + "\n"
    if not body5:
        body5 = "*No ex-parte evidence found.*\n"
    sections.append((sect5, body5))

    # === 6. BERRY/BARNES CONSPIRACY ===
    print("\n=== 6. BERRY/BARNES CONSPIRACY ===")
    
    # 6a. berry_ethics_violations (dedicated table!)
    q6a_cols = safe_query(conn, "bev_schema", "PRAGMA table_info(berry_ethics_violations)")
    print(f"  berry_ethics_violations columns: {[r['name'] for r in q6a_cols]}")
    
    q6a = safe_query(conn, "berry_ethics",
        "SELECT * FROM berry_ethics_violations LIMIT 30")
    
    # 6b. evidence_quotes — Berry/Barnes coordination
    q6b = safe_query(conn, "eq_berry_barnes",
        """SELECT quote_text, document_id, evidence_category, speaker, legal_significance
           FROM evidence_quotes 
           WHERE (quote_text LIKE '%Berry%' OR quote_text LIKE '%Barnes%')
           AND (quote_text LIKE '%conspir%' OR quote_text LIKE '%coordinat%' 
                OR quote_text LIKE '%plan%' OR quote_text LIKE '%together%'
                OR quote_text LIKE '%direct%' OR quote_text LIKE '%instruct%'
                OR quote_text LIKE '%told%' OR quote_text LIKE '%advis%')
           LIMIT 30""")
    
    # 6c. evidence_quotes — Ronald Berry specifically
    q6c = safe_query(conn, "eq_berry",
        """SELECT quote_text, document_id, evidence_category, speaker, legal_significance
           FROM evidence_quotes 
           WHERE quote_text LIKE '%Ronald%Berry%' OR quote_text LIKE '%Ron Berry%'
                 OR speaker LIKE '%Berry%'
           LIMIT 20""")
    
    # 6d. actor_violations for Berry/Barnes
    q6d_cols = safe_query(conn, "av_schema", "PRAGMA table_info(actor_violations)")
    print(f"  actor_violations columns: {[r['name'] for r in q6d_cols]}")
    
    # Find actor column name
    av_cols = [r['name'] for r in q6d_cols]
    actor_col = None
    for c in av_cols:
        if 'actor' in c.lower() or 'name' in c.lower() or 'person' in c.lower():
            actor_col = c
            break
    
    q6d = []
    if actor_col:
        q6d = safe_query(conn, "av_berry_barnes",
            f"""SELECT * FROM actor_violations 
                WHERE [{actor_col}] LIKE '%Berry%' OR [{actor_col}] LIKE '%Barnes%'
                LIMIT 20""")
    else:
        q6d = safe_query(conn, "av_all", "SELECT * FROM actor_violations LIMIT 10")
    
    summary["6a_Berry_Ethics"] = len(q6a)
    summary["6b_EQ_Berry_Barnes"] = len(q6b)
    summary["6c_EQ_Berry"] = len(q6c)
    summary["6d_Actor_Violations"] = len(q6d)
    
    sect6 = "## 6. BERRY/BARNES CONSPIRACY\n\n"
    sect6 += ("Ronald Berry (non-attorney domestic partner) and Jennifer Barnes (P55406, withdrew) "
              "coordinated to manipulate proceedings against Andrew Pigors.\n\n"
              "**Filing Relevance:** F4 (§1983 conspiracy under color of state law), "
              "F5 (MSC officers of the court participated in fraud)\n\n")
    
    body6 = ""
    if q6a:
        body6 += "### 6a. Berry Ethics Violations (Dedicated Table)\n\n"
        body6 += format_items(q6a) + "\n"
    if q6b:
        body6 += "### 6b. Evidence Quotes — Berry/Barnes Coordination\n\n"
        body6 += format_items(q6b) + "\n"
    if q6c:
        body6 += "### 6c. Evidence Quotes — Ronald Berry\n\n"
        body6 += format_items(q6c) + "\n"
    if q6d:
        body6 += "### 6d. Actor Violations — Berry/Barnes\n\n"
        body6 += format_items(q6d) + "\n"
    if not body6:
        body6 = "*No Berry/Barnes conspiracy evidence found.*\n"
    sections.append((sect6, body6))

    # === 7. McNEILL-HOOPES / JUDICIAL CONFLICT ===
    print("\n=== 7. McNEILL-HOOPES CONNECTION ===")
    
    # 7a. evidence_quotes — Hoopes + judicial conflict
    q7a = safe_query(conn, "eq_hoopes",
        """SELECT quote_text, document_id, evidence_category, speaker, legal_significance
           FROM evidence_quotes 
           WHERE quote_text LIKE '%Hoopes%' OR quote_text LIKE '%shared office%' 
                 OR quote_text LIKE '%law office%' OR quote_text LIKE '%former partner%'
           LIMIT 20""")
    
    # 7b. evidence_quotes — judicial bias/conflict
    q7b = safe_query(conn, "eq_bias",
        """SELECT quote_text, document_id, evidence_category, speaker, legal_significance
           FROM evidence_quotes 
           WHERE (quote_text LIKE '%McNeill%' OR quote_text LIKE '%judge%')
           AND (quote_text LIKE '%conflict%' OR quote_text LIKE '%bias%' 
                OR quote_text LIKE '%impartial%' OR quote_text LIKE '%recus%'
                OR quote_text LIKE '%disqualif%')
           LIMIT 20""")
    
    # 7c. judicial_conflicts table (dedicated!)
    q7c = safe_query(conn, "jc_all",
        "SELECT * FROM judicial_conflicts LIMIT 20")
    
    # 7d. forensic_judicial_analysis
    q7d_cols = safe_query(conn, "fja_schema", "PRAGMA table_info(forensic_judicial_analysis)")
    print(f"  forensic_judicial_analysis columns: {[r['name'] for r in q7d_cols]}")
    
    q7d = safe_query(conn, "forensic_judicial",
        "SELECT * FROM forensic_judicial_analysis LIMIT 20")
    
    summary["7a_EQ_Hoopes"] = len(q7a)
    summary["7b_EQ_Judicial_Bias"] = len(q7b)
    summary["7c_Judicial_Conflicts"] = len(q7c)
    summary["7d_Forensic_Judicial"] = len(q7d)
    
    sect7 = "## 7. McNEILL-HOOPES CONNECTION — Judicial Conflict of Interest\n\n"
    sect7 += ("Evidence of Judge McNeill's conflicts of interest and judicial bias, "
              "including Hoopes connection.\n\n"
              "**Filing Relevance:** F3 (MCR 2.003 requires recusal), "
              "F5 (MSC judicial misconduct)\n\n")
    
    body7 = ""
    if q7a:
        body7 += "### 7a. Evidence Quotes — Hoopes Connection\n\n"
        body7 += format_items(q7a) + "\n"
    if q7b:
        body7 += "### 7b. Evidence Quotes — Judicial Bias\n\n"
        body7 += format_items(q7b) + "\n"
    if q7c:
        body7 += "### 7c. Judicial Conflicts (Dedicated Table)\n\n"
        body7 += format_items(q7c) + "\n"
    if q7d:
        body7 += "### 7d. Forensic Judicial Analysis\n\n"
        body7 += format_items(q7d) + "\n"
    if not body7:
        body7 = "*No Hoopes/judicial conflict evidence found.*\n"
    sections.append((sect7, body7))

    # === 8. CLAIMS + LEGAL THEORIES ===
    print("\n=== 8. CLAIMS CROSS-REFERENCE ===")
    
    q8a = safe_query(conn, "claims_fraud",
        """SELECT claim_id, classification, actor, proposition, evidence_targets, status
           FROM claims 
           WHERE classification LIKE '%fraud%' OR classification LIKE '%perjur%'
                 OR classification LIKE '%conspir%' OR classification LIKE '%1983%'
                 OR classification LIKE '%due process%' OR classification LIKE '%misconduct%'
                 OR proposition LIKE '%fraud%' OR proposition LIKE '%perjur%'
                 OR proposition LIKE '%conspir%' OR proposition LIKE '%1983%'
           LIMIT 30""")
    
    # cycle6_legal_claims
    q8b_cols = safe_query(conn, "c6_schema", "PRAGMA table_info(cycle6_legal_claims)")
    print(f"  cycle6_legal_claims columns: {[r['name'] for r in q8b_cols]}")
    
    q8b = safe_query(conn, "cycle6_claims",
        """SELECT * FROM cycle6_legal_claims 
           WHERE rowid IN (SELECT rowid FROM cycle6_legal_claims LIMIT 30)""")
    
    summary["8a_Claims_Fraud"] = len(q8a)
    summary["8b_Cycle6_Claims"] = len(q8b)
    
    body8 = ""
    if q8a:
        body8 += "### 8a. Claims — Fraud/Perjury/Conspiracy\n\n"
        body8 += format_items(q8a) + "\n"
    if q8b:
        body8 += "### 8b. Cycle 6 Legal Claims\n\n"
        body8 += format_items(q8b) + "\n"
    if body8:
        sections.append(("## 8. CLAIMS & LEGAL THEORIES CROSS-REFERENCE\n\n"
            "Active legal claims matching fraud, perjury, conspiracy, and misconduct.\n\n",
            body8))

    # === 9. EVIDENCE ARSENAL STATS ===
    print("\n=== 9. EVIDENCE ARSENAL ===")
    
    arsenal = safe_query(conn, "arsenal",
        """SELECT 
            (SELECT COUNT(*) FROM evidence_quotes) as total_quotes,
            (SELECT COUNT(DISTINCT document_id) FROM evidence_quotes) as unique_docs,
            (SELECT COUNT(DISTINCT evidence_category) FROM evidence_quotes) as categories,
            (SELECT COUNT(*) FROM judicial_violations) as jv_count,
            (SELECT COUNT(*) FROM watson_perjury_compilation) as perjury_count,
            (SELECT COUNT(*) FROM conspiracy_timeline) as conspiracy_count,
            (SELECT COUNT(*) FROM watson_family_conspiracy) as wfc_count,
            (SELECT COUNT(*) FROM berry_ethics_violations) as berry_count,
            (SELECT COUNT(*) FROM judicial_conflicts) as jc_count,
            (SELECT COUNT(*) FROM constitutional_violations) as cv_count
        """)
    
    cat_breakdown = safe_query(conn, "categories",
        """SELECT evidence_category, COUNT(*) as cnt FROM evidence_quotes 
           GROUP BY evidence_category ORDER BY cnt DESC LIMIT 25""")

    # =========================================================================
    # WRITE REPORT
    # =========================================================================
    print("\n=== WRITING REPORT ===")
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("# FRAUD UPON THE COURT / FRUIT OF THE POISONOUS TREE\n")
        f.write("# Evidence Compilation for Filings F3, F4, F5\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("**Case:** Pigors v. Watson, No. 2024-001507-DC (14th Circuit Court, Muskegon County)\n\n")
        f.write("**Plaintiff:** Andrew James Pigors, *pro se*\n\n")
        f.write("**Defendant:** Emily A. Watson\n\n")
        f.write("**Judge:** Hon. Jenny L. McNeill\n\n")
        f.write("---\n\n")
        
        # Filing targets
        f.write("## FILING TARGETS\n\n")
        f.write("| Filing | Description | Strategy | Key Sections |\n")
        f.write("| --- | --- | --- | --- |\n")
        f.write("| **F3** | Motion for Disqualification (MCR 2.003) | McNeill must be removed — bias + conflicts | §1, §3, §4, §5, §7 |\n")
        f.write("| **F4** | 42 U.S.C. §1983 Federal Civil Rights | Bypass Muskegon — federal jurisdiction | §1, §2, §4, §5, §6 |\n")
        f.write("| **F5** | MSC Complaint for Superintending Control | Bypass COA — go straight to MSC | §1–§7 (all) |\n")
        f.write("\n---\n\n")
        
        # Legal framework
        f.write("## LEGAL FRAMEWORK\n\n")
        f.write("### Fraud Upon the Court\n\n")
        f.write("Fraud upon the court vitiates all orders flowing from the fraud. "
                "*Hazel-Atlas Glass Co. v. Hartford-Empire Co.*, 322 U.S. 238 (1944). "
                "A judgment obtained through fraud is void and may be vacated at any time. "
                "MCR 2.612(C)(1)(c) authorizes relief from judgment for fraud, "
                "misrepresentation, or other misconduct.\n\n")
        f.write("### Fruit of the Poisonous Tree\n\n")
        f.write("Evidence and orders derived from an initial unconstitutional or "
                "fraudulent act must be suppressed. *Wong Sun v. United States*, "
                "371 U.S. 471 (1963). The doctrine applies in civil context when "
                "the initial tainted act is a constitutional violation. "
                "If the PPO was obtained through perjury, ALL subsequent orders, "
                "custody modifications, and restrictions based on that PPO are tainted fruit.\n\n")
        f.write("### The Cascade\n\n")
        f.write("```\n")
        f.write("FALSE PPO PETITION (perjury)\n")
        f.write("  → PPO Granted (tainted)\n")
        f.write("    → Custody Modification (fruit of tainted PPO)\n")
        f.write("      → Parenting Time Restrictions (fruit)\n")
        f.write("        → August 8, 2025 Ex-Parte Order (compounded fruit)\n")
        f.write("          → ALL current restrictions on Andrew Pigors (illegitimate)\n")
        f.write("```\n\n")
        f.write("---\n\n")
        
        # Arsenal summary at top
        if arsenal:
            a = arsenal[0]
            f.write("## EVIDENCE ARSENAL OVERVIEW\n\n")
            f.write("| Database Table | Record Count |\n")
            f.write("| --- | --- |\n")
            f.write(f"| evidence_quotes | {a['total_quotes']} |\n")
            f.write(f"| judicial_violations | {a['jv_count']} |\n")
            f.write(f"| watson_perjury_compilation | {a['perjury_count']} |\n")
            f.write(f"| conspiracy_timeline | {a['conspiracy_count']} |\n")
            f.write(f"| watson_family_conspiracy | {a['wfc_count']} |\n")
            f.write(f"| berry_ethics_violations | {a['berry_count']} |\n")
            f.write(f"| judicial_conflicts | {a['jc_count']} |\n")
            f.write(f"| constitutional_violations | {a['cv_count']} |\n")
            f.write(f"| Unique source documents | {a['unique_docs']} |\n")
            f.write(f"| Evidence categories | {a['categories']} |\n")
            f.write("\n")
            
            if cat_breakdown:
                f.write("### Evidence Categories\n\n")
                f.write("| Category | Count |\n")
                f.write("| --- | --- |\n")
                for r in cat_breakdown:
                    f.write(f"| {r['evidence_category'] or 'NULL'} | {r['cnt']} |\n")
                f.write("\n")
            f.write("---\n\n")
        
        # All sections
        for header, body in sections:
            f.write(header + "\n")
            f.write(body + "\n")
            f.write("---\n\n")
        
        # Query summary
        f.write("## QUERY RESULTS SUMMARY\n\n")
        f.write("| Query | Results |\n")
        f.write("| --- | --- |\n")
        total_evidence = 0
        for k, v in summary.items():
            f.write(f"| {k.replace('_', ' ')} | {v} |\n")
            total_evidence += v
        f.write(f"| **TOTAL EVIDENCE ITEMS** | **{total_evidence}** |\n")
        f.write("\n---\n\n")
        
        f.write("*This compilation was generated from litigation_context.db SQL queries. "
                "Every statistic is traceable to a specific query. "
                "No statistics were fabricated or extrapolated.*\n")

    print(f"\nReport written: {OUTPUT_PATH}")
    file_size = os.path.getsize(OUTPUT_PATH)
    print(f"Report size: {file_size:,} bytes ({file_size/1024:.0f} KB)")
    
    # Final summary
    print("\n" + "=" * 65)
    print("EVIDENCE COMPILATION SUMMARY")
    print("=" * 65)
    total = 0
    for k, v in summary.items():
        print(f"  {k:40s} : {v:4d}")
        total += v
    print(f"  {'TOTAL':40s} : {total:4d}")
    print("=" * 65)
    
    if arsenal:
        a = arsenal[0]
        print(f"\nDB Arsenal:")
        print(f"  {a['total_quotes']} evidence quotes | {a['jv_count']} judicial violations")
        print(f"  {a['perjury_count']} perjury records | {a['conspiracy_count']} conspiracy events")
        print(f"  {a['wfc_count']} Watson family conspiracy | {a['berry_count']} Berry ethics violations")
        print(f"  {a['jc_count']} judicial conflicts | {a['cv_count']} constitutional violations")
    
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
