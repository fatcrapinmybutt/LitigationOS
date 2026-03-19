#!/usr/bin/env python3
"""
APEX Reranker v2 — Cross-encoder reranking with legal-BERT
============================================================
When legal-BERT available: neural relevance scoring.
When not available: keyword overlap + TF-IDF cosine fallback.

Coexists with reranker.py (GGUF-based). This module uses a lighter
cross-encoder approach optimized for Michigan legal text.

Shadow-programmed: APEX_LLM_ENABLED gates neural features.
NEVER crashes — all methods try/except with fallbacks.
Never sets CWD to repo root (shadow modules).
Uses Path(__file__).parent for paths.
Thread-safe, UTF-8 safe, logging, type hints.
"""

import json
import logging
import math
import os
import re
import sys
import time
import threading
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── APEX Shadow Programming ────────────────────────────────────────
APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent

# ── Legal stop words ───────────────────────────────────────────────
_STOP_WORDS = frozenset({
    "the", "and", "for", "that", "this", "with", "was", "are", "not", "but",
    "have", "has", "had", "been", "from", "they", "will", "would", "could",
    "should", "their", "there", "what", "which", "when", "where", "who",
    "how", "can", "does", "did", "its", "you", "your", "she", "her", "his",
    "him", "our", "out", "all", "also", "than", "then", "into", "about",
    "were", "being", "other", "some", "more", "such", "each", "only",
})

# ── Legal domain boost terms ──────────────────────────────────────
_LEGAL_BOOST_TERMS = frozenset({
    "mcr", "mcl", "mre", "usc", "custody", "parenting", "disqualification",
    "recusal", "contempt", "sanctions", "appeal", "motion", "hearing",
    "ppo", "evidence", "due process", "alienation", "misconduct", "jtc",
    "discovery", "deposition", "subpoena", "judgment", "order", "brief",
    "statute", "rule", "canon", "amendment", "habeas", "mandamus",
    "ex parte", "void", "jurisdiction", "standing", "moot",
})


