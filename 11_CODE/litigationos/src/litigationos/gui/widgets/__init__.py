"""Reusable GUI widgets for LitigationOS."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import customtkinter as ctk


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

COLORS = {
    # Core backgrounds
    "bg_dark": "#0D0D0D",        # Near-black background
    "bg_card": "#1A1A1A",        # Dark card background
    "bg_sidebar": "#111111",     # Sidebar — deep black

    # Brand accent — Hot pink
    "accent": "#FF1493",          # Deep pink (MBP brand)
    "accent_hover": "#FF69B4",    # Hot pink hover
    "accent_dim": "#C71585",      # Medium violet-red

    # Semantic colors
    "green": "#00E676",           # Bright green (success)
    "yellow": "#FFD600",          # Vivid yellow (warning)
    "orange": "#FF6D00",          # Orange (caution)
    "red": "#FF1744",             # Red (danger/overdue)
    "blue": "#448AFF",            # Blue (info)
    "purple": "#E040FB",          # Purple (special)
    "gray": "#616161",            # Muted gray

    # Text
    "text": "#F5F5F5",            # Bright white text
    "text_dim": "#9E9E9E",        # Dimmed gray text

    # Borders
    "border": "#2A2A2A",          # Dark border
    "border_light": "#3A3A3A",    # Lighter border for hover
}

STATUS_COLORS = {
    "active": COLORS["green"],
    "closed": COLORS["gray"],
    "appealed": COLORS["blue"],
    "settled": COLORS["yellow"],
    "draft": COLORS["text_dim"],
    "review": COLORS["orange"],
    "ready": COLORS["green"],
    "filed": COLORS["blue"],
    "served": COLORS["gray"],
    "pending": COLORS["yellow"],
    "met": COLORS["green"],
    "missed": COLORS["red"],
    "extended": COLORS["orange"],
}

PRIORITY_COLORS = {
    "critical": COLORS["red"],
    "high": COLORS["orange"],
    "medium": COLORS["yellow"],
    "low": COLORS["text_dim"],
    "normal": COLORS["text_dim"],
}


# ---------------------------------------------------------------------------
# StatusBadge
# ---------------------------------------------------------------------------

class StatusBadge(ctk.CTkFrame):
    """Coloured label for displaying a status value."""

    def __init__(
        self,
        parent,
        text: str = "",
        color: Optional[str] = None,
        **kwargs,
    ):
        color = color or STATUS_COLORS.get(text.lower(), COLORS["gray"])
        super().__init__(parent, fg_color=color, corner_radius=6, **kwargs)

        self._label = ctk.CTkLabel(
            self,
            text=text.upper(),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#ffffff",
        )
        self._label.pack(padx=8, pady=2)

    def set(self, text: str, color: Optional[str] = None):
        color = color or STATUS_COLORS.get(text.lower(), COLORS["gray"])
        self.configure(fg_color=color)
        self._label.configure(text=text.upper())


# ---------------------------------------------------------------------------
# DataCard
# ---------------------------------------------------------------------------

class DataCard(ctk.CTkFrame):
    """Stat card displaying a large numeric value with a label below."""

    def __init__(
        self,
        parent,
        title: str = "",
        value: str | int = "0",
        color: str = COLORS["blue"],
        **kwargs,
    ):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=12, **kwargs)

        self._accent = ctk.CTkFrame(self, fg_color=color, width=4, corner_radius=2)
        self._accent.pack(side="left", fill="y", padx=(0, 10), pady=8)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=(0, 12), pady=8)

        self._value_label = ctk.CTkLabel(
            inner,
            text=str(value),
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=color,
            anchor="w",
        )
        self._value_label.pack(anchor="w")

        self._title_label = ctk.CTkLabel(
            inner,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
            anchor="w",
        )
        self._title_label.pack(anchor="w")

    def set(self, value: str | int, title: Optional[str] = None):
        self._value_label.configure(text=str(value))
        if title is not None:
            self._title_label.configure(text=title)


# ---------------------------------------------------------------------------
# DeadlineRow
# ---------------------------------------------------------------------------

class DeadlineRow(ctk.CTkFrame):
    """Single row showing a deadline with priority colour coding."""

    def __init__(
        self,
        parent,
        title: str = "",
        due_date: str = "",
        priority: str = "medium",
        days_remaining: int = 0,
        **kwargs,
    ):
        color = PRIORITY_COLORS.get(priority.lower(), COLORS["text_dim"])
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=8, **kwargs)

        # Priority colour strip
        strip = ctk.CTkFrame(self, fg_color=color, width=5, corner_radius=2)
        strip.pack(side="left", fill="y", padx=(0, 8), pady=4)

        # Title + due date
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=4, pady=6)

        ctk.CTkLabel(
            info,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info,
            text=f"Due: {due_date}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
            anchor="w",
        ).pack(anchor="w")

        # Days remaining badge
        if days_remaining <= 3:
            days_color = COLORS["red"]
        elif days_remaining <= 7:
            days_color = COLORS["orange"]
        elif days_remaining <= 14:
            days_color = COLORS["yellow"]
        else:
            days_color = COLORS["green"]

        days_frame = ctk.CTkFrame(self, fg_color=days_color, corner_radius=8)
        days_frame.pack(side="right", padx=10, pady=6)

        ctk.CTkLabel(
            days_frame,
            text=f"{days_remaining}d",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
        ).pack(padx=10, pady=4)


# ---------------------------------------------------------------------------
# ProgressScore
# ---------------------------------------------------------------------------

class ProgressScore(ctk.CTkFrame):
    """Label + progress bar representing a 0-100 score."""

    def __init__(
        self,
        parent,
        label: str = "",
        score: int = 0,
        **kwargs,
    ):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=8, **kwargs)

        if score >= 80:
            bar_color = COLORS["green"]
        elif score >= 50:
            bar_color = COLORS["yellow"]
        else:
            bar_color = COLORS["red"]

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            header,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(side="left")

        self._score_label = ctk.CTkLabel(
            header,
            text=f"{score}%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=bar_color,
            anchor="e",
        )
        self._score_label.pack(side="right")

        self._bar = ctk.CTkProgressBar(
            self,
            progress_color=bar_color,
            fg_color=COLORS["border"],
            height=10,
            corner_radius=5,
        )
        self._bar.pack(fill="x", padx=10, pady=(2, 8))
        self._bar.set(score / 100.0)

    def set(self, score: int):
        if score >= 80:
            bar_color = COLORS["green"]
        elif score >= 50:
            bar_color = COLORS["yellow"]
        else:
            bar_color = COLORS["red"]

        self._score_label.configure(text=f"{score}%", text_color=bar_color)
        self._bar.configure(progress_color=bar_color)
        self._bar.set(score / 100.0)


# ---------------------------------------------------------------------------
# Tooltip
# ---------------------------------------------------------------------------

class Tooltip:
    """Hover tooltip for any widget. Shows after a short delay."""

    def __init__(self, widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._tip_window = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._cancel)
        widget.bind("<Button>", self._cancel)

    def _schedule(self, event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self, event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self):
        if self._tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        import tkinter as tk
        self._tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)

        frame = tk.Frame(tw, bg="#1A1A1A", bd=1, relief="solid",
                         highlightbackground="#FF1493", highlightthickness=1)
        frame.pack()
        label = tk.Label(
            frame, text=self.text, bg="#1A1A1A", fg="#F5F5F5",
            font=("Segoe UI", 9), padx=8, pady=4, wraplength=300, justify="left",
        )
        label.pack()

    def _hide(self):
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None

    def update_text(self, text: str):
        self.text = text


# ---------------------------------------------------------------------------
# ContextMenu
# ---------------------------------------------------------------------------

class ContextMenu:
    """Right-click context menu helper for any widget."""

    def __init__(self, widget, items: list[tuple] = None):
        import tkinter as tk
        self.widget = widget
        self.menu = tk.Menu(widget, tearoff=0, bg="#1A1A1A", fg="#F5F5F5",
                            activebackground="#FF1493", activeforeground="#FFFFFF",
                            font=("Segoe UI", 10))
        if items:
            for label, command in items:
                if label == "---":
                    self.menu.add_separator()
                else:
                    self.menu.add_command(label=label, command=command)
        widget.bind("<Button-3>", self._show)

    def _show(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def add_item(self, label: str, command: callable):
        self.menu.add_command(label=label, command=command)

    def add_separator(self):
        self.menu.add_separator()


__all__ = [
    "COLORS",
    "STATUS_COLORS",
    "PRIORITY_COLORS",
    "StatusBadge",
    "DataCard",
    "DeadlineRow",
    "ProgressScore",
    "Tooltip",
    "ContextMenu",
]
