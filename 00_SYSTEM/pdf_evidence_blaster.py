#!/usr/bin/env python3
"""PDF Evidence Blaster — Bleeding-edge PDF scanner using pypdfium2 + fd + orjson.

Scans ALL drives for .pdf files, extracts text from first N pages,
scores by litigation keyword density, deep-reads top files, outputs report + JSON.

Architecture:
  Phase 1: fd discovery (Rust, 5-50x faster than os.walk)
  Phase 2: Peek first 2 pages of every PDF (pypdfium2, 5x faster than PyMuPDF)
  Phase 3: Deep-read top-scoring PDFs (all pages)
  Phase 4: Generate report + JSON

Usage:
  python -I pdf_evidence_blaster.py
"""

import subprocess, re, os, sys, time, json, hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter, defaultdict

# --- CONFIG ---
DRIVES = ["C:\\Users\\andre\\LitigationOS", "D:\\", "F:\\", "G:\\", "J:\\"]
# I:\ EXCLUDED — slow SD card hangs pypdfium2 C-level threads permanently
# G:\ still included (355 PDFs, USB flash, reads OK)
FD_TIMEOUT = 180  # seconds per drive
PEEK_PAGES = 2    # pages to read in peek phase
DEEP_READ_TOP_N = 200  # how many top files to deep-read
DEEP_READ_MAX_PAGES = 20  # max pages per file in deep-read
MAX_WORKERS = 4   # reduced from 6 for stability
OUTPUT_DIR = Path(r"D:\LitigationOS_tmp")
REPORT_FILE = OUTPUT_DIR / "pdf_hunt_report.md"
JSON_FILE = OUTPUT_DIR / "pdf_hunt_results.json"

# --- KEYWORDS (same as TXT blaster, weighted by litigation value) ---
KEYWORDS = {
    # Score 10 — smoking gun terms
    "ex parte": 10, "premeditated": 10, "admitted": 10, "meth": 10,
    "shut my mouth": 10, "quit nitpicking": 10, "poison": 10, "arsenic": 10,
    "perjury": 10, "fabricat": 10,
    # Score 9 — high severity
    "contempt": 9, "jail": 9, "incarcerat": 9, "false arrest": 9,
    "retaliat": 9,
    # Score 8 — judicial misconduct / key legal
    "mcneill": 8, "bias": 8, "disqualif": 8, "jtc": 8, "canon": 8,
    "benchbook": 8, "misconduct": 8, "healthwest": 8, "mcr 2.003": 8,
    "ex parte order": 8, "ladas": 8, "hoopes": 8,
    # Score 7 — custody / abuse / key evidence
    "parenting time": 7, "alienat": 7, "withhold": 7, "best interest": 7,
    "mcl 722": 7, "show cause": 7, "transcript": 7, "albert": 7,
    "police report": 7, "testimony": 7, "due process": 7,
    # Score 6 — core case terms
    "custody": 6, "ppo": 6, "watson": 6, "trial": 6, "affidavit": 6,
    "appclose": 6, "factor": 6, "protection order": 6, "constitutional": 6,
    # Score 5 — supporting terms
    "pigors": 5, "violation": 5, "emily": 5, "hearing": 5, "exhibit": 5,
    "officer": 5, "allegation": 5, "damages": 5, "andrew": 4,
    # Score 4 — general legal
    "evidence": 4, "motion": 4, "complaint": 4, "discovery": 4, "brief": 4,
    "foia": 4, "rusco": 6, "ronald berry": 7, "cavan berry": 8,
    "jennifer barnes": 6, "pamela rusco": 7,
}

# Compiled regex for speed
KW_PATTERN = re.compile(
    "|".join(re.escape(k) for k in sorted(KEYWORDS.keys(), key=len, reverse=True)),
    re.IGNORECASE
)
DATE_PATTERN = re.compile(
    r'\b(?:20[12][0-9][-/][01]?\d[-/][0-3]?\d|'
    r'[01]?\d[-/][0-3]?\d[-/]20[12][0-9]|'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20[12][0-9])\b',
    re.IGNORECASE
)

