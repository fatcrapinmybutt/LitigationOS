#!/usr/bin/env python3
"""
MCP Server for Litigation Context — permanent PDF knowledge base + legal knowledge graphs.

Scans local drives for PDF files, extracts text via PyMuPDF,
stores permanently in SQLite with FTS5 full-text search.
Integrates Michigan court rules, authority graphs, and risk event taxonomies.
"""

import json
import logging
import sqlite3
import sys
import time
import traceback
from contextlib import asynccontextmanager
from enum import Enum
from typing import Optional, List

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field, ConfigDict, field_validator

from . import db, pdf_extractor

logger = logging.getLogger("litigation_context_mcp")


# ── Lifespan: load knowledge graphs at startup ────────────────────
@asynccontextmanager
async def app_lifespan(server):
    """Initialize DB and load knowledge graphs on server start."""
    db.health.startup_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    conn = None
    try:
        conn = db.get_connection()
        logger.info("Loading knowledge graphs into database...")
        graph_results = db.load_all_knowledge_graphs(conn)
        logger.info("Knowledge graphs loaded: %s", graph_results)
        db.health.graphs_loaded = True
    except Exception as e:
        logger.error("Non-fatal: knowledge graph loading failed: %s", e)
        db.health.graph_errors.append(str(e))
        db.health.degraded = True
    finally:
        if conn:
            conn.close()
    yield {"health": db.health.status}


# ── Server ────────────────────────────────────────────────────────
mcp = FastMCP("litigation_context_mcp", lifespan=app_lifespan)


# ── Shared Error Helpers ──────────────────────────────────────────
def _format_error(e: Exception, context: str = "") -> str:
    """Consistent structured error formatting for all tools.

    Maps exception types to ErrorCodes, records telemetry, and returns
    actionable error messages with recovery hints.
    """
    prefix = f"[{context}] " if context else ""

    # Map to structured error code
    code: Optional[db.ErrorCode] = None
    if isinstance(e, db.StructuredError):
        code = e.code
        msg = f"**{prefix}Error** `{e.code.value}`: {e.message}\n\n💡 **Recovery**: {e.hint}"
    elif isinstance(e, db.DatabaseError):
        code = db.ErrorCode.ERR_DB_CONNECT
        msg = f"**{prefix}Database Error**: {e}\n\n💡 **Recovery**: {db._RECOVERY_HINTS[code]}"
    elif isinstance(e, ValueError):
        msg = f"**{prefix}Validation Error**: {e}"
    elif isinstance(e, FileNotFoundError):
        msg = f"**{prefix}File Not Found**: {e}"
    elif isinstance(e, PermissionError):
        code = db.ErrorCode.ERR_PDF_PERMISSION
        msg = f"**{prefix}Permission Denied**: {e}\n\n💡 **Recovery**: {db._RECOVERY_HINTS[code]}"
    elif isinstance(e, TimeoutError):
        code = db.ErrorCode.ERR_PDF_TIMEOUT
        msg = f"**{prefix}Timeout**: {e}\n\n💡 **Recovery**: {db._RECOVERY_HINTS[code]}"
    elif isinstance(e, json.JSONDecodeError):
        msg = f"**{prefix}Invalid JSON**: {e}"
    elif isinstance(e, sqlite3.OperationalError):
        err_msg = str(e).lower()
        if "fts5" in err_msg or "syntax" in err_msg or "parse" in err_msg:
            code = db.ErrorCode.ERR_FTS_SYNTAX
            msg = f"**{prefix}FTS5 Query Error**: {e}\n\n💡 **Recovery**: {db._RECOVERY_HINTS[code]}"
        elif "locked" in err_msg:
            code = db.ErrorCode.ERR_DB_LOCKED
            msg = f"**{prefix}Database Locked**: {e}\n\n💡 **Recovery**: {db._RECOVERY_HINTS[code]}"
        else:
            msg = f"**{prefix}Database Error**: {e}"
    else:
        tb = traceback.format_exc()
        logger.error("Unexpected error in %s: %s\n%s", context, e, tb)
        msg = f"**{prefix}Unexpected Error** `{type(e).__name__}`: {e}"

    # Record telemetry (best-effort, never crashes)
    if code:
        try:
            conn = db.get_connection()
            db.record_error(conn, code, context, str(e), traceback.format_exc())
            conn.close()
        except Exception:
            pass

    return msg


def _safe_conn():
    """Get DB connection with structured error wrapping and disk space guard."""
    db.check_disk_space(min_mb=50)
    try:
        return db.get_connection()
    except db.StructuredError:
        raise
    except db.DatabaseError as e:
        raise db.StructuredError(db.ErrorCode.ERR_DB_CONNECT, str(e), e) from e


