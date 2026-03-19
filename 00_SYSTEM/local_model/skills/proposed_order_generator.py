"""
Proposed Order Generator for Michigan Court Filings.

Michigan practice requires proposed orders with many motions per MCR 2.602.
This module generates properly formatted proposed orders that adapt to
circuit court, COA, MSC, stipulated, and ex parte contexts.

Usage:
    from skills.proposed_order_generator import generate_proposed_order
    from skills.proposed_order_generator import generate_from_motion

    order = generate_proposed_order(
        court_level='circuit',
        case_key='circuit_custody',
        motion_title='Motion to Restore Parenting Time',
        relief_items=[
            'Parenting time is immediately restored per the prior schedule.',
            'Defendant shall not interfere with Plaintiff\\'s parenting time.',
        ],
    )
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from skills.caption_engine import (
    CIRCUIT,
    COA,
    JTC,
    MSC,
    USDC,
    VALID_COURT_LEVELS,
    generate_caption,
    generate_certificate_of_service,
    generate_signature_block,
    _resolve_case_data,
)


@dataclass
class ProposedOrderResult:
    """Result of proposed order generation."""
    text: str
    court_level: str
    case_key: str
    motion_title: str
    relief_count: int
    is_ex_parte: bool = False
    is_stipulated: bool = False
    closes_case: bool = False


# Judge title by court level
_JUDGE_TITLES = {
    CIRCUIT: 'Circuit Court Judge',
    COA: 'Court of Appeals Judge',
    MSC: 'Supreme Court Justice',
    USDC: 'United States District Judge',
    JTC: 'Judicial Tenure Commission',
}

# Court session location by court level
_COURT_LOCATIONS = {
    CIRCUIT: ('Muskegon', 'Muskegon'),
    COA: ('Lansing', 'Ingham'),
    MSC: ('Lansing', 'Ingham'),
    USDC: ('Grand Rapids', 'Kent'),
    JTC: ('Detroit', 'Wayne'),
}


def _build_order_header(
    court_level: str,
    case_info: Dict[str, Any],
    motion_title: str,
    order_type: str = 'GRANTING',
) -> str:
    """Build the order title line."""
    return f'ORDER {order_type} {motion_title.upper()}'


def _build_session_block(
    court_level: str,
    case_info: Dict[str, Any],
) -> str:
    """Build the 'At a session of said Court' block."""
    city, county = _COURT_LOCATIONS.get(court_level, ('Muskegon', 'Muskegon'))
    judge_title = _JUDGE_TITLES.get(court_level, 'Judge')
    judge = case_info.get('judge', f'Hon. {"_" * 20}')

    lines = [
        f'At a session of said Court held in {city}, County of {county},',
        'State of Michigan, on _____________, 2026.',
        '',
        f'PRESENT: {judge}',
        f'         {judge_title}',
    ]
    return '\n'.join(lines)


def _build_recital_block(
    moving_party: str,
    motion_title: str,
    is_ex_parte: bool = False,
    is_stipulated: bool = False,
) -> str:
    """Build the recital (preamble) paragraph."""
    if is_stipulated:
        return (
            f'    The Court having considered the parties\' Stipulation and '
            f'{motion_title}, and the Court being otherwise fully advised '
            f'in the premises,'
        )
    if is_ex_parte:
        return (
            f'    The Court having considered {moving_party}\'s Ex Parte '
            f'{motion_title}, and the Court finding that immediate and '
            f'irreparable injury, loss, or damage will result from the delay '
            f'required to effect notice, and the Court being otherwise fully '
            f'advised in the premises,'
        )
    return (
        f'    The Court having considered {moving_party}\'s {motion_title}, '
        f'and the Court being otherwise fully advised in the premises,'
    )


def _build_relief_block(
    relief_items: List[str],
    additional_provisions: Optional[List[str]] = None,
) -> str:
    """Build the IT IS HEREBY ORDERED section."""
    lines = ['    IT IS HEREBY ORDERED:', '']

    for i, item in enumerate(relief_items, 1):
        lines.append(f'    {i}. {item}')
        lines.append('')

    if additional_provisions:
        for provision in additional_provisions:
            lines.append(f'    IT IS FURTHER ORDERED that {provision}.')
            lines.append('')

    return '\n'.join(lines)


def _build_closing_block(
    court_level: str,
    case_info: Dict[str, Any],
    closes_case: bool = False,
) -> str:
    """Build the closing and signature block for the judge."""
    judge_title = _JUDGE_TITLES.get(court_level, 'Judge')
    judge = case_info.get('judge', f'Hon. {"_" * 20}')

    close_text = 'does' if closes_case else 'does not'

    lines = [
        f'    This Order {close_text} resolve all pending claims and closes the case.',
        '',
        f'Dated: {"_" * 20}     ________________________________',
        f'                              {judge}',
        f'                              {judge_title}',
    ]
    return '\n'.join(lines)


def _build_coa_order(
    case_info: Dict[str, Any],
    data: Dict[str, Any],
    motion_title: str,
    relief_items: List[str],
    additional_provisions: Optional[List[str]] = None,
    closes_case: bool = False,
) -> str:
    """Build a COA-style order (different format from circuit)."""
    lines = [
        '',
        f'ORDER {motion_title.upper()}',
        '',
        f'    The motion by {data["plaintiff_role"].split("/")[0].lower()} for '
        f'{motion_title.lower()} is GRANTED.',
        '',
    ]

    for i, item in enumerate(relief_items, 1):
        lines.append(f'    {i}. {item}')
        lines.append('')

    if additional_provisions:
        for provision in additional_provisions:
            lines.append(f'    IT IS FURTHER ORDERED that {provision}.')
            lines.append('')

    lines.extend([
        '',
        '                              ________________________________',
        '                              Presiding Judge',
    ])

    return '\n'.join(lines)


def _build_msc_order(
    case_info: Dict[str, Any],
    data: Dict[str, Any],
    motion_title: str,
    relief_items: List[str],
    additional_provisions: Optional[List[str]] = None,
    closes_case: bool = False,
) -> str:
    """Build an MSC-style order."""
    lines = [
        '',
        f'ORDER {motion_title.upper()}',
        '',
        f'    On order of the Court, the application for '
        f'{motion_title.lower()} is considered, and it is ORDERED:',
        '',
    ]

    for i, item in enumerate(relief_items, 1):
        lines.append(f'    {i}. {item}')
        lines.append('')

    if additional_provisions:
        for provision in additional_provisions:
            lines.append(f'    IT IS FURTHER ORDERED that {provision}.')
            lines.append('')

    lines.extend([
        '',
        '                              ________________________________',
        '                              Chief Justice',
    ])

    return '\n'.join(lines)


def generate_proposed_order(
    court_level: str,
    case_key: str,
    motion_title: str,
    relief_items: List[str],
    case_data: Optional[Dict[str, Any]] = None,
    order_type: str = 'GRANTING',
    moving_party: str = "Plaintiff",
    additional_provisions: Optional[List[str]] = None,
    is_ex_parte: bool = False,
    is_stipulated: bool = False,
    closes_case: bool = False,
    include_certificate_of_service: bool = False,
) -> str:
    """
    Generate a proposed order per MCR 2.602.

    Args:
        court_level: One of 'circuit', 'coa', 'msc', 'usdc', 'jtc'.
        case_key: Key into cases dict (e.g., 'circuit_custody').
        motion_title: Title of the underlying motion.
        relief_items: List of ordered relief paragraphs.
        case_data: Optional override for default case data.
        order_type: Verb for order header (default 'GRANTING').
        moving_party: Who filed the motion (default 'Plaintiff').
        additional_provisions: Extra 'IT IS FURTHER ORDERED' clauses.
        is_ex_parte: Whether this is an ex parte order.
        is_stipulated: Whether this is a stipulated order.
        closes_case: Whether this order closes the case.
        include_certificate_of_service: Append certificate of service.

    Returns:
        Formatted proposed order text.

    Raises:
        ValueError: If court_level invalid or case_key not found.
    """
    if court_level not in VALID_COURT_LEVELS:
        raise ValueError(
            f"Invalid court_level '{court_level}'. "
            f"Must be one of: {', '.join(sorted(VALID_COURT_LEVELS))}"
        )

    data = _resolve_case_data(case_data)
    cases = data.get('cases', {})

    if case_key not in cases:
        raise ValueError(
            f"Case key '{case_key}' not found. "
            f"Available keys: {', '.join(sorted(cases.keys()))}"
        )

    case_info = cases[case_key]

    # Caption
    order_title = _build_order_header(court_level, case_info, motion_title, order_type)
    caption = generate_caption(court_level, case_key, order_title, case_data)

    # Build order body based on court level
    if court_level == COA:
        body = _build_coa_order(
            case_info, data, motion_title, relief_items,
            additional_provisions, closes_case,
        )
    elif court_level == MSC:
        body = _build_msc_order(
            case_info, data, motion_title, relief_items,
            additional_provisions, closes_case,
        )
    else:
        # Standard circuit / USDC / JTC format
        session = _build_session_block(court_level, case_info)
        recital = _build_recital_block(
            moving_party, motion_title, is_ex_parte, is_stipulated,
        )
        relief = _build_relief_block(relief_items, additional_provisions)
        closing = _build_closing_block(court_level, case_info, closes_case)
        body = '\n\n'.join([session, recital, '', relief, closing])

    parts = [caption, '', body]

    if is_ex_parte:
        parts.append('')
        parts.append('NOTE: This order was entered ex parte. Opposing party')
        parts.append('shall be served forthwith and may move to modify or')
        parts.append('dissolve within 14 days per MCR 3.207(C).')

    if include_certificate_of_service:
        parts.append('')
        parts.append('')
        parts.append(generate_certificate_of_service(case_data=case_data))

    return '\n'.join(parts)


def generate_from_motion(
    motion_text: str,
    court_level: str,
    case_key: str,
    case_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Auto-extract relief requested from a motion and generate a proposed order.

    Parses the motion text for relief/prayer paragraphs and converts them
    into ordered relief items.

    Args:
        motion_text: Full text of the motion.
        court_level: One of 'circuit', 'coa', 'msc', 'usdc', 'jtc'.
        case_key: Key into cases dict.
        case_data: Optional override for default case data.

    Returns:
        Formatted proposed order text.
    """
    motion_title = _extract_motion_title(motion_text)
    relief_items = _extract_relief_items(motion_text)
    is_ex_parte = _detect_ex_parte(motion_text)

    if not relief_items:
        relief_items = ['[Relief to be specified by the Court.]']

    return generate_proposed_order(
        court_level=court_level,
        case_key=case_key,
        motion_title=motion_title,
        relief_items=relief_items,
        case_data=case_data,
        is_ex_parte=is_ex_parte,
    )


