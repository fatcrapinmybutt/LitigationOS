#!/usr/bin/env python3
"""
Desktop ZIP Ingest Bridge for Litigation Command Center
- Unpacks a desktop export ZIP
- Builds append-only corpus inventory (CRC32 + bytes + zip mtime integrity keys)
- Classifies artifact themes
- Emits JSON/CSV for GUI Desktop Corpus panel
"""
from __future__ import annotations
import argparse, csv, json, re, zipfile
from pathlib import Path
from collections import Counter, defaultdict

THEME_KEYS = [
    "event_horizon","copilot","delta9","cyclecore","operator","replay",
    "transition","pydantic","mermaid","schema","msc","prompt","planes","launcher"
]

def classify(name: str) -> list[str]:
    s = name.lower()
    return [k for k in THEME_KEYS if k in s]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("zip_path", help="Path to Desktop.zip or similar corpus zip")
    ap.add_argument("--out-dir", default="desktop_ingest_out", help="Output directory")
    args = ap.parse_args()

    zip_path = Path(args.zip_path)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = out_dir / "extracted"
    extract_dir.mkdir(exist_ok=True)

    records = []
    ext_counts = Counter()
    dup = defaultdict(list)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
        for zi in zf.infolist():
            p = extract_dir / zi.filename
            ext = p.suffix.lower()
            ext_counts[ext] += 1
            crc = f"{zi.CRC:08X}"
            mtime = "%04d-%02d-%02dT%02d:%02d:%02d" % zi.date_time
            tags = classify(zi.filename)
            preview = ""
            if ext in {".md",".txt",".json",".py",".ps1",".mmd"}:
                try:
                    txt = p.read_text(encoding="utf-8", errors="replace")
                    preview = re.sub(r"\s+", " ", txt[:300]).strip()
                    line_count = txt.count("\n") + 1
                except Exception:
                    line_count = None
            else:
                line_count = None
            rec = {
                "path": zi.filename,
                "ext": ext,
                "bytes": zi.file_size,
                "zip_crc32": crc,
                "zip_mtime": mtime,
                "integrity_key": f"{crc}|{zi.file_size}|{mtime}",
                "theme_tags": tags,
                "line_count": line_count,
                "preview": preview,
            }
            records.append(rec)
            dup[f"{crc}|{zi.file_size}"].append(zi.filename)

    records.sort(key=lambda r: r["path"].lower())
    dup_clusters = [{"sig":k,"paths":v} for k,v in dup.items() if len(v)>1]

    (out_dir/"desktop_corpus_inventory.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    (out_dir/"desktop_duplicate_clusters.json").write_text(json.dumps(dup_clusters, indent=2), encoding="utf-8")

    with open(out_dir/"desktop_corpus_inventory.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path","ext","bytes","zip_crc32","zip_mtime","integrity_key","line_count","theme_tags","preview"])
        for r in records:
            w.writerow([r["path"], r["ext"], r["bytes"], r["zip_crc32"], r["zip_mtime"], r["integrity_key"], r["line_count"] or "", ",".join(r["theme_tags"]), r["preview"]])

    summary = {
        "total_files": len(records),
        "extension_counts": dict(ext_counts),
        "duplicate_cluster_count": len(dup_clusters),
        "discovery_targets": [
            "Map operator catalog and transition compiler into Ops/Replay panel",
            "Wire pydantic/EBNF/mermaid artifacts into Desktop Corpus panel filters",
            "Promote launcher scripts into Runtime readiness cards"
        ]
    }
    (out_dir/"desktop_corpus_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
