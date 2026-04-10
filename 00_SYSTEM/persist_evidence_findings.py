"""Persist high-value evidence findings to litigation_context.db."""
import sqlite3
from datetime import datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

# High-value un-ingested files discovered by agent
HIGH_VALUE_FILES = [
    # (path, size_mb, category, priority, description)
    (r"I:\02_EVIDENCE\Primary\05_EVIDENCE\fred\Archives\OneDrive_2_4-30-2025.zip", 12458.9, "ZIP_ARCHIVE", "CRITICAL", "Massive evidence package - 12.5 GB compressed"),
    (r"I:\02_EVIDENCE\Primary\05_EVIDENCE\fred\Organized_Litigation_Supreme\ZIP_Archives\FRED PRIME DOCUMENT & FILE INTEL.zip", 1408.8, "ZIP_ARCHIVE", "CRITICAL", "Consolidated evidence package"),
    (r"I:\02_EVIDENCE\Primary\05_EVIDENCE\fred\GitRepo\fredprime\FRED-PRIME\SHADYOAKS-EVIDENCE\motion for summary disposition shady oaks.zip", 1029.6, "ZIP_ARCHIVE", "HIGH", "Housing/civil case evidence"),
    (r"I:\Mostly custody stuff, very important.zip", 552.5, "ZIP_ARCHIVE", "HIGH", "User-labeled high-value custody evidence"),
    (r"C:\Users\andre\Desktop\original_PPO_B_S_Page_1[1].pdf", 172.0, "COURT_DOCUMENT", "CRITICAL", "Original PPO filing - custody/PPO evidence"),
    (r"C:\Users\andre\LitigationOS\01_FILINGS\EMERGENCY\FULL BENCHBOOK CONTEMPT RULES.pdf", 105.0, "LEGAL_REFERENCE", "HIGH", "Full benchbook contempt rules"),
    (r"C:\Users\andre\LitigationOS\07_PDF\HOA SHADY OAKS NEIGHBOR DOCUMENTS Copy.pdf", 83.9, "COURT_DOCUMENT", "HIGH", "Housing/civil case - Shady Oaks HOA"),
    (r"C:\Users\andre\LitigationOS\01_FILINGS\TRIAL_14TH\final custody judgement disrespectful wording by emily barnes_1_1.pdf", 69.7, "COURT_DOCUMENT", "CRITICAL", "Custody judgment - trial evidence"),
    (r"C:\Users\andre\LitigationOS\01_FILINGS\TRIAL_14TH\Custody_Parenting_ChildSupport_parenting time logs_20250312_041016.pdf", 48.6, "COURT_DOCUMENT", "HIGH", "Custody parenting time logs"),
    (r"I:\Court Ordered Judgment of Custody PT CS and FOC10 FOC10d FOC10.docx", 26.6, "COURT_DOCUMENT", "CRITICAL", "Primary custody judgment - DOCX"),
    (r"I:\Custody, PT and CS Trial Brief_20250107182537.docx", 20.8, "COURT_DOCUMENT", "HIGH", "Trial brief - DOCX"),
    (r"I:\clerks submitted ppo.docx", 9.8, "COURT_DOCUMENT", "HIGH", "PPO filing - clerk submitted"),
    (r"I:\terminateppoFILINGS_20250107182539.docx", 9.0, "COURT_DOCUMENT", "HIGH", "PPO termination filing"),
]

INGESTION_STATS = {
    "total_files_cataloged": 610220,
    "un_ingested_files": 525353,
    "un_ingested_gb": 194.35,
    "already_ingested": 84867,
    "zip_files_total": 2737,
    "zip_total_gb": 102.18,
    "pdf_un_ingested": 13303,
    "video_files": 289,
    "video_gb": 18.25,
    "email_files": 1068,  # 909 MSG + 159 EML
}

def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")

    # Create ingestion_priority table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_priority (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            size_mb REAL,
            category TEXT,
            priority TEXT,
            description TEXT,
            status TEXT DEFAULT 'PENDING',
            discovered_at TEXT DEFAULT (datetime('now')),
            ingested_at TEXT,
            UNIQUE(file_path)
        )
    """)

    # Insert high-value files
    inserted = 0
    for path, size, cat, pri, desc in HIGH_VALUE_FILES:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO ingestion_priority (file_path, size_mb, category, priority, description) VALUES (?, ?, ?, ?, ?)",
                (path, size, cat, pri, desc)
            )
            inserted += 1
        except Exception as e:
            print(f"  Skip {path}: {e}")

    # Create automation_campaign_stats table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS automation_campaign_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_name TEXT NOT NULL,
            stat_value REAL,
            measured_at TEXT DEFAULT (datetime('now')),
            UNIQUE(stat_name)
        )
    """)

    for name, val in INGESTION_STATS.items():
        conn.execute(
            "INSERT OR REPLACE INTO automation_campaign_stats (stat_name, stat_value) VALUES (?, ?)",
            (name, val)
        )

    conn.commit()

    # Verify
    total = conn.execute("SELECT COUNT(*) FROM ingestion_priority").fetchone()[0]
    stats = conn.execute("SELECT COUNT(*) FROM automation_campaign_stats").fetchone()[0]
    print(f"✅ Persisted {inserted} high-value files to ingestion_priority (total: {total})")
    print(f"✅ Persisted {stats} stats to automation_campaign_stats")

    # Show priorities
    print("\n📋 CRITICAL priority files:")
    for row in conn.execute("SELECT file_path, size_mb, description FROM ingestion_priority WHERE priority='CRITICAL' ORDER BY size_mb DESC"):
        print(f"  {row[2]}: {row[1]:.0f} MB — {row[0]}")

    conn.close()

if __name__ == "__main__":
    main()
