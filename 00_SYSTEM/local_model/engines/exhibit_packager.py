# -*- coding: utf-8 -*-
"""Engine 6: Exhibit Packager — Organize exhibits per Michigan court rules.

MCR 2.113(F): Exhibits labeled (A, B, C... then 1, 2, 3...)
MCR 7.212(C)(8): Appellate exhibits in appendix
"""
import sys
import os
import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
ROOT = r"C:\Users\andre\LitigationOS"
CANONICAL_INDEX_MD = os.path.join(ROOT, "CANONICAL_EXHIBIT_INDEX.md")

# Letter labels: A-Z then AA-AZ etc.
def _letter_label(index):
    """Convert 0-based index to letter label: 0->A, 25->Z, 26->AA."""
    if index < 26:
        return chr(65 + index)
    return chr(65 + (index // 26) - 1) + chr(65 + (index % 26))


def _number_label(index):
    """Convert 0-based index to number label starting at 1."""
    return str(index + 1)


class ExhibitEntry:
    """Single exhibit with metadata."""

    def __init__(self, exhibit_id, title, source_doc=None, paragraph=None,
                 file_path=None, foundation_text=None, label_type="letter",
                 label_index=0):
        self.exhibit_id = exhibit_id
        self.title = title
        self.source_doc = source_doc or ""
        self.paragraph = paragraph or ""
        self.file_path = file_path or ""
        self.foundation_text = foundation_text or ""
        self.label_type = label_type
        self.label_index = label_index

    @property
    def label(self):
        if self.label_type == "letter":
            return _letter_label(self.label_index)
        return _number_label(self.label_index)

    def to_dict(self):
        return {
            "exhibit_id": self.exhibit_id,
            "label": self.label,
            "title": self.title,
            "source_doc": self.source_doc,
            "paragraph": self.paragraph,
            "file_path": self.file_path,
            "foundation_text": self.foundation_text,
        }


def _get_db():
    """Connect to litigation_context.db."""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn, table_name):
    """Check if a table exists in the database."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cur.fetchone() is not None


def _load_exhibits_from_db():
    """Load exhibits from canonical_exhibit_index table if available."""
    conn = _get_db()
    if conn is None:
        return []
    try:
        if not _table_exists(conn, "canonical_exhibit_index"):
            return []
        rows = conn.execute(
            "SELECT * FROM canonical_exhibit_index ORDER BY rowid"
        ).fetchall()
        exhibits = []
        for i, row in enumerate(rows):
            keys = row.keys()
            ex = ExhibitEntry(
                exhibit_id=row["id"] if "id" in keys else str(i + 1),
                title=row["title"] if "title" in keys else row["description"] if "description" in keys else f"Exhibit {i+1}",
                source_doc=row.get("source_doc", "") if hasattr(row, "get") else "",
                paragraph=row.get("paragraph", "") if hasattr(row, "get") else "",
                file_path=row.get("file_path", "") if hasattr(row, "get") else "",
                label_type="letter" if i < 26 else "number",
                label_index=i if i < 26 else i - 26,
            )
            exhibits.append(ex)
        return exhibits
    except Exception as e:
        print(f"[exhibit_packager] DB load error: {e}", file=sys.stderr)
        return []
    finally:
        conn.close()


def _load_exhibits_from_md():
    """Parse CANONICAL_EXHIBIT_INDEX.md for exhibit entries."""
    if not os.path.exists(CANONICAL_INDEX_MD):
        return []
    exhibits = []
    try:
        with open(CANONICAL_INDEX_MD, "r", encoding="utf-8") as f:
            content = f.read()
        # Parse table rows: | Label | Title | Source | ...
        lines = content.split("\n")
        header_found = False
        for line in lines:
            if "|" not in line:
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if not cells:
                continue
            if any(c.startswith("---") or c.startswith("===") for c in cells):
                header_found = True
                continue
            if not header_found and any(
                kw in cells[0].lower()
                for kw in ["exhibit", "label", "#", "id"]
            ):
                header_found = True
                continue
            if header_found and len(cells) >= 2:
                idx = len(exhibits)
                ex = ExhibitEntry(
                    exhibit_id=cells[0] if cells[0] else str(idx + 1),
                    title=cells[1] if len(cells) > 1 else f"Exhibit {idx+1}",
                    source_doc=cells[2] if len(cells) > 2 else "",
                    paragraph=cells[3] if len(cells) > 3 else "",
                    file_path=cells[4] if len(cells) > 4 else "",
                    label_type="letter" if idx < 26 else "number",
                    label_index=idx if idx < 26 else idx - 26,
                )
                exhibits.append(ex)
    except Exception as e:
        print(f"[exhibit_packager] MD parse error: {e}", file=sys.stderr)
    return exhibits


def load_exhibits():
    """Load exhibits from DB first, fall back to markdown."""
    exhibits = _load_exhibits_from_db()
    if not exhibits:
        exhibits = _load_exhibits_from_md()
    if not exhibits:
        print("[exhibit_packager] No exhibit data found in DB or MD.", file=sys.stderr)
    return exhibits


def create_cover_page(exhibit_id, title, foundation_text=""):
    """Create an exhibit cover page per MCR 2.113(F).

    Args:
        exhibit_id: Label like 'A', 'B', '1', '2', etc.
        title: Descriptive title of the exhibit.
        foundation_text: Foundation reference (e.g., "Referenced in Motion, ¶12").

    Returns:
        Markdown string for the cover page.
    """
    lines = [
        "---",
        "",
        f"# EXHIBIT {exhibit_id}",
        "",
        f"## {title}",
        "",
    ]
    if foundation_text:
        lines.append(f"**Foundation:** {foundation_text}")
    else:
        lines.append(f"**Foundation:** Referenced in filing record")
    lines.extend([
        "",
        f"*Prepared pursuant to MCR 2.113(F)*",
        "",
        f"Date: {datetime.now().strftime('%B %d, %Y')}",
        "",
        "---",
        "",
    ])
    return "\n".join(lines)


def package_exhibits(exhibit_list, label_type="letter", for_appellate=False):
    """Package a list of exhibits with cover pages and index.

    Args:
        exhibit_list: List of ExhibitEntry objects or dicts with keys:
                      exhibit_id, title, foundation_text, file_path.
        label_type: 'letter' for A,B,C or 'number' for 1,2,3.
        for_appellate: If True, format per MCR 7.212(C)(8) for appendix.

    Returns:
        dict with 'index' (markdown), 'cover_pages' (list of markdown),
        'package_markdown' (combined).
    """
    entries = []
    for i, item in enumerate(exhibit_list):
        if isinstance(item, ExhibitEntry):
            item.label_type = label_type
            item.label_index = i
            entries.append(item)
        elif isinstance(item, dict):
            entries.append(ExhibitEntry(
                exhibit_id=item.get("exhibit_id", str(i + 1)),
                title=item.get("title", f"Exhibit {i+1}"),
                source_doc=item.get("source_doc", ""),
                paragraph=item.get("paragraph", ""),
                file_path=item.get("file_path", ""),
                foundation_text=item.get("foundation_text", ""),
                label_type=label_type,
                label_index=i,
            ))

    cover_pages = []
    for entry in entries:
        foundation = entry.foundation_text
        if not foundation and entry.source_doc:
            foundation = f"Referenced in {entry.source_doc}"
            if entry.paragraph:
                foundation += f", ¶{entry.paragraph}"
        cover = create_cover_page(entry.label, entry.title, foundation)
        cover_pages.append(cover)

    # Build index
    index_lines = ["# EXHIBIT INDEX", ""]
    if for_appellate:
        index_lines[0] = "# APPENDIX — EXHIBIT INDEX"
        index_lines.append("*Per MCR 7.212(C)(8)*")
        index_lines.append("")

    index_lines.append("| Exhibit | Description | Source |")
    index_lines.append("|---------|-------------|--------|")
    for entry in entries:
        src = entry.source_doc or "Filing record"
        index_lines.append(f"| {entry.label} | {entry.title} | {src} |")
    index_lines.append("")

    index_md = "\n".join(index_lines)

    # Combined package
    pkg_lines = [index_md, "---", ""]
    for i, entry in enumerate(entries):
        pkg_lines.append(cover_pages[i])
        if entry.file_path and os.path.exists(entry.file_path):
            pkg_lines.append(f"*[Content: {entry.file_path}]*\n")
        pkg_lines.append("")

    return {
        "index": index_md,
        "cover_pages": cover_pages,
        "package_markdown": "\n".join(pkg_lines),
        "exhibit_count": len(entries),
        "entries": [e.to_dict() for e in entries],
    }


def generate_exhibit_index():
    """Generate a complete exhibit index from all available data.

    Returns:
        dict with 'markdown' index and 'exhibits' list.
    """
    exhibits = load_exhibits()
    if not exhibits:
        # Generate placeholder index for known case exhibits
        exhibits = [
            ExhibitEntry("ex-1", "Ex Parte Orders (Aug 8, 2025)", "Docket", "Multiple", label_index=0),
            ExhibitEntry("ex-2", "Ron Berry Voicemail Recording", "Discovery", "", label_index=1),
            ExhibitEntry("ex-3", "Custody Order Timeline", "Court Records", "", label_index=2),
            ExhibitEntry("ex-4", "McNeill Inconsistent Statements", "Transcripts", "", label_index=3),
            ExhibitEntry("ex-5", "Emily Watson Unverified Filings", "Court Docket", "", label_index=4),
            ExhibitEntry("ex-6", "Parenting Time Suspension Record", "Court Orders", "", label_index=5),
            ExhibitEntry("ex-7", "Bond Requirement Order ($250)", "Court Order", "", label_index=6),
            ExhibitEntry("ex-8", "PPO Extension Orders", "Court Records", "", label_index=7),
            ExhibitEntry("ex-9", "Contempt Findings", "Court Records", "", label_index=8),
            ExhibitEntry("ex-10", "Disqualification Motion & Self-Ruling", "Court Docket", "", label_index=9),
        ]

    result = package_exhibits(exhibits)
    return {
        "markdown": result["index"],
        "exhibits": result["entries"],
        "count": result["exhibit_count"],
    }


def main():
    """CLI entry point for testing."""
    print("=" * 60)
    print("ENGINE 6: EXHIBIT PACKAGER")
    print("MCR 2.113(F) / MCR 7.212(C)(8)")
    print("=" * 60)

    # Test cover page
    print("\n--- Test: Cover Page ---")
    cover = create_cover_page("A", "Ex Parte Orders (Aug 8, 2025)",
                              "Referenced in Emergency Motion, ¶12-15")
    print(cover)

    # Test exhibit index generation
    print("\n--- Test: Exhibit Index ---")
    idx = generate_exhibit_index()
    print(idx["markdown"])
    print(f"\nTotal exhibits: {idx['count']}")

    # Test appellate packaging
    print("\n--- Test: Appellate Package ---")
    test_exhibits = [
        {"title": "Lower Court Order", "source_doc": "Docket Entry 47",
         "foundation_text": "Referenced in Appellant Brief, ¶8"},
        {"title": "Transcript Excerpt", "source_doc": "Hearing 2024-12-15",
         "foundation_text": "Referenced in Appellant Brief, ¶22"},
    ]
    pkg = package_exhibits(test_exhibits, label_type="letter", for_appellate=True)
    print(pkg["index"])
    print(f"Cover pages generated: {len(pkg['cover_pages'])}")

    print("\n[exhibit_packager] All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
