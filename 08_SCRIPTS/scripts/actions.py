from typing import Dict, Any, List

# Minimal scoring logic focusing on "single best action" selection.
class ActionabilityEngine:
    def best_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Very simple heuristic for now.
        candidates: List[Dict[str, Any]] = [
            {"action": "object_tax_intercept", "score": 0.86},
            {"action": "enforce_parenting_time", "score": 0.83},
            {"action": "move_to_disqualify", "score": 0.77},
            {"action": "file_show_cause", "score": 0.74},
        ]
        top = max(candidates, key=lambda x: x["score"])
        return {"top": top, "ranked": candidates}
