"""Quick check of v2 consolidation state."""
import polars as pl
from pathlib import Path

PQ = Path(r"D:\LitigationOS_tmp\consolidation_v2")

inv = pl.read_parquet(PQ / "inventory.parquet")
print(f"=== V2 INVENTORY: {len(inv):,} files ===")
print(f"Columns: {inv.columns}")
print()

by_drive = inv.group_by("source_drive").agg(
    pl.len().alias("n"),
    pl.col("file_size").sum().alias("bytes")
).sort("n", descending=True)
for r in by_drive.iter_rows(named=True):
    print(f"  {r['source_drive']}: {r['n']:>8,} files  {r['bytes']/1e9:>8.2f} GB")

print()
plan = pl.read_parquet(PQ / "copy_plan.parquet")
print(f"=== COPY PLAN: {len(plan):,} entries ===")
print(f"Columns: {plan.columns}")
print()

if "copy_status" in plan.columns:
    for r in plan.group_by("copy_status").agg(pl.len().alias("n")).sort("n", descending=True).iter_rows(named=True):
        print(f"  {r['copy_status']}: {r['n']:,}")

if "dedup_status" in inv.columns:
    print()
    print("=== DEDUP STATUS ===")
    for r in inv.group_by("dedup_status").agg(pl.len().alias("n")).sort("n", descending=True).iter_rows(named=True):
        print(f"  {r['dedup_status']}: {r['n']:,}")

# Check target paths
if "target_path" in plan.columns:
    sample = plan.filter(pl.col("target_path").is_not_null()).head(5)
    print()
    print("=== SAMPLE TARGET PATHS ===")
    for r in sample.select("source_path", "target_path").iter_rows(named=True):
        print(f"  {r['source_path'][:60]}...")
        print(f"    -> {r['target_path'][:80]}")
