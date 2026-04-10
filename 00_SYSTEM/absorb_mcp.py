#!/usr/bin/env python3
"""MCP → NEXUS Absorption Script.

Reads the current nexus_daemon.py, inserts 22 new handler functions + helpers,
updates the HANDLERS dict, writes the merged result, and validates syntax.

Run: python -I D:\LitigationOS_tmp\absorb_mcp.py
"""
import ast
import os
import shutil
from pathlib import Path
from datetime import datetime

DAEMON_PATH = Path(r"C:\Users\andre\LitigationOS\.github\extensions\singularity\nexus_daemon.py")
BACKUP_PATH = Path(r"C:\Users\andre\LitigationOS\11_ARCHIVES\nexus_daemon_pre_absorb.py")

# ═══════════════════════════════════════════════════════════════════════════
# NEW CODE BLOCKS TO INSERT
# ═══════════════════════════════════════════════════════════════════════════

HELPERS_BLOCK = '''
# ── Absorbed MCP Helpers (2026-04-05) ─────────────────────────────────────
import hashlib
from pathlib import Path as _Path

_HEADING_RE = __import__("re").compile(r"^(#{1,6})\\s+(.*)", __import__("re").MULTILINE)

_REF_PATTERNS = [
    ("rule",      __import__("re").compile(r"MCR\\s+\\d+\\.\\d+[\\w()]*", __import__("re").IGNORECASE)),
    ("rule",      __import__("re").compile(r"MCL\\s+\\d+\\.\\d+[\\w()]*", __import__("re").IGNORECASE)),
    ("rule",      __import__("re").compile(r"MRE\\s+\\d+\\.?\\d*", __import__("re").IGNORECASE)),
    ("authority", __import__("re").compile(r"\\d+\\s+(?:Mich(?:\\s+App)?|USC|US)\\s+\\d+")),
    ("agent",     __import__("re").compile(r"AGENT:\\s*(\\w+)")),
]

_FTS_UNSAFE = __import__("re").compile(r"[^\\w\\s*\\\"\\-]")


def _table_exists(table):
    """Check if table exists in the SQLite database."""
    try:
        row = pool.sqlite.execute(
            "SELECT 1 FROM sqlite_master WHERE type=\'table\' AND name=?", (table,)
        ).fetchone()
        return row is not None
    except Exception:
        return False


def _doc_columns():
    """Adaptive document table column detection (handles schema mismatches)."""
    if not _table_exists("documents"):
        return None
    cols = {r[1] for r in pool.sqlite.execute("PRAGMA table_info(documents)").fetchall()}
    return cols


def _sanitize_enhanced(query):
    """Enhanced FTS5 sanitizer: balanced quotes, safe chars only."""
    q = _FTS_UNSAFE.sub(" ", query).strip()
    if q.count(\'\\"\') % 2 != 0:
        q = q.replace(\'\\"\', " ")
    return q


def _validate_path(path_str):
    """Validate path is within allowed directories."""
    p = _Path(path_str).resolve()
    allowed = [
        _Path(r"C:\\Users\\andre\\LitigationOS").resolve(),
        _Path(r"D:\\").resolve(),
        _Path(r"F:\\").resolve(),
        _Path(r"G:\\").resolve(),
        _Path(r"I:\\").resolve(),
        _Path(r"J:\\").resolve(),
    ]
    return any(str(p).startswith(str(a)) for a in allowed)


def _extract_cross_refs(text):
    """Extract cross-references from text using compiled patterns."""
    refs = []
    for ref_type, pattern in _REF_PATTERNS:
        for m in pattern.finditer(text):
            refs.append({"type": ref_type, "value": m.group(0).strip()})
    return refs

'''

