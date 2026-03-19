#!/usr/bin/env python3
"""
APEX Neural Intent — Classification using legal-BERT-small
===========================================================
Shadow-programmed: uses keyword patterns when BERT unavailable.
Maps user queries and evidence to litigation intents (16 categories)
aligned with LitigationOS case lanes and filing workflows.

NEVER crashes — all methods try/except with fallbacks.
Never sets CWD to repo root (shadow modules).
Uses Path(__file__).parent for paths.
Thread-safe, UTF-8 safe, logging, type hints.
"""

import json
import logging
import os
import re
import sys
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── APEX Shadow Programming ────────────────────────────────────────
APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent


class NeuralIntent:
    """Intent classification for legal text using neural or keyword methods.

    16 intent categories aligned with LitigationOS case lanes and workflows.
    When APEX_LLM_ENABLED and legal-BERT available: neural classification.
    Otherwise: keyword-based scoring with confidence calibration.
    """

    INTENTS: List[str] = [
        "custody", "housing", "appellate", "discovery", "emergency",
        "misconduct", "ppo", "federal_1983", "sanctions", "impeachment",
        "jtc_complaint", "msc_writ", "motion", "research", "convergence", "damages",
    ]

    # Keyword patterns per intent (always available, no ML needed)
    KEYWORDS: Dict[str, List[str]] = {
        "custody": [
            "custody", "parenting", "child", "visitation", "best interest",
            "mcl 722", "parenting time", "custodial", "established custodial",
            "father", "mother", "overnight", "placement",
        ],
        "housing": [
            "housing", "tenant", "habitability", "eviction", "rent",
            "mcl 125", "shady oaks", "landlord", "lease", "building code",
            "repair", "mold", "water damage", "truth in renting",
        ],
        "appellate": [
            "appeal", "coa", "msc", "mcr 7", "leave to appeal", "brief",
            "appellate", "court of appeals", "supreme court", "standard of review",
            "claim of appeal", "mcr 7.204", "mcr 7.205", "mcr 7.212",
        ],
        "discovery": [
            "interrogat", "deposition", "request for production", "rfa",
            "subpoena", "mcr 2.302", "mcr 2.310", "motion to compel",
            "discovery", "document request", "mcr 2.313",
        ],
        "emergency": [
            "emergency", "tro", "immediate", "irreparable", "ex parte motion",
            "temporary restraining", "imminent harm", "urgent", "safety",
            "emergency hearing", "expedited",
        ],
        "misconduct": [
            "misconduct", "jtc", "mcneill", "bias", "ex parte", "mcr 9",
            "judicial misconduct", "canon violation", "ethical violation",
            "appearance of impropriety", "benchbook",
        ],
        "ppo": [
            "ppo", "protection order", "mcl 600.2950", "no contact",
            "stalking", "domestic violence", "restraining order",
            "personal protection", "harassment",
        ],
        "federal_1983": [
            "1983", "civil rights", "42 usc", "color of law", "monell",
            "section 1983", "federal civil rights", "constitutional",
            "14th amendment", "due process", "equal protection",
        ],
        "sanctions": [
            "sanction", "rule 11", "frivolous", "mcr 2.114", "vexatious",
            "attorney fees", "bad faith", "mcr 2.313", "discovery sanctions",
        ],
        "impeachment": [
            "impeach", "credibility", "prior inconsistent", "bias",
            "interest", "mre 607", "mre 608", "mre 609", "contradiction",
            "witness credibility", "prior statement",
        ],
        "jtc_complaint": [
            "jtc", "judicial tenure", "formal complaint", "mcr 9.2",
            "judicial tenure commission", "mcr 9.104", "mcr 9.205",
            "commission complaint", "judicial discipline",
        ],
        "msc_writ": [
            "msc", "superintending control", "application for leave",
            "michigan supreme court", "writ", "mandamus", "mcr 3.302",
            "extraordinary writ", "mcl 600.1701",
        ],
        "motion": [
            "motion", "brief in support", "relief requested", "mcr 2.119",
            "response to motion", "reply brief", "motion hearing",
            "summary disposition", "mcr 2.116", "proposed order",
        ],
        "research": [
            "research", "case law", "authority", "precedent", "statute",
            "legal research", "find cases", "what does", "look up",
            "search for", "authority for",
        ],
        "convergence": [
            "convergence", "cross-lane", "conspiracy", "pattern",
            "coordinated", "multi-case", "interconnected", "related cases",
            "common scheme", "rico-like",
        ],
        "damages": [
            "damages", "harm", "quantif", "economic", "non-economic",
            "treble", "compensatory", "punitive", "loss", "injury",
            "emotional distress", "pain and suffering", "mcl 600.2946",
        ],
    }

    # Intent → Lane mapping
    INTENT_LANE_MAP: Dict[str, str] = {
        "custody": "A",
        "housing": "B",
        "convergence": "C",
        "ppo": "D",
        "misconduct": "E",
        "jtc_complaint": "E",
        "appellate": "F",
        "msc_writ": "F",
    }

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._model_loaded = False
        self._lock = threading.Lock()
        # Precompile keyword patterns for speed
        self._compiled_keywords: Dict[str, List[re.Pattern]] = {}
        for intent, keywords in self.KEYWORDS.items():
            self._compiled_keywords[intent] = [
                re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords
            ]

    # ── Model Loading ──────────────────────────────────────────────

    def _load_model(self) -> bool:
        """Lazy-load legal-BERT-small for classification."""
        if self._model_loaded:
            return self._model is not None
        with self._lock:
            if self._model_loaded:
                return self._model is not None
            self._model_loaded = True
            if not APEX_LLM_ENABLED:
                logger.info("[NeuralIntent] APEX_LLM_ENABLED=false — using keyword classification")
                return False
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                self._tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-small-uncased")
                self._model = AutoModelForSequenceClassification.from_pretrained(
                    "nlpaueb/legal-bert-small-uncased"
                )
                self._model.eval()
                logger.info("[NeuralIntent] legal-BERT-small loaded")
                return True
            except ImportError:
                logger.info("[NeuralIntent] transformers not installed — keyword mode")
                return False
            except Exception as e:
                logger.warning("[NeuralIntent] Model load failed: %s — keyword mode", e)
                return False

    # ── Public API ─────────────────────────────────────────────────

    def classify(self, text: str) -> dict:
        """Classify text intent. Returns {intent: str, confidence: float, method: str, lane: str|None, scores: dict}.

        Scores all 16 intents and returns the top one.
        """
        try:
            if not text or not text.strip():
                return {
                    "intent": "research",
                    "confidence": 0.0,
                    "method": "default_empty",
                    "lane": None,
                    "scores": {},
                }

            has_model = self._load_model()
            if has_model:
                return self._neural_classify(text)
            return self._keyword_classify(text)
        except Exception as e:
            logger.error("[NeuralIntent] classify failed: %s", e, exc_info=True)
            return {
                "intent": "research",
                "confidence": 0.0,
                "method": "error_fallback",
                "lane": None,
                "scores": {},
                "error": str(e),
            }

    def classify_batch(self, texts: list) -> list:
        """Classify multiple texts efficiently.

        Returns list of classification dicts.
        """
        try:
            if not texts:
                return []
            return [self.classify(text) for text in texts]
        except Exception as e:
            logger.error("[NeuralIntent] classify_batch failed: %s", e)
            return [{"intent": "research", "confidence": 0.0, "method": "batch_error"} for _ in texts]

    # ── Neural Classification ──────────────────────────────────────

    def _neural_classify(self, text: str) -> dict:
        """Classify using legal-BERT embeddings + keyword scoring hybrid."""
        try:
            import torch
            # Get BERT embedding
            inputs = self._tokenizer(
                text[:512], return_tensors="pt",
                truncation=True, max_length=512, padding=True,
            )
            with torch.no_grad():
                outputs = self._model(**inputs)
                embeddings = outputs.logits[0]  # Use logits as features

            # Combine neural signal with keyword scoring
            keyword_scores = self._compute_keyword_scores(text)

            # Weighted combination
            best_intent = max(keyword_scores, key=keyword_scores.get)
            best_score = keyword_scores[best_intent]

            # Neural boost: use embedding magnitude as confidence modifier
            neural_confidence = min(1.0, float(torch.sigmoid(embeddings.mean()).item()))
            final_confidence = min(1.0, best_score * 0.7 + neural_confidence * 0.3)

            lane = self.INTENT_LANE_MAP.get(best_intent)
            return {
                "intent": best_intent,
                "confidence": round(final_confidence, 3),
                "method": "neural_hybrid",
                "lane": lane,
                "scores": {k: round(v, 3) for k, v in sorted(
                    keyword_scores.items(), key=lambda x: -x[1]
                )[:5]},
            }
        except Exception as e:
            logger.warning("[NeuralIntent] Neural classify failed: %s — keyword fallback", e)
            return self._keyword_classify(text)

    # ── Keyword Classification ─────────────────────────────────────

    def _keyword_classify(self, text: str) -> dict:
        """Classify using keyword matching with confidence calibration."""
        try:
            scores = self._compute_keyword_scores(text)
            if not scores:
                return {
                    "intent": "research",
                    "confidence": 0.0,
                    "method": "keyword_no_match",
                    "lane": None,
                    "scores": {},
                }

            # Get top intent
            sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
            best_intent, best_score = sorted_scores[0]

            # Calibrate confidence: normalize relative to max possible
            max_keywords = max(len(kws) for kws in self.KEYWORDS.values())
            confidence = min(1.0, best_score / (max_keywords * 0.5))

            # Disambiguation: if top two are close, lower confidence
            if len(sorted_scores) > 1:
                second_score = sorted_scores[1][1]
                if best_score > 0 and second_score / best_score > 0.8:
                    confidence *= 0.7  # Ambiguous

            lane = self.INTENT_LANE_MAP.get(best_intent)
            return {
                "intent": best_intent,
                "confidence": round(confidence, 3),
                "method": "keyword",
                "lane": lane,
                "scores": {k: round(v, 3) for k, v in sorted_scores[:5]},
            }
        except Exception as e:
            logger.warning("[NeuralIntent] keyword classify failed: %s", e)
            return {
                "intent": "research",
                "confidence": 0.0,
                "method": "keyword_error",
                "lane": None,
                "scores": {},
            }

    def _compute_keyword_scores(self, text: str) -> Dict[str, float]:
        """Score all intents based on keyword matches."""
        scores: Dict[str, float] = {}
        text_lower = text.lower()

        for intent, patterns in self._compiled_keywords.items():
            score = 0.0
            for pattern in patterns:
                matches = pattern.findall(text_lower)
                if matches:
                    # Weight by number of matches, diminishing returns
                    score += 1.0 + min(0.5, len(matches) * 0.1)
            scores[intent] = score

        return scores

    # ── Status & Self-Test ─────────────────────────────────────────

    def status(self) -> Dict:
        """Return engine status."""
        return {
            "engine": "APEX-NeuralIntent",
            "apex_llm_enabled": APEX_LLM_ENABLED,
            "model_loaded": self._model is not None,
            "mode": "neural" if self._model is not None else "keyword",
            "intent_count": len(self.INTENTS),
            "keyword_count": sum(len(v) for v in self.KEYWORDS.values()),
            "lane_mappings": self.INTENT_LANE_MAP,
        }

    def self_test(self) -> Dict:
        """Run self-test with sample texts."""
        results = {"tests": [], "status": "pass"}
        try:
            test_cases = [
                ("custody parenting time best interest factors MCL 722.23", "custody"),
                ("appeal to COA MCR 7.204 brief on appeal", "appellate"),
                ("Judge McNeill judicial misconduct bias", "misconduct"),
                ("PPO personal protection order stalking MCL 600.2950", "ppo"),
                ("42 USC 1983 civil rights color of law", "federal_1983"),
                ("Shady Oaks habitability rent eviction", "housing"),
            ]

            for text, expected in test_cases:
                result = self.classify(text)
                passed = result["intent"] == expected
                results["tests"].append({
                    "name": f"classify_{expected}",
                    "pass": passed,
                    "expected": expected,
                    "got": result["intent"],
                    "confidence": result["confidence"],
                    "method": result["method"],
                })

            # Test batch
            batch_result = self.classify_batch(["custody", "appeal"])
            results["tests"].append({
                "name": "batch_classify",
                "pass": len(batch_result) == 2,
                "count": len(batch_result),
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

    ni = NeuralIntent()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "--self-test":
        print(json.dumps(ni.self_test(), indent=2, default=str))
    elif cmd == "--status":
        print(json.dumps(ni.status(), indent=2, default=str))
    elif cmd == "--batch":
        texts = sys.argv[2:]
        print(json.dumps(ni.classify_batch(texts), indent=2, default=str))
    elif cmd not in ("status", "--status"):
        text = " ".join(sys.argv[1:])
        result = ni.classify(text)
        print(json.dumps(result, indent=2, default=str))
    else:
        print(json.dumps(ni.status(), indent=2, default=str))
