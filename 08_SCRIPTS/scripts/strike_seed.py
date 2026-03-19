import os, json
from .graph_analytics import GraphAnalytics

class GraphStrikeSeeder:
    """
    Converts graph analytics findings into allegations paragraphs and exhibit items.
    """
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data")

    def seed_from_run(self, run_id: str | None = None) -> dict:
        ga = GraphAnalytics()
        analysis = ga.analyze(run_id)
        if not analysis.get("ok"):
            return {"ok": False, "error": analysis.get("error", "analysis_failed")}
        details = analysis.get("details", {})
        al = []
        ex = []

        # Allegations based on common agents
        for agent in details.get("common_registered_agents", [])[:10]:
            al.append(f"Registered agent {agent.get('agent_name')} is linked to at least {agent.get('llc_count')} LLCs forming a network suggestive of shell structuring.")
        # Ownership loops
        if details.get("ownership_loops"):
            for loop in details["ownership_loops"][:10]:
                al.append(f"Ownership loop detected between {loop.get('a_name')} and {loop.get('b_name')} via reciprocal control, indicative of circular ownership.")
        # Rent extraction chains
        for chain in details.get("rent_extraction_chains", [])[:10]:
            al.append(f"Tenant {chain.get('tenant_name')} leases {chain.get('property_name')}; property owned by {chain.get('owner_llc_name')} and managed by {chain.get('manager_llc_name')}, evidencing a rent-extraction structure.")

        # Exhibits: persist analysis summary as JSON for attachment
        out_dir = os.path.join(self.data_dir, "graph_runs", analysis["run_id"])
        os.makedirs(out_dir, exist_ok=True)
        summary_path = os.path.join(out_dir, "graph_analysis_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        ex.append(f"Graph Analysis Summary ({analysis['run_id']}) — graph_analysis_summary.json")

        return {"ok": True, "allegations": al, "exhibits": ex, "run_id": analysis["run_id"], "summary_path": summary_path}
