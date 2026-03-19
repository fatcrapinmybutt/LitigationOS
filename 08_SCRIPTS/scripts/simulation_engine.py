class SimulationEngine:
    """
    Predicts adversary responses and judicial posture for each recommended action.
    Outputs: list of likely counter-moves + notes for anticipated replies.
    """
    def predict(self, action: str):
        action_l = action.lower()
        counters = []
        if "§1983" in action or "complaint" in action_l:
            counters += [
                "Motion to Dismiss (failure to state a claim / immunity)",
                "You: Pre-draft opposition, clarify facts, qualified immunity analysis."
            ]
        if "injunction" in action_l or "tro" in action_l:
            counters += [
                "Opposition on likelihood of success / no irreparable harm",
                "You: Emphasize irreparable harm and public interest, attach exhibits."
            ]
        if "disqualify" in action_l:
            counters += [
                "Court denies for 'adverse ruling ≠ bias'",
                "You: Provide non-judicial source of bias + specific Canon cites."
            ]
        if "relief from judgment" in action_l:
            counters += [
                "Opp burns 'finality' and 'no new evidence' arguments",
                "You: Narrow grounds under MCR 2.612(C), show diligence."
            ]
        if "jtc" in action_l:
            counters += [
                "Dismiss as disagreement with rulings",
                "You: Focus on Canons and procedural violations, not mere outcomes."
            ]
        return counters
