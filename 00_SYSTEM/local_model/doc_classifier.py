"""
Document Intelligence Classifier — MBP LitigationOS 2026
=========================================================
ML-powered classifier that identifies document types from content.
Trained on 308K+ evidence quotes and 18K+ documents from litigation_context.db.

Document Types:
    court_order, transcript, motion, brief, evidence, correspondence,
    financial, medical, ppo, custody, discovery, chatgpt, personal,
    administrative
"""

import os
import re
import json
import sqlite3
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from collections import Counter

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import SGDClassifier
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        classification_report
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False
    try:
        import pickle
    except ImportError:
        pass

logger = logging.getLogger("doc_classifier")

# ── Target document type taxonomy ──────────────────────────────────────
DOC_TYPES = [
    "court_order", "transcript", "motion", "brief", "evidence",
    "correspondence", "financial", "medical", "ppo", "custody",
    "discovery", "chatgpt", "personal", "administrative",
]

# Map existing DB categories → target types
CATEGORY_MAP = {
    # evidence_quotes categories
    "court_order": "court_order",
    "JUDGE_ORDER": "court_order",
    "EX_PARTE_ORDER": "court_order",
    "court_filing": "motion",
    "general_court_doc": "court_order",
    "transcript": "transcript",
    "TRANSCRIPT": "transcript",
    "hearing": "transcript",
    "motion": "motion",
    "MOTION": "motion",
    "brief": "brief",
    "evidence": "evidence",
    "exhibit": "evidence",
    "ppo": "ppo",
    "PPO": "ppo",
    "custody": "custody",
    "CUSTODY_ORDER": "custody",
    "discovery": "discovery",
    "complaint": "motion",
    "affidavit": "evidence",
    "response": "motion",
    "report": "administrative",
    "docket": "administrative",
    "DOCKET_ENTRY": "administrative",
    # documents categories
    "MEDICAL_RECORD": "medical",
    "EMAIL": "correspondence",
    "FINANCIAL": "financial",
    "NOTICE": "administrative",
    "JTC_FILING": "administrative",
    "OPPOSING_FILING": "motion",
    "unclassified": None,
    "UNCLASSIFIED": None,
}

# ── Path-based classification patterns ─────────────────────────────────
PATH_PATTERNS = {
    "court_order": [r"order", r"ruling", r"judgment", r"decree"],
    "transcript": [r"transcript", r"hearing", r"deposition"],
    "motion": [r"motion", r"complaint", r"petition", r"response"],
    "brief": [r"brief", r"memorand", r"argument"],
    "evidence": [r"evidence", r"exhibit", r"affidavit", r"declaration"],
    "correspondence": [r"email", r"letter", r"correspondence", r"mail"],
    "financial": [r"financ", r"income", r"tax", r"bank", r"statement"],
    "medical": [r"medical", r"health", r"doctor", r"hospital", r"therap"],
    "ppo": [r"ppo", r"protection.?order", r"restraining"],
    "custody": [r"custody", r"parenting", r"visitation", r"child"],
    "discovery": [r"discovery", r"interrogat", r"subpoena", r"request.*produc"],
    "chatgpt": [r"chatgpt", r"ai.?gen", r"gpt", r"copilot"],
    "personal": [r"personal", r"text", r"message", r"sms", r"chat"],
    "administrative": [r"foc", r"scao", r"admin", r"report", r"docket", r"jtc"],
}

