"""
Filing Engine Pipeline — Full Orchestration
=============================================

Orchestrates the complete filing preparation pipeline:
    TRIGGER → SCAN → VALIDATE → FORMAT → ASSEMBLE → QA → OUTPUT

Each phase is a method that can be run independently or as part
of the full pipeline. State is tracked in FilingState DB.

Template Integration:
    Uses modules from 00_SYSTEM/templates/filing_framework/ for:
    - Caption generation (caption_generator)
    - Certificate of Service (cos_generator)
    - Signature blocks (signature_block)
    - Exhibit indexing (exhibit_indexer)
    - Format specs (michigan_format_specs)
    - Filing checklists (filing_checklist)
    - Deadline calculation (deadline_calculator)
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from .state import FilingState, Phase, RunStatus
from .validator import FilingValidator, ValidationResult

logger = logging.getLogger("filing_engine.pipeline")

# --- Wire in the filing_framework templates ---
_FRAMEWORK_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "filing_framework"
if str(_FRAMEWORK_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_DIR.parent))

from filing_framework.caption_generator import generate_caption
from filing_framework.cos_generator import generate_cos
from filing_framework.signature_block import generate_signature
from filing_framework.exhibit_indexer import (
    generate_exhibit_index, generate_exhibit_list_markdown,
)
from filing_framework.michigan_format_specs import get_specs
from filing_framework.filing_checklist import generate_checklist
from filing_framework.deadline_calculator import calculate_deadline


class FilingPipeline:
    """Full filing preparation pipeline."""

    def __init__(self, state: Optional[FilingState] = None,
                 court_type: str = "mi_circuit"):
        self.state = state or FilingState()
        self.validator = FilingValidator(court_type)
        self.court_type = court_type

    def run(self, filing_id: str, case_number: str = "",
            court: str = "", dry_run: bool = True,
            trigger_reason: str = "manual",
            document_text: str = "",
            case_info: dict = None,
            parties_served: list = None,
            exhibits: list = None,
            signer_info: dict = None,
            output_dir: str = "",
            components: dict = None) -> dict:
        """Execute the full filing pipeline.

        Args:
            filing_id: Filing identifier (e.g., "F1", "V2")
            case_number: Court case number
            court: Court name
            dry_run: If True, validate only — don't produce output
            trigger_reason: Why this run was initiated
            document_text: Main document text for validation
            case_info: Dict for caption generation:
                {case_number, court, county, judge, plaintiff, defendant}
            parties_served: List of dicts for COS:
                [{name, address, via, email}]
            exhibits: List of exhibit dicts:
                [{label, title, path, bates_start, bates_end, page_count}]
            signer_info: Dict for signature block:
                {name, address, city_state_zip, phone, email, pro_se}
            output_dir: Where to write assembled output (default: 05_FILINGS/)
            components: Dict of component flags:
                {has_cos, has_proposed_order, has_caption,
                 has_signature, has_exhibits, has_toc,
                 has_authority_index, page_count, filing_type,
                 pro_se}

        Returns:
            Dict with run results, validation, and output paths.
        """
        components = components or {}
        case_info = case_info or {}
        parties_served = parties_served or []
        exhibits = exhibits or []
        signer_info = signer_info or {}

        # Store assembly inputs for later phases
        self._assembly_ctx = {
            "case_info": case_info,
            "parties_served": parties_served,
            "exhibits": exhibits,
            "signer_info": signer_info,
            "document_text": document_text,
            "filing_id": filing_id,
            "output_dir": output_dir,
        }

        run_id = self.state.start_run(
            filing_id, case_number, court, dry_run, trigger_reason
        )

        result = {
            "run_id": run_id,
            "filing_id": filing_id,
            "dry_run": dry_run,
            "started_at": datetime.now().isoformat(),
            "phases": {},
        }

        try:
            # Phase 1: SCANNING
            scan_result = self._phase_scan(run_id, filing_id, document_text)
            result["phases"]["scan"] = scan_result

            # Phase 2: VALIDATING
            validation = self._phase_validate(
                run_id, filing_id, document_text,
                case_number=case_number, **components
            )
            result["phases"]["validate"] = {
                "summary": validation.summary,
                "passed": validation.passed,
                "critical_failures": validation.critical_failures,
                "warnings": validation.warnings,
                "checks": [
                    {"name": c.name, "passed": c.passed,
                     "severity": c.severity, "message": c.message,
                     "rule": c.rule}
                    for c in validation.checks
                ]
            }

            if not validation.passed:
                result["status"] = "VALIDATION_FAILED"
                result["message"] = (
                    f"{validation.critical_failures} critical failures — "
                    f"resolve before filing"
                )
                if dry_run:
                    self.state.finish_run(run_id, json.dumps(result, default=str))
                    result["finished_at"] = datetime.now().isoformat()
                    return result

            # Phase 3: FORMATTING
            format_result = self._phase_format(run_id, filing_id)
            result["phases"]["format"] = format_result

            # Phase 4: ASSEMBLING
            if not dry_run:
                assemble_result = self._phase_assemble(run_id, filing_id)
                result["phases"]["assemble"] = assemble_result

            # Phase 5: QA
            qa_result = self._phase_qa(run_id, filing_id, validation)
            result["phases"]["qa"] = qa_result

            # Phase 6: OUTPUT
            if not dry_run:
                output_result = self._phase_output(run_id, filing_id)
                result["phases"]["output"] = output_result

            # Complete
            result["status"] = "COMPLETE" if not dry_run else "DRY_RUN_COMPLETE"
            result["message"] = (
                f"Filing {filing_id} — "
                f"{'dry run complete' if dry_run else 'assembled and ready'}"
            )
            self.state.finish_run(run_id, json.dumps(result, default=str))

        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            self.state.fail_run(run_id, Phase.FAILED, str(e))

        result["finished_at"] = datetime.now().isoformat()
        return result

    def _phase_scan(self, run_id: int, filing_id: str,
                    document_text: str) -> dict:
        """Phase 1: Scan for available components."""
        start = time.time()
        self.state.advance_phase(run_id, Phase.SCANNING,
                                "Scanning filing components")

        ctx = getattr(self, "_assembly_ctx", {})
        inventory = {
            "document_present": bool(document_text),
            "document_length": len(document_text),
            "word_count": len(document_text.split()) if document_text else 0,
            "has_case_info": bool(ctx.get("case_info")),
            "has_parties_served": bool(ctx.get("parties_served")),
            "has_exhibits": bool(ctx.get("exhibits")),
            "exhibit_count": len(ctx.get("exhibits", [])),
            "has_signer_info": bool(ctx.get("signer_info")),
        }

        # Generate checklist for this filing type
        filing_type = (ctx.get("case_info") or {}).get("filing_type", "motion")
        try:
            checklist = generate_checklist(filing_type, self.court_type)
            inventory["checklist_items"] = len(checklist)
            inventory["checklist_type"] = filing_type
        except Exception as e:
            logger.warning(f"Checklist generation failed for {filing_type}: {e}")
            inventory["checklist_items"] = 0

        elapsed = int((time.time() - start) * 1000)
        self.state.complete_phase(run_id, Phase.SCANNING,
                                 f"Scanned: {inventory['word_count']} words, "
                                 f"{inventory['exhibit_count']} exhibits",
                                 elapsed)
        return inventory

    def _phase_validate(self, run_id: int, filing_id: str,
                        document_text: str, **kwargs) -> ValidationResult:
        """Phase 2: Run MCR/FRCP compliance validation."""
        start = time.time()
        self.state.advance_phase(run_id, Phase.VALIDATING,
                                "Running compliance checks")

        result = self.validator.validate_filing(
            filing_id=filing_id,
            document_text=document_text,
            **kwargs
        )

        for check in result.checks:
            self.state.add_qa_finding(
                run_id, check.name, check.passed,
                check.severity, check.message, check.rule,
                check.auto_fixable
            )

        elapsed = int((time.time() - start) * 1000)
        self.state.complete_phase(run_id, Phase.VALIDATING,
                                 result.summary, elapsed)
        return result

    def _phase_format(self, run_id: int, filing_id: str) -> dict:
        """Phase 3: Apply court-specific formatting via template specs."""
        start = time.time()
        self.state.advance_phase(run_id, Phase.FORMATTING,
                                "Applying court formatting")

        specs = get_specs(self.court_type)

        format_result = {
            "court": specs.get("court_name", self.court_type),
            "font": specs.get("font", "12pt"),
            "margins": specs.get("margins", "1 inch"),
            "spacing": specs.get("line_spacing", "double"),
            "page_limit": specs.get("page_limit", "N/A"),
            "authority": specs.get("authority", ""),
            "applied": True,
        }

        elapsed = int((time.time() - start) * 1000)
        self.state.complete_phase(run_id, Phase.FORMATTING,
                                 f"Formatted for {format_result['court']}",
                                 elapsed)
        return format_result

    def _phase_assemble(self, run_id: int, filing_id: str) -> dict:
        """Phase 4: Assemble filing package using template modules.

        Generates: caption, COS, signature block, exhibit index,
        and writes assembled markdown to the output directory.
        """
        start = time.time()
        self.state.advance_phase(run_id, Phase.ASSEMBLING,
                                "Assembling filing package")

        ctx = getattr(self, "_assembly_ctx", {})
        generated = []
        sections = {}

        # 1. Generate caption
        case_info = ctx.get("case_info", {})
        if case_info:
            doc_title = case_info.pop("document_title", filing_id)
            try:
                caption_text = generate_caption(
                    case_info, doc_title, court_type=self.court_type
                )
                sections["caption"] = caption_text
                generated.append("caption")
            except Exception as e:
                logger.error(f"Caption generation failed: {e}", exc_info=True)
                sections["caption_error"] = str(e)

        # 2. Generate Certificate of Service
        parties = ctx.get("parties_served", [])
        if parties:
            signer = ctx.get("signer_info", {})
            try:
                cos_text = generate_cos(
                    parties_served=parties,
                    method="electronic",
                    filer_name=signer.get("name", ""),
                )
                sections["certificate_of_service"] = cos_text
                generated.append("cos")
            except Exception as e:
                logger.error(f"COS generation failed: {e}", exc_info=True)
                sections["cos_error"] = str(e)

        # 3. Generate signature block
        signer_info = ctx.get("signer_info", {})
        if signer_info:
            try:
                sig_text = generate_signature(signer_info)
                sections["signature_block"] = sig_text
                generated.append("signature")
            except Exception as e:
                logger.error(f"Signature block generation failed: {e}", exc_info=True)
                sections["signature_error"] = str(e)

        # 4. Generate exhibit index
        exhibits = ctx.get("exhibits", [])
        if exhibits:
            try:
                exhibit_index = generate_exhibit_index(exhibits)
                exhibit_md = generate_exhibit_list_markdown(exhibits)
                sections["exhibit_index"] = exhibit_index
                sections["exhibit_list_markdown"] = exhibit_md
                generated.append(f"exhibits ({len(exhibits)})")
            except Exception as e:
                logger.error(f"Exhibit index generation failed: {e}", exc_info=True)
                sections["exhibit_error"] = str(e)

        # 5. Assemble full document markdown
        doc_text = ctx.get("document_text", "")
        assembled_parts = []
        if "caption" in sections:
            assembled_parts.append(sections["caption"])
        if doc_text:
            assembled_parts.append(doc_text)
        if "exhibit_index" in sections:
            assembled_parts.append("\n\nEXHIBIT INDEX\n" + sections["exhibit_index"])
        if "certificate_of_service" in sections:
            assembled_parts.append("\n\n" + sections["certificate_of_service"])
        if "signature_block" in sections:
            assembled_parts.append("\n\n" + sections["signature_block"])

        assembled_text = "\n\n".join(assembled_parts)
        sections["assembled_length"] = len(assembled_text)
        sections["assembled_word_count"] = len(assembled_text.split())

        # 6. Write to output directory
        output_dir = ctx.get("output_dir", "")
        output_path = None
        if output_dir and assembled_text:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            output_path = out / f"{filing_id}_assembled.md"
            output_path.write_text(assembled_text, encoding="utf-8")
            generated.append(f"written → {output_path}")

        assemble_result = {
            "components_generated": generated,
            "assembled": bool(assembled_text),
            "assembled_length": len(assembled_text),
            "output_path": str(output_path) if output_path else None,
            "sections": list(sections.keys()),
        }

        # Record components in state DB
        for comp in generated:
            self.state.add_component(run_id, comp, "generated")

        elapsed = int((time.time() - start) * 1000)
        self.state.complete_phase(
            run_id, Phase.ASSEMBLING,
            f"Assembled: {len(generated)} components, "
            f"{len(assembled_text)} chars", elapsed
        )
        return assemble_result

    def _phase_qa(self, run_id: int, filing_id: str,
                  validation: ValidationResult) -> dict:
        """Phase 5: Final QA sweep."""
        start = time.time()
        self.state.advance_phase(run_id, Phase.QA, "Final QA sweep")

        qa_result = {
            "total_checks": len(validation.checks),
            "passed": sum(1 for c in validation.checks if c.passed),
            "failed": sum(1 for c in validation.checks if not c.passed),
            "auto_fixable": sum(1 for c in validation.checks
                               if not c.passed and c.auto_fixable),
            "go_no_go": "GO" if validation.passed else "NO-GO",
        }

        elapsed = int((time.time() - start) * 1000)
        self.state.complete_phase(run_id, Phase.QA,
                                 f"QA: {qa_result['go_no_go']}", elapsed)
        return qa_result

    def _phase_output(self, run_id: int, filing_id: str) -> dict:
        """Phase 6: Generate final output and filing manifest."""
        start = time.time()
        self.state.advance_phase(run_id, Phase.OUTPUT,
                                "Generating output package")

        ctx = getattr(self, "_assembly_ctx", {})
        output_dir = ctx.get("output_dir", "")
        filing_id = ctx.get("filing_id", filing_id)

        manifest = {
            "filing_id": filing_id,
            "court_type": self.court_type,
            "generated_at": datetime.now().isoformat(),
            "format_specs": get_specs(self.court_type),
        }

        output_files = []
        if output_dir:
            out = Path(output_dir)
            # Write manifest
            manifest_path = out / f"{filing_id}_manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, default=str), encoding="utf-8"
            )
            output_files.append(str(manifest_path))

            # Collect any assembled files
            for f in out.glob(f"{filing_id}_*"):
                if str(f) not in output_files:
                    output_files.append(str(f))

        output_result = {
            "status": "COMPLETE",
            "output_dir": output_dir or None,
            "output_files": output_files,
            "file_count": len(output_files),
            "manifest": manifest,
        }

        elapsed = int((time.time() - start) * 1000)
        self.state.complete_phase(
            run_id, Phase.OUTPUT,
            f"Output: {len(output_files)} files to {output_dir or 'N/A'}",
            elapsed
        )
        return output_result
