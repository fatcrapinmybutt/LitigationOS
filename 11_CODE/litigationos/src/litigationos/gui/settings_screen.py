"""Settings screen — jurisdiction, paths, LLM, appearance.

Four-section settings form backed by ``SettingsEngine`` with save, reset,
and live theme switching.
"""

from __future__ import annotations

import logging
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from litigationos.app import App

from litigationos.engines.settings import SettingsEngine

logger = logging.getLogger(__name__)

_US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]


class SettingsFrame(ctk.CTkFrame):
    """Settings screen — jurisdiction, paths, LLM, appearance."""

    def __init__(self, parent: ctk.CTkFrame, app: "App"):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.engine = SettingsEngine(app.db)

        self._build_ui()
        self.refresh()

    # -- Layout ---------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(12, 4)
        )

        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        scroll.grid_columnconfigure(0, weight=1)

        self._build_jurisdiction_section(scroll)
        self._build_paths_section(scroll)
        self._build_ai_section(scroll)
        self._build_appearance_section(scroll)

        # Bottom buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 12))
        ctk.CTkButton(btn_frame, text="Save Settings", width=140, command=self._save).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            btn_frame, text="Reset Defaults", width=140, fg_color="#EF4444",
            hover_color="#DC2626", command=self._reset,
        ).pack(side="left", padx=8)

    # -- Section builders -----------------------------------------------------

    def _section_header(self, parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=(12, 4))
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 4)
        )
        return frame

    def _build_jurisdiction_section(self, parent: ctk.CTkFrame) -> None:
        sec = self._section_header(parent, "⚖  Jurisdiction")
        r = 1

        ctk.CTkLabel(sec, text="State").grid(row=r, column=0, sticky="w", padx=12)
        self._state_combo = ctk.CTkComboBox(sec, values=_US_STATES, width=120)
        self._state_combo.grid(row=r, column=1, sticky="w", padx=8, pady=2)
        r += 1

        ctk.CTkLabel(sec, text="County").grid(row=r, column=0, sticky="w", padx=12)
        self._county_entry = ctk.CTkEntry(sec, placeholder_text="County name")
        self._county_entry.grid(row=r, column=1, sticky="ew", padx=8, pady=2)
        r += 1

        ctk.CTkLabel(sec, text="Court").grid(row=r, column=0, sticky="w", padx=12)
        self._court_entry = ctk.CTkEntry(sec, placeholder_text="e.g. 14th Circuit")
        self._court_entry.grid(row=r, column=1, sticky="ew", padx=8, pady=(2, 8))

    def _build_paths_section(self, parent: ctk.CTkFrame) -> None:
        sec = self._section_header(parent, "📁  Paths")
        self._path_entries: dict[str, ctk.CTkEntry] = {}

        labels = [
            ("Data Directory", "data_dir"),
            ("Output Directory", "output_dir"),
            ("Template Directory", "template_dir"),
        ]
        for r, (label, key) in enumerate(labels, start=1):
            ctk.CTkLabel(sec, text=label).grid(row=r, column=0, sticky="w", padx=12)
            row_frame = ctk.CTkFrame(sec, fg_color="transparent")
            row_frame.grid(row=r, column=1, sticky="ew", padx=8, pady=2)
            row_frame.grid_columnconfigure(0, weight=1)
            entry = ctk.CTkEntry(row_frame, placeholder_text=f"Select {label.lower()}…")
            entry.grid(row=0, column=0, sticky="ew")
            ctk.CTkButton(
                row_frame, text="…", width=32,
                command=lambda e=entry: self._pick_folder(e),
            ).grid(row=0, column=1, padx=(4, 0))
            self._path_entries[key] = entry

    def _build_ai_section(self, parent: ctk.CTkFrame) -> None:
        sec = self._section_header(parent, "🤖  AI / LLM")
        r = 1

        ctk.CTkLabel(sec, text="Model Name").grid(row=r, column=0, sticky="w", padx=12)
        self._model_entry = ctk.CTkEntry(sec, placeholder_text="qwen2.5:7b")
        self._model_entry.grid(row=r, column=1, sticky="ew", padx=8, pady=2)
        r += 1

        ctk.CTkLabel(sec, text="Embedding Model").grid(row=r, column=0, sticky="w", padx=12)
        self._embed_entry = ctk.CTkEntry(sec, placeholder_text="nomic-embed-text")
        self._embed_entry.grid(row=r, column=1, sticky="ew", padx=8, pady=2)
        r += 1

        ctk.CTkLabel(sec, text="Ollama URL").grid(row=r, column=0, sticky="w", padx=12)
        self._ollama_entry = ctk.CTkEntry(sec, placeholder_text="http://localhost:11434")
        self._ollama_entry.grid(row=r, column=1, sticky="ew", padx=8, pady=2)
        r += 1

        ctk.CTkButton(
            sec, text="Test Connection", width=140, fg_color="#3B82F6",
            command=self._test_connection,
        ).grid(row=r, column=1, sticky="w", padx=8, pady=(4, 8))

    def _build_appearance_section(self, parent: ctk.CTkFrame) -> None:
        sec = self._section_header(parent, "🎨  Appearance")
        r = 1

        ctk.CTkLabel(sec, text="Theme").grid(row=r, column=0, sticky="w", padx=12)
        self._theme_combo = ctk.CTkComboBox(sec, values=["Dark", "Light", "System"], width=140)
        self._theme_combo.grid(row=r, column=1, sticky="w", padx=8, pady=2)
        r += 1

        ctk.CTkLabel(sec, text="Font Size").grid(row=r, column=0, sticky="w", padx=12)
        size_frame = ctk.CTkFrame(sec, fg_color="transparent")
        size_frame.grid(row=r, column=1, sticky="ew", padx=8, pady=(2, 8))
        size_frame.grid_columnconfigure(0, weight=1)
        self._font_slider = ctk.CTkSlider(size_frame, from_=10, to=18, number_of_steps=8,
                                            command=self._on_font_slide)
        self._font_slider.grid(row=0, column=0, sticky="ew")
        self._font_label = ctk.CTkLabel(size_frame, text="12", width=30)
        self._font_label.grid(row=0, column=1, padx=(8, 0))

    # -- Helpers --------------------------------------------------------------

    @staticmethod
    def _pick_folder(entry: ctk.CTkEntry) -> None:
        path = filedialog.askdirectory(title="Select directory")
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _on_font_slide(self, value: float) -> None:
        self._font_label.configure(text=str(int(value)))

    # -- Load / Save ----------------------------------------------------------

    def refresh(self) -> None:
        """Load current values from DB into the form."""
        try:
            juris = self.engine.get_jurisdiction()
            self._state_combo.set(juris.get("state") or "MI")
            self._set_entry(self._county_entry, juris.get("county") or "")
            self._set_entry(self._court_entry, juris.get("court") or "")

            paths = self.engine.get_paths()
            for key, entry in self._path_entries.items():
                self._set_entry(entry, paths.get(key) or "")

            self._set_entry(self._model_entry, self.engine.get("llm.model") or "qwen2.5:7b")
            self._set_entry(self._embed_entry, self.engine.get("llm.embedding_model") or "nomic-embed-text")
            self._set_entry(self._ollama_entry, self.engine.get("ollama_url") or "http://localhost:11434")

            theme = self.engine.get("app.theme") or "dark"
            self._theme_combo.set(theme.capitalize())

            font_size = int(self.engine.get("app.font_size") or "12")
            self._font_slider.set(font_size)
            self._font_label.configure(text=str(font_size))
        except Exception as exc:
            logger.warning("Failed to load settings: %s", exc)

    @staticmethod
    def _set_entry(entry: ctk.CTkEntry, value: str) -> None:
        entry.delete(0, "end")
        entry.insert(0, value)

    def _save(self) -> None:
        """Write all form values via SettingsEngine."""
        try:
            self.engine.set_jurisdiction(
                self._state_combo.get(),
                self._county_entry.get().strip(),
                self._court_entry.get().strip(),
            )
            for key, entry in self._path_entries.items():
                val = entry.get().strip()
                if val:
                    self.engine.set_path(key, val)

            self.engine.set("llm.model", self._model_entry.get().strip())
            self.engine.set("llm.embedding_model", self._embed_entry.get().strip())
            self.engine.set("ollama_url", self._ollama_entry.get().strip())

            theme = self._theme_combo.get().lower()
            self.engine.set("app.theme", theme)
            ctk.set_appearance_mode(theme)

            font_size = int(self._font_slider.get())
            self.engine.set("app.font_size", str(font_size))

            messagebox.showinfo("Settings", "Settings saved successfully.")
        except Exception as exc:
            messagebox.showerror("Settings", f"Failed to save: {exc}")

    def _reset(self) -> None:
        """Reset all fields to defaults."""
        if not messagebox.askyesno("Reset", "Reset all settings to defaults?"):
            return
        defaults = {
            "jurisdiction.state": "MI",
            "jurisdiction.county": "Muskegon",
            "jurisdiction.court": "14th Circuit",
            "llm.model": "qwen2.5:7b",
            "llm.embedding_model": "nomic-embed-text",
            "ollama_url": "http://localhost:11434",
            "app.theme": "dark",
            "app.font_size": "12",
        }
        try:
            for key, val in defaults.items():
                self.engine.set(key, val)
            # Clear path entries to defaults
            for key in self._path_entries:
                self.engine.set(f"paths.{key}", "")
            self.refresh()
            ctk.set_appearance_mode("dark")
            messagebox.showinfo("Settings", "Settings reset to defaults.")
        except Exception as exc:
            messagebox.showerror("Settings", f"Failed to reset: {exc}")

    def _test_connection(self) -> None:
        """Test Ollama connectivity."""
        url = self._ollama_entry.get().strip() or "http://localhost:11434"
        try:
            import urllib.request
            req = urllib.request.Request(f"{url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    messagebox.showinfo("Connection", f"✅ Connected to Ollama at {url}")
                else:
                    messagebox.showwarning("Connection", f"Unexpected status: {resp.status}")
        except Exception as exc:
            messagebox.showerror("Connection", f"❌ Cannot reach Ollama at {url}\n\n{exc}")