# ── Keyword-based classification rules ─────────────────────────────────
KEYWORD_RULES = {
    "court_order": [
        "it is hereby ordered", "the court orders", "order of the court",
        "so ordered", "ruling", "judgment", "decree", "is granted",
        "is denied", "upon consideration",
    ],
    "transcript": [
        "the court:", "q.", "a.", "direct examination", "cross-examination",
        "the witness", "proceedings", "on the record", "off the record",
        "court reporter", "hearing held",
    ],
    "motion": [
        "plaintiff moves", "defendant moves", "motion to", "comes now",
        "respectfully requests", "wherefore", "prayer for relief",
        "movant", "relief requested",
    ],
    "brief": [
        "statement of facts", "argument", "conclusion", "issue presented",
        "question presented", "standard of review", "summary of argument",
        "appellate brief", "amicus",
    ],
    "evidence": [
        "exhibit", "attached hereto", "true and correct copy", "affidavit",
        "declaration", "sworn", "under penalty of perjury",
    ],
    "correspondence": [
        "dear", "sincerely", "regards", "from:", "to:", "subject:",
        "sent:", "cc:", "re:", "thank you for",
    ],
    "financial": [
        "income", "expense", "bank statement", "tax return", "w-2",
        "1099", "gross income", "net income", "assets", "liabilities",
        "child support", "spousal support",
    ],
    "medical": [
        "diagnosis", "patient", "treatment", "medication", "therapy",
        "medical record", "prescription", "symptoms", "prognosis",
        "clinical", "dr.", "physician",
    ],
    "ppo": [
        "personal protection order", "ppo", "restraining order",
        "no contact", "shall not", "protected person", "respondent shall",
        "mcl 600.2950",
    ],
    "custody": [
        "best interest", "custodial environment", "parenting time",
        "mcl 722.23", "factor", "custody", "guardian ad litem",
        "friend of the court", "foc recommendation",
    ],
    "discovery": [
        "interrogatory", "request for production", "request to admit",
        "discovery", "subpoena", "deponent", "privilege log",
        "mcr 2.302", "mcr 2.310",
    ],
    "chatgpt": [
        "chatgpt", "ai-generated", "language model", "generated by",
        "openai", "gpt-4", "copilot analysis", "ai research",
    ],
    "personal": [
        "text message", "imessage", "sms", "hey", "lol", "ok",
        "screenshot", "messenger", "whatsapp",
    ],
    "administrative": [
        "friend of the court", "foc report", "scao", "case management",
        "docket entry", "filing fee", "proof of service",
        "certificate of service", "administrative order",
    ],
}

# Legal citation patterns
CITATION_PATTERNS = {
    "mcr": re.compile(r"MCR\s+\d+\.\d+", re.IGNORECASE),
    "mcl": re.compile(r"MCL\s+\d+\.\d+", re.IGNORECASE),
    "mre": re.compile(r"MRE\s+\d+", re.IGNORECASE),
    "case_law": re.compile(
        r"\d+\s+(?:Mich\s+App|Mich|NW(?:2d)?)\s+\d+", re.IGNORECASE
    ),
    "usc": re.compile(r"\d+\s+U\.?S\.?C\.?\s+§?\s*\d+", re.IGNORECASE),
}


def _save_model(obj, path):
    """Save model object to disk."""
    if HAS_JOBLIB:
        joblib.dump(obj, path)
    else:
        import pickle
        with open(path, "wb") as f:
            pickle.dump(obj, f)


def _load_model(path):
    """Load model object from disk."""
    if HAS_JOBLIB:
        return joblib.load(path)
    else:
        import pickle
        with open(path, "rb") as f:
            return pickle.load(f)


