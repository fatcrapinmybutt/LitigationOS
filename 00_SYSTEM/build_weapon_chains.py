"""
THEMANBEARPIG — Weaponization Chain Builder
Maps: Adversary→Date→Instance→Effect→Doctrine→Remedy→Filing Stack
"""
import sqlite3, json, os, re
from collections import defaultdict
from datetime import datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")
conn.row_factory = sqlite3.Row

# ══════════════════════════════════════════════════
# DOCTRINE MAP: weapon_type → legal doctrine + remedy + filing
# ══════════════════════════════════════════════════
DOCTRINE_MAP = {
    "FALSE_ALLEGATION": {
        "doctrines": ["MCR 2.114(D) sanctions", "MCL 600.2591 frivolous claims", "MRE 608 character for truthfulness", "MRE 613 prior inconsistent statements"],
        "effects": ["Reputation damage", "Arrest risk", "CPS investigations", "Lost parenting time", "Emotional distress"],
        "remedies": ["Sanctions under MCR 2.114(D)", "Attorney fees MCL 600.2591", "Impeachment at trial", "Motion to strike false statements"],
        "filing_stack": ["MC 375 Motion for Sanctions", "Affidavit of False Allegations", "Exhibit: Police reports showing no probable cause"],
    },
    "EX_PARTE": {
        "doctrines": ["MCR 2.119(B) ex parte orders", "US Const Amend XIV due process", "Mathews v Eldridge 424 US 319", "MCR 3.207(A) temporary orders"],
        "effects": ["Loss of custody without hearing", "Loss of parenting time", "Constitutional rights violated", "No opportunity to respond"],
        "remedies": ["Motion to set aside ex parte order MCR 2.612", "Emergency motion to restore parenting time", "MSC superintending control MCR 7.306"],
        "filing_stack": ["MC 375 Motion to Set Aside", "Affidavit of Due Process Violation", "Proposed Order Restoring Rights"],
    },
    "PARENTING_TIME_DENIAL": {
        "doctrines": ["MCL 722.27a parenting time", "MCL 722.23(j) factor j willingness", "Brown v Loveman 260 Mich App 576", "MCR 3.206 custody modification"],
        "effects": ["Parent-child bond damage", "Separation trauma to L.D.W.", "Parental alienation", "248+ days without contact"],
        "remedies": ["Motion to enforce parenting time", "Motion for makeup time", "Contempt against custodial parent", "Change of custody"],
        "filing_stack": ["FOC 89 Parenting Time Complaint", "MC 375 Motion to Enforce", "Affidavit of Withholding"],
    },
    "CONTEMPT_ABUSE": {
        "doctrines": ["MCL 600.1701 contempt power", "MCR 3.606 contempt proceedings", "US Const Amend I free speech", "In re Contempt of Dougherty 429 Mich 81"],
        "effects": ["59 days incarceration", "Lost 2 homes", "Lost 2 jobs", "Financial devastation", "Separation from child"],
        "remedies": ["Motion to vacate contempt MCR 2.612", "Habeas corpus MCL 600.4301", "§1983 false imprisonment claim"],
        "filing_stack": ["MC 375 Motion to Vacate", "Habeas Corpus Petition", "Federal §1983 Complaint"],
    },
    "PPO_WEAPONIZATION": {
        "doctrines": ["MCL 600.2950 domestic PPO", "MCR 3.707 PPO proceedings", "Hayford v Hayford 279 Mich App 324", "MCL 764.15b criminal contempt PPO"],
        "effects": ["Criminal charges", "No-contact orders", "Housing restrictions", "Employment impact"],
        "remedies": ["Motion to terminate PPO MCR 3.707(B)", "Motion to modify PPO", "Sanctions for bad faith PPO"],
        "filing_stack": ["MC 375 Motion to Terminate PPO", "Affidavit: Recantation + No Evidence", "Exhibit: NSPD-2023-08121 recantation"],
    },
    "JUDICIAL_BIAS": {
        "doctrines": ["MCR 2.003(C)(1)(b) bias/prejudice", "Canon 2 Michigan Code of Judicial Conduct", "Canon 3 impartiality", "28 USC §455 federal disqualification"],
        "effects": ["Unfair rulings", "Predetermined outcomes", "Denial of fair hearing", "Loss of confidence in judiciary"],
        "remedies": ["MCR 2.003 disqualification motion", "JTC complaint", "MSC superintending control", "§1983 judicial misconduct"],
        "filing_stack": ["MC 375 Motion to Disqualify", "Affidavit of Bias", "JTC Complaint Letter", "MSC Original Action"],
    },
    "EVIDENCE_SUPPRESSION": {
        "doctrines": ["MRE 402 relevant evidence admissible", "MRE 702-703 expert testimony", "MRE 901 authentication", "MCR 2.302 discovery scope"],
        "effects": ["Incomplete record", "Unfair trial", "Excluded HealthWest evaluation", "Hidden exculpatory evidence"],
        "remedies": ["Motion to compel discovery MCR 2.313", "Motion to admit excluded evidence", "New trial motion MCR 2.611"],
        "filing_stack": ["MC 375 Motion to Compel", "MC 375 Motion for New Trial", "Affidavit of Excluded Evidence"],
    },
    "PARENTAL_ALIENATION": {
        "doctrines": ["MCL 722.23(j) factor j", "MCL 722.23(l) other factors", "Pierron v Pierron 486 Mich 81", "Shade v Wright 291 Mich App 17"],
        "effects": ["Destruction of parent-child bond", "Child's emotional harm", "False narrative to child", "Complete cutoff"],
        "remedies": ["Change of custody MCL 722.27", "GAL appointment MCR 3.915", "Therapy-directed reunification"],
        "filing_stack": ["MC 375 Motion to Change Custody", "Motion for GAL", "Affidavit of Alienation Pattern"],
    },
    "DUE_PROCESS_VIOLATION": {
        "doctrines": ["US Const Amend XIV", "MI Const Art 1 §17", "Mathews v Eldridge 424 US 319", "Troxel v Granville 530 US 57"],
        "effects": ["Constitutional rights violated", "No notice of proceedings", "No hearing before deprivation", "Fundamental liberty interest taken"],
        "remedies": ["§1983 civil rights action", "MSC original jurisdiction", "Emergency appellate relief"],
        "filing_stack": ["Federal §1983 Complaint", "MSC Superintending Control", "COA Emergency Application"],
    },
}

