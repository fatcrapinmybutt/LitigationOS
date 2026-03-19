import sqlite3, json
from datetime import datetime

DB = r"I:\DRIVE_ORG\drive_inventory.db"
conn = sqlite3.connect(DB)

groups = conn.execute("SELECT * FROM dedup_groups ORDER BY size * file_count DESC LIMIT 200").fetchall()
total_groups = conn.execute("SELECT COUNT(*) FROM dedup_groups").fetchone()[0]
total_dupes = conn.execute("SELECT COUNT(*) FROM files WHERE is_duplicate=1").fetchone()[0]
total_bytes = conn.execute("SELECT COALESCE(SUM(size),0) FROM files WHERE is_duplicate=1").fetchone()[0]

drive_stats = conn.execute("""
    SELECT drive, COUNT(*), COALESCE(SUM(size),0)
    FROM files WHERE is_duplicate=1
    GROUP BY drive ORDER BY SUM(size) DESC
""").fetchall()

junk_stats = conn.execute("""
    SELECT drive, COUNT(*), COALESCE(SUM(size),0)
    FROM files WHERE classification IN ('JUNK','SYSTEM') OR is_junk=1
    GROUP BY drive ORDER BY SUM(size) DESC
""").fetchall()
total_junk = sum(r[2] for r in junk_stats)

big_junk = conn.execute("""
    SELECT path, size, classification FROM files
    WHERE (classification='JUNK' OR is_junk=1) AND size > 10000000
    ORDER BY size DESC LIMIT 50
""").fetchall()

top_groups = []
for gid, fname, sz, cnt, keep, status in groups[:200]:
    dupes = [r[0] for r in conn.execute("SELECT path FROM files WHERE dedup_group=? AND is_duplicate=1", (gid,))]
    top_groups.append({
        "group_id": gid, "filename": fname, "size": sz,
        "keep": keep, "duplicates": dupes,
        "recoverable_gb": round(sz * len(dupes) / 1024/1024/1024, 3)
    })

with open(r"I:\DRIVE_ORG\DEDUP_CANDIDATES.json", "w") as f:
    json.dump({
        "generated": datetime.now().isoformat(),
        "total_groups": total_groups,
        "total_duplicate_files": total_dupes,
        "total_recoverable_gb": round(total_bytes/1024/1024/1024, 2),
        "total_junk_gb": round(total_junk/1024/1024/1024, 2),
        "combined_recovery_gb": round((total_bytes+total_junk)/1024/1024/1024, 2),
        "per_drive": [{"drive": d, "dupes": c, "gb": round(s/1024/1024/1024,2)} for d,c,s in drive_stats],
        "top_groups": top_groups[:100]
    }, f, indent=2)

with open(r"I:\DRIVE_ORG\JUNK_TARGETS.json", "w") as f:
    json.dump({
        "generated": datetime.now().isoformat(),
        "total_junk_gb": round(total_junk/1024/1024/1024, 2),
        "by_drive": [{"drive": d, "files": c, "size_gb": round(s/1024/1024/1024, 2)} for d,c,s in junk_stats],
        "big_junk": [{"path": p, "size_mb": round(s/1024/1024, 1), "class": cl} for p,s,cl in big_junk]
    }, f, indent=2)

print(f"PASS 1 RESULTS:")
print(f"  Duplicate groups: {total_groups:,}")
print(f"  Duplicate files: {total_dupes:,}")
print(f"  Dedup recoverable: {total_bytes/1024/1024/1024:.2f}GB")
print(f"  Junk recoverable: {total_junk/1024/1024/1024:.2f}GB")
print(f"  TOTAL RECOVERABLE: {(total_bytes+total_junk)/1024/1024/1024:.2f}GB")
print()
print("PER-DRIVE DUPLICATES:")
for d,c,s in drive_stats:
    print(f"  {d}: {c:,} files = {s/1024/1024/1024:.2f}GB")
print()
print("PER-DRIVE JUNK:")
for d,c,s in junk_stats:
    print(f"  {d}: {c:,} files = {s/1024/1024/1024:.2f}GB")
print()
print("TOP 10 BIGGEST DEDUP GROUPS:")
for g in top_groups[:10]:
    fname = g["filename"]
    sz = g["size"]/1024/1024
    nd = len(g["duplicates"])
    rg = g["recoverable_gb"]
    kp = g["keep"][:60]
    print(f"  {fname}: {sz:.1f}MB x {nd} dupes = {rg:.2f}GB | keep: {kp}")
print()
print("TOP 10 BIGGEST JUNK:")
for p,s,cl in big_junk[:10]:
    print(f"  {s/1024/1024:.0f}MB | {cl} | {p[:80]}")

conn.close()
