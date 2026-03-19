"""Tests for embedding_manager.py and chunk_optimizer.py.

Comprehensive unit tests covering enums, dataclasses, caching,
TF-IDF hashing embedder, EmbeddingManager, ChunkOptimizer strategies,
legal-section splitting, and statistics computation.

100 % self-contained: no database, no file I/O, no network.
"""
from __future__ import annotations

import math
import pathlib
import struct
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

# ── Module under test ─────────────────────────────────────────────
from .. import embedding_manager as em
from .. import chunk_optimizer as co


# ===================================================================
# embedding_manager.py — Enums
# ===================================================================

class TestModelTypeEnum(unittest.TestCase):
    """ModelType enum values."""

    def test_sentence_transformer_value(self):
        self.assertEqual(em.ModelType.SENTENCE_TRANSFORMER.value, "sentence_transformer")

    def test_legal_bert_value(self):
        self.assertEqual(em.ModelType.LEGAL_BERT.value, "legal_bert")

    def test_ner_value(self):
        self.assertEqual(em.ModelType.NER.value, "ner")

    def test_enum_members_count(self):
        self.assertEqual(len(em.ModelType), 3)


class TestEmbeddingBackendEnum(unittest.TestCase):
    """EmbeddingBackend enum values."""

    def test_onnx_value(self):
        self.assertEqual(em.EmbeddingBackend.ONNX.value, "onnx")

    def test_sentence_transformers_value(self):
        self.assertEqual(em.EmbeddingBackend.SENTENCE_TRANSFORMERS.value, "sentence_transformers")

    def test_tfidf_hash_value(self):
        self.assertEqual(em.EmbeddingBackend.TFIDF_HASH.value, "tfidf_hash")

    def test_enum_members_count(self):
        self.assertEqual(len(em.EmbeddingBackend), 3)


# ===================================================================
# embedding_manager.py — ModelSpec dataclass
# ===================================================================

class TestModelSpec(unittest.TestCase):
    """ModelSpec dataclass creation and to_dict."""

    def _make_spec(self, **overrides):
        defaults = dict(
            name="test-model",
            dimensions=384,
            model_dir=pathlib.Path("/fake/models/test-model"),
            model_type="sentence_transformer",
            has_onnx=True,
            has_safetensors=False,
            max_seq_length=256,
            vocab_size=30522,
        )
        defaults.update(overrides)
        return em.ModelSpec(**defaults)

    def test_creation(self):
        spec = self._make_spec()
        self.assertEqual(spec.name, "test-model")
        self.assertEqual(spec.dimensions, 384)

    def test_to_dict_keys(self):
        d = self._make_spec().to_dict()
        expected_keys = {
            "name", "dimensions", "model_dir", "model_type",
            "has_onnx", "has_safetensors", "max_seq_length", "vocab_size",
        }
        self.assertEqual(set(d.keys()), expected_keys)

    def test_to_dict_model_dir_is_string(self):
        d = self._make_spec().to_dict()
        self.assertIsInstance(d["model_dir"], str)

    def test_config_raw_default_empty(self):
        spec = self._make_spec()
        self.assertEqual(spec.config_raw, {})

    def test_config_raw_custom(self):
        spec = self._make_spec(config_raw={"hidden_size": 384})
        self.assertEqual(spec.config_raw["hidden_size"], 384)


# ===================================================================
# embedding_manager.py — EmbeddingCache
# ===================================================================

