from typing import List, Dict, Any

class CanonDetector:
    def scan(self, timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Minimal pass-through with counters you can expand.
        hits = [t for t in timeline if t.get("flag") == "ex_parte_without_findings"]
        return {"count": len(hits), "hits": hits}
