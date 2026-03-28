"""
EVENT HORIZON Δ∞ — ORACLE: The Intelligence Engine
====================================================
Multi-signal decision engine. Wraps agentic_router_v2 pattern matching
with confidence scoring, content analysis, and genetic memory recall.

4-layer decision cascade:
  1. Pattern match (filename regex from agentic_router_v2)
  2. Extension classification (monad.classify_extension)
  3. Content sampling (first 2KB text analysis)
  4. Genetic memory (learned patterns from prior runs)
"""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Optional

from .models import (
    Confidence,
    FileManifest,
    REPO_ROOT,
    ALLOWED_ROOT_FILES,
    RoutingDecision,
    RoutingPlan,
    RoutingTier,
)
from .monad import (
    classify_extension,
    is_junk,
    is_protected_dir,
    is_allowed_root_file,
    is_canonical_path,
)

log = logging.getLogger("event_horizon.oracle")

# ---------------------------------------------------------------------------
# Import pattern regexes from agentic_router_v2 (DON'T REWRITE — WRAP)
# ---------------------------------------------------------------------------
_router_dir = str(REPO_ROOT / "00_SYSTEM" / "tools")
if _router_dir not in sys.path:
    sys.path.insert(0, _router_dir)

try:
    from agentic_router_v2 import (
        JUNK_PATTERNS,
        EVIDENCE_RE, EVIDENCE_PHOTO_RE,
        COURT_RE,
        FILING_RE, DATED_FILING_RE,
        ANALYSIS_RE,
        AUTHORITY_RE,
        NPM_PACKAGE_RE, DOC_HASH_RE, PYTHON_INTERNAL_RE,
        sub_route_evidence,
        sub_route_filing,
        sub_route_analysis,
    )
    ROUTER_IMPORTED = True
except ImportError:
    log.warning("ORACLE: Could not import agentic_router_v2 — using fallback patterns")
    ROUTER_IMPORTED = False
    # Minimal fallback patterns
    JUNK_PATTERNS = re.compile(r"^\.DS_Store$|^Thumbs\.db$|^desktop\.ini$", re.I)
    EVIDENCE_RE = re.compile(r"evidence|exhibit|police|witness|testimony", re.I)
    EVIDENCE_PHOTO_RE = re.compile(r"^file-[A-Za-z0-9]{20,}", re.I)
    COURT_RE = re.compile(r"court.order|judgment|disposition|docket|transcript", re.I)
    FILING_RE = re.compile(r"motion|brief|complaint|petition|certificate", re.I)
    DATED_FILING_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_(?:COA|MSC|JTC)", re.I)
    ANALYSIS_RE = re.compile(r"analysis|report|timeline|impeach|contradiction", re.I)
    AUTHORITY_RE = re.compile(r"MCR|MCL|MRE|Benchbook|statute|court.rule", re.I)
    NPM_PACKAGE_RE = re.compile(r"^package_\d+", re.I)
    DOC_HASH_RE = re.compile(r"^doc_[0-9a-f]{8}", re.I)
    PYTHON_INTERNAL_RE = re.compile(r"^__(?:init|main)__\.", re.I)
    def sub_route_evidence(name): return "01_EVIDENCE/CUSTODY"
    def sub_route_filing(name): return "05_FILINGS/DRAFTS"
    def sub_route_analysis(name): return "04_ANALYSIS"

# ---------------------------------------------------------------------------
# Content-based routing signals
# ---------------------------------------------------------------------------
CONTENT_EVIDENCE_RE = re.compile(
    r"(?:parenting\s+time|custody|visitation|Emily\s+Watson|"
    r"PPO|protective\s+order|ex\s+parte|"
    r"L\.D\.W\.|the\s+child|"
    r"police\s+report|NSPD|incident\s+report|"
    r"allegation|false\s+report|recant)", re.I
)

CONTENT_LEGAL_RE = re.compile(
    r"(?:MCR\s+\d|MCL\s+\d|MRE\s+\d|"
    r"Michigan\s+(?:Court|Compiled|Rules)|"
    r"(?:Const|Constitution)\s+(?:1963|art)|"
    r"42\s+USC|28\s+USC|"
    r"Canon\s+\d|SCAO)", re.I
)

CONTENT_FILING_RE = re.compile(
    r"(?:COMES\s+NOW|respectfully\s+(?:requests?|moves?|submits?)|"
    r"WHEREFORE|prayer\s+for\s+relief|"
    r"Certificate\s+of\s+Service|"
    r"(?:14th|Fourteenth)\s+Circuit|"
    r"Case\s+No\.\s*\d{4}|"
    r"Pigors\s+v\.\s+Watson)", re.I
)

