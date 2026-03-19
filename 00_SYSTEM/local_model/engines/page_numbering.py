# -*- coding: utf-8 -*-
"""Engine 8: Page Numbering — Consistent page numbering per court rules.

MCR 7.212(B): Brief page/word limits for COA.
MSC: Varies by filing type.
Lower court: Reasonable length, no strict limit.
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

# ── Constants ───────────────────────────────────────────────────────────────
# Double-spaced, 12pt Times New Roman: ~250 words/page
WORDS_PER_PAGE = 250

# Court-specific page and word limits
PAGE_LIMITS = {
    "14th_circuit": {
        "brief": {"pages": None, "words": None, "label": "No specific limit"},
        "motion": {"pages": None, "words": None, "label": "Reasonable length"},
        "response": {"pages": None, "words": None, "label": "Reasonable length"},
    },
    "coa": {
        "brief": {"pages": 50, "words": 16000, "label": "MCR 7.212(B)"},
        "reply_brief": {"pages": 25, "words": 8000, "label": "MCR 7.212(B)"},
        "motion": {"pages": 20, "words": 5000, "label": "MCR 7.211(B)"},
        "application": {"pages": 50, "words": 16000, "label": "MCR 7.205(B)"},
    },
    "msc": {
        "application": {"pages": 50, "words": 16000, "label": "MCR 7.305(A)"},
        "brief": {"pages": 50, "words": 16000, "label": "MCR 7.312(A)"},
        "superintending": {"pages": None, "words": None, "label": "No specific limit"},
        "emergency": {"pages": None, "words": None, "label": "Concise, no limit"},
    },
    "usdc": {
        "brief": {"pages": None, "words": 13000, "label": "L.Civ.R. 7.1(d)"},
        "motion": {"pages": 25, "words": None, "label": "W.D. Mich. L.Civ.R."},
        "complaint": {"pages": None, "words": None, "label": "No specific limit"},
    },
    "jtc": {
        "complaint": {"pages": None, "words": None, "label": "No limit"},
    },
}


def count_words(text):
    """Count words in text, excluding markdown formatting markers."""
    # Strip markdown formatting
    clean = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    clean = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', clean)
    clean = re.sub(r'`[^`]+`', '', clean)
    clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
    clean = re.sub(r'^[-*+]\s+', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'^\|.+\|$', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'^[-=:| ]+$', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'^>\s*', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'---+', '', clean)
    words = clean.split()
    return len(words)


def estimate_pages(word_count, words_per_page=WORDS_PER_PAGE):
    """Estimate page count from word count.

    Args:
        word_count: Number of words.
        words_per_page: Words per page estimate (default 250 for double-spaced).

    Returns:
        Estimated page count (rounded up).
    """
    if word_count <= 0:
        return 0
    return math.ceil(word_count / words_per_page)


def count_pages(md_file):
    """Count estimated pages in a markdown file.

    Args:
        md_file: Path to markdown file.

    Returns:
        dict with word_count, estimated_pages, and file info.
    """
    if not os.path.exists(md_file):
        return {"error": f"File not found: {md_file}", "word_count": 0,
                "estimated_pages": 0}

    try:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(md_file, "r", encoding="latin-1") as f:
            content = f.read()

    wc = count_words(content)
    pages = estimate_pages(wc)
    line_count = content.count("\n") + 1
    char_count = len(content)

    return {
        "file": md_file,
        "word_count": wc,
        "estimated_pages": pages,
        "line_count": line_count,
        "char_count": char_count,
        "words_per_page": WORDS_PER_PAGE,
    }


def estimate_word_count(md_file):
    """Get word count for a markdown file.

    Args:
        md_file: Path to markdown file.

    Returns:
        Integer word count.
    """
    result = count_pages(md_file)
    return result.get("word_count", 0)


def check_page_limit(md_file, court, filing_type="brief"):
    """Check if a filing meets page/word limits for a court.

    Args:
        md_file: Path to markdown file.
        court: Court key (14th_circuit, coa, msc, usdc, jtc).
        filing_type: Type of filing (brief, motion, etc.).

    Returns:
        dict with compliance status, limits, and recommendations.
    """
    stats = count_pages(md_file)
    if "error" in stats:
        return stats

    court_key = court.lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "circuit": "14th_circuit", "14th": "14th_circuit",
        "appeals": "coa", "court_of_appeals": "coa",
        "supreme": "msc", "federal": "usdc",
        "tenure": "jtc",
    }
    court_key = aliases.get(court_key, court_key)

    court_limits = PAGE_LIMITS.get(court_key, {})
    type_limits = court_limits.get(filing_type, court_limits.get("brief", {}))

    if not type_limits:
        return {
            **stats,
            "compliant": True,
            "message": f"No limits defined for {court}/{filing_type}",
        }

    page_limit = type_limits.get("pages")
    word_limit = type_limits.get("words")
    rule_ref = type_limits.get("label", "")

    issues = []
    compliant = True

    if page_limit and stats["estimated_pages"] > page_limit:
        compliant = False
        over = stats["estimated_pages"] - page_limit
        issues.append(
            f"OVER PAGE LIMIT: {stats['estimated_pages']}/{page_limit} pages "
            f"(+{over} pages, ~{over * WORDS_PER_PAGE} words to cut)"
        )

    if word_limit and stats["word_count"] > word_limit:
        compliant = False
        over = stats["word_count"] - word_limit
        issues.append(
            f"OVER WORD LIMIT: {stats['word_count']:,}/{word_limit:,} words "
            f"(+{over:,} words to cut)"
        )

    if compliant:
        msg = "COMPLIANT"
        if page_limit:
            remaining_pages = page_limit - stats["estimated_pages"]
            msg += f" — {remaining_pages} pages remaining"
        if word_limit:
            remaining_words = word_limit - stats["word_count"]
            msg += f" ({remaining_words:,} words remaining)"
    else:
        msg = "NON-COMPLIANT: " + "; ".join(issues)

    return {
        **stats,
        "court": court_key,
        "filing_type": filing_type,
        "page_limit": page_limit,
        "word_limit": word_limit,
        "rule_reference": rule_ref,
        "compliant": compliant,
        "message": msg,
        "issues": issues,
    }


def add_page_numbers(content, start_page=1, format_str="— {page} —",
                     position="footer"):
    """Add page number markers to markdown content.

    Inserts page break markers with page numbers. Since markdown doesn't
    natively support page numbers, this adds markers that can be processed
    during DOCX/PDF conversion.

    Args:
        content: Markdown string.
        start_page: Starting page number.
        format_str: Page number format (use {page} placeholder).
        position: 'header' or 'footer'.

    Returns:
        Modified content with page markers.
    """
    lines = content.split("\n")
    word_count = 0
    current_page = start_page
    output_lines = []

    # Add first page marker
    if position == "header":
        output_lines.append(f"<!-- PAGE {current_page} -->")
        output_lines.append(f"<div class='page-number'>{format_str.format(page=current_page)}</div>")
        output_lines.append("")

    for line in lines:
        words_in_line = len(line.split())
        word_count += words_in_line

        output_lines.append(line)

        # Check for page break
        if word_count >= WORDS_PER_PAGE:
            word_count = 0
            current_page += 1
            output_lines.append("")
            output_lines.append(f"<!-- PAGE_BREAK -->")
            output_lines.append(f"<!-- PAGE {current_page} -->")
            if position == "footer":
                prev_page = current_page - 1
                output_lines.append(
                    f"<div class='page-number'>"
                    f"{format_str.format(page=prev_page)}</div>"
                )
            elif position == "header":
                output_lines.append(
                    f"<div class='page-number'>"
                    f"{format_str.format(page=current_page)}</div>"
                )
            output_lines.append("")

    # Final page footer
    if position == "footer":
        output_lines.append("")
        output_lines.append(
            f"<div class='page-number'>"
            f"{format_str.format(page=current_page)}</div>"
        )

    total_pages = current_page - start_page + 1
    output_lines.insert(0, f"<!-- TOTAL_PAGES: {total_pages} -->")

    return "\n".join(output_lines)


def check_all_filings(filings_dir=None):
    """Check page limits for all filing documents.

    Args:
        filings_dir: Directory to scan. Defaults to LitigationOS filing paths.

    Returns:
        List of check results for each filing.
    """
    root = r"C:\Users\andre\LitigationOS"
    search_dirs = [filings_dir] if filings_dir else [
        os.path.join(root, "LANE_A"),
        os.path.join(root, "LANE_F"),
        os.path.join(root, "04_MSC"),
        os.path.join(root, "03_JTC"),
        os.path.join(root, "04_COURT_FILINGS"),
    ]

    # Map directory patterns to courts
    dir_court_map = {
        "LANE_A": ("14th_circuit", "motion"),
        "LANE_F": ("coa", "brief"),
        "04_MSC": ("msc", "application"),
        "03_JTC": ("jtc", "complaint"),
        "04_COURT_FILINGS": ("14th_circuit", "motion"),
    }

    results = []
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        dirname = os.path.basename(d)
        court, ftype = dir_court_map.get(dirname, ("14th_circuit", "brief"))
        for fname in os.listdir(d):
            if fname.endswith(".md"):
                fpath = os.path.join(d, fname)
                result = check_page_limit(fpath, court, ftype)
                results.append(result)

    return results


def main():
    """CLI entry point for testing."""
    print("=" * 60)
    print("ENGINE 8: PAGE NUMBERING")
    print("MCR 7.212(B) / Court-Specific Limits")
    print("=" * 60)

    # Test word counting
    test_text = "This is a test sentence. " * 100  # 5 words × 100 = 500
    wc = count_words(test_text)
    pages = estimate_pages(wc)
    print(f"\n--- Word Count Test ---")
    print(f"Words: {wc}, Estimated pages: {pages}")
    assert wc == 500, f"Expected 500 words, got {wc}"
    assert pages == 2, f"Expected 2 pages, got {pages}"

    # Test page limit checking
    print(f"\n--- Page Limit Rules ---")
    for court, types in PAGE_LIMITS.items():
        for ftype, limits in types.items():
            label = limits.get("label", "")
            plim = limits.get("pages", "∞")
            wlim = limits.get("words", "∞")
            if wlim and wlim != "∞":
                wlim = f"{wlim:,}"
            print(f"  {court}/{ftype}: {plim} pages, {wlim} words [{label}]")

    # Test add_page_numbers
    print(f"\n--- Page Number Insertion Test ---")
    sample = "\n".join([f"Line {i}: " + "word " * 50 for i in range(20)])
    numbered = add_page_numbers(sample, start_page=1)
    page_markers = [l for l in numbered.split("\n") if "PAGE " in l]
    print(f"Page markers inserted: {len(page_markers)}")

    # Test against actual filings if they exist
    print(f"\n--- Filing Compliance Check ---")
    results = check_all_filings()
    if results:
        for r in results:
            status = "✓" if r.get("compliant") else "✗"
            fname = os.path.basename(r.get("file", "?"))
            print(f"  {status} {fname}: {r.get('word_count', 0):,} words, "
                  f"~{r.get('estimated_pages', 0)} pages — {r.get('message', '')}")
    else:
        print("  No filing files found in standard directories.")

    print("\n[page_numbering] All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
