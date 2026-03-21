"""Pricing & Feature Gate — Tier comparison, feature matrix, and license activation."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable, Optional

import customtkinter as ctk

from litigationos.gui.widgets import COLORS, DataCard, StatusBadge, Tooltip, ContextMenu

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

try:
    from litigationos.engines.license_manager import LicenseManager

    _HAS_LICENSE = True
except ImportError:
    _HAS_LICENSE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LICENSE_KEY_PATTERN = re.compile(
    r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
)

_TIERS: list[dict[str, Any]] = [
    {
        "name": "Free",
        "price": "$0",
        "period": "/mo",
        "highlight": False,
        "badge": None,
        "button_text": "Current Plan",
        "limits": {"Cases": "1", "Filings": "3", "Evidence Items": "100"},
        "features": {
            "Legal Brain Search": True,
            "IRAC Analysis": False,
            "Discovery Generator": False,
            "Motion Templates": False,
            "PDF Production": False,
            "Court Form Filler": False,
            "Pipeline Runner": False,
            "Judge Profiling": False,
            "API Access": False,
            "Custom Branding": False,
            "Multi-User": False,
        },
        "support": "Community",
    },
    {
        "name": "Pro",
        "price": "$49.99",
        "period": "/mo",
        "highlight": True,
        "badge": "MOST POPULAR",
        "button_text": "Upgrade",
        "limits": {"Cases": "5", "Filings": "50", "Evidence Items": "10,000"},
        "features": {
            "Legal Brain Search": True,
            "IRAC Analysis": True,
            "Discovery Generator": True,
            "Motion Templates": True,
            "PDF Production": True,
            "Court Form Filler": True,
            "Pipeline Runner": False,
            "Judge Profiling": False,
            "API Access": False,
            "Custom Branding": False,
            "Multi-User": False,
        },
        "support": "Email",
    },
    {
        "name": "Enterprise",
        "price": "$199.99",
        "period": "/mo",
        "highlight": False,
        "badge": None,
        "button_text": "Contact Us",
        "limits": {
            "Cases": "Unlimited",
            "Filings": "Unlimited",
            "Evidence Items": "Unlimited",
        },
        "features": {
            "Legal Brain Search": True,
            "IRAC Analysis": True,
            "Discovery Generator": True,
            "Motion Templates": True,
            "PDF Production": True,
            "Court Form Filler": True,
            "Pipeline Runner": True,
            "Judge Profiling": True,
            "API Access": True,
            "Custom Branding": True,
            "Multi-User": True,
        },
        "support": "Priority",
    },
]

# Ordered list for comparison table rows
_FEATURE_ROWS: list[str] = [
    "Cases",
    "Filings",
    "Evidence Items",
    "Legal Brain Search",
    "IRAC Analysis",
    "Discovery Generator",
    "Motion Templates",
    "PDF Production",
    "Court Form Filler",
    "Pipeline Runner",
    "Judge Profiling",
    "API Access",
    "Custom Branding",
    "Multi-User",
    "Support",
]


# ---------------------------------------------------------------------------
# PricingFrame
# ---------------------------------------------------------------------------


class PricingFrame(ctk.CTkFrame):
    """Pricing tiers, feature comparison matrix, and license activation.

    Displays three subscription tiers (Free / Pro / Enterprise), a detailed
    feature gate comparison table, and a license-key activation form.  When
    the optional ``LicenseManager`` engine is available, activations and
    trials are persisted; otherwise the screen degrades gracefully with
    placeholder behaviour.
    """

    # ------------------------------------------------------------------ init

    def __init__(
        self,
        parent: Any,
        db: DatabaseManager | None = None,
        navigate_cb: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb

        # Engine (optional)
        self._license_mgr: Any | None = None
        if _HAS_LICENSE:
            try:
                self._license_mgr = LicenseManager(db=db)
                logger.info("LicenseManager engine loaded")
            except Exception:
                logger.exception("Failed to initialise LicenseManager")

        # State
        self._current_tier: str = "Free"
        self._license_key: str = ""
        self._expiry_date: datetime | None = None
        self._trial_active: bool = False

        self._load_license_state()

        # Build UI
        self._build_ui()

    # -------------------------------------------------------- license state

    def _load_license_state(self) -> None:
        """Load current license / tier information from engine or DB."""
        if self._license_mgr is not None:
            try:
                info = self._license_mgr.get_license_info()
                self._current_tier = info.get("tier", "Free")
                self._license_key = info.get("key", "")
                exp = info.get("expiry")
                if isinstance(exp, str) and exp:
                    self._expiry_date = datetime.fromisoformat(exp)
                elif isinstance(exp, datetime):
                    self._expiry_date = exp
                self._trial_active = info.get("trial", False)
            except Exception:
                logger.exception("Could not load license state")
        elif self._db is not None:
            try:
                row = self._db.execute(
                    "SELECT value FROM settings WHERE key = 'license_tier'"
                ).fetchone()
                if row:
                    self._current_tier = row[0]
            except Exception:
                logger.debug("No license_tier in settings table")

    # --------------------------------------------------------- UI assembly

    def _build_ui(self) -> None:
        """Assemble all screen sections inside a master scrollable frame."""
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_dark"],
            corner_radius=0,
            scrollbar_button_color=COLORS["accent_dim"],
        )
        self._scroll.pack(fill="both", expand=True)

        self._build_header()
        self._build_pricing_cards()
        self._build_comparison_table()
        self._build_license_section()

    # ---------------------------------------------------------------- header

    def _build_header(self) -> None:
        """Top banner with title, subtitle, and current-plan badge."""
        header = ctk.CTkFrame(
            self._scroll, fg_color=COLORS["bg_card"], corner_radius=12
        )
        header.pack(fill="x", padx=20, pady=(20, 8))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=16, pady=14)

        ctk.CTkLabel(
            left,
            text="💎  LitigationOS Plans",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="Choose the plan that fits your fight",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(2, 0))

        # Current plan badge
        badge_frame = ctk.CTkFrame(header, fg_color="transparent")
        badge_frame.pack(side="right", padx=16, pady=14)

        ctk.CTkLabel(
            badge_frame,
            text="Current Plan:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(0, 6))

        self._plan_badge = StatusBadge(
            badge_frame,
            text=self._current_tier,
            color=self._tier_color(self._current_tier),
        )
        self._plan_badge.pack(side="left")

    # -------------------------------------------------------- pricing cards

    def _build_pricing_cards(self) -> None:
        """Render the three tier cards in a responsive 3-column grid."""
        container = ctk.CTkFrame(self._scroll, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=(8, 8))
        for i in range(3):
            container.columnconfigure(i, weight=1)

        for col, tier in enumerate(_TIERS):
            self._build_tier_card(container, tier, col)

    def _build_tier_card(
        self, parent: ctk.CTkFrame, tier: dict[str, Any], col: int
    ) -> None:
        """Build a single pricing tier card."""
        is_current = tier["name"] == self._current_tier
        is_highlighted = tier["highlight"]

        border_clr = COLORS["accent"] if is_highlighted else COLORS["border"]
        border_w = 2 if is_highlighted else 1

        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=14,
            border_color=border_clr,
            border_width=border_w,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=8, pady=4)

        # Popular badge
        if tier["badge"]:
            badge_bar = ctk.CTkFrame(
                card, fg_color=COLORS["accent"], corner_radius=6, height=26
            )
            badge_bar.pack(fill="x", padx=12, pady=(12, 0))
            ctk.CTkLabel(
                badge_bar,
                text=f"⭐  {tier['badge']}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#FFFFFF",
            ).pack(pady=2)

        # Tier name
        ctk.CTkLabel(
            card,
            text=tier["name"],
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text"],
        ).pack(pady=(16 if not tier["badge"] else 10, 0))

        # Price
        price_frame = ctk.CTkFrame(card, fg_color="transparent")
        price_frame.pack(pady=(4, 2))

        ctk.CTkLabel(
            price_frame,
            text=tier["price"],
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["accent"] if is_highlighted else COLORS["text"],
        ).pack(side="left")

        ctk.CTkLabel(
            price_frame,
            text=tier["period"],
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(2, 0), anchor="s", pady=(0, 4))

        # Current-plan badge
        if is_current:
            cur_badge = ctk.CTkFrame(
                card, fg_color=COLORS["green"], corner_radius=6, height=24
            )
            cur_badge.pack(pady=(6, 0))
            ctk.CTkLabel(
                cur_badge,
                text="  ✓ CURRENT PLAN  ",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=COLORS["bg_dark"],
            ).pack(padx=8, pady=2)

        # Divider
        ctk.CTkFrame(
            card, fg_color=COLORS["border"], height=1, corner_radius=0
        ).pack(fill="x", padx=16, pady=(12, 8))

        # Limits
        for label, value in tier["limits"].items():
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(
                row,
                text=f"📊  {label}:",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_dim"],
            ).pack(side="left")
            val_color = COLORS["green"] if value == "Unlimited" else COLORS["text"]
            ctk.CTkLabel(
                row,
                text=value,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=val_color,
            ).pack(side="right")

        # Divider
        ctk.CTkFrame(
            card, fg_color=COLORS["border"], height=1, corner_radius=0
        ).pack(fill="x", padx=16, pady=(8, 8))

        # Features list
        for feat, enabled in tier["features"].items():
            feat_row = ctk.CTkFrame(card, fg_color="transparent")
            feat_row.pack(fill="x", padx=20, pady=1)

            icon = "✅" if enabled else "❌"
            text_clr = COLORS["text"] if enabled else COLORS["gray"]

            lbl = ctk.CTkLabel(
                feat_row,
                text=f"{icon}  {feat}",
                font=ctk.CTkFont(size=11),
                text_color=text_clr,
            )
            lbl.pack(side="left")

            if not enabled:
                upgrade_target = "Pro" if tier["name"] == "Free" else "Enterprise"
                Tooltip(
                    lbl,
                    f"Upgrade to {upgrade_target} to unlock {feat}",
                )

        # Support row
        support_row = ctk.CTkFrame(card, fg_color="transparent")
        support_row.pack(fill="x", padx=20, pady=(4, 2))
        ctk.CTkLabel(
            support_row,
            text=f"🛟  Support: {tier['support']}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        # CTA button
        btn_color = COLORS["accent"] if is_highlighted else COLORS["accent_dim"]
        hover_color = COLORS["accent_hover"]

        if is_current:
            btn_text = "Current Plan"
            btn_state = "disabled"
        else:
            btn_text = tier["button_text"]
            btn_state = "normal"

        btn = ctk.CTkButton(
            card,
            text=btn_text,
            state=btn_state,
            fg_color=btn_color,
            hover_color=hover_color,
            text_color="#FFFFFF",
            corner_radius=8,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda t=tier["name"]: self._on_tier_select(t),
        )
        btn.pack(fill="x", padx=20, pady=(14, 18))

    # ---------------------------------------------------- comparison table

    def _build_comparison_table(self) -> None:
        """Render the full feature comparison matrix."""
        section = ctk.CTkFrame(
            self._scroll, fg_color=COLORS["bg_card"], corner_radius=12
        )
        section.pack(fill="x", padx=20, pady=(8, 8))

        # Section header
        ctk.CTkLabel(
            section,
            text="📋  Feature Comparison",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=20, pady=(16, 8))

        # Table container
        table = ctk.CTkFrame(section, fg_color="transparent")
        table.pack(fill="x", padx=16, pady=(0, 16))

        # 4 columns: Feature | Free | Pro | Enterprise
        table.columnconfigure(0, weight=3)
        for c in range(1, 4):
            table.columnconfigure(c, weight=1)

        # Header row
        headers = ["Feature", "Free", "Pro", "Enterprise"]
        for c, hdr in enumerate(headers):
            bg = COLORS["accent"] if c == 2 else COLORS["border"]
            h_frame = ctk.CTkFrame(table, fg_color=bg, corner_radius=6)
            h_frame.grid(row=0, column=c, sticky="ew", padx=2, pady=2)
            ctk.CTkLabel(
                h_frame,
                text=hdr,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#FFFFFF" if c == 2 else COLORS["text"],
            ).pack(padx=10, pady=6)

        # Data rows
        for r, feature in enumerate(_FEATURE_ROWS, start=1):
            bg = COLORS["bg_dark"] if r % 2 == 0 else "transparent"

            # Feature name
            f_cell = ctk.CTkFrame(table, fg_color=bg, corner_radius=0)
            f_cell.grid(row=r, column=0, sticky="ew", padx=2, pady=1)
            ctk.CTkLabel(
                f_cell,
                text=f"  {feature}",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text"],
                anchor="w",
            ).pack(fill="x", padx=10, pady=5)

            # Tier values
            for c, tier in enumerate(_TIERS, start=1):
                cell = ctk.CTkFrame(table, fg_color=bg, corner_radius=0)
                cell.grid(row=r, column=c, sticky="ew", padx=2, pady=1)

                cell_text = self._get_cell_value(feature, tier)
                cell_color = self._get_cell_color(cell_text)

                lbl = ctk.CTkLabel(
                    cell,
                    text=cell_text,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=cell_color,
                )
                lbl.pack(pady=5)

    @staticmethod
    def _get_cell_value(feature: str, tier: dict[str, Any]) -> str:
        """Resolve the display string for a comparison-table cell."""
        if feature == "Support":
            return tier["support"]
        if feature in tier["limits"]:
            return tier["limits"][feature]
        return "✅" if tier["features"].get(feature, False) else "❌"

    @staticmethod
    def _get_cell_color(text: str) -> str:
        """Pick a colour for comparison-table cell text."""
        if text == "✅" or text == "Unlimited":
            return COLORS["green"]
        if text == "❌":
            return COLORS["red"]
        if text in {"Community", "Email", "Priority"}:
            return COLORS["text_dim"]
        return COLORS["text"]

    # ---------------------------------------------------- license section

    def _build_license_section(self) -> None:
        """License-key activation, trial button, and status display."""
        section = ctk.CTkFrame(
            self._scroll, fg_color=COLORS["bg_card"], corner_radius=12
        )
        section.pack(fill="x", padx=20, pady=(8, 20))

        # Section header
        ctk.CTkLabel(
            section,
            text="🔑  License Activation",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            section,
            text="Enter your license key to unlock premium features",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", padx=20, pady=(0, 10))

        # Key input row
        key_row = ctk.CTkFrame(section, fg_color="transparent")
        key_row.pack(fill="x", padx=20, pady=(0, 8))

        self._key_var = ctk.StringVar(value="")
        self._key_entry = ctk.CTkEntry(
            key_row,
            textvariable=self._key_var,
            placeholder_text="XXXX-XXXX-XXXX-XXXX",
            width=340,
            height=40,
            border_color=COLORS["accent"],
            border_width=2,
            corner_radius=8,
            font=ctk.CTkFont(size=14, family="Consolas"),
        )
        self._key_entry.pack(side="left", padx=(0, 8))
        self._key_entry.bind("<Return>", lambda _e: self._activate_license())
        Tooltip(self._key_entry, "Format: XXXX-XXXX-XXXX-XXXX")

        self._activate_btn = ctk.CTkButton(
            key_row,
            text="Activate",
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            corner_radius=8,
            height=40,
            width=120,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._activate_license,
        )
        self._activate_btn.pack(side="left")

        self._key_status_lbl = ctk.CTkLabel(
            key_row,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        )
        self._key_status_lbl.pack(side="left", padx=(12, 0))

        # License status cards
        status_row = ctk.CTkFrame(section, fg_color="transparent")
        status_row.pack(fill="x", padx=20, pady=(4, 8))
        for i in range(3):
            status_row.columnconfigure(i, weight=1)

        self._tier_card = DataCard(
            status_row, title="Current Tier", value=self._current_tier,
            color=self._tier_color(self._current_tier),
        )
        self._tier_card.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=4)

        expiry_str = (
            self._expiry_date.strftime("%Y-%m-%d") if self._expiry_date else "—"
        )
        self._expiry_card = DataCard(
            status_row, title="Expires", value=expiry_str,
            color=COLORS["blue"],
        )
        self._expiry_card.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        days = self._days_remaining()
        days_str = str(days) if days is not None else "∞"
        days_color = (
            COLORS["red"] if days is not None and days <= 7
            else COLORS["yellow"] if days is not None and days <= 30
            else COLORS["green"]
        )
        self._days_card = DataCard(
            status_row, title="Days Left", value=days_str, color=days_color,
        )
        self._days_card.grid(row=0, column=2, sticky="ew", padx=(6, 0), pady=4)

        # Trial + deactivate row
        action_row = ctk.CTkFrame(section, fg_color="transparent")
        action_row.pack(fill="x", padx=20, pady=(4, 16))

        if self._current_tier == "Free" and not self._trial_active:
            self._trial_btn = ctk.CTkButton(
                action_row,
                text="🚀  Start 14-Day Pro Trial",
                fg_color=COLORS["purple"],
                hover_color=COLORS["accent_hover"],
                text_color="#FFFFFF",
                corner_radius=8,
                height=36,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=self._start_trial,
            )
            self._trial_btn.pack(side="left", padx=(0, 12))
        else:
            self._trial_btn = None

        if self._current_tier != "Free":
            deactivate_lbl = ctk.CTkLabel(
                action_row,
                text="Deactivate License",
                font=ctk.CTkFont(size=12, underline=True),
                text_color=COLORS["red"],
                cursor="hand2",
            )
            deactivate_lbl.pack(side="right")
            deactivate_lbl.bind("<Button-1>", lambda _e: self._deactivate_license())
            Tooltip(deactivate_lbl, "Remove license and revert to Free tier")

    # ------------------------------------------------------------- helpers

    @staticmethod
    def _tier_color(tier: str) -> str:
        """Return a brand colour for the given tier name."""
        return {
            "Free": COLORS["gray"],
            "Pro": COLORS["accent"],
            "Enterprise": COLORS["purple"],
        }.get(tier, COLORS["gray"])

    def _days_remaining(self) -> int | None:
        """Return days until expiry, or ``None`` if no expiry set."""
        if self._expiry_date is None:
            return None
        delta = self._expiry_date - datetime.now()
        return max(delta.days, 0)

    # --------------------------------------------------------- interactions

    def _on_tier_select(self, tier_name: str) -> None:
        """Handle tier card button clicks."""
        if tier_name == self._current_tier:
            return

        logger.info("Tier selection requested: %s", tier_name)

        if tier_name == "Enterprise":
            self._show_contact_dialog()
        else:
            self._show_upgrade_dialog(tier_name)

    def _show_upgrade_dialog(self, tier_name: str) -> None:
        """Display an upgrade / payment instructions dialog (placeholder)."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Upgrade to {tier_name}")
        dialog.geometry("440x340")
        dialog.configure(fg_color=COLORS["bg_dark"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Centre content
        inner = ctk.CTkFrame(dialog, fg_color=COLORS["bg_card"], corner_radius=12)
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            inner,
            text=f"💎  Upgrade to {tier_name}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(24, 8))

        price = "$49.99/mo" if tier_name == "Pro" else "$199.99/mo"
        ctk.CTkLabel(
            inner,
            text=price,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text"],
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            inner,
            text=(
                "Payment processing is not yet integrated.\n"
                "Purchase a license key from the LitigationOS\n"
                "website, then enter it below to activate."
            ),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
            justify="center",
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            inner,
            text="https://litigationos.com/pricing",
            font=ctk.CTkFont(size=12, underline=True),
            text_color=COLORS["blue"],
        ).pack(pady=(0, 8))

        ctk.CTkButton(
            inner,
            text="Close",
            fg_color=COLORS["accent_dim"],
            hover_color=COLORS["accent"],
            text_color="#FFFFFF",
            corner_radius=8,
            height=34,
            width=120,
            command=dialog.destroy,
        ).pack(pady=(8, 20))

    def _show_contact_dialog(self) -> None:
        """Display Enterprise contact dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Enterprise Inquiry")
        dialog.geometry("440x300")
        dialog.configure(fg_color=COLORS["bg_dark"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        inner = ctk.CTkFrame(dialog, fg_color=COLORS["bg_card"], corner_radius=12)
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            inner,
            text="🏢  Enterprise Plan",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["purple"],
        ).pack(pady=(24, 8))

        ctk.CTkLabel(
            inner,
            text=(
                "For multi-user deployments, custom integrations,\n"
                "and priority support, contact our team."
            ),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
            justify="center",
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            inner,
            text="enterprise@litigationos.com",
            font=ctk.CTkFont(size=13, underline=True),
            text_color=COLORS["accent"],
        ).pack(pady=(0, 8))

        ctk.CTkButton(
            inner,
            text="Close",
            fg_color=COLORS["accent_dim"],
            hover_color=COLORS["accent"],
            text_color="#FFFFFF",
            corner_radius=8,
            height=34,
            width=120,
            command=dialog.destroy,
        ).pack(pady=(8, 20))

    # ----------------------------------------------------- license actions

    def _activate_license(self) -> None:
        """Validate and activate the entered license key."""
        raw_key = self._key_var.get().strip().upper()

        if not raw_key:
            self._set_key_status("Enter a license key", COLORS["yellow"])
            return

        if not _LICENSE_KEY_PATTERN.match(raw_key):
            self._set_key_status("Invalid format — use XXXX-XXXX-XXXX-XXXX", COLORS["red"])
            logger.warning("Invalid license key format: %s", raw_key[:8] + "…")
            return

        logger.info("Activating license key: %s…%s", raw_key[:4], raw_key[-4:])

        if self._license_mgr is not None:
            try:
                result = self._license_mgr.activate(raw_key)
                if result.get("success"):
                    self._current_tier = result.get("tier", "Pro")
                    exp = result.get("expiry")
                    if isinstance(exp, str):
                        self._expiry_date = datetime.fromisoformat(exp)
                    elif isinstance(exp, datetime):
                        self._expiry_date = exp
                    self._license_key = raw_key
                    self._set_key_status(
                        f"✅ Activated — {self._current_tier} plan", COLORS["green"]
                    )
                    self._refresh_status_cards()
                    logger.info("License activated: tier=%s", self._current_tier)
                else:
                    msg = result.get("error", "Activation failed")
                    self._set_key_status(f"❌ {msg}", COLORS["red"])
            except Exception:
                logger.exception("License activation error")
                self._set_key_status("❌ Activation error — check logs", COLORS["red"])
        else:
            # Graceful fallback: accept the key locally
            self._current_tier = "Pro"
            self._license_key = raw_key
            self._expiry_date = datetime.now() + timedelta(days=365)
            self._set_key_status("✅ Key accepted (offline mode)", COLORS["green"])
            self._persist_tier()
            self._refresh_status_cards()
            logger.info("License accepted in offline mode")

    def _start_trial(self) -> None:
        """Activate a 14-day Pro trial."""
        logger.info("Starting 14-day Pro trial")

        if self._license_mgr is not None:
            try:
                result = self._license_mgr.start_trial()
                if result.get("success"):
                    self._current_tier = "Pro"
                    self._trial_active = True
                    exp = result.get("expiry")
                    if isinstance(exp, str):
                        self._expiry_date = datetime.fromisoformat(exp)
                    elif isinstance(exp, datetime):
                        self._expiry_date = exp
                    else:
                        self._expiry_date = datetime.now() + timedelta(days=14)
                else:
                    self._set_key_status(
                        f"❌ {result.get('error', 'Trial start failed')}",
                        COLORS["red"],
                    )
                    return
            except Exception:
                logger.exception("Trial activation error")
                self._set_key_status("❌ Trial error — check logs", COLORS["red"])
                return
        else:
            # Offline fallback
            self._current_tier = "Pro"
            self._trial_active = True
            self._expiry_date = datetime.now() + timedelta(days=14)
            self._persist_tier()

        self._set_key_status("🚀 14-day Pro trial activated!", COLORS["green"])
        self._refresh_status_cards()

        # Hide trial button
        if self._trial_btn is not None:
            self._trial_btn.configure(
                text="✓ Trial Active", state="disabled",
                fg_color=COLORS["gray"],
            )

        logger.info("Pro trial activated, expires %s", self._expiry_date)

    def _deactivate_license(self) -> None:
        """Revert to Free tier after confirmation."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Deactivate License")
        dialog.geometry("380x220")
        dialog.configure(fg_color=COLORS["bg_dark"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        inner = ctk.CTkFrame(dialog, fg_color=COLORS["bg_card"], corner_radius=12)
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            inner,
            text="⚠️  Deactivate License?",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["yellow"],
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            inner,
            text=(
                "You will revert to the Free tier.\n"
                "Premium features will become locked."
            ),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
            justify="center",
        ).pack(pady=(0, 16))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(pady=(0, 16))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            fg_color=COLORS["accent_dim"],
            hover_color=COLORS["accent"],
            text_color="#FFFFFF",
            corner_radius=8,
            height=34,
            width=100,
            command=dialog.destroy,
        ).pack(side="left", padx=(0, 8))

        def _confirm() -> None:
            self._do_deactivate()
            dialog.destroy()

        ctk.CTkButton(
            btn_row,
            text="Deactivate",
            fg_color=COLORS["red"],
            hover_color="#FF4444",
            text_color="#FFFFFF",
            corner_radius=8,
            height=34,
            width=120,
            command=_confirm,
        ).pack(side="left")

    def _do_deactivate(self) -> None:
        """Perform the actual deactivation."""
        logger.info("Deactivating license, reverting to Free tier")

        if self._license_mgr is not None:
            try:
                self._license_mgr.deactivate()
            except Exception:
                logger.exception("Engine deactivation failed")

        self._current_tier = "Free"
        self._license_key = ""
        self._expiry_date = None
        self._trial_active = False
        self._persist_tier()
        self._set_key_status("License deactivated — Free tier active", COLORS["yellow"])
        self._refresh_status_cards()

    # -------------------------------------------------------- persistence

    def _persist_tier(self) -> None:
        """Write the current tier to the settings table if a DB is available."""
        if self._db is None:
            return
        try:
            self._db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("license_tier", self._current_tier),
            )
            self._db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (
                    "license_expiry",
                    self._expiry_date.isoformat() if self._expiry_date else "",
                ),
            )
            self._db.commit()
        except Exception:
            logger.debug("Could not persist license tier to settings table")

    # ----------------------------------------------------------- refresh

    def _set_key_status(self, text: str, color: str) -> None:
        """Update the inline status label next to the key entry."""
        self._key_status_lbl.configure(text=text, text_color=color)

    def _refresh_status_cards(self) -> None:
        """Update the three DataCards and plan badge with current state."""
        self._tier_card.set(self._current_tier)
        self._plan_badge.set(
            self._current_tier, color=self._tier_color(self._current_tier)
        )

        expiry_str = (
            self._expiry_date.strftime("%Y-%m-%d") if self._expiry_date else "—"
        )
        self._expiry_card.set(expiry_str)

        days = self._days_remaining()
        days_str = str(days) if days is not None else "∞"
        self._days_card.set(days_str)

    def refresh(self) -> None:
        """Public entry point — reload license state and update UI."""
        self._load_license_state()
        self._refresh_status_cards()
