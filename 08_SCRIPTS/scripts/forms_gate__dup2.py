from typing import Dict, Any

class FormsGate:
    MAP = {
        "Parenting Time Injunction": ["FOC 65 (Show Cause)","FOC 88 (Entry of Parenting Time Order)"],
        "Abuse-of-Process Counterclaim": ["MC 01 (Complaint)","MC 12 (Summons)"],
        "JTC Complaint": ["No SCAO form; JTC submission package"]
    }
    def map_action_to_forms(self, action: str) -> Dict[str, Any]:
        return {"action": action, "required_forms": self.MAP.get(action, [])}
