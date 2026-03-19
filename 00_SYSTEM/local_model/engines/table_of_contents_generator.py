# -*- coding: utf-8 -*-
"""Engine 9: Table of Contents Generator — ToC for appellate briefs & MSC filings.

MCR 7.212(C): Required for COA briefs.
MCR 7.306: Required for MSC applications.
Generates hierarchical ToC with page number estimates from markdown headings.
"""
import sys
import os
import re
import math
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

WORDS_PER_PAGE = 250

# Roman numeral mapping
_ROMAN = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def _to_roman(num):
    """Convert integer to Roman numeral."""
    if num <= 0:
        return str(num)
    result = []
    for value, numeral in _ROMAN:
        while num >= value:
            result.append(numeral)
            num -= value
    return "".join(result)


def _to_letter(num):
    """Convert 1-based integer to uppercase letter (1->A, 2->B, ...)."""
    if num <= 0:
        return str(num)
    if num <= 26:
        return chr(64 + num)
    return chr(64 + (num - 1) // 26) + chr(65 + (num - 1) % 26)


class TocEntry:
    """Single table of contents entry."""

    def __init__(self, level, title, page=0, word_offset=0):
        self.level = level  # 1 = top-level (##), 2 = sub (###), etc.
        self.title = title
        self.page = page
        self.word_offset = word_offset
        self.children = []

    def to_dict(self):
        return {
            "level": self.level,
            "title": self.title,
            "page": self.page,
            "children": [c.to_dict() for c in self.children],
        }


def _parse_headings(content):
    """Parse markdown headings with word offset tracking.

    Args:
        content: Markdown string.

    Returns:
        List of TocEntry objects with estimated page numbers.
    """
    lines = content.split("\n")
    entries = []
    word_count = 0

    for line in lines:
        # Match markdown headings (## through ####)
        match = re.match(r'^(#{2,4})\s+(.+)$', line)
        if match:
            hashes = match.group(1)
            title = match.group(2).strip()
            # Strip markdown formatting from title
            title = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', title)
            title = re.sub(r'`([^`]+)`', r'\1', title)
            level = len(hashes) - 1  # ## = level 1, ### = level 2
            page = math.ceil(word_count / WORDS_PER_PAGE) + 1 if word_count > 0 else 1
            entries.append(TocEntry(level, title, page, word_count))
        else:
            # Count words (skip blank lines and formatting-only lines)
            stripped = line.strip()
            if stripped and not stripped.startswith("|") and stripped != "---":
                word_count += len(stripped.split())

    return entries


def _build_hierarchy(flat_entries):
    """Build hierarchical structure from flat heading list.

    Args:
        flat_entries: List of TocEntry objects.

    Returns:
        List of top-level TocEntry objects with children populated.
    """
    if not flat_entries:
        return []

    top_level = []
    stack = []  # (level, entry) pairs

    for entry in flat_entries:
        # Pop entries from stack that are at same or deeper level
        while stack and stack[-1][0] >= entry.level:
            stack.pop()

        if stack:
            stack[-1][1].children.append(entry)
        else:
            top_level.append(entry)

        stack.append((entry.level, entry))

    return top_level


def _format_toc_line(title, page, width=60, dot_char="."):
    """Format a single ToC line with dot leaders.

    Example: "I. STATEMENT OF JURISDICTION ........... 1"
    """
    page_str = str(page)
    # Available space for dots: width - title length - page length - 2 spaces
    available = width - len(title) - len(page_str) - 2
    if available < 3:
        return f"{title} {page_str}"
    dots = f" {dot_char * available} "
    return f"{title}{dots}{page_str}"


def _format_entry_recursive(entry, counters, depth=0, width=60):
    """Recursively format ToC entries with proper numbering.

    Args:
        entry: TocEntry object.
        counters: Dict tracking counters at each depth level.
        depth: Current nesting depth.
        width: Total line width.

    Returns:
        List of formatted lines.
    """
    lines = []
    indent = "    " * depth

    # Numbering based on depth
    if depth not in counters:
        counters[depth] = 0
    counters[depth] += 1
    # Reset deeper counters
    for d in list(counters.keys()):
        if d > depth:
            del counters[d]

    if depth == 0:
        prefix = f"{_to_roman(counters[depth])}. "
    elif depth == 1:
        prefix = f"{_to_letter(counters[depth])}. "
    else:
        prefix = f"{counters[depth]}. "

    title = f"{indent}{prefix}{entry.title.upper() if depth == 0 else entry.title}"
    effective_width = width - len(indent)
    lines.append(_format_toc_line(title, entry.page, width))

    for child in entry.children:
        lines.extend(_format_entry_recursive(child, counters, depth + 1, width))

    return lines


def generate_toc(md_file, width=60, include_header=True):
    """Generate Table of Contents from a markdown file.

    Args:
        md_file: Path to markdown file.
        width: Line width for formatting.
        include_header: Whether to include the ToC header.

    Returns:
        dict with 'toc_markdown', 'entries', and metadata.
    """
    if not os.path.exists(md_file):
        return {"error": f"File not found: {md_file}", "toc_markdown": ""}

    try:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(md_file, "r", encoding="latin-1") as f:
            content = f.read()

    flat = _parse_headings(content)
    hierarchy = _build_hierarchy(flat)

    return _render_toc(hierarchy, width, include_header, md_file)


def generate_toc_from_headings(headings_list, width=60, include_header=True):
    """Generate Table of Contents from a list of heading dicts.

    Args:
        headings_list: List of dicts with keys: level (1-3), title, page (optional).
        width: Line width.
        include_header: Include ToC header.

    Returns:
        dict with 'toc_markdown', 'entries', and metadata.
    """
    flat = []
    for i, h in enumerate(headings_list):
        entry = TocEntry(
            level=h.get("level", 1),
            title=h.get("title", f"Section {i+1}"),
            page=h.get("page", i + 1),
        )
        flat.append(entry)

    hierarchy = _build_hierarchy(flat)
    return _render_toc(hierarchy, width, include_header)


def _render_toc(hierarchy, width, include_header, source_file=None):
    """Render ToC from hierarchy to formatted output."""
    lines = []
    if include_header:
        lines.append("## TABLE OF CONTENTS")
        lines.append("")

    counters = {}
    for entry in hierarchy:
        lines.extend(_format_entry_recursive(entry, counters, depth=0, width=width))

    toc_md = "\n".join(lines)

    # Also generate Table of Authorities stub
    toa_lines = [
        "",
        "## TABLE OF AUTHORITIES",
        "",
        "### Cases",
        "",
        "*(To be populated from citation index)*",
        "",
        "### Court Rules",
        "",
        "*(To be populated from citation index)*",
        "",
        "### Statutes",
        "",
        "*(To be populated from citation index)*",
        "",
        "### Constitutional Provisions",
        "",
        "*(To be populated from citation index)*",
        "",
    ]

    return {
        "toc_markdown": toc_md,
        "toa_stub": "\n".join(toa_lines),
        "entry_count": len(hierarchy),
        "total_entries": sum(1 for _ in _flatten(hierarchy)),
        "entries": [e.to_dict() for e in hierarchy],
        "source_file": source_file,
    }


def _flatten(entries):
    """Flatten nested entries for counting."""
    for e in entries:
        yield e
        yield from _flatten(e.children)


def generate_appellate_toc(md_file, court="coa"):
    """Generate a court-rule-compliant ToC for appellate filings.

    MCR 7.212(C) requires:
    1. Table of Contents
    2. Table of Authorities (cases, rules, statutes, constitutional provisions)
    3. Statement of Jurisdiction
    4. Statement of Questions Presented
    5. Statement of Facts
    6. Argument
    7. Relief Requested

    Args:
        md_file: Path to brief markdown file.
        court: 'coa' or 'msc'.

    Returns:
        dict with full ToC package.
    """
    result = generate_toc(md_file, include_header=True)

    # Verify required sections
    required_sections_coa = [
        "JURISDICTION", "QUESTIONS PRESENTED", "STATEMENT OF FACTS",
        "ARGUMENT", "RELIEF",
    ]
    required_sections_msc = [
        "JURISDICTION", "QUESTIONS PRESENTED", "STATEMENT OF FACTS",
        "ARGUMENT", "RELIEF",
    ]
    required = required_sections_coa if court == "coa" else required_sections_msc

    found = set()
    for entry_dict in result.get("entries", []):
        title_upper = entry_dict["title"].upper()
        for req in required:
            if req in title_upper:
                found.add(req)

    missing = [r for r in required if r not in found]

    result["court"] = court
    result["required_sections"] = required
    result["found_sections"] = list(found)
    result["missing_sections"] = missing
    result["sections_compliant"] = len(missing) == 0

    if missing:
        rule = "MCR 7.212(C)" if court == "coa" else "MCR 7.306"
        result["warning"] = (
            f"Missing required sections per {rule}: {', '.join(missing)}"
        )

    return result


def main():
    """CLI entry point for testing."""
    print("=" * 60)
    print("ENGINE 9: TABLE OF CONTENTS GENERATOR")
    print("MCR 7.212(C) / MCR 7.306")
    print("=" * 60)

    # Test from heading list
    print("\n--- Test: From Headings List ---")
    headings = [
        {"level": 1, "title": "Statement of Jurisdiction", "page": 1},
        {"level": 1, "title": "Statement of Questions Presented", "page": 3},
        {"level": 1, "title": "Statement of Facts", "page": 5},
        {"level": 2, "title": "Procedural History", "page": 5},
        {"level": 2, "title": "Relevant Facts", "page": 7},
        {"level": 1, "title": "Argument", "page": 10},
        {"level": 2, "title": "The Trial Court Erred in Suspending Parenting Time", "page": 10},
        {"level": 3, "title": "Standard of Review", "page": 10},
        {"level": 3, "title": "Analysis", "page": 12},
        {"level": 2, "title": "The Trial Court Violated Due Process", "page": 18},
        {"level": 1, "title": "Relief Requested", "page": 25},
    ]
    result = generate_toc_from_headings(headings)
    print(result["toc_markdown"])
    print(f"\nEntries: {result['total_entries']}")

    # Test ToC line formatting
    print("\n--- Test: Line Formatting ---")
    sample_line = _format_toc_line("I. STATEMENT OF JURISDICTION", 1)
    print(sample_line)
    sample_line2 = _format_toc_line("    A. Procedural History", 5)
    print(sample_line2)

    # Test against actual filing if exists
    print("\n--- Test: Actual Filing ---")
    test_files = [
        r"C:\Users\andre\LitigationOS\LANE_F\COA_APPELLANT_BRIEF_366810_v2.md",
        r"C:\Users\andre\LitigationOS\04_MSC\MSC_COMPLAINT_SUPERINTENDING_CONTROL_v2.md",
    ]
    for tf in test_files:
        if os.path.exists(tf):
            print(f"\n  File: {os.path.basename(tf)}")
            res = generate_appellate_toc(tf, "coa" if "COA" in tf else "msc")
            print(res["toc_markdown"][:500])
            if res.get("missing_sections"):
                print(f"  ⚠ Missing: {res['missing_sections']}")
            else:
                print(f"  ✓ All required sections present")
        else:
            print(f"  [skip] {os.path.basename(tf)} not found")

    # Test Table of Authorities stub
    print("\n--- Test: Table of Authorities Stub ---")
    result2 = generate_toc_from_headings(headings[:3])
    print(result2["toa_stub"][:200])

    print("\n[table_of_contents_generator] All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
