#!/usr/bin/env python3
"""
Ω8: BATES/EXHIBIT STAMPER — OMEGA-ELITE-MASTER
Right-click any folder → auto-number all documents as exhibits with Bates stamps.
Generates exhibit index, cover sheets, and filing-ready manifest.
"""
import sys, os, json, csv
from pathlib import Path
from datetime import datetime

EXHIBIT_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PREFIX = "PIGORS"

def generate_exhibit_label(index):
    """A, B, ... Z, AA, AB, ..."""
    if index < 26:
        return EXHIBIT_LETTERS[index]
    return EXHIBIT_LETTERS[index // 26 - 1] + EXHIBIT_LETTERS[index % 26]

def stamp_folder(target):
    target = Path(target).resolve()
    print(f"{'='*60}")
    print(f"  Ω8: BATES / EXHIBIT STAMPER")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    # Collect all stampable files
    files = []
    for fp in sorted(target.rglob("*")):
        if fp.suffix.lower() in ('.pdf', '.md', '.txt', '.docx', '.jpg', '.png') and fp.is_file():
            if not fp.name.startswith("_"):
                files.append(fp)

    if not files:
        print("No stampable files found.")
        return

    print(f"Found {len(files)} files to stamp\n")

    bates_number = 1
    exhibits = []

    for i, fp in enumerate(files):
        label = generate_exhibit_label(i)
        sz = fp.stat().st_size
        page_est = max(1, sz // 3000) if fp.suffix.lower() in ('.pdf', '.docx') else 1
        bates_start = bates_number
        bates_end = bates_number + page_est - 1
        bates_number = bates_end + 1

        exhibit = {
            "label": f"Exhibit {label}",
            "file": fp.name,
            "path": str(fp.relative_to(target)),
            "bates_range": f"{PREFIX}-{bates_start:06d} to {PREFIX}-{bates_end:06d}",
            "bates_start": bates_start,
            "bates_end": bates_end,
            "pages_est": page_est,
            "size": sz,
            "type": fp.suffix.lower(),
        }
        exhibits.append(exhibit)
        print(f"  {exhibit['label']:12s}  {exhibit['bates_range']}  {fp.name}")

    total_pages = bates_number - 1

    # Generate Exhibit Index (Markdown)
    index_path = target / "_EXHIBIT_INDEX.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(f"# EXHIBIT INDEX\n\n")
        f.write(f"**Case:** Pigors v. Watson\n")
        f.write(f"**Generated:** {datetime.now():%B %d, %Y}\n")
        f.write(f"**Bates Range:** {PREFIX}-000001 to {PREFIX}-{total_pages:06d}\n\n")
        f.write(f"| Exhibit | Bates Range | Description | Pages |\n")
        f.write(f"|---------|-------------|-------------|-------|\n")
        for ex in exhibits:
            f.write(f"| {ex['label']} | {ex['bates_range']} | {ex['file']} | {ex['pages_est']} |\n")
        f.write(f"\n**Total Exhibits:** {len(exhibits)}\n")
        f.write(f"**Total Pages:** {total_pages}\n")

    # Generate CSV manifest
    csv_path = target / f"_exhibit_manifest_{datetime.now():%Y%m%d}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["label", "file", "bates_range", "bates_start", "bates_end", "pages_est", "size", "type"])
        writer.writeheader()
        writer.writerows(exhibits)

    # Generate JSON
    report_path = target / f"_exhibit_stamp_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(report_path, "w") as f:
        json.dump({
            "stamp_time": datetime.now().isoformat(),
            "prefix": PREFIX,
            "total_exhibits": len(exhibits),
            "total_pages": total_pages,
            "bates_range": f"{PREFIX}-000001 to {PREFIX}-{total_pages:06d}",
            "exhibits": exhibits,
        }, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  STAMPING COMPLETE")
    print(f"  Exhibits: {len(exhibits)}")
    print(f"  Bates range: {PREFIX}-000001 to {PREFIX}-{total_pages:06d}")
    print(f"  Est. pages: {total_pages}")
    print(f"\n  📋 Index: {index_path}")
    print(f"  📋 CSV:   {csv_path}")
    print(f"  📋 JSON:  {report_path}")
    print(f"{'='*60}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python omega_08_exhibit_stamper.py <folder_path>")
        sys.exit(1)
    stamp_folder(sys.argv[1])
    input("\nPress Enter to close...")
