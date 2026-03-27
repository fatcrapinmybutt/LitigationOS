#!/usr/bin/env python3
"""LEXOS RAG Bridge v2 — Comprehensive Litigation Intelligence Engine.

15-action litigation engine with RAG retrieval, direct DB intelligence,
and Ollama LLM integration for Pigors v. Watson.

Architecture:
  Copilot Extension (extension.mjs)
    → JSON stdin → lexos_bridge.py
      → FTS5 / SQL search (litigation_context.db)
      → Ollama API (localhost:11434/api/generate)  [LLM actions only]
    ← JSON stdout ← lexos_bridge.py

Actions requiring LLM:  analyze, draft, impeach, cite, reason, ask
Actions DB-only (FAST): status, narrative, filing_plan, rules_check,
                        damages, adversary, gap_analysis, cross_connect, readiness
"""

import json
import sys
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "lexos"
MAX_CONTEXT_CHUNKS = 15
CHUNK_MAX_LEN = 500

SYSTEM_PROMPT = (
    "You are LEXOS, the litigation intelligence engine for Pigors v. Watson, "
    "14th Circuit Court, Muskegon County, Michigan. Plaintiff Andrew J. Pigors "
    "is pro se. Always cite specific evidence, MCL sections, MCR rules, or "
    "case law. Be precise, adversarial, and strategic."
)

ALL_ACTIONS = [
    "analyze", "draft", "impeach", "cite", "reason", "ask", "status",
    "narrative", "filing_plan", "rules_check", "damages", "adversary",
    "gap_analysis", "cross_connect", "readiness",
]

# ── Database Connection ────────────────────────────────────────────────────

