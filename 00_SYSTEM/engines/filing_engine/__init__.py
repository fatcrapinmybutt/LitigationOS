"""
Filing Engine — Autonomous Court Document Preparation System
=============================================================

LitigationOS Engine that automatically activates when conditions are met
to prepare, validate, format, and assemble court-ready filing packages.

Architecture:
    TRIGGER → SCANNER → VALIDATOR → FORMATTER → ASSEMBLER → QA → OUTPUT

Activation triggers:
    - Deadline within configurable window (default: 14 days)
    - EGCP readiness score crosses threshold (default: 65)
    - Manual invocation via CLI or API
    - New court order detected (creates response deadline)

Usage:
    from filing_engine import FilingEngine
    engine = FilingEngine()
    result = engine.run("F1", dry_run=True)

CLI:
    python -m filing_engine --filing F1 --dry-run
    python -m filing_engine --scan-triggers
    python -m filing_engine --status
"""

from pathlib import Path
import sys

# Ensure shared module is importable
_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
if str(_root / "00_SYSTEM") not in sys.path:
    sys.path.insert(0, str(_root / "00_SYSTEM"))

from .engine import FilingEngine
from .state import FilingState, Phase, RunStatus
from .triggers import TriggerScanner
from .pipeline import FilingPipeline

__version__ = "1.1.0"
__all__ = ["FilingEngine", "FilingState", "Phase", "RunStatus",
           "TriggerScanner", "FilingPipeline"]
