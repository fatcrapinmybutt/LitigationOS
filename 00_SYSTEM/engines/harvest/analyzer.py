"""Harvest Engine — Deep analysis layer.

Impeachment value scoring (1-10), cross-exam question generation,
harm categorization, credibility assessment, pattern detection.
Zero API dependency — all analysis is rule-based local NLP.
"""

import logging
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Impeachment Patterns ─────────────────────────────────────────────────────
# Sworn statements, denials, admissions — high impeachment value
SWORN_PATTERNS = [
    re.compile(r"(?:I\s+)?(?:swear|affirm|state)\s+(?:under|that)", re.IGNORECASE),
    re.compile(r"under\s+(?:penalty\s+of\s+)?perjury", re.IGNORECASE),
    re.compile(r"subscribed\s+and\s+sworn", re.IGNORECASE),
    re.compile(r"(?:I\s+)?(?:deny|denied|never)", re.IGNORECASE),
    re.compile(r"(?:I\s+)?(?:admit|acknowledge|concede)", re.IGNORECASE),
    re.compile(r"to\s+(?:my|the\s+best\s+of\s+my)\s+knowledge", re.IGNORECASE),
]

DENIAL_PATTERNS = [
    re.compile(r"(?:I\s+)?(?:did\s+not|never|have\s+not|was\s+not)", re.IGNORECASE),
    re.compile(r"(?:I\s+)?deny\b", re.IGNORECASE),
    re.compile(r"(?:no\s+such|nothing\s+happened|did\s+not\s+occur)", re.IGNORECASE),
]

ADMISSION_PATTERNS = [
    re.compile(r"(?:I\s+)?(?:did|have|was|am)\s+(?:guilty|responsible|wrong)", re.IGNORECASE),
    re.compile(r"(?:I\s+)?admit\b", re.IGNORECASE),
    re.compile(r"(?:I\s+)?(?:acknowledge|concede|agree\s+that)", re.IGNORECASE),
    re.compile(r"nothing\s+was\s+physical", re.IGNORECASE),
]

# ── Harm Categories ──────────────────────────────────────────────────────────
HARM_PATTERNS = {
    "parenting_time_denial": re.compile(
        r"(?:denied|withheld|refused|prevented|blocked)\s+(?:parenting|visitation|contact|time)",
        re.IGNORECASE,
    ),
    "false_allegation": re.compile(
        r"(?:false|fabricat|unfounded|baseless|unsubstantiat)\w*\s+(?:allegation|claim|report|accusation)",
        re.IGNORECASE,
    ),
    "ex_parte_abuse": re.compile(
        r"(?:ex\s+parte|without\s+(?:notice|hearing)|emergency\s+(?:order|motion))",
        re.IGNORECASE,
    ),
    "contempt_abuse": re.compile(
        r"(?:contempt|jail|incarcerat|imprison|sentence)",
        re.IGNORECASE,
    ),
    "due_process_denial": re.compile(
        r"(?:due\s+process|right\s+to\s+(?:be\s+heard|hearing|notice)|denied\s+(?:hearing|opportunity))",
        re.IGNORECASE,
    ),
    "financial_harm": re.compile(
        r"(?:lost\s+(?:job|employment|income|house|home)|fired|evict|foreclos)",
        re.IGNORECASE,
    ),
    "child_alienation": re.compile(
        r"(?:alienat|estrang|interfere\w*\s+with\s+(?:relationship|bond)|withhold\w*\s+child)",
        re.IGNORECASE,
    ),
    "medication_coercion": re.compile(
        r"(?:medic(?:ation|ine)|prescri(?:ption|be)|mental\s+health\s+(?:eval|treat|condition))",
        re.IGNORECASE,
    ),
    "ppo_weaponization": re.compile(
        r"(?:PPO|protection\s+order|restraining\s+order)\s*(?:as|for|used|weaponiz)",
        re.IGNORECASE,
    ),
    "evidence_exclusion": re.compile(
        r"(?:exclud|suppress|ignor|disregard|refus)\w*\s+(?:evidence|exhibit|testimony|report)",
        re.IGNORECASE,
    ),
}

# ── Credibility Indicators ───────────────────────────────────────────────────
CREDIBILITY_NEGATIVE = [
    re.compile(r"(?:inconsistent|contradict|changed\s+(?:story|statement|version))", re.IGNORECASE),
    re.compile(r"(?:lied|dishonest|untruthful|perjur|fabricat)", re.IGNORECASE),
    re.compile(r"(?:recant|retract|walk(?:ed)?\s+back)", re.IGNORECASE),
    re.compile(r"(?:meth|drug|substance)\s*(?:use|abuse|addict)", re.IGNORECASE),
]

CREDIBILITY_POSITIVE = [
    re.compile(r"(?:consistent|corroborat|verified|confirmed|documented)", re.IGNORECASE),
    re.compile(r"(?:officer|police|investigat|report)\s+(?:found|confirmed|stated)", re.IGNORECASE),
    re.compile(r"(?:medical|clinical|psychological)\s+(?:record|report|evaluat)", re.IGNORECASE),
]