HANDLERS_BLOCK = '''

# ══════════════════════════════════════════════════════════════════════════
# ABSORBED MCP HANDLERS (34 capabilities from litigation_context MCP server)
# ══════════════════════════════════════════════════════════════════════════


def handle_list_documents(req):
    """List documents in the knowledge base with metadata."""
    limit = min(req.get("limit", 20), 100)
    offset = req.get("offset", 0)
    name_filter = req.get("name_filter")
    conn = pool.sqlite
    cols = _doc_columns()
    if cols is None:
        return {"ok": False, "error": "documents table not found"}

    has_file_name = "file_name" in cols
    has_title = "title" in cols

    if has_file_name:
        base = "SELECT id, file_name, file_size_bytes, page_count, sha256_hash, created_at FROM documents"
        count_q = "SELECT COUNT(*) FROM documents"
        if name_filter:
            base += " WHERE file_name LIKE ?"
            count_q += " WHERE file_name LIKE ?"
            params = [f"%{name_filter}%"]
        else:
            params = []
    elif has_title:
        base = "SELECT id, title, doc_type, content_preview, created_at FROM documents"
        count_q = "SELECT COUNT(*) FROM documents"
        if name_filter:
            base += " WHERE title LIKE ?"
            count_q += " WHERE title LIKE ?"
            params = [f"%{name_filter}%"]
        else:
            params = []
    else:
        base = "SELECT * FROM documents"
        count_q = "SELECT COUNT(*) FROM documents"
        params = []

    total = conn.execute(count_q, params).fetchone()[0]
    base += " ORDER BY id DESC LIMIT ? OFFSET ?"
    rows = conn.execute(base, params + [limit, offset]).fetchall()
    return {"ok": True, "documents": [dict(r) for r in rows], "total": total, "count": len(rows)}


def handle_get_document(req):
    """Get full text of a document by ID, optionally specific pages."""
    doc_id = req.get("document_id")
    page_numbers = req.get("page_numbers")
    if not doc_id:
        return {"ok": False, "error": "document_id required"}
    conn = pool.sqlite

    cols = _doc_columns()
    if cols is None:
        return {"ok": False, "error": "documents table not found"}

    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not doc:
        return {"ok": False, "error": f"Document {doc_id} not found"}

    if _table_exists("pages"):
        if page_numbers:
            placeholders = ",".join("?" for _ in page_numbers)
            pages = conn.execute(
                f"SELECT page_number, content FROM pages WHERE document_id = ? AND page_number IN ({placeholders}) ORDER BY page_number",
                [doc_id] + list(page_numbers)
            ).fetchall()
        else:
            pages = conn.execute(
                "SELECT page_number, content FROM pages WHERE document_id = ? ORDER BY page_number",
                (doc_id,)
            ).fetchall()
        return {"ok": True, "document": dict(doc), "pages": [dict(p) for p in pages], "page_count": len(pages)}

    return {"ok": True, "document": dict(doc), "pages": [], "page_count": 0}


def handle_search_pages(req):
    """FTS5 search across PDF pages."""
    query = req.get("query", "")
    limit = min(req.get("limit", 20), 100)
    if not query:
        return {"ok": False, "error": "query required"}

    conn = pool.sqlite
    safe_q = _sanitize_enhanced(query)

    if _table_exists("pages_fts"):
        try:
            rows = conn.execute(
                "SELECT p.document_id, p.page_number, snippet(pages_fts, 0, \'>>>\', \'<<<\', \'...\', 40) as snippet "
                "FROM pages_fts JOIN pages p ON p.rowid = pages_fts.rowid "
                "WHERE pages_fts MATCH ? ORDER BY rank LIMIT ?",
                (safe_q, limit)
            ).fetchall()
            return {"ok": True, "results": [dict(r) for r in rows], "count": len(rows), "method": "fts5"}
        except Exception:
            pass

    if _table_exists("pages"):
        rows = conn.execute(
            "SELECT document_id, page_number, substr(content, 1, 200) as snippet "
            "FROM pages WHERE content LIKE ? LIMIT ?",
            (f"%{query}%", limit)
        ).fetchall()
        return {"ok": True, "results": [dict(r) for r in rows], "count": len(rows), "method": "like_fallback"}

    return {"ok": True, "results": [], "count": 0, "method": "no_pages_table"}


def handle_search_rules(req):
    """Search Michigan Court Rules (MCR/MCL) by citation or keyword."""
    query = req.get("query", "")
    limit = min(req.get("limit", 20), 100)
    if not query:
        return {"ok": False, "error": "query required"}
    conn = pool.sqlite
    results = []

    # Search graph_nodes for authority entries
    if _table_exists("graph_nodes"):
        try:
            rows = conn.execute(
                "SELECT id, label, node_type, metadata FROM graph_nodes "
                "WHERE (id LIKE ? OR label LIKE ?) AND node_type IN (\'authority\',\'rule\',\'statute\') LIMIT ?",
                (f"%{query}%", f"%{query}%", limit)
            ).fetchall()
            results.extend([dict(r) for r in rows])
        except Exception:
            pass

    # Search michigan_rules_extracted
    if _table_exists("michigan_rules_extracted"):
        try:
            rows = conn.execute(
                "SELECT rule_number, rule_type, title, substr(full_text, 1, 500) as text_preview "
                "FROM michigan_rules_extracted "
                "WHERE rule_number LIKE ? OR title LIKE ? OR full_text LIKE ? LIMIT ?",
                (f"%{query}%", f"%{query}%", f"%{query}%", limit)
            ).fetchall()
            results.extend([dict(r) for r in rows])
        except Exception:
            pass

    return {"ok": True, "results": results, "count": len(results)}


def handle_search_graph(req):
    """Search knowledge graph nodes by label, type, or source."""
    query = req.get("query", "")
    node_type = req.get("node_type")
    graph_source = req.get("graph_source")
    limit = min(req.get("limit", 20), 100)
    if not query:
        return {"ok": False, "error": "query required"}
    conn = pool.sqlite

    if not _table_exists("graph_nodes"):
        return {"ok": False, "error": "graph_nodes table not found"}

    sql = "SELECT id, label, node_type, metadata FROM graph_nodes WHERE (id LIKE ? OR label LIKE ?)"
    params = [f"%{query}%", f"%{query}%"]

    if node_type:
        sql += " AND node_type = ?"
        params.append(node_type)
    if graph_source:
        sql += " AND metadata LIKE ?"
        params.append(f"%{graph_source}%")

    sql += f" LIMIT {limit}"
    rows = conn.execute(sql, params).fetchall()
    return {"ok": True, "nodes": [dict(r) for r in rows], "count": len(rows)}


def handle_lookup_authority(req):
    """Look up legal authorities (case law, statutes, rules) with pin cites."""
    query = req.get("query", "")
    limit = min(req.get("limit", 20), 100)
    if not query:
        return {"ok": False, "error": "query required"}
    conn = pool.sqlite
    results = []

    for table in ["graph_nodes", "authority_chains_v2", "master_citations", "michigan_rules_extracted"]:
        if not _table_exists(table):
            continue
        try:
            cols_info = conn.execute(f"PRAGMA table_info({table})").fetchall()
            col_names = [c[1] for c in cols_info]
            text_cols = [c for c in col_names if any(k in c.lower() for k in ["text", "label", "citation", "rule", "title", "name"])]
            if not text_cols:
                continue
            where_parts = " OR ".join(f"{c} LIKE ?" for c in text_cols[:3])
            params = [f"%{query}%"] * min(len(text_cols), 3)
            select_cols = ", ".join(col_names[:8])
            rows = conn.execute(f"SELECT {select_cols} FROM {table} WHERE {where_parts} LIMIT ?", params + [limit]).fetchall()
            for r in rows:
                d = dict(r)
                d["_source_table"] = table
                results.append(d)
        except Exception:
            continue

    return {"ok": True, "authorities": results[:limit], "count": min(len(results), limit)}


def handle_risk_events(req):
    """Assess litigation risks from the risk event taxonomy."""
    severity_min = req.get("severity_min", 0)
    risk_class = req.get("risk_class")
    conn = pool.sqlite

    if not _table_exists("risk_events"):
        return {"ok": True, "risks": [], "count": 0, "note": "risk_events table not found"}

    sql = "SELECT * FROM risk_events WHERE severity >= ?"
    params = [severity_min]
    if risk_class:
        sql += " AND risk_class = ?"
        params.append(risk_class)
    sql += " ORDER BY severity DESC LIMIT 50"

    rows = conn.execute(sql, params).fetchall()
    return {"ok": True, "risks": [dict(r) for r in rows], "count": len(rows)}


def handle_self_test(req):
    """Run diagnostic self-tests on the database."""
    conn = pool.sqlite
    tests = []
    t0 = datetime.now()

    # Test 1: DB connectivity
    try:
        conn.execute("SELECT 1")
        tests.append({"test": "db_connectivity", "pass": True, "ms": 0})
    except Exception as e:
        tests.append({"test": "db_connectivity", "pass": False, "error": str(e)})

    # Test 2: Schema presence
    key_tables = ["evidence_quotes", "authority_chains_v2", "timeline_events", "michigan_rules_extracted"]
    for t in key_tables:
        exists = _table_exists(t)
        tests.append({"test": f"table_{t}", "pass": exists})

    # Test 3: FTS5 round-trip
    if _table_exists("evidence_fts"):
        try:
            r = conn.execute("SELECT COUNT(*) FROM evidence_fts WHERE evidence_fts MATCH \'custody\'").fetchone()
            tests.append({"test": "fts5_roundtrip", "pass": True, "rows": r[0]})
        except Exception as e:
            tests.append({"test": "fts5_roundtrip", "pass": False, "error": str(e)})

    # Test 4: Graph counts
    for t in ["graph_nodes", "graph_edges"]:
        if _table_exists(t):
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            tests.append({"test": f"count_{t}", "pass": True, "count": cnt})

    elapsed = (datetime.now() - t0).total_seconds() * 1000
    passed = sum(1 for t in tests if t.get("pass"))
    return {"ok": True, "tests": tests, "passed": passed, "total": len(tests), "elapsed_ms": round(elapsed, 1)}


def handle_self_audit(req):
    """Run comprehensive data-quality audit. Returns quality score 0-100."""
    conn = pool.sqlite
    findings = []
    score = 100

    # Check key tables exist and have data
    critical = {
        "evidence_quotes": 1000, "authority_chains_v2": 1000, "timeline_events": 500,
        "michigan_rules_extracted": 100, "documents": 1,
    }
    for table, min_rows in critical.items():
        if not _table_exists(table):
            findings.append({"severity": "critical", "finding": f"Table {table} missing"})
            score -= 15
        else:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if cnt < min_rows:
                findings.append({"severity": "warning", "finding": f"{table}: {cnt} rows (expected >= {min_rows})"})
                score -= 5

    # Check FTS5 indexes
    for fts in ["evidence_fts", "timeline_fts", "md_sections_fts"]:
        if not _table_exists(fts):
            findings.append({"severity": "warning", "finding": f"FTS5 index {fts} missing"})
            score -= 3

    score = max(0, score)
    return {"ok": True, "quality_score": score, "findings": findings, "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "F"}


def handle_convergence_status(req):
    """Check convergence status of the knowledge base."""
    conn = pool.sqlite
    result = {"converged": False, "quality_score": 0, "blockers": [], "delta_new": 0}

    if _table_exists("convergence_domains"):
        rows = conn.execute("SELECT status, COUNT(*) as cnt FROM convergence_domains GROUP BY status").fetchall()
        result["domain_status"] = {r["status"]: r["cnt"] for r in rows}
        total = sum(r["cnt"] for r in rows)
        green = result["domain_status"].get("GREEN", 0)
        result["convergence_pct"] = round(green * 100 / total, 1) if total else 0
        result["converged"] = result["convergence_pct"] >= 95

    if _table_exists("convergence_waves"):
        waves = conn.execute("SELECT wave_id, wave_name, status FROM convergence_waves WHERE status != \'COMPLETE\' ORDER BY wave_number LIMIT 5").fetchall()
        result["pending_waves"] = [dict(w) for w in waves]

    if _table_exists("convergence_todos"):
        todos = conn.execute(
            "SELECT todo_id, title, status FROM convergence_todos WHERE status IN (\'PENDING\',\'IN_PROGRESS\') LIMIT 10"
        ).fetchall()
        result["next_todos"] = [dict(t) for t in todos]

    return {"ok": True, **result}


def handle_compute_deadlines_ext(req):
    """Compute legal deadlines from a trigger event and date."""
    trigger_event = req.get("trigger_event", "")
    trigger_date = req.get("trigger_date", "")
    if not trigger_event or not trigger_date:
        return {"ok": False, "error": "trigger_event and trigger_date required"}

    from datetime import timedelta
    try:
        base = datetime.strptime(trigger_date, "%Y-%m-%d")
    except ValueError:
        return {"ok": False, "error": f"Invalid date format: {trigger_date}. Use YYYY-MM-DD."}

    # Michigan standard deadlines
    RULES = {
        "complaint_filed": [
            (21, "Answer due", "MCR 2.108(A)(1)"),
            (28, "Default possible if no answer", "MCR 2.603"),
            (91, "Scheduling conference", "MCR 2.401"),
        ],
        "motion_served": [
            (14, "Response to motion due", "MCR 2.119(C)(1)"),
            (7, "Reply brief due (after response)", "MCR 2.119(C)(2)"),
            (21, "Hearing (if not sooner)", "MCR 2.119(E)"),
        ],
        "motion_filed": [
            (14, "Response due", "MCR 2.119(C)(1)"),
        ],
        "order_entered": [
            (21, "Motion for reconsideration", "MCR 2.119(F)(1)"),
            (42, "Claim of appeal (COA)", "MCR 7.204(A)"),
        ],
        "judgment_entered": [
            (21, "Motion for new trial/reconsideration", "MCR 2.611/2.119(F)"),
            (42, "Claim of appeal", "MCR 7.204(A)"),
            (182, "Motion for relief from judgment (a)(b)(c)", "MCR 2.612(C)(2)"),
            (365, "Relief from judgment final deadline", "MCR 2.612(C)(2)"),
        ],
        "claim_of_appeal_filed": [
            (56, "Appellant brief due", "MCR 7.212(A)(1)"),
            (35, "Appellee brief due (after appellant)", "MCR 7.212(A)(2)"),
        ],
    }

    event_rules = RULES.get(trigger_event, [])
    if not event_rules:
        return {"ok": True, "deadlines": [], "note": f"No rules for event: {trigger_event}. Known: {list(RULES.keys())}"}

    deadlines = []
    for days, desc, authority in event_rules:
        deadline_date = base + timedelta(days=days)
        days_left = (deadline_date - datetime.now()).days
        deadlines.append({
            "deadline": deadline_date.strftime("%Y-%m-%d"),
            "days_from_trigger": days,
            "days_until": days_left,
            "description": desc,
            "authority": authority,
            "urgency": "OVERDUE" if days_left < 0 else "CRITICAL" if days_left <= 3 else "URGENT" if days_left <= 7 else "OK",
        })

    return {"ok": True, "trigger_event": trigger_event, "trigger_date": trigger_date, "deadlines": deadlines}


def handle_red_team(req):
    """Red-team validate a legal claim or argument."""
    claim = req.get("claim", "")
    if not claim:
        return {"ok": False, "error": "claim required"}
    conn = pool.sqlite
    findings = []
    scores = {"authority": 0, "evidence": 0, "consistency": 0}

    safe_q = sanitize_fts5(claim)

    # Check authority support
    if _table_exists("authority_chains_v2"):
        try:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM authority_chains_v2 WHERE primary_citation LIKE ? OR paragraph_context LIKE ?",
                (f"%{claim[:50]}%", f"%{claim[:50]}%")
            ).fetchone()[0]
            scores["authority"] = min(100, cnt * 10)
            if cnt == 0:
                findings.append({"severity": "HIGH", "finding": "No authority chain found for this claim"})
        except Exception:
            pass

    # Check evidence support
    if _table_exists("evidence_fts"):
        try:
            cnt = conn.execute("SELECT COUNT(*) FROM evidence_fts WHERE evidence_fts MATCH ?", (safe_q,)).fetchone()[0]
            scores["evidence"] = min(100, cnt * 5)
            if cnt < 3:
                findings.append({"severity": "MEDIUM", "finding": f"Weak evidence support: only {cnt} matching quotes"})
        except Exception:
            pass

    # Check contradictions
    if _table_exists("contradiction_map"):
        try:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM contradiction_map WHERE contradiction_text LIKE ?",
                (f"%{claim[:50]}%",)
            ).fetchone()[0]
            if cnt > 0:
                findings.append({"severity": "HIGH", "finding": f"{cnt} contradictions found related to this claim"})
                scores["consistency"] = max(0, 100 - cnt * 20)
            else:
                scores["consistency"] = 100
        except Exception:
            scores["consistency"] = 50

    overall = sum(scores.values()) / 3
    return {
        "ok": True, "claim": claim, "scores": scores, "overall_score": round(overall, 1),
        "findings": findings, "filing_ready": overall >= 60 and not any(f["severity"] == "HIGH" for f in findings),
    }


def handle_evidence_chain(req):
    """Trace the evidence chain for a legal claim."""
    claim = req.get("claim", "")
    if not claim:
        return {"ok": False, "error": "claim required"}
    conn = pool.sqlite
    chain = {"sections": [], "cross_refs": [], "sources": [], "gaps": []}

    safe_q = sanitize_fts5(claim)

    # Find matching evidence sections
    if _table_exists("evidence_fts"):
        try:
            rows = conn.execute(
                "SELECT eq.id, eq.quote_text, eq.source_file, eq.category, eq.lane "
                "FROM evidence_fts JOIN evidence_quotes eq ON eq.id = evidence_fts.rowid "
                "WHERE evidence_fts MATCH ? LIMIT 20", (safe_q,)
            ).fetchall()
            chain["sections"] = [dict(r) for r in rows]
        except Exception:
            pass

    # Find authority chain
    if _table_exists("authority_chains_v2"):
        try:
            rows = conn.execute(
                "SELECT primary_citation, supporting_citation, relationship, source_document "
                "FROM authority_chains_v2 WHERE paragraph_context LIKE ? LIMIT 15",
                (f"%{claim[:50]}%",)
            ).fetchall()
            chain["cross_refs"] = [dict(r) for r in rows]
        except Exception:
            pass

    total = len(chain["sections"]) + len(chain["cross_refs"])
    completeness = min(100, total * 5)
    if completeness < 50:
        chain["gaps"].append("Insufficient evidence — need more supporting quotes or authority")

    return {"ok": True, "claim": claim, "chain": chain, "completeness_pct": completeness}


def handle_vector_search(req):
    """Perform REAL vector similarity search using LanceDB (not FTS5 proxy)."""
    query = req.get("query", "")
    top_k = min(req.get("top_k", 10), 50)
    if not query:
        return {"ok": False, "error": "query required"}

    # Try real LanceDB vector search first
    lt = pool.lance_table
    if lt is not None:
        try:
            results = lt.search(query).limit(top_k).to_list()
            return {
                "ok": True,
                "results": [{"text": r.get("text", ""), "score": r.get("_distance", 0), **{k: v for k, v in r.items() if k not in ("text", "vector", "_distance")}} for r in results],
                "count": len(results),
                "method": "lancedb_vector",
            }
        except Exception:
            pass

    # Fallback: FTS5 proxy search
    conn = pool.sqlite
    safe_q = sanitize_fts5(query)
    if _table_exists("evidence_fts") and safe_q:
        try:
            rows = conn.execute(
                "SELECT eq.id, eq.quote_text as text, eq.source_file, eq.category, eq.lane "
                "FROM evidence_fts JOIN evidence_quotes eq ON eq.id = evidence_fts.rowid "
                "WHERE evidence_fts MATCH ? ORDER BY rank LIMIT ?", (safe_q, top_k)
            ).fetchall()
            return {"ok": True, "results": [dict(r) for r in rows], "count": len(rows), "method": "fts5_fallback"}
        except Exception:
            pass

    return {"ok": True, "results": [], "count": 0, "method": "no_search_available"}


def handle_vehicle_map(req):
    """Map a relief type to its litigation vehicle, authority chain, elements, and deadlines."""
    relief_type = req.get("relief_type", "")
    if not relief_type:
        return {"ok": False, "error": "relief_type required"}
    conn = pool.sqlite

    # Search md_sections for vehicle-related content
    if _table_exists("md_sections_fts") and _table_exists("md_sections"):
        safe_q = _sanitize_enhanced(relief_type)
        try:
            rows = conn.execute(
                "SELECT ms.heading, ms.content, ms.source_file "
                "FROM md_sections_fts JOIN md_sections ms ON ms.id = md_sections_fts.rowid "
                "WHERE md_sections_fts MATCH ? LIMIT 15", (safe_q,)
            ).fetchall()
            return {"ok": True, "relief_type": relief_type, "vehicle_sections": [dict(r) for r in rows], "count": len(rows)}
        except Exception:
            pass

    # LIKE fallback
    if _table_exists("md_sections"):
        rows = conn.execute(
            "SELECT heading, content, source_file FROM md_sections WHERE content LIKE ? LIMIT 15",
            (f"%{relief_type}%",)
        ).fetchall()
        return {"ok": True, "relief_type": relief_type, "vehicle_sections": [dict(r) for r in rows], "count": len(rows), "method": "like"}

    return {"ok": True, "relief_type": relief_type, "vehicle_sections": [], "count": 0}


def handle_evolve_md(req):
    """Trigger evolution on .md files — extract sections, cross-refs, link to graph."""
    directory = req.get("directory", "")
    if not directory:
        return {"ok": False, "error": "directory required"}
    if not _validate_path(directory):
        return {"ok": False, "error": f"Path not allowed: {directory}"}

    conn = pool.sqlite
    # Ensure tables exist
    for ddl in [
        "CREATE TABLE IF NOT EXISTS md_sections (id INTEGER PRIMARY KEY, heading TEXT, content TEXT, source_file TEXT, source_path TEXT, level INTEGER DEFAULT 0, parent_heading TEXT)",
        "CREATE TABLE IF NOT EXISTS md_cross_refs (id INTEGER PRIMARY KEY, section_id INTEGER, ref_type TEXT, ref_value TEXT, source_file TEXT)",
    ]:
        conn.execute(ddl)
    conn.commit()

    p = _Path(directory)
    if not p.exists():
        return {"ok": False, "error": f"Directory not found: {directory}"}

    processed = 0
    sections_added = 0
    refs_added = 0
    for md_file in p.rglob("*.md"):
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
            # Check if already evolved
            existing = conn.execute("SELECT COUNT(*) FROM md_sections WHERE source_path = ?", (str(md_file),)).fetchone()[0]
            if existing > 0:
                continue

            # Split into sections by headings
            parts = _HEADING_RE.split(text)
            current_heading = md_file.stem
            current_level = 0
            for i in range(1, len(parts), 3):
                if i + 1 < len(parts):
                    level = len(parts[i])
                    heading = parts[i + 1].strip()
                    content = parts[i + 2].strip() if i + 2 < len(parts) else ""
                    if content:
                        conn.execute(
                            "INSERT INTO md_sections (heading, content, source_file, source_path, level) VALUES (?,?,?,?,?)",
                            (heading, content[:5000], md_file.name, str(md_file), level)
                        )
                        sections_added += 1
                        # Extract cross-references
                        for ref in _extract_cross_refs(content):
                            conn.execute(
                                "INSERT INTO md_cross_refs (section_id, ref_type, ref_value, source_file) VALUES (last_insert_rowid(),?,?,?)",
                                (ref["type"], ref["value"], md_file.name)
                            )
                            refs_added += 1
            processed += 1
        except Exception:
            continue

    conn.commit()
    return {"ok": True, "files_processed": processed, "sections_added": sections_added, "refs_added": refs_added}


def handle_search_evolved(req):
    """FTS5 search across all evolved content (md, txt, pdf sections)."""
    query = req.get("query", "")
    source_type = req.get("source_type")
    limit = min(req.get("limit", 20), 100)
    if not query:
        return {"ok": False, "error": "query required"}

    conn = pool.sqlite
    safe_q = _sanitize_enhanced(query)

    if _table_exists("md_sections_fts"):
        try:
            sql = ("SELECT ms.heading, snippet(md_sections_fts, 0, \'>>>\', \'<<<\', \'...\', 40) as snippet, ms.source_file "
                   "FROM md_sections_fts JOIN md_sections ms ON ms.id = md_sections_fts.rowid "
                   "WHERE md_sections_fts MATCH ?")
            params = [safe_q]
            if source_type:
                sql += " AND ms.source_file LIKE ?"
                params.append(f"%.{source_type}")
            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return {"ok": True, "results": [dict(r) for r in rows], "count": len(rows), "method": "fts5"}
        except Exception:
            pass

    if _table_exists("md_sections"):
        rows = conn.execute(
            "SELECT heading, substr(content, 1, 200) as snippet, source_file FROM md_sections WHERE content LIKE ? LIMIT ?",
            (f"%{query}%", limit)
        ).fetchall()
        return {"ok": True, "results": [dict(r) for r in rows], "count": len(rows), "method": "like_fallback"}

    return {"ok": True, "results": [], "count": 0}


def handle_cross_refs(req):
    """Query the cross-reference network for matching references."""
    query = req.get("query", "")
    ref_type = req.get("ref_type")
    limit = min(req.get("limit", 50), 200)
    if not query:
        return {"ok": False, "error": "query required"}

    conn = pool.sqlite
    if not _table_exists("md_cross_refs"):
        return {"ok": True, "refs": [], "count": 0, "note": "md_cross_refs table not found"}

    sql = "SELECT cr.ref_type, cr.ref_value, cr.source_file, ms.heading FROM md_cross_refs cr LEFT JOIN md_sections ms ON cr.section_id = ms.id WHERE cr.ref_value LIKE ?"
    params = [f"%{query}%"]
    if ref_type:
        sql += " AND cr.ref_type = ?"
        params.append(ref_type)
    sql += f" LIMIT {limit}"

    rows = conn.execute(sql, params).fetchall()
    return {"ok": True, "refs": [dict(r) for r in rows], "count": len(rows)}


def handle_evolution_stats(req):
    """Get evolution coverage statistics."""
    conn = pool.sqlite
    stats = {"md_files": 0, "total_sections": 0, "cross_refs": 0, "pages_evolved": 0}

    if _table_exists("md_sections"):
        stats["total_sections"] = conn.execute("SELECT COUNT(*) FROM md_sections").fetchone()[0]
        stats["md_files"] = conn.execute("SELECT COUNT(DISTINCT source_path) FROM md_sections").fetchone()[0]

    if _table_exists("md_cross_refs"):
        stats["cross_refs"] = conn.execute("SELECT COUNT(*) FROM md_cross_refs").fetchone()[0]

    if _table_exists("pages"):
        stats["pages_evolved"] = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]

    return {"ok": True, **stats}


def handle_search_master(req):
    """Search across master CSV data."""
    query = req.get("query", "")
    dataset = req.get("dataset")
    limit = min(req.get("limit", 20), 100)
    if not query:
        return {"ok": False, "error": "query required"}

    conn = pool.sqlite

    if _table_exists("master_data_fts") and _table_exists("master_data"):
        safe_q = _sanitize_enhanced(query)
        try:
            sql = ("SELECT md.dataset, md.row_number, snippet(master_data_fts, 0, \'>>>\', \'<<<\', \'...\', 40) as snippet "
                   "FROM master_data_fts JOIN master_data md ON md.id = master_data_fts.rowid "
                   "WHERE master_data_fts MATCH ?")
            params = [safe_q]
            if dataset:
                sql += " AND md.dataset = ?"
                params.append(dataset)
            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return {"ok": True, "results": [dict(r) for r in rows], "count": len(rows), "method": "fts5"}
        except Exception:
            pass

    if _table_exists("master_data"):
        sql = "SELECT dataset, row_number, substr(text_content, 1, 200) as snippet FROM master_data WHERE text_content LIKE ?"
        params = [f"%{query}%"]
        if dataset:
            sql += " AND dataset = ?"
            params.append(dataset)
        sql += " LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return {"ok": True, "results": [dict(r) for r in rows], "count": len(rows), "method": "like_fallback"}

    return {"ok": True, "results": [], "count": 0}


def handle_subagent_spec(req):
    """Retrieve specification for a SUPERPIN sub-agent."""
    agent_name = req.get("agent_name", "")
    if not agent_name:
        return {"ok": False, "error": "agent_name required"}
    conn = pool.sqlite

    results = []
    # Search md_sections for agent specs
    if _table_exists("md_sections"):
        rows = conn.execute(
            "SELECT heading, content, source_file FROM md_sections "
            "WHERE (heading LIKE ? OR content LIKE ?) LIMIT 10",
            (f"%{agent_name}%", f"%AGENT:{agent_name}%")
        ).fetchall()
        results = [dict(r) for r in rows]

    # Also check cross-refs tagged as agent
    if _table_exists("md_cross_refs"):
        refs = conn.execute(
            "SELECT ref_value, source_file FROM md_cross_refs WHERE ref_type = \'agent\' AND ref_value LIKE ? LIMIT 10",
            (f"%{agent_name}%",)
        ).fetchall()
        if refs:
            results.append({"_agent_refs": [dict(r) for r in refs]})

    return {"ok": True, "agent_name": agent_name, "specs": results, "count": len(results)}


def handle_dispatch_swarm(req):
    """Dispatch a task to the agent swarm for recommendations."""
    task = req.get("task", "")
    if not task:
        return {"ok": False, "error": "task required"}

    # Agent recommendation based on keyword matching
    AGENT_MAP = [
        (["evidence", "quote", "search", "find"], "evidence-warfare-commander", "Evidence search and gap analysis"),
        (["filing", "motion", "brief", "draft"], "filing-forge-master", "Filing assembly and QA"),
        (["judge", "mcneill", "judicial", "bias"], "judicial-accountability-engine", "Judicial misconduct documentation"),
        (["impeach", "contradict", "credibility"], "impeachment-commander", "Cross-examination preparation"),
        (["custody", "parenting", "child", "best interest"], "family-law-guardian", "Custody analysis"),
        (["appeal", "coa", "msc", "appellate"], "appellate-record-builder", "Appellate record assembly"),
        (["federal", "1983", "civil rights"], "federal-1983-specialist", "Federal civil rights claims"),
        (["ppo", "protection order"], "compliance-auditor", "PPO compliance and tracking"),
        (["damage", "cost", "fee"], "damages-calculator", "Damages calculation"),
        (["deadline", "timeline", "calendar"], "deadline-sentinel", "Deadline tracking"),
    ]

    task_lower = task.lower()
    recommendations = []
    for keywords, agent, description in AGENT_MAP:
        relevance = sum(1 for k in keywords if k in task_lower)
        if relevance > 0:
            recommendations.append({"agent": agent, "description": description, "relevance": relevance})

    recommendations.sort(key=lambda x: -x["relevance"])
    return {"ok": True, "task": task, "recommendations": recommendations[:5], "count": len(recommendations)}

'''

