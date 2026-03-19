#!/usr/bin/env python3
"""
LEXOS BIBLE — lexos_server.py
50 specialized micro-AI brains accessed as a local Python library.
Usage: from lexos_server import LexosLibrary; lib = LexosLibrary()
"""
import os, sys, re, json, hashlib, math, time, threading, traceback, signal
from collections import Counter, defaultdict
from datetime import datetime, timezone

sys.path.insert(0, "D:/TEMP")
sys.path.insert(0, "D:/TEMP/pylibs")

BASE_DIR = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
CONFIG_PATH = os.path.join(BASE_DIR, "lexos_config.json").replace("\\", "/")
INDEX_PATH = os.path.join(BASE_DIR, "lexos_index.json").replace("\\", "/")
BRAINS_DIR = os.path.join(BASE_DIR, "brains").replace("\\", "/")

VERSION = "1.0.0"

# ════════════════════════════════════════════════════════════════════════
#  Configuration
# ════════════════════════════════════════════════════════════════════════

def load_config():
    defaults = {
        "brains_dir": BRAINS_DIR,
        "query_timeout_sec": 30,
        "health_check_interval_sec": 60,
        "top_k_default": 5,
        "confidence_threshold": 0.3,
        "llm_backend": "local",
        "llm_fallback": "local",
        "convergence_threshold": 0.01,
        "self_repair_on_load": True,
    }
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8", errors="replace") as f:
                defaults.update(json.load(f))
        except Exception:
            pass
    return defaults

# ════════════════════════════════════════════════════════════════════════
#  LexosBrain — single specialized micro-AI brain
# ════════════════════════════════════════════════════════════════════════