# ── Retaliation/Escalation Patterns ──────────────────────────────────────────
RETALIATION_INDICATORS = [
    re.compile(r"(?:filed|obtained|sought)\s+(?:after|following|in\s+response)", re.IGNORECASE),
    re.compile(r"(?:retaliat|punish|punitive|vindictive|revenge)", re.IGNORECASE),
    re.compile(r"(?:within\s+\d+\s+(?:days?|hours?|weeks?)\s+(?:of|after))", re.IGNORECASE),
]

ESCALATION_INDICATORS = [
    re.compile(r"(?:escalat|intensif|worsen|increas)\w*", re.IGNORECASE),
    re.compile(r"(?:additional|new|further)\s+(?:allegation|charge|motion|order)", re.IGNORECASE),
    re.compile(r"(?:jail|incarcerat|arrest|suspend)\w*\s+(?:parenting|time|rights)", re.IGNORECASE),
]

# ── Cross-Examination Question Templates ─────────────────────────────────────
CROSS_EXAM_TEMPLATES = {
    "denial": [
        "You stated under oath that {claim}. Is that correct?",
        "And at the time you made that statement, you believed it to be true?",
        "But isn't it true that {contradiction}?",
    ],
    "admission": [
        "You acknowledged that {claim}. Is that accurate?",
        "And this admission was made voluntarily?",
    ],
    "inconsistency": [
        "On {date_a}, you stated {statement_a}. Correct?",
        "And on {date_b}, you stated {statement_b}. Also correct?",
        "Can you explain the inconsistency between these statements?",
    ],
    "pattern": [
        "This was not the first time {pattern_description}, was it?",
        "In fact, this has happened on at least {count} occasions?",
    ],
}


class AnalysisResult:
    """Result of deep analysis on extracted + classified content."""
    __slots__ = (
        "impeachment_value", "impeachment_reason", "harm_categories",
        "credibility_score", "credibility_factors", "cross_exam_questions",
        "retaliation_indicators", "escalation_indicators", "sworn_statements",
        "denials", "admissions", "pattern_tags",
    )

    def __init__(self):
        self.impeachment_value = 0          # 1-10 scale
        self.impeachment_reason = ""
        self.harm_categories = []           # [(category, snippet)]
        self.credibility_score = 0.5        # 0.0=no credibility, 1.0=high
        self.credibility_factors = []       # [(factor, direction)]
        self.cross_exam_questions = []      # [question_text]
        self.retaliation_indicators = 0
        self.escalation_indicators = 0
        self.sworn_statements = []          # [snippet]
        self.denials = []                   # [snippet]
        self.admissions = []                # [snippet]
        self.pattern_tags = []              # [tag_string]

    def to_dict(self) -> Dict:
        return {
            "impeachment_value": self.impeachment_value,
            "impeachment_reason": self.impeachment_reason,
            "harm_categories": self.harm_categories,
            "credibility_score": self.credibility_score,
            "credibility_factors": self.credibility_factors,
            "cross_exam_questions": self.cross_exam_questions,
            "retaliation_indicators": self.retaliation_indicators,
            "escalation_indicators": self.escalation_indicators,
            "sworn_statements": self.sworn_statements,
            "denials": self.denials,
            "admissions": self.admissions,
            "pattern_tags": self.pattern_tags,
        }


def _extract_context(text: str, match: re.Match, window: int = 120) -> str:
    """Extract surrounding context around a regex match."""
    start = max(0, match.start() - window)
    end = min(len(text), match.end() + window)
    snippet = text[start:end].strip()
    snippet = re.sub(r"\s+", " ", snippet)
    return snippet


