"""
Exhibit Index / Table Generator
================================

Generates formatted exhibit indexes for court filings with sequential
labels (Exhibit A, B, C … Z, AA, AB …), titles, Bates ranges, and
page counts.

Usage::

    from exhibit_indexer import generate_exhibit_index

    exhibits = [
        {"title": "Email dated Jan 15, 2025", "bates_start": "SMITH-000001",
         "bates_end": "SMITH-000003", "pages": 3},
        {"title": "Lease Agreement", "bates_start": "SMITH-000004",
         "bates_end": "SMITH-000015", "pages": 12},
    ]
    index = generate_exhibit_index(exhibits)
    print(index)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _label_sequence(n: int) -> List[str]:
    """Generate *n* sequential exhibit labels: A, B, … Z, AA, AB, …"""
    labels: List[str] = []
    for i in range(n):
        if i < 26:
            labels.append(chr(65 + i))
        else:
            first = chr(65 + (i - 26) // 26)
            second = chr(65 + (i - 26) % 26)
            labels.append(f"{first}{second}")
    return labels


def generate_exhibit_index(
    exhibits: List[Dict[str, Any]],
    *,
    prefix: str = "Exhibit",
    start_label: Optional[str] = None,
    include_header: bool = True,
    header_title: str = "EXHIBIT INDEX",
) -> str:
    """Generate a formatted exhibit index table.

    Args:
        exhibits: List of exhibit dicts with keys:

            - ``title`` (str): Short description of the exhibit.
            - ``bates_start`` (str, optional): First Bates number.
            - ``bates_end`` (str, optional): Last Bates number.
            - ``pages`` (int, optional): Page count.
            - ``label`` (str, optional): Override auto-generated label.
            - ``description`` (str, optional): Longer description.

        prefix: Prefix for labels (default ``"Exhibit"``).
        start_label: Starting label letter (default ``"A"``).
        include_header: Whether to include the table header.
        header_title: Title text for the header line (default ``"EXHIBIT INDEX"``).

    Returns:
        Formatted exhibit index as a plain-text table.
    """
    if not exhibits:
        return "No exhibits to index."

    labels = _label_sequence(len(exhibits))
    if start_label:
        offset = ord(start_label.upper()) - 65
        labels = _label_sequence(len(exhibits) + offset)[offset:]

    # Calculate column widths
    label_width = max(
        len(f"{prefix} {lbl}")
        for lbl in labels[: len(exhibits)]
    )
    label_width = max(label_width, len("Label"))

    title_width = max(len(e.get("title", "")) for e in exhibits)
    title_width = max(title_width, len("Description"), 20)
    title_width = min(title_width, 60)  # cap at 60 chars

    bates_width = 25  # "SMITH-000001 – SMITH-000003"

    lines: List[str] = []

    if include_header:
        lines.append(header_title)
        lines.append("")

    # Table header
    header = (
        f"{'Label':<{label_width}}  "
        f"{'Description':<{title_width}}  "
        f"{'Bates Range':<{bates_width}}  "
        f"{'Pages':>5}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    # Rows
    total_pages = 0
    for i, exhibit in enumerate(exhibits):
        label = exhibit.get("label", f"{prefix} {labels[i]}")
        title = exhibit.get("title", "")
        if len(title) > title_width:
            title = title[: title_width - 3] + "..."
        bates_start = exhibit.get("bates_start", "")
        bates_end = exhibit.get("bates_end", "")
        pages = exhibit.get("pages", 0)
        total_pages += pages

        if bates_start and bates_end:
            bates_range = f"{bates_start} – {bates_end}"
        elif bates_start:
            bates_range = bates_start
        else:
            bates_range = ""

        row = (
            f"{label:<{label_width}}  "
            f"{title:<{title_width}}  "
            f"{bates_range:<{bates_width}}  "
            f"{pages:>5}"
        )
        lines.append(row)

    # Total
    lines.append("-" * len(header))
    total_label = f"TOTAL ({len(exhibits)} exhibits)"
    lines.append(
        f"{total_label:<{label_width + title_width + bates_width + 6}}  "
        f"{total_pages:>5}"
    )

    return "\n".join(lines)


def generate_exhibit_list_markdown(
    exhibits: List[Dict[str, Any]],
    prefix: str = "Exhibit",
) -> str:
    """Generate an exhibit index as a Markdown table.

    Args:
        exhibits: Same format as :func:`generate_exhibit_index`.
        prefix: Prefix for labels.

    Returns:
        Markdown-formatted table string.
    """
    if not exhibits:
        return "No exhibits to index."

    labels = _label_sequence(len(exhibits))
    lines = [
        "## Exhibit Index",
        "",
        "| Label | Description | Bates Range | Pages |",
        "|-------|-------------|-------------|------:|",
    ]

    total_pages = 0
    for i, exhibit in enumerate(exhibits):
        label = exhibit.get("label", f"{prefix} {labels[i]}")
        title = exhibit.get("title", "")
        bates_start = exhibit.get("bates_start", "")
        bates_end = exhibit.get("bates_end", "")
        pages = exhibit.get("pages", 0)
        total_pages += pages

        if bates_start and bates_end:
            bates_range = f"{bates_start} – {bates_end}"
        elif bates_start:
            bates_range = bates_start
        else:
            bates_range = "—"

        lines.append(f"| {label} | {title} | {bates_range} | {pages} |")

    lines.append(f"| **TOTAL** | **{len(exhibits)} exhibits** | | **{total_pages}** |")

    return "\n".join(lines)


if __name__ == "__main__":
    sample_exhibits = [
        {
            "title": "Email correspondence dated January 15, 2025",
            "bates_start": "SMITH-000001",
            "bates_end": "SMITH-000003",
            "pages": 3,
        },
        {
            "title": "Lease Agreement",
            "bates_start": "SMITH-000004",
            "bates_end": "SMITH-000015",
            "pages": 12,
        },
        {
            "title": "Inspection Report",
            "bates_start": "SMITH-000016",
            "bates_end": "SMITH-000022",
            "pages": 7,
        },
        {
            "title": "Photograph of premises",
            "bates_start": "SMITH-000023",
            "bates_end": "SMITH-000023",
            "pages": 1,
        },
        {
            "title": "Bank statement summary",
            "bates_start": "SMITH-000024",
            "bates_end": "SMITH-000030",
            "pages": 7,
        },
    ]

    print("=== PLAIN TEXT INDEX ===")
    print(generate_exhibit_index(sample_exhibits))
    print()
    print("=== MARKDOWN INDEX ===")
    print(generate_exhibit_list_markdown(sample_exhibits))