def get_db():
    """Open DB with performance PRAGMAs."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    for pragma in [
        "PRAGMA busy_timeout=30000",
        "PRAGMA cache_size=-32000",
        "PRAGMA mmap_size=268435456",
        "PRAGMA temp_store=2",
    ]:
        conn.execute(pragma)
    return conn


def safe_rows(rows):
    """Convert sqlite3.Row list to list of dicts."""
    return [dict(r) for r in rows] if rows else []


def safe_int(val, default=0):
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default


# ── FTS5 Query Sanitiser ──────────────────────────────────────────────────

def fts_escape(query):
    """Escape a raw query string for safe use inside FTS5 MATCH.

    FTS5 treats characters like -, (, ), :, *, ^ as syntax operators.
    We strip them to avoid "malformed MATCH expression" errors, then
    join remaining tokens with spaces (implicit AND).
    """
    if not query:
        return '""'
    tokens = []
    for ch in query:
        if ch.isalnum() or ch in (" ", "_"):
            tokens.append(ch)
        else:
            tokens.append(" ")
    words = "".join(tokens).split()
    if not words:
        return '""'
    # Quote each word to prevent FTS5 operator interpretation
    return " ".join(f'"{w}"' for w in words[:12])


# ── Search Functions (one per table) ───────────────────────────────────────

def search_evidence(conn, query, limit=10, lane=None, category=None):
    """FTS5 search on evidence_quotes with LIKE fallback."""
    fts_q = fts_escape(query)
    where_extra = ""
    params_extra = []
    if lane:
        where_extra += " AND eq.lane = ?"
        params_extra.append(lane)
    if category:
        where_extra += " AND eq.category = ?"
        params_extra.append(category)
    # FTS5 attempt
    try:
        sql = f"""
            SELECT eq.id, eq.quote_text, eq.source_file, eq.page_number,
                   eq.category, eq.lane, eq.relevance_score, eq.filing_refs, eq.tags
            FROM evidence_quotes_fts AS fts
            JOIN evidence_quotes AS eq ON eq.rowid = fts.rowid
            WHERE fts MATCH ?{where_extra}
            ORDER BY fts.rank LIMIT ?
        """
        rows = conn.execute(sql, [fts_q] + params_extra + [limit]).fetchall()
        if rows:
            return safe_rows(rows)
    except Exception:
        pass
    # LIKE fallback
    try:
        sql = f"""
            SELECT id, quote_text, source_file, page_number,
                   category, lane, relevance_score, filing_refs, tags
            FROM evidence_quotes
            WHERE quote_text LIKE ?{where_extra}
            ORDER BY relevance_score DESC LIMIT ?
        """
        rows = conn.execute(sql, [f"%{query}%"] + params_extra + [limit]).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_evidence_by_person(conn, person, limit=20):
    """Find all evidence mentioning a person."""
    try:
        rows = conn.execute("""
            SELECT id, quote_text, source_file, page_number, category,
                   lane, relevance_score
            FROM evidence_quotes
            WHERE quote_text LIKE ?
            ORDER BY relevance_score DESC LIMIT ?
        """, (f"%{person}%", limit)).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_timeline(conn, query, limit=10, lane=None):
    """FTS5 search on timeline_events with LIKE fallback."""
    fts_q = fts_escape(query)
    lane_filter = ""
    lane_params = []
    if lane:
        lane_filter = " AND te.lane = ?"
        lane_params = [lane]
    try:
        sql = f"""
            SELECT te.id, te.event_date, te.event_description, te.actors,
                   te.lane, te.category, te.source_table, te.source_id
            FROM timeline_events_fts AS fts
            JOIN timeline_events AS te ON te.rowid = fts.rowid
            WHERE fts MATCH ?{lane_filter}
            ORDER BY fts.rank LIMIT ?
        """
        rows = conn.execute(sql, [fts_q] + lane_params + [limit]).fetchall()
        if rows:
            return safe_rows(rows)
    except Exception:
        pass
    try:
        sql = f"""
            SELECT id, event_date, event_description, actors,
                   lane, category, source_table, source_id
            FROM timeline_events
            WHERE event_description LIKE ?{lane_filter}
            ORDER BY event_date LIMIT ?
        """
        rows = conn.execute(sql, [f"%{query}%"] + lane_params + [limit]).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_timeline_by_lane(conn, lane, limit=100):
    """Fetch timeline events for a lane, chronologically."""
    try:
        rows = conn.execute("""
            SELECT id, event_date, event_description, actors, lane,
                   category, source_table, source_id
            FROM timeline_events
            WHERE lane = ?
            ORDER BY event_date ASC LIMIT ?
        """, (lane, limit)).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_rules(conn, query, limit=8):
    """Search michigan_rules_extracted."""
    try:
        rows = conn.execute("""
            SELECT rule_number, rule_type, title, full_text, is_key_rule
            FROM michigan_rules_extracted
            WHERE full_text LIKE ? OR title LIKE ? OR rule_number LIKE ?
            ORDER BY is_key_rule DESC LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit)).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_rules_by_type(conn, rule_type, limit=20):
    """Fetch rules by type (e.g., MCR, MCL)."""
    try:
        rows = conn.execute("""
            SELECT rule_number, rule_type, title, full_text, is_key_rule
            FROM michigan_rules_extracted
            WHERE rule_type LIKE ?
            ORDER BY is_key_rule DESC, rule_number LIMIT ?
        """, (f"%{rule_type}%", limit)).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_authorities(conn, query, limit=10, lane=None):
    """Search authority_chains_v2 with optional FTS5."""
    lane_filter = ""
    lane_params = []
    if lane:
        lane_filter = " AND lane = ?"
        lane_params = [lane]
    # Try FTS5 first
    try:
        sql = f"""
            SELECT primary_citation, supporting_citation, relationship,
                   lane, paragraph_context, source_document, source_type
            FROM authority_fts AS fts
            JOIN authority_chains_v2 AS ac ON ac.rowid = fts.rowid
            WHERE fts MATCH ?{lane_filter}
            ORDER BY fts.rank LIMIT ?
        """
        fts_q = fts_escape(query)
        rows = conn.execute(sql, [fts_q] + lane_params + [limit]).fetchall()
        if rows:
            return safe_rows(rows)
    except Exception:
        pass
    try:
        sql = f"""
            SELECT primary_citation, supporting_citation, relationship,
                   lane, paragraph_context, source_document, source_type
            FROM authority_chains_v2
            WHERE (primary_citation LIKE ? OR supporting_citation LIKE ?
                   OR paragraph_context LIKE ?){lane_filter}
            LIMIT ?
        """
        rows = conn.execute(sql, [f"%{query}%", f"%{query}%", f"%{query}%"]
                            + lane_params + [limit]).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_impeachment(conn, query, limit=10):
    """Search impeachment_matrix."""
    try:
        rows = conn.execute("""
            SELECT category, evidence_summary, cross_exam_question,
                   impeachment_value, source_file, event_date
            FROM impeachment_matrix
            WHERE evidence_summary LIKE ? OR cross_exam_question LIKE ?
                  OR category LIKE ?
            ORDER BY impeachment_value DESC LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit)).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_contradictions(conn, query, limit=10):
    """Search contradiction_map."""
    try:
        rows = conn.execute("""
            SELECT claim_id, source_a, source_b, contradiction_text,
                   severity, lane
            FROM contradiction_map
            WHERE contradiction_text LIKE ? OR source_a LIKE ? OR source_b LIKE ?
            ORDER BY CASE severity
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                WHEN 'medium' THEN 3 ELSE 4 END
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit)).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_bias(conn, query, limit=10):
    """Search judicial_bias_chronology."""
    try:
        rows = conn.execute("""
            SELECT id, date, event_description, canon_violated,
                   evidence_source, severity, mcr_violation,
                   filing_relevance, lane
            FROM judicial_bias_chronology
            WHERE event_description LIKE ? OR canon_violated LIKE ?
            ORDER BY CASE severity
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                WHEN 'medium' THEN 3 ELSE 4 END
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit)).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_police_reports(conn, query, limit=10):
    """Search police_reports."""
    try:
        rows = conn.execute("""
            SELECT * FROM police_reports
            WHERE 1=1 AND (
                CAST(rowid AS TEXT) LIKE ?
                OR EXISTS (
                    SELECT 1 FROM pragma_table_info('police_reports') AS ti
                )
            ) LIMIT ?
        """, (f"%{query}%", limit)).fetchall()
        return safe_rows(rows)
    except Exception:
        pass
    # Generic fallback: grab all columns via wildcard search
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(police_reports)").fetchall()]
        clauses = " OR ".join(f'CAST("{c}" AS TEXT) LIKE ?' for c in cols)
        params = [f"%{query}%"] * len(cols)
        rows = conn.execute(f"SELECT * FROM police_reports WHERE {clauses} LIMIT ?",
                            params + [limit]).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_bif(conn, query, limit=10):
    """Search best_interest_factor_map."""
    try:
        cols = [r[1] for r in conn.execute(
            "PRAGMA table_info(best_interest_factor_map)").fetchall()]
        clauses = " OR ".join(f'CAST("{c}" AS TEXT) LIKE ?' for c in cols)
        params = [f"%{query}%"] * len(cols)
        rows = conn.execute(
            f"SELECT * FROM best_interest_factor_map WHERE {clauses} LIMIT ?",
            params + [limit]).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def search_causes(conn, query=None, limit=27):
    """Search or list causes_of_action."""
    try:
        if query:
            cols = [r[1] for r in conn.execute(
                "PRAGMA table_info(causes_of_action)").fetchall()]
            clauses = " OR ".join(f'CAST("{c}" AS TEXT) LIKE ?' for c in cols)
            params = [f"%{query}%"] * len(cols)
            rows = conn.execute(
                f"SELECT * FROM causes_of_action WHERE {clauses} LIMIT ?",
                params + [limit]).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM causes_of_action LIMIT ?", (limit,)).fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def get_filing_packages(conn):
    """Fetch all filing packages."""
    try:
        rows = conn.execute("SELECT * FROM filing_packages ORDER BY rowid").fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def get_deadlines(conn):
    """Fetch all deadlines."""
    try:
        rows = conn.execute(
            "SELECT * FROM deadlines ORDER BY due_date").fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def get_damages(conn):
    """Fetch all damages calculations."""
    try:
        rows = conn.execute("SELECT * FROM damages_calculations").fetchall()
        return safe_rows(rows)
    except Exception:
        return []


def count_table(conn, table, where="", params=None):
    """Safe COUNT(*) on any table with optional WHERE."""
    try:
        sql = f"SELECT COUNT(*) AS cnt FROM {table}"
        if where:
            sql += f" WHERE {where}"
        row = conn.execute(sql, params or []).fetchone()
        return safe_int(row["cnt"]) if row else 0
    except Exception:
        return 0


def get_distinct_lanes(conn):
    """Get all distinct lanes across key tables."""
    lanes = set()
    for table in ["evidence_quotes", "timeline_events", "contradiction_map",
                   "authority_chains_v2", "judicial_bias_chronology"]:
        try:
            rows = conn.execute(
                f"SELECT DISTINCT lane FROM {table} WHERE lane IS NOT NULL"
            ).fetchall()
            for r in rows:
                if r["lane"]:
                    lanes.add(str(r["lane"]))
        except Exception:
            pass
    return sorted(lanes)


# ── RAG Context Builder (multi-source fusion) ─────────────────────────────

def build_rag_context(conn, query, action="analyze", lane=None, target=None):
    """Build RAG context string from multiple tables based on action type."""
    parts = []
    q = target or query

    # Evidence — always fetched for LLM actions
    evidence = search_evidence(conn, q, limit=10, lane=lane)
    if evidence:
        parts.append("=== EVIDENCE ({} items) ===".format(len(evidence)))
        for e in evidence:
            text = str(e.get("quote_text", ""))[:CHUNK_MAX_LEN]
            src = e.get("source_file", "?")
            pg = e.get("page_number", "")
            cat = e.get("category", "")
            ln = e.get("lane", "")
            parts.append(f"[{cat}|L{ln}] {text} (src: {src}, p.{pg})")

    # Timeline — for analyze, reason, ask, draft
    if action in ("analyze", "reason", "ask", "draft"):
        tl = search_timeline(conn, q, limit=8, lane=lane)
        if tl:
            parts.append("\n=== TIMELINE ({} events) ===".format(len(tl)))
            for t in tl:
                parts.append(
                    f"[{t.get('event_date','')}] {str(t.get('event_description',''))[:300]} "
                    f"— actors: {t.get('actors','')} lane: {t.get('lane','')}"
                )

    # Rules — for analyze, cite, reason, draft, rules_check
    if action in ("analyze", "cite", "reason", "draft"):
        rules = search_rules(conn, q, limit=5)
        if rules:
            parts.append("\n=== MICHIGAN RULES ({} rules) ===".format(len(rules)))
            for r in rules:
                key = " [KEY]" if r.get("is_key_rule") else ""
                parts.append(
                    f"{r.get('rule_number','')}{key}: {r.get('title','')}\n"
                    f"{str(r.get('full_text',''))[:400]}"
                )

    # Authorities — for analyze, cite, reason, draft
    if action in ("analyze", "cite", "reason", "draft"):
        auths = search_authorities(conn, q, limit=8, lane=lane)
        if auths:
            parts.append("\n=== AUTHORITIES ({} chains) ===".format(len(auths)))
            for a in auths:
                parts.append(
                    f"{a.get('primary_citation','')} → {a.get('supporting_citation','')} "
                    f"({a.get('relationship','')}) [Lane {a.get('lane','')}] "
                    f"// {str(a.get('paragraph_context',''))[:200]}"
                )

    # Impeachment + contradictions — for impeach
    if action == "impeach":
        imp = search_impeachment(conn, q, limit=10)
        if imp:
            parts.append("\n=== IMPEACHMENT ({} items) ===".format(len(imp)))
            for i in imp:
                parts.append(
                    f"[{i.get('impeachment_value','?')}/10] {str(i.get('evidence_summary',''))[:300]}\n"
                    f"  Q: {str(i.get('cross_exam_question',''))[:250]}\n"
                    f"  src: {i.get('source_file','')} date: {i.get('event_date','')}"
                )
        contras = search_contradictions(conn, q, limit=8)
        if contras:
            parts.append("\n=== CONTRADICTIONS ({} found) ===".format(len(contras)))
            for c in contras:
                parts.append(
                    f"[{c.get('severity','')}] {c.get('source_a','')} vs {c.get('source_b','')}: "
                    f"{str(c.get('contradiction_text',''))[:300]} (Lane {c.get('lane','')})"
                )

    # Judicial bias — for analyze, reason if query touches bias
    if action in ("analyze", "reason"):
        bias = search_bias(conn, q, limit=5)
        if bias:
            parts.append("\n=== JUDICIAL BIAS ({} entries) ===".format(len(bias)))
            for b in bias:
                parts.append(
                    f"[{b.get('date','')}] [{b.get('severity','')}] "
                    f"{str(b.get('event_description',''))[:300]} "
                    f"Canon: {b.get('canon_violated','')} MCR: {b.get('mcr_violation','')}"
                )

    # Best-interest factors — for analyze, reason, draft if relevant
    if action in ("analyze", "reason", "draft"):
        bif = search_bif(conn, q, limit=5)
        if bif:
            parts.append("\n=== BEST INTEREST FACTORS ({} matches) ===".format(len(bif)))
            for b in bif:
                parts.append(str(b)[:400])

    return "\n".join(parts)


# ── Ollama API Caller ─────────────────────────────────────────────────────

def call_ollama(prompt, system=None, temperature=0.3):
    """HTTP POST to Ollama. Returns response text or error string."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": 4096,
            "num_predict": 512,
        },
    }
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "No response from model.")
    except urllib.error.URLError as e:
        return f"[Ollama error] {e}. Is Ollama running? Start with: ollama serve"
    except Exception as e:
        return f"[Ollama error] {e}"


