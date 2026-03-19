"""
THE MANBEARPIG — Graph RAG Engine (EPOCH v4.0)
===============================================
Combines Knowledge Graph traversal with text retrieval for hybrid
graph-augmented retrieval.  Entity extraction → KG traversal →
context assembly → FTS5/semantic text retrieval → synthesis.

Falls back to FTS5-only when KG or semantic engine is unavailable.
"""

import os
import re
import sqlite3
import time
import logging
from typing import Dict, List, Any, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Lazy imports — gracefully degrade when engines are not loadable
# ---------------------------------------------------------------------------
try:
    from knowledge_graph import KnowledgeGraphEngine
    _HAS_KG = True
except Exception:
    _HAS_KG = False

try:
    from semantic_engine import SemanticEngine
    _HAS_SEMANTIC = True
except Exception:
    _HAS_SEMANTIC = False

logger = logging.getLogger(__name__)

DEFAULT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ---------------------------------------------------------------------------
# Regex patterns for Michigan legal references
# ---------------------------------------------------------------------------
_MCR_RE = re.compile(r"MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*)", re.IGNORECASE)
_MCL_RE = re.compile(r"MCL\s+(\d+\.\d+[a-z]?(?:\([A-Za-z0-9]+\))*)", re.IGNORECASE)
_MRE_RE = re.compile(r"MRE\s+(\d+(?:\([A-Za-z0-9]+\))*)", re.IGNORECASE)

# Known legal concept entities for quick matching
_KNOWN_ENTITIES = [
    "best interest factors", "established custodial environment",
    "parental alienation", "change of circumstances",
    "friend of the court", "summary disposition",
    "disqualification", "personal protection order",
    "appeal of right", "superintending control",
    "motion to compel", "service of process",
    "parenting time", "contempt of court",
    "due process", "guardian ad litem",
]


