import os, json, datetime
from .actions import ActionabilityEngine
from .forms_gate import FormsGate
from .binder import Binderizer

class ODB:
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data")
        self.rules_dir = os.path.join(self.data_dir, "ruleswatch")
        os.makedirs(self.rules_dir, exist_ok=True)
        self.graph_dir = os.path.join(self.data_dir, "graph_runs")
        self.index_path = os.path.join(self.data_dir, "evidence_index.json")
        self.patch_log = os.path.join(self.rules_dir, "patch_log.json")

    def _load_json(self, path, default):
        try:
            if os.path.exists(path):
                return json.load(open(path, "r", encoding="utf-8"))
        except Exception:
            pass
        return default

    def run(self, context=None):
        context = context or {}
        evidence = self._load_json(self.index_path, {"files": []})
        patches_hist = self._load_json(self.patch_log, [])
        latest_patches = patches_hist[-1] if patches_hist else {"patches": [], "weapons": []}

        actions = {
            "initiating": [
                "Verified Complaint (§1983, RICO, Fraud)",
                "Custody/Parenting Petition",
                "Petition for Superintending Control",
                "Injunction/TRO (Stay eviction, enforce parenting time, suspend PPO)",
                "Show Cause Petition (custody, housing)",
                "Regulatory Complaint (EGLE, HUD/FHA, DHHS)"
            ],
            "mid_case": [
                "Motion in Limine (exclude evidence)",
                "Discovery Sanctions",
                "Summary Disposition",
                "Affirmative Defense (jurisdiction/service defects)",
                "Counterclaim (fraud, abuse of process)",
                "Discovery Demand (subpoena, interrogatories, RFP)",
                "Contempt/Enforcement (show cause, jail time)",
                "Judicial Disqualification (MCR 2.003)"
            ],
            "post_judgment": [
                "Relief from Judgment (MCR 2.612)",
                "Appeal (COA leave/interlocutory, MSC supervisory, mandamus)",
                "Sanctions/Fees (MCR 1.109(E)(6))",
                "Record Correction (strike/settle transcript)"
            ],
            "parallel": [
                "Federal Civil Rights (§1983, RICO)",
                "Regulatory Filings (HUD/FHA, EGLE, FOIA/MOAA)",
                "JTC Complaint (Canon violations)",
                "Settlement Engineering (consent judgments, freeze rent, enforce parenting time)"
            ]
        }

        # Simple scoring
        scores = {}
        for cat, opts in actions.items():
            for opt in opts:
                score = 0.3
                if "parenting" in opt.lower(): score += 0.4
                if "service" in opt.lower() or "jurisdiction" in opt.lower(): score += 0.3
                if "appeal" in opt.lower() or "relief" in opt.lower(): score += 0.2
                if "jtc" in opt.lower() or "disqualification" in opt.lower(): score += 0.2
                scores[opt] = score
        for w in latest_patches.get("weapons", []):
            strategy = (w.get("strategy") or "").lower()
            for opt in scores:
                if any(k in strategy for k in ["service", "parenting", "motion", "canon"]):
                    scores[opt] += 0.2

        
        # Apply external pressure multipliers
        pressure = (context or {}).get("pressure", {})
        def bump(keys, amt):
            for opt in scores:
                if any(k.lower() in opt.lower() for k in keys):
                    scores[opt] += amt
        if pressure.get("registered_agent_network"):
            bump(["federal civil rights", "regulatory filings", "verified complaint", "rico"], pressure["registered_agent_network"])
        if pressure.get("ownership_loop"):
            bump(["federal civil rights", "verified complaint", "counterclaim"], pressure["ownership_loop"])
        if pressure.get("rent_extraction_chain"):
            bump(["regulatory filings", "settlement engineering", "verified complaint"], pressure["rent_extraction_chain"])

        ranking = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


        fg = FormsGate()
        # Map the top-ranked ODB path to forms via heuristic
        chosen_action = ranking[0][0]
        forms = fg.map_action_to_forms("Parenting Time Injunction").get("required_forms", [])
        bz = Binderizer()
        binder_zip = bz.build(action="Parenting Time Injunction")

        return {
            "ts": datetime.datetime.now().isoformat(),
            "ranking": ranking[:10],
            "initiating": actions["initiating"],
            "mid_case": actions["mid_case"],
            "post_judgment": actions["post_judgment"],
            "parallel": actions["parallel"],
            "chosen_action": chosen_action,
            "forms_required": forms,
            "binder_zip": binder_zip,
            "rules_latest": latest_patches,
            "evidence_index_path": self.index_path
        }
