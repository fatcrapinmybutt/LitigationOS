"""
Caption Template Engine for Michigan Court Filings.

Generates court-rule-compliant caption blocks for any Michigan court filing.
Different courts require different caption formats per MCR 2.113(C)(1),
MCR 7.212(A), MCR 7.306, FRCP, and JTC rules.

Usage:
    from skills.caption_engine import generate_caption, generate_caption_docx

    # Generate a circuit court caption
    text = generate_caption('circuit', 'circuit_custody', 'MOTION FOR RECONSIDERATION')

    # Generate with custom case data
    text = generate_caption('circuit', 'circuit_custody', 'MOTION', case_data=my_data)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


DEFAULT_CASE: Dict[str, Any] = {
    'plaintiff': 'ANDREW PIGORS',
    'defendant': 'EMILY WATSON',
    'plaintiff_role': 'Plaintiff/Appellant',
    'defendant_role': 'Defendant/Appellee',
    'plaintiff_address': '[Address]',
    'plaintiff_phone': '[Phone]',
    'plaintiff_email': '[Email]',
    'pro_se': True,
    'cases': {
        'circuit_custody': {
            'number': '2024-001507-DC',
            'court': '14th Circuit Court',
            'county': 'Muskegon',
            'judge': 'Hon. Jenny L. McNeill',
        },
        'circuit_ppo': {
            'number': '2023-5907-PP',
            'court': '14th Circuit Court',
            'county': 'Muskegon',
            'judge': 'Hon. Jenny L. McNeill',
        },
        'coa': {
            'number': '366810',
            'court': 'Michigan Court of Appeals',
        },
        'msc': {
            'number': '[To Be Assigned]',
            'court': 'Michigan Supreme Court',
        },
        'usdc': {
            'number': '[To Be Assigned]',
            'court': 'United States District Court, Western District of Michigan',
        },
        'jtc': {
            'number': '[To Be Assigned]',
            'court': 'Judicial Tenure Commission',
        },
    },
}

# Court level constants
CIRCUIT = 'circuit'
COA = 'coa'
MSC = 'msc'
USDC = 'usdc'
JTC = 'jtc'

VALID_COURT_LEVELS = {CIRCUIT, COA, MSC, USDC, JTC}


@dataclass
class CaptionResult:
    """Result of caption generation."""
    text: str
    court_level: str
    case_key: str
    document_title: str
    formatting_notes: list[str] = field(default_factory=list)


def _resolve_case_data(case_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Merge provided case_data with defaults."""
    if case_data is None:
        return DEFAULT_CASE.copy()
    merged = DEFAULT_CASE.copy()
    for key, value in case_data.items():
        if key == 'cases' and isinstance(value, dict):
            merged_cases = merged.get('cases', {}).copy()
            merged_cases.update(value)
            merged['cases'] = merged_cases
        else:
            merged[key] = value
    return merged


def _pad_right(left: str, right: str, total_width: int = 70) -> str:
    """Create a line with left-aligned and right-aligned text."""
    padding = max(total_width - len(left) - len(right), 2)
    return left + ' ' * padding + right


def _build_circuit_caption(
    case_info: Dict[str, Any],
    data: Dict[str, Any],
    document_title: str,
) -> str:
    """Build caption for 14th Circuit Court per MCR 2.113(C)(1)."""
    county = case_info.get('county', 'Muskegon')
    court_name = case_info.get('court', '14th Circuit Court')
    case_number = case_info.get('number', '[Case No.]')
    judge = case_info.get('judge', 'Hon. [Judge Name]')

    # Extract ordinal from court name (e.g., "14th")
    court_ordinal = court_name.split()[0] if court_name else '14th'

    plaintiff = data['plaintiff']
    defendant = data['defendant']

    left_col_width = 38
    separator = ' ' * 2

    lines = [
        'STATE OF MICHIGAN',
        f'IN THE {court_ordinal} CIRCUIT COURT FOR THE COUNTY OF {county.upper()}',
        '',
    ]

    # Party block with right-aligned case info
    lines.append(
        f'{plaintiff + ",":<{left_col_width}}{separator}Case No. {case_number}'
    )
    lines.append(
        f'{"    Plaintiff,":<{left_col_width}}{separator}{judge}'
    )
    lines.append(
        f'{"":<{left_col_width}}{separator}'
    )
    lines.append(
        f'{"v.":<{left_col_width}}{separator}{document_title}'
    )
    lines.append('')
    lines.append(f'{defendant + ","}')
    lines.append('    Defendant.')
    lines.append('________________________________/')

    return '\n'.join(lines)


