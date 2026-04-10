"""
Centralized path resolution for LitigationOS.

All paths respect environment variable overrides for portability.
Default paths match the canonical LitigationOS deployment on Windows.
"""

import os
import functools
from pathlib import Path

# ---------------------------------------------------------------------------
# Root path — the SINGLE source of truth for LitigationOS location
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def get_root() -> Path:
    """Return the LitigationOS root directory.

    Resolution order:
      1. LITIGOS_ROOT environment variable (highest priority)
      2. Path-based inference from this file's location (portable)
      3. Hardcoded fallback (last resort)

    Returns:
        Path to LitigationOS root.

    Raises:
        LitigationDBError: If the resolved path does not exist.
    """
    from .db import LitigationDBError

    # 1. Environment variable
    env_root = os.environ.get("LITIGOS_ROOT")
    if env_root:
        p = Path(env_root)
        if p.exists():
            return p

    # 2. Infer from file location: internal/ -> shared/ -> 00_SYSTEM/ -> repo
    inferred = Path(__file__).resolve().parents[3]
    if (inferred / "_CANON.md").exists():
        return inferred

    # 3. Hardcoded fallback (last resort — only works on dev machine)
    fallback = Path(r"C:\Users\andre\LitigationOS")
    if not fallback.exists():
        raise LitigationDBError(
            f"LitigationOS root not found. Tried: env LITIGOS_ROOT, "
            f"inferred {inferred}, fallback {fallback}. "
            f"Set LITIGOS_ROOT environment variable."
        )
    return fallback


@functools.lru_cache(maxsize=1)
def get_brain_dir() -> Path:
    """Return the brains directory (00_SYSTEM/brains/)."""
    return get_root() / "00_SYSTEM" / "brains"


@functools.lru_cache(maxsize=1)
def get_engine_dir() -> Path:
    """Return the engines directory (00_SYSTEM/engines/)."""
    return get_root() / "00_SYSTEM" / "engines"


@functools.lru_cache(maxsize=1)
def get_tools_dir() -> Path:
    """Return the tools directory (00_SYSTEM/tools/)."""
    return get_root() / "00_SYSTEM" / "tools"


# ---------------------------------------------------------------------------
# Database registry — maps logical names to paths relative to root
# ---------------------------------------------------------------------------

DB_REGISTRY: dict[str, str] = {
    # Primary
    "litigation": "litigation_context.db",

    # Brain databases
    "authority_brain": "00_SYSTEM/brains/authority_brain.db",
    "narrative_brain": "00_SYSTEM/brains/narrative_brain.db",
    "entity_brain": "00_SYSTEM/brains/entity_brain.db",
    "claims_brain": "00_SYSTEM/brains/claims_brain.db",
    "interpretation_brain": "00_SYSTEM/brains/interpretation_brain.db",
    "chat_intelligence_brain": "00_SYSTEM/brains/chat_intelligence_brain.db",
    "contradictions": "00_SYSTEM/brains/contradictions.db",
    "shadyoaks_brain": "00_SYSTEM/brains/shadyoaks_brain.db",

    # Pipeline
    "pipeline": "00_SYSTEM/pipeline/pipeline.db",

    # Skill index
    "skill_index": "00_SYSTEM/engines/skill_index.db",
}

# Extended registry entries for brain databases discovered during audit
DB_REGISTRY.update({
    "filing_engine": "00_SYSTEM/engines/filing_engine/filing_engine.db",
    "failsafe_incidents": "00_SYSTEM/failsafe_incidents.db",
    "evidence_checkpoint": "00_SYSTEM/evidence_checkpoint.db",
    "file_catalog": "00_SYSTEM/file_catalog.db",
})


@functools.lru_cache(maxsize=1)
def get_filing_dir() -> Path:
    """Return the filings directory (05_FILINGS/)."""
    return get_root() / "05_FILINGS"


@functools.lru_cache(maxsize=1)
def get_evidence_dir() -> Path:
    """Return the evidence directory (01_EVIDENCE/)."""
    return get_root() / "01_EVIDENCE"


@functools.lru_cache(maxsize=1)
def get_analysis_dir() -> Path:
    """Return the analysis directory (04_ANALYSIS/)."""
    return get_root() / "04_ANALYSIS"


@functools.lru_cache(maxsize=1)
def get_workspace_dir() -> Path:
    """Return the workspace directory (12_WORKSPACE/)."""
    return get_root() / "12_WORKSPACE"


@functools.lru_cache(maxsize=1)
def get_archive_dir() -> Path:
    """Return the archive directory (11_ARCHIVES/)."""
    return get_root() / "11_ARCHIVES"


@functools.lru_cache(maxsize=1)
def get_data_dir() -> Path:
    """Return the data directory (06_DATA/)."""
    return get_root() / "06_DATA"


# Canonical directory map (matches _CANON.md)
CANON_DIRS: dict[str, str] = {
    "system": "00_SYSTEM",
    "evidence": "01_EVIDENCE",
    "authority": "02_AUTHORITY",
    "court": "03_COURT",
    "analysis": "04_ANALYSIS",
    "filings": "05_FILINGS",
    "data": "06_DATA",
    "code": "07_CODE",
    "media": "08_MEDIA",
    "reference": "09_REFERENCE",
    "external": "10_EXTERNAL",
    "archives": "11_ARCHIVES",
    "workspace": "12_WORKSPACE",
}


@functools.lru_cache(maxsize=16)
def get_canon_dir(name: str) -> Path:
    """Resolve a canonical directory name to its path.

    Args:
        name: Canonical name (e.g., 'evidence', 'filings', 'archives')

    Returns:
        Path to the canonical directory.

    Raises:
        LitigationDBError if name is unknown.
    """
    from .db import LitigationDBError
    if name not in CANON_DIRS:
        raise LitigationDBError(
            f"Unknown canonical directory: '{name}'. "
            f"Known: {', '.join(sorted(CANON_DIRS.keys()))}"
        )
    return get_root() / CANON_DIRS[name]