def fd_discover(drive: str) -> list[str]:
    """Use fd (Rust) to find all .pdf files on a drive."""
    try:
        cmd = ["fd", "-e", "pdf", "--type", "f", "--no-ignore", "--hidden",
               "--absolute-path", ".", drive]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=FD_TIMEOUT, encoding="utf-8", errors="replace")
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        return files
    except subprocess.TimeoutExpired:
        print(f"  ⚠ fd timed out on {drive} after {FD_TIMEOUT}s")
        return []
    except Exception as e:
        print(f"  ❌ fd error on {drive}: {e}")
        return []

def extract_text_pypdfium2(pdf_path: str, max_pages: int = 2) -> str:
    """Extract text from PDF using pypdfium2 (5x faster than PyMuPDF)."""
    # Skip huge files (likely scanned images, not text PDFs)
    try:
        sz = os.path.getsize(pdf_path)
        if sz > 100_000_000:  # 100MB — skip
            return ""
    except OSError:
        return ""
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(pdf_path)
        pages_to_read = min(len(doc), max_pages)
        text_parts = []
        for i in range(pages_to_read):
            page = doc[i]
            textpage = page.get_textpage()
            text_parts.append(textpage.get_text_bounded())
            textpage.close()
            page.close()
        doc.close()
        return "\n".join(text_parts)
    except Exception:
        # Fallback to PyMuPDF if pypdfium2 fails
        try:
            import fitz
            doc = fitz.open(pdf_path)
            pages_to_read = min(len(doc), max_pages)
            text_parts = []
            for i in range(pages_to_read):
                text_parts.append(doc[i].get_text())
            doc.close()
            return "\n".join(text_parts)
        except Exception:
            return ""

def score_text(text: str) -> tuple[int, dict, list]:
    """Score text by weighted keyword density. Returns (score, keyword_counts, dates)."""
    if not text:
        return (0, {}, [])
    text_lower = text.lower()
    kw_counts = Counter()
    for match in KW_PATTERN.finditer(text_lower):
        kw = match.group().lower()
        for keyword in KEYWORDS:
            if keyword == kw:
                kw_counts[keyword] += 1
                break
    total_score = sum(count * KEYWORDS.get(kw, 1) for kw, count in kw_counts.items())
    dates = DATE_PATTERN.findall(text)[:50]
    return (total_score, dict(kw_counts.most_common(20)), dates)

def extract_quotes(text: str, min_line_score: int = 15) -> list[dict]:
    """Extract high-value lines with their keyword composition."""
    quotes = []
    for i, line in enumerate(text.split("\n"), 1):
        line = line.strip()
        if len(line) < 30 or len(line) > 1000:
            continue
        line_lower = line.lower()
        line_kws = []
        line_score = 0
        for kw, weight in KEYWORDS.items():
            if kw in line_lower:
                line_kws.append(kw)
                line_score += weight
        if line_score >= min_line_score:
            quotes.append({
                "line_num": i,
                "text": line[:500],
                "score": line_score,
                "keywords": line_kws[:10],
            })
    quotes.sort(key=lambda x: x["score"], reverse=True)
    return quotes[:100]

def peek_pdf(pdf_path: str) -> dict:
    """Phase 2: Quick peek at first 2 pages, score, return metadata."""
    try:
        fsize = os.path.getsize(pdf_path)
    except OSError:
        return None
    if fsize < 100:  # skip tiny files
        return None
    text = extract_text_pypdfium2(pdf_path, max_pages=PEEK_PAGES)
    if not text or len(text) < 20:
        return None
    score, kw_counts, dates = score_text(text)
    if score == 0:
        return None
    return {
        "path": pdf_path,
        "size_kb": round(fsize / 1024, 1),
        "peek_score": score,
        "keywords": kw_counts,
        "date_count": len(dates),
        "text_len": len(text),
    }

