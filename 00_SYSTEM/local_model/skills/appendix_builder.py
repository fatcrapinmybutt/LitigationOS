#!/usr/bin/env python3
"""
MBP LitigationOS -- Appellate Appendix Builder Skill
=====================================================
Build MCR 7.212(C)-compliant appendix packages for Michigan Court of
Appeals briefs.  Pulls register of actions from ``docket_events``, orders
from the DB, and assembles a paginated appendix with TOC and tab labels.

Case: Andrew Pigors v. Tiffany Watson
COA Docket: 366810
Lower Court: 14th Circuit Court, Muskegon County (Case 2024-001507-DC)

MCR 7.212(C) mandatory appendix contents (in order):
  1. Register of Actions from lower court
  2. Verdict form / jury instructions / judgment or order appealed
  3. Any opinion or findings by the trial court
  4. Any order that is the subject of the appeal
  5. Relevant portions of the transcript (or statement re separate filing)
  6. Any other document referenced in the brief necessary for review
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        if "skills" in str(Path(__file__))
        else Path(__file__).resolve().parent
    ),
)
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Case constants ───────────────────────────────────────────────────────────
CASE_IDS = {
    "custody": "2024-001507-DC",
    "ppo": "2023-5907-PP",
}
COURT_NAME = "14th Circuit Court, Muskegon County"
COA_DOCKET = "366810"


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class AppendixItem:
    """Single item within the appendix."""
    tab_label: str
    title: str
    content: str
    page_start: int = 0
    page_end: int = 0


@dataclass
class AppendixResult:
    """Complete MCR 7.212(C) appendix package."""
    toc: str = ""
    register_of_actions: str = ""
    orders: List[str] = field(default_factory=list)
    transcript_note: str = ""
    supplemental_items: List[AppendixItem] = field(default_factory=list)
    page_count: int = 0
    items: List[AppendixItem] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# ── DB helper ────────────────────────────────────────────────────────────────

def _get_db(db_path: str = DB_PATH) -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


# ── Register of Actions ─────────────────────────────────────────────────────

def generate_register_of_actions(
    db_path: str = DB_PATH,
    case_id: str = CASE_IDS["custody"],
) -> str:
    """Build a formatted Register of Actions from ``docket_events``.

    Format per MCR 7.212(C)(1):
        Date          Document/Event                              Filed By
        ----------    ----------------------------------------    ----------------
        2024-01-15    Complaint for Custody                       Plaintiff

    Args:
        db_path: Path to the litigation SQLite database.
        case_id: Case number to filter on (e.g. '2024-001507-DC').

    Returns:
        Formatted register text, or error message if DB unavailable.
    """
    conn = _get_db(db_path)
    if conn is None:
        return f"[ERROR: Cannot connect to database at {db_path}]"

    try:
        rows = conn.execute(
            """
            SELECT event_date_iso, event_type, title, summary
            FROM docket_events
            WHERE case_id = ?
            ORDER BY event_date_iso ASC, rowid ASC
            """,
            (case_id,),
        ).fetchall()
    except Exception as exc:
        conn.close()
        return f"[ERROR: Query failed — {exc}]"

    if not rows:
        conn.close()
        return (
            f"REGISTER OF ACTIONS\n"
            f"Case No. {case_id}\n"
            f"{COURT_NAME}\n\n"
            f"[No docket events found for case {case_id}]"
        )

    # Build header
    lines: List[str] = [
        "REGISTER OF ACTIONS",
        f"Case No. {case_id}",
        COURT_NAME,
        "",
        f"{'Date':<14}{'Document/Event':<44}{'Filed By'}",
        f"{'----------':<14}{'----------------------------------------':<44}{'----------------'}",
    ]

    for row in rows:
        date_str = row["event_date_iso"] or "Unknown"
        # Use title first, fall back to event_type + summary
        event_desc = row["title"] or row["event_type"] or ""
        if not event_desc and row["summary"]:
            event_desc = row["summary"]
        # Truncate long descriptions to keep formatting clean
        if len(event_desc) > 42:
            event_desc = event_desc[:39] + "..."
        # Infer filer from event_type/title heuristics
        filed_by = _infer_filer(row)
        lines.append(f"{date_str:<14}{event_desc:<44}{filed_by}")

    conn.close()
    return "\n".join(lines)


def _infer_filer(row: sqlite3.Row) -> str:
    """Best-effort inference of filing party from event metadata."""
    title = (row["title"] or "").lower()
    event_type = (row["event_type"] or "").lower()
    summary = (row["summary"] or "").lower()
    combined = f"{title} {event_type} {summary}"

    if any(w in combined for w in ("plaintiff", "father", "pigors", "appellant")):
        return "Plaintiff"
    if any(w in combined for w in ("defendant", "mother", "watson", "appellee")):
        return "Defendant"
    if any(w in combined for w in ("court", "judge", "order", "ruling", "opinion")):
        return "Court"
    if any(w in combined for w in ("foc", "friend of court", "referee")):
        return "FOC"
    return ""


# ── Appendix TOC ────────────────────────────────────────────────────────────

def generate_appendix_toc(appendix_items: List[AppendixItem]) -> str:
    """Generate a Table of Contents for the appendix.

    Args:
        appendix_items: Ordered list of AppendixItem entries.

    Returns:
        Formatted TOC text with tab labels and page references.
    """
    lines: List[str] = [
        "TABLE OF CONTENTS — APPENDIX",
        "",
        f"{'Tab':<8}{'Description':<56}{'Page'}",
        f"{'---':<8}{'---------------------------------------------':<56}{'----'}",
    ]
    for item in appendix_items:
        title_display = item.title
        if len(title_display) > 54:
            title_display = title_display[:51] + "..."
        page_ref = (
            f"{item.page_start}"
            if item.page_start == item.page_end
            else f"{item.page_start}-{item.page_end}"
        )
        lines.append(f"{item.tab_label:<8}{title_display:<56}{page_ref}")

    return "\n".join(lines)


# ── Appendix Page Formatter ─────────────────────────────────────────────────

def format_appendix_page(
    item_number: int,
    item_title: str,
    content: str,
) -> str:
    """Format a single appendix page with tab label and header.

    Args:
        item_number: Sequential item number (used for tab label, e.g. 'A-1').
        item_title: Descriptive title for this appendix item.
        content: Body text of the appendix item.

    Returns:
        Formatted page text with tab label header and separator.
    """
    tab_label = f"A-{item_number}"
    lines: List[str] = [
        f"{'=' * 70}",
        f"  APPENDIX TAB {tab_label}",
        f"  {item_title.upper()}",
        f"{'=' * 70}",
        "",
        content,
        "",
        f"[End of Appendix Tab {tab_label}]",
    ]
    return "\n".join(lines)


# ── Main builder ─────────────────────────────────────────────────────────────

def build_appendix(
    db_path: str = DB_PATH,
    case_id: str = CASE_IDS["custody"],
    orders_appealed: Optional[List[str]] = None,
    transcript_note: Optional[str] = None,
) -> AppendixResult:
    """Build a complete MCR 7.212(C) appendix package.

    Assembles all six mandatory sections in the order required by the rule:
      1. Register of Actions
      2. Judgment/order being appealed
      3. Trial court opinions/findings
      4. Orders subject of appeal
      5. Transcript note
      6. Supplemental documents

    Args:
        db_path: Path to the litigation SQLite database.
        case_id: Lower-court case number.
        orders_appealed: List of order descriptions or dates to pull from DB.
            If ``None``, attempts to pull all orders from docket_events.
        transcript_note: Statement about transcript status.  Defaults to a
            standard "filed separately" note per MCR 7.212(C)(5).

    Returns:
        AppendixResult with all sections populated and page counts.
    """
    result = AppendixResult()
    items: List[AppendixItem] = []
    current_page = 1

    # ── 1. Register of Actions (MCR 7.212(C)(1)) ────────────────────────
    register_text = generate_register_of_actions(db_path, case_id)
    result.register_of_actions = register_text
    register_page_count = max(1, register_text.count("\n") // 50 + 1)
    items.append(AppendixItem(
        tab_label="A-1",
        title="Register of Actions",
        content=register_text,
        page_start=current_page,
        page_end=current_page + register_page_count - 1,
    ))
    current_page += register_page_count

    # ── 2-4. Orders appealed (MCR 7.212(C)(2)-(4)) ──────────────────────
    order_texts = _fetch_orders(db_path, case_id, orders_appealed)
    result.orders = order_texts
    for idx, order_text in enumerate(order_texts):
        tab_num = len(items) + 1
        order_pages = max(1, order_text.count("\n") // 50 + 1)
        items.append(AppendixItem(
            tab_label=f"A-{tab_num}",
            title=f"Order/Judgment — Item {idx + 1}",
            content=order_text,
            page_start=current_page,
            page_end=current_page + order_pages - 1,
        ))
        current_page += order_pages

    if not order_texts:
        result.errors.append(
            "No orders found in database — manually add orders appealed"
        )

    # ── 5. Transcript note (MCR 7.212(C)(5)) ────────────────────────────
    if transcript_note is None:
        transcript_note = (
            "The transcript of proceedings is being filed separately "
            "as a separate volume in accordance with MCR 7.210(B)(2)."
        )
    result.transcript_note = transcript_note
    tab_num = len(items) + 1
    items.append(AppendixItem(
        tab_label=f"A-{tab_num}",
        title="Statement Regarding Transcript",
        content=transcript_note,
        page_start=current_page,
        page_end=current_page,
    ))
    current_page += 1

    # ── 6. Supplemental items placeholder (MCR 7.212(C)(6)) ─────────────
    supplemental = _fetch_supplemental_docs(db_path, case_id)
    result.supplemental_items = supplemental
    for supp in supplemental:
        tab_num = len(items) + 1
        supp.tab_label = f"A-{tab_num}"
        supp_pages = max(1, supp.content.count("\n") // 50 + 1)
        supp.page_start = current_page
        supp.page_end = current_page + supp_pages - 1
        items.append(supp)
        current_page += supp_pages

    # ── Assemble ─────────────────────────────────────────────────────────
    result.items = items
    result.page_count = current_page - 1
    result.toc = generate_appendix_toc(items)

    return result


# ── DB fetch helpers ─────────────────────────────────────────────────────────

def _fetch_orders(
    db_path: str,
    case_id: str,
    orders_appealed: Optional[List[str]],
) -> List[str]:
    """Fetch order texts from the database.

    Searches docket_events for entries matching the orders_appealed
    descriptions, or pulls all 'order' type events if none specified.
    """
    conn = _get_db(db_path)
    if conn is None:
        return []

    texts: List[str] = []
    try:
        if orders_appealed:
            for order_desc in orders_appealed:
                rows = conn.execute(
                    """
                    SELECT event_date_iso, title, summary
                    FROM docket_events
                    WHERE case_id = ?
                      AND (title LIKE ? OR summary LIKE ?)
                    ORDER BY event_date_iso ASC
                    """,
                    (case_id, f"%{order_desc}%", f"%{order_desc}%"),
                ).fetchall()
                if rows:
                    for r in rows:
                        texts.append(_format_order_entry(r))
                else:
                    texts.append(
                        f"[Order not found in database: {order_desc}]"
                    )
        else:
            # Pull all order-type events
            rows = conn.execute(
                """
                SELECT event_date_iso, title, summary
                FROM docket_events
                WHERE case_id = ?
                  AND (
                    LOWER(event_type) LIKE '%order%'
                    OR LOWER(title) LIKE '%order%'
                    OR LOWER(event_type) LIKE '%judgment%'
                    OR LOWER(title) LIKE '%judgment%'
                  )
                ORDER BY event_date_iso ASC
                """,
                (case_id,),
            ).fetchall()
            for r in rows:
                texts.append(_format_order_entry(r))
    except Exception:
        pass
    finally:
        conn.close()

    return texts


def _format_order_entry(row: sqlite3.Row) -> str:
    """Format a single order/judgment row into appendix text."""
    date_str = row["event_date_iso"] or "Date Unknown"
    title = row["title"] or "Order"
    summary = row["summary"] or ""
    lines = [
        f"Date: {date_str}",
        f"Title: {title}",
    ]
    if summary:
        lines.append(f"\n{summary}")
    return "\n".join(lines)


def _fetch_supplemental_docs(
    db_path: str,
    case_id: str,
) -> List[AppendixItem]:
    """Fetch supplemental documents referenced in the brief.

    Pulls key evidence items such as ex parte orders and critical filings
    that may need to be included per MCR 7.212(C)(6).
    """
    conn = _get_db(db_path)
    if conn is None:
        return []

    items: List[AppendixItem] = []
    try:
        # Pull critical ex parte orders as supplemental evidence
        rows = conn.execute(
            """
            SELECT event_date_iso, title, summary
            FROM docket_events
            WHERE case_id = ?
              AND (
                LOWER(title) LIKE '%ex parte%'
                OR LOWER(summary) LIKE '%ex parte%'
              )
            ORDER BY event_date_iso ASC
            LIMIT 20
            """,
            (case_id,),
        ).fetchall()

        for row in rows:
            date_str = row["event_date_iso"] or "Unknown"
            title = row["title"] or "Ex Parte Order"
            summary = row["summary"] or ""
            content = f"Date: {date_str}\nTitle: {title}"
            if summary:
                content += f"\n\n{summary}"
            items.append(AppendixItem(
                tab_label="",  # Assigned later
                title=f"Supplemental — {title} ({date_str})",
                content=content,
            ))
    except Exception:
        pass
    finally:
        conn.close()

    return items


# ── Class interface (for SkillBase / registry compatibility) ─────────────────

class AppendixBuilder:
    """MCR 7.212(C) Appendix Builder — class interface for the skill registry.

    Wraps the module-level functions for use with ``load_skill()`` and
    ``get_skill_class()``.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def build(
        self,
        case_id: str = CASE_IDS["custody"],
        orders_appealed: Optional[List[str]] = None,
        transcript_note: Optional[str] = None,
    ) -> AppendixResult:
        """Build a complete appendix.  See :func:`build_appendix`."""
        return build_appendix(self.db_path, case_id, orders_appealed, transcript_note)

    def register_of_actions(
        self,
        case_id: str = CASE_IDS["custody"],
    ) -> str:
        """Generate register of actions.  See :func:`generate_register_of_actions`."""
        return generate_register_of_actions(self.db_path, case_id)

    @staticmethod
    def toc(items: List[AppendixItem]) -> str:
        """Generate TOC.  See :func:`generate_appendix_toc`."""
        return generate_appendix_toc(items)

    @staticmethod
    def format_page(item_number: int, title: str, content: str) -> str:
        """Format a page.  See :func:`format_appendix_page`."""
        return format_appendix_page(item_number, title, content)


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build MCR 7.212(C) appendix for COA brief"
    )
    parser.add_argument(
        "--case-id",
        default=CASE_IDS["custody"],
        help="Lower-court case number",
    )
    parser.add_argument(
        "--orders",
        nargs="*",
        help="Order descriptions to include",
    )
    parser.add_argument(
        "--transcript-note",
        default=None,
        help="Transcript status statement",
    )
    args = parser.parse_args()

    result = build_appendix(
        db_path=DB_PATH,
        case_id=args.case_id,
        orders_appealed=args.orders,
        transcript_note=args.transcript_note,
    )
    print(result.toc)
    print()
    for item in result.items:
        print(format_appendix_page(
            int(item.tab_label.split("-")[1]),
            item.title,
            item.content,
        ))
        print()
    if result.errors:
        print("WARNINGS:")
        for err in result.errors:
            print(f"  - {err}")
    print(f"\nTotal appendix pages: {result.page_count}")
