#!/usr/bin/env python3
"""
TXT Evidence Blaster — Ripgrep + DuckDB powered evidence harvester.
Scans ALL drives for .txt files, scores by litigation value, extracts weaponizable intel.
Bleeding-edge: fd for discovery, rg for content matching, DuckDB for analytics.
"""
import subprocess, json, os, re, sys, time, sqlite3
from pathlib import Path
from collections import defaultdict, Counter

# ── CONFIG ──────────────────────────────────────────────────────────────────
DRIVES = [r"C:\Users\andre\LitigationOS", r"D:\\", r"F:\\", r"I:\\", r"J:\\"]
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUTPUT = r"D:\LitigationOS_tmp\txt_hunt_results.json"
REPORT = r"D:\LitigationOS_tmp\txt_hunt_report.md"

# Litigation keyword patterns — weighted by weaponization value
KEYWORDS = {
    # Severity 10 — smoking guns
    "ex parte": 10, "premeditated": 10, "admitted": 10, "confession": 10,
    "perjury": 10, "fabricated": 10, "false allegation": 10, "recant": 10,
    "meth": 10, "drug use": 10, "arsenic": 10, "poison": 10,
    "contempt": 9, "jail": 9, "incarcerat": 9, "imprison": 9,
    # Severity 8 — judicial misconduct
    "mcneill": 8, "bias": 8, "misconduct": 8, "disqualif": 8,
    "benchbook": 8, "canon": 8, "jtc": 8, "judicial tenure": 8,
    "ex parte order": 8, "without notice": 8, "without hearing": 8,
    "denied access": 8, "shut my mouth": 10, "do not file": 10,
    # Severity 7 — custody/alienation
    "alienat": 7, "withhold": 7, "denied parenting": 7, "denied visitation": 7,
    "best interest": 7, "mcl 722": 7, "factor": 6, "custody": 6,
    "parenting time": 7, "suspended": 7, "emergency motion": 7,
    # Severity 6 — key actors/events
    "watson": 6, "emily": 5, "albert": 7, "ronald berry": 7, "ron berry": 7,
    "jennifer barnes": 6, "pamela rusco": 6, "hoopes": 7, "ladas": 7,
    "cavan berry": 8, "pigors": 5, "andrew": 4,
    # Severity 5 — procedural/evidence
    "ppo": 6, "protection order": 6, "mcr 2.003": 8, "mcr 7.306": 7,
    "healthwest": 8, "locus": 8, "psychosis": 8,
    "police report": 7, "nspd": 7, "ns250": 8, "officer": 5,
    "appclose": 6, "recording": 7, "audio": 6, "transcript": 7,
    "affidavit": 6, "testimony": 7, "hearing": 5, "trial": 6,
    "contempt of court": 8, "show cause": 7, "violation": 5,
    # Severity 4 — supporting
    "complaint": 4, "motion": 4, "brief": 4, "exhibit": 5,
    "evidence": 4, "allegation": 5, "accusation": 5,
    "foia": 5, "subpoena": 5, "discovery": 4,
    "damages": 5, "retaliation": 7, "conspiracy": 7,
    "1983": 6, "civil rights": 6, "due process": 7, "constitutional": 6,
}

# Compile mega-pattern for ripgrep (case-insensitive)
RG_PATTERN = "|".join(re.escape(k) for k in sorted(KEYWORDS.keys(), key=len, reverse=True))


def run_fd(drive):
    """Use fd (Rust) to find all .txt files >512 bytes on a drive."""
    try:
        args = ["fd", "-e", "txt", "--type", "f", "--size", "+512b",
                "-E", "node_modules", "-E", ".git", "-E", "__pycache__",
                "-E", "pytools_venv", "-E", ".mcp_venv", "-E", ".venv",
                "--no-ignore", ".", drive]
        result = subprocess.run(args, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        return files
    except Exception as e:
        print(f"  [WARN] fd failed on {drive}: {e}")
        return []


def run_rg_json(drive, pattern, max_count=50):
    """Use ripgrep (Rust) to search .txt files for litigation keywords. Returns JSON matches."""
    try:
        args = ["rg", "--json", "-i", "--max-count", str(max_count),
                "-t", "txt", "--no-ignore",
                "-E", "node_modules", "-E", ".git", "-E", "__pycache__",
                pattern, drive]
        result = subprocess.run(args, capture_output=True, text=True, timeout=180,
                                encoding="utf-8", errors="replace")
        return result.stdout
    except Exception as e:
        print(f"  [WARN] rg failed on {drive}: {e}")
        return ""


def peek_file(filepath, chars=2000):
    """Read first N chars of a file for quick assessment."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read(chars)
    except Exception:
        return ""


def full_read(filepath, max_chars=500000):
    """Read full file content (capped)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_chars)
    except Exception:
        return ""