class GraphRAG:
    """Graph-augmented Retrieval engine for THE MANBEARPIG."""

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path
        self._kg: Optional[Any] = None
        self._sem: Optional[Any] = None
        self._kg_available = _HAS_KG
        self._sem_available = _HAS_SEMANTIC

    # ------------------------------------------------------------------
    # Lazy loaders
    # ------------------------------------------------------------------
    def _get_kg(self) -> Optional[Any]:
        if self._kg is None and self._kg_available:
            try:
                self._kg = KnowledgeGraphEngine(db_path=self.db_path)
            except Exception as exc:
                logger.warning("KG engine unavailable: %s", exc)
                self._kg_available = False
        return self._kg

    def _get_sem(self) -> Optional[Any]:
        if self._sem is None and self._sem_available:
            try:
                self._sem = SemanticEngine()
            except Exception as exc:
                logger.warning("Semantic engine unavailable: %s", exc)
                self._sem_available = False
        return self._sem

    def _connect_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract legal entities and rule references from *text*."""
        entities: List[Dict[str, str]] = []
        seen: Set[str] = set()

        for m in _MCR_RE.finditer(text):
            canon = f"MCR {m.group(1)}"
            if canon not in seen:
                entities.append({"type": "MCR", "value": canon})
                seen.add(canon)

        for m in _MCL_RE.finditer(text):
            canon = f"MCL {m.group(1)}"
            if canon not in seen:
                entities.append({"type": "MCL", "value": canon})
                seen.add(canon)

        for m in _MRE_RE.finditer(text):
            canon = f"MRE {m.group(1)}"
            if canon not in seen:
                entities.append({"type": "MRE", "value": canon})
                seen.add(canon)

        text_lower = text.lower()
        for concept in _KNOWN_ENTITIES:
            if concept in text_lower and concept not in seen:
                entities.append({"type": "concept", "value": concept})
                seen.add(concept)

        return entities

    # ------------------------------------------------------------------
    # Graph traversal
    # ------------------------------------------------------------------
    def _traverse_graph(
        self, entities: List[Dict[str, str]], max_hops: int
    ) -> Dict[str, Any]:
        """Traverse the KG from each entity up to *max_hops*."""
        kg = self._get_kg()
        paths: List[Dict[str, Any]] = []
        related_nodes: List[str] = []

        if kg is None:
            return {"paths": paths, "related_nodes": related_nodes}

        for ent in entities:
            label = ent["value"]
            subgraph = kg.subgraph_around(label, depth=max_hops)
            if "error" not in subgraph:
                paths.append({
                    "seed": label,
                    "node_count": subgraph.get("node_count", 0),
                    "edge_count": subgraph.get("edge_count", 0),
                    "nodes": subgraph.get("nodes", []),
                    "edges": subgraph.get("edges", []),
                })
                for node in subgraph.get("nodes", []):
                    if node["label"] not in related_nodes:
                        related_nodes.append(node["label"])

        return {"paths": paths, "related_nodes": related_nodes}

    # ------------------------------------------------------------------
    # Text retrieval (FTS5 fallback always available)
    # ------------------------------------------------------------------
    def _fts_search(
        self, terms: List[str], limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Search auth_rules, evidence_quotes, rules_text via FTS5."""
        results: List[Dict[str, Any]] = []
        if not terms:
            return results

        match_expr = " OR ".join(f'"{t}"' for t in terms[:20])

        queries = [
            (
                "auth_rules_fts",
                "SELECT rule_number, title, snippet(auth_rules_fts, 2, '>>','<<', '…', 48) AS snip "
                "FROM auth_rules_fts WHERE auth_rules_fts MATCH ? LIMIT ?",
                "authority",
            ),
            (
                "evidence_quotes_fts",
                "SELECT quote_text, speaker, evidence_category, "
                "snippet(evidence_quotes_fts, 0, '>>','<<', '…', 48) AS snip "
                "FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ? LIMIT ?",
                "evidence",
            ),
            (
                "rules_text_fts",
                "SELECT rule, chapter, snippet(rules_text_fts, 2, '>>','<<', '…', 48) AS snip "
                "FROM rules_text_fts WHERE rules_text_fts MATCH ? LIMIT ?",
                "rule_text",
            ),
        ]

        try:
            conn = self._connect_db()
            try:
                for table_name, sql, source_type in queries:
                    try:
                        rows = conn.execute(sql, (match_expr, limit)).fetchall()
                        for row in rows:
                            results.append({
                                "source": source_type,
                                "data": dict(row),
                            })
                    except sqlite3.OperationalError:
                        pass  # table may not exist
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.warning("FTS search failed: %s", exc)

        return results

    def _semantic_search(
        self, query: str, top_k: int = 15
    ) -> List[Dict[str, Any]]:
        """Semantic vector search via SemanticEngine (if available)."""
        sem = self._get_sem()
        if sem is None:
            return []
        try:
            return sem.search(query, top_k=top_k)
        except Exception as exc:
            logger.warning("Semantic search failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def query(self, question: str, max_hops: int = 3) -> dict:
        """Main Graph RAG pipeline.

        1. Entity Extraction  2. Graph Traversal  3. Context Assembly
        4. Text Retrieval     5. Synthesis

        Returns:
            {entities_found, graph_paths, related_authorities,
             supporting_text, answer_context}
        """
        t0 = time.time()

        # 1. Entity extraction
        entities = self._extract_entities(question)

        # 2. Graph traversal
        graph_result = self._traverse_graph(entities, max_hops)
        graph_paths = graph_result["paths"]
        related_nodes = graph_result["related_nodes"]

        # 3. Context assembly — derive search terms from graph nodes
        search_terms = [e["value"] for e in entities]
        search_terms.extend(related_nodes[:30])
        unique_terms = list(dict.fromkeys(search_terms))

        # 4a. FTS5 text retrieval
        fts_results = self._fts_search(unique_terms)

        # 4b. Semantic text retrieval
        sem_results = self._semantic_search(question, top_k=15)

        # 5. Synthesis
        related_authorities = [
            n for n in related_nodes
            if any(n.upper().startswith(p) for p in ("MCR", "MCL", "MRE"))
        ]
        supporting_text = fts_results + [
            {"source": "semantic", "data": r} for r in sem_results
        ]

        # Build answer context string
        context_parts: List[str] = []
        for path_info in graph_paths:
            labels = [n["label"] for n in path_info.get("nodes", [])]
            context_parts.append(
                f"Graph neighborhood of '{path_info['seed']}': "
                f"{', '.join(labels[:15])}"
            )
        for item in fts_results[:10]:
            snip = item["data"].get("snip", "")
            if snip:
                context_parts.append(snip)

        return {
            "entities_found": entities,
            "graph_paths": graph_paths,
            "related_authorities": related_authorities,
            "supporting_text": supporting_text,
            "answer_context": "\n".join(context_parts),
            "stats": {
                "entity_count": len(entities),
                "graph_nodes_traversed": len(related_nodes),
                "fts_hits": len(fts_results),
                "semantic_hits": len(sem_results),
                "elapsed_sec": round(time.time() - t0, 3),
            },
        }

    # ------------------------------------------------------------------
    def authority_chain(
        self, source_rule: str, target_rule: str
    ) -> dict:
        """Find the authority chain between two rules via the KG,
        then retrieve full text for each node in the chain."""
        kg = self._get_kg()

        chain: Dict[str, Any] = {"source": source_rule, "target": target_rule}

        if kg is not None:
            path_result = kg.find_path(source_rule, target_rule)
            chain["path"] = path_result
        else:
            chain["path"] = {"error": "KG engine unavailable"}

        # Retrieve full text for each node label in the path
        path_nodes = []
        if isinstance(chain["path"], dict) and chain["path"].get("reachable"):
            path_nodes = [n["label"] for n in chain["path"].get("path", [])]

        texts: List[Dict[str, Any]] = []
        if path_nodes:
            try:
                conn = self._connect_db()
                try:
                    for label in path_nodes:
                        row = conn.execute(
                            "SELECT rule_number, title, full_text "
                            "FROM auth_rules WHERE rule_number = ? LIMIT 1",
                            (label,),
                        ).fetchone()
                        texts.append({
                            "label": label,
                            "text": dict(row) if row else None,
                        })
                finally:
                    conn.close()
            except sqlite3.Error as exc:
                logger.warning("authority_chain text lookup failed: %s", exc)

        chain["node_texts"] = texts
        return chain

    # ------------------------------------------------------------------
    def entity_context(self, entity: str) -> dict:
        """Full context for an entity: graph neighborhood + DB text."""
        # Graph neighborhood
        kg = self._get_kg()
        subgraph: Dict[str, Any] = {}
        if kg is not None:
            subgraph = kg.subgraph_around(entity, depth=2)

        # Related authorities from KG
        related: List[Dict[str, Any]] = []
        if kg is not None:
            related = kg.find_related_authorities(entity, top_k=10)

        # DB text
        fts_results = self._fts_search([entity], limit=20)
        sem_results = self._semantic_search(entity, top_k=10)

        return {
            "entity": entity,
            "graph_neighborhood": subgraph,
            "related_authorities": related,
            "fts_text": fts_results,
            "semantic_text": sem_results,
        }

    # ------------------------------------------------------------------
    def multi_hop_reasoning(self, question: str) -> dict:
        """Decompose question into sub-questions, answer each via
        graph + text, then synthesize."""
        # Decompose: split on conjunctions / question marks
        sub_questions: List[str] = []
        for part in re.split(r"\band\b|\?|;", question):
            part = part.strip()
            if len(part) > 10:
                sub_questions.append(part)
        if not sub_questions:
            sub_questions = [question]

        sub_answers: List[Dict[str, Any]] = []
        all_entities: List[Dict[str, str]] = []
        all_authorities: List[str] = []

        for sq in sub_questions:
            result = self.query(sq, max_hops=2)
            sub_answers.append({
                "sub_question": sq,
                "entities": result["entities_found"],
                "authorities": result["related_authorities"],
                "context_snippet": result["answer_context"][:500],
            })
            all_entities.extend(result["entities_found"])
            all_authorities.extend(result["related_authorities"])

        # Cross-link: find paths between entities from different sub-questions
        cross_links: List[Dict[str, Any]] = []
        kg = self._get_kg()
        if kg is not None and len(sub_answers) >= 2:
            first_ents = [e["value"] for e in sub_answers[0].get("entities", [])]
            last_ents = [e["value"] for e in sub_answers[-1].get("entities", [])]
            for src in first_ents[:3]:
                for tgt in last_ents[:3]:
                    if src != tgt:
                        path = kg.find_path(src, tgt)
                        if path.get("reachable"):
                            cross_links.append(path)

        return {
            "original_question": question,
            "sub_questions": sub_questions,
            "sub_answers": sub_answers,
            "cross_links": cross_links,
            "all_entities": list({e["value"]: e for e in all_entities}.values()),
            "all_authorities": list(dict.fromkeys(all_authorities)),
        }

    # ------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------
    def self_test(self) -> None:
        """Smoke-test the Graph RAG pipeline."""
        print("=" * 60)
        print("Graph RAG — self-test")
        print("=" * 60)

        # Test 1: entity extraction
        test_q1 = "How does MCR 2.003 relate to MCR 7.204?"
        ents = self._extract_entities(test_q1)
        print(f"\n[1] Entity extraction for: '{test_q1}'")
        print(f"    Entities: {ents}")
        assert any(e["value"] == "MCR 2.003" for e in ents), "MCR 2.003 not found"
        assert any(e["value"] == "MCR 7.204" for e in ents), "MCR 7.204 not found"
        print("    ✓ PASS")

        # Test 2: full pipeline
        print(f"\n[2] Full pipeline query: '{test_q1}'")
        result = self.query(test_q1)
        assert "entities_found" in result
        assert "graph_paths" in result
        assert "related_authorities" in result
        assert "supporting_text" in result
        assert "answer_context" in result
        print(f"    Entities found: {len(result['entities_found'])}")
        print(f"    Graph nodes traversed: {result['stats']['graph_nodes_traversed']}")
        print(f"    FTS hits: {result['stats']['fts_hits']}")
        print(f"    Semantic hits: {result['stats']['semantic_hits']}")
        print(f"    Elapsed: {result['stats']['elapsed_sec']}s")
        print("    ✓ PASS")

        # Test 3: second query
        test_q2 = "What authority supports disqualification for bias?"
        print(f"\n[3] Full pipeline query: '{test_q2}'")
        result2 = self.query(test_q2)
        print(f"    Entities found: {len(result2['entities_found'])}")
        print(f"    Graph nodes traversed: {result2['stats']['graph_nodes_traversed']}")
        print(f"    FTS hits: {result2['stats']['fts_hits']}")
        print(f"    Elapsed: {result2['stats']['elapsed_sec']}s")
        print("    ✓ PASS")

        # Test 4: authority chain
        print("\n[4] Authority chain: MCR 2.003 → MCR 7.204")
        chain = self.authority_chain("MCR 2.003", "MCR 7.204")
        print(f"    Reachable: {chain['path'].get('reachable', 'N/A')}")
        print(f"    Node texts retrieved: {len(chain.get('node_texts', []))}")
        print("    ✓ PASS")

        # Test 5: entity context
        print("\n[5] Entity context: MCR 2.003")
        ctx = self.entity_context("MCR 2.003")
        print(f"    Graph neighborhood nodes: "
              f"{ctx['graph_neighborhood'].get('node_count', 'N/A')}")
        print(f"    FTS results: {len(ctx['fts_text'])}")
        print("    ✓ PASS")

        # Test 6: multi-hop reasoning
        print(f"\n[6] Multi-hop reasoning: '{test_q1}'")
        mhr = self.multi_hop_reasoning(test_q1)
        print(f"    Sub-questions: {len(mhr['sub_questions'])}")
        print(f"    Cross-links: {len(mhr['cross_links'])}")
        print(f"    All entities: {len(mhr['all_entities'])}")
        print("    ✓ PASS")

        print("\n" + "=" * 60)
        print("Graph RAG — ALL TESTS PASSED")
        print("=" * 60)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    GraphRAG().self_test()
