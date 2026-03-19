"""
SENTINEL Intelligent File Classifier
======================================
Classifies files by case lane (A-F) and document type using:
  Pass 1: Extension + path pattern matching
  Pass 2: Content signal scoring (citations, keywords, persons)
  Pass 3: MEEK lane assignment
Reuses Phase 3 classification logic in single-file mode.

Story 1.2: Intelligent File Classifier
"""
import sys
import re
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import (
    MEEK_SIGNALS, LANE_REGISTRY, LANE_PRIORITY,
    MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN,
    USC_PATTERN, CANON_PATTERN, VIOLATION_KEYWORDS, PERSON_NAMES,
    HIGH_PRIORITY_PATTERNS, LEGAL_EXTENSIONS,
    DOCUMENT_TYPES, SENTINEL_SKIP_EXTENSIONS,
)


@dataclass
class ClassificationResult:
    """Result of file classification."""
    file_path: str
    category: str = "OTHER"          # LEGAL_DOC, EVIDENCE_IMAGE, SCRIPT, etc.
    priority: str = "LOW"            # HIGH, MEDIUM, LOW, SKIP
    doc_type: str = "unknown"        # motion, order, affidavit, brief, etc.
    lane: str = ""                   # A-F
    lane_name: str = ""              # Human-readable lane name
    meek_signals: list[str] = None   # Which MEEK patterns matched
    confidence: float = 0.0          # 0.0 - 1.0
    content_score: float = 0.0       # From pass 2
    signals: dict = None             # Detailed signal counts
    error: str = ""

    def __post_init__(self):
        if self.meek_signals is None:
            self.meek_signals = []
        if self.signals is None:
            self.signals = {}


# ── Pass 1: Extension + Path Pattern ────────────────────────────────
CATEGORY_MAP = {
    ".pdf": "LEGAL_DOC", ".docx": "LEGAL_DOC", ".doc": "LEGAL_DOC", ".rtf": "LEGAL_DOC",
    ".md": "LEGAL_TEXT", ".txt": "LEGAL_TEXT",
    ".json": "STRUCTURED_DATA", ".jsonl": "STRUCTURED_DATA", ".csv": "STRUCTURED_DATA",
    ".graphml": "GRAPH_DATA", ".cypher": "GRAPH_DATA",
    ".png": "EVIDENCE_IMAGE", ".jpg": "EVIDENCE_IMAGE", ".jpeg": "EVIDENCE_IMAGE",
    ".tiff": "EVIDENCE_IMAGE", ".tif": "EVIDENCE_IMAGE", ".bmp": "EVIDENCE_IMAGE",
    ".heic": "EVIDENCE_IMAGE",
    ".zip": "ARCHIVE", ".rar": "ARCHIVE", ".7z": "ARCHIVE",
    ".py": "SCRIPT", ".ps1": "SCRIPT", ".bat": "SCRIPT", ".sh": "SCRIPT",
    ".html": "WEB_DOC", ".htm": "WEB_DOC",
    ".mp3": "AUDIO", ".wav": "AUDIO", ".m4a": "AUDIO",
    ".mp4": "VIDEO", ".avi": "VIDEO", ".mov": "VIDEO", ".mkv": "VIDEO",
    ".xlsx": "SPREADSHEET", ".xls": "SPREADSHEET",
    ".db": "DATABASE", ".sqlite": "DATABASE", ".sqlite3": "DATABASE",
}


