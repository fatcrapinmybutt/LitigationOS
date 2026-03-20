"""Filing Wizard — Guided filing workflow with compliance gates.

Walks the user through a step-by-step process to prepare and file
court documents: select type --> choose court --> select docs --> compliance
check --> GO/NO-GO gate --> generate PDFs --> filing instructions.

Wired to: FilingEngine, CourtRulesEngine (prefiling QA + efiling prep).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from litigationos.gui.widgets import COLORS

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# Engine imports -- graceful fallback
try:
    from litigationos.engines.filing import FilingEngine, FilingStack, ValidationResult
    _HAS_FILING_ENGINE = True
except ImportError:
    _HAS_FILING_ENGINE = False

try:
    from litigationos.engines.court_rules import CourtRulesEngine
    _HAS_RULES_ENGINE = True
except ImportError:
    _HAS_RULES_ENGINE = False

try:
    from litigationos.engines.evidence import EvidenceEngine
    _HAS_EVIDENCE_ENGINE = True
except ImportError:
    _HAS_EVIDENCE_ENGINE = False

_STEPS = [
    "Select Filing Type",
    "Choose Court & Case",
    "Select Documents",
    "Compliance Check",
    "Generate PDFs",
    "Service Packet",
    "Filing Instructions",
]

_FILING_TYPES = [
    "Motion to Disqualify Judge",
    "Appellate Brief (COA)",
    "Original Action (MSC)",
    "Tort Complaint",
    "Federal 1983 Action",
    "Emergency Motion",
]


class FilingWizardFrame(ctk.CTkFrame):
    """Step-by-step wizard for preparing and filing court documents."""

    def __init__(
        self,
        parent,
        db: "DatabaseManager",
        navigate_cb=None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb
        self._current_step = 0
        self._selected_type: Optional[str] = None
        self._selected_case_id: Optional[int] = None
        self._selected_court: str = "circuit"
        self._validation_result: Optional[dict] = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
        )
        self._scroll.pack(fill="both", expand=True)

        # Header
        hdr = ctk.CTkFrame(self._scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        hdr.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            hdr,
            text="📝  FILING WIZARD",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=16, pady=12)

        # Progress bar
        prog_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        prog_frame.pack(fill="x", padx=16, pady=(4, 0))

        self._progress = ctk.CTkProgressBar(prog_frame, height=14, corner_radius=6)
        self._progress.pack(fill="x", pady=4)
        self._progress.set(0)

        self._step_label = ctk.CTkLabel(
            prog_frame,
            text=f"Step 1 of {len(_STEPS)}: {_STEPS[0]}",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_dim"],
        )
        self._step_label.pack(anchor="w")

        # Content area
        self._content = ctk.CTkFrame(
            self._scroll, fg_color=COLORS["bg_card"], corner_radius=10,
        )
        self._content.pack(fill="both", expand=True, padx=16, pady=8)

        self._render_step()

        # Navigation
        nav = ctk.CTkFrame(self._scroll, fg_color="transparent")
        nav.pack(fill="x", padx=16, pady=(4, 16))

        self._back_btn = ctk.CTkButton(
            nav, text="← Back", width=100, command=self._prev_step,
            fg_color=COLORS["bg_card"], hover_color=COLORS["accent"],
            state="disabled", corner_radius=8,
        )
        self._back_btn.pack(side="left", padx=4)

        self._next_btn = ctk.CTkButton(
            nav, text="Next →", width=100, command=self._next_step,
            fg_color=COLORS["blue"], hover_color=COLORS["accent"], corner_radius=8,
        )
        self._next_btn.pack(side="left", padx=4)

    # ------------------------------------------------------------------
    # Step rendering
    # ------------------------------------------------------------------

    def _render_step(self):
        for w in self._content.winfo_children():
            w.destroy()

        if self._current_step == 0:
            self._render_filing_type_selector()
        elif self._current_step == 1:
            self._render_court_case_selector()
        elif self._current_step == 2:
            self._render_document_selector()
        elif self._current_step == 3:
            self._render_compliance_check()
        elif self._current_step == 4:
            self._render_go_nogo_gate()
        elif self._current_step == 5:
            self._render_service_packet()
        elif self._current_step == 6:
            self._render_filing_instructions()

    def _render_filing_type_selector(self):
        ctk.CTkLabel(
            self._content,
            text="Select Filing Type",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=16, pady=(16, 8))

        for ft in _FILING_TYPES:
            ctk.CTkButton(
                self._content,
                text=ft,
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["accent"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=14),
                height=40,
                corner_radius=8,
                command=lambda t=ft: self._select_type(t),
            ).pack(fill="x", padx=16, pady=2)

    def _render_court_case_selector(self):
        """Step 2: Choose court and case from DB."""
        ctk.CTkLabel(
            self._content,
            text="Choose Court & Case",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=16, pady=(16, 8))

        # Court selector
        court_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        court_frame.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(court_frame, text="Court:", text_color=COLORS["text"]).pack(side="left", padx=4)
        courts = ["circuit", "coa", "supreme"]
        for ct in courts:
            btn_fg = COLORS["blue"] if ct == self._selected_court else "transparent"
            ctk.CTkButton(
                court_frame, text=ct.upper(), width=80,
                fg_color=btn_fg, hover_color=COLORS["accent"], corner_radius=8,
                command=lambda c=ct: self._set_court(c),
            ).pack(side="left", padx=4)

        # Case list from DB
        ctk.CTkLabel(
            self._content, text="Select Case:",
            font=ctk.CTkFont(size=13), text_color=COLORS["text"],
        ).pack(anchor="w", padx=16, pady=(8, 4))

        cases = []
        if self._db:
            try:
                cases = [dict(r) for r in self._db.fetchall(
                    "SELECT id, case_number, title FROM cases WHERE status = 'active' ORDER BY id",
                )]
            except Exception:
                pass

        if not cases:
            ctk.CTkLabel(
                self._content, text="No active cases found",
                text_color=COLORS["text_dim"],
            ).pack(padx=16, pady=4)
        else:
            for c in cases:
                fg = COLORS["blue"] if c["id"] == self._selected_case_id else "transparent"
                ctk.CTkButton(
                    self._content,
                    text=f"{c.get('case_number', '')}  {c['title']}",
                    anchor="w", fg_color=fg,
                    hover_color=COLORS["accent"], text_color=COLORS["text"],
                    font=ctk.CTkFont(size=13), height=36, corner_radius=8,
                    command=lambda cid=c["id"]: self._set_case(cid),
                ).pack(fill="x", padx=16, pady=2)

    def _render_document_selector(self):
        """Step 3: Select documents -- shows filings from DB via FilingEngine."""
        ctk.CTkLabel(
            self._content,
            text="Select Documents",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=16, pady=(16, 8))

        filings = []
        if _HAS_FILING_ENGINE and self._db and self._selected_case_id:
            try:
                engine = FilingEngine(self._db)
                filings = engine.get_filings(case_id=self._selected_case_id)
            except Exception:
                logger.debug("FilingEngine.get_filings failed")

        if not filings and self._db and self._selected_case_id:
            try:
                filings = [dict(r) for r in self._db.fetchall(
                    "SELECT * FROM filings WHERE case_id = ? ORDER BY created_at DESC",
                    (self._selected_case_id,),
                )]
            except Exception:
                pass

        if not filings:
            ctk.CTkLabel(
                self._content, text="No filings found for this case",
                text_color=COLORS["text_dim"],
            ).pack(padx=16, pady=8)
            return

        for f in filings:
            status = f.get("status", "draft")
            s_color = {"draft": COLORS["text_dim"], "review": COLORS["orange"],
                       "ready": COLORS["green"], "filed": COLORS["blue"]}.get(status, COLORS["text_dim"])
            row = ctk.CTkFrame(self._content, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(
                row, text=f.get("title", "Untitled"),
                font=ctk.CTkFont(size=13), text_color=COLORS["text"],
            ).pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(
                row, text=f"[{status.upper()}]",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=s_color,
            ).pack(side="right", padx=10, pady=6)

    def _render_compliance_check(self):
        """Step 4: Real-time compliance checking via engines."""
        ctk.CTkLabel(
            self._content,
            text="Compliance Check",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=16, pady=(16, 8))

        issues: list[str] = []
        warnings: list[str] = []
        score = 0

        # Run filing stack validation
        if _HAS_FILING_ENGINE and self._db and self._selected_case_id:
            try:
                engine = FilingEngine(self._db)
                filings = engine.get_filings(case_id=self._selected_case_id)
                if filings:
                    filing_type = filings[0].get("filing_type", "motion")
                    try:
                        stack = engine.build_stack(self._selected_case_id, filing_type)
                        result = engine.validate_stack(stack)
                        score = result.score
                        issues = list(result.issues)
                        warnings = list(result.warnings)
                        self._validation_result = result.to_dict()
                    except LookupError as e:
                        issues.append(str(e))
                else:
                    issues.append("No filings to validate for this case.")
            except Exception as e:
                issues.append(f"Validation error: {e}")

        # Court rules check
        if _HAS_RULES_ENGINE and self._db:
            try:
                rules_engine = CourtRulesEngine(self._db)
                applicable = rules_engine.get_applicable_rules(
                    filing_type="motion", court_type=self._selected_court,
                )
                if applicable:
                    ctk.CTkLabel(
                        self._content,
                        text=f"Applicable rules: {len(applicable)}",
                        font=ctk.CTkFont(size=12), text_color=COLORS["blue"],
                    ).pack(anchor="w", padx=16, pady=2)
            except Exception:
                pass

        # Display score
        score_color = COLORS["green"] if score >= 80 else (COLORS["yellow"] if score >= 50 else COLORS["red"])
        ctk.CTkLabel(
            self._content,
            text=f"Compliance Score: {score}%",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=score_color,
        ).pack(padx=16, pady=8)

        if issues:
            ctk.CTkLabel(
                self._content, text="Issues:",
                font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["red"],
            ).pack(anchor="w", padx=16, pady=(8, 2))
            for iss in issues:
                ctk.CTkLabel(
                    self._content, text=f"  - {iss}",
                    font=ctk.CTkFont(size=12), text_color=COLORS["red"],
                ).pack(anchor="w", padx=24)

        if warnings:
            ctk.CTkLabel(
                self._content, text="Warnings:",
                font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["orange"],
            ).pack(anchor="w", padx=16, pady=(8, 2))
            for w in warnings:
                ctk.CTkLabel(
                    self._content, text=f"  - {w}",
                    font=ctk.CTkFont(size=12), text_color=COLORS["orange"],
                ).pack(anchor="w", padx=24)

        if not issues and not warnings:
            ctk.CTkLabel(
                self._content, text="All checks passed",
                font=ctk.CTkFont(size=13), text_color=COLORS["green"],
            ).pack(padx=16, pady=4)

    def _render_go_nogo_gate(self):
        """Step 5: GO/NO-GO decision gate before final output."""
        ctk.CTkLabel(
            self._content,
            text="GO / NO-GO GATE",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=16, pady=(16, 8))

        vr = self._validation_result
        if vr and vr.get("valid"):
            decision = "GO"
            color = COLORS["green"]
            msg = "Filing package meets all requirements. Ready to proceed."
        elif vr and vr.get("score", 0) >= 50:
            decision = "CONDITIONAL"
            color = COLORS["orange"]
            msg = "Filing has warnings. Review before proceeding."
        else:
            decision = "NO-GO"
            color = COLORS["red"]
            msg = "Filing does not meet requirements. Fix issues before filing."

        ctk.CTkLabel(
            self._content,
            text=decision,
            font=ctk.CTkFont(size=36, weight="bold"), text_color=color,
        ).pack(pady=16)

        ctk.CTkLabel(
            self._content, text=msg,
            font=ctk.CTkFont(size=14), text_color=COLORS["text"],
        ).pack(padx=16, pady=4)

        if vr:
            ctk.CTkLabel(
                self._content,
                text=f"Score: {vr.get('score', 0)}%  |  Issues: {len(vr.get('issues', []))}  |  Warnings: {len(vr.get('warnings', []))}",
                font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"],
            ).pack(padx=16, pady=4)

    def _render_service_packet(self):
        """Step 6: Service packet summary."""
        ctk.CTkLabel(
            self._content,
            text="Service Packet",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=16, pady=(16, 8))

        # Show evidence/exhibits available
        exhibit_count = 0
        if _HAS_EVIDENCE_ENGINE and self._db and self._selected_case_id:
            try:
                ev_engine = EvidenceEngine(self._db)
                exhibits = ev_engine.get_evidence(case_id=self._selected_case_id)
                exhibit_count = len(exhibits)
            except Exception:
                pass
        elif self._db and self._selected_case_id:
            try:
                row = self._db.fetchone(
                    "SELECT COUNT(*) FROM evidence WHERE case_id = ?",
                    (self._selected_case_id,),
                )
                exhibit_count = row[0] if row else 0
            except Exception:
                pass

        items = [
            ("Main Document", COLORS["green"] if self._selected_type else COLORS["red"]),
            ("Proof of Service", COLORS["orange"]),
            (f"Exhibits ({exhibit_count} available)", COLORS["green"] if exhibit_count else COLORS["red"]),
            ("Proposed Order", COLORS["orange"]),
        ]
        for label, color in items:
            row = ctk.CTkFrame(self._content, fg_color=COLORS["bg_card"], corner_radius=6)
            row.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(
                row, text=label, font=ctk.CTkFont(size=13), text_color=color,
            ).pack(side="left", padx=10, pady=6)

    def _render_filing_instructions(self):
        """Step 7: Final filing instructions."""
        ctk.CTkLabel(
            self._content,
            text="Filing Instructions",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=16, pady=(16, 8))

        court_label = self._selected_court.upper() if self._selected_court else "CIRCUIT"
        instructions = [
            f"1. Court: {court_label}",
            f"2. Filing type: {self._selected_type or 'Not selected'}",
            "3. Ensure all documents are signed",
            "4. Verify proof of service is complete",
            "5. Submit via TrueFiling (MI e-filing) or in person",
            "6. Retain copies of all filed documents",
            "7. Calendar response deadlines after filing",
        ]
        for instr in instructions:
            ctk.CTkLabel(
                self._content, text=instr,
                font=ctk.CTkFont(size=13), text_color=COLORS["text"], anchor="w",
            ).pack(anchor="w", padx=16, pady=2)

    def _select_type(self, filing_type: str):
        self._selected_type = filing_type
        logger.info("Filing type selected: %s", filing_type)
        self._next_step()

    def _set_court(self, court: str):
        self._selected_court = court
        self._render_step()

    def _set_case(self, case_id: int):
        self._selected_case_id = case_id
        self._render_step()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _next_step(self):
        if self._current_step < len(_STEPS) - 1:
            self._current_step += 1
            self._update_nav()

    def _prev_step(self):
        if self._current_step > 0:
            self._current_step -= 1
            self._update_nav()

    def _update_nav(self):
        frac = self._current_step / (len(_STEPS) - 1) if len(_STEPS) > 1 else 1
        self._progress.set(frac)
        self._step_label.configure(
            text=f"Step {self._current_step + 1} of {len(_STEPS)}: "
                 f"{_STEPS[self._current_step]}",
        )
        self._back_btn.configure(
            state="normal" if self._current_step > 0 else "disabled",
        )
        self._next_btn.configure(
            text="Finish" if self._current_step == len(_STEPS) - 1 else "Next →",
        )
        self._render_step()
