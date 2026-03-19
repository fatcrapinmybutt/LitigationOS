#!/usr/bin/env python3
"""
AUTO818 Cycle Runner — append-only canon builder.

Design goals:
- deterministic queue (nested ZIP traversal + stable sort)
- resumable (state.json)
- append-only canon file
- scope guard (exclude housing terms)
- optional OCR fallback when PDF text layer is empty

USAGE:
  python cycle_runner.py --input-zip "123Max Document.zip" --canon "CANON.txt" --state "state.json" --config "config.yaml"

This tool does NOT require internet.
"""

from __future__ import annotations
import argparse, io, json, os, time, hashlib, zipfile, tempfile, datetime
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Any
from pathlib import Path

# deps
import yaml
from tqdm import tqdm  # noqa: F401

# PDF: text-layer + render
import fitz  # PyMuPDF
from pypdf import PdfReader

# OCR
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

# DOCX
try:
    import docx
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

DEFAULT_EXCLUDE = ["shady oaks", "housing", "landlord", "lot 17"]

@dataclass(frozen=True)
class ZipPointer:
    chain: Tuple[str, ...]   # ["root.zip", "inner.zip", ...]
    member: str              # final file path inside last zip

@dataclass
class Config:
    exclude_keywords: List[str]
    ocr_enabled: bool
    tesseract_cmd: str
    max_cycles_per_run: int
    time_budget_seconds: int
    max_chars_per_doc: int
    pdf_pages_per_cycle: int

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def load_config(path: Path) -> Config:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    ex = data.get("scope_guard", {}).get("exclude_keywords", DEFAULT_EXCLUDE)
    ocr = data.get("ocr", {})
    runner = data.get("runner", {})
    return Config(
        exclude_keywords=[str(x).lower() for x in ex],
        ocr_enabled=bool(ocr.get("enabled", True)),
        tesseract_cmd=str(ocr.get("tesseract_cmd","") or "").strip(),
        max_cycles_per_run=int(runner.get("max_cycles_per_run", 25)),
        time_budget_seconds=int(runner.get("time_budget_seconds", 900)),
        max_chars_per_doc=int(runner.get("max_chars_per_doc", 250000)),
        pdf_pages_per_cycle=int(runner.get("pdf_pages_per_cycle", 3)),
    )

def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"version":"auto818_state_v1","cycle_current":0,"cycle_target":1000,"queue_built":False,"queue":[],"processed_sha256":[]}
    return json.loads(path.read_text(encoding="utf-8"))

def save_state(path: Path, state: Dict[str, Any]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(path)

def scope_excluded(name: str, exclude_keywords: List[str]) -> bool:
    s = name.lower()
    return any(k in s for k in exclude_keywords)

def is_zip_name(name: str) -> bool:
    return name.lower().endswith(".zip")

def build_recursive_queue(root_zip: Path, cfg: Config) -> List[ZipPointer]:
    """
    Deterministic queue of relevant files (PDF/DOCX/TXT/CSV/JSON/MD/XML/HTML) inside nested zips.
    Nested zips are traversed by reading bytes and opening via ZipFile(BytesIO).
    """
    targets_ext = {".pdf",".docx",".txt",".md",".csv",".json",".jsonl",".xml",".html"}
    queue: List[ZipPointer] = []

    def traverse(chain: List[str], zbytes: bytes, zlabel: str):
        try:
            with zipfile.ZipFile(io.BytesIO(zbytes), "r") as z:
                members_sorted = sorted(z.namelist(), key=lambda x: (x.count("/"), x.lower()))
                for m in members_sorted:
                    if m.endswith("/"):
                        continue
                    if scope_excluded(m, cfg.exclude_keywords):
                        continue
                    lower = m.lower()
                    ext = os.path.splitext(lower)[1]
                    if is_zip_name(lower):
                        try:
                            nb = z.read(m)
                            traverse(chain + [zlabel], nb, m)
                        except Exception:
                            continue
                    elif ext in targets_ext:
                        queue.append(ZipPointer(chain=tuple(chain + [zlabel]), member=m))
        except Exception:
            return

    with zipfile.ZipFile(root_zip,"r") as root:
        members_sorted = sorted(root.namelist(), key=lambda x: (x.count("/"), x.lower()))
        for m in members_sorted:
            if m.endswith("/"):
                continue
            if scope_excluded(m, cfg.exclude_keywords):
                continue
            lower = m.lower()
            ext = os.path.splitext(lower)[1]
            if is_zip_name(lower):
                try:
                    traverse([root_zip.name], root.read(m), m)
                except Exception:
                    continue
            elif ext in targets_ext:
                queue.append(ZipPointer(chain=(root_zip.name,), member=m))

    return sorted(queue, key=lambda zp: ("::".join(zp.chain).lower(), zp.member.lower()))

def resolve_pointer_to_bytes(root_zip: Path, zp: ZipPointer) -> Tuple[bytes, str]:
    chain = list(zp.chain)
    if not chain or chain[0] != root_zip.name:
        chain = [root_zip.name] + chain
    with zipfile.ZipFile(root_zip,"r") as z:
        cur = z
        for i in range(1, len(chain)):
            nm = chain[i]
            b = cur.read(nm)
            cur = zipfile.ZipFile(io.BytesIO(b), "r")
        out = cur.read(zp.member)
    return out, "::".join(chain) + "::" + zp.member

def extract_text_pdf(b: bytes, max_pages: int, cfg: Config) -> Tuple[str, Dict[str, Any]]:
    meta = {"method":"textlayer","pages_used":0,"ocr_used":False,"ocr_status":None}
    if max_pages < 1:
        return "", meta

    # pypdf text layer
    try:
        reader = PdfReader(io.BytesIO(b))
        use = min(len(reader.pages), max_pages)
        meta["pages_used"] = use
        parts = []
        for i in range(use):
            try:
                parts.append(reader.pages[i].extract_text() or "")
            except Exception:
                parts.append("")
        txt = "\n".join(parts).strip()
        if txt:
            return txt, meta
    except Exception:
        pass

    # pymupdf text extraction
    try:
        doc = fitz.open(stream=b, filetype="pdf")
        use = min(doc.page_count, max_pages)
        meta["pages_used"] = use
        parts = [(doc.load_page(i).get_text("text") or "") for i in range(use)]
        txt = "\n".join(parts).strip()
        if txt:
            meta["method"] = "pymupdf_text"
            return txt, meta
    except Exception:
        pass

    # OCR fallback
    if not cfg.ocr_enabled:
        meta["method"] = "no_ocr_enabled"
        meta["ocr_status"] = "OCR_DISABLED"
        return "", meta

    if not OCR_AVAILABLE:
        meta["method"] = "no_ocr_available"
        meta["ocr_status"] = "OCR_SKIPPED"
        return "", meta

    meta["method"] = "ocr"
    meta["ocr_used"] = True
    try:
        doc = fitz.open(stream=b, filetype="pdf")
        if doc.page_count < 1:
            meta["ocr_status"] = "no_pages"
            return "", meta
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=250)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        txt = (pytesseract.image_to_string(img) or "").strip()
        meta["ocr_status"] = "ok" if txt else "ocr_empty"
        return txt, meta
    except Exception as e:
        meta["ocr_status"] = f"ocr_error:{type(e).__name__}"
        return "", meta

