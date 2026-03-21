"""Bridge: register tools_v4 functions with a FastMCP server instance.

Usage in server.py:
    from tools_v4_bridge import register_v4_tools
    register_v4_tools(mcp)   # call after mcp = FastMCP(...)

Provides 7 Convergence & Combat Intelligence tools:
  1. litigation_convergence_status  — Quality score + lane readiness
  2. litigation_egcp_score          — EGCP component breakdown per lane
  3. litigation_gap_tracker         — BLOCKER/DNEW/NEXT_PATCH queries
  4. litigation_emergence_scan      — Cross-lane emergence patterns
  5. litigation_filing_priority     — Ranked filing matrix
  6. litigation_impeachment_lookup  — Impeachment package queries
  7. litigation_red_team_findings   — Adversarial vulnerability report
"""
import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Pydantic input models ───────────────────────────────────────────

class EgcpScoreInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    lane: Optional[str] = Field(
        default=None,
        description="Case lane to score: 'A_CUSTODY', 'B_HOUSING', 'C_FEDERAL', "
                    "'D_PPO', 'E_MISCONDUCT', or 'F_APPELLATE'. Omit for all lanes.",
    )


class GapTrackerInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    gap_type: Optional[str] = Field(
        default=None,
        description="Gap classification: 'BLOCKER', 'DNEW', or 'NEXT_PATCH'. Omit for all.",
    )
    lane: Optional[str] = Field(
        default=None,
        description="Case lane filter (e.g., 'A_CUSTODY'). Omit for all lanes.",
    )
    severity: Optional[str] = Field(
        default=None,
        description="Severity filter: 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'. Omit for all.",
    )
    status: Optional[str] = Field(
        default=None,
        description="Resolution status: 'OPEN', 'MITIGATED', 'ACKNOWLEDGED', 'RESOLVED'. Omit for all.",
    )
    limit: int = Field(default=50, ge=1, le=200, description="Maximum gaps to return.")


class EmergenceScanInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    signal_type: Optional[str] = Field(
        default=None,
        description="Emergence signal type: 'CROSS_GRAPH', 'CHAIN_COMPLETE', "
                    "'CONTRADICTION', 'NOVEL_STRATEGY', or 'WITNESS_OVERLAP'. Omit for all.",
    )
    min_novelty: int = Field(
        default=1, ge=1, le=10,
        description="Minimum novelty score (1-10). Events below this threshold are excluded. "
                    "Use 7+ for only high-significance events.",
    )
    limit: int = Field(default=30, ge=1, le=100, description="Maximum events to return.")


class FilingPriorityInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    lane: Optional[str] = Field(
        default=None,
        description="Filter to a specific lane. Omit for the full priority matrix.",
    )
    limit: int = Field(default=20, ge=1, le=50, description="Maximum filings to return.")


class ImpeachmentLookupInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    target: Optional[str] = Field(
        default=None,
        description="Impeachment target name (partial match, e.g., 'Watson'). Omit for all targets.",
    )
    lane: Optional[str] = Field(
        default=None,
        description="Case lane filter (e.g., 'A_CUSTODY'). Omit for all lanes.",
    )
    severity: Optional[str] = Field(
        default=None,
        description="Severity filter: 'critical', 'high', 'medium'. Omit for all.",
    )
    limit: int = Field(default=50, ge=1, le=200, description="Maximum packages to return.")


class RedTeamFindingsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    severity: Optional[str] = Field(
        default=None,
        description="Severity filter: 'CRITICAL', 'HIGH', or 'MEDIUM'. Omit for all.",
    )
    lane: Optional[str] = Field(
        default=None,
        description="Affected lane filter (e.g., 'A_CUSTODY', 'ALL'). Omit for all.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Attack category (e.g., 'Judicial Immunity', 'Hearsay', 'Standing'). Omit for all.",
    )
    limit: int = Field(default=30, ge=1, le=100, description="Maximum findings to return.")


class LegalSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(description="Search terms (FTS5 syntax: AND, OR, NOT, phrases).")
    source_type: Optional[str] = Field(
        default=None,
        description="Filter: 'MCR', 'MCL', 'MRE', 'CASE', 'CANON'. Omit for all.",
    )
    limit: int = Field(default=25, ge=1, le=100, description="Maximum results to return.")


class AuthorityLookupInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    authority_type: str = Field(description="One of 'MCR', 'MCL', 'MRE', 'CASE'.")
    authority_number: str = Field(description="Identifier (e.g. 'MCR 2.119', 'MCL 722.23').")


class FilingAuthoritiesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    filing_id: str = Field(description="Filing identifier (e.g. 'F1', 'F3', 'F5').")


# ── Registration function ───────────────────────────────────────────

def register_v4_tools(mcp):
    """Register all v4 Convergence & Combat Intelligence tools."""
    from . import tools_v4 as t4

    _RO = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }

    # ── Tool 1: Convergence Status ──────────────────────────────────

    @mcp.tool(
        name="litigation_convergence_status",
        annotations={"title": "Convergence Quality Status", **_RO},
    )
    async def _convergence_status() -> str:
        """Current convergence quality score (0-100), lane readiness, gap counts, and cycle mode.

        Returns overall quality score, per-lane EGCP scores, blocker/DNEW/NEXT_PATCH
        counts, emergence event count, and whether the system is COURTROOM_READY,
        NEAR_READY, IN_PROGRESS, or CRITICAL.
        """
        return json.dumps(t4.litigation_convergence_status(), indent=2, default=str)

    # ── Tool 2: EGCP Score ──────────────────────────────────────────

    @mcp.tool(
        name="litigation_egcp_score",
        annotations={"title": "EGCP Lane Scores", **_RO},
    )
    async def _egcp_score(params: EgcpScoreInput) -> str:
        """EGCP (Evidence/Grounds/Citations/Presentation) scores per lane.

        Each component scored 0-25, total 0-100. Scores ≥65 = filing ready.
        Scores <50 = critical gaps. Returns component breakdown and readiness status.
        """
        return json.dumps(
            t4.litigation_egcp_score(lane=params.lane), indent=2, default=str
        )

    # ── Tool 3: Gap Tracker ─────────────────────────────────────────

    @mcp.tool(
        name="litigation_gap_tracker",
        annotations={"title": "Convergence Gap Tracker", **_RO},
    )
    async def _gap_tracker(params: GapTrackerInput) -> str:
        """Query convergence gaps: BLOCKERs preventing filing, DNEW discoveries, deferred patches.

        Gaps are prioritized by severity (CRITICAL→HIGH→MEDIUM→LOW). BLOCKER items
        must be resolved before any filing proceeds. Filter by type, lane, severity, or status.
        """
        return json.dumps(
            t4.litigation_gap_tracker(
                gap_type=params.gap_type,
                lane=params.lane,
                severity=params.severity,
                status=params.status,
                limit=params.limit,
            ),
            indent=2,
            default=str,
        )

    # ── Tool 4: Emergence Scanner ───────────────────────────────────

    @mcp.tool(
        name="litigation_emergence_scan",
        annotations={"title": "Cross-Lane Emergence Scanner", **_RO},
    )
    async def _emergence_scan(params: EmergenceScanInput) -> str:
        """Detect cross-lane emergence patterns: entity overlap, authority completion,
        contradictions, novel strategies, and witness overlap.

        Novelty scores 7-10 indicate significant strategic opportunities requiring
        immediate attorney review. Returns events sorted by novelty (highest first).
        """
        return json.dumps(
            t4.litigation_emergence_scan(
                signal_type=params.signal_type,
                min_novelty=params.min_novelty,
                limit=params.limit,
            ),
            indent=2,
            default=str,
        )

    # ── Tool 5: Filing Priority ─────────────────────────────────────

    @mcp.tool(
        name="litigation_filing_priority",
        annotations={"title": "Filing Priority Matrix", **_RO},
    )
    async def _filing_priority(params: FilingPriorityInput) -> str:
        """Ranked filing priority matrix combining EGCP scores, urgency, impeachment
        support, and red team vulnerabilities.

        Returns filings sorted by composite priority score. Each entry includes
        lane, EGCP score, urgency level, impeachment support count, critical
        vulnerabilities, and READY/DEVELOPING status.
        """
        return json.dumps(
            t4.litigation_filing_priority(lane=params.lane, limit=params.limit),
            indent=2,
            default=str,
        )

    # ── Tool 6: Impeachment Lookup ──────────────────────────────────

    @mcp.tool(
        name="litigation_impeachment_lookup",
        annotations={"title": "Impeachment Package Lookup", **_RO},
    )
    async def _impeachment_lookup(params: ImpeachmentLookupInput) -> str:
        """Query assembled impeachment packages for cross-examination and motion support.

        Each package contains prior inconsistent statements, documented contradictions,
        and evidence mapped to MRE rules. Filter by target name, lane, or severity.
        """
        return json.dumps(
            t4.litigation_impeachment_lookup(
                target=params.target,
                lane=params.lane,
                severity=params.severity,
                limit=params.limit,
            ),
            indent=2,
            default=str,
        )

    # ── Tool 7: Red Team Findings ───────────────────────────────────

    @mcp.tool(
        name="litigation_red_team_findings",
        annotations={"title": "Red Team Vulnerability Report", **_RO},
    )
    async def _red_team_findings(params: RedTeamFindingsInput) -> str:
        """Adversarial vulnerabilities opposing counsel would exploit.

        Each finding includes attack vector, severity, affected lane, and
        recommended mitigation. CRITICAL findings must be addressed before filing.
        Sorted by severity (CRITICAL first).
        """
        return json.dumps(
            t4.litigation_red_team_findings(
                severity=params.severity,
                lane=params.lane,
                category=params.category,
                limit=params.limit,
            ),
            indent=2,
            default=str,
        )

    # ── Tool 8: Legal Knowledge Search ──────────────────────────────

    @mcp.tool(
        name="litigation_legal_search",
        annotations={"title": "Legal Knowledge FTS5 Search", **_RO},
    )
    async def _legal_search(params: LegalSearchInput) -> str:
        """Full-text search across all Michigan legal knowledge — MCR rules,
        MCL statutes, MRE evidence rules, case law, and judicial canons.
        Supports FTS5 syntax: AND, OR, NOT, and quoted phrases.
        """
        return json.dumps(
            t4.litigation_legal_search(
                query=params.query,
                source_type=params.source_type,
                limit=params.limit,
            ),
            indent=2,
            default=str,
        )

    # ── Tool 9: Authority Lookup ────────────────────────────────────

    @mcp.tool(
        name="litigation_authority_lookup",
        annotations={"title": "Legal Authority Lookup", **_RO},
    )
    async def _authority_lookup(params: AuthorityLookupInput) -> str:
        """Look up a specific Michigan legal authority — court rule, statute,
        evidence rule, or case — with full text and cross-references.
        """
        return json.dumps(
            t4.litigation_authority_lookup(
                authority_type=params.authority_type,
                authority_number=params.authority_number,
            ),
            indent=2,
            default=str,
        )

    # ── Tool 10: Filing Authorities ─────────────────────────────────

    @mcp.tool(
        name="litigation_filing_authorities",
        annotations={"title": "Filing Required Authorities", **_RO},
    )
    async def _filing_authorities(params: FilingAuthoritiesInput) -> str:
        """Get all legal authorities required for a specific filing (F1-F10),
        grouped by type (MCR/MCL/MRE/CASE) with mandatory/optional status.
        """
        return json.dumps(
            t4.litigation_filing_authorities(filing_id=params.filing_id),
            indent=2,
            default=str,
        )