class TestEmbeddingCache(unittest.TestCase):
    """EmbeddingCache with mocked SQLite connections."""

    @patch.object(em.EmbeddingCache, "_ensure_table")
    def _make_cache(self, mock_ensure, **kw):
        return em.EmbeddingCache(db_path="/fake/db.db", max_size=10, ttl_hours=24, **kw)

    def test_init_counters(self):
        cache = self._make_cache()
        self.assertEqual(cache._hits, 0)
        self.assertEqual(cache._misses, 0)
        self.assertEqual(cache._evictions, 0)

    @patch.object(em.EmbeddingCache, "_ensure_table")
    @patch.object(em.EmbeddingCache, "_connect")
    def test_get_miss(self, mock_conn_fn, mock_ensure):
        cache = em.EmbeddingCache(db_path="/fake/db.db", max_size=10, ttl_hours=24)
        conn = MagicMock()
        mock_conn_fn.return_value = conn
        conn.execute.return_value.fetchone.return_value = None
        result = cache.get("abc123")
        self.assertIsNone(result)
        self.assertEqual(cache._misses, 1)

    @patch.object(em.EmbeddingCache, "_ensure_table")
    @patch.object(em.EmbeddingCache, "_connect")
    def test_get_hit(self, mock_conn_fn, mock_ensure):
        cache = em.EmbeddingCache(db_path="/fake/db.db", max_size=10, ttl_hours=24)
        conn = MagicMock()
        mock_conn_fn.return_value = conn
        vec = [0.1, 0.2, 0.3]
        blob = struct.pack("<3f", *vec)
        row = {"embedding": blob, "dimensions": 3,
               "created_at": datetime.utcnow().isoformat()}
        conn.execute.return_value.fetchone.return_value = row
        result = cache.get("abc123")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result[0], 0.1, places=5)
        self.assertEqual(cache._hits, 1)

    @patch.object(em.EmbeddingCache, "_ensure_table")
    @patch.object(em.EmbeddingCache, "_connect")
    def test_get_expired_ttl(self, mock_conn_fn, mock_ensure):
        cache = em.EmbeddingCache(db_path="/fake/db.db", max_size=10, ttl_hours=1)
        conn = MagicMock()
        mock_conn_fn.return_value = conn
        old_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        row = {"embedding": struct.pack("<1f", 0.5), "dimensions": 1,
               "created_at": old_time}
        conn.execute.return_value.fetchone.return_value = row
        result = cache.get("abc123")
        self.assertIsNone(result)
        self.assertEqual(cache._misses, 1)

    @patch.object(em.EmbeddingCache, "_ensure_table")
    @patch.object(em.EmbeddingCache, "_connect")
    def test_put_calls_insert(self, mock_conn_fn, mock_ensure):
        cache = em.EmbeddingCache(db_path="/fake/db.db", max_size=100, ttl_hours=24)
        conn = MagicMock()
        mock_conn_fn.return_value = conn
        # _enforce_max_size expects count below max
        conn.execute.return_value.fetchone.return_value = {"cnt": 1}
        cache.put("hash1", [0.1, 0.2], "test_model")
        self.assertTrue(conn.execute.called)
        self.assertTrue(conn.commit.called)

    @patch.object(em.EmbeddingCache, "_ensure_table")
    @patch.object(em.EmbeddingCache, "_connect")
    def test_clear(self, mock_conn_fn, mock_ensure):
        cache = em.EmbeddingCache(db_path="/fake/db.db", max_size=10, ttl_hours=24)
        conn = MagicMock()
        mock_conn_fn.return_value = conn
        cursor = MagicMock()
        cursor.rowcount = 5
        conn.execute.return_value = cursor
        removed = cache.clear()
        self.assertEqual(removed, 5)

    @patch.object(em.EmbeddingCache, "_ensure_table")
    def test_stats_returns_dict(self, mock_ensure):
        cache = em.EmbeddingCache(db_path="/fake/db.db", max_size=10, ttl_hours=24)
        cache._hits = 5
        cache._misses = 3
        s = cache.stats()
        self.assertIn("hits", s)
        self.assertIn("misses", s)
        self.assertIn("hit_rate", s)
        self.assertAlmostEqual(s["hit_rate"], 5 / 8, places=3)

    @patch.object(em.EmbeddingCache, "_ensure_table")
    @patch.object(em.EmbeddingCache, "_connect")
    def test_eviction_triggered(self, mock_conn_fn, mock_ensure):
        cache = em.EmbeddingCache(db_path="/fake/db.db", max_size=5, ttl_hours=24)
        conn = MagicMock()
        mock_conn_fn.return_value = conn
        # Simulate count above max
        conn.execute.return_value.fetchone.return_value = {"cnt": 8}
        cache._enforce_max_size(conn)
        self.assertEqual(cache._evictions, 3)


