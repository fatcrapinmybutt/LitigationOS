"""
WizTree Full Drive Audit — DuckDB Analysis of 2.35M files across all drives.
Produces comprehensive breakdown by drive, extension, size tier, age, and anomalies.
"""
import duckdb
import json
import os
import sys
from pathlib import Path
from datetime import datetime

WIZTREE = r"C:\Users\andre\Desktop\WizTree_20260408181538"
REPORT_OUT = r"C:\Users\andre\LitigationOS\04_ANALYSIS\WIZTREE_DRIVE_AUDIT.md"
JSON_OUT = r"C:\Users\andre\LitigationOS\04_ANALYSIS\wiztree_audit_data.json"

con = duckdb.connect(":memory:")

print("[1/12] Loading WizTree CSV into DuckDB...")

# First discover the actual column count
test = con.execute(f"""
SELECT * FROM read_csv('{WIZTREE}',
    header=false,
    skip=2,
    ignore_errors=true,
    all_varchar=true,
    max_line_size=1048576
) LIMIT 1
""").fetchone()
ncols = len(test)
col_names = [f"column{i:02d}" for i in range(ncols)]
print(f"   Detected {ncols} columns: {', '.join(col_names[:5])}...{', '.join(col_names[-3:])}")

con.execute(f"""
CREATE TABLE wiz AS
SELECT
    column00 AS file_path,
    TRY_CAST(column01 AS BIGINT) AS size_bytes,
    TRY_CAST(column02 AS BIGINT) AS allocated_bytes,
    column03 AS modified,
    column04 AS attributes,
    TRY_CAST(column05 AS INT) AS files_count,
    TRY_CAST(column06 AS INT) AS folders_count,
    {'column13 AS drive,' if ncols > 13 else "'?' AS drive,"}
    {'column14 AS folder_name,' if ncols > 14 else "'' AS folder_name,"}
    {'column15 AS file_name,' if ncols > 15 else "'' AS file_name,"}
    {'column16 AS file_ext,' if ncols > 16 else "'' AS file_ext,"}
    {'TRY_CAST(column18 AS BIGINT) AS drive_capacity,' if ncols > 18 else '0 AS drive_capacity,'}
    {'TRY_CAST(column19 AS BIGINT) AS free_space,' if ncols > 19 else '0 AS free_space,'}
    {'TRY_CAST(column20 AS BIGINT) AS used_space' if ncols > 20 else '0 AS used_space'}
FROM read_csv('{WIZTREE}',
    header=false,
    skip=2,
    ignore_errors=true,
    all_varchar=true,
    max_line_size=1048576
)
WHERE column00 IS NOT NULL AND column00 != ''
""")

total_rows = con.execute("SELECT COUNT(*) FROM wiz").fetchone()[0]
print(f"   Loaded {total_rows:,} rows")

report_lines = []
audit_data = {}

def section(title):
    report_lines.append(f"\n## {title}\n")
    print(f"   > {title}")

def table_header(cols):
    report_lines.append("| " + " | ".join(cols) + " |")
    report_lines.append("| " + " | ".join(["---"] * len(cols)) + " |")

def table_row(vals):
    report_lines.append("| " + " | ".join(str(v) for v in vals) + " |")

def fmt_bytes(b):
    if b is None: return "0 B"
    b = int(b)
    if b >= 1_099_511_627_776: return f"{b/1_099_511_627_776:.2f} TB"
    if b >= 1_073_741_824: return f"{b/1_073_741_824:.2f} GB"
    if b >= 1_048_576: return f"{b/1_048_576:.1f} MB"
    if b >= 1024: return f"{b/1024:.0f} KB"
    return f"{b} B"

