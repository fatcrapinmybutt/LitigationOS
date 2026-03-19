"""
ChatGPT Conversation Export Parser — LitigationOS Legal AI
==========================================================
Extracts legal analysis, citations, code blocks, and evidence references
from ChatGPT export files (conversations.json format).

Supports:
  - Full ChatGPT export parsing (array of conversation objects)
  - Michigan citations: MCL, MCR, MRE
  - Federal citations: USC, 42 U.S.C. § 1983, F.3d, S.Ct.
  - Case citations: NAME v NAME, Mich/NW2d reporters
  - Code block extraction with language detection
  - Legal analysis and strategy marker detection
  - Keyword search across parsed conversations
  - SQLite export with WAL mode and busy_timeout

Usage:
    from legal_ai.chatgpt_parser import ChatGPTParser
    parser = ChatGPTParser()
    conversations = parser.parse_export("path/to/conversations.json")
    parser.export_to_db(conversations, "chatgpt_extracts.db")
"""

from __future__ import annotations

import hashlib
import html
import json
import logging
import re
import sqlite3
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("legal_ai.chatgpt_parser")

# ── Data Models ──────────────────────────────────────────────────


@dataclass
class ChatMessage:
    """A single message from a ChatGPT conversation."""

    role: str  # user, assistant, system, tool
    content: str
    timestamp: Optional[float] = None
    message_id: str = ""

    def __post_init__(self) -> None:
        if not self.message_id:
            self.message_id = str(uuid.uuid4())


@dataclass
class CodeBlock:
    """An extracted code block with its language and surrounding context."""

    language: str
    code: str
    context: str = ""  # surrounding text for provenance


@dataclass
class LegalExtract:
    """A legal reference or analysis fragment extracted from conversation text."""

    extract_type: str  # citation, statute, case_ref, analysis, strategy
    text: str
    source_message_id: str = ""
    confidence: float = 0.0


@dataclass
class ParsedConversation:
    """Fully parsed ChatGPT conversation with extracted legal content."""

    conversation_id: str
    title: str
    create_time: Optional[float] = None
    messages: List[ChatMessage] = field(default_factory=list)
    code_blocks: List[CodeBlock] = field(default_factory=list)
    legal_extracts: List[LegalExtract] = field(default_factory=list)
    word_count: int = 0
    message_count: int = 0


# ── Regex Patterns ───────────────────────────────────────────────

# Michigan citations
_MCL_PAT = re.compile(r"\bMCL\s+\d+\.\d+[a-z]?\b", re.IGNORECASE)
_MCR_PAT = re.compile(r"\bMCR\s+\d+\.\d+(?:\([A-Z]\))?\b", re.IGNORECASE)
_MRE_PAT = re.compile(r"\bMRE\s+\d+\b", re.IGNORECASE)

# Michigan reporter citations: 123 Mich 456, 123 Mich App 456
_MICH_REPORTER = re.compile(r"\b\d+\s+Mich(?:\s+App)?\s+\d+\b")
# NW2d reporter: 123 NW.2d 456 or 123 NW2d 456
_NW2D_REPORTER = re.compile(r"\b\d+\s+NW\.?\s*2d\s+\d+\b")

# Case name pattern: Word(s) v. Word(s) — anchored to avoid over-matching
_CASE_NAME = re.compile(
    r"\b([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)*)"
    r"\s+v\.?\s+"
    r"([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)*)\b"
)

# Federal citations
_USC_PAT = re.compile(r"\b\d+\s+U\.?S\.?C\.?\s*§?\s*\d+\b", re.IGNORECASE)
_SECTION_1983 = re.compile(
    r"\b42\s+U\.?S\.?C\.?\s*§?\s*1983\b", re.IGNORECASE
)
_FED_REPORTER = re.compile(r"\b\d+\s+(?:F\.?\s*(?:2d|3d|4th)|S\.?\s*Ct\.?|U\.?S\.?)\s+\d+\b")

