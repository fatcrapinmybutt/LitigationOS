import os, json, datetime
from .actions import ActionabilityEngine
from .forms_gate import FormsGate
from .binder import Binderizer

class ODB:
    """
    Offense/Defense Brain (ODB) — Expanded
    Multidimensional action universe:
    - Initiating/Emergency
    - Mid-Litigation
    - Post-Judgment/Appellate
    - Parallel/Extra-Procedural
    """
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

        # Baseline actionability (motions etc.)
        ae = ActionabilityEngine()
        best = ae.best_action(context=context)

        # Core categories
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

        # Heuristic scoring
        scores = {}
        for cat, opts in actions.items():
            for opt in opts:
                score = 0.3
                if "Parenting" in opt or "custody" in opt.lower():
                    score += 0.4
                if "Service" in opt or "jurisdiction" in opt.lower():
                    score += 0.3
                if "Appeal" in opt or "Relief" in opt:
                    score += 0.2
                if "JTC" in opt or "Disqualification" in opt:
                    score += 0.2
                scores[opt] = score

        # Patch-driven nudges
        for w in latest_patches.get("weapons", []):
            strategy = (w.get("strategy") or "").lower()
            for opt in scores:
                if any(k in strategy for k in ["service", "parenting", "motion", "canon"]):
                    scores[opt] += 0.2

        # Rank all options
        ranking = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

        # Binderize the top recommended action
        fg = FormsGate()
        chosen_action = ranking[0][0]
        forms = fg.map_action_to_forms(best["top"]["action"]).get("required_forms", [])
        bz = Binderizer()
        binder_zip = bz.build(action=best["top"]["action"])

        plan = {
            "ts": datetime.datetime.now().isoformat(),
            "initiating": actions["initiating"],
            "mid_case": actions["mid_case"],
            "post_judgment": actions["post_judgment"],
            "parallel": actions["parallel"],
            "ranking": ranking[:10],
            "chosen_action": chosen_action,
            "forms_required": forms,
            "binder_zip": binder_zip,
            "rules_latest": latest_patches,
            "evidence_index_path": self.index_path
        }
        return plan
