from typing import List, Dict, Any

class VeilPiercer:
    def map_entities(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Minimal structure: assumes records contain {parent, child, relation}
        edges = [{"from": r.get("parent"), "to": r.get("child"), "rel": r.get("relation","owns")} for r in records]
        nodes = sorted(set([e["from"] for e in edges] + [e["to"] for e in edges]))
        return {"nodes": nodes, "edges": edges}