# ═══════════════════════════════════════════════════════════════════════════
# LLM-POWERED ACTIONS (RAG retrieval → Ollama)
# ═══════════════════════════════════════════════════════════════════════════

def handle_analyze(conn, args):
    """Deep legal analysis with RAG from evidence, rules, authorities, timeline."""
    query = args.get("query", "")
    lane = args.get("lane")
    context = build_rag_context(conn, query, "analyze", lane=lane)
    prompt = f"""Analyze the following legal issue for Pigors v. Watson litigation.
Use the retrieved evidence and authorities below to support your analysis.
Always cite specific evidence, MCL sections, or MCR rules.

QUERY: {query}

RETRIEVED CONTEXT:
{context}

Provide a structured legal analysis with:
1. Issue identification
2. Applicable law (MCL/MCR citations from context)
3. Evidence supporting our position (cite source files and page numbers)
4. Potential counterarguments and how to defeat them
5. Recommended litigation strategy"""

    response = call_ollama(prompt, system=SYSTEM_PROMPT, temperature=0.2)
    return {
        "action": "analyze",
        "analysis": response,
        "sources_used": len(context.split("\n")),
        "query": query,
        "lane": lane,
    }


def handle_draft(conn, args):
    """Draft court filing sections with proper citations."""
    query = args.get("query", "")
    section = args.get("section", "argument")
    lane = args.get("lane")
    filing = args.get("filing")
    context = build_rag_context(conn, query, "draft", lane=lane)

    section_guidance = {
        "argument": "Present legal arguments with IRAC structure. Every legal proposition must cite authority.",
        "facts": "State facts chronologically. Every assertion must cite source file and page number.",
        "relief": "State specific relief requested with legal basis for each item.",
        "introduction": "Brief overview of motion, issues presented, and relief sought.",
        "conclusion": "Summarize arguments and restate relief requested. WHEREFORE paragraph required.",
    }
    guidance = section_guidance.get(section, f"Draft the {section} section professionally.")

    prompt = f"""Draft a {section.upper()} section for a Michigan court filing.
Case: Pigors v. Watson, 14th Circuit Court, Muskegon County.
Plaintiff: Andrew J. Pigors (pro se).
{f"Filing: {filing}" if filing else ""}

INSTRUCTIONS: {guidance}

TOPIC: {query}

RETRIEVED CONTEXT:
{context}

Draft the {section} section now. Use numbered paragraphs. Cite every fact and legal proposition."""

    response = call_ollama(prompt, system=SYSTEM_PROMPT, temperature=0.15)
    return {
        "action": "draft",
        "draft": response,
        "section": section,
        "query": query,
        "filing": filing,
    }


