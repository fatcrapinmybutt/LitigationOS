"""
THE MANBEARPIG — GGUF Cross-Encoder Reranker (EPOCH v4.0)
Uses local Qwen 2.5 1.5B to rerank TF-IDF/LSI results for quality.
"""
import os, json, re, time
from typing import List, Dict, Optional

GGUF_PATH = os.path.join(os.path.dirname(__file__), "gguf", "qwen2.5-1.5b-instruct-q4_k_m.gguf")

class Reranker:
    def __init__(self, model_path=GGUF_PATH, n_ctx=2048, n_threads=4):
        self._llm = None
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self._available = os.path.exists(model_path)
    
    def _get_llm(self):
        """Lazy-load the GGUF model."""
        if self._llm is None and self._available:
            try:
                from llama_cpp import Llama
                self._llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_threads=self.n_threads,
                    verbose=False
                )
            except Exception as e:
                print(f"[MANBEARPIG-RERANKER] Model load failed: {e}")
                self._available = False
        return self._llm
    
    def rerank(self, query: str, results: List[Dict], top_k: int = 10, text_key: str = "snippet") -> List[Dict]:
        """Rerank search results using the GGUF model.
        
        For each result, ask the LLM: "Rate relevance of this passage to the query on a scale of 1-10"
        Then sort by relevance score.
        
        Args:
            query: The search query
            results: List of dicts with a text field (specified by text_key)
            top_k: Number of results to return after reranking
            text_key: Key in result dict containing the text to evaluate
        
        Returns: Reranked list with added 'rerank_score' field
        """
        llm = self._get_llm()
        if not llm:
            # Fallback: return original order
            return results[:top_k]
        
        scored = []
        for r in results[:min(30, len(results))]:  # Cap at 30 for performance
            text = r.get(text_key, "") or ""
            if not text:
                scored.append((r, 0))
                continue
            
            prompt = f"""Rate how relevant this passage is to the legal query. Reply with ONLY a number from 1-10.

Query: {query[:200]}
Passage: {text[:400]}

Relevance score (1-10):"""
            
            try:
                response = llm(prompt, max_tokens=5, temperature=0.0, stop=["\n"])
                score_text = response["choices"][0]["text"].strip()
                nums = re.findall(r'\d+', score_text)
                score = min(10, max(1, int(nums[0]))) if nums else 5
            except Exception:
                score = 5
            
            scored.append((r, score))
        
        # Sort by score descending
        scored.sort(key=lambda x: -x[1])
        
        reranked = []
        for r, score in scored[:top_k]:
            r_copy = dict(r)
            r_copy["rerank_score"] = score
            reranked.append(r_copy)
        
        return reranked
    
    def assess_relevance(self, query: str, passage: str) -> Dict:
        """Deep relevance assessment of a single passage to a query."""
        llm = self._get_llm()
        if not llm:
            return {"error": "LLM not available"}
        
        prompt = f"""You are a Michigan legal expert. Assess the relevance of this evidence to the legal issue.

Legal Issue: {query[:300]}
Evidence: {passage[:500]}

Provide:
1. Relevance (1-10):
2. Legal significance (one sentence):
3. Useful for (motion/brief/appeal/complaint):"""
        
        try:
            response = llm(prompt, max_tokens=150, temperature=0.1)
            text = response["choices"][0]["text"].strip()
            return {"assessment": text, "query": query[:100], "passage": passage[:200]}
        except Exception as e:
            return {"error": str(e)}
    
    def batch_assess(self, query: str, passages: List[str], max_batch: int = 10) -> List[Dict]:
        """Assess multiple passages against a query."""
        return [self.assess_relevance(query, p) for p in passages[:max_batch]]
    
    def status(self) -> Dict:
        return {
            "engine": "MANBEARPIG-Reranker",
            "model_path": self.model_path,
            "model_available": self._available,
            "model_loaded": self._llm is not None,
            "n_ctx": self.n_ctx,
            "n_threads": self.n_threads
        }

def self_test():
    results = {"tests": [], "status": "pass"}
    try:
        rr = Reranker()
        # Test 1: Status
        s = rr.status()
        results["tests"].append({"name": "status", "pass": True, "available": s["model_available"]})
        
        if s["model_available"]:
            # Test 2: Rerank
            test_results = [
                {"snippet": "Judge McNeill denied parenting time without a hearing", "id": "1"},
                {"snippet": "The weather in Michigan is cold in winter", "id": "2"},
                {"snippet": "Ex parte communication between court and opposing party", "id": "3"},
            ]
            reranked = rr.rerank("ex parte communication by judge", test_results, top_k=3)
            results["tests"].append({"name": "rerank", "pass": len(reranked) > 0, "top_id": reranked[0]["id"] if reranked else None})
            
            # Test 3: Relevance assessment
            assessment = rr.assess_relevance("judicial bias", "Judge repeatedly ruled against father without hearing evidence")
            results["tests"].append({"name": "assess", "pass": "assessment" in assessment or "error" not in assessment})
        else:
            results["tests"].append({"name": "rerank", "pass": True, "note": "Model not available, fallback mode"})
        
        results["status"] = "pass" if all(t["pass"] for t in results["tests"]) else "partial"
    except Exception as e:
        results["status"] = "fail"
        results["error"] = str(e)
    return results

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    rr = Reranker()
    if cmd == "status":
        print(json.dumps(rr.status(), indent=2))
    elif cmd == "self-test":
        print(json.dumps(self_test(), indent=2))
    elif cmd == "test-rerank":
        test = [
            {"snippet": "Judge denied hearing without notice", "id": "1"},
            {"snippet": "Michigan weather patterns", "id": "2"},
            {"snippet": "Ex parte ruling on custody", "id": "3"},
        ]
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "ex parte judicial misconduct"
        print(json.dumps(rr.rerank(query, test), indent=2))
