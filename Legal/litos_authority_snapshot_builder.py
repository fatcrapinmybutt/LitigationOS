#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LitigationOS Tool: AuthoritySnapshot Builder (offline; pin-first; no hallucinated holdings)
What it does (FIRST-PASS, PROVABLE):
  1) Reads a LawPack manifest (SCHEMA/authority/law_pack_manifest.schema.json), OR builds a manifest from --inputs.
  2) Extracts text (PDF via pypdf, txt/md/html as text) into a work folder (optional).
  3) Scans extracted text for Michigan authority citation patterns (MCR/MCL/MRE) and builds:
     - authority_index.jsonl (AuthorityRef rows; each requires pins)
     - authority_pin_map.jsonl (pin locators: file, page marker if known, line number, char offsets)
  4) Emits receipt.json (AuthoritySnapshotReceipt).
Non-goals:
  - This tool does NOT “understand” rule structure. It does NOT invent effective dates or holdings.
  - It produces pointers/pins so later layers (QuoteLock + manual verification) can promote to VERIFIED quotes.

Safety:
  - Read-only on inputs.
  - Writes only under --outdir.

Usage:
  # Build from inputs directly (MIXED pack):
  python TOOLS/litos_authority_snapshot_builder.py --inputs SOURCES/extracted/*.txt --outdir AUTHORITY/snapshots --snapshot-id SNAP_20260118_0001

  # Build from an existing pack manifest:
  python TOOLS/litos_authority_snapshot_builder.py --pack-manifest AUTHORITY/packs/pack_x/manifest.json --outdir AUTHORITY/snapshots --snapshot-id SNAP_...
"""
from __future__ import annotations
import argparse, json, os, re, sys, pathlib, hashlib, datetime, traceback
from typing import Dict, List, Tuple, Iterable, Optional

CIT_PATTERNS = [
  ("MCR", re.compile(r"\bMCR\s+(\d+(?:\.\d+)?(?:\([A-Za-z0-9]+\))*)\b")),
  ("MCL", re.compile(r"\bMCL\s+(\d+(?:\.\d+)?[a-zA-Z]?)\b")),
  ("MRE", re.compile(r"\bMRE\s+(\d+[A-Za-z]?)\b")),
]

def utc_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def die(msg: str, code: int = 2) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(code)

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="*", default=[], help="Input files (txt/md/html/pdf) to scan if no --pack-manifest is supplied.")
    ap.add_argument("--pack-manifest", default="", help="Path to LawPack manifest.json (preferred).")
    ap.add_argument("--outdir", required=True, help="Output root dir (will create snapshot subdir).")
    ap.add_argument("--snapshot-id", required=True, help="Snapshot id (directory name).")
    ap.add_argument("--extract-pdfs", action="store_true", help="If inputs include PDFs, extract them to text under snapshot/work/ before scanning.")
    ap.add_argument("--max-pages", type=int, default=0, help="If extracting PDFs, cap pages (0=all).")
    ap.add_argument("--context-chars", type=int, default=180, help="Chars to capture around each match for text_pointer snippet.")
    ap.add_argument("--strict", action="store_true", help="Fail if any input is missing/unreadable.")
    return ap.parse_args()

def load_manifest(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"Unable to read manifest: {path} ({e})")

def infer_media_type(p: pathlib.Path) -> str:
    ext = p.suffix.lower().lstrip(".")
    if ext in ("pdf","txt","md","html","htm","docx"):
        return ext
    return "other"

def build_manifest_from_inputs(inputs: List[pathlib.Path]) -> dict:
    srcs = []
    for i,p in enumerate(inputs, start=1):
        src_id = f"src_{i:04d}"
        srcs.append({
            "source_id": src_id,
            "path": str(p),
            "media_type": infer_media_type(p),
            "origin": "operator_saved",
            "url": "",
            "sha256": sha256_bytes(p.read_bytes()) if p.exists() and p.is_file() else "",
            "effective_start": None,
            "effective_end": None,
            "tags": []
        })
    return {
        "pack_id": "pack_mixed_auto",
        "pack_kind": "MIXED",
        "created_utc": utc_now(),
        "notes": "Auto-built from --inputs by litos_authority_snapshot_builder.py",
        "sources": srcs
    }

def pdf_to_text(pdf_path: pathlib.Path, max_pages: int) -> str:
    try:
        from pypdf import PdfReader
    except Exception as e:
        die(f"Missing dependency pypdf/PyPDF2: {e}")
    reader = PdfReader(str(pdf_path))
    pages = reader.pages
    limit = len(pages) if max_pages <= 0 else min(len(pages), max_pages)
    out = []
    for i in range(limit):
        try:
            t = pages[i].extract_text() or ""
        except Exception:
            t = ""
        t = t.replace("\r\n", "\n").replace("\r", "\n")
        out.append(f"=== PAGE {i+1} ===\n{t}".strip())
    return "\n\n".join(out).strip() + "\n"

def read_text_any(path: pathlib.Path, extract_pdfs: bool, max_pages: int, workdir: pathlib.Path) -> Tuple[str, Optional[pathlib.Path]]:
    mt = infer_media_type(path)
    if mt == "pdf" and extract_pdfs:
        workdir.mkdir(parents=True, exist_ok=True)
        out_txt = workdir / (path.stem + ".txt")
        out_txt.write_text(pdf_to_text(path, max_pages), encoding="utf-8")
        return out_txt.read_text(encoding="utf-8", errors="ignore"), out_txt
    if mt in ("txt","md","html","htm"):
        return path.read_text(encoding="utf-8", errors="ignore"), None
    if mt == "pdf" and not extract_pdfs:
        # attempt direct extract anyway
        return pdf_to_text(path, max_pages), None
    # fallback: treat as bytes and decode lossily
    try:
        b = path.read_bytes()
        return b.decode("utf-8", errors="ignore"), None
    except Exception:
        return "", None

def scan_text_for_cites(text: str) -> List[Tuple[str,str,int,int,int]]:
    """
    Returns list of (kind, cite, page, start, end) where page is derived from markers if present; 0 if unknown.
    """
    results = []
    # build page boundaries based on markers
    # We split by markers; keep running page index.
    pages = [(0, text)]
    if "=== PAGE " in text:
        parts = re.split(r"=== PAGE (\d+) ===\n", text)
        # parts like [before, num, content, num, content, ...]
        pages = []
        it = iter(parts)
        pre = next(it, "")
        if pre.strip():
            pages.append((0, pre))
        while True:
            try:
                num = next(it)
                content = next(it)
            except StopIteration:
                break
            try:
                pnum = int(num)
            except Exception:
                pnum = 0
            pages.append((pnum, content))
    for pnum, ptxt in pages:
        for kind, rx in CIT_PATTERNS:
            for m in rx.finditer(ptxt):
                cite = m.group(1)
                results.append((kind, cite, pnum, m.start(), m.end()))
    return results

def make_pin_id(snapshot_id: str, source_id: str, kind: str, cite: str, pnum: int, line_no: int, start: int, end: int) -> str:
    raw = f"{snapshot_id}|{source_id}|{kind}|{cite}|p{pnum}|l{line_no}|{start}-{end}"
    return "pin_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

def make_auth_id(kind: str, cite: str, source_id: str) -> str:
    raw = f"{kind}|{cite}|{source_id}"
    return "auth_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

def context_snip(line: str, start: int, end: int, ctx: int) -> str:
    a = max(0, start - ctx)
    b = min(len(line), end + ctx)
    return line[a:b].replace("\n"," ").strip()

def main() -> int:
    ns = parse_args()
    outroot = pathlib.Path(ns.outdir)
    snapdir = outroot / ns.snapshot_id
    snapdir.mkdir(parents=True, exist_ok=True)
    workdir = snapdir / "work"
    # Determine inputs
    manifest = None
    inputs: List[Tuple[str, pathlib.Path]] = []
    if ns.pack_manifest:
        mpath = pathlib.Path(ns.pack_manifest)
        if not mpath.exists():
            die(f"Manifest not found: {mpath}")
        manifest = load_manifest(mpath)
        for s in manifest.get("sources", []):
            sid = s.get("source_id","")
            p = pathlib.Path(s.get("path",""))
            inputs.append((sid, p))
    else:
        if not ns.inputs:
            die("Provide --pack-manifest or --inputs")
        ipaths = [pathlib.Path(p) for p in ns.inputs]
        manifest = build_manifest_from_inputs(ipaths)
        for s in manifest["sources"]:
            inputs.append((s["source_id"], pathlib.Path(s["path"])))

    # Input digest for receipt
    dig_acc = hashlib.sha256()
    for sid, p in inputs:
        dig_acc.update(sid.encode("utf-8")+b"\n")
        dig_acc.update(str(p).encode("utf-8")+b"\n")
        if p.exists() and p.is_file():
            dig_acc.update(hashlib.sha256(p.read_bytes()).digest())
        else:
            if ns.strict:
                die(f"Missing input file: {p}")
    inputs_sha = dig_acc.hexdigest()

    index_path = snapdir / "authority_index.jsonl"
    pins_path = snapdir / "authority_pin_map.jsonl"
    err_path = snapdir / "errors.jsonl"
    stats_path = snapdir / "stats.json"
    receipt_path = snapdir / "receipt.json"

    # Build index/pins
    seen_auth = {}  # auth_id -> dict(row)
    pin_rows = []
    err_rows = []
    stats = {"snapshot_id": ns.snapshot_id, "files_scanned": 0, "matches": 0, "authority_refs": 0, "pins": 0}

    for source_id, path in inputs:
        if not path.exists() or not path.is_file():
            msg = f"Missing: {path}"
            err_rows.append({"kind":"MISSING_INPUT","source_id":source_id,"path":str(path),"msg":msg,"ts":utc_now()})
            if ns.strict:
                die(msg)
            continue
        try:
            text, extracted_path = read_text_any(path, ns.extract_pdfs, ns.max_pages, workdir)
            if not text.strip():
                raise ValueError("Empty text after extraction")
            stats["files_scanned"] += 1
            # line-based scan for better pinning (line numbers)
            for ln_no, line in enumerate(text.splitlines(), start=1):
                for kind, rx in CIT_PATTERNS:
                    for m in rx.finditer(line):
                        cite = m.group(1)
                        auth_id = make_auth_id(kind, cite, source_id)
                        # pin
                        pnum = 0
                        # if workdir extract has page markers, derive pnum from nearby marker in the file:
                        # (approx) we don't have page context in single line, so keep 0 unless markers are in the line
                        if "=== PAGE " in line:
                            try:
                                pnum = int(re.findall(r"=== PAGE (\d+) ===", line)[0])
                            except Exception:
                                pnum = 0
                        pin_id = make_pin_id(ns.snapshot_id, source_id, kind, cite, pnum, ln_no, m.start(), m.end())
                        pin_rows.append({
                            "pin_id": pin_id,
                            "snapshot_id": ns.snapshot_id,
                            "source_id": source_id,
                            "source_path": str(extracted_path or path),
                            "page": pnum,
                            "line": ln_no,
                            "start": m.start(),
                            "end": m.end(),
                            "snippet": context_snip(line, m.start(), m.end(), ns.context_chars)
                        })
                        stats["matches"] += 1
                        # authority ref
                        if auth_id not in seen_auth:
                            seen_auth[auth_id] = {
                                "authority_ref_id": auth_id,
                                "kind": kind,
                                "citation_key": f"{kind} {cite}",
                                "section_path": cite,
                                "effective_start": None,
                                "effective_end": None,
                                "source_id": source_id,
                                "source_path": str(path),
                                "text_pointer": str(extracted_path or path),
                                "pin_ids": [pin_id],
                                "meta": {"pack_id": manifest.get("pack_id"), "pack_kind": manifest.get("pack_kind")}
                            }
                        else:
                            seen_auth[auth_id]["pin_ids"].append(pin_id)
        except Exception as e:
            err_rows.append({"kind":"EXTRACT_FAIL","source_id":source_id,"path":str(path),"msg":str(e),"ts":utc_now()})
            if ns.strict:
                raise

    # Write outputs deterministically
    with index_path.open("w", encoding="utf-8") as f:
        for k in sorted(seen_auth.keys()):
            row = seen_auth[k]
            # dedupe pins while preserving order
            seen = set()
            pins = []
            for pid in row["pin_ids"]:
                if pid not in seen:
                    pins.append(pid)
                    seen.add(pid)
            row["pin_ids"] = pins
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with pins_path.open("w", encoding="utf-8") as f:
        # sort pins by source_id then line
        for r in sorted(pin_rows, key=lambda x: (x["source_id"], x["page"], x["line"], x["start"])):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with err_path.open("w", encoding="utf-8") as f:
        for r in err_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    stats["authority_refs"] = len(seen_auth)
    stats["pins"] = len(pin_rows)
    stats_path.write_text(json.dumps(stats, indent=2, sort_keys=True), encoding="utf-8")

    receipt = {
        "snapshot_id": ns.snapshot_id,
        "generated_utc": utc_now(),
        "pack_manifest_path": ns.pack_manifest or "(auto-built)",
        "tool": "TOOLS/litos_authority_snapshot_builder.py",
        "tool_version": "v1",
        "inputs_sha256": inputs_sha,
        "outputs": {
            "authority_index_jsonl": str(index_path),
            "authority_pin_map_jsonl": str(pins_path),
            "errors_jsonl": str(err_path),
            "stats_json": str(stats_path)
        }
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    print(f"[OK] snapshot={ns.snapshot_id} files={stats['files_scanned']} refs={stats['authority_refs']} pins={stats['pins']} out={snapdir}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