# ══════════════════════════════════════════════════
# GATHER: All adversary actions from multiple DB tables
# ══════════════════════════════════════════════════
print("=== THEMANBEARPIG Weaponization Chain Builder ===\n")

# 1. Impeachment matrix — high-severity items
print("[1/6] Impeachment matrix (severity >= 7)...")
imp_rows = conn.execute("""
    SELECT category, evidence_summary, source_file, quote_text, 
           impeachment_value, cross_exam_question, filing_relevance, event_date
    FROM impeachment_matrix WHERE impeachment_value >= 7
    ORDER BY impeachment_value DESC
""").fetchall()
print(f"  {len(imp_rows)} high-severity impeachment items")

# 2. Contradictions — critical severity
print("[2/6] Contradiction map (critical)...")
contra_rows = conn.execute("""
    SELECT claim_id, source_a, source_b, contradiction_text, severity, lane
    FROM contradiction_map WHERE severity = 'critical'
    ORDER BY ROWID DESC LIMIT 500
""").fetchall()
print(f"  {len(contra_rows)} critical contradictions")

# 3. Judicial violations
print("[3/6] Judicial violations...")
jv_rows = conn.execute("""
    SELECT violation_type, severity, COUNT(*) as cnt
    FROM judicial_violations GROUP BY violation_type, severity
    ORDER BY cnt DESC
""").fetchall()
jv_total = conn.execute("SELECT COUNT(*) FROM judicial_violations").fetchone()[0]
print(f"  {jv_total} judicial violations ({len(jv_rows)} categories)")

