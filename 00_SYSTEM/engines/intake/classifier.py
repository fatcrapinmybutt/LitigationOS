"""
Document Classifier — Content-based document and lane classification.
=====================================================================

Classifies documents by:
  1. Document type (motion, order, evidence, transcript, etc.)
  2. Litigation lane (A=custody, B=housing, C=federal, D=PPO, etc.)
  3. Urgency level (critical, high, normal, low)
  4. Legal topics (best interest, parenting time, due process, etc.)

100% case-agnostic. Classification patterns are general legal concepts,
not tied to any specific party names or case numbers.

Case-specific patterns (party names, case numbers) come from CaseConfig
and are dynamically added at runtime, not hardcoded.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from .case_config import CaseConfig


@dataclass
class ClassificationResult:
    """Result of document classification."""
    doc_type: str = "unknown"
    doc_type_confidence: float = 0.0
    lanes: list[str] = field(default_factory=list)
    lane_confidence: dict = field(default_factory=dict)
    urgency: str = "normal"
    legal_topics: list[str] = field(default_factory=list)
    entities_found: list[str] = field(default_factory=list)
    dates_found: list[str] = field(default_factory=list)
    citations_found: list[str] = field(default_factory=list)


# ─── Generic Document Type Patterns (case-agnostic) ─────────────
DOC_TYPE_PATTERNS = {
    "order": [
        re.compile(r"(?i)\b(IT\s+IS\s+(?:HEREBY\s+)?ORDERED)", re.IGNORECASE),
        re.compile(r"(?i)\b(ORDER\s+(?:OF|GRANTING|DENYING|REGARDING))", re.IGNORECASE),
        re.compile(r"(?i)\b(JUDGMENT|RULING|DECREE)\b"),
    ],
    "motion": [
        re.compile(r"(?i)\b(MOTION\s+(?:TO|FOR|IN))\b"),
        re.compile(r"(?i)\b(MOVANT|MOVING\s+PARTY)\b"),
        re.compile(r"(?i)\b(respectfully\s+(?:moves|requests|submits))\b"),
    ],
    "brief": [
        re.compile(r"(?i)\b(BRIEF\s+(?:IN|OF))\b"),
        re.compile(r"(?i)\b(MEMORANDUM\s+(?:OF|IN))\b"),
        re.compile(r"(?i)\b(ARGUMENT|STATEMENT\s+OF\s+(?:FACTS|ISSUES|QUESTIONS))\b"),
    ],
    "complaint": [
        re.compile(r"(?i)\b(COMPLAINT\s+(?:FOR|TO|AND))\b"),
        re.compile(r"(?i)\b(PETITION\s+(?:FOR|TO))\b"),
        re.compile(r"(?i)\b(CAUSE\s+OF\s+ACTION|COUNT\s+[IVX\d]+)\b"),
    ],
    "affidavit": [
        re.compile(r"(?i)\b(AFFIDAVIT\s+(?:OF|IN))\b"),
        re.compile(r"(?i)\b(DECLARATION\s+(?:OF|IN))\b"),
        re.compile(r"(?i)\b(being\s+(?:first\s+)?duly\s+sworn)\b"),
    ],
    "subpoena": [
        re.compile(r"(?i)\b(SUBPOENA)\b"),
        re.compile(r"(?i)\b(COMMANDED\s+TO\s+(?:APPEAR|PRODUCE))\b"),
    ],
    "transcript": [
        re.compile(r"(?i)\b(TRANSCRIPT\s+OF\s+(?:PROCEEDINGS|HEARING))\b"),
        re.compile(r"(?i)\b(COURT\s+REPORTER|DIRECT\s+EXAMINATION)\b"),
        re.compile(r"(?i)\bQ\.\s+.+\n\s*A\.\s+"),
    ],
    "police_report": [
        re.compile(r"(?i)\b(INCIDENT\s+REPORT|POLICE\s+REPORT|OFFENSE\s+REPORT)\b"),
        re.compile(r"(?i)\b(RESPONDING\s+OFFICER|BADGE\s+(?:NO|NUMBER))\b"),
        re.compile(r"(?i)\b(POLICE\s+(?:DEPT|DEPARTMENT)|DISPATCH|INCIDENT\s+NUMBER|CASE\s+NUMBER|REPORT\s+NUMBER)\b"),
    ],
    "medical_record": [
        re.compile(r"(?i)\b(DIAGNOSIS|TREATMENT\s+PLAN|ASSESSMENT)\b"),
        re.compile(r"(?i)\b(PATIENT|CLINICAL\s+(?:NOTES|SUMMARY))\b"),
    ],
    "financial": [
        re.compile(r"(?i)\b(BANK\s+STATEMENT|TRANSACTION|LEDGER)\b"),
        re.compile(r"(?i)\b(INVOICE|RECEIPT|BALANCE\s+(?:DUE|FORWARD))\b"),
    ],
    "correspondence": [
        re.compile(r"(?i)\b(Dear\s+\w+|To\s+Whom\s+It\s+May\s+Concern)\b"),
        re.compile(r"(?i)\b(RE:|SUBJECT:)\b"),
    ],
    "form": [
        re.compile(r"(?i)\b(SCAO|MC\s*\d{3}|CC\s*\d{3}|FOC\s*\d{2,3})\b"),
        re.compile(r"(?i)\b(APPROVED\s*,?\s*SCAO)\b"),
    ],
    "evidence": [
        re.compile(r"(?i)\b(EXHIBIT\s+[A-Z\d])\b"),
        re.compile(r"(?i)\b(SCREENSHOT|PHOTOGRAPH|EVIDENCE\s+LOG)\b"),
    ],
}

# ─── Generic Lane Detection Patterns (case-agnostic legal concepts) ──
LANE_PATTERNS = {
    # Family law / custody
    "custody": [
        re.compile(r"(?i)\b(custody|parenting\s+time|visitation|best\s+interest)\b"),
        re.compile(r"(?i)\b(child\s+support|parental\s+(?:alienation|fitness))\b"),
        re.compile(r"(?i)\b(MCL\s+722\.(?:2[3-7]|27a)|MCR\s+3\.2(?:0[5-9]|1[0-8]))\b"),
        re.compile(r"(?i)\b(established\s+custodial|change\s+of\s+circumstances)\b"),
    ],
    # PPO / domestic protection
    "ppo": [
        re.compile(r"(?i)\b(personal\s+protection\s+order|PPO|stalking)\b"),
        re.compile(r"(?i)\b(MCL\s+600\.295[0-5]|domestic\s+(?:violence|assault))\b"),
        re.compile(r"(?i)\b(restrain|no.?contact|protection\s+order)\b"),
    ],
    # Housing / landlord-tenant
    "housing": [
        re.compile(r"(?i)\b(landlord|tenant|eviction|habitability)\b"),
        re.compile(r"(?i)\b(lease|rent|housing\s+(?:code|violation))\b"),
        re.compile(r"(?i)\b(mobile\s+home|manufactured|MHP|MHCRRA)\b"),
        re.compile(r"(?i)\b(MCL\s+125\.(?:2301|2501)|TILA|RESPA)\b"),
    ],
    # Appellate
    "appellate": [
        re.compile(r"(?i)\b(appeal|appellant|appellee|appellate)\b"),
        re.compile(r"(?i)\b(MCR\s+7\.(?:2\d{2}|3\d{2})|COA|Supreme\s+Court)\b"),
        re.compile(r"(?i)\b(reversible\s+error|abuse\s+of\s+discretion)\b"),
    ],
    # Federal civil rights
    "federal": [
        re.compile(r"(?i)\b(42\s+USC\s+.?\s*1983|section\s+1983|civil\s+rights)\b"),
        re.compile(r"(?i)\b(qualified\s+immunity|color\s+of\s+(?:law|state))\b"),
        re.compile(r"(?i)\b(due\s+process|equal\s+protection|14th\s+amendment)\b"),
        re.compile(r"(?i)\b(28\s+USC\s+.?\s*134[3-6]|USDC|federal\s+court)\b"),
    ],
    # Judicial misconduct
    "judicial": [
        re.compile(r"(?i)\b(judicial\s+(?:misconduct|tenure|ethics|canon))\b"),
        re.compile(r"(?i)\b(JTC|disqualif|recus|ex\s+parte\s+communic)\b"),
        re.compile(r"(?i)\b(bias|prejudice|impartial)\b"),
    ],
    # Criminal
    "criminal": [
        re.compile(r"(?i)\b(People\s+v|criminal|misdemeanor|felony)\b"),
        re.compile(r"(?i)\b(arraignment|plea|bond|probation)\b"),
        re.compile(r"(?i)\b(MCL\s+7(?:50|51|52)\.)\b"),
    ],
}

# ─── Legal Topic Patterns ────────────────────────────────────────
TOPIC_PATTERNS = {
    "best_interest_factors": re.compile(r"(?i)\b(MCL\s+722\.23|best\s+interest\s+factor)\b"),
    "parenting_time": re.compile(r"(?i)\b(MCL\s+722\.27a|parenting\s+time)\b"),
    "due_process": re.compile(r"(?i)\b(due\s+process|14th\s+amendment|Mathews\s+v)\b"),
    "ex_parte": re.compile(r"(?i)\b(ex\s+parte|MCR\s+3\.207|without\s+notice)\b"),
    "contempt": re.compile(r"(?i)\b(contempt|MCL\s+600\.170[1-5]|show\s+cause)\b"),
    "disqualification": re.compile(r"(?i)\b(disqualif|MCR\s+2\.003|recus)\b"),
    "service": re.compile(r"(?i)\b(service\s+of\s+process|MCR\s+2\.10[5-7]|proof\s+of\s+service)\b"),
    "discovery": re.compile(r"(?i)\b(discovery|interrogator|deposition|subpoena\s+duces)\b"),
    "summary_disposition": re.compile(r"(?i)\b(MCR\s+2\.116|summary\s+disposition)\b"),
    "parental_alienation": re.compile(r"(?i)\b(parental\s+alienation|MCL\s+722\.23\(j\)|facilitate)\b"),
    "endangerment": re.compile(r"(?i)\b(endanger|clear\s+and\s+convincing|physical\s+health)\b"),
    "constitutional_rights": re.compile(r"(?i)\b(liberty\s+interest|fundamental\s+right|Troxel)\b"),
    "fraud": re.compile(r"(?i)\b(fraud|misrepresent|false\s+(?:statement|allegation))\b"),
    "sanctions": re.compile(r"(?i)\b(sanctions|MCR\s+2\.114|frivolous)\b"),
}

# ─── Citation Extraction Pattern ─────────────────────────────────
CITATION_PATTERN = re.compile(
    r"(?:"
    r"MCR\s+\d+\.\d+(?:\([A-Z\d]+\))?"          # MCR 2.119(C)
    r"|MCL\s+\d+\.\d+(?:[a-z])?"                  # MCL 722.23
    r"|MRE\s+\d+"                                   # MRE 801
    r"|\d+\s+(?:US|USC|Mich\s+App|Mich|NW2d|F\.\d[dh])\s+\d+"  # Case cites
    r"|42\s+USC\s+.?\s*\d+"                         # Federal statutes
    r"|28\s+USC\s+.?\s*\d+"
    r")",
    re.IGNORECASE,
)

# ─── Date Extraction Pattern ─────────────────────────────────────
DATE_PATTERN = re.compile(
    r"\b(?:"
    r"\d{4}-\d{2}-\d{2}"                           # 2025-07-29
    r"|(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4}"                        # March 25, 2026
    r"|\d{1,2}/\d{1,2}/\d{4}"                      # 3/25/2026
    r")\b",
    re.IGNORECASE,
)


class DocumentClassifier:
    """Classifies documents by type, lane, urgency, and legal topics.

    Case-agnostic by default. Pass a CaseConfig to add case-specific
    patterns (party names, case numbers) at runtime.
    """

    def __init__(self, case_config: CaseConfig = None):
        self.case_config = case_config
        self._case_lane_patterns = self._build_case_patterns()

    def _build_case_patterns(self) -> dict:
        """Build case-specific lane patterns from CaseConfig."""
        if not self.case_config or not self.case_config.is_configured:
            return {}

        patterns = {}
        for lane_id, lane_info in self.case_config.lanes.items():
            lane_patterns = []
            # Add case number pattern
            case_num = lane_info.get("case_number", "")
            if case_num:
                escaped = re.escape(case_num)
                lane_patterns.append(re.compile(escaped, re.IGNORECASE))
            # Add judge name pattern
            judge = lane_info.get("judge", "")
            if judge:
                # Extract last name for matching
                parts = judge.replace("Hon.", "").strip().split()
                if parts:
                    lane_patterns.append(
                        re.compile(r"(?i)\b" + re.escape(parts[-1]) + r"\b")
                    )
            if lane_patterns:
                patterns[lane_id] = lane_patterns

        # Add party name patterns (match to any lane)
        party_names = []
        for party_key in ("plaintiff", "defendant"):
            p = getattr(self.case_config, party_key, {})
            name = p.get("name", "") if isinstance(p, dict) else ""
            if name:
                # Extract last name
                parts = name.split()
                if parts:
                    party_names.append(parts[-1])

        if party_names:
            patterns["_parties"] = [
                re.compile(r"(?i)\b" + re.escape(n) + r"\b")
                for n in party_names
            ]

        return patterns

    def classify(self, text: str, file_name: str = "") -> ClassificationResult:
        """Classify a document from its extracted text."""
        result = ClassificationResult()

        combined = f"{file_name}\n{text[:50000]}"  # Cap at 50K for speed

        # 1. Document type
        result.doc_type, result.doc_type_confidence = self._classify_doc_type(combined)

        # 2. Lane detection
        result.lanes, result.lane_confidence = self._classify_lanes(combined)

        # 3. Urgency
        result.urgency = self._classify_urgency(combined, result.doc_type)

        # 4. Legal topics
        result.legal_topics = self._extract_topics(combined)

        # 5. Citations
        result.citations_found = list(set(CITATION_PATTERN.findall(combined)))

        # 6. Dates
        result.dates_found = list(set(DATE_PATTERN.findall(combined)))[:20]

        return result

    def _classify_doc_type(self, text: str) -> tuple[str, float]:
        """Classify document type using pattern matching."""
        scores = {}
        for doc_type, patterns in DOC_TYPE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = pattern.findall(text)
                score += len(matches)
            if score > 0:
                scores[doc_type] = score

        if not scores:
            return "unknown", 0.0

        best = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = scores[best] / total if total > 0 else 0.0
        return best, round(confidence, 2)

    def _classify_lanes(self, text: str) -> tuple[list[str], dict]:
        """Classify litigation lanes. Returns primary + secondary lanes."""
        scores = {}

        # Generic patterns
        for lane_name, patterns in LANE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                score += len(pattern.findall(text))
            if score > 0:
                scores[lane_name] = score

        # Case-specific patterns
        for lane_id, patterns in self._case_lane_patterns.items():
            if lane_id == "_parties":
                continue
            for pattern in patterns:
                if pattern.search(text):
                    scores[lane_id] = scores.get(lane_id, 0) + 5  # Boost

        if not scores:
            return [], {}

        # Sort by score, return all with score > 0
        sorted_lanes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        total = sum(s for _, s in sorted_lanes)
        lanes = [lane for lane, _ in sorted_lanes]
        confidence = {lane: round(score / total, 2) for lane, score in sorted_lanes}

        return lanes, confidence

    def _classify_urgency(self, text: str, doc_type: str) -> str:
        """Classify urgency level."""
        urgent_patterns = [
            re.compile(r"(?i)\b(emergency|urgent|ex\s+parte|TRO|immediate)\b"),
            re.compile(r"(?i)\b(irreparable\s+harm|imminent\s+danger)\b"),
        ]
        critical_patterns = [
            re.compile(r"(?i)\b(IT\s+IS\s+(?:HEREBY\s+)?ORDERED)\b"),
            re.compile(r"(?i)\b(DEADLINE|DUE\s+(?:BY|DATE)|MUST\s+FILE\s+BY)\b"),
        ]

        urgent_score = sum(
            len(p.findall(text)) for p in urgent_patterns
        )
        critical_score = sum(
            len(p.findall(text)) for p in critical_patterns
        )

        if doc_type == "order":
            return "critical"
        if urgent_score >= 3 or doc_type in ("motion",) and urgent_score >= 1:
            return "high"
        if critical_score >= 2:
            return "high"
        if urgent_score >= 1:
            return "normal"
        return "low"

    def _extract_topics(self, text: str) -> list[str]:
        """Extract legal topics from text."""
        topics = []
        for topic, pattern in TOPIC_PATTERNS.items():
            if pattern.search(text):
                topics.append(topic)
        return topics
