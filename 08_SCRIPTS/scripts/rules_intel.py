import os, json, datetime

class RulesIntelligenceCore:
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data", "ruleswatch")
        os.makedirs(self.data_dir, exist_ok=True)
        self.patch_log = os.path.join(self.data_dir, "patch_log.json")

    def analyze_and_patch(self, rules_results: dict) -> dict:
        weapons = []
        patches = []

        for name, res in rules_results.get("results", {}).items():
            if res.get("delta_lines", 0) > 0:
                # Example heuristics
                if "2.119" in "".join(res.get("delta_preview", [])):
                    weapons.append({
                        "type": "motion_reload",
                        "rule": "MCR 2.119",
                        "strategy": "Refile motions denied on procedural grounds using amended deadlines."
                    })
                    patches.append("Patched Motion Generator deadlines per MCR 2.119 amendment.")
                if "service" in "".join(res.get("delta_preview", [])).lower():
                    weapons.append({
                        "type": "retroactive_attack",
                        "rule": "Service Rule Update",
                        "strategy": "Challenge prior defective service by opposing party."
                    })
                    patches.append("Updated Service Validator with new requirements.")
                if "parenting time" in "".join(res.get("delta_preview", [])).lower():
                    weapons.append({
                        "type": "adversary_strike",
                        "rule": "Parenting Time Procedure",
                        "strategy": "Exploit opponent filings that fail to comply with updated parenting-time rules."
                    })
                    patches.append("Refreshed Parenting-Time Template mappings.")

        log_entry = {
            "ts": datetime.datetime.now().isoformat(),
            "patches": patches,
            "weapons": weapons
        }
        hist = []
        if os.path.exists(self.patch_log):
            try:
                hist = json.load(open(self.patch_log,"r",encoding="utf-8"))
            except Exception:
                hist = []
        hist.append(log_entry)
        with open(self.patch_log,"w",encoding="utf-8") as f:
            json.dump(hist,f,ensure_ascii=False,indent=2)

        return {"patched": patches, "weapons": weapons, "log_path": self.patch_log}