# 4. Timeline events with dates
print("[4/6] Timeline events with adversary dates...")
adversary_kw = {
    "Emily Watson": "emily OR watson OR defendant OR mother",
    "Judge McNeill": "mcneill OR judge",
    "Albert Watson": "albert",
    "Pamela Rusco": "rusco OR pamela OR foc",
    "Ronald Berry": "ronald OR berry",
    "Jennifer Barnes": "barnes OR attorney OR counsel",
    "Kenneth Hoopes": "hoopes",
    "Lori Watson": "lori",
}
adv_timeline = {}
for adv, kw in adversary_kw.items():
    try:
        sanitized = re.sub(r'[^\w\s*"OR]', ' ', kw)
        rows = conn.execute("""
            SELECT event_date, event_description, source_table, lane
            FROM timeline_events WHERE ROWID IN (
                SELECT ROWID FROM timeline_fts WHERE timeline_fts MATCH ?
            ) AND event_date IS NOT NULL AND event_date != ''
            ORDER BY event_date DESC LIMIT 50
        """, (sanitized,)).fetchall()
    except:
        rows = conn.execute("""
            SELECT event_date, event_description, source_table, lane
            FROM timeline_events 
            WHERE (event_description LIKE ? OR actors LIKE ?)
            AND event_date IS NOT NULL AND event_date != ''
            ORDER BY event_date DESC LIMIT 50
        """, (f"%{adv.split()[0].lower()}%", f"%{adv.split()[0].lower()}%")).fetchall()
    adv_timeline[adv] = [dict(r) for r in rows]
    print(f"  {adv}: {len(rows)} dated events")

# 5. Filing pipeline with readiness
print("[5/6] Filing pipeline...")
filings = conn.execute("""
    SELECT vehicle_name, filing_id, status, readiness_score, lane, deadline,
           blockers, exhibit_count, authority_count
    FROM filing_readiness ORDER BY readiness_score DESC
""").fetchall()
print(f"  {len(filings)} filing packages")

# 6. Police reports weaponization
print("[6/6] Police reports...")
pr_rows = conn.execute("""
    SELECT id, dates, filename, allegations, 
           exculpatory, key_quotes, witnesses, incident_numbers
    FROM police_reports WHERE allegations IS NOT NULL
    ORDER BY ROWID DESC LIMIT 100
""").fetchall()
print(f"  {len(pr_rows)} police reports with allegations")

# ══════════════════════════════════════════════════
# BUILD: Full weaponization chains
# ══════════════════════════════════════════════════
print("\n[BUILD] Constructing weaponization chains...")

chains = []
chain_id = 0

# Map impeachment items to adversaries and chains
adversary_keywords = {
    "Emily Watson": ["watson","emily","defendant","mother","respondent"],
    "Judge McNeill": ["mcneill","judge","court","judicial","hon."],
    "Albert Watson": ["albert"],
    "Pamela Rusco": ["rusco","pamela","foc","friend of court"],
    "Ronald Berry": ["ronald berry","ron berry"],
    "Jennifer Barnes": ["barnes","jennifer","attorney","counsel"],
    "Kenneth Hoopes": ["hoopes","chief judge"],
    "Lori Watson": ["lori watson","lori"],
    "Cavan Berry": ["cavan","magistrate"],
    "Maria Ladas-Hoopes": ["ladas","maria"],
}

def detect_adversary(text):
    text_lower = text.lower() if text else ""
    matched = []
    for adv, kws in adversary_keywords.items():
        if any(kw in text_lower for kw in kws):
            matched.append(adv)
    return matched or ["SYSTEM"]

