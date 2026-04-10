"""New handler code block to insert into nexus_daemon.py.
This file is used by splice_daemon.py — not executed directly.
"""

NEW_HANDLERS_CODE = r'''

# ══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (shared by ported MCP handlers)
# ══════════════════════════════════════════════════════════════════════════


def _table_exists(table_name):
    """Check if a table exists in the database."""
    try:
        row = pool.sqlite.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        ).fetchone()
        return row is not None
    except Exception:
        return False


def _count_table(conn, table_name):
    """Count rows in a table safely."""
    if not _table_exists(table_name):
        return 0
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()
        return row[0] if row else 0
    except Exception:
        return 0


def _paginated_query(conn, sql, params, limit=20, offset=0):
    """Execute a paginated query returning column names and row dicts."""
    full_sql = f"{sql} LIMIT ? OFFSET ?"
    full_params = list(params) + [limit, offset]
    cur = conn.execute(full_sql, full_params)
    columns = [desc[0] for desc in cur.description] if cur.description else []
    rows = [dict(zip(columns, r)) for r in cur.fetchall()]
    return columns, rows


# ══════════════════════════════════════════════════════════════════════════
# DOCUMENT MANAGEMENT HANDLERS
# ══════════════════════════════════════════════════════════════════════════


def handle_list_documents(req):
    """List documents in the knowledge base with metadata."""
    conn = pool.sqlite
    if not _table_exists("documents"):
        return {"ok": True, "documents": [], "count": 0, "note": "documents table not found"}

    limit = min(req.get("limit", 20), 100)
    offset = req.get("offset", 0)
    name_filter = req.get("name_filter")

    cols_info = conn.execute("PRAGMA table_info(documents)").fetchall()
    col_names = {c[1] for c in cols_info}

    select_cols = []
    for c in ["id", "file_name", "title", "file_path", "file_size_bytes",
              "page_count", "created_at", "doc_type", "content_preview"]:
        if c in col_names:
            select_cols.append(c)
    if "id" not in col_names:
        select_cols.insert(0, "rowid AS id")
    if not select_cols:
        select_cols = ["*"]

    sql = f"SELECT {', '.join(select_cols)} FROM documents"
    params = []
    if name_filter:
        filter_col = next((c for c in ["file_name", "title", "file_path"] if c in col_names), None)
        if filter_col:
            sql += f" WHERE {filter_col} LIKE ?"
            params.append(f"%{name_filter}%")

    sql += " ORDER BY rowid DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    try:
        cur = conn.execute(sql, params)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = [dict(zip(columns, r)) for r in cur.fetchall()]
        total = _count_table(conn, "documents")
        return {"ok": True, "documents": rows, "count": len(rows), "total": total}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_get_document(req):
    """Retrieve full extracted text of a document by ID."""
    conn = pool.sqlite
    doc_id = req.get("document_id")
    if not doc_id:
        return {"ok": False, "error": "document_id required"}

    page_numbers = req.get("page_numbers")
    doc_meta = {}

    if _table_exists("documents"):
        try:
            doc = conn.execute(
                "SELECT * FROM documents WHERE rowid = ?", (doc_id,)
            ).fetchone()
            if doc:
                doc_meta = dict(doc)
        except Exception:
            pass

    pages = []
    if _table_exists("pages"):
        try:
            cols_info = conn.execute("PRAGMA table_info(pages)").fetchall()
            pcols = {c[1] for c in cols_info}
            doc_col = next((c for c in ["document_id", "doc_id"] if c in pcols), None)
            text_col = next((c for c in ["text", "content", "page_text"] if c in pcols), None)
            page_col = next((c for c in ["page_number", "page_num", "page"] if c in pcols), None)

            if doc_col and text_col:
                if page_numbers and page_col:
                    ph = ",".join("?" * len(page_numbers))
                    sql = f"SELECT {page_col}, {text_col} FROM pages WHERE {doc_col} = ? AND {page_col} IN ({ph}) ORDER BY {page_col}"
                    cur = conn.execute(sql, [doc_id] + list(page_numbers))
                else:
                    order = f"ORDER BY {page_col}" if page_col else ""
                    sql = f"SELECT {page_col or 'rowid'} AS page_number, {text_col} FROM pages WHERE {doc_col} = ? {order}"
                    cur = conn.execute(sql, (doc_id,))
                pages = [{"page": r[0], "text": r[1]} for r in cur.fetchall()]
        except Exception as e:
            return {"ok": False, "error": f"Error reading pages: {e}"}

    return {"ok": True, "document": doc_meta, "pages": pages, "page_count": len(pages)}


def handle_search_documents(req):
    """Full-text search across all ingested PDF content."""
    conn = pool.sqlite
    query = req.get("query", "").strip()
    if not query:
        return {"ok": False, "error": "query required"}

    limit = min(req.get("limit", 20), 100)
    offset = req.get("offset", 0)
    clean = sanitize_fts5(query)

    if _table_exists("pages_fts") and _table_exists("pages"):
        try:
            cur = conn.execute(
                """SELECT p.document_id, p.page_number,
                          snippet(pages_fts, 0, '>>>', '<<<', '...', 60) AS snippet
                   FROM pages_fts
                   JOIN pages p ON p.rowid = pages_fts.rowid
                   WHERE pages_fts MATCH ?
                   ORDER BY rank LIMIT ? OFFSET ?""",
                (clean, limit, offset)
            )
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, r)) for r in cur.fetchall()]
            return {"ok": True, "results": rows, "count": len(rows), "engine": "fts5"}
        except Exception:
            pass

    if _table_exists("pages"):
        try:
            cur = conn.execute(
                """SELECT document_id, page_number,
                          substr(text, max(1, instr(lower(text), lower(?)) - 60), 150) AS snippet
                   FROM pages WHERE text LIKE ?
                   LIMIT ? OFFSET ?""",
                (query, f"%{query}%", limit, offset)
            )
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, r)) for r in cur.fetchall()]
            return {"ok": True, "results": rows, "count": len(rows), "engine": "like"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return {"ok": True, "results": [], "count": 0, "note": "No searchable content tables found"}


def handle_ingest_pdf(_req):
    """Ingest a PDF. BLOCKED: daemon is read-only."""
    return {"ok": False, "error": "BLOCKED: Daemon is READ-ONLY. Use exec_python with a dedicated ingest script."}


def handle_bulk_ingest(_req):
    """Bulk ingest PDFs. BLOCKED: daemon is read-only."""
    return {"ok": False, "error": "BLOCKED: Daemon is READ-ONLY. Use exec_python with a dedicated ingest script."}


# ══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH & RULES HANDLERS
# ══════════════════════════════════════════════════════════════════════════


def handle_lookup_rule(req):
    """Look up Michigan Court Rules (MCR/MCL) by citation or keyword."""
    conn = pool.sqlite
    query = req.get("query", "").strip()
    if not query:
        return {"ok": False, "error": "query required"}

    limit = min(req.get("limit", 20), 100)
    offset = req.get("offset", 0)

    if not _table_exists("michigan_rules_extracted"):
        return {"ok": True, "rules": [], "count": 0, "note": "michigan_rules_extracted not found"}

    try:
        cur = conn.execute(
            """SELECT rule_number, rule_type, title, full_text
               FROM michigan_rules_extracted
               WHERE rule_number LIKE ?
               LIMIT ? OFFSET ?""",
            (f"%{query}%", limit, offset)
        )
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, r)) for r in cur.fetchall()]
        if results:
            return {"ok": True, "rules": results, "count": len(results), "match": "citation"}
    except Exception:
        pass

    try:
        cur = conn.execute(
            """SELECT rule_number, rule_type, title,
                      substr(full_text, 1, 500) AS excerpt
               FROM michigan_rules_extracted
               WHERE full_text LIKE ? OR title LIKE ?
               LIMIT ? OFFSET ?""",
            (f"%{query}%", f"%{query}%", limit, offset)
        )
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, r)) for r in cur.fetchall()]
    except Exception as e:
        return {"ok": False, "error": str(e)}

    return {"ok": True, "rules": results, "count": len(results), "match": "text"}


def handle_query_graph(req):
    """Search the knowledge graph for authorities, case law, forms, procedures."""
    conn = pool.sqlite
    query = req.get("query", "").strip()
    if not query:
        return {"ok": False, "error": "query required"}

    limit = min(req.get("limit", 20), 100)
    node_type = req.get("node_type")
    graph_source = req.get("graph_source")
    results = []

    for table in ["knowledge_graph", "graph_nodes", "authority_graph"]:
        if not _table_exists(table):
            continue

        cols_info = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
        col_names = {c[1] for c in cols_info}

        where_parts = []
        params = []
        label_col = next((c for c in ["label", "name", "node_id"] if c in col_names), None)
        if label_col:
            search_expr = f"({label_col} LIKE ?"
            params.append(f"%{query}%")
            if "node_id" in col_names and label_col != "node_id":
                search_expr += " OR node_id LIKE ?"
                params.append(f"%{query}%")
            search_expr += ")"
            where_parts.append(search_expr)

        if node_type and "node_type" in col_names:
            where_parts.append("node_type = ?")
            params.append(node_type)
        if graph_source and "graph_source" in col_names:
            where_parts.append("graph_source = ?")
            params.append(graph_source)

        if not where_parts:
            continue

        try:
            params.append(limit)
            cur = conn.execute(
                f"SELECT * FROM [{table}] WHERE {' AND '.join(where_parts)} LIMIT ?", params
            )
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, r)) for r in cur.fetchall()]
            results.extend(rows)
        except Exception:
            continue

    return {"ok": True, "nodes": results[:limit], "count": min(len(results), limit)}


def handle_lookup_authority(req):
    """Look up specific legal authorities (case law, statutes, court rules)."""
    conn = pool.sqlite
    query = req.get("query", "").strip()
    if not query:
        return {"ok": False, "error": "query required"}

    limit = min(req.get("limit", 20), 100)
    node_type = req.get("node_type")
    results = []

    if _table_exists("authority_chains_v2"):
        try:
            where = "primary_citation LIKE ? OR supporting_citation LIKE ?"
            params = [f"%{query}%", f"%{query}%"]
            if node_type:
                where += " AND source_type = ?"
                params.append(node_type)
            params.append(limit)
            cur = conn.execute(
                f"""SELECT primary_citation, supporting_citation, relationship,
                           source_document, source_type, lane
                    FROM authority_chains_v2 WHERE {where} LIMIT ?""", params
            )
            columns = [desc[0] for desc in cur.description]
            results.extend([dict(zip(columns, r)) for r in cur.fetchall()])
        except Exception:
            pass

    if _table_exists("master_citations") and len(results) < limit:
        try:
            cols_info = conn.execute("PRAGMA table_info(master_citations)").fetchall()
            cn = {c[1] for c in cols_info}
            cit_col = next((c for c in ["citation", "cite", "reference"] if c in cn), None)
            if cit_col:
                cur = conn.execute(
                    f"SELECT * FROM master_citations WHERE [{cit_col}] LIKE ? LIMIT ?",
                    (f"%{query}%", limit - len(results))
                )
                columns = [desc[0] for desc in cur.description]
                results.extend([dict(zip(columns, r)) for r in cur.fetchall()])
        except Exception:
            pass

    return {"ok": True, "authorities": results[:limit], "count": min(len(results), limit)}


# ══════════════════════════════════════════════════════════════════════════
# INTELLIGENCE HANDLERS
# ══════════════════════════════════════════════════════════════════════════


def handle_assess_risk(req):
    """Assess litigation risks from the risk event taxonomy."""
    conn = pool.sqlite
    severity_min = req.get("severity_min", 0)
    risk_class = req.get("risk_class")
    results = []

    for table in ["risk_events", "litigation_risks", "risk_taxonomy"]:
        if not _table_exists(table):
            continue

        cols_info = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
        col_names = {c[1] for c in cols_info}

        where_parts = []
        params = []

        sev_col = next((c for c in ["severity", "severity_score", "risk_score"] if c in col_names), None)
        if sev_col and severity_min > 0:
            where_parts.append(f"{sev_col} >= ?")
            params.append(severity_min)

        class_col = next((c for c in ["risk_class", "classification", "category"] if c in col_names), None)
        if class_col and risk_class:
            where_parts.append(f"{class_col} = ?")
            params.append(risk_class)

        where = " AND ".join(where_parts) if where_parts else "1=1"
        order = f"ORDER BY {sev_col} DESC" if sev_col else "ORDER BY rowid DESC"

        try:
            cur = conn.execute(f"SELECT * FROM [{table}] WHERE {where} {order} LIMIT 50", params)
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, r)) for r in cur.fetchall()]
        except Exception:
            continue
        break

    return {"ok": True, "risks": results, "count": len(results)}


def handle_get_vehicle_map(req):
    """Map relief type to litigation vehicle, authority chain, and deadlines."""
    conn = pool.sqlite
    relief_type = req.get("relief_type", "").strip()
    if not relief_type:
        return {"ok": False, "error": "relief_type required"}

    results = []
    if _table_exists("md_sections_fts") and _table_exists("md_sections"):
        clean = sanitize_fts5(relief_type)
        if clean:
            try:
                cur = conn.execute(
                    """SELECT ms.file_path, ms.heading, ms.content
                       FROM md_sections_fts
                       JOIN md_sections ms ON ms.rowid = md_sections_fts.rowid
                       WHERE md_sections_fts MATCH ?
                       ORDER BY rank LIMIT 20""", (clean,)
                )
                for row in cur.fetchall():
                    text = (row[2] or "").lower()
                    if any(kw in text for kw in ["vehicle", "authority", "element", "deadline", "relief"]):
                        results.append({"file": row[0], "heading": row[1], "excerpt": (row[2] or "")[:500]})
            except Exception:
                pass

    if not results and _table_exists("md_sections"):
        try:
            cur = conn.execute(
                """SELECT file_path, heading, substr(content, 1, 500) AS excerpt
                   FROM md_sections
                   WHERE content LIKE ?
                     AND (content LIKE '%vehicle%' OR content LIKE '%authority%' OR content LIKE '%deadline%')
                   LIMIT 20""", (f"%{relief_type}%",)
            )
            results = [{"file": r[0], "heading": r[1], "excerpt": r[2]} for r in cur.fetchall()]
        except Exception:
            pass

    return {"ok": True, "vehicle_map": results, "count": len(results)}


def handle_case_health(_req):
    """Case health dashboard — evidence, harms, impeachment, contradictions, deadlines."""
    conn = pool.sqlite
    health = {}
    for table, key in [
        ("evidence_quotes", "evidence_count"),
        ("timeline_events", "timeline_count"),
        ("impeachment_matrix", "impeachment_count"),
        ("contradiction_map", "contradiction_count"),
        ("judicial_violations", "judicial_violation_count"),
        ("authority_chains_v2", "authority_count"),
        ("police_reports", "police_report_count"),
        ("deadlines", "deadline_count"),
        ("filing_packages", "filing_count"),
    ]:
        health[key] = _count_table(conn, table)
    health["separation_days"] = (date.today() - date(2025, 7, 29)).days
    return {"ok": True, "health": health}


def handle_adversary_threats(req):
    """Ranked adversary threat matrix with harm counts."""
    conn = pool.sqlite
    limit = min(req.get("limit", 20), 200)

    if not _table_exists("impeachment_matrix"):
        return {"ok": True, "threats": [], "count": 0, "note": "impeachment_matrix not found"}

    cols_info = conn.execute("PRAGMA table_info(impeachment_matrix)").fetchall()
    col_names = {c[1] for c in cols_info}
    target_col = next((c for c in ["target", "actor", "person", "witness"] if c in col_names), None)
    results = []

    if target_col:
        try:
            cur = conn.execute(
                f"""SELECT {target_col} AS adversary,
                           COUNT(*) AS harm_count,
                           COUNT(DISTINCT category) AS category_spread
                    FROM impeachment_matrix
                    GROUP BY {target_col}
                    ORDER BY harm_count DESC LIMIT ?""", (limit,)
            )
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, r)) for r in cur.fetchall()]
        except Exception:
            pass

    return {"ok": True, "threats": results, "count": len(results)}


def handle_filing_pipeline(_req):
    """Filing pipeline — every action with phase, readiness, risk score, gaps."""
    conn = pool.sqlite

    for table in ["filing_packages", "filing_readiness"]:
        if _table_exists(table):
            try:
                cur = conn.execute(f"SELECT * FROM [{table}] ORDER BY rowid")
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, r)) for r in cur.fetchall()]
                return {"ok": True, "pipeline": results, "count": len(results), "source": table}
            except Exception:
                continue

    return {"ok": True, "pipeline": [], "count": 0, "note": "No filing pipeline table found"}


def handle_get_subagent_spec(req):
    """Retrieve the specification for a SUPERPIN sub-agent."""
    conn = pool.sqlite
    agent_name = req.get("agent_name", "").strip()
    if not agent_name:
        return {"ok": False, "error": "agent_name required"}

    results = []
    if _table_exists("md_sections_fts") and _table_exists("md_sections"):
        clean = sanitize_fts5(agent_name)
        if clean:
            try:
                cur = conn.execute(
                    """SELECT ms.file_path, ms.heading, ms.content
                       FROM md_sections_fts
                       JOIN md_sections ms ON ms.rowid = md_sections_fts.rowid
                       WHERE md_sections_fts MATCH ?
                       ORDER BY rank LIMIT 10""", (clean,)
                )
                for row in cur.fetchall():
                    text = row[2] or ""
                    if "agent" in text.lower() or agent_name.lower() in text.lower():
                        results.append({"file": row[0], "heading": row[1], "excerpt": text[:1000]})
            except Exception:
                pass

    if not results and _table_exists("md_sections"):
        try:
            cur = conn.execute(
                """SELECT file_path, heading, substr(content, 1, 1000) AS excerpt
                   FROM md_sections WHERE content LIKE ? LIMIT 10""",
                (f"%{agent_name}%",)
            )
            results = [{"file": r[0], "heading": r[1], "excerpt": r[2]} for r in cur.fetchall()]
        except Exception:
            pass

    return {"ok": True, "agent_spec": results, "count": len(results)}


# ══════════════════════════════════════════════════════════════════════════
# EVOLUTION PIPELINE HANDLERS
# ══════════════════════════════════════════════════════════════════════════


def handle_evolution_stats(_req):
    """Evolution coverage statistics dashboard."""
    conn = pool.sqlite
    stats = {
        "md_sections": _count_table(conn, "md_sections"),
        "md_cross_refs": _count_table(conn, "md_cross_refs"),
    }

    if _table_exists("pdf_sections"):
        stats["pdf_sections"] = _count_table(conn, "pdf_sections")

    if _table_exists("md_sections"):
        try:
            cur = conn.execute(
                """SELECT
                       SUM(CASE WHEN file_path LIKE '%.md' THEN 1 ELSE 0 END) AS md_count,
                       SUM(CASE WHEN file_path LIKE '%.txt' THEN 1 ELSE 0 END) AS txt_count,
                       SUM(CASE WHEN file_path LIKE '%.pdf' THEN 1 ELSE 0 END) AS pdf_count,
                       COUNT(DISTINCT file_path) AS files_evolved
                   FROM md_sections"""
            )
            row = cur.fetchone()
            if row:
                stats.update({"md_files": row[0] or 0, "txt_files": row[1] or 0,
                              "pdf_files": row[2] or 0, "files_evolved": row[3] or 0})
        except Exception:
            pass

    if _table_exists("md_cross_refs"):
        try:
            cur = conn.execute(
                "SELECT ref_type, COUNT(*) AS cnt FROM md_cross_refs GROUP BY ref_type ORDER BY cnt DESC"
            )
            stats["cross_ref_types"] = [{"type": r[0], "count": r[1]} for r in cur.fetchall()]
        except Exception:
            pass

    return {"ok": True, "evolution": stats}


def handle_search_evolved(req):
    """FTS5 search across all evolved content (md, txt, pdf sections)."""
    conn = pool.sqlite
    query = req.get("query", "").strip()
    if not query:
        return {"ok": False, "error": "query required"}

    limit = min(req.get("limit", 20), 100)
    source_type = req.get("source_type")
    clean = sanitize_fts5(query)

    if _table_exists("md_sections_fts") and _table_exists("md_sections"):
        try:
            fts_where = ""
            params = [clean]
            if source_type:
                fts_where = " AND ms.file_path LIKE ?"
                params.append(f"%.{source_type}")
            params.append(limit)

            cur = conn.execute(
                f"""SELECT ms.file_path, ms.heading,
                           snippet(md_sections_fts, 0, '>>>', '<<<', '...', 60) AS snippet
                    FROM md_sections_fts
                    JOIN md_sections ms ON ms.rowid = md_sections_fts.rowid
                    WHERE md_sections_fts MATCH ?{fts_where}
                    ORDER BY rank LIMIT ?""", params
            )
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, r)) for r in cur.fetchall()]
            return {"ok": True, "results": rows, "count": len(rows), "engine": "fts5"}
        except Exception:
            pass

    if _table_exists("md_sections"):
        try:
            like_where = ""
            params = [query, f"%{query}%"]
            if source_type:
                like_where = " AND file_path LIKE ?"
                params.append(f"%.{source_type}")
            params.append(limit)

            cur = conn.execute(
                f"""SELECT file_path, heading,
                           substr(content, max(1, instr(lower(content), lower(?)) - 60), 150) AS snippet
                    FROM md_sections WHERE content LIKE ?{like_where}
                    LIMIT ?""", params
            )
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, r)) for r in cur.fetchall()]
            return {"ok": True, "results": rows, "count": len(rows), "engine": "like"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return {"ok": True, "results": [], "count": 0, "note": "No evolved content tables found"}


def handle_cross_refs(req):
    """Query the cross-reference network for matching references."""
    conn = pool.sqlite
    query = req.get("query", "").strip()
    if not query:
        return {"ok": False, "error": "query required"}

    limit = min(req.get("limit", 50), 200)
    ref_type = req.get("ref_type")

    if not _table_exists("md_cross_refs"):
        return {"ok": True, "cross_refs": [], "count": 0, "note": "md_cross_refs not found"}

    cols_info = conn.execute("PRAGMA table_info(md_cross_refs)").fetchall()
    col_names = {c[1] for c in cols_info}
    val_col = next((c for c in ["ref_value", "value", "reference"] if c in col_names), None)
    type_col = next((c for c in ["ref_type", "type"] if c in col_names), None)
    sec_col = next((c for c in ["section_id", "source_section"] if c in col_names), None)
    file_col = next((c for c in ["file_path", "source_file"] if c in col_names), None)

    select_parts = []
    if type_col: select_parts.append(type_col)
    if val_col: select_parts.append(val_col)
    if sec_col: select_parts.append(sec_col)
    if file_col: select_parts.append(file_col)
    if not select_parts:
        select_parts = ["*"]

    where_parts = []
    params = []
    if val_col:
        where_parts.append(f"{val_col} LIKE ?")
        params.append(f"%{query}%")
    if ref_type and type_col:
        where_parts.append(f"{type_col} = ?")
        params.append(ref_type)

    if not where_parts:
        return {"ok": True, "cross_refs": [], "count": 0}

    params.append(limit)
    try:
        cur = conn.execute(
            f"SELECT {', '.join(select_parts)} FROM md_cross_refs WHERE {' AND '.join(where_parts)} LIMIT ?",
            params
        )
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, r)) for r in cur.fetchall()]
        return {"ok": True, "cross_refs": rows, "count": len(rows)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_convergence_status(_req):
    """Check convergence status of the knowledge base."""
    conn = pool.sqlite
    status = {"converged": False, "quality_score": 0, "core_tables": {}}

    for t in ["evidence_quotes", "authority_chains_v2", "michigan_rules_extracted",
              "timeline_events", "md_sections", "md_cross_refs"]:
        status["core_tables"][t] = _count_table(conn, t)

    if _table_exists("convergence_domains"):
        try:
            cur = conn.execute(
                "SELECT status, COUNT(*) AS cnt FROM convergence_domains GROUP BY status"
            )
            status["domain_status"] = {r[0]: r[1] for r in cur.fetchall()}
        except Exception:
            pass

    if _table_exists("convergence_waves"):
        try:
            cur = conn.execute(
                "SELECT wave_id, wave_name, status FROM convergence_waves WHERE status != 'COMPLETE' ORDER BY wave_number LIMIT 5"
            )
            status["pending_waves"] = [{"wave_id": r[0], "name": r[1], "status": r[2]} for r in cur.fetchall()]
        except Exception:
            pass

    total = sum(status["core_tables"].values())
    if total > 500000:
        status["quality_score"] = 90
    elif total > 100000:
        status["quality_score"] = 70
    elif total > 10000:
        status["quality_score"] = 50
    else:
        status["quality_score"] = 30
    status["converged"] = status["quality_score"] >= 80

    return {"ok": True, "convergence": status}


# ══════════════════════════════════════════════════════════════════════════
# SYSTEM & MASTER DATA HANDLERS
# ══════════════════════════════════════════════════════════════════════════


def handle_stats_extended(_req):
    """Extended stats including graphs, rules, risk data, and DB size."""
    conn = pool.sqlite
    stats = {}
    for t in STATS_TABLES:
        stats[t] = _count_table(conn, t)

    for t in ["knowledge_graph", "graph_nodes", "risk_events", "convergence_domains",
              "legal_theories", "bates_registry", "filing_readiness"]:
        if _table_exists(t):
            stats[t] = _count_table(conn, t)

    try:
        stats["db_size_mb"] = round(os.path.getsize(DB_PATH) / (1024 * 1024), 1)
    except OSError:
        stats["db_size_mb"] = None

    return {"ok": True, "stats": stats}


def handle_self_test(_req):
    """Run diagnostic self-tests on the litigation database."""
    conn = pool.sqlite
    tests = []

    try:
        conn.execute("SELECT 1")
        tests.append({"test": "db_connectivity", "status": "PASS"})
    except Exception as e:
        tests.append({"test": "db_connectivity", "status": "FAIL", "error": str(e)})

    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        tests.append({"test": "schema_presence", "status": "PASS", "table_count": len(tables)})
    except Exception as e:
        tests.append({"test": "schema_presence", "status": "FAIL", "error": str(e)})

    if _table_exists("evidence_fts"):
        try:
            conn.execute("SELECT * FROM evidence_fts WHERE evidence_fts MATCH 'test' LIMIT 1")
            tests.append({"test": "fts5_roundtrip", "status": "PASS"})
        except Exception as e:
            tests.append({"test": "fts5_roundtrip", "status": "FAIL", "error": str(e)})
    else:
        tests.append({"test": "fts5_roundtrip", "status": "SKIP", "reason": "evidence_fts not found"})

    for t in ["evidence_quotes", "authority_chains_v2", "timeline_events"]:
        count = _count_table(conn, t)
        tests.append({"test": f"table_{t}", "status": "PASS" if count > 0 else "WARN", "count": count})

    tests.append({
        "test": "duckdb",
        "status": "PASS" if (_HAS_DUCKDB and pool.duck) else "SKIP",
        **({} if (_HAS_DUCKDB and pool.duck) else {"reason": "DuckDB not available"})
    })
    tests.append({
        "test": "lancedb",
        "status": "PASS" if (_HAS_LANCEDB and pool.lance_table) else "SKIP",
        **({} if (_HAS_LANCEDB and pool.lance_table) else {"reason": "LanceDB not available"})
    })

    all_pass = all(t["status"] in ("PASS", "SKIP") for t in tests)
    return {"ok": True, "tests": tests, "all_pass": all_pass}


def handle_ingest_csv(_req):
    """Ingest master CSV datasets. BLOCKED: daemon is read-only."""
    return {"ok": False, "error": "BLOCKED: Daemon is READ-ONLY. Use exec_python with a dedicated CSV ingest script."}


def handle_query_master(req):
    """Search across master CSV data with optional dataset filtering."""
    conn = pool.sqlite
    query = req.get("query", "").strip()
    if not query:
        return {"ok": False, "error": "query required"}

    limit = min(req.get("limit", 20), 100)
    dataset = req.get("dataset")

    for table in ["master_csv_data", "master_data"]:
        if not _table_exists(table):
            continue

        cols_info = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
        col_names = {c[1] for c in cols_info}
        text_col = next((c for c in ["text_content", "content", "text", "data"] if c in col_names), None)
        ds_col = next((c for c in ["dataset_name", "dataset", "source"] if c in col_names), None)

        if not text_col:
            continue

        where = f"{text_col} LIKE ?"
        params = [f"%{query}%"]
        if dataset and ds_col:
            where += f" AND {ds_col} = ?"
            params.append(dataset)
        params.append(limit)

        try:
            cur = conn.execute(f"SELECT * FROM [{table}] WHERE {where} LIMIT ?", params)
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, r)) for r in cur.fetchall()]
            if results:
                return {"ok": True, "results": results, "count": len(results), "source": table}
        except Exception:
            continue

    return {"ok": True, "results": [], "count": 0}
'''


