"""Bridge: register tools_v3 functions with a FastMCP server instance.

Usage in server.py:
    from tools_v3_bridge import register_v3_tools
    register_v3_tools(mcp)   # call after mcp = FastMCP(...)

This keeps server.py clean while adding the v3 enhancement tools.
"""
import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# ── Pydantic input models (match FastMCP pattern) ───────────────────

class AdversaryThreatsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    limit: int = Field(default=20, ge=1, le=200, description="Max adversaries to return.")

class DedupDuplicatesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    drive: Optional[str] = Field(default=None, description="Filter by drive letter.")
    limit: int = Field(default=50, ge=1, le=500, description="Max duplicates to return.")

class DriveOrgLogInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    status: Optional[str] = Field(default=None, description="Filter by action status.")
    limit: int = Field(default=50, ge=1, le=500, description="Max log entries to return.")

class QueryBenchmarksInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    limit: int = Field(default=20, ge=1, le=200, description="Max benchmark entries to return.")


# ── Registration function ───────────────────────────────────────────

def register_v3_tools(mcp):
    """Register all v3 tools on the given FastMCP instance."""
    from . import tools_v3 as t3

    _RO = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }

    @mcp.tool(name="litigation_case_health", annotations={"title": "Case Health Dashboard", **_RO})
    async def _case_health() -> str:
        """Case health dashboard — quotes, harms, impeachment, contradictions, claims, deadlines."""
        return json.dumps(t3.litigation_case_health(), indent=2, default=str)

    @mcp.tool(name="litigation_adversary_threats", annotations={"title": "Adversary Threat Matrix", **_RO})
    async def _adversary_threats(params: AdversaryThreatsInput) -> str:
        """Ranked adversary threat matrix with harm counts and category spread."""
        return json.dumps(t3.litigation_adversary_threats(limit=params.limit), indent=2, default=str)

    @mcp.tool(name="litigation_filing_pipeline", annotations={"title": "Filing Pipeline Status", **_RO})
    async def _filing_pipeline() -> str:
        """Filing pipeline — every action with phase, readiness %, risk score, gaps."""
        return json.dumps(t3.litigation_filing_pipeline(), indent=2, default=str)

    @mcp.tool(name="litigation_dedup_status", annotations={"title": "Dedup Status", **_RO})
    async def _dedup_status() -> str:
        """Deduplication aggregate stats — total files, unique hashes, duplicates, drives."""
        return json.dumps(t3.litigation_dedup_status(), indent=2, default=str)

    @mcp.tool(name="litigation_dedup_duplicates", annotations={"title": "List Duplicates", **_RO})
    async def _dedup_duplicates(params: DedupDuplicatesInput) -> str:
        """List duplicate files with path, size, SHA-256, canonical ref, and action status."""
        return json.dumps(t3.litigation_dedup_duplicates(drive=params.drive, limit=params.limit), indent=2, default=str)

    @mcp.tool(name="litigation_drive_summary", annotations={"title": "Drive Summary", **_RO})
    async def _drive_summary() -> str:
        """Per-drive file summary — file count, total bytes, unique names, duplicates, status."""
        return json.dumps(t3.litigation_drive_summary(), indent=2, default=str)

    @mcp.tool(name="litigation_drive_org_log", annotations={"title": "Drive Org Log", **_RO})
    async def _drive_org_log(params: DriveOrgLogInput) -> str:
        """Drive organization action log with optional status filter."""
        return json.dumps(t3.litigation_drive_org_log(status=params.status, limit=params.limit), indent=2, default=str)

    @mcp.tool(name="litigation_query_benchmarks", annotations={"title": "Query Benchmarks", **_RO})
    async def _query_benchmarks(params: QueryBenchmarksInput) -> str:
        """Recent query performance benchmarks — name, execution time (ms), row count."""
        return json.dumps(t3.litigation_query_benchmarks(limit=params.limit), indent=2, default=str)

    @mcp.tool(name="litigation_agent_inventory", annotations={"title": "Agent Fleet Inventory", **_RO})
    async def _agent_inventory() -> str:
        """List all Copilot agents and skills with counts and file metadata."""
        return json.dumps(t3.litigation_agent_inventory(), indent=2, default=str)