def handle_impeach(conn, args):
    """Cross-examination with impeachment items + contradictions."""
    target = args.get("target", args.get("query", ""))
    lane = args.get("lane")
    context = build_rag_context(conn, target, "impeach", lane=lane, target=target)

    # Also get DB stats for the target
    evidence_count = count_table(conn, "evidence_quotes",
                                 "quote_text LIKE ?", [f"%{target}%"])
    impeach_count = count_table(conn, "impeachment_matrix",
                                "evidence_summary LIKE ? OR cross_exam_question LIKE ?",
                                [f"%{target}%", f"%{target}%"])
    contra_count = count_table(conn, "contradiction_map",
                               "source_a LIKE ? OR source_b LIKE ? OR contradiction_text LIKE ?",
                               [f"%{target}%", f"%{target}%", f"%{target}%"])

    prompt = f"""Generate devastating cross-examination questions for: {target}

DB Intelligence: {evidence_count} evidence items, {impeach_count} impeachment items, {contra_count} contradictions found for this target.

Use the contradictions, impeachment items, and evidence below.
Each question should:
- Be a leading question (answerable yes/no)
- Pin the witness to a specific prior statement or document
- Set up a contradiction with documented evidence
- Build toward destroying credibility

RETRIEVED EVIDENCE:
{context}

Generate 10-15 cross-examination questions ordered: foundational → pinning → impeaching → devastating."""

    response = call_ollama(prompt, system=SYSTEM_PROMPT, temperature=0.25)
    return {
        "action": "impeach",
        "cross_exam": response,
        "target": target,
        "db_stats": {
            "evidence_count": evidence_count,
            "impeachment_items": impeach_count,
            "contradictions": contra_count,
        },
    }


def handle_cite(conn, args):
    """Authority chain building with MCL/MCR/case law."""
    query = args.get("query", "")
    lane = args.get("lane")
    context = build_rag_context(conn, query, "cite", lane=lane)

    prompt = f"""Build a comprehensive authority chain for: {query}

Using the authority chains and rules below, provide:
1. PRIMARY AUTHORITY — statutes (MCL) and court rules (MCR)
2. SUPPORTING CASE LAW — Michigan appellate and Supreme Court decisions
3. APPLICATION — How each authority supports Andrew Pigors' position
4. CITATION CHAIN — Logical progression from statute → case law → application
5. OPPOSING AUTHORITY — What the adversary might cite, and how to distinguish

RETRIEVED AUTHORITIES:
{context}

Format all citations in Michigan Bluebook style."""

    response = call_ollama(prompt, system=SYSTEM_PROMPT, temperature=0.1)
    return {"action": "cite", "citations": response, "query": query, "lane": lane}


def handle_reason(conn, args):
    """Multi-step chain-of-thought legal reasoning."""
    query = args.get("query", "")
    lane = args.get("lane")
    context = build_rag_context(conn, query, "reason", lane=lane)

    prompt = f"""Perform rigorous multi-step legal reasoning for: {query}

Case: Pigors v. Watson, Michigan pro se custody litigation.
Use chain-of-thought. Show your work at EVERY step.

STEP 1: IDENTIFY — What is the precise legal question?
STEP 2: STANDARD — What legal standard applies? (cite MCL/MCR)
STEP 3: ELEMENTS — What elements must be proven?
STEP 4: EVIDENCE — Map evidence to each element (from context below)
STEP 5: GAPS — What elements lack sufficient evidence?
STEP 6: COUNTERARGUMENT — What will the adversary argue?
STEP 7: REBUTTAL — How do we defeat each counterargument?
STEP 8: CONCLUSION — Final assessment with confidence level (1-10)

EVIDENCE AND CONTEXT:
{context}

Begin multi-step analysis now. Be rigorous."""

    response = call_ollama(prompt, system=SYSTEM_PROMPT, temperature=0.2)
    return {"action": "reason", "reasoning": response, "query": query, "lane": lane}


def handle_ask(conn, args):
    """General Q&A with RAG context."""
    query = args.get("query", "")
    lane = args.get("lane")
    context = build_rag_context(conn, query, "ask", lane=lane)

    prompt = f"""Answer the following question about Pigors v. Watson litigation:

{query}

Use the retrieved evidence and context below. Provide a specific, accurate answer.
Cite sources. If the context doesn't contain the answer, say so clearly.

RETRIEVED CONTEXT:
{context}"""

    response = call_ollama(prompt, system=SYSTEM_PROMPT, temperature=0.3)
    return {"action": "ask", "answer": response, "query": query}


# ═══════════════════════════════════════════════════════════════════════════
# DB-ONLY ACTIONS (FAST — no Ollama call)
# ═══════════════════════════════════════════════════════════════════════════