def _extract_motion_title(text: str) -> str:
    """Extract motion title from motion text."""
    # Try to find title in common patterns
    patterns = [
        r'(?:MOTION|PETITION)\s+(?:FOR|TO)\s+(.+?)(?:\n|$)',
        r'(?:EMERGENCY\s+)?MOTION\s+(.+?)(?:\n|$)',
        r'^#\s*(.+?)$',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            title = match.group(0).strip().rstrip('.')
            # Clean up markdown
            title = re.sub(r'^#+\s*', '', title)
            return title.upper()

    return 'MOTION'


def _extract_relief_items(text: str) -> List[str]:
    """Extract relief/prayer items from motion text."""
    items: List[str] = []

    # Look for a RELIEF REQUESTED or PRAYER section
    relief_section = None
    relief_patterns = [
        r'(?:RELIEF\s+REQUESTED|PRAYER\s+FOR\s+RELIEF|WHEREFORE|'
        r'REQUESTS?\s+(?:THAT|THE\s+COURT))(.*?)(?=\n\s*(?:RESPECTFULLY|'
        r'CERTIFICATE|SIGNATURE|$))',
    ]
    for pattern in relief_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            relief_section = match.group(1)
            break

    if relief_section is None:
        return items

    # Extract numbered items
    numbered = re.findall(
        r'(?:^|\n)\s*\d+[.)]\s*(.+?)(?=\n\s*\d+[.)]|\Z)',
        relief_section,
        re.DOTALL,
    )
    if numbered:
        for item in numbered:
            cleaned = ' '.join(item.split()).strip().rstrip(';.')
            if cleaned:
                items.append(cleaned + '.')

    # If no numbered items, try bullet points or semicolons
    if not items:
        bullets = re.findall(r'[-•]\s*(.+?)(?:\n|$)', relief_section)
        if bullets:
            for b in bullets:
                cleaned = b.strip().rstrip(';.')
                if cleaned:
                    items.append(cleaned + '.')

    # If still no items, treat the whole section as one item
    if not items:
        cleaned = ' '.join(relief_section.split()).strip()
        if len(cleaned) > 10:
            items.append(cleaned.rstrip('.') + '.')

    return items


def _detect_ex_parte(text: str) -> bool:
    """Detect if a motion is ex parte."""
    return bool(re.search(r'ex\s*parte', text, re.IGNORECASE))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print('=== Proposed Order Generator Demo ===\n')

    # Circuit court order
    print('--- CIRCUIT COURT ORDER ---')
    order = generate_proposed_order(
        court_level='circuit',
        case_key='circuit_custody',
        motion_title='Motion to Restore Parenting Time',
        relief_items=[
            'Plaintiff\'s parenting time is immediately restored consistent '
            'with the schedule established in the prior order.',
            'Defendant shall not interfere with Plaintiff\'s court-ordered '
            'parenting time.',
            'The Friend of the Court shall monitor compliance with this Order.',
        ],
        additional_provisions=[
            'any violation of this Order may result in a finding of contempt',
        ],
    )
    print(order)
    print()

    # Ex parte order
    print('--- EX PARTE ORDER ---')
    order = generate_proposed_order(
        court_level='circuit',
        case_key='circuit_custody',
        motion_title='Emergency Motion to Restore Parenting Time',
        relief_items=[
            'Parenting time is restored on an emergency basis pending hearing.',
        ],
        is_ex_parte=True,
    )
    print(order)
    print()

    # COA order
    print('--- COA ORDER ---')
    order = generate_proposed_order(
        court_level='coa',
        case_key='coa',
        motion_title='Peremptory Reversal',
        relief_items=[
            'The trial court\'s order of August 8, 2025 is REVERSED.',
            'The matter is REMANDED for proceedings consistent with this order.',
        ],
    )
    print(order)