# ===================================================================
# embedding_manager.py — _TfidfHashEmbedder
# ===================================================================

class TestTfidfHashEmbedder(unittest.TestCase):
    """_TfidfHashEmbedder deterministic embedding tests."""

    def setUp(self):
        self.emb = em._TfidfHashEmbedder(dim=128)

    def test_embed_returns_list_of_floats(self):
        vec = self.emb.embed("MCL 722.23 best interest factors")
        self.assertIsInstance(vec, list)
        self.assertEqual(len(vec), 128)
        for v in vec:
            self.assertIsInstance(v, float)

    def test_embed_correct_dimensionality(self):
        for dim in (64, 256, 512):
            e = em._TfidfHashEmbedder(dim=dim)
            vec = e.embed("legal test text")
            self.assertEqual(len(vec), dim)

    def test_l2_normalisation(self):
        vec = self.emb.embed("motion to compel discovery responses")
        magnitude = math.sqrt(sum(v * v for v in vec))
        self.assertAlmostEqual(magnitude, 1.0, places=5)

    def test_deterministic_same_input(self):
        v1 = self.emb.embed("MCR 2.003 disqualification")
        v2 = self.emb.embed("MCR 2.003 disqualification")
        self.assertEqual(v1, v2)

    def test_different_inputs_different_outputs(self):
        v1 = self.emb.embed("custody motion")
        v2 = self.emb.embed("eviction complaint housing discrimination")
        self.assertNotEqual(v1, v2)

    def test_empty_text_returns_zero_vector(self):
        vec = self.emb.embed("")
        self.assertEqual(vec, [0.0] * 128)

    def test_whitespace_only_text(self):
        vec = self.emb.embed("   \n\t  ")
        self.assertEqual(vec, [0.0] * 128)

    def test_embed_batch(self):
        texts = ["first text", "second text", "third text"]
        results = self.emb.embed_batch(texts)
        self.assertEqual(len(results), 3)
        for v in results:
            self.assertEqual(len(v), 128)

    def test_embed_batch_empty_list(self):
        results = self.emb.embed_batch([])
        self.assertEqual(results, [])

    def test_subword_ngrams(self):
        e = em._TfidfHashEmbedder(dim=64, subword=True)
        v1 = e.embed("test")
        e2 = em._TfidfHashEmbedder(dim=64, subword=False)
        v2 = e2.embed("test")
        # Subword should produce a different vector due to n-gram augmentation
        self.assertNotEqual(v1, v2)

    def test_get_stats(self):
        self.emb.embed("sample text")
        stats = self.emb.get_stats()
        self.assertEqual(stats["backend"], "tfidf_hash")
        self.assertEqual(stats["dimensions"], 128)
        self.assertGreater(stats["doc_count"], 0)
        self.assertGreater(stats["vocab_size"], 0)

    def test_idf_updates_on_multiple_embeds(self):
        e = em._TfidfHashEmbedder(dim=64)
        e.embed("alpha beta gamma")
        self.assertEqual(e._doc_count, 1)
        e.embed("delta epsilon zeta")
        self.assertEqual(e._doc_count, 2)


# ===================================================================
# embedding_manager.py — EmbeddingManager
# ===================================================================

