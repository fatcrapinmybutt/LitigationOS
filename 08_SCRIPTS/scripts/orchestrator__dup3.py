import os, json, datetime
from .rules_intel import RulesIntelligenceCore
from .draft_engine import DraftEngine
from .simulation_engine import SimulationEngine
from .oversight_engine import OversightEngine
from .actions import ActionabilityEngine

class MultiFrontOrchestrator:
    """
    Consumes ODB's ranked actions and produces:
    - Auto-drafted DOCX filings (top 3 actions)
    - Predicted adversary counter-moves
    - Parallel oversight/regulatory filings list
    - Bundle output paths for dashboard download
    """
    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.de = DraftEngine(self.data_dir)
        self.se = SimulationEngine()
        self.oe = OversightEngine()

    def _draft_for(self, action: str) -> str:
        a = action.lower()
        if "complaint" in a or "§1983" in a or "rico" in a:
            return self.de.complaint_doc(kind="§1983 Retaliation / Due Process")
        if "injunction" in a or "tro" in a:
            return self.de.injunction_doc()
        if "disqualify" in a:
            return self.de.disqualification_doc()
        if "relief from judgment" in a:
            return self.de.relief_from_judgment_doc()
        if "appeal" in a:
            return self.de.appeal_packet()
        if "show cause" in a or "contempt" in a:
            return self.de.show_cause_doc()
        if "discovery" in a or "subpoena" in a:
            return self.de.discovery_packet()
        if "jtc" in a:
            return self.de.jtc_complaint()
        if "egle" in a:
            return self.de.egle_letter()
        if "hud" in a:
            return self.de.hud_letter()
        if "foia" in a:
            return self.de.foia_request()
        # default
        return self.de.discovery_packet()

    def orchestrate(self, ranking: list, topk: int = 3):
        chosen = [r[0] for r in ranking[:topk]]
        drafts = []
        counters = {}
        parallels = {}
        for act in chosen:
            path = self._draft_for(act)
            drafts.append({"action": act, "docx": path})
            counters[act] = self.se.predict(act)
            parallels[act] = self.oe.parallel_for(act)
        return {
            "ts": datetime.datetime.now().isoformat(),
            "chosen_actions": chosen,
            "drafts": drafts,
            "predicted_counters": counters,
            "parallel_paths": parallels
        }
