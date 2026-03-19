"""
Exhibit Cover Page Generator — LitigationOS
Generates Michigan-court-standard exhibit cover pages per MRE 901.
"""

import os
import re
import glob
import datetime
from pathlib import Path

# ── Default Case Info ──────────────────────────────────────────────────────────

CASE_INFO = {
    'A': {
        'caption': 'ANDREW PIGORS, Plaintiff, v. TIFFANY WATSON, Defendant',
        'number': '2024-001507-DC',
        'court': '14th Circuit Court, Muskegon County',
        'judge': 'Hon. Jenny L. McNeill',
    },
    'B': {
        'caption': 'ANDREW PIGORS, Plaintiff, v. SOUTH HAVEN PARK MHC LLC d/b/a SHADY OAKS, et al., Defendants',
        'number': '2025-002760-CZ',
        'court': 'Van Buren County Circuit Court',
        'judge': 'TBD',
    },
    'F': {
        'caption': 'ANDREW PIGORS, Appellant, v. TIFFANY WATSON, Appellee',
        'number': 'COA 366810',
        'court': 'Michigan Court of Appeals',
        'judge': 'Panel TBD',
    },
    'MSC': {
        'caption': 'ANDREW PIGORS, Plaintiff-Appellant, v. TIFFANY WATSON, Defendant-Appellee',
        'number': 'TBD',
        'court': 'Michigan Supreme Court',
        'judge': 'N/A',
    },
}

# ── MRE 901(b) Foundation Methods ─────────────────────────────────────────────

FOUNDATION_METHODS = {
    '(b)(1)':  'Testimony of witness with knowledge',
    '(b)(2)':  'Nonexpert opinion on handwriting',
    '(b)(3)':  'Comparison by trier or expert witness',
    '(b)(4)':  'Distinctive characteristics and the like',
    '(b)(5)':  'Voice identification',
    '(b)(6)':  'Telephone conversations',
    '(b)(7)':  'Public records or reports',
    '(b)(8)':  'Ancient documents or data compilation',
    '(b)(9)':  'Process or system',
    '(b)(10)': 'Methods provided by statute or rule',
}

# ── Template path ──────────────────────────────────────────────────────────────

TEMPLATE_PATH = Path(__file__).parent / 'exhibit_cover_template.md'

LINE = '━' * 46


def _parse_caption(caption: str):
    """Split a caption string into plaintiff and defendant parts."""
    parts = re.split(r',?\s+v\.\s+', caption, maxsplit=1)
    plaintiff = parts[0].strip().rstrip(',') if len(parts) > 0 else 'ANDREW PIGORS'
    defendant = parts[1].strip().rstrip(',') if len(parts) > 1 else 'TIFFANY WATSON'
    # Strip role suffixes for the template fields
    plaintiff_name = re.sub(r',?\s*(Plaintiff|Appellant|Plaintiff-Appellant).*', '', plaintiff).strip()
    defendant_name = re.sub(r',?\s*(Defendant(?:s|-Appellee)?|Appellee)$', '', defendant).strip()
    return plaintiff_name, defendant_name


def _resolve_case_info(case_info=None, lane='A'):
    """Return a case_info dict, falling back to CASE_INFO[lane] then lane A."""
    if case_info:
        return case_info
    return CASE_INFO.get(lane, CASE_INFO['A'])


def generate_cover_page(
    exhibit_label: str,
    description: str,
    foundation_method: str,
    relevance: str,
    hearsay_exception: str = None,
    case_info: dict = None,
    lane: str = 'A',
    page_count: int = 0,
    date_str: str = None,
) -> str:
    """
    Generate a single exhibit cover page in markdown.

    Args:
        exhibit_label:     e.g. "A", "B-1", "1", "14"
        description:       Plain-English description of the exhibit
        foundation_method: MRE 901(b) key, e.g. '(b)(1)' or '(b)(7)'
        relevance:         Relevance statement (MRE 401/402)
        hearsay_exception: Optional hearsay exception cite, e.g. 'MRE 803(6)'
        case_info:         Dict with caption, number, court, judge (overrides lane)
        lane:              Case lane key (A/B/F/MSC) — used if case_info is None
        page_count:        Number of pages in attached document
        date_str:          Date string; defaults to today

    Returns:
        Formatted markdown string for the cover page.
    """
    info = _resolve_case_info(case_info, lane)
    plaintiff, defendant = _parse_caption(info['caption'])
    foundation_desc = FOUNDATION_METHODS.get(foundation_method, foundation_method)
    hearsay_text = hearsay_exception if hearsay_exception else 'N/A — not hearsay / no exception required'
    date_str = date_str or datetime.date.today().strftime('%B %d, %Y')
    page_text = str(page_count) if page_count else 'See attached'

    # Determine plaintiff/defendant role labels from caption
    caption = info['caption']
    # Extract roles: look for role keywords after party names
    role_pattern = r'(Plaintiff(?:-Appellant)?|Appellant|Plaintiff)'
    p_match = re.search(role_pattern, caption)
    p_role = p_match.group(1) if p_match else 'Plaintiff'
    d_role_pattern = r'(Defendants|Defendant-Appellee|Defendant|Appellee)'
    d_match = re.search(d_role_pattern, caption)
    d_role = d_match.group(1) if d_match else 'Defendant'

    # Build cover page from template structure
    lines = [
        LINE,
        info['court'].upper(),
        f"Case No. {info['number']}",
        '',
        f"{plaintiff}, {p_role},",
        'v.',
        f"{defendant}, {d_role}.",
        '_' * 45,
        info['judge'],
        LINE,
        '',
        f"                EXHIBIT {exhibit_label}",
        '',
        f"Description:  {description}",
        f"Foundation:   MRE 901{foundation_method} — {foundation_desc}",
        f"Relevance:    {relevance}",
        f"Hearsay:      {hearsay_text}",
        f"Pages:        {page_text}",
        '',
        'Offered By:   Plaintiff Andrew Pigors (Pro Se)',
        f"Date:         {date_str}",
        '',
        LINE,
    ]
    return '\n'.join(lines)


