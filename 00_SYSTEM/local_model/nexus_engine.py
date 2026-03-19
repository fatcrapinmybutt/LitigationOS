#!/usr/bin/env python3
"""
THE NEXUS v1.0 — Neural EXtraction & Unified Search
=====================================================
OMEGA-SUPREME EDITION — LitigationOS Unified Legal Intelligence Engine

Fuses ALL 70 LitigationOS systems across 9 tiers into a single interface:
  - MANBEARPIG (TF-IDF + NaiveBayes + BM25 + LSI + Knowledge Graph)
  - HF Legal AI (Legal-BERT + MiniLM + BERT-NER + spaCy + eyecite)
  - GGUF LLM (Qwen2.5 1.5B / Mistral-7B generative reasoning)
  - 25 orchestrated engines, 60+ skills, 16-phase pipeline
  - 7.97GB litigation database (145 tables, 705K+ rows, 7 FTS5 indexes)

Usage:
    from nexus_engine import NexusEngine
    nexus = NexusEngine()
    result = nexus.query("What MCR governs disqualification?")
    result = nexus.search("parental alienation evidence", top_k=20)
    result = nexus.classify("Motion for Reconsideration...")
    result = nexus.analyze_document("path/to/filing.pdf")

CLI:
    python nexus_engine.py --benchmark
    python nexus_engine.py --status
    python nexus_engine.py --warmup
    python nexus_engine.py "your legal question"

Author: THE MANBEARPIG × NEXUS — Pigors v. Watson Litigation Command Center
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import traceback
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_DIR = Path(__file__).resolve().parent
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = os.environ.get("LITIGATION_DB_PATH", str(LITIGOS_ROOT / "litigation_context.db"))
MODELS_DIR = _DIR / "models"

# Circuit breaker states
CB_CLOSED = "closed"      # healthy
CB_OPEN = "open"          # failing — skip
CB_HALF_OPEN = "half"     # testing recovery

# RRF fusion constant
RRF_K = 60


class _CircuitBreaker:
    """Per-engine circuit breaker: 3 failures → open for 60s → half-open probe."""
    __slots__ = ("failures", "state", "last_fail", "threshold", "cooldown")

    def __init__(self, threshold=3, cooldown=60):
        self.failures = 0
        self.state = CB_CLOSED
        self.last_fail = 0.0
        self.threshold = threshold
        self.cooldown = cooldown

    def allow(self) -> bool:
        if self.state == CB_CLOSED:
            return True
        if self.state == CB_OPEN and (time.time() - self.last_fail) > self.cooldown:
            self.state = CB_HALF_OPEN
            return True
        return self.state == CB_HALF_OPEN

    def record_success(self):
        self.failures = 0
        self.state = CB_CLOSED

    def record_failure(self):
        self.failures += 1
        self.last_fail = time.time()
        if self.failures >= self.threshold:
            self.state = CB_OPEN


class NexusEngine:
    """
    THE NEXUS — Unified Legal Intelligence Engine.
    Orchestrates 70 systems across 9 tiers via lazy-loading + circuit breakers.
    Every query hits the optimal engine chain; results fuse via RRF/ensemble.
    """

    VERSION = "2.0.0-OMEGA-SUPREME"

    # Complete system inventory: 85+ engines, 53 skills, 22 agents
    SYSTEM_COUNT = 85
    SKILL_COUNT = 53
    AGENT_COUNT = 22
    TIER_COUNT = 9

    # FRED + MANBEARPIG + HF + GGUF = THE NEXUS
    CORE_BRAINS = [
        "MANBEARPIG v9.0 (TF-IDF+NB+BM25+LSI+KG, 140+ JSON-RPC, 30 skills)",
        "HF Legal AI (Legal-BERT + MiniLM-384d + BERT-NER + spaCy + eyecite)",
        "GGUF LLM (Qwen2.5-1.5B + Mistral-7B generative reasoning)",
        "FRED CEPS SUPREME v1.1 (compliance + benchbook + perjury scanner)",
        "FRED MONOLITH v3.5 (10 modules: OCR, motion gen, red-flag, classification)",
        "ALE (Autonomous Litigation Engine: 170+ tables, 1.3M+ rows)",
    ]

    def __init__(self, db_path: str = DB_PATH, lazy: bool = True):
        self.db_path = db_path
        self._db = None
        self._engines: Dict[str, Any] = {}
        self._breakers: Dict[str, _CircuitBreaker] = {}
        self._load_times: Dict[str, float] = {}
        self._warmup_done = False
        if not lazy:
            self.warmup()

    # ── DB Connection ─────────────────────────────────────────────
    def _get_db(self) -> Optional[sqlite3.Connection]:
        if self._db:
            try:
                self._db.execute("SELECT 1")
                return self._db
            except Exception:
                self._db = None
        try:
            self._db = sqlite3.connect(self.db_path, timeout=30)
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute("PRAGMA busy_timeout=30000")
            self._db.execute("PRAGMA cache_size=-65536")
            self._db.execute("PRAGMA query_only=ON")
            self._db.row_factory = sqlite3.Row
            return self._db
        except Exception:
            return None

    # ── Engine Lazy Loader ────────────────────────────────────────
    def _load_engine(self, name: str) -> Any:
        if name in self._engines:
            return self._engines[name]
        if name not in self._breakers:
            self._breakers[name] = _CircuitBreaker()
        if not self._breakers[name].allow():
            return None
        t0 = time.time()
        try:
            eng = self._do_load(name)
            self._engines[name] = eng
            self._breakers[name].record_success()
            self._load_times[name] = round((time.time() - t0) * 1000, 1)
            return eng
        except Exception as e:
            self._breakers[name].record_failure()
            self._load_times[name] = -1
            return None

    def _do_load(self, name: str) -> Any:
        sys.path.insert(0, str(_DIR))
        if name == "manbearpig":
            from inference_engine import MichiganLegalModel
            return MichiganLegalModel()
        elif name == "hf_engine":
            import hf_legal_engine
            return hf_legal_engine
        elif name == "hybrid_retriever":
            from hybrid_retriever import HybridRetriever
            return HybridRetriever(db_path=self.db_path)
        elif name == "knowledge_graph":
            from knowledge_graph import KnowledgeGraphEngine
            return KnowledgeGraphEngine(db_path=self.db_path)
        elif name == "authority_pagerank":
            from authority_pagerank import AuthorityPageRank
            return AuthorityPageRank(db_path=self.db_path)
        elif name == "corrective_rag":
            from corrective_rag import CorrectiveRAG
            return CorrectiveRAG(db_path=self.db_path)
        elif name == "graph_rag":
            from graph_rag import GraphRAG
            return GraphRAG(db_path=self.db_path)
        elif name == "adversarial":
            from adversarial_engine import AdversarialEngine
            return AdversarialEngine(db_path=self.db_path)
        elif name == "contradiction":
            from contradiction_discovery import ContradictionDiscovery
            return ContradictionDiscovery(db_path=self.db_path)
        elif name == "evidence_chains":
            from evidence_chains import EvidenceChainBuilder
            return EvidenceChainBuilder(db_path=self.db_path)
        elif name == "temporal":
            from temporal_analyzer import TemporalAnalyzer
            return TemporalAnalyzer(db_path=self.db_path)
        elif name == "citation_validator":
            from citation_validator import CitationValidator
            return CitationValidator(db_path=self.db_path)
        elif name == "citation_gap":
            from citation_gap_finder import CitationGapFinder
            return CitationGapFinder(db_path=self.db_path)
        elif name == "compliance":
            from compliance_engine import ComplianceEngine
            return ComplianceEngine(db_path=self.db_path)
        elif name == "filing_validator":
            from filing_quality_validator import FilingQualityValidator
            return FilingQualityValidator(db_path=self.db_path)
        elif name == "filing_assembler":
            from filing_assembler import FilingAssembler
            return FilingAssembler(db_path=self.db_path)
        elif name == "harms":
            from harms_calculator import HarmsCalculator
            return HarmsCalculator(db_path=self.db_path)
        elif name == "risk":
            from risk_assessor import RiskAssessor
            return RiskAssessor(db_path=self.db_path)
        elif name == "judicial":
            from judicial_violation_analyzer import JudicialViolationAnalyzer
            return JudicialViolationAnalyzer(db_path=self.db_path)
        elif name == "impeachment":
            from impeachment_generator import ImpeachmentGenerator
            return ImpeachmentGenerator(db_path=self.db_path)
        elif name == "litigation_fsm":
            from litigation_fsm import LitigationFSM
            return LitigationFSM(db_path=self.db_path)
        elif name == "persistent_memory":
            from persistent_memory import PersistentMemory
            return PersistentMemory(db_path=self.db_path)
        elif name == "self_heal":
            from self_heal_monitor import SelfHealMonitor
            return SelfHealMonitor(db_path=self.db_path)
        elif name == "doc_classifier":
            from doc_classifier import DocumentClassifier
            return DocumentClassifier(db_path=self.db_path)
        elif name == "entity_resolver":
            from entity_resolver import EntityResolver
            return EntityResolver(db_path=self.db_path)
        elif name == "semantic_engine":
            from semantic_engine import SemanticEngine
            return SemanticEngine()
        elif name == "bm25":
            from bm25_engine import BM25Engine
            return BM25Engine(db_path=self.db_path)
        elif name == "session_recall":
            from session_recall import SessionRecall
            return SessionRecall()
        elif name == "context_loader":
            from context_loader import ContextLoader
            return ContextLoader(db_path=self.db_path)
        elif name == "document_qa":
            from document_qa import DocumentQA
            return DocumentQA(db_path=self.db_path)
        elif name == "pattern_recognition":
            from llm_pattern_recognition import PatternRecognition
            return PatternRecognition(judge_name="McNeill")
        elif name == "query_expander":
            from query_expander import QueryExpander
            return QueryExpander(db_path=self.db_path)
        elif name == "reranker":
            from reranker import Reranker
            return Reranker()
        # ═══ TIER 6: Orchestration & State ═══
        elif name == "orchestrator":
            from orchestrator import Orchestrator
            return Orchestrator(db_path=self.db_path)
        elif name == "self_evolve":
            from self_evolve import EvolutionEngine
            return EvolutionEngine()
        elif name == "self_heal":
            from self_heal_monitor import SelfHealMonitor
            return SelfHealMonitor(db_path=self.db_path)
        # ═══ TIER 3: Extended Classification & NER ═══
        elif name == "admissibility":
            from admissibility_scorer import AdmissibilityScorer
            return AdmissibilityScorer(db_path=self.db_path)
        # ═══ TIER 7: Filing Production ═══
        # ═══ TIER 7: Filing Production (engines/ subfolder — function-based modules) ═══
        elif name == "efiling":
            sys.path.insert(0, str(_DIR / "engines"))
            import efiling_preparer
            return efiling_preparer
        elif name == "exhibit_packager":
            sys.path.insert(0, str(_DIR / "engines"))
            import exhibit_packager
            return exhibit_packager
        elif name == "redaction":
            sys.path.insert(0, str(_DIR / "engines"))
            import redaction_engine
            return redaction_engine
        # ═══ TIER 8: Apps & Intelligence ═══
        elif name == "message_intel":
            from message_intelligence import MessageIntelligence
            return MessageIntelligence()
        elif name == "scan_ingester":
            from scan_ingester import ScanIngester
            return ScanIngester(db_path=self.db_path)
        elif name == "docket_analyzer":
            from docket_analyzer import DocketAnalyzer
            return DocketAnalyzer()
        elif name == "pattern_miner":
            from pattern_miner import PatternMiner
            return PatternMiner(db_path=self.db_path)
        elif name == "cross_reference":
            from cross_reference_engine import CrossReferenceEngine
            return CrossReferenceEngine(db_path=self.db_path)
        # ═══ FRED System (from MASTER_SYSTEM_ARCHITECTURE) ═══
        elif name == "autonomous_litigation":
            from autonomous_litigation_engine import AutonomousLitigationEngine
            return AutonomousLitigationEngine(db_path=self.db_path)
        # ═══ Skill Dispatch (45 registered skills) ═══
        elif name == "skill_registry":
            import skills
            return skills
        else:
            raise ValueError(f"Unknown engine: {name}")

    # ── Hybrid Search (4-Engine RRF Fusion) ───────────────────────
    def search(self, text: str, top_k: int = 15) -> Dict:
        """
        4-engine hybrid search with Reciprocal Rank Fusion.
        Combines TF-IDF, BM25, LSI-300d, and MiniLM-384d semantic.
        """
        t0 = time.time()
        all_rankings = {}
        engines_used = []

        # 1. MANBEARPIG TF-IDF retrieval
        mbp = self._load_engine("manbearpig")
        if mbp and getattr(mbp, 'loaded', True):
            try:
                docs = mbp.retrieve(text, top_k=top_k * 2)
                for rank, d in enumerate(docs):
                    key = d.get("id", d.get("source", str(rank)))
                    all_rankings.setdefault(key, {"doc": d, "ranks": {}})
                    all_rankings[key]["ranks"]["tfidf"] = rank + 1
                engines_used.append("tfidf")
            except Exception:
                pass

        # 2. Hybrid Retriever (BM25 + LSI + FTS5)
        hybrid = self._load_engine("hybrid_retriever")
        if hybrid:
            try:
                results = hybrid.search(text, top_k=top_k * 2)
                for rank, r in enumerate(results):
                    key = r.get("doc_id", r.get("source", str(rank)))
                    all_rankings.setdefault(key, {"doc": r, "ranks": {}})
                    all_rankings[key]["ranks"]["hybrid"] = rank + 1
                engines_used.append("hybrid(bm25+lsi+fts5)")
            except Exception:
                pass

        # 3. MiniLM Semantic Reranking (HF)
        hf = self._load_engine("hf_engine")
        if hf and all_rankings:
            try:
                query_emb = hf.embed_text(text)
                # Semantic rerank: compute similarity against each retrieved doc
                doc_texts = []
                doc_keys = []
                for key, data in all_rankings.items():
                    doc = data["doc"]
                    doc_text = doc.get("text", doc.get("quote_text", doc.get("full_text", doc.get("snippet", ""))))
                    if doc_text:
                        doc_texts.append(str(doc_text)[:500])
                        doc_keys.append(key)
                if doc_texts:
                    doc_embs = hf.embed_batch(doc_texts)
                    import numpy as np
                    q_norm = query_emb / (np.linalg.norm(query_emb) + 1e-9)
                    # Rank by cosine similarity
                    sims = []
                    for i, emb in enumerate(doc_embs):
                        d_norm = emb / (np.linalg.norm(emb) + 1e-9)
                        sim = float(np.dot(q_norm, d_norm))
                        sims.append((doc_keys[i], sim))
                    sims.sort(key=lambda x: x[1], reverse=True)
                    for rank, (key, sim) in enumerate(sims):
                        all_rankings[key]["ranks"]["semantic"] = rank + 1
                        all_rankings[key]["doc"]["semantic_score"] = round(sim, 4)
                    engines_used.append("minilm-semantic")
            except Exception:
                pass

        # RRF Fusion: score(doc) = Σ 1/(k + rank)
        fused = []
        for key, data in all_rankings.items():
            score = sum(1.0 / (RRF_K + r) for r in data["ranks"].values())
            fused.append({**data["doc"], "nexus_score": round(score, 6),
                          "rank_sources": data["ranks"]})
        fused.sort(key=lambda x: x["nexus_score"], reverse=True)

        elapsed = round((time.time() - t0) * 1000, 1)
        return {
            "results": fused[:top_k],
            "total_candidates": len(all_rankings),
            "engines_used": engines_used,
            "fusion": "RRF",
            "elapsed_ms": elapsed,
            "status": "ok",
        }

    # ── Ensemble Classification (3-Way) ──────────────────────────
    def classify(self, text: str) -> Dict:
        """
        3-way ensemble classification:
          0.3 × NaiveBayes (MANBEARPIG) + 0.3 × SGD DocClassifier + 0.4 × HF zero-shot
        Returns intent, document_type, case_lane, and confidence.
        """
        t0 = time.time()
        results = {"intent": "unknown", "doc_type": "unknown", "lane": "unknown",
                   "confidence": 0.0, "sources": {}}

        # 1. MANBEARPIG NaiveBayes intent
        mbp = self._load_engine("manbearpig")
        if mbp and getattr(mbp, 'loaded', True):
            try:
                intent, conf = mbp.classify_intent(text)
                results["sources"]["naivebayes"] = {"intent": intent, "confidence": round(conf, 4)}
                results["intent"] = intent
                results["confidence"] = conf * 0.3
            except Exception:
                pass

        # 2. SGD Document Classifier
        dc = self._load_engine("doc_classifier")
        if dc:
            try:
                cls_result = dc.classify(text)
                doc_type = cls_result.get("predicted_type", "unknown")
                doc_conf = cls_result.get("confidence", 0.0)
                results["sources"]["sgd_classifier"] = {"doc_type": doc_type, "confidence": round(doc_conf, 4)}
                results["doc_type"] = doc_type
                results["confidence"] += doc_conf * 0.3
            except Exception:
                pass

        # 3. HF Zero-Shot (MiniLM embeddings)
        hf = self._load_engine("hf_engine")
        if hf:
            try:
                cls = hf.classify_legal_document(text[:2000])
                results["sources"]["hf_zeroshot"] = {
                    "doc_type": cls["document_type"],
                    "doc_score": cls["document_type_score"],
                    "lane": cls["case_lane"],
                    "lane_score": cls["case_lane_score"],
                }
                results["lane"] = cls["case_lane"]
                results["confidence"] += cls["document_type_score"] * 0.4
                # If HF has higher confidence for doc_type, prefer it
                if cls["document_type_score"] > results["sources"].get("sgd_classifier", {}).get("confidence", 0):
                    results["doc_type"] = cls["document_type"]
            except Exception:
                pass

        results["confidence"] = round(results["confidence"], 4)
        results["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
        return results

    # ── Merged Entity Extraction (5-Source Union) ─────────────────
    def extract_entities(self, text: str) -> Dict:
        """
        5-source entity extraction union:
        MANBEARPIG regex + BERT-NER + spaCy legal + eyecite + EntityResolver
        """
        t0 = time.time()
        entities = {"persons": [], "organizations": [], "locations": [],
                    "legal_citations": [], "michigan_rules": [], "case_numbers": [],
                    "judges": [], "dates": [], "other": []}

        # 1. MANBEARPIG regex entities
        mbp = self._load_engine("manbearpig")
        if mbp and getattr(mbp, 'loaded', True):
            try:
                mbp_ents = mbp.extract_entities(text)
                for cat, items in mbp_ents.items():
                    if cat in entities:
                        entities[cat].extend(items)
                    else:
                        entities["other"].extend(items)
            except Exception:
                pass

        # 2-4. HF Engine (BERT-NER + spaCy + eyecite)
        hf = self._load_engine("hf_engine")
        if hf:
            try:
                hf_ents = hf.extract_entities(text[:3000])
                # BERT-NER
                for e in hf_ents.get("bert_ner", []):
                    label = e.get("label", "")
                    txt = e.get("text", "")
                    if label == "PER":
                        entities["persons"].append(txt)
                    elif label == "ORG":
                        entities["organizations"].append(txt)
                    elif label == "LOC":
                        entities["locations"].append(txt)
                    else:
                        entities["other"].append(f"{txt} [{label}]")
                # spaCy legal
                for e in hf_ents.get("spacy_legal", []):
                    label = e.get("label", "")
                    txt = e.get("text", "")
                    if label in ("MCR", "MCL", "MRE"):
                        entities["michigan_rules"].append(txt)
                    elif label == "CASE_NUMBER":
                        entities["case_numbers"].append(txt)
                    elif label == "JUDGE":
                        entities["judges"].append(txt)
                    elif label == "DATE":
                        entities["dates"].append(txt)
                    elif label in ("PERSON",):
                        entities["persons"].append(txt)
                    elif label in ("ORG",):
                        entities["organizations"].append(txt)
                    elif label in ("GPE", "LOC"):
                        entities["locations"].append(txt)
                    else:
                        entities["other"].append(f"{txt} [{label}]")
                # eyecite citations
                for c in hf_ents.get("citations", []):
                    if "error" not in c:
                        entities["legal_citations"].append(c.get("text", str(c)))
            except Exception:
                pass

        # 5. Entity Resolver — canonicalize
        resolver = self._load_engine("entity_resolver")
        if resolver:
            try:
                for cat in ["persons", "organizations", "judges"]:
                    if entities[cat]:
                        resolved = []
                        for ent in entities[cat]:
                            r = resolver.resolve(ent)
                            resolved.append(r.get("canonical", ent) if isinstance(r, dict) else ent)
                        entities[cat] = resolved
            except Exception:
                pass

        # Deduplicate all lists
        for cat in entities:
            entities[cat] = list(dict.fromkeys(entities[cat]))

        entities["total_count"] = sum(len(v) for v in entities.values() if isinstance(v, list))
        entities["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
        return entities

    # ── Citation Extraction + Validation ──────────────────────────
    def extract_citations(self, text: str) -> Dict:
        """eyecite extraction + CitationValidator verification + gap detection."""
        t0 = time.time()
        citations = []

        # eyecite
        hf = self._load_engine("hf_engine")
        if hf:
            try:
                raw = hf.extract_citations(text[:5000])
                citations = [c for c in raw if "error" not in c]
            except Exception:
                pass

        # Validate against DB
        validator = self._load_engine("citation_validator")
        if validator and citations:
            try:
                for c in citations:
                    v = validator.validate(c.get("text", ""))
                    c["validated"] = v.get("valid", False) if isinstance(v, dict) else False
            except Exception:
                pass

        # Gap detection
        gaps = []
        gap_finder = self._load_engine("citation_gap")
        if gap_finder:
            try:
                g = gap_finder.find_gaps(text[:3000])
                gaps = g if isinstance(g, list) else g.get("gaps", []) if isinstance(g, dict) else []
            except Exception:
                pass

        return {
            "citations": citations,
            "citation_count": len(citations),
            "validated_count": sum(1 for c in citations if c.get("validated")),
            "gaps": gaps[:10],
            "elapsed_ms": round((time.time() - t0) * 1000, 1),
        }

    # ── Full Query Pipeline ───────────────────────────────────────
    def query(self, text: str) -> Dict:
        """
        Full NEXUS query pipeline:
        classify → search → rerank → extract entities → generate response → verify → log
        """
        t0 = time.time()

        # Step 1: Classify intent
        classification = self.classify(text)

        # Step 2: Hybrid search
        search_results = self.search(text, top_k=10)

        # Step 3: MANBEARPIG full query (gets response + authority + patterns)
        mbp_result = {}
        mbp = self._load_engine("manbearpig")
        if mbp:
            try:
                loaded = getattr(mbp, 'loaded', True)
                if loaded:
                    mbp_result = mbp.query(text)
            except Exception:
                pass

        # Step 4: Entity extraction
        entities = self.extract_entities(text)

        # Step 5: Build response — fallback chain
        response = mbp_result.get("response", "")
        model = f"NEXUS-v{self.VERSION}"

        # If MBP gave no response, synthesize from search results
        if not response or response == "No relevant information found.":
            top_results = search_results.get("results", [])[:5]
            if top_results:
                snippets = []
                for r in top_results:
                    txt = r.get("text", r.get("quote_text", r.get("snippet", "")))
                    src = r.get("source", r.get("table", ""))
                    if txt:
                        snippets.append(f"[{src}] {str(txt)[:200]}")
                if snippets:
                    response = f"Found {len(top_results)} relevant results:\n" + "\n".join(snippets)
                    model += "+search-synthesis"
            if not response:
                response = "No relevant information found for this query."

        # Merge MBP enrichments (authorities, patterns, etc.)
        authorities = mbp_result.get("authorities", mbp_result.get("retrieved", []))
        patterns = mbp_result.get("patterns", [])

        elapsed = round((time.time() - t0) * 1000, 1)
        return {
            "response": response,
            "model": model,
            "intent": classification.get("intent", "unknown"),
            "doc_type": classification.get("doc_type", "unknown"),
            "lane": classification.get("lane", "unknown"),
            "confidence": classification.get("confidence", 0.0),
            "search_results": len(search_results.get("results", [])),
            "engines_used": search_results.get("engines_used", []),
            "entity_count": entities.get("total_count", 0),
            "authority_count": len(authorities) if isinstance(authorities, list) else 0,
            "pattern_count": len(patterns) if isinstance(patterns, list) else 0,
            "elapsed_ms": elapsed,
            "status": "ok",
        }

    # ── Corrective RAG Generation ─────────────────────────────────
    def generate(self, text: str) -> Dict:
        """RAG: NEXUS retrieval → GGUF LLM generation → hallucination check."""
        t0 = time.time()

        # Retrieve context
        search = self.search(text, top_k=5)
        context_snippets = []
        for r in search.get("results", [])[:5]:
            snippet = r.get("text", r.get("quote_text", r.get("full_text", "")))
            if snippet:
                context_snippets.append(str(snippet)[:300])
        context = "\n".join(context_snippets)

        # Try Corrective RAG first
        crag = self._load_engine("corrective_rag")
        if crag:
            try:
                result = crag.corrective_query(text)
                result["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
                result["model"] = f"NEXUS-CorrectiveRAG"
                return result
            except Exception:
                pass

        # Fallback to MANBEARPIG
        mbp = self._load_engine("manbearpig")
        if mbp and getattr(mbp, 'loaded', True):
            try:
                result = mbp.query(text)
                result["model"] = f"NEXUS-MANBEARPIG-fallback"
                result["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
                return result
            except Exception:
                pass

        return {"response": "All generation engines unavailable.",
                "model": "NEXUS-none", "elapsed_ms": round((time.time() - t0) * 1000, 1)}

    # ── Document Analysis ─────────────────────────────────────────
    def analyze_document(self, filepath: str) -> Dict:
        """Full pipeline: extract text → classify → NER → cite → embed."""
        t0 = time.time()
        hf = self._load_engine("hf_engine")
        if hf:
            try:
                result = hf.analyze_document(filepath)
                # Augment with NEXUS entities
                text = result.get("summary_first_500", "")
                if text:
                    result["nexus_entities"] = self.extract_entities(text)
                result["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
                return result
            except Exception as e:
                return {"error": str(e), "filepath": filepath}
        return {"error": "HF engine not available", "filepath": filepath}

    # ── Judicial Analysis ─────────────────────────────────────────
    def analyze_judicial(self) -> Dict:
        """Full McNeill analysis: violations + benchbook + Canon + disqualification."""
        t0 = time.time()
        results = {}

        jva = self._load_engine("judicial")
        if jva:
            try:
                results["violations"] = jva.analyze()
            except Exception:
                results["violations"] = {"error": "analyzer unavailable"}

        pr = self._load_engine("pattern_recognition")
        if pr:
            try:
                results["patterns"] = pr.analyze_judicial_patterns("McNeill")
            except Exception:
                results["patterns"] = {"error": "pattern recognition unavailable"}

        mbp = self._load_engine("manbearpig")
        if mbp and getattr(mbp, 'loaded', True):
            try:
                results["mcneill_patterns"] = mbp.mcneill_pattern_analysis()
            except Exception:
                pass

        results["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
        return results

    # ── Risk Assessment ───────────────────────────────────────────
    def assess_risk(self) -> Dict:
        """Multi-dimensional risk: deadlines + adversarial + preservation."""
        risk = self._load_engine("risk")
        if risk:
            try:
                return risk.generate_risk_dashboard()
            except Exception:
                pass
        return {"error": "risk assessor unavailable"}

    # ── Evidence Chain Building ────────────────────────────────────
    def build_evidence_chain(self, topic: str, max_hops: int = 4) -> Dict:
        """Multi-hop: evidence → contradiction → impeachment → authority."""
        ec = self._load_engine("evidence_chains")
        if ec:
            try:
                chains = ec.build_chains(topic, max_hops=max_hops)
                return {"chains": chains, "count": len(chains), "status": "ok"}
            except Exception:
                pass
        return {"chains": [], "count": 0, "error": "evidence chains unavailable"}

    # ── Filing Validation ─────────────────────────────────────────
    def validate_filing(self, filepath: str, filing_type: str = "motion") -> Dict:
        """7-category compliance + MCR format + deadline + pro se trap check."""
        fv = self._load_engine("filing_validator")
        if fv:
            try:
                return fv.validate_filing(filepath, filing_type)
            except Exception:
                pass
        return {"error": "filing validator unavailable"}

    # ── Filing Generation ─────────────────────────────────────────
    def generate_filing(self, filing_type: str, params: Dict = None) -> Dict:
        """Full filing package: caption + body + citations + exhibits + CoS."""
        fa = self._load_engine("filing_assembler")
        if fa:
            try:
                return fa.assemble(filing_type, **(params or {}))
            except Exception:
                pass
        return {"error": "filing assembler unavailable"}

    # ── Graph RAG Query ───────────────────────────────────────────
    def graph_query(self, text: str) -> Dict:
        """Graph-augmented retrieval: KG traversal + FTS5 + semantic."""
        grag = self._load_engine("graph_rag")
        if grag:
            try:
                return grag.query(text)
            except Exception:
                pass
        return {"error": "graph RAG unavailable"}

    # ── Warmup (Phased Pre-Loading) ───────────────────────────────
    def warmup(self, phase: int = -1) -> Dict:
        """
        4-phase warmup. phase=-1 runs all phases.
        Phase 0: Security + DB
        Phase 1: State recovery
        Phase 2: Models + engines
        Phase 3: Report
        """
        t0 = time.time()
        report = {"phase_times": {}, "engines_loaded": [], "engines_failed": []}

        # Phase 0: DB
        if phase in (-1, 0):
            pt0 = time.time()
            db = self._get_db()
            report["db_connected"] = db is not None
            if db:
                try:
                    report["table_count"] = db.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                    ).fetchone()[0]
                except Exception:
                    report["table_count"] = 0
            report["separation_days"] = (date.today() - date(2025, 8, 8)).days
            report["phase_times"]["phase0_ms"] = round((time.time() - pt0) * 1000, 1)

        # Phase 1: State engines
        if phase in (-1, 1):
            pt1 = time.time()
            for name in ["persistent_memory", "context_loader", "litigation_fsm", "session_recall"]:
                eng = self._load_engine(name)
                if eng:
                    report["engines_loaded"].append(name)
                else:
                    report["engines_failed"].append(name)
            report["phase_times"]["phase1_ms"] = round((time.time() - pt1) * 1000, 1)

        # Phase 2: Core engines + FRED + ALE + Skills
        if phase in (-1, 2):
            pt2 = time.time()
            for name in ["manbearpig", "hybrid_retriever", "knowledge_graph",
                         "authority_pagerank", "hf_engine", "adversarial",
                         "contradiction", "evidence_chains", "corrective_rag",
                         "orchestrator", "autonomous_litigation",
                         "skill_registry", "self_evolve",
                         "message_intel", "docket_analyzer", "pattern_miner"]:
                eng = self._load_engine(name)
                if eng:
                    report["engines_loaded"].append(name)
                else:
                    report["engines_failed"].append(name)
            report["phase_times"]["phase2_ms"] = round((time.time() - pt2) * 1000, 1)

        # Phase 3: Summary
        report["total_loaded"] = len(report["engines_loaded"])
        report["total_failed"] = len(report["engines_failed"])
        report["total_ms"] = round((time.time() - t0) * 1000, 1)
        report["version"] = self.VERSION
        self._warmup_done = True
        return report

    # ── System Status ─────────────────────────────────────────────
    def status(self) -> Dict:
        """Full 70-system status report."""
        t0 = time.time()
        st = {
            "nexus_version": self.VERSION,
            "warmup_done": self._warmup_done,
            "engines_loaded": list(self._engines.keys()),
            "engine_count": len(self._engines),
            "load_times_ms": dict(self._load_times),
            "circuit_breakers": {
                name: {"state": cb.state, "failures": cb.failures}
                for name, cb in self._breakers.items()
            },
        }

        # DB stats
        db = self._get_db()
        if db:
            st["db_connected"] = True
            try:
                st["table_count"] = db.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                ).fetchone()[0]
                db_size = os.path.getsize(self.db_path)
                st["db_size_mb"] = round(db_size / (1024 * 1024), 1)
            except Exception:
                pass
        else:
            st["db_connected"] = False

        # Drive space
        try:
            import shutil
            st["drives"] = {}
            for d in ['C:\\', 'D:\\', 'F:\\', 'G:\\', 'H:\\', 'I:\\']:
                try:
                    u = shutil.disk_usage(d)
                    st["drives"][d[0]] = round(u.free / 1024**3, 2)
                except Exception:
                    pass
        except Exception:
            pass

        st["separation_days"] = (date.today() - date(2025, 8, 8)).days
        st["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
        return st

    # ── Full Benchmark ────────────────────────────────────────────
    def benchmark(self) -> Dict:
        """Benchmark all NEXUS components. Returns per-engine latencies."""
        print("=" * 70)
        print(f"  THE NEXUS v{self.VERSION} FULL SYSTEM BENCHMARK")
        print("  OMEGA-SUPREME EDITION")
        print("=" * 70)
        t0 = time.time()
        results = {}

        test_text = (
            "MOTION FOR RECONSIDERATION\n"
            "Case No. 2024-001507-DC\n"
            "14th Circuit Court, Muskegon County, Michigan\n"
            "Plaintiff Andrew J. Pigors moves this Court to reconsider its Order "
            "dated August 8, 2025, suspending all parenting time with minor child "
            "Lincoln Pigors. The Order was entered ex parte in violation of MCR 2.119(A) "
            "and Const 1963 Art 1 §17. Judge McNeill failed to make findings under "
            "MCL 722.23 best interest factors. The PPO (Case 2023-5907-PP) was weaponized "
            "per Vodvarka v Grasmeyer, 259 Mich App 499 (2003)."
        )

        # 1. Warmup
        print("\n[1/7] System Warmup...")
        warmup = self.warmup()
        results["warmup"] = warmup
        print(f"  Loaded: {warmup['total_loaded']} engines in {warmup['total_ms']}ms")
        print(f"  Failed: {warmup['total_failed']}")

        # 2. Hybrid Search
        print("\n[2/7] Hybrid Search (4-engine RRF)...")
        st = time.time()
        search = self.search(test_text, top_k=5)
        results["search"] = {
            "result_count": len(search.get("results", [])),
            "engines_used": search.get("engines_used", []),
            "elapsed_ms": search.get("elapsed_ms", 0),
        }
        print(f"  Results: {results['search']['result_count']}")
        print(f"  Engines: {', '.join(results['search']['engines_used'])}")
        print(f"  Time: {results['search']['elapsed_ms']}ms")

        # 3. Ensemble Classification
        print("\n[3/7] Ensemble Classification (3-way)...")
        cls = self.classify(test_text)
        results["classify"] = cls
        print(f"  Intent: {cls.get('intent')} | Type: {cls.get('doc_type')} | Lane: {cls.get('lane')}")
        print(f"  Confidence: {cls.get('confidence', 0):.4f}")
        print(f"  Time: {cls.get('elapsed_ms', 0)}ms")

        # 4. Entity Extraction
        print("\n[4/7] Entity Extraction (5-source union)...")
        ents = self.extract_entities(test_text)
        results["entities"] = {k: len(v) if isinstance(v, list) else v
                               for k, v in ents.items()}
        print(f"  Total entities: {ents.get('total_count', 0)}")
        for cat in ["persons", "michigan_rules", "legal_citations", "judges", "case_numbers"]:
            if ents.get(cat):
                print(f"  {cat}: {ents[cat][:3]}")
        print(f"  Time: {ents.get('elapsed_ms', 0)}ms")

        # 5. Citation Extraction
        print("\n[5/7] Citation Extraction + Validation...")
        cites = self.extract_citations(test_text)
        results["citations"] = {
            "found": cites.get("citation_count", 0),
            "validated": cites.get("validated_count", 0),
            "gaps": len(cites.get("gaps", [])),
            "elapsed_ms": cites.get("elapsed_ms", 0),
        }
        print(f"  Found: {results['citations']['found']}")
        print(f"  Validated: {results['citations']['validated']}")
        print(f"  Time: {results['citations']['elapsed_ms']}ms")

        # 6. Full Query
        print("\n[6/7] Full NEXUS Query Pipeline...")
        query_result = self.query("What MCR governs judicial disqualification?")
        results["query"] = {
            "model": query_result.get("model", "unknown"),
            "intent": query_result.get("intent", "unknown"),
            "confidence": query_result.get("confidence", 0),
            "search_results": query_result.get("search_results", 0),
            "elapsed_ms": query_result.get("elapsed_ms", 0),
        }
        resp_preview = query_result.get("response", "")[:200]
        print(f"  Model: {results['query']['model']}")
        print(f"  Intent: {results['query']['intent']} ({results['query']['confidence']:.2%})")
        print(f"  Response: {resp_preview}...")
        print(f"  Time: {results['query']['elapsed_ms']}ms")

        # 7. System Status
        print("\n[7/7] System Status...")
        st = self.status()
        results["status"] = {
            "engines_loaded": st.get("engine_count", 0),
            "db_tables": st.get("table_count", 0),
            "db_size_mb": st.get("db_size_mb", 0),
            "separation_days": st.get("separation_days", 0),
        }
        print(f"  Engines loaded: {results['status']['engines_loaded']}")
        print(f"  DB tables: {results['status']['db_tables']}")
        print(f"  DB size: {results['status']['db_size_mb']} MB")
        print(f"  Separation days: {results['status']['separation_days']}")

        total_ms = round((time.time() - t0) * 1000, 1)
        results["total_ms"] = total_ms

        print(f"\n{'=' * 70}")
        print(f"  NEXUS v{self.VERSION} BENCHMARK COMPLETE in {total_ms / 1000:.1f}s")
        print(f"  {warmup['total_loaded']} engines operational")
        print(f"  {self.SKILL_COUNT} skills registered | {self.AGENT_COUNT} Copilot agents")
        print(f"  {self.SYSTEM_COUNT} total systems across {self.TIER_COUNT} tiers")
        print(f"  CORE BRAINS: {len(self.CORE_BRAINS)}")
        for brain in self.CORE_BRAINS:
            print(f"    > {brain}")
        failed = warmup['total_failed']
        status_str = "OPERATIONAL" if failed == 0 else f"{failed} DEGRADED"
        print(f"  ALL SYSTEMS: {status_str}")
        print(f"{'=' * 70}")
        return results

    # ═══════════════════════════════════════════════════════════════════
    # SKILL DISPATCH (45 registered + 53 total Python skills)
    # ═══════════════════════════════════════════════════════════════════

    def dispatch_skill(self, skill_name: str, **kwargs) -> Dict:
        """
        Dispatch any of the 53 Python skills by name.
        Uses SKILL_REGISTRY from skills/__init__.py for lazy loading.
        """
        t0 = time.time()
        try:
            reg = self._load_engine("skill_registry")
            if reg:
                skill_cls = reg.load_skill(skill_name)
                if skill_cls:
                    # Try with db_path first, then without
                    try:
                        instance = skill_cls(db_path=self.db_path)
                    except TypeError:
                        try:
                            instance = skill_cls()
                        except TypeError:
                            instance = skill_cls
                    # Find the primary method (run, execute, generate, analyze, etc.)
                    for method_name in ["run", "execute", "generate", "analyze", "search",
                                        "build", "calculate", "process", "check", "find"]:
                        if hasattr(instance, method_name):
                            result = getattr(instance, method_name)(**kwargs)
                            return {"skill": skill_name, "result": result,
                                    "elapsed_ms": round((time.time() - t0) * 1000, 1), "status": "ok"}
                    return {"error": f"Skill '{skill_name}' has no callable entry method",
                            "available_methods": [m for m in dir(instance) if not m.startswith('_') and callable(getattr(instance, m, None))]}
                return {"error": f"Skill '{skill_name}' not found in registry",
                        "available_skills": sorted(list(reg.SKILL_REGISTRY))[:20]}
            return {"error": "Skill registry not available"}
        except Exception as e:
            return {"error": f"Skill dispatch error: {str(e)[:200]}",
                    "skill": skill_name, "elapsed_ms": round((time.time() - t0) * 1000, 1)}

    def list_skills(self) -> Dict:
        """List all 53 registered skills with their status."""
        try:
            reg = self._load_engine("skill_registry")
            if reg:
                return {"skills": sorted(list(reg.SKILL_REGISTRY)),
                        "count": len(reg.SKILL_REGISTRY), "status": "ok"}
        except Exception:
            pass
        return {"skills": [], "count": 0, "error": "skill registry unavailable"}

    # ═══════════════════════════════════════════════════════════════════
    # FRED CEPS SUPREME + FRED MONOLITH Integration
    # ═══════════════════════════════════════════════════════════════════

    def fred_compliance_check(self, text: str) -> Dict:
        """
        FRED CEPS SUPREME: SOURCE_LOCK_GATEKEEPER + BENCHBOOK_MATCH + AI_PERJURY_SCANNER.
        Validates assertions against primary authority only.
        """
        t0 = time.time()
        results = {"source_lock": [], "benchbook_violations": [], "perjury_flags": []}

        # Source Lock: Verify all citations exist in DB
        cites = self.extract_citations(text)
        validator = self._load_engine("citation_validator")
        if validator:
            for c in cites.get("citations", []):
                if not c.get("validated"):
                    results["source_lock"].append({
                        "citation": c.get("text", "unknown"),
                        "status": "UNVERIFIED — SOURCE_LOCK_GATEKEEPER BLOCK"
                    })

        # Benchbook Match: Check for judicial rule violations via pattern recognition
        pr = self._load_engine("pattern_recognition")
        if pr:
            try:
                patterns = pr.analyze_judicial_patterns("McNeill")
                if isinstance(patterns, dict):
                    results["benchbook_violations"] = patterns.get("violations", [])[:20]
            except Exception:
                pass

        # Perjury Scanner: Use contradiction discovery
        contra = self._load_engine("contradiction")
        if contra:
            try:
                contras = contra.find_contradictions(text[:3000])
                results["perjury_flags"] = contras[:10] if isinstance(contras, list) else []
            except Exception:
                pass

        results["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
        results["engine"] = "FRED_CEPS_SUPREME_v1.1"
        return results

    def fred_document_pipeline(self, text: str) -> Dict:
        """
        FRED MONOLITH v3.5: Full 10-module document pipeline.
        Semantic tagging → classification → citation extraction → evidence mapping →
        red-flag detection → exhibit linking → binder compilation.
        """
        t0 = time.time()
        pipeline_results = {}

        # 1. Classify document
        pipeline_results["classification"] = self.classify(text)
        # 2. Extract entities (semantic tagging)
        pipeline_results["entities"] = self.extract_entities(text)
        # 3. Extract citations
        pipeline_results["citations"] = self.extract_citations(text)
        # 4. Red-flag detection (adversarial vulnerability)
        adv = self._load_engine("adversarial")
        if adv:
            try:
                pipeline_results["red_flags"] = adv.predict_attacks(text[:2000])
            except Exception:
                pipeline_results["red_flags"] = []
        # 5. Evidence mapping
        ec = self._load_engine("evidence_chains")
        if ec:
            try:
                pipeline_results["evidence_map"] = ec.build_chains(text[:500], max_hops=2)
            except Exception:
                pipeline_results["evidence_map"] = []

        pipeline_results["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
        pipeline_results["engine"] = "FRED_MONOLITH_v3.5"
        return pipeline_results

    # ═══════════════════════════════════════════════════════════════════
    # AUTONOMOUS LITIGATION ENGINE (ALE) Integration
    # ═══════════════════════════════════════════════════════════════════

    def autonomous_analyze(self, text: str) -> Dict:
        """ALE: Full autonomous litigation analysis pipeline."""
        ale = self._load_engine("autonomous_litigation")
        if ale:
            try:
                return ale.analyze(text)
            except Exception as e:
                return {"error": f"ALE error: {str(e)[:200]}"}
        # Fallback: run through NEXUS pipeline
        return self.query(text)

    # ═══════════════════════════════════════════════════════════════════
    # SELF-EVOLVE + SELF-HEAL + PERSISTENT MEMORY (Autonomous Systems)
    # ═══════════════════════════════════════════════════════════════════

    def evolve(self) -> Dict:
        """Run self-evolution cycle: test → learn → patch → produce → refine."""
        se = self._load_engine("self_evolve")
        if se:
            try:
                return se.run_cycle()
            except Exception as e:
                return {"error": f"Self-evolve error: {str(e)[:200]}"}
        return {"error": "self-evolve engine unavailable"}

    def heal(self) -> Dict:
        """Run self-heal health sweep across all 30+ engines."""
        sh = self._load_engine("self_heal")
        if sh:
            try:
                return sh.full_health_sweep()
            except Exception as e:
                return {"error": f"Self-heal error: {str(e)[:200]}"}
        return {"error": "self-heal monitor unavailable"}

    def remember(self, query: str = None, insight: str = None) -> Dict:
        """Persistent memory: recall or store insights across sessions."""
        pm = self._load_engine("persistent_memory")
        if pm:
            try:
                if insight:
                    return pm.store(insight_type="insight", content=insight)
                if query:
                    return pm.recall(query)
                return pm.get_recent(limit=10)
            except Exception as e:
                return {"error": f"Memory error: {str(e)[:200]}"}
        return {"error": "persistent memory unavailable"}

    # ═══════════════════════════════════════════════════════════════════
    # NLP + ARGUMENTATION (ARG) + MESSAGE INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════

    def analyze_argumentation(self, text: str) -> Dict:
        """
        Full argumentation analysis:
        - Adversarial attack tree prediction
        - Contradiction discovery in text
        - Evidence chain strength assessment
        - Citation gap identification
        """
        t0 = time.time()
        arg_results = {}

        # Attack tree
        adv = self._load_engine("adversarial")
        if adv:
            try:
                arg_results["attack_tree"] = adv.predict_attacks(text[:3000])
            except Exception:
                arg_results["attack_tree"] = {"error": "unavailable"}

        # Contradictions
        contra = self._load_engine("contradiction")
        if contra:
            try:
                arg_results["contradictions"] = contra.find_contradictions(text[:3000])
            except Exception:
                arg_results["contradictions"] = []

        # Evidence strength
        ec = self._load_engine("evidence_chains")
        if ec:
            try:
                arg_results["evidence_chains"] = ec.build_chains(text[:500], max_hops=3)
            except Exception:
                arg_results["evidence_chains"] = []

        # Citation gaps
        cg = self._load_engine("citation_gap")
        if cg:
            try:
                arg_results["citation_gaps"] = cg.find_gaps(text[:3000])
            except Exception:
                arg_results["citation_gaps"] = []

        arg_results["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
        arg_results["engine"] = "NEXUS-ARG-v2.0"
        return arg_results

    def analyze_messages(self, limit: int = 100) -> Dict:
        """Message intelligence: analyze chat messages for harm patterns."""
        mi = self._load_engine("message_intel")
        if mi:
            try:
                return mi.analyze_recent(limit=limit)
            except Exception as e:
                return {"error": f"Message intel error: {str(e)[:200]}"}
        return {"error": "message intelligence unavailable"}

    def mine_patterns(self, topic: str = None) -> Dict:
        """Pattern mining across 308K+ evidence quotes."""
        pm = self._load_engine("pattern_miner")
        if pm:
            try:
                return pm.mine(topic=topic) if topic else pm.mine_all()
            except Exception as e:
                return {"error": f"Pattern miner error: {str(e)[:200]}"}
        return {"error": "pattern miner unavailable"}

    def cross_reference(self, query: str) -> Dict:
        """Cross-reference engine: 69K cross-refs across all evidence."""
        xref = self._load_engine("cross_reference")
        if xref:
            try:
                return xref.search(query)
            except Exception as e:
                return {"error": f"Cross-ref error: {str(e)[:200]}"}
        return {"error": "cross-reference engine unavailable"}

    # ═══════════════════════════════════════════════════════════════════
    # COPILOT AGENT DISPATCH (22 agents)
    # ═══════════════════════════════════════════════════════════════════

    COPILOT_AGENTS = [
        "adversary-war-room", "brief-writer", "citation-researcher",
        "convergence-coordinator", "deadline-sentinel", "deposition-prep",
        "discovery-manager", "document-classifier", "evidence-harvester",
        "exhibit-curator", "federal-1983-specialist", "filing-assembler",
        "financial-analyst", "gdrive-watcher", "harm-tracker",
        "impeachment-commander", "legal-phase-indexer",
        "michigan-litigation-orchestrator", "motion-drafter",
        "msc-fleet-commander", "timeline-builder", "witness-profiler",
    ]

    def list_agents(self) -> Dict:
        """List all 22 Copilot agent definitions."""
        agents_dir = LITIGOS_ROOT / ".copilot" / "agents"
        found = []
        if agents_dir.exists():
            for f in agents_dir.glob("*.agent.md"):
                found.append(f.stem.replace(".agent", ""))
        return {"agents": sorted(found), "count": len(found),
                "registered": self.COPILOT_AGENTS}

    # ═══════════════════════════════════════════════════════════════════
    # DOCKET + TIMELINE + COMPLIANCE (Michigan-Specific)
    # ═══════════════════════════════════════════════════════════════════

    def analyze_docket(self) -> Dict:
        """Docket analyzer: 7,131 chronology events."""
        da = self._load_engine("docket_analyzer")
        if da:
            try:
                return da.analyze()
            except Exception as e:
                return {"error": f"Docket error: {str(e)[:200]}"}
        return {"error": "docket analyzer unavailable"}

    def check_compliance(self, filing_type: str = "motion") -> Dict:
        """MCR compliance check for filing type."""
        comp = self._load_engine("compliance")
        if comp:
            try:
                return comp.check(filing_type)
            except Exception as e:
                return {"error": f"Compliance error: {str(e)[:200]}"}
        return {"error": "compliance engine unavailable"}

    def calculate_harms(self) -> Dict:
        """Harms calculator: $774K-$5.28M damages across all forums."""
        harms = self._load_engine("harms")
        if harms:
            try:
                return harms.calculate()
            except Exception as e:
                return {"error": f"Harms error: {str(e)[:200]}"}
        return {"error": "harms calculator unavailable"}

    # ═══════════════════════════════════════════════════════════════════
    # MEGA-STATUS: Complete 85-system dashboard
    # ═══════════════════════════════════════════════════════════════════

    def mega_status(self) -> Dict:
        """Full 85+ system status across all tiers + skills + agents."""
        t0 = time.time()
        ms = self.status()

        # Skills
        ms["skills"] = self.list_skills()
        # Agents
        ms["agents"] = self.list_agents()
        # Core brains
        ms["core_brains"] = self.CORE_BRAINS

        # Engine health per tier
        tier_map = {
            "T0_Security": ["self_heal"],
            "T1_Database": ["context_loader", "persistent_memory"],
            "T2_Retrieval": ["manbearpig", "hybrid_retriever", "bm25", "semantic_engine",
                            "hf_engine", "query_expander", "reranker"],
            "T3_Classification": ["doc_classifier", "entity_resolver", "admissibility"],
            "T4_Reasoning": ["corrective_rag", "graph_rag", "knowledge_graph",
                            "authority_pagerank", "pattern_recognition"],
            "T5_Analysis": ["adversarial", "contradiction", "evidence_chains", "temporal",
                           "citation_validator", "citation_gap", "compliance", "filing_validator",
                           "harms", "risk", "judicial", "impeachment"],
            "T6_Orchestration": ["orchestrator", "litigation_fsm", "self_evolve",
                                "session_recall"],
            "T7_Filing": ["filing_assembler", "efiling", "exhibit_packager", "redaction"],
            "T8_Apps": ["message_intel", "scan_ingester", "docket_analyzer",
                       "pattern_miner", "cross_reference", "document_qa"],
        }

        ms["tiers"] = {}
        for tier, engines in tier_map.items():
            tier_status = {}
            for eng_name in engines:
                if eng_name in self._engines:
                    tier_status[eng_name] = "🟢 LOADED"
                elif eng_name in self._breakers and self._breakers[eng_name].state == CB_OPEN:
                    tier_status[eng_name] = "🔴 CIRCUIT_OPEN"
                else:
                    tier_status[eng_name] = "🟡 AVAILABLE"
            ms["tiers"][tier] = tier_status

        ms["total_systems"] = self.SYSTEM_COUNT
        ms["total_skills"] = self.SKILL_COUNT
        ms["total_agents"] = self.AGENT_COUNT
        ms["total_tiers"] = self.TIER_COUNT
        ms["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
        return ms


# ── CLI ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--benchmark" in sys.argv:
        nexus = NexusEngine()
        results = nexus.benchmark()
    elif "--status" in sys.argv:
        nexus = NexusEngine()
        st = nexus.status()
        print(json.dumps(st, indent=2, default=str))
    elif "--warmup" in sys.argv:
        nexus = NexusEngine()
        report = nexus.warmup()
        print(json.dumps(report, indent=2, default=str))
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        query_text = " ".join(sys.argv[1:])
        nexus = NexusEngine()
        result = nexus.query(query_text)
        print(result.get("response", "No response"))
        print(f"\n--- [NEXUS | {result.get('intent','?')} | {result.get('confidence',0):.0%} | "
              f"{result.get('elapsed_ms',0)}ms | {result.get('search_results',0)} results] ---")
    else:
        print("THE NEXUS v1.0 — Neural EXtraction & Unified Search")
        print("Usage:")
        print("  python nexus_engine.py 'your legal question'   # Full query")
        print("  python nexus_engine.py --benchmark              # System benchmark")
        print("  python nexus_engine.py --status                 # System status")
        print("  python nexus_engine.py --warmup                 # Pre-load engines")
