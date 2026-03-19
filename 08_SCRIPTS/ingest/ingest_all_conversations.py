#!/usr/bin/env python3
"""
ingest_all_conversations.py — Ingest ALL conversation data into litigation_context.db

Sources:
  - Gemini masterpacks (01_DATA/gemini_masterpack, gemini_masterpack_03)
  - Gemini CLI chat log (99_ARCHIVE/home_cleanup/wholeGEMNI_CLI_chat.md)
  - Copilot all chat (99_ARCHIVE/home_cleanup/MEEK_COPILOT_ALLCHAT.md)
  - Copilot session exports (02_EVIDENCE/session_exports/)
  - Copilot extracted session state (02_EVIDENCE/extracts/C__Users_andre_...)

Tables created/populated:
  - gemini_conversations + gemini_conversations_fts
  - copilot_sessions + copilot_sessions_fts
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = r"C:\Users\andre\litigation_context.db"
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")

GEMINI_MASTERPACK = LITIGOS_ROOT / "01_DATA" / "gemini_masterpack"
GEMINI_MASTERPACK_03 = LITIGOS_ROOT / "01_DATA" / "gemini_masterpack_03"
GEMINI_CLI_CHAT = LITIGOS_ROOT / "99_ARCHIVE" / "home_cleanup" / "wholeGEMNI_CLI_chat.md"
COPILOT_ALLCHAT = LITIGOS_ROOT / "99_ARCHIVE" / "home_cleanup" / "MEEK_COPILOT_ALLCHAT.md"
COPILOT_SESSION_EXPORTS = LITIGOS_ROOT / "02_EVIDENCE" / "session_exports"
COPILOT_EXTRACTS = (
    LITIGOS_ROOT
    / "02_EVIDENCE"
    / "extracts"
    / "C__Users_andre_.copilot_session-state_session-state"
)

# Extensions to ingest as text (skip binary like .png, .zip)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".jsonl", ".csv", ".py", ".ps1", ".sh",
    ".html", ".yaml", ".yml", ".toml", ".env", ".rtf", ".geminiignore",
}

BATCH_SIZE = 500

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def content_hash(text: str) -> str:
    """SHA-256 of text for dedup."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def read_file_safe(path: Path) -> str | None:
    """Read a text file with encoding fallbacks."""
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            return None
    return None


def infer_content_type(filename: str) -> str:
    """Infer copilot content_type from filename."""
    name = filename.lower()
    if "checkpoint" in name:
        return "checkpoint"
    if "plan" in name:
        return "plan"
    if "audit" in name:
        return "audit"
    if "event" in name:
        return "events"
    if "index" in name:
        return "index"
    if "summary" in name:
        return "summary"
    if "context" in name:
        return "context"
    return "artifact"


def extract_session_id(filepath: Path) -> str:
    """Extract session UUID from path components."""
    for part in filepath.parts:
        if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", part):
            # May have suffixes like __checkpoints__001-...
            return part.split("__")[0]
    return ""


