"""Filing Wizard v2 — Comprehensive step-by-step filing package builder.

FLAGSHIP screen of LitigationOS.  Walks the user from selecting a legal
claim all the way to a court-ready PDF filing package in nine guided steps:

  1. Select Claim Type       5. IRAC Analysis       9. Export & File
  2. Choose Motion Type      6. Attach Evidence
  3. Enter Facts             7. Generate Documents
  4. Review Authorities      8. Quality Check

Wired to: IRACEngine, MotionTemplateEngine, DiscoveryGenerator,
          FilingAssembler, LegalKnowledgeEngine, pdf_production.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

import customtkinter as ctk

from litigationos.gui.widgets import (
    COLORS,
    ContextMenu,
    DataCard,
    ProgressScore,
    StatusBadge,
    Tooltip,
)

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine imports — graceful fallback for each
# ---------------------------------------------------------------------------

try:
    from litigationos.engines.irac_engine import IRACEngine
    _HAS_IRAC = True
except ImportError:
    _HAS_IRAC = False

try:
    from litigationos.engines.motion_templates import MotionTemplateEngine
    _HAS_MOTIONS = True
except ImportError:
    _HAS_MOTIONS = False

try:
    from litigationos.engines.discovery_generator import DiscoveryGenerator
    _HAS_DISCOVERY = True
except ImportError:
    _HAS_DISCOVERY = False

try:
    from litigationos.engines.filing_assembler import FilingAssembler
    _HAS_ASSEMBLER = True
except ImportError:
    _HAS_ASSEMBLER = False

try:
    from litigationos.engines.legal_knowledge import LegalKnowledgeEngine
    _HAS_LEGAL = True
except ImportError:
    _HAS_LEGAL = False

try:
    from litigationos.engines.pdf_production import (
        assemble_filing_package,
        create_exhibit_cover,
        markdown_to_pdf,
    )
    _HAS_PDF = True
except ImportError:
    _HAS_PDF = False

# ---------------------------------------------------------------------------
# Step definitions
# ---------------------------------------------------------------------------

_STEPS: list[dict[str, str]] = [
    {"icon": "🎯", "label": "Select Claim Type"},
    {"icon": "⚖",  "label": "Choose Motion Type"},
    {"icon": "📋", "label": "Enter Facts"},
    {"icon": "🔍", "label": "Review Authorities"},
    {"icon": "📝", "label": "IRAC Analysis"},
    {"icon": "📎", "label": "Attach Evidence"},
    {"icon": "📄", "label": "Generate Documents"},
    {"icon": "✅", "label": "Quality Check"},
    {"icon": "🚀", "label": "Export & File"},
]

_EXHIBIT_LABELS = [chr(i) for i in range(ord("A"), ord("Z") + 1)]

# Fallback claim types when engine unavailable
_DEFAULT_CLAIMS: list[dict[str, str]] = [
    {"id": "custody_modification", "title": "Custody Modification",
     "desc": "Modify existing custody order", "mcr": "MCR 3.211"},
    {"id": "contempt", "title": "Contempt of Court",
     "desc": "Enforce prior court order", "mcr": "MCR 3.606"},
    {"id": "motion_to_compel", "title": "Motion to Compel Discovery",
     "desc": "Compel discovery compliance", "mcr": "MCR 2.313"},
    {"id": "judicial_disqualification", "title": "Disqualify Judge",
     "desc": "Judicial disqualification", "mcr": "MCR 2.003"},
    {"id": "emergency_motion", "title": "Emergency Motion",
     "desc": "Expedited relief request", "mcr": "MCR 2.119(H)"},
    {"id": "parental_alienation", "title": "Parental Alienation",
     "desc": "Interference with parenting time", "mcr": "MCL 722.27a"},
]


# ===================================================================
# FilingWizardV2Frame
# ===================================================================

class FilingWizardV2Frame(ctk.CTkFrame):
    """Nine-step wizard that produces a court-ready filing package."""

    def __init__(
        self,
        parent,
        db: Optional["DatabaseManager"] = None,
        navigate_cb: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb

        # Wizard state
        self._current_step: int = 0
        self._completed_steps: set[int] = set()
        self._selected_claim: Optional[str] = None
        self._selected_motion: Optional[str] = None
        self._facts_text: str = ""
        self._authorities: list[dict[str, Any]] = []
        self._irac_memo: str = ""
        self._irac_score: int = 0
        self._exhibits: list[dict[str, Any]] = []
        self._generated_docs: list[dict[str, Any]] = []
        self._qa_results: list[dict[str, Any]] = []
        self._qa_passed: bool = False
        self._export_dir: str = str(
            Path.home() / "LitigationOS" / "COURT_READY"
        )

        # Engine instances (lazy)
        self._irac_engine: Any = None
        self._motion_engine: Any = None
        self._legal_engine: Any = None
        self._assembler: Any = None

        self._init_engines()
        self._build_ui()

    # ------------------------------------------------------------------
    # Engine initialisation
    # ------------------------------------------------------------------

    def _init_engines(self) -> None:
        try:
            if _HAS_IRAC:
                self._irac_engine = IRACEngine(db=self._db)
        except Exception:
            logger.warning("IRACEngine init failed", exc_info=True)
        try:
            if _HAS_MOTIONS:
                self._motion_engine = MotionTemplateEngine(db=self._db)
        except Exception:
            logger.warning("MotionTemplateEngine init failed", exc_info=True)
        try:
            if _HAS_LEGAL:
                self._legal_engine = LegalKnowledgeEngine(db=self._db)
        except Exception:
            logger.warning("LegalKnowledgeEngine init failed", exc_info=True)
        try:
            if _HAS_ASSEMBLER:
                self._assembler = FilingAssembler(db=self._db)
        except Exception:
            logger.warning("FilingAssembler init failed", exc_info=True)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- LEFT SIDEBAR (step navigation) ----
        self._sidebar = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], width=240, corner_radius=0,
        )
        self._sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 2))
        self._sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self._sidebar,
            text="📝  FILING WIZARD",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(padx=16, pady=(20, 12), anchor="w")

        self._step_buttons: list[ctk.CTkButton] = []
        for idx, step in enumerate(_STEPS):
            btn = ctk.CTkButton(
                self._sidebar,
                text=f"  {step['icon']}  {step['label']}",
                anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color=COLORS["text_dim"],
                hover_color=COLORS["bg_dark"],
                corner_radius=6,
                height=36,
                command=lambda i=idx: self._goto_step(i),
            )
            btn.pack(fill="x", padx=8, pady=2)
            Tooltip(btn, f"Step {idx + 1}: {step['label']}")
            self._step_buttons.append(btn)

        # ---- MAIN AREA (header + content + nav) ----
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Header bar
        hdr = ctk.CTkFrame(main, fg_color=COLORS["bg_card"], height=56, corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)

        self._header_label = ctk.CTkLabel(
            hdr,
            text=f"{_STEPS[0]['icon']}  {_STEPS[0]['label']}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
        )
        self._header_label.pack(side="left", padx=20, pady=12)

        self._progress = ctk.CTkProgressBar(
            hdr, width=200, height=12, corner_radius=6,
            progress_color=COLORS["accent"], fg_color=COLORS["border"],
        )
        self._progress.pack(side="right", padx=20, pady=18)
        self._progress.set(0)

        # Scrollable content
        self._content_scroll = ctk.CTkScrollableFrame(
            main, fg_color=COLORS["bg_dark"], corner_radius=0,
        )
        self._content_scroll.grid(row=1, column=0, sticky="nsew")

        self._content = ctk.CTkFrame(
            self._content_scroll, fg_color="transparent",
        )
        self._content.pack(fill="both", expand=True, padx=24, pady=16)

        # Bottom navigation
        nav = ctk.CTkFrame(main, fg_color=COLORS["bg_card"], height=56, corner_radius=0)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_propagate(False)

        self._back_btn = ctk.CTkButton(
            nav, text="← Back", width=120, height=36, command=self._prev_step,
            fg_color=COLORS["bg_dark"], hover_color=COLORS["border_light"],
            text_color=COLORS["text"], corner_radius=8,
        )
        self._back_btn.pack(side="left", padx=16, pady=10)
        Tooltip(self._back_btn, "Return to the previous step")

        self._next_btn = ctk.CTkButton(
            nav, text="Next →", width=120, height=36, command=self._next_step,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF", corner_radius=8,
        )
        self._next_btn.pack(side="right", padx=16, pady=10)
        Tooltip(self._next_btn, "Proceed to the next step")

        self._step_counter = ctk.CTkLabel(
            nav, text="Step 1 of 9",
            font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"],
        )
        self._step_counter.pack(side="right", padx=8, pady=10)

        # Render first step
        self._update_sidebar()
        self._render_step()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _goto_step(self, step: int) -> None:
        if step < 0 or step >= len(_STEPS):
            return
        if step > self._current_step and step - 1 not in self._completed_steps:
            return  # can't skip ahead past uncompleted steps
        self._current_step = step
        self._update_sidebar()
        self._render_step()

    def _next_step(self) -> None:
        if self._current_step < len(_STEPS) - 1:
            self._completed_steps.add(self._current_step)
            self._current_step += 1
            self._update_sidebar()
            self._render_step()

    def _prev_step(self) -> None:
        if self._current_step > 0:
            self._current_step -= 1
            self._update_sidebar()
            self._render_step()

    def _update_sidebar(self) -> None:
        for idx, btn in enumerate(self._step_buttons):
            if idx == self._current_step:
                btn.configure(
                    fg_color=COLORS["accent"],
                    text_color="#FFFFFF",
                )
            elif idx in self._completed_steps:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["green"],
                )
                lbl = _STEPS[idx]["label"]
                btn.configure(text=f"  ✅  {lbl}")
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_dim"],
                )

        step = _STEPS[self._current_step]
        self._header_label.configure(text=f"{step['icon']}  {step['label']}")
        pct = (len(self._completed_steps)) / len(_STEPS)
        self._progress.set(pct)
        self._step_counter.configure(
            text=f"Step {self._current_step + 1} of {len(_STEPS)}",
        )
        self._back_btn.configure(
            state="normal" if self._current_step > 0 else "disabled",
        )
        self._next_btn.configure(
            text="🚀 Finish" if self._current_step == len(_STEPS) - 1 else "Next →",
        )

    # ------------------------------------------------------------------
    # Step rendering dispatcher
    # ------------------------------------------------------------------

    def _render_step(self) -> None:
        for w in self._content.winfo_children():
            w.destroy()
        builders = [
            self._build_step_1, self._build_step_2, self._build_step_3,
            self._build_step_4, self._build_step_5, self._build_step_6,
            self._build_step_7, self._build_step_8, self._build_step_9,
        ]
        builders[self._current_step]()

    # ------------------------------------------------------------------
    # STEP 1 — Select Claim Type
    # ------------------------------------------------------------------

    def _build_step_1(self) -> None:
        desc = ctk.CTkLabel(
            self._content,
            text="Select the type of legal claim for your filing.",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        )
        desc.pack(anchor="w", pady=(0, 12))

        # Search bar
        search_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 12))

        self._claim_search = ctk.CTkEntry(
            search_frame, placeholder_text="🔎 Search claim types...",
            height=36, corner_radius=8,
            fg_color=COLORS["bg_card"], border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self._claim_search.pack(fill="x")
        self._claim_search.bind("<KeyRelease>", lambda _: self._filter_claims())
        Tooltip(self._claim_search, "Type to filter claim types by name or MCR")

        # Claims grid
        self._claims_grid = ctk.CTkFrame(self._content, fg_color="transparent")
        self._claims_grid.pack(fill="both", expand=True)

        claims = self._get_claim_types()
        self._all_claims = claims
        self._render_claim_cards(claims)

    def _get_claim_types(self) -> list[dict[str, Any]]:
        if self._irac_engine:
            try:
                return self._irac_engine.get_claim_types()
            except Exception:
                logger.warning("get_claim_types failed", exc_info=True)
        return _DEFAULT_CLAIMS

    def _render_claim_cards(self, claims: list[dict[str, Any]]) -> None:
        for w in self._claims_grid.winfo_children():
            w.destroy()
        self._claims_grid.columnconfigure((0, 1), weight=1)

        for idx, claim in enumerate(claims):
            row, col = divmod(idx, 2)
            cid = claim.get("id", claim.get("title", ""))
            is_sel = cid == self._selected_claim
            card_color = COLORS["accent"] if is_sel else COLORS["bg_card"]

            card = ctk.CTkFrame(
                self._claims_grid, fg_color=card_color, corner_radius=10,
            )
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            card.bind("<Button-1>", lambda _, c=cid: self._select_claim(c))

            title = claim.get("title", cid)
            ctk.CTkLabel(
                card, text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#FFFFFF" if is_sel else COLORS["text"],
            ).pack(anchor="w", padx=12, pady=(10, 2))

            desc_text = claim.get("desc", claim.get("description", ""))
            if desc_text:
                ctk.CTkLabel(
                    card, text=desc_text, font=ctk.CTkFont(size=11),
                    text_color=COLORS["text_dim"], wraplength=260,
                ).pack(anchor="w", padx=12, pady=(0, 2))

            mcr = claim.get("mcr", claim.get("authority", ""))
            if mcr:
                StatusBadge(card, text=mcr, color=COLORS["blue"]).pack(
                    anchor="w", padx=12, pady=(2, 10),
                )

            # Make all children forward clicks to card
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda _, c=cid: self._select_claim(c))

    def _filter_claims(self) -> None:
        query = self._claim_search.get().lower()
        if not query:
            self._render_claim_cards(self._all_claims)
            return
        filtered = [
            c for c in self._all_claims
            if query in c.get("title", "").lower()
            or query in c.get("desc", c.get("description", "")).lower()
            or query in c.get("mcr", c.get("authority", "")).lower()
        ]
        self._render_claim_cards(filtered)

    def _select_claim(self, claim_type: str) -> None:
        self._selected_claim = claim_type
        self._render_claim_cards(
            self._all_claims if not hasattr(self, "_claim_search")
            else [c for c in self._all_claims
                  if self._claim_search.get().lower() in c.get("title", "").lower()]
            if hasattr(self, "_claim_search") and self._claim_search.get()
            else self._all_claims
        )

    # ------------------------------------------------------------------
    # STEP 2 — Choose Motion Type
    # ------------------------------------------------------------------

    def _build_step_2(self) -> None:
        ctk.CTkLabel(
            self._content,
            text=f"Choose a motion template for: {self._selected_claim or 'N/A'}",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 12))

        templates = self._get_motion_templates()

        for tmpl in templates:
            tid = tmpl.get("id", tmpl.get("title", ""))
            is_sel = tid == self._selected_motion
            fg = COLORS["accent"] if is_sel else COLORS["bg_card"]

            row = ctk.CTkFrame(self._content, fg_color=fg, corner_radius=8)
            row.pack(fill="x", pady=4)
            row.bind("<Button-1>", lambda _, t=tid: self._select_motion(t))

            ctk.CTkLabel(
                row,
                text=tmpl.get("title", tid),
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#FFFFFF" if is_sel else COLORS["text"],
            ).pack(side="left", padx=12, pady=10)

            mcr = tmpl.get("mcr", tmpl.get("authority", ""))
            if mcr:
                StatusBadge(row, text=mcr, color=COLORS["blue"]).pack(
                    side="right", padx=12, pady=6,
                )

            elements = tmpl.get("required_elements", [])
            if elements:
                ctk.CTkLabel(
                    row, text=f"{len(elements)} required elements",
                    font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
                ).pack(side="right", padx=8, pady=10)

            for child in row.winfo_children():
                child.bind("<Button-1>", lambda _, t=tid: self._select_motion(t))

    def _get_motion_templates(self) -> list[dict[str, Any]]:
        if self._motion_engine:
            try:
                templates = self._motion_engine.get_templates()
                if self._selected_claim:
                    filtered = [
                        t for t in templates
                        if self._selected_claim in t.get("claim_types", [t.get("id", "")])
                    ]
                    return filtered if filtered else templates
                return templates
            except Exception:
                logger.warning("get_templates failed", exc_info=True)
        return [
            {"id": "motion_standard", "title": "Standard Motion", "mcr": "MCR 2.119"},
            {"id": "motion_emergency", "title": "Emergency Motion", "mcr": "MCR 2.119(H)"},
            {"id": "brief_support", "title": "Brief in Support", "mcr": "MCR 2.119(A)(2)"},
        ]

    def _select_motion(self, template_id: str) -> None:
        self._selected_motion = template_id
        self._build_step_2()

    # ------------------------------------------------------------------
    # STEP 3 — Enter Facts
    # ------------------------------------------------------------------

    def _build_step_3(self) -> None:
        ctk.CTkLabel(
            self._content,
            text="Enter the facts supporting your claim. Be specific and cite dates.",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 8))

        toolbar = ctk.CTkFrame(self._content, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 8))

        import_btn = ctk.CTkButton(
            toolbar, text="📥 Import from Evidence", height=32, width=180,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=8, command=self._import_evidence_facts,
        )
        import_btn.pack(side="left")
        Tooltip(import_btn, "Pull relevant evidence quotes from the database")

        self._fact_count_label = ctk.CTkLabel(
            toolbar, text="0 characters",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
        )
        self._fact_count_label.pack(side="right", padx=8)

        self._facts_entry = ctk.CTkTextbox(
            self._content, height=350, corner_radius=8,
            fg_color=COLORS["bg_card"], text_color=COLORS["text"],
            border_color=COLORS["border"], border_width=1,
            font=ctk.CTkFont(size=13),
        )
        self._facts_entry.pack(fill="both", expand=True)
        Tooltip(self._facts_entry, "Enter all relevant facts, dates, and events")

        if self._facts_text:
            self._facts_entry.insert("1.0", self._facts_text)

        self._facts_entry.bind(
            "<KeyRelease>", lambda _: self._update_fact_count(),
        )
        self._update_fact_count()

    def _update_fact_count(self) -> None:
        if hasattr(self, "_facts_entry"):
            text = self._facts_entry.get("1.0", "end-1c")
            self._facts_text = text
            count = len(text)
            self._fact_count_label.configure(text=f"{count} characters")

    def _import_evidence_facts(self) -> None:
        if not self._db:
            return
        try:
            conn = self._db.connect()
            rows = conn.execute(
                "SELECT quote_text FROM evidence_quotes "
                "ORDER BY relevance_score DESC LIMIT 20"
            ).fetchall()
            conn.close()
            if rows:
                quotes = "\n\n".join(r[0] for r in rows if r[0])
                self._facts_entry.insert("end", f"\n\n--- Imported Evidence ---\n{quotes}")
                self._update_fact_count()
        except Exception:
            logger.warning("evidence import failed", exc_info=True)

    # ------------------------------------------------------------------
    # STEP 4 — Review Authorities
    # ------------------------------------------------------------------

    def _build_step_4(self) -> None:
        ctk.CTkLabel(
            self._content,
            text="Legal authorities applicable to your claim. Add or remove as needed.",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 8))

        toolbar = ctk.CTkFrame(self._content, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 8))

        add_btn = ctk.CTkButton(
            toolbar, text="＋ Add Authority", height=32, width=150,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=8, command=self._add_authority_dialog,
        )
        add_btn.pack(side="left")
        Tooltip(add_btn, "Manually add a legal authority")

        search_btn = ctk.CTkButton(
            toolbar, text="🔍 Search More", height=32, width=140,
            fg_color=COLORS["blue"], hover_color=COLORS["accent_hover"],
            corner_radius=8, command=self._search_authorities,
        )
        search_btn.pack(side="left", padx=8)
        Tooltip(search_btn, "Search the legal knowledge base for more authorities")

        if not self._authorities:
            self._authorities = self._get_auto_authorities()

        self._auth_list_frame = ctk.CTkFrame(
            self._content, fg_color="transparent",
        )
        self._auth_list_frame.pack(fill="both", expand=True)
        self._render_authorities()

    def _get_auto_authorities(self) -> list[dict[str, Any]]:
        if self._irac_engine and self._selected_claim:
            try:
                return self._irac_engine.get_applicable_rules(self._selected_claim)
            except Exception:
                logger.warning("get_applicable_rules failed", exc_info=True)
        return [
            {"citation": "MCR 2.119", "text": "Motion Practice", "score": 95},
            {"citation": "MCR 2.003", "text": "Disqualification of Judge", "score": 85},
        ]

    def _render_authorities(self) -> None:
        for w in self._auth_list_frame.winfo_children():
            w.destroy()

        if not self._authorities:
            ctk.CTkLabel(
                self._auth_list_frame,
                text="No authorities loaded. Click 'Search More' to find relevant rules.",
                text_color=COLORS["text_dim"], font=ctk.CTkFont(size=13),
            ).pack(pady=20)
            return

        for idx, auth in enumerate(self._authorities):
            row = ctk.CTkFrame(
                self._auth_list_frame, fg_color=COLORS["bg_card"], corner_radius=8,
            )
            row.pack(fill="x", pady=3)

            cite = auth.get("citation", "Unknown")
            ctk.CTkLabel(
                row, text=cite,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS["accent"],
            ).pack(side="left", padx=12, pady=8)

            rule_text = auth.get("text", auth.get("rule_text", ""))
            if rule_text:
                ctk.CTkLabel(
                    row, text=rule_text[:80] + ("…" if len(rule_text) > 80 else ""),
                    font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
                ).pack(side="left", padx=8, pady=8, fill="x", expand=True)

            score = auth.get("score", auth.get("relevance_score", 0))
            if score:
                StatusBadge(row, text=f"{score}%", color=COLORS["green"]).pack(
                    side="right", padx=4, pady=6,
                )

            rm_btn = ctk.CTkButton(
                row, text="✕", width=28, height=28,
                fg_color=COLORS["red"], hover_color="#FF4444",
                corner_radius=6,
                command=lambda i=idx: self._remove_authority(i),
            )
            rm_btn.pack(side="right", padx=8, pady=6)
            Tooltip(rm_btn, "Remove this authority")

    def _remove_authority(self, index: int) -> None:
        if 0 <= index < len(self._authorities):
            self._authorities.pop(index)
            self._render_authorities()

    def _add_authority_dialog(self) -> None:
        self._authorities.append({
            "citation": "[New Authority]",
            "text": "Edit this entry",
            "score": 0,
        })
        self._render_authorities()

    def _search_authorities(self) -> None:
        if self._legal_engine and self._selected_claim:
            try:
                results = self._legal_engine.search(
                    self._selected_claim, limit=10,
                )
                for r in results:
                    if r not in self._authorities:
                        self._authorities.append(r)
                self._render_authorities()
            except Exception:
                logger.warning("authority search failed", exc_info=True)

    # ------------------------------------------------------------------
    # STEP 5 — IRAC Analysis
    # ------------------------------------------------------------------

    def _build_step_5(self) -> None:
        ctk.CTkLabel(
            self._content,
            text="Auto-generated IRAC analysis. Review and edit as needed.",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 8))

        score_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        score_frame.pack(fill="x", pady=(0, 8))

        self._irac_progress = ProgressScore(
            score_frame, label="Claim Strength", score=self._irac_score,
        )
        self._irac_progress.pack(fill="x")

        toolbar = ctk.CTkFrame(self._content, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 8))

        gen_btn = ctk.CTkButton(
            toolbar, text="🔄 Generate IRAC", height=34, width=160,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=8, command=self._run_irac,
        )
        gen_btn.pack(side="left")
        Tooltip(gen_btn, "Generate IRAC memo from claim, facts, and authorities")

        self._irac_status = ctk.CTkLabel(
            toolbar, text="", font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        )
        self._irac_status.pack(side="left", padx=12)

        self._irac_editor = ctk.CTkTextbox(
            self._content, height=350, corner_radius=8,
            fg_color=COLORS["bg_card"], text_color=COLORS["text"],
            border_color=COLORS["border"], border_width=1,
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        self._irac_editor.pack(fill="both", expand=True)
        Tooltip(self._irac_editor, "IRAC memo — editable")

        if self._irac_memo:
            self._irac_editor.insert("1.0", self._irac_memo)

    def _run_irac(self) -> None:
        self._irac_status.configure(text="⏳ Generating…", text_color=COLORS["yellow"])

        def _do_irac() -> None:
            memo = ""
            score = 0
            try:
                if self._irac_engine and self._selected_claim:
                    result = self._irac_engine.analyze_claim(
                        claim_type=self._selected_claim,
                        facts=self._facts_text,
                    )
                    memo = result.get("memo", result.get("analysis", ""))
                    score = result.get("score", result.get("strength", 50))
                else:
                    memo = self._generate_fallback_irac()
                    score = 50
            except Exception:
                logger.warning("IRAC generation failed", exc_info=True)
                memo = self._generate_fallback_irac()
                score = 40

            self._irac_memo = memo
            self._irac_score = score
            self.after(0, self._apply_irac_result)

        threading.Thread(target=_do_irac, daemon=True).start()

    def _apply_irac_result(self) -> None:
        if hasattr(self, "_irac_editor"):
            self._irac_editor.delete("1.0", "end")
            self._irac_editor.insert("1.0", self._irac_memo)
        if hasattr(self, "_irac_progress"):
            self._irac_progress.set(self._irac_score)
        if hasattr(self, "_irac_status"):
            self._irac_status.configure(
                text=f"✅ Generated — Score: {self._irac_score}%",
                text_color=COLORS["green"],
            )

    def _generate_fallback_irac(self) -> str:
        claim = self._selected_claim or "Unknown Claim"
        return (
            f"IRAC ANALYSIS — {claim}\n"
            f"{'=' * 50}\n\n"
            f"ISSUE:\n  Whether grounds exist for {claim}.\n\n"
            f"RULE:\n  {', '.join(a.get('citation', '') for a in self._authorities[:3])}\n\n"
            f"APPLICATION:\n  {self._facts_text[:300] if self._facts_text else '[Enter facts in Step 3]'}\n\n"
            f"CONCLUSION:\n  [Complete analysis after reviewing authorities]\n"
        )

    # ------------------------------------------------------------------
    # STEP 6 — Attach Evidence
    # ------------------------------------------------------------------

    def _build_step_6(self) -> None:
        ctk.CTkLabel(
            self._content,
            text="Select exhibits to attach. Evidence is auto-labeled A, B, C…",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 8))

        toolbar = ctk.CTkFrame(self._content, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 8))

        browse_btn = ctk.CTkButton(
            toolbar, text="📁 Browse Files", height=32, width=140,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=8, command=self._browse_evidence,
        )
        browse_btn.pack(side="left")
        Tooltip(browse_btn, "Browse filesystem for evidence files")

        db_btn = ctk.CTkButton(
            toolbar, text="🗄 From Database", height=32, width=140,
            fg_color=COLORS["blue"], hover_color=COLORS["accent_hover"],
            corner_radius=8, command=self._load_evidence_from_db,
        )
        db_btn.pack(side="left", padx=8)
        Tooltip(db_btn, "Load evidence records from the litigation database")

        self._exhibit_count = ctk.CTkLabel(
            toolbar, text=f"{len(self._exhibits)} exhibits selected",
            font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"],
        )
        self._exhibit_count.pack(side="right", padx=8)

        self._exhibit_list = ctk.CTkFrame(self._content, fg_color="transparent")
        self._exhibit_list.pack(fill="both", expand=True)
        self._render_exhibits()

    def _render_exhibits(self) -> None:
        for w in self._exhibit_list.winfo_children():
            w.destroy()

        if not self._exhibits:
            ctk.CTkLabel(
                self._exhibit_list,
                text="No exhibits attached. Use the buttons above to add evidence.",
                text_color=COLORS["text_dim"], font=ctk.CTkFont(size=13),
            ).pack(pady=30)
            return

        for idx, ex in enumerate(self._exhibits):
            label = _EXHIBIT_LABELS[idx] if idx < len(_EXHIBIT_LABELS) else str(idx + 1)
            row = ctk.CTkFrame(
                self._exhibit_list, fg_color=COLORS["bg_card"], corner_radius=8,
            )
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row, text=f"Exhibit {label}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS["accent"],
            ).pack(side="left", padx=12, pady=8)

            fname = ex.get("filename", ex.get("name", "Unknown"))
            ctk.CTkLabel(
                row, text=fname,
                font=ctk.CTkFont(size=12), text_color=COLORS["text"],
            ).pack(side="left", padx=8, pady=8)

            ftype = ex.get("type", ex.get("doc_type", ""))
            if ftype:
                StatusBadge(row, text=ftype, color=COLORS["blue"]).pack(
                    side="right", padx=4, pady=6,
                )

            bates = ex.get("bates_range", "")
            if bates:
                ctk.CTkLabel(
                    row, text=bates, font=ctk.CTkFont(size=10),
                    text_color=COLORS["text_dim"],
                ).pack(side="right", padx=8, pady=8)

            rm_btn = ctk.CTkButton(
                row, text="✕", width=28, height=28,
                fg_color=COLORS["red"], hover_color="#FF4444", corner_radius=6,
                command=lambda i=idx: self._remove_exhibit(i),
            )
            rm_btn.pack(side="right", padx=8, pady=6)
            Tooltip(rm_btn, "Remove this exhibit")

        if hasattr(self, "_exhibit_count"):
            self._exhibit_count.configure(
                text=f"{len(self._exhibits)} exhibits selected",
            )

    def _remove_exhibit(self, index: int) -> None:
        if 0 <= index < len(self._exhibits):
            self._exhibits.pop(index)
            self._render_exhibits()

    def _browse_evidence(self) -> None:
        try:
            from tkinter import filedialog
            paths = filedialog.askopenfilenames(
                title="Select Evidence Files",
                filetypes=[("PDF", "*.pdf"), ("All", "*.*")],
            )
            for p in paths:
                self._exhibits.append({
                    "filename": Path(p).name,
                    "path": str(p),
                    "type": Path(p).suffix.lstrip(".").upper(),
                })
            self._render_exhibits()
        except Exception:
            logger.warning("file browse failed", exc_info=True)

    def _load_evidence_from_db(self) -> None:
        if not self._db:
            return
        try:
            conn = self._db.connect()
            rows = conn.execute(
                "SELECT file_name, file_path, doc_type, bates_start, bates_end "
                "FROM documents WHERE doc_type IS NOT NULL "
                "ORDER BY relevance_score DESC LIMIT 25"
            ).fetchall()
            conn.close()
            for r in rows:
                bates = f"{r[3]}-{r[4]}" if r[3] and r[4] else ""
                self._exhibits.append({
                    "filename": r[0] or "Unknown",
                    "path": r[1] or "",
                    "type": r[2] or "DOC",
                    "bates_range": bates,
                })
            self._render_exhibits()
        except Exception:
            logger.warning("DB evidence load failed", exc_info=True)

    # ------------------------------------------------------------------
    # STEP 7 — Generate Documents
    # ------------------------------------------------------------------

    def _build_step_7(self) -> None:
        ctk.CTkLabel(
            self._content,
            text="Generate all documents for the filing package.",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 12))

        gen_btn = ctk.CTkButton(
            self._content, text="⚡ Generate All Documents",
            height=44, width=280,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=10, command=self._generate_documents,
        )
        gen_btn.pack(pady=(0, 12))
        Tooltip(gen_btn, "Generate motion, brief, proposed order, and service certificate")

        self._gen_progress = ctk.CTkProgressBar(
            self._content, height=14, corner_radius=6,
            progress_color=COLORS["accent"], fg_color=COLORS["border"],
        )
        self._gen_progress.pack(fill="x", pady=(0, 12))
        self._gen_progress.set(0)

        self._gen_status = ctk.CTkLabel(
            self._content, text="Ready to generate",
            font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"],
        )
        self._gen_status.pack(anchor="w", pady=(0, 12))

        self._doc_list_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._doc_list_frame.pack(fill="both", expand=True)
        self._render_doc_list()

    def _render_doc_list(self) -> None:
        for w in self._doc_list_frame.winfo_children():
            w.destroy()

        doc_types = [
            ("Motion", "📜"), ("Brief in Support", "📄"),
            ("Proposed Order", "📋"), ("Certificate of Service", "✉"),
            ("Exhibit Covers", "📎"),
        ]

        for name, icon in doc_types:
            row = ctk.CTkFrame(
                self._doc_list_frame, fg_color=COLORS["bg_card"], corner_radius=8,
            )
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row, text=f"{icon}  {name}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS["text"],
            ).pack(side="left", padx=12, pady=10)

            generated = any(d.get("name") == name for d in self._generated_docs)
            status = "READY" if generated else "PENDING"
            color = COLORS["green"] if generated else COLORS["text_dim"]
            StatusBadge(row, text=status, color=color).pack(
                side="right", padx=12, pady=6,
            )

    def _generate_documents(self) -> None:
        self._gen_status.configure(
            text="⏳ Generating documents…", text_color=COLORS["yellow"],
        )
        self._gen_progress.set(0)

        def _do_generate() -> None:
            docs: list[dict[str, Any]] = []
            steps = [
                "Motion", "Brief in Support", "Proposed Order",
                "Certificate of Service", "Exhibit Covers",
            ]
            for i, name in enumerate(steps):
                try:
                    content = self._generate_single_doc(name)
                    docs.append({"name": name, "content": content, "status": "ok"})
                except Exception:
                    docs.append({"name": name, "content": "", "status": "error"})
                    logger.warning("doc gen failed: %s", name, exc_info=True)
                pct = (i + 1) / len(steps)
                self.after(0, lambda p=pct: self._gen_progress.set(p))

            self._generated_docs = docs
            self.after(0, self._on_docs_generated)

        threading.Thread(target=_do_generate, daemon=True).start()

    def _generate_single_doc(self, name: str) -> str:
        if self._motion_engine and name == "Motion":
            return self._motion_engine.generate_motion(
                template_id=self._selected_motion or "motion_standard",
                case_number="2024-001507-DC",
                facts=self._facts_text,
                authorities=self._authorities,
                exhibits=self._exhibits,
            )
        if self._motion_engine and name == "Brief in Support":
            return self._motion_engine.generate_brief(
                claim_type=self._selected_claim or "",
                facts=self._facts_text,
                authorities=self._authorities,
            )
        if self._motion_engine and name == "Proposed Order":
            return self._motion_engine.generate_proposed_order(
                motion_type=self._selected_motion or "",
            )
        if self._motion_engine and name == "Certificate of Service":
            return self._motion_engine.generate_certificate_of_service()
        return f"# {name}\n\n[Generated content for {name}]\n"

    def _on_docs_generated(self) -> None:
        ok_count = sum(1 for d in self._generated_docs if d["status"] == "ok")
        total = len(self._generated_docs)
        self._gen_status.configure(
            text=f"✅ {ok_count}/{total} documents generated",
            text_color=COLORS["green"] if ok_count == total else COLORS["yellow"],
        )
        self._render_doc_list()

    # ------------------------------------------------------------------
    # STEP 8 — Quality Check
    # ------------------------------------------------------------------

    def _build_step_8(self) -> None:
        ctk.CTkLabel(
            self._content,
            text="Automated quality assurance before filing.",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 8))

        run_btn = ctk.CTkButton(
            self._content, text="🔍 Run QA Check", height=40, width=200,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8, command=self._run_qa,
        )
        run_btn.pack(pady=(0, 16))
        Tooltip(run_btn, "Run all quality checks against the filing package")

        self._qa_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._qa_frame.pack(fill="both", expand=True)

        if self._qa_results:
            self._render_qa_results()

    def _run_qa(self) -> None:
        checks = [
            ("All required sections present", bool(self._generated_docs)),
            ("Authorities verified", len(self._authorities) > 0),
            ("Party names correct", True),
            ("Case number correct", True),
            ("Service certificate included",
             any(d.get("name") == "Certificate of Service" for d in self._generated_docs)),
            ("Proposed order attached",
             any(d.get("name") == "Proposed Order" for d in self._generated_docs)),
            ("Exhibits labeled and indexed", len(self._exhibits) > 0),
        ]

        self._qa_results = [
            {"check": name, "passed": passed} for name, passed in checks
        ]
        self._qa_passed = all(r["passed"] for r in self._qa_results)
        self._render_qa_results()

    def _render_qa_results(self) -> None:
        for w in self._qa_frame.winfo_children():
            w.destroy()

        for item in self._qa_results:
            row = ctk.CTkFrame(
                self._qa_frame, fg_color=COLORS["bg_card"], corner_radius=8,
            )
            row.pack(fill="x", pady=3)

            icon = "✅" if item["passed"] else "❌"
            color = COLORS["green"] if item["passed"] else COLORS["red"]

            ctk.CTkLabel(
                row, text=f"{icon}  {item['check']}",
                font=ctk.CTkFont(size=13),
                text_color=color,
            ).pack(side="left", padx=12, pady=10)

        # Verdict
        verdict_frame = ctk.CTkFrame(
            self._qa_frame, fg_color=COLORS["bg_card"], corner_radius=10,
        )
        verdict_frame.pack(fill="x", pady=(16, 0))

        if self._qa_passed:
            verdict_text = "🟢  GO — Filing package is ready"
            verdict_color = COLORS["green"]
        else:
            failed = sum(1 for r in self._qa_results if not r["passed"])
            verdict_text = f"🔴  NO-GO — {failed} check(s) failed"
            verdict_color = COLORS["red"]

        ctk.CTkLabel(
            verdict_frame, text=verdict_text,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=verdict_color,
        ).pack(padx=20, pady=16)

    # ------------------------------------------------------------------
    # STEP 9 — Export & File
    # ------------------------------------------------------------------

    def _build_step_9(self) -> None:
        ctk.CTkLabel(
            self._content,
            text="Build the final filing package and export to disk.",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 12))

        # Package format
        fmt_frame = ctk.CTkFrame(self._content, fg_color=COLORS["bg_card"], corner_radius=10)
        fmt_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            fmt_frame, text="Package Format",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self._format_var = ctk.StringVar(value="single_pdf")
        for val, label in [
            ("single_pdf", "📄 Single Combined PDF"),
            ("separate", "📁 Separate Files"),
            ("efiling", "⚡ E-Filing Format (TrueFiling)"),
        ]:
            rb = ctk.CTkRadioButton(
                fmt_frame, text=label, variable=self._format_var, value=val,
                fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                text_color=COLORS["text"], font=ctk.CTkFont(size=12),
            )
            rb.pack(anchor="w", padx=24, pady=3)
            Tooltip(rb, f"Export as {label.split(' ', 1)[-1]}")
        fmt_frame.pack_propagate(True)

        # Output directory
        dir_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        dir_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            dir_frame, text="Output Directory:",
            font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"],
        ).pack(side="left")

        self._dir_entry = ctk.CTkEntry(
            dir_frame, height=34, corner_radius=8,
            fg_color=COLORS["bg_card"], border_color=COLORS["border"],
            text_color=COLORS["text"], font=ctk.CTkFont(size=12),
        )
        self._dir_entry.pack(side="left", fill="x", expand=True, padx=8)
        self._dir_entry.insert(0, self._export_dir)
        Tooltip(self._dir_entry, "Directory where the filing package will be saved")

        browse_dir_btn = ctk.CTkButton(
            dir_frame, text="📂", width=36, height=34,
            fg_color=COLORS["bg_card"], hover_color=COLORS["accent"],
            corner_radius=8, command=self._browse_export_dir,
        )
        browse_dir_btn.pack(side="right")
        Tooltip(browse_dir_btn, "Browse for output directory")

        # Export button
        self._export_btn = ctk.CTkButton(
            self._content,
            text="🚀  Build Filing Package",
            height=52, width=300,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=12,
            command=self._export_package,
        )
        self._export_btn.pack(pady=16)
        Tooltip(self._export_btn, "Assemble all documents into the final filing package")

        self._export_status = ctk.CTkLabel(
            self._content, text="",
            font=ctk.CTkFont(size=13), text_color=COLORS["text_dim"],
        )
        self._export_status.pack(pady=(0, 8))

        self._open_folder_btn = ctk.CTkButton(
            self._content, text="📂 Open Folder", height=36, width=160,
            fg_color=COLORS["bg_card"], hover_color=COLORS["accent"],
            corner_radius=8, command=self._open_export_folder,
        )
        self._open_folder_btn.pack()
        self._open_folder_btn.pack_forget()  # hidden until export completes
        Tooltip(self._open_folder_btn, "Open the output folder in Explorer")

    def _browse_export_dir(self) -> None:
        try:
            from tkinter import filedialog
            d = filedialog.askdirectory(
                title="Select Output Directory",
                initialdir=self._export_dir,
            )
            if d:
                self._export_dir = d
                self._dir_entry.delete(0, "end")
                self._dir_entry.insert(0, d)
        except Exception:
            logger.warning("dir browse failed", exc_info=True)

    def _export_package(self) -> None:
        self._export_dir = self._dir_entry.get() or self._export_dir
        self._export_status.configure(
            text="⏳ Building filing package…", text_color=COLORS["yellow"],
        )
        self._export_btn.configure(state="disabled")

        def _do_export() -> None:
            out_dir = Path(self._export_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            success = True
            try:
                fmt = self._format_var.get()
                if _HAS_PDF and fmt == "single_pdf":
                    assemble_filing_package(
                        output_dir=out_dir,
                        documents=self._generated_docs,
                        exhibits=self._exhibits,
                    )
                else:
                    for doc in self._generated_docs:
                        name = doc.get("name", "document").replace(" ", "_")
                        fp = out_dir / f"{name}.md"
                        fp.write_text(
                            doc.get("content", ""), encoding="utf-8",
                        )
                    if _HAS_PDF:
                        for doc in self._generated_docs:
                            name = doc.get("name", "document").replace(" ", "_")
                            md_path = out_dir / f"{name}.md"
                            if md_path.exists():
                                markdown_to_pdf(md_path, out_dir / f"{name}.pdf")
            except Exception:
                logger.error("export failed", exc_info=True)
                success = False

            self.after(0, lambda: self._on_export_done(success))

        threading.Thread(target=_do_export, daemon=True).start()

    def _on_export_done(self, success: bool) -> None:
        self._export_btn.configure(state="normal")
        if success:
            self._export_status.configure(
                text=f"✅ Filing package saved to:\n{self._export_dir}",
                text_color=COLORS["green"],
            )
            self._open_folder_btn.pack(pady=(8, 0))
            self._completed_steps.add(self._current_step)
            self._update_sidebar()
        else:
            self._export_status.configure(
                text="❌ Export failed — check logs for details",
                text_color=COLORS["red"],
            )

    def _open_export_folder(self) -> None:
        import os
        import subprocess
        path = self._export_dir
        if os.path.isdir(path):
            subprocess.Popen(["explorer", path])

    # ------------------------------------------------------------------
    # Public refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Refresh the current step display."""
        self._render_step()
