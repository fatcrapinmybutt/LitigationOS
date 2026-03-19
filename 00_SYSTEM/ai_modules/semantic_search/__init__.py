"""LitigationOS Semantic Evidence Neural Search.

Local-only semantic search over litigation evidence.  Combines TF-IDF
(always available) or sentence-transformers (optional) embeddings with
FAISS (optional) or brute-force numpy cosine similarity to provide
fast, relevant evidence retrieval across all six case lanes.

Quick start::

    from semantic_search import SemanticSearchEngine, IngestPipeline

    # Build or load an index
    engine = SemanticSearchEngine()
    engine.ingest_document("exhibit_A1.pdf", text, {"lane": "A"})
    results = engine.search("motion to disqualify", lane="E", top_k=5)

    # Or ingest from the central database
    pipeline = IngestPipeline(engine=engine)
    pipeline.run(source="db", limit=500)
"""
from __future__ import annotations

from .ingest_pipeline import IngestPipeline
from .search_engine import SemanticSearchEngine

__all__ = ["SemanticSearchEngine", "IngestPipeline"]
__version__ = "1.0.0"