# ── Enums & Models ───────────────────────────────────────────────
class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class ScanDrivesInput(BaseModel):
    """Input for scanning drives/folders for PDF files."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    path: Optional[str] = Field(
        default=None,
        description="Directory to scan. If omitted, scans all available drives.",
    )
    max_results: int = Field(
        default=500, ge=1, le=10000,
        description="Maximum number of PDF files to return.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class IngestPdfInput(BaseModel):
    """Input for ingesting a single PDF."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    file_path: str = Field(
        ..., min_length=3,
        description="Absolute path to the PDF file to ingest (e.g. 'C:\\Users\\andre\\Scans\\document.pdf').",
    )

    @field_validator("file_path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v.lower().endswith(".pdf"):
            raise ValueError("Path must end with .pdf")
        return v


class BulkIngestInput(BaseModel):
    """Input for bulk-ingesting PDFs from a directory."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    path: str = Field(
        ..., min_length=1,
        description="Directory to scan and ingest all PDFs from.",
    )
    max_files: int = Field(
        default=200, ge=1, le=5000,
        description="Maximum number of files to ingest in this batch.",
    )
    skip_existing: bool = Field(
        default=True,
        description="Skip PDFs already in the database (matched by file path).",
    )


class SearchInput(BaseModel):
    """Input for full-text search."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ..., min_length=1, max_length=500,
        description="FTS5 search query. Supports AND, OR, NOT, phrases (\"...\"), prefix*. Example: 'ex parte AND McNeill'.",
    )
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class ListDocumentsInput(BaseModel):
    """Input for listing indexed documents."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    name_filter: Optional[str] = Field(
        default=None,
        description="Filter documents by file name (partial match).",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class GetDocumentInput(BaseModel):
    """Input for retrieving a specific document."""
    model_config = ConfigDict(extra="forbid")

    document_id: int = Field(..., ge=1, description="Document ID from the database.")
    page_numbers: Optional[List[int]] = Field(
        default=None,
        description="Specific page numbers to retrieve. Omit for all pages.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class DeleteDocumentInput(BaseModel):
    """Input for deleting a document."""
    model_config = ConfigDict(extra="forbid")
    document_id: int = Field(..., ge=1, description="Document ID to delete.")


class StatsInput(BaseModel):
    """Input for knowledge base statistics."""
    model_config = ConfigDict(extra="forbid")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class LookupRuleInput(BaseModel):
    """Input for looking up Michigan Court Rules."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ..., min_length=1, max_length=200,
        description="Rule citation (e.g. 'MCR 3.706') or keyword to search in rule text.",
    )
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class QueryGraphInput(BaseModel):
    """Input for querying the knowledge graph."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ..., min_length=1, max_length=300,
        description="Search term to match against node labels and IDs (e.g. 'PPO', 'custody', 'MCL 600.2950').",
    )
    node_type: Optional[str] = Field(
        default=None,
        description="Filter by node type (e.g. 'authority', 'CASELAW', 'FORM', 'PROCEDURE').",
    )
    graph_source: Optional[str] = Field(
        default=None,
        description="Filter by graph source (e.g. 'court_forms_graph', 'authority_forms_graph', 'master_graph').",
    )
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class AssessRiskInput(BaseModel):
    """Input for litigation risk assessment."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    severity_min: int = Field(
        default=0, ge=0, le=100,
        description="Minimum severity threshold (0-100). Higher = only critical risks.",
    )
    risk_class: Optional[str] = Field(
        default=None,
        description="Filter by risk class (e.g. 'record_incomplete', 'curable_defect').",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class SelfTestInput(BaseModel):
    """Input for self-test diagnostics."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class SelfAuditInput(BaseModel):
    """Input for data-quality self-audit."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class ConvergenceInput(BaseModel):
    """Input for convergence status check."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


# ══════════════════════════════════════════════════════════════════
#  TOOLS — PDF Knowledge Base (8 original, upgraded)
# ══════════════════════════════════════════════════════════════════

@mcp.tool(
    name="litigation_scan_drives",
    annotations={
        "title": "Scan Drives for PDFs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_scan_drives(params: ScanDrivesInput, ctx: Context) -> str:
    """Scan local drives or a specific folder for PDF files without ingesting them.

    Returns a list of discovered PDF files with their paths, sizes, and dates.
    Use this to preview what's available before ingesting.
    """
    try:
        paths_to_scan: List[str] = []
        if params.path:
            paths_to_scan = [params.path]
        else:
            paths_to_scan = pdf_extractor.get_available_drives()

        await ctx.report_progress(0.1, f"Scanning {len(paths_to_scan)} location(s)...")
        all_pdfs: list = []
        for scan_path in paths_to_scan:
            try:
                for pdf_info in pdf_extractor.scan_for_pdfs(scan_path, params.max_results - len(all_pdfs)):
                    all_pdfs.append(pdf_info)
                    if len(all_pdfs) >= params.max_results:
                        break
            except PermissionError:
                logger.warning("Permission denied scanning: %s", scan_path)
                continue
            if len(all_pdfs) >= params.max_results:
                break

        await ctx.report_progress(1.0, "Scan complete.")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"count": len(all_pdfs), "pdfs": all_pdfs}, indent=2, default=str)

        lines = ["# PDF Scan Results", f"Found **{len(all_pdfs)}** PDF files\n"]
        for pdf in all_pdfs[:100]:
            size_mb = round(pdf["file_size_bytes"] / (1024 * 1024), 2)
            lines.append(f"- `{pdf['file_path']}` ({size_mb} MB)")
        if len(all_pdfs) > 100:
            lines.append(f"\n... and {len(all_pdfs) - 100} more. Use JSON format for full list.")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "scan_drives")


@mcp.tool(
    name="litigation_ingest_pdf",
    annotations={
        "title": "Ingest Single PDF",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_ingest_pdf(params: IngestPdfInput, ctx: Context) -> str:
    """Extract text from a single PDF file and store it permanently in the knowledge base.

    Extracts text page-by-page using PyMuPDF with per-page error resilience.
    Skips if the exact file path is already indexed. Deduplicates by content hash.
    """
    conn = None
    try:
        conn = _safe_conn()
        if db.document_exists(conn, params.file_path):
            return f"Already indexed: `{params.file_path}`. Use litigation_delete_document first to re-ingest."

        await ctx.report_progress(0.2, "Extracting text...")
        data = pdf_extractor.extract_pdf_text(params.file_path)

        existing = db.hash_exists(conn, data["sha256_hash"])
        if existing:
            return f"Duplicate content: same file already indexed as `{existing}`."

        await ctx.report_progress(0.7, "Storing in database...")
        doc_id = db.insert_document(
            conn,
            file_path=data["file_path"],
            file_name=data["file_name"],
            file_size_bytes=data["file_size_bytes"],
            modified_date=data["modified_date"],
            page_count=data["page_count"],
            sha256_hash=data["sha256_hash"],
            pages=data["pages"],
        )

        total_chars = sum(len(p["text_content"]) for p in data["pages"])
        result = (
            f"✅ Ingested **{data['file_name']}**\n"
            f"- Document ID: {doc_id}\n"
            f"- Pages extracted: {data['page_count']}\n"
            f"- Characters: {total_chars:,}\n"
            f"- SHA-256: `{data['sha256_hash'][:16]}...`"
        )
        if data.get("extraction_errors"):
            result += f"\n- ⚠️ Page errors: {len(data['extraction_errors'])} (partial extraction)"
            for err in data["extraction_errors"][:5]:
                result += f"\n  - {err}"
        return result
    except (ValueError, db.DatabaseError) as e:
        return _format_error(e, "ingest_pdf")
    except Exception as e:
        return _format_error(e, "ingest_pdf")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_bulk_ingest",
    annotations={
        "title": "Bulk Ingest PDFs",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_bulk_ingest(params: BulkIngestInput, ctx: Context) -> str:
    """Scan a directory and ingest all PDF files found.

    Walks the directory tree, extracts text from each PDF, and stores in the database.
    Skips files already indexed (by path or content hash). Resilient to per-file failures.
    """
    conn = None
    try:
        conn = _safe_conn()
        pdfs = list(pdf_extractor.scan_for_pdfs(params.path, params.max_files))
        total = len(pdfs)
        if total == 0:
            return f"No PDF files found in `{params.path}`."

        ingested = 0
        skipped = 0
        errors: List[str] = []
        total_chars = 0

        for i, pdf_info in enumerate(pdfs):
            if total > 0:
                await ctx.report_progress((i + 1) / total, f"Processing {i + 1}/{total}...")

            fp = pdf_info["file_path"]
            if params.skip_existing and db.document_exists(conn, fp):
                skipped += 1
                continue

            try:
                data = pdf_extractor.extract_pdf_text(fp)
                existing = db.hash_exists(conn, data["sha256_hash"])
                if existing:
                    skipped += 1
                    continue

                db.insert_document(
                    conn,
                    file_path=data["file_path"],
                    file_name=data["file_name"],
                    file_size_bytes=data["file_size_bytes"],
                    modified_date=data["modified_date"],
                    page_count=data["page_count"],
                    sha256_hash=data["sha256_hash"],
                    pages=data["pages"],
                )
                ingested += 1
                total_chars += sum(len(p["text_content"]) for p in data["pages"])
            except Exception as e:
                errors.append(f"{pdf_info['file_name']}: {type(e).__name__}: {e}")

        lines = [
            "# Bulk Ingest Complete",
            f"- **Scanned**: {total} PDFs in `{params.path}`",
            f"- **Ingested**: {ingested} ({total_chars:,} characters)",
            f"- **Skipped**: {skipped} (already indexed or duplicate)",
            f"- **Errors**: {len(errors)}",
        ]
        if errors:
            lines.append("\n## Errors (first 10)")
            for err in errors[:10]:
                lines.append(f"- {err}")
            if len(errors) > 10:
                lines.append(f"- ... and {len(errors) - 10} more")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "bulk_ingest")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_search",
    annotations={
        "title": "Search Litigation Knowledge Base",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_search(params: SearchInput) -> str:
    """Full-text search across all ingested PDF content.

    Uses SQLite FTS5 with porter stemming. Supports:
    - AND/OR/NOT boolean operators
    - "quoted phrases" for exact matches
    - prefix* for prefix matching
    """
    conn = None
    try:
        conn = _safe_conn()
        # Sanitize FTS5 query to prevent syntax crashes
        safe_query = db.sanitize_fts_query(params.query)
        results = db.search_pages(conn, safe_query, params.limit, params.offset)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        if results["total"] == 0:
            return f"No results found for: `{params.query}`\n\nTips:\n- Try simpler terms\n- Use OR for alternatives: `custody OR parenting`\n- Use prefix*: `ex parte*`"

        lines = [
            f"# Search Results: `{params.query}`",
            f"Showing {results['count']} of {results['total']} matches\n",
        ]
        for r in results["results"]:
            lines.append(f"### {r['file_name']} — Page {r['page_number']}")
            lines.append(f"*Doc ID: {r['document_id']}* | `{r['file_path']}`")
            lines.append(f"> {r['snippet']}\n")

        if results["has_more"]:
            lines.append(f"*More results available. Use offset={results['next_offset']}*")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "search")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_list_documents",
    annotations={
        "title": "List Indexed Documents",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_list_documents(params: ListDocumentsInput) -> str:
    """List all documents in the litigation knowledge base with metadata."""
    conn = None
    try:
        conn = _safe_conn()
        results = db.list_documents(conn, params.limit, params.offset, params.name_filter)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        if results["total"] == 0:
            return "No documents indexed yet. Use `litigation_ingest_pdf` or `litigation_bulk_ingest` to add PDFs."

        lines = [
            "# Indexed Documents",
            f"Showing {results['count']} of {results['total']}\n",
            "| ID | File Name | Pages | Size (MB) | Ingested |",
            "|----|-----------|-------|-----------|----------|",
        ]
        for d in results["documents"]:
            size_mb = round(d["file_size_bytes"] / (1024 * 1024), 2)
            ingested = d["ingested_at"][:10] if d["ingested_at"] else "—"
            lines.append(f"| {d['id']} | {d['file_name']} | {d['page_count']} | {size_mb} | {ingested} |")

        if results["has_more"]:
            lines.append(f"\n*More documents available. Use offset={results['next_offset']}*")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "list_documents")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_get_document",
    annotations={
        "title": "Get Document Full Text",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_get_document(params: GetDocumentInput) -> str:
    """Retrieve the full extracted text of a specific document by ID."""
    conn = None
    try:
        conn = _safe_conn()
        result = db.get_document_text(conn, params.document_id)
        if not result:
            return f"Error: Document ID {params.document_id} not found. Use litigation_list_documents to see available documents."

        doc = result["document"]
        pages = result["pages"]
        if params.page_numbers:
            pages = [p for p in pages if p["page_number"] in params.page_numbers]

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"document": doc, "pages": pages}, indent=2, default=str)

        lines = [
            f"# {doc['file_name']}",
            f"**Path**: `{doc['file_path']}`",
            f"**Pages**: {doc['page_count']} | **Size**: {round(doc['file_size_bytes'] / (1024*1024), 2)} MB",
            f"**Ingested**: {doc['ingested_at']}\n",
        ]
        for p in pages:
            lines.append(f"---\n## Page {p['page_number']}\n")
            lines.append(p["text_content"])
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "get_document")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_delete_document",
    annotations={
        "title": "Delete Document from Index",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_delete_document(params: DeleteDocumentInput) -> str:
    """Remove a document and all its pages from the knowledge base.
    Does NOT delete the original PDF file — only removes it from the index.
    """
    conn = None
    try:
        conn = _safe_conn()
        if db.delete_document(conn, params.document_id):
            return f"✅ Deleted document ID {params.document_id} from the knowledge base."
        return f"Error: Document ID {params.document_id} not found."
    except Exception as e:
        return _format_error(e, "delete_document")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_get_stats",
    annotations={
        "title": "Knowledge Base Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_get_stats(params: StatsInput) -> str:
    """Get statistics about the litigation knowledge base including graphs, rules, and risk data."""
    conn = None
    try:
        conn = _safe_conn()
        stats = db.get_stats(conn)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(stats, indent=2, default=str)

        lines = [
            "# Litigation Knowledge Base Stats\n",
            "## PDF Documents",
            f"- **Documents**: {stats['total_documents']}",
            f"- **Pages**: {stats['total_pages']}",
            f"- **Total Size**: {stats['total_size_mb']} MB",
            f"- **Last Ingested**: {stats['last_ingested_at'] or 'Never'}\n",
            "## Knowledge Graphs",
            f"- **Graph Nodes**: {stats['graph_nodes']}",
            f"- **Court Rules Indexed**: {stats['court_rules_indexed']}",
            f"- **Rule Text Entries**: {stats['rules_text_entries']}",
            f"- **Risk Events**: {stats['risk_events']}\n",
        ]
        if stats["graphs_loaded"]:
            lines.append("## Loaded Graphs")
            for g in stats["graphs_loaded"]:
                lines.append(f"- **{g['graph_source']}**: {g['record_count']} records ({g['loaded_at'][:10]})")
        lines.append(f"\n**Database**: `{stats['database_path']}`")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "get_stats")
    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════════
#  TOOLS — Knowledge Graph Queries (4 new tools)
# ══════════════════════════════════════════════════════════════════

@mcp.tool(
    name="litigation_lookup_rule",
    annotations={
        "title": "Lookup Michigan Court Rule",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_lookup_rule(params: LookupRuleInput) -> str:
    """Look up Michigan Court Rules (MCR/MCL) by citation or keyword.

    Searches the indexed rules authority database (873 MCR rules) and
    full-text rule extractions with context snippets.

    Examples:
    - 'MCR 3.706' — find the PPO issuance/service/enforcement rule
    - 'MCR 2.116' — find summary disposition rules
    - 'custody' — search rule text for custody-related provisions
    """
    conn = None
    try:
        conn = _safe_conn()
        results = db.search_rules(conn, params.query, params.limit, params.offset)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        if results["total"] == 0:
            return f"No rules found for: `{params.query}`\n\nTry a broader search (e.g., 'MCR 3' for all Chapter 3 rules)."

        lines = [
            f"# Court Rules: `{params.query}`",
            f"Showing {results['count']} of {results['total']} matches\n",
        ]
        for r in results["results"]:
            rule = r.get("rule", "")
            chapter = r.get("chapter", "")
            lines.append(f"### {rule} (Chapter {chapter})")
            if r.get("authority_id"):
                lines.append(f"*Authority ID: {r['authority_id']}*")
            if r.get("source_doc"):
                lines.append(f"*Source: {r['source_doc'][:60]}*")
            if r.get("snippet"):
                lines.append(f"> {r['snippet']}")
            if r.get("context"):
                lines.append(f"> {r['context'][:200]}...")
            if r.get("context_count"):
                lines.append(f"*References: {r['context_count']}*")
            lines.append("")

        if results["has_more"]:
            lines.append(f"*More results available. Use offset={results['next_offset']}*")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "lookup_rule")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_query_graph",
    annotations={
        "title": "Query Knowledge Graph",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_query_graph(params: QueryGraphInput) -> str:
    """Search the litigation knowledge graph for authorities, case law, forms, and procedures.

    Queries across all loaded graphs (MasterGraph, Court Forms, Authority Forms, etc.).
    Filter by node_type (authority, CASELAW, FORM, PROCEDURE) or graph_source.

    Examples:
    - query='PPO' — find all PPO-related authorities and forms
    - query='Pierron' node_type='CASELAW' — find the Pierron v Pierron case node
    - query='MCL 600.2950' — find the domestic PPO statute
    """
    conn = None
    try:
        conn = _safe_conn()
        results = db.search_graph_nodes(
            conn, params.query, params.node_type, params.graph_source,
            params.limit, params.offset,
        )

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        if results["total"] == 0:
            return f"No graph nodes found for: `{params.query}`\n\nAvailable node types: authority, CASELAW, FORM, PROCEDURE\nAvailable sources: court_forms_graph, authority_forms_graph, master_graph, mcr_organized"

        lines = [
            f"# Knowledge Graph: `{params.query}`",
            f"Showing {results['count']} of {results['total']} nodes\n",
        ]
        for r in results["results"]:
            lines.append(f"### {r['label'] or r['id']}")
            lines.append(f"- **Type**: {r['node_type']} | **Source**: {r['graph_source']}")
            lines.append(f"- **ID**: `{r['id']}`")
            # Parse data blob for extra details
            try:
                node_data = json.loads(r["data"]) if isinstance(r["data"], str) else r["data"]
                if node_data.get("citation"):
                    lines.append(f"- **Citation**: {node_data['citation']}")
                if node_data.get("pin_cite"):
                    lines.append(f"- **Pin Cite**: {node_data['pin_cite']}")
                if node_data.get("tags"):
                    lines.append(f"- **Tags**: {', '.join(node_data['tags'])}")
                if node_data.get("confidence"):
                    lines.append(f"- **Confidence**: {node_data['confidence']}")
            except (json.JSONDecodeError, TypeError):
                pass
            lines.append("")

        if results["has_more"]:
            lines.append(f"*More results available. Use offset={results['next_offset']}*")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "query_graph")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_assess_risk",
    annotations={
        "title": "Assess Litigation Risks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_assess_risk(params: AssessRiskInput) -> str:
    """Assess litigation risks from the risk event taxonomy.

    Returns risk events with severity scores, cure steps, deadlines, and authority references.
    Filter by minimum severity (0-100) and risk class.

    Risk classes: record_incomplete, curable_defect, etc.
    """
    conn = None
    try:
        conn = _safe_conn()
        risks = db.get_risk_events(conn, params.severity_min, params.risk_class)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(risks, indent=2, default=str)

        if not risks:
            return f"No risk events found with severity >= {params.severity_min}" + (
                f" and class='{params.risk_class}'" if params.risk_class else ""
            )

        lines = [
            "# Litigation Risk Assessment",
            f"Found **{len(risks)}** risk events (severity >= {params.severity_min})\n",
        ]
        for r in risks:
            sev = r["severity"]
            emoji = "🔴" if sev >= 80 else "🟡" if sev >= 50 else "🟢"
            lines.append(f"### {emoji} {r['title']} (Severity: {sev})")
            lines.append(f"- **ID**: `{r['risk_type_id']}`")
            lines.append(f"- **Class**: {r['risk_class']} | **Track**: {r['track']} | **Forum**: {r['forum']}")
            lines.append(f"- **Cure Cost**: {r['cure_cost']} | **Deadline**: {r['cure_deadline_clock']}")
            # Cure steps
            try:
                cure_steps = json.loads(r["cure_packet_json"]) if r["cure_packet_json"] else []
                if cure_steps:
                    lines.append("- **Cure Steps**:")
                    for step in cure_steps:
                        lines.append(f"  1. {step}")
            except json.JSONDecodeError:
                pass
            # Triggers
            try:
                triggers = json.loads(r["trigger_json"]) if r["trigger_json"] else []
                if triggers:
                    lines.append(f"- **Triggers**: {', '.join(triggers)}")
            except json.JSONDecodeError:
                pass
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "assess_risk")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_lookup_authority",
    annotations={
        "title": "Lookup Legal Authority",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_lookup_authority(params: QueryGraphInput) -> str:
    """Look up specific legal authorities (case law, statutes, court rules) with pin cites.

    Searches across all authority graphs for Michigan case law, MCR rules, MCL statutes,
    and SCAO forms with jurisdiction, confidence scores, and source data.

    Examples:
    - 'Pierron' — find Pierron v Pierron custody case
    - 'MCL 722' — find Child Custody Act provisions
    - 'PPO' — find all PPO-related authorities
    """
    conn = None
    try:
        conn = _safe_conn()
        # Search specifically in authority-type graphs
        results = db.search_graph_nodes(
            conn, params.query, params.node_type, params.graph_source,
            params.limit, params.offset,
        )

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        if results["total"] == 0:
            return f"No authorities found for: `{params.query}`\n\nTry broader terms or check litigation_get_stats to see loaded graphs."

        lines = [
            f"# Legal Authority Lookup: `{params.query}`",
            f"Showing {results['count']} of {results['total']} authorities\n",
        ]
        for r in results["results"]:
            lines.append(f"### {r['label'] or r['id']}")
            try:
                node_data = json.loads(r["data"]) if isinstance(r["data"], str) else r["data"]
                if node_data.get("citation"):
                    lines.append(f"- **Citation**: {node_data['citation']}")
                if node_data.get("pin_cite"):
                    lines.append(f"- **Pin Cite**: {node_data['pin_cite']}")
                if node_data.get("jurisdiction"):
                    lines.append(f"- **Jurisdiction**: {node_data['jurisdiction']}")
                if node_data.get("node_type"):
                    lines.append(f"- **Type**: {node_data['node_type']}")
                if node_data.get("confidence"):
                    lines.append(f"- **Confidence**: {node_data['confidence']}")
                if node_data.get("tags"):
                    lines.append(f"- **Tags**: {', '.join(node_data['tags'])}")
                if node_data.get("url"):
                    lines.append(f"- **URL**: {node_data['url']}")
            except (json.JSONDecodeError, TypeError):
                lines.append(f"- **Type**: {r['node_type']} | **Source**: {r['graph_source']}")
            lines.append("")

        if results["has_more"]:
            lines.append(f"*More results available. Use offset={results['next_offset']}*")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "lookup_authority")
    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════════
#  TOOLS — SUPERPIN Architecture Queries (evolved .md sections)
# ══════════════════════════════════════════════════════════════════

class VehicleMapInput(BaseModel):
    """Input for mapping relief types to litigation vehicles."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    relief_type: str = Field(
        ..., min_length=1, max_length=200,
        description="Relief type to map (e.g. 'custody modification', 'PPO', 'contempt', 'disqualification').",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="litigation_get_vehicle_map",
    annotations={
        "title": "Get Litigation Vehicle Map",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_get_vehicle_map(params: VehicleMapInput) -> str:
    """Map a relief type to its litigation vehicle, authority chain, required elements, and deadlines.

    Searches the SUPERPIN evolved .md sections for vehicle-related content matching
    the requested relief type. Returns the full pipeline:
    RELIEF → VEHICLE → AUTHORITY → ELEMENTS → ATTACHMENTS → DEADLINES → SERVICE

    Examples:
    - 'custody modification' — find the motion vehicle for modifying custody
    - 'PPO' — find the ex parte PPO petition vehicle
    - 'contempt' — find the contempt/show cause vehicle
    """
    conn = None
    try:
        conn = _safe_conn()
        relief_pattern = f"%{params.relief_type}%"

        # 1. Search md_sections for vehicle-related sections matching the relief type
        sections = conn.execute(
            """SELECT * FROM md_sections WHERE
               (section_path LIKE '%ehicle%' OR section_title LIKE '%ehicle%' OR section_title LIKE '%lane%')
               AND (content LIKE ? OR section_title LIKE ?)
               ORDER BY section_level, id""",
            (relief_pattern, relief_pattern),
        ).fetchall()

        # 2. FTS search for the relief type
        fts_results = []
        try:
            fts_results = conn.execute(
                """SELECT ms.*, snippet(md_sections_fts, 1, '>>>', '<<<', '...', 50) AS snippet
                   FROM md_sections_fts
                   JOIN md_sections ms ON ms.id = md_sections_fts.rowid
                   WHERE md_sections_fts MATCH ?
                   ORDER BY rank LIMIT 20""",
                (params.relief_type,),
            ).fetchall()
        except Exception:
            pass  # FTS match syntax may fail on some inputs

        # 3. Cross-refs for vehicle-type refs matching the relief
        xrefs = conn.execute(
            """SELECT cr.*, ms.section_title, ms.section_path, ms.content
               FROM md_cross_refs cr
               JOIN md_sections ms ON ms.id = cr.section_id
               WHERE cr.ref_type = 'vehicle' AND cr.ref_value LIKE ?
               ORDER BY cr.confidence DESC""",
            (relief_pattern,),
        ).fetchall()

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "relief_type": params.relief_type,
                "vehicle_sections": [dict(r) for r in sections],
                "fts_results": [dict(r) for r in fts_results],
                "cross_refs": [dict(r) for r in xrefs],
            }, indent=2, default=str)

        if not sections and not fts_results and not xrefs:
            return (
                f"No vehicle map found for relief type: `{params.relief_type}`\n\n"
                "**Suggestion:** Run `litigation_evolve_files` first to load LitigationOS .md files "
                "into the SUPERPIN architecture, then retry this query."
            )

        lines = [
            f"# Vehicle Map: `{params.relief_type}`",
            f"## RELIEF → VEHICLE → AUTHORITY → ELEMENTS → ATTACHMENTS → DEADLINES → SERVICE\n",
        ]

        if sections:
            lines.append("### Vehicle Sections")
            for s in sections:
                lines.append(f"#### {s['section_title']}")
                lines.append(f"*Path: {s['section_path']}* | *Source: {s['source_file']}*")
                lines.append(f"{s['content'][:500]}")
                if len(s["content"]) > 500:
                    lines.append("*(truncated — use litigation_search for full text)*")
                lines.append("")

        if fts_results:
            lines.append("### Full-Text Matches")
            for r in fts_results:
                lines.append(f"- **{r['section_title']}** ({r['section_path']})")
                if r.get("snippet"):
                    lines.append(f"  > {r['snippet']}")
            lines.append("")

        if xrefs:
            lines.append("### Cross-Reference Links")
            for x in xrefs:
                lines.append(f"- **{x['ref_value']}** → {x['section_title']} (confidence: {x['confidence']})")
                if x.get("graph_node_id"):
                    lines.append(f"  Graph node: `{x['graph_node_id']}` ({x['graph_source']})")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "get_vehicle_map")
    finally:
        if conn:
            conn.close()


