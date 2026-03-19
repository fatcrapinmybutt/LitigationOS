#!/usr/bin/env python3
"""
harvest_runner.py — PublicLitigationOS / LitigationOS AutoHarvest runner (stdlib-first).

Goal:
- Recursively scan one or more roots, skipping low-signal/system junk.
- Inventory documents (pdf/docx/txt/md/csv/json/html/eml + archives optionally).
- Extract text (best-effort), detect dates, "order" language, negative-connotation flags,
  and procedural due-process / rights / rule-violation keywords (heuristic).
- Emit a run folder containing machine-readable logs + a human-ready report + NEXT_PROMPT.md.

Design constraints:
- Standard library only by default.
- Optional readers if installed: pypdf / PyPDF2 (PDF), python-docx (DOCX).
- Safe, fail-soft: never crash a whole run because one file is unreadable/corrupt.

Usage examples:
  python .gemini/scripts/harvest_runner.py --root "C:\\Users\\andre\\LITIGATION_OS" --include-archives --hash 1
  python harvest_runner.py --root "G:\\Capstone\\HARVEST_ROOT" --max-mb 80 --out ".gemini/out"
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import fnmatch
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import unicodedata
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

###############################################################################
# Defaults: skip/noise filters
###############################################################################

DEFAULT_SKIP_DIR_NAMES = {
    ".git", ".svn", ".hg", "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", "dist", "build", "out", ".next", ".nuxt",
    ".venv", "venv", "env", ".tox",
    ".vscode", ".idea", ".vs", ".cache", ".gradle", ".npm", ".yarn",
    ".cargo", ".rustup",
    "$RECYCLE.BIN", "System Volume Information",
    "Temp", "tmp",
    ".ollama", ".gemini", ".copilot", ".claude", ".chatgpt-copilot", ".continue", ".cline", ".codex",
    ".azure",
}

DEFAULT_SKIP_FILE_GLOBS = [
    "*.exe", "*.dll", "*.sys", "*.msi", "*.cab",
    "*.iso", "*.img", "*.vhd", "*.vhdx",
    "*.mp4", "*.mkv", "*.mov", "*.avi", "*.mp3", "*.wav",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp",
    "*.zipx", "*.7z", "*.rar", "*.tar", "*.gz", "*.bz2", "*.xz",
    "*.sqlite", "*.db", "*.pdb",
]

DEFAULT_ALLOWED_EXTS = {
    ".pdf", ".docx", ".doc", ".rtf",
    ".txt", ".md", ".csv", ".tsv", ".json",
    ".html", ".htm", ".xml",
    ".eml", ".msg",
    ".log",
}

ARCHIVE_EXTS = {".zip"}

###############################################################################
# Keyword lexicons (heuristic signals)
###############################################################################

KEYWORDS: Dict[str, List[str]] = {
    "order_language": [
        "IT IS ORDERED", "IT IS FURTHER ORDERED", "ORDERED", "JUDGMENT", "ADJUDGED",
        "THIS MATTER came before", "HEARING", "FINDINGS OF FACT", "CONCLUSIONS OF LAW",
    ],
    "ex_parte": [
        "ex parte", "without notice", "without hearing", "emergency", "irreparable injury",
        "temporary order", "immediate", "on an emergency basis",
    ],
    "due_process": [
        "due process", "notice and an opportunity", "opportunity to be heard",
        "hearing is denied", "without a hearing", "no hearing", "not allowed to present",
        "refused to accept", "evidence not accepted", "procedural", "fundamental fairness",
    ],
    "bias_prejudice": [
        "bias", "prejudice", "favoritism", "appearance of impropriety", "conflict of interest",
        "recuse", "recusal", "impartial", "disqualify",
    ],
    "contempt_sanctions": [
        "contempt", "show cause", "sanctions", "fees", "attorney fees",
        "bench warrant", "jail", "incarcerat",
    ],
    "ppo_no_contact": [
        "personal protection order", "PPO", "no contact", "restraining order",
        "stalking", "harass", "threat", "credible threat",
    ],
    "drug_mental_health_allegations": [
        "meth", "drug", "substance", "drug screen", "random screen", "urinalysis",
        "mental health", "psychological", "evaluation", "assessment", "manic", "paranoid",
    ],
    "hearsay_evidence_rules": [
        "hearsay", "foundation", "authentication", "best evidence", "relevance",
        "objection", "inadmissible", "excluded", "record", "transcript",
    ],
    "perjury_falsehood": [
        "perjury", "false", "misrepresent", "lied", "under oath", "affidavit", "sworn",
        "declaration", "not true", "fabricat",
    ],
    "parenting_time_custody": [
        "parenting time", "custody", "legal custody", "physical custody", "suspend",
        "supervised", "make-up parenting time", "FOC", "Friend of the Court",
        "minor child", "best interests", "722.27a", "722.23", "overnights",
    ],
}

NEGATIVE_CONNOTATION_WORDS = [
    "unstable", "erratic", "dangerous", "threatening", "harassing", "stalking",
    "manipulative", "abusive", "violent", "unfit", "drug", "meth", "paranoid",
    "delusional", "manic", "aggressive", "obsessed", "fixated",
]

###############################################################################
# Date extraction patterns
###############################################################################

MONTHS = (
    "january february march april may june july august september october november december"
).split()

DATE_PATTERNS = [
    re.compile(r"\b(?P<m>\d{1,2})[/-](?P<d>\d{1,2})[/-](?P<y>\d{2,4})\b"),
    re.compile(r"\b(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})\b"),
    re.compile(
        r"\b(?P<mon>(" + "|".join([m[:3] for m in MONTHS] + MONTHS) + r"))\.?\s+"
        r"(?P<d>\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(?P<y>\d{4})\b",
        re.IGNORECASE,
    ),
]

###############################################################################
# Helpers
###############################################################################

def now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def normalize_text(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = unicodedata.normalize("NFKC", s)
    return s

def try_decode_bytes(b: bytes) -> str:
    for enc in ("utf-8", "utf-16", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return b.decode(enc)
        except Exception:
            pass
    return b.decode("latin-1", errors="replace")

def match_any_glob(name: str, globs: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(name.lower(), g.lower()) for g in globs)

def load_ignore_file(root: Path, filename: str = ".harvestignore") -> List[str]:
    p = root / filename
    if not p.exists():
        return []
    try:
        lines = [ln.strip() for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines()]
        return [ln for ln in lines if ln and not ln.startswith("#")]
    except Exception:
        return []

def should_skip_dir(dir_path: Path, skip_names: set, ignore_globs: List[str]) -> bool:
    n = dir_path.name
    if n in skip_names:
        return True
    for pat in ignore_globs:
        if pat.endswith("/"):
            pat2 = pat[:-1]
            if fnmatch.fnmatch(n, pat2) or fnmatch.fnmatch(str(dir_path).replace("\\", "/"), pat2):
                return True
    return False

def should_skip_file(file_path: Path, skip_file_globs: Sequence[str], ignore_globs: List[str]) -> bool:
    n = file_path.name
    if match_any_glob(n, skip_file_globs):
        return True
    sp = str(file_path).replace("\\", "/")
    for pat in ignore_globs:
        if pat.endswith("/"):
            continue
        if fnmatch.fnmatch(n, pat) or fnmatch.fnmatch(sp, pat):
            return True
    return False

###############################################################################
# Text extraction
###############################################################################

def extract_text_txt_like(path: Path, max_chars: int = 2_000_000) -> str:
    b = path.read_bytes()
    s = try_decode_bytes(b)
    s = normalize_text(s)
    if len(s) > max_chars:
        s = s[:max_chars] + "\n\n[TRUNCATED]"
    return s

def extract_text_docx_stdlib(path: Path, max_chars: int = 2_000_000) -> str:
    try:
        import docx  # python-docx
        d = docx.Document(str(path))
        paras = [p.text for p in d.paragraphs]
        s = "\n".join([p for p in paras if p.strip()])
        s = normalize_text(s)
        if len(s) > max_chars:
            s = s[:max_chars] + "\n\n[TRUNCATED]"
        return s
    except Exception:
        pass

    with zipfile.ZipFile(path, "r") as z:
        cand = None
        for name in ("word/document.xml", "word/document2.xml"):
            if name in z.namelist():
                cand = name
                break
        if not cand:
            return ""
        xml = try_decode_bytes(z.read(cand))
        xml = xml.replace("</w:p>", "\n").replace("</w:tbl>", "\n")
        txt = re.sub(r"<[^>]+>", "", xml)
        txt = normalize_text(txt)
        txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
        if len(txt) > max_chars:
            txt = txt[:max_chars] + "\n\n[TRUNCATED]"
        return txt

def extract_text_pdf(path: Path, max_chars: int = 2_000_000) -> str:
    for modname in ("pypdf", "PyPDF2"):
        try:
            m = __import__(modname)
            Reader = getattr(m, "PdfReader", None)
            if Reader is None and modname == "PyPDF2":
                Reader = getattr(m, "PdfFileReader", None)
            if Reader is None:
                continue
            reader = Reader(str(path))
            texts = []
            pages = getattr(reader, "pages", None)
            if pages is None:
                pages = [reader.getPage(i) for i in range(reader.getNumPages())]
            for pg in pages:
                try:
                    t = pg.extract_text() if hasattr(pg, "extract_text") else pg.extractText()
                except Exception:
                    t = ""
                if t:
                    texts.append(t)
            s = "\n".join(texts)
            s = normalize_text(s)
            if len(s) > max_chars:
                s = s[:max_chars] + "\n\n[TRUNCATED]"
            return s
        except Exception:
            continue

    try:
        cmd = ["pdftotext", "-layout", str(path), "-"]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if p.returncode == 0 and p.stdout:
            s = try_decode_bytes(p.stdout)
            s = normalize_text(s)
            if len(s) > max_chars:
                s = s[:max_chars] + "\n\n[TRUNCATED]"
            return s
    except Exception:
        pass

    return ""

###############################################################################
# Analysis
###############################################################################

def find_dates(text: str) -> List[str]:
    out: List[str] = []
    for rx in DATE_PATTERNS:
        for m in rx.finditer(text):
            gd = m.groupdict()
            try:
                if "mon" in gd:
                    mon = gd["mon"].lower().rstrip(".")
                    mon_full = None
                    for mm in MONTHS:
                        if mon == mm or mon == mm[:3]:
                            mon_full = mm
                            break
                    if not mon_full:
                        continue
                    month = MONTHS.index(mon_full) + 1
                    day = int(gd["d"])
                    year = int(gd["y"])
                    dt = _dt.date(year, month, day)
                else:
                    month = int(gd["m"])
                    day = int(gd["d"])
                    year = int(gd["y"])
                    if year < 100:
                        year += 2000 if year < 70 else 1900
                    dt = _dt.date(year, month, day)
                out.append(dt.isoformat())
            except Exception:
                continue
    return sorted(set(out))

def keyword_hits(text_lc: str) -> Dict[str, int]:
    hits: Dict[str, int] = {}
    for cat, kws in KEYWORDS.items():
        c = 0
        for kw in kws:
            c += text_lc.count(kw.lower())
        if c:
            hits[cat] = c
    return hits

def negative_connotation_hits(text_lc: str) -> Dict[str, int]:
    hits = {}
    for w in NEGATIVE_CONNOTATION_WORDS:
        c = text_lc.count(w.lower())
        if c:
            hits[w] = c
    return hits

def extract_order_snippets(text: str, max_snips: int = 30) -> List[str]:
    lines = text.splitlines()
    snips: List[str] = []
    trigger = re.compile(r"\b(IT IS ORDERED|IT IS FURTHER ORDERED|ORDERED|JUDGMENT|ADJUDGED)\b", re.IGNORECASE)
    for i, ln in enumerate(lines):
        if trigger.search(ln):
            start = max(0, i - 2)
            end = min(len(lines), i + 6)
            block = "\n".join(lines[start:end]).strip()
            if block and block not in snips:
                snips.append(block)
                if len(snips) >= max_snips:
                    break
    return snips

###############################################################################
# Data model + Output
###############################################################################

@dataclass
class FileRecord:
    kind: str
    path: str
    root: str
    rel: str
    size_bytes: int
    mtime_iso: str
    sha256: Optional[str]
    ext: str
    extracted_chars: int
    dates: List[str]
    keyword_hits: Dict[str, int]
    negative_terms: Dict[str, int]
    order_snips: List[str]
    errors: List[str]

def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def write_csv(path: Path, rows: List[FileRecord]) -> None:
    fieldnames = [
        "kind","path","root","rel","size_bytes","mtime_iso","sha256","ext","extracted_chars",
        "dates","keyword_hits","negative_terms","order_snips","errors"
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            d = asdict(r)
            d["dates"] = ";".join(r.dates)
            d["keyword_hits"] = json.dumps(r.keyword_hits, ensure_ascii=False)
            d["negative_terms"] = json.dumps(r.negative_terms, ensure_ascii=False)
            d["order_snips"] = json.dumps(r.order_snips, ensure_ascii=False)
            d["errors"] = json.dumps(r.errors, ensure_ascii=False)
            w.writerow(d)

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def best_out_dir(base: Optional[str], runner_root: Path) -> Path:
    ts = now_stamp()
    if base:
        b = Path(base)
        ensure_dir(b)
        return b / ts
    cand = runner_root / ".gemini" / "out" / ts
    try:
        ensure_dir(cand)
        return cand
    except Exception:
        cand2 = runner_root / f"harvest_out_{ts}"
        ensure_dir(cand2)
        return cand2

def summarize_run(records: List[FileRecord]) -> Dict[str, object]:
    by_ext: Dict[str, int] = {}
    total_bytes = 0
    flagged = 0
    date_set = set()
    top_keyword_cats: Dict[str, int] = {}
    top_neg: Dict[str, int] = {}
    for r in records:
        by_ext[r.ext] = by_ext.get(r.ext, 0) + 1
        total_bytes += r.size_bytes
        if r.keyword_hits or r.negative_terms:
            flagged += 1
        for d in r.dates:
            date_set.add(d)
        for k, v in r.keyword_hits.items():
            top_keyword_cats[k] = top_keyword_cats.get(k, 0) + v
        for k, v in r.negative_terms.items():
            top_neg[k] = top_neg.get(k, 0) + v

    top_keyword = sorted(top_keyword_cats.items(), key=lambda x: x[1], reverse=True)[:15]
    top_neg2 = sorted(top_neg.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "files_total": len(records),
        "total_bytes": total_bytes,
        "by_ext": dict(sorted(by_ext.items(), key=lambda x: x[0])),
        "flagged_files": flagged,
        "date_min": min(date_set) if date_set else None,
        "date_max": max(date_set) if date_set else None,
        "top_keyword_categories": top_keyword,
        "top_negative_terms": top_neg2,
    }

def write_report(out_dir: Path, run_meta: Dict[str, object], records: List[FileRecord]) -> None:
    summary = summarize_run(records)

    def fmt_bytes(n: int) -> str:
        x = float(n)
        for unit in ("B","KB","MB","GB","TB"):
            if x < 1024:
                return f"{x:.0f} {unit}"
            x /= 1024
        return f"{x:.1f} PB"

    lines: List[str] = []
    lines.append("# Harvest Run Report\n")
    lines.append(f"- started: {run_meta['started_iso']}")
    lines.append(f"- runner_root: {run_meta['runner_root']}")
    lines.append(f"- roots: {', '.join(run_meta['roots'])}")
    lines.append(f"- out_dir: {str(out_dir)}\n")
    lines.append("## Summary\n")
    lines.append(f"- files_total: {summary['files_total']}")
    lines.append(f"- total_bytes: {fmt_bytes(int(summary['total_bytes']))}")
    lines.append(f"- flagged_files: {summary['flagged_files']}")
    lines.append(f"- date_range: {summary['date_min']} → {summary['date_max']}\n")

    lines.append("### By extension\n")
    for ext, cnt in (summary["by_ext"] or {}).items():
        lines.append(f"- {ext}: {cnt}")

    lines.append("\n### Top keyword categories (counts)\n")
    for k, v in summary["top_keyword_categories"]:
        lines.append(f"- {k}: {v}")

    lines.append("\n### Top negative terms (counts)\n")
    for k, v in summary["top_negative_terms"]:
        lines.append(f"- {k}: {v}")

    lines.append("\n## High-signal snippets (order language)\n")
    snip_count = 0
    for r in records:
        if r.order_snips:
            lines.append(f"\n### {r.rel}\n")
            for sn in r.order_snips[:5]:
                lines.append("```")
                lines.append(sn.strip())
                lines.append("```")
                snip_count += 1
                if snip_count >= 30:
                    break
        if snip_count >= 30:
            break
    if snip_count == 0:
        lines.append("\n(No order-language snippets found by heuristic search.)\n")

    lines.append("\n## Next steps (for the LLM)\n")
    lines.append("- Use INVENTORY.csv + LOG.jsonl as the record spine.")
    lines.append("- Build a chronological timeline from extracted dates (DATE_INDEX.csv).")
    lines.append("- For any legal proposition or quote, require authority pinpoints and verify via primary sources.")
    lines.append("- Treat all extracted “signals” as candidates until verified against the original documents.\n")

    (out_dir / "RUN_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

def write_next_prompt(out_dir: Path, run_meta: Dict[str, object]) -> None:
    prompt = f"""# NEXT_PROMPT — AutoHarvest synthesis