CONTENT_ANALYSIS_RE = re.compile(
    r"(?:analysis|findings?|conclusions?|recommendations?|"
    r"score|rating|assessment|evaluation|"
    r"impeachment|contradiction|timeline|"
    r"damages?\s+(?:calcul|estim)|"
    r"gap\s+(?:analysis|report)|convergence)", re.I
)


class Oracle:
    """🔮 ORACLE — Multi-signal decision engine.
    
    Uses a 4-layer cascade to route files with confidence scoring:
    1. Pattern match (filename regex)
    2. Extension classification
    3. Content analysis (text files only)
    4. Genetic memory (if available)
    """

    def __init__(self, root: Path = REPO_ROOT, state_db=None):
        self.root = root
        self.state_db = state_db

    def decide(self, manifests: list[FileManifest]) -> RoutingPlan:
        """Process all manifests and produce a complete routing plan."""
        plan = RoutingPlan(zone="batch")
        for m in manifests:
            decision = self._route_single(m)
            if decision:
                plan.decisions.append(decision)
            else:
                plan.skipped.append((m.path, "no route determined"))

        # Compute stats
        plan.stats = {
            "total": plan.total,
            "routable": plan.routable,
            "skipped": len(plan.skipped),
            "by_tier": {},
            "by_confidence": {},
        }
        for d in plan.decisions:
            plan.stats["by_tier"][d.tier.name] = plan.stats["by_tier"].get(d.tier.name, 0) + 1
            plan.stats["by_confidence"][d.confidence.name] = plan.stats["by_confidence"].get(d.confidence.name, 0) + 1

        log.info(f"ORACLE: Decided {plan.routable}/{plan.total} files "
                 f"(skipped {len(plan.skipped)})")
        return plan

    def _route_single(self, m: FileManifest) -> Optional[RoutingDecision]:
        """Route a single file through the 4-layer cascade."""
        signals: list[str] = []
        name = m.name
        ext = m.extension

        # Skip protected
        if m.is_protected:
            return None

        # Skip already-canonical files (unless in a bloated zone being sub-routed)
        if m.path.parent == self.root and is_allowed_root_file(name):
            return None

        # --------------- LAYER 1: Pattern matching (from agentic_router_v2) ---------------
        
        # T0: Junk
        if JUNK_PATTERNS.search(name):
            return RoutingDecision(
                source=m.path,
                destination=self.root / "11_ARCHIVES" / "JUNK" / name,
                tier=RoutingTier.T0_JUNK,
                confidence=Confidence.GREEN,
                score=0.95,
                reason="Junk file pattern match",
                signals=["pattern:junk"],
            )

        # T1: Evidence
        if EVIDENCE_RE.search(name):
            dest_folder = sub_route_evidence(name) if ROUTER_IMPORTED else "01_EVIDENCE/CUSTODY"
            signals.append("pattern:evidence_name")
            return RoutingDecision(
                source=m.path,
                destination=self.root / dest_folder / name,
                tier=RoutingTier.T1_EVIDENCE,
                confidence=Confidence.GREEN,
                score=0.92,
                reason=f"Evidence name pattern → {dest_folder}",
                signals=signals,
            )

        if EVIDENCE_PHOTO_RE.search(name) and ext in (".png", ".jpg", ".jpeg", ".webp"):
            signals.append("pattern:evidence_photo")
            return RoutingDecision(
                source=m.path,
                destination=self.root / "01_EVIDENCE" / "PHOTOS" / name,
                tier=RoutingTier.T1_EVIDENCE,
                confidence=Confidence.YELLOW,
                score=0.85,
                reason="Evidence photo pattern (ChatGPT upload / camera)",
                signals=signals,
            )

        # T2: Court records
        if COURT_RE.search(name):
            signals.append("pattern:court_record")
            return RoutingDecision(
                source=m.path,
                destination=self.root / "03_COURT" / "ORDERS" / name,
                tier=RoutingTier.T2_COURT,
                confidence=Confidence.GREEN,
                score=0.91,
                reason="Court record name pattern",
                signals=signals,
            )

        # T3: Filings
        if FILING_RE.search(name) or DATED_FILING_RE.search(name):
            dest_folder = sub_route_filing(name) if ROUTER_IMPORTED else "05_FILINGS/DRAFTS"
            signals.append("pattern:filing")
            return RoutingDecision(
                source=m.path,
                destination=self.root / dest_folder / name,
                tier=RoutingTier.T3_FILING,
                confidence=Confidence.GREEN,
                score=0.90,
                reason=f"Filing pattern → {dest_folder}",
                signals=signals,
            )

        # T4: Analysis
        if ANALYSIS_RE.search(name):
            dest_folder = sub_route_analysis(name) if ROUTER_IMPORTED else "04_ANALYSIS"
            signals.append("pattern:analysis")
            return RoutingDecision(
                source=m.path,
                destination=self.root / dest_folder / name,
                tier=RoutingTier.T4_ANALYSIS,
                confidence=Confidence.GREEN,
                score=0.90,
                reason=f"Analysis pattern → {dest_folder}",
                signals=signals,
            )

        # T5: Authority
        if AUTHORITY_RE.search(name):
            signals.append("pattern:authority")
            return RoutingDecision(
                source=m.path,
                destination=self.root / "02_AUTHORITY" / name,
                tier=RoutingTier.T5_AUTHORITY,
                confidence=Confidence.GREEN,
                score=0.90,
                reason="Authority/legal reference pattern",
                signals=signals,
            )

        # T6: Bulk artifacts
        if NPM_PACKAGE_RE.search(name) or DOC_HASH_RE.search(name) or PYTHON_INTERNAL_RE.search(name):
            signals.append("pattern:bulk_artifact")
            return RoutingDecision(
                source=m.path,
                destination=self.root / "10_EXTERNAL" / "ARTIFACTS" / name,
                tier=RoutingTier.T6_BULK,
                confidence=Confidence.GREEN,
                score=0.88,
                reason="Bulk artifact pattern",
                signals=signals,
            )

        # --------------- LAYER 2: Content analysis (text files) ---------------
        if m.content_sample and m.content_sample != "__JUNK__":
            content_decision = self._analyze_content(m, signals)
            if content_decision:
                return content_decision

        # --------------- LAYER 3: Extension-based fallback ---------------
        return self._extension_fallback(m, signals)

    def _analyze_content(self, m: FileManifest, signals: list[str]) -> Optional[RoutingDecision]:
        """Layer 2: Analyze file content for routing signals."""
        sample = m.content_sample
        score_bumps: dict[str, float] = {}

        if CONTENT_EVIDENCE_RE.search(sample):
            score_bumps["evidence"] = 0.78
            signals.append("content:evidence_terms")

        if CONTENT_FILING_RE.search(sample):
            score_bumps["filing"] = 0.80
            signals.append("content:filing_language")

        if CONTENT_LEGAL_RE.search(sample):
            score_bumps["authority"] = 0.75
            signals.append("content:legal_citations")

        if CONTENT_ANALYSIS_RE.search(sample):
            score_bumps["analysis"] = 0.72
            signals.append("content:analysis_terms")

        if not score_bumps:
            return None

        # Pick highest-scoring content signal
        best = max(score_bumps, key=score_bumps.get)
        score = score_bumps[best]

        route_map = {
            "evidence": ("01_EVIDENCE/CUSTODY", RoutingTier.T1_EVIDENCE),
            "filing": ("05_FILINGS/DRAFTS", RoutingTier.T3_FILING),
            "authority": ("02_AUTHORITY", RoutingTier.T5_AUTHORITY),
            "analysis": ("04_ANALYSIS", RoutingTier.T4_ANALYSIS),
        }

        dest_folder, tier = route_map[best]
        return RoutingDecision(
            source=m.path,
            destination=self.root / dest_folder / m.name,
            tier=tier,
            confidence=Confidence.from_score(score),
            score=score,
            reason=f"Content analysis: {best} (score={score:.2f})",
            signals=signals,
        )

    def _extension_fallback(self, m: FileManifest, signals: list[str]) -> RoutingDecision:
        """Layer 3: Extension-based fallback routing."""
        group = classify_extension(m.extension)
        signals.append(f"extension:{group}")

        ext_routes = {
            "image":    ("08_MEDIA", 0.65),
            "video":    ("08_MEDIA", 0.70),
            "audio":    ("08_MEDIA", 0.70),
            "archive":  ("11_ARCHIVES", 0.75),
            "document": ("06_DATA/DOCUMENTS", 0.60),
            "data":     ("06_DATA", 0.55),
            "code":     ("07_CODE", 0.60),
            "web":      ("09_REFERENCE", 0.55),
            "text":     ("06_DATA/TEXT", 0.50),
            "markdown": ("04_ANALYSIS", 0.50),
            "config":   ("07_CODE/CONFIG", 0.60),
        }

        if group in ext_routes:
            dest, score = ext_routes[group]
            return RoutingDecision(
                source=m.path,
                destination=self.root / dest / m.name,
                tier=RoutingTier.T7_FALLBACK,
                confidence=Confidence.from_score(score),
                score=score,
                reason=f"Extension fallback: .{m.extension} → {group} → {dest}",
                signals=signals,
            )

        # Ultimate fallback: TRIAGE queue
        return RoutingDecision(
            source=m.path,
            destination=self.root / "12_WORKSPACE" / "TRIAGE" / m.name,
            tier=RoutingTier.T7_FALLBACK,
            confidence=Confidence.RED,
            score=0.30,
            reason="No pattern/content/extension match → triage queue",
            signals=signals,
        )