def _classify_pass1(ext: str, file_path: str) -> tuple[str, str]:
    """Pass 1: Extension + path pattern classification."""
    if ext.lower() in SENTINEL_SKIP_EXTENSIONS:
        return "IRRELEVANT", "SKIP"

    cat = CATEGORY_MAP.get(ext.lower(), "OTHER")
    lp = file_path.lower()

    for pat in HIGH_PRIORITY_PATTERNS:
        if pat.search(lp):
            return cat, "HIGH"

    if cat in ("LEGAL_DOC", "LEGAL_TEXT", "STRUCTURED_DATA", "GRAPH_DATA"):
        return cat, "HIGH"
    elif cat in ("EVIDENCE_IMAGE", "ARCHIVE"):
        return cat, "MEDIUM"
    elif cat in ("AUDIO", "VIDEO"):
        return cat, "MEDIUM"
    elif cat == "SCRIPT":
        return cat, "LOW"
    else:
        return cat, "LOW"


# ── Pass 2: Content Signal Scoring ──────────────────────────────────
def _classify_pass2(text: str) -> tuple[float, dict]:
    """Pass 2: Content signal scoring. Returns (score, signals_dict)."""
    if not text:
        return 0.0, {}

    mcl_hits = len(MCL_PATTERN.findall(text))
    mcr_hits = len(MCR_PATTERN.findall(text))
    mre_hits = len(MRE_PATTERN.findall(text))
    case_hits = len(CASE_CITE_PATTERN.findall(text))
    usc_hits = len(USC_PATTERN.findall(text))
    canon_hits = len(CANON_PATTERN.findall(text))

    citations = mcl_hits + mcr_hits + mre_hits + case_hits + usc_hits + canon_hits

    kw_count = sum(1 for kw in VIOLATION_KEYWORDS if kw.lower() in text.lower())

    persons_found = []
    for name in PERSON_NAMES:
        if name.lower() in text.lower():
            persons_found.append(name)

    date_hits = len(re.findall(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b", text))
    dollar_hits = len(re.findall(r"\$[\d,]+\.?\d*", text))

    length_factor = min(len(text) / 5000, 3.0)
    score = (citations * 3.0 + kw_count * 1.5 + dollar_hits + date_hits) * max(length_factor, 0.1)

    signals = {
        "mcl": mcl_hits, "mcr": mcr_hits, "mre": mre_hits,
        "case_cites": case_hits, "usc": usc_hits, "canons": canon_hits,
        "keywords": kw_count, "persons": persons_found,
        "dates": date_hits, "dollars": dollar_hits,
        "total_citations": citations,
    }
    return score, signals


# ── Pass 3: MEEK Lane Assignment ────────────────────────────────────
# Priority: E → D → F → C → A → B
MEEK_PRIORITY = ["MEEK4", "MEEK3", "MEEK5", "MEEK2", "MEEK1"]
MEEK_TO_LANE = {"MEEK1": "B", "MEEK2": "A", "MEEK3": "D", "MEEK4": "E", "MEEK5": "F"}


def _classify_pass3(text: str) -> list[str]:
    """Pass 3: MEEK lane assignment. Returns list of matching MEEK signals."""
    if not text:
        return []
    lanes = []
    for meek_id in MEEK_PRIORITY:
        pattern = MEEK_SIGNALS.get(meek_id)
        if pattern and pattern.search(text):
            lanes.append(meek_id)
    return lanes


# ── Document Type Detection ─────────────────────────────────────────
def _detect_doc_type(ext: str, text: str, file_path: str) -> tuple[str, float]:
    """Detect document type from content and extension. Returns (type, confidence)."""
    text_lower = text.lower() if text else ""
    path_lower = file_path.lower()

    best_type = "unknown"
    best_score = 0.0

    for dtype, spec in DOCUMENT_TYPES.items():
        score = 0.0
        # Extension match
        if ext.lower() in spec["extensions"]:
            score += 0.3
        # Keyword matches
        kw_matches = sum(1 for kw in spec["keywords"] if kw in text_lower or kw in path_lower)
        if spec["keywords"]:
            score += min(kw_matches / len(spec["keywords"]), 1.0) * 0.7
        elif score > 0:
            # No keywords defined — extension-only types (photo, code, data)
            score += 0.5

        if score > best_score:
            best_score = score
            best_type = dtype

    return best_type, min(best_score, 1.0)


# ── Content Sampling ────────────────────────────────────────────────
def _sample_content(file_path: Path, max_bytes: int = 4096) -> str:
    """Read first N bytes of text content. Returns empty string for binary/unreadable."""
    try:
        if file_path.suffix.lower() == ".pdf":
            return _sample_pdf(file_path, max_bytes)
        # Try UTF-8, fallback to latin-1
        for encoding in ("utf-8", "latin-1"):
            try:
                with open(file_path, "r", encoding=encoding, errors="replace") as f:
                    return f.read(max_bytes)
            except UnicodeDecodeError:
                continue
    except (OSError, PermissionError):
        pass
    return ""


def _sample_pdf(file_path: Path, max_chars: int = 4096) -> str:
    """Extract text from first few pages of a PDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(file_path))
        text = ""
        for page_num in range(min(3, len(doc))):
            text += doc[page_num].get_text()
            if len(text) >= max_chars:
                break
        doc.close()
        return text[:max_chars]
    except Exception:
        return ""


# ── Main Classifier ─────────────────────────────────────────────────
def classify_file(file_path: str | Path) -> ClassificationResult:
    """
    Classify a single file through all 3 passes.
    Returns a ClassificationResult with lane, type, and confidence.
    """
    fp = Path(file_path)
    result = ClassificationResult(file_path=str(fp))

    if not fp.exists():
        result.error = "File not found"
        return result

    try:
        ext = fp.suffix
        # Pass 1: Extension + path
        result.category, result.priority = _classify_pass1(ext, str(fp))
        if result.priority == "SKIP":
            result.confidence = 1.0
            return result

        # Sample content for passes 2 and 3
        text = _sample_content(fp)

        # Pass 2: Content signal scoring
        result.content_score, result.signals = _classify_pass2(text)

        # Document type detection
        result.doc_type, type_conf = _detect_doc_type(ext, text, str(fp))

        # Pass 3: MEEK lane assignment
        meek_matches = _classify_pass3(text)
        result.meek_signals = meek_matches

        # Assign best lane (highest priority MEEK match)
        if meek_matches:
            best_meek = meek_matches[0]  # Already in priority order
            result.lane = MEEK_TO_LANE.get(best_meek, "")
            if result.lane in LANE_REGISTRY:
                result.lane_name = LANE_REGISTRY[result.lane]["name"]
        else:
            # No MEEK match — check path for lane hints
            path_lower = str(fp).lower()
            for lane_letter, info in LANE_REGISTRY.items():
                if info["name"].lower().split()[0] in path_lower:
                    result.lane = lane_letter
                    result.lane_name = info["name"]
                    break

        # Calculate overall confidence
        # Higher with more signals
        signal_conf = min(result.content_score / 20.0, 1.0) if result.content_score > 0 else 0.1
        lane_conf = 0.8 if result.lane else 0.2
        result.confidence = round((type_conf * 0.4 + signal_conf * 0.3 + lane_conf * 0.3), 3)

    except Exception as e:
        result.error = str(e)
        result.confidence = 0.0

    return result


# ── CLI Entry Point ─────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="SENTINEL File Classifier")
    parser.add_argument("file", help="File path to classify")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = classify_file(args.file)

    if args.json:
        from dataclasses import asdict
        print(json.dumps(asdict(result), indent=2))
    else:
        print(f"File:       {result.file_path}")
        print(f"Category:   {result.category}")
        print(f"Priority:   {result.priority}")
        print(f"Doc Type:   {result.doc_type}")
        print(f"Lane:       {result.lane} ({result.lane_name})")
        print(f"Confidence: {result.confidence:.1%}")
        print(f"Score:      {result.content_score:.1f}")
        if result.meek_signals:
            print(f"MEEK:       {', '.join(result.meek_signals)}")
        if result.error:
            print(f"Error:      {result.error}")