def _build_coa_caption(
    case_info: Dict[str, Any],
    data: Dict[str, Any],
    document_title: str,
) -> str:
    """Build caption for Michigan Court of Appeals per MCR 7.212(A)."""
    coa_number = case_info.get('number', '[COA No.]')

    # Look up lower court case info
    cases = data.get('cases', {})
    lower_case = cases.get('circuit_custody', {})
    lower_number = lower_case.get('number', '[Lower Court Case No.]')
    lower_court = lower_case.get('court', '14th Circuit Court')
    lower_county = lower_case.get('county', 'Muskegon')

    plaintiff = data['plaintiff']
    defendant = data['defendant']

    left_col_width = 38
    separator = ' ' * 2

    lines = [
        'STATE OF MICHIGAN',
        'IN THE COURT OF APPEALS',
        '',
    ]

    lines.append(
        f'{plaintiff + ",":<{left_col_width}}{separator}Court of Appeals No. {coa_number}'
    )
    lines.append(
        f'{"    Plaintiff-Appellant,":<{left_col_width}}{separator}'
    )
    lines.append(
        f'{"":<{left_col_width}}{separator}Lower Court Case No. {lower_number}'
    )
    lines.append(
        f'{"v.":<{left_col_width}}{separator}{lower_court}, {lower_county} County'
    )
    lines.append('')
    lines.append(f'{defendant + ","}')
    lines.append('    Defendant-Appellee.')
    lines.append('________________________________/')

    return '\n'.join(lines)


def _build_msc_caption(
    case_info: Dict[str, Any],
    data: Dict[str, Any],
    document_title: str,
) -> str:
    """Build caption for Michigan Supreme Court per MCR 7.306."""
    msc_number = case_info.get('number', '[To Be Assigned]')

    cases = data.get('cases', {})
    coa_case = cases.get('coa', {})
    coa_number = coa_case.get('number', '[COA No.]')
    lower_case = cases.get('circuit_custody', {})
    lower_number = lower_case.get('number', '[Lower Court Case No.]')

    plaintiff = data['plaintiff']
    defendant = data['defendant']

    left_col_width = 38
    separator = ' ' * 2

    lines = [
        'STATE OF MICHIGAN',
        'IN THE SUPREME COURT',
        '',
    ]

    lines.append(
        f'{plaintiff + ",":<{left_col_width}}{separator}Supreme Court No. {msc_number}'
    )
    lines.append(
        f'{"    Plaintiff-Appellant,":<{left_col_width}}{separator}'
    )
    lines.append(
        f'{"":<{left_col_width}}{separator}Court of Appeals No. {coa_number}'
    )
    lines.append(
        f'{"v.":<{left_col_width}}{separator}Lower Court Case No. {lower_number}'
    )
    lines.append('')
    lines.append(f'{defendant + ","}')
    lines.append('    Defendant-Appellee.')
    lines.append('________________________________/')

    return '\n'.join(lines)


def _build_usdc_caption(
    case_info: Dict[str, Any],
    data: Dict[str, Any],
    document_title: str,
) -> str:
    """Build caption for USDC Western District of Michigan."""
    case_number = case_info.get('number', '[To Be Assigned]')
    judge = case_info.get('judge', 'Hon. [TBD]')

    plaintiff = data['plaintiff']
    defendant = data['defendant']

    left_col_width = 38
    separator = ' ' * 2

    lines = [
        'UNITED STATES DISTRICT COURT',
        'WESTERN DISTRICT OF MICHIGAN',
        'SOUTHERN DIVISION',
        '',
    ]

    lines.append(
        f'{plaintiff + ",":<{left_col_width}}{separator}Case No. {case_number}'
    )
    lines.append(
        f'{"    Plaintiff,":<{left_col_width}}{separator}'
    )
    lines.append(
        f'{"":<{left_col_width}}{separator}{judge}'
    )
    lines.append(
        f'{"v.":<{left_col_width}}{separator}'
    )
    lines.append(
        f'{"":<{left_col_width}}{separator}JURY TRIAL DEMANDED'
    )
    lines.append(f'{defendant + ", et al.,"}')
    lines.append('    Defendants.')
    lines.append('________________________________/')

    return '\n'.join(lines)


def _build_jtc_caption(
    case_info: Dict[str, Any],
    data: Dict[str, Any],
    document_title: str,
) -> str:
    """Build caption for Judicial Tenure Commission."""
    jtc_number = case_info.get('number', '[To Be Assigned]')

    # For JTC, the subject is the judge from the underlying case
    cases = data.get('cases', {})
    circuit_case = cases.get('circuit_custody', {})
    judge_name = circuit_case.get('judge', 'Hon. [Judge Name]')
    court_name = circuit_case.get('court', '14th Circuit Court')

    left_col_width = 38
    separator = ' ' * 2

    lines = [
        'BEFORE THE JUDICIAL TENURE COMMISSION',
        'STATE OF MICHIGAN',
        '',
    ]

    lines.append(
        f'{"In the Matter of:":<{left_col_width}}{separator}JTC File No. {jtc_number}'
    )
    lines.append(f'{judge_name.upper()},')
    lines.append(f'    {court_name} Judge')
    lines.append('________________________________/')

    return '\n'.join(lines)


# Dispatch table for caption builders
_CAPTION_BUILDERS = {
    CIRCUIT: _build_circuit_caption,
    COA: _build_coa_caption,
    MSC: _build_msc_caption,
    USDC: _build_usdc_caption,
    JTC: _build_jtc_caption,
}