class LexosBrain:
    """One of 50 specialized knowledge nuclei with TF-IDF query capability."""

    def __init__(self, brain_id, name, domain, nucleus_path):
        self.brain_id = brain_id
        self.name = name
        self.domain = domain
        self.nucleus_path = nucleus_path
        self.nucleus = {}
        self.entries = []
        self.index = {}           # token -> [entry_indices]
        self.idf = {}             # token -> idf score
        self.query_count = 0
        self.error_count = 0
        self.last_query = None
        self.last_query_time = None
        self.health = "GREEN"
        self.health_detail = ""
        self.confidence_threshold = 0.3
        self.loaded = False
        self.load_time = None
        self.entry_count = 0
        self.nucleus_size_kb = 0
        self._lock = threading.Lock()
        self._delta_log = []      # enrichment deltas

    def load(self):
        """Load nucleus JSON and build inverted TF-IDF index."""
        try:
            if not os.path.isfile(self.nucleus_path):
                self.health = "RED"
                self.health_detail = "Nucleus file not found"
                self.loaded = False
                return False
            with open(self.nucleus_path, "r", encoding="utf-8", errors="replace") as f:
                self.nucleus = json.load(f)
            self.entries = self.nucleus.get("entries", [])
            self.entry_count = len(self.entries)
            self.nucleus_size_kb = self.nucleus.get("nucleus_size_kb", 0)
            raw_index = self.nucleus.get("index", {})
            self.index = {k: v for k, v in raw_index.items() if isinstance(v, list)}
            self._build_idf()
            self.loaded = True
            self.load_time = time.time()
            self.health = "GREEN" if self.entry_count > 0 else "YELLOW"
            self.health_detail = f"{self.entry_count} entries loaded"
            return True
        except Exception as e:
            self.health = "RED"
            self.health_detail = f"Load error: {e}"
            self.error_count += 1
            return False

    def _build_idf(self):
        """Compute IDF scores from the inverted index."""
        n = max(len(self.entries), 1)
        self.idf = {}
        for token, postings in self.index.items():
            df = len(postings)
            self.idf[token] = math.log((n + 1) / (df + 1)) + 1.0

    def _tokenize(self, text):
        return re.findall(r"[a-z0-9]+(?:\.[a-z0-9]+)*", text.lower())

    def query(self, question, top_k=5):
        """TF-IDF similarity search against nucleus entries."""
        with self._lock:
            self.query_count += 1
            self.last_query = question
            self.last_query_time = time.time()

        if not self.loaded or not self.entries:
            return {"brain": self.brain_id, "results": [], "confidence": 0, "note": "Brain not loaded or empty"}

        try:
            q_tokens = self._tokenize(question)
            if not q_tokens:
                return {"brain": self.brain_id, "results": [], "confidence": 0, "note": "Empty query after tokenization"}

            # Compute query TF vector
            q_tf = Counter(q_tokens)
            q_max = max(q_tf.values())
            q_vec = {}
            for tok, cnt in q_tf.items():
                tf = 0.5 + 0.5 * (cnt / q_max)
                idf = self.idf.get(tok, 1.0)
                q_vec[tok] = tf * idf

            # Score each candidate entry (only those with at least one matching token)
            candidate_indices = set()
            for tok in q_tokens:
                if tok in self.index:
                    candidate_indices.update(self.index[tok])

            scored = []
            for idx in candidate_indices:
                if idx >= len(self.entries):
                    continue
                entry = self.entries[idx]
                e_tokens = self._tokenize(entry.get("text", ""))
                e_tf = Counter(e_tokens)
                e_max = max(e_tf.values()) if e_tf else 1

                dot = 0.0
                e_norm_sq = 0.0
                for tok, cnt in e_tf.items():
                    tf = 0.5 + 0.5 * (cnt / e_max)
                    idf = self.idf.get(tok, 1.0)
                    w = tf * idf
                    e_norm_sq += w * w
                    if tok in q_vec:
                        dot += q_vec[tok] * w

                q_norm = math.sqrt(sum(v * v for v in q_vec.values()))
                e_norm = math.sqrt(e_norm_sq) if e_norm_sq > 0 else 1.0
                sim = dot / (q_norm * e_norm) if (q_norm * e_norm) > 0 else 0.0

                # Boost by entry's pre-computed score
                entry_score_boost = entry.get("score", 0) * 0.1
                final = sim + entry_score_boost

                scored.append((final, idx, entry))

            scored.sort(key=lambda x: x[0], reverse=True)
            top = scored[:top_k]

            results = []
            for score, idx, entry in top:
                results.append({
                    "entry_id": entry.get("id", f"e{idx}"),
                    "text": entry.get("text", ""),
                    "confidence": round(score, 4),
                    "citations": entry.get("citations", []),
                    "tags": entry.get("tags", []),
                    "source": entry.get("source", ""),
                })

            overall = results[0]["confidence"] if results else 0.0
            return {
                "brain": self.brain_id,
                "name": self.name,
                "results": results,
                "confidence": round(overall, 4),
                "entries_searched": len(candidate_indices),
                "total_entries": self.entry_count,
            }
        except Exception as e:
            self.error_count += 1
            self.health = "YELLOW"
            self.health_detail = f"Query error: {e}"
            return {"brain": self.brain_id, "results": [], "confidence": 0, "error": str(e)}

    def deep_reason(self, question, context=None):
        """Route to Gemini/Ollama for deep reasoning (stub — returns guidance)."""
        local = self.query(question, top_k=3)
        return {
            "brain": self.brain_id,
            "mode": "deep_reason",
            "local_context": local.get("results", []),
            "guidance": (
                f"Deep reasoning requested for brain '{self.name}'. "
                f"Top {len(local.get('results', []))} nucleus entries provided as context. "
                "Route to configured LLM backend for synthesis."
            ),
            "llm_prompt_hint": f"Given the following legal knowledge from the {self.name} domain:\n"
                + "\n".join(r["text"][:200] for r in local.get("results", []))
                + f"\n\nAnswer: {question}",
        }

    def enrich(self, new_data):
        """Add new knowledge entries to the nucleus and rebuild index."""
        with self._lock:
            added = 0
            existing_hashes = {hashlib.sha1(e["text"].encode("utf-8", errors="replace")).hexdigest()[:12]
                               for e in self.entries}
            for item in (new_data if isinstance(new_data, list) else [new_data]):
                text = item if isinstance(item, str) else item.get("text", "")
                h = hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:12]
                if h in existing_hashes:
                    continue
                new_entry = {
                    "id": f"e{self.entry_count + added + 1:04d}",
                    "text": text,
                    "score": 0.5,
                    "source": "enrichment",
                    "citations": [],
                    "tags": ["enriched"],
                }
                self.entries.append(new_entry)
                existing_hashes.add(h)
                added += 1

            if added > 0:
                self.entry_count = len(self.entries)
                self.nucleus["entries"] = self.entries
                self.nucleus["entry_count"] = self.entry_count
                # Rebuild index
                new_index = defaultdict(list)
                for i, entry in enumerate(self.entries):
                    for tok in set(self._tokenize(entry.get("text", ""))):
                        new_index[tok].append(i)
                self.index = dict(new_index)
                self.nucleus["index"] = self.index
                self._build_idf()
                # Persist
                try:
                    with open(self.nucleus_path, "w", encoding="utf-8") as f:
                        json.dump(self.nucleus, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass
                self._delta_log.append({
                    "time": datetime.now(timezone.utc).isoformat(),
                    "added": added,
                    "new_total": self.entry_count,
                })

            return {"brain": self.brain_id, "added": added, "total": self.entry_count}

    def health_check(self):
        """Verify nucleus integrity and index freshness."""
        issues = []
        if not self.loaded:
            issues.append("not_loaded")
        if not os.path.isfile(self.nucleus_path):
            issues.append("file_missing")
        if self.entry_count == 0:
            issues.append("empty_nucleus")
        if self.error_count > 10:
            issues.append("high_error_rate")
        idx_tokens = len(self.index)
        if self.entry_count > 0 and idx_tokens == 0:
            issues.append("index_empty")

        if not issues:
            self.health = "GREEN"
            self.health_detail = "All checks passed"
        elif "not_loaded" in issues or "file_missing" in issues:
            self.health = "RED"
            self.health_detail = "; ".join(issues)
        else:
            self.health = "YELLOW"
            self.health_detail = "; ".join(issues)

        return {
            "brain": self.brain_id,
            "health": self.health,
            "detail": self.health_detail,
            "issues": issues,
            "entry_count": self.entry_count,
            "index_tokens": idx_tokens,
            "error_count": self.error_count,
            "query_count": self.query_count,
        }

    def self_repair(self):
        """Rebuild index if corrupted; reload nucleus if needed."""
        repaired = []
        if not self.loaded:
            if self.load():
                repaired.append("reloaded_nucleus")
        if self.loaded and self.entry_count > 0 and len(self.index) == 0:
            new_index = defaultdict(list)
            for i, entry in enumerate(self.entries):
                for tok in set(self._tokenize(entry.get("text", ""))):
                    new_index[tok].append(i)
            self.index = dict(new_index)
            self._build_idf()
            repaired.append("rebuilt_index")
        self.health_check()
        return {"brain": self.brain_id, "repaired": repaired, "health": self.health}

    def metadata(self):
        return {
            "brain_id": self.brain_id,
            "name": self.name,
            "domain": self.domain,
            "entry_count": self.entry_count,
            "nucleus_size_kb": self.nucleus_size_kb,
            "query_count": self.query_count,
            "error_count": self.error_count,
            "health": self.health,
            "health_detail": self.health_detail,
            "last_query": self.last_query,
            "loaded": self.loaded,
        }

    def sample(self, n=3):
        """Return a sample of top-scored entries."""
        top = sorted(self.entries, key=lambda e: e.get("score", 0), reverse=True)[:n]
        return [{"id": e.get("id"), "text": e.get("text", "")[:300], "score": e.get("score", 0)} for e in top]





# ════════════════════════════════════════════════════════════════════════
#  LexosLibrary — brain loader (NO HTTP SERVER)
# ════════════════════════════════════════════════════════════════════════

class LexosLibrary:
    """LEXOS BIBLE library — loads 50 specialized micro-AI brains.
    NO server, NO HTTP, NO ports. Direct Python access only."""

    def __init__(self, config=None):
        self.config = config or load_config()
        self.brains = {}
        self.start_time = time.time()
        self.total_queries = 0
        self._load_all_brains()

    def _load_all_brains(self):
        """Load all brain nucleus files from the brains directory."""
        brains_dir = self.config.get("brains_dir", BRAINS_DIR)
        index_path = INDEX_PATH

        brain_meta = {}
        if os.path.isfile(index_path):
            try:
                with open(index_path, "r", encoding="utf-8", errors="replace") as f:
                    idx = json.load(f)
                for b in idx.get("brains", []):
                    brain_meta[b["id"]] = (b["name"], b["domain"])
            except Exception:
                pass

        if not os.path.isdir(brains_dir):
            os.makedirs(brains_dir, exist_ok=True)

        loaded = 0
        for fname in sorted(os.listdir(brains_dir)):
            if not fname.startswith("brain_") or not fname.endswith(".json"):
                continue
            fpath = os.path.join(brains_dir, fname).replace("\\", "/")
            parts = fname.replace(".json", "").split("_", 1)
            if len(parts) < 2:
                continue
            brain_id = parts[1]
            name, domain = brain_meta.get(brain_id, (brain_id, "unknown"))
            brain = LexosBrain(brain_id, name, domain, fpath)
            if brain.load():
                loaded += 1
            if self.config.get("self_repair_on_load") and brain.health != "GREEN":
                brain.self_repair()
            self.brains[brain_id] = brain

        print(f"[LEXOS] Loaded {loaded}/{len(self.brains)} brains from {brains_dir}")

    def ask(self, brain_id, question):
        """Query a specific brain directly. No network involved."""
        brain = self.brains.get(brain_id)
        if not brain:
            return {"error": f"Brain '{brain_id}' not found"}
        return brain.ask(question)


# Keep old class name as alias for backward compatibility (but no HTTP)
LexosServer = LexosLibrary


# ════════════════════════════════════════════════════════════════════════
#  Main entry point — NO SERVER
# ════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  LEXOS BIBLE — 50 Specialized Micro-AI Brains")
    print("  HTTP server PERMANENTLY REMOVED — library mode only")
    print(f"  Version: {VERSION}")
    print("=" * 70)
    print("[LEXOS] Usage:")
    print("  from lexos_server import LexosLibrary")
    print("  lib = LexosLibrary()")
    print("  result = lib.ask('01_mcl', 'What is MCL 722.23?')")
    sys.exit(0)


if __name__ == "__main__":
    main()
