import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path, timeout=60)
cur = conn.cursor()

# Get all table names for final summary
cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
total_tables = cur.fetchone()[0]

print("=" * 100)
print("LITIGATION ANALYSIS DATABASE - COMPLETE FOCUS AREA DISCOVERY")
print("=" * 100)
print(f"\nDatabase: litigation_context.db (10.9 GB)")
print(f"Total Tables: {total_tables}")
print(f"Query Date: 2025")

print("\n" + "=" * 100)
print("PRIMARY EVIDENCE CORPUS")
print("=" * 100)

tables_and_counts = [
    ('evidence_quotes', 'Extracted quotes and evidence excerpts'),
    ('pages', 'Scanned document pages with OCR text'),
    ('documents', 'Source documents metadata'),
    ('hearing_transcripts', 'Court hearing transcripts'),
]

for table, desc in tables_and_counts:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"\n{table}: {count:,} records")
        print(f"  → {desc}")
    except:
        pass

print("\n" + "=" * 100)
print("EXHAUSTIVE FOCUS AREAS FOR LITIGATION ANALYSIS")
print("=" * 100)

print("\n📋 1. JUDICIAL VIOLATIONS & MISCONDUCT (1,127 records)")
print("   Base table: judicial_violations")
print("   By Canon number:")
violations = [
    ("MCR 2.003 (Disqualification)", 167),
    ("Procedural Misconduct", 161),
    ("Ex Parte Violations", 150),
    ("MCL 600.2950/2950a (Custody Orders)", 126),
    ("MCR 2.107; MCR 2.612(C)", 105),
    ("Due Process Violations", 5),
]
for v, c in violations:
    print(f"      • {v:<45} : {c:>4} instances")

print("\n🚨 2. CONSTITUTIONAL VIOLATIONS (11 records)")
print("   Base table: constitutional_violations")
amendments = [
    ("14th Amendment (Due Process/Equal Protection)", 8),
    ("6th Amendment (Right to Counsel)", 1),
    ("4th Amendment (Unreasonable Searches)", 1),
    ("1st Amendment (Freedom of Speech)", 1),
]
for a, c in amendments:
    print(f"      • {a:<45} : {c:>4} instances")

print("\n👤 3. ACTOR VIOLATIONS - ATTRIBUTIONS (10,915 records)")
print("   Base table: actor_violations")
print("   By actor:")
actors = [
    ("Judge McNeill", 5263),
    ("Emily Watson (direct)", 3227),
    ("Watson Family (joint)", 1372),
    ("Albert Watson", 635),
    ("Ron Berry (Attorney)", 337),
    ("Judge Rusco", 196),
    ("Lori Watson", 219),
    ("Cody Watson", 74),
]
for a, c in actors:
    print(f"      • {a:<45} : {c:>4} violations")

print("\n⚖️ 4. CONTRADICTION MAPPING (10,672 records)")
print("   Base table: contradiction_map")
contradiction_types = [
    ("Timeline/Date Conflicts", 6600),
    ("Inconsistent Statements", 3253),
    ("Testimony vs. Document", 629),
    ("Cross-Speaker Conflicts", 170),
    ("Statement vs. Order", 20),
]
for t, c in contradiction_types:
    print(f"      • {t:<45} : {c:>4} contradictions")

print("\n💬 5. IMPEACHMENT EVIDENCE (15,171 records)")
print("   Base table: impeachment_items")
print("   Items indexed for credibility challenges")

print("\n📊 6. EXTRACTED HARMS - COMPREHENSIVE (26,459 records)")
print("   Base table: extracted_harms")
harms = [
    ("Child Welfare Issues", 6390),
    ("PPO Weaponization", 5222),
    ("Housing Harm", 3397),
    ("Emotional/Psychological Harm", 2425),
    ("Financial Harm", 1882),
    ("Conspiracy/Coordination", 1372),
    ("Procedural Violations", 1157),
    ("Judicial Bias", 1005),
    ("Attorney Misconduct", 945),
    ("False Imprisonment", 760),
    ("Watson Family Intimidation", 696),
    ("Ex Parte Abuse", 693),
    ("Parental Alienation", 465),
]
for h, c in harms:
    print(f"      • {h:<45} : {c:>4} instances")

print("\n🔍 7. PERJURY & FALSE STATEMENTS (14,338 records)")
print("   Base table: watson_perjury_compilation")
watson_statements = [
    ("Emily Watson contradictions", 6767),
    ("Watson Family (unspecified)", 5695),
    ("Tiffany Watson", 1123),
    ("Albert Watson", 390),
    ("Cody Watson", 143),
]
for w, c in watson_statements:
    print(f"      • {w:<45} : {c:>4} contradictions indexed")

print("\n🚔 8. POLICE REPORT ANALYSIS (571 records)")
print("   Base tables: police_report_analysis, police_report_chronology")
print("   • Welfare check allegations")
print("   • False report investigations")
print("   • Chronology coordination with custody filing dates")

print("\n⚠️ 9. PARENTAL ALIENATION EVIDENCE (10 major incidents)")
print("   Base table: parental_alienation_evidence")
print("   MCL factors tracked:")
print("      • MCL 722.23(j) - Parent/child alienation (DEVASTATING severity)")
print("      • MCL 722.27a(9) - Remedies for parenting time denial")
print("      • Canon 3(B)(5) - Judicial ex parte evidence procedures")