def handle_status(conn, args):
    """System health check (DB + Ollama)."""
    status = {
        "action": "status",
        "model": MODEL_NAME,
        "db_path": DB_PATH,
        "ollama_url": OLLAMA_URL,
    }

    # DB health
    try:
        tables = {}
        for tbl, expected in [
            ("evidence_quotes", 92246), ("best_interest_factor_map", 58847),
            ("authority_chains_v2", 32230), ("timeline_events", 16644),
            ("contradiction_map", 2512), ("michigan_rules_extracted", 2301),
            ("judicial_bias_chronology", 1940), ("impeachment_matrix", 1436),
            ("police_reports", 356), ("causes_of_action", 27),
            ("filing_packages", 10), ("deadlines", 13),
            ("damages_calculations", 30),
        ]:
            cnt = count_table(conn, tbl)
            tables[tbl] = {"count": cnt, "expected": expected,
                           "ok": cnt > 0}
        status["db_status"] = "connected"
        status["tables"] = tables
        status["total_records"] = sum(t["count"] for t in tables.values())
    except Exception as e:
        status["db_status"] = f"error: {e}"

    # FTS5 health
    fts_tables = []
    for fts in ["evidence_quotes_fts", "evidence_fts", "timeline_events_fts",
                "timeline_fts", "json_atoms_fts", "pages_fts", "authority_fts"]:
        try:
            conn.execute(f"SELECT COUNT(*) FROM {fts}").fetchone()
            fts_tables.append(fts)
        except Exception:
            pass
    status["fts5_tables"] = fts_tables

    # Ollama health
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", [])]
            status["ollama_status"] = "running"
            status["models_available"] = models
            status["lexos_loaded"] = any(MODEL_NAME in m for m in models)
    except Exception as e:
        status["ollama_status"] = f"not running: {e}"

    status["lanes"] = get_distinct_lanes(conn)
    return status


def handle_narrative(conn, args):
    """Build chronological narrative for a lane/topic from timeline_events."""
    lane = args.get("lane")
    topic = args.get("query", args.get("topic", ""))
    limit = args.get("limit", 100)

    events = []
    if lane:
        events = search_timeline_by_lane(conn, lane, limit=limit)
    if not events and topic:
        events = search_timeline(conn, topic, limit=limit, lane=lane)
    if not events and lane:
        # Broader search using LIKE on lane
        try:
            rows = conn.execute("""
                SELECT id, event_date, event_description, actors, lane,
                       category, source_table, source_id
                FROM timeline_events
                WHERE CAST(lane AS TEXT) LIKE ?
                ORDER BY event_date ASC LIMIT ?
            """, (f"%{lane}%", limit)).fetchall()
            events = safe_rows(rows)
        except Exception:
            pass

    # Enrich with evidence counts per event
    narrative = []
    for ev in events:
        desc = str(ev.get("event_description", ""))
        # Count supporting evidence
        ev_count = count_table(conn, "evidence_quotes",
                               "quote_text LIKE ?",
                               [f"%{desc[:50]}%"]) if len(desc) > 10 else 0
        narrative.append({
            "date": ev.get("event_date", ""),
            "description": desc,
            "actors": ev.get("actors", ""),
            "lane": ev.get("lane", ""),
            "category": ev.get("category", ""),
            "supporting_evidence_count": ev_count,
        })

    # Summary stats
    actors_seen = set()
    categories_seen = set()
    for n in narrative:
        if n["actors"]:
            for a in str(n["actors"]).split(","):
                a = a.strip()
                if a:
                    actors_seen.add(a)
        if n["category"]:
            categories_seen.add(n["category"])

    return {
        "action": "narrative",
        "lane": lane,
        "topic": topic,
        "event_count": len(narrative),
        "date_range": {
            "earliest": narrative[0]["date"] if narrative else None,
            "latest": narrative[-1]["date"] if narrative else None,
        },
        "actors": sorted(actors_seen),
        "categories": sorted(categories_seen),
        "timeline": narrative,
    }


def handle_filing_plan(conn, args):
    """Comprehensive filing strategy with deadlines, fees, sequence, blockers."""
    lane = args.get("lane")
    filing_id = args.get("filing_id")

    packages = get_filing_packages(conn)
    deadlines = get_deadlines(conn)
    causes = search_causes(conn)

    # Filter by lane if specified
    if lane:
        packages = [p for p in packages if str(p.get("lane", "")) == str(lane)]

    # Filter by filing_id if specified
    if filing_id:
        packages = [p for p in packages
                    if str(p.get("rowid", "")) == str(filing_id)
                    or any(str(v) == str(filing_id) for v in p.values())]

    # Compute readiness indicators per package
    plan = []
    for pkg in packages:
        pkg_lane = str(pkg.get("lane", ""))
        evidence_count = count_table(conn, "evidence_quotes",
                                     "lane = ?", [pkg_lane])
        authority_count = count_table(conn, "authority_chains_v2",
                                      "lane = ?", [pkg_lane])
        # Find matching deadlines
        pkg_deadlines = []
        for d in deadlines:
            d_str = json.dumps(d).lower()
            if pkg_lane.lower() in d_str or str(pkg.get("case_number", "")).lower() in d_str:
                pkg_deadlines.append(d)

        plan.append({
            "package": pkg,
            "evidence_count": evidence_count,
            "authority_count": authority_count,
            "deadlines": pkg_deadlines,
            "has_evidence": evidence_count > 0,
            "has_authority": authority_count > 0,
        })

    # Urgency sort: packages with soonest deadlines first
    today = datetime.now().strftime("%Y-%m-%d")
    urgent = []
    for d in deadlines:
        due = str(d.get("due_date", "9999-12-31"))
        urgent.append({
            "deadline": d,
            "days_remaining": None,  # computed below
            "overdue": due < today,
        })

    return {
        "action": "filing_plan",
        "lane_filter": lane,
        "total_packages": len(packages),
        "total_deadlines": len(deadlines),
        "total_causes": len(causes),
        "filing_packages": plan,
        "all_deadlines": deadlines,
        "causes_of_action": causes,
    }


