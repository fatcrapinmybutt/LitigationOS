"""
LitigationOS Legal NLP Engine v1.0
Unified interface to: eyecite, courts-db, reporters-db, juriscraper,
legal-bert (HuggingFace), and MANBEARPIG local inference.
All tools are free, offline-capable, and CPU-only.
"""

import sys
import os
import re
import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger("LegalNLPEngine")


# ── Data Classes ──────────────────────────────────────────────


@dataclass
class Citation:
    """Extracted legal citation with metadata."""

    raw_text: str
    citation_type: str  # case, statute, rule, regulation
    reporter: str = ""
    volume: str = ""
    page: str = ""
    court: str = ""
    year: str = ""
    pin_cite: str = ""
    canonical: str = ""
    confidence: float = 0.0


@dataclass
class LegalEntity:
    """Named entity from legal text."""

    text: str
    entity_type: str  # JUDGE, PARTY, COURT, STATUTE, CASE, DATE, AMOUNT
    start: int = 0
    end: int = 0
    confidence: float = 0.0


@dataclass
class CourtInfo:
    """Court metadata from courts-db."""

    name: str
    court_id: str = ""
    jurisdiction: str = ""
    level: str = ""  # trial, appellate, supreme
    url: str = ""


@dataclass
class AnalysisResult:
    """Result of analyzing a legal document."""

    citations: List[Citation] = field(default_factory=list)
    entities: List[LegalEntity] = field(default_factory=list)
    courts_referenced: List[CourtInfo] = field(default_factory=list)
    michigan_rules: List[str] = field(default_factory=list)
    michigan_statutes: List[str] = field(default_factory=list)
    key_phrases: List[str] = field(default_factory=list)
    document_type: str = ""
    lane_assignment: str = ""
    confidence: float = 0.0
    processing_time_ms: float = 0.0


# ── Michigan-Specific Constants ──────────────────────────────

MICHIGAN_COURTS = {
    "mich. ct. app.": CourtInfo(
        "Michigan Court of Appeals", "michctapp", "Michigan", "appellate"
    ),
    "michigan court of appeals": CourtInfo(
        "Michigan Court of Appeals", "michctapp", "Michigan", "appellate"
    ),
    "court of appeals": CourtInfo(
        "Michigan Court of Appeals", "michctapp", "Michigan", "appellate"
    ),
    "mich.": CourtInfo(
        "Michigan Supreme Court", "mich", "Michigan", "supreme"
    ),
    "michigan supreme court": CourtInfo(
        "Michigan Supreme Court", "mich", "Michigan", "supreme"
    ),
    "14th circuit": CourtInfo(
        "14th Judicial Circuit Court",
        "mich14cir",
        "Muskegon County",
        "trial",
    ),
    "14th judicial circuit": CourtInfo(
        "14th Judicial Circuit Court",
        "mich14cir",
        "Muskegon County",
        "trial",
    ),
    "muskegon circuit": CourtInfo(
        "Muskegon County Circuit Court",
        "muskegoncir",
        "Muskegon County",
        "trial",
    ),
    "3rd circuit": CourtInfo(
        "3rd Judicial Circuit Court", "mich3cir", "Wayne County", "trial"
    ),
    "6th circuit": CourtInfo(
        "U.S. Court of Appeals, Sixth Circuit",
        "ca6",
        "Federal",
        "appellate",
    ),
    "western district of michigan": CourtInfo(
        "U.S. District Court, W.D. Michigan",
        "wdmich",
        "Federal",
        "trial",
    ),
}

# Lane signals — detection priority: E → D → F → C → A → B
LANE_SIGNALS: Dict[str, List[str]] = {
    "E": [
        "judicial tenure",
        "jtc",
        "judicial misconduct",
        "canon",
        "mcneill bias",
        "ex parte",
        "disqualification",
    ],
    "D": [
        "ppo",
        "personal protection",
        "protection order",
        "2023-5907",
        "stalking",
        "domestic violence",
    ],
    "F": [
        "court of appeals",
        "appellate",
        "leave to appeal",
        "366810",
        "supreme court",
        "coa",
    ],
    "C": [
        "convergence",
        "1983",
        "civil rights",
        "2025-002760",
        "federal",
        "cross-lane",
    ],
    "A": [
        "custody",
        "parenting time",
        "child support",
        "2024-001507",
        "best interest",
        "foc",
        "friend of the court",
    ],
    "B": [
        "housing",
        "habitability",
        "shady oaks",
        "landlord",
        "mcl 554",
        "rent",
        "tenant",
    ],
}