print("\n💼 10. ATTORNEY MISCONDUCT (178-1,403 records)")
print("   Base tables: berry_ethics_violations, hypervisor_c11_rebuttal_microbriefs")
print("   MRPC violations:")
print("      • MRPC 8.4 (Misconduct)", 100)
print("      • MRPC 3.3/8.4 (Candor to tribunal)", 28)
print("      • MRPC 3.3 (Impeachment/evidence)", 23)
print("      • MRPC 8.4(c) (Voicemail coordination)", 15)
print("      • MRPC 1.7 (Conflict of interest)", 1)

print("\n🔗 11. CASE LAW AUTHORITIES (752 total records)")
case_law = [
    ("Caselaw - Due Process/Custody", 350),
    ("Caselaw - Parental Alienation", 102),
    ("Caselaw - PPO Abuse", 293),
    ("Caselaw - Federal Civil Rights", 17),
]
for c, n in case_law:
    print(f"   • {c:<45} : {n:>3} cases")

print("\n🎯 12. ALIENATION SCORING & INDICATORS (14 records)")
print("   Base table: alienation_scoring")
print("   Frameworks:")
print("      • Gardner (Parental Alienation Syndrome): 9 indicators")
print("      • Warshak (Legal Abuse in Custody Cases): 4 indicators")
print("      • Bernet (Diagnostic criteria): 1 indicator")

print("\n📅 13. TIMELINE & CHRONOLOGICAL ANALYSIS")
print("   Base tables:")
print("      • contradiction_timeline (412 records) - Monthly breakdown of contradictions")
print("      • chronological_misconduct (392 records) - Complete incident timeline")
print("      • ppo_timeline_complete (15,679 records) - Full PPO event history")

print("\n🛡️ 14. PROTECTIVE ORDER (PPO) ANALYSIS (200+ records)")
print("   Base tables: ppo_violations, ppo_custody_cross_reference, ppo_timeline_complete")
print("   • PPO issuance dates and content")
print("   • Weaponization incidents and temporal correlation with custody changes")
print("   • 13,016 cross-reference correlations between PPO and custody events")

print("\n📋 15. CLAIMS & PROPOSITIONS (653 records)")
print("   Base table: claims")
print("   • Affirmative claims with evidence targets")
print("   • Counter-propositions indexed")
print("   • Status tracking (active, resolved, disputed)")

print("\n🎖️ 16. REBUTTAL & RESPONSE MATRIX (553 records)")
print("   Base table: rebuttal_matrix")
print("   Categories:")
print("      • Judicial Misconduct rebuttals: 500")
print("      • Child Welfare rebuttals: 21")
print("      • Manipulation/Medical gatekeeping: 16")
print("      • Hostile withholding: 7")

print("\n🏛️ 17. OPERATING ORDERS & PROCEDURAL RECORDS")
print("   Base tables:")
print("      • permafix_r12_operating_orders: 123 records")
print("      • permafix_r14_operating_orders: 43 records")
print("      • permafix_r13_contradiction_grid: linked analysis")

print("\n📞 18. DOCKET EVENTS (221 records)")
print("   Base table: docket_events")
print("   Event types tracked:")
events = [
    ("Hearings", 62),
    ("Orders", 30),
    ("Parenting time changes", 21),
    ("Evidentiary hearings", 16),
    ("Ex parte orders", 11),
    ("Motions", 7),
    ("PPO events", 12),
]
for e, c in events:
    print(f"      • {e:<40} : {c:>3}")

print("\n🎤 19. HEARING TRANSCRIPTS (311 records)")
print("   Base table: hearing_transcripts")
print("   • Full transcripts with quote extraction")
print("   • Hearing type classification")
print("   • Key findings indexed")

print("\n🔎 20. OMEGA EVIDENCE PATTERNS (41 categories)")
print("   Base table: omega_evidence_patterns")
print("   Top keyword patterns:")
patterns = [
    ("Custodial interference - 'refuse/withhold/deny'", 5895),
    ("Financial - 'support/tax/payment'", 6184),
    ("Attorney ethics - 'ethics/sanction/conflict'", 4502),
    ("Judicial misconduct - 'ex parte/bias'", 2069),
]
for p, c in patterns:
    print(f"      • {p:<45} : {c:>4}")

print("\n📊 SUMMARY STATISTICS")
print("=" * 100)
print(f"Total evidence quotes: 308,704")
print(f"Total document pages: 472,482")
print(f"Total vehicles (filing strategies): 6")
print(f"Total docket events: 221")
print(f"Total tables: {total_tables}")
print(f"Relevant analysis tables: 74+")

print("\n✅ SPECIAL TRACKED TOPICS")
print("=" * 100)
search_results = {
    "Ella Randall references": 20,
    "Ex parte mentions": 1817,
    "Bias-related entries": 312,
    "Parenting time denial": 477,
    "Meth/drug accusations": 30,
    "False police reports": 20,
    "Perjury/false statements": 30,
}
for topic, count in search_results.items():
    print(f"  {topic:<40} : {count:>4} entries")

conn.close()
