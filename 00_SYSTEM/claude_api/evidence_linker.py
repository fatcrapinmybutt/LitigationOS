"""
Evidence-to-Claim Linker for LitigationOS.

Uses Claude to semantically link evidence atoms to claim elements with
confidence scores and structured reasoning.  Gracefully degrades when
the API is unavailable — callers always receive a ``LinkageResult``.

Claim domains: custody best-interest factors, housing code violations,
PPO violations, judicial misconduct, due process violations, appellate
errors (Michigan family law / Pigors v. Watson).

Usage::

    from claude_api.evidence_linker import link_evidence, EvidenceAtom, ClaimElement

    atoms = [EvidenceAtom(atom_id="E001", text="...", source="depo_p12", evidence_type="testimony")]
    claims = [ClaimElement(claim_id="C001", description="...", claim_type="custody")]
    result = link_evidence(atoms, claims)
    for link in result.links:
        print(f"{link.atom_id} -> {link.claim_id}  ({link.confidence:.0%})")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Sequence

from .client import is_available, create_json_message, cost_tracker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

RELEVANCE_TYPES = frozenset({"direct", "circumstantial", "impeachment", "corroborative"})
BATCH_SIZE = 10


@dataclass
class EvidenceAtom:
    """A single piece of evidence: quote, document excerpt, or exhibit."""

    atom_id: str
    text: str
    source: str
    date: str | None = None
    evidence_type: str = "document"  # testimony | document | exhibit


@dataclass
class ClaimElement:
    """A legal requirement or factor for a cause of action."""

    claim_id: str
    description: str
    legal_standard: str | None = None
    claim_type: str = "custody"  # custody | housing | ppo | misconduct | due_process | appellate


@dataclass
class EvidenceLink:
    """A scored link between one evidence atom and one claim element."""

    atom_id: str
    claim_id: str
    confidence: float  # 0.0 – 1.0
    reasoning: str
    relevance_type: str = "direct"  # direct | circumstantial | impeachment | corroborative

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        if self.relevance_type not in RELEVANCE_TYPES:
            self.relevance_type = "direct"


@dataclass
class LinkageResult:
    """Aggregated result of an evidence-to-claim linkage run."""

    links: list[EvidenceLink] = field(default_factory=list)
    unlinked_atoms: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    available: bool = True
    cost_usd: float = 0.0
    summary: str = ""


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a Michigan family law litigation analyst specialising in evidence
evaluation for Pigors v. Watson.  Your task is to link evidence atoms to
claim elements and assign a confidence score.

## Evaluation standards
- **Direct evidence** (relevance_type "direct"): proves the claim element
  without inference.  Example: a court transcript where the judge states a
  ruling on the record.
- **Circumstantial evidence** (relevance_type "circumstantial"): requires
  one logical inference step to connect to the claim.
- **Impeachment evidence** (relevance_type "impeachment"): contradicts an
  opposing party's statement, undermining credibility.
- **Corroborative evidence** (relevance_type "corroborative"): supports or
  strengthens another piece of evidence already linked to the claim.

## Confidence scoring
- 0.9-1.0 — Evidence directly and unambiguously proves the claim element.
- 0.7-0.89 — Strong connection; minor inference required.
- 0.5-0.69 — Moderate connection; relevance is arguable but reasonable.
- 0.3-0.49 — Weak connection; tangential relevance.
- 0.0-0.29 — No meaningful connection (omit these from output).

## Michigan-specific guidance
- Custody claims: evaluate against MCL 722.23 best-interest factors (a-l).
- Housing claims: reference Michigan housing code, warranty of habitability.
- PPO claims: MCL 600.2950 requirements.
- Judicial misconduct: Michigan Code of Judicial Conduct, MCR 9.104-9.205.
- Appellate: preserve error standards, MCR 7.211 requirements.

## Output format
Return a JSON array of objects.  Each object MUST have exactly these keys:
  atom_id   (str)  — ID of the evidence atom
  claim_id  (str)  — ID of the claim element
  confidence (float) — 0.0-1.0
  reasoning  (str)  — 1-2 sentence explanation of the link
  relevance_type (str) — one of "direct", "circumstantial", "impeachment", "corroborative"

Only include links with confidence >= 0.3.  If an atom has no relevant
claims, omit it entirely.  Do NOT include any text outside the JSON array.
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _atoms_to_prompt(atoms: Sequence[EvidenceAtom]) -> str:
    """Serialise atoms into a compact prompt block."""
    lines: list[str] = []
    for a in atoms:
        parts = [f"ID: {a.atom_id}", f"Type: {a.evidence_type}", f"Source: {a.source}"]
        if a.date:
            parts.append(f"Date: {a.date}")
        parts.append(f"Text: {a.text}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _claims_to_prompt(claims: Sequence[ClaimElement]) -> str:
    """Serialise claims into a compact prompt block."""
    lines: list[str] = []
    for c in claims:
        parts = [f"ID: {c.claim_id}", f"Type: {c.claim_type}", f"Description: {c.description}"]
        if c.legal_standard:
            parts.append(f"Standard: {c.legal_standard}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _parse_links(raw: list | None) -> list[EvidenceLink]:
    """Parse Claude's JSON output into EvidenceLink objects."""
    if not raw or not isinstance(raw, list):
        return []

    links: list[EvidenceLink] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            links.append(
                EvidenceLink(
                    atom_id=str(item.get("atom_id", "")),
                    claim_id=str(item.get("claim_id", "")),
                    confidence=float(item.get("confidence", 0.0)),
                    reasoning=str(item.get("reasoning", "")),
                    relevance_type=str(item.get("relevance_type", "direct")),
                )
            )
        except (ValueError, TypeError) as exc:
            logger.warning("Skipping malformed link entry: %s (%s)", item, exc)
    return links