def parse_conversation_turns(text: str) -> list[dict]:
    """Parse a markdown chat log into user/assistant turns.

    Heuristics:
      - Lines starting with 'User:' or '>' → user turn
      - Lines starting with 'Model:', 'Assistant:', 'Copilot:', 'Gemini:' → assistant
      - Consecutive lines of same role are merged
    """
    turns = []
    current_role = None
    current_lines: list[str] = []

    role_patterns = [
        (re.compile(r"^(?:User|Human|Me)\s*:\s*", re.IGNORECASE), "user"),
        (re.compile(r"^>\s*"), "user"),
        (re.compile(r"^(?:Model|Assistant|Copilot|Gemini|AI|Response)\s*:\s*", re.IGNORECASE), "assistant"),
    ]

    def flush():
        if current_role and current_lines:
            text_block = "\n".join(current_lines).strip()
            if text_block:
                turns.append({"role": current_role, "text": text_block})

    for line in text.split("\n"):
        matched_role = None
        cleaned_line = line
        for pattern, role in role_patterns:
            m = pattern.match(line)
            if m:
                matched_role = role
                cleaned_line = line[m.end():]
                break

        if matched_role and matched_role != current_role:
            flush()
            current_role = matched_role
            current_lines = [cleaned_line]
        elif matched_role:
            current_lines.append(cleaned_line)
        else:
            if current_role:
                current_lines.append(line)
            else:
                # Before first role marker, treat as assistant context
                current_role = "assistant"
                current_lines.append(line)

    flush()
    return turns


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS gemini_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT,
    conversation_id TEXT,
    message_role TEXT,
    message_text TEXT,
    message_index INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    ingested_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS copilot_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    source_file TEXT,
    content_type TEXT,
    title TEXT,
    content TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    ingested_at TEXT DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS gemini_conversations_fts USING fts5(
    message_text, source_file, conversation_id,
    content='gemini_conversations',
    content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS copilot_sessions_fts USING fts5(
    content, title, session_id,
    content='copilot_sessions',
    content_rowid='id'
);
"""

# ---------------------------------------------------------------------------
# Ingestion functions
# ---------------------------------------------------------------------------

class Ingester:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-64000")  # 64 MB cache
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

        # Build dedup sets from existing rows
        print("Building dedup indexes from existing rows...")
        self._gemini_hashes: set[str] = set()
        for (h,) in self.conn.execute(
            "SELECT DISTINCT source_file FROM gemini_conversations WHERE source_file IS NOT NULL"
        ):
            self._gemini_hashes.add(h)

        self._copilot_hashes: set[str] = set()
        for (h,) in self.conn.execute(
            "SELECT DISTINCT source_file FROM copilot_sessions WHERE source_file IS NOT NULL"
        ):
            self._copilot_hashes.add(h)

        self.stats = {
            "gemini_inserted": 0,
            "gemini_skipped": 0,
            "copilot_inserted": 0,
            "copilot_skipped": 0,
            "errors": [],
        }

    # -- Gemini bulk files ------------------------------------------------

    def _insert_gemini_batch(self, rows: list[tuple]):
        if not rows:
            return
        self.conn.executemany(
            "INSERT INTO gemini_conversations "
            "(source_file, conversation_id, message_role, message_text, message_index) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        self.stats["gemini_inserted"] += len(rows)

    def ingest_gemini_masterpacks(self):
        """Ingest all text files from gemini masterpack dirs."""
        print("\n=== Ingesting Gemini Masterpacks ===")
        dirs = [GEMINI_MASTERPACK, GEMINI_MASTERPACK_03]
        batch: list[tuple] = []
        processed = 0

        for d in dirs:
            if not d.exists():
                print(f"  SKIP (missing): {d}")
                continue
            files = sorted(d.rglob("*"))
            for fp in files:
                if not fp.is_file():
                    continue
                if fp.suffix.lower() not in TEXT_EXTENSIONS:
                    continue

                rel = str(fp)
                if rel in self._gemini_hashes:
                    self.stats["gemini_skipped"] += 1
                    continue

                try:
                    text = read_file_safe(fp)
                    if text is None or not text.strip():
                        continue

                    # For JSON files, try to parse conversation structure
                    if fp.suffix.lower() in (".json", ".jsonl"):
                        self._ingest_gemini_json(fp, text, batch)
                    else:
                        conv_id = fp.stem
                        batch.append((rel, conv_id, "mixed", text, 0))

                    self._gemini_hashes.add(rel)
                    processed += 1
                    if processed % 100 == 0:
                        print(f"  Processed {processed} files...")
                        if len(batch) >= BATCH_SIZE:
                            self._insert_gemini_batch(batch)
                            batch.clear()
                            self.conn.commit()

                except Exception as e:
                    self.stats["errors"].append(f"gemini_masterpack:{fp.name}: {e}")

        self._insert_gemini_batch(batch)
        self.conn.commit()
        print(f"  Masterpacks done: {processed} files processed")

    def _ingest_gemini_json(self, fp: Path, text: str, batch: list[tuple]):
        """Try to parse JSON conversation structure."""
        rel = str(fp)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # JSONL: one JSON object per line
            for i, line in enumerate(text.strip().split("\n")):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    msg = obj.get("text", obj.get("content", obj.get("message", json.dumps(obj))))
                    role = obj.get("role", obj.get("author", "mixed"))
                    batch.append((rel, fp.stem, str(role), str(msg), i))
                except json.JSONDecodeError:
                    batch.append((rel, fp.stem, "mixed", line, i))
            return

        # Single JSON object or array
        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    msg = item.get("text", item.get("content", item.get("message", json.dumps(item))))
                    role = item.get("role", item.get("author", "mixed"))
                    batch.append((rel, fp.stem, str(role), str(msg), i))
                else:
                    batch.append((rel, fp.stem, "mixed", str(item), i))
        elif isinstance(data, dict):
            # Might have a messages array
            messages = data.get("messages", data.get("conversation", data.get("turns", [])))
            if isinstance(messages, list) and messages:
                for i, item in enumerate(messages):
                    if isinstance(item, dict):
                        msg = item.get("text", item.get("content", item.get("message", json.dumps(item))))
                        role = item.get("role", item.get("author", "mixed"))
                        batch.append((rel, fp.stem, str(role), str(msg), i))
                    else:
                        batch.append((rel, fp.stem, "mixed", str(item), i))
            else:
                batch.append((rel, fp.stem, "mixed", text, 0))

    def ingest_gemini_cli_chat(self):
        """Parse and ingest the Gemini CLI chat log."""
        print("\n=== Ingesting Gemini CLI Chat ===")
        if not GEMINI_CLI_CHAT.exists():
            print("  SKIP (missing)")
            return

        rel = str(GEMINI_CLI_CHAT)
        if rel in self._gemini_hashes:
            print("  SKIP (already ingested)")
            self.stats["gemini_skipped"] += 1
            return

        text = read_file_safe(GEMINI_CLI_CHAT)
        if not text:
            print("  SKIP (empty/unreadable)")
            return

        turns = parse_conversation_turns(text)
        batch = []
        for i, turn in enumerate(turns):
            batch.append((rel, "gemini_cli_chat", turn["role"], turn["text"], i))

        self._insert_gemini_batch(batch)
        self._gemini_hashes.add(rel)
        self.conn.commit()
        print(f"  Ingested {len(turns)} turns from Gemini CLI chat")

    # -- Copilot ----------------------------------------------------------

    def _insert_copilot_batch(self, rows: list[tuple]):
        if not rows:
            return
        self.conn.executemany(
            "INSERT INTO copilot_sessions "
            "(session_id, source_file, content_type, title, content) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        self.stats["copilot_inserted"] += len(rows)

    def ingest_copilot_allchat(self):
        """Parse and ingest the full Copilot chat archive."""
        print("\n=== Ingesting Copilot All-Chat ===")
        if not COPILOT_ALLCHAT.exists():
            print("  SKIP (missing)")
            return

        rel = str(COPILOT_ALLCHAT)
        if rel in self._copilot_hashes:
            print("  SKIP (already ingested)")
            self.stats["copilot_skipped"] += 1
            return

        text = read_file_safe(COPILOT_ALLCHAT)
        if not text:
            print("  SKIP (empty/unreadable)")
            return

        turns = parse_conversation_turns(text)
        batch = []
        for i, turn in enumerate(turns):
            batch.append(("copilot_allchat", rel, "turn", f"turn_{i}_{turn['role']}", turn["text"]))

        self._insert_copilot_batch(batch)
        self._copilot_hashes.add(rel)
        self.conn.commit()
        print(f"  Ingested {len(turns)} turns from Copilot all-chat")

    def ingest_copilot_session_exports(self):
        """Ingest session export .md files."""
        print("\n=== Ingesting Copilot Session Exports ===")
        if not COPILOT_SESSION_EXPORTS.exists():
            print("  SKIP (missing)")
            return

        batch: list[tuple] = []
        processed = 0

        for fp in sorted(COPILOT_SESSION_EXPORTS.rglob("*")):
            if not fp.is_file() or fp.suffix.lower() not in TEXT_EXTENSIONS:
                continue

            rel = str(fp)
            if rel in self._copilot_hashes:
                self.stats["copilot_skipped"] += 1
                continue

            try:
                text = read_file_safe(fp)
                if not text or not text.strip():
                    continue

                ctype = infer_content_type(fp.name)
                session_id = extract_session_id(fp)
                title = fp.stem

                batch.append((session_id, rel, ctype, title, text))
                self._copilot_hashes.add(rel)
                processed += 1

                if len(batch) >= BATCH_SIZE:
                    self._insert_copilot_batch(batch)
                    batch.clear()
                    self.conn.commit()

            except Exception as e:
                self.stats["errors"].append(f"session_exports:{fp.name}: {e}")

        self._insert_copilot_batch(batch)
        self.conn.commit()
        print(f"  Session exports done: {processed} files ingested")

    def ingest_copilot_extracts(self):
        """Ingest extracted Copilot session state files."""
        print("\n=== Ingesting Copilot Extracted Session State ===")
        if not COPILOT_EXTRACTS.exists():
            print("  SKIP (missing)")
            return

        batch: list[tuple] = []
        processed = 0

        for fp in sorted(COPILOT_EXTRACTS.rglob("*")):
            if not fp.is_file():
                continue
            if fp.suffix.lower() not in TEXT_EXTENSIONS:
                continue

            rel = str(fp)
            if rel in self._copilot_hashes:
                self.stats["copilot_skipped"] += 1
                continue

            try:
                text = read_file_safe(fp)
                if not text or not text.strip():
                    continue

                session_id = extract_session_id(fp)
                ctype = infer_content_type(fp.name)
                title = fp.stem

                batch.append((session_id, rel, ctype, title, text))
                self._copilot_hashes.add(rel)
                processed += 1

                if processed % 100 == 0:
                    print(f"  Processed {processed} extract files...")

                if len(batch) >= BATCH_SIZE:
                    self._insert_copilot_batch(batch)
                    batch.clear()
                    self.conn.commit()

            except Exception as e:
                self.stats["errors"].append(f"extracts:{fp.name}: {e}")

        self._insert_copilot_batch(batch)
        self.conn.commit()
        print(f"  Extracts done: {processed} files ingested")

    # -- FTS rebuild & stats ----------------------------------------------

    def rebuild_fts(self):
        """Rebuild FTS indexes."""
        print("\n=== Rebuilding FTS Indexes ===")
        try:
            self.conn.execute(
                "INSERT INTO gemini_conversations_fts(gemini_conversations_fts) VALUES('rebuild')"
            )
            print("  gemini_conversations_fts rebuilt")
        except Exception as e:
            print(f"  gemini_conversations_fts rebuild error: {e}")
            self.stats["errors"].append(f"fts_rebuild:gemini: {e}")

        try:
            self.conn.execute(
                "INSERT INTO copilot_sessions_fts(copilot_sessions_fts) VALUES('rebuild')"
            )
            print("  copilot_sessions_fts rebuilt")
        except Exception as e:
            print(f"  copilot_sessions_fts rebuild error: {e}")
            self.stats["errors"].append(f"fts_rebuild:copilot: {e}")

        self.conn.commit()

    def print_stats(self):
        """Print final ingestion statistics."""
        print("\n" + "=" * 60)
        print("INGESTION COMPLETE — STATISTICS")
        print("=" * 60)

        # Table row counts
        tables = [
            ("chatgpt_conversations", "(existing)"),
            ("gemini_conversations", "(new)"),
            ("copilot_sessions", "(new)"),
        ]
        total = 0
        for tbl, label in tables:
            try:
                (count,) = self.conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()
                print(f"  {tbl:40s} {label:10s} {count:>10,} rows")
                total += count
            except Exception:
                print(f"  {tbl:40s} {'ERROR':10s}")

        print(f"  {'TOTAL':40s} {'':10s} {total:>10,} rows")
        print()
        print(f"  Gemini rows inserted this run:   {self.stats['gemini_inserted']:>10,}")
        print(f"  Gemini rows skipped (dedup):     {self.stats['gemini_skipped']:>10,}")
        print(f"  Copilot rows inserted this run:  {self.stats['copilot_inserted']:>10,}")
        print(f"  Copilot rows skipped (dedup):    {self.stats['copilot_skipped']:>10,}")
        print()

        if self.stats["errors"]:
            print(f"  ERRORS ({len(self.stats['errors'])}):")
            for e in self.stats["errors"][:20]:
                print(f"    - {e}")
            if len(self.stats["errors"]) > 20:
                print(f"    ... and {len(self.stats['errors']) - 20} more")
        else:
            print("  No errors.")

        print("=" * 60)

    def close(self):
        self.conn.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    start = time.time()
    print("=" * 60)
    print("LitigationOS — Conversation Ingestion Pipeline")
    print(f"Database: {DB_PATH}")
    print("=" * 60)

    ing = Ingester(DB_PATH)

    # Gemini sources
    ing.ingest_gemini_masterpacks()
    ing.ingest_gemini_cli_chat()

    # Copilot sources
    ing.ingest_copilot_allchat()
    ing.ingest_copilot_session_exports()
    ing.ingest_copilot_extracts()

    # FTS & stats
    ing.rebuild_fts()
    ing.print_stats()

    elapsed = time.time() - start
    print(f"\nCompleted in {elapsed:.1f}s")
    ing.close()


if __name__ == "__main__":
    main()
