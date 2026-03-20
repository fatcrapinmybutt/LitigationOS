"""AI Chat screen powered by the MANBEARPIG local inference engine.

This is the conversational interface for LitigationOS — a ChatGPT-style
experience that runs 100 % offline.  Every query is answered by the local
MANBEARPIG engine (TF-IDF + Naive Bayes + BM25); no data ever leaves the
machine.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple

import customtkinter as ctk

from litigationos.gui.widgets import COLORS

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENGINE_PATH = Path(
    r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model\inference_engine.py"
)

SLASH_COMMANDS: Dict[str, str] = {
    "/help": "Show available commands",
    "/search <query>": "Search evidence database",
    "/deadline": "Show upcoming deadlines",
    "/evidence <query>": "Find evidence by keyword",
    "/rules <rule>": "Look up court rule (e.g., /rules MCR 2.119)",
    "/filing <id>": "Check filing status",
    "/stats": "Show database statistics",
    "/clear": "Clear chat history",
    "/export": "Export chat to markdown",
}

WELCOME_MESSAGE = (
    "🤖 Welcome to LitigationOS AI Assistant\n\n"
    "I'm MANBEARPIG v10 — your 100 % offline legal intelligence engine.\n"
    "No internet needed. No data leaves your machine.\n\n"
    "I can help with:\n"
    "  • 📜  Court rules — MCR, MCL, FRCP lookups\n"
    "  • 📋  Filing strategy — what to file, when, and how\n"
    "  • 🔍  Evidence analysis — search your evidence quotes\n"
    "  • ⏰  Deadlines — calculate and track filing deadlines\n"
    "  • ⚖️  Case law — research authorities and precedent\n\n"
    "Quick commands: /help  /search  /deadline  /stats  /rules\n\n"
    "Ask me anything about your litigation…"
)

MAX_INPUT_CHARS = 2000


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  ChatBubble                                                          ║
# ╚═══════════════════════════════════════════════════════════════════════╝


class ChatBubble(ctk.CTkFrame):
    """A single message bubble in the chat history."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        text: str,
        is_user: bool = False,
        timestamp: Optional[str] = None,
        **kwargs,
    ) -> None:
        bg = COLORS["accent"] if is_user else COLORS["bg_card"]
        super().__init__(parent, fg_color=bg, corner_radius=12, **kwargs)

        self._text = text
        self._is_user = is_user
        ts = timestamp or datetime.now().strftime("%H:%M")

        # --- outer padding --------------------------------------------------
        pad_frame = ctk.CTkFrame(self, fg_color="transparent")
        pad_frame.pack(fill="x", padx=10, pady=(6, 2))

        # Role icon
        icon = "👤" if is_user else "🤖"
        role_label = ctk.CTkLabel(
            pad_frame,
            text=f"{icon}  {'You' if is_user else 'MANBEARPIG'}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        )
        role_label.pack(side="left")

        # Timestamp
        ts_label = ctk.CTkLabel(
            pad_frame,
            text=ts,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"],
            anchor="e",
        )
        ts_label.pack(side="right")

        # --- message body (selectable CTkTextbox) ----------------------------
        line_count = min(max(text.count("\n") + 1, 1), 30)
        # Rough height: ~20 px per line + padding
        height = min(line_count * 20 + 16, 500)

        self._body = ctk.CTkTextbox(
            self,
            fg_color=bg,
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            height=height,
            activate_scrollbars=line_count > 20,
            border_width=0,
        )
        self._body.pack(fill="x", padx=10, pady=(0, 4))
        self._body.insert("1.0", text)
        self._body.configure(state="disabled")

        # --- copy button row -------------------------------------------------
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 6))

        copy_btn = ctk.CTkButton(
            btn_frame,
            text="📋 Copy",
            width=60,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color=COLORS["border"],
            hover_color=COLORS["bg_sidebar"],
            text_color=COLORS["text_dim"],
            corner_radius=6,
            command=self._copy_text,
        )
        copy_btn.pack(side="right")

    # -- helpers --------------------------------------------------------------

    def _copy_text(self) -> None:
        """Copy the full message to the system clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self._text)
        except Exception:
            pass


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  ChatFrame — main screen                                            ║
# ╚═══════════════════════════════════════════════════════════════════════╝


class ChatFrame(ctk.CTkFrame):
    """AI Chat interface powered by the MANBEARPIG inference engine."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        db: "DatabaseManager",
        navigate_cb: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb
        self._messages: List[Tuple[str, str, str]] = []  # (role, text, ts)
        self._busy = False

        self._ensure_chat_table()
        self._build_ui()
        self._load_history()

    # ------------------------------------------------------------------ #
    #  DB helpers                                                         #
    # ------------------------------------------------------------------ #

    def _ensure_chat_table(self) -> None:
        """Create the chat_history table if it doesn't already exist."""
        try:
            conn = self._db.connect()
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id        INTEGER PRIMARY KEY AUTOINCREMENT,
                        role      TEXT NOT NULL,
                        content   TEXT NOT NULL,
                        timestamp TEXT DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("Could not ensure chat_history table: %s", exc)

    def _persist_message(self, role: str, content: str) -> None:
        """Save a message to the database."""
        try:
            conn = self._db.connect()
            try:
                conn.execute(
                    "INSERT INTO chat_history (role, content) VALUES (?, ?)",
                    (role, content),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:
            logger.debug("Could not persist chat message: %s", exc)

    def _load_history(self) -> None:
        """Load prior messages from the DB and display them."""
        loaded = False
        try:
            conn = self._db.connect()
            try:
                rows = conn.execute(
                    "SELECT role, content, timestamp FROM chat_history "
                    "ORDER BY id ASC LIMIT 200"
                ).fetchall()
                for row in rows:
                    self._add_bubble(
                        row["content"],
                        is_user=(row["role"] == "user"),
                        timestamp=row["timestamp"],
                        persist=False,
                    )
                loaded = bool(rows)
            finally:
                conn.close()
        except Exception as exc:
            logger.debug("Could not load chat history: %s", exc)

        if not loaded:
            self._add_bubble(WELCOME_MESSAGE, is_user=False, persist=False)

    # ------------------------------------------------------------------ #
    #  UI construction                                                    #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_chat_area()
        self._build_input_area()

    # -- header -----------------------------------------------------------

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_sidebar"], height=50, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            header,
            text="💬  AI Legal Assistant — MANBEARPIG v10",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
        )
        title.grid(row=0, column=0, padx=16, pady=10, sticky="w")

        status = ctk.CTkLabel(
            header,
            text="🟢 Offline · Local-Only" if ENGINE_PATH.exists() else "🔴 Engine Missing",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["green"] if ENGINE_PATH.exists() else COLORS["red"],
        )
        status.grid(row=0, column=1, padx=16, pady=10, sticky="e")

        export_btn = ctk.CTkButton(
            header,
            text="📥 Export",
            width=80,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["border"],
            hover_color=COLORS["bg_card"],
            text_color=COLORS["text_dim"],
            corner_radius=6,
            command=self._export_chat,
        )
        export_btn.grid(row=0, column=2, padx=(0, 16), pady=10, sticky="e")

    # -- scrollable chat area ---------------------------------------------

    def _build_chat_area(self) -> None:
        self._chat_area = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_dark"],
            corner_radius=0,
        )
        self._chat_area.grid(row=1, column=0, sticky="nsew")
        self._chat_area.grid_columnconfigure(0, weight=1)

    # -- input area -------------------------------------------------------

    def _build_input_area(self) -> None:
        input_wrapper = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0)
        input_wrapper.grid(row=2, column=0, sticky="ew")
        input_wrapper.grid_columnconfigure(0, weight=1)

        # --- text entry row --------------------------------------------------
        entry_row = ctk.CTkFrame(input_wrapper, fg_color="transparent")
        entry_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        entry_row.grid_columnconfigure(0, weight=1)

        self._input_box = ctk.CTkTextbox(
            entry_row,
            height=60,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=COLORS["bg_dark"],
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=10,
            wrap="word",
        )
        self._input_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._input_box.bind("<Return>", self._on_enter)
        self._input_box.bind("<Shift-Return>", self._on_shift_enter)
        self._input_box.bind("<KeyRelease>", self._update_char_count)

        self._send_btn = ctk.CTkButton(
            entry_row,
            text="➤  Send",
            width=90,
            height=56,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color="#c0392b",
            text_color=COLORS["text"],
            corner_radius=10,
            command=self._send_message,
        )
        self._send_btn.grid(row=0, column=1, sticky="e")

        # --- char count + slash hints ----------------------------------------
        hints_row = ctk.CTkFrame(input_wrapper, fg_color="transparent")
        hints_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        hints_row.grid_columnconfigure(0, weight=1)

        hint_text = "  ".join(
            cmd for cmd in SLASH_COMMANDS if not cmd.startswith("/export")
        )
        hints_label = ctk.CTkLabel(
            hints_row,
            text=hint_text,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"],
            anchor="w",
        )
        hints_label.grid(row=0, column=0, sticky="w")

        self._char_count_label = ctk.CTkLabel(
            hints_row,
            text=f"0 / {MAX_INPUT_CHARS}",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"],
            anchor="e",
        )
        self._char_count_label.grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------ #
    #  Chat interaction logic                                             #
    # ------------------------------------------------------------------ #

    def _on_enter(self, event: "object" = None) -> str:
        """Enter = send.  Return 'break' to prevent newline insertion."""
        self._send_message()
        return "break"

    def _on_shift_enter(self, event: "object" = None) -> None:
        """Shift+Enter = insert newline (default behaviour, do nothing)."""

    def _update_char_count(self, event: "object" = None) -> None:
        text = self._input_box.get("1.0", "end-1c")
        count = len(text)
        colour = COLORS["text_dim"] if count <= MAX_INPUT_CHARS else COLORS["red"]
        self._char_count_label.configure(
            text=f"{count} / {MAX_INPUT_CHARS}", text_color=colour,
        )

    def _send_message(self) -> None:
        """Read input, display the user bubble, dispatch processing."""
        if self._busy:
            return

        text = self._input_box.get("1.0", "end-1c").strip()
        if not text:
            return
        if len(text) > MAX_INPUT_CHARS:
            self._add_bubble(
                f"⚠️ Message too long ({len(text)} chars). "
                f"Limit is {MAX_INPUT_CHARS}.",
                is_user=False,
                persist=False,
            )
            return

        # Clear input box
        self._input_box.delete("1.0", "end")
        self._update_char_count()

        # Show user bubble
        self._add_bubble(text, is_user=True)

        # Show typing indicator
        self._set_busy(True)
        self._typing_label = ctk.CTkLabel(
            self._chat_area,
            text="🤖 MANBEARPIG is thinking…",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=COLORS["text_dim"],
            anchor="w",
        )
        self._typing_label.pack(anchor="w", padx=16, pady=(4, 4))
        self._scroll_to_bottom()

        # Background thread
        threading.Thread(
            target=self._process_query, args=(text,), daemon=True
        ).start()

    def _process_query(self, text: str) -> None:
        """Run in a worker thread — resolve slash commands or call engine."""
        try:
            if text.startswith("/"):
                response = self._handle_slash_command(text)
            else:
                response = self._query_manbearpig(text)
        except Exception as exc:
            response = f"⚠️ Unexpected error: {exc}"

        # Schedule UI update on the main thread
        self.after(0, self._finish_response, response)

    def _finish_response(self, response: Optional[str]) -> None:
        """Called on the main thread after the worker is done."""
        # Remove typing indicator
        if hasattr(self, "_typing_label") and self._typing_label.winfo_exists():
            self._typing_label.destroy()

        if response is not None:
            self._add_bubble(response, is_user=False)

        self._set_busy(False)

    # ------------------------------------------------------------------ #
    #  Bubble management                                                  #
    # ------------------------------------------------------------------ #

    def _add_bubble(
        self,
        text: str,
        is_user: bool = False,
        timestamp: Optional[str] = None,
        persist: bool = True,
    ) -> None:
        """Create a ChatBubble and append it to the scrollable area."""
        ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M")
        anchor = "e" if is_user else "w"
        padx = (80, 12) if is_user else (12, 80)

        bubble = ChatBubble(
            self._chat_area,
            text=text,
            is_user=is_user,
            timestamp=ts,
        )
        bubble.pack(anchor=anchor, fill="x", padx=padx, pady=(6, 2))

        self._messages.append(("user" if is_user else "assistant", text, ts))

        if persist:
            self._persist_message("user" if is_user else "assistant", text)

        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        """Scroll the chat area to the very bottom."""
        self._chat_area.after(50, self._chat_area._parent_canvas.yview_moveto, 1.0)

    def _clear_chat(self) -> None:
        """Remove all bubbles from the chat area and wipe DB history."""
        for widget in self._chat_area.winfo_children():
            widget.destroy()
        self._messages.clear()

        try:
            conn = self._db.connect()
            try:
                conn.execute("DELETE FROM chat_history")
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

        self._add_bubble(WELCOME_MESSAGE, is_user=False, persist=False)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self._send_btn.configure(state=state)
        self._input_box.configure(state=state)

    # ------------------------------------------------------------------ #
    #  MANBEARPIG engine                                                  #
    # ------------------------------------------------------------------ #

    def _query_manbearpig(self, question: str) -> str:
        """Query the local MANBEARPIG inference engine via subprocess."""
        if not ENGINE_PATH.exists():
            return (
                "⚠️ MANBEARPIG engine not found at:\n"
                f"  {ENGINE_PATH}\n\n"
                "Run the setup script or check the path."
            )
        try:
            result = subprocess.run(
                [sys.executable, str(ENGINE_PATH), question],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(ENGINE_PATH.parent),
                env={**os.environ, "PYTHONUTF8": "1"},
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            stderr = (result.stderr or "").strip()
            if stderr:
                return f"⚠️ Engine error:\n{stderr[:500]}"
            return "No response from inference engine."
        except subprocess.TimeoutExpired:
            return "⏰ Query timed out (30 s). Try a shorter or simpler question."
        except FileNotFoundError:
            return "⚠️ Python interpreter not found. Check your installation."
        except Exception as exc:
            return f"⚠️ Error calling engine: {exc}"

    # ------------------------------------------------------------------ #
    #  Slash commands                                                     #
    # ------------------------------------------------------------------ #

    def _handle_slash_command(self, cmd: str) -> Optional[str]:
        """Dispatch a /slash command and return the response text."""
        cmd_lower = cmd.strip().lower()

        # /help ---------------------------------------------------------------
        if cmd_lower == "/help":
            lines = [f"  {k}  —  {v}" for k, v in SLASH_COMMANDS.items()]
            return "📖 Available commands:\n" + "\n".join(lines)

        # /clear --------------------------------------------------------------
        if cmd_lower == "/clear":
            self.after(0, self._clear_chat)
            return None

        # /export -------------------------------------------------------------
        if cmd_lower == "/export":
            return self._export_chat_to_md()

        # /stats --------------------------------------------------------------
        if cmd_lower == "/stats":
            return self._cmd_stats()

        # /deadline -----------------------------------------------------------
        if cmd_lower == "/deadline":
            return self._cmd_deadline()

        # /search <query> -----------------------------------------------------
        if cmd_lower.startswith("/search "):
            return self._cmd_search(cmd[8:].strip())

        # /evidence <query> ---------------------------------------------------
        if cmd_lower.startswith("/evidence "):
            return self._cmd_search(cmd[10:].strip())

        # /rules <rule> -------------------------------------------------------
        if cmd_lower.startswith("/rules "):
            rule_query = cmd[7:].strip()
            return self._query_manbearpig(f"Explain court rule: {rule_query}")

        # /filing <id> --------------------------------------------------------
        if cmd_lower.startswith("/filing "):
            return self._cmd_filing(cmd[8:].strip())

        # Unknown command — pass to engine
        return self._query_manbearpig(cmd)

    # -- /search & /evidence --------------------------------------------------

    def _cmd_search(self, query: str) -> str:
        if not query:
            return "Usage: /search <query>"
        try:
            conn = self._db.connect()
            try:
                rows = conn.execute(
                    "SELECT quote_text, source_file FROM evidence_quotes "
                    "WHERE quote_text LIKE ? LIMIT 10",
                    (f"%{query}%",),
                ).fetchall()
                if rows:
                    results = "\n".join(
                        f"  • {row['quote_text'][:120]}…\n"
                        f"    📄 {row['source_file']}"
                        for row in rows
                    )
                    return f"📎 Found {len(rows)} evidence match(es):\n{results}"
                return f"No evidence found for '{query}'."
            finally:
                conn.close()
        except Exception as exc:
            return f"⚠️ Search error: {exc}"

    # -- /stats ---------------------------------------------------------------

    def _cmd_stats(self) -> str:
        try:
            conn = self._db.connect()
            try:
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "ORDER BY name"
                ).fetchall()
                stats: List[str] = []
                for t in tables:
                    name = t["name"]
                    try:
                        count = conn.execute(
                            f"SELECT COUNT(*) AS c FROM [{name}]"
                        ).fetchone()["c"]
                        if count > 0:
                            stats.append(f"  {name}: {count:,} rows")
                    except Exception:
                        pass
                header = f"📊 Database Statistics — {len(tables)} tables"
                body = "\n".join(stats[:30]) if stats else "  (no populated tables)"
                if len(stats) > 30:
                    body += f"\n  … and {len(stats) - 30} more"
                return f"{header}\n{body}"
            finally:
                conn.close()
        except Exception as exc:
            return f"⚠️ Stats error: {exc}"

    # -- /deadline ------------------------------------------------------------

    def _cmd_deadline(self) -> str:
        try:
            conn = self._db.connect()
            try:
                # Verify column names dynamically
                cols = {
                    r["name"]
                    for r in conn.execute("PRAGMA table_info(deadlines)").fetchall()
                }
                if not cols:
                    return "⚠️ Deadlines table not found in this database."

                title_col = "title" if "title" in cols else "description"
                date_col = (
                    "due_date"
                    if "due_date" in cols
                    else "due_date_iso"
                    if "due_date_iso" in cols
                    else "deadline_date"
                )
                priority_col = "priority" if "priority" in cols else None
                status_col = "status" if "status" in cols else None

                where = f"WHERE [{status_col}] = 'pending'" if status_col else ""
                order = f"ORDER BY [{date_col}]" if date_col in cols else ""
                sql = (
                    f"SELECT [{title_col}], [{date_col}]"
                    + (f", [{priority_col}]" if priority_col else "")
                    + f" FROM deadlines {where} {order} LIMIT 10"
                )

                rows = conn.execute(sql).fetchall()
                if rows:
                    lines: List[str] = []
                    for r in rows:
                        icon = "🔴"
                        if priority_col and r[priority_col]:
                            p = str(r[priority_col]).lower()
                            if p in ("low", "normal"):
                                icon = "🟢"
                            elif p == "medium":
                                icon = "🟡"
                            elif p == "high":
                                icon = "🟠"
                        lines.append(
                            f"  {icon} {r[title_col]}  —  due {r[date_col]}"
                        )
                    return "⏰ Upcoming Deadlines:\n" + "\n".join(lines)
                return "No pending deadlines found."
            finally:
                conn.close()
        except Exception as exc:
            return f"⚠️ Deadline error: {exc}"

    # -- /filing <id> ---------------------------------------------------------

    def _cmd_filing(self, filing_id: str) -> str:
        if not filing_id:
            return "Usage: /filing <id>"
        try:
            conn = self._db.connect()
            try:
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name LIKE '%filing%'"
                ).fetchall()
                if not tables:
                    return "⚠️ No filing tables found in this database."

                for t in tables:
                    tname = t["name"]
                    try:
                        cols = {
                            r["name"]
                            for r in conn.execute(
                                f"PRAGMA table_info([{tname}])"
                            ).fetchall()
                        }
                        search_col = next(
                            (
                                c
                                for c in (
                                    "filing_id",
                                    "id",
                                    "vehicle_name",
                                    "case_number",
                                )
                                if c in cols
                            ),
                            None,
                        )
                        if not search_col:
                            continue
                        row = conn.execute(
                            f"SELECT * FROM [{tname}] WHERE [{search_col}] = ? LIMIT 1",
                            (filing_id,),
                        ).fetchone()
                        if row:
                            items = "\n".join(
                                f"  {k}: {row[k]}" for k in cols if row[k]
                            )
                            return f"📄 Filing from [{tname}]:\n{items}"
                    except Exception:
                        continue
                return f"No filing found with ID '{filing_id}'."
            finally:
                conn.close()
        except Exception as exc:
            return f"⚠️ Filing lookup error: {exc}"

    # ------------------------------------------------------------------ #
    #  Export                                                              #
    # ------------------------------------------------------------------ #

    def _export_chat_to_md(self) -> str:
        """Build a Markdown string from the current message history."""
        if not self._messages:
            return "Nothing to export."
        lines = [
            "# LitigationOS Chat Export",
            f"*Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        ]
        for role, text, ts in self._messages:
            prefix = "**You**" if role == "user" else "**MANBEARPIG**"
            lines.append(f"### {prefix}  _{ts}_\n")
            lines.append(text + "\n")
        return "\n".join(lines)

    def _export_chat(self) -> None:
        """Export chat to a Markdown file and show confirmation."""
        md = self._export_chat_to_md()
        export_dir = Path(
            r"C:\Users\andre\LitigationOS\Vault\90_REPORTS"
        )
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            export_dir = Path.home() / "Desktop"

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = export_dir / f"chat_export_{ts}.md"
        try:
            path.write_text(md, encoding="utf-8")
            self._add_bubble(
                f"✅ Chat exported to:\n  {path}", is_user=False, persist=False,
            )
        except Exception as exc:
            self._add_bubble(
                f"⚠️ Export failed: {exc}", is_user=False, persist=False,
            )

    # ------------------------------------------------------------------ #
    #  Public API (called by app.py refresh cycle)                        #
    # ------------------------------------------------------------------ #

    def refresh(self) -> None:
        """No-op refresh — chat doesn't auto-refresh, but keeps the API."""