def generate_exhibit_index(exhibits: list) -> str:
    """
    Generate a markdown table indexing all exhibits.

    Args:
        exhibits: List of dicts, each with keys:
            label, description, foundation_method, relevance,
            hearsay_exception (optional), page_count (optional)

    Returns:
        Markdown table string.
    """
    header = (
        '| # | Exhibit | Description | Foundation | Relevance | Hearsay | Pages |\n'
        '|---|---------|-------------|------------|-----------|---------|-------|\n'
    )
    rows = []
    for i, ex in enumerate(exhibits, start=1):
        label = ex.get('label', str(i))
        desc = ex.get('description', '')
        fm = ex.get('foundation_method', '')
        fm_desc = FOUNDATION_METHODS.get(fm, fm)
        rel = ex.get('relevance', '')
        hearsay = ex.get('hearsay_exception', 'N/A')
        pages = ex.get('page_count', '—')
        rows.append(
            f"| {i} | **{label}** | {desc} | MRE 901{fm} — {fm_desc} | {rel} | {hearsay} | {pages} |"
        )

    title = '## EXHIBIT INDEX\n\n'
    return title + header + '\n'.join(rows) + '\n'


def package_filing(filing_path: str, exhibits_dir: str, output_dir: str) -> str:
    """
    Read a filing, find referenced exhibits, generate cover pages, and
    create a complete filing package with a table of contents.

    Expects exhibit references in the filing like:
        Exhibit A, Exhibit B-1, Exhibit 1, etc.

    Exhibit source files should exist in exhibits_dir named like:
        Exhibit_A.pdf, Exhibit_B-1.pdf, etc.

    Args:
        filing_path:  Path to the main filing document (markdown/text).
        exhibits_dir: Directory containing raw exhibit files.
        output_dir:   Directory to write the packaged output.

    Returns:
        Path to the generated package index file.
    """
    filing_path = Path(filing_path)
    exhibits_dir = Path(exhibits_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read filing text
    filing_text = filing_path.read_text(encoding='utf-8')

    # Extract exhibit references (e.g. "Exhibit A", "Exhibit B-1", "Exhibit 14")
    pattern = r'Exhibit\s+([A-Z0-9](?:[A-Z0-9-]*))'
    found = re.findall(pattern, filing_text, re.IGNORECASE)
    # Deduplicate preserving order
    seen = set()
    labels = []
    for label in found:
        upper = label.upper()
        if upper not in seen:
            seen.add(upper)
            labels.append(upper)

    if not labels:
        print('[WARN] No exhibit references found in filing.')
        return str(output_dir)

    print(f"[INFO] Found {len(labels)} exhibit reference(s): {', '.join(labels)}")

    exhibits_meta = []
    cover_pages = []

    for label in labels:
        # Try to find matching file
        file_pattern = f"Exhibit_{label}.*"
        matches = list(exhibits_dir.glob(file_pattern))
        page_count = 0
        if matches:
            # Rough page estimate: 3000 chars per page for text files
            try:
                size = matches[0].stat().st_size
                page_count = max(1, size // 3000)
            except OSError:
                page_count = 0

        meta = {
            'label': label,
            'description': f'[Exhibit {label} — description pending]',
            'foundation_method': '(b)(1)',
            'relevance': '[Relevance statement pending]',
            'hearsay_exception': 'N/A',
            'page_count': page_count if page_count else '—',
        }
        exhibits_meta.append(meta)

        cover = generate_cover_page(
            exhibit_label=label,
            description=meta['description'],
            foundation_method=meta['foundation_method'],
            relevance=meta['relevance'],
            hearsay_exception=meta['hearsay_exception'],
            page_count=page_count,
        )
        cover_pages.append((label, cover))

        # Write individual cover page
        cover_file = output_dir / f"Cover_Exhibit_{label}.md"
        cover_file.write_text(cover, encoding='utf-8')

    # Generate exhibit index
    index_md = generate_exhibit_index(exhibits_meta)

    # Build package TOC
    toc_lines = [
        '# FILING PACKAGE — TABLE OF CONTENTS\n',
        f"**Filing:** {filing_path.name}",
        f"**Generated:** {datetime.date.today().strftime('%B %d, %Y')}",
        f"**Exhibits:** {len(labels)}\n",
        '---\n',
        '## Documents\n',
        f"1. **Main Filing** — {filing_path.name}",
    ]
    for i, label in enumerate(labels, start=2):
        toc_lines.append(f"{i}. **Exhibit {label}** — Cover_Exhibit_{label}.md + source file")
    toc_lines.append('')
    toc_lines.append('---\n')
    toc_lines.append(index_md)

    package_index = output_dir / 'PACKAGE_INDEX.md'
    package_index.write_text('\n'.join(toc_lines), encoding='utf-8')

    print(f"[INFO] Package written to: {output_dir}")
    print(f"[INFO] Index: {package_index}")
    return str(package_index)


# ── Self-Test ──────────────────────────────────────────────────────────────────

def _self_test():
    """Generate 5 sample exhibit covers and an exhibit index for validation."""
    print('=' * 60)
    print('EXHIBIT COVER GENERATOR — SELF-TEST')
    print('=' * 60)

    sample_exhibits = [
        {
            'label': 'A',
            'description': 'Text message thread between Plaintiff and Defendant, Jan 5–12 2024, showing denial of parenting time',
            'foundation_method': '(b)(1)',
            'relevance': 'Directly relevant to MCL 722.23(j) — willingness to facilitate parent-child relationship (MRE 401/402)',
            'hearsay_exception': 'MRE 801(d)(2) — Opposing party statement',
            'page_count': 14,
            'lane': 'A',
        },
        {
            'label': 'B',
            'description': 'Friend of the Court Recommendation dated March 15 2024',
            'foundation_method': '(b)(7)',
            'relevance': 'FOC findings on best interest factors under MCL 722.23 (MRE 401/402)',
            'hearsay_exception': 'MRE 803(8) — Public records and reports',
            'page_count': 8,
            'lane': 'A',
        },
        {
            'label': 'C',
            'description': 'Defendant\'s sworn Financial Disclosure Statement filed with the Court',
            'foundation_method': '(b)(7)',
            'relevance': 'Contradicts Defendant\'s testimony re income and assets; relevant to credibility and support (MRE 401/402)',
            'hearsay_exception': None,
            'page_count': 4,
            'lane': 'A',
        },
        {
            'label': 'D',
            'description': 'School attendance records for minor child, 2023-2024 academic year',
            'foundation_method': '(b)(9)',
            'relevance': 'Demonstrates impact of custodial environment on child welfare — MCL 722.23(a),(b),(d) (MRE 401/402)',
            'hearsay_exception': 'MRE 803(6) — Records of regularly conducted activity',
            'page_count': 3,
            'lane': 'A',
        },
        {
            'label': 'E',
            'description': 'Lease agreement for Shady Oaks mobile home park, executed June 2023',
            'foundation_method': '(b)(4)',
            'relevance': 'Establishes housing conditions and landlord obligations relevant to Lane B claims (MRE 401/402)',
            'hearsay_exception': 'N/A — not offered for truth of matter asserted',
            'page_count': 12,
            'lane': 'B',
        },
    ]

    # Generate each cover page
    for i, ex in enumerate(sample_exhibits):
        print(f"\n{'─' * 60}")
        print(f"SAMPLE {i + 1} OF 5 — Exhibit {ex['label']}")
        print('─' * 60)
        cover = generate_cover_page(
            exhibit_label=ex['label'],
            description=ex['description'],
            foundation_method=ex['foundation_method'],
            relevance=ex['relevance'],
            hearsay_exception=ex.get('hearsay_exception'),
            lane=ex.get('lane', 'A'),
            page_count=ex.get('page_count', 0),
        )
        print(cover)

    # Generate exhibit index
    print(f"\n{'─' * 60}")
    print('EXHIBIT INDEX')
    print('─' * 60)
    index = generate_exhibit_index(sample_exhibits)
    print(index)

    # Write samples to disk for inspection
    out_dir = Path(__file__).parent / '_self_test_output'
    out_dir.mkdir(exist_ok=True)
    for ex in sample_exhibits:
        cover = generate_cover_page(
            exhibit_label=ex['label'],
            description=ex['description'],
            foundation_method=ex['foundation_method'],
            relevance=ex['relevance'],
            hearsay_exception=ex.get('hearsay_exception'),
            lane=ex.get('lane', 'A'),
            page_count=ex.get('page_count', 0),
        )
        (out_dir / f"Cover_Exhibit_{ex['label']}.md").write_text(cover, encoding='utf-8')

    (out_dir / 'EXHIBIT_INDEX.md').write_text(index, encoding='utf-8')
    print(f"\n[OK] Self-test output written to: {out_dir}")
    print(f"[OK] {len(sample_exhibits)} cover pages + 1 index generated successfully.")
    print('=' * 60)


if __name__ == '__main__':
    _self_test()
