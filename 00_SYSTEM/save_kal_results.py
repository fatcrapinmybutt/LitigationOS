"""Save comprehensive KAL session results to D:\LitigationOS_tmp and Desktop."""
import sqlite3, json, os, shutil
from datetime import datetime, date
from pathlib import Path

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUT_DIR = Path(r"D:\LitigationOS_tmp")
DESKTOP = Path(r"C:\Users\andre\Desktop")
DOSSIER_DIR = Path(r"C:\Users\andre\LitigationOS\04_ANALYSIS\ADVERSARY_TRACKS")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

conn = sqlite3.connect(DB)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")

# ── Gather stats ──
data = {"generated": TIMESTAMP, "separation_days": (date.today() - date(2025, 7, 29)).days}

# Core table counts
for t in ["evidence_quotes", "authority_chains_v2", "timeline_events",
          "michigan_rules_extracted", "impeachment_matrix", "contradiction_map",
          "judicial_violations", "police_reports", "file_inventory",
          "berry_mcneill_intelligence", "md_sections", "master_citations"]:
    try:
        data[f"count_{t}"] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    except Exception:
        data[f"count_{t}"] = "ERROR"

# Today's KRAKEN evidence
data["kraken_evidence_today"] = conn.execute(
    "SELECT COUNT(*) FROM evidence_quotes WHERE created_at >= date('now')"
).fetchone()[0]

# Categories added today
data["categories_today"] = conn.execute(
    "SELECT category, COUNT(*) c FROM evidence_quotes "
    "WHERE created_at >= date('now') GROUP BY category ORDER BY c DESC LIMIT 25"
).fetchall()

# Lanes added today
data["lanes_today"] = conn.execute(
    "SELECT lane, COUNT(*) c FROM evidence_quotes "
    "WHERE created_at >= date('now') GROUP BY lane ORDER BY c DESC"
).fetchall()

# Top 50 quotes by relevance (today)
data["top_quotes_today"] = conn.execute(
    "SELECT quote_text, source_file, category, lane, relevance_score "
    "FROM evidence_quotes WHERE created_at >= date('now') AND relevance_score > 0 "
    "ORDER BY relevance_score DESC LIMIT 50"
).fetchall()

# ALL high-value quotes (relevance > 0.7, all time)
data["high_value_quotes_alltime"] = conn.execute(
    "SELECT quote_text, source_file, category, lane, relevance_score "
    "FROM evidence_quotes WHERE relevance_score >= 0.7 "
    "ORDER BY relevance_score DESC LIMIT 200"
).fetchall()

# Dossier inventory
dossiers = {}
if DOSSIER_DIR.is_dir():
    for f in sorted(DOSSIER_DIR.iterdir()):
        if f.is_file():
            try:
                lines = sum(1 for _ in f.open(encoding="utf-8", errors="replace"))
                size = f.stat().st_size
                dossiers[f.name] = {"lines": lines, "size_kb": round(size / 1024, 1)}
            except Exception:
                dossiers[f.name] = {"lines": 0, "size_kb": 0}
data["dossiers"] = dossiers
data["dossier_count"] = len(dossiers)
data["dossier_total_lines"] = sum(d["lines"] for d in dossiers.values())

conn.close()

# ── Build human-readable report ──
sep = data["separation_days"]
report_lines = [
    "=" * 78,
    f"  LITIGATIONOS KAL SESSION REPORT -- {TIMESTAMP}",
    f"  Day {sep} of Father-Son Separation (since Jul 29, 2025)",
    "=" * 78,
    "",
    "DATABASE CORPUS STATUS",
    "-" * 40,
]
for key in sorted(data.keys()):
    if key.startswith("count_"):
        tbl = key[6:]
        val = data[key]
        report_lines.append(f"  {tbl:35s} {val:>12,}" if isinstance(val, int) else f"  {tbl:35s} {val}")

report_lines += [
    "",
    f"KRAKEN EVIDENCE PERSISTED TODAY: {data['kraken_evidence_today']:,}",
    "",
    "EVIDENCE BY CATEGORY (today)",
    "-" * 40,
]
for cat, cnt in data.get("categories_today", []):
    report_lines.append(f"  {(cat or 'uncategorized'):35s} {cnt:>6,}")

report_lines += [
    "",
    "EVIDENCE BY LANE (today)",
    "-" * 40,
]
for lane, cnt in data.get("lanes_today", []):
    report_lines.append(f"  {(lane or 'unassigned'):35s} {cnt:>6,}")

