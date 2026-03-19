#!/usr/bin/env python3
"""
formos_cli.py - FormOS Upgrade v2

Local-only pipeline: scan + unzip + CAS dedup + extraction + form detection + instructions + specs + AKN + stacks + coverage.
No network calls. Extracted form text is stored locally (not emitted to chat).

Optional deps: pypdf, python-docx
Optional OCR: external tool (e.g., ocrmypdf) if enabled and present on PATH.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

PDF_TEXT_AVAILABLE = True
try:
    from pypdf import PdfReader
except Exception:
    PDF_TEXT_AVAILABLE = False

DOCX_AVAILABLE = True
try:
    import docx  # python-docx
except Exception:
    DOCX_AVAILABLE = False

GENERATOR_VERSION = "formos.v2.0.0"

def now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def deterministic_id(*parts: str, n: int = 24) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8", errors="ignore")).hexdigest()[:n]

def safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def guess_mime(path: Path) -> str:
    mt, _ = mimetypes.guess_type(str(path))
    return mt or "application/octet-stream"

def is_zip(path: Path) -> bool:
    return path.suffix.lower() == ".zip" and zipfile.is_zipfile(path)

def iter_files(root: Path) -> Iterable[Path]:
    skip = {".git", "__pycache__", "node_modules"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            yield Path(dirpath) / fn

@dataclass
class Config:
    roots: List[str]
    vault_root: str
    sqlite_db: str
    explode_zips: bool = True
    zip_staging_subdir: str = "05_ZIP_STAGING"
    max_zip_depth: int = 8
    extract_pdf_text: bool = True
    pdf_text_min_chars_per_page: int = 80
    enable_ocr: bool = False
    ocr_tool: str = "ocrmypdf"
    ocr_languages: str = "eng"
    rules: Dict = None

def load_config(path: Path) -> Config:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "rules" not in data or data["rules"] is None:
        data["rules"] = {"default_rulebank_paths": []}
    return Config(**data)

def connect_db(db_path: Path) -> sqlite3.Connection:
    safe_mkdir(db_path.parent)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL;")
    return con

def init_db(con: sqlite3.Connection, schema_path: Path) -> None:
    con.executescript(schema_path.read_text(encoding="utf-8"))
    con.commit()

def cas_store(vault_root: Path, src_path: Path, sha: str) -> Path:
    ext = src_path.suffix.lower().lstrip(".") or "bin"
    obj_dir = vault_root / "00_OBJECTS" / sha[:2]
    safe_mkdir(obj_dir)
    dest = obj_dir / f"{sha}.{ext}"
    if not dest.exists():
        shutil.copy2(src_path, dest)
    return dest

def explode_zip(zip_path: Path, out_dir: Path, depth: int, max_depth: int) -> None:
    if depth > max_depth:
        return
    safe_mkdir(out_dir)
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(out_dir)
    except Exception as ex:
        print(f"[WARN] unzip failed: {zip_path}: {ex}", file=sys.stderr)
        return
    for p in out_dir.rglob("*.zip"):
        if zipfile.is_zipfile(p):
            explode_zip(p, p.with_suffix(""), depth + 1, max_depth)

def pdf_extract_text_pages(pdf_path: Path, min_chars_per_page: int) -> Tuple[List[Dict], str, float, bool]:
    if not PDF_TEXT_AVAILABLE:
        return [], "", 0.0, True
    try:
        reader = PdfReader(str(pdf_path))
        pages: List[Dict] = []
        total_chars = 0
        low_pages = 0
        for i, pg in enumerate(reader.pages):
            try:
                txt = pg.extract_text() or ""
            except Exception:
                txt = ""
            cc = len(txt.strip())
            total_chars += cc
            if cc < min_chars_per_page:
                low_pages += 1
            pages.append({"page": i + 1, "text": txt, "char_count": cc})
        n = max(len(pages), 1)
        avg = total_chars / n
        quality = min(avg / 1500.0, 1.0)
        needs_ocr = (low_pages / n) > 0.5
        fulltext = "\n\n".join([f"---PAGE {p['page']:04d}---\n{p['text']}" for p in pages])
        return pages, fulltext, float(quality), bool(needs_ocr)
    except Exception as ex:
        print(f"[WARN] PDF extract failed: {pdf_path}: {ex}", file=sys.stderr)
        return [], "", 0.0, True

def docx_extract_text(docx_path: Path) -> str:
    if not DOCX_AVAILABLE:
        return ""
    try:
        d = docx.Document(str(docx_path))
        return "\n".join([p.text for p in d.paragraphs if p.text]).strip()
    except Exception as ex:
        print(f"[WARN] DOCX extract failed: {docx_path}: {ex}", file=sys.stderr)
        return ""

def run_ocr(cfg: Config, pdf_path: Path, out_pdf: Path) -> bool:
    if not cfg.enable_ocr:
        return False
    tool = cfg.ocr_tool
    if shutil.which(tool) is None:
        print(f"[WARN] OCR tool not found on PATH: {tool}", file=sys.stderr)
        return False
    try:
        safe_mkdir(out_pdf.parent)
        cmd = [tool, "--skip-text", "--language", cfg.ocr_languages, str(pdf_path), str(out_pdf)]
        cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if cp.returncode != 0:
            print(f"[WARN] OCR failed: {pdf_path}: {cp.stderr[:500]}", file=sys.stderr)
            return False
        return True
    except Exception as ex:
        print(f"[WARN] OCR exception: {pdf_path}: {ex}", file=sys.stderr)
        return False

FORM_CODE_RE = re.compile(r"\b(FOC|MC|DC|CC|PC|JC)\s*[-]?\s*(\d+[A-Za-z]?)\b", re.IGNORECASE)
REV_RE = re.compile(r"\b(\d{1,2}/\d{2}|\d{1,2}/\d{4})\b")

def guess_form_code_from_name(name: str) -> Optional[str]:
    m = FORM_CODE_RE.search(name)
    return f"{m.group(1).upper()} {m.group(2)}" if m else None

def guess_form_code_from_text(text: str) -> Optional[str]:
    m = FORM_CODE_RE.search(text)
    return f"{m.group(1).upper()} {m.group(2)}" if m else None

def guess_revision(text: str) -> Optional[str]:
    m = REV_RE.search(text)
    return m.group(1) if m else None

def guess_title(text: str) -> Optional[str]:
    lines = [ln.strip() for ln in text.splitlines()[:80] if ln.strip()]
    for ln in lines:
        if any(k in ln.lower() for k in ["motion", "petition", "summons", "notice", "complaint", "affidavit", "order"]):
            if 10 <= len(ln) <= 140:
                return ln
    for ln in lines:
        if 10 <= len(ln) <= 140:
            return ln
    return None

def guess_doctype(text: str, filename: str) -> str:
    s = (text[:4000] + " " + filename).lower()
    mapping = [
        ("affidavit", "affidavit"),
        ("petition", "petition"),
        ("application", "application"),
        ("motion", "motion"),
        ("summons", "summons"),
        ("complaint", "complaint"),
        ("notice", "notice"),
        ("order", "order"),
        ("judgment", "judgment"),
        ("brief", "brief"),
    ]
    for k, dt in mapping:
        if k in s:
            return dt
    return "submission"

def looks_like_form(filename: str, extracted_text: str) -> bool:
    name = filename.lower()
    if guess_form_code_from_name(name):
        return True
    lt = extracted_text.lower()
    cues = ["state court administrative office", "for office use only", "approved", "instructions", "case no."]
    hits = sum(1 for c in cues if c in lt)
    return hits >= 3

INSTR_CUES = [
    "instructions", "you must", "must be", "required", "attach", "separate sheet", "certificate of service",
    "do not write below", "for office use only"
]

def instruction_spans(fulltext: str) -> List[Dict]:
    lines = fulltext.splitlines()
    spans = []
    window = 12
    for i in range(0, len(lines)):
        chunk = "\n".join(lines[i:i+window]).lower()
        hits = sum(1 for c in INSTR_CUES if c in chunk)
        if hits >= 2:
            spans.append({"start_line": i, "end_line": min(i+window, len(lines)), "cue_hits": hits})
    merged = []
    for sp in spans:
        if not merged:
            merged.append(sp); continue
        last = merged[-1]
        if sp["start_line"] <= last["end_line"]:
            last["end_line"] = max(last["end_line"], sp["end_line"])
            last["cue_hits"] = max(last["cue_hits"], sp["cue_hits"])
        else:
            merged.append(sp)
    return merged[:200]

REQ_PATTERNS = [
    (re.compile(r"\battach\b", re.IGNORECASE), "ATTACHMENT_REQUIRED"),
    (re.compile(r"\bseparate sheet", re.IGNORECASE), "SEPARATE_SHEET_REQUIRED"),
    (re.compile(r"\bmust\b", re.IGNORECASE), "MANDATORY"),
    (re.compile(r"\brequired\b", re.IGNORECASE), "MANDATORY"),
    (re.compile(r"\bserve\b", re.IGNORECASE), "SERVICE_REQUIRED"),
    (re.compile(r"\bcertificate of (service|mailing)", re.IGNORECASE), "SERVICE_CERTIFICATE"),
    (re.compile(r"\bnotice of hearing\b", re.IGNORECASE), "NOTICE_OF_HEARING"),
]

def compile_requirements(fulltext: str) -> Dict:
    requirements = []
    lines = [ln.strip() for ln in fulltext.splitlines() if ln.strip()]
    for idx, ln in enumerate(lines[:5000]):
        for pat, rtype in REQ_PATTERNS:
            if pat.search(ln):
                requirements.append({"type": rtype, "text": ln, "line": idx + 1})
                break
    seen = set()
    deduped = []
    for r in requirements:
        key = (r["type"], r["text"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    return {"requirements": deduped[:1000], "generatedAt": now_iso(), "compiler": GENERATOR_VERSION}

def akn_root_for_doctype(dt: str) -> str:
    if dt in ("motion", "petition", "application"):
        return "motion" if dt == "motion" else dt
    if dt in ("order", "judgment"):
        return "judgment"
    if dt == "affidavit":
        return "statement"
    return "doc"

def generate_akn_template(form_code: str, doctype: str) -> str:
    root = akn_root_for_doctype(doctype)
    fc = form_code.replace(" ", "")
    return """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <{root} name="{doctype}" eId="{eid}">
    <meta>
      <identification source="#formos">
        <FRBRWork>
          <FRBRthis value="urn:akn:us-mi:form:{fc}:{ver}!{doctype}"/>
          <FRBRuri value="urn:akn:us-mi:form:{fc}"/>
          <FRBRdate date="{date}" name="Generation"/>
          <FRBRauthor href="#movingParty"/>
          <FRBRcountry value="us"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="urn:akn:us-mi:form:{fc}:{ver}!{doctype}@en"/>
          <FRBRuri value="urn:akn:us-mi:form:{fc}:{ver}!{doctype}"/>
          <FRBRdate date="{date}" name="Generation"/>
          <FRBRauthor href="#movingParty"/>
          <FRBRlanguage language="en"/>
        </FRBRExpression>
      </identification>
      <references source="#formos">
        <TLCOrganization eId="court" href="urn:akn:us-mi:court:trial" showAs="[FIELD:court_name]"/>
        <TLCPerson eId="movingParty" href="urn:akn:us-mi:person:moving" showAs="[FIELD:moving_party_name]"/>
        <TLCPerson eId="otherParty" href="urn:akn:us-mi:person:other" showAs="[FIELD:other_party_name]"/>
      </references>
    </meta>

    <mainBody>
      <block eId="caption">
        <p eId="cap_court">[FIELD:court_name]</p>
        <p eId="cap_case">Case No.: [FIELD:case_no] - Judge/Referee: [FIELD:judge_referee]</p>
        <p eId="cap_parties">[FIELD:plaintiff_name] v [FIELD:defendant_name]</p>
      </block>

      <heading eId="title">[FIELD:document_title]</heading>

      <heading eId="facts_hdr">FACTS</heading>
      <p eId="facts">[FIELD:facts_block]</p>

      <heading eId="law_hdr">LEGAL STANDARD</heading>
      <p eId="law">[FIELD:legal_standard_block]</p>

      <heading eId="arg_hdr">ARGUMENT / GROUNDS</heading>
      <p eId="arg">[FIELD:argument_block]</p>

      <heading eId="relief_hdr">RELIEF REQUESTED</heading>
      <p eId="relief">[FIELD:relief_requested]</p>

      <heading eId="sig_hdr">SIGNATURE</heading>
      <p eId="sig">/s/ [FIELD:signed_name]</p>

      <heading eId="service_hdr">CERTIFICATE / PROOF OF SERVICE</heading>
      <p eId="service">[FIELD:service_block]</p>

      <heading eId="idx_hdr">INDEX TO ATTACHMENTS</heading>
      <p eId="idx">[FIELD:index_to_attachments]</p>
    </mainBody>
  </{root}>
