from typing import Dict, Any, List

class ActionabilityEngine:
    def best_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        candidates: List[Dict[str, Any]] = [
            {"action": "Parenting Time Injunction", "score": 0.91},
            {"action": "Abuse-of-Process Counterclaim", "score": 0.86},
            {"action": "JTC Complaint", "score": 0.82}
        ]
        top = max(candidates, key=lambda x: x["score"])
        return {"top": top, "ranked": candidates}