# Michigan citation regex patterns: (pattern, citation_type, reporter_label)
MICHIGAN_CITE_PATTERNS: List[Tuple[str, str, str]] = [
    (r"MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*)", "rule", "MCR"),
    (r"MCL\s+(\d+\.\d+[a-z]?(?:\([0-9]+\))*)", "statute", "MCL"),
    (r"MRE\s+(\d+(?:\([a-z]\))*)", "rule", "MRE"),
    (r"(\d+)\s+Mich\s+App\s+(\d+)", "case", "Mich App"),
    (r"(\d+)\s+Mich\s+(\d+)", "case", "Mich"),
    (r"(\d+)\s+NW2d\s+(\d+)", "case", "NW2d"),
    (r"(\d+)\s+NW\s+2d\s+(\d+)", "case", "NW2d"),
    (r"42\s+USC\s+[§]?\s*1983", "statute", "USC"),
    (r"28\s+USC\s+[§]?\s*1331", "statute", "USC"),
    (r"(\d+)\s+F\.?\s*3d\s+(\d+)", "case", "F.3d"),
    (r"(\d+)\s+F\.?\s*Supp\.?\s*(?:2d|3d)\s+(\d+)", "case", "F.Supp."),
    (r"(\d+)\s+US\s+(\d+)", "case", "US"),
    (r"(\d+)\s+S\.?\s*Ct\.?\s+(\d+)", "case", "S.Ct."),
]

# Michigan legal entity patterns: (pattern, entity_type)
MICHIGAN_ENTITY_PATTERNS: List[Tuple[str, str]] = [
    (
        r"(?:Judge|Hon\.?)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-zA-Z]+)",
        "JUDGE",
    ),
    (r"(\d{4}-\d{6}-[A-Z]{2})", "CASE_NUMBER"),
    (r"(\d{4}-\d{4}-[A-Z]{2})", "CASE_NUMBER"),
    (r"(?:14th|Third|Sixth)\s+(?:Judicial\s+)?Circuit", "COURT"),
    (
        r"(?:Muskegon|Wayne|Kent|Oakland|Washtenaw)\s+County",
        "JURISDICTION",
    ),
    (
        r"(?:Michigan\s+)?(?:Court\s+of\s+Appeals?|Supreme\s+Court)",
        "COURT",
    ),
    (r"MCL\s+\d+\.\d+[a-z]?", "STATUTE"),
    (r"MCR\s+\d+\.\d+", "RULE"),
    (r"Friend\s+of\s+the\s+Court", "ORGANIZATION"),
]

# Document classifiers: (keywords, doc_type)
DOCUMENT_CLASSIFIERS: List[Tuple[List[str], str]] = [
    (["motion", "moves this court", "respectfully moves"], "motion"),
    (["complaint", "plaintiff alleges", "cause of action"], "complaint"),
    (["brief", "argument", "points and authorities"], "brief"),
    (["affidavit", "swear", "affirm under penalty"], "affidavit"),
    (["order", "it is ordered", "the court orders"], "order"),
    (["subpoena", "you are commanded"], "subpoena"),
    (["deposition", "testimony", "q:", "a:"], "deposition"),
    (
        ["discovery", "interrogator", "request for production"],
        "discovery",
    ),
    (["appeal", "appellant", "appellee"], "appellate_filing"),
    (
        ["proof of service", "certificate of service", "i certify"],
        "proof_of_service",
    ),
]