def detect_weapon_type(text):
    text_lower = text.lower() if text else ""
    weapons = []
    if any(w in text_lower for w in ["false","fabricat","lie","untrue","misrepresent","perjur","recant"]):
        weapons.append("FALSE_ALLEGATION")
    if any(w in text_lower for w in ["ex parte","without notice","no notice","unilateral"]):
        weapons.append("EX_PARTE")
    if any(w in text_lower for w in ["withhold","deny parenting","block","restrict parenting","no contact"]):
        weapons.append("PARENTING_TIME_DENIAL")
    if any(w in text_lower for w in ["contempt","jail","incarcerat","59 days","14 days","45 days"]):
        weapons.append("CONTEMPT_ABUSE")
    if any(w in text_lower for w in ["ppo","protection order","stalking petition"]):
        weapons.append("PPO_WEAPONIZATION")
    if any(w in text_lower for w in ["bias","prejudic","one-sided","partial","favoritism"]):
        weapons.append("JUDICIAL_BIAS")
    if any(w in text_lower for w in ["suppress","exclud","ignor","disregard","refused to consider"]):
        weapons.append("EVIDENCE_SUPPRESSION")
    if any(w in text_lower for w in ["alienat","interfere","manipulat","undermine parent","replace father"]):
        weapons.append("PARENTAL_ALIENATION")
    if any(w in text_lower for w in ["due process","rights violat","constitutional","no hearing","no notice"]):
        weapons.append("DUE_PROCESS_VIOLATION")
    return weapons or ["EVIDENCE_SUPPRESSION"]

# Build chains from impeachment items
for r in imp_rows:
    text = f"{r['category']} {r['evidence_summary']} {r['quote_text']}"
    advs = detect_adversary(text)
    weapons = detect_weapon_type(text)
    
    for adv in advs:
        for weapon in weapons:
            doctrine = DOCTRINE_MAP.get(weapon, DOCTRINE_MAP["EVIDENCE_SUPPRESSION"])
            chain_id += 1
            chains.append({
                "chain_id": f"WC-{chain_id:05d}",
                "adversary": adv,
                "date": r["event_date"] or "UNDATED",
                "instance": r["evidence_summary"][:200] if r["evidence_summary"] else r["category"],
                "weapon_type": weapon,
                "effect_on_father_son": doctrine["effects"],
                "doctrine_rule_law": doctrine["doctrines"],
                "remedy_prayer": doctrine["remedies"],
                "filing_stack": doctrine["filing_stack"],
                "source": r["source_file"] or "impeachment_matrix",
                "severity": r["impeachment_value"],
                "quote": (r["quote_text"] or "")[:300],
                "cross_exam": (r["cross_exam_question"] or "")[:300],
                "filing_relevance": r["filing_relevance"],
            })

# Build chains from contradictions
for r in contra_rows:
    text = f"{r['source_a']} {r['source_b']} {r['contradiction_text']}"
    advs = detect_adversary(text)
    weapons = detect_weapon_type(text)
    
    for adv in advs:
        for weapon in weapons[:2]:  # limit to top 2 per contradiction
            doctrine = DOCTRINE_MAP.get(weapon, DOCTRINE_MAP["FALSE_ALLEGATION"])
            chain_id += 1
            chains.append({
                "chain_id": f"WC-{chain_id:05d}",
                "adversary": adv,
                "date": "PATTERN",
                "instance": (r["contradiction_text"] or "")[:200],
                "weapon_type": weapon,
                "effect_on_father_son": doctrine["effects"],
                "doctrine_rule_law": doctrine["doctrines"],
                "remedy_prayer": doctrine["remedies"],
                "filing_stack": doctrine["filing_stack"],
                "source": f"contradiction:{r['claim_id']}",
                "severity": 9 if r["severity"] == "critical" else 7,
                "quote": f"{r['source_a'][:100]} vs {r['source_b'][:100]}",
                "cross_exam": "",
                "filing_relevance": r["lane"] or "ALL",
            })

