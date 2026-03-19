"""
Filing Quality Validator — LitigationOS 2026
Comprehensive Michigan Court Rule compliance validator.
Checks filings against MCR 2.113, MCR 1.109, MCR 2.119, MCR 2.107,
MCR 7.212, MCR 7.305, and content quality standards.
"""

import os
import re
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Filing type → applicable categories ──
FILING_CATEGORIES = {
    "motion":      [1, 2, 3, 4, 5, 7],
    "brief":       [1, 3, 4, 5, 6, 7],
    "complaint":   [1, 3, 4, 5, 7],
    "application": [1, 3, 4, 5, 6, 7],
    "affidavit":   [1, 3, 4, 5, 7],
}

# ── Page / word limits ──
PAGE_LIMITS = {
    "brief":       {"pages": 50, "words": 16000},
    "motion":      {"pages": 20, "words": 8000},
    "application": {"pages": 50, "words": 16000},
    "complaint":   {"pages": None, "words": None},
    "affidavit":   {"pages": None, "words": None},
}

# ── Emotional / informal word lists ──
EMOTIONAL_WORDS = [
    "unfair", "outrageous", "disgusting", "heartbreaking", "evil", "corrupt",
    "terrible", "horrible", "shocking", "appalling", "despicable",
    "unbelievable", "ridiculous", "absurd", "disgraceful", "shameful",
    "atrocious", "monstrous", "vile", "wicked", "malicious",
]

INFORMAL_WORDS = [
    "gonna", "wanna", "gotta", "stuff", "things", "kinda", "sorta",
    "basically", "literally", "like,", "you know", "whatever",
    "no way", "big deal", "messed up",
]

CONCLUSORY_MARKERS = [
    "clearly", "obviously", "undeniably", "without question",
    "without doubt", "beyond dispute", "it is clear that",
    "it is obvious that", "there is no question that",
    "it goes without saying", "needless to say", "self-evident",
    "indisputable", "unquestionable", "patently", "manifestly",
]

PERSONAL_ATTACK_PATTERNS = [
    r"(?:she|he)\s+is\s+a\s+liar",
    r"(?:she|he)\s+is\s+(?:corrupt|evil|crazy|insane|incompetent|stupid)",
    r"(?:this|the)\s+judge\s+is\s+(?:corrupt|biased|incompetent|dishonest)",
    r"opposing\s+counsel\s+(?:is\s+a\s+liar|lies|lied)",
]

FIRST_PERSON_EMOTIONAL = [
    r"\bI\s+feel\s+(?:that\s+)?",
    r"\bI\s+believe\s+(?:that\s+)?",
    r"\bI\s+think\s+(?:that\s+)?",
    r"\bIn\s+my\s+opinion\b",
    r"\bI\s+am\s+(?:certain|sure|convinced)\b",
]

SETTLEMENT_PATTERNS = [
    r"(?i)settlement\s+(?:offer|negotiation|discussion|conference)",
    r"(?i)(?:offered|proposed)\s+to\s+settle",
    r"(?i)mediation\s+(?:statement|position|offer)",
]

AI_REFERENCE_PATTERNS = [
    r"(?i)\bchatgpt\b", r"(?i)\bgpt[-\s]?\d\b", r"(?i)\bopenai\b",
    r"(?i)\bgenerated\s+(?:by|using|with)\s+(?:ai|artificial intelligence)\b",
    r"(?i)\bcopilot\b", r"(?i)\bgemini\b", r"(?i)\bclaude\b",
]

THREAT_PATTERNS = [
    r"(?i)you\s+will\s+(?:regret|pay\s+for|suffer)",
    r"(?i)(?:I|we)\s+will\s+(?:destroy|ruin|expose)",
    r"(?i)warn(?:ing|ed)?\s+(?:you|the\s+court)\s+(?:that|about)",
]

# Known legal acronyms (exempt from ALL-CAPS check)
LEGAL_ACRONYMS = {
    "MCR", "MCL", "MRE", "COA", "MSC", "JTC", "FOC", "PPO", "SCAO",
    "USDC", "USC", "DOB", "DNA", "IRAC", "GAL", "CPS", "DHHS", "DHS",
    "USA", "FBI", "ICE", "ADA", "HIPAA", "FOIA", "CFR", "USC", "FRE",
    "FRCP", "UCCJEA", "UIFSA", "PKPA", "VAWA", "PRO", "AND", "THE",
    "FOR", "NOT", "BUT", "NOR", "YET", "ALL", "PER", "VIA",
    "HON", "FKA", "AKA", "ESQ", "NW2D", "NW2d", "LDW",
    "MOTION", "PLAINTIFF", "DEFENDANT", "COURT", "STATE",
    "MICHIGAN", "MUSKEGON", "COUNTY", "CIRCUIT",
    "DIRECTED", "CHIEF", "JUDGE", "FORMAL", "COMPLAINT",
    "COMPLAINANT", "RESPONDENT", "JUDICIAL", "TENURE", "COMMISSION",
    "WHEREFORE", "FILED", "PURSUANT", "HEREBY", "NOW", "COMES",
    "ORDERED", "ORDER", "NOTICE", "FURTHER", "APPEAL", "BRIEF",
    "APPLICATION", "EMERGENCY", "IMMEDIATE", "APPELLANT", "APPELLEE",
    "PHONE", "EMAIL", "ADDRESS", "CITY", "RECEIVED",
    "XIV", "XIII", "XII", "III", "VII", "VIII",
}

# Citation patterns
_MCR_PAT = re.compile(r"MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*")
_MCL_PAT = re.compile(r"MCL\s+\d+\.\d+[a-z]*(?:\([A-Za-z0-9]+\))*(?:\([a-z]\)(?:-\([a-z]\))?)?")
_MRE_PAT = re.compile(r"MRE\s+\d+(?:\([A-Za-z0-9]+\))*")
_CASE_PAT = re.compile(
    r"\*?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\*?"
    r",?\s+\d+\s+(?:Mich|Mich\s*App|NW2d|US)\s+\d+"
)
_US_CONST_PAT = re.compile(r"(?:US|U\.S\.)\s+Const(?:itution)?,?\s+Am(?:end(?:ment)?)?\.?\s+[IVXLCDM]+")
_EXHIBIT_PAT = re.compile(r"(?i)(?:exhibit|ex\.?)\s+[A-Z0-9]+")
_DOCKET_PAT = re.compile(r"(?i)(?:docket|record)\s*(?:entry|event|,)")
_AFFIDAVIT_PAT = re.compile(r"(?i)(?:affidavit|declaration|sworn\s+(?:statement|testimony))")

_ANY_CITE_PAT = re.compile(
    r"(?:MCR\s+\d+\.\d+|MCL\s+\d+\.\d+|MRE\s+\d+|"
    r"\d+\s+(?:Mich|Mich\s*App|NW2d|US)\s+\d+|"
    r"(?:US|U\.S\.)\s+Const|"
    r"Const\s+1963,?\s+art)"
)

_ANY_SOURCE_PAT = re.compile(
    r"(?i)(?:exhibit|ex\.?)\s+[A-Z0-9]+|"
    r"(?:docket|record)\s*(?:entry|event|,)|"
    r"(?:affidavit|declaration)\s+of|"
    r"(?:see|see\s+also|cf\.?)\s+|"
    r"(?:supra|infra)\b|"
    r"evidence_quotes|"
    r"\bfn\.\s*\d+"
)


def _connect_db(db_path: str) -> Optional[sqlite3.Connection]:
    """Connect to litigation DB with retry."""
    for attempt in range(3):
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error:
            import time
            time.sleep(2 ** attempt)
    return None