class DocumentClassifier:
    """ML-powered document classifier for LitigationOS ingestion pipeline."""

    TFIDF_PATH = "doc_classifier_tfidf.pkl"
    MODEL_PATH = "doc_classifier_model.pkl"
    META_PATH = "doc_classifier_meta.json"

    def __init__(self, db_path=None, model_dir=None):
        self.db_path = db_path or r"C:\Users\andre\LitigationOS\litigation_context.db"
        self.model_dir = model_dir or os.path.join(
            r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model", "model_data"
        )
        os.makedirs(self.model_dir, exist_ok=True)

        self._vectorizer = None
        self._model = None
        self._meta = None
        self._model_loaded = False

    # ── Database helpers ───────────────────────────────────────────────

    def _get_conn(self):
        """Get a database connection with error handling."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error("DB connection failed: %s", e)
            return None

    def _query_db(self, sql, params=(), fetchone=False):
        """Execute a query and return results."""
        conn = self._get_conn()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchone() if fetchone else cur.fetchall()
        except Exception as e:
            logger.error("DB query failed: %s — %s", sql[:80], e)
            return None
        finally:
            conn.close()

    # ── Data loading ───────────────────────────────────────────────────

    def _load_training_data(self):
        """Load labeled data from evidence_quotes and documents tables."""
        texts, labels = [], []

        # Source 1: evidence_quotes with known categories
        conn = self._get_conn()
        if not conn:
            return texts, labels
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT quote_text, evidence_category FROM evidence_quotes "
                "WHERE evidence_category IS NOT NULL AND quote_text IS NOT NULL "
                "AND LENGTH(quote_text) > 20"
            )
            for row in cur:
                cat = CATEGORY_MAP.get(row[1])
                if cat and row[0]:
                    texts.append(row[0])
                    labels.append(cat)
        except Exception as e:
            logger.error("Failed loading evidence_quotes: %s", e)
        finally:
            conn.close()

        # Source 2: documents — classify by file_path patterns
        conn = self._get_conn()
        if not conn:
            return texts, labels
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT d.file_path, d.evidence_category, "
                "GROUP_CONCAT(p.text_content, ' ') as full_text "
                "FROM documents d LEFT JOIN pages p ON p.document_id = d.id "
                "WHERE d.evidence_category IS NOT NULL "
                "GROUP BY d.id "
                "HAVING full_text IS NOT NULL AND LENGTH(full_text) > 50 "
                "LIMIT 5000"
            )
            for row in cur:
                fp = row[0] or ""
                cat = CATEGORY_MAP.get(row[1])
                if not cat:
                    cat = self._classify_by_path(fp)
                if cat and row[2]:
                    # Use first 2000 chars to keep training manageable
                    texts.append(row[2][:2000])
                    labels.append(cat)
        except Exception as e:
            logger.error("Failed loading documents: %s", e)
        finally:
            conn.close()

        logger.info("Loaded %d training samples across %d classes",
                     len(texts), len(set(labels)))
        return texts, labels

    def _classify_by_path(self, file_path):
        """Classify a document by its file path patterns."""
        fp_lower = file_path.lower()
        for doc_type, patterns in PATH_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, fp_lower):
                    return doc_type
        return None

    # ── Training ───────────────────────────────────────────────────────

    def train(self, force=False):
        """
        Train the document classifier on existing labeled data.

        Args:
            force: Retrain even if model already exists and data hasn't changed.

        Returns:
            dict with accuracy, precision, recall, f1, samples_used, classes
        """
        if not HAS_SKLEARN:
            return {
                "error": "sklearn not available — using rule-based fallback",
                "fallback": True,
            }

        tfidf_path = os.path.join(self.model_dir, self.TFIDF_PATH)
        model_path = os.path.join(self.model_dir, self.MODEL_PATH)
        meta_path = os.path.join(self.model_dir, self.META_PATH)

        # Check if retrain is needed
        if not force and os.path.exists(model_path) and os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                # Check data freshness
                current_count = self._query_db(
                    "SELECT COUNT(*) FROM evidence_quotes "
                    "WHERE evidence_category IS NOT NULL", fetchone=True
                )
                if current_count and current_count[0] == meta.get("source_rows"):
                    logger.info("Model is current — skipping retrain")
                    return meta.get("metrics", {})
            except Exception:
                pass

        logger.info("Training document classifier...")
        texts, labels = self._load_training_data()
        if len(texts) < 100:
            return {"error": "Insufficient training data", "samples": len(texts)}

        # Balance classes — cap dominant classes to prevent bias
        class_counts = Counter(labels)
        max_per_class = max(5000, int(len(texts) / len(class_counts) * 3))
        balanced_texts, balanced_labels = [], []
        class_seen = Counter()
        for t, l in zip(texts, labels):
            if class_seen[l] < max_per_class:
                balanced_texts.append(t)
                balanced_labels.append(l)
                class_seen[l] += 1
        texts, labels = balanced_texts, balanced_labels

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )

        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(
            max_features=20000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            max_df=0.95,
            strip_accents="unicode",
        )
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)

        # Train SGDClassifier (supports partial_fit for incremental updates)
        model = SGDClassifier(
            loss="modified_huber",  # gives probability estimates
            penalty="l2",
            alpha=1e-4,
            max_iter=1000,
            tol=1e-3,
            random_state=42,
            class_weight="balanced",
        )
        model.fit(X_train_vec, y_train)

        # Evaluate
        y_pred = model.predict(X_test_vec)
        present_labels = sorted(set(y_test) | set(y_pred))
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

        metrics = {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "samples_used": len(texts),
            "classes": present_labels,
        }

        logger.info("Accuracy=%.4f  F1=%.4f  Samples=%d  Classes=%d",
                     acc, f1, len(texts), len(present_labels))

        # Save models
        _save_model(vectorizer, tfidf_path)
        _save_model(model, model_path)

        # Save metadata
        source_rows = self._query_db(
            "SELECT COUNT(*) FROM evidence_quotes "
            "WHERE evidence_category IS NOT NULL", fetchone=True
        )
        meta = {
            "trained_at": datetime.now().isoformat(),
            "source_rows": source_rows[0] if source_rows else 0,
            "metrics": metrics,
            "class_distribution": dict(Counter(labels)),
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        self._vectorizer = vectorizer
        self._model = model
        self._meta = meta
        self._model_loaded = True

        return metrics

    # ── Model loading ──────────────────────────────────────────────────

    def _ensure_model(self):
        """Load trained model from disk if not already loaded."""
        if self._model_loaded:
            return True

        tfidf_path = os.path.join(self.model_dir, self.TFIDF_PATH)
        model_path = os.path.join(self.model_dir, self.MODEL_PATH)
        meta_path = os.path.join(self.model_dir, self.META_PATH)

        if not os.path.exists(model_path) or not os.path.exists(tfidf_path):
            return False

        try:
            self._vectorizer = _load_model(tfidf_path)
            self._model = _load_model(model_path)
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    self._meta = json.load(f)
            self._model_loaded = True
            return True
        except Exception as e:
            logger.error("Failed loading model: %s", e)
            return False

    # ── Classification ─────────────────────────────────────────────────

    def classify(self, text, return_proba=False):
        """
        Classify a document's text content.

        Args:
            text: Document text to classify.
            return_proba: If True, return per-class probabilities.

        Returns:
            dict with doc_type, confidence (and probabilities if requested)
        """
        if not text or len(text.strip()) < 10:
            return {"doc_type": "evidence", "confidence": 0.0, "method": "default"}

        # Try ML model first
        if HAS_SKLEARN and self._ensure_model():
            try:
                X = self._vectorizer.transform([text])
                pred = self._model.predict(X)[0]
                result = {"doc_type": pred, "method": "ml"}

                # Get confidence via decision_function or predict_proba
                try:
                    proba = self._model.predict_proba(X)[0]
                    classes = list(self._model.classes_)
                    result["confidence"] = round(float(max(proba)), 4)
                    if return_proba:
                        result["probabilities"] = {
                            c: round(float(p), 4) for c, p in zip(classes, proba)
                        }
                except Exception:
                    result["confidence"] = 0.8

                return result
            except Exception as e:
                logger.warning("ML classification failed, using rules: %s", e)

        # Fallback to rule-based
        return self.get_classification_rules(text)

    def classify_file(self, file_path):
        """
        Read a file and classify its content.

        Args:
            file_path: Path to the file to classify.

        Returns:
            dict with file_path, doc_type, confidence, summary
        """
        file_path = str(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        # Skip binary files
        binary_exts = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".png",
                       ".jpg", ".jpeg", ".gif", ".zip", ".exe", ".dll"}
        if ext in binary_exts:
            # Classify by path only
            path_type = self._classify_by_path(file_path)
            return {
                "file_path": file_path,
                "doc_type": path_type or "evidence",
                "confidence": 0.5,
                "summary": f"Binary file classified by path ({ext})",
                "method": "path",
            }

        # Read text content
        text = ""
        try:
            if ext == ".json":
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                text = json.dumps(data, indent=2)[:5000]
            elif ext == ".csv":
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= 10:
                            break
                        lines.append(line)
                    text = "".join(lines)
            else:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read(10000)
        except Exception as e:
            return {
                "file_path": file_path,
                "doc_type": self._classify_by_path(file_path) or "evidence",
                "confidence": 0.3,
                "summary": f"Read error: {e}",
                "method": "path_fallback",
            }

        if not text.strip():
            return {
                "file_path": file_path,
                "doc_type": self._classify_by_path(file_path) or "evidence",
                "confidence": 0.2,
                "summary": "Empty file",
                "method": "path_fallback",
            }

        result = self.classify(text)
        # Boost confidence if path agrees with ML prediction
        path_type = self._classify_by_path(file_path)
        if path_type and path_type == result["doc_type"]:
            result["confidence"] = min(1.0, result.get("confidence", 0.5) + 0.1)

        result["file_path"] = file_path
        result["summary"] = text[:150].replace("\n", " ").strip()
        return result

    def batch_classify(self, file_paths=None, scan_dir=None, limit=500):
        """
        Classify multiple files.

        Args:
            file_paths: List of file paths to classify.
            scan_dir: Directory to walk for files.
            limit: Maximum number of files to process.

        Returns:
            dict with classified count, by_type breakdown, avg_confidence, results
        """
        if file_paths is None:
            file_paths = []

        if scan_dir and os.path.isdir(scan_dir):
            count = 0
            for root, _dirs, files in os.walk(scan_dir):
                for fname in files:
                    if count >= limit:
                        break
                    file_paths.append(os.path.join(root, fname))
                    count += 1
                if count >= limit:
                    break

        file_paths = file_paths[:limit]
        results = []
        by_type = Counter()
        total_conf = 0.0

        for fp in file_paths:
            try:
                r = self.classify_file(fp)
                results.append(r)
                by_type[r["doc_type"]] += 1
                total_conf += r.get("confidence", 0.0)
            except Exception as e:
                logger.warning("Skipping %s: %s", fp, e)

        classified = len(results)
        return {
            "classified": classified,
            "by_type": dict(by_type),
            "avg_confidence": round(total_conf / max(classified, 1), 4),
            "results": results,
        }

    # ── Feature extraction ─────────────────────────────────────────────

    def extract_features(self, text):
        """
        Extract structured features beyond TF-IDF from document text.

        Returns:
            dict of feature names → values
        """
        if not text:
            return {}

        text_lower = text.lower()

        # Legal citation counts
        citation_counts = {}
        total_citations = 0
        for ctype, pattern in CITATION_PATTERNS.items():
            matches = pattern.findall(text)
            citation_counts[f"cite_{ctype}"] = len(matches)
            total_citations += len(matches)

        # Date mentions
        date_pattern = re.compile(
            r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
            r"(?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+\d{1,2},?\s+\d{4})\b",
            re.IGNORECASE,
        )
        date_count = len(date_pattern.findall(text))

        # Party name mentions
        party_names = ["pigors", "watson", "tiffany", "andrew", "mcneill"]
        party_mentions = sum(text_lower.count(name) for name in party_names)

        # Legal keyword density
        legal_terms = [
            "court", "order", "motion", "plaintiff", "defendant", "custody",
            "hearing", "evidence", "ruling", "objection", "sustained",
            "overruled", "stipulate", "statute", "pursuant", "mcr", "mcl",
        ]
        word_count = max(len(text.split()), 1)
        legal_count = sum(text_lower.count(t) for t in legal_terms)
        legal_density = round(legal_count / word_count, 4)

        # Sentence structure analysis
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        avg_sentence_len = (
            round(sum(len(s.split()) for s in sentences) / max(len(sentences), 1), 1)
        )
        # Formal indicators
        formal_markers = [
            "hereby", "whereas", "thereof", "herein", "pursuant",
            "aforementioned", "notwithstanding", "wherefore",
        ]
        formality_score = sum(text_lower.count(m) for m in formal_markers)

        features = {
            **citation_counts,
            "total_citations": total_citations,
            "date_mentions": date_count,
            "party_mentions": party_mentions,
            "legal_keyword_density": legal_density,
            "word_count": word_count,
            "avg_sentence_length": avg_sentence_len,
            "formality_score": formality_score,
            "sentence_count": len(sentences),
            "has_case_caption": int(bool(re.search(
                r"(?:plaintiff|defendant|appellant|appellee)", text_lower
            ))),
            "has_certificate_of_service": int(
                "certificate of service" in text_lower
            ),
            "has_signature_block": int(bool(re.search(
                r"respectfully submitted|/s/|___", text_lower
            ))),
        }
        return features

    # ── Rule-based fallback ────────────────────────────────────────────

    def get_classification_rules(self, text=None):
        """
        Rule-based classifier fallback when ML model is unavailable.

        Args:
            text: Optional text to classify. If None, returns the rules dict.

        Returns:
            If text given: dict with doc_type, confidence, method='rules'
            If text is None: the KEYWORD_RULES dict
        """
        if text is None:
            return KEYWORD_RULES

        text_lower = text.lower()
        scores = {}

        # Keyword matching
        for doc_type, keywords in KEYWORD_RULES.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[doc_type] = score

        # Citation pattern boost
        features = self.extract_features(text)
        if features.get("total_citations", 0) > 3:
            for dt in ["motion", "brief", "court_order"]:
                scores[dt] = scores.get(dt, 0) + 2

        if features.get("has_certificate_of_service"):
            for dt in ["motion", "brief"]:
                scores[dt] = scores.get(dt, 0) + 3

        if features.get("formality_score", 0) < 2:
            for dt in ["personal", "correspondence"]:
                scores[dt] = scores.get(dt, 0) + 1

        if not scores:
            return {"doc_type": "evidence", "confidence": 0.1, "method": "rules"}

        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        total_score = sum(scores.values())
        confidence = round(min(max_score / max(total_score, 1), 1.0), 4)

        return {
            "doc_type": best_type,
            "confidence": confidence,
            "method": "rules",
        }

    # ── Incremental update ─────────────────────────────────────────────

    def update_model(self, new_texts, new_labels):
        """
        Incrementally update the model with new labeled data.

        Uses partial_fit for SGDClassifier, else retrains from scratch.

        Args:
            new_texts: list of document texts
            new_labels: list of corresponding labels

        Returns:
            dict with status and sample count
        """
        if not HAS_SKLEARN:
            return {"error": "sklearn not available"}

        if not new_texts or not new_labels:
            return {"error": "No data provided"}

        if len(new_texts) != len(new_labels):
            return {"error": "texts and labels must be same length"}

        # Validate labels
        valid = [l for l in new_labels if l in DOC_TYPES]
        if len(valid) != len(new_labels):
            invalid = set(new_labels) - set(DOC_TYPES)
            return {"error": f"Invalid labels: {invalid}"}

        if not self._ensure_model():
            # No existing model — do full train
            logger.info("No existing model — running full train")
            return self.train(force=True)

        try:
            X_new = self._vectorizer.transform(new_texts)
            self._model.partial_fit(X_new, new_labels, classes=DOC_TYPES)

            # Save updated model
            model_path = os.path.join(self.model_dir, self.MODEL_PATH)
            _save_model(self._model, model_path)

            # Update metadata
            meta_path = os.path.join(self.model_dir, self.META_PATH)
            if self._meta:
                self._meta["last_updated"] = datetime.now().isoformat()
                self._meta["incremental_samples"] = (
                    self._meta.get("incremental_samples", 0) + len(new_texts)
                )
                with open(meta_path, "w") as f:
                    json.dump(self._meta, f, indent=2)

            return {
                "status": "updated",
                "samples_added": len(new_texts),
                "method": "partial_fit",
            }
        except Exception as e:
            logger.error("Incremental update failed: %s", e)
            return {"error": str(e)}

    # ── Model stats ────────────────────────────────────────────────────

    def get_model_stats(self):
        """
        Get model status and statistics.

        Returns:
            dict with model_exists, last_trained, accuracy, feature_count,
            class_distribution
        """
        model_path = os.path.join(self.model_dir, self.MODEL_PATH)
        tfidf_path = os.path.join(self.model_dir, self.TFIDF_PATH)
        meta_path = os.path.join(self.model_dir, self.META_PATH)

        stats = {
            "model_exists": os.path.exists(model_path),
            "tfidf_exists": os.path.exists(tfidf_path),
            "last_trained": None,
            "accuracy": None,
            "feature_count": None,
            "class_distribution": None,
            "sklearn_available": HAS_SKLEARN,
            "numpy_available": HAS_NUMPY,
            "joblib_available": HAS_JOBLIB,
        }

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                stats["last_trained"] = meta.get("trained_at")
                metrics = meta.get("metrics", {})
                stats["accuracy"] = metrics.get("accuracy")
                stats["f1"] = metrics.get("f1")
                stats["samples_used"] = metrics.get("samples_used")
                stats["classes"] = metrics.get("classes")
                stats["class_distribution"] = meta.get("class_distribution")
            except Exception:
                pass

        if self._ensure_model() and self._vectorizer is not None:
            try:
                stats["feature_count"] = len(self._vectorizer.get_feature_names_out())
            except AttributeError:
                try:
                    stats["feature_count"] = len(self._vectorizer.vocabulary_)
                except Exception:
                    pass

        # DB stats
        try:
            row = self._query_db(
                "SELECT COUNT(*) FROM evidence_quotes "
                "WHERE evidence_category IS NOT NULL", fetchone=True
            )
            stats["db_labeled_quotes"] = row[0] if row else 0
            row = self._query_db("SELECT COUNT(*) FROM documents", fetchone=True)
            stats["db_total_documents"] = row[0] if row else 0
        except Exception:
            pass

        return stats


# ── Main entry point ───────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
    MODEL_DIR = os.path.join(
        r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model", "model_data"
    )

    clf = DocumentClassifier(db_path=DB, model_dir=MODEL_DIR)

    # 1) Print model stats
    print("\n═══ Model Stats (pre-train) ═══")
    stats = clf.get_model_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # 2) Train model
    print("\n═══ Training Classifier ═══")
    metrics = clf.train(force=True)
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # 3) Sample classifications
    print("\n═══ Sample Classifications ═══")
    samples = [
        (
            "IT IS HEREBY ORDERED that defendant's motion is denied. "
            "The Court finds no basis under MCR 2.116(C)(10) for summary disposition.",
            "court_order",
        ),
        (
            "Q. Can you state your name for the record? "
            "A. Andrew Pigors. Q. And where do you reside?",
            "transcript",
        ),
        (
            "Plaintiff respectfully moves this Court for an order compelling "
            "defendant to respond to discovery requests pursuant to MCR 2.313.",
            "motion",
        ),
        (
            "hey can u pick up the kids at 3 today? i have a dr appt lol",
            "personal",
        ),
        (
            "The Friend of the Court recommends that parenting time be modified "
            "to a 50/50 schedule per SCAO form FOC 67.",
            "administrative",
        ),
    ]
    for text, expected in samples:
        result = clf.classify(text)
        match = "✓" if result["doc_type"] == expected else "✗"
        print(f"  {match} expected={expected:15s} got={result['doc_type']:15s} "
              f"conf={result.get('confidence', 0):.3f} [{result['method']}]")

    # 4) Feature extraction demo
    print("\n═══ Feature Extraction Demo ═══")
    demo_text = (
        "Pursuant to MCR 2.003(C)(1), Plaintiff moves for disqualification "
        "of Hon. Jenny L. McNeill. Under MCL 722.23, the best interest "
        "factors were not properly weighed. See Vodvarka v Grasher, "
        "259 Mich App 499 (2003)."
    )
    features = clf.extract_features(demo_text)
    for k, v in features.items():
        print(f"  {k}: {v}")

    # 5) Post-train stats
    print("\n═══ Model Stats (post-train) ═══")
    stats = clf.get_model_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n═══ Document Classifier Ready ═══")