def deep_read_pdf(pdf_path: str) -> dict:
    """Phase 3: Full read of top-scoring PDFs."""
    text = extract_text_pypdfium2(pdf_path, max_pages=DEEP_READ_MAX_PAGES)
    if not text:
        return {"path": pdf_path, "score": 0, "quotes": [], "keywords": {}, "dates": []}
    score, kw_counts, dates = score_text(text)
    quotes = extract_quotes(text)
    return {
        "path": pdf_path,
        "score": score,
        "quotes": quotes,
        "keywords": kw_counts,
        "dates": dates[:20],
        "text_preview": text[:500],
    }

def main():
    t0 = time.time()
    print("=" * 70)
    print("  PDF EVIDENCE BLASTER — Bleeding-Edge Edition")
    print("  pypdfium2 + fd + ThreadPool + weighted keyword scoring")
    print("=" * 70)

    # --- PHASE 1: fd discovery ---
    print("\n📡 PHASE 1: fd discovery across all drives...")
    all_pdfs = []
    for drive in DRIVES:
        if not os.path.exists(drive.rstrip("\\")):
            print(f"  ⚠ {drive} not accessible, skipping")
            continue
        print(f"  Scanning {drive}...", end=" ", flush=True)
        t1 = time.time()
        found = fd_discover(drive)
        elapsed = time.time() - t1
        print(f"{len(found)} PDFs in {elapsed:.1f}s")
        all_pdfs.extend(found)
    
    # Dedup by path
    all_pdfs = list(dict.fromkeys(all_pdfs))
    print(f"\n  Total unique PDFs: {len(all_pdfs)}")

    # --- PHASE 2: Peek (parallel) ---
    print(f"\n🔍 PHASE 2: Peeking first {PEEK_PAGES} pages of {len(all_pdfs)} PDFs...")
    peek_results = []
    errors = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(peek_pdf, p): p for p in all_pdfs}
        done_count = 0
        try:
            for future in as_completed(futures, timeout=900):  # 15 min max total
                done_count += 1
                if done_count % 500 == 0:
                    print(f"  Peeked {done_count}/{len(all_pdfs)}...", flush=True)
                try:
                    result = future.result(timeout=10)  # 10s per file
                    if result:
                        peek_results.append(result)
                except Exception:
                    errors += 1
        except TimeoutError:
            skipped = len(all_pdfs) - done_count
            print(f"  ⚠ Global timeout reached — {done_count} done, {skipped} skipped")
            errors += skipped
            pool.shutdown(wait=False, cancel_futures=True)
    
    peek_results.sort(key=lambda x: x["peek_score"], reverse=True)
    print(f"  Files with keywords: {len(peek_results)}")
    print(f"  Errors/timeouts: {errors}")

    # --- PHASE 3: Deep-read top N ---
    top_paths = [r["path"] for r in peek_results[:DEEP_READ_TOP_N]]
    print(f"\n📖 PHASE 3: Deep-reading top {len(top_paths)} PDFs (up to {DEEP_READ_MAX_PAGES} pages each)...")
    deep_results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(deep_read_pdf, p): p for p in top_paths}
        done_count = 0
        try:
            for future in as_completed(futures, timeout=600):  # 10 min max
                done_count += 1
                if done_count % 50 == 0:
                    print(f"  Deep-read {done_count}/{len(top_paths)}...", flush=True)
                try:
                    result = future.result(timeout=30)
                    deep_results.append(result)
                except Exception:
                    pass
        except TimeoutError:
            print(f"  ⚠ Deep-read timeout — {done_count}/{len(top_paths)} done")
            pool.shutdown(wait=False, cancel_futures=True)
    
    deep_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Count quotes
    all_quotes = []
    for dr in deep_results:
        for q in dr.get("quotes", []):
            q["source_file"] = dr["path"]
            all_quotes.append(q)
    all_quotes.sort(key=lambda x: x["score"], reverse=True)
    
    smoking_guns = [q for q in all_quotes if q["score"] >= 30]
    high_value = [q for q in all_quotes if q["score"] >= 15]
    
    elapsed = time.time() - t0
    print(f"\n{'='*70}")
    print(f"  COMPLETE in {elapsed:.1f}s")
    print(f"  PDFs scanned: {len(all_pdfs)}")
    print(f"  With keywords: {len(peek_results)}")
    print(f"  Deep-read: {len(deep_results)}")
    print(f"  Total quotes: {len(all_quotes)}")
    print(f"  🔫 Smoking guns (≥30): {len(smoking_guns)}")
    print(f"  🔥 High-value (≥15): {len(high_value)}")
    print(f"{'='*70}")

    # --- PHASE 4: Generate outputs ---
    print("\n📝 PHASE 4: Generating report + JSON...")
    
    # Keyword frequency across ALL peeked files
    global_kw = Counter()
    for pr in peek_results:
        for kw, count in pr["keywords"].items():
            global_kw[kw] += count

    # Markdown report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# PDF Evidence Hunt Report\n")
        f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Elapsed:** {elapsed:.1f}s\n")
        f.write(f"**Total PDFs scanned:** {len(all_pdfs)}\n")
        f.write(f"**PDFs with keywords:** {len(peek_results)}\n")
        f.write(f"**Deep-read PDFs:** {len(deep_results)}\n")
        f.write(f"**Total quotes extracted:** {len(all_quotes)}\n")
        f.write(f"**Smoking guns (score≥30):** {len(smoking_guns)}\n")
        f.write(f"**High-value (score≥15):** {len(high_value)}\n\n---\n\n")
        
        f.write("## 🔫 TOP 50 PDFs BY LITIGATION VALUE\n\n")
        for dr in deep_results[:50]:
            relpath = dr["path"]
            f.write(f"### [{dr['score']}] `{relpath}`\n")
            kw_str = ", ".join(f"{k}({v})" for k, v in list(dr["keywords"].items())[:8])
            f.write(f"Quotes: {len(dr.get('quotes',[]))} | Dates: {len(dr.get('dates',[]))}\n")
            f.write(f"Keywords: {kw_str}\n\n")
        
        f.write("---\n\n## 🔥 TOP SMOKING GUN QUOTES (score ≥ 30)\n\n")
        for q in smoking_guns[:100]:
            f.write(f"**[{q['score']}]** `{q['source_file']}` L{q['line_num']}\n")
            f.write(f"> {q['text'][:300]}\n")
            f.write(f"Keywords: {', '.join(q['keywords'][:10])}\n\n")
        
        f.write("---\n\n## 📊 KEYWORD FREQUENCY (across all PDFs)\n\n")
        f.write("| Keyword | Hits | Weight | Total Score |\n")
        f.write("|---------|------|--------|-------------|\n")
        for kw, count in global_kw.most_common(60):
            weight = KEYWORDS.get(kw, 1)
            f.write(f"| {kw} | {count:,} | {weight} | {count*weight:,} |\n")
    
    print(f"  Report: {REPORT_FILE}")

    # JSON output
    json_data = {
        "generated": time.strftime('%Y-%m-%d %H:%M:%S'),
        "elapsed_seconds": round(elapsed, 1),
        "total_pdfs": len(all_pdfs),
        "pdfs_with_keywords": len(peek_results),
        "deep_read_count": len(deep_results),
        "smoking_gun_count": len(smoking_guns),
        "high_value_count": len(high_value),
        "top_100_files": [
            {"path": dr["path"], "score": dr["score"],
             "quote_count": len(dr.get("quotes", [])),
             "keywords": dr.get("keywords", {})}
            for dr in deep_results[:100]
        ],
        "smoking_guns": [
            {"source": q["source_file"], "line": q["line_num"],
             "text": q["text"][:500], "score": q["score"],
             "keywords": q["keywords"][:10]}
            for q in smoking_guns[:300]
        ],
        "high_value_quotes": [
            {"source": q["source_file"], "line": q["line_num"],
             "text": q["text"][:500], "score": q["score"],
             "keywords": q["keywords"][:10]}
            for q in high_value[:500]
        ],
        "keyword_frequency": {kw: count for kw, count in global_kw.most_common(60)},
    }
    
    try:
        import orjson
        with open(JSON_FILE, "wb") as f:
            f.write(orjson.dumps(json_data, option=orjson.OPT_INDENT_2))
    except ImportError:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"  JSON: {JSON_FILE}")
    print(f"\n✅ PDF Evidence Blaster complete!")

if __name__ == "__main__":
    main()