def score_content(text):
    """Score text by litigation keyword density. Returns (total_score, keyword_hits dict)."""
    text_lower = text.lower()
    total = 0
    hits = {}
    for kw, weight in KEYWORDS.items():
        count = text_lower.count(kw.lower())
        if count > 0:
            hits[kw] = {"count": count, "weight": weight, "score": count * weight}
            total += count * weight
    return total, hits


def extract_quotes(text, filepath):
    """Extract verbatim quotes and key passages from text."""
    quotes = []
    lines = text.split("\n")
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 20:
            continue
        # Check for quote markers
        if any(marker in line_stripped for marker in ['"', "'", "stated", "said", "testified",
                "admitted", "told", "reported", "wrote", "claimed", "alleged"]):
            score, hits = score_content(line_stripped)
            if score >= 5:
                quotes.append({
                    "text": line_stripped[:500],
                    "line": i,
                    "score": score,
                    "keywords": list(hits.keys())[:10],
                    "source": filepath
                })
        # Also catch high-value lines regardless
        else:
            score, hits = score_content(line_stripped)
            if score >= 15:
                quotes.append({
                    "text": line_stripped[:500],
                    "line": i,
                    "score": score,
                    "keywords": list(hits.keys())[:10],
                    "source": filepath
                })
    return quotes


def extract_dates(text):
    """Extract dates from text."""
    patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b',
    ]
    dates = set()
    for p in patterns:
        dates.update(re.findall(p, text, re.IGNORECASE))
    return sorted(dates)