class TestEmbeddingManager(unittest.TestCase):
    """EmbeddingManager with mocked file system and backends."""

    @patch.object(em.EmbeddingCache, "_ensure_table")
    @patch.object(em.EmbeddingManager, "discover_models", return_value=[])
    def _make_mgr(self, mock_discover, mock_ensure, **kw):
        return em.EmbeddingManager(
            models_dir="/fake/models",
            db_path="/fake/db.db",
            **kw,
        )

    def test_init_no_crash(self):
        mgr = self._make_mgr()
        self.assertIsNotNone(mgr)

    def test_discover_models_no_dir(self):
        mgr = self._make_mgr()
        # Re-call discover with a non-existent dir
        with patch.object(pathlib.Path, "is_dir", return_value=False):
            specs = mgr.discover_models()
        self.assertEqual(specs, [])

    @patch.object(em.EmbeddingCache, "_ensure_table")
    @patch.object(em.EmbeddingManager, "discover_models")
    def test_select_model_raises_when_empty(self, mock_discover, mock_ensure):
        mock_discover.return_value = []
        mgr = em.EmbeddingManager(models_dir="/fake/models", db_path="/fake/db.db")
        mgr._specs = {}
        with self.assertRaises(ValueError):
            mgr.select_model("semantic_search")

    @patch.object(em.EmbeddingCache, "_ensure_table")
    @patch.object(em.EmbeddingManager, "discover_models")
    def test_select_model_fallback_to_first(self, mock_discover, mock_ensure):
        mock_discover.return_value = []
        mgr = em.EmbeddingManager(models_dir="/fake/models", db_path="/fake/db.db")
        spec = em.ModelSpec(
            name="fallback-model", dimensions=384,
            model_dir=pathlib.Path("/fake"), model_type="sentence_transformer",
            has_onnx=False, has_safetensors=False, max_seq_length=256, vocab_size=0,
        )
        mgr._specs = {"fallback-model": spec}
        result = mgr.select_model("nonexistent_task")
        self.assertEqual(result.name, "fallback-model")

    def test_embed_text_empty(self):
        mgr = self._make_mgr()
        vec = mgr.embed_text("", model="default")
        self.assertTrue(all(v == 0.0 for v in vec))

    def test_embed_text_tfidf_fallback(self):
        mgr = self._make_mgr()
        vec = mgr.embed_text("MCL 722.23 custody factors", model="default", use_cache=False)
        self.assertEqual(len(vec), 300)  # default dim
        magnitude = math.sqrt(sum(v * v for v in vec))
        self.assertAlmostEqual(magnitude, 1.0, places=4)
        self.assertGreater(mgr._fallback_count, 0)

    def test_embed_batch_multiple(self):
        mgr = self._make_mgr()
        texts = ["MCL 722.23", "MCR 2.003", "MRE 702"]
        results = mgr.embed_batch(texts, model="default", use_cache=False)
        self.assertEqual(len(results), 3)
        for v in results:
            self.assertEqual(len(v), 300)

    def test_reduce_dimensions_empty(self):
        mgr = self._make_mgr()
        result = mgr.reduce_dimensions([], target_dim=50)
        self.assertEqual(result, [])

    def test_reduce_dimensions_no_reduction_needed(self):
        mgr = self._make_mgr()
        vectors = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        result = mgr.reduce_dimensions(vectors, target_dim=10)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 3)  # no reduction

    def test_reduce_dimensions_stdlib_pca(self):
        mgr = self._make_mgr()
        vectors = [[float(i + j) for j in range(10)] for i in range(5)]
        # Force stdlib path by temporarily disabling numpy
        original = em._HAS_NUMPY
        try:
            em._HAS_NUMPY = False
            result = mgr.reduce_dimensions(vectors, target_dim=3)
            self.assertEqual(len(result), 5)
            self.assertEqual(len(result[0]), 3)
        finally:
            em._HAS_NUMPY = original

    def test_get_stats_returns_dict(self):
        mgr = self._make_mgr()
        stats = mgr.get_stats()
        self.assertIn("models_discovered", stats)
        self.assertIn("backends_available", stats)
        self.assertIn("embed_count", stats)
        self.assertIn("cache", stats)

    def test_list_models_empty(self):
        mgr = self._make_mgr()
        self.assertEqual(mgr.list_models(), [])


# ===================================================================
# embedding_manager.py — helper functions
# ===================================================================

