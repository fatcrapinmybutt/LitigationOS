"""
Evidence Admissibility Scorer — MBP LitigationOS 2026
MRE-based admissibility analysis for Pigors v. Watson.

Analyzes evidence under Michigan Rules of Evidence (MRE 401-902)
and returns structured admissibility scores with objection predictions,
cure suggestions, and foundation checklists.

Stdlib only: sqlite3, re, json, collections, datetime.
"""

import sqlite3
import re
import json
from collections import OrderedDict
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH_DEFAULT = r"C:\Users\andre\LitigationOS\litigation_context.db"

PARTY_OPPONENT = "Tiffany Watson"
JUDGE = "Judge McNeill"

# MRE hearsay exception catalogue
HEARSAY_EXCEPTIONS = OrderedDict([
    ("MRE 801(d)(1)", "Prior inconsistent statement under oath"),
    ("MRE 801(d)(2)", "Admission by party-opponent"),
    ("MRE 803(1)", "Present sense impression"),
    ("MRE 803(2)", "Excited utterance"),
    ("MRE 803(3)", "Then-existing mental/emotional/physical condition"),
    ("MRE 803(4)", "Statement for medical diagnosis or treatment"),
    ("MRE 803(5)", "Recorded recollection"),
    ("MRE 803(6)", "Business records"),
    ("MRE 803(8)", "Public records and reports"),
    ("MRE 804(b)(1)", "Former testimony"),
    ("MRE 807", "Residual exception"),
])

# Keywords that signal specific hearsay exceptions
_EXCEPTION_SIGNALS = {
    "MRE 801(d)(1)": [
        "under oath", "testified", "deposition", "transcript", "sworn",
        "hearing", "prior testimony",
    ],
    "MRE 801(d)(2)": [
        "party", "opponent", "admission", "defendant said", "she said",
        "tiffany", "watson", "respondent",
    ],
    "MRE 803(1)": [
        "while perceiving", "immediately after", "present sense",
        "contemporaneous",
    ],
    "MRE 803(2)": [
        "excited", "startling", "911", "emergency", "scared", "screamed",
        "shocked", "just happened",
    ],
    "MRE 803(3)": [
        "felt", "feeling", "believed", "intended", "planned", "afraid",
        "wanted", "state of mind", "emotion",
    ],
    "MRE 803(4)": [
        "doctor", "medical", "diagnosis", "treatment", "hospital",
        "therapist", "counselor", "physician",
    ],
    "MRE 803(5)": [
        "recorded", "memo", "note made at the time", "fresh in memory",
    ],
    "MRE 803(6)": [
        "business record", "kept in the regular course", "regular practice",
        "custodian", "routine", "log", "ledger", "invoice",
    ],
    "MRE 803(8)": [
        "public record", "government", "court order", "official",
        "agency", "report filed", "certified",
    ],
    "MRE 804(b)(1)": [
        "former testimony", "unavailable", "prior proceeding",
    ],
    "MRE 807": [
        "trustworthy", "equivalent guarantees", "residual",
    ],
}

# Common objection templates
_OBJECTION_TEMPLATES = [
    {
        "objection": "Hearsay",
        "basis": "MRE 801-802",
        "keywords": [
            "said", "told", "stated", "wrote", "texted", "messaged",
            "he said", "she said", "they said",
        ],
    },
    {
        "objection": "Relevance",
        "basis": "MRE 401-402",
        "keywords": [
            "unrelated", "collateral", "tangential",
        ],
    },
    {
        "objection": "Unfair prejudice outweighs probative value",
        "basis": "MRE 403",
        "keywords": [
            "inflammatory", "gruesome", "emotional", "shocking",
            "prejudicial",
        ],
    },
    {
        "objection": "Lack of foundation / authentication",
        "basis": "MRE 901",
        "keywords": [
            "screenshot", "printout", "copy", "photo", "video",
            "unauthenticated", "text message",
        ],
    },
    {
        "objection": "Speculation / Lack of personal knowledge",
        "basis": "MRE 602",
        "keywords": [
            "I think", "maybe", "probably", "I believe", "speculate",
            "guess", "assume",
        ],
    },
    {
        "objection": "Improper character evidence",
        "basis": "MRE 404(a)",
        "keywords": [
            "always does", "type of person", "character", "reputation",
            "propensity", "habit",
        ],
    },
    {
        "objection": "Best evidence rule — original required",
        "basis": "MRE 1002",
        "keywords": [
            "copy", "screenshot", "printout", "duplicate",
        ],
    },
    {
        "objection": "Privilege",
        "basis": "MRE 501",
        "keywords": [
            "attorney", "lawyer", "counselor", "therapist",
            "privilege", "confidential",
        ],
    },
]

