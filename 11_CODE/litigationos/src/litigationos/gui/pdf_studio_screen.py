"""PDF Studio screen — visual tool for Bates stamping, form filling,
exhibit covers, and filing package assembly."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import customtkinter as ctk

from litigationos.gui.widgets import COLORS, ContextMenu, ProgressScore, Tooltip

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine imports — graceful fallback
# ---------------------------------------------------------------------------
try:
    from litigationos.engines.pdf_production import (
        assemble_filing_package,
        create_exhibit_cover,
        embed_pdf_metadata,
        fill_pdf_form,
        generate_toa,
        generate_toc,
        get_form_fields,
        stamp_bates_batch,
        stamp_bates_on_pdf,
    )

    _HAS_PDF = True
except ImportError:
    _HAS_PDF = False

try:
    from litigationos.engines.filing_assembler import FilingAssembler

    _HAS_ASSEMBLER = True
except ImportError:
    _HAS_ASSEMBLER = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PARTY_DATA: Dict[str, str] = {
    "plaintiff_name": "Andrew James Pigors",
    "plaintiff_address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
    "plaintiff_phone": "(231) 903-5690",
    "plaintiff_email": "andrewjpigors@gmail.com",
    "defendant_name": "Emily A. Watson",
    "defendant_address": "2160 Garland Drive, Norton Shores, MI 49441",
    "judge": "Hon. Jenny L. McNeill",
    "court": "14th Circuit Court, Family Division",
    "county": "Muskegon",
    "child_initials": "L.D.W.",
    "case_number": "2024-001507-DC",
}

_BATES_POSITIONS = ["bottom-right", "bottom-left", "top-right", "top-left"]

_FILING_TYPES = [
    "Motion",
    "Brief",
    "Petition",
    "Response",
    "Reply",
    "Emergency Motion",
    "Appellate Brief",
    "Complaint",
    "Affidavit",
    "Notice",
]

_LANE_CASES: Dict[str, str] = {
    "Lane A — Custody": "2024-001507-DC",
    "Lane B — Housing": "2025-002760-CZ",
    "Lane D — PPO": "2023-5907-PP",
    "Lane E — Misconduct": "2024-001507-DC",
    "Lane F — Appellate": "COA 366810",
}


# ═══════════════════════════════════════════════════════════════════════════
#  PDFStudioFrame
# ═══════════════════════════════════════════════════════════════════════════


class PDFStudioFrame(ctk.CTkFrame):
    """All-in-one PDF operations: Bates stamp, form fill, exhibit covers,
    and package assembly."""

    # ------------------------------------------------------------------
    #  Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        db: Optional["DatabaseManager"] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._busy = False

        # Collect file list for package assembly tab
        self._package_files: List[Path] = []
        # Exhibit batch list
        self._exhibit_batch: List[Dict[str, str]] = []
        # Form field widgets (label → entry)
        self._form_field_entries: Dict[str, ctk.CTkEntry] = {}

        self._build_ui()

    # ------------------------------------------------------------------
    #  Top-level layout
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the full screen: header, tabs, status bar."""
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
        )
        self._scroll.pack(fill="both", expand=True)

        self._build_header()
        self._build_tabs()
        self._build_status_bar()

    # ------------------------------------------------------------------
    #  Header
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        """Title bar with screen name and subtitle."""
        hdr = ctk.CTkFrame(
            self._scroll, fg_color=COLORS["bg_card"], corner_radius=12,
        )
        hdr.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            hdr,
            text="📄 PDF Studio",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(side="left", padx=16, pady=(12, 2))

        ctk.CTkLabel(
            hdr,
            text="Bates Stamp  •  Fill Forms  •  Build Exhibits  •  Assemble Packages",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(4, 16), pady=(12, 2))

        if not _HAS_PDF:
            ctk.CTkLabel(
                hdr,
                text="⚠ pdf_production engine not available",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["yellow"],
            ).pack(side="right", padx=16, pady=12)

    # ------------------------------------------------------------------
    #  Tab view
    # ------------------------------------------------------------------

    def _build_tabs(self) -> None:
        """Create four-tab interface inside a CTkTabview."""
        self._tabview = ctk.CTkTabview(
            self._scroll,
            fg_color=COLORS["bg_card"],
            segmented_button_fg_color=COLORS["bg_dark"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            segmented_button_unselected_color=COLORS["bg_dark"],
            segmented_button_unselected_hover_color=COLORS["border_light"],
            corner_radius=12,
        )
        self._tabview.pack(fill="both", expand=True, padx=16, pady=8)

        self._tab_bates = self._tabview.add("Bates Stamp")
        self._tab_form = self._tabview.add("Form Filler")
        self._tab_exhibit = self._tabview.add("Exhibit Covers")
        self._tab_package = self._tabview.add("Package Assembly")

        self._build_bates_tab()
        self._build_form_tab()
        self._build_exhibit_tab()
        self._build_package_tab()

    # ══════════════════════════════════════════════════════════════════
    #  TAB 1 — Bates Stamp
    # ══════════════════════════════════════════════════════════════════

    def _build_bates_tab(self) -> None:
        """Controls for applying Bates numbers to PDFs."""
        tab = self._tab_bates

        # --- Input file ---
        row_file = ctk.CTkFrame(tab, fg_color="transparent")
        row_file.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            row_file, text="Input PDF:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 6))

        self._bates_input_var = ctk.StringVar()
        inp = ctk.CTkEntry(
            row_file, textvariable=self._bates_input_var, width=360,
            corner_radius=8,
        )
        inp.pack(side="left", padx=4)
        Tooltip(inp, "Path to the PDF file to stamp")

        browse_btn = ctk.CTkButton(
            row_file, text="Browse…", width=90, corner_radius=8,
            fg_color=COLORS["border_light"],
            hover_color=COLORS["accent"],
            command=lambda: self._browse_file(self._bates_input_var),
        )
        browse_btn.pack(side="left", padx=4)
        Tooltip(browse_btn, "Select a PDF file from disk")

        # --- Options row 1: prefix + start number ---
        row_opts = ctk.CTkFrame(tab, fg_color="transparent")
        row_opts.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            row_opts, text="Prefix:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 4))

        self._bates_prefix_var = ctk.StringVar(value="PIGORS")
        prefix_entry = ctk.CTkEntry(
            row_opts, textvariable=self._bates_prefix_var, width=120,
            corner_radius=8,
        )
        prefix_entry.pack(side="left", padx=4)
        Tooltip(prefix_entry, "Text prefix before the Bates number (e.g. PIGORS)")

        ctk.CTkLabel(
            row_opts, text="Start #:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(16, 4))

        self._bates_start_var = ctk.StringVar(value="000001")
        start_entry = ctk.CTkEntry(
            row_opts, textvariable=self._bates_start_var, width=100,
            corner_radius=8,
        )
        start_entry.pack(side="left", padx=4)
        Tooltip(start_entry, "Starting Bates number (zero-padded)")

        # --- Options row 2: position + font size ---
        row_opts2 = ctk.CTkFrame(tab, fg_color="transparent")
        row_opts2.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            row_opts2, text="Position:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 4))

        self._bates_position_var = ctk.StringVar(value="bottom-right")
        pos_menu = ctk.CTkOptionMenu(
            row_opts2,
            variable=self._bates_position_var,
            values=_BATES_POSITIONS,
            width=150,
            fg_color=COLORS["bg_dark"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            corner_radius=8,
        )
        pos_menu.pack(side="left", padx=4)
        Tooltip(pos_menu, "Where to place the Bates stamp on each page")

        ctk.CTkLabel(
            row_opts2, text="Font size:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(16, 4))

        self._bates_fontsize_var = ctk.IntVar(value=10)
        font_slider = ctk.CTkSlider(
            row_opts2, from_=8, to=14, number_of_steps=6,
            variable=self._bates_fontsize_var, width=140,
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            progress_color=COLORS["accent_dim"],
        )
        font_slider.pack(side="left", padx=4)
        Tooltip(font_slider, "Bates stamp font size (8–14 pt)")

        self._fontsize_label = ctk.CTkLabel(
            row_opts2, text="10 pt", text_color=COLORS["text_dim"],
            font=ctk.CTkFont(size=12),
        )
        self._fontsize_label.pack(side="left", padx=4)
        self._bates_fontsize_var.trace_add(
            "write",
            lambda *_: self._fontsize_label.configure(
                text=f"{self._bates_fontsize_var.get()} pt",
            ),
        )

        # --- Output path ---
        row_out = ctk.CTkFrame(tab, fg_color="transparent")
        row_out.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            row_out, text="Output PDF:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 6))

        self._bates_output_var = ctk.StringVar()
        out_entry = ctk.CTkEntry(
            row_out, textvariable=self._bates_output_var, width=360,
            corner_radius=8,
        )
        out_entry.pack(side="left", padx=4)
        Tooltip(out_entry, "Where to save the stamped PDF")

        out_browse = ctk.CTkButton(
            row_out, text="Browse…", width=90, corner_radius=8,
            fg_color=COLORS["border_light"],
            hover_color=COLORS["accent"],
            command=lambda: self._browse_save(self._bates_output_var),
        )
        out_browse.pack(side="left", padx=4)
        Tooltip(out_browse, "Choose save location")

        # --- Action buttons ---
        row_actions = ctk.CTkFrame(tab, fg_color="transparent")
        row_actions.pack(fill="x", padx=12, pady=(12, 4))

        self._stamp_btn = ctk.CTkButton(
            row_actions,
            text="⬤  Stamp All",
            width=160,
            height=38,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            command=self._stamp_bates,
        )
        self._stamp_btn.pack(side="left", padx=4)
        Tooltip(self._stamp_btn, "Apply Bates stamps to every page of the PDF")

        # --- Progress bar ---
        self._bates_progress = ctk.CTkProgressBar(
            tab, height=10, corner_radius=6,
            progress_color=COLORS["accent"],
        )
        self._bates_progress.pack(fill="x", padx=12, pady=(8, 12))
        self._bates_progress.set(0)

    # ══════════════════════════════════════════════════════════════════
    #  TAB 2 — Form Filler
    # ══════════════════════════════════════════════════════════════════

    def _build_form_tab(self) -> None:
        """Controls for selecting a form template and filling fields."""
        tab = self._tab_form

        # --- Template selector ---
        row_tmpl = ctk.CTkFrame(tab, fg_color="transparent")
        row_tmpl.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            row_tmpl, text="Form template:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 6))

        self._form_template_var = ctk.StringVar()
        tmpl_entry = ctk.CTkEntry(
            row_tmpl, textvariable=self._form_template_var, width=340,
            corner_radius=8,
        )
        tmpl_entry.pack(side="left", padx=4)
        Tooltip(tmpl_entry, "Path to a fillable PDF template")

        tmpl_browse = ctk.CTkButton(
            row_tmpl, text="Browse…", width=90, corner_radius=8,
            fg_color=COLORS["border_light"],
            hover_color=COLORS["accent"],
            command=lambda: self._browse_file(self._form_template_var),
        )
        tmpl_browse.pack(side="left", padx=4)
        Tooltip(tmpl_browse, "Select a fillable PDF template")

        load_btn = ctk.CTkButton(
            row_tmpl, text="Load Fields", width=110, corner_radius=8,
            fg_color=COLORS["blue"],
            hover_color=COLORS["accent"],
            command=self._load_form_fields,
        )
        load_btn.pack(side="left", padx=4)
        Tooltip(load_btn, "Read AcroForm fields from the selected template")

        # --- Court form dropdown (populated from DB when available) ---
        row_court = ctk.CTkFrame(tab, fg_color="transparent")
        row_court.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            row_court, text="Court form:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 6))

        self._court_form_list = self._load_court_form_names()
        self._court_form_var = ctk.StringVar(
            value=self._court_form_list[0] if self._court_form_list else "",
        )
        court_menu = ctk.CTkOptionMenu(
            row_court,
            variable=self._court_form_var,
            values=self._court_form_list or ["(no court_forms.db)"],
            width=340,
            fg_color=COLORS["bg_dark"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            corner_radius=8,
        )
        court_menu.pack(side="left", padx=4)
        Tooltip(court_menu, "Select a Michigan SCAO court form")

        # --- Auto-fill button ---
        autofill_btn = ctk.CTkButton(
            row_court, text="Auto-Fill Party Data", width=160, corner_radius=8,
            fg_color=COLORS["green"], hover_color="#00a381",
            command=self._auto_fill_party_data,
        )
        autofill_btn.pack(side="left", padx=8)
        Tooltip(autofill_btn, "Populate known party info (Pigors, Watson, McNeill …)")

        # --- Scrollable fields area ---
        self._fields_frame = ctk.CTkScrollableFrame(
            tab, fg_color=COLORS["bg_dark"], corner_radius=10, height=220,
        )
        self._fields_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self._fields_placeholder = ctk.CTkLabel(
            self._fields_frame,
            text="Load a PDF template to see fillable fields",
            text_color=COLORS["text_dim"],
            font=ctk.CTkFont(size=12, slant="italic"),
        )
        self._fields_placeholder.pack(padx=12, pady=24)

        # --- Output + save ---
        row_save = ctk.CTkFrame(tab, fg_color="transparent")
        row_save.pack(fill="x", padx=12, pady=(4, 4))

        ctk.CTkLabel(
            row_save, text="Output PDF:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 6))

        self._form_output_var = ctk.StringVar()
        form_out = ctk.CTkEntry(
            row_save, textvariable=self._form_output_var, width=340,
            corner_radius=8,
        )
        form_out.pack(side="left", padx=4)
        Tooltip(form_out, "Save location for the filled form")

        form_out_browse = ctk.CTkButton(
            row_save, text="Browse…", width=90, corner_radius=8,
            fg_color=COLORS["border_light"],
            hover_color=COLORS["accent"],
            command=lambda: self._browse_save(self._form_output_var),
        )
        form_out_browse.pack(side="left", padx=4)

        self._fill_btn = ctk.CTkButton(
            row_save, text="⬤  Fill & Save", width=140, height=36,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            command=self._fill_form,
        )
        self._fill_btn.pack(side="right", padx=4)
        Tooltip(self._fill_btn, "Fill all fields and save the completed PDF")

    # ══════════════════════════════════════════════════════════════════
    #  TAB 3 — Exhibit Covers
    # ══════════════════════════════════════════════════════════════════

    def _build_exhibit_tab(self) -> None:
        """Controls for generating exhibit cover pages."""
        tab = self._tab_exhibit

        # --- Single cover fields ---
        row1 = ctk.CTkFrame(tab, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            row1, text="Exhibit #:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 4))

        self._exhibit_num_var = ctk.StringVar(value="A")
        num_entry = ctk.CTkEntry(
            row1, textvariable=self._exhibit_num_var, width=60, corner_radius=8,
        )
        num_entry.pack(side="left", padx=4)
        Tooltip(num_entry, "Exhibit letter or number (A, B, 1, 2 …)")

        ctk.CTkLabel(
            row1, text="Title:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(16, 4))

        self._exhibit_title_var = ctk.StringVar()
        title_entry = ctk.CTkEntry(
            row1, textvariable=self._exhibit_title_var, width=300, corner_radius=8,
        )
        title_entry.pack(side="left", padx=4)
        Tooltip(title_entry, "Short descriptive title for the exhibit")

        # --- Case info row ---
        row2 = ctk.CTkFrame(tab, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            row2, text="Case:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 4))

        lane_values = list(_LANE_CASES.keys())
        self._exhibit_lane_var = ctk.StringVar(value=lane_values[0])
        lane_menu = ctk.CTkOptionMenu(
            row2,
            variable=self._exhibit_lane_var,
            values=lane_values,
            width=220,
            fg_color=COLORS["bg_dark"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            corner_radius=8,
            command=self._on_lane_changed,
        )
        lane_menu.pack(side="left", padx=4)
        Tooltip(lane_menu, "Select the litigation lane")

        ctk.CTkLabel(
            row2, text="Case #:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(16, 4))

        self._exhibit_case_var = ctk.StringVar(
            value=_LANE_CASES.get(lane_values[0], ""),
        )
        case_entry = ctk.CTkEntry(
            row2, textvariable=self._exhibit_case_var, width=160, corner_radius=8,
        )
        case_entry.pack(side="left", padx=4)
        Tooltip(case_entry, "Case number (auto-filled from lane)")

        # --- Description ---
        ctk.CTkLabel(
            tab, text="Description:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self._exhibit_desc = ctk.CTkTextbox(
            tab, height=80, corner_radius=8,
            fg_color=COLORS["bg_dark"], text_color=COLORS["text"],
        )
        self._exhibit_desc.pack(fill="x", padx=12, pady=(0, 8))
        Tooltip(self._exhibit_desc, "Optional description shown on the cover page")

        # --- Buttons ---
        row_btns = ctk.CTkFrame(tab, fg_color="transparent")
        row_btns.pack(fill="x", padx=12, pady=4)

        gen_btn = ctk.CTkButton(
            row_btns, text="⬤  Generate Cover", width=160, height=36,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10,
            command=self._generate_cover,
        )
        gen_btn.pack(side="left", padx=4)
        Tooltip(gen_btn, "Create a single exhibit cover page PDF")

        add_batch_btn = ctk.CTkButton(
            row_btns, text="+ Add to Batch", width=130, corner_radius=8,
            fg_color=COLORS["blue"], hover_color=COLORS["accent"],
            command=self._add_exhibit_to_batch,
        )
        add_batch_btn.pack(side="left", padx=8)
        Tooltip(add_batch_btn, "Queue this exhibit for batch generation")

        gen_all_btn = ctk.CTkButton(
            row_btns, text="Generate All", width=120, corner_radius=8,
            fg_color=COLORS["green"], hover_color="#00a381",
            command=self._generate_batch_covers,
        )
        gen_all_btn.pack(side="left", padx=4)
        Tooltip(gen_all_btn, "Generate cover pages for all queued exhibits")

        clear_btn = ctk.CTkButton(
            row_btns, text="Clear Batch", width=100, corner_radius=8,
            fg_color=COLORS["border_light"], hover_color=COLORS["red"],
            command=self._clear_exhibit_batch,
        )
        clear_btn.pack(side="left", padx=4)
        Tooltip(clear_btn, "Remove all exhibits from the batch queue")

        # --- Batch list ---
        self._batch_list_frame = ctk.CTkScrollableFrame(
            tab, fg_color=COLORS["bg_dark"], corner_radius=10, height=100,
        )
        self._batch_list_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self._batch_placeholder = ctk.CTkLabel(
            self._batch_list_frame,
            text="No exhibits queued — add items above",
            text_color=COLORS["text_dim"],
            font=ctk.CTkFont(size=12, slant="italic"),
        )
        self._batch_placeholder.pack(padx=12, pady=16)

    # ══════════════════════════════════════════════════════════════════
    #  TAB 4 — Package Assembly
    # ══════════════════════════════════════════════════════════════════

    def _build_package_tab(self) -> None:
        """Controls for merging documents into a court filing package."""
        tab = self._tab_package

        # --- Filing type ---
        row_type = ctk.CTkFrame(tab, fg_color="transparent")
        row_type.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            row_type, text="Filing type:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 6))

        self._pkg_type_var = ctk.StringVar(value=_FILING_TYPES[0])
        type_menu = ctk.CTkOptionMenu(
            row_type,
            variable=self._pkg_type_var,
            values=_FILING_TYPES,
            width=200,
            fg_color=COLORS["bg_dark"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            corner_radius=8,
        )
        type_menu.pack(side="left", padx=4)
        Tooltip(type_menu, "Select the type of court filing")

        ctk.CTkLabel(
            row_type, text="Output filename:", text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(16, 6))

        self._pkg_output_var = ctk.StringVar(value="filing_package.pdf")
        pkg_out = ctk.CTkEntry(
            row_type, textvariable=self._pkg_output_var, width=240, corner_radius=8,
        )
        pkg_out.pack(side="left", padx=4)
        Tooltip(pkg_out, "Filename for the assembled PDF package")

        # --- File list management ---
        row_files = ctk.CTkFrame(tab, fg_color="transparent")
        row_files.pack(fill="x", padx=12, pady=4)

        add_file_btn = ctk.CTkButton(
            row_files, text="+ Add Files…", width=120, corner_radius=8,
            fg_color=COLORS["blue"], hover_color=COLORS["accent"],
            command=self._add_package_files,
        )
        add_file_btn.pack(side="left", padx=4)
        Tooltip(add_file_btn, "Browse and add PDF files to the package")

        self._move_up_btn = ctk.CTkButton(
            row_files, text="▲ Up", width=70, corner_radius=8,
            fg_color=COLORS["border_light"], hover_color=COLORS["accent"],
            command=lambda: self._reorder_file(-1),
        )
        self._move_up_btn.pack(side="left", padx=4)
        Tooltip(self._move_up_btn, "Move the selected file up in the list")

        self._move_down_btn = ctk.CTkButton(
            row_files, text="▼ Down", width=70, corner_radius=8,
            fg_color=COLORS["border_light"], hover_color=COLORS["accent"],
            command=lambda: self._reorder_file(1),
        )
        self._move_down_btn.pack(side="left", padx=4)
        Tooltip(self._move_down_btn, "Move the selected file down in the list")

        remove_btn = ctk.CTkButton(
            row_files, text="✕ Remove", width=90, corner_radius=8,
            fg_color=COLORS["border_light"], hover_color=COLORS["red"],
            command=self._remove_selected_file,
        )
        remove_btn.pack(side="left", padx=4)
        Tooltip(remove_btn, "Remove the selected file from the package")

        # --- File listbox ---
        self._file_list_frame = ctk.CTkScrollableFrame(
            tab, fg_color=COLORS["bg_dark"], corner_radius=10, height=130,
        )
        self._file_list_frame.pack(fill="both", expand=True, padx=12, pady=4)
        self._file_labels: List[ctk.CTkLabel] = []
        self._selected_file_idx: Optional[int] = None

        self._file_placeholder = ctk.CTkLabel(
            self._file_list_frame,
            text="No files added — click '+ Add Files…' to begin",
            text_color=COLORS["text_dim"],
            font=ctk.CTkFont(size=12, slant="italic"),
        )
        self._file_placeholder.pack(padx=12, pady=24)

        # --- Options ---
        row_opts = ctk.CTkFrame(tab, fg_color="transparent")
        row_opts.pack(fill="x", padx=12, pady=4)

        self._include_toc_var = ctk.BooleanVar(value=False)
        toc_cb = ctk.CTkCheckBox(
            row_opts, text="Include TOC", variable=self._include_toc_var,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=4,
        )
        toc_cb.pack(side="left", padx=8)
        Tooltip(toc_cb, "Generate a Table of Contents page")

        self._include_toa_var = ctk.BooleanVar(value=False)
        toa_cb = ctk.CTkCheckBox(
            row_opts, text="Include TOA", variable=self._include_toa_var,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=4,
        )
        toa_cb.pack(side="left", padx=8)
        Tooltip(toa_cb, "Generate a Table of Authorities page")

        self._include_cert_var = ctk.BooleanVar(value=False)
        cert_cb = ctk.CTkCheckBox(
            row_opts, text="Include Service Cert", variable=self._include_cert_var,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            corner_radius=4,
        )
        cert_cb.pack(side="left", padx=8)
        Tooltip(cert_cb, "Append a Certificate of Service page")

        # --- Assemble button + progress ---
        row_assemble = ctk.CTkFrame(tab, fg_color="transparent")
        row_assemble.pack(fill="x", padx=12, pady=(8, 4))

        self._assemble_btn = ctk.CTkButton(
            row_assemble,
            text="⬤  Assemble Package",
            width=180,
            height=38,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            command=self._assemble_package,
        )
        self._assemble_btn.pack(side="left", padx=4)
        Tooltip(self._assemble_btn, "Merge all files into a single court-ready PDF")

        self._pkg_status_label = ctk.CTkLabel(
            row_assemble, text="", text_color=COLORS["text_dim"],
            font=ctk.CTkFont(size=12),
        )
        self._pkg_status_label.pack(side="left", padx=12)

        self._pkg_progress = ctk.CTkProgressBar(
            tab, height=10, corner_radius=6,
            progress_color=COLORS["accent"],
        )
        self._pkg_progress.pack(fill="x", padx=12, pady=(4, 12))
        self._pkg_progress.set(0)

    # ------------------------------------------------------------------
    #  Status bar
    # ------------------------------------------------------------------

    def _build_status_bar(self) -> None:
        """Bottom bar showing last operation result and stats."""
        bar = ctk.CTkFrame(
            self._scroll, fg_color=COLORS["bg_card"], corner_radius=10,
        )
        bar.pack(fill="x", padx=16, pady=(4, 16))

        self._status_label = ctk.CTkLabel(
            bar,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        )
        self._status_label.pack(side="left", padx=12, pady=8)

        self._stats_label = ctk.CTkLabel(
            bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        )
        self._stats_label.pack(side="right", padx=12, pady=8)

    # ══════════════════════════════════════════════════════════════════
    #  Actions
    # ══════════════════════════════════════════════════════════════════

    def _stamp_bates(self) -> None:
        """Stamp Bates numbers on the selected PDF (threaded)."""
        if self._busy:
            return
        if not _HAS_PDF:
            self._update_status("pdf_production engine not available", is_error=True)
            return

        input_path = self._bates_input_var.get().strip()
        output_path = self._bates_output_var.get().strip()
        if not input_path:
            self._update_status("Select an input PDF first", is_error=True)
            return
        if not output_path:
            output_path = str(
                Path(input_path).with_stem(Path(input_path).stem + "_bates"),
            )
            self._bates_output_var.set(output_path)

        self._set_busy(True)
        self._bates_progress.set(0)
        self._update_status("Stamping…")

        def _work() -> None:
            try:
                start = int(self._bates_start_var.get())
            except ValueError:
                start = 1

            try:
                result_path, page_count = stamp_bates_on_pdf(
                    input_pdf=input_path,
                    output_pdf=output_path,
                    start_number=start,
                    prefix=self._bates_prefix_var.get(),
                    position=self._bates_position_var.get(),
                    font_size=self._bates_fontsize_var.get(),
                )
                self.after(
                    0,
                    self._finish_bates,
                    str(result_path),
                    page_count,
                    None,
                )
            except Exception as exc:
                logger.exception("Bates stamping failed")
                self.after(0, self._finish_bates, "", 0, str(exc))

        threading.Thread(target=_work, daemon=True).start()

    def _finish_bates(
        self, path: str, pages: int, error: Optional[str],
    ) -> None:
        """Callback on main thread after Bates stamping completes."""
        self._bates_progress.set(1.0)
        self._set_busy(False)
        if error:
            self._update_status(f"Bates error: {error}", is_error=True)
        else:
            self._update_status(f"✓ Stamped {pages} pages → {Path(path).name}")
            self._stats_label.configure(text=f"{pages} pages stamped")

    def _fill_form(self) -> None:
        """Fill the selected PDF form with current field values (threaded)."""
        if self._busy:
            return
        if not _HAS_PDF:
            self._update_status("pdf_production engine not available", is_error=True)
            return

        template = self._form_template_var.get().strip()
        output = self._form_output_var.get().strip()
        if not template:
            self._update_status("Select a form template first", is_error=True)
            return
        if not output:
            output = str(Path(template).with_stem(Path(template).stem + "_filled"))
            self._form_output_var.set(output)

        field_values: Dict[str, str] = {
            name: entry.get() for name, entry in self._form_field_entries.items()
        }

        self._set_busy(True)
        self._update_status("Filling form…")

        def _work() -> None:
            try:
                result_path = fill_pdf_form(
                    template_pdf=template,
                    output_pdf=output,
                    field_values=field_values,
                    flatten=True,
                )
                self.after(
                    0,
                    self._finish_fill,
                    str(result_path),
                    len(field_values),
                    None,
                )
            except Exception as exc:
                logger.exception("Form fill failed")
                self.after(0, self._finish_fill, "", 0, str(exc))

        threading.Thread(target=_work, daemon=True).start()

    def _finish_fill(
        self, path: str, field_count: int, error: Optional[str],
    ) -> None:
        """Callback on main thread after form fill completes."""
        self._set_busy(False)
        if error:
            self._update_status(f"Form fill error: {error}", is_error=True)
        else:
            self._update_status(
                f"✓ Filled {field_count} fields → {Path(path).name}",
            )

    def _generate_cover(self) -> None:
        """Create a single exhibit cover page (threaded)."""
        if self._busy:
            return
        if not _HAS_PDF:
            self._update_status("pdf_production engine not available", is_error=True)
            return

        exhibit_num = self._exhibit_num_var.get().strip()
        title = self._exhibit_title_var.get().strip()
        if not exhibit_num or not title:
            self._update_status("Exhibit # and title are required", is_error=True)
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"Exhibit_{exhibit_num}_Cover.pdf",
            title="Save exhibit cover",
        )
        if not save_path:
            return

        self._set_busy(True)
        self._update_status("Generating exhibit cover…")

        def _work() -> None:
            try:
                result = create_exhibit_cover(
                    exhibit_num=exhibit_num,
                    title=title,
                    output_pdf=save_path,
                )
                self.after(0, self._finish_cover, str(result), None)
            except Exception as exc:
                logger.exception("Exhibit cover generation failed")
                self.after(0, self._finish_cover, "", str(exc))

        threading.Thread(target=_work, daemon=True).start()

    def _finish_cover(self, path: str, error: Optional[str]) -> None:
        """Callback on main thread after cover generation completes."""
        self._set_busy(False)
        if error:
            self._update_status(f"Cover error: {error}", is_error=True)
        else:
            self._update_status(f"✓ Cover created → {Path(path).name}")

    def _assemble_package(self) -> None:
        """Merge all listed files into one court-ready PDF (threaded)."""
        if self._busy:
            return
        if not _HAS_PDF:
            self._update_status("pdf_production engine not available", is_error=True)
            return
        if not self._package_files:
            self._update_status("Add files to the package first", is_error=True)
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=self._pkg_output_var.get() or "filing_package.pdf",
            title="Save assembled package",
        )
        if not save_path:
            return

        self._set_busy(True)
        self._pkg_progress.set(0)
        self._pkg_status_label.configure(text="Assembling…")
        self._update_status("Assembling filing package…")

        include_toc = self._include_toc_var.get()
        include_toa = self._include_toa_var.get()
        files = list(self._package_files)

        def _work() -> None:
            try:
                result = assemble_filing_package(
                    component_pdfs=files,
                    output_pdf=save_path,
                )
                self.after(
                    0,
                    self._finish_assemble,
                    str(result),
                    len(files),
                    None,
                )
            except Exception as exc:
                logger.exception("Package assembly failed")
                self.after(0, self._finish_assemble, "", 0, str(exc))

        threading.Thread(target=_work, daemon=True).start()

    def _finish_assemble(
        self, path: str, file_count: int, error: Optional[str],
    ) -> None:
        """Callback on main thread after package assembly completes."""
        self._pkg_progress.set(1.0)
        self._set_busy(False)
        if error:
            self._pkg_status_label.configure(
                text=f"Error: {error[:60]}", text_color=COLORS["red"],
            )
            self._update_status(f"Assembly error: {error}", is_error=True)
        else:
            self._pkg_status_label.configure(
                text=f"✓ {file_count} files merged", text_color=COLORS["green"],
            )
            self._update_status(f"✓ Package assembled → {Path(path).name}")
            self._stats_label.configure(text=f"{file_count} files merged")

    # ══════════════════════════════════════════════════════════════════
    #  Helpers
    # ══════════════════════════════════════════════════════════════════

    def _browse_file(self, target_var: ctk.StringVar) -> None:
        """Open a file dialog and store the selected path."""
        path = filedialog.askopenfilename(
            filetypes=[("PDF", "*.pdf"), ("All files", "*.*")],
            title="Select a file",
        )
        if path:
            target_var.set(path)

    def _browse_save(self, target_var: ctk.StringVar) -> None:
        """Open a save-file dialog and store the chosen path."""
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Save as",
        )
        if path:
            target_var.set(path)

    def _auto_fill_party_data(self) -> None:
        """Populate form fields with known party information."""
        filled = 0
        for field_name, entry in self._form_field_entries.items():
            lower = field_name.lower().replace(" ", "_").replace("-", "_")
            for key, value in PARTY_DATA.items():
                if key in lower or lower in key:
                    entry.delete(0, "end")
                    entry.insert(0, value)
                    filled += 1
                    break
        self._update_status(f"Auto-filled {filled} fields with party data")

    def _update_status(self, message: str, *, is_error: bool = False) -> None:
        """Update the bottom status bar text and colour."""
        color = COLORS["red"] if is_error else COLORS["green"]
        self._status_label.configure(text=message, text_color=color)
        if is_error:
            logger.warning("PDF Studio: %s", message)
        else:
            logger.info("PDF Studio: %s", message)

    def _set_busy(self, busy: bool) -> None:
        """Toggle the busy flag and disable/enable action buttons."""
        self._busy = busy
        state = "disabled" if busy else "normal"
        for btn in (
            self._stamp_btn,
            self._fill_btn,
            self._assemble_btn,
        ):
            btn.configure(state=state)

    # --- Form field loading ---

    def _load_form_fields(self) -> None:
        """Read AcroForm fields from the selected template and build entries."""
        template = self._form_template_var.get().strip()
        if not template:
            self._update_status("Select a template PDF first", is_error=True)
            return
        if not _HAS_PDF:
            self._update_status("pdf_production engine not available", is_error=True)
            return

        try:
            fields = get_form_fields(template)
        except Exception as exc:
            logger.exception("Failed to read form fields")
            self._update_status(f"Error reading fields: {exc}", is_error=True)
            return

        # Clear existing field widgets
        for w in self._fields_frame.winfo_children():
            w.destroy()
        self._form_field_entries.clear()

        if not fields:
            ctk.CTkLabel(
                self._fields_frame,
                text="No fillable fields found in this PDF",
                text_color=COLORS["text_dim"],
                font=ctk.CTkFont(size=12, slant="italic"),
            ).pack(padx=12, pady=24)
            return

        for field in fields:
            name = field.get("name", field.get("field_name", "unknown"))
            current_val = field.get("value", "")

            row = ctk.CTkFrame(self._fields_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)

            ctk.CTkLabel(
                row, text=name, width=180, anchor="w",
                text_color=COLORS["text"], font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=(4, 8))

            entry = ctk.CTkEntry(row, width=280, corner_radius=6)
            entry.pack(side="left", padx=4, fill="x", expand=True)
            if current_val:
                entry.insert(0, str(current_val))

            self._form_field_entries[name] = entry

        self._update_status(f"Loaded {len(fields)} form fields")

    def _load_court_form_names(self) -> List[str]:
        """Attempt to load court form names from court_forms.db."""
        forms: List[str] = []
        try:
            import sqlite3

            db_path = Path(
                r"C:\Users\andre\LitigationOS\databases\court_forms.db",
            )
            if not db_path.exists():
                return forms
            conn = sqlite3.connect(str(db_path), timeout=10)
            try:
                rows = conn.execute(
                    "SELECT form_number, title FROM court_forms "
                    "ORDER BY form_number LIMIT 100",
                ).fetchall()
                forms = [f"{r[0]} — {r[1]}" for r in rows]
            except Exception:
                # Table may not exist or have different schema
                pass
            finally:
                conn.close()
        except Exception:
            pass
        return forms

    # --- Exhibit batch helpers ---

    def _on_lane_changed(self, choice: str) -> None:
        """Update the case number when the lane dropdown changes."""
        self._exhibit_case_var.set(_LANE_CASES.get(choice, ""))

    def _add_exhibit_to_batch(self) -> None:
        """Add the current exhibit to the batch queue."""
        num = self._exhibit_num_var.get().strip()
        title = self._exhibit_title_var.get().strip()
        if not num or not title:
            self._update_status("Exhibit # and title are required", is_error=True)
            return

        self._exhibit_batch.append({
            "num": num,
            "title": title,
            "case": self._exhibit_case_var.get(),
            "desc": self._exhibit_desc.get("1.0", "end-1c").strip(),
        })
        self._refresh_batch_list()
        self._update_status(
            f"Added Exhibit {num} to batch ({len(self._exhibit_batch)} queued)",
        )

    def _clear_exhibit_batch(self) -> None:
        """Remove all items from the batch queue."""
        self._exhibit_batch.clear()
        self._refresh_batch_list()
        self._update_status("Batch cleared")

    def _refresh_batch_list(self) -> None:
        """Rebuild the visual batch list from self._exhibit_batch."""
        for w in self._batch_list_frame.winfo_children():
            w.destroy()

        if not self._exhibit_batch:
            self._batch_placeholder = ctk.CTkLabel(
                self._batch_list_frame,
                text="No exhibits queued — add items above",
                text_color=COLORS["text_dim"],
                font=ctk.CTkFont(size=12, slant="italic"),
            )
            self._batch_placeholder.pack(padx=12, pady=16)
            return

        for idx, item in enumerate(self._exhibit_batch):
            row = ctk.CTkFrame(self._batch_list_frame, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=1)

            ctk.CTkLabel(
                row,
                text=f"  Ex. {item['num']}  —  {item['title']}  [{item['case']}]",
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=12),
                anchor="w",
            ).pack(side="left", padx=4)

            rm_btn = ctk.CTkButton(
                row, text="✕", width=28, height=24, corner_radius=4,
                fg_color="transparent", hover_color=COLORS["red"],
                text_color=COLORS["text_dim"],
                command=lambda i=idx: self._remove_batch_item(i),
            )
            rm_btn.pack(side="right", padx=4)

    def _remove_batch_item(self, idx: int) -> None:
        """Remove a single item from the batch by index."""
        if 0 <= idx < len(self._exhibit_batch):
            removed = self._exhibit_batch.pop(idx)
            self._refresh_batch_list()
            self._update_status(f"Removed Exhibit {removed['num']} from batch")

    def _generate_batch_covers(self) -> None:
        """Generate cover pages for all queued exhibits (threaded)."""
        if self._busy:
            return
        if not _HAS_PDF:
            self._update_status("pdf_production engine not available", is_error=True)
            return
        if not self._exhibit_batch:
            self._update_status("No exhibits in batch", is_error=True)
            return

        out_dir = filedialog.askdirectory(title="Select output folder for covers")
        if not out_dir:
            return

        self._set_busy(True)
        batch = list(self._exhibit_batch)
        self._update_status(f"Generating {len(batch)} exhibit covers…")

        def _work() -> None:
            created = 0
            errors: List[str] = []
            for item in batch:
                try:
                    out_path = Path(out_dir) / f"Exhibit_{item['num']}_Cover.pdf"
                    create_exhibit_cover(
                        exhibit_num=item["num"],
                        title=item["title"],
                        output_pdf=str(out_path),
                    )
                    created += 1
                except Exception as exc:
                    errors.append(f"Ex. {item['num']}: {exc}")
            self.after(0, self._finish_batch_covers, created, errors)

        threading.Thread(target=_work, daemon=True).start()

    def _finish_batch_covers(
        self, created: int, errors: List[str],
    ) -> None:
        """Callback on main thread after batch cover generation completes."""
        self._set_busy(False)
        if errors:
            self._update_status(
                f"Created {created}, {len(errors)} errors: {errors[0]}",
                is_error=True,
            )
        else:
            self._update_status(f"✓ Generated {created} exhibit covers")

    # --- Package file list helpers ---

    def _add_package_files(self) -> None:
        """Browse for PDF files and add them to the package list."""
        paths = filedialog.askopenfilenames(
            filetypes=[("PDF", "*.pdf"), ("All files", "*.*")],
            title="Select files for the package",
        )
        if not paths:
            return
        for p in paths:
            self._package_files.append(Path(p))
        self._refresh_file_list()
        self._update_status(f"{len(paths)} file(s) added to package")

    def _refresh_file_list(self) -> None:
        """Rebuild the visual file list from self._package_files."""
        for w in self._file_list_frame.winfo_children():
            w.destroy()
        self._file_labels.clear()

        if not self._package_files:
            self._selected_file_idx = None
            self._file_placeholder = ctk.CTkLabel(
                self._file_list_frame,
                text="No files added — click '+ Add Files…' to begin",
                text_color=COLORS["text_dim"],
                font=ctk.CTkFont(size=12, slant="italic"),
            )
            self._file_placeholder.pack(padx=12, pady=24)
            return

        for idx, fp in enumerate(self._package_files):
            lbl = ctk.CTkLabel(
                self._file_list_frame,
                text=f"  {idx + 1}.  {fp.name}",
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=12),
                anchor="w",
                cursor="hand2",
            )
            lbl.pack(fill="x", padx=4, pady=1)
            lbl.bind(
                "<Button-1>", lambda e, i=idx: self._select_file(i),
            )
            ContextMenu(lbl, [
                ("Remove", lambda i=idx: self._remove_file_at(i)),
                ("---", None),
                ("Move to top", lambda i=idx: self._move_file_to(i, 0)),
            ])
            self._file_labels.append(lbl)

        if self._selected_file_idx is not None:
            self._highlight_file(self._selected_file_idx)

    def _select_file(self, idx: int) -> None:
        """Mark a file as selected in the list."""
        self._selected_file_idx = idx
        self._highlight_file(idx)

    def _highlight_file(self, idx: int) -> None:
        """Visually highlight the selected file row."""
        for i, lbl in enumerate(self._file_labels):
            if i == idx:
                lbl.configure(
                    fg_color=COLORS["accent_dim"], corner_radius=4,
                )
            else:
                lbl.configure(fg_color="transparent")

    def _reorder_file(self, direction: int) -> None:
        """Move the selected file up (-1) or down (+1)."""
        idx = self._selected_file_idx
        if idx is None or not self._package_files:
            return
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._package_files):
            return
        self._package_files[idx], self._package_files[new_idx] = (
            self._package_files[new_idx],
            self._package_files[idx],
        )
        self._selected_file_idx = new_idx
        self._refresh_file_list()

    def _move_file_to(self, from_idx: int, to_idx: int) -> None:
        """Move a file from one position to another."""
        if from_idx == to_idx or not self._package_files:
            return
        item = self._package_files.pop(from_idx)
        self._package_files.insert(to_idx, item)
        self._selected_file_idx = to_idx
        self._refresh_file_list()

    def _remove_selected_file(self) -> None:
        """Remove the currently selected file from the package list."""
        idx = self._selected_file_idx
        if idx is not None and 0 <= idx < len(self._package_files):
            self._remove_file_at(idx)

    def _remove_file_at(self, idx: int) -> None:
        """Remove a file by index."""
        if 0 <= idx < len(self._package_files):
            removed = self._package_files.pop(idx)
            self._selected_file_idx = None
            self._refresh_file_list()
            self._update_status(f"Removed {removed.name}")
