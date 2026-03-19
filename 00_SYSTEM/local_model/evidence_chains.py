"""
THE MANBEARPIG — Evidence Chain Reasoning (EPOCH v4.0)
Multi-hop reasoning: evidence → contradiction → impeachment → authority
"""
import os, sqlite3, json, time
from typing import List, Dict, Optional

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")

class EvidenceChainBuilder:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._semantic = None
        self._pagerank = None
    
    def _get_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_semantic(self):
        """Lazy-load semantic engine."""
        if self._semantic is None:
            try:
                from semantic_engine import SemanticEngine
                self._semantic = SemanticEngine()
            except:
                self._semantic = False  # Mark as unavailable
        return self._semantic if self._semantic else None
    
    def _get_pagerank(self):
        """Lazy-load pagerank engine."""
        if self._pagerank is None:
            try:
                from authority_pagerank import AuthorityPageRank
                self._pagerank = AuthorityPageRank()
            except:
                self._pagerank = False
        return self._pagerank if self._pagerank else None
    
    def build_chain(self, legal_ground: str, max_hops: int = 4, top_k: int = 10) -> Dict:
        """Build a complete multi-hop evidence chain for a legal ground.
        
        Hops:
        1. Find relevant evidence (semantic search or FTS)
        2. For each evidence, find related contradictions
        3. For each contradiction, find impeachment material
        4. For each piece, find supporting authority (PageRank-ranked)
        
        Returns: {
            ground: str,
            chains: [{evidence, contradictions, impeachments, authorities}],
            total_evidence: int,
            total_authorities: int,
            strength_score: float (0-1)
        }
        """
        start = time.time()
        db = self._get_db()
        semantic = self._get_semantic()
        pagerank = self._get_pagerank()
        
        chains = []
        
        # HOP 1: Find evidence
        if semantic:
            evidence_hits = semantic.search(legal_ground, top_k=top_k, doc_type="evidence")
            evidence_ids = [int(h["id"].split(":")[1]) for h in evidence_hits if h["id"].startswith("evidence:")]
        else:
            # Fallback to FTS
            rows = db.execute(
                "SELECT rowid, quote_text, speaker, evidence_category FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?) LIMIT ?",
                (legal_ground.replace(" ", " OR "), top_k)
            ).fetchall()
            evidence_ids = [r["rowid"] for r in rows]
            evidence_hits = [{"id": f"evidence:{r['rowid']}", "snippet": r["quote_text"][:200]} for r in rows]
        
        for i, ev in enumerate(evidence_hits[:top_k]):
            chain = {
                "hop_1_evidence": {
                    "id": ev["id"],
                    "text": ev.get("snippet", ""),
                    "score": ev.get("score", 0)
                },
                "hop_2_contradictions": [],
                "hop_3_impeachments": [],
                "hop_4_authorities": []
            }
            
            ev_text = ev.get("snippet", "")
            
            # HOP 2: Find contradictions related to this evidence
            if ev_text:
                # Search contradiction_map for related text
                search_terms = " OR ".join(ev_text.split()[:10])
                try:
                    contras = db.execute(
                        "SELECT rowid, source_a_text, source_b_text, contradiction_type, severity FROM contradiction_map WHERE source_a_text LIKE ? OR source_b_text LIKE ? LIMIT 5",
                        (f"%{ev_text[:50]}%", f"%{ev_text[:50]}%")
                    ).fetchall()
                    for c in contras:
                        chain["hop_2_contradictions"].append({
                            "id": c["rowid"],
                            "type": c["contradiction_type"],
                            "severity": c["severity"],
                            "text_a": (c["source_a_text"] or "")[:200],
                            "text_b": (c["source_b_text"] or "")[:200]
                        })
                except:
                    pass
            
            # HOP 3: Find impeachment items
            if ev_text:
                try:
                    imps = db.execute(
                        "SELECT rowid, speaker, statement, contradicting_text, legal_hook FROM impeachment_items WHERE statement LIKE ? OR contradicting_text LIKE ? LIMIT 5",
                        (f"%{ev_text[:50]}%", f"%{ev_text[:50]}%")
                    ).fetchall()
                    for imp in imps:
                        chain["hop_3_impeachments"].append({
                            "id": imp["rowid"],
                            "speaker": imp["speaker"],
                            "statement": (imp["statement"] or "")[:200],
                            "contradicting": (imp["contradicting_text"] or "")[:200],
                            "legal_hook": imp["legal_hook"]
                        })
                except:
                    pass
            
            # HOP 4: Find governing authority
            if pagerank:
                try:
                    authorities = pagerank.get_strongest_chain(legal_ground, depth=2)
                    if authorities:
                        for auth in authorities[:5]:
                            chain["hop_4_authorities"].append(auth)
                except:
                    pass
            
            # Fallback authority search
            if not chain["hop_4_authorities"]:
                try:
                    auths = db.execute(
                        "SELECT rule_number, title FROM auth_rules WHERE full_text LIKE ? LIMIT 5",
                        (f"%{legal_ground}%",)
                    ).fetchall()
                    for a in auths:
                        chain["hop_4_authorities"].append({
                            "rule": a["rule_number"],
                            "title": a["title"]
                        })
                except:
                    pass
            
            chains.append(chain)
        
        db.close()
        
        # Calculate strength score
        total_evidence = len(chains)
        total_contras = sum(len(c["hop_2_contradictions"]) for c in chains)
        total_imps = sum(len(c["hop_3_impeachments"]) for c in chains)
        total_auths = sum(len(c["hop_4_authorities"]) for c in chains)
        
        evidence_score = min(1.0, total_evidence / 10)
        contra_score = min(1.0, total_contras / 10) * 0.8
        imp_score = min(1.0, total_imps / 10) * 0.7
        auth_score = min(1.0, total_auths / 5)
        strength = (evidence_score * 0.3 + contra_score * 0.2 + imp_score * 0.2 + auth_score * 0.3)
        
        elapsed = time.time() - start
        
        return {
            "ground": legal_ground,
            "chains": chains,
            "total_evidence": total_evidence,
            "total_contradictions": total_contras,
            "total_impeachments": total_imps,
            "total_authorities": total_auths,
            "strength_score": round(strength, 4),
            "strength_grade": "STRONG" if strength > 0.7 else "ADEQUATE" if strength > 0.4 else "WEAK",
            "elapsed_seconds": round(elapsed, 2)
        }
    
    def build_irac_chain(self, issue: str) -> Dict:
        """Build a complete IRAC argument chain for a legal issue.
        Issue -> Rule (from authority) -> Application (from evidence chains) -> Conclusion
        """
        chain = self.build_chain(issue, top_k=15)
        
        db = self._get_db()
        
        # RULE: Find the governing rule
        rules = []
        for c in chain["chains"]:
            for auth in c["hop_4_authorities"]:
                rule = auth.get("rule") or auth.get("label", "")
                if rule and rule not in [r["rule"] for r in rules]:
                    # Get full text
                    try:
                        row = db.execute("SELECT rule_number, title, full_text FROM auth_rules WHERE rule_number = ?", (rule,)).fetchone()
                        if row:
                            rules.append({"rule": row["rule_number"], "title": row["title"], "text": (row["full_text"] or "")[:500]})
                    except:
                        rules.append({"rule": rule})
        
        # APPLICATION: Best evidence with contradictions
        applications = []
        for c in chain["chains"]:
            if c["hop_2_contradictions"] or c["hop_3_impeachments"]:
                applications.append({
                    "evidence": c["hop_1_evidence"]["text"][:300],
                    "contradictions": len(c["hop_2_contradictions"]),
                    "impeachments": len(c["hop_3_impeachments"])
                })
        
        db.close()
        
        return {
            "issue": issue,
            "rule": rules[:5],
            "application": applications[:10],
            "conclusion": {
                "strength": chain["strength_score"],
                "grade": chain["strength_grade"],
                "evidence_count": chain["total_evidence"],
                "authority_count": chain["total_authorities"]
            },
            "full_chain": chain
        }
    
    def build_filing_argument(self, filing_type: str, grounds: List[str]) -> Dict:
        """Build complete argument structure for a filing.
        For each ground, build an IRAC chain. Combine into filing-ready structure."""
        arguments = []
        for ground in grounds:
            irac = self.build_irac_chain(ground)
            arguments.append(irac)
        
        overall_strength = sum(a["conclusion"]["strength"] for a in arguments) / max(len(arguments), 1)
        
        return {
            "filing_type": filing_type,
            "arguments": arguments,
            "overall_strength": round(overall_strength, 4),
            "overall_grade": "STRONG" if overall_strength > 0.7 else "ADEQUATE" if overall_strength > 0.4 else "WEAK",
            "total_grounds": len(grounds),
            "strongest_ground": max(arguments, key=lambda a: a["conclusion"]["strength"])["issue"] if arguments else None,
            "weakest_ground": min(arguments, key=lambda a: a["conclusion"]["strength"])["issue"] if arguments else None
        }
    
    def status(self) -> Dict:
        return {
            "engine": "MANBEARPIG-EvidenceChains",
            "semantic_available": self._get_semantic() is not None,
            "pagerank_available": self._get_pagerank() is not None,
            "db_path": self.db_path
        }

