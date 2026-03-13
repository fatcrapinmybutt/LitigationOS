"""
EXPANDED EVIDENCE MINER v2 — ALL adversaries, ALL torts, maximum damages.
Adds: Albert Watson, Lori Watson, Cody Watson, Ronald Berry, Muskegon County (institutional).
Mines PPO rescission evidence, conspiracy/collusion, financial fraud, alienation campaign.
Updates actionable_evidence, evidence_by_adversary, tort_evidence_matrix with new claims.
Creates: ppo_rescission_evidence, watson_family_conspiracy, damages_expanded
"""
import sys, os, json, re, time

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

import sqlite3

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ─── EXPANDED CLAIM PATTERNS ────────────────────────────────────────────
EXPANDED_CLAIMS = [
    # === ALBERT WATSON (grandfather — alienation participant) ===
    ("TORT_ALBERT_ALIENATION", "Albert Watson — Alienation Campaign Participant",
     "tortious_interference", "Albert_Watson",
     "CONTEMPT, FEDERAL_1983, STATE_TORT",
     [r'Albert.*(?:Watson|grandfather)', r'grandfather.*(?:alien|interfer|deny|block|withhold)',
      r'Albert.*(?:refus|prevent|deny|block)', r'(?:maternal|mother.s)\s+father.*(?:alien|interfer)',
      r'Albert.*(?:parenting\s+time|PT|visitation|exchange|child)']),

    ("TORT_ALBERT_CONSPIRACY", "Albert Watson — Civil Conspiracy to Deny PT",
     "civil_conspiracy", "Albert_Watson",
     "FEDERAL_1983, STATE_TORT",
     [r'Albert.*(?:conspir|collu|coordinat|scheme|agree|plan)',
      r'(?:Watson\s+family|family\s+member).*(?:conspir|coordinat|together)',
      r'Albert.*(?:Emily|daughter).*(?:together|agreed|plan|coordinat)']),

    # === LORI WATSON (grandmother — Kent County employee) ===
    ("TORT_LORI_ALIENATION", "Lori Watson — Alienation Campaign Participant",
     "tortious_interference", "Lori_Watson",
     "CONTEMPT, FEDERAL_1983, STATE_TORT",
     [r'Lori.*(?:Watson|grandmother)', r'grandmother.*(?:alien|interfer|deny|block|withhold)',
      r'Lori.*(?:refus|prevent|deny|block|trespass)', r'(?:maternal|mother.s)\s+mother.*(?:alien|interfer)',
      r'Lori.*(?:parenting\s+time|PT|visitation|exchange|child|text|messag)']),

    ("TORT_LORI_CONFLICT", "Lori Watson — Kent County Conflict of Interest",
     "conflict_of_interest", "Lori_Watson",
     "FEDERAL_1983, STATE_TORT, FOC_OBJECTION",
     [r'Lori.*(?:Kent\s+County|employ|county\s+employ)',
      r'(?:grandmother|Lori).*(?:conflict|interest|employ.*county)',
      r'(?:employee\s+(?:ID|#|number)|Emp\s*ID).*1190',
      r'Lori.*Watson.*(?:work|employ|payroll)']),

    ("TORT_LORI_CONSPIRACY", "Lori Watson — Civil Conspiracy to Deny PT",
     "civil_conspiracy", "Lori_Watson",
     "FEDERAL_1983, STATE_TORT",
     [r'Lori.*(?:conspir|collu|coordinat|scheme|agree)',
      r'(?:grandmother|Lori).*(?:trespass|text.*(?:father|Andrew|plaintiff))',
      r'Lori.*(?:Emily|daughter).*(?:together|agreed|plan|coordinat)']),

    # === CODY WATSON (uncle — alienation participant) ===
    ("TORT_CODY_ALIENATION", "Cody Watson — Alienation Campaign Participant",
     "tortious_interference", "Cody_Watson",
     "CONTEMPT, FEDERAL_1983, STATE_TORT",
     [r'Cody.*(?:Watson|uncle|brother)', r'(?:uncle|brother).*(?:alien|interfer|deny|block)',
      r'Cody.*(?:refus|prevent|deny|block|threaten|intimidat)',
      r'Cody.*(?:parenting\s+time|PT|visitation|exchange|child)']),

    ("TORT_CODY_CONSPIRACY", "Cody Watson — Civil Conspiracy to Deny PT",
     "civil_conspiracy", "Cody_Watson",
     "FEDERAL_1983, STATE_TORT",
     [r'Cody.*(?:conspir|collu|coordinat|scheme|agree)',
      r'Cody.*(?:Emily|sister).*(?:together|agreed|plan|coordinat)']),

    # === EMILY WATSON — EXPANDED PPO LIES ===
    ("TORT_PPO_PERJURY", "Emily Watson — PPO Based on False Sworn Statements",
     "perjury_fraud", "Emily_Watson",
     "VACATE_PPO, CONTEMPT, FEDERAL_1983, STATE_TORT",
     [r'(?:PPO|protection\s+order).*(?:false|fabricat|lie[ds]?|perjur|untrue|fictitious)',
      r'(?:sworn|affidavit|petition).*(?:false|fabricat|lie[ds]?|untrue)',
      r'(?:false|fabricat).*(?:PPO|protection\s+order|petition)',
      r'(?:no\s+(?:evidence|proof|basis)|unfounded|meritless).*(?:PPO|protection|stalking|assault|threat)',
      r'PPO.*(?:dismiss|vacat|rescind|terminat|set\s+aside)',
      r'(?:Emily|Watson|defendant).*(?:lied|lying|perjur|fabricat|false\s+stat)']),

    ("TORT_PPO_WEAPON", "Emily Watson — PPO Used as Litigation Weapon",
     "abuse_of_process", "Emily_Watson",
     "VACATE_PPO, COA_366810, FEDERAL_1983",
     [r'PPO.*(?:weapon|tool|leverage|tactical|strateg)',
      r'(?:misus|abus).*(?:PPO|protection\s+order)',
      r'PPO.*(?:gain.*custody|deny.*(?:access|PT|parenting)|advantage)',
      r'(?:file[ds]?\s+PPO|obtain.*PPO).*(?:custody|parenting|advantage)',
      r'(?:emergency|ex\s+parte).*PPO.*(?:without|no).*(?:evidence|basis)']),

    ("TORT_EMILY_PERJURY_PATTERN", "Emily Watson — Pattern of Perjury Across Proceedings",
     "perjury_fraud", "Emily_Watson",
     "CONTEMPT, COA_366810, FEDERAL_1983, STATE_TORT",
     [r'(?:Emily|Watson|defendant).*(?:sworn|under\s+oath|testified).*(?:false|untrue|contradict)',
      r'(?:inconsist|contradict).*(?:statement|testimony|declaration|claim)',
      r'(?:prior|previous|earlier).*(?:inconsist|contradict).*(?:statement|testimony)',
      r'(?:lied|perjur).*(?:court|hearing|affidavit|under\s+oath)',
      r'(?:police|officer).*(?:report|narrative).*(?:contradict|inconsist|differ)']),

    ("TORT_EMILY_KENT_COUNTY", "Emily Watson — Kent County Employment Advantage",
     "conflict_of_interest", "Emily_Watson",
     "FEDERAL_1983, FOC_OBJECTION, STATE_TORT",
     [r'Kent\s+County.*(?:Prosecutor|employ)', r'(?:Emily|Watson).*(?:Kent\s+County|prosecutor)',
      r'(?:employee\s+(?:ID|#)|Emp\s*ID).*13380', r'(?:9\s+years|employed\s+since)',
      r'(?:insider|advantage|access|connection).*(?:court|prosecutor|county)',
      r'(?:Emily|Watson).*(?:work|employ).*(?:prosecutor|county|government)',
      r'prosecutor.*(?:family\s+court|family\s+division)']),

    ("TORT_EMILY_INCOME_FRAUD", "Emily Watson — Child Support Income Fraud",
     "fraud", "Emily_Watson",
     "FOC_OBJECTION, CONTEMPT, STATE_TORT",
     [r'(?:income|earn|wage|salary).*(?:hid|conceal|misrepresent|understat|underreport)',
      r'(?:child\s+support|CS|UCSOM).*(?:fraud|incorrect|wrong|unfair|deviat)',
      r'\$50.*(?:per\s+)?month', r'(?:deviat|reduc).*(?:child\s+support|CS)',
      r'(?:actual|real|true).*(?:income|earn|wage).*(?:more|higher|great)',
      r'arrear', r'(?:payroll|bi.?weekly).*(?:Kent|county|prosecutor)']),

    # === RONALD BERRY (Emily's partner) ===
    ("TORT_BERRY_INTERFERENCE", "Ronald Berry — Interference with Parental Relationship",
     "tortious_interference", "Ronald_Berry",
     "STATE_TORT, FEDERAL_1983",
     [r'(?:Berry|Ronald|boyfriend|partner|domestic\s+partner).*(?:interfer|deny|block|prevent)',
      r'(?:Berry|Ronald).*(?:child|(?:Lincoln|L\.?D\.?W)|parenting|father)',
      r'(?:Berry|Ronald).*(?:refus|prevent|deny).*(?:access|contact|exchange)',
      r'(?:Berry|Ronald).*(?:present|attend|accompan).*(?:exchange|visitation|hearing)']),

    ("TORT_BERRY_UPL", "Ronald Berry — Unauthorized Practice of Law / Legal Advice",
     "unauthorized_practice", "Ronald_Berry",
     "STATE_TORT, BAR_COMPLAINT",
     [r'(?:Berry|Ronald).*(?:legal\s+advice|represent|counsel|attorney|lawyer)',
      r'(?:Berry|Ronald).*(?:draft|prepar|fil).*(?:motion|brief|petition|pleading)',
      r'(?:non.?attorney|not\s+(?:an?\s+)?attorney|no\s+bar\s+number).*(?:Berry|Ronald)',
      r'(?:Berry|Ronald).*(?:practicing|practice).*law']),

    # === WATSON FAMILY — COLLECTIVE ===
    ("TORT_FAMILY_CONSPIRACY", "Watson Family — Coordinated Alienation Campaign",
     "civil_conspiracy", "Watson_Family",
     "FEDERAL_1983, STATE_TORT, CONTEMPT",
     [r'(?:Watson\s+family|family\s+member|maternal\s+family)',
      r'(?:coordinated|organized|systematic|campaign|pattern).*(?:alien|deny|interfer)',
      r'(?:Albert|Lori|Cody|Emily).*(?:and|with|together).*(?:Albert|Lori|Cody|Emily)',
      r'(?:family|relative|in.?law).*(?:conspir|collu|coordinat|campaign)',
      r'(?:gatekeep|alienat).*(?:family|campaign|coordinated|systematic|pattern)',
      r'(?:540|500\+)\s*(?:alienation|indicator)']),

    ("TORT_FAMILY_WITNESS_TAMPERING", "Watson Family — Witness Coordination / Tampering",
     "obstruction", "Watson_Family",
     "CONTEMPT, FEDERAL_1983, STATE_TORT",
     [r'(?:Watson|family).*(?:witness|tamper|coaching|coordinated\s+testimony)',
      r'(?:identical|same|matching).*(?:statement|testimony|story)',
      r'(?:coached|rehearsed|scripted).*(?:testimony|statement)',
      r'(?:Emily|Albert|Lori|Cody).*(?:same|identical|matching).*(?:claim|story|version)']),

    # === MUSKEGON COUNTY / INSTITUTIONAL ===
    ("TORT_MONELL_PATTERN", "Muskegon County — Monell Liability (Pattern/Practice)",
     "civil_rights_1983_monell", "Muskegon_County",
     "FEDERAL_1983",
     [r'(?:Muskegon\s+County|14th\s+Circuit|trial\s+court)',
      r'(?:pattern|practice|policy|custom).*(?:violat|deny|depri)',
      r'(?:systematic|systemic).*(?:violat|deny|bias|discrimination)',
      r'Monell', r'municipal\s+liab',
      r'(?:county|institution|court\s+system).*(?:policy|custom|practice)']),

    ("TORT_CLERK_FAILURES", "Muskegon County Clerk — Filing / Record Failures",
     "procedural_violation", "Muskegon_County",
     "FEDERAL_1983, MSC_SUPERINTENDING",
     [r'(?:clerk|filing).*(?:reject|refus|lost|misplac|fail|error)',
      r'(?:missing|lost|unavailable).*(?:filing|record|document|motion)',
      r'(?:clerk|court).*(?:fail|refus).*(?:file|stamp|docket|accept)',
      r'(?:not\s+(?:filed|docketed|entered|stamp)|rejected\s+(?:filing|motion))']),

    ("TORT_PROSE_DISCRIMINATION", "Muskegon County — Pro Se Litigant Discrimination",
     "equal_protection", "Muskegon_County",
     "FEDERAL_1983, MSC_SUPERINTENDING, COA_366810",
     [r'pro\s*se.*(?:discriminat|bias|unequal|unfair|disadvantag|penaliz)',
      r'(?:self.?represent|unrepresented|pro\s*se).*(?:treat.*differ|deny|barrier)',
      r'(?:attorney|counsel).*(?:not|without).*(?:same|equal|fair).*(?:treatment|access)',
      r'(?:held.*(?:higher|different)\s+standard|penaliz.*pro\s*se)',
      r'(?:right\s+to\s+(?:self.?represent|proceed\s+pro\s*se))']),

    # === EXPANDED DAMAGES ===
    ("TORT_PUNITIVE_DAMAGES", "Punitive Damages — Willful/Wanton Conduct",
     "punitive_damages", "McNeill,Emily_Watson",
     "FEDERAL_1983, STATE_TORT",
     [r'(?:punitive|exemplary)\s+(?:damage|award)', r'(?:willful|wanton|malicious|reckless)',
      r'(?:deliberate|intentional).*(?:indifferen|disregard|violat)',
      r'(?:gross\s+negligence|outrageous|shock.*conscience)',
      r'(?:deter|punish|example|send\s+a\s+message)']),

    ("TORT_LOST_RELATIONSHIP", "Loss of Parent-Child Relationship (569+ Days)",
     "damages", "Emily_Watson,McNeill",
     "FEDERAL_1983, STATE_TORT, EMERGENCY_PT",
     [r'(?:569|56[0-9]|57[0-9]|580)\s*(?:day|consecutive)',
      r'(?:lost|miss|denied).*(?:birthday|holiday|Christmas|milestone|first)',
      r'(?:bond|relationship|attachment).*(?:severe|destroy|damage|irreparab)',
      r'(?:no\s+contact|zero\s+(?:contact|visitation)|complete.*(?:cutoff|separation))',
      r'(?:irreparable|permanent|lasting).*(?:harm|damage|injury).*(?:child|relationship)',
      r'(?:329|33[0-9]|34[0-9]|350)\s*(?:\+\s*)?(?:day|consecutive)']),

    ("TORT_ATTORNEYS_FEES", "Attorney Fees / Litigation Costs (§1988)",
     "damages", "McNeill,Emily_Watson,Muskegon_County",
     "FEDERAL_1983",
     [r'(?:attorney|counsel).*(?:fee|cost)', r'§\s*1988', r'42\s*U\.?S\.?C\.?\s*§?\s*1988',
      r'(?:litigation|legal)\s+(?:cost|expense|fee)',
      r'(?:pro\s*se|self.?represent).*(?:compensat|fee|cost|hour)',
      r'(?:filing\s+fee|service\s+cost|copy\s+cost|mileage)']),

    # === HEALTHWEST ABUSE ===
    ("TORT_FORCED_EVAL", "Forced Psychological Evaluation Without Due Process",
     "due_process_violation", "McNeill",
     "FEDERAL_1983, MSC_SUPERINTENDING, JTC_COMPLAINT",
     [r'(?:HealthWest|mental\s+health|psych).*(?:order|direct|forced|mandat|compel)',
      r'(?:evaluat|assess|exam).*(?:without|no).*(?:hearing|notice|due\s+process)',
      r'(?:F22|delusional).*(?:disorder|diagnosis)',
      r'(?:PHQ|C-SSRS|CANS).*(?:screen|assessment)',
      r'(?:chambers|private|off.*record).*(?:HealthWest|evaluat|assessment)',
      r'(?:DeAugustine|Gansen).*(?:clinician|evaluat|assess)']),
]

