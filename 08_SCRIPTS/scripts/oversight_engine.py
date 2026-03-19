class OversightEngine:
    """
    Produces parallel-path drafts and checklists for regulators/oversight:
    - HUD/FHA, EGLE, FOIA/MOAA, JTC
    """
    def parallel_for(self, action: str):
        action_l = action.lower()
        paths = []
        if "housing" in action_l or "eviction" in action_l or "injunction" in action_l:
            paths += ["EGLE violation letter", "HUD discrimination complaint"]
        if "parenting" in action_l or "custody" in action_l:
            paths += ["DHHS complaint for interference"]
        if "disqualify" in action_l or "canon" in action_l or "bias" in action_l:
            paths += ["JTC misconduct complaint"]
        return paths
