"""Evidence Map — Visual graph of claims linked to evidence.

Displays claims with their supporting evidence items and highlights
gaps where a claim has no linked evidence.  Uses EvidenceEngine for
gap analysis and evidence listing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import customtkinter as ctk

from litigationos.gui.widgets import COLORS

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# Engine import -- graceful fallback
try:
    from litigationos.engines.evidence import EvidenceEngine
    _HAS_EVIDENCE_ENGINE = True
except ImportError:
    _HAS_EVIDENCE_ENGINE = False


class EvidenceMapFrame(ctk.CTkFrame):
    """Visual evidence-to-claims mapping with gap analysis."""

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
        self._build_ui()
        self.refresh()

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
            text="🗺  EVIDENCE MAP",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkButton(
            hdr, text="⟳  Refresh", width=100, command=self.refresh,
            fg_color=COLORS["blue"], hover_color=COLORS["accent"], corner_radius=8,
        ).pack(side="right", padx=16, pady=12)

        # Stats bar
        stats = ctk.CTkFrame(self._scroll, fg_color=COLORS["bg_card"], corner_radius=10)
        stats.pack(fill="x", padx=16, pady=4)
        stats.columnconfigure((0, 1, 2), weight=1)

        self._evidence_label = ctk.CTkLabel(
            stats, text="Evidence: —",
            font=ctk.CTkFont(size=14), text_color=COLORS["text"],
        )
        self._evidence_label.grid(row=0, column=0, padx=20, pady=8)

        self._claims_label = ctk.CTkLabel(
            stats, text="Claims: —",
            font=ctk.CTkFont(size=14), text_color=COLORS["text"],
        )
        self._claims_label.grid(row=0, column=1, padx=20, pady=8)

        self._gaps_label = ctk.CTkLabel(
            stats, text="Gaps: —",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["orange"],
        )
        self._gaps_label.grid(row=0, column=2, padx=20, pady=8)

        # Claims list
        ctk.CTkLabel(
            self._scroll, text="Claims & Evidence",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_dim"], anchor="w",
        ).pack(anchor="w", padx=16, pady=(8, 2))

        self._claims_container = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._claims_container.pack(fill="both", expand=True, padx=16, pady=4)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def refresh(self):
        """Reload statistics and claim/evidence list from the database."""
        self._load_stats()
        self._load_claims()

    def _load_stats(self):
        evidence_count = 0
        claims_count = 0
        gap_count = 0

        if self._db:
            try:
                row = self._db.fetchone("SELECT COUNT(*) FROM evidence")
                evidence_count = row[0] if row else 0
            except Exception:
                logger.debug("evidence table not available")

            try:
                row = self._db.fetchone("SELECT COUNT(*) FROM claims")
                claims_count = row[0] if row else 0
            except Exception:
                logger.debug("claims table not available")

            # Use engine for gap analysis across all active cases
            if _HAS_EVIDENCE_ENGINE:
                try:
                    engine = EvidenceEngine(self._db)
                    case_rows = self._db.fetchall(
                        "SELECT id FROM cases WHERE status = 'active'",
                    )
                    for cr in case_rows:
                        try:
                            gaps = engine.check_gaps(dict(cr)["id"])
                            gap_count += len(gaps)
                        except Exception:
                            pass
                except Exception:
                    logger.debug("EvidenceEngine gap analysis failed")

        self._evidence_label.configure(text=f"Evidence: {evidence_count:,}")
        self._claims_label.configure(text=f"Claims: {claims_count:,}")
        gap_color = COLORS["red"] if gap_count > 0 else COLORS["green"]
        self._gaps_label.configure(text=f"Gaps: {gap_count}", text_color=gap_color)

    def _load_claims(self):
        for w in self._claims_container.winfo_children():
            w.destroy()

        if not self._db:
            self._placeholder("Database not available")
            return

        try:
            rows = self._db.fetchall(
                "SELECT id, title, description FROM claims ORDER BY id",
            )
        except Exception:
            self._placeholder("No claims data found")
            return

        if not rows:
            self._placeholder("No claims recorded yet")
            return

        # Get all evidence for linking
        all_evidence: dict[int, list[dict]] = {}
        if _HAS_EVIDENCE_ENGINE:
            try:
                engine = EvidenceEngine(self._db)
                case_rows = self._db.fetchall("SELECT DISTINCT id FROM cases")
                for cr in case_rows:
                    cid = dict(cr)["id"]
                    ev_list = engine.get_evidence(case_id=cid)
                    all_evidence[cid] = ev_list
            except Exception:
                pass

        gaps = 0
        for row in rows:
            claim = dict(row)
            claim_id = claim["id"]

            frame = ctk.CTkFrame(
                self._claims_container, fg_color=COLORS["bg_card"], corner_radius=8,
            )
            frame.pack(fill="x", pady=3)

            ctk.CTkLabel(
                frame, text=claim.get("title", f"Claim #{claim_id}"),
                font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text"],
            ).pack(anchor="w", padx=12, pady=(8, 2))

            # Count linked evidence
            try:
                erow = self._db.fetchone(
                    "SELECT COUNT(*) FROM evidence WHERE claim_id = ?", (claim_id,),
                )
                linked = erow[0] if erow else 0
            except Exception:
                linked = 0

            if linked == 0:
                gaps += 1

            color = COLORS["green"] if linked else COLORS["red"]
            status_text = f"{linked} evidence item(s)" if linked else "MISSING - No evidence linked"
            icon = "+" if linked else "X"
            ctk.CTkLabel(
                frame,
                text=f"{icon} {status_text}",
                font=ctk.CTkFont(size=12), text_color=color,
            ).pack(anchor="w", padx=12, pady=(0, 2))

            # Show evidence details when linked
            if linked > 0:
                try:
                    ev_rows = self._db.fetchall(
                        "SELECT title, file_type, bates_number FROM evidence "
                        "WHERE claim_id = ? ORDER BY bates_number",
                        (claim_id,),
                    )
                    for er in ev_rows:
                        ev = dict(er)
                        bates = ev.get("bates_number") or ""
                        ev_text = f"    {bates}  {ev.get('title', '')}  [{ev.get('file_type', '')}]"
                        ctk.CTkLabel(
                            frame, text=ev_text,
                            font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
                        ).pack(anchor="w", padx=20)
                except Exception:
                    pass

            # Description snippet
            desc = claim.get("description", "")
            if desc:
                ctk.CTkLabel(
                    frame, text=desc[:120],
                    font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
                ).pack(anchor="w", padx=12, pady=(0, 8))

        gap_color = COLORS["red"] if gaps > 0 else COLORS["green"]
        self._gaps_label.configure(text=f"Gaps: {gaps}", text_color=gap_color)

    def _placeholder(self, text: str):
        ctk.CTkLabel(
            self._claims_container, text=text,
            font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"],
        ).pack(pady=16)