def analyze_text(
    text: str,
    source_file: str = "",
    actors: Optional[List[str]] = None,
    lane: str = "A",
) -> AnalysisResult:
    """Perform deep analysis on extracted text.

    Returns impeachment scoring, harm categories, credibility assessment,
    cross-exam questions, and pattern detection — all locally, zero API.
    """
    result = AnalysisResult()
    if not text or len(text) < 20:
        return result

    text_lower = text.lower()
    actors = actors or []

    # ── Sworn statement detection ────────────────────────────────────────
    for pat in SWORN_PATTERNS:
        for m in pat.finditer(text):
            snippet = _extract_context(text, m, 150)
            if snippet not in result.sworn_statements:
                result.sworn_statements.append(snippet)
            if len(result.sworn_statements) >= 20:
                break

    # ── Denial detection ─────────────────────────────────────────────────
    for pat in DENIAL_PATTERNS:
        for m in pat.finditer(text):
            snippet = _extract_context(text, m, 120)
            if snippet not in result.denials:
                result.denials.append(snippet)
            if len(result.denials) >= 15:
                break

    # ── Admission detection ──────────────────────────────────────────────
    for pat in ADMISSION_PATTERNS:
        for m in pat.finditer(text):
            snippet = _extract_context(text, m, 120)
            if snippet not in result.admissions:
                result.admissions.append(snippet)
            if len(result.admissions) >= 15:
                break

    # ── Harm categorization ──────────────────────────────────────────────
    for category, pat in HARM_PATTERNS.items():
        for m in pat.finditer(text):
            snippet = _extract_context(text, m, 100)
            result.harm_categories.append((category, snippet))
            if len(result.harm_categories) >= 30:
                break

    # ── Credibility assessment ───────────────────────────────────────────
    neg_hits = 0
    pos_hits = 0
    for pat in CREDIBILITY_NEGATIVE:
        hits = len(pat.findall(text))
        neg_hits += hits
        if hits > 0:
            result.credibility_factors.append((pat.pattern[:60], "negative"))
    for pat in CREDIBILITY_POSITIVE:
        hits = len(pat.findall(text))
        pos_hits += hits
        if hits > 0:
            result.credibility_factors.append((pat.pattern[:60], "positive"))

    total_cred = neg_hits + pos_hits
    if total_cred > 0:
        result.credibility_score = pos_hits / total_cred
    else:
        result.credibility_score = 0.5  # neutral

    # ── Retaliation / escalation detection ───────────────────────────────
    for pat in RETALIATION_INDICATORS:
        result.retaliation_indicators += len(pat.findall(text))
    for pat in ESCALATION_INDICATORS:
        result.escalation_indicators += len(pat.findall(text))

    # ── Impeachment value scoring (1-10) ─────────────────────────────────
    score = 0
    reasons = []

    if result.sworn_statements:
        score += min(3, len(result.sworn_statements))
        reasons.append(f"{len(result.sworn_statements)} sworn statement(s)")

    if result.denials:
        score += min(2, len(result.denials))
        reasons.append(f"{len(result.denials)} denial(s)")

    if result.admissions:
        score += min(3, len(result.admissions))
        reasons.append(f"{len(result.admissions)} admission(s)")

    # Emily-specific boost: her own filings are impeachment gold
    source_lower = source_file.lower()
    if "emily" in source_lower or "watson" in source_lower:
        score += 2
        reasons.append("Emily Watson filing — impeachment source")

    # Harm categories boost
    if len(result.harm_categories) >= 3:
        score += 1
        reasons.append(f"{len(result.harm_categories)} harm categories")

    # Credibility issue boost
    if neg_hits >= 2:
        score += 1
        reasons.append("credibility concerns detected")

    result.impeachment_value = min(10, max(1, score))
    result.impeachment_reason = "; ".join(reasons) if reasons else "minimal impeachment value"

    # ── Pattern tags ─────────────────────────────────────────────────────
    if result.retaliation_indicators >= 2:
        result.pattern_tags.append("RETALIATION_PATTERN")
    if result.escalation_indicators >= 2:
        result.pattern_tags.append("ESCALATION_PATTERN")
    if "nothing was physical" in text_lower:
        result.pattern_tags.append("RECANTATION")
    if "ex parte" in text_lower:
        result.pattern_tags.append("EX_PARTE")
    if any(a.lower() in ["mcneill", "judge mcneill"] for a in actors):
        result.pattern_tags.append("JUDICIAL_ACTOR")

    # Actor-specific patterns for known adversaries
    has_watson = any("watson" in a.lower() or "emily" in a.lower() for a in actors)
    has_mcneill = any("mcneill" in a.lower() for a in actors)
    has_rusco = any("rusco" in a.lower() for a in actors)

    if has_watson and result.denials:
        result.pattern_tags.append("WATSON_DENIAL")
    if has_mcneill and "ex parte" in text_lower:
        result.pattern_tags.append("MCNEILL_EX_PARTE")
    if has_rusco:
        result.pattern_tags.append("FOC_INVOLVEMENT")

    # ── Cross-exam question generation ───────────────────────────────────
    for denial in result.denials[:5]:
        q = f"You stated: \"{denial[:100]}...\" Is that your testimony?"
        result.cross_exam_questions.append(q)

    for admission in result.admissions[:5]:
        q = f"You acknowledged: \"{admission[:100]}...\" Correct?"
        result.cross_exam_questions.append(q)

    if result.retaliation_indicators >= 2:
        result.cross_exam_questions.append(
            "This action was filed shortly after the opposing party's filing. Can you explain the timing?"
        )

    if result.harm_categories:
        cats = set(c for c, _ in result.harm_categories)
        if "false_allegation" in cats:
            result.cross_exam_questions.append(
                "Were any of these allegations ever substantiated by law enforcement?"
            )
        if "parenting_time_denial" in cats:
            result.cross_exam_questions.append(
                "On how many occasions was parenting time denied or interfered with?"
            )

    return result


def score_impeachment_batch(
    items: List[Dict],
) -> List[Dict]:
    """Score impeachment value for a batch of items.

    Each item should have 'text', 'source_file', 'actors', 'lane' keys.
    Returns items with 'analysis' key added.
    """
    results = []
    for item in items:
        analysis = analyze_text(
            text=item.get("text", ""),
            source_file=item.get("source_file", ""),
            actors=item.get("actors", []),
            lane=item.get("lane", "A"),
        )
        item["analysis"] = analysis.to_dict()
        results.append(item)
    return results
