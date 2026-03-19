import os, yaml, datetime

class VenueRules:
    """
    Loads venue rules from YAML and provides simple compliance/dependency checks.
    """
    def __init__(self, rules_dir: str):
        self.rules_dir = rules_dir

    def load(self, county: str):
        path = os.path.join(self.rules_dir, f"{county.lower()}.yaml")
        if not os.path.exists(path):
            return {"ok": False, "error": f"rules_not_found:{county}"}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return {"ok": True, "rules": data, "path": path}

    def dependencies_for(self, rules: dict, action: str):
        return (rules.get("dependencies") or {}).get(action, [])

    def check_plan(self, rules: dict, chosen_action: str, completed: list[str] | None = None):
        deps = self.dependencies_for(rules, chosen_action)
        completed = completed or []
        missing = [d for d in deps if d not in completed]
        compliant = len(missing) == 0
        return {"compliant": compliant, "missing_dependencies": missing}
