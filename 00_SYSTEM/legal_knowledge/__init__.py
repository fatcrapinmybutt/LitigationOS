"""
Michigan Legal Knowledge Base
=============================
Comprehensive Michigan court rules, statutes, document formats,
filing requirements, and evidence rules for litigation document generation.

DISCLAIMER: This module is a reference aid. All rules, statutes, and formatting
requirements MUST be verified against current official sources before use in
actual court filings. Rules are subject to amendment. Last structural review
baseline: 2024.

Official sources:
- Michigan Court Rules: https://courts.michigan.gov/courts/michigansupremecourt/rules
- Michigan Compiled Laws: http://www.legislature.mi.gov
- Michigan Rules of Evidence: incorporated in Michigan Court Rules Chapter 10
"""

from .michigan_court_rules import (
    MICHIGAN_COURT_RULES,
    MICHIGAN_STATUTES,
    DOCUMENT_FORMATS,
    FILING_REQUIREMENTS,
    EVIDENCE_RULES,
    get_rule,
    get_format,
    get_filing_reqs,
    validate_document,
)

__all__ = [
    "MICHIGAN_COURT_RULES",
    "MICHIGAN_STATUTES",
    "DOCUMENT_FORMATS",
    "FILING_REQUIREMENTS",
    "EVIDENCE_RULES",
    "get_rule",
    "get_format",
    "get_filing_reqs",
    "validate_document",
]
