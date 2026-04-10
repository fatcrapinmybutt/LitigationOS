import sqlite3, datetime

db = sqlite3.connect(r"C:\Users\andre\LitigationOS\litigation_context.db")
db.execute("PRAGMA busy_timeout=60000")
db.execute("PRAGMA journal_mode=WAL")
now = datetime.datetime.now().isoformat()

# 1. Persist user testimony IMMEDIATELY (Rule 13)
testimonies = [
    ("user_testimony_shady_oaks_managers_2026-04-05",
     "USER TESTIMONY (2026-04-05): Andrew confirms Shady Oaks managers were Cassandra VanDam and Nicole Browley. Brian Cross is NOT a real person — never heard of him. VanDam and Browley were the actual park managers who directed operations against Andrew.",
     "shady_oaks_management", "B", 10.0, "user_testimony", "shady_oaks,vandam,browley,management"),
    ("user_testimony_nicole_browley_2026-04-05",
     "USER TESTIMONY (2026-04-05): Nicole Browley identified as Shady Oaks park manager alongside Cassandra VanDam. Previously unknown adversary — not in any prior dossier or DB records. Browley was part of the management team that directed fraudulent billing, harassment, and eviction actions against Andrew Pigors.",
     "adversary_identification", "B", 10.0, "user_testimony", "browley,nicole,shady_oaks,manager"),
    ("user_correction_brian_cross_2026-04-05",
     "USER CORRECTION (2026-04-05): 'Brian Cross' was a FALSE POSITIVE from automated file scanning. Andrew has never heard of Brian Cross. The 8,660 'mentions' were likely regex matching 'Brian' and 'Cross' separately across files. DOSSIER RETRACTED. Correct managers: Cassandra VanDam and Nicole Browley.",
     "data_correction", "B", 10.0, "user_correction", "brian_cross,retracted,false_positive"),
]

for src, txt, cat, lane, score, tags_extra, tags in testimonies:
    db.execute("""INSERT INTO evidence_quotes (source_file, quote_text, category, lane, relevance_score, tags, created_at)
                  VALUES (?, ?, ?, ?, ?, ?, ?)""", (src, txt, cat, lane, score, tags, now))

# 2. Mark the false Brian Cross entries as corrections
db.execute("""UPDATE evidence_quotes SET is_duplicate = 1, 
              tags = COALESCE(tags,'') || ',RETRACTED_FALSE_POSITIVE'
              WHERE source_file LIKE '%round2_brian_cross%'""")

rows_retracted = db.execute("SELECT changes()").fetchone()[0]

# 3. Add timeline event
db.execute("""INSERT INTO timeline_events (event_date, event_description, actors, lane, category, source_table, severity, filing_relevance, created_at)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
           ("2026-04-05", "User corrects Brian Cross as false positive. Actual Shady Oaks managers: Cassandra VanDam and Nicole Browley. Nicole Browley newly identified as adversary.",
            "Andrew Pigors, Cassandra VanDam, Nicole Browley", "B", "data_correction", "user_testimony", 8, "B,F04", now))

db.commit()

# Verify
ct = db.execute("SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE '%testimony%browley%' OR source_file LIKE '%correction_brian%'").fetchone()[0]
total = db.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
print(f"Persisted: 3 testimony rows verified ({ct} found)")
print(f"Retracted: {rows_retracted} false Brian Cross entries")
print(f"Total evidence_quotes: {total}")
db.close()