# Code block: fenced (```lang ... ```) — DOTALL for multi-line
_FENCED_CODE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)

# Legal analysis markers
_ANALYSIS_MARKERS = re.compile(
    r"\b(?:legal\s+analysis|legal\s+argument|motion\s+to|brief\s+in|"
    r"filing\s+deadline|cause\s+of\s+action|standard\s+of\s+review|"
    r"burden\s+of\s+proof|due\s+process|judicial\s+misconduct)\b",
    re.IGNORECASE,
)
# Strategy markers
_STRATEGY_MARKERS = re.compile(
    r"\b(?:strategy|strategic\s+approach|recommend(?:ation)?|"
    r"next\s+steps?|action\s+items?|tactical|game\s+plan)\b",
    re.IGNORECASE,
)


# ── DB Schema ────────────────────────────────────────────────────

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS chatgpt_conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    create_time REAL,
    message_count INTEGER,
    word_count INTEGER,
    legal_extract_count INTEGER,
    imported_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chatgpt_messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    role TEXT,
    content TEXT,
    timestamp REAL,
    FOREIGN KEY (conversation_id) REFERENCES chatgpt_conversations(id)
);

CREATE TABLE IF NOT EXISTS chatgpt_legal_extracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT,
    message_id TEXT,
    extract_type TEXT,
    text TEXT,
    confidence REAL,
    FOREIGN KEY (conversation_id) REFERENCES chatgpt_conversations(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_conv
    ON chatgpt_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_extracts_conv
    ON chatgpt_legal_extracts(conversation_id);
CREATE INDEX IF NOT EXISTS idx_extracts_type
    ON chatgpt_legal_extracts(extract_type);
"""


# ── Parser ───────────────────────────────────────────────────────


class ChatGPTParser:
    """Parse ChatGPT conversation exports and extract legal content.

    Handles the standard ChatGPT data export format where
    ``conversations.json`` is an array of conversation objects, each
    containing a ``mapping`` dict of message nodes.
    """

    def __init__(self) -> None:
        self._stats: Dict[str, int] = {
            "conversations_parsed": 0,
            "messages_extracted": 0,
            "code_blocks_found": 0,
            "legal_extracts_found": 0,
            "parse_errors": 0,
        }

    # ── Public API ───────────────────────────────────────────────

    def parse_export(self, json_path: str) -> List[ParsedConversation]:
        """Parse a full ChatGPT export file (conversations.json).

        Args:
            json_path: Path to conversations.json.

        Returns:
            List of parsed conversations with extracted legal content.
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Export file not found: {json_path}")

        logger.info("Parsing ChatGPT export: %s", json_path)

        raw_text = path.read_text(encoding="utf-8", errors="replace")
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error("Malformed JSON in %s: %s", json_path, exc)
            # Attempt recovery: try line-delimited JSON
            data = self._try_jsonl_fallback(raw_text)
            if data is None:
                raise ValueError(
                    f"Cannot parse {json_path} as JSON or JSONL"
                ) from exc

        if isinstance(data, dict):
            # Some exports wrap conversations under a key
            for key in ("conversations", "data", "items"):
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break
            else:
                # Single conversation object
                data = [data]

        if not isinstance(data, list):
            raise ValueError(
                f"Expected a JSON array of conversations, got {type(data).__name__}"
            )

        results: List[ParsedConversation] = []
        for idx, conv_obj in enumerate(data):
            if not isinstance(conv_obj, dict):
                logger.warning("Skipping non-dict entry at index %d", idx)
                self._stats["parse_errors"] += 1
                continue
            try:
                parsed = self.parse_single(conv_obj)
                results.append(parsed)
            except Exception as exc:
                logger.warning(
                    "Failed to parse conversation at index %d: %s", idx, exc
                )
                self._stats["parse_errors"] += 1

        logger.info(
            "Parsed %d conversations (%d errors)",
            len(results),
            self._stats["parse_errors"],
        )
        return results

    def parse_single(self, conversation: dict) -> ParsedConversation:
        """Parse a single ChatGPT conversation object.

        Args:
            conversation: A conversation dict from the export.

        Returns:
            ParsedConversation with messages, code blocks, and legal extracts.
        """
        conv_id = conversation.get("id") or conversation.get(
            "conversation_id", str(uuid.uuid4())
        )
        title = conversation.get("title") or "(untitled)"
        create_time = conversation.get("create_time")

        messages = self._extract_messages(conversation)
        all_code_blocks: List[CodeBlock] = []
        all_legal_extracts: List[LegalExtract] = []
        total_words = 0

        for msg in messages:
            if not msg.content:
                continue

            total_words += len(msg.content.split())

            code_blocks = self.extract_code_blocks(msg.content)
            for cb in code_blocks:
                all_code_blocks.append(cb)

            legal_extracts = self.extract_legal_content(msg.content)
            for le in legal_extracts:
                le.source_message_id = msg.message_id
                all_legal_extracts.append(le)

        self._stats["conversations_parsed"] += 1
        self._stats["messages_extracted"] += len(messages)
        self._stats["code_blocks_found"] += len(all_code_blocks)
        self._stats["legal_extracts_found"] += len(all_legal_extracts)

        return ParsedConversation(
            conversation_id=conv_id,
            title=title,
            create_time=create_time,
            messages=messages,
            code_blocks=all_code_blocks,
            legal_extracts=all_legal_extracts,
            word_count=total_words,
            message_count=len(messages),
        )

    def extract_legal_content(self, text: str) -> List[LegalExtract]:
        """Extract legal citations, case references, and analysis markers.

        Args:
            text: Raw message text to scan.

        Returns:
            List of LegalExtract objects found in the text.
        """
        if not text:
            return []

        # Normalize HTML entities that appear in some exports
        clean = html.unescape(text)
        extracts: List[LegalExtract] = []
        seen: set = set()

        def _add(extract_type: str, match_text: str, confidence: float) -> None:
            key = (extract_type, match_text.strip())
            if key not in seen:
                seen.add(key)
                extracts.append(
                    LegalExtract(
                        extract_type=extract_type,
                        text=match_text.strip(),
                        confidence=confidence,
                    )
                )

        # Michigan statutes — high confidence
        for m in _MCL_PAT.finditer(clean):
            _add("statute", m.group(), 0.95)
        for m in _MCR_PAT.finditer(clean):
            _add("statute", m.group(), 0.95)
        for m in _MRE_PAT.finditer(clean):
            _add("statute", m.group(), 0.90)

        # Michigan case reporters
        for m in _MICH_REPORTER.finditer(clean):
            _add("citation", m.group(), 0.90)
        for m in _NW2D_REPORTER.finditer(clean):
            _add("citation", m.group(), 0.90)

        # Federal statutes
        for m in _SECTION_1983.finditer(clean):
            _add("statute", m.group(), 0.95)
        for m in _USC_PAT.finditer(clean):
            # Skip if already captured as § 1983
            if not _SECTION_1983.search(m.group()):
                _add("statute", m.group(), 0.85)

        # Federal reporter citations
        for m in _FED_REPORTER.finditer(clean):
            _add("citation", m.group(), 0.85)

        # Case name references (NAME v NAME)
        for m in _CASE_NAME.finditer(clean):
            full = m.group()
            # Filter out common false positives
            if self._is_plausible_case_name(full):
                _add("case_ref", full, 0.75)

        # Legal analysis fragments — extract surrounding sentence
        for m in _ANALYSIS_MARKERS.finditer(clean):
            sentence = self._extract_sentence(clean, m.start(), m.end())
            _add("analysis", sentence, 0.70)

        # Strategy markers
        for m in _STRATEGY_MARKERS.finditer(clean):
            sentence = self._extract_sentence(clean, m.start(), m.end())
            _add("strategy", sentence, 0.65)

        return extracts

    def extract_code_blocks(self, text: str) -> List[CodeBlock]:
        """Extract fenced code blocks from message text.

        Args:
            text: Raw message text.

        Returns:
            List of CodeBlock objects.
        """
        if not text:
            return []

        blocks: List[CodeBlock] = []
        for m in _FENCED_CODE.finditer(text):
            lang = m.group(1) or "text"
            code = m.group(2).rstrip("\n")
            # Grab a few words before the code block as context
            ctx_start = max(0, m.start() - 120)
            context = text[ctx_start : m.start()].strip()
            # Trim context to last complete sentence or line
            if "\n" in context:
                context = context.rsplit("\n", 1)[-1].strip()
            blocks.append(CodeBlock(language=lang, code=code, context=context))

        return blocks

    def search_conversations(
        self, conversations: List[ParsedConversation], query: str
    ) -> List[ParsedConversation]:
        """Search parsed conversations by keyword (case-insensitive).

        Args:
            conversations: List of previously parsed conversations.
            query: Search query string.

        Returns:
            Conversations whose title or message content matches the query.
        """
        if not query:
            return list(conversations)

        query_lower = query.lower()
        terms = query_lower.split()
        results: List[ParsedConversation] = []

        for conv in conversations:
            # Check title
            if all(t in (conv.title or "").lower() for t in terms):
                results.append(conv)
                continue

            # Check message content
            matched = False
            for msg in conv.messages:
                if msg.content and all(
                    t in msg.content.lower() for t in terms
                ):
                    matched = True
                    break
            if matched:
                results.append(conv)
                continue

            # Check legal extract text
            for le in conv.legal_extracts:
                if all(t in le.text.lower() for t in terms):
                    matched = True
                    break
            if matched:
                results.append(conv)

        return results

    def export_to_db(
        self, conversations: List[ParsedConversation], db_path: str
    ) -> None:
        """Export parsed conversations to a SQLite database.

        Creates tables if they do not exist. Uses WAL journal mode and
        busy_timeout for safe concurrent access.

        Args:
            conversations: Parsed conversations to export.
            db_path: Path to the SQLite database file.
        """
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Exporting %d conversations to %s", len(conversations), db_path)

        conn = sqlite3.connect(str(db_file))
        try:
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA cache_size = -32000")
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.executescript(_SCHEMA_SQL)

            conv_rows = []
            msg_rows = []
            extract_rows = []

            for conv in conversations:
                conv_rows.append((
                    conv.conversation_id,
                    conv.title,
                    conv.create_time,
                    conv.message_count,
                    conv.word_count,
                    len(conv.legal_extracts),
                ))

                for msg in conv.messages:
                    msg_rows.append((
                        msg.message_id,
                        conv.conversation_id,
                        msg.role,
                        msg.content,
                        msg.timestamp,
                    ))

                for le in conv.legal_extracts:
                    extract_rows.append((
                        conv.conversation_id,
                        le.source_message_id,
                        le.extract_type,
                        le.text,
                        le.confidence,
                    ))

            conn.executemany(
                "INSERT OR REPLACE INTO chatgpt_conversations "
                "(id, title, create_time, message_count, word_count, legal_extract_count) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                conv_rows,
            )
            conn.executemany(
                "INSERT OR REPLACE INTO chatgpt_messages "
                "(id, conversation_id, role, content, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                msg_rows,
            )
            conn.executemany(
                "INSERT INTO chatgpt_legal_extracts "
                "(conversation_id, message_id, extract_type, text, confidence) "
                "VALUES (?, ?, ?, ?, ?)",
                extract_rows,
            )
            conn.commit()

            logger.info(
                "Exported: %d conversations, %d messages, %d legal extracts",
                len(conv_rows),
                len(msg_rows),
                len(extract_rows),
            )
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, int]:
        """Return cumulative parsing statistics.

        Returns:
            Dict with counts of conversations, messages, code blocks,
            legal extracts, and parse errors.
        """
        return dict(self._stats)

    # ── Private Helpers ──────────────────────────────────────────

    def _extract_messages(self, conversation: dict) -> List[ChatMessage]:
        """Walk the conversation tree and extract messages in order.

        ChatGPT exports store messages in a ``mapping`` dict where each
        node has an ``id``, optional ``parent``, and ``message`` payload.
        This method linearises the tree into chronological order.
        """
        messages: List[ChatMessage] = []

        # Format 1: mapping-based (standard ChatGPT export)
        mapping = conversation.get("mapping")
        if isinstance(mapping, dict):
            nodes = self._linearise_mapping(mapping)
            for node in nodes:
                msg = self._node_to_message(node)
                if msg is not None:
                    messages.append(msg)
            return messages

        # Format 2: flat messages array
        raw_messages = conversation.get("messages")
        if isinstance(raw_messages, list):
            for raw in raw_messages:
                msg = self._raw_to_message(raw)
                if msg is not None:
                    messages.append(msg)
            return messages

        # Format 3: bare conversation with content keys
        if "content" in conversation or "text" in conversation:
            content = conversation.get("content") or conversation.get("text", "")
            if content:
                messages.append(
                    ChatMessage(
                        role=conversation.get("role", "unknown"),
                        content=str(content),
                        timestamp=conversation.get("create_time"),
                    )
                )

        return messages

    def _linearise_mapping(self, mapping: dict) -> List[dict]:
        """Sort mapping nodes into parent→child order."""
        # Find root(s) — nodes whose parent is None or absent
        children_of: Dict[Optional[str], List[str]] = {}
        for node_id, node in mapping.items():
            parent = node.get("parent")
            children_of.setdefault(parent, []).append(node_id)

        ordered: List[dict] = []
        # BFS from root(s)
        queue = list(children_of.get(None, []))
        visited: set = set()
        while queue:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            node = mapping.get(nid)
            if node is not None:
                ordered.append(node)
            queue.extend(children_of.get(nid, []))

        return ordered

    def _node_to_message(self, node: dict) -> Optional[ChatMessage]:
        """Convert a mapping node to a ChatMessage, or None if empty."""
        msg_data = node.get("message")
        if not isinstance(msg_data, dict):
            return None

        author = msg_data.get("author", {})
        role = author.get("role", "unknown") if isinstance(author, dict) else "unknown"

        content_obj = msg_data.get("content", {})
        content = self._resolve_content(content_obj)
        if not content:
            return None

        return ChatMessage(
            role=role,
            content=content,
            timestamp=msg_data.get("create_time"),
            message_id=msg_data.get("id", node.get("id", str(uuid.uuid4()))),
        )

    def _raw_to_message(self, raw: Any) -> Optional[ChatMessage]:
        """Convert a flat message dict to a ChatMessage."""
        if not isinstance(raw, dict):
            return None

        role = raw.get("role") or raw.get("author", {}).get("role", "unknown")
        content_obj = raw.get("content", "")
        content = self._resolve_content(content_obj)
        if not content:
            return None

        return ChatMessage(
            role=role,
            content=content,
            timestamp=raw.get("create_time") or raw.get("timestamp"),
            message_id=raw.get("id", str(uuid.uuid4())),
        )

    @staticmethod
    def _resolve_content(content_obj: Any) -> str:
        """Normalise various content representations to a plain string."""
        if isinstance(content_obj, str):
            return html.unescape(content_obj).strip()

        if isinstance(content_obj, dict):
            parts = content_obj.get("parts")
            if isinstance(parts, list):
                text_parts = []
                for part in parts:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict):
                        # Image or file attachment — note its presence
                        text_parts.append(
                            part.get("text", part.get("content_type", "[attachment]"))
                        )
                return html.unescape("\n".join(text_parts)).strip()
            # Fallback to text key
            text = content_obj.get("text", "")
            if isinstance(text, str):
                return html.unescape(text).strip()

        if isinstance(content_obj, list):
            # Some formats use a bare list of strings
            return html.unescape(
                "\n".join(str(p) for p in content_obj if p)
            ).strip()

        return ""

    @staticmethod
    def _is_plausible_case_name(text: str) -> bool:
        """Filter out false-positive case name matches."""
        # Reject very short matches or common non-case phrases
        parts = text.split()
        if len(parts) < 3:
            return False
        # 'v' or 'v.' must be in the middle
        v_idx = None
        for i, w in enumerate(parts):
            if w.lower() in ("v", "v."):
                v_idx = i
                break
        if v_idx is None or v_idx == 0 or v_idx == len(parts) - 1:
            return False

        # Reject if both sides are single very common words
        _STOP = {
            "The", "This", "That", "If", "Or", "And", "But", "Not",
            "It", "We", "He", "She", "They", "You", "My", "Our",
            "What", "How", "When", "Where", "Why", "Which",
        }
        left_word = parts[v_idx - 1]
        right_word = parts[v_idx + 1]
        if left_word in _STOP or right_word in _STOP:
            return False

        return True

    @staticmethod
    def _extract_sentence(text: str, start: int, end: int) -> str:
        """Extract the sentence surrounding a match span."""
        # Walk backward to sentence start
        s = start
        while s > 0 and text[s - 1] not in ".!?\n":
            s -= 1

        # Walk forward to sentence end
        e = end
        while e < len(text) and text[e] not in ".!?\n":
            e += 1
        if e < len(text) and text[e] in ".!?":
            e += 1  # include the punctuation

        sentence = text[s:e].strip()
        # Cap length to avoid pulling in entire paragraphs
        if len(sentence) > 500:
            sentence = sentence[:500] + "…"
        return sentence

    @staticmethod
    def _try_jsonl_fallback(raw_text: str) -> Optional[list]:
        """Attempt to parse as line-delimited JSON (one object per line)."""
        results = []
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    results.append(obj)
            except json.JSONDecodeError:
                continue
        return results if results else None