# ═══════════════════════════════════════════════════════════════════════════
# NEW HANDLERS DICT (replaces the old one)
# ═══════════════════════════════════════════════════════════════════════════

NEW_HANDLERS_DICT = '''HANDLERS = {
    # ── Original 24 actions ──
    "ping": handle_ping,
    "query": handle_query,
    "analytics": handle_analytics,
    "stats": handle_stats,
    "fts_search": handle_fts_search,
    "search_evidence": handle_search_evidence,
    "search_impeachment": handle_search_impeachment,
    "search_contradictions": handle_search_contradictions,
    "search_authority": handle_search_authority,
    "nexus_fuse": handle_nexus_fuse,
    "nexus_argue": handle_nexus_argue,
    "nexus_readiness": handle_nexus_readiness,
    "nexus_damages": handle_nexus_damages,
    "narrative": handle_narrative,
    "filing_plan": handle_filing_plan,
    "rules_check": handle_rules_check,
    "adversary": handle_adversary,
    "gap_analysis": handle_gap_analysis,
    "cross_connect": handle_cross_connect,
    "judicial_intel": handle_judicial_intel,
    "timeline_search": handle_timeline_search,
    "case_context": handle_case_context,
    "filing_status": handle_filing_status,
    "deadlines": handle_deadlines,
    # ── Absorbed MCP capabilities (22 new actions) ──
    "list_documents": handle_list_documents,
    "get_document": handle_get_document,
    "search_pages": handle_search_pages,
    "search_rules": handle_search_rules,
    "search_graph": handle_search_graph,
    "lookup_authority": handle_lookup_authority,
    "risk_events": handle_risk_events,
    "self_test": handle_self_test,
    "self_audit": handle_self_audit,
    "convergence_status": handle_convergence_status,
    "compute_deadlines_ext": handle_compute_deadlines_ext,
    "red_team": handle_red_team,
    "evidence_chain": handle_evidence_chain,
    "vector_search": handle_vector_search,
    "vehicle_map": handle_vehicle_map,
    "evolve_md": handle_evolve_md,
    "search_evolved": handle_search_evolved,
    "cross_refs": handle_cross_refs,
    "evolution_stats": handle_evolution_stats,
    "search_master": handle_search_master,
    "subagent_spec": handle_subagent_spec,
    "dispatch_swarm": handle_dispatch_swarm,
}'''