class TestEmbeddingHelpers(unittest.TestCase):
    """Test module-level helper functions."""

    def test_tokenize_removes_stop_words(self):
        tokens = em._tokenize("the court is in session for the hearing")
        self.assertNotIn("the", tokens)
        self.assertNotIn("is", tokens)
        self.assertNotIn("in", tokens)

    def test_tokenize_keeps_legal_terms(self):
        tokens = em._tokenize("MCL 722.23 custody disqualification")
        self.assertIn("mcl", tokens)
        self.assertIn("722.23", tokens)
        self.assertIn("custody", tokens)

    def test_text_hash_deterministic(self):
        h1 = em._text_hash("MCR 2.003(C)(1)")
        h2 = em._text_hash("MCR 2.003(C)(1)")
        self.assertEqual(h1, h2)

    def test_text_hash_normalises_whitespace(self):
        h1 = em._text_hash("  hello   world  ")
        h2 = em._text_hash("hello world")
        self.assertEqual(h1, h2)

    def test_cosine_similarity_identical(self):
        v = [0.5, 0.3, 0.1]
        self.assertAlmostEqual(em.cosine_similarity(v, v), 1.0, places=5)

    def test_cosine_similarity_orthogonal(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        self.assertAlmostEqual(em.cosine_similarity(a, b), 0.0, places=5)

    def test_cosine_similarity_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 1.0]
        self.assertAlmostEqual(em.cosine_similarity(a, b), 0.0, places=5)


# ===================================================================
# chunk_optimizer.py — Enums
# ===================================================================

class TestChunkingStrategyEnum(unittest.TestCase):
    """ChunkingStrategy enum values."""

    def test_fixed_size(self):
        self.assertEqual(co.ChunkingStrategy.FIXED_SIZE.value, "fixed_size")

    def test_sentence(self):
        self.assertEqual(co.ChunkingStrategy.SENTENCE.value, "sentence")

    def test_paragraph(self):
        self.assertEqual(co.ChunkingStrategy.PARAGRAPH.value, "paragraph")

    def test_semantic(self):
        self.assertEqual(co.ChunkingStrategy.SEMANTIC.value, "semantic")

    def test_legal_section(self):
        self.assertEqual(co.ChunkingStrategy.LEGAL_SECTION.value, "legal_section")

    def test_recursive(self):
        self.assertEqual(co.ChunkingStrategy.RECURSIVE.value, "recursive")

    def test_enum_count(self):
        self.assertEqual(len(co.ChunkingStrategy), 6)


# ===================================================================
# chunk_optimizer.py — ChunkConfig dataclass
# ===================================================================

class TestChunkConfig(unittest.TestCase):
    """ChunkConfig dataclass defaults and to_dict."""

    def test_defaults(self):
        cfg = co.ChunkConfig()
        self.assertEqual(cfg.strategy, co.ChunkingStrategy.RECURSIVE)
        self.assertEqual(cfg.chunk_size, 512)
        self.assertEqual(cfg.chunk_overlap, 64)
        self.assertEqual(cfg.min_chunk_size, 50)
        self.assertEqual(cfg.max_chunk_size, 1024)
        self.assertEqual(cfg.doc_type, "general")
        self.assertAlmostEqual(cfg.similarity_threshold, 0.5)

    def test_custom_values(self):
        cfg = co.ChunkConfig(
            strategy=co.ChunkingStrategy.LEGAL_SECTION,
            chunk_size=768,
            chunk_overlap=96,
        )
        self.assertEqual(cfg.chunk_size, 768)
        self.assertEqual(cfg.strategy, co.ChunkingStrategy.LEGAL_SECTION)

    def test_to_dict_keys(self):
        d = co.ChunkConfig().to_dict()
        expected = {
            "strategy", "chunk_size", "chunk_overlap", "min_chunk_size",
            "max_chunk_size", "separators", "preserve_metadata",
            "similarity_threshold", "doc_type",
        }
        self.assertEqual(set(d.keys()), expected)

    def test_to_dict_strategy_is_string(self):
        d = co.ChunkConfig().to_dict()
        self.assertEqual(d["strategy"], "recursive")


# ===================================================================
# chunk_optimizer.py — Chunk dataclass
# ===================================================================

class TestChunk(unittest.TestCase):
    """Chunk dataclass creation and to_dict."""

    def test_creation(self):
        c = co.Chunk(text="Hello world", chunk_id="abc123")
        self.assertEqual(c.text, "Hello world")
        self.assertEqual(c.chunk_id, "abc123")
        self.assertEqual(c.start_offset, 0)

    def test_to_dict_keys(self):
        c = co.Chunk(text="Test", chunk_id="id1")
        d = c.to_dict()
        expected = {
            "text", "chunk_id", "source_doc_id", "start_offset",
            "end_offset", "metadata", "token_count", "overlap_prev",
            "overlap_next",
        }
        self.assertEqual(set(d.keys()), expected)

    def test_metadata_default_empty(self):
        c = co.Chunk(text="Test", chunk_id="id1")
        self.assertEqual(c.metadata, {})