class RerankerV2:
    """Cross-encoder reranking with legal-BERT or keyword fallback.

    When APEX_LLM_ENABLED and legal-BERT model available: neural relevance scoring.
    Otherwise: keyword overlap + TF-IDF cosine + position scoring.
    """

    def __init__(self, model_name: str = "nlpaueb/legal-bert-small-uncased"):
        self._model_name = model_name
        self._model = None
        self._tokenizer = None
        self._model_loaded = False
        self._lock = threading.Lock()

    # ── Model Loading ──────────────────────────────────────────────

    def _load_model(self) -> bool:
        """Lazy-load legal-BERT cross-encoder. Returns True if loaded."""
        if self._model_loaded:
            return self._model is not None
        with self._lock:
            if self._model_loaded:
                return self._model is not None
            self._model_loaded = True
            if not APEX_LLM_ENABLED:
                logger.info("[RerankerV2] APEX_LLM_ENABLED=false — using keyword fallback")
                return False
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                import torch
                self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(self._model_name)
                self._model.eval()
                logger.info("[RerankerV2] legal-BERT loaded: %s", self._model_name)
                return True
            except ImportError:
                logger.info("[RerankerV2] transformers/torch not installed — using keyword fallback")
                return False
            except Exception as e:
                logger.warning("[RerankerV2] Model load failed: %s — using keyword fallback", e)
                return False

    # ── Public API ─────────────────────────────────────────────────

    def rerank(self, query: str, documents: list, top_k: int = 10) -> list:
        """Rerank documents by relevance to query. Returns sorted list.

        Each document should be a dict with a text field. Tries keys:
        'text', 'snippet', 'quote_text', 'full_text', 'content', 'body'.

        Returns:
            List of dicts with added 'rerank_score' (0.0-1.0) and 'rerank_method'.
        """
        try:
            if not query or not documents:
                return documents[:top_k] if documents else []

            has_model = self._load_model()
            if has_model:
                scored = self._neural_rerank(query, documents)
            else:
                scored = self._keyword_rerank(query, documents)

            # Sort descending by score
            scored.sort(key=lambda d: d.get("rerank_score", 0.0), reverse=True)
            return scored[:top_k]
        except Exception as e:
            logger.error("[RerankerV2] rerank failed: %s", e, exc_info=True)
            # Return original order as fallback
            for d in documents[:top_k]:
                d["rerank_score"] = 0.5
                d["rerank_method"] = "error_fallback"
            return documents[:top_k]

    def _neural_rerank(self, query: str, documents: list) -> list:
        """Use legal-BERT cross-encoder for reranking."""
        try:
            import torch
            results = []
            for doc in documents[:50]:  # Cap at 50 for performance
                text = self._extract_text(doc)
                if not text:
                    doc_copy = dict(doc)
                    doc_copy["rerank_score"] = 0.0
                    doc_copy["rerank_method"] = "neural_skip"
                    results.append(doc_copy)
                    continue

                # Tokenize query + document pair
                inputs = self._tokenizer(
                    query[:256], text[:512],
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                    padding=True,
                )
                with torch.no_grad():
                    outputs = self._model(**inputs)
                    logits = outputs.logits
                    # Use sigmoid for binary relevance score
                    if logits.shape[-1] == 1:
                        score = torch.sigmoid(logits).item()
                    else:
                        score = torch.softmax(logits, dim=-1)[0, -1].item()

                doc_copy = dict(doc)
                doc_copy["rerank_score"] = round(max(0.0, min(1.0, score)), 4)
                doc_copy["rerank_method"] = "neural_legal_bert"
                results.append(doc_copy)

            return results
        except Exception as e:
            logger.warning("[RerankerV2] Neural rerank failed: %s — falling back to keywords", e)
            return self._keyword_rerank(query, documents)

    def _keyword_rerank(self, query: str, documents: list) -> list:
        """Fallback: keyword overlap + TF-IDF cosine + position scoring."""
        try:
            query_tokens = self._tokenize(query)
            query_counter = Counter(query_tokens)
            if not query_tokens:
                for d in documents:
                    d["rerank_score"] = 0.5
                    d["rerank_method"] = "keyword_default"
                return documents

            # Build IDF from document set
            doc_count = len(documents) + 1
            df: Counter = Counter()
            doc_token_lists: List[List[str]] = []
            for doc in documents:
                text = self._extract_text(doc)
                tokens = self._tokenize(text)
                doc_token_lists.append(tokens)
                for unique_token in set(tokens):
                    df[unique_token] += 1

            results = []
            for idx, doc in enumerate(documents):
                doc_tokens = doc_token_lists[idx]
                if not doc_tokens:
                    doc_copy = dict(doc)
                    doc_copy["rerank_score"] = 0.0
                    doc_copy["rerank_method"] = "keyword_empty"
                    results.append(doc_copy)
                    continue

                doc_counter = Counter(doc_tokens)

                # TF-IDF cosine similarity
                cosine = self._tfidf_cosine(query_counter, doc_counter, df, doc_count)

                # Keyword overlap ratio
                query_set = set(query_tokens)
                doc_set = set(doc_tokens)
                overlap = len(query_set & doc_set) / len(query_set) if query_set else 0.0

                # Legal domain boost: bonus for legal terms in both query and doc
                legal_in_both = query_set & doc_set & _LEGAL_BOOST_TERMS
                legal_boost = min(0.15, len(legal_in_both) * 0.05)

                # Citation match bonus
                text = self._extract_text(doc)
                cite_re = re.compile(r'(?:MCR|MCL|MRE)\s*[\d.]+', re.IGNORECASE)
                q_cites = set(c.upper() for c in cite_re.findall(query))
                d_cites = set(c.upper() for c in cite_re.findall(text))
                cite_bonus = 0.1 if q_cites and (q_cites & d_cites) else 0.0

                # Position discount: early docs get slight penalty
                # (counteracts position bias from retrieval)
                position_factor = 1.0  # No position bias

                score = (
                    cosine * 0.45
                    + overlap * 0.30
                    + legal_boost
                    + cite_bonus
                ) * position_factor

                doc_copy = dict(doc)
                doc_copy["rerank_score"] = round(max(0.0, min(1.0, score)), 4)
                doc_copy["rerank_method"] = "keyword_tfidf"
                results.append(doc_copy)

            return results
        except Exception as e:
            logger.warning("[RerankerV2] Keyword rerank failed: %s", e)
            for d in documents:
                d["rerank_score"] = 0.5
                d["rerank_method"] = "keyword_error"
            return documents

    # ── Internal helpers ───────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize text into lowercase words, filtering stop words."""
        if not text:
            return []
        words = re.findall(r'[\w.]+', text.lower())
        return [w for w in words if w not in _STOP_WORDS and len(w) > 1]

    @staticmethod
    def _tfidf_cosine(
        q_counter: Counter, d_counter: Counter,
        df: Counter, doc_count: int,
    ) -> float:
        """Compute TF-IDF cosine similarity between query and document."""
        try:
            # Compute TF-IDF vectors
            vocab = set(q_counter.keys()) | set(d_counter.keys())
            if not vocab:
                return 0.0

            dot_product = 0.0
            q_norm_sq = 0.0
            d_norm_sq = 0.0

            for term in vocab:
                idf = math.log((doc_count + 1) / (df.get(term, 0) + 1)) + 1
                q_tfidf = q_counter.get(term, 0) * idf
                d_tfidf = d_counter.get(term, 0) * idf
                dot_product += q_tfidf * d_tfidf
                q_norm_sq += q_tfidf ** 2
                d_norm_sq += d_tfidf ** 2

            if q_norm_sq == 0 or d_norm_sq == 0:
                return 0.0

            return dot_product / (math.sqrt(q_norm_sq) * math.sqrt(d_norm_sq))
        except Exception:
            return 0.0

    @staticmethod
    def _extract_text(doc: dict) -> str:
        """Extract text content from a document dict."""
        for key in ("text", "snippet", "quote_text", "full_text",
                     "content", "body", "passage_text", "context", "text_content"):
            val = doc.get(key)
            if val and isinstance(val, str) and len(val) > 3:
                return val
        parts = [str(v) for v in doc.values() if isinstance(v, str) and len(str(v)) > 3]
        return " ".join(parts[:3]) if parts else ""

    # ── Status & Self-Test ─────────────────────────────────────────

    def status(self) -> Dict:
        """Return engine status."""
        return {
            "engine": "APEX-RerankerV2",
            "apex_llm_enabled": APEX_LLM_ENABLED,
            "model_name": self._model_name,
            "model_loaded": self._model is not None,
            "mode": "neural" if self._model is not None else "keyword_tfidf",
        }

    def self_test(self) -> Dict:
        """Run self-test with sample documents."""
        results = {"tests": [], "status": "pass"}
        try:
            test_docs = [
                {"snippet": "Judge McNeill denied parenting time without a hearing", "id": "1"},
                {"snippet": "The weather in Michigan is cold in winter", "id": "2"},
                {"snippet": "Ex parte communication between court and opposing party", "id": "3"},
                {"snippet": "MCR 2.003 requires disqualification for bias", "id": "4"},
                {"snippet": "Michigan recipes include pasties and cherry pie", "id": "5"},
            ]
            query = "judicial bias disqualification MCR 2.003"
            reranked = self.rerank(query, test_docs, top_k=3)

            results["tests"].append({
                "name": "rerank_count",
                "pass": len(reranked) == 3,
                "count": len(reranked),
            })
            results["tests"].append({
                "name": "rerank_has_scores",
                "pass": all("rerank_score" in d for d in reranked),
            })
            # Top result should be the MCR 2.003 doc or the ex parte doc
            top_id = reranked[0].get("id") if reranked else None
            results["tests"].append({
                "name": "top_result_relevant",
                "pass": top_id in ("3", "4"),
                "top_id": top_id,
                "top_score": reranked[0].get("rerank_score") if reranked else 0,
            })

            results["status"] = "pass" if all(t["pass"] for t in results["tests"]) else "partial"
        except Exception as e:
            results["status"] = "fail"
            results["error"] = str(e)
        return results


# ── CLI Entry Point ────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    rr = RerankerV2()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(json.dumps(rr.status(), indent=2))
    elif cmd == "self-test":
        print(json.dumps(rr.self_test(), indent=2))
    else:
        print(json.dumps(rr.status(), indent=2))