NEW_HANDLERS_DICT = """\
HANDLERS = {
    # Core (existing 24)
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
    # Document management (new)
    "list_documents": handle_list_documents,
    "get_document": handle_get_document,
    "search_documents": handle_search_documents,
    "ingest_pdf": handle_ingest_pdf,
    "bulk_ingest": handle_bulk_ingest,
    # Knowledge graph & rules (new)
    "lookup_rule": handle_lookup_rule,
    "query_graph": handle_query_graph,
    "lookup_authority": handle_lookup_authority,
    # Intelligence (new)
    "assess_risk": handle_assess_risk,
    "get_vehicle_map": handle_get_vehicle_map,
    "case_health": handle_case_health,
    "adversary_threats": handle_adversary_threats,
    "filing_pipeline": handle_filing_pipeline,
    "get_subagent_spec": handle_get_subagent_spec,
    # Evolution pipeline (new)
    "evolution_stats": handle_evolution_stats,
    "search_evolved": handle_search_evolved,
    "cross_refs": handle_cross_refs,
    "convergence_status": handle_convergence_status,
    # System & master data (new)
    "stats_extended": handle_stats_extended,
    "self_test": handle_self_test,
    "ingest_csv": handle_ingest_csv,
    "query_master": handle_query_master,
}"""


NEW_DOCSTRING_ACTIONS = """\
Actions (46):
  # Core
  query / analytics / fts_search / stats / ping
  # Evidence & Search
  search_evidence / search_impeachment / search_contradictions / search_authority
  # NEXUS Intelligence
  nexus_fuse / nexus_argue / nexus_readiness / nexus_damages
  # LEXOS Instant
  narrative / filing_plan / rules_check / adversary / gap_analysis / cross_connect
  # Case Operations
  judicial_intel / timeline_search / case_context / filing_status / deadlines
  # Document Management (NEW)
  list_documents / get_document / search_documents / ingest_pdf / bulk_ingest
  # Knowledge Graph & Rules (NEW)
  lookup_rule / query_graph / lookup_authority
  # Intelligence (NEW)
  assess_risk / get_vehicle_map / case_health / adversary_threats
  filing_pipeline / get_subagent_spec
  # Evolution Pipeline (NEW)
  evolution_stats / search_evolved / cross_refs / convergence_status
  # System & Master Data (NEW)
  stats_extended / self_test / ingest_csv / query_master

Started by extension.mjs on load. Stays alive for entire session."""