# ===================================================================
# chunk_optimizer.py — ChunkOptimizer
# ===================================================================

class TestChunkOptimizerFixedSize(unittest.TestCase):
    """ChunkOptimizer._fixed_size_split tests."""

    def setUp(self):
        self.opt = co.ChunkOptimizer()

    def test_normal_text(self):
        text = "Word " * 2000  # long enough for multiple chunks at default 512-token size
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(strategy=co.ChunkingStrategy.FIXED_SIZE),
        )
        self.assertGreaterEqual(len(chunks), 1)
        for c in chunks:
            self.assertIsInstance(c, co.Chunk)
            self.assertGreater(len(c.text), 0)

    def test_very_short_text(self):
        chunks = self.opt.chunk_text(
            "Short.", config=co.ChunkConfig(strategy=co.ChunkingStrategy.FIXED_SIZE),
        )
        self.assertEqual(len(chunks), 1)

    def test_empty_text_returns_empty(self):
        chunks = self.opt.chunk_text("", config=co.ChunkConfig(strategy=co.ChunkingStrategy.FIXED_SIZE))
        self.assertEqual(chunks, [])

    def test_overlap_present(self):
        text = "Sentence one. " * 2000
        cfg = co.ChunkConfig(
            strategy=co.ChunkingStrategy.FIXED_SIZE,
            chunk_size=50, chunk_overlap=10,
            min_chunk_size=1,
        )
        chunks = self.opt.chunk_text(text, config=cfg)
        self.assertGreater(len(chunks), 1)


class TestChunkOptimizerSentence(unittest.TestCase):
    """ChunkOptimizer._sentence_split tests."""

    def setUp(self):
        self.opt = co.ChunkOptimizer()

    def test_multiple_sentences(self):
        text = (
            "The court found a violation. The defendant objected. "
            "A motion was filed. Evidence was presented."
        )
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(strategy=co.ChunkingStrategy.SENTENCE),
        )
        self.assertGreater(len(chunks), 0)

    def test_single_sentence(self):
        text = "The court entered a ruling."
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(strategy=co.ChunkingStrategy.SENTENCE),
        )
        self.assertEqual(len(chunks), 1)


class TestChunkOptimizerParagraph(unittest.TestCase):
    """ChunkOptimizer._paragraph_split tests."""

    def setUp(self):
        self.opt = co.ChunkOptimizer()

    def test_paragraphs(self):
        text = "Paragraph one has some text.\n\nParagraph two is here.\n\nParagraph three."
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(strategy=co.ChunkingStrategy.PARAGRAPH),
        )
        self.assertGreater(len(chunks), 0)

    def test_no_paragraph_breaks(self):
        text = "This is a single continuous block of text without any paragraph breaks."
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(strategy=co.ChunkingStrategy.PARAGRAPH),
        )
        self.assertGreater(len(chunks), 0)


