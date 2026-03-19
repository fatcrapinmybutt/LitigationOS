"""
THE MANBEARPIG — Semantic Intelligence Engine (EPOCH v4.0)
Latent Semantic Indexing (LSI) for meaning-based legal search.
Transforms 200K TF-IDF vectors into dense semantic space via TruncatedSVD.
"""
import os, sqlite3, pickle, json, time, hashlib
import numpy as np
from scipy.sparse import load_npz, vstack, issparse
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "model_data")
SEMANTIC_DIR = os.path.join(os.path.dirname(__file__), "model_data", "semantic")

class SemanticEngine:
    """LSI-based semantic search engine for legal documents."""
    
    def __init__(self, n_components=300):
        """Initialize. Load pre-computed semantic index if available, else compute."""
        self.n_components = n_components
        self.svd = None
        self.semantic_matrix = None  # Dense (n_docs, n_components)
        self.vectorizer = None
        self.doc_ids = []  # Parallel array: doc_ids[i] -> identifier for row i
        self.doc_texts = []  # Parallel array: original text snippets for context
        self._load_or_build()
    
    def _get_db(self):
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def _load_or_build(self):
        """Load pre-computed index or build from scratch."""
        os.makedirs(SEMANTIC_DIR, exist_ok=True)
        index_path = os.path.join(SEMANTIC_DIR, "lsi_index.npz")
        svd_path = os.path.join(SEMANTIC_DIR, "svd_model.pkl")
        meta_path = os.path.join(SEMANTIC_DIR, "doc_meta.json")
        vec_path = os.path.join(MODEL_DIR, "vectorizer.pkl")
        
        if all(os.path.exists(p) for p in [index_path, svd_path, meta_path, vec_path]):
            try:
                self.semantic_matrix = np.load(index_path)["matrix"]
                with open(svd_path, "rb") as f:
                    self.svd = pickle.load(f)
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    self.doc_ids = meta["doc_ids"]
                    self.doc_texts = meta.get("doc_texts", [])
                with open(vec_path, "rb") as f:
                    self.vectorizer = pickle.load(f)
                print(f"[MANBEARPIG-LSI] Loaded semantic index: {self.semantic_matrix.shape}")
                return
            except Exception as e:
                print(f"[MANBEARPIG-LSI] Load failed, rebuilding: {e}")
        
        self.build_index()
    
    def build_index(self, max_evidence=50000, max_authority=10000):
        """Build the LSI semantic index from DB data.
        
        Sources: evidence_quotes (most important), auth_rules, md_sections, 
        judicial_violations, impeachment_items.
        """
        print("[MANBEARPIG-LSI] Building semantic index...")
        start = time.time()
        
        # Load vectorizer
        vec_path = os.path.join(MODEL_DIR, "vectorizer.pkl")
        if os.path.exists(vec_path):
            with open(vec_path, "rb") as f:
                self.vectorizer = pickle.load(f)
        else:
            raise FileNotFoundError(f"Vectorizer not found at {vec_path}")
        
        db = self._get_db()
        texts = []
        ids = []
        snippets = []
        
        # 1. Evidence quotes (highest priority)
        print("[MANBEARPIG-LSI] Loading evidence_quotes...")
        rows = db.execute(f"SELECT id, quote_text, speaker, evidence_category FROM evidence_quotes LIMIT {max_evidence}").fetchall()
        for r in rows:
            text = r["quote_text"] or ""
            if len(text) > 20:  # Skip very short
                texts.append(text)
                ids.append(f"evidence:{r['id']}")
                snippets.append(text[:200])
        print(f"  Loaded {len(texts)} evidence quotes")
        
        # 2. Auth rules
        print("[MANBEARPIG-LSI] Loading auth_rules...")
        rows = db.execute(f"SELECT id, rule_number, title, full_text FROM auth_rules LIMIT {max_authority}").fetchall()
        for r in rows:
            text = f"{r['rule_number']} {r['title']} {r['full_text'] or ''}"
            if len(text) > 20:
                texts.append(text)
                ids.append(f"rule:{r['rule_number']}")
                snippets.append(text[:200])
        print(f"  Total after rules: {len(texts)}")
        
        # 3. Judicial violations
        print("[MANBEARPIG-LSI] Loading judicial_violations...")
        rows = db.execute("SELECT violation_id, violation_description, canon_text, severity FROM judicial_violations").fetchall()
        for r in rows:
            text = f"{r['violation_description'] or ''} {r['canon_text'] or ''}"
            if len(text) > 20:
                texts.append(text)
                ids.append(f"violation:{r['violation_id']}")
                snippets.append(text[:200])
        
        # 4. Impeachment items
        print("[MANBEARPIG-LSI] Loading impeachment_items...")
        rows = db.execute("SELECT id, statement, contradicting_text, legal_hook FROM impeachment_items LIMIT 15000").fetchall()
        for r in rows:
            text = f"{r['statement'] or ''} {r['contradicting_text'] or ''} {r['legal_hook'] or ''}"
            if len(text) > 20:
                texts.append(text)
                ids.append(f"impeachment:{r['id']}")
                snippets.append(text[:200])
        
        # 5. Forensic findings
        print("[MANBEARPIG-LSI] Loading forensic_findings...")
        rows = db.execute("SELECT id, source, finding_type, severity, actor, description, evidence_text, legal_hook FROM forensic_findings LIMIT 10000").fetchall()
        for r in rows:
            text = f"{r['description'] or ''} {r['evidence_text'] or ''} {r['legal_hook'] or ''} {r['finding_type'] or ''}"
            if len(text) > 20:
                texts.append(text)
                ids.append(f"forensic:{r['id']}")
                snippets.append(text[:200])
        
        db.close()
        
        print(f"[MANBEARPIG-LSI] Total documents: {len(texts)}")
        
        # TF-IDF transform
        print("[MANBEARPIG-LSI] Computing TF-IDF vectors...")
        tfidf_matrix = self.vectorizer.transform(texts)
        
        # Truncated SVD (LSI)
        n_comp = min(self.n_components, tfidf_matrix.shape[0] - 1, tfidf_matrix.shape[1] - 1)
        print(f"[MANBEARPIG-LSI] Computing SVD with {n_comp} components...")
        self.svd = TruncatedSVD(n_components=n_comp, random_state=42, algorithm='randomized')
        self.semantic_matrix = self.svd.fit_transform(tfidf_matrix)
        self.semantic_matrix = normalize(self.semantic_matrix)  # L2 normalize for cosine
        
        self.doc_ids = ids
        self.doc_texts = snippets
        
        explained = self.svd.explained_variance_ratio_.sum()
        print(f"[MANBEARPIG-LSI] Explained variance: {explained:.4f}")
        
        # Save
        np.savez_compressed(os.path.join(SEMANTIC_DIR, "lsi_index.npz"), matrix=self.semantic_matrix)
        with open(os.path.join(SEMANTIC_DIR, "svd_model.pkl"), "wb") as f:
            pickle.dump(self.svd, f)
        with open(os.path.join(SEMANTIC_DIR, "doc_meta.json"), "w") as f:
            json.dump({"doc_ids": ids, "doc_texts": snippets}, f)
        
        elapsed = time.time() - start
        print(f"[MANBEARPIG-LSI] Index built in {elapsed:.1f}s: {self.semantic_matrix.shape}")
        return {"documents": len(texts), "components": n_comp, "explained_variance": round(explained, 4), "elapsed_seconds": round(elapsed, 1)}
    
    def search(self, query: str, top_k: int = 20, doc_type: str = None) -> list:
        """Semantic search: find documents most similar in meaning to query.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            doc_type: Optional filter ('evidence', 'rule', 'violation', 'impeachment', 'forensic')
        
        Returns: List of {id, score, snippet, doc_type}
        """
        if self.semantic_matrix is None or self.vectorizer is None:
            return []
        
        # Transform query to semantic space
        q_tfidf = self.vectorizer.transform([query])
        q_semantic = self.svd.transform(q_tfidf)
        q_semantic = normalize(q_semantic)
        
        # Cosine similarity against all documents
        scores = cosine_similarity(q_semantic, self.semantic_matrix)[0]
        
        # Apply doc_type filter if specified
        if doc_type:
            mask = np.array([did.startswith(doc_type + ":") for did in self.doc_ids])
            scores = scores * mask
        
        # Top-K
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] < 0.01:
                break
            results.append({
                "id": self.doc_ids[idx],
                "score": round(float(scores[idx]), 4),
                "snippet": self.doc_texts[idx] if idx < len(self.doc_texts) else "",
                "doc_type": self.doc_ids[idx].split(":")[0]
            })
        return results
    
    def find_similar(self, doc_id: str, top_k: int = 10) -> list:
        """Find documents most similar to a given document by ID."""
        if doc_id not in self.doc_ids:
            return []
        idx = self.doc_ids.index(doc_id)
        doc_vec = self.semantic_matrix[idx:idx+1]
        scores = cosine_similarity(doc_vec, self.semantic_matrix)[0]
        scores[idx] = -1  # Exclude self
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for i in top_indices:
            if scores[i] < 0.01:
                break
            results.append({
                "id": self.doc_ids[i],
                "score": round(float(scores[i]), 4),
                "snippet": self.doc_texts[i] if i < len(self.doc_texts) else "",
                "doc_type": self.doc_ids[i].split(":")[0]
            })
        return results
    
    def cluster_evidence(self, n_clusters: int = 12) -> dict:
        """K-Means clustering on the semantic matrix to find evidence themes."""
        from sklearn.cluster import KMeans
        if self.semantic_matrix is None:
            return {}
        
        # Only cluster evidence docs
        evidence_mask = [i for i, did in enumerate(self.doc_ids) if did.startswith("evidence:")]
        if len(evidence_mask) < n_clusters:
            return {"error": "Not enough evidence documents"}
        
        evidence_matrix = self.semantic_matrix[evidence_mask]
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(evidence_matrix)
        
        clusters = {}
        for i, label in enumerate(labels):
            label_str = f"cluster_{label}"
            if label_str not in clusters:
                clusters[label_str] = {"count": 0, "samples": [], "doc_ids": []}
            clusters[label_str]["count"] += 1
            clusters[label_str]["doc_ids"].append(self.doc_ids[evidence_mask[i]])
            if len(clusters[label_str]["samples"]) < 3:
                clusters[label_str]["samples"].append(self.doc_texts[evidence_mask[i]] if evidence_mask[i] < len(self.doc_texts) else "")
        
        return {"n_clusters": n_clusters, "total_evidence": len(evidence_mask), "clusters": clusters}
    
    def find_semantic_gaps(self, legal_grounds: list) -> dict:
        """For each legal ground, check if we have sufficient semantic evidence coverage.
        
        Args:
            legal_grounds: List of legal topics (e.g., ['ex parte', 'due process', 'alienation'])
        
        Returns: Dict mapping ground -> {evidence_count, avg_score, strongest, weakest, gap_score}
        """
        gaps = {}
        for ground in legal_grounds:
            results = self.search(ground, top_k=50, doc_type="evidence")
            if not results:
                gaps[ground] = {"evidence_count": 0, "avg_score": 0, "gap_score": 1.0, "assessment": "CRITICAL GAP"}
                continue
            
            scores = [r["score"] for r in results]
            avg = np.mean(scores)
            gap_score = max(0, 1.0 - (len(results) / 50) * avg)
            
            assessment = "STRONG" if gap_score < 0.3 else "ADEQUATE" if gap_score < 0.6 else "WEAK" if gap_score < 0.8 else "CRITICAL GAP"
            
            gaps[ground] = {
                "evidence_count": len(results),
                "avg_score": round(avg, 4),
                "strongest": results[0] if results else None,
                "gap_score": round(gap_score, 4),
                "assessment": assessment
            }
        return gaps
    
    def status(self) -> dict:
        """Return engine status."""
        return {
            "engine": "MANBEARPIG-LSI",
            "loaded": self.semantic_matrix is not None,
            "documents": self.semantic_matrix.shape[0] if self.semantic_matrix is not None else 0,
            "components": self.semantic_matrix.shape[1] if self.semantic_matrix is not None else 0,
            "explained_variance": round(float(self.svd.explained_variance_ratio_.sum()), 4) if self.svd else 0,
            "index_path": SEMANTIC_DIR,
            "doc_types": dict(sorted(
                {t: sum(1 for d in self.doc_ids if d.startswith(t + ":")) for t in set(d.split(":")[0] for d in self.doc_ids)}.items(),
                key=lambda x: -x[1]
            )) if self.doc_ids else {}
        }

