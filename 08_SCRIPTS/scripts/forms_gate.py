from typing import Dict, Any

class FormsGate:
    MAP = {
        "object_tax_intercept": ["MC 13 (Objection)", "MC 20 (Fee Waiver)"],
        "enforce_parenting_time": ["FOC 65 (Show Cause)","FOC 88 (Entry of Parenting Time Order)"],
        "move_to_disqualify": ["No SCAO form (Motion under MCR 2.003)"],
        "file_show_cause": ["FOC 65 (Show Cause)"]
    }
    def map_action_to_forms(self, action: str) -> Dict[str, Any]:
        return {"action": action, "required_forms": self.MAP.get(action, [])}