def self_test():
    results = {"tests": [], "status": "pass"}
    try:
        ecb = EvidenceChainBuilder()
        # Test 1: build_chain
        chain = ecb.build_chain("ex parte communication", top_k=5)
        results["tests"].append({"name": "build_chain", "pass": chain["total_evidence"] > 0, "evidence": chain["total_evidence"], "strength": chain["strength_score"]})
        # Test 2: build_irac_chain
        irac = ecb.build_irac_chain("due process violation")
        results["tests"].append({"name": "irac_chain", "pass": "rule" in irac, "rules": len(irac["rule"]), "grade": irac["conclusion"]["grade"]})
        # Test 3: build_filing_argument
        filing = ecb.build_filing_argument("MSC_original_action", ["ex parte", "due process", "custody"])
        results["tests"].append({"name": "filing_argument", "pass": filing["total_grounds"] == 3, "strength": filing["overall_strength"]})
        results["status"] = "pass" if all(t["pass"] for t in results["tests"]) else "partial"
    except Exception as e:
        results["status"] = "fail"
        results["error"] = str(e)
    return results

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    ecb = EvidenceChainBuilder()
    if cmd == "chain":
        ground = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "ex parte"
        print(json.dumps(ecb.build_chain(ground), indent=2, default=str))
    elif cmd == "irac":
        issue = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "due process"
        print(json.dumps(ecb.build_irac_chain(issue), indent=2, default=str))
    elif cmd == "filing":
        filing_type = sys.argv[2] if len(sys.argv) > 2 else "MSC_original_action"
        grounds = sys.argv[3:] if len(sys.argv) > 3 else ["ex parte", "due process", "custody", "alienation"]
        print(json.dumps(ecb.build_filing_argument(filing_type, grounds), indent=2, default=str))
    elif cmd == "self-test":
        print(json.dumps(self_test(), indent=2))
    elif cmd == "status":
        print(json.dumps(ecb.status(), indent=2))