def self_test():
    """Self-test: build index, run searches, verify quality."""
    results = {"tests": [], "status": "pass"}
    try:
        engine = SemanticEngine(n_components=100)  # Use smaller for test
        
        # Test 1: Index loaded
        s = engine.status()
        results["tests"].append({"name": "index_loaded", "pass": s["loaded"], "docs": s["documents"]})
        
        # Test 2: Search works
        hits = engine.search("ex parte communication with judge", top_k=5)
        results["tests"].append({"name": "search_ex_parte", "pass": len(hits) > 0, "hits": len(hits)})
        
        # Test 3: Type filter works
        evidence_hits = engine.search("custody violation", top_k=5, doc_type="evidence")
        results["tests"].append({"name": "type_filter", "pass": all(h["doc_type"] == "evidence" for h in evidence_hits), "hits": len(evidence_hits)})
        
        # Test 4: Gap analysis
        gaps = engine.find_semantic_gaps(["due process", "ex parte", "alienation"])
        results["tests"].append({"name": "gap_analysis", "pass": len(gaps) == 3, "gaps": {k: v["assessment"] for k, v in gaps.items()}})
        
        # Test 5: Clustering
        clusters = engine.cluster_evidence(n_clusters=5)
        results["tests"].append({"name": "clustering", "pass": "clusters" in clusters, "n_clusters": clusters.get("n_clusters", 0)})
        
        results["status"] = "pass" if all(t["pass"] for t in results["tests"]) else "partial"
    except Exception as e:
        results["status"] = "fail"
        results["error"] = str(e)
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "build":
            engine = SemanticEngine()
            print(json.dumps(engine.build_index(), indent=2))
        elif cmd == "search":
            engine = SemanticEngine()
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "ex parte communication"
            results = engine.search(query, top_k=10)
            print(json.dumps(results, indent=2))
        elif cmd == "status":
            engine = SemanticEngine()
            print(json.dumps(engine.status(), indent=2))
        elif cmd == "gaps":
            engine = SemanticEngine()
            grounds = sys.argv[2:] if len(sys.argv) > 2 else ["due process", "ex parte", "alienation", "custody", "parenting time"]
            print(json.dumps(engine.find_semantic_gaps(grounds), indent=2))
        elif cmd == "cluster":
            engine = SemanticEngine()
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
            print(json.dumps(engine.cluster_evidence(n), indent=2, default=str))
        elif cmd == "self-test":
            print(json.dumps(self_test(), indent=2))
        else:
            print("Commands: build, search <query>, status, gaps <ground1> <ground2>, cluster <n>, self-test")
    else:
        # Default: build index and show status
        engine = SemanticEngine()
        print(json.dumps(engine.status(), indent=2))