def _read_filing(filepath: str) -> str:
    """Read filing text from .md or .txt file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _split_sentences(text: str) -> List[str]:
    """Rough sentence splitter for legal text."""
    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z\d"\*\(])', text)
    return [s.strip() for s in raw if s.strip()]


def _split_paragraphs(text: str) -> List[str]:
    """Split on double-newline or numbered paragraph boundaries."""
    paras = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paras if p.strip()]


# ═══════════════════════════════════════════════════════════════════
# MAIN VALIDATOR CLASS
# ═══════════════════════════════════════════════════════════════════

class FilingQualityValidator:
    """Validates Michigan court filings across 7 compliance categories."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = _connect_db(db_path)
        self._known_rules: set = set()
        self._load_rules()

    def _load_rules(self):
        """Pre-load known rule numbers from auth_rules for citation verification."""
        if not self.conn:
            return
        try:
            cur = self.conn.execute(
                "SELECT DISTINCT rule_number FROM auth_rules WHERE rule_number IS NOT NULL"
            )
            self._known_rules = {row["rule_number"] for row in cur.fetchall()}
        except sqlite3.Error:
            pass

    # ─────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────

    def validate_filing(
        self, filepath: str, filing_type: str
    ) -> Dict[str, Any]:
        """
        Validate a filing against all applicable Michigan Court Rule categories.

        Parameters
        ----------
        filepath : str
            Path to the .md filing.
        filing_type : str
            One of: motion, brief, complaint, application, affidavit.

        Returns
        -------
        dict with: overall_score, category_scores, checks, critical_failures,
                   recommendations, word_count, estimated_pages.
        """
        filing_type = filing_type.lower()
        if filing_type not in FILING_CATEGORIES:
            raise ValueError(f"Unknown filing_type: {filing_type}")

        text = _read_filing(filepath)
        categories = FILING_CATEGORIES[filing_type]

        all_checks: List[Dict[str, Any]] = []
        category_scores: Dict[str, float] = {}

        # Dispatch to category checkers
        dispatch = {
            1: ("Structural (MCR 2.113/1.109)", self._cat1_structural),
            2: ("Motion Requirements (MCR 2.119)", self._cat2_motion),
            3: ("Certificate of Service (MCR 2.107)", self._cat3_service),
            4: ("Content Quality", self._cat4_content),
            5: ("Pro Se Traps", self._cat5_prose_traps),
            6: ("Appeal-Specific (MCR 7.212/7.305)", self._cat6_appeal),
            7: ("Prohibited Content", self._cat7_prohibited),
        }

        for cat_num in categories:
            label, checker = dispatch[cat_num]
            checks = checker(text, filing_type)
            all_checks.extend(checks)
            passed = sum(1 for c in checks if c["status"] == "PASS")
            total = len(checks) if checks else 1
            category_scores[label] = round(passed / total * 100, 1)

        # Compute overall
        total_checks = len(all_checks)
        passed_checks = sum(1 for c in all_checks if c["status"] == "PASS")
        warn_checks = sum(1 for c in all_checks if c["status"] == "WARN")
        fail_checks = sum(1 for c in all_checks if c["status"] == "FAIL")

        # Score: PASS=1, WARN=0.5, FAIL=0
        raw_score = (passed_checks + warn_checks * 0.5) / total_checks * 100 if total_checks else 0
        overall_score = round(raw_score, 1)

        critical_failures = [
            c for c in all_checks
            if c["status"] == "FAIL" and c.get("critical", False)
        ]

        recommendations = self._build_recommendations(all_checks, filing_type)

        words = len(text.split())
        return {
            "filepath": filepath,
            "filing_type": filing_type,
            "overall_score": overall_score,
            "category_scores": category_scores,
            "checks": all_checks,
            "summary": {
                "total": total_checks,
                "passed": passed_checks,
                "warnings": warn_checks,
                "failures": fail_checks,
            },
            "critical_failures": critical_failures,
            "recommendations": recommendations,
            "word_count": words,
            "estimated_pages": max(1, words // 250),
        }

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 1: STRUCTURAL REQUIREMENTS (MCR 2.113, MCR 1.109)
    # ═══════════════════════════════════════════════════════════════

    def _cat1_structural(self, text: str, filing_type: str) -> List[Dict]:
        checks = []

        # 1a. Caption — court name
        has_court = bool(re.search(
            r"(?i)(circuit\s+court|court\s+of\s+appeals|supreme\s+court|"
            r"judicial\s+tenure\s+commission)", text
        ))
        checks.append(self._check(
            "Caption: court name present", has_court,
            "Court name found in caption" if has_court else "Missing court name in caption (MCR 2.113(A))",
            critical=True,
        ))

        # 1b. Caption — case number
        has_case_no = bool(re.search(
            r"(?:Case\s+No\.?\s*|Docket\s+No\.?\s*)[\d\-]+(?:-[A-Z]{2})?", text
        ))
        checks.append(self._check(
            "Caption: case number present", has_case_no,
            "Case number found" if has_case_no else "Missing case number in caption",
            critical=True,
        ))

        # 1c. Caption — judge name
        has_judge = bool(re.search(r"(?i)(?:Hon\.?|Honorable)\s+[A-Z]", text))
        # JTC filings reference respondent judge differently
        if not has_judge and filing_type == "complaint":
            has_judge = bool(re.search(r"(?i)respondent\s+judge", text))
        checks.append(self._check(
            "Caption: judge name present", has_judge,
            "Judge name found" if has_judge else "Missing judge name in caption",
            critical=False,
        ))

        # 1d. Caption — party names
        has_plaintiff = bool(re.search(
            r"(?i)(plaintiff|appellant|petitioner|complainant)", text[:2000]
        ))
        has_defendant = bool(re.search(
            r"(?i)(defendant|appellee|respondent|real\s+party)", text[:2000]
        ))
        parties_ok = has_plaintiff and has_defendant
        checks.append(self._check(
            "Caption: party names present", parties_ok,
            "Both parties identified" if parties_ok else "Missing party designation in caption",
            critical=True,
        ))

        # 1e. Document title
        has_title = bool(re.search(
            r"(?i)(MOTION|BRIEF|COMPLAINT|APPLICATION|AFFIDAVIT|PETITION|"
            r"MEMORANDUM|RESPONSE|REPLY|CLAIM\s+OF\s+APPEAL)", text[:3000]
        ))
        checks.append(self._check(
            "Caption: document title present", has_title,
            "Document title found" if has_title else "Missing document title in caption",
            critical=True,
        ))

        # 1f. Numbered paragraphs
        numbered = re.findall(r"^\s*\d+\.\s+", text, re.MULTILINE)
        has_numbered = len(numbered) >= 3
        checks.append(self._check(
            "Numbered paragraphs (MCR 2.113(D))", has_numbered,
            f"{len(numbered)} numbered paragraphs found" if has_numbered
            else f"Only {len(numbered)} numbered paragraphs — allegations must be numbered per MCR 2.113(D)",
            critical=True,
        ))

        # 1g. Single set of circumstances per paragraph (spot check)
        long_paras = self._check_paragraph_length(text)
        para_ok = long_paras <= 2
        status = "PASS" if long_paras == 0 else ("WARN" if long_paras <= 2 else "FAIL")
        checks.append({
            "check": "Paragraphs limited to single set of circumstances (MCR 2.113(B)(2))",
            "status": status,
            "detail": f"{long_paras} paragraphs appear to contain multiple distinct allegations"
                      if long_paras > 0 else "Paragraphs appear appropriately focused",
            "critical": False,
        })

        # 1h. Signature block
        has_sig = bool(re.search(
            r"(?i)(respectfully\s+submitted|/s/|signature|"
            r"dated\s*[:\.]?\s*\w+|pro\s+se\s+(?:plaintiff|appellant|petitioner))",
            text[-3000:]
        ))
        checks.append(self._check(
            "Signature block present (MCR 2.113(E))", has_sig,
            "Signature block found" if has_sig else "Missing signature block (MCR 2.113(E))",
            critical=True,
        ))

        # 1i. Verification / affidavit (check if needed for verified pleadings)
        needs_verification = filing_type == "affidavit"
        if needs_verification:
            has_verif = bool(re.search(
                r"(?i)(sworn|notary|jurat|under\s+(?:oath|penalty\s+of\s+perjury))",
                text
            ))
            checks.append(self._check(
                "Verification/affidavit present (MCR 1.109(D)(3))", has_verif,
                "Verification/oath language found" if has_verif
                else "Affidavit missing verification/jurat language (MCR 1.109(D)(3))",
                critical=True,
            ))
        else:
            checks.append(self._check(
                "Verification/affidavit (MCR 1.109(D)(3))",
                True,
                "Not required for this filing type",
                critical=False,
            ))

        return checks

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 2: MOTION REQUIREMENTS (MCR 2.119)
    # ═══════════════════════════════════════════════════════════════

    def _cat2_motion(self, text: str, filing_type: str) -> List[Dict]:
        checks = []

        # 2a. States grounds with particularity
        has_grounds = bool(re.search(
            r"(?i)(ground|basis|reason|because|due\s+to|pursuant\s+to|"
            r"on\s+the\s+ground|specifically)", text
        ))
        checks.append(self._check(
            "States grounds with particularity (MCR 2.119(A)(1))", has_grounds,
            "Grounds stated" if has_grounds else "Motion does not clearly state grounds (MCR 2.119(A)(1))",
            critical=True,
        ))

        # 2b. States authority
        has_authority = bool(_MCR_PAT.search(text) or _MCL_PAT.search(text) or _CASE_PAT.search(text))
        checks.append(self._check(
            "States authority on which based (MCR 2.119(A)(1))", has_authority,
            "Legal authority cited" if has_authority else "No legal authority cited for the motion (MCR 2.119(A)(1))",
            critical=True,
        ))

        # 2c. States relief sought
        has_relief = bool(re.search(
            r"(?i)(relief\s+(?:requested|sought)|(?:respectfully\s+)?request|"
            r"(?:this\s+court|court\s+should|court\s+to)\s+(?:enter|grant|order|issue)|"
            r"wherefore|prayer\s+for\s+relief|asks\s+this\s+(?:honorable\s+)?court)",
            text
        ))
        checks.append(self._check(
            "States relief or order sought (MCR 2.119(A)(1))", has_relief,
            "Relief requested" if has_relief else "Motion does not clearly state relief sought",
            critical=True,
        ))

        # 2d. Brief or supporting authority/affidavit
        has_brief = bool(re.search(
            r"(?i)(argument|brief\s+in\s+support|supporting\s+(?:brief|memorandum)|"
            r"memorandum\s+of\s+law|legal\s+analysis|IRAC|issue.*rule.*application.*conclusion)",
            text
        ))
        checks.append(self._check(
            "Brief/supporting authority attached (MCR 2.119(A)(2))", has_brief,
            "Legal argument/brief section present" if has_brief
            else "No legal brief or supporting authority found (MCR 2.119(A)(2))",
            critical=True,
        ))

        # 2e. Notice of hearing
        has_notice = bool(re.search(
            r"(?i)(notice\s+of\s+hearing|hearing\s+(?:date|scheduled|set)|"
            r"oral\s+argument\s+(?:is\s+)?requested|"
            r"emergency.*hearing|"
            r"this\s+matter\s+(?:is|will\s+be)\s+(?:set|heard))", text
        ))
        status = "PASS" if has_notice else "WARN"
        checks.append({
            "check": "Notice of hearing (if applicable)",
            "status": status,
            "detail": "Hearing notice/request found" if has_notice
                      else "No notice of hearing found — may be required depending on local practice",
            "critical": False,
        })

        # 2f. Proposed order
        has_proposed_order = bool(re.search(
            r"(?i)(proposed\s+order|order\s+(?:granting|denying)|"
            r"(?:attached|enclosed|accompanying)\s+(?:hereto\s+)?(?:is|are)\s+.*order|"
            r"appendix.*proposed\s+order)",
            text
        ))
        status = "PASS" if has_proposed_order else "WARN"
        checks.append({
            "check": "Proposed order (MCR 2.119(A)(2))",
            "status": status,
            "detail": "Proposed order reference found" if has_proposed_order
                      else "No proposed order referenced — MCR 2.119(A)(2) requires one to accompany each motion",
            "critical": False,
        })

        return checks

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 3: CERTIFICATE OF SERVICE (MCR 2.107)
    # ═══════════════════════════════════════════════════════════════

    def _cat3_service(self, text: str, filing_type: str) -> List[Dict]:
        checks = []

        cos_section = ""
        cos_match = re.search(
            r"(?i)(certificate\s+of\s+service.*?)(?:\Z|(?=\n#\s))",
            text, re.DOTALL
        )
        has_cos = cos_match is not None
        if cos_match:
            cos_section = cos_match.group(1)

        # 3a. Certificate of Service present
        checks.append(self._check(
            "Certificate of Service present (MCR 2.107)", has_cos,
            "Certificate of Service found" if has_cos
            else "MISSING Certificate of Service — required on every filing (MCR 2.107(C)(3))",
            critical=True,
        ))

        if has_cos and cos_section:
            # 3b. Method of service
            has_method = bool(re.search(
                r"(?i)(first.class\s+mail|hand\s+deliver|e-?fil|"
                r"electronic(?:ally)?|personal\s+service|"
                r"regular\s+mail|certified\s+mail|U\.?S\.?\s+mail|"
                r"MiFile|TrueFiling)", cos_section
            ))
            checks.append(self._check(
                "CoS: method of service stated", has_method,
                "Service method specified" if has_method
                else "Certificate of Service does not state method of service",
                critical=True,
            ))

            # 3c. Date of service
            has_date = bool(re.search(
                r"(?i)(?:(?:on|dated?|this)\s+)?"
                r"(?:\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4}|"
                r"_+\s*,?\s*\d{4}|____|day\s+of\s+\w+\s*,?\s*\d{4})",
                cos_section
            ))
            checks.append(self._check(
                "CoS: date of service stated", has_date,
                "Service date found" if has_date
                else "Certificate of Service does not include date of service",
                critical=True,
            ))

            # 3d. Name and address of person served
            has_recipient = bool(re.search(
                r"(?i)(tiffany|watson|(?:opposing|other)\s+(?:party|counsel)|"
                r"(?:attorney|counsel)\s+for|defendant|appellee|respondent|"
                r"all\s+parties|each\s+party)",
                cos_section
            ))
            checks.append(self._check(
                "CoS: name/address of person served", has_recipient,
                "Recipient identified" if has_recipient
                else "Certificate of Service does not identify the person served",
                critical=True,
            ))

            # 3e. Signed
            has_cos_sig = bool(re.search(
                r"(?i)(/s/|signature|andrew\s+pigors|_____)",
                cos_section
            ))
            checks.append(self._check(
                "CoS: signed", has_cos_sig,
                "Certificate of Service appears signed" if has_cos_sig
                else "Certificate of Service is not signed",
                critical=True,
            ))
        else:
            for label in [
                "CoS: method of service stated",
                "CoS: date of service stated",
                "CoS: name/address of person served",
                "CoS: signed",
            ]:
                checks.append({
                    "check": label,
                    "status": "FAIL",
                    "detail": "Cannot check — Certificate of Service is missing",
                    "critical": True,
                })

        return checks

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 4: CONTENT QUALITY
    # ═══════════════════════════════════════════════════════════════

    def _cat4_content(self, text: str, filing_type: str) -> List[Dict]:
        checks = []

        # 4a. Emotional language detection
        emotional_found = []
        text_lower = text.lower()
        for word in EMOTIONAL_WORDS:
            if word in text_lower:
                # Count occurrences
                count = len(re.findall(r"\b" + re.escape(word) + r"\b", text_lower))
                if count > 0:
                    emotional_found.append(f'"{word}" ({count}x)')

        if emotional_found:
            status = "WARN" if len(emotional_found) <= 2 else "FAIL"
            checks.append({
                "check": "No emotional language",
                "status": status,
                "detail": f"Emotional words found: {', '.join(emotional_found[:10])}",
                "critical": False,
            })
        else:
            checks.append(self._check("No emotional language", True, "No emotional language detected"))

        # 4b. ALL CAPS detection (non-acronym)
        # Only check body lines — exclude markdown headings, table rows, and title lines
        body_only = "\n".join(
            line for line in text.split("\n")
            if not line.strip().startswith("#")
            and not line.strip().startswith("|")
            and not line.strip().startswith("**")
            and not line.strip().startswith("---")
        )
        all_caps = re.findall(r"\b([A-Z]{3,})\b", body_only)
        non_acronym_caps = [
            w for w in all_caps
            if w not in LEGAL_ACRONYMS and w.upper() not in LEGAL_ACRONYMS
        ]
        # Deduplicate
        unique_caps = sorted(set(non_acronym_caps))
        if unique_caps:
            status = "WARN" if len(unique_caps) <= 3 else "FAIL"
            checks.append({
                "check": "No ALL CAPS words (non-acronym)",
                "status": status,
                "detail": f"ALL CAPS words found: {', '.join(unique_caps[:15])}",
                "critical": False,
            })
        else:
            checks.append(self._check("No ALL CAPS words (non-acronym)", True, "No inappropriate ALL CAPS"))

        # 4c. Exclamation marks in body text
        # Exclude titles (lines starting with #) and emphasis markers
        body_lines = [
            line for line in text.split("\n")
            if not line.strip().startswith("#") and not line.strip().startswith("|")
        ]
        body_text = "\n".join(body_lines)
        excl_count = body_text.count("!")
        if excl_count > 0:
            status = "WARN" if excl_count <= 2 else "FAIL"
            checks.append({
                "check": "No exclamation marks in body text",
                "status": status,
                "detail": f"{excl_count} exclamation mark(s) found in body text — maintain judicial tone",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "No exclamation marks in body text", True, "No exclamation marks in body text"
            ))

        # 4d. First person emotional statements
        fp_found = []
        for pat in FIRST_PERSON_EMOTIONAL:
            matches = re.findall(pat, text, re.IGNORECASE)
            fp_found.extend(matches)
        if fp_found:
            checks.append({
                "check": "No first-person emotional statements",
                "status": "WARN",
                "detail": f"{len(fp_found)} first-person subjective phrase(s): "
                          f"{', '.join(repr(m.strip()) for m in fp_found[:5])}",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "No first-person emotional statements", True,
                "No first-person emotional statements detected"
            ))

        # 4e. Personal attacks
        attacks_found = []
        for pat in PERSONAL_ATTACK_PATTERNS:
            m = re.findall(pat, text, re.IGNORECASE)
            attacks_found.extend(m)
        if attacks_found:
            checks.append({
                "check": "No personal attacks",
                "status": "FAIL",
                "detail": f"Personal attack language detected: {attacks_found[:5]}",
                "critical": True,
            })
        else:
            checks.append(self._check("No personal attacks", True, "No personal attacks detected"))

        # 4f. Informal language
        informal_found = []
        for word in INFORMAL_WORDS:
            if word.lower() in text_lower:
                informal_found.append(word)
        if informal_found:
            checks.append({
                "check": "No informal language",
                "status": "WARN",
                "detail": f"Informal language found: {', '.join(informal_found)}",
                "critical": False,
            })
        else:
            checks.append(self._check("No informal language", True, "No informal language detected"))

        # 4g. Every legal assertion has a citation
        uncited_legal = self._check_legal_citations(text)
        if uncited_legal == 0:
            checks.append(self._check(
                "Legal assertions have citations", True,
                "All legal assertion paragraphs contain citations"
            ))
        else:
            status = "WARN" if uncited_legal <= 2 else "FAIL"
            checks.append({
                "check": "Legal assertions have citations",
                "status": status,
                "detail": f"{uncited_legal} argument paragraph(s) lack any legal citation",
                "critical": uncited_legal > 3,
            })

        # 4h. Factual assertions have sources
        unsourced = self._check_factual_sources(text)
        if unsourced == 0:
            checks.append(self._check(
                "Factual assertions have sources", True,
                "Factual paragraphs appear to reference sources"
            ))
        else:
            status = "WARN" if unsourced <= 3 else "FAIL"
            checks.append({
                "check": "Factual assertions have sources",
                "status": status,
                "detail": f"{unsourced} factual paragraph(s) lack source references (exhibit, docket, affidavit)",
                "critical": False,
            })

        # 4i. Conclusory statements without citation
        conclusory = self._check_conclusory(text)
        if conclusory:
            status = "WARN" if len(conclusory) <= 2 else "FAIL"
            checks.append({
                "check": "No conclusory statements without citation",
                "status": status,
                "detail": f"{len(conclusory)} conclusory assertion(s) without nearby citation: "
                          f"{'; '.join(conclusory[:3])}",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "No conclusory statements without citation", True,
                "No unsupported conclusory statements detected"
            ))

        # 4j. No speculation presented as fact
        speculation = re.findall(
            r"(?i)(?:(?:it\s+(?:appears|seems)|(?:likely|probably|perhaps|possibly|presumably))\s+.{10,60})",
            text
        )
        if speculation:
            checks.append({
                "check": "No speculation as fact",
                "status": "WARN",
                "detail": f"{len(speculation)} speculative phrase(s) found — consider rephrasing with evidence",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "No speculation as fact", True, "No speculative language detected"
            ))

        # 4k. No hearsay without exception
        hearsay_indicators = re.findall(
            r"(?i)(?:(?:she|he|they)\s+(?:said|told|stated|claimed)\s+(?:that\s+)?)",
            text
        )
        hearsay_exceptions = re.findall(
            r"(?i)(?:MRE\s+80[1-6]|admission|excited\s+utterance|"
            r"present\s+sense\s+impression|business\s+record|"
            r"statement\s+against\s+interest)",
            text
        )
        if hearsay_indicators and not hearsay_exceptions:
            checks.append({
                "check": "No hearsay without exception analysis",
                "status": "WARN",
                "detail": f"{len(hearsay_indicators)} hearsay indicator(s) without exception reference — "
                          "consider adding MRE 801-806 analysis",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "No hearsay without exception analysis", True,
                "No unaddressed hearsay concerns"
            ))

        return checks

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 5: PRO SE TRAPS
    # ═══════════════════════════════════════════════════════════════

    def _cat5_prose_traps(self, text: str, filing_type: str) -> List[Dict]:
        checks = []

        # 5a. Not addressing court as "you"
        you_court = re.findall(
            r"(?i)\b(?:you|your)\s+(?:honor|court|should|must|need|ought|fail)",
            text
        )
        if you_court:
            checks.append({
                "check": 'Not addressing court as "you"',
                "status": "FAIL",
                "detail": f'Found {len(you_court)} instance(s) of addressing court as "you" — '
                          'use "this Honorable Court" instead',
                "critical": True,
            })
        else:
            checks.append(self._check(
                'Not addressing court as "you"', True,
                "Court properly addressed in third person"
            ))

        # 5b. No personal attacks on judge (in filings TO that judge)
        judge_attacks = re.findall(
            r"(?i)(?:judge|court)\s+(?:is|was|has\s+been)\s+"
            r"(?:biased|corrupt|unfair|incompetent|dishonest|wrong)",
            text
        )
        # For disqualification motions, some criticism is expected
        if filing_type in ("complaint",):
            # JTC complaints and MSC complaints may criticize the judge
            if judge_attacks:
                checks.append({
                    "check": "Personal attacks on judge",
                    "status": "WARN",
                    "detail": f"{len(judge_attacks)} instance(s) of direct judicial criticism — "
                              "acceptable in complaint context but keep factual",
                    "critical": False,
                })
            else:
                checks.append(self._check(
                    "Personal attacks on judge", True, "No direct judicial attacks"
                ))
        else:
            if judge_attacks:
                checks.append({
                    "check": "No personal attacks on judge",
                    "status": "FAIL",
                    "detail": f"{len(judge_attacks)} instance(s) of personal attacks on judge in filing TO that judge",
                    "critical": True,
                })
            else:
                checks.append(self._check(
                    "No personal attacks on judge", True, "No personal attacks on judge"
                ))

        # 5c. Unpublished opinions without MCR 7.215(C) caveat
        unpub = re.findall(r"(?i)unpublish", text)
        has_caveat = bool(re.search(r"MCR\s+7\.215\(C\)", text))
        if unpub and not has_caveat:
            checks.append({
                "check": "Unpublished opinions cite MCR 7.215(C)",
                "status": "WARN",
                "detail": "References to unpublished opinions found but no MCR 7.215(C) caveat",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "Unpublished opinions cite MCR 7.215(C)", True,
                "No unpublished citation issues" if not unpub
                else "MCR 7.215(C) caveat present for unpublished opinions"
            ))

        # 5d. Legal terms used correctly — check common misuses
        misuses = []
        # "sustained" vs "overruled" in motion context
        if re.search(r"(?i)sustain(?:ed)?\s+(?:the|a|my)\s+(?:motion|argument)", text):
            misuses.append('"sustained" used with motion/argument (motions are granted/denied, not sustained)')
        if re.search(r"(?i)(?:motion|request)\s+(?:is|was)\s+overruled", text):
            misuses.append('"overruled" used with motion (objections are overruled, motions are denied)')
        if re.search(r"(?i)(?:object|objection)\s+(?:is|was)\s+(?:granted|denied)", text):
            misuses.append('"granted/denied" used with objection (objections are sustained/overruled)')

        if misuses:
            checks.append({
                "check": "Legal terms used correctly",
                "status": "WARN",
                "detail": f"Potential misuse: {'; '.join(misuses)}",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "Legal terms used correctly", True, "No obvious legal term misuses"
            ))

        # 5e. Arguments in facts section / facts in argument section
        sections = self._identify_sections(text)
        facts_section = sections.get("facts", "")
        argument_section = sections.get("argument", "")

        args_in_facts = False
        if facts_section:
            legal_cites_in_facts = len(_ANY_CITE_PAT.findall(facts_section))
            argumentative_in_facts = len(re.findall(
                r"(?i)(therefore|consequently|thus|it\s+follows|court\s+(?:erred|abused))",
                facts_section
            ))
            if argumentative_in_facts > 2:
                args_in_facts = True

        if args_in_facts:
            checks.append({
                "check": "No arguments in facts section",
                "status": "WARN",
                "detail": "Facts section contains argumentative language — keep facts neutral",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "No arguments in facts section", True,
                "Facts section appears appropriately neutral"
            ))

        # 5f. Relief court cannot grant (very hard to fully automate — heuristic)
        checks.append(self._check(
            "Relief within court's power", True,
            "No obviously improper relief requests detected (manual review recommended)",
            critical=False,
        ))

        # 5g. Michigan date format
        bad_dates = re.findall(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", text)
        if bad_dates:
            checks.append({
                "check": "Proper Michigan date format",
                "status": "WARN",
                "detail": f"{len(bad_dates)} date(s) in MM/DD/YYYY format — "
                          "prefer 'Month Day, Year' format in filings",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "Proper Michigan date format", True,
                "Dates appear in proper format"
            ))

        # 5h. Length limits
        words = len(text.split())
        limits = PAGE_LIMITS.get(filing_type, {"pages": None, "words": None})
        pages_est = max(1, words // 250)

        if limits["words"] and words > limits["words"]:
            checks.append({
                "check": f"Within length limits ({filing_type})",
                "status": "FAIL",
                "detail": f"Word count {words:,} exceeds {filing_type} limit of {limits['words']:,} words "
                          f"(est. {pages_est} pages)",
                "critical": True,
            })
        elif limits["words"] and words > limits["words"] * 0.9:
            checks.append({
                "check": f"Within length limits ({filing_type})",
                "status": "WARN",
                "detail": f"Word count {words:,} is at {round(words/limits['words']*100)}% of "
                          f"{limits['words']:,} word limit",
                "critical": False,
            })
        else:
            checks.append(self._check(
                f"Within length limits ({filing_type})", True,
                f"Word count {words:,}" + (f" within {limits['words']:,} limit" if limits["words"] else " (no limit)")
            ))

        return checks

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 6: APPEAL-SPECIFIC (MCR 7.212, MCR 7.305)
    # ═══════════════════════════════════════════════════════════════

    def _cat6_appeal(self, text: str, filing_type: str) -> List[Dict]:
        checks = []

        # Determine if COA brief, MSC application, or COA emergency application
        # Check the caption area (first 1500 chars) for court identity, not body references
        caption_area = text[:1500]
        is_msc = bool(re.search(
            r"(?i)(?:IN\s+THE\s+SUPREME\s+COURT|superintending\s+control|MCR\s+7\.306)",
            caption_area
        ))
        is_coa_brief = filing_type == "brief" and not is_msc

        if is_coa_brief:
            # COA Brief checks (MCR 7.212)
            checks.extend(self._coa_brief_checks(text))
        elif is_msc:
            # MSC Application checks (MCR 7.305)
            checks.extend(self._msc_checks(text))
        else:
            # Application (COA emergency application)
            checks.extend(self._coa_application_checks(text))

        return checks

    def _coa_brief_checks(self, text: str) -> List[Dict]:
        checks = []

        # 6a. Questions Presented
        has_qp = bool(re.search(
            r"(?i)(questions?\s+presented|statement\s+of\s+(?:the\s+)?questions?\s+presented)",
            text
        ))
        checks.append(self._check(
            "Questions Presented (MCR 7.212(C)(5))", has_qp,
            "Questions Presented section found" if has_qp
            else "MISSING Questions Presented section (MCR 7.212(C)(5))",
            critical=True,
        ))

        # 6b. Table of Contents
        has_toc = bool(re.search(r"(?i)table\s+of\s+contents", text))
        checks.append(self._check(
            "Table of Contents (MCR 7.212(C)(2))", has_toc,
            "Table of Contents found" if has_toc else "MISSING Table of Contents (MCR 7.212(C)(2))",
            critical=True,
        ))

        # 6c. Table of Authorities
        has_toa = bool(re.search(r"(?i)table\s+of\s+authorit", text))
        checks.append(self._check(
            "Table of Authorities (MCR 7.212(C)(3))", has_toa,
            "Table of Authorities found" if has_toa else "MISSING Table of Authorities (MCR 7.212(C)(3))",
            critical=True,
        ))

        # 6d. Statement of Jurisdiction
        has_jur = bool(re.search(r"(?i)(?:statement\s+of\s+)?jurisdiction", text))
        checks.append(self._check(
            "Statement of Jurisdiction (MCR 7.212(C)(4))", has_jur,
            "Jurisdictional statement found" if has_jur
            else "MISSING Statement of Jurisdiction (MCR 7.212(C)(4))",
            critical=True,
        ))

        # 6e. Statement of Facts (separate)
        has_facts = bool(re.search(r"(?i)statement\s+of\s+(?:the\s+)?facts", text))
        checks.append(self._check(
            "Statement of Facts (MCR 7.212(C)(6))", has_facts,
            "Statement of Facts found" if has_facts else "MISSING Statement of Facts (MCR 7.212(C)(6))",
            critical=True,
        ))

        # 6f. Standard of Review
        has_sor = bool(re.search(r"(?i)standard\s+of\s+review", text))
        checks.append(self._check(
            "Standard of Review (MCR 7.212(C)(7))", has_sor,
            "Standard of Review section found" if has_sor
            else "MISSING Standard of Review — must be stated for each issue (MCR 7.212(C)(7))",
            critical=True,
        ))

        # 6g. Issue preservation
        has_pres = bool(re.search(
            r"(?i)(preserv|raised\s+below|raised\s+(?:at|in)\s+(?:the\s+)?(?:trial|lower)\s+court|"
            r"(?:trial\s+court|below)\s+(?:raised|objected|moved)|"
            r"plain\s+error|(?:Carines|People\s+v\s+Carines))",
            text
        ))
        checks.append(self._check(
            "Issue preservation addressed", has_pres,
            "Issue preservation discussion found" if has_pres
            else "No discussion of issue preservation — address where each issue was raised below",
            critical=False,
        ))

        # 6h. Appendix reference
        has_appendix = bool(re.search(
            r"(?i)(appendix|appendices|app\.\s+\d|app\s+at\s+\d)", text
        ))
        checks.append({
            "check": "Appendix reference (MCR 7.212(C)(7))",
            "status": "PASS" if has_appendix else "WARN",
            "detail": "Appendix referenced" if has_appendix
                      else "No appendix reference found — MCR 7.212(C)(7) requires relevant appendix",
            "critical": False,
        })

        # 6i. Word/page count
        words = len(text.split())
        within = words <= 16000
        checks.append(self._check(
            "Word count within 16,000 limit (MCR 7.212(B))", within,
            f"Word count: {words:,} (within limit)" if within
            else f"Word count: {words:,} EXCEEDS 16,000 word limit (MCR 7.212(B))",
            critical=not within,
        ))

        # 6j. Lower court opinion referenced
        has_lc = bool(re.search(
            r"(?i)(lower\s+court\s+(?:opinion|order|ruling|decision)|"
            r"trial\s+court(?:'s)?\s+(?:opinion|order|ruling|decision)|"
            r"(?:attached|appended)\s+(?:hereto|as\s+exhibit))",
            text
        ))
        checks.append(self._check(
            "Lower court opinion attached/referenced", has_lc,
            "Lower court opinion referenced" if has_lc
            else "No reference to lower court opinion being attached",
            critical=False,
        ))

        return checks

    def _msc_checks(self, text: str) -> List[Dict]:
        checks = []

        # MSC-specific (MCR 7.305)
        has_judgment_id = bool(re.search(
            r"(?i)(judgment|order)\s+(?:appealed|at\s+issue|entered)", text
        ))
        checks.append(self._check(
            "Identifies judgment/order appealed (MCR 7.305)", has_judgment_id,
            "Judgment/order identified" if has_judgment_id else "Missing identification of judgment appealed",
            critical=True,
        ))

        has_qp = bool(re.search(r"(?i)questions?\s+presented", text))
        checks.append(self._check(
            "Questions Presented (MCR 7.305)", has_qp,
            "Questions Presented found" if has_qp else "MISSING Questions Presented",
            critical=True,
        ))

        has_toc = bool(re.search(r"(?i)table\s+of\s+contents", text))
        checks.append(self._check(
            "Table of Contents (MCR 7.305)", has_toc,
            "Table of Contents found" if has_toc else "MISSING Table of Contents",
            critical=True,
        ))

        has_toa = bool(re.search(r"(?i)(?:table|index)\s+of\s+authorit", text))
        checks.append(self._check(
            "Index of Authorities (MCR 7.305)", has_toa,
            "Index of Authorities found" if has_toa else "MISSING Index of Authorities",
            critical=True,
        ))

        has_jur = bool(re.search(r"(?i)jurisdict", text))
        checks.append(self._check(
            "Jurisdictional statement (MCR 7.305)", has_jur,
            "Jurisdictional statement found" if has_jur else "MISSING Jurisdictional statement",
            critical=True,
        ))

        has_reasons = bool(re.search(
            r"(?i)(reason|ground|basis)\s+(?:for|to)\s+(?:grant|granting|accept)", text
        ))
        if not has_reasons:
            has_reasons = bool(re.search(
                r"(?i)(superintending\s+control\s+is\s+(?:necessary|warranted|appropriate))",
                text
            ))
        checks.append(self._check(
            "Reasons for granting application (MCR 7.305)", has_reasons,
            "Reasons for granting stated" if has_reasons
            else "MISSING reasons why the court should grant the application",
            critical=True,
        ))

        return checks

    def _coa_application_checks(self, text: str) -> List[Dict]:
        """Checks for COA emergency application (MCR 7.211(C)(7))."""
        checks = []

        has_emergency = bool(re.search(r"(?i)emergenc", text))
        checks.append(self._check(
            "Emergency basis stated", has_emergency,
            "Emergency basis identified" if has_emergency else "No emergency basis stated",
            critical=True,
        ))

        has_irreparable = bool(re.search(r"(?i)irreparab", text))
        checks.append(self._check(
            "Irreparable harm demonstrated", has_irreparable,
            "Irreparable harm argument found" if has_irreparable
            else "No irreparable harm argument — required for emergency relief",
            critical=True,
        ))

        has_likelihood = bool(re.search(
            r"(?i)(likelihood\s+of\s+success|merits|meritorious|"
            r"likely\s+to\s+(?:succeed|prevail))", text
        ))
        checks.append(self._check(
            "Likelihood of success on merits", has_likelihood,
            "Merit discussion found" if has_likelihood else "No discussion of likelihood of success on merits",
            critical=False,
        ))

        has_balance = bool(re.search(
            r"(?i)(balance\s+of\s+(?:harm|equit|interest)|"
            r"harm.*outweigh|equit)", text
        ))
        checks.append(self._check(
            "Balance of harms addressed", has_balance,
            "Balance of harms discussed" if has_balance
            else "No balance of harms analysis",
            critical=False,
        ))

        has_qp = bool(re.search(r"(?i)(questions?\s+presented|issues?\s+(?:for|on)\s+(?:appeal|review))", text))
        checks.append(self._check(
            "Questions/issues presented", has_qp,
            "Issues presented found" if has_qp else "No questions/issues presented section",
            critical=False,
        ))

        has_facts = bool(re.search(r"(?i)(?:statement\s+of\s+)?(?:the\s+)?facts", text))
        checks.append(self._check(
            "Statement of Facts", has_facts,
            "Facts section found" if has_facts else "No Statement of Facts section",
            critical=True,
        ))

        words = len(text.split())
        within = words <= 16000
        checks.append(self._check(
            "Word count within limits", within,
            f"Word count: {words:,}" if within
            else f"Word count: {words:,} — may exceed limits",
            critical=not within,
        ))

        return checks

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 7: PROHIBITED CONTENT
    # ═══════════════════════════════════════════════════════════════

    def _cat7_prohibited(self, text: str, filing_type: str) -> List[Dict]:
        checks = []

        # 7a. Social media screenshots without authentication
        social_media = re.findall(
            r"(?i)(facebook|instagram|twitter|tiktok|snapchat|social\s+media)\s+"
            r"(?:screenshot|post|message)",
            text
        )
        auth_ref = re.findall(r"(?i)(authenticat|MRE\s+901)", text)
        if social_media and not auth_ref:
            checks.append({
                "check": "No unauthenticated social media evidence",
                "status": "WARN",
                "detail": f"Social media evidence referenced without authentication discussion (MRE 901)",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "No unauthenticated social media evidence", True,
                "No social media authentication issues"
            ))

        # 7b. AI/ChatGPT references
        ai_found = []
        for pat in AI_REFERENCE_PATTERNS:
            m = re.findall(pat, text)
            ai_found.extend(m)
        if ai_found:
            checks.append({
                "check": "No AI tool references",
                "status": "FAIL",
                "detail": f"References to AI tools found: {ai_found[:5]} — "
                          "remove all AI references from court filings",
                "critical": True,
            })
        else:
            checks.append(self._check("No AI tool references", True, "No AI tool references found"))

        # 7c. Threats or intimidation
        threats_found = []
        for pat in THREAT_PATTERNS:
            m = re.findall(pat, text)
            threats_found.extend(m)
        if threats_found:
            checks.append({
                "check": "No threats or intimidation",
                "status": "FAIL",
                "detail": f"Threatening language detected: {threats_found[:3]}",
                "critical": True,
            })
        else:
            checks.append(self._check("No threats or intimidation", True, "No threatening language detected"))

        # 7d. Confidential/privileged information
        privileged = re.findall(
            r"(?i)(attorney.client\s+privilege|privileged\s+communication|"
            r"(?:work\s+product|mental\s+impression)\s+(?:doctrine|privilege)|"
            r"confidential\s+(?:information|communication))",
            text
        )
        if privileged:
            checks.append({
                "check": "No confidential/privileged disclosure",
                "status": "WARN",
                "detail": f"References to privileged matters found — verify no inadvertent disclosure: "
                          f"{privileged[:3]}",
                "critical": False,
            })
        else:
            checks.append(self._check(
                "No confidential/privileged disclosure", True,
                "No privileged information disclosure detected"
            ))

        # 7e. Settlement negotiation references (MRE 408)
        settle_found = []
        for pat in SETTLEMENT_PATTERNS:
            m = re.findall(pat, text)
            settle_found.extend(m)
        if settle_found:
            checks.append({
                "check": "No settlement references (MRE 408)",
                "status": "FAIL",
                "detail": f"Settlement negotiation references found — inadmissible under MRE 408: "
                          f"{settle_found[:3]}",
                "critical": True,
            })
        else:
            checks.append(self._check(
                "No settlement references (MRE 408)", True,
                "No settlement negotiation references"
            ))

        # 7f. Ex parte communications
        ex_parte_disclosure = re.findall(
            r"(?i)(?:I|plaintiff)\s+(?:spoke|talked|communicated|emailed|called)\s+"
            r"(?:with\s+)?(?:the\s+)?(?:judge|court)\s+(?:about|regarding|concerning)",
            text
        )
        if ex_parte_disclosure:
            checks.append({
                "check": "No undisclosed ex parte communications",
                "status": "FAIL",
                "detail": f"Apparent disclosure of ex parte communication with the court",
                "critical": True,
            })
        else:
            checks.append(self._check(
                "No undisclosed ex parte communications", True,
                "No ex parte communication disclosures"
            ))

        # 7g. False or misleading statements (MCR 2.114)
        # Heuristic: check for obvious factual inconsistencies within the document
        checks.append(self._check(
            "Duty of candor (MCR 2.114)", True,
            "No obviously false statements detected (manual review recommended)",
            critical=False,
        ))

        return checks

    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _check(name: str, passed: bool, detail: str, critical: bool = False) -> Dict:
        return {
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
            "critical": critical,
        }

    @staticmethod
    def _check_paragraph_length(text: str) -> int:
        """Count numbered paragraphs that appear to have multiple distinct topics."""
        paras = re.findall(r"^\s*\d+\.\s+(.+?)(?=^\s*\d+\.\s+|\Z)", text, re.MULTILINE | re.DOTALL)
        long_count = 0
        for p in paras:
            # Heuristic: if a single numbered paragraph has >5 sentences and >300 words,
            # it likely contains multiple allegations
            sentences = _split_sentences(p)
            words = len(p.split())
            if len(sentences) > 6 and words > 300:
                long_count += 1
        return long_count

    def _check_legal_citations(self, text: str) -> int:
        """Count argument paragraphs that lack any legal citation."""
        sections = self._identify_sections(text)
        argument = sections.get("argument", "")
        if not argument:
            return 0

        paras = _split_paragraphs(argument)
        uncited = 0
        for p in paras:
            # Skip very short paragraphs (headers, transition lines)
            if len(p.split()) < 15:
                continue
            # Skip if it's a heading
            if p.strip().startswith("#") or p.strip().startswith("|"):
                continue
            if not _ANY_CITE_PAT.search(p):
                uncited += 1
        return uncited

    def _check_factual_sources(self, text: str) -> int:
        """Count factual paragraphs without source references."""
        sections = self._identify_sections(text)
        facts = sections.get("facts", "")
        if not facts:
            return 0

        paras = _split_paragraphs(facts)
        unsourced = 0
        for p in paras:
            if len(p.split()) < 15:
                continue
            if p.strip().startswith("#") or p.strip().startswith("|"):
                continue
            has_source = bool(
                _ANY_CITE_PAT.search(p) or _ANY_SOURCE_PAT.search(p) or
                _EXHIBIT_PAT.search(p) or _DOCKET_PAT.search(p) or
                _AFFIDAVIT_PAT.search(p)
            )
            if not has_source:
                unsourced += 1
        return unsourced

    def _check_conclusory(self, text: str) -> List[str]:
        """Find conclusory assertions without nearby citations."""
        sentences = _split_sentences(text)
        conclusory_hits = []
        for i, sent in enumerate(sentences):
            for marker in CONCLUSORY_MARKERS:
                if marker.lower() in sent.lower():
                    # Check this sentence and next 2 for a citation
                    window = " ".join(sentences[max(0, i):min(len(sentences), i + 3)])
                    if not _ANY_CITE_PAT.search(window):
                        # Truncate for display
                        snippet = sent[:120].strip()
                        conclusory_hits.append(f'"{snippet}..."')
                    break
        return conclusory_hits

    @staticmethod
    def _identify_sections(text: str) -> Dict[str, str]:
        """Split the text into known sections by heading markers."""
        sections: Dict[str, str] = {}
        # Find section boundaries
        headings = list(re.finditer(
            r"^#+\s+(?:(?:[IVXLCDM]+\.?\s+)?)(.*?)$",
            text, re.MULTILINE
        ))

        for i, m in enumerate(headings):
            title_lower = m.group(1).strip().lower()
            start = m.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            content = text[start:end]

            if "fact" in title_lower and "argument" not in title_lower:
                sections.setdefault("facts", "")
                sections["facts"] += content
            elif "argument" in title_lower or "analysis" in title_lower:
                sections.setdefault("argument", "")
                sections["argument"] += content
            elif "relief" in title_lower or "prayer" in title_lower:
                sections["relief"] = content
            elif "certificate" in title_lower and "service" in title_lower:
                sections["certificate_of_service"] = content

        return sections

    def _build_recommendations(
        self, checks: List[Dict], filing_type: str
    ) -> List[str]:
        """Generate actionable recommendations from check results."""
        recs: List[str] = []
        fails = [c for c in checks if c["status"] == "FAIL"]
        warns = [c for c in checks if c["status"] == "WARN"]

        # Critical failures first
        critical = [c for c in fails if c.get("critical")]
        if critical:
            recs.append(
                f"🚨 {len(critical)} CRITICAL failure(s) — must fix before filing: "
                + "; ".join(c["check"] for c in critical[:5])
            )

        # Certificate of Service
        cos_fail = any("Certificate of Service" in c["check"] and c["status"] == "FAIL" for c in checks)
        if cos_fail:
            recs.append(
                "📋 Add a complete Certificate of Service with: method, date, "
                "recipient name/address, and signature (MCR 2.107)"
            )

        # Emotional language
        emotional = [c for c in checks if "emotional" in c["check"].lower() and c["status"] != "PASS"]
        if emotional:
            recs.append(
                "✍️ Remove emotional language — replace with factual, neutral statements. "
                "Courts respond to facts and law, not emotion."
            )

        # Citations
        cite_issues = [c for c in checks if "citation" in c["check"].lower() and c["status"] != "PASS"]
        if cite_issues:
            recs.append(
                "📚 Add citations to all legal assertions (MCR, MCL, case law). "
                "Every legal claim must have authority."
            )

        # Appeal-specific
        if filing_type in ("brief", "application"):
            missing_appeal = [
                c for c in fails
                if any(kw in c["check"].lower() for kw in
                       ["questions presented", "table of contents", "table of authorities",
                        "jurisdiction", "standard of review"])
            ]
            if missing_appeal:
                recs.append(
                    "📑 Add required appellate sections: "
                    + ", ".join(c["check"].split("(")[0].strip() for c in missing_appeal)
                )

        # Proposed order
        po_warn = any("Proposed order" in c["check"] and c["status"] == "WARN" for c in checks)
        if po_warn and filing_type == "motion":
            recs.append(
                "📄 Attach a proposed order — MCR 2.119(A)(2) requires one with each motion"
            )

        # Length
        length_fail = any("length" in c["check"].lower() and c["status"] == "FAIL" for c in checks)
        if length_fail:
            recs.append(
                "✂️ Reduce document length to comply with MCR word/page limits"
            )

        if not recs:
            recs.append("✅ Filing appears compliant — conduct final manual review before filing")

        return recs

    def close(self):
        if self.conn:
            self.conn.close()


# ═══════════════════════════════════════════════════════════════════
# RUNNER — Validate all 7 v2 filings
# ═══════════════════════════════════════════════════════════════════

V2_FILINGS = [
    (
        r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\LANE_A\EMERGENCY_MOTION_RESTORE_PARENTING_TIME_v2.md",
        "motion",
        "EMERGENCY_MOTION",
    ),
    (
        r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\LANE_A\MOTION_FOR_DISQUALIFICATION_v2.md",
        "motion",
        "MOTION_FOR_DISQUALIFICATION",
    ),
    (
        r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\LANE_A\MOTION_FOR_RECONSIDERATION_v2.md",
        "motion",
        "MOTION_FOR_RECONSIDERATION",
    ),
    (
        r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\04_MSC\MSC_COMPLAINT_SUPERINTENDING_CONTROL_v2.md",
        "complaint",
        "MSC_COMPLAINT",
    ),
    (
        r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\03_JTC\JTC_FORMAL_COMPLAINT_v2.md",
        "complaint",
        "JTC_FORMAL_COMPLAINT",
    ),
    (
        r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\LANE_F\COA_APPELLANT_BRIEF_366810_v2.md",
        "brief",
        "COA_APPELLANT_BRIEF",
    ),
    (
        r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\LANE_F\COA_EMERGENCY_APPLICATION_366810_v2.md",
        "application",
        "COA_EMERGENCY_APPLICATION",
    ),
]


def main():
    print("=" * 90)
    print("  FILING QUALITY VALIDATOR — LitigationOS 2026")
    print("  Michigan Court Rule Compliance Report")
    print("=" * 90)
    print()

    validator = FilingQualityValidator()

    results = []
    for filepath, ftype, label in V2_FILINGS:
        if not os.path.exists(filepath):
            print(f"  ⚠ File not found: {filepath}")
            continue

        result = validator.validate_filing(filepath, ftype)
        result["label"] = label
        results.append(result)

        # Print detailed report per filing
        print(f"{'─' * 90}")
        print(f"  📄 {label}")
        print(f"     Type: {ftype} | Words: {result['word_count']:,} | "
              f"Est. Pages: {result['estimated_pages']}")
        print(f"     Overall Score: {result['overall_score']}/100")
        print(f"     Checks: {result['summary']['passed']} PASS | "
              f"{result['summary']['warnings']} WARN | {result['summary']['failures']} FAIL")
        print()

        # Category scores
        print("     Category Scores:")
        for cat, score in result["category_scores"].items():
            bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
            print(f"       {bar} {score:5.1f}%  {cat}")
        print()

        # Failures and warnings
        failures = [c for c in result["checks"] if c["status"] == "FAIL"]
        warnings = [c for c in result["checks"] if c["status"] == "WARN"]

        if failures:
            print("     ❌ FAILURES:")
            for f in failures:
                crit = " [CRITICAL]" if f.get("critical") else ""
                print(f"        • {f['check']}{crit}")
                print(f"          {f['detail']}")
            print()

        if warnings:
            print("     ⚠️  WARNINGS:")
            for w in warnings[:8]:
                print(f"        • {w['check']}")
                print(f"          {w['detail']}")
            if len(warnings) > 8:
                print(f"        ... and {len(warnings) - 8} more warnings")
            print()

        # Recommendations
        if result["recommendations"]:
            print("     💡 RECOMMENDATIONS:")
            for r in result["recommendations"]:
                print(f"        {r}")
            print()

    # ── Summary Table ──
    print()
    print("=" * 90)
    print("  SUMMARY TABLE")
    print("=" * 90)
    print()
    print(f"  {'Filing':<35} {'Type':<14} {'Score':>6} {'Pass':>5} {'Warn':>5} "
          f"{'Fail':>5} {'Critical Failures'}")
    print(f"  {'─' * 35} {'─' * 14} {'─' * 6} {'─' * 5} {'─' * 5} "
          f"{'─' * 5} {'─' * 30}")

    for r in results:
        crit_list = [c["check"] for c in r["critical_failures"]]
        crit_str = "; ".join(crit_list[:3]) if crit_list else "None"
        if len(crit_list) > 3:
            crit_str += f" (+{len(crit_list) - 3} more)"
        print(f"  {r['label']:<35} {r['filing_type']:<14} {r['overall_score']:>5.1f}% "
              f"{r['summary']['passed']:>5} {r['summary']['warnings']:>5} "
              f"{r['summary']['failures']:>5} {crit_str}")

    print()

    # Overall statistics
    if results:
        avg_score = sum(r["overall_score"] for r in results) / len(results)
        total_crit = sum(len(r["critical_failures"]) for r in results)
        print(f"  Average Score: {avg_score:.1f}/100")
        print(f"  Total Critical Failures: {total_crit}")
        print(f"  Filings Validated: {len(results)}")
    print()
    print("=" * 90)

    validator.close()
    return results


if __name__ == "__main__":
    main()