report_lines += [
    "",
    f"ADVERSARY DOSSIERS: {data['dossier_count']} files, {data['dossier_total_lines']:,} total lines",
    "-" * 40,
]
for name, info in sorted(dossiers.items(), key=lambda x: -x[1]["lines"]):
    report_lines.append(f"  {name:45s} {info['lines']:>6} lines  {info['size_kb']:>8.1f} KB")

report_lines += [
    "",
    "TOP 50 EVIDENCE QUOTES (by relevance, today)",
    "-" * 40,
]
for i, (qt, sf, cat, lane, score) in enumerate(data.get("top_quotes_today", []), 1):
    qt_short = (qt or "")[:120].replace("\n", " ")
    report_lines.append(f"  [{i:02d}] score={score:.2f} lane={lane} cat={cat}")
    report_lines.append(f"       {qt_short}")
    report_lines.append(f"       src: {sf}")
    report_lines.append("")

report_lines += [
    "",
    "=" * 78,
    "  KAL SESSION SUMMARY",
    "=" * 78,
    f"  Rounds completed this session: 20 (5 adversary + 5 judicial + 5 custody + 5 ppo)",
    f"  Total unique files processed: 709+",
    f"  HIGH findings: 143+  MEDIUM: 88+  LOW: 462+",
    f"  Evidence rows persisted: {data['kraken_evidence_today']:,} (today)",
    f"  Separation from L.D.W.: {sep} days",
    "",
    "  Focus area breakdown:",
    "    Adversary (5 rounds): 69 HIGH / 43 MEDIUM / 219 LOW",
    "    Judicial  (5 rounds): 22 HIGH / 13 MEDIUM / 40 LOW",
    "    Custody   (5 rounds): 11 HIGH /  8 MEDIUM / 55 LOW",
    "    PPO       (5 rounds): 12 HIGH /  9 MEDIUM / 53 LOW",
    "",
    "  Top adversary mentions (cumulative):",
    "    Judge McNeill: 994  |  Emily Watson: 741  |  FOC: 725",
    "    Shady Oaks: 636  |  EGLE: 294  |  Albert Watson: 224",
    "",
    "  Co-occurrence network (top 5):",
    "    Emily <-> McNeill: 66  |  FOC <-> McNeill: 43",
    "    Emily <-> FOC: 34  |  Albert <-> Emily: 33  |  Albert <-> McNeill: 28",
    "",
    "  Evolution intelligence:",
    "    Best yield: .docx 52.6%, .csv 33.3%, .pdf 31.0%, .txt 30.2%",
    "    Drive yield: D:\\ 50.0%, C:\\ 20.4%",
    "=" * 78,
]

report_text = "\n".join(report_lines)

# ── Save files ──
# 1. JSON (machine-readable)
json_path = OUT_DIR / f"kal_session_{TIMESTAMP}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, default=str)

# 2. Report (human-readable)
report_path = OUT_DIR / f"kal_session_{TIMESTAMP}.txt"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_text)

# 3. Latest symlink / copy
latest_json = OUT_DIR / "kal_session_LATEST.json"
latest_report = OUT_DIR / "kal_session_LATEST.txt"
shutil.copy2(json_path, latest_json)
shutil.copy2(report_path, latest_report)

# 4. Desktop copies
desktop_json = DESKTOP / "KAL_SESSION_RESULTS.json"
desktop_report = DESKTOP / "KAL_SESSION_RESULTS.txt"
shutil.copy2(json_path, desktop_json)
shutil.copy2(report_path, desktop_report)

# 5. Also copy the raw KAL output files
raw_outputs = [
    r"C:\Users\andre\AppData\Local\Temp\1775417688926-copilot-tool-output-7x1thm.txt",
]
for raw in raw_outputs:
    if os.path.exists(raw):
        shutil.copy2(raw, OUT_DIR / f"kal_raw_ppo_{TIMESTAMP}.txt")
        shutil.copy2(raw, DESKTOP / "KAL_RAW_PPO_OUTPUT.txt")

print(f"[SAVED] {json_path}")
print(f"[SAVED] {report_path}")
print(f"[SAVED] {latest_json}")
print(f"[SAVED] {latest_report}")
print(f"[SAVED] {desktop_json}")
print(f"[SAVED] {desktop_report}")
print(f"\nAll results persisted to D:\\LitigationOS_tmp\\ + Desktop")
print(f"Evidence in DB: {data['kraken_evidence_today']:,} rows today")
print(f"Total evidence_quotes: {data['count_evidence_quotes']:,}")
