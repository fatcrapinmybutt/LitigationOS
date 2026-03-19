# LitigationOS Court-Filing Engines
# MANBEARPIG v8.0 — Pigors v. Watson
"""
Engine modules for Michigan court-filing automation.
All engines connect to litigation_context.db and follow MCR formatting standards.
"""

__version__ = "1.2.0"
__engine_range__ = "1-15"
__all__ = [
    # Engines 1-5
    "service_calculator",
    "separation_day_counter",
    "court_address_book",
    "certificate_of_service_generator",
    "cross_reference_engine",
    # Engine 6: Exhibit Packager (MCR 2.113(F))
    "exhibit_packager",
    # Engine 7: Caption Generator (MCR 2.113)
    "caption_generator",
    # Engine 8: Page Numbering (MCR 7.212(B))
    "page_numbering",
    # Engine 9: Table of Contents Generator (MCR 7.212(C))
    "table_of_contents_generator",
    # Engine 10: Filing Fee Calculator
    "filing_fee_calculator",
    # Engine 11: Filing Receipt Tracker
    "filing_receipt_tracker",
    # Engine 12: Notarization Tracker
    "notarization_tracker",
    # Engine 13: Redaction Engine (MCR 1.109(D)(9))
    "redaction_engine",
    # Engine 14: Local Rule Checker (MCR 8.112(B))
    "local_rule_checker",
    # Engine 15: E-Filing Preparer (MiFile/TrueFiling/CM-ECF)
    "efiling_preparer",
]

# ── Engine 6-10 imports ─────────────────────────────────────────────────────
from .exhibit_packager import (
    create_cover_page,
    package_exhibits,
    generate_exhibit_index,
    load_exhibits,
    ExhibitEntry,
)

from .caption_generator import (
    generate_caption,
    generate_all_captions,
    get_caption_for_lane,
    COURTS,
    PARTY_LABELS,
)

from .page_numbering import (
    count_pages,
    estimate_word_count,
    check_page_limit,
    add_page_numbers,
    count_words,
    estimate_pages,
    check_all_filings,
    PAGE_LIMITS,
)

from .table_of_contents_generator import (
    generate_toc,
    generate_toc_from_headings,
    generate_appellate_toc,
    TocEntry,
)

from .filing_fee_calculator import (
    calculate_fee,
    get_fee_waiver_requirements,
    track_fees_paid,
    record_fee,
    get_total_estimated_cost,
    FEE_SCHEDULE,
)

# ── Engine 13-15 imports ─────────────────────────────────────────────────────
from .redaction_engine import (
    redact_text,
    redact_file,
    check_pii_exposure,
    generate_redaction_log,
    REDACTION_LEVELS,
)

from .local_rule_checker import (
    check_local_compliance,
    get_local_rules,
    generate_compliance_checklist,
    LOCAL_RULES,
)

from .efiling_preparer import (
    prepare_for_mifile,
    prepare_for_truefiling,
    prepare_for_ecf,
    validate_efile_requirements,
    generate_efile_checklist,
    MIFILE_FILING_CODES,
)
