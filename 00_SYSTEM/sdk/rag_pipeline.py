"""
Local RAG Pipeline — emulates inference.sh RAG patterns using MANBEARPIG + FTS5.

Instead of Tavily/Exa cloud search → OpenRouter LLM, this uses:
  - FTS5 full-text search over litigation_context.db (694 tables)
  - TF-IDF retrieval via MANBEARPIG vectorizer
  - BM25 scoring via HybridRetriever (when available)
  - Authority chain lookup via find_authority()
  - Legal concept matching via match_concepts()
  - Synthesis via MANBEARPIG's query() method

Patterns supported:
  1. Simple Search + Answer (single source)
  2. Multi-Source Research (FTS5 + TF-IDF + authority + concepts)
  3. Extract + Process (document analysis + synthesis)
  4. Fact-Checking (citation verification + authority cross-ref)
  5. Iterative Research (broad → narrow → synthesis)

Usage:
    from sdk.rag_pipeline import RAGPipeline

    rag = RAGPipeline()
    result = rag.search("MCR 2.003 disqualification requirements")
    result = rag.research_report("judicial misconduct patterns in Michigan")
    result = rag.fact_check("Judge McNeill violated MCR 2.003")
"""

from __future__ import annotations

import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)
MCR_DB_PATH = os.environ.get(
    "MCR_DB_PATH",
    r"C:\Users\andre\LitigationOS\mcr_rules.db",
)


@dataclass
class SearchResult:
    """A single search result from any source."""
    source: str        # "fts5", "tfidf", "authority", "concept", "mcr_db"
    title: str
    text: str
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "title": self.title,
            "text": self.text[:500],
            "score": self.score,
            "metadata": self.metadata,
        }


@dataclass
class RAGResult:
    """Complete RAG pipeline result."""
    query: str
    synthesis: str
    sources: List[SearchResult]
    confidence: float
    elapsed_ms: float
    source_counts: Dict[str, int]
    patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "synthesis": self.synthesis,
            "sources": [s.to_dict() for s in self.sources],
            "confidence": self.confidence,
            "elapsed_ms": self.elapsed_ms,
            "source_counts": self.source_counts,
            "total_sources": len(self.sources),
            "patterns": self.patterns,
        }


def _get_db(path: str = DB_PATH) -> Optional[sqlite3.Connection]:
    """Get a read-only DB connection with proper PRAGMAs."""
    try:
        if not Path(path).exists():
            return None
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        return conn
    except Exception as e:
        logger.error(f"DB connection failed for {path}: {e}")
        return None