class SubagentSpecInput(BaseModel):
    """Input for retrieving a SUPERPIN sub-agent specification."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    agent_name: str = Field(
        ..., min_length=1, max_length=200,
        description="Agent name (e.g. 'AUTH_HARVESTER', 'DRAFTER_COA', 'TIMELINE_BUILDER').",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="litigation_get_subagent_spec",
    annotations={
        "title": "Get Sub-Agent Specification",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_get_subagent_spec(params: SubagentSpecInput) -> str:
    """Retrieve the specification for a SUPERPIN sub-agent (role, inputs, outputs, triggers).

    Searches evolved .md sections for AGENT:{name} patterns and cross-references
    tagged as agent type. Returns the full agent spec including role description,
    required inputs, expected outputs, and trigger conditions.

    Examples:
    - 'AUTH_HARVESTER' — find the authority harvesting agent spec
    - 'DRAFTER_COA' — find the Court of Appeals drafter spec
    - 'TIMELINE_BUILDER' — find the timeline construction agent spec
    """
    conn = None
    try:
        conn = _safe_conn()
        agent_tag = f"%AGENT:{params.agent_name}%"
        name_pattern = f"%{params.agent_name}%"

        # 1. Search md_sections for agent spec content
        sections = conn.execute(
            """SELECT * FROM md_sections
               WHERE content LIKE ? OR section_title LIKE ?
               ORDER BY section_level, id""",
            (agent_tag, name_pattern),
        ).fetchall()

        # Also match on the plain name in content
        if not sections:
            sections = conn.execute(
                """SELECT * FROM md_sections
                   WHERE content LIKE ? OR section_title LIKE ?
                   ORDER BY section_level, id""",
                (name_pattern, name_pattern),
            ).fetchall()

        # 2. Cross-refs where ref_type = 'agent'
        xrefs = conn.execute(
            """SELECT cr.*, ms.section_title, ms.section_path, ms.content
               FROM md_cross_refs cr
               JOIN md_sections ms ON ms.id = cr.section_id
               WHERE cr.ref_type = 'agent' AND cr.ref_value LIKE ?
               ORDER BY cr.confidence DESC""",
            (name_pattern,),
        ).fetchall()

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "agent_name": params.agent_name,
                "sections": [dict(r) for r in sections],
                "cross_refs": [dict(r) for r in xrefs],
            }, indent=2, default=str)

        if not sections and not xrefs:
            # List available agents
            available = conn.execute(
                """SELECT DISTINCT ref_value FROM md_cross_refs
                   WHERE ref_type = 'agent' ORDER BY ref_value"""
            ).fetchall()
            agent_list = ", ".join(f"`{a['ref_value']}`" for a in available) if available else "*(none indexed)*"
            return (
                f"No agent spec found for: `{params.agent_name}`\n\n"
                f"**Available agents:** {agent_list}\n\n"
                "If no agents are listed, run `litigation_evolve_files` first to load "
                "LitigationOS .md files into the SUPERPIN architecture."
            )

        lines = [f"# Sub-Agent Spec: `{params.agent_name}`\n"]

        if sections:
            for s in sections:
                lines.append(f"## {s['section_title']}")
                lines.append(f"*Path: {s['section_path']}* | *Source: {s['source_file']}*\n")
                lines.append(s["content"])
                lines.append("")

        if xrefs:
            lines.append("### Cross-Reference Links")
            for x in xrefs:
                lines.append(f"- **{x['ref_value']}** → {x['section_title']} (confidence: {x['confidence']})")
                if x.get("graph_node_id"):
                    lines.append(f"  Graph node: `{x['graph_node_id']}` ({x['graph_source']})")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "get_subagent_spec")
    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════════
#  TOOLS — Diagnostics & Convergence
# ══════════════════════════════════════════════════════════════════

@mcp.tool(
    name="litigation_self_test",
    annotations={
        "title": "Run Self-Test Diagnostics",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_self_test(params: SelfTestInput) -> str:
    """Run diagnostic self-tests on the litigation database.

    Tests DB connectivity, schema presence, FTS5 round-trip, knowledge graph counts,
    and .md evolution counts.  Returns a pass/fail report with timing for each test.
    """
    results = []

    # 1. DB connection test
    conn = None
    t0 = time.perf_counter()
    try:
        conn = _safe_conn()
        elapsed = time.perf_counter() - t0
        results.append({"test": "db_connection", "passed": True, "ms": round(elapsed * 1000, 2)})
    except Exception as e:
        elapsed = time.perf_counter() - t0
        results.append({"test": "db_connection", "passed": False, "ms": round(elapsed * 1000, 2), "error": str(e)})
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"tests": results, "all_passed": False}, indent=2)
        return f"# Self-Test Results\n\n❌ **db_connection** — FAIL ({elapsed*1000:.1f}ms): {e}"

    try:
        # 2. Schema check
        t0 = time.perf_counter()
        try:
            required_tables = ["documents", "pages", "graph_nodes", "md_sections"]
            existing = {
                r["name"]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            missing = [t for t in required_tables if t not in existing]
            elapsed = time.perf_counter() - t0
            results.append({
                "test": "schema_check",
                "passed": len(missing) == 0,
                "ms": round(elapsed * 1000, 2),
                "missing_tables": missing,
            })
        except Exception as e:
            elapsed = time.perf_counter() - t0
            results.append({"test": "schema_check", "passed": False, "ms": round(elapsed * 1000, 2), "error": str(e)})

        # 3. FTS5 round-trip
        t0 = time.perf_counter()
        try:
            conn.execute(
                "INSERT INTO md_sections (source_file, source_path, section_level, section_title, section_path, content, evolved_at) "
                "VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
                ("__selftest__", "__selftest__", 1, "selftest", "selftest", "xyzzy_selftest_token"),
            )
            conn.commit()
            test_rowid = conn.execute(
                "SELECT id FROM md_sections WHERE source_file = '__selftest__'"
            ).fetchone()["id"]
            fts_hit = conn.execute(
                "SELECT COUNT(*) as c FROM md_sections_fts WHERE md_sections_fts MATCH ?",
                ("xyzzy_selftest_token",),
            ).fetchone()["c"]
            conn.execute("DELETE FROM md_sections WHERE id = ?", (test_rowid,))
            conn.commit()
            elapsed = time.perf_counter() - t0
            results.append({
                "test": "fts5_round_trip",
                "passed": fts_hit >= 1,
                "ms": round(elapsed * 1000, 2),
            })
        except Exception as e:
            elapsed = time.perf_counter() - t0
            try:
                conn.execute("DELETE FROM md_sections WHERE source_file = '__selftest__'")
                conn.commit()
            except Exception:
                pass
            results.append({"test": "fts5_round_trip", "passed": False, "ms": round(elapsed * 1000, 2), "error": str(e)})

        # 4. Knowledge graph check
        t0 = time.perf_counter()
        try:
            graph_count = conn.execute("SELECT COUNT(*) as c FROM graph_nodes").fetchone()["c"]
            elapsed = time.perf_counter() - t0
            results.append({
                "test": "knowledge_graph",
                "passed": True,
                "ms": round(elapsed * 1000, 2),
                "count": graph_count,
            })
        except Exception as e:
            elapsed = time.perf_counter() - t0
            results.append({"test": "knowledge_graph", "passed": False, "ms": round(elapsed * 1000, 2), "error": str(e)})

        # 5. Evolution check
        t0 = time.perf_counter()
        try:
            section_count = conn.execute("SELECT COUNT(*) as c FROM md_sections").fetchone()["c"]
            elapsed = time.perf_counter() - t0
            results.append({
                "test": "md_evolution",
                "passed": True,
                "ms": round(elapsed * 1000, 2),
                "count": section_count,
            })
        except Exception as e:
            elapsed = time.perf_counter() - t0
            results.append({"test": "md_evolution", "passed": False, "ms": round(elapsed * 1000, 2), "error": str(e)})

        all_passed = all(r["passed"] for r in results)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"tests": results, "all_passed": all_passed}, indent=2)

        emoji = "✅" if all_passed else "❌"
        lines = [
            f"# Self-Test Results {emoji}",
            f"**Overall**: {'ALL PASSED' if all_passed else 'SOME FAILED'}\n",
        ]
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            line = f"- **{r['test']}** — {status} ({r['ms']:.1f}ms)"
            if r.get("count") is not None:
                line += f" — {r['count']} rows"
            if r.get("missing_tables"):
                line += f" — missing: {', '.join(r['missing_tables'])}"
            if r.get("error"):
                line += f" — {r['error']}"
            lines.append(line)

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "self_test")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_self_audit",
    annotations={
        "title": "Run Data-Quality Audit",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_self_audit(params: SelfAuditInput) -> str:
    """Run a comprehensive data-quality audit on the litigation database.

    Returns a quality score (0-100), findings with severity levels,
    and summary statistics for documents, pages, graphs, and .md evolution.
    """
    conn = None
    try:
        conn = _safe_conn()
        audit = db.run_self_audit(conn)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(audit, indent=2, default=str)

        score = audit["quality_score"]
        emoji = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
        lines = [
            f"# Data-Quality Audit {emoji}",
            f"## Quality Score: **{score}/100**\n",
        ]

        # Findings
        if audit["findings"]:
            lines.append("## Findings\n")
            for f in audit["findings"]:
                sev = f["severity"]
                sev_icon = "🔴" if sev == "critical" else "🟠" if sev == "high" else "🟡"
                line = f"- {sev_icon} **{f['issue']}** (severity: {sev})"
                if f.get("count") is not None:
                    line += f" — count: {f['count']}"
                if f.get("missing"):
                    line += f" — missing: {', '.join(str(m) for m in f['missing'][:5])}"
                lines.append(line)
        else:
            lines.append("*No issues found — database is healthy.*\n")

        # Summary stats
        s = audit["summary"]
        lines.append("\n## Summary Stats\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Documents | {s['documents']} |")
        lines.append(f"| Pages | {s['pages']} |")
        lines.append(f"| Graph Nodes | {s['graph_nodes']} |")
        lines.append(f"| MD Files Evolved | {s['md_files_evolved']} |")
        lines.append(f"| MD Sections | {s['md_sections']} |")
        lines.append(f"| Cross-Refs | {s['cross_refs']} |")
        lines.append(f"| Cross-Ref Link Rate | {s['cross_ref_link_rate']}% |")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "self_audit")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_convergence_status",
    annotations={
        "title": "Check Convergence Status",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_convergence_status(params: ConvergenceInput) -> str:
    """Check convergence status of the litigation knowledge base.

    Shows whether the system has converged, quality score, ΔNEW items,
    BLOCKERS, NEXT_PATCH recommendation, and emergence signals (cross-ref clusters).
    """
    conn = None
    try:
        conn = _safe_conn()
        status = db.get_convergence_status(conn)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(status, indent=2, default=str)

        converged_emoji = "✅" if status["converged"] else "🔄"
        score = status["quality_score"]
        score_emoji = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"

        lines = [
            f"# Convergence Status {converged_emoji}",
            f"## CONVERGED: **{'YES' if status['converged'] else 'NO'}**",
            f"## Quality Score: {score_emoji} **{score}/100**",
            f"*Cycle count: {status['cycle_count']}*\n",
        ]

        # ΔNEW
        if status["delta_new"]:
            lines.append("## ΔNEW\n")
            for item in status["delta_new"]:
                lines.append(f"- {item}")
            lines.append("")

        # BLOCKERS
        if status["blockers"]:
            lines.append("## 🚫 BLOCKERS\n")
            for b in status["blockers"]:
                lines.append(f"- ❌ {b}")
            lines.append("")
        else:
            lines.append("## BLOCKERS: *None* ✅\n")

        # NEXT_PATCH
        lines.append("## NEXT_PATCH\n")
        lines.append(f"➡️ **{status['next_patch']}**\n")

        # Emergence signals
        if status["emergence_signals"]:
            lines.append("## Emergence Signals (Cross-Ref Clusters)\n")
            lines.append("| Reference | Mentions |")
            lines.append("|-----------|----------|")
            for sig in status["emergence_signals"]:
                lines.append(f"| {sig['ref_value']} | {sig['mentions']} |")
        else:
            lines.append("*No emergence signals yet — keep ingesting.*")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "convergence_status")
    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════════
#  TOOLS — Evolution Pipeline
# ══════════════════════════════════════════════════════════════════

class EvolveFilesInput(BaseModel):
    """Input for triggering evolution on md/txt files."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    directory: str = Field(
        ..., min_length=1,
        description="Path to scan for .md and .txt files.",
    )
    file_types: str = Field(
        default="both",
        description="md, txt, or both",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class EvolvePdfsInput(BaseModel):
    """Input for evolving ingested PDF pages."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    document_id: Optional[int] = Field(
        default=None,
        description="Specific document ID, or None for all",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class SearchEvolvedInput(BaseModel):
    """Input for FTS5 search across all evolved content."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(..., min_length=1, description="Search query.")
    source_type: Optional[str] = Field(
        default=None,
        description="Filter by source: md, txt, pdf, or None for all",
    )
    limit: int = Field(default=20, ge=1, le=100)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class CrossRefsInput(BaseModel):
    """Input for querying the cross-reference network."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ..., min_length=1,
        description='Search value, e.g. "MCR 3.706", "AUTH_HARVESTER", "custody"',
    )
    ref_type: Optional[str] = Field(
        default=None,
        description="Filter: agent, rule, vehicle, risk, authority",
    )
    limit: int = Field(default=50, ge=1, le=200)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class EvolutionStatsInput(BaseModel):
    """Input for evolution coverage stats."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="litigation_evolve_files",
    annotations={
        "title": "Evolve MD/TXT Files",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_evolve_files(params: EvolveFilesInput) -> str:
    """Trigger evolution on .md and/or .txt files in a directory.

    Parses files into sections, extracts cross-references, and links them
    to the knowledge graph. Idempotent — already-evolved files are skipped.
    """
    conn = None
    try:
        conn = _safe_conn()
        results = {"md": None, "txt": None}
        if params.file_types in ("md", "both"):
            results["md"] = db.evolve_all_md_files(conn, params.directory)
        if params.file_types in ("txt", "both"):
            results["txt"] = db.evolve_all_txt_files(conn, params.directory)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        lines = ["# File Evolution Results\n"]
        for ftype, res in results.items():
            if res is None:
                continue
            lines.append(f"## {ftype.upper()} Files")
            lines.append(f"- Evolved: **{res['evolved']}**")
            lines.append(f"- Skipped: {res['skipped']}")
            lines.append(f"- Errors: {res['errors']}\n")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "evolve_files")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_evolve_pdfs",
    annotations={
        "title": "Evolve Ingested PDF Pages",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_evolve_pdfs(params: EvolvePdfsInput) -> str:
    """Evolve ingested PDF pages into the cross-reference knowledge layer.

    Converts PDF page text into sections, extracts cross-references, and
    links them to the knowledge graph. Idempotent — already-evolved pages are skipped.
    """
    conn = None
    try:
        conn = _safe_conn()
        result = db.evolve_from_pages(conn, params.document_id)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2, default=str)

        lines = [
            "# PDF Evolution Results\n",
            f"- Status: **{result.get('status', 'done')}**",
            f"- Documents evolved: **{result.get('documents', result.get('docs_evolved', 0))}**",
            f"- Sections created: **{result.get('sections', result.get('total_sections', 0))}**",
            f"- Cross-refs found: **{result.get('cross_refs', result.get('total_refs', 0))}**",
        ]

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "evolve_pdfs")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_search_evolved",
    annotations={
        "title": "Search Evolved Content",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_search_evolved(params: SearchEvolvedInput) -> str:
    """FTS5 search across all evolved content (md, txt, pdf sections).

    Returns matching sections with snippets. Optionally filter by source type.
    """
    conn = None
    try:
        conn = _safe_conn()

        # Map source_type to a source_file filter hint
        source_file_filter = None
        if params.source_type == "pdf":
            source_file_filter = ".pdf"
        elif params.source_type == "md":
            source_file_filter = ".md"
        elif params.source_type == "txt":
            source_file_filter = ".txt"

        result = db.search_evolved_knowledge(
            conn, params.query, source_file=source_file_filter, limit=params.limit,
        )

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2, default=str)

        lines = [
            f"# Evolved Knowledge Search: '{params.query}'\n",
            f"**{result['total']}** total matches (showing {result['count']})\n",
        ]
        for r in result["results"]:
            lines.append(f"### {r.get('section_title', 'Untitled')}")
            lines.append(f"*Source: {r.get('source_file', '?')} | Level {r.get('section_level', '?')}*")
            lines.append(f"> {r.get('snippet', '')}\n")

        if result.get("has_more"):
            lines.append(f"*More results available (next offset: {result['next_offset']})*")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "search_evolved")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_cross_refs",
    annotations={
        "title": "Query Cross-Reference Network",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_cross_refs(params: CrossRefsInput) -> str:
    """Query the cross-reference network for matching references.

    Search by value (e.g. 'MCR 3.706', 'custody') and optionally filter by
    reference type (agent, rule, vehicle, risk, authority).
    """
    conn = None
    try:
        conn = _safe_conn()
        refs = db.get_cross_refs(conn, ref_type=params.ref_type, ref_value=params.query, limit=params.limit)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(refs, indent=2, default=str)

        lines = [f"# Cross-References: '{params.query}'\n", f"**{len(refs)}** matches\n"]
        if refs:
            lines.append("| Type | Value | Section | Source |")
            lines.append("|------|-------|---------|--------|")
            for r in refs:
                lines.append(
                    f"| {r.get('ref_type', '')} | {r.get('ref_value', '')} "
                    f"| {r.get('section_title', '')} | {r.get('source_file', '')} |"
                )
        else:
            lines.append("*No cross-references found.*")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "cross_refs")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_evolution_stats",
    annotations={
        "title": "Evolution Coverage Stats",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_evolution_stats(params: EvolutionStatsInput) -> str:
    """Get evolution coverage statistics as a dashboard.

    Shows files evolved by type, total sections, cross-refs,
    graph link coverage, and evolution completeness.
    """
    conn = None
    try:
        conn = _safe_conn()
        stats = db.get_evolution_stats(conn)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(stats, indent=2, default=str)

        total_files = stats["total_files_evolved"]
        md_count = sum(1 for f in stats["evolved_files"] if f["source_path"].endswith(".md"))
        txt_count = sum(1 for f in stats["evolved_files"] if f["source_path"].endswith(".txt"))
        pdf_count = sum(1 for f in stats["evolved_files"] if f["source_path"].endswith(".pdf"))

        link_rate = stats["link_rate"]
        completeness_emoji = "🟢" if link_rate >= 80 else "🟡" if link_rate >= 50 else "🔴"

        lines = [
            "# 📊 Evolution Coverage Dashboard\n",
            "## Files Evolved by Type",
            f"| Type | Count |",
            f"|------|-------|",
            f"| MD   | {md_count} |",
            f"| TXT  | {txt_count} |",
            f"| PDF  | {pdf_count} |",
            f"| **Total** | **{total_files}** |\n",
            "## Metrics",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Sections | {stats['total_sections']} |",
            f"| Total Cross-Refs | {stats['total_cross_refs']} |",
            f"| Graph-Linked Refs | {stats['graph_linked_refs']} |",
            f"| Link Coverage | {completeness_emoji} **{link_rate}%** |\n",
        ]

        if stats["ref_types"]:
            lines.append("## Cross-Ref Types")
            lines.append("| Type | Count |")
            lines.append("|------|-------|")
            for rt in stats["ref_types"]:
                lines.append(f"| {rt['ref_type']} | {rt['cnt']} |")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "evolution_stats")
    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════════