# ── CLI Entry Point ──────────────────────────────────────────────

def main() -> None:
    """Minimal CLI: parse a ChatGPT export and print summary stats."""
    if len(sys.argv) < 2:
        print("Usage: python chatgpt_parser.py <conversations.json> [--db <output.db>]")
        sys.exit(1)

    # UTF-8 stdout safety
    if hasattr(sys.stdout, "fileno"):
        try:
            sys.stdout = open(
                sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
            )
        except Exception:
            pass

    json_path = sys.argv[1]
    db_path = None
    if "--db" in sys.argv:
        db_idx = sys.argv.index("--db")
        if db_idx + 1 < len(sys.argv):
            db_path = sys.argv[db_idx + 1]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    parser = ChatGPTParser()
    conversations = parser.parse_export(json_path)

    print(f"\n{'=' * 60}")
    print(f"ChatGPT Export Parse Results")
    print(f"{'=' * 60}")
    print(f"Conversations: {len(conversations)}")

    total_msgs = sum(c.message_count for c in conversations)
    total_words = sum(c.word_count for c in conversations)
    total_code = sum(len(c.code_blocks) for c in conversations)
    total_legal = sum(len(c.legal_extracts) for c in conversations)

    print(f"Messages:      {total_msgs}")
    print(f"Words:         {total_words:,}")
    print(f"Code blocks:   {total_code}")
    print(f"Legal extracts:{total_legal}")

    # Breakdown by extract type
    type_counts: Dict[str, int] = {}
    for conv in conversations:
        for le in conv.legal_extracts:
            type_counts[le.extract_type] = type_counts.get(le.extract_type, 0) + 1
    if type_counts:
        print(f"\nExtract types:")
        for etype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {etype:12s}: {count}")

    stats = parser.get_stats()
    if stats.get("parse_errors"):
        print(f"\nParse errors:  {stats['parse_errors']}")

    if db_path:
        parser.export_to_db(conversations, db_path)
        print(f"\nExported to: {db_path}")

    print()


if __name__ == "__main__":
    main()
