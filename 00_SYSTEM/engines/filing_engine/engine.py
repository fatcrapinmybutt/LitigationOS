"""
Filing Engine — Main Entry Point
==================================

The FilingEngine is the primary interface. It:
  1. Scans for triggers (deadlines, readiness, manual)
  2. Orchestrates the pipeline for each triggered filing
  3. Tracks state across sessions (crash-resilient)
  4. Provides CLI and API access

Usage:
    engine = FilingEngine()

    # Check what needs attention
    triggers = engine.scan_triggers()

    # Run a specific filing through the pipeline
    result = engine.run("F1", case_number="2024-001507-DC", dry_run=True)

    # Get status of all active runs
    status = engine.status()
"""

import json
import logging
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Use shared module for DB access when available
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from shared import get_db, get_root, get_engine_dir, DB_REGISTRY
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False

from .state import FilingState, Phase, RunStatus
from .triggers import TriggerScanner, TriggerConfig, Trigger
from .pipeline import FilingPipeline
from .validator import FilingValidator, COURT_SPECS


def _resolve_lit_db() -> str:
    """Resolve litigation_context.db path via shared module or fallback."""
    if _HAS_SHARED:
        try:
            root = get_root()
            return str(root / DB_REGISTRY.get("litigation", "litigation_context.db"))
        except Exception as e:
            logger.debug("Shared module DB resolution failed, using fallback: %s", e)
    return str(Path(__file__).resolve().parent.parent.parent.parent / "litigation_context.db")


def _resolve_engine_db() -> str:
    """Resolve engine state DB path via shared module or fallback."""
    if _HAS_SHARED:
        try:
            return str(get_engine_dir() / "filing_engine" / "filing_engine.db")
        except Exception as e:
            logger.debug("Shared module engine DB resolution failed, using fallback: %s", e)
    return str(Path(__file__).resolve().parent / "filing_engine.db")


class FilingEngine:
    """Autonomous Court Document Preparation Engine.

    Monitors case state and automatically activates filing preparation
    when conditions are met (deadline proximity, readiness threshold,
    or manual trigger).
    """

    VERSION = "1.1.0"

    def __init__(self, db_path: Optional[str] = None,
                 lit_db_path: Optional[str] = None,
                 config: Optional[TriggerConfig] = None):
        """Initialize the Filing Engine.

        Args:
            db_path: Path to engine state database.
                     Default: filing_engine/filing_engine.db
            lit_db_path: Path to litigation database for trigger scanning.
                         Default: litigation_context.db at repo root
            config: Trigger configuration thresholds.
        """
        self.state = FilingState(db_path or _resolve_engine_db())
        self.trigger_scanner = TriggerScanner(lit_db_path or _resolve_lit_db(), config)
        self.config = config or TriggerConfig()

    def scan_triggers(self) -> list:
        """Scan for all active triggers. Returns list of Trigger objects."""
        return self.trigger_scanner.scan_all()

    def run(self, filing_id: str, case_number: str = "",
            court: str = "", court_type: str = "mi_circuit",
            dry_run: bool = True, trigger_reason: str = "manual",
            document_text: str = "",
            case_info: dict = None,
            parties_served: list = None,
            exhibits: list = None,
            signer_info: dict = None,
            output_dir: str = "",
            components: dict = None) -> dict:
        """Run a filing through the full pipeline.

        Args:
            filing_id: Filing identifier (e.g., "F1", "V2")
            case_number: Court case number
            court: Court name (display)
            court_type: Court spec key (mi_circuit, wdmi_federal, etc.)
            dry_run: If True, validate only — don't produce files
            trigger_reason: Why this run was initiated
            document_text: Main document text for validation
            case_info: Dict for caption generation
            parties_served: List of dicts for COS generation
            exhibits: List of exhibit dicts for index generation
            signer_info: Dict for signature block generation
            output_dir: Where to write assembled output
            components: Dict of component flags for validation

        Returns:
            Complete run result dict.
        """
        pipeline = FilingPipeline(self.state, court_type)
        return pipeline.run(
            filing_id=filing_id,
            case_number=case_number,
            court=court,
            dry_run=dry_run,
            trigger_reason=trigger_reason,
            document_text=document_text,
            case_info=case_info,
            parties_served=parties_served,
            exhibits=exhibits,
            signer_info=signer_info,
            output_dir=output_dir,
            components=components
        )

    def validate(self, filing_id: str, document_text: str,
                 court_type: str = "mi_circuit",
                 case_number: str = "",
                 filing_type: str = "motion",
                 pro_se: bool = True,
                 **component_flags) -> dict:
        """Quick validation without full pipeline run.

        Returns validation result dict with pass/fail and findings.
        """
        validator = FilingValidator(court_type)
        result = validator.validate_filing(
            filing_id=filing_id,
            document_text=document_text,
            case_number=case_number,
            filing_type=filing_type,
            pro_se=pro_se,
            **component_flags
        )
        return {
            "filing_id": filing_id,
            "court": result.court,
            "passed": result.passed,
            "summary": result.summary,
            "critical_failures": result.critical_failures,
            "warnings": result.warnings,
            "checks": [
                {"name": c.name, "passed": c.passed,
                 "severity": c.severity, "message": c.message,
                 "rule": c.rule, "auto_fixable": c.auto_fixable}
                for c in result.checks
            ]
        }

    def status(self) -> dict:
        """Get current engine status: active runs, recent history, triggers."""
        active = self.state.get_active_runs()
        history = self.state.get_run_history(limit=10)
        triggers = self.scan_triggers()

        return {
            "engine": "FilingEngine",
            "version": self.VERSION,
            "timestamp": datetime.now().isoformat(),
            "shared_module": _HAS_SHARED,
            "active_runs": len(active),
            "runs": active,
            "recent_history": history,
            "active_triggers": len(triggers),
            "triggers": [
                {"type": t.trigger_type, "filing": t.filing_id,
                 "urgency": t.urgency, "description": t.description}
                for t in triggers
            ],
            "courts_supported": list(COURT_SPECS.keys()),
        }

    def get_run_detail(self, run_id: int) -> dict:
        """Get detailed information about a specific run."""
        run = self.state.get_run(run_id)
        if not run:
            return {"error": f"Run {run_id} not found"}

        phases = self.state.get_phase_log(run_id)
        return {
            "run": run,
            "phase_log": phases,
        }

    def trigger_report(self) -> str:
        """Generate human-readable trigger report."""
        triggers = self.scan_triggers()
        return self.trigger_scanner.to_report(triggers)

    def close(self):
        """Close all database connections."""
        self.state.close()
        self.trigger_scanner.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