def extract_text_docx(b: bytes) -> str:
    if not DOCX_AVAILABLE:
        return ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tf:
        tf.write(b)
        p = tf.name
    try:
        d = docx.Document(p)
        return "\n".join([para.text for para in d.paragraphs]).strip()
    finally:
        try:
            os.unlink(p)
        except Exception:
            pass

def extract_text_plain(b: bytes) -> str:
    for enc in ("utf-8","utf-8-sig","cp1252","latin-1"):
        try:
            return b.decode(enc, errors="replace")
        except Exception:
            continue
    return b.decode("utf-8", errors="replace")

def write_cycle(canon: Path, cycle_no: int, pointer: str, sha: str, kind: str, text: str, meta: Dict[str, Any], cfg: Config) -> None:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    header = f"\n\n=== CYCLE {cycle_no:04d} | {ts} UTC ===\nPOINTER: {pointer}\nSHA256: {sha}\nKIND: {kind}\nMETA: {json.dumps(meta, sort_keys=True)}\n"
    body = text
    if len(body) > cfg.max_chars_per_doc:
        body = body[:cfg.max_chars_per_doc] + "\n\n[TRUNCATED]\n"
    with canon.open("a", encoding="utf-8") as f:
        f.write(header)
        f.write(body)
        f.write("\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-zip", required=True)
    ap.add_argument("--canon", required=True)
    ap.add_argument("--state", default="state.json")
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()

    root_zip = Path(args.input_zip).expanduser().resolve()
    canon = Path(args.canon).expanduser().resolve()
    state_path = Path(args.state).expanduser().resolve()
    cfg_path = Path(args.config).expanduser().resolve()

    cfg = load_config(cfg_path)
    if cfg.tesseract_cmd and OCR_AVAILABLE:
        pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_cmd

    state = load_state(state_path)

    if not state.get("queue_built", False):
        q = build_recursive_queue(root_zip, cfg)
        state["queue"] = [{"chain": list(zp.chain), "member": zp.member} for zp in q]
        state["queue_built"] = True
        save_state(state_path, state)

    cycle_current = int(state.get("cycle_current", 0))
    cycle_target = int(state.get("cycle_target", 1000))
    processed = set(state.get("processed_sha256", []))

    start = time.time()
    cycles_done = 0

    queue = state.get("queue", [])

    for item in queue:
        if cycle_current >= cycle_target:
            break
        if cycles_done >= cfg.max_cycles_per_run:
            break
        if (time.time() - start) > cfg.time_budget_seconds:
            break

        zp = ZipPointer(chain=tuple(item["chain"]), member=item["member"])
        try:
            b, pointer = resolve_pointer_to_bytes(root_zip, zp)
        except Exception as e:
            cycle_current += 1
            cycles_done += 1
            meta = {"error": f"resolve_error:{type(e).__name__}"}
            write_cycle(canon, cycle_current, f"{'::'.join(zp.chain)}::{zp.member}", "NA", "ERROR", "", meta, cfg)
            continue

        sha = sha256_bytes(b)
        if sha in processed:
            continue

        ext = os.path.splitext(zp.member.lower())[1].lstrip(".") or "unknown"
        meta: Dict[str, Any] = {}
        try:
            if ext == "pdf":
                text, meta = extract_text_pdf(b, cfg.pdf_pages_per_cycle, cfg)
            elif ext == "docx":
                text = extract_text_docx(b)
            else:
                text = extract_text_plain(b)
        except Exception as e:
            text = ""
            meta = {"error": f"extract_error:{type(e).__name__}"}

        cycle_current += 1
        cycles_done += 1

        write_cycle(canon, cycle_current, pointer, sha, ext, text, meta, cfg)

        processed.add(sha)
        state["processed_sha256"] = sorted(list(processed))
        state["cycle_current"] = cycle_current
        state["last_run_utc"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        save_state(state_path, state)

    print(f"Run complete. cycles_done={cycles_done}, cycle_current={cycle_current}/{cycle_target}, canon={canon}")
    if cycle_current >= cycle_target:
        print("TARGET REACHED.")

if __name__ == "__main__":
    main()