#  TOOLS — Health & Error Telemetry (new)
# ══════════════════════════════════════════════════════════════════

class HealthInput(BaseModel):
    """Input for system health check."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    reset_circuit_breaker: bool = Field(
        default=False,
        description="If True, resets the circuit breaker to CLOSED state.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="litigation_health",
    annotations={
        "title": "System Health & Error Telemetry",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_health(params: HealthInput) -> str:
    """Get server health status, circuit breaker state, and recent error telemetry.

    Shows startup state, knowledge graph loading status, circuit breaker state,
    and a summary of errors from the last 24 hours grouped by code and tool.
    Optionally resets the circuit breaker if it has tripped.
    """
    if params.reset_circuit_breaker:
        db._db_circuit.reset()

    health_data = db.health.status
    conn = None
    error_summary = []
    try:
        conn = _safe_conn()
        error_summary = db.get_error_summary(conn, hours=24)
    except Exception as e:
        error_summary = [{"error": str(e)}]
    finally:
        if conn:
            conn.close()

    result = {
        "health": health_data,
        "error_telemetry_24h": error_summary,
    }

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(result, indent=2, default=str)

    h = health_data
    cb = h.get("circuit_breaker", {})
    cb_state = cb.get("state", "unknown")
    cb_emoji = "🟢" if cb_state == "closed" else "🟡" if cb_state == "half_open" else "🔴"
    deg_emoji = "🟡 DEGRADED" if h.get("degraded") else "🟢 HEALTHY"

    lines = [
        f"# 🏥 Server Health: {deg_emoji}\n",
        f"- **Startup**: {h.get('startup_time', 'N/A')}",
        f"- **Graphs Loaded**: {'✅' if h.get('graphs_loaded') else '❌'}",
    ]
    if h.get("graph_errors"):
        for ge in h["graph_errors"]:
            lines.append(f"  - ⚠️ {ge}")

    lines.extend([
        f"\n## Circuit Breaker: {cb_emoji} **{cb_state.upper()}**",
        f"- Failures: {cb.get('failure_count', 0)}/{cb.get('threshold', 5)}",
        f"- Reset timeout: {cb.get('reset_timeout_s', 60)}s",
    ])
    if params.reset_circuit_breaker:
        lines.append("- ♻️ **Circuit breaker has been reset.**")

    if error_summary and not error_summary[0].get("error"):
        lines.append("\n## Error Telemetry (Last 24h)")
        lines.append("| Code | Tool | Count | Last Seen |")
        lines.append("|------|------|-------|-----------|")
        for es in error_summary:
            lines.append(
                f"| `{es.get('error_code', '?')}` | {es.get('tool_name', '?')} "
                f"| {es.get('count', 0)} | {es.get('last_seen', '?')[:19]} |"
            )
    elif not error_summary:
        lines.append("\n*No errors in the last 24 hours.* ✅")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
#  TOOLS — GOD-Level System Tools (8 tools)
# ══════════════════════════════════════════════════════════════════

class GODStatusInput(BaseModel):
    """Input for GOD system status dashboard."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class GODIngestCSVInput(BaseModel):
    """Input for GOD master CSV ingestion."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    data_dir: str = Field(
        default=r"D:\LITIGATIONOS_DATA",
        description="Root directory containing master CSV datasets.",
    )
    dataset: Optional[str] = Field(
        default=None,
        description="Specific dataset name to ingest. If omitted, ingests all.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class GODQueryMasterInput(BaseModel):
    """Input for GOD master data query."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ..., min_length=1,
        description="Search query against master data.",
    )
    dataset: Optional[str] = Field(
        default=None,
        description="Limit search to a specific dataset.",
    )
    limit: int = Field(
        default=20, ge=1, le=100,
        description="Maximum number of results to return.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class GODVectorSearchInput(BaseModel):
    """Input for GOD vector similarity search."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ..., min_length=1,
        description="Natural language query for vector similarity search.",
    )
    top_k: int = Field(
        default=10, ge=1, le=50,
        description="Number of top results to return.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class GODDeadlinesInput(BaseModel):
    """Input for GOD deadline computation."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    trigger_event: str = Field(
        ..., min_length=1,
        description="The triggering event (e.g. 'complaint_filed', 'motion_served').",
    )
    trigger_date: str = Field(
        ..., min_length=1,
        description="Date of the trigger event (ISO format, e.g. '2025-01-15').",
    )
    jurisdiction: str = Field(
        default="MI",
        description="Jurisdiction code (default: MI for Michigan).",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class GODRedTeamInput(BaseModel):
    """Input for GOD red-team validation."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    claim: str = Field(
        ..., min_length=1,
        description="Legal claim or argument to red-team validate.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class GODEvidenceChainInput(BaseModel):
    """Input for GOD evidence chain tracing."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    claim: str = Field(
        ..., min_length=1,
        description="Legal claim to trace evidence chain for.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class GODSwarmDispatchInput(BaseModel):
    """Input for GOD swarm agent dispatch."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    task: str = Field(
        ..., min_length=1,
        description="Task description to dispatch to the agent swarm.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="god_system_status",
    annotations={
        "title": "GOD System Status Dashboard",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def god_system_status(params: GODStatusInput) -> str:
    """Get GOD-level system status dashboard.

    Scans the system registry and reports each system's type, path,
    version, file count, and status with totals by type.
    """
    conn = None
    try:
        conn = _safe_conn()
        registry = db.scan_all_systems(conn)

        rows = conn.execute(
            "SELECT * FROM system_registry ORDER BY system_type, system_name"
        ).fetchall()
        cols = [d[0] for d in conn.execute(
            "SELECT * FROM system_registry LIMIT 0"
        ).description] if rows else []
        systems = [dict(zip(cols, r)) for r in rows]

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"registry": registry, "systems": systems}, indent=2, default=str)

        lines = ["# 🖥️ GOD System Status Dashboard\n"]

        totals: dict = {}
        for s in systems:
            stype = s.get("system_type", "unknown")
            lines.append(
                f"- **{s.get('system_name', '?')}** ({stype}) — "
                f"v{s.get('version', '?')} | "
                f"{s.get('file_count', 0)} files | "
                f"Status: {s.get('status', 'unknown')} | "
                f"Path: `{s.get('path', '?')}`"
            )
            totals[stype] = totals.get(stype, 0) + 1

        lines.append("\n## Totals by Type")
        lines.append("| Type | Count |")
        lines.append("|------|-------|")
        for t, c in sorted(totals.items()):
            lines.append(f"| {t} | {c} |")
        lines.append(f"| **Total** | **{len(systems)}** |")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "god_system_status")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="god_ingest_master_csv",
    annotations={
        "title": "GOD Ingest Master CSV",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def god_ingest_master_csv(params: GODIngestCSVInput) -> str:
    """Ingest master CSV datasets into the GOD knowledge base.

    If a specific dataset is provided, ingests only that dataset.
    Otherwise, ingests all master CSVs from the data directory.
    """
    conn = None
    try:
        conn = _safe_conn()

        if params.dataset:
            import os
            path = os.path.join(params.data_dir, params.dataset)
            results = db.ingest_master_csv(conn, path, params.dataset)
        else:
            results = db.ingest_all_master_csvs(conn, params.data_dir)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        lines = ["# 📥 Master CSV Ingestion Results\n"]
        if isinstance(results, dict):
            for ds, info in results.items():
                rows = info if isinstance(info, int) else info.get("rows_ingested", info)
                lines.append(f"- **{ds}**: {rows} rows ingested")
        else:
            lines.append(f"- Result: {results}")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "god_ingest_master_csv")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="god_query_master",
    annotations={
        "title": "GOD Query Master Data",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def god_query_master(params: GODQueryMasterInput) -> str:
    """Search across master data with optional dataset filtering.

    Returns matching rows with dataset name, text, and row info.
    """
    conn = None
    try:
        conn = _safe_conn()
        results = db.search_master_data(conn, params.query, params.dataset, params.limit)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        lines = [f"# 🔎 Master Data Results for: *{params.query}*\n"]
        if not results:
            lines.append("No results found.")
        else:
            for i, r in enumerate(results, 1):
                ds = r.get("dataset", "unknown")
                text = r.get("text", r.get("matching_text", str(r)))[:200]
                row_info = r.get("row_id", r.get("id", ""))
                lines.append(f"### {i}. [{ds}] Row {row_info}")
                lines.append(f"{text}\n")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "god_query_master")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="god_vector_search",
    annotations={
        "title": "GOD Vector Similarity Search",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def god_vector_search(params: GODVectorSearchInput) -> str:
    """Perform vector similarity search across the knowledge base.

    Returns top-k results ranked by similarity score with text snippets.
    """
    conn = None
    try:
        conn = _safe_conn()
        results = db.vector_search(conn, params.query, params.top_k)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        lines = [f"# 🧲 Vector Search: *{params.query}*\n"]
        if not results:
            lines.append("No similar results found.")
        else:
            for i, r in enumerate(results, 1):
                score = r.get("similarity", r.get("score", 0))
                snippet = r.get("snippet", r.get("text", str(r)))[:200]
                source = r.get("source", r.get("document", "unknown"))
                lines.append(f"### {i}. (score: {score:.4f}) — {source}")
                lines.append(f"{snippet}\n")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "god_vector_search")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="god_compute_deadlines",
    annotations={
        "title": "GOD Compute Legal Deadlines",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def god_compute_deadlines(params: GODDeadlinesInput) -> str:
    """Compute legal deadlines from a trigger event and date.

    Uses jurisdiction-specific rules to calculate a timeline
    of upcoming deadlines with applicable rule citations.
    """
    conn = None
    try:
        conn = _safe_conn()
        results = db.compute_deadlines(conn, params.trigger_event, params.trigger_date, params.jurisdiction)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        lines = [
            f"# ⏰ Deadline Timeline\n",
            f"**Trigger**: {params.trigger_event} on {params.trigger_date} ({params.jurisdiction})\n",
            "| # | Deadline Date | Description | Rule |",
            "|---|--------------|-------------|------|",
        ]
        if isinstance(results, list):
            for i, d in enumerate(results, 1):
                date = d.get("deadline_date", d.get("date", "?"))
                desc = d.get("description", d.get("name", "?"))
                rule = d.get("rule", d.get("authority", "—"))
                lines.append(f"| {i} | {date} | {desc} | {rule} |")
        else:
            lines.append(f"\n{results}")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "god_compute_deadlines")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="god_red_team",
    annotations={
        "title": "GOD Red-Team Validation",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def god_red_team(params: GODRedTeamInput) -> str:
    """Red-team validate a legal claim or argument.

    Scores authority, evidence, and consistency. Reports findings
    by severity and overall FILING_READY status.
    """
    conn = None
    try:
        conn = _safe_conn()
        results = db.red_team_validate(conn, params.claim)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        scores = results.get("scores", {})
        findings = results.get("findings", [])
        filing_ready = results.get("filing_ready", False)
        status_emoji = "✅" if filing_ready else "❌"

        lines = [
            f"# 🔴 Red-Team Validation\n",
            f"**Claim**: {params.claim}\n",
            f"## {status_emoji} FILING_READY: {'YES' if filing_ready else 'NO'}\n",
            "## Scores",
            "| Metric | Score |",
            "|--------|-------|",
            f"| Authority | {scores.get('authority', '?')} |",
            f"| Evidence | {scores.get('evidence', '?')} |",
            f"| Consistency | {scores.get('consistency', '?')} |\n",
        ]

        if findings:
            lines.append("## Findings")
            for f in findings:
                severity = f.get("severity", "info")
                sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
                lines.append(f"- {sev_icon} **{severity.upper()}**: {f.get('message', f.get('detail', str(f)))}")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "god_red_team")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="god_evidence_chain",
    annotations={
        "title": "GOD Evidence Chain Tracer",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def god_evidence_chain(params: GODEvidenceChainInput) -> str:
    """Trace the evidence chain for a legal claim.

    Maps claim → sections → cross-references → sources,
    showing completeness percentage and any gaps.
    """
    conn = None
    try:
        conn = _safe_conn()
        results = db.trace_evidence_chain(conn, params.claim)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        completeness = results.get("completeness_pct", 0)
        comp_emoji = "🟢" if completeness >= 80 else "🟡" if completeness >= 50 else "🔴"
        gaps = results.get("gaps", [])

        lines = [
            f"# 🔗 Evidence Chain: *{params.claim}*\n",
            f"## Completeness: {comp_emoji} **{completeness}%**\n",
        ]

        sections = results.get("sections", [])
        if sections:
            lines.append("## Sections")
            for s in sections:
                lines.append(f"- {s.get('title', s.get('name', str(s)))}")

        cross_refs = results.get("cross_refs", [])
        if cross_refs:
            lines.append("\n## Cross-References")
            for cr in cross_refs:
                lines.append(f"- {cr.get('ref', cr.get('citation', str(cr)))}")

        sources = results.get("sources", [])
        if sources:
            lines.append("\n## Sources")
            for src in sources:
                lines.append(f"- {src.get('name', src.get('path', str(src)))}")

        if gaps:
            lines.append("\n## ⚠️ Gaps")
            for g in gaps:
                lines.append(f"- {g}")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "god_evidence_chain")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="god_swarm_dispatch",
    annotations={
        "title": "GOD Swarm Agent Dispatch",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def god_swarm_dispatch(params: GODSwarmDispatchInput) -> str:
    """Dispatch a task to the agent swarm for recommendations.

    Returns ranked agent recommendations with relevance scores,
    roles, and suggested inputs for the top matching agents.
    """
    conn = None
    try:
        conn = _safe_conn()
        results = db.dispatch_to_swarm(conn, params.task)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(results, indent=2, default=str)

        agents = results.get("agents", results if isinstance(results, list) else [])
        lines = [
            f"# 🐝 Swarm Dispatch: *{params.task}*\n",
            "## Top Agent Recommendations\n",
        ]

        if not agents:
            lines.append("No matching agents found for this task.")
        else:
            lines.append("| Rank | Agent | Role | Relevance | Suggested Input |")
            lines.append("|------|-------|------|-----------|-----------------|")
            for i, a in enumerate(agents, 1):
                name = a.get("agent", a.get("name", "?"))
                role = a.get("role", "—")
                score = a.get("relevance", a.get("score", 0))
                suggested = a.get("suggested_input", a.get("input", "—"))
                lines.append(f"| {i} | {name} | {role} | {score:.2f} | {suggested} |")

        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "god_swarm_dispatch")
    finally:
        if conn:
            conn.close()


# ── DELTA9 Fleet Intelligence Bridge ──────────────────────────────
# These tools expose the DELTA9 agent fleet data (master_index.db)
# through the MCP server for real-time case intelligence.

import os as _os
_FLEET_DB = _os.path.join(
    _os.path.dirname(_os.path.abspath(__file__)),
    "..", "..", "pipeline", "agents", "master_index.db",
)


def _fleet_conn():
    """Get read-only connection to the DELTA9 fleet database."""
    if not _os.path.exists(_FLEET_DB):
        raise db.StructuredError(
            db.ErrorCode.ERR_DB_CONNECT,
            f"Fleet DB not found: {_FLEET_DB}",
        )
    conn = sqlite3.connect(f"file:{_FLEET_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool(
    name="fleet_status",
    description="Get DELTA9 agent fleet status: file counts, atoms, judicial findings, action scores, and filing readiness.",
)
async def fleet_status() -> str:
    fconn = None
    try:
        fconn = _fleet_conn()
        files = fconn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        hashed = fconn.execute("SELECT COUNT(*) FROM files WHERE sha256 IS NOT NULL").fetchone()[0]
        atoms = fconn.execute("SELECT COUNT(*) FROM atoms").fetchone()[0]
        jf = fconn.execute("SELECT COUNT(*) FROM judicial_findings").fetchone()[0]
        scores = fconn.execute("SELECT COUNT(*) FROM action_scores").fetchone()[0]
        ready = fconn.execute("SELECT COUNT(*) FROM action_scores WHERE composite_score >= 70").fetchone()[0]

        atom_types = fconn.execute(
            "SELECT atom_type, COUNT(*) c FROM atoms GROUP BY atom_type ORDER BY c DESC"
        ).fetchall()

        lines = [
            "# DELTA9 Fleet Status",
            f"- **Files indexed**: {files:,}",
            f"- **Files hashed**: {hashed:,} ({hashed/max(files,1)*100:.1f}%)",
            f"- **Atoms**: {atoms:,}",
            f"- **Judicial findings**: {jf:,}",
            f"- **Action scores**: {scores}",
            f"- **Ready to file**: {ready}",
            "",
            "## Atom Breakdown",
        ]
        for r in atom_types:
            lines.append(f"- {r[0]}: {r[1]:,}")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "fleet_status")
    finally:
        if fconn:
            fconn.close()


@mcp.tool(
    name="fleet_damages",
    description="Get calculated damages for all legal actions across Lane A (Watson/Custody), Lane B (Shady Oaks/Housing), and Lane C (Federal §1983).",
)
async def fleet_damages() -> str:
    fconn = None
    try:
        import json as _json
        fconn = _fleet_conn()
        rows = fconn.execute(
            "SELECT action_id, lane, composite_score, damages_json FROM action_scores ORDER BY lane, action_id"
        ).fetchall()
        totals = {"A": 0.0, "B": 0.0, "C": 0.0}
        lines = ["# Damages Report\n"]
        for r in rows:
            dj = r["damages_json"]
            dmg = 0.0
            if dj:
                try:
                    dmg = _json.loads(dj).get("total_estimated", 0.0)
                except (ValueError, TypeError):
                    pass
            totals[r["lane"]] += dmg
            lines.append(
                f"- **{r['action_id']}** (Lane {r['lane']}): readiness={r['composite_score']:.1f}, damages=${dmg:,.2f}"
            )
        lines.append("")
        lines.append("## Totals")
        lines.append(f"- Lane A (Watson/Custody): ${totals['A']:,.2f}")
        lines.append(f"- Lane B (Shady Oaks/Housing): ${totals['B']:,.2f}")
        lines.append(f"- Lane C (Federal §1983): ${totals['C']:,.2f}")
        lines.append(f"- **GRAND TOTAL: ${sum(totals.values()):,.2f}**")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "fleet_damages")
    finally:
        if fconn:
            fconn.close()


@mcp.tool(
    name="fleet_ready_actions",
    description="Get all legal actions that are READY TO FILE (composite score >= 70). Shows action details, readiness, and estimated damages.",
)
async def fleet_ready_actions() -> str:
    fconn = None
    try:
        import json as _json
        fconn = _fleet_conn()
        rows = fconn.execute(
            "SELECT action_id, lane, composite_score, damages_json FROM action_scores "
            "WHERE composite_score >= 70 ORDER BY composite_score DESC"
        ).fetchall()
        if not rows:
            return "No actions currently meet the filing threshold (composite >= 70)."
        lines = [f"# {len(rows)} Actions READY TO FILE\n"]
        for r in rows:
            dmg = 0.0
            conf = "UNKNOWN"
            if r["damages_json"]:
                try:
                    d = _json.loads(r["damages_json"])
                    dmg = d.get("total_estimated", 0.0)
                    conf = d.get("confidence", "UNKNOWN")
                except (ValueError, TypeError):
                    pass
            lines.append(
                f"### {r['action_id']} — Lane {r['lane']}\n"
                f"- Readiness: **{r['composite_score']:.1f}%**\n"
                f"- Estimated damages: **${dmg:,.2f}**\n"
                f"- Confidence: {conf}\n"
            )
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "fleet_ready_actions")
    finally:
        if fconn:
            fconn.close()


@mcp.tool(
    name="fleet_judicial_intel",
    description="Get judicial intelligence findings for judges McNeill, Hoopes, and others. Shows patterns, biases, and misconduct indicators.",
)
async def fleet_judicial_intel(judge: str = "") -> str:
    fconn = None
    try:
        fconn = _fleet_conn()
        if judge:
            rows = fconn.execute(
                "SELECT judge, finding_type, description, severity, confidence "
                "FROM judicial_findings WHERE LOWER(judge) LIKE ? ORDER BY severity DESC LIMIT 50",
                (f"%{judge.lower()}%",),
            ).fetchall()
        else:
            rows = fconn.execute(
                "SELECT judge, finding_type, COUNT(*) c, AVG(severity) avg_sev "
                "FROM judicial_findings GROUP BY judge, finding_type ORDER BY c DESC LIMIT 50"
            ).fetchall()

        if not rows:
            return f"No judicial findings found{' for ' + judge if judge else ''}."

        lines = [f"# Judicial Intelligence{' — ' + judge if judge else ''}\n"]
        if judge:
            for r in rows:
                lines.append(
                    f"- **{r['finding_type']}** (severity={r['severity']:.1f}, conf={r['confidence']:.2f}): "
                    f"{str(r['description'])[:200]}"
                )
        else:
            for r in rows:
                lines.append(f"- **{r['judge']}** — {r['finding_type']}: {r['c']} findings (avg severity {r['avg_sev']:.1f})")
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "fleet_judicial_intel")
    finally:
        if fconn:
            fconn.close()


# ── NEW: Deadline / Filing / Evidence Query Tools ─────────────────

class UpcomingDeadlinesInput(BaseModel):
    """Input for querying upcoming deadlines with urgency."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    days_ahead: int = Field(
        default=30, ge=1, le=365,
        description="Number of days ahead to look for deadlines.",
    )
    trigger_event: Optional[str] = Field(
        default=None,
        description="Optional: filter by trigger event type.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class FilingSearchInput(BaseModel):
    """Input for searching filings by case, court, or type."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ..., min_length=1,
        description="Search query: case number, court name, filing type, or keyword.",
    )
    filing_type: Optional[str] = Field(
        default=None,
        description="Filter by filing type: motion, brief, order, petition, complaint, etc.",
    )
    limit: int = Field(default=25, ge=1, le=100)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


class EvidenceLookupInput(BaseModel):
    """Input for searching evidence by keyword or date."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    keyword: str = Field(
        ..., min_length=1,
        description="Keyword to search in evidence text (e.g. 'custody', 'violation', 'email').",
    )
    date_from: Optional[str] = Field(
        default=None,
        description="Filter evidence from this date (ISO YYYY-MM-DD).",
    )
    date_to: Optional[str] = Field(
        default=None,
        description="Filter evidence up to this date (ISO YYYY-MM-DD).",
    )
    limit: int = Field(default=25, ge=1, le=100)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="litigation_upcoming_deadlines",
    annotations={
        "title": "Upcoming Deadlines with Urgency",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_upcoming_deadlines(params: UpcomingDeadlinesInput) -> str:
    """Query upcoming court deadlines with urgency indicators.

    Scans all known trigger events and computes deadlines within the
    requested window, sorted by urgency (soonest first).
    """
    conn = None
    try:
        from datetime import datetime as _dt, timedelta as _td

        conn = _safe_conn()
        today = _dt.now()
        cutoff = today + _td(days=params.days_ahead)

        trigger_events = [
            "motion_filed", "order_entered", "service_completed",
            "complaint_filed", "motion_served", "hearing_scheduled",
            "discovery_request", "appeal_filed",
        ]
        if params.trigger_event:
            trigger_events = [params.trigger_event]

        all_deadlines = []
        today_str = today.strftime("%Y-%m-%d")
        for evt in trigger_events:
            try:
                dls = db.compute_deadlines(conn, evt, today_str, "MI")
                for d in dls:
                    dl_date = _dt.strptime(d["deadline"], "%Y-%m-%d")
                    if today <= dl_date <= cutoff:
                        remaining = (dl_date - today).days
                        if remaining <= 3:
                            urgency = "🔴 CRITICAL"
                        elif remaining <= 7:
                            urgency = "🟠 URGENT"
                        elif remaining <= 14:
                            urgency = "🟡 SOON"
                        else:
                            urgency = "🟢 NORMAL"
                        d["urgency"] = urgency
                        d["trigger_event"] = evt
                        d["days_remaining"] = remaining
                        all_deadlines.append(d)
            except Exception:
                continue

        all_deadlines.sort(key=lambda x: x["deadline"])

        if not all_deadlines:
            return f"No upcoming deadlines found within {params.days_ahead} days."

        lines = [
            f"# ⏰ Upcoming Deadlines (next {params.days_ahead} days)\n",
            f"**{len(all_deadlines)} deadlines found** | Today: {today_str}\n",
            "| # | Urgency | Date | Days Left | Rule | Description | Trigger |",
            "|---|---------|------|-----------|------|-------------|---------|",
        ]
        for i, d in enumerate(all_deadlines, 1):
            lines.append(
                f"| {i} | {d['urgency']} | {d['deadline']} | {d['days_remaining']} | "
                f"{d.get('rule', '?')} | {d.get('description', '?')} | {d['trigger_event']} |"
            )
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "litigation_upcoming_deadlines")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_filing_search",
    annotations={
        "title": "Search Filings by Case/Court/Type",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_filing_search(params: FilingSearchInput) -> str:
    """Search filings across ingested documents and master CSV data.

    Searches documents table, pages FTS, and master_csv_data for
    filings matching case number, court, type, or keywords.
    """
    conn = None
    try:
        conn = _safe_conn()
        results = []

        # 1. Search pages_fts for filing-related content
        fts_query = params.query
        if params.filing_type:
            fts_query = f"{params.query} AND {params.filing_type}"
        try:
            rows = conn.execute(
                """SELECT p.id, p.page_number, d.file_name, d.file_path,
                          snippet(pages_fts, 0, '>>>', '<<<', '...', 40) AS snippet,
                          rank
                   FROM pages_fts
                   JOIN pages p ON pages_fts.rowid = p.id
                   JOIN documents d ON p.document_id = d.id
                   WHERE pages_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (fts_query, params.limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "source": "document",
                    "file": r["file_name"],
                    "page": r["page_number"],
                    "path": r["file_path"],
                    "snippet": r["snippet"],
                })
        except Exception:
            pass

        # 2. Search master_csv_data for filing records
        try:
            csv_q = f"%{params.query}%"
            type_filter = ""
            type_params = [csv_q]
            if params.filing_type:
                type_filter = " AND LOWER(row_data) LIKE ?"
                type_params.append(f"%{params.filing_type.lower()}%")
            csv_rows = conn.execute(
                f"""SELECT dataset, row_data, source_file, row_number
                    FROM master_csv_data
                    WHERE row_data LIKE ?{type_filter}
                    ORDER BY id DESC
                    LIMIT ?""",
                (*type_params, params.limit),
            ).fetchall()
            for r in csv_rows:
                results.append({
                    "source": f"csv:{r['dataset']}",
                    "data": r["row_data"][:300],
                    "file": r["source_file"] or "?",
                })
        except Exception:
            pass

        if not results:
            return f"No filings found for query: '{params.query}'"

        lines = [
            f"# 📋 Filing Search: '{params.query}'\n",
            f"**{len(results)} results found**\n",
        ]
        for i, r in enumerate(results, 1):
            if r["source"] == "document":
                lines.append(
                    f"### {i}. 📄 {r['file']} (p.{r['page']})\n"
                    f"- Path: `{r['path']}`\n"
                    f"- Snippet: {r['snippet']}\n"
                )
            else:
                lines.append(
                    f"### {i}. 📊 {r['source']} — {r['file']}\n"
                    f"- Data: {r['data']}\n"
                )
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "litigation_filing_search")
    finally:
        if conn:
            conn.close()


@mcp.tool(
    name="litigation_evidence_lookup",
    annotations={
        "title": "Evidence Lookup by Keyword/Date",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def litigation_evidence_lookup(params: EvidenceLookupInput) -> str:
    """Search evidence by keyword and optional date range.

    Searches ingested PDFs, master CSV evidence index, and document
    metadata for evidence matching the keyword and date filters.
    """
    conn = None
    try:
        conn = _safe_conn()
        results = []

        # 1. FTS search in pages for evidence
        try:
            rows = conn.execute(
                """SELECT p.id, p.page_number, d.file_name, d.file_path,
                          d.modified_date,
                          snippet(pages_fts, 0, '>>>', '<<<', '...', 40) AS snippet,
                          rank
                   FROM pages_fts
                   JOIN pages p ON pages_fts.rowid = p.id
                   JOIN documents d ON p.document_id = d.id
                   WHERE pages_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (params.keyword, params.limit),
            ).fetchall()
            for r in rows:
                mod_date = r["modified_date"] or ""
                # Apply date filters if specified
                if params.date_from and mod_date and mod_date < params.date_from:
                    continue
                if params.date_to and mod_date and mod_date > params.date_to:
                    continue
                results.append({
                    "source": "document",
                    "file": r["file_name"],
                    "page": r["page_number"],
                    "path": r["file_path"],
                    "date": mod_date,
                    "snippet": r["snippet"],
                })
        except Exception:
            pass

        # 2. Search master_csv_data evidence_index dataset
        try:
            csv_params = [f"%{params.keyword}%"]
            date_filter = ""
            if params.date_from:
                date_filter += " AND row_data LIKE ?"
                csv_params.append(f"%{params.date_from[:7]}%")  # year-month match
            csv_rows = conn.execute(
                f"""SELECT dataset, row_data, source_file, row_number
                    FROM master_csv_data
                    WHERE (dataset = 'evidence_index' OR dataset LIKE '%evidence%')
                    AND row_data LIKE ?{date_filter}
                    ORDER BY id DESC
                    LIMIT ?""",
                (*csv_params, params.limit),
            ).fetchall()
            for r in csv_rows:
                results.append({
                    "source": f"csv:{r['dataset']}",
                    "data": r["row_data"][:300],
                    "file": r["source_file"] or "?",
                })
        except Exception:
            pass

        if not results:
            return f"No evidence found for keyword: '{params.keyword}'"

        date_info = ""
        if params.date_from or params.date_to:
            date_info = f" | Date range: {params.date_from or '...'} → {params.date_to or '...'}"

        lines = [
            f"# 🔍 Evidence Lookup: '{params.keyword}'{date_info}\n",
            f"**{len(results)} results found**\n",
        ]
        for i, r in enumerate(results, 1):
            if r["source"] == "document":
                lines.append(
                    f"### {i}. 📄 {r['file']} (p.{r['page']})\n"
                    f"- Date: {r.get('date', 'unknown')}\n"
                    f"- Path: `{r['path']}`\n"
                    f"- Evidence: {r['snippet']}\n"
                )
            else:
                lines.append(
                    f"### {i}. 📊 {r['source']} — {r['file']}\n"
                    f"- Data: {r['data']}\n"
                )
        return "\n".join(lines)
    except Exception as e:
        return _format_error(e, "litigation_evidence_lookup")
    finally:
        if conn:
            conn.close()


# ── Register Enhancement Tool Layers ─────────────────────────────
try:
    from .tools_v3_bridge import register_v3_tools
    register_v3_tools(mcp)
    logger.info("v3 tools registered (9 enhancement tools)")
except ImportError:
    logger.warning("tools_v3_bridge not found — v3 tools unavailable")
except Exception as e:
    logger.warning("Failed to register v3 tools: %s", e)

try:
    from .tools_v4_bridge import register_v4_tools
    register_v4_tools(mcp)
    logger.info("v4 tools registered (7 convergence & combat tools)")
except ImportError:
    logger.warning("tools_v4_bridge not found — v4 tools unavailable")
except Exception as e:
    logger.warning("Failed to register v4 tools: %s", e)


# ── Entry Point ───────────────────────────────────────────────────
def main():
    """Run MCP server via stdin/stdout (NOT a network server)."""
    mcp.run()


if __name__ == "__main__":
    main()