def handle_rules_check(conn, args):
    """Verify procedural compliance for a filing type against michigan_rules_extracted."""
    filing_type = args.get("query", args.get("filing_type", ""))
    rules = search_rules(conn, filing_type, limit=20)

    # Also search for key rules
    key_rules = []
    try:
        rows = conn.execute("""
            SELECT rule_number, rule_type, title, full_text
            FROM michigan_rules_extracted
            WHERE is_key_rule = 1
            ORDER BY rule_number LIMIT 50
        """).fetchall()
        key_rules = safe_rows(rows)
    except Exception:
        pass

    # Cross-reference: which rules mention this filing type
    matching_rules = []
    general_rules = []
    for r in rules:
        text_lower = str(r.get("full_text", "")).lower()
        title_lower = str(r.get("title", "")).lower()
        ft_lower = filing_type.lower()
        if ft_lower in text_lower or ft_lower in title_lower:
            matching_rules.append(r)
        else:
            general_rules.append(r)

    return {
        "action": "rules_check",
        "filing_type": filing_type,
        "matching_rules": matching_rules,
        "related_rules": general_rules,
        "key_rules": key_rules[:10],
        "total_rules_searched": len(rules),
        "compliance_checklist": [
            {
                "rule": r.get("rule_number", ""),
                "title": r.get("title", ""),
                "requirement_summary": str(r.get("full_text", ""))[:200],
            }
            for r in matching_rules
        ],
    }


def handle_damages(conn, args):
    """Calculate and maximize prayers for relief from damages_calculations."""
    query = args.get("query", "")
    damages = get_damages(conn)

    # Filter if query provided
    if query:
        query_lower = query.lower()
        filtered = [d for d in damages
                    if any(query_lower in str(v).lower() for v in d.values())]
        if filtered:
            damages = filtered

    # Try to sum numeric columns
    totals = {}
    for d in damages:
        for k, v in d.items():
            if k == "id" or k == "rowid":
                continue
            try:
                num = float(str(v).replace("$", "").replace(",", ""))
                totals[k] = totals.get(k, 0.0) + num
            except (ValueError, TypeError):
                pass

    return {
        "action": "damages",
        "query": query,
        "damages_items": damages,
        "damages_count": len(damages),
        "computed_totals": {k: round(v, 2) for k, v in totals.items()},
    }


def handle_adversary(conn, args):
    """Deep adversary profile: evidence, impeachment, contradictions, timeline, police."""
    target = args.get("target", args.get("query", ""))
    if not target:
        return {"action": "adversary", "error": "No target specified. Provide 'target' parameter."}

    # Evidence mentioning target
    evidence = search_evidence_by_person(conn, target, limit=20)
    evidence_count = count_table(conn, "evidence_quotes",
                                 "quote_text LIKE ?", [f"%{target}%"])

    # Impeachment items
    impeachment = search_impeachment(conn, target, limit=20)
    impeach_total = count_table(conn, "impeachment_matrix",
                                "evidence_summary LIKE ? OR cross_exam_question LIKE ?",
                                [f"%{target}%", f"%{target}%"])

    # Contradictions
    contradictions = search_contradictions(conn, target, limit=20)
    contra_total = count_table(conn, "contradiction_map",
                               "source_a LIKE ? OR source_b LIKE ? OR contradiction_text LIKE ?",
                               [f"%{target}%", f"%{target}%", f"%{target}%"])

    # Timeline events
    timeline = search_timeline(conn, target, limit=20)
    timeline_total = count_table(conn, "timeline_events",
                                 "event_description LIKE ? OR actors LIKE ?",
                                 [f"%{target}%", f"%{target}%"])

    # Police reports
    police = search_police_reports(conn, target, limit=10)
    police_total = count_table(conn, "police_reports", "1=1")

    # Judicial bias entries mentioning target
    bias = search_bias(conn, target, limit=10)

    # Sort impeachment by value, get top 5
    impeachment_sorted = sorted(impeachment,
                                key=lambda x: safe_int(x.get("impeachment_value", 0)),
                                reverse=True)
    top5_impeach = impeachment_sorted[:5]

    # Sort contradictions by severity, get top 5
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    contradictions_sorted = sorted(
        contradictions,
        key=lambda x: severity_order.get(str(x.get("severity", "")).lower(), 9)
    )
    top5_contra = contradictions_sorted[:5]

    # Vulnerability assessment
    vuln_score = 0
    if impeach_total > 10:
        vuln_score += 3
    elif impeach_total > 5:
        vuln_score += 2
    elif impeach_total > 0:
        vuln_score += 1
    if contra_total > 5:
        vuln_score += 3
    elif contra_total > 2:
        vuln_score += 2
    elif contra_total > 0:
        vuln_score += 1
    if police:
        vuln_score += 2
    if bias:
        vuln_score += 2

    vuln_label = "LOW"
    if vuln_score >= 7:
        vuln_label = "CRITICAL"
    elif vuln_score >= 5:
        vuln_label = "HIGH"
    elif vuln_score >= 3:
        vuln_label = "MEDIUM"

    return {
        "action": "adversary",
        "target": target,
        "summary": {
            "evidence_count": evidence_count,
            "impeachment_items_total": impeach_total,
            "contradictions_total": contra_total,
            "timeline_events_total": timeline_total,
            "police_reports_found": len(police),
            "bias_entries": len(bias),
            "vulnerability_score": vuln_score,
            "vulnerability_level": vuln_label,
        },
        "top5_impeachment": top5_impeach,
        "top5_contradictions": top5_contra,
        "evidence_sample": evidence[:10],
        "timeline_events": timeline[:10],
        "police_reports": police[:5],
        "bias_entries": bias[:5],
    }