def main():
    start = time.time()
    all_files = {}
    file_scores = {}
    all_quotes = []
    all_dates = defaultdict(list)

    print("=" * 80)
    print("TXT EVIDENCE BLASTER — Ripgrep + fd Powered")
    print("=" * 80)

    # ── PHASE 1: Discovery (fd) ─────────────────────────────────────────────
    print("\n[PHASE 1] File discovery with fd (Rust)...")
    for drive in DRIVES:
        if not os.path.exists(drive.rstrip("\\")):
            print(f"  {drive}: NOT MOUNTED — skipping")
            continue
        print(f"  Scanning {drive}...", end=" ", flush=True)
        files = run_fd(drive)
        print(f"{len(files)} .txt files found")
        for f in files:
            all_files[f] = {"drive": drive, "size": 0}
            try:
                all_files[f]["size"] = os.path.getsize(f)
            except:
                pass

    total_files = len(all_files)
    total_size = sum(v["size"] for v in all_files.values())
    print(f"\n  TOTAL: {total_files} .txt files, {total_size / (1024*1024):.1f} MB")

    # ── PHASE 2: Quick peek + score every file ──────────────────────────────
    print("\n[PHASE 2] Peeking inside every file (first 2KB)...")
    scored = []
    for i, (filepath, meta) in enumerate(all_files.items()):
        if i % 500 == 0:
            print(f"  Peeked {i}/{total_files}...", flush=True)
        peek = peek_file(filepath)
        score, hits = score_content(peek)
        file_scores[filepath] = {
            "score": score,
            "hits": hits,
            "size": meta["size"],
            "drive": meta["drive"]
        }
        if score > 0:
            scored.append((filepath, score, hits))

    scored.sort(key=lambda x: -x[1])
    print(f"\n  Files with litigation keywords: {len(scored)}/{total_files}")
    print(f"  Top 20 files by score:")
    for fp, sc, _ in scored[:20]:
        print(f"    [{sc:>6}] {fp}")

    # ── PHASE 3: Deep read top files ────────────────────────────────────────
    # Read top 200 files fully (or all files scoring > 20)
    deep_read_targets = [fp for fp, sc, _ in scored if sc >= 10][:300]
    print(f"\n[PHASE 3] Deep reading {len(deep_read_targets)} high-value files...")

    deep_results = []
    for i, filepath in enumerate(deep_read_targets):
        if i % 50 == 0:
            print(f"  Read {i}/{len(deep_read_targets)}...", flush=True)
        content = full_read(filepath)
        full_score, full_hits = score_content(content)
        file_scores[filepath]["full_score"] = full_score
        file_scores[filepath]["full_hits"] = full_hits

        # Extract quotes and dates
        quotes = extract_quotes(content, filepath)
        dates = extract_dates(content)
        all_quotes.extend(quotes)
        for d in dates:
            all_dates[d].append(filepath)

        if full_score >= 20:
            deep_results.append({
                "path": filepath,
                "score": full_score,
                "size": file_scores[filepath]["size"],
                "top_keywords": sorted(full_hits.items(), key=lambda x: -x[1]["score"])[:15],
                "quote_count": len(quotes),
                "date_count": len(dates),
            })

    deep_results.sort(key=lambda x: -x["score"])

    # ── PHASE 4: Generate report ────────────────────────────────────────────
    print(f"\n[PHASE 4] Generating report...")

    # Sort quotes by score
    all_quotes.sort(key=lambda x: -x["score"])
    smoking_guns = [q for q in all_quotes if q["score"] >= 30]
    high_value = [q for q in all_quotes if 15 <= q["score"] < 30]

    elapsed = time.time() - start

    report_lines = [
        f"# TXT Evidence Hunt Report",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Elapsed:** {elapsed:.1f}s",
        f"**Total .txt files scanned:** {total_files}",
        f"**Files with keywords:** {len(scored)}",
        f"**Deep-read files:** {len(deep_read_targets)}",
        f"**Total quotes extracted:** {len(all_quotes)}",
        f"**Smoking guns (score≥30):** {len(smoking_guns)}",
        f"**High-value (score≥15):** {len(high_value)}",
        "",
        "---",
        "",
        "## 🔫 TOP 50 FILES BY LITIGATION VALUE",
        "",
    ]

    for r in deep_results[:50]:
        kw_str = ", ".join(f"{k}({v['count']})" for k, v in r["top_keywords"][:8])
        report_lines.append(f"### [{r['score']:,}] `{r['path']}`")
        report_lines.append(f"Size: {r['size']/1024:.1f}KB | Quotes: {r['quote_count']} | Dates: {r['date_count']}")
        report_lines.append(f"Keywords: {kw_str}")
        report_lines.append("")

    report_lines.extend([
        "---",
        "",
        "## 🔥 SMOKING GUN QUOTES (score ≥ 30)",
        "",
    ])
    for q in smoking_guns[:100]:
        report_lines.append(f"**[{q['score']}]** `{q['source']}` L{q['line']}")
        report_lines.append(f"> {q['text'][:300]}")
        report_lines.append(f"Keywords: {', '.join(q['keywords'])}")
        report_lines.append("")

    report_lines.extend([
        "---",
        "",
        "## ⚡ HIGH-VALUE QUOTES (score 15-29)",
        "",
    ])
    for q in high_value[:200]:
        report_lines.append(f"**[{q['score']}]** `{q['source']}` L{q['line']}")
        report_lines.append(f"> {q['text'][:200]}")
        report_lines.append("")

    report_lines.extend([
        "---",
        "",
        "## 📊 KEYWORD FREQUENCY (across all files)",
        "",
        "| Keyword | Hits | Weight | Total Score |",
        "|---------|------|--------|-------------|",
    ])
    # Aggregate keyword stats
    kw_totals = defaultdict(lambda: {"count": 0, "weight": 0, "score": 0})
    for fp, data in file_scores.items():
        hits = data.get("full_hits", data.get("hits", {}))
        for kw, info in hits.items():
            kw_totals[kw]["count"] += info["count"]
            kw_totals[kw]["weight"] = info["weight"]
            kw_totals[kw]["score"] += info["score"]
    for kw, info in sorted(kw_totals.items(), key=lambda x: -x[1]["score"])[:50]:
        report_lines.append(f"| {kw} | {info['count']:,} | {info['weight']} | {info['score']:,} |")

    # Write report
    report_text = "\n".join(report_lines)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"  Report written to {REPORT}")

    # Write JSON for programmatic access
    json_data = {
        "stats": {
            "total_files": total_files,
            "keyword_files": len(scored),
            "deep_read": len(deep_read_targets),
            "quotes": len(all_quotes),
            "smoking_guns": len(smoking_guns),
            "elapsed_seconds": elapsed,
        },
        "top_files": deep_results[:100],
        "smoking_guns": smoking_guns[:200],
        "high_value_quotes": high_value[:500],
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, default=str)
    print(f"  JSON written to {OUTPUT}")

    # ── Summary ─────────────────────────────────────────────────────────────
    print(f"\n{'='*80}")
    print(f"HUNT COMPLETE in {elapsed:.1f}s")
    print(f"  {total_files} files scanned | {len(scored)} with keywords | {len(deep_read_targets)} deep-read")
    print(f"  {len(smoking_guns)} smoking guns | {len(high_value)} high-value quotes")
    print(f"  Report: {REPORT}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