You are an expert litigation analyst / drafting assistant (Michigan-first). You MUST:

1) Read the run outputs:
   - {str(out_dir / "RUN_REPORT.md")}
   - {str(out_dir / "INVENTORY.csv")}
   - {str(out_dir / "LOG.jsonl")}
   - {str(out_dir / "DATE_INDEX.csv")}

2) Build a structured case-relevant database (do NOT invent facts):
   - Chronological timeline: event_date, doc_path, snippet pointer, actor, lane (MEEK2/3/4), confidence.
   - Issue grid: due process / notice / hearing / evidence exclusion / bias / contempt / PPO / parenting-time.
   - Candidate “negative connotation” statements with doc pointers (path + snippet).

3) Output ONLY these artifacts (label DRAFT if drafting):
   - CASE_STATE (≤25 lines) + Delta
   - ExhibitMatrix (doc pointer + foundation notes)
   - ContradictionMap (claims vs record)
   - Deadlines/Service tracker (if any dates imply deadlines)
   - Single Best Next Action (SBNA)

Hard rules:
- No invented facts. If missing, output UNKNOWN + acquisition plan.
- Do not quote rules/caselaw word-for-word unless verified against primary sources.
- Treat the record as adversarial; rebut every negative statement with record-grounded analysis.

Run meta:
- roots: {', '.join(run_meta['roots'])}
- started: {run_meta['started_iso']}
"""
    (out_dir / "NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")

def write_date_index(out_dir: Path, records: List[FileRecord]) -> None:
    rows: List[Tuple[str, str, str]] = []
    for r in records:
        for d in r.dates:
            rows.append((d, r.rel, r.path))
    rows.sort(key=lambda x: (x[0], x[1]))
    p = out_dir / "DATE_INDEX.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date_iso", "rel_path", "path"])
        w.writerows(rows)

###############################################################################
# File scanning
###############################################################################

def iter_files(roots: List[Path],
               max_mb: int,
               skip_dirs: set,
               skip_file_globs: Sequence[str],
               ignore_globs: List[str],
               include_archives: bool) -> Iterator[Tuple[str, Path, Optional[str]]]:
    max_bytes = max_mb * 1024 * 1024

    for root in roots:
        ignore_from_root = load_ignore_file(root)
        all_ignore = ignore_globs + ignore_from_root

        for dirpath, dirnames, filenames in os.walk(root):
            d = Path(dirpath)
            pruned = []
            for dn in list(dirnames):
                dp = d / dn
                if should_skip_dir(dp, skip_dirs, all_ignore):
                    continue
                pruned.append(dn)
            dirnames[:] = pruned

            for fn in filenames:
                fp = d / fn
                if should_skip_file(fp, skip_file_globs, all_ignore):
                    continue

                ext = fp.suffix.lower()

                if ext in ARCHIVE_EXTS and include_archives:
                    try:
                        if fp.stat().st_size > max_bytes:
                            yield ("file", fp, None)
                            continue
                        with zipfile.ZipFile(fp, "r") as z:
                            for name in z.namelist():
                                if name.endswith("/"):
                                    continue
                                mext = Path(name).suffix.lower()
                                if mext not in DEFAULT_ALLOWED_EXTS:
                                    continue
                                try:
                                    info = z.getinfo(name)
                                    if info.file_size > max_bytes:
                                        continue
                                except Exception:
                                    continue
                                yield ("zip_member", fp, name)
                    except Exception:
                        yield ("file", fp, None)
                    continue

                if ext not in DEFAULT_ALLOWED_EXTS:
                    continue

                yield ("file", fp, None)

###############################################################################
# Main runner
###############################################################################

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="harvest_runner.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    ap.add_argument("--root", action="append", default=[],
                    help="Root directory to scan. Can be repeated. If omitted, uses current directory.")
    ap.add_argument("--out", default=None,
                    help="Base output directory. Default: <cwd>/.gemini/out/<timestamp>.")
    ap.add_argument("--include-archives", action="store_true",
                    help="If set, enumerate .zip members and harvest allowed text-like files within.")
    ap.add_argument("--max-mb", type=int, default=120,
                    help="Skip extracting text from any single file/member larger than this many MB (still inventoried).")
    ap.add_argument("--hash", type=int, default=0,
                    help="Compute SHA-256 for on-disk files (0/1). Default 0.")
    ap.add_argument("--extract-max-chars", type=int, default=2_000_000,
                    help="Max chars to keep per extracted text.")
    ap.add_argument("--write-text", type=int, default=0,
                    help="If 1, write extracted text per file under out_dir/text/ (can be large).")
    args = ap.parse_args(argv)

    started = _dt.datetime.now().isoformat(timespec="seconds")
    runner_root = Path.cwd()

    roots: List[Path] = [Path(r).expanduser() for r in args.root] if args.root else [runner_root]
    roots = [r for r in roots if r.exists()]
    if not roots:
        print("No valid --root paths exist.", file=sys.stderr)
        return 2

    out_dir = best_out_dir(args.out, runner_root)
    ensure_dir(out_dir)

    ignore_globs: List[str] = [
        "**/AppData/**", "**/ProgramData/**", "**/Windows/**",
        "**/.git/**", "**/node_modules/**", "**/__pycache__/**",
    ]

    skip_dirs = set(DEFAULT_SKIP_DIR_NAMES)
    records: List[FileRecord] = []
    log_rows: List[dict] = []
    text_dir = out_dir / "text"
    if args.write_text:
        ensure_dir(text_dir)

    max_bytes = args.max_mb * 1024 * 1024

    for kind, fp, member in iter_files(
        roots=roots,
        max_mb=args.max_mb,
        skip_dirs=skip_dirs,
        skip_file_globs=DEFAULT_SKIP_FILE_GLOBS,
        ignore_globs=ignore_globs,
        include_archives=bool(args.include_archives),
    ):
        errors: List[str] = []
        ext = fp.suffix.lower()

        root_for_rel = None
        for r in roots:
            try:
                fp.resolve().relative_to(r.resolve())
                root_for_rel = r
                break
            except Exception:
                continue
        if root_for_rel is None:
            root_for_rel = roots[0]

        virt_path = str(fp) if kind == "file" else f"zip://{fp}!{member}"
        rel = safe_rel(fp, root_for_rel)
        if kind == "zip_member":
            rel = f"{rel}!{member}"

        size_bytes = 0
        mtime_iso = ""
        try:
            st = fp.stat()
            size_bytes = int(st.st_size)
            mtime_iso = _dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
        except Exception as e:
            errors.append(f"stat_error:{e.__class__.__name__}:{e}")

        sha = None
        if args.hash and kind == "file" and fp.exists():
            try:
                if size_bytes <= max_bytes:
                    sha = sha256_file(fp)
            except Exception as e:
                errors.append(f"hash_error:{e.__class__.__name__}:{e}")

        text = ""
        extracted_chars = 0
        dates: List[str] = []
        kw_hits: Dict[str, int] = {}
        neg_hits: Dict[str, int] = {}
        order_snips: List[str] = []

        can_extract = True
        if kind == "file" and size_bytes and size_bytes > max_bytes:
            can_extract = False

        if can_extract:
            try:
                if kind == "zip_member":
                    with zipfile.ZipFile(fp, "r") as z:
                        b = z.read(member)  # type: ignore[arg-type]
                    tmp_ext = Path(member).suffix.lower()
                    if tmp_ext in {".txt", ".md", ".csv", ".tsv", ".json", ".log", ".xml", ".html", ".htm"}:
                        text = normalize_text(try_decode_bytes(b))
                    elif tmp_ext == ".docx":
                        with zipfile.ZipFile(io.BytesIO(b), "r") as dz:
                            cand = None
                            for name in ("word/document.xml", "word/document2.xml"):
                                if name in dz.namelist():
                                    cand = name
                                    break
                            if cand:
                                xml = try_decode_bytes(dz.read(cand))
                                xml = xml.replace("</w:p>", "\n").replace("</w:tbl>", "\n")
                                txt = re.sub(r"<[^>]+>", "", xml)
                                text = normalize_text(re.sub(r"\n{3,}", "\n\n", txt).strip())
                else:
                    if ext in {".txt", ".md", ".csv", ".tsv", ".json", ".log", ".xml", ".html", ".htm", ".rtf"}:
                        text = extract_text_txt_like(fp, max_chars=args.extract_max_chars)
                    elif ext == ".docx":
                        text = extract_text_docx_stdlib(fp, max_chars=args.extract_max_chars)
                    elif ext == ".pdf":
                        text = extract_text_pdf(fp, max_chars=args.extract_max_chars)
            except Exception as e:
                errors.append(f"extract_error:{e.__class__.__name__}:{e}")
                text = ""

        if text:
            extracted_chars = len(text)
            tlc = text.lower()
            dates = find_dates(text)
            kw_hits = keyword_hits(tlc)
            neg_hits = negative_connotation_hits(tlc)
            order_snips = extract_order_snippets(text, max_snips=10)

            if args.write_text:
                safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", rel)[:180]
                (text_dir / f"{safe_name}.txt").write_text(text, encoding="utf-8")

        rec = FileRecord(
            kind=kind,
            path=virt_path,
            root=str(root_for_rel),
            rel=rel,
            size_bytes=size_bytes,
            mtime_iso=mtime_iso,
            sha256=sha,
            ext=(Path(member).suffix.lower() if kind == "zip_member" else ext),
            extracted_chars=extracted_chars,
            dates=dates,
            keyword_hits=kw_hits,
            negative_terms=neg_hits,
            order_snips=order_snips,
            errors=errors,
        )
        records.append(rec)
        log_rows.append(asdict(rec))

    run_meta = {
        "started_iso": started,
        "runner_root": str(runner_root),
        "roots": [str(r) for r in roots],
        "args": vars(args),
        "python": sys.version,
        "platform": sys.platform,
        "records": len(records),
    }

    (out_dir / "META.json").write_text(json.dumps(run_meta, indent=2, ensure_ascii=False), encoding="utf-8")
    write_jsonl(out_dir / "LOG.jsonl", log_rows)
    write_csv(out_dir / "INVENTORY.csv", records)
    write_date_index(out_dir, records)
    write_report(out_dir, run_meta, records)
    write_next_prompt(out_dir, run_meta)

    print(str(out_dir))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