report_lines.append("# 🔍 WIZTREE FULL DRIVE AUDIT")
report_lines.append(f"\n> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append(f"> Source: WizTree 4.31 export — **{total_rows:,} files** across all drives\n")

# ═══════════════════════════════════════════════════════════════
# 1. DRIVE SUMMARY
# ═══════════════════════════════════════════════════════════════
print("[2/12] Drive summary...")
section("1. Drive Summary")

rows = con.execute("""
SELECT
    drive,
    COUNT(*) AS file_count,
    SUM(size_bytes) AS total_size,
    MAX(drive_capacity) AS capacity,
    MAX(free_space) AS free,
    MAX(used_space) AS used,
    ROUND(100.0 * MAX(used_space) / NULLIF(MAX(drive_capacity), 0), 1) AS pct_used
FROM wiz
WHERE drive IS NOT NULL AND drive != ''
GROUP BY drive
ORDER BY total_size DESC
""").fetchall()

table_header(["Drive", "Files", "Total Size", "Capacity", "Free", "Used", "% Used"])
drive_data = []
for r in rows:
    table_row([r[0], f"{r[1]:,}", fmt_bytes(r[2]), fmt_bytes(r[3]), fmt_bytes(r[4]), fmt_bytes(r[5]), f"{r[6]}%" if r[6] else "?"])
    drive_data.append({"drive": r[0], "files": r[1], "total_size": int(r[2] or 0), "capacity": int(r[3] or 0), "free": int(r[4] or 0)})
audit_data["drives"] = drive_data

# ═══════════════════════════════════════════════════════════════
# 2. TOP 50 LARGEST FILES
# ═══════════════════════════════════════════════════════════════
print("[3/12] Top 50 largest files...")
section("2. Top 50 Largest Files")

rows = con.execute("""
SELECT file_path, size_bytes, file_ext, drive
FROM wiz
WHERE size_bytes > 0
ORDER BY size_bytes DESC
LIMIT 50
""").fetchall()

table_header(["#", "File", "Size", "Ext", "Drive"])
top_files = []
for i, r in enumerate(rows, 1):
    path_short = r[0][-80:] if len(r[0]) > 80 else r[0]
    table_row([i, f"`{path_short}`", fmt_bytes(r[1]), r[2] or "—", r[3]])
    top_files.append({"path": r[0], "size": int(r[1] or 0), "ext": r[2]})
audit_data["top50_files"] = top_files

# ═══════════════════════════════════════════════════════════════
# 3. FILE EXTENSION BREAKDOWN (top 40)
# ═══════════════════════════════════════════════════════════════
print("[4/12] Extension breakdown...")
section("3. File Extension Breakdown (Top 40 by Total Size)")

rows = con.execute("""
SELECT
    COALESCE(LOWER(file_ext), '(none)') AS ext,
    COUNT(*) AS cnt,
    SUM(size_bytes) AS total,
    ROUND(AVG(size_bytes), 0) AS avg_size,
    MAX(size_bytes) AS max_size
FROM wiz
WHERE size_bytes > 0
GROUP BY LOWER(file_ext)
ORDER BY total DESC
LIMIT 40
""").fetchall()

table_header(["Extension", "Count", "Total Size", "Avg Size", "Max Size"])
ext_data = []
for r in rows:
    table_row([r[0], f"{r[1]:,}", fmt_bytes(r[2]), fmt_bytes(r[3]), fmt_bytes(r[4])])
    ext_data.append({"ext": r[0], "count": r[1], "total": int(r[2] or 0)})
audit_data["extensions"] = ext_data

# ═══════════════════════════════════════════════════════════════
# 4. SIZE TIER DISTRIBUTION
# ═══════════════════════════════════════════════════════════════
print("[5/12] Size tier distribution...")
section("4. File Size Distribution")

rows = con.execute("""
SELECT
    CASE
        WHEN size_bytes >= 1073741824 THEN '1 GB+'
        WHEN size_bytes >= 104857600 THEN '100 MB - 1 GB'
        WHEN size_bytes >= 10485760 THEN '10 MB - 100 MB'
        WHEN size_bytes >= 1048576 THEN '1 MB - 10 MB'
        WHEN size_bytes >= 102400 THEN '100 KB - 1 MB'
        WHEN size_bytes >= 10240 THEN '10 KB - 100 KB'
        WHEN size_bytes >= 1024 THEN '1 KB - 10 KB'
        ELSE '< 1 KB'
    END AS tier,
    COUNT(*) AS cnt,
    SUM(size_bytes) AS total,
    CASE
        WHEN size_bytes >= 1073741824 THEN 8
        WHEN size_bytes >= 104857600 THEN 7
        WHEN size_bytes >= 10485760 THEN 6
        WHEN size_bytes >= 1048576 THEN 5
        WHEN size_bytes >= 102400 THEN 4
        WHEN size_bytes >= 10240 THEN 3
        WHEN size_bytes >= 1024 THEN 2
        ELSE 1
    END AS sort_key
FROM wiz
WHERE size_bytes > 0
GROUP BY tier, sort_key
ORDER BY sort_key DESC
""").fetchall()

table_header(["Size Tier", "File Count", "Total Size", "% of Files"])
for r in rows:
    pct = round(100.0 * r[1] / total_rows, 1)
    table_row([r[0], f"{r[1]:,}", fmt_bytes(r[2]), f"{pct}%"])

# ═══════════════════════════════════════════════════════════════
# 5. EXTENSION × DRIVE MATRIX
# ═══════════════════════════════════════════════════════════════
print("[6/12] Extension × Drive matrix...")
section("5. Extension × Drive Matrix (Top 15 Extensions)")

rows = con.execute("""
WITH top_ext AS (
    SELECT COALESCE(LOWER(file_ext), '(none)') AS ext
    FROM wiz WHERE size_bytes > 0
    GROUP BY COALESCE(LOWER(file_ext), '(none)') ORDER BY SUM(size_bytes) DESC LIMIT 15
)
SELECT
    COALESCE(LOWER(w.file_ext), '(none)') AS ext,
    w.drive,
    COUNT(*) AS cnt,
    SUM(w.size_bytes) AS total
FROM wiz w
JOIN top_ext t ON COALESCE(LOWER(w.file_ext), '(none)') = t.ext
WHERE w.size_bytes > 0
GROUP BY COALESCE(LOWER(w.file_ext), '(none)'), w.drive
ORDER BY COALESCE(LOWER(w.file_ext), '(none)'), total DESC
""").fetchall()

# Pivot manually
from collections import defaultdict
pivot = defaultdict(lambda: defaultdict(lambda: (0, 0)))
all_drives_set = set()
for r in rows:
    pivot[r[0]][r[1]] = (r[2], r[3])
    all_drives_set.add(r[1])
drives_sorted = sorted(all_drives_set)

table_header(["Extension"] + [f"{d}" for d in drives_sorted])
for ext in sorted(pivot.keys()):
    vals = []
    for d in drives_sorted:
        cnt, total = pivot[ext].get(d, (0, 0))
        if cnt > 0:
            vals.append(f"{cnt:,} ({fmt_bytes(total)})")
        else:
            vals.append("—")
    table_row([ext] + vals)

# ═══════════════════════════════════════════════════════════════
# 6. DUPLICATE DB ANALYSIS
# ═══════════════════════════════════════════════════════════════
print("[7/12] Duplicate DB analysis...")
section("6. Database Files (.db) — Duplicate & Space Analysis")

rows = con.execute("""
SELECT file_path, size_bytes, drive, file_name
FROM wiz
WHERE LOWER(file_ext) = 'db'
AND size_bytes > 1048576
ORDER BY size_bytes DESC
LIMIT 60
""").fetchall()

table_header(["Database", "Size", "Drive", "Path"])
db_total = 0
for r in rows:
    path_short = r[0][-90:] if len(r[0]) > 90 else r[0]
    table_row([r[3], fmt_bytes(r[1]), r[2], f"`{path_short}`"])
    db_total += r[1]
report_lines.append(f"\n**Total DB space (top 60): {fmt_bytes(db_total)}**")

# ═══════════════════════════════════════════════════════════════
# 7. CHK FILES (filesystem recovery)
# ═══════════════════════════════════════════════════════════════
print("[8/12] CHK file analysis...")
section("7. Filesystem Recovery Files (.CHK)")

rows = con.execute("""
SELECT
    drive,
    folder_name,
    COUNT(*) AS cnt,
    SUM(size_bytes) AS total
FROM wiz
WHERE LOWER(file_ext) = 'chk'
GROUP BY drive, folder_name
ORDER BY total DESC
LIMIT 20
""").fetchall()

table_header(["Drive", "Folder", "Files", "Total Size"])
chk_total = 0
for r in rows:
    table_row([r[0], r[1], f"{r[2]:,}", fmt_bytes(r[3])])
    chk_total += r[3]
report_lines.append(f"\n**Total CHK space: {fmt_bytes(chk_total)}** — filesystem recovery fragments, likely safe to delete after inspection")

# ═══════════════════════════════════════════════════════════════
# 8. GIT OBJECTS ANALYSIS
# ═══════════════════════════════════════════════════════════════
print("[9/12] Git objects analysis...")
section("8. Git Objects & Pack Files")

rows = con.execute("""
SELECT file_path, size_bytes, file_ext
FROM wiz
WHERE file_path LIKE '%\\.git\\%'
AND size_bytes > 10485760
ORDER BY size_bytes DESC
LIMIT 30
""").fetchall()

table_header(["File", "Size"])
git_total = 0
for r in rows:
    path_short = r[0].replace("C:\\Users\\andre\\LitigationOS\\", "")
    table_row([f"`{path_short}`", fmt_bytes(r[1])])
    git_total += r[1]
report_lines.append(f"\n**Total large git objects (>10MB): {fmt_bytes(git_total)}**")

# ═══════════════════════════════════════════════════════════════
# 9. C: DRIVE SPACE BREAKDOWN (Critical — SSD tight)
# ═══════════════════════════════════════════════════════════════
print("[10/12] C: drive detailed breakdown...")
section("9. C: Drive Detailed Breakdown (SSD — Space Critical)")

rows = con.execute("""
SELECT
    CASE
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\.git%' THEN '.git (repo objects)'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\06_DATA%' THEN '06_DATA'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\00_SYSTEM%' THEN '00_SYSTEM'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\pytools_venv%' THEN 'pytools_venv'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\.agents%' THEN '.agents'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\01_EVIDENCE%' THEN '01_EVIDENCE'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\09_REFERENCE%' THEN '09_REFERENCE'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\11_ARCHIVES%' THEN '11_ARCHIVES'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\12_WORKSPACE%' THEN '12_WORKSPACE'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\04_ANALYSIS%' THEN '04_ANALYSIS'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\05_FILINGS%' THEN '05_FILINGS'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\08_MEDIA%' THEN '08_MEDIA'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\02_AUTHORITY%' THEN '02_AUTHORITY'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\03_COURT%' THEN '03_COURT'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\07_CODE%' THEN '07_CODE'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS\\10_EXTERNAL%' THEN '10_EXTERNAL'
        WHEN folder_name LIKE 'Users\\andre\\LitigationOS%' THEN 'LitigationOS (other)'
        WHEN folder_name LIKE 'Users\\andre\\Desktop%' THEN 'Desktop'
        WHEN folder_name LIKE 'Users\\andre\\AppData%' THEN 'AppData'
        WHEN folder_name LIKE 'Users\\andre\\.copilot%' THEN '.copilot'
        WHEN folder_name LIKE 'Users\\andre%' THEN 'User Home (other)'
        WHEN folder_name LIKE 'Windows%' THEN 'Windows'
        WHEN folder_name LIKE 'Program Files%' OR folder_name LIKE 'Program Files (x86)%' THEN 'Program Files'
        WHEN folder_name LIKE 'ProgramData%' THEN 'ProgramData'
        WHEN folder_name = '' THEN '(root files)'
        ELSE 'Other'
    END AS category,
    COUNT(*) AS file_count,
    SUM(size_bytes) AS total_size
FROM wiz
WHERE drive = 'C:'
AND size_bytes > 0
GROUP BY category
ORDER BY total_size DESC
""").fetchall()

table_header(["Category", "Files", "Size", "% of C:"])
c_total = sum(r[2] for r in rows)
for r in rows:
    pct = round(100.0 * r[2] / c_total, 1) if c_total > 0 else 0
    table_row([r[0], f"{r[1]:,}", fmt_bytes(r[2]), f"{pct}%"])
report_lines.append(f"\n**C: drive total indexed: {fmt_bytes(c_total)}**")

# ═══════════════════════════════════════════════════════════════
# 10. EVIDENCE FILES INVENTORY
# ═══════════════════════════════════════════════════════════════
print("[11/12] Evidence file inventory...")
section("10. Evidence-Relevant Files by Type & Drive")

rows = con.execute("""
SELECT
    drive,
    LOWER(file_ext) AS ext,
    COUNT(*) AS cnt,
    SUM(size_bytes) AS total
FROM wiz
WHERE LOWER(file_ext) IN ('pdf', 'docx', 'doc', 'txt', 'csv', 'json', 'jsonl', 'xlsx', 'xls', 'msg', 'eml', 'html', 'htm', 'png', 'jpg', 'jpeg', 'mp3', 'mp4', 'wav', 'mov', 'avi', 'zip', 'rar', '7z')
AND size_bytes > 0
GROUP BY drive, ext
ORDER BY drive, total DESC
""").fetchall()

current_drive = None
for r in rows:
    if r[0] != current_drive:
        current_drive = r[0]
        report_lines.append(f"\n### {current_drive}")
        table_header(["Extension", "Count", "Total Size"])
    table_row([r[1], f"{r[2]:,}", fmt_bytes(r[3])])

# ═══════════════════════════════════════════════════════════════
# 11. SPACE RECOVERY OPPORTUNITIES
# ═══════════════════════════════════════════════════════════════
print("[12/12] Space recovery analysis...")
section("11. SPACE RECOVERY OPPORTUNITIES")

# C: drive recoverable
c_git = con.execute("SELECT SUM(size_bytes) FROM wiz WHERE drive='C:' AND file_path LIKE '%\\.git\\%'").fetchone()[0] or 0
c_hiber = con.execute("SELECT SUM(size_bytes) FROM wiz WHERE drive='C:' AND LOWER(file_name)='hiberfil' AND LOWER(file_ext)='sys'").fetchone()[0] or 0
c_page = con.execute("SELECT SUM(size_bytes) FROM wiz WHERE drive='C:' AND LOWER(file_name)='pagefile' AND LOWER(file_ext)='sys'").fetchone()[0] or 0
c_wedb = con.execute("SELECT SUM(size_bytes) FROM wiz WHERE drive='C:' AND LOWER(file_ext)='edb'").fetchone()[0] or 0
c_pyenv = con.execute("SELECT SUM(size_bytes) FROM wiz WHERE drive='C:' AND file_path LIKE '%pytools_venv%'").fetchone()[0] or 0
c_pip = con.execute("SELECT SUM(size_bytes) FROM wiz WHERE drive='C:' AND file_path LIKE '%pip%cache%'").fetchone()[0] or 0
c_temp = con.execute("SELECT SUM(size_bytes) FROM wiz WHERE drive='C:' AND (file_path LIKE '%\\Temp\\%' OR file_path LIKE '%\\tmp\\%')").fetchone()[0] or 0

report_lines.append("### C: Drive Recovery (SSD — highest priority)")
table_header(["Item", "Size", "Action", "Risk"])
table_row([".git pack files", fmt_bytes(c_git), "`git gc --aggressive`", "⚠️ Low — keeps history"])
table_row(["hiberfil.sys", fmt_bytes(c_hiber), "`powercfg -h off`", "⚠️ Disables hibernation"])
table_row(["pagefile.sys", fmt_bytes(c_page), "Reduce size in System Settings", "⚠️ May affect performance"])
table_row(["Windows.edb (Search)", fmt_bytes(c_wedb), "Rebuild Windows Search index", "🟢 Safe"])
table_row(["pytools_venv", fmt_bytes(c_pyenv), "Recreate if needed", "🟢 Safe"])
table_row(["pip cache", fmt_bytes(c_pip), "`pip cache purge`", "🟢 Safe"])
table_row(["Temp files", fmt_bytes(c_temp), "Disk Cleanup utility", "🟢 Safe"])

c_recoverable = c_git + c_hiber + c_wedb + c_pyenv + c_pip + c_temp
report_lines.append(f"\n**C: Potential recoverable (safe items): {fmt_bytes(c_recoverable)}**")
report_lines.append(f"**C: Potential recoverable (all items): {fmt_bytes(c_recoverable + c_page)}**")

# J: drive
j_chk = con.execute("SELECT SUM(size_bytes) FROM wiz WHERE drive='J:' AND LOWER(file_ext)='chk'").fetchone()[0] or 0
report_lines.append(f"\n### J: Drive — {fmt_bytes(j_chk)} in .CHK recovery files")
report_lines.append("These are filesystem recovery fragments from exFAT corruption. Inspect before deleting.")

# I: drive duplicate DBs
i_dup_dbs = con.execute("""
SELECT SUM(size_bytes) FROM wiz 
WHERE drive='I:' AND LOWER(file_ext)='db' 
AND (file_path LIKE '%backup%' OR file_path LIKE '%duplicate%' OR file_path LIKE '%copy%')
""").fetchone()[0] or 0
report_lines.append(f"\n### I: Drive — {fmt_bytes(i_dup_dbs)} in backup/duplicate databases")

# ═══════════════════════════════════════════════════════════════
# 12. ANOMALIES
# ═══════════════════════════════════════════════════════════════
section("12. Anomalies & Warnings")

# Zero-byte files
zb = con.execute("SELECT COUNT(*) FROM wiz WHERE size_bytes = 0").fetchone()[0]
report_lines.append(f"- **Zero-byte files**: {zb:,}")

# Very old files (before 2020)
old = con.execute("SELECT COUNT(*) FROM wiz WHERE modified < '2020/01/01' AND size_bytes > 0").fetchone()[0]
report_lines.append(f"- **Files older than 2020**: {old:,}")

# Extremely large files (>1GB)
huge = con.execute("SELECT COUNT(*), SUM(size_bytes) FROM wiz WHERE size_bytes > 1073741824").fetchone()
report_lines.append(f"- **Files >1 GB**: {huge[0]:,} files totaling {fmt_bytes(huge[1])}")

# Potential PII/sensitive
pii = con.execute("""
SELECT COUNT(*) FROM wiz WHERE 
    LOWER(file_name) LIKE '%password%' OR LOWER(file_name) LIKE '%secret%' 
    OR LOWER(file_name) LIKE '%credential%' OR LOWER(file_name) LIKE '%private_key%'
""").fetchone()[0]
report_lines.append(f"- **Potentially sensitive filenames**: {pii:,}")

# Files with child's name (MCR 8.119(H) check)
child_name_count = con.execute("""
SELECT COUNT(*) FROM wiz WHERE 
    LOWER(file_path) LIKE '%lincoln%david%' OR LOWER(file_path) LIKE '%lincoln%watson%'
""").fetchone()[0]
if child_name_count > 0:
    report_lines.append(f"- **⚠️ FILES WITH CHILD'S FULL NAME IN PATH**: {child_name_count:,} — MCR 8.119(H) violation risk")

report_lines.append(f"\n---\n*Audit complete. {total_rows:,} files analyzed across all drives.*")

# ═══════════════════════════════════════════════════════════════
# WRITE OUTPUTS
# ═══════════════════════════════════════════════════════════════
report_text = "\n".join(report_lines)

os.makedirs(os.path.dirname(REPORT_OUT), exist_ok=True)
with open(REPORT_OUT, "w", encoding="utf-8") as f:
    f.write(report_text)
print(f"\n[OK] Report saved: {REPORT_OUT}")

audit_data["total_files"] = total_rows
audit_data["generated"] = datetime.now().isoformat()
with open(JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(audit_data, f, indent=2)
print(f"[OK] JSON data saved: {JSON_OUT}")

# Print summary to stdout
print("\n" + "="*60)
print("DRIVE AUDIT SUMMARY")
print("="*60)
for d in drive_data:
    print(f"  {d['drive']:4s}  {d['files']:>10,} files  {fmt_bytes(d['total_size']):>12s}  Free: {fmt_bytes(d['free'])}")
print(f"\n  TOTAL: {total_rows:,} files")
print(f"  C: recoverable (safe): {fmt_bytes(c_recoverable)}")
print(f"  J: CHK fragments: {fmt_bytes(j_chk)}")
print(f"  I: duplicate DBs: {fmt_bytes(i_dup_dbs)}")
print(f"\n  Report: {REPORT_OUT}")

con.close()