def _link_batch(
    atoms: Sequence[EvidenceAtom],
    claims: Sequence[ClaimElement],
) -> tuple[list[EvidenceLink], float]:
    """Send one batch of atoms + all claims to Claude. Returns (links, cost)."""
    user_msg = (
        "## Evidence atoms\n"
        f"{_atoms_to_prompt(atoms)}\n\n"
        "## Claim elements\n"
        f"{_claims_to_prompt(claims)}\n\n"
        "Link each evidence atom to every relevant claim element. "
        "Return a JSON array of linkage objects."
    )

    resp = create_json_message(
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        max_tokens=4096,
    )

    parsed = resp.get("parsed")
    cost = float(resp.get("cost_usd", 0.0))
    links = _parse_links(parsed)
    return links, cost


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def link_evidence(
    atoms: list[EvidenceAtom],
    claims: list[ClaimElement],
    min_confidence: float = 0.3,
) -> LinkageResult:
    """
    Semantically link evidence atoms to claim elements via Claude.

    Atoms are batched into groups of :data:`BATCH_SIZE` (10) to stay within
    token limits.  Each batch is processed independently — a single batch
    failure does not abort the whole run.

    Parameters
    ----------
    atoms:
        Evidence atoms to evaluate.
    claims:
        Claim elements to link against.
    min_confidence:
        Discard links below this threshold (default 0.3).

    Returns
    -------
    LinkageResult
        Always returns; never raises.  Check ``result.available`` to know
        whether the API was used.
    """
    if not atoms or not claims:
        return LinkageResult(
            available=True,
            summary="No atoms or claims provided.",
        )

    if not is_available():
        return LinkageResult(
            available=False,
            unlinked_atoms=[a.atom_id for a in atoms],
            unsupported_claims=[c.claim_id for c in claims],
            summary="Claude API not available — skipping semantic linkage.",
        )

    all_links: list[EvidenceLink] = []
    total_cost = 0.0
    batch_errors = 0

    # Process atoms in batches
    for i in range(0, len(atoms), BATCH_SIZE):
        batch = atoms[i : i + BATCH_SIZE]
        try:
            links, cost = _link_batch(batch, claims)
            all_links.extend(links)
            total_cost += cost
            logger.info(
                "Batch %d-%d: %d links (cost $%.4f)",
                i, i + len(batch) - 1, len(links), cost,
            )
        except Exception as exc:
            batch_errors += 1
            logger.error(
                "Batch %d-%d failed (%s): %s — continuing with next batch",
                i, i + len(batch) - 1, type(exc).__name__, exc,
            )

    # Apply confidence filter
    filtered = [lk for lk in all_links if lk.confidence >= min_confidence]

    # Compute unlinked atoms and unsupported claims
    linked_atom_ids = {lk.atom_id for lk in filtered}
    linked_claim_ids = {lk.claim_id for lk in filtered}
    unlinked = [a.atom_id for a in atoms if a.atom_id not in linked_atom_ids]
    unsupported = [c.claim_id for c in claims if c.claim_id not in linked_claim_ids]

    # Build summary
    parts = [f"{len(filtered)} links across {len(linked_atom_ids)} atoms and {len(linked_claim_ids)} claims"]
    if unlinked:
        parts.append(f"{len(unlinked)} unlinked atoms")
    if unsupported:
        parts.append(f"{len(unsupported)} unsupported claims")
    if batch_errors:
        parts.append(f"{batch_errors} batch errors")

    return LinkageResult(
        links=filtered,
        unlinked_atoms=unlinked,
        unsupported_claims=unsupported,
        available=True,
        cost_usd=round(total_cost, 6),
        summary="; ".join(parts) + f" (${total_cost:.4f})",
    )


def link_single_atom(
    atom: EvidenceAtom,
    claims: list[ClaimElement],
    min_confidence: float = 0.3,
) -> list[EvidenceLink]:
    """
    Link a single evidence atom against all claims.

    Convenience wrapper for incremental processing.  Returns an empty list
    if the API is unavailable or on error.
    """
    if not claims:
        return []

    if not is_available():
        logger.debug("Claude API not available — skipping link for %s", atom.atom_id)
        return []

    try:
        links, _cost = _link_batch([atom], claims)
        return [lk for lk in links if lk.confidence >= min_confidence]
    except Exception as exc:
        logger.error("link_single_atom failed for %s: %s", atom.atom_id, exc)
        return []