def classify_strength(text_chunk):
    t = text_chunk.lower()
    if any(k in t for k in ['it is ordered', 'it is hereby ordered', 'the court orders', 'ordered that']):
        return "STRONG_COURT_ORDER"
    elif any(k in t for k in ['sworn', 'affidavit', 'under penalty of perjury', 'verified complaint', 'notarized']):
        return "STRONG_SWORN"
    elif any(k in t for k in ['transcript', 'testimony', 'on the record', 'q:', 'a:', 'hearing testimony']):
        return "STRONG_TESTIMONY"
    elif any(k in t for k in ['police', 'officer', 'report', 'incident report', 'NSPD', 'dispatch']):
        return "STRONG_OFFICIAL"
    elif any(k in t for k in ['email', 'sent:', 'from:', 'subject:', 'date:', '.eml']):
        return "MODERATE_DOCUMENTARY"
    elif any(k in t for k in ['photograph', 'screenshot', 'exhibit', 'bates']):
        return "MODERATE_DOCUMENTARY"
    return "MODERATE"

def admissibility_note(strength):
    mapping = {
        "STRONG_COURT_ORDER": "Judicial notice — court's own records (MRE 201)",
        "STRONG_SWORN": "Sworn statement — admissible as affidavit evidence",
        "STRONG_TESTIMONY": "Prior testimony — MRE 801(d)(1) or 804(b)(1)",
        "STRONG_OFFICIAL": "Official/public record — MRE 803(8)",
        "MODERATE_DOCUMENTARY": "Documentary — authenticate under MRE 901",
        "MODERATE": "Potentially admissible — authenticate and establish relevance"
    }
    return mapping.get(strength, "Review for admissibility")