# Foundation checklists by evidence type
_FOUNDATION_CHECKLISTS = {
    "text_message": {
        "label": "Text Messages / SMS / Chat",
        "steps": [
            "Authenticate: witness with knowledge identifies the phone number or account (MRE 901(b)(1))",
            "Identify sender/receiver and relationship to the case",
            "Show the message is a fair and accurate representation (MRE 901(b)(4))",
            "Assess hearsay: offered for truth of matter asserted? If so, identify exception",
            "Check MRE 801(d)(2) — if sender is opposing party, it is an admission",
            "Relevance: tie to a fact of consequence under MRE 401",
            "Preserve metadata (timestamps, phone numbers) for authentication",
        ],
        "authority": ["MRE 901(b)(1)", "MRE 901(b)(4)", "MRE 801(d)(2)", "MRE 401"],
    },
    "court_order": {
        "label": "Court Orders / Judgments",
        "steps": [
            "Self-authenticating under MRE 902(1) — domestic public document under seal",
            "Obtain certified copy from clerk if original unavailable",
            "Judicial notice may apply under MRE 201 for court's own orders",
            "Generally not hearsay — legal operative documents, not offered for truth",
            "If offered for truth of findings, check MRE 803(8) public records exception",
        ],
        "authority": ["MRE 902(1)", "MRE 201", "MRE 803(8)"],
    },
    "transcript": {
        "label": "Deposition / Hearing Transcripts",
        "steps": [
            "Obtain certified copy from court reporter (MRE 902(4))",
            "Prior testimony under oath — MRE 801(d)(1) if inconsistent with current testimony",
            "Former testimony exception — MRE 804(b)(1) if witness unavailable",
            "Identify specific pages and line numbers for the record",
            "Verify transcript accuracy if challenged",
        ],
        "authority": ["MRE 902(4)", "MRE 801(d)(1)", "MRE 804(b)(1)"],
    },
    "photo": {
        "label": "Photographs / Videos",
        "steps": [
            "Authenticate via witness with knowledge: 'fair and accurate depiction' (MRE 901(b)(1))",
            "Identify what is depicted, when/where taken",
            "Establish chain of custody if digital (no alterations)",
            "Check MRE 403 — prejudicial effect vs. probative value",
            "If screenshot of digital content, authenticate underlying content too",
        ],
        "authority": ["MRE 901(b)(1)", "MRE 403"],
    },
    "business_record": {
        "label": "Business Records",
        "steps": [
            "Custodian or qualified witness must testify to foundation (MRE 803(6))",
            "Show record was made at or near the time of the event",
            "Show record was made by person with knowledge (or from info transmitted by such person)",
            "Show record was kept in the regular course of business",
            "Show it was regular practice to make such a record",
            "Alternative: certification under MCR 2.306(G) in lieu of live testimony",
        ],
        "authority": ["MRE 803(6)", "MCR 2.306(G)"],
    },
    "email": {
        "label": "Email Correspondence",
        "steps": [
            "Authenticate: identify sender via email address, content, context (MRE 901(b)(4))",
            "Show witness recognizes the email or can identify distinctive characteristics",
            "Preserve headers and metadata for authentication",
            "Hearsay analysis: if offered for truth, identify applicable exception",
            "If from opposing party, MRE 801(d)(2) admission by party-opponent",
        ],
        "authority": ["MRE 901(b)(4)", "MRE 801(d)(2)"],
    },
    "affidavit": {
        "label": "Affidavits / Sworn Statements",
        "steps": [
            "Verify proper notarization and oath (MCR 2.114)",
            "Self-authenticating if acknowledged before notary (MRE 902(8))",
            "Generally inadmissible hearsay at trial — use for motions only",
            "At trial, affiant must testify live; affidavit is not a substitute",
            "Exception: summary disposition under MCR 2.116 allows affidavit support",
        ],
        "authority": ["MRE 902(8)", "MCR 2.114", "MCR 2.116"],
    },
    "social_media": {
        "label": "Social Media Posts",
        "steps": [
            "Authenticate: show post is attributable to the claimed author (MRE 901(b)(4))",
            "Screenshot plus URL, timestamp, account name as minimum",
            "Testimony from someone who saw the post on the platform",
            "Platform records or metadata if available",
            "Hearsay: if opponent's post, MRE 801(d)(2) party admission",
            "MRE 403 balancing if content is inflammatory",
        ],
        "authority": ["MRE 901(b)(4)", "MRE 801(d)(2)", "MRE 403"],
    },
}

# Map common evidence_category / source_type values to foundation keys
_CATEGORY_TO_FOUNDATION = {
    "text": "text_message",
    "text_message": "text_message",
    "sms": "text_message",
    "chat": "text_message",
    "message": "text_message",
    "court_order": "court_order",
    "order": "court_order",
    "judgment": "court_order",
    "transcript": "transcript",
    "deposition": "transcript",
    "hearing": "transcript",
    "photo": "photo",
    "photograph": "photo",
    "video": "photo",
    "image": "photo",
    "screenshot": "photo",
    "business_record": "business_record",
    "financial": "business_record",
    "invoice": "business_record",
    "receipt": "business_record",
    "email": "email",
    "affidavit": "affidavit",
    "sworn_statement": "affidavit",
    "social_media": "social_media",
    "facebook": "social_media",
    "instagram": "social_media",
}

# Best-interest factors for relevance boost in custody context
_BEST_INTEREST_KEYWORDS = [
    "love", "affection", "emotional ties",  # (a)
    "capacity to give love",  # (b)
    "food", "clothing", "medical", "health",  # (c)
    "established custodial environment",  # (d)
    "moral fitness",  # (e)
    "mental health", "physical health",  # (f)
    "school", "community",  # (g)
    "preference of the child",  # (h)
    "facilitate", "relationship", "encourage",  # (i)
    "alienat", "interfere", "obstruct", "withhold",  # (j) — parental alienation
    "domestic violence",  # (k)
    "any other factor",  # (l)
]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _kw_score(text, keywords):
    """Return fraction of keywords found in text (case-insensitive)."""
    if not text:
        return 0.0
    lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in lower)
    return hits / max(len(keywords), 1)