class RAGPipeline:
    """
    Local RAG pipeline — retrieval + augmentation + generation using MANBEARPIG.

    All computation is local. No network calls. No API keys.
    """

    def __init__(self, model=None):
        self._model = model

    @property
    def model(self):
        """Lazy-load MANBEARPIG."""
        if self._model is None:
            import sys
            model_dir = str(Path(__file__).resolve().parent.parent / "local_model")
            sys.path.insert(0, model_dir)
            try:
                from inference_engine import MichiganLegalModel
                self._model = MichiganLegalModel()
            except Exception as e:
                logger.error(f"Failed to load MANBEARPIG: {e}")
            finally:
                if model_dir in sys.path:
                    sys.path.remove(model_dir)
        return self._model

    # ── Pattern 1: Simple Search + Answer ──────────────────────────

    def search(self, query: str, top_k: int = 10) -> RAGResult:
        """Single-source search: FTS5 + TF-IDF retrieval + synthesis."""
        start = time.time()
        sources = []
        source_counts = {}

        # Source 1: FTS5 full-text search
        fts_results = self._fts5_search(query, limit=top_k)
        sources.extend(fts_results)
        source_counts["fts5"] = len(fts_results)

        # Source 2: TF-IDF retrieval
        if self.model:
            tfidf_results = self._tfidf_search(query, top_k=top_k)
            sources.extend(tfidf_results)
            source_counts["tfidf"] = len(tfidf_results)

        # Synthesis
        synthesis, confidence = self._synthesize(query, sources)

        elapsed = (time.time() - start) * 1000
        return RAGResult(
            query=query,
            synthesis=synthesis,
            sources=sources,
            confidence=confidence,
            elapsed_ms=elapsed,
            source_counts=source_counts,
        )

    # ── Pattern 2: Multi-Source Research ────────────────────────────

    def research(self, query: str, top_k: int = 10) -> RAGResult:
        """Multi-source research: FTS5 + TF-IDF + authority + concepts + MCR DB."""
        start = time.time()
        all_sources = []
        source_counts = {}

        # Source 1: FTS5
        fts = self._fts5_search(query, limit=top_k)
        all_sources.extend(fts)
        source_counts["fts5"] = len(fts)

        # Source 2: TF-IDF
        if self.model:
            tfidf = self._tfidf_search(query, top_k=top_k)
            all_sources.extend(tfidf)
            source_counts["tfidf"] = len(tfidf)

        # Source 3: Authority chains
        if self.model:
            authority = self._authority_search(query, limit=5)
            all_sources.extend(authority)
            source_counts["authority"] = len(authority)

        # Source 4: Legal concepts
        if self.model:
            concepts = self._concept_search(query)
            all_sources.extend(concepts)
            source_counts["concepts"] = len(concepts)

        # Source 5: MCR rules DB
        mcr = self._mcr_search(query, limit=5)
        all_sources.extend(mcr)
        source_counts["mcr_db"] = len(mcr)

        # Deduplicate by title
        seen_titles = set()
        unique_sources = []
        for s in sorted(all_sources, key=lambda x: x.score, reverse=True):
            if s.title not in seen_titles:
                seen_titles.add(s.title)
                unique_sources.append(s)

        # Synthesis
        synthesis, confidence = self._synthesize(query, unique_sources)

        elapsed = (time.time() - start) * 1000
        return RAGResult(
            query=query,
            synthesis=synthesis,
            sources=unique_sources,
            confidence=confidence,
            elapsed_ms=elapsed,
            source_counts=source_counts,
        )

    # ── Pattern 3: Document Analysis ───────────────────────────────

    def analyze(self, text: str) -> RAGResult:
        """Extract + Process: analyze a document and augment with DB context."""
        start = time.time()
        sources = []

        if self.model:
            analysis = self.model.analyze_document(text)

            # Use extracted entities to find authority
            citations = analysis.get("citations", [])
            for cite in citations[:10]:
                if isinstance(cite, dict):
                    ref = cite.get("reference", cite.get("citation", ""))
                else:
                    ref = str(cite)
                auth_results = self._authority_search(ref, limit=2)
                sources.extend(auth_results)

            synthesis = json.dumps(analysis, default=str, indent=2) if isinstance(analysis, dict) else str(analysis)
            confidence = analysis.get("confidence", 0.5) if isinstance(analysis, dict) else 0.5
        else:
            synthesis = "MANBEARPIG model not loaded."
            confidence = 0.0

        elapsed = (time.time() - start) * 1000
        return RAGResult(
            query=f"[document analysis: {len(text)} chars]",
            synthesis=synthesis,
            sources=sources,
            confidence=confidence,
            elapsed_ms=elapsed,
            source_counts={"authority": len(sources)},
        )

    # ── Pattern 4: Fact-Checking ───────────────────────────────────

    def fact_check(self, claim: str) -> RAGResult:
        """Verify a legal claim against DB authority and evidence."""
        start = time.time()
        sources = []
        source_counts = {}
        patterns = []

        if self.model:
            # Step 1: Check citations in claim
            cite_results = self.model.check_citations(claim)
            if isinstance(cite_results, list):
                for cr in cite_results:
                    status = cr.get("status", "unknown") if isinstance(cr, dict) else "unknown"
                    sources.append(SearchResult(
                        source="citation_check",
                        title=cr.get("citation", str(cr)) if isinstance(cr, dict) else str(cr),
                        text=f"Status: {status}",
                        score=1.0 if status == "verified" else 0.3,
                        metadata=cr if isinstance(cr, dict) else {},
                    ))
                source_counts["citation_check"] = len(cite_results)

            # Step 2: Search for supporting/contradicting evidence
            evidence = self._fts5_search(claim, limit=10)
            sources.extend(evidence)
            source_counts["fts5"] = len(evidence)

            # Step 3: Authority verification
            authority = self._authority_search(claim, limit=5)
            sources.extend(authority)
            source_counts["authority"] = len(authority)

            # Step 4: Synthesize verdict
            verified_count = sum(1 for s in sources if s.score > 0.7)
            total = len(sources)
            if verified_count > total * 0.7:
                patterns.append("SUPPORTED — strong evidence found")
            elif verified_count > total * 0.3:
                patterns.append("PARTIALLY_SUPPORTED — mixed evidence")
            else:
                patterns.append("UNVERIFIED — insufficient supporting evidence")

            synthesis, confidence = self._synthesize(claim, sources)
        else:
            synthesis = "MANBEARPIG model not loaded."
            confidence = 0.0

        elapsed = (time.time() - start) * 1000
        return RAGResult(
            query=claim,
            synthesis=synthesis,
            sources=sources,
            confidence=confidence,
            elapsed_ms=elapsed,
            source_counts=source_counts,
            patterns=patterns,
        )

    # ── Pattern 5: Research Report ─────────────────────────────────

    def research_report(self, topic: str) -> RAGResult:
        """Generate a comprehensive research report with executive summary."""
        start = time.time()

        # Broad search
        broad = self.research(topic, top_k=15)

        # Narrow search on key subtopics from broad results
        subtopics = self._extract_subtopics(broad.sources)
        narrow_sources = []
        for sub in subtopics[:3]:
            narrow = self.search(f"{topic} {sub}", top_k=5)
            narrow_sources.extend(narrow.sources)

        all_sources = broad.sources + narrow_sources

        # Deduplicate
        seen = set()
        unique = []
        for s in sorted(all_sources, key=lambda x: x.score, reverse=True):
            if s.title not in seen:
                seen.add(s.title)
                unique.append(s)

        synthesis, confidence = self._synthesize(topic, unique)

        elapsed = (time.time() - start) * 1000
        return RAGResult(
            query=topic,
            synthesis=synthesis,
            sources=unique[:30],
            confidence=confidence,
            elapsed_ms=elapsed,
            source_counts={"total": len(unique)},
            patterns=[f"subtopics_explored: {subtopics[:3]}"],
        )

    # ── Internal Search Methods ────────────────────────────────────

    def _fts5_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search using FTS5 across known FTS tables."""
        results = []
        conn = _get_db()
        if not conn:
            return results

        try:
            # Search the main search_index FTS5 table if it exists
            fts_tables = [
                ("search_index", "content", "source"),
                ("documents_fts", "content", "title"),
                ("evidence_fts", "text", "source_file"),
            ]

            # Sanitize query for FTS5 — remove special chars
            safe_query = " ".join(
                w for w in query.split()
                if w.isalnum() or w.replace(".", "").replace("-", "").isalnum()
            )
            if not safe_query:
                safe_query = query.split()[0] if query.split() else "law"

            for table, content_col, title_col in fts_tables:
                try:
                    rows = conn.execute(
                        f"SELECT {content_col}, {title_col}, rank "
                        f"FROM {table} WHERE {table} MATCH ? "
                        f"ORDER BY rank LIMIT ?",
                        (safe_query, limit),
                    ).fetchall()
                    for row in rows:
                        results.append(SearchResult(
                            source="fts5",
                            title=str(row[1] or "unknown"),
                            text=str(row[0] or "")[:500],
                            score=abs(float(row[2])) if row[2] else 0.5,
                            metadata={"table": table},
                        ))
                except sqlite3.OperationalError:
                    continue  # Table doesn't exist

            # Fallback: LIKE search on key tables
            if not results:
                like_pattern = f"%{query.split()[0] if query.split() else ''}%"
                for table, col in [
                    ("court_rules", "rule_text"),
                    ("mcl_sections", "section_text"),
                    ("master_citations", "citation_text"),
                ]:
                    try:
                        rows = conn.execute(
                            f"SELECT {col}, rowid FROM {table} "
                            f"WHERE {col} LIKE ? LIMIT ?",
                            (like_pattern, limit),
                        ).fetchall()
                        for row in rows:
                            results.append(SearchResult(
                                source="fts5",
                                title=f"{table}:{row[1]}",
                                text=str(row[0] or "")[:500],
                                score=0.3,
                                metadata={"table": table, "fallback": True},
                            ))
                    except sqlite3.OperationalError:
                        continue
        except Exception as e:
            logger.error(f"FTS5 search error: {e}")
        finally:
            conn.close()

        return results

    def _tfidf_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search using MANBEARPIG's TF-IDF retriever."""
        results = []
        if not self.model:
            return results

        try:
            raw = self.model.retrieve(query, top_k=top_k)
            for item in raw:
                if isinstance(item, dict):
                    results.append(SearchResult(
                        source="tfidf",
                        title=item.get("label", item.get("title", "unknown")),
                        text=item.get("text", item.get("snippet", ""))[:500],
                        score=float(item.get("score", item.get("similarity", 0.5))),
                        metadata={k: v for k, v in item.items() if k not in ("text", "snippet")},
                    ))
        except Exception as e:
            logger.error(f"TF-IDF search error: {e}")

        return results

    def _authority_search(self, topic: str, limit: int = 5) -> List[SearchResult]:
        """Search authority chains via MANBEARPIG."""
        results = []
        if not self.model:
            return results

        try:
            raw = self.model.find_authority(topic, limit=limit)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        results.append(SearchResult(
                            source="authority",
                            title=item.get("rule_number", item.get("citation", item.get("title", "unknown"))),
                            text=item.get("text", item.get("description", item.get("rule_text", "")))[:500],
                            score=float(item.get("relevance", item.get("score", 0.7))),
                            metadata=item,
                        ))
            elif isinstance(raw, dict) and "results" in raw:
                for item in raw["results"]:
                    if isinstance(item, dict):
                        results.append(SearchResult(
                            source="authority",
                            title=item.get("rule_number", "unknown"),
                            text=item.get("text", "")[:500],
                            score=0.7,
                        ))
        except Exception as e:
            logger.error(f"Authority search error: {e}")

        return results

    def _concept_search(self, query: str) -> List[SearchResult]:
        """Match legal concepts via MANBEARPIG."""
        results = []
        if not self.model:
            return results

        try:
            raw = self.model.match_concepts(query)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        results.append(SearchResult(
                            source="concept",
                            title=item.get("id", item.get("name", "unknown")),
                            text=item.get("description", item.get("text", ""))[:500],
                            score=float(item.get("score", 0.6)),
                            metadata=item,
                        ))
        except Exception as e:
            logger.error(f"Concept search error: {e}")

        return results

    def _mcr_search(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Search Michigan Court Rules database directly."""
        results = []
        conn = _get_db(MCR_DB_PATH)
        if not conn:
            return results

        try:
            # Try FTS first
            safe_q = " ".join(w for w in query.split() if w.isalnum() or w.replace(".", "").isalnum())
            if safe_q:
                try:
                    rows = conn.execute(
                        "SELECT rule_number, rule_text, rank FROM rules_fts "
                        "WHERE rules_fts MATCH ? ORDER BY rank LIMIT ?",
                        (safe_q, limit),
                    ).fetchall()
                    for row in rows:
                        results.append(SearchResult(
                            source="mcr_db",
                            title=str(row[0]),
                            text=str(row[1])[:500],
                            score=abs(float(row[2])) if row[2] else 0.5,
                            metadata={"db": "mcr_rules.db"},
                        ))
                except sqlite3.OperationalError:
                    pass

            # Fallback: LIKE
            if not results:
                kw = query.split()[0] if query.split() else ""
                if kw:
                    try:
                        rows = conn.execute(
                            "SELECT rule_number, rule_text FROM rules "
                            "WHERE rule_text LIKE ? OR rule_number LIKE ? LIMIT ?",
                            (f"%{kw}%", f"%{kw}%", limit),
                        ).fetchall()
                        for row in rows:
                            results.append(SearchResult(
                                source="mcr_db",
                                title=str(row[0]),
                                text=str(row[1])[:500],
                                score=0.3,
                                metadata={"db": "mcr_rules.db", "fallback": True},
                            ))
                    except sqlite3.OperationalError:
                        pass
        except Exception as e:
            logger.error(f"MCR search error: {e}")
        finally:
            conn.close()

        return results

    def _synthesize(self, query: str, sources: List[SearchResult]) -> tuple:
        """Synthesize a response from sources using MANBEARPIG."""
        if not self.model:
            if sources:
                return (
                    "\n".join(f"- [{s.source}] {s.title}: {s.text[:200]}" for s in sources[:5]),
                    0.3,
                )
            return ("No results found.", 0.0)

        # Build context-augmented query
        context_parts = []
        for s in sources[:10]:
            context_parts.append(f"[{s.source}:{s.title}] {s.text[:300]}")

        augmented_query = query
        if context_parts:
            augmented_query = f"{query}\n\nRelevant context:\n" + "\n".join(context_parts)

        result = self.model.query(augmented_query)
        return (
            result.get("response", ""),
            result.get("confidence", 0.5),
        )

    def _extract_subtopics(self, sources: List[SearchResult]) -> List[str]:
        """Extract key subtopics from search results for iterative research."""
        if not self.model:
            return []

        # Collect all titles and extract entities
        all_text = " ".join(s.title for s in sources[:10])
        entities = self.model.extract_entities(all_text)

        subtopics = []
        for key, vals in entities.items():
            subtopics.extend(vals[:2])

        return list(set(subtopics))[:5]


# ── Convenience import for JSON serialization ──────────────────────
try:
    import json
except ImportError:
    pass