# ═══════════════════════════════════════════════════════════════════════════
# MERGE LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print(f"[ABSORB] Reading daemon from {DAEMON_PATH}")
    original = DAEMON_PATH.read_text(encoding="utf-8")
    lines = original.split("\n")
    total_lines = len(lines)
    print(f"[ABSORB] Original: {total_lines} lines, {len(original)} bytes")

    # Backup
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DAEMON_PATH, BACKUP_PATH)
    print(f"[ABSORB] Backup saved to {BACKUP_PATH}")

    # Find insertion points
    # 1. After sanitize_fts5 function (after "return re.sub..." line ~97)
    helpers_insert_line = None
    for i, line in enumerate(lines):
        if "return re.sub" in line and "sanitize_fts5" in lines[i-1] if i > 0 else False:
            helpers_insert_line = i + 1
            break
    if helpers_insert_line is None:
        # Fallback: search for the function
        for i, line in enumerate(lines):
            if line.strip().startswith("def sanitize_fts5"):
                # Find end of function
                for j in range(i+1, min(i+10, total_lines)):
                    if lines[j].strip().startswith("return"):
                        helpers_insert_line = j + 1
                        break
                break

    if helpers_insert_line is None:
        print("[ERROR] Could not find sanitize_fts5 function for helper insertion")
        return 1

    print(f"[ABSORB] Helpers insertion point: line {helpers_insert_line + 1}")

    # 2. Before ACTION ROUTER section
    handlers_insert_line = None
    for i, line in enumerate(lines):
        if "ACTION ROUTER" in line:
            handlers_insert_line = i - 1  # Insert before the comment
            break

    if handlers_insert_line is None:
        print("[ERROR] Could not find ACTION ROUTER section")
        return 1

    print(f"[ABSORB] Handlers insertion point: line {handlers_insert_line + 1}")

    # 3. Find HANDLERS dict to replace
    handlers_dict_start = None
    handlers_dict_end = None
    for i, line in enumerate(lines):
        if line.startswith("HANDLERS = {"):
            handlers_dict_start = i
        if handlers_dict_start and line.strip() == "}" and i > handlers_dict_start:
            handlers_dict_end = i
            break

    if handlers_dict_start is None or handlers_dict_end is None:
        print("[ERROR] Could not find HANDLERS dict boundaries")
        return 1

    print(f"[ABSORB] HANDLERS dict: lines {handlers_dict_start + 1}-{handlers_dict_end + 1}")

    # Build new file
    new_lines = []

    # Part 1: Everything up to and including sanitize_fts5
    new_lines.extend(lines[:helpers_insert_line])

    # Part 2: Insert helpers
    new_lines.extend(HELPERS_BLOCK.split("\n"))

    # Part 3: Everything from after sanitize_fts5 to before ACTION ROUTER
    new_lines.extend(lines[helpers_insert_line:handlers_insert_line])

    # Part 4: Insert new handlers
    new_lines.extend(HANDLERS_BLOCK.split("\n"))

    # Part 5: ACTION ROUTER section header
    new_lines.extend(lines[handlers_insert_line:handlers_dict_start])

    # Part 6: New HANDLERS dict (replaces old)
    new_lines.extend(NEW_HANDLERS_DICT.split("\n"))

    # Part 7: Everything after old HANDLERS dict
    new_lines.extend(lines[handlers_dict_end + 1:])

    merged = "\n".join(new_lines)
    print(f"[ABSORB] Merged: {len(new_lines)} lines, {len(merged)} bytes")

    # Update the docstring action list
    old_actions_end = "Started by extension.mjs on load. Stays alive for entire session."
    new_actions_doc = """  list_documents   — List documents in knowledge base
  get_document     — Get document text by ID
  search_pages     — FTS5 search across PDF pages
  search_rules     — MCR/MCL rules lookup
  search_graph     — Knowledge graph node search
  lookup_authority — Authority lookup with pin cites
  risk_events      — Litigation risk events
  self_test        — Diagnostic self-tests
  self_audit       — Data quality audit (score 0-100)
  convergence_status — Convergence check
  compute_deadlines_ext — Deadline computation
  red_team         — Red-team validation
  evidence_chain   — Evidence chain tracing
  vector_search    — REAL LanceDB vector search
  vehicle_map      — Relief→vehicle mapping
  evolve_md        — Markdown evolution
  search_evolved   — Search evolved content
  cross_refs       — Cross-reference lookup
  evolution_stats  — Evolution coverage stats
  search_master    — Master CSV search
  subagent_spec    — Subagent specification
  dispatch_swarm   — Agent swarm dispatch

""" + old_actions_end
    merged = merged.replace(old_actions_end, new_actions_doc)

    # Syntax check
    print("[ABSORB] Validating syntax...")
    try:
        ast.parse(merged)
        print("[ABSORB] ✅ Syntax valid!")
    except SyntaxError as e:
        print(f"[ABSORB] ❌ Syntax error: {e}")
        # Write to temp for debugging
        debug_path = Path(r"D:\LitigationOS_tmp\nexus_daemon_debug.py")
        debug_path.write_text(merged, encoding="utf-8")
        print(f"[ABSORB] Debug file written to {debug_path}")
        return 1

    # Write merged file
    DAEMON_PATH.write_text(merged, encoding="utf-8")
    print(f"[ABSORB] ✅ Written to {DAEMON_PATH}")

    # Also update backup
    backup2 = Path(r"C:\Users\andre\LitigationOS\scripts\nexus_daemon.py")
    if backup2.parent.exists():
        shutil.copy2(DAEMON_PATH, backup2)
        print(f"[ABSORB] Backup synced to {backup2}")

    print(f"\n[ABSORB] COMPLETE: 24 original + 22 new = 46 total actions")
    return 0


if __name__ == "__main__":
    exit(main())