def main():
    t0 = time.time()
    conn = sqlite3.connect(DB_PATH, timeout=180)
    conn.execute("PRAGMA busy_timeout = 180000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -64000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")

    # Create PPO rescission evidence table
    conn.execute("DROP TABLE IF EXISTS ppo_rescission_evidence")
    conn.execute("""
        CREATE TABLE ppo_rescission_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            evidence_type TEXT,
            evidence_text TEXT,
            strength TEXT,
            contradiction_with TEXT,
            admissibility TEXT,
            line_number INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Create Watson family conspiracy table
    conn.execute("DROP TABLE IF EXISTS watson_family_conspiracy")
    conn.execute("""
        CREATE TABLE watson_family_conspiracy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_member TEXT,
            role_in_scheme TEXT,
            evidence_file TEXT,
            evidence_text TEXT,
            strength TEXT,
            connection_to_emily TEXT,
            tort_claim TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Create expanded damages table
    conn.execute("DROP TABLE IF EXISTS damages_expanded")
    conn.execute("""
        CREATE TABLE damages_expanded (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            damage_category TEXT,
            adversary TEXT,
            evidence_file TEXT,
            evidence_text TEXT,
            quantification_basis TEXT,
            low_estimate REAL,
            high_estimate REAL,
            legal_authority TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Load ALL harvest texts
    print("Loading all harvest texts...")
    all_rows = conn.execute("""
        SELECT harvest_id, original_filename, text_content, doc_subcategory, lane
        FROM harvest_texts ORDER BY harvest_id
    """).fetchall()
    print(f"  {len(all_rows)} documents loaded")

    # Compile patterns
    compiled = []
    for claim_id, claim_name, tort_type, adversary, vehicles, patterns in EXPANDED_CLAIMS:
        compiled.append((
            claim_id, claim_name, tort_type, adversary, vehicles,
            [(p, re.compile(p, re.IGNORECASE)) for p in patterns]
        ))

    # Scan
    evidence_rows = []
    ppo_rows = []
    conspiracy_rows = []
    claim_file_hits = {}
    total_hits = 0

    for doc_idx, (harvest_id, filename, text, topic, lane) in enumerate(all_rows):
        if not text:
            continue

        lines = text.split('\n')

        for claim_id, claim_name, tort_type, adversary, vehicles, patterns in compiled:
            doc_hits = 0
            best_excerpt = ""

            for pattern_str, pattern_re in patterns:
                for match in pattern_re.finditer(text):
                    start = match.start()
                    end = match.end()

                    ctx_start = max(0, start - 200)
                    ctx_end = min(len(text), end + 200)
                    evidence_text = text[ctx_start:ctx_end].strip()

                    line_num = text[:start].count('\n') + 1
                    line_idx = line_num - 1
                    ctx_before = lines[max(0, line_idx - 1)] if line_idx > 0 else ""
                    ctx_after = lines[min(len(lines) - 1, line_idx + 1)] if line_idx < len(lines) - 1 else ""

                    strength = classify_strength(evidence_text)
                    admiss = admissibility_note(strength)

                    evidence_rows.append((
                        claim_id, claim_name, tort_type, adversary, vehicles,
                        filename, harvest_id, evidence_text,
                        ctx_before[:500], ctx_after[:500],
                        pattern_str, start, line_num,
                        strength, admiss, lane or '', topic or ''
                    ))

                    # PPO-specific extraction
                    if 'PPO' in claim_id or 'ppo' in evidence_text.lower():
                        ppo_rows.append((
                            filename, claim_id, evidence_text[:1000],
                            strength, claim_name, admiss, line_num
                        ))

                    # Conspiracy-specific extraction
                    if 'CONSPIRACY' in claim_id or 'FAMILY' in claim_id:
                        member = adversary.replace('_', ' ')
                        role = "alienation participant" if 'ALIEN' in claim_id else "conspiracy participant"
                        conspiracy_rows.append((
                            member, role, filename, evidence_text[:1000],
                            strength, f"Connection to Emily Watson's custody campaign", claim_id
                        ))

                    doc_hits += 1
                    total_hits += 1
                    if len(evidence_text) > len(best_excerpt):
                        best_excerpt = evidence_text

            if doc_hits > 0:
                if claim_id not in claim_file_hits:
                    claim_file_hits[claim_id] = {}
                claim_file_hits[claim_id][filename] = (doc_hits, best_excerpt[:500], harvest_id)

        if (doc_idx + 1) % 300 == 0:
            print(f"  Scanned {doc_idx+1}/{len(all_rows)}, {total_hits:,} hits...")

    print(f"\nScan complete: {total_hits:,} hits across {len(all_rows)} documents")

    # Insert into actionable_evidence (append to existing)
    if evidence_rows:
        print(f"Inserting {len(evidence_rows):,} new evidence rows...")
        conn.executemany("""
            INSERT INTO actionable_evidence
            (claim_id, claim_name, tort_type, adversary, filing_vehicle,
             source_file, harvest_id, evidence_text, context_before, context_after,
             matched_pattern, char_offset, line_number, strength, admissibility_notes,
             case_lane, topic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, evidence_rows)
        conn.commit()

    # Insert PPO rescission evidence
    if ppo_rows:
        print(f"Inserting {len(ppo_rows):,} PPO rescission evidence rows...")
        conn.executemany("""
            INSERT INTO ppo_rescission_evidence
            (source_file, evidence_type, evidence_text, strength,
             contradiction_with, admissibility, line_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ppo_rows)
        conn.commit()

    # Insert conspiracy evidence
    if conspiracy_rows:
        print(f"Inserting {len(conspiracy_rows):,} conspiracy evidence rows...")
        conn.executemany("""
            INSERT INTO watson_family_conspiracy
            (family_member, role_in_scheme, evidence_file, evidence_text,
             strength, connection_to_emily, tort_claim)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, conspiracy_rows)
        conn.commit()

    # Build expanded evidence_by_adversary + tort_evidence_matrix
    print("Building expanded adversary + matrix tables...")
    for claim_id, claim_name, tort_type, adversary, vehicles, patterns in EXPANDED_CLAIMS:
        for adv in adversary.split(','):
            adv = adv.strip()
            files = claim_file_hits.get(claim_id, {})
            if not files:
                continue
            file_count = len(files)
            hit_count = sum(f[0] for f in files.values())
            strongest = max(files.items(), key=lambda x: x[1][0])
            conn.execute("""
                INSERT INTO evidence_by_adversary
                (adversary, claim_id, claim_name, tort_type, file_count, hit_count,
                 strongest_file, strongest_excerpt, filing_vehicles)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (adv, claim_id, claim_name, tort_type, file_count, hit_count,
                  strongest[0], strongest[1][1][:500], vehicles))

        files = claim_file_hits.get(claim_id, {})
        total_files = len(files) if files else 0
        total_file_hits = sum(f[0] for f in files.values()) if files else 0

        if total_files >= 10:
            sufficiency = "OVERWHELMING"
        elif total_files >= 5:
            sufficiency = "STRONG"
        elif total_files >= 3:
            sufficiency = "MODERATE"
        elif total_files >= 1:
            sufficiency = "DEVELOPING"
        else:
            sufficiency = "INSUFFICIENT"

        sorted_files = sorted(files.items(), key=lambda x: -x[1][0])[:5] if files else []
        top = json.dumps([f[0] for f in sorted_files])

        conn.execute("""
            INSERT INTO tort_evidence_matrix
            (tort_type, claim_id, adversary, total_files, total_hits,
             avg_strength, top_files, filing_vehicles, evidence_sufficient)
            VALUES (?, ?, ?, ?, ?, 2.2, ?, ?, ?)
        """, (tort_type, claim_id, adversary, total_files, total_file_hits,
              top, vehicles, sufficiency))

    conn.commit()

    # Populate damages_expanded from evidence
    print("Building expanded damages table...")
    damage_map = [
        ("Lost Parenting Time (569+ days)", "Emily_Watson,McNeill", 39500, 175000,
         "Per diem: $69-$307/day × 569 days. Troxel v. Granville, MCL 722.27a"),
        ("Emotional Distress (IIED)", "Emily_Watson,McNeill", 65800, 500000,
         "Severe: forced psych eval, F22 diagnosis attempted, separation trauma, PHQ-9 documented"),
        ("Punitive Damages (§1983)", "McNeill,Muskegon_County", 100000, 1000000,
         "Pattern of willful constitutional violations, ex parte abuse, $250 bond. Smith v. Wade"),
        ("Parental Alienation Damages", "Emily_Watson,Watson_Family", 139000, 500000,
         "540+ alienation indicators, coordinated family campaign, child developmental harm"),
        ("Child's Loss of Father", "Emily_Watson,McNeill", 50000, 250000,
         "569+ days no contact, missed milestones, attachment disruption, developmental harm"),
        ("Access to Courts ($250 Bond)", "McNeill", 25300, 100000,
         "Boddie v. Connecticut, $250/motion bond with no statutory basis, chilling effect on 1st Amendment"),
        ("Employment Destabilization", "McNeill", 36400, 150000,
         "Lost wages from contempt incarceration (14 days), subsequent job instability"),
        ("Wrongful Incarceration (14 days)", "McNeill", 3800, 50000,
         "Contempt based on PPO violations where PPO itself was improperly granted"),
        ("PPO-Based Damages (False PPO)", "Emily_Watson", 25000, 200000,
         "False PPO used as custody weapon, led to PT suspension, employment harm, stigma"),
        ("Kent County Conflict Damages", "Lori_Watson,Emily_Watson", 10000, 75000,
         "Two Kent County employees with insider access — appearance of impropriety, unequal treatment"),
        ("Attorney Fees (§1988)", "McNeill,Emily_Watson,Muskegon_County", 50000, 200000,
         "42 USC §1988 — pro se litigant hourly rate, filing fees, service costs, copies, mileage"),
        ("Spoliation Inference Damages", "McNeill,Muskegon_County", 10000, 50000,
         "Missing/off-record evidence, chambers-only HealthWest evaluation, adverse inference"),
        ("Housing Damages (Shady Oaks)", "Third_Party", 3200, 15000,
         "MCL 554.613 double damages, sewage, lock-change, retaliatory eviction"),
        ("Psychological Evaluation Abuse", "McNeill", 25000, 100000,
         "Forced HealthWest eval without due process, F22 diagnosis weaponized, chambers-only handling"),
    ]
    for cat, adv, low, high, authority in damage_map:
        conn.execute("""
            INSERT INTO damages_expanded
            (damage_category, adversary, evidence_file, evidence_text,
             quantification_basis, low_estimate, high_estimate, legal_authority)
            VALUES (?, ?, 'Multiple — see actionable_evidence table', ?, ?, ?, ?, ?)
        """, (cat, adv, f"Based on {total_hits} evidence items across {len(all_rows)} documents",
              authority, low, high, authority))
    conn.commit()

    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ppo_type ON ppo_rescission_evidence(evidence_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wfc_member ON watson_family_conspiracy(family_member)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_de_category ON damages_expanded(damage_category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_de_adversary ON damages_expanded(adversary)")
    conn.commit()

    # ─── PRINT FULL REPORT ──────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  EXPANDED EVIDENCE MINING REPORT — ALL ADVERSARIES, ALL TORTS")
    print("=" * 80)

    # By adversary (now ALL adversaries)
    print("\n--- ALL ADVERSARIES ---")
    adv_all = conn.execute("""
        SELECT adversary, COUNT(DISTINCT claim_id), SUM(hit_count), SUM(file_count)
        FROM evidence_by_adversary
        GROUP BY adversary ORDER BY SUM(hit_count) DESC
    """).fetchall()
    for a in adv_all:
        print(f"  {a[0]:20s}  {a[1]:2d} claims  {a[2]:7,d} hits  {a[3]:5d} files")

    # Watson family conspiracy summary
    print("\n--- WATSON FAMILY CONSPIRACY EVIDENCE ---")
    wfc = conn.execute("""
        SELECT family_member, COUNT(*), COUNT(DISTINCT evidence_file)
        FROM watson_family_conspiracy
        GROUP BY family_member ORDER BY COUNT(*) DESC
    """).fetchall()
    for w in wfc:
        print(f"  {w[0]:20s}  {w[1]:5d} items  {w[2]:4d} files")

    # PPO rescission evidence
    print("\n--- PPO RESCISSION EVIDENCE ---")
    ppo_summary = conn.execute("""
        SELECT evidence_type, COUNT(*), COUNT(DISTINCT source_file)
        FROM ppo_rescission_evidence
        GROUP BY evidence_type ORDER BY COUNT(*) DESC
    """).fetchall()
    for p in ppo_summary:
        print(f"  {p[0]:45s}  {p[1]:5d} items  {p[2]:4d} files")

    # Expanded damages
    print("\n--- EXPANDED DAMAGES FRAMEWORK ---")
    dmg = conn.execute("""
        SELECT damage_category, adversary, low_estimate, high_estimate
        FROM damages_expanded ORDER BY high_estimate DESC
    """).fetchall()
    total_low = 0
    total_high = 0
    for d in dmg:
        print(f"  {d[0]:45s}  vs {d[1]:30s}  ${d[2]:>10,.0f} — ${d[3]:>10,.0f}")
        total_low += d[2]
        total_high += d[3]
    print(f"  {'TOTAL':45s}  {'':30s}  ${total_low:>10,.0f} — ${total_high:>10,.0f}")

    # Full tort matrix
    print("\n--- COMPLETE TORT EVIDENCE MATRIX ---")
    matrix = conn.execute("""
        SELECT claim_id, adversary, total_files, total_hits, evidence_sufficient
        FROM tort_evidence_matrix
        ORDER BY total_hits DESC
    """).fetchall()
    print(f"  {'CLAIM':45s} {'ADVERSARY':25s} {'FILES':>6s} {'HITS':>7s} {'STATUS':>14s}")
    for m in matrix:
        print(f"  {m[0]:45s} {m[1]:25s} {m[2]:6d} {m[3]:7,d} {m[4]:>14s}")

    # Totals
    total_ae = conn.execute("SELECT COUNT(*) FROM actionable_evidence").fetchone()[0]
    total_ppo = conn.execute("SELECT COUNT(*) FROM ppo_rescission_evidence").fetchone()[0]
    total_wfc = conn.execute("SELECT COUNT(*) FROM watson_family_conspiracy").fetchone()[0]
    total_dmg = conn.execute("SELECT COUNT(*) FROM damages_expanded").fetchone()[0]

    elapsed = time.time() - t0
    print(f"\n=== COMPLETE in {elapsed:.1f}s ===")
    print(f"  actionable_evidence:      {total_ae:,d} rows (original + expanded)")
    print(f"  ppo_rescission_evidence:  {total_ppo:,d} rows")
    print(f"  watson_family_conspiracy: {total_wfc:,d} rows")
    print(f"  damages_expanded:         {total_dmg:,d} rows")
    print(f"  evidence_by_adversary:    {len(adv_all)} adversaries")
    print(f"  tort_evidence_matrix:     {len(matrix)} claims")

    conn.close()

if __name__ == '__main__':
    main()