class LegalNLPEngine:
    """
    Unified Legal NLP Engine for LitigationOS.

    Wraps: eyecite, courts-db, reporters-db, legal-bert, spaCy,
    and custom Michigan-specific extractors.

    All tools are lazy-loaded.  If a dependency is missing the engine
    degrades gracefully — Michigan regex extractors always work.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self._eyecite = None
        self._courts_db = None
        self._reporters_db = None
        self._spacy_nlp = None
        self._legal_bert = None
        self._tokenizer = None
        self._available_tools: Dict[str, bool] = {}
        self._init_tools()

    # ── Initialisation ───────────────────────────────────────

    def _init_tools(self) -> None:
        """Lazy-load all available NLP tools."""
        self._init_eyecite()
        self._init_courts_db()
        self._init_reporters_db()
        self._init_spacy()
        self._init_transformers()

    def _init_eyecite(self) -> None:
        try:
            import eyecite

            self._eyecite = eyecite
            self._available_tools["eyecite"] = True
            logger.info("eyecite loaded")
        except ImportError:
            self._available_tools["eyecite"] = False
            logger.warning("eyecite not available")

    def _init_courts_db(self) -> None:
        try:
            import courts_db

            self._courts_db = courts_db
            self._available_tools["courts_db"] = True
            logger.info("courts-db loaded")
        except ImportError:
            self._available_tools["courts_db"] = False

    def _init_reporters_db(self) -> None:
        try:
            from reporters_db import REPORTERS

            self._reporters_db = REPORTERS
            self._available_tools["reporters_db"] = True
            logger.info("reporters-db loaded")
        except ImportError:
            self._available_tools["reporters_db"] = False

    def _init_spacy(self) -> None:
        try:
            import spacy

            for model in ("en_core_web_sm", "en_core_web_md"):
                if spacy.util.is_package(model):
                    self._spacy_nlp = spacy.load(model)
                    break
            if self._spacy_nlp:
                self._available_tools["spacy"] = True
                logger.info("spaCy loaded")
            else:
                self._available_tools["spacy"] = False
        except ImportError:
            self._available_tools["spacy"] = False

    def _init_transformers(self) -> None:
        try:
            import transformers  # noqa: F401

            # Model loaded on demand via load_legal_bert()
            self._available_tools["legal_bert"] = False
            logger.info(
                "transformers available (legal-bert can be loaded on demand)"
            )
        except ImportError:
            self._available_tools["legal_bert"] = False

    # ── Status ───────────────────────────────────────────────

    def status(self) -> Dict[str, bool]:
        """Return availability status of all NLP tools."""
        return dict(self._available_tools)

    # ── Citation Extraction ──────────────────────────────────

    def extract_citations(self, text: str) -> List[Citation]:
        """Extract all legal citations using eyecite + regex fallback."""
        citations: List[Citation] = []

        if self._available_tools.get("eyecite"):
            citations.extend(self._extract_eyecite(text))

        # Michigan-specific regex (always runs — catches MCR/MCL/MRE etc.)
        citations.extend(self._extract_michigan_citations(text))

        return self._deduplicate_citations(citations)

    def _extract_eyecite(self, text: str) -> List[Citation]:
        """Use the eyecite library for broad citation extraction."""
        results: List[Citation] = []
        try:
            raw_cites = self._eyecite.get_citations(text)
            for rc in raw_cites:
                c = Citation(
                    raw_text=str(rc),
                    citation_type=self._classify_citation_type(str(rc)),
                    canonical=str(rc),
                    confidence=0.95,
                )
                if hasattr(rc, "groups"):
                    groups = rc.groups
                    c.volume = str(getattr(groups, "volume", ""))
                    c.reporter = str(getattr(groups, "reporter", ""))
                    c.page = str(getattr(groups, "page", ""))
                results.append(c)
        except Exception as e:
            logger.warning("eyecite error: %s", e)
        return results

    def _extract_michigan_citations(self, text: str) -> List[Citation]:
        """Michigan-specific citation patterns (MCR, MCL, MRE, etc.)."""
        results: List[Citation] = []
        for pattern, cite_type, reporter in MICHIGAN_CITE_PATTERNS:
            for m in re.finditer(pattern, text):
                results.append(
                    Citation(
                        raw_text=m.group(0),
                        citation_type=cite_type,
                        reporter=reporter,
                        confidence=0.85,
                    )
                )
        return results

    @staticmethod
    def _classify_citation_type(text: str) -> str:
        """Classify a citation string as case, statute, rule, or regulation."""
        tl = text.lower()
        if any(kw in tl for kw in ("mcr", "mre", "frcp", "fre")):
            return "rule"
        if any(kw in tl for kw in ("mcl", "usc", "§", "stat.")):
            return "statute"
        if any(kw in tl for kw in ("cfr", "reg.")):
            return "regulation"
        return "case"

    @staticmethod
    def _deduplicate_citations(
        citations: List[Citation],
    ) -> List[Citation]:
        """Remove duplicate citations preserving insertion order."""
        seen: set = set()
        unique: List[Citation] = []
        for c in citations:
            key = c.raw_text.strip().lower()
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    # ── Entity Extraction ────────────────────────────────────

    def extract_entities(self, text: str) -> List[LegalEntity]:
        """Extract legal entities using spaCy + custom Michigan patterns."""
        entities: List[LegalEntity] = []

        if self._spacy_nlp:
            entities.extend(self._extract_spacy_entities(text))

        entities.extend(self._extract_michigan_entities(text))
        return entities

    def _extract_spacy_entities(self, text: str) -> List[LegalEntity]:
        """Use spaCy NER and map labels to legal types."""
        results: List[LegalEntity] = []
        try:
            doc = self._spacy_nlp(text[:100_000])
            for ent in doc.ents:
                mapped = self._map_spacy_to_legal(ent.label_)
                if mapped:
                    results.append(
                        LegalEntity(
                            text=ent.text,
                            entity_type=mapped,
                            start=ent.start_char,
                            end=ent.end_char,
                            confidence=0.8,
                        )
                    )
        except Exception as e:
            logger.warning("spaCy NER error: %s", e)
        return results

    @staticmethod
    def _map_spacy_to_legal(label: str) -> Optional[str]:
        """Map spaCy NER labels to legal entity types."""
        mapping = {
            "PERSON": "PARTY",
            "ORG": "ORGANIZATION",
            "DATE": "DATE",
            "MONEY": "AMOUNT",
            "GPE": "JURISDICTION",
            "LAW": "STATUTE",
            "FAC": "LOCATION",
            "NORP": "ORGANIZATION",
        }
        return mapping.get(label)

    @staticmethod
    def _extract_michigan_entities(text: str) -> List[LegalEntity]:
        """Michigan-specific entity extraction via regex."""
        entities: List[LegalEntity] = []
        for pattern, entity_type in MICHIGAN_ENTITY_PATTERNS:
            for m in re.finditer(pattern, text):
                entities.append(
                    LegalEntity(
                        text=m.group(0),
                        entity_type=entity_type,
                        start=m.start(),
                        end=m.end(),
                        confidence=0.9,
                    )
                )
        return entities

    # ── Court Lookup ─────────────────────────────────────────

    def lookup_court(self, query: str) -> List[CourtInfo]:
        """Look up court info from courts-db with Michigan fallback."""
        if self._available_tools.get("courts_db"):
            try:
                raw = self._courts_db.find_court(query)
                items = raw if isinstance(raw, list) else [raw]
                results = [
                    CourtInfo(
                        name=r.get("name", query),
                        court_id=r.get("id", ""),
                        jurisdiction=r.get("jurisdiction", ""),
                    )
                    for r in items
                    if r
                ]
                if results:
                    return results
            except Exception:
                pass

        return self._michigan_court_fallback(query)

    @staticmethod
    def _michigan_court_fallback(query: str) -> List[CourtInfo]:
        """Hardcoded Michigan court data as fallback."""
        q = query.lower().strip()
        for key, court in MICHIGAN_COURTS.items():
            if key in q or q in key:
                return [court]
        return []

    # ── Document Analysis ────────────────────────────────────

    def analyze_document(
        self, text: str, filename: str = ""
    ) -> AnalysisResult:
        """Full analysis pipeline for a single legal document."""
        import time

        start = time.time()

        result = AnalysisResult()
        result.citations = self.extract_citations(text)
        result.entities = self.extract_entities(text)

        result.michigan_rules = [
            c.raw_text for c in result.citations if c.citation_type == "rule"
        ]
        result.michigan_statutes = [
            c.raw_text
            for c in result.citations
            if c.citation_type == "statute"
        ]
        result.document_type = self._classify_document(text, filename)
        result.lane_assignment = self._assign_lane(text)
        result.key_phrases = self._extract_key_phrases(text)
        result.confidence = self._calculate_confidence(result)
        result.processing_time_ms = (time.time() - start) * 1000

        return result

    @staticmethod
    def _classify_document(text: str, filename: str) -> str:
        """Classify document type by keyword matching."""
        text_lower = text[:5000].lower()
        fn_lower = filename.lower()

        for keywords, doc_type in DOCUMENT_CLASSIFIERS:
            if any(kw in text_lower or kw in fn_lower for kw in keywords):
                return doc_type
        return "unknown"

    @staticmethod
    def _assign_lane(text: str) -> str:
        """Assign document to a case lane via MEEK signal detection.

        Detection priority: E → D → F → C → A → B.
        """
        text_lower = text[:10_000].lower()

        scores: Dict[str, int] = {}
        for lane, signals in LANE_SIGNALS.items():
            scores[lane] = sum(1 for s in signals if s in text_lower)

        best_lane = max(scores, key=lambda k: scores[k])
        return best_lane if scores[best_lane] > 0 else "C"

    @staticmethod
    def _extract_key_phrases(text: str) -> List[str]:
        """Extract key legal phrases from the text."""
        phrases: List[str] = []
        important = [
            "due process",
            "equal protection",
            "best interest of the child",
            "abuse of discretion",
            "clear and convincing",
            "preponderance of the evidence",
            "summary disposition",
            "personal jurisdiction",
            "subject matter jurisdiction",
            "res judicata",
            "collateral estoppel",
            "qualified immunity",
            "deliberate indifference",
            "color of law",
            "void ab initio",
        ]
        text_lower = text.lower()
        for phrase in important:
            if phrase in text_lower:
                phrases.append(phrase)
        return phrases

    @staticmethod
    def _calculate_confidence(result: "AnalysisResult") -> float:
        """Calculate overall analysis confidence score (0-1)."""
        factors: List[float] = []
        if result.citations:
            factors.append(min(len(result.citations) / 10.0, 1.0))
        if result.entities:
            factors.append(min(len(result.entities) / 20.0, 1.0))
        if result.document_type != "unknown":
            factors.append(0.9)
        if result.lane_assignment:
            factors.append(0.8)
        return sum(factors) / max(len(factors), 1)

    # ── Batch Processing ─────────────────────────────────────

    def analyze_directory(
        self,
        dir_path: str,
        extensions: Tuple[str, ...] = (".md", ".txt"),
    ) -> List[Dict]:
        """Analyze all legal documents in a directory tree."""
        results: List[Dict] = []
        p = Path(dir_path)
        if not p.is_dir():
            logger.warning("Not a directory: %s", dir_path)
            return results

        for f in sorted(p.rglob("*")):
            if f.suffix.lower() in extensions and f.is_file():
                try:
                    text = f.read_text(encoding="utf-8", errors="replace")
                    analysis = self.analyze_document(text, f.name)
                    results.append(
                        {
                            "file": str(f),
                            "filename": f.name,
                            "size": f.stat().st_size,
                            "analysis": asdict(analysis),
                        }
                    )
                except Exception as e:
                    logger.warning("Error analyzing %s: %s", f, e)
        return results

    # ── Legal-BERT Integration ───────────────────────────────

    def load_legal_bert(
        self,
        model_name: str = "nlpaueb/legal-bert-small-uncased",
    ) -> bool:
        """Download and load Legal-BERT for semantic analysis."""
        try:
            from transformers import AutoTokenizer, AutoModel

            logger.info("Loading %s ...", model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._legal_bert = AutoModel.from_pretrained(model_name)
            self._available_tools["legal_bert"] = True
            logger.info("Legal-BERT loaded: %s", model_name)
            return True
        except Exception as e:
            logger.error("Failed to load Legal-BERT: %s", e)
            return False

    def get_legal_embeddings(self, texts: List[str]) -> Optional[Any]:
        """Get semantic embeddings from Legal-BERT (CLS pooling)."""
        if not self._legal_bert or not self._tokenizer:
            return None
        try:
            import torch

            inputs = self._tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            with torch.no_grad():
                outputs = self._legal_bert(**inputs)
            return outputs.last_hidden_state[:, 0, :].numpy()
        except Exception as e:
            logger.error("Embedding error: %s", e)
            return None

    # ── Reporter Lookup ──────────────────────────────────────

    def lookup_reporter(self, abbreviation: str) -> Optional[Dict]:
        """Look up a legal reporter by abbreviation."""
        if not self._reporters_db:
            return None
        return self._reporters_db.get(abbreviation)

    def get_michigan_reporters(self) -> Dict:
        """Get all Michigan-specific reporters."""
        if not self._reporters_db:
            return {
                "Mich.": "Michigan Reports (Supreme Court)",
                "Mich. App.": "Michigan Appeals Reports",
                "N.W.2d": "North Western Reporter, 2d Series",
            }
        mi: Dict = {}
        for k, v in self._reporters_db.items():
            try:
                editions = v if isinstance(v, list) else [v]
                for ed in editions:
                    if isinstance(ed, dict):
                        ed_list = ed.get("editions", {})
                        for ed_info in (
                            ed_list.values()
                            if isinstance(ed_list, dict)
                            else []
                        ):
                            if isinstance(ed_info, dict):
                                cite_type = ed_info.get(
                                    "cite_type", ""
                                )
                                if "mich" in str(cite_type).lower():
                                    mi[k] = v
                                    break
            except Exception:
                pass
        return mi if mi else {
            "Mich.": "Michigan Reports (Supreme Court)",
            "Mich. App.": "Michigan Appeals Reports",
            "N.W.2d": "North Western Reporter, 2d Series",
        }

    # ── Database Persistence ─────────────────────────────────

    def save_results_to_db(
        self,
        conn: sqlite3.Connection,
        results: List[Dict],
        *,
        table: str = "nlp_analysis_results",
    ) -> int:
        """Persist analysis results to SQLite (batch insert).

        Creates the target table if it doesn't exist.
        Returns the number of rows inserted.
        """
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                filename TEXT,
                document_type TEXT,
                lane_assignment TEXT,
                citation_count INTEGER,
                entity_count INTEGER,
                confidence REAL,
                processing_time_ms REAL,
                raw_json TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        rows = [
            (
                r.get("file", ""),
                r.get("filename", ""),
                r["analysis"]["document_type"],
                r["analysis"]["lane_assignment"],
                len(r["analysis"]["citations"]),
                len(r["analysis"]["entities"]),
                r["analysis"]["confidence"],
                r["analysis"]["processing_time_ms"],
                json.dumps(r["analysis"]),
            )
            for r in results
        ]
        conn.executemany(
            f"""
            INSERT INTO {table}
                (file_path, filename, document_type, lane_assignment,
                 citation_count, entity_count, confidence,
                 processing_time_ms, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        return len(rows)


# ── Module-level convenience functions ───────────────────────

_engine: Optional[LegalNLPEngine] = None


def get_engine(db_path: Optional[str] = None) -> LegalNLPEngine:
    """Get or create the singleton engine instance."""
    global _engine
    if _engine is None:
        _engine = LegalNLPEngine(db_path)
    return _engine


def extract_citations(text: str) -> List[Citation]:
    """Convenience: extract citations from *text*."""
    return get_engine().extract_citations(text)


def extract_entities(text: str) -> List[LegalEntity]:
    """Convenience: extract legal entities from *text*."""
    return get_engine().extract_entities(text)


def analyze_document(text: str, filename: str = "") -> AnalysisResult:
    """Convenience: full document analysis."""
    return get_engine().analyze_document(text, filename)


def status() -> Dict[str, bool]:
    """Convenience: NLP tool availability."""
    return get_engine().status()
