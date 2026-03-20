"""RAG/AI engine — local-first retrieval-augmented generation via Ollama + ChromaDB.

Provides:
- Vector embedding and storage via ChromaDB (persistent, local)
- LLM inference via Ollama (Qwen2.5:7b for generation, nomic-embed-text for embeddings)
- Hybrid search: vector similarity + SQLite FTS5 keyword search
- Classification, summarization, and structured Q&A with citations

Gracefully degrades when Ollama or ChromaDB are unavailable.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: dict[str, Any] = {
    "ollama_url": "http://localhost:11434",
    "llm_model": "qwen2.5:7b",
    "embed_model": "nomic-embed-text",
    "chromadb_path": None,  # auto-detect next to DB
    "max_context_tokens": 4096,
}

_SYSTEM_PROMPT = (
    "You are a legal research assistant for Michigan family law litigation.\n\n"
    "RULES:\n"
    "1. Ground every answer in Michigan Court Rules (MCR), Michigan Compiled Laws (MCL), "
    "Michigan Rules of Evidence (MRE), or applicable federal law\n"
    "2. Cite as [SOURCE: authority_name] — only cite authorities present in the provided context\n"
    "3. If an authority is not in the context, state 'UNVERIFIED' — never fabricate citations\n"
    "4. End each answer with:\n"
    "   - CONFIDENCE: HIGH / MEDIUM / LOW\n"
    "   - SOURCES: list of cited authorities\n"
    "5. If the context is insufficient, state what additional information is needed"
)


class RAGEngine:
    """Local-first RAG engine backed by Ollama (LLM) and ChromaDB (vectors).

    Parameters
    ----------
    db : DatabaseManager
        Product database connection (used for FTS5 keyword searches).
    config : dict, optional
        Override any key in ``DEFAULT_CONFIG``.
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self, db: DatabaseManager, config: dict[str, Any] | None = None):
        self._db = db
        self._config = {**DEFAULT_CONFIG, **(config or {})}

        # Resolve ChromaDB persist path next to the product DB
        if self._config["chromadb_path"] is None:
            self._config["chromadb_path"] = str(
                Path(self._db.db_path).parent / "chromadb"
            )

        self._chroma_client: Any | None = None
        self._ollama_available: bool | None = None

        self._init_chromadb()
        self._check_ollama()

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _init_chromadb(self) -> None:
        """Initialise the ChromaDB persistent client."""
        try:
            import chromadb  # noqa: WPS433

            persist_dir = self._config["chromadb_path"]
            Path(persist_dir).mkdir(parents=True, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(path=persist_dir)
            logger.info("ChromaDB initialised at %s", persist_dir)
        except ImportError:
            logger.warning("chromadb package not installed -- vector search disabled")
            self._chroma_client = None
        except Exception:
            logger.exception("Failed to initialise ChromaDB")
            self._chroma_client = None

    def _check_ollama(self) -> None:
        """Probe the Ollama API to confirm it is reachable."""
        try:
            import urllib.request

            url = f"{self._config['ollama_url']}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5):
                pass
            self._ollama_available = True
            logger.info("Ollama reachable at %s", self._config["ollama_url"])
        except Exception:
            self._ollama_available = False
            logger.warning(
                "Ollama not reachable at %s -- LLM features disabled",
                self._config["ollama_url"],
            )

    @property
    def available(self) -> bool:
        """Return ``True`` if both Ollama and ChromaDB are usable."""
        return bool(self._chroma_client) and bool(self._ollama_available)

    # ------------------------------------------------------------------
    # Ollama HTTP helpers
    # ------------------------------------------------------------------

    def _ollama_post(self, endpoint: str, payload: dict) -> dict:
        """Send a POST request to the Ollama API and return the JSON response."""
        import urllib.request

        url = f"{self._config['ollama_url']}{endpoint}"
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode())

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def embed_text(self, text: str) -> list[float]:
        """Return an embedding vector for *text* via the configured embed model.

        Raises
        ------
        RuntimeError
            If Ollama is unreachable.
        """
        if not self._ollama_available:
            raise RuntimeError("Ollama is not available -- cannot embed text")

        resp = self._ollama_post(
            "/api/embeddings",
            {"model": self._config["embed_model"], "prompt": text},
        )
        return resp["embedding"]

    def embed_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Embed *text* and upsert it into the default ChromaDB collection.

        Parameters
        ----------
        doc_id : str
            Unique document identifier (used as the ChromaDB ID).
        text : str
            Document text to embed.
        metadata : dict, optional
            Arbitrary metadata stored alongside the vector.
        """
        if self._chroma_client is None:
            raise RuntimeError("ChromaDB is not available -- cannot store embeddings")

        embedding = self.embed_text(text)
        collection = self._chroma_client.get_or_create_collection("documents")
        collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}],
        )
        logger.debug("Embedded document %s (%d dims)", doc_id, len(embedding))

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        n_results: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Hybrid search: ChromaDB vector similarity + SQLite FTS5 keyword search.

        Results from both sources are merged and re-ranked by a combined score.

        Parameters
        ----------
        query : str
            Natural-language search query.
        n_results : int
            Maximum results to return (default 5).
        filters : dict, optional
            ChromaDB ``where`` filter dict.

        Returns
        -------
        list[dict]
            Each dict has keys: ``id``, ``text``, ``score``, ``source``, ``metadata``.
        """
        merged: dict[str, dict[str, Any]] = {}

        # --- 1. ChromaDB vector similarity ---
        if self._chroma_client is not None and self._ollama_available:
            try:
                query_embedding = self.embed_text(query)
                collection = self._chroma_client.get_or_create_collection("documents")
                kwargs: dict[str, Any] = {
                    "query_embeddings": [query_embedding],
                    "n_results": n_results,
                }
                if filters:
                    kwargs["where"] = filters
                results = collection.query(**kwargs)

                ids = results.get("ids", [[]])[0]
                docs = results.get("documents", [[]])[0]
                dists = results.get("distances", [[]])[0]
                metas = results.get("metadatas", [[]])[0]

                for idx, doc_id in enumerate(ids):
                    # ChromaDB distance → similarity (lower distance = higher score)
                    score = 1.0 / (1.0 + dists[idx])
                    merged[doc_id] = {
                        "id": doc_id,
                        "text": docs[idx] if idx < len(docs) else "",
                        "score": score,
                        "source": "vector",
                        "metadata": metas[idx] if idx < len(metas) else {},
                    }
            except Exception:
                logger.exception("ChromaDB search failed for query: %s", query[:80])

        # --- 2. SQLite FTS5 keyword search ---
        fts_tables = [
            ("evidence_fts", "evidence", "title", "description"),
            ("court_rules_fts", "court_rules", "rule_number", "full_text"),
        ]
        for fts_table, base_table, *text_cols in fts_tables:
            try:
                safe_query = query.replace('"', '""')
                rows = self._db.fetchall(
                    f"SELECT rowid, rank, {', '.join(text_cols)} "
                    f"FROM {fts_table} WHERE {fts_table} MATCH ? "
                    f"ORDER BY rank LIMIT ?",
                    (f'"{safe_query}"', n_results),
                )
                for row in rows:
                    fts_id = f"{base_table}:{row['rowid']}"
                    text_parts = [str(row[c]) for c in text_cols if row[c]]
                    fts_score = 1.0 / (1.0 + abs(row["rank"]))
                    if fts_id in merged:
                        # Boost items found in both vector and FTS
                        merged[fts_id]["score"] += fts_score
                        merged[fts_id]["source"] = "hybrid"
                    else:
                        merged[fts_id] = {
                            "id": fts_id,
                            "text": " | ".join(text_parts),
                            "score": fts_score,
                            "source": "fts",
                            "metadata": {"table": base_table},
                        }
            except Exception:
                logger.debug("FTS search on %s failed (table may not exist)", fts_table)

        # --- 3. Re-rank and return ---
        ranked = sorted(merged.values(), key=lambda r: r["score"], reverse=True)
        return ranked[:n_results]

    # ------------------------------------------------------------------
    # Question answering
    # ------------------------------------------------------------------

    def ask(
        self,
        question: str,
        context_docs: list[str] | None = None,
    ) -> dict[str, Any]:
        """Answer *question* using Qwen2.5:7b via Ollama with RAG context.

        If *context_docs* is ``None``, the engine runs ``search(question)`` to
        retrieve relevant context automatically.

        Returns
        -------
        dict
            ``{"answer": str, "citations": list[str], "model": str}``
        """
        if not self._ollama_available:
            raise RuntimeError("Ollama is not available -- cannot answer questions")

        # Auto-retrieve context when none supplied
        if context_docs is None:
            results = self.search(question, n_results=5)
            context_docs = [r["text"] for r in results if r.get("text")]

        # Build prompt with context
        context_block = ""
        if context_docs:
            numbered = "\n".join(
                f"[{i + 1}] {doc}" for i, doc in enumerate(context_docs)
            )
            context_block = (
                f"\n\n--- REFERENCE DOCUMENTS ---\n{numbered}\n--- END DOCUMENTS ---\n"
            )

        user_prompt = (
            f"Question: {question}{context_block}\n\n"
            "Provide a thorough answer. Cite specific documents by their [N] number "
            "and reference applicable Michigan rules or statutes."
        )

        resp = self._ollama_post(
            "/api/generate",
            {
                "model": self._config["llm_model"],
                "system": _SYSTEM_PROMPT,
                "prompt": user_prompt,
                "stream": False,
                "options": {"num_ctx": self._config["max_context_tokens"]},
            },
        )

        answer_text = resp.get("response", "")

        # Extract citation references like [1], [2] etc.
        import re

        citation_nums = sorted(set(int(m) for m in re.findall(r"\[(\d+)\]", answer_text)))
        citations = []
        for n in citation_nums:
            if context_docs and 1 <= n <= len(context_docs):
                citations.append(context_docs[n - 1][:200])

        return {
            "answer": answer_text,
            "citations": citations,
            "model": self._config["llm_model"],
        }

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def classify(self, text: str, categories: list[str]) -> dict[str, Any]:
        """Use the LLM to classify *text* into one of the given *categories*.

        Returns
        -------
        dict
            ``{"category": str, "confidence": str, "reasoning": str}``
        """
        if not self._ollama_available:
            raise RuntimeError("Ollama is not available -- cannot classify text")

        cats_str = ", ".join(f'"{c}"' for c in categories)
        prompt = (
            f"Classify the following text into exactly one of these categories: "
            f"[{cats_str}].\n\n"
            f'Text: """{text[:2000]}"""\n\n'
            f"Respond ONLY with valid JSON: "
            f'{{"category": "<chosen>", "confidence": "high|medium|low", '
            f'"reasoning": "<one sentence>"}}'
        )

        resp = self._ollama_post(
            "/api/generate",
            {
                "model": self._config["llm_model"],
                "system": _SYSTEM_PROMPT,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": self._config["max_context_tokens"]},
            },
        )

        raw = resp.get("response", "").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON classification: %s", raw[:200])
            return {"category": raw[:100], "confidence": "low", "reasoning": raw}

    # ------------------------------------------------------------------
    # Summarisation
    # ------------------------------------------------------------------

    def summarize(self, text: str, max_length: int = 500) -> str:
        """Summarise *text* to approximately *max_length* characters.

        Returns
        -------
        str
            The summary text.
        """
        if not self._ollama_available:
            raise RuntimeError("Ollama is not available -- cannot summarise text")

        prompt = (
            f"Summarize the following legal text in approximately {max_length} "
            f"characters. Preserve key legal terms, dates, and party names.\n\n"
            f'Text: """{text[:6000]}"""'
        )

        resp = self._ollama_post(
            "/api/generate",
            {
                "model": self._config["llm_model"],
                "system": _SYSTEM_PROMPT,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": self._config["max_context_tokens"]},
            },
        )

        return resp.get("response", "").strip()

    # ------------------------------------------------------------------
    # Bulk indexing
    # ------------------------------------------------------------------

    def index_collection(
        self,
        name: str,
        documents: list[dict[str, Any]],
    ) -> int:
        """Bulk-index *documents* into a named ChromaDB collection.

        Each document dict must have at least ``id`` and ``text`` keys.
        An optional ``metadata`` key is stored alongside the vector.

        Parameters
        ----------
        name : str
            ChromaDB collection name (e.g. ``"evidence"``, ``"court_rules"``).
        documents : list[dict]
            List of ``{"id": str, "text": str, "metadata": dict}`` dicts.

        Returns
        -------
        int
            Number of documents successfully indexed.
        """
        if self._chroma_client is None:
            raise RuntimeError("ChromaDB is not available -- cannot index collection")
        if not self._ollama_available:
            raise RuntimeError("Ollama is not available -- cannot generate embeddings")

        collection = self._chroma_client.get_or_create_collection(name)
        indexed = 0
        batch_size = 50

        for start in range(0, len(documents), batch_size):
            batch = documents[start : start + batch_size]
            ids: list[str] = []
            embeddings: list[list[float]] = []
            texts: list[str] = []
            metadatas: list[dict] = []

            for doc in batch:
                try:
                    text = doc["text"]
                    emb = self.embed_text(text)
                    ids.append(str(doc["id"]))
                    embeddings.append(emb)
                    texts.append(text)
                    metadatas.append(doc.get("metadata", {}))
                except Exception:
                    logger.warning("Failed to embed document %s", doc.get("id"))
                    continue

            if ids:
                collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                )
                indexed += len(ids)
                logger.info(
                    "Indexed %d/%d documents into collection '%s'",
                    indexed,
                    len(documents),
                    name,
                )

        return indexed