class TestChunkOptimizerLegalSection(unittest.TestCase):
    """ChunkOptimizer._legal_section_split — Michigan citation preservation."""

    def setUp(self):
        self.opt = co.ChunkOptimizer()

    def test_mcl_citation_not_split(self):
        text = (
            "I. STATEMENT OF FACTS\n"
            "Under MCL 722.23(3)(a), the court must consider best interest factors. "
            "This statute requires consideration of the emotional ties between parent "
            "and child as established by the testimony presented at the hearing.\n"
            "II. ARGUMENT\n"
            "The evidence clearly demonstrates a violation of MCL 722.23(3)(a) "
            "as the respondent failed to comply with the court order."
        )
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(strategy=co.ChunkingStrategy.LEGAL_SECTION),
        )
        for c in chunks:
            # MCL citation should not be split across chunks
            if "MCL" in c.text:
                self.assertIn("722.23", c.text)

    def test_mcr_reference_not_split(self):
        text = (
            "ARGUMENT\n"
            "Pursuant to MCR 2.003(C)(1), the judge must disqualify themselves. "
            "The standard under MCR 2.003(C)(1) is whether a reasonable person "
            "would question the judge's impartiality based on the record.\n"
            "CONCLUSION\n"
            "The motion should be granted based on MCR 2.003 requirements."
        )
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(strategy=co.ChunkingStrategy.LEGAL_SECTION),
        )
        for c in chunks:
            if "MCR" in c.text and "2.003" in c.text:
                # Ensure parenthetical stays with MCR
                self.assertTrue(
                    "MCR 2.003" in c.text,
                    f"MCR citation fragmented in chunk: {c.text[:100]}"
                )

    def test_section_headers_detected(self):
        text = (
            "I. INTRODUCTION\n"
            "The plaintiff brings this motion to compel. "
            "The court should grant this motion.\n"
            "II. FACTS\n"
            "On January 1, the defendant violated the order.\n"
            "A. Background\n"
            "The parties have a history of litigation.\n"
            "B. Current Dispute\n"
            "The current dispute concerns custody."
        )
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(strategy=co.ChunkingStrategy.LEGAL_SECTION),
        )
        self.assertGreater(len(chunks), 0)

    def test_court_section_headers(self):
        text = (
            "COMES NOW the Plaintiff and files this motion.\n"
            "Some introductory text here about the matter.\n"
            "WHEREFORE, Plaintiff requests the following relief.\n"
            "CERTIFICATE OF SERVICE\n"
            "I certify service was completed."
        )
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(strategy=co.ChunkingStrategy.LEGAL_SECTION),
        )
        self.assertGreater(len(chunks), 0)


class TestChunkOptimizerRecursive(unittest.TestCase):
    """ChunkOptimizer._recursive_split tests."""

    def setUp(self):
        self.opt = co.ChunkOptimizer()

    def test_recursive_split_basic(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(strategy=co.ChunkingStrategy.RECURSIVE),
        )
        self.assertGreater(len(chunks), 0)

    def test_recursive_split_long_text(self):
        text = ("Word " * 100 + "\n\n") * 10
        chunks = self.opt.chunk_text(
            text, config=co.ChunkConfig(
                strategy=co.ChunkingStrategy.RECURSIVE,
                chunk_size=100,
            ),
        )
        self.assertGreater(len(chunks), 1)


class TestChunkOptimizerLegalDocument(unittest.TestCase):
    """ChunkOptimizer.chunk_legal_document for different doc types."""

    def setUp(self):
        self.opt = co.ChunkOptimizer()
        self.text = (
            "INTRODUCTION\n"
            "This is a legal document with substantive content. "
            "The defendant violated multiple statutory provisions.\n\n"
            "ARGUMENT\n"
            "Under MCL 722.23, the court must weigh best interest factors. "
            "The evidence demonstrates a pattern of non-compliance.\n\n"
            "CONCLUSION\n"
            "For the foregoing reasons, the motion should be granted."
        )

    def test_motion(self):
        chunks = self.opt.chunk_legal_document(self.text, doc_type="motion")
        self.assertGreater(len(chunks), 0)

    def test_brief(self):
        chunks = self.opt.chunk_legal_document(self.text, doc_type="brief")
        self.assertGreater(len(chunks), 0)

    def test_complaint(self):
        chunks = self.opt.chunk_legal_document(self.text, doc_type="complaint")
        self.assertGreater(len(chunks), 0)

    def test_unknown_doc_type_falls_back(self):
        chunks = self.opt.chunk_legal_document(self.text, doc_type="nonexistent_type")
        self.assertGreater(len(chunks), 0)

    def test_metadata_propagated(self):
        chunks = self.opt.chunk_legal_document(
            self.text, doc_type="motion",
            metadata={"case_no": "2024-001507-DC"},
        )
        for c in chunks:
            self.assertIn("case_no", c.metadata)
            self.assertEqual(c.metadata["case_no"], "2024-001507-DC")