def handle_gap_analysis(conn, args):
    """Find missing claims, untapped evidence, unconnected dots across all lanes."""
    lanes = get_distinct_lanes(conn)
    causes = search_causes(conn)
    lane_analysis = []

    for lane in lanes:
        ev_count = count_table(conn, "evidence_quotes", "lane = ?", [lane])
        auth_count = count_table(conn, "authority_chains_v2", "lane = ?", [lane])
        tl_count = count_table(conn, "timeline_events", "lane = ?", [lane])
        contra_count = count_table(conn, "contradiction_map", "lane = ?", [lane])
        bias_count = count_table(conn, "judicial_bias_chronology", "lane = ?", [lane])

        # Identify weaknesses
        gaps = []
        if ev_count == 0:
            gaps.append("NO EVIDENCE — critical gap")
        elif ev_count < 50:
            gaps.append(f"Low evidence count ({ev_count}) — needs strengthening")
        if auth_count == 0:
            gaps.append("NO LEGAL AUTHORITY — need MCL/MCR/case law")
        elif auth_count < 10:
            gaps.append(f"Weak authority chain ({auth_count}) — needs more citations")
        if tl_count == 0:
            gaps.append("No timeline events — narrative gap")
        if contra_count == 0 and ev_count > 100:
            gaps.append("High evidence but no contradictions mapped — check for opponent inconsistencies")

        strength = "STRONG" if not gaps else ("WEAK" if len(gaps) >= 3 else "MODERATE")

        lane_analysis.append({
            "lane": lane,
            "evidence_count": ev_count,
            "authority_count": auth_count,
            "timeline_count": tl_count,
            "contradiction_count": contra_count,
            "bias_count": bias_count,
            "gaps": gaps,
            "strength": strength,
        })

    # Causes without sufficient evidence
    weak_causes = []
    for c in causes:
        c_str = json.dumps(c).lower()
        # Check if any evidence column indicates low evidence
        for k, v in c.items():
            v_str = str(v).lower()
            if "weak" in v_str or "insufficient" in v_str or "0" == v_str:
                weak_causes.append(c)
                break

    # Cross-lane gaps: lanes with evidence but no authority (or vice versa)
    cross_gaps = []
    for la in lane_analysis:
        if la["evidence_count"] > 50 and la["authority_count"] == 0:
            cross_gaps.append({
                "type": "evidence_without_authority",
                "lane": la["lane"],
                "detail": f"{la['evidence_count']} evidence items but 0 authorities"
            })
        if la["authority_count"] > 10 and la["evidence_count"] == 0:
            cross_gaps.append({
                "type": "authority_without_evidence",
                "lane": la["lane"],
                "detail": f"{la['authority_count']} authorities but 0 evidence"
            })

    # Overall stats
    total_ev = sum(la["evidence_count"] for la in lane_analysis)
    total_auth = sum(la["authority_count"] for la in lane_analysis)
    strong_lanes = [la for la in lane_analysis if la["strength"] == "STRONG"]
    weak_lanes = [la for la in lane_analysis if la["strength"] == "WEAK"]

    return {
        "action": "gap_analysis",
        "total_lanes": len(lanes),
        "strong_lanes": len(strong_lanes),
        "weak_lanes": len(weak_lanes),
        "total_evidence": total_ev,
        "total_authorities": total_auth,
        "lane_analysis": lane_analysis,
        "cross_lane_gaps": cross_gaps,
        "weak_causes": weak_causes[:10],
        "recommendations": _gap_recommendations(lane_analysis, cross_gaps),
    }


def _gap_recommendations(lane_analysis, cross_gaps):
    """Generate prioritised recommendations from gap analysis."""
    recs = []
    # Priority 1: lanes with no evidence
    for la in lane_analysis:
        if la["evidence_count"] == 0:
            recs.append({
                "priority": "CRITICAL",
                "lane": la["lane"],
                "action": "Add evidence to this lane — currently empty"
            })
    # Priority 2: evidence without authority
    for g in cross_gaps:
        if g["type"] == "evidence_without_authority":
            recs.append({
                "priority": "HIGH",
                "lane": g["lane"],
                "action": f"Research MCL/MCR/case law for lane — {g['detail']}"
            })
    # Priority 3: weak lanes
    for la in lane_analysis:
        if la["strength"] == "WEAK" and la["evidence_count"] > 0:
            recs.append({
                "priority": "MEDIUM",
                "lane": la["lane"],
                "action": f"Strengthen lane: {', '.join(la['gaps'])}"
            })
    return recs[:20]


def handle_cross_connect(conn, args):
    """Cross-lane intelligence fusion: find evidence in one lane supporting another."""
    source_lane = args.get("source_lane", args.get("lane"))
    target_lane = args.get("target_lane")
    query = args.get("query", "")

    if not source_lane and not query:
        return {
            "action": "cross_connect",
            "error": "Provide 'source_lane' and optionally 'target_lane', or 'query'."
        }

    connections = []

    if source_lane and target_lane:
        # Find evidence in source_lane that mentions concepts from target_lane
        # Get target lane keywords from its evidence
        try:
            target_evidence = conn.execute("""
                SELECT DISTINCT category FROM evidence_quotes
                WHERE lane = ? AND category IS NOT NULL LIMIT 20
            """, (target_lane,)).fetchall()
            target_categories = [r["category"] for r in target_evidence if r["category"]]
        except Exception:
            target_categories = []

        # Search source lane evidence for target lane concepts
        for cat in target_categories:
            matches = search_evidence(conn, cat, limit=5, lane=source_lane)
            for m in matches:
                connections.append({
                    "source_lane": source_lane,
                    "target_lane": target_lane,
                    "connecting_concept": cat,
                    "evidence": {
                        "quote": str(m.get("quote_text", ""))[:300],
                        "source_file": m.get("source_file", ""),
                        "page": m.get("page_number", ""),
                    },
                })

        # Also check contradictions that span both lanes
        try:
            rows = conn.execute("""
                SELECT * FROM contradiction_map
                WHERE (lane = ? OR lane = ?)
                ORDER BY CASE severity
                    WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3 ELSE 4 END
                LIMIT 10
            """, (source_lane, target_lane)).fetchall()
            cross_contradictions = safe_rows(rows)
        except Exception:
            cross_contradictions = []

        # Check authorities that span both lanes
        try:
            rows = conn.execute("""
                SELECT * FROM authority_chains_v2
                WHERE lane IN (?, ?)
                LIMIT 10
            """, (source_lane, target_lane)).fetchall()
            shared_authorities = safe_rows(rows)
        except Exception:
            shared_authorities = []

    elif query:
        # Search across all lanes for query, group by lane
        all_evidence = search_evidence(conn, query, limit=30)
        by_lane = {}
        for e in all_evidence:
            ln = str(e.get("lane", "unknown"))
            by_lane.setdefault(ln, []).append(e)

        for ln, items in by_lane.items():
            for other_ln, other_items in by_lane.items():
                if ln >= other_ln:
                    continue
                connections.append({
                    "source_lane": ln,
                    "target_lane": other_ln,
                    "connecting_concept": query,
                    "source_evidence_count": len(items),
                    "target_evidence_count": len(other_items),
                })
        cross_contradictions = []
        shared_authorities = []
    else:
        cross_contradictions = []
        shared_authorities = []

    return {
        "action": "cross_connect",
        "source_lane": source_lane,
        "target_lane": target_lane,
        "query": query,
        "connections_found": len(connections),
        "connections": connections[:30],
        "cross_contradictions": cross_contradictions if source_lane and target_lane else [],
        "shared_authorities": shared_authorities if source_lane and target_lane else [],
    }