def _has_any(text, keywords):
    """True if any keyword appears in text."""
    if not text:
        return False
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


# ---------------------------------------------------------------------------
# AdmissibilityScorer
# ---------------------------------------------------------------------------

class AdmissibilityScorer:
    """MRE-based evidence admissibility analysis for Pigors v. Watson."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH_DEFAULT
        self._conn = None
        self._connect()

    # -- connection management ----------------------------------------------

    def _connect(self):
        """Open DB connection with retry (3 attempts, exponential backoff)."""
        import time
        for attempt in range(3):
            try:
                self._conn = sqlite3.connect(self.db_path, timeout=10)
                self._conn.row_factory = sqlite3.Row
                return
            except sqlite3.Error:
                if attempt < 2:
                    time.sleep(2 ** attempt)
        self._conn = None

    def _cursor(self):
        if self._conn is None:
            self._connect()
        if self._conn is None:
            raise RuntimeError("Cannot connect to litigation_context.db")
        return self._conn.cursor()

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # -- internal DB helpers ------------------------------------------------

    def _fetch_mre_rule(self, rule_number):
        """Return full_text for an MRE rule from auth_rules, or None."""
        try:
            cur = self._cursor()
            cur.execute(
                "SELECT full_text FROM auth_rules WHERE rule_number = ? LIMIT 1",
                (rule_number,),
            )
            row = cur.fetchone()
            return row["full_text"] if row else None
        except Exception:
            return None

    def _search_rules_fts(self, query, limit=5):
        """FTS5 search on auth_rules_fts. Returns list of dicts."""
        results = []
        try:
            cur = self._cursor()
            cur.execute(
                "SELECT rule_number, title, full_text FROM auth_rules_fts "
                "WHERE auth_rules_fts MATCH ? LIMIT ?",
                (query, limit),
            )
            for row in cur.fetchall():
                results.append(dict(row))
        except Exception:
            pass
        return results

    def _fetch_evidence(self, evidence_id):
        """Return a single evidence_quotes row by id."""
        try:
            cur = self._cursor()
            cur.execute("SELECT * FROM evidence_quotes WHERE id = ?", (evidence_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        except Exception:
            return None

    def _search_evidence_fts(self, query, limit=50):
        """FTS5 search on evidence_quotes. Returns list of dicts."""
        results = []
        try:
            cur = self._cursor()
            # Try FTS table first
            cur.execute(
                "SELECT eq.* FROM evidence_quotes eq "
                "JOIN evidence_quotes_fts fts ON eq.id = fts.rowid "
                "WHERE evidence_quotes_fts MATCH ? LIMIT ?",
                (query, limit),
            )
            for row in cur.fetchall():
                results.append(dict(row))
        except Exception:
            # Fallback: LIKE search
            try:
                cur = self._cursor()
                cur.execute(
                    "SELECT * FROM evidence_quotes WHERE quote_text LIKE ? LIMIT ?",
                    (f"%{query}%", limit),
                )
                for row in cur.fetchall():
                    results.append(dict(row))
            except Exception:
                pass
        return results

    def _fetch_evidence_batch(self, ids=None, category=None, limit=100):
        """Fetch evidence rows by id list or category."""
        results = []
        try:
            cur = self._cursor()
            if ids:
                placeholders = ",".join("?" for _ in ids)
                cur.execute(
                    f"SELECT * FROM evidence_quotes WHERE id IN ({placeholders}) LIMIT ?",
                    list(ids) + [limit],
                )
            elif category:
                cur.execute(
                    "SELECT * FROM evidence_quotes WHERE evidence_category = ? LIMIT ?",
                    (category, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM evidence_quotes LIMIT ?", (limit,),
                )
            for row in cur.fetchall():
                results.append(dict(row))
        except Exception:
            pass
        return results

    # -- core analysis methods ---------------------------------------------

    def _analyze_relevance(self, evidence_text, evidence_type=None):
        """Score relevance under MRE 401-403."""
        score = 0.3  # baseline — most evidence offered has *some* relevance

        if not evidence_text:
            return {"score": 0.0, "analysis": "No evidence text provided."}

        # Boost for best-interest factor keywords (custody context)
        bi_score = _kw_score(evidence_text, _BEST_INTEREST_KEYWORDS)
        score += bi_score * 0.5

        # Boost for case-specific terms
        case_keywords = [
            "custody", "parenting time", "child", "parent",
            "visitation", "separation", "best interest",
            PARTY_OPPONENT.lower(), "pigors",
        ]
        case_score = _kw_score(evidence_text, case_keywords)
        score += case_score * 0.2

        # MRE 403 prejudice discount
        prejudice_kw = [
            "inflammatory", "gruesome", "shocking", "prejudicial",
            "graphic", "disturbing",
        ]
        if _has_any(evidence_text, prejudice_kw):
            score *= 0.7

        score = min(score, 1.0)

        analysis_parts = []
        if bi_score > 0.05:
            analysis_parts.append(
                f"Relevant to best-interest factors (MCL 722.23) — keyword match {bi_score:.0%}."
            )
        if case_score > 0.05:
            analysis_parts.append("Directly references case parties or custody issues.")
        if score < 0.3:
            analysis_parts.append(
                "Low relevance — may face MRE 401/402 objection. "
                "Consider tying to a specific best-interest factor."
            )
        if _has_any(evidence_text, prejudice_kw):
            analysis_parts.append(
                "MRE 403 risk: potential unfair prejudice. "
                "Prepare to argue probative value outweighs prejudicial effect."
            )
        if not analysis_parts:
            analysis_parts.append("General relevance to the proceedings under MRE 401.")

        return {"score": round(score, 2), "analysis": " ".join(analysis_parts)}

    def _analyze_hearsay(self, evidence_text, speaker=None, evidence_type=None):
        """Analyze hearsay status and exceptions under MRE 801-807."""
        result = {
            "is_hearsay": False,
            "exception": None,
            "exceptions_applicable": [],
            "analysis": "",
            "admissible": True,
        }

        if not evidence_text:
            result["analysis"] = "No evidence text to analyze."
            return result

        lower = evidence_text.lower()

        # Determine if statement is hearsay (out-of-court statement for truth)
        hearsay_signals = [
            "said", "told me", "stated", "wrote", "texted",
            "messaged", "he said", "she said", "they said",
            "according to", "reported that", "claimed",
        ]
        is_likely_hearsay = _has_any(evidence_text, hearsay_signals)

        # Not hearsay: verbal acts, commands, questions, effect on listener
        non_hearsay_signals = [
            "i promise", "i agree", "do you", "verbal act",
            "effect on the listener", "notice", "demand",
            "offer", "acceptance", "threat",
        ]
        if _has_any(evidence_text, non_hearsay_signals):
            is_likely_hearsay = False
            result["analysis"] = (
                "Likely not hearsay — may be a verbal act, operative language, "
                "or offered for effect on the listener rather than truth of matter asserted."
            )

        result["is_hearsay"] = is_likely_hearsay

        if not is_likely_hearsay:
            if not result["analysis"]:
                result["analysis"] = "Does not appear to be hearsay under MRE 801(c)."
            return result

        # Check exceptions
        exceptions_found = []

        # Speaker-specific fast paths
        if speaker:
            speaker_lower = speaker.lower()
            if any(n in speaker_lower for n in ["watson", "tiffany"]):
                exceptions_found.append({
                    "rule": "MRE 801(d)(2)",
                    "description": HEARSAY_EXCEPTIONS["MRE 801(d)(2)"],
                    "confidence": 0.95,
                    "analysis": (
                        f"Statement by {PARTY_OPPONENT} is an admission by "
                        "party-opponent — not hearsay by definition under MRE 801(d)(2)."
                    ),
                })
            if any(n in speaker_lower for n in ["judge", "mcneill", "court"]):
                exceptions_found.append({
                    "rule": "MRE 803(8)",
                    "description": HEARSAY_EXCEPTIONS["MRE 803(8)"],
                    "confidence": 0.85,
                    "analysis": (
                        "Statement from judicial officer — likely admissible as "
                        "public record under MRE 803(8) or as judicial notice under MRE 201."
                    ),
                })

        # Evidence-type fast paths
        if evidence_type:
            et_lower = evidence_type.lower()
            if any(t in et_lower for t in ["transcript", "deposition", "hearing"]):
                exceptions_found.append({
                    "rule": "MRE 801(d)(1)",
                    "description": HEARSAY_EXCEPTIONS["MRE 801(d)(1)"],
                    "confidence": 0.80,
                    "analysis": (
                        "Statement from court transcript — prior statement "
                        "under oath admissible under MRE 801(d)(1) if inconsistent, "
                        "or MRE 804(b)(1) as former testimony."
                    ),
                })
            if any(t in et_lower for t in ["business", "record", "log", "invoice"]):
                exceptions_found.append({
                    "rule": "MRE 803(6)",
                    "description": HEARSAY_EXCEPTIONS["MRE 803(6)"],
                    "confidence": 0.80,
                    "analysis": "Business record exception — requires custodian foundation.",
                })

        # Keyword-based exception scanning
        for rule, signals in _EXCEPTION_SIGNALS.items():
            # Skip if we already found this exception via speaker/type
            if any(e["rule"] == rule for e in exceptions_found):
                continue
            if _has_any(evidence_text, signals):
                confidence = _kw_score(evidence_text, signals)
                confidence = max(0.3, min(confidence * 3, 0.90))
                exceptions_found.append({
                    "rule": rule,
                    "description": HEARSAY_EXCEPTIONS[rule],
                    "confidence": round(confidence, 2),
                    "analysis": f"Keyword signals suggest {rule} ({HEARSAY_EXCEPTIONS[rule]}) may apply.",
                })

        # Sort by confidence
        exceptions_found.sort(key=lambda e: e["confidence"], reverse=True)

        result["exceptions_applicable"] = exceptions_found
        if exceptions_found:
            best = exceptions_found[0]
            result["exception"] = best["rule"]
            result["admissible"] = True
            result["analysis"] = (
                f"Hearsay detected, but likely admissible under {best['rule']} "
                f"({best['description']}). Confidence: {best['confidence']:.0%}. "
                f"{best['analysis']}"
            )
        else:
            result["admissible"] = False
            result["analysis"] = (
                "Hearsay detected with no clear exception. "
                "This evidence faces exclusion under MRE 802 unless an exception "
                "or exemption is established. Consider: (1) offering for a non-hearsay "
                "purpose (notice, effect on listener, verbal act); "
                "(2) laying foundation for a recognized exception."
            )

        return result

    def _analyze_authentication(self, evidence_text, evidence_type=None):
        """Score authentication requirements under MRE 901-902."""
        score = 0.5  # baseline
        requirements = []

        # Self-authenticating categories (MRE 902)
        self_auth_types = ["court_order", "order", "judgment", "certified", "public_record"]
        if evidence_type and any(t in evidence_type.lower() for t in self_auth_types):
            score = 0.95
            requirements.append(
                "Self-authenticating under MRE 902(1) — ensure certified copy is obtained."
            )
            return {"score": round(score, 2), "requirements": requirements}

        if evidence_type and "transcript" in evidence_type.lower():
            score = 0.90
            requirements.append(
                "Certified transcript is self-authenticating under MRE 902(4)."
            )
            return {"score": round(score, 2), "requirements": requirements}

        # Digital evidence needs more foundation
        digital_types = [
            "text", "email", "social_media", "screenshot", "message",
            "sms", "chat", "facebook", "instagram",
        ]
        if evidence_type and any(t in evidence_type.lower() for t in digital_types):
            score = 0.40
            requirements.extend([
                "Authenticate via witness with knowledge (MRE 901(b)(1)).",
                "Identify sender/receiver and account ownership.",
                "Show distinctive characteristics and context (MRE 901(b)(4)).",
                "Preserve metadata (timestamps, headers) for authentication.",
            ])
        else:
            requirements.append(
                "Testimony of witness with knowledge that item is what it purports to be (MRE 901(b)(1))."
            )

        # Keyword boosts
        if _has_any(evidence_text, ["certified", "notarized", "authenticated", "seal"]):
            score = min(score + 0.2, 1.0)
            requirements.append("Evidence appears to have certification markers.")

        return {"score": round(score, 2), "requirements": requirements}

    def _analyze_best_evidence(self, evidence_text, evidence_type=None):
        """Analyze compliance with Best Evidence Rule (MRE 1001-1008)."""
        compliant = True
        analysis_parts = []

        copy_signals = [
            "copy", "screenshot", "printout", "photograph of document",
            "duplicate", "scan",
        ]
        is_copy = _has_any(evidence_text, copy_signals)

        if is_copy:
            compliant = False
            analysis_parts.append(
                "Evidence may be a copy — MRE 1002 requires the original to prove "
                "the content of a writing, recording, or photograph."
            )
            analysis_parts.append(
                "Cure: MRE 1003 allows duplicates unless genuine question of authenticity "
                "or unfairness. Alternatively, MRE 1004 allows secondary evidence if "
                "original is lost, destroyed, or unobtainable."
            )
        else:
            analysis_parts.append(
                "No best-evidence concerns detected. If offering a writing or recording, "
                "ensure original or admissible duplicate is available."
            )

        return {"compliant": compliant, "analysis": " ".join(analysis_parts)}

    def _compile_objection_risks(self, evidence_text, evidence_type=None):
        """Predict likely objections from opposing counsel."""
        objections = []
        for tmpl in _OBJECTION_TEMPLATES:
            if _has_any(evidence_text, tmpl["keywords"]):
                response = self._generate_objection_response(
                    tmpl["objection"], tmpl["basis"], evidence_text, evidence_type,
                )
                objections.append({
                    "objection": tmpl["objection"],
                    "basis": tmpl["basis"],
                    "response": response,
                })

        # Family law relaxed rules note
        objections.append({
            "objection": "NOTE: Relaxed evidentiary rules",
            "basis": "MRE 1101(b)(3)",
            "response": (
                "In certain family law proceedings (e.g., custody evaluations, "
                "preliminary matters), the Michigan Rules of Evidence are relaxed "
                "under MRE 1101(b)(3). This may allow admission of evidence that "
                "would otherwise be excluded."
            ),
        })
        return objections

    def _generate_objection_response(self, objection, basis, evidence_text, evidence_type):
        """Generate a response to a predicted objection."""
        responses = {
            "Hearsay": (
                "Response: The statement falls under [applicable exception]. "
                "Alternatively, it is offered not for the truth of the matter "
                "asserted but for [non-hearsay purpose — notice, effect on "
                "listener, verbal act, or state of mind]."
            ),
            "Relevance": (
                "Response: This evidence is relevant under MRE 401 because it "
                "makes a fact of consequence (best-interest factor under MCL 722.23) "
                "more or less probable. Its probative value is substantial."
            ),
            "Unfair prejudice outweighs probative value": (
                "Response: Under MRE 403, the probative value of this evidence "
                "is not substantially outweighed by the danger of unfair prejudice. "
                "The evidence goes directly to a contested best-interest factor."
            ),
            "Lack of foundation / authentication": (
                "Response: Foundation will be laid through testimony of a witness "
                "with knowledge under MRE 901(b)(1), or the exhibit is "
                "self-authenticating under MRE 902."
            ),
            "Speculation / Lack of personal knowledge": (
                "Response: The witness has personal knowledge of these facts "
                "under MRE 602. The testimony is based on firsthand observation."
            ),
            "Improper character evidence": (
                "Response: This evidence is not offered to prove character or "
                "propensity under MRE 404(a). It is offered for a permissible "
                "purpose: motive, intent, plan, or absence of mistake under "
                "MRE 404(b). In custody proceedings, moral fitness is a "
                "best-interest factor under MCL 722.23(e)."
            ),
            "Best evidence rule — original required": (
                "Response: Under MRE 1003, a duplicate is admissible to the "
                "same extent as the original unless there is a genuine question "
                "of authenticity. No such question exists here."
            ),
            "Privilege": (
                "Response: No privilege applies. The communication was not "
                "between attorney and client, and no other recognized privilege "
                "under MRE 501 attaches."
            ),
        }
        return responses.get(objection, f"Response: Objection under {basis} is not well-taken.")

    def _compile_cure_suggestions(self, hearsay_result, auth_result, best_ev_result):
        """Suggest how to cure admissibility issues."""
        cures = []

        if hearsay_result.get("is_hearsay") and not hearsay_result.get("admissible"):
            cures.extend([
                "Hearsay cure: Identify a recognized exception (MRE 803/804/807).",
                "Hearsay cure: Offer for a non-hearsay purpose (notice, verbal act, state of mind).",
                "Hearsay cure: Call the declarant as a witness to testify directly.",
            ])

        if auth_result.get("score", 1.0) < 0.6:
            cures.extend([
                "Authentication cure: Obtain testimony from a witness with knowledge (MRE 901(b)(1)).",
                "Authentication cure: Obtain a certified copy if the item is a public record (MRE 902).",
                "Authentication cure: Preserve and present metadata for digital evidence.",
            ])

        if not best_ev_result.get("compliant", True):
            cures.extend([
                "Best evidence cure: Obtain the original document if available.",
                "Best evidence cure: Establish that original is lost/destroyed for MRE 1004 exception.",
                "Best evidence cure: Argue duplicate is admissible under MRE 1003.",
            ])

        if not cures:
            cures.append("No significant admissibility issues to cure.")

        return cures

    # -- public API ---------------------------------------------------------

    def score_admissibility(self, evidence_text, evidence_type=None, speaker=None):
        """
        Full MRE admissibility analysis.

        Returns dict with overall_score (0-100), sub-analyses, objection
        risks, and cure suggestions.
        """
        relevance = self._analyze_relevance(evidence_text, evidence_type)
        hearsay = self._analyze_hearsay(evidence_text, speaker, evidence_type)
        authentication = self._analyze_authentication(evidence_text, evidence_type)
        best_evidence = self._analyze_best_evidence(evidence_text, evidence_type)
        objection_risks = self._compile_objection_risks(evidence_text, evidence_type)
        cure_suggestions = self._compile_cure_suggestions(hearsay, authentication, best_evidence)

        # Composite score (0-100)
        rel_weight = 0.30
        hearsay_weight = 0.35
        auth_weight = 0.25
        best_ev_weight = 0.10

        hearsay_score = 1.0 if hearsay["admissible"] else 0.2
        best_ev_score = 1.0 if best_evidence["compliant"] else 0.5

        overall = (
            relevance["score"] * rel_weight
            + hearsay_score * hearsay_weight
            + authentication["score"] * auth_weight
            + best_ev_score * best_ev_weight
        ) * 100

        overall = round(min(overall, 100), 1)
        admissible = overall >= 50 and hearsay["admissible"]

        return {
            "overall_score": overall,
            "relevance": relevance,
            "hearsay": {
                "is_hearsay": hearsay["is_hearsay"],
                "exception": hearsay["exception"],
                "exceptions_applicable": hearsay.get("exceptions_applicable", []),
                "analysis": hearsay["analysis"],
            },
            "authentication": authentication,
            "best_evidence": best_evidence,
            "admissible": admissible,
            "objection_risks": objection_risks,
            "cure_suggestions": cure_suggestions,
        }

    def batch_score_evidence(self, evidence_ids=None, category=None, limit=100):
        """
        Score multiple evidence items. Returns list sorted by overall_score
        descending (strongest evidence first).
        """
        rows = self._fetch_evidence_batch(
            ids=evidence_ids, category=category, limit=limit,
        )
        scored = []
        for row in rows:
            try:
                result = self.score_admissibility(
                    evidence_text=row.get("quote_text", ""),
                    evidence_type=row.get("evidence_category") or row.get("source_type"),
                    speaker=row.get("speaker"),
                )
                result["evidence_id"] = row.get("id")
                result["quote_text"] = (row.get("quote_text") or "")[:200]
                result["speaker"] = row.get("speaker")
                result["evidence_category"] = row.get("evidence_category")
                scored.append(result)
            except Exception:
                continue

        scored.sort(key=lambda x: x["overall_score"], reverse=True)
        return scored

    def find_hearsay_exceptions(self, evidence_text, speaker=None):
        """
        Deep hearsay-exception analysis.

        Returns list of applicable exceptions with confidence scores and
        specific analysis for the Pigors v. Watson context.
        """
        exceptions = []

        if not evidence_text:
            return exceptions

        # Party-opponent admission
        if speaker:
            speaker_lower = speaker.lower()
            if any(n in speaker_lower for n in ["watson", "tiffany"]):
                exceptions.append({
                    "rule": "MRE 801(d)(2)",
                    "description": "Admission by party-opponent",
                    "confidence": 0.95,
                    "analysis": (
                        f"Any statement by {PARTY_OPPONENT} offered against her "
                        "is admissible as a party admission. This is an exemption "
                        "from hearsay — it is 'not hearsay' by definition under "
                        "MRE 801(d)(2). No additional foundation required beyond "
                        "identifying the declarant as the opposing party."
                    ),
                    "authority": "MRE 801(d)(2)",
                })
            if any(n in speaker_lower for n in ["judge", "mcneill", "court"]):
                exceptions.append({
                    "rule": "MRE 803(8)",
                    "description": "Public records and reports",
                    "confidence": 0.85,
                    "analysis": (
                        "Statement by judicial officer in official capacity is "
                        "likely a public record under MRE 803(8). Court orders "
                        "and findings are also subject to judicial notice under MRE 201."
                    ),
                    "authority": "MRE 803(8), MRE 201",
                })

        # Transcript / prior statement under oath
        oath_signals = [
            "under oath", "testified", "deposition", "transcript",
            "sworn", "hearing testimony",
        ]
        if _has_any(evidence_text, oath_signals):
            exceptions.append({
                "rule": "MRE 801(d)(1)",
                "description": "Prior inconsistent statement under oath",
                "confidence": 0.80,
                "analysis": (
                    "If the declarant testifies at trial and the statement is "
                    "inconsistent with their current testimony, it is admissible "
                    "under MRE 801(d)(1) as substantive evidence (not merely for "
                    "impeachment). The statement must have been given under oath "
                    "subject to penalty of perjury."
                ),
                "authority": "MRE 801(d)(1)(A)",
            })

        # Scan all exception keyword groups
        for rule, signals in _EXCEPTION_SIGNALS.items():
            if any(e["rule"] == rule for e in exceptions):
                continue
            if _has_any(evidence_text, signals):
                confidence = _kw_score(evidence_text, signals)
                confidence = max(0.3, min(confidence * 3, 0.90))
                exceptions.append({
                    "rule": rule,
                    "description": HEARSAY_EXCEPTIONS.get(rule, rule),
                    "confidence": round(confidence, 2),
                    "analysis": (
                        f"Keyword analysis suggests {rule} "
                        f"({HEARSAY_EXCEPTIONS.get(rule, '')}) may apply. "
                        "Review the specific foundational requirements for this exception."
                    ),
                    "authority": rule,
                })

        exceptions.sort(key=lambda e: e["confidence"], reverse=True)
        return exceptions

    def predict_objections(self, evidence_text, evidence_type=None):
        """
        Predict objections opposing counsel will raise and provide
        response strategies with MRE authority.
        """
        predictions = []

        for tmpl in _OBJECTION_TEMPLATES:
            if _has_any(evidence_text, tmpl["keywords"]):
                likelihood = _kw_score(evidence_text, tmpl["keywords"])
                likelihood = max(0.3, min(likelihood * 4, 0.95))
                response = self._generate_objection_response(
                    tmpl["objection"], tmpl["basis"], evidence_text, evidence_type,
                )
                predictions.append({
                    "objection": tmpl["objection"],
                    "basis": tmpl["basis"],
                    "likelihood": round(likelihood, 2),
                    "response": response,
                    "authority": tmpl["basis"],
                })

        # Always note relaxed rules in family law
        predictions.append({
            "objection": "General: Relaxed evidentiary standard in family proceedings",
            "basis": "MRE 1101(b)(3)",
            "likelihood": 1.0,
            "response": (
                "In certain family law proceedings, the strict rules of "
                "evidence do not apply under MRE 1101(b)(3). This includes "
                "preliminary examinations, sentencing, probation proceedings, "
                "and certain dispositional hearings. Argue applicability if "
                "the proceeding qualifies."
            ),
            "authority": "MRE 1101(b)(3)",
        })

        predictions.sort(key=lambda p: p["likelihood"], reverse=True)
        return predictions

    def score_exhibit_readiness(self, evidence_category=None):
        """
        Score overall trial readiness for a category of evidence.
        """
        rows = self._fetch_evidence_batch(category=evidence_category, limit=500)
        if not rows:
            return {
                "category": evidence_category or "all",
                "total_items": 0,
                "admissible_count": 0,
                "score": 0,
                "issues": ["No evidence items found for this category."],
            }

        admissible_count = 0
        total_score = 0.0
        issues = []
        hearsay_no_exception = 0
        low_auth = 0
        best_ev_issues = 0

        for row in rows:
            try:
                result = self.score_admissibility(
                    evidence_text=row.get("quote_text", ""),
                    evidence_type=row.get("evidence_category") or row.get("source_type"),
                    speaker=row.get("speaker"),
                )
                total_score += result["overall_score"]
                if result["admissible"]:
                    admissible_count += 1
                if result["hearsay"]["is_hearsay"] and not result["hearsay"]["exception"]:
                    hearsay_no_exception += 1
                if result["authentication"]["score"] < 0.5:
                    low_auth += 1
                if not result["best_evidence"]["compliant"]:
                    best_ev_issues += 1
            except Exception:
                continue

        total = len(rows)
        avg_score = round(total_score / max(total, 1), 1)

        if hearsay_no_exception > 0:
            issues.append(
                f"{hearsay_no_exception} item(s) are hearsay with no identified exception."
            )
        if low_auth > 0:
            issues.append(
                f"{low_auth} item(s) have low authentication scores — foundation needed."
            )
        if best_ev_issues > 0:
            issues.append(
                f"{best_ev_issues} item(s) may violate the best evidence rule."
            )
        if not issues:
            issues.append("No significant admissibility issues detected.")

        return {
            "category": evidence_category or "all",
            "total_items": total,
            "admissible_count": admissible_count,
            "score": avg_score,
            "issues": issues,
        }

    def generate_foundation_checklist(self, evidence_type):
        """
        Return a foundation checklist for the given evidence type.
        """
        key = _CATEGORY_TO_FOUNDATION.get(
            evidence_type.lower() if evidence_type else "",
            None,
        )
        if key and key in _FOUNDATION_CHECKLISTS:
            checklist = _FOUNDATION_CHECKLISTS[key].copy()
            checklist["evidence_type_input"] = evidence_type
            return checklist

        # Generic fallback
        return {
            "label": f"Generic Foundation — {evidence_type}",
            "evidence_type_input": evidence_type,
            "steps": [
                "Authenticate: testimony of witness with knowledge (MRE 901(b)(1)).",
                "Establish relevance under MRE 401 — tie to a fact of consequence.",
                "Perform hearsay analysis — identify applicable exception if needed.",
                "Check MRE 403 balancing — probative value vs. unfair prejudice.",
                "Ensure original or admissible duplicate under MRE 1002-1003.",
            ],
            "authority": ["MRE 901(b)(1)", "MRE 401", "MRE 403", "MRE 1002"],
        }

    def find_strongest_evidence(self, topic, top_n=10):
        """
        Find the N most admissible evidence items on a topic.
        Searches evidence_quotes via FTS, scores each, returns ranked.
        """
        rows = self._search_evidence_fts(topic, limit=top_n * 3)
        if not rows:
            return []

        scored = []
        for row in rows:
            try:
                result = self.score_admissibility(
                    evidence_text=row.get("quote_text", ""),
                    evidence_type=row.get("evidence_category") or row.get("source_type"),
                    speaker=row.get("speaker"),
                )
                scored.append({
                    "evidence_id": row.get("id"),
                    "quote_text": (row.get("quote_text") or "")[:200],
                    "speaker": row.get("speaker"),
                    "evidence_category": row.get("evidence_category"),
                    "overall_score": result["overall_score"],
                    "admissible": result["admissible"],
                    "hearsay_exception": result["hearsay"]["exception"],
                    "relevance_score": result["relevance"]["score"],
                    "authentication_score": result["authentication"]["score"],
                })
            except Exception:
                continue

        scored.sort(key=lambda x: x["overall_score"], reverse=True)
        return scored[:top_n]


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("MBP LitigationOS — Evidence Admissibility Scorer")
    print("=" * 60)

    scorer = AdmissibilityScorer()

    # 1. Score a sample party-admission
    print("\n[1] Party-opponent admission test:")
    r1 = scorer.score_admissibility(
        evidence_text="Tiffany Watson texted 'I will not let you see the kids ever again'",
        evidence_type="text_message",
        speaker="Tiffany Watson",
    )
    print(f"  Overall score: {r1['overall_score']}")
    print(f"  Admissible:    {r1['admissible']}")
    print(f"  Hearsay:       {r1['hearsay']['is_hearsay']}")
    print(f"  Exception:     {r1['hearsay']['exception']}")

    # 2. Hearsay exception finder
    print("\n[2] Hearsay exception finder:")
    exc = scorer.find_hearsay_exceptions(
        evidence_text="She said she would keep the children away from their father",
        speaker="Tiffany Watson",
    )
    for e in exc:
        print(f"  {e['rule']} — confidence {e['confidence']:.0%}: {e['description']}")

    # 3. Predict objections
    print("\n[3] Objection prediction:")
    obj = scorer.predict_objections(
        evidence_text="A copy of a text message screenshot showing she said she would move away",
        evidence_type="text_message",
    )
    for o in obj[:3]:
        print(f"  Objection: {o['objection']} ({o['basis']}) — likelihood {o['likelihood']:.0%}")

    # 4. Foundation checklist
    print("\n[4] Foundation checklist for text messages:")
    fc = scorer.generate_foundation_checklist("text_message")
    for step in fc["steps"]:
        print(f"  - {step}")

    # 5. Find strongest evidence on a topic (if DB is available)
    print("\n[5] Strongest evidence on 'custody':")
    try:
        strong = scorer.find_strongest_evidence("custody", top_n=5)
        if strong:
            for s in strong:
                print(
                    f"  ID={s['evidence_id']} score={s['overall_score']} "
                    f"speaker={s['speaker']} excerpt={s['quote_text'][:80]}..."
                )
        else:
            print("  No evidence found for topic 'custody'.")
    except Exception as ex:
        print(f"  DB search unavailable: {ex}")

    scorer.close()
    print("\n" + "=" * 60)
    print("Smoke test complete.")