# Build chains from police reports
for r in pr_rows:
    text = f"{r['allegations']} {r['exculpatory']} {r['key_quotes']}"
    advs = detect_adversary(text)
    
    chain_id += 1
    chains.append({
        "chain_id": f"WC-{chain_id:05d}",
        "adversary": advs[0] if advs else "Emily Watson",
        "date": r["dates"] or "UNDATED",
        "instance": (r["allegations"] or "")[:200],
        "weapon_type": "FALSE_ALLEGATION",
        "effect_on_father_son": DOCTRINE_MAP["FALSE_ALLEGATION"]["effects"],
        "doctrine_rule_law": DOCTRINE_MAP["FALSE_ALLEGATION"]["doctrines"],
        "remedy_prayer": DOCTRINE_MAP["FALSE_ALLEGATION"]["remedies"],
        "filing_stack": DOCTRINE_MAP["FALSE_ALLEGATION"]["filing_stack"],
        "source": f"police_report:{r['incident_numbers'] or r['id']}",
        "severity": 8,
        "quote": (r["key_quotes"] or "")[:300],
        "cross_exam": "",
        "filing_relevance": "A,D",
    })

# ══════════════════════════════════════════════════
# PERSIST: Save to DB + JSON
# ══════════════════════════════════════════════════
print(f"\n[PERSIST] {len(chains)} weaponization chains built")

# Create weapon_chains table
conn.execute("DROP TABLE IF EXISTS weapon_chains")
conn.execute("""
    CREATE TABLE weapon_chains (
        chain_id TEXT PRIMARY KEY,
        adversary TEXT,
        date TEXT,
        instance TEXT,
        weapon_type TEXT,
        effect_on_father_son TEXT,
        doctrine_rule_law TEXT,
        remedy_prayer TEXT,
        filing_stack TEXT,
        source TEXT,
        severity INTEGER,
        quote TEXT,
        cross_exam TEXT,
        filing_relevance TEXT
    )
""")
conn.executemany("""
    INSERT INTO weapon_chains VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
""", [
    (c["chain_id"], c["adversary"], c["date"], c["instance"],
     c["weapon_type"], json.dumps(c["effect_on_father_son"]),
     json.dumps(c["doctrine_rule_law"]), json.dumps(c["remedy_prayer"]),
     json.dumps(c["filing_stack"]), c["source"], c["severity"],
     c["quote"], c["cross_exam"], c["filing_relevance"])
    for c in chains
])
conn.commit()

# Verify
total = conn.execute("SELECT COUNT(*) FROM weapon_chains").fetchone()[0]
print(f"  DB: weapon_chains = {total} rows")

# Summary by adversary
print("\n[SUMMARY] Chains per adversary:")
for row in conn.execute("SELECT adversary, COUNT(*) as cnt FROM weapon_chains GROUP BY adversary ORDER BY cnt DESC"):
    print(f"  {row[0]}: {row[1]} chains")

print("\n[SUMMARY] Chains per weapon type:")
for row in conn.execute("SELECT weapon_type, COUNT(*) as cnt FROM weapon_chains GROUP BY weapon_type ORDER BY cnt DESC"):
    print(f"  {row[0]}: {row[1]} chains")

# Save JSON
out = r"D:\LitigationOS_tmp\weapon_chains.json"
with open(out, "w") as f:
    json.dump(chains, f, indent=2, default=str)
print(f"\n[SAVED] {out} ({len(chains)} chains, {os.path.getsize(out):,} bytes)")

# Also save the adversary timeline data
timeline_out = r"D:\LitigationOS_tmp\adversary_timelines.json"
serializable = {}
for adv, events in adv_timeline.items():
    serializable[adv] = events
with open(timeline_out, "w") as f:
    json.dump(serializable, f, indent=2, default=str)
print(f"[SAVED] {timeline_out}")

# Save filing pipeline
filing_out = r"D:\LitigationOS_tmp\filing_pipeline.json"
filing_list = [dict(r) for r in filings]
with open(filing_out, "w") as f:
    json.dump(filing_list, f, indent=2, default=str)
print(f"[SAVED] {filing_out} ({len(filing_list)} filings)")

conn.close()
print("\n=== WEAPONIZATION CHAINS COMPLETE ===")
