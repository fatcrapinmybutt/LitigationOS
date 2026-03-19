from __future__ import annotations
import json, re, sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Iterable
from .log import Logger
from .util_fs import ensure_dir

RE_MCR  = re.compile(r"\bMCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))?\b")
RE_MCL  = re.compile(r"\bMCL\s+\d+\.\d+[a-z]?(?:\([0-9A-Za-z]+\))?\b", re.IGNORECASE)
RE_MRE  = re.compile(r"\bMRE\s+\d+\b", re.IGNORECASE)

def _load_pymupdf():
    try:
        import fitz  # type: ignore
        return fitz
    except Exception:
        return None

def init_authority_db(db_path: Path) -> None:
    ensure_dir(db_path.parent)
    conn = sqlite3.connect(str(db_path)); cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sources("
        "source_id TEXT PRIMARY KEY,"
        "title TEXT,"
        "path TEXT,"
        "kind TEXT,"
        "effective_date TEXT,"
        "notes TEXT"
        ");"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS refs("
        "citation TEXT,"
        "source_id TEXT,"
        "path TEXT,"
        "page_no INTEGER,"
        "line_no INTEGER,"
        "context TEXT,"
        "PRIMARY KEY(citation, source_id, page_no, line_no)"
        ");"
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_refs_citation ON refs(citation);")
    conn.commit(); conn.close()

def _iter_lines_for_pdf(path: Path, max_pages: int=0) -> Iterable[Tuple[int,int,str]]:
    fitz = _load_pymupdf()
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) not installed")
    doc = fitz.open(str(path))
    n = doc.page_count
    if max_pages and max_pages < n:
        n = max_pages
    for i in range(n):
        page = doc.load_page(i)
        text = page.get_text("text") or ""
        lines = text.splitlines()
        for j, ln in enumerate(lines, start=1):
            if ln.strip():
                yield (i+1, j, ln.rstrip())
    doc.close()

def ingest_authority_pdfs(
    pdf_paths: List[Path],
    run_dir: Path,
    logger: Logger,
    kind: str="authority",
    effective_date: str="",
    max_pages: int=0,
    context_window: int=2
) -> Dict[str,str]:
    stores = run_dir / "stores"
    out_dir = stores / "authority"
    ensure_dir(out_dir)
    db = out_dir / "authority.sqlite"
    init_authority_db(db)

    conn = sqlite3.connect(str(db)); cur = conn.cursor()
    wrote_sources=0; wrote_refs=0; errors=0

    index_jsonl = out_dir / "authority_index.jsonl"
    fp = index_jsonl.open("w", encoding="utf-8")

    for p in pdf_paths:
        p = Path(p)
        if not p.exists():
            logger.emit("ERROR","AUTH_PDF_MISSING","Authority PDF missing", path=str(p))
            errors += 1
            continue
        source_id = p.stem.replace(" ","_")[:80]
        title = p.stem
        cur.execute("INSERT OR REPLACE INTO sources(source_id,title,path,kind,effective_date,notes) VALUES(?,?,?,?,?,?)",
                    (source_id, title, str(p), kind, effective_date, ""))
        wrote_sources += 1
        # Build a rolling buffer for context lines
        page_lines: Dict[Tuple[int,int], str] = {}
        try:
            for (page_no, line_no, ln) in _iter_lines_for_pdf(p, max_pages=max_pages):
                # Store line for potential context
                page_lines[(page_no, line_no)] = ln
                # Evaluate citation matches
                citations = set()
                citations.update(m.group(0).upper() for m in RE_MCR.finditer(ln))
                citations.update(m.group(0).upper() for m in RE_MCL.finditer(ln))
                citations.update(m.group(0).upper() for m in RE_MRE.finditer(ln))
                if not citations:
                    continue
                # Build context window text
                ctx_lines=[]
                for k in range(line_no-context_window, line_no+context_window+1):
                    t = page_lines.get((page_no,k))
                    if t:
                        ctx_lines.append(t)
                ctx = "\n".join(ctx_lines)[:2000]
                for cit in sorted(citations):
                    cur.execute("INSERT OR REPLACE INTO refs(citation,source_id,path,page_no,line_no,context) VALUES(?,?,?,?,?,?)",
                                (cit, source_id, str(p), page_no, line_no, ctx))
                    wrote_refs += 1
                    fp.write(json.dumps({"citation":cit,"source_id":source_id,"path":str(p),
                                         "page_no":page_no,"line_no":line_no,"context":ctx}, ensure_ascii=False) + "\n")
        except Exception as e:
            errors += 1
            logger.emit("ERROR","AUTH_INGEST_ERR","Error ingesting authority PDF", path=str(p), err=str(e))

    fp.close()
    conn.commit(); conn.close()
    logger.emit("INFO","AUTH_INGEST_DONE","Authority ingest complete", sources=wrote_sources, refs=wrote_refs, out_db=str(db), out_index=str(index_jsonl))
    return {"status":"ok","sources":str(wrote_sources),"refs":str(wrote_refs),"db":str(db),"index":str(index_jsonl)}