class TestChunkOptimizerAnalyze(unittest.TestCase):
    """ChunkOptimizer.analyze_chunks statistics computation."""

    def setUp(self):
        self.opt = co.ChunkOptimizer()

    def test_analyze_empty(self):
        stats = self.opt.analyze_chunks([])
        self.assertEqual(stats["count"], 0)

    def test_analyze_normal_chunks(self):
        chunks = [
            co.Chunk(text="Hello world", chunk_id="a", token_count=2,
                     start_offset=0, end_offset=11, metadata={"strategy": "recursive"}),
            co.Chunk(text="Another chunk", chunk_id="b", token_count=2,
                     start_offset=12, end_offset=25, metadata={"strategy": "recursive"}),
        ]
        stats = self.opt.analyze_chunks(chunks)
        self.assertEqual(stats["count"], 2)
        self.assertIn("char_sizes", stats)
        self.assertIn("token_sizes", stats)
        self.assertIn("total_chars", stats)
        self.assertEqual(stats["total_chars"], 11 + 13)
        self.assertIn("strategies_used", stats)

    def test_analyze_computes_overlap_stats(self):
        chunks = [
            co.Chunk(text="A", chunk_id="1", token_count=1, overlap_prev=0, overlap_next=5),
            co.Chunk(text="B", chunk_id="2", token_count=1, overlap_prev=5, overlap_next=0),
        ]
        stats = self.opt.analyze_chunks(chunks)
        self.assertIn("overlap_prev", stats)
        self.assertIn("overlap_next", stats)


class TestChunkOptimizerGetStats(unittest.TestCase):
    """ChunkOptimizer.get_stats returns valid dict."""

    def test_get_stats(self):
        opt = co.ChunkOptimizer()
        stats = opt.get_stats()
        self.assertIn("total_texts_processed", stats)
        self.assertIn("total_chunks_produced", stats)
        self.assertIn("strategy_counts", stats)
        self.assertIn("default_config", stats)
        self.assertEqual(stats["total_texts_processed"], 0)

    def test_get_stats_after_processing(self):
        opt = co.ChunkOptimizer()
        opt.chunk_text("Some test text for chunking purposes.", config=co.ChunkConfig())
        stats = opt.get_stats()
        self.assertGreater(stats["total_texts_processed"], 0)


# ===================================================================
# chunk_optimizer.py — helper functions
# ===================================================================

class TestChunkHelpers(unittest.TestCase):
    """Test chunk_optimizer helper functions."""

    def test_estimate_tokens(self):
        result = co._estimate_tokens("hello world test")
        self.assertEqual(result, 3)

    def test_estimate_tokens_empty(self):
        result = co._estimate_tokens("")
        self.assertEqual(result, 1)  # max(1, 0)

    def test_chars_for_tokens(self):
        result = co._chars_for_tokens(100)
        self.assertEqual(result, 550)  # 100 * 5.5

    def test_chunk_id_deterministic(self):
        id1 = co._chunk_id("text", "doc1", 0)
        id2 = co._chunk_id("text", "doc1", 0)
        self.assertEqual(id1, id2)

    def test_chunk_id_different_for_different_offsets(self):
        id1 = co._chunk_id("text", "doc1", 0)
        id2 = co._chunk_id("text", "doc1", 100)
        self.assertNotEqual(id1, id2)

    def test_is_inside_citation_mcl(self):
        text = "Under MCL 722.23(3)(a) the court must decide."
        # Position inside the MCL citation
        mcl_start = text.index("MCL")
        mcl_end = text.index("(a)") + 3
        mid_pos = (mcl_start + mcl_end) // 2
        self.assertTrue(co._is_inside_citation(text, mid_pos))

    def test_is_inside_citation_outside(self):
        text = "The court ruled. MCL 722.23 applies here."
        # Position at "The court"
        self.assertFalse(co._is_inside_citation(text, 5))

    def test_protect_restore_citations(self):
        text = "Under MCL 722.23 and MCR 2.003 the court ruled."
        protected, mapping = co._protect_citations(text)
        self.assertNotIn("MCL 722.23", protected)
        restored = co._restore_citations(protected, mapping)
        self.assertIn("MCL 722.23", restored)


if __name__ == "__main__":
    unittest.main()