</akomaNtoso>
""".format(root=root, doctype=doctype, eid=f"{fc.lower()}_{doctype}", fc=fc, ver=GENERATOR_VERSION, date=now_iso()[:10])

def cmd_init_db(cfg: Config, schema_path: Path) -> None:
    con = connect_db(Path(cfg.sqlite_db))
    init_db(con, schema_path)
    con.close()
    print("OK: DB initialized")

def cmd_load_rulebanks(cfg: Config, rulebank_paths: List[str]) -> None:
    con = connect_db(Path(cfg.sqlite_db))
    loaded = 0
    for rp in rulebank_paths:
        p = Path(rp)
        if not p.exists():
            continue
        b = p.read_bytes()
        sha = sha256_bytes(b)
        rb_id = deterministic_id("RB", sha, n=24)
        txt = b.decode("utf-8", errors="ignore")
        jur = "UNKNOWN"
        m = re.search(r'jurisdiction:\s*"?([A-Za-z0-9\-_]+)"?', txt)
        if m:
            jur = m.group(1).strip()
        con.execute("INSERT OR IGNORE INTO rulebanks(rulebank_id, jurisdiction, path, sha256, loaded_at) VALUES(?,?,?,?,?)",
                    (rb_id, jur, str(p), sha, now_iso()))
        loaded += 1
    con.commit()
    con.close()
    print(f"OK: rulebanks_loaded={loaded}")

def cmd_ingest(cfg: Config) -> None:
    vault = Path(cfg.vault_root)
    safe_mkdir(vault)
    con = connect_db(Path(cfg.sqlite_db))

    run_id = deterministic_id(now_iso(), json.dumps(cfg.roots), n=26)
    con.execute("INSERT OR REPLACE INTO ingest_runs(run_id, started_at, roots_json) VALUES(?,?,?)",
                (run_id, now_iso(), json.dumps(cfg.roots)))
    con.commit()

    staging = vault / cfg.zip_staging_subdir
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    safe_mkdir(staging)

    expanded_roots: List[Path] = [Path(r) for r in cfg.roots]
    if cfg.explode_zips:
        for r in list(expanded_roots):
            if not r.exists():
                continue
            for f in iter_files(r):
                if is_zip(f):
                    sha = sha256_file(f)
                    out_dir = staging / deterministic_id(str(f), sha, n=32)
                    explode_zip(f, out_dir, 1, cfg.max_zip_depth)
                    expanded_roots.append(out_dir)

    docs = 0
    for root in expanded_roots:
        if not root.exists():
            continue
        for f in iter_files(root):
            if not f.is_file():
                continue
            try:
                size = f.stat().st_size
            except Exception:
                continue
            if size <= 0:
                continue
            sha = sha256_file(f)
            stored = cas_store(vault, f, sha)
            doc_id = deterministic_id(sha, str(stored), n=24)
            con.execute(
                "INSERT OR IGNORE INTO documents(doc_id, sha256, size_bytes, ext, mime, original_path, stored_object_path, created_at) VALUES(?,?,?,?,?,?,?,?)",
                (doc_id, sha, size, f.suffix.lower(), guess_mime(f), str(f), str(stored), now_iso())
            )
            docs += 1

    con.execute("UPDATE ingest_runs SET ended_at=?, stats_json=? WHERE run_id=?",
                (now_iso(), json.dumps({"documents_ingested": docs}), run_id))
    con.commit()
    con.close()
    print(f"OK: ingest run_id={run_id} documents_ingested={docs}")

def cmd_extract(cfg: Config) -> None:
    vault = Path(cfg.vault_root)
    con = connect_db(Path(cfg.sqlite_db))
    rows = con.execute("SELECT doc_id, sha256, original_path, stored_object_path, ext FROM documents").fetchall()
    extracted = 0
    for doc_id, sha, orig_path, stored_path, ext in rows:
        ext = (ext or "").lower()
        if con.execute("SELECT 1 FROM extractions WHERE doc_id=? LIMIT 1", (doc_id,)).fetchone():
            continue
        p = Path(orig_path)
        if not p.exists():
            p = Path(stored_path)
        if not p.exists():
            continue

        if ext == ".pdf" and cfg.extract_pdf_text:
            pages, fulltext, quality, needs_ocr = pdf_extract_text_pages(p, cfg.pdf_text_min_chars_per_page)
            if (not fulltext) and cfg.enable_ocr:
                ocr_out = vault / "90_REPORTS" / "ocr" / sha[:2] / f"{sha}.ocr.pdf"
                if run_ocr(cfg, p, ocr_out):
                    pages, fulltext, quality, needs_ocr = pdf_extract_text_pages(ocr_out, cfg.pdf_text_min_chars_per_page)
            if not fulltext:
                continue
            out_dir = vault / "90_REPORTS" / "extractions" / sha[:2] / sha
            safe_mkdir(out_dir / "pages")
            pages_meta = []
            for pg in pages:
                tp = out_dir / "pages" / f"p{pg['page']:04d}.txt"
                tp.write_text(pg["text"] or "", encoding="utf-8")
                pages_meta.append({"page": pg["page"], "text_path": str(tp), "char_count": pg["char_count"]})
            full_path = out_dir / "fulltext.txt"
            full_path.write_text(fulltext, encoding="utf-8")
            ex_sha = sha256_bytes(fulltext.encode("utf-8", errors="ignore"))
            extraction_id = deterministic_id(doc_id, "pdf_text", ex_sha, n=24)
            con.execute(
                "INSERT OR IGNORE INTO extractions(extraction_id, doc_id, method, quality_score, needs_ocr, pages_json, fulltext_path, sha256, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (extraction_id, doc_id, "pdf_text", quality, int(needs_ocr), json.dumps(pages_meta), str(full_path), ex_sha, now_iso())
            )
            extracted += 1

        elif ext == ".docx" and DOCX_AVAILABLE:
            txt = docx_extract_text(p)
            if not txt:
                continue
            out_dir = vault / "90_REPORTS" / "extractions" / sha[:2] / sha
            safe_mkdir(out_dir)
            full_path = out_dir / "fulltext.txt"
            full_path.write_text(txt, encoding="utf-8")
            ex_sha = sha256_bytes(txt.encode("utf-8", errors="ignore"))
            extraction_id = deterministic_id(doc_id, "docx", ex_sha, n=24)
            con.execute(
                "INSERT OR IGNORE INTO extractions(extraction_id, doc_id, method, quality_score, needs_ocr, pages_json, fulltext_path, sha256, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (extraction_id, doc_id, "docx", 1.0, 0, None, str(full_path), ex_sha, now_iso())
            )
            extracted += 1

        elif ext in (".txt", ".md"):
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                txt = ""
            if not txt:
                continue
            out_dir = vault / "90_REPORTS" / "extractions" / sha[:2] / sha
            safe_mkdir(out_dir)
            full_path = out_dir / "fulltext.txt"
            full_path.write_text(txt, encoding="utf-8")
            ex_sha = sha256_bytes(txt.encode("utf-8", errors="ignore"))
            extraction_id = deterministic_id(doc_id, "txt", ex_sha, n=24)
            con.execute(
                "INSERT OR IGNORE INTO extractions(extraction_id, doc_id, method, quality_score, needs_ocr, pages_json, fulltext_path, sha256, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (extraction_id, doc_id, "txt", 1.0, 0, None, str(full_path), ex_sha, now_iso())
            )
            extracted += 1

    con.commit()
    con.close()
    print(f"OK: extracted={extracted}")

def cmd_detect_forms(cfg: Config) -> None:
    con = connect_db(Path(cfg.sqlite_db))
    rows = con.execute("""
        SELECT d.doc_id, d.original_path, d.ext, e.extraction_id, e.fulltext_path
        FROM documents d
        JOIN extractions e ON e.doc_id = d.doc_id
        LEFT JOIN forms f ON f.doc_id = d.doc_id
        WHERE f.form_id IS NULL
    """).fetchall()
    detected = 0
    for doc_id, orig_path, ext, extraction_id, fulltext_path in rows:
        filename = Path(orig_path).name
        try:
            text = Path(fulltext_path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not looks_like_form(filename, text):
            continue
        code = guess_form_code_from_name(filename) or guess_form_code_from_text(text) or f"FORM-{doc_id[:8]}"
        title = guess_title(text) or "Court Form"
        rev = guess_revision(text)
        doctype = guess_doctype(text, filename)
        family = code.split()[0] if " " in code else "UNKNOWN"
        jur = "MI" if family in {"FOC","MC","DC","CC","PC","JC"} else "UNKNOWN"
        form_id = deterministic_id(doc_id, "FORM", code, rev or "", n=24)
        con.execute("""
            INSERT OR IGNORE INTO forms(form_id, doc_id, extraction_id, jurisdiction_guess, court_level_guess, family_guess,
                                        form_code_guess, title_guess, revision_guess, doctype_guess, detected_by, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """, (form_id, doc_id, extraction_id, jur, "TRIAL", family, code, title, rev, doctype, "heuristic_v2", now_iso()))
        detected += 1
    con.commit()
    con.close()
    print(f"OK: forms_detected={detected}")

def cmd_instructions(cfg: Config) -> None:
    vault = Path(cfg.vault_root)
    con = connect_db(Path(cfg.sqlite_db))
    rows = con.execute("""
        SELECT f.form_id, f.form_code_guess, f.revision_guess, d.sha256, e.fulltext_path
        FROM forms f
        JOIN documents d ON d.doc_id=f.doc_id
        JOIN extractions e ON e.extraction_id=f.extraction_id
        LEFT JOIN form_instructions i ON i.form_id=f.form_id
        WHERE i.instr_id IS NULL
    """).fetchall()
    done = 0
    for form_id, code, rev, sha, fulltext_path in rows:
        try:
            fulltext = Path(fulltext_path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        spans = instruction_spans(fulltext)
        family = (code.split()[0] if code and " " in code else "UNKNOWN")
        jur = "MI" if family in {"FOC","MC","DC","CC","PC","JC"} else "UNKNOWN"
        plane = vault / "10_FORMS" / jur / "TRIAL" / family / (code.replace(" ", "") if code else form_id) / (rev or sha[:8])
        out_dir = plane / "derived"
        safe_mkdir(out_dir)
        instr_path = out_dir / "instructions_fulltext.txt"
        instr_path.write_text(fulltext.strip(), encoding="utf-8")
        spans_path = out_dir / "instructions_spans.json"
        spans_path.write_text(json.dumps(spans, indent=2), encoding="utf-8")
        instr_sha = sha256_bytes(fulltext.encode("utf-8", errors="ignore"))
        instr_id = deterministic_id(form_id, "INSTR", instr_sha, n=24)
        con.execute("""
            INSERT OR IGNORE INTO form_instructions(instr_id, form_id, instruction_fulltext_path, instruction_sha256, spans_json_path, created_at)
            VALUES(?,?,?,?,?,?)
        """, (instr_id, form_id, str(instr_path), instr_sha, str(spans_path), now_iso()))
        done += 1
    con.commit()
    con.close()
    print(f"OK: instructions_stored={done}")

def cmd_specs(cfg: Config) -> None:
    con = connect_db(Path(cfg.sqlite_db))
    rows = con.execute("""
        SELECT f.form_id, i.instruction_fulltext_path
        FROM forms f
        JOIN form_instructions i ON i.form_id=f.form_id
        LEFT JOIN form_specs s ON s.form_id=f.form_id
        WHERE s.spec_id IS NULL
    """).fetchall()
    made = 0
    for form_id, instr_path in rows:
        try:
            txt = Path(instr_path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        spec = compile_requirements(txt)
        spec_path = Path(instr_path).with_name("requirements.json")
        spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        spec_sha = sha256_bytes(spec_path.read_bytes())
        spec_id = deterministic_id(form_id, "SPEC", spec_sha, n=24)
        con.execute("INSERT OR IGNORE INTO form_specs(spec_id, form_id, spec_json_path, spec_sha256, created_at) VALUES(?,?,?,?,?)",
                    (spec_id, form_id, str(spec_path), spec_sha, now_iso()))
        made += 1
    con.commit()
    con.close()
    print(f"OK: specs_compiled={made}")

def cmd_akn(cfg: Config) -> None:
    vault = Path(cfg.vault_root)
    con = connect_db(Path(cfg.sqlite_db))
    rows = con.execute("""
        SELECT f.form_id, f.form_code_guess, f.doctype_guess, f.revision_guess, d.sha256
        FROM forms f
        JOIN documents d ON d.doc_id=f.doc_id
        LEFT JOIN akn_templates a ON a.form_id=f.form_id
        WHERE a.akn_id IS NULL
    """).fetchall()
    made = 0
    for form_id, code, doctype, rev, sha in rows:
        code = code or f"FORM-{form_id[:8]}"
        doctype = doctype or "submission"
        family = code.split()[0] if " " in code else "UNKNOWN"
        jur = "MI" if family in {"FOC","MC","DC","CC","PC","JC"} else "UNKNOWN"
        plane = vault / "10_FORMS" / jur / "TRIAL" / family / code.replace(" ", "") / (rev or sha[:8])
        out_dir = plane / "derived" / "akn"
        safe_mkdir(out_dir)
        xml = generate_akn_template(code, doctype)
        xml_path = out_dir / "template.xml"
        xml_path.write_text(xml, encoding="utf-8")
        xml_sha = sha256_bytes(xml.encode("utf-8", errors="ignore"))
        akn_id = deterministic_id(form_id, "AKN", xml_sha, n=24)
        con.execute("""
            INSERT OR IGNORE INTO akn_templates(akn_id, form_id, template_xml_path, template_sha256, generated_at, generator_version, validation_json)
            VALUES(?,?,?,?,?,?,?)
        """, (akn_id, form_id, str(xml_path), xml_sha, now_iso(), GENERATOR_VERSION, json.dumps({"wellformed": True})))
        made += 1
    con.commit()
    con.close()
    print(f"OK: akn_templates_generated={made}")

def cmd_stacks(cfg: Config, case_id: str) -> None:
    vault = Path(cfg.vault_root)
    con = connect_db(Path(cfg.sqlite_db))
    rows = con.execute("SELECT form_id, form_code_guess, title_guess FROM forms").fetchall()
    built = 0
    for form_id, code, title in rows:
        code = code or f"FORM-{form_id[:8]}"
        out_root = vault / "40_FILINGS_OUTPUT" / case_id / code.replace(" ", "")
        for sub in ("lead","attachments","service","exhibits"):
            safe_mkdir(out_root / sub)
        manifest = {
            "schemaVersion": "formos.stack_manifest.v1",
            "caseId": case_id,
            "formId": form_id,
            "formCode": code,
            "title": title,
            "folders": {k: str((out_root / k).resolve()) for k in ["lead","attachments","service","exhibits"]},
            "notes": "Place generated PDFs here. Use requirements.json + rulebanks for linting."
        }
        manifest_path = out_root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        msha = sha256_bytes(manifest_path.read_bytes())
        stack_id = deterministic_id(form_id, case_id, "STACK", n=24)
        con.execute("""
            INSERT OR REPLACE INTO stack_manifests(stack_id, form_id, case_id, stack_root, manifest_json_path, manifest_sha256, generated_at)
            VALUES(?,?,?,?,?,?,?)
        """, (stack_id, form_id, case_id, str(out_root), str(manifest_path), msha, now_iso()))
        built += 1
    con.commit()
    con.close()
    print(f"OK: stacks_built={built} case_id={case_id}")

def cmd_coverage(cfg: Config, out_path: Path) -> None:
    con = connect_db(Path(cfg.sqlite_db))
    forms = con.execute("SELECT form_id, form_code_guess, title_guess FROM forms").fetchall()
    missing = []
    covered = 0
    for form_id, code, title in forms:
        has_instr = con.execute("SELECT 1 FROM form_instructions WHERE form_id=? LIMIT 1", (form_id,)).fetchone() is not None
        has_spec = con.execute("SELECT 1 FROM form_specs WHERE form_id=? LIMIT 1", (form_id,)).fetchone() is not None
        has_akn = con.execute("SELECT 1 FROM akn_templates WHERE form_id=? LIMIT 1", (form_id,)).fetchone() is not None
        if has_instr and has_spec and has_akn:
            covered += 1
        else:
            missing.append({"formId": form_id, "formCode": code, "title": title,
                            "missing": {"instructions": not has_instr, "spec": not has_spec, "akn": not has_akn}})
    report = {
        "schemaVersion": "formos.coverage.v1",
        "generatedAt": now_iso(),
        "formsTotal": len(forms),
        "formsCovered": covered,
        "coveragePct": (covered / len(forms) * 100.0) if forms else 0.0,
        "missing": missing
    }
    safe_mkdir(out_path.parent)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    con.close()
    print(f"OK: coverage written to {out_path} (covered {covered}/{len(forms)})")

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-db")
    p_init.add_argument("--config", required=True)
    p_init.add_argument("--schema", required=True)

    p_loadrb = sub.add_parser("load-rulebanks")
    p_loadrb.add_argument("--config", required=True)
    p_loadrb.add_argument("--paths", nargs="+", required=True)

    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument("--config", required=True)

    p_extract = sub.add_parser("extract")
    p_extract.add_argument("--config", required=True)

    p_detect = sub.add_parser("detect-forms")
    p_detect.add_argument("--config", required=True)

    p_instr = sub.add_parser("instructions")
    p_instr.add_argument("--config", required=True)

    p_specs = sub.add_parser("specs")
    p_specs.add_argument("--config", required=True)

    p_akn = sub.add_parser("akn")
    p_akn.add_argument("--config", required=True)

    p_stacks = sub.add_parser("stacks")
    p_stacks.add_argument("--config", required=True)
    p_stacks.add_argument("--case-id", required=True)

    p_cov = sub.add_parser("coverage")
    p_cov.add_argument("--config", required=True)
    p_cov.add_argument("--out", required=True)

    args = ap.parse_args()
    cfg = load_config(Path(args.config))

    if args.cmd == "init-db":
        con = connect_db(Path(cfg.sqlite_db))
        init_db(con, Path(args.schema))
        con.close()
        print("OK: DB initialized")
    elif args.cmd == "load-rulebanks":
        cmd_load_rulebanks(cfg, args.paths)
    elif args.cmd == "ingest":
        cmd_ingest(cfg)
    elif args.cmd == "extract":
        cmd_extract(cfg)
    elif args.cmd == "detect-forms":
        cmd_detect_forms(cfg)
    elif args.cmd == "instructions":
        cmd_instructions(cfg)
    elif args.cmd == "specs":
        cmd_specs(cfg)
    elif args.cmd == "akn":
        cmd_akn(cfg)
    elif args.cmd == "stacks":
        cmd_stacks(cfg, args.case_id)
    elif args.cmd == "coverage":
        cmd_coverage(cfg, Path(args.out))
    else:
        raise RuntimeError("Unknown command")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