def generate_caption(
    court_level: str,
    case_key: str,
    document_title: str,
    case_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a court-rule-compliant caption block.

    Args:
        court_level: One of 'circuit', 'coa', 'msc', 'usdc', 'jtc'.
        case_key: Key into cases dict (e.g., 'circuit_custody', 'coa').
        document_title: Title of the document (e.g., 'MOTION FOR RECONSIDERATION').
        case_data: Optional override for default case data.

    Returns:
        Formatted caption string ready for inclusion in a filing.

    Raises:
        ValueError: If court_level is not recognized or case_key not found.
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
    builder = _CAPTION_BUILDERS[court_level]
    return builder(case_info, data, document_title)


def generate_caption_docx(
    court_level: str,
    case_key: str,
    document_title: str,
    case_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a docx-ready caption with formatting instructions.

    Returns a dict with the caption text and formatting metadata
    suitable for python-docx or similar document generation libraries.

    Args:
        court_level: One of 'circuit', 'coa', 'msc', 'usdc', 'jtc'.
        case_key: Key into cases dict.
        document_title: Title of the document.
        case_data: Optional override for default case data.

    Returns:
        Dict with keys:
            - 'text': The caption text.
            - 'formatting': Formatting instructions for docx rendering.
            - 'court_level': The court level used.
    """
    caption_text = generate_caption(court_level, case_key, document_title, case_data)

    formatting = {
        'font': 'Times New Roman',
        'font_size_pt': 12,
        'alignment': 'left',
        'line_spacing': 1.0,
        'space_after_pt': 0,
        'court_header': {
            'font_size_pt': 14,
            'bold': True,
            'alignment': 'center',
        },
        'party_names': {
            'bold': True,
            'caps': True,
        },
        'case_number': {
            'bold': True,
        },
        'document_title': {
            'bold': True,
            'underline': True,
            'caps': True,
        },
        'separator_line': {
            'text': '________________________________/',
            'bold': False,
        },
    }

    # Court-specific formatting overrides
    if court_level == USDC:
        formatting['court_header']['font_size_pt'] = 14
    elif court_level == JTC:
        formatting['court_header']['font_size_pt'] = 13

    return {
        'text': caption_text,
        'formatting': formatting,
        'court_level': court_level,
    }


def generate_signature_block(case_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a pro se signature block per MCR 2.113(E).

    Args:
        case_data: Optional override for default case data.

    Returns:
        Formatted signature block string.
    """
    data = _resolve_case_data(case_data)

    lines = [
        'Respectfully submitted,',
        '',
        '',
        '________________________________',
        f'{data["plaintiff"]}',
    ]

    if data.get('pro_se'):
        lines.append('Plaintiff, Pro Se')

    lines.extend([
        f'{data["plaintiff_address"]}',
        f'{data["plaintiff_phone"]}',
        f'{data["plaintiff_email"]}',
    ])

    lines.extend([
        '',
        f'Dated: {"_" * 20}',
    ])

    return '\n'.join(lines)


def generate_certificate_of_service(
    served_parties: Optional[list[Dict[str, str]]] = None,
    method: str = 'first-class mail',
    case_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a Certificate of Service per MCR 2.107.

    Args:
        served_parties: List of dicts with 'name' and 'address' keys.
            Defaults to defendant info from case_data.
        method: Service method (e.g., 'first-class mail', 'personal service',
            'electronic service via MiFILE').
        case_data: Optional override for default case data.

    Returns:
        Formatted certificate of service string.
    """
    data = _resolve_case_data(case_data)

    if served_parties is None:
        served_parties = [
            {
                'name': data['defendant'],
                'address': '[Defendant Address]',
            }
        ]

    lines = [
        'CERTIFICATE OF SERVICE',
        '',
        '    I hereby certify that on the _____ day of _____________, 2026,',
        f'I served a true and correct copy of the foregoing document upon',
        f'the following by {method}:',
        '',
    ]

    for party in served_parties:
        lines.append(f'    {party["name"]}')
        lines.append(f'    {party.get("address", "[Address]")}')
        lines.append('')

    lines.extend([
        '',
        '________________________________',
        f'{data["plaintiff"]}',
    ])

    if data.get('pro_se'):
        lines.append('Plaintiff, Pro Se')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import sys

    print('=== Caption Engine Demo ===\n')

    demos = [
        (CIRCUIT, 'circuit_custody', 'MOTION FOR RECONSIDERATION'),
        (COA, 'coa', 'APPELLANT BRIEF'),
        (MSC, 'msc', 'COMPLAINT FOR SUPERINTENDING CONTROL'),
        (USDC, 'usdc', 'COMPLAINT UNDER 42 USC § 1983'),
        (JTC, 'jtc', 'FORMAL COMPLAINT'),
    ]

    for court, key, title in demos:
        print(f'--- {court.upper()} ---')
        print(generate_caption(court, key, title))
        print()

    print('--- SIGNATURE BLOCK ---')
    print(generate_signature_block())
    print()

    print('--- CERTIFICATE OF SERVICE ---')
    print(generate_certificate_of_service())
