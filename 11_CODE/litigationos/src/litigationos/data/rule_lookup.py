"""Unified rule lookup across all static legal data modules.

Provides a single ``lookup_rule(citation)`` function that searches MCR, MCL,
MRE, FRCP, FRE, federal statutes, local rules, and SCAO forms — returning
full text, practice tips, and cross-references without any DB or network call.

All engines (IRAC, Discovery, Motion) can import this as a fallback when the
litigation_context.db tables are empty or unavailable.
"""

from __future__ import annotations

import re
from typing import Any

from litigationos.data.mcr_complete import MCR_RULES
from litigationos.data.mcl_complete import MCL_STATUTES
from litigationos.data.mre_complete import MRE_RULES
from litigationos.data.federal_rules import (
    FRCP_RULES,
    FRE_RULES,
    FEDERAL_STATUTES,
    WDMI_LOCAL_RULES,
)
from litigationos.data.local_rules import (
    LOCAL_RULES_14TH_CIRCUIT,
    ADMIN_ORDERS,
    JURY_INSTRUCTIONS,
    BENCH_BOOK_ENTRIES,
)
from litigationos.data.scao_forms import SCAO_FORMS

# ---------------------------------------------------------------------------
# Build a unified index (citation → entry) on first import
# ---------------------------------------------------------------------------

_INDEX: dict[str, dict[str, Any]] = {}


def _normalize(citation: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation for matching."""
    return re.sub(r"[^a-z0-9. §]+", " ", citation.lower()).strip()


def _register(entry: dict[str, Any], source: str) -> None:
    """Add *entry* to the index under its citation key."""
    key = entry.get("citation") or entry.get("form_number") or ""
    if not key:
        return
    norm = _normalize(key)
    entry_copy = dict(entry)
    entry_copy["_source"] = source
    _INDEX[norm] = entry_copy
    # Also index by title for fuzzy matches
    title = entry.get("title", "")
    if title:
        title_norm = _normalize(title)
        if title_norm not in _INDEX:
            _INDEX[title_norm] = entry_copy


def _build_index() -> None:
    """Populate the index from all static data modules."""
    if _INDEX:
        return  # already built

    for rule in MCR_RULES:
        _register(rule, "MCR")

    # MCL_STATUTES is a flat list of dicts
    for entry in MCL_STATUTES:
        _register(entry, "MCL")

    for rule in MRE_RULES:
        _register(rule, "MRE")

    for rule in FRCP_RULES:
        _register(rule, "FRCP")

    for rule in FRE_RULES:
        _register(rule, "FRE")

    for stat in FEDERAL_STATUTES:
        _register(stat, "Federal")

    for rule in WDMI_LOCAL_RULES:
        _register(rule, "WDMI")

    for rule in LOCAL_RULES_14TH_CIRCUIT:
        _register(rule, "14th Circuit")

    for order in ADMIN_ORDERS:
        _register(order, "Admin Order")

    for instr in JURY_INSTRUCTIONS:
        _register(instr, "Jury Instruction")

    for entry in BENCH_BOOK_ENTRIES:
        _register(entry, "Bench Book")

    for form in SCAO_FORMS:
        _register(form, "SCAO")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def lookup_rule(citation: str) -> dict[str, Any] | None:
    """Look up a rule/statute/form by citation string.

    Returns the full entry dict (with ``_source`` added) or *None*.

    Examples
    --------
    >>> lookup_rule("MCR 3.210")
    {'citation': 'MCR 3.210', 'title': '...', 'full_text': '...', ...}
    >>> lookup_rule("MCL 722.23")
    {'citation': 'MCL 722.23', 'title': '...', ...}
    """
    _build_index()
    norm = _normalize(citation)

    # Exact match
    if norm in _INDEX:
        return _INDEX[norm]

    # Partial / substring match
    for key, entry in _INDEX.items():
        if norm in key or key in norm:
            return entry

    return None


def search_rules(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Full-text search across all static legal data.

    Searches citation, title, and full_text fields.  Returns up to *limit*
    results ordered by relevance (exact citation match first, then title,
    then body text).

    Parameters
    ----------
    query : str
        Search terms (e.g. ``"parenting time"`` or ``"hearsay exception"``).
    limit : int
        Maximum results to return.

    Returns
    -------
    list[dict]
        Each dict is the entry with ``_source`` and ``_match_field`` keys.
    """
    _build_index()
    query_lower = query.lower()
    terms = query_lower.split()

    scored: list[tuple[int, dict[str, Any]]] = []
    seen_citations: set[str] = set()

    for _key, entry in _INDEX.items():
        citation = (entry.get("citation") or entry.get("form_number") or "").lower()
        if citation in seen_citations:
            continue

        title = entry.get("title", "").lower()
        text = entry.get("full_text", "").lower()
        tips = entry.get("practice_tips", "").lower()

        score = 0
        match_field = ""

        # Exact citation match → highest priority
        if query_lower in citation:
            score += 100
            match_field = "citation"
        # Title match
        if query_lower in title:
            score += 50
            match_field = match_field or "title"
        # Individual term matches
        for term in terms:
            if term in citation:
                score += 30
            if term in title:
                score += 20
            if term in text:
                score += 5
            if term in tips:
                score += 3

        if score > 0:
            result = dict(entry)
            result["_match_field"] = match_field or "text"
            scored.append((score, result))
            seen_citations.add(citation)

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored[:limit]]


def get_rule_text(citation: str) -> str:
    """Get just the full_text for a citation, or empty string."""
    entry = lookup_rule(citation)
    if entry is None:
        return ""
    return entry.get("full_text", "")


def get_practice_tips(citation: str) -> str:
    """Get practice tips for a citation, or empty string."""
    entry = lookup_rule(citation)
    if entry is None:
        return ""
    return entry.get("practice_tips", "")


def get_cross_references(citation: str) -> list[str]:
    """Get cross-references for a citation, or empty list."""
    entry = lookup_rule(citation)
    if entry is None:
        return []
    refs = entry.get("cross_references", [])
    if isinstance(refs, str):
        return [r.strip() for r in refs.split(",") if r.strip()]
    return refs


def get_all_sources() -> dict[str, int]:
    """Return a count of entries per source type."""
    _build_index()
    counts: dict[str, int] = {}
    seen: set[str] = set()
    for entry in _INDEX.values():
        cit = entry.get("citation") or entry.get("form_number") or ""
        if cit in seen:
            continue
        seen.add(cit)
        src = entry.get("_source", "unknown")
        counts[src] = counts.get(src, 0) + 1
    return counts


def get_rules_for_claim(rule_refs: list[str]) -> list[dict[str, Any]]:
    """Look up multiple citations and return structured results.

    Used by IRAC engine as a fallback when DB tables are empty.

    Parameters
    ----------
    rule_refs : list[str]
        E.g. ``["MCR 3.210", "MCL 722.27", "MCL 722.23"]``

    Returns
    -------
    list[dict]
        Each dict: ``rule_id``, ``title``, ``text``, ``source_table``,
        ``relevance``, ``practice_tips``.
    """
    _build_index()
    results: list[dict[str, Any]] = []
    for ref in rule_refs:
        entry = lookup_rule(ref)
        if entry:
            results.append({
                "rule_id": entry.get("citation") or entry.get("form_number", ""),
                "title": entry.get("title", ""),
                "text": entry.get("full_text", "")[:500],
                "source_table": f"static_{entry.get('_source', 'unknown')}",
                "relevance": ref,
                "practice_tips": entry.get("practice_tips", ""),
            })
    return results