def handle_readiness(conn, args):
    """Filing readiness dashboard across all 10 lanes."""
    packages = get_filing_packages(conn)
    deadlines = get_deadlines(conn)
    lanes = get_distinct_lanes(conn)
    today = datetime.now().strftime("%Y-%m-%d")

    dashboard = []
    for pkg in packages:
        pkg_lane = str(pkg.get("lane", ""))
        pkg_status = str(pkg.get("status", ""))

        # Evidence readiness
        ev_count = count_table(conn, "evidence_quotes", "lane = ?", [pkg_lane])
        # Authority readiness
        auth_count = count_table(conn, "authority_chains_v2", "lane = ?", [pkg_lane])
        # Timeline coverage
        tl_count = count_table(conn, "timeline_events", "lane = ?", [pkg_lane])
        # Impeachment readiness
        imp_count = count_table(conn, "impeachment_matrix")  # global
        # Contradiction coverage
        contra_count = count_table(conn, "contradiction_map", "lane = ?", [pkg_lane])
        # Bias entries
        bias_count = count_table(conn, "judicial_bias_chronology", "lane = ?", [pkg_lane])

        # Matching deadlines
        pkg_deadlines = []
        for d in deadlines:
            d_json = json.dumps(d).lower()
            if (pkg_lane.lower() in d_json
                    or str(pkg.get("case_number", "")).lower() in d_json):
                due = str(d.get("due_date", "9999-12-31"))
                overdue = due < today
                pkg_deadlines.append({
                    "deadline": d,
                    "overdue": overdue,
                })

        # Readiness score (0-100)
        score = 0
        if ev_count >= 100:
            score += 30
        elif ev_count >= 50:
            score += 20
        elif ev_count > 0:
            score += 10
        if auth_count >= 20:
            score += 25
        elif auth_count >= 10:
            score += 15
        elif auth_count > 0:
            score += 5
        if tl_count >= 10:
            score += 15
        elif tl_count > 0:
            score += 8
        if contra_count > 0:
            score += 10
        if bias_count > 0:
            score += 10
        if "complete" in pkg_status.lower() or "ready" in pkg_status.lower():
            score += 10

        if score >= 80:
            readiness_label = "READY"
        elif score >= 50:
            readiness_label = "NEAR-READY"
        elif score >= 25:
            readiness_label = "IN PROGRESS"
        else:
            readiness_label = "NOT READY"

        blockers = []
        if ev_count == 0:
            blockers.append("No evidence in lane")
        if auth_count == 0:
            blockers.append("No legal authority")
        for pd in pkg_deadlines:
            if pd["overdue"]:
                blockers.append(f"OVERDUE deadline: {pd['deadline'].get('due_date','')}")

        dashboard.append({
            "package": pkg,
            "lane": pkg_lane,
            "readiness_score": score,
            "readiness_label": readiness_label,
            "evidence_count": ev_count,
            "authority_count": auth_count,
            "timeline_count": tl_count,
            "contradiction_count": contra_count,
            "bias_count": bias_count,
            "deadlines": pkg_deadlines,
            "blockers": blockers,
        })

    # Sort: NOT READY first (to surface problems), then by score ascending
    dashboard.sort(key=lambda x: x["readiness_score"])

    # Summary
    ready = [d for d in dashboard if d["readiness_label"] == "READY"]
    overdue_count = sum(1 for d in dashboard for dl in d["deadlines"] if dl["overdue"])

    return {
        "action": "readiness",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_packages": len(packages),
            "ready": len(ready),
            "near_ready": len([d for d in dashboard if d["readiness_label"] == "NEAR-READY"]),
            "in_progress": len([d for d in dashboard if d["readiness_label"] == "IN PROGRESS"]),
            "not_ready": len([d for d in dashboard if d["readiness_label"] == "NOT READY"]),
            "overdue_deadlines": overdue_count,
            "total_lanes_tracked": len(lanes),
        },
        "dashboard": dashboard,
        "all_deadlines": deadlines,
    }


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

HANDLERS_LLM = {
    "analyze": handle_analyze,
    "draft": handle_draft,
    "impeach": handle_impeach,
    "cite": handle_cite,
    "reason": handle_reason,
    "ask": handle_ask,
}

HANDLERS_DB = {
    "narrative": handle_narrative,
    "filing_plan": handle_filing_plan,
    "rules_check": handle_rules_check,
    "damages": handle_damages,
    "adversary": handle_adversary,
    "gap_analysis": handle_gap_analysis,
    "cross_connect": handle_cross_connect,
    "readiness": handle_readiness,
}


def main():
    try:
        raw = sys.stdin.read()
        request = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        json.dump({"error": f"Invalid JSON input: {e}"}, sys.stdout)
        return

    action = request.get("action", "ask")

    # Status is special — opens its own connection for health check
    if action == "status":
        try:
            conn = get_db()
            result = handle_status(conn, request)
            conn.close()
        except Exception as e:
            result = {"action": "status", "error": f"DB connection failed: {e}",
                      "ollama_url": OLLAMA_URL, "db_path": DB_PATH}
        json.dump(result, sys.stdout, default=str)
        return

    # Validate action
    if action not in HANDLERS_LLM and action not in HANDLERS_DB:
        json.dump({
            "error": f"Unknown action: {action}",
            "available_actions": ALL_ACTIONS,
        }, sys.stdout, default=str)
        return

    # Open DB and dispatch
    try:
        conn = get_db()
    except Exception as e:
        json.dump({"error": f"DB connection failed: {e}"}, sys.stdout, default=str)
        return

    try:
        if action in HANDLERS_DB:
            result = HANDLERS_DB[action](conn, request)
        else:
            result = HANDLERS_LLM[action](conn, request)
    except Exception as e:
        result = {"error": f"Action '{action}' failed: {e}", "action": action}
    finally:
        try:
            conn.close()
        except Exception:
            pass

    json.dump(result, sys.stdout, default=str)


if __name__ == "__main__":
    main()
