"""
DARWIN Engine — Main Orchestrator
The brain of the self-evolving agent system.
Coordinates genome registration, evolution cycles, and fleet management.

Usage:
    python darwin_engine.py bootstrap     # Register all existing agents as genomes
    python darwin_engine.py evolve        # Run one evolution cycle
    python darwin_engine.py dashboard     # Show fleet fitness dashboard
    python darwin_engine.py breed A B     # Crossbreed two agents
    python darwin_engine.py specialize A domain  # Create specialist
    python darwin_engine.py learn A "failure notes"  # Learn from failure
    python darwin_engine.py stats A       # Show agent stats
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"

# Ensure we can import from parent
sys.path.insert(0, str(Path(__file__).parent.parent))

from darwin.agent_genome import AgentGenome, GenomeDB
from darwin.mutation_engine import MutationEngine, NaturalSelection


class DarwinEngine:
    """
    The DARWIN Engine — Self-Evolving Agent Fleet Management.

    Capabilities:
    1. Bootstrap: Register all existing agents as genomes
    2. Evolve: Run mutation/crossbreeding cycles
    3. Learn: Adapt agents based on failure analysis
    4. Speciate: Create domain specialists
    5. Dashboard: Visualize fleet fitness
    6. Predict: Recommend best agent for a task
    """

    REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
    AGENT_DIRS = [
        REPO_ROOT / ".agents" / "agents",
        REPO_ROOT / ".github" / "agents",
    ]
    SKILL_DIRS = [
        REPO_ROOT / ".agents" / "skills",
        REPO_ROOT / ".github" / "skills",
    ]

    def __init__(self):
        self.db = GenomeDB()
        self.mutator = MutationEngine(self.db)
        self.selector = NaturalSelection(self.db)

    def bootstrap(self) -> dict:
        """Register all existing agents as genomes in the DARWIN DB."""
        registered = []
        skipped = []

        for agent_dir in self.AGENT_DIRS:
            if not agent_dir.exists():
                continue
            # Collect .md files — agents can be subdirs OR flat .md files
            md_candidates = []
            for item in agent_dir.iterdir():
                if item.is_dir():
                    sub_mds = list(item.glob("*.md"))
                    if sub_mds:
                        md_candidates.append((item.name, sub_mds[0]))
                elif item.suffix == ".md":
                    agent_name = item.stem.replace(".agent", "")
                    md_candidates.append((agent_name, item))

            for agent_id, md_file in md_candidates:
                # Check if already registered
                existing = self.db.load_genome(agent_id)
                if existing:
                    skipped.append(agent_id)
                    continue

                # Create genome from agent definition
                genome = AgentGenome.from_agent_md(agent_id, md_file)

                # Detect OMEGA skill associations
                agent_content = md_file.read_text(encoding="utf-8", errors="replace").lower()
                omega_skills = []
                omega_names = [
                    "omega-litigation-supreme", "omega-evidence", "omega-research",
                    "omega-architect", "omega-code", "omega-data", "omega-security",
                    "omega-devops", "omega-writing", "omega-memory", "omega-mcp",
                    "omega-orchestrator", "omega-qa-validator", "omega-transcript-analyzer",
                    "omega-discovery", "omega-flatten", "omega-ocr",
                    "omega-forensic-accounting", "omega-expert-witness",
                ]
                for skill_name in omega_names:
                    if skill_name in agent_content:
                        omega_skills.append(skill_name)
                genome.omega_skills = omega_skills

                # Detect court format knowledge
                court_formats = []
                if "14th circuit" in agent_content or "circuit court" in agent_content:
                    court_formats.append("14th_circuit")
                if "60th district" in agent_content or "district court" in agent_content:
                    court_formats.append("60th_district")
                if "court of appeals" in agent_content or "coa" in agent_content:
                    court_formats.append("michigan_coa")
                if "supreme court" in agent_content or "msc" in agent_content:
                    court_formats.append("michigan_msc")
                if "federal" in agent_content or "usdc" in agent_content:
                    court_formats.append("usdc_wdmi")
                genome.court_formats = court_formats

                # Detect MCR rules knowledge
                mcr_rules = []
                import re
                mcr_matches = re.findall(r'MCR\s+[\d.]+', agent_content, re.IGNORECASE)
                mcr_rules = list(set(m.upper() for m in mcr_matches))[:20]
                genome.mcr_rules_known = mcr_rules

                # Initial fitness (untested = 0.5)
                genome.fitness_score = 0.5

                self.db.save_genome(genome)
                registered.append(agent_id)

        return {
            "registered": len(registered),
            "skipped": len(skipped),
            "agents": registered,
        }

    def evolve(self, intensity: float = 0.1) -> dict:
        """Run one full evolution cycle."""
        return self.selector.evolution_cycle(intensity)

    def recommend_agent(self, task_description: str) -> list:
        """
        Recommend the best agent(s) for a task based on genome fitness
        and domain matching.
        """
        all_agents = self.db.get_all_active()
        if not all_agents:
            return []

        task_lower = task_description.lower()

        # Score each agent for this task
        scored = []
        for genome in all_agents:
            score = genome.fitness_score * 0.4  # Base: historical performance

            # Domain match bonus
            domain_keywords = {
                "evidence": ["evidence", "exhibit", "authentication", "bates", "chain of custody"],
                "filing": ["motion", "brief", "draft", "filing", "complaint", "petition", "order"],
                "research": ["research", "case law", "MCL", "MCR", "precedent", "authority"],
                "investigation": ["investigate", "search", "find", "pattern", "conspiracy", "connection"],
                "custody": ["custody", "parenting", "child", "best interest", "L.D.W."],
                "judicial": ["judge", "McNeill", "misconduct", "recusal", "JTC", "bias"],
                "housing": ["Shady Oaks", "housing", "eviction", "property", "title"],
                "appellate": ["appeal", "COA", "MSC", "appellate", "brief"],
                "criminal": ["criminal", "self-defense", "trial", "Kostrzewa"],
                "emergency": ["emergency", "immediate", "urgent", "stay"],
            }

            domain_match = 0
            for domain, keywords in domain_keywords.items():
                if any(kw.lower() in task_lower for kw in keywords):
                    if domain in genome.expertise_domains:
                        domain_match += 0.2
                    # Also check weights
                    weight_map = {
                        "evidence": genome.evidence_weight,
                        "filing": genome.filing_weight,
                        "research": genome.research_weight,
                        "investigation": genome.investigation_weight,
                    }
                    if domain in weight_map:
                        domain_match += weight_map[domain] * 0.1

            score += min(0.4, domain_match)  # Cap domain bonus

            # Anti-hallucination bonus (important for litigation)
            score += len(genome.required_verifications) * 0.01
            score += genome.citation_strictness * 0.1

            # Penalty for agents with hallucination history
            if genome.hallucination_count > 0:
                score -= genome.hallucination_count * 0.05

            scored.append((genome, round(score, 3)))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return [(g.agent_id, g.name, s) for g, s in scored[:5]]

    def fleet_report(self) -> str:
        """Generate comprehensive fleet evolution report."""
        all_agents = self.db.get_all_active()

        # Categorize by generation
        gen_counts = {}
        for g in all_agents:
            gen_counts[g.generation] = gen_counts.get(g.generation, 0) + 1

        # Domain distribution
        domain_counts = {}
        for g in all_agents:
            for d in g.expertise_domains:
                domain_counts[d] = domain_counts.get(d, 0) + 1

        # Fitness distribution
        fitness_ranges = {"elite (0.8+)": 0, "strong (0.6-0.8)": 0,
                          "average (0.4-0.6)": 0, "weak (<0.4)": 0}
        for g in all_agents:
            if g.fitness_score >= 0.8:
                fitness_ranges["elite (0.8+)"] += 1
            elif g.fitness_score >= 0.6:
                fitness_ranges["strong (0.6-0.8)"] += 1
            elif g.fitness_score >= 0.4:
                fitness_ranges["average (0.4-0.6)"] += 1
            else:
                fitness_ranges["weak (<0.4)"] += 1

        import sqlite3
        with sqlite3.connect(str(self.db.db_path)) as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            evo_count = conn.execute(
                "SELECT COUNT(*) FROM evolution_log"
            ).fetchone()[0]
            task_count = conn.execute(
                "SELECT COUNT(*) FROM task_outcomes"
            ).fetchone()[0]
            culled_count = conn.execute(
                "SELECT COUNT(*) FROM evolution_log WHERE event_type = 'cull'"
            ).fetchone()[0]

        lines = [
            "╔══════════════════════════════════════════════════════════════════════╗",
            "║           🧬 DARWIN FLEET EVOLUTION REPORT 🧬                       ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║  Total Active Genomes:  {len(all_agents):<44}║",
            f"║  Evolution Events:      {evo_count:<44}║",
            f"║  Task Outcomes Tracked: {task_count:<44}║",
            f"║  Agents Culled:         {culled_count:<44}║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            "║  GENERATION DISTRIBUTION:                                            ║",
        ]
        for gen, count in sorted(gen_counts.items()):
            bar = "█" * min(count, 40)
            lines.append(f"║    Gen {gen}: {bar} ({count}){' ' * (50 - len(bar) - len(str(count)))}║")

        lines.append("╠══════════════════════════════════════════════════════════════════════╣")
        lines.append("║  FITNESS DISTRIBUTION:                                               ║")
        for label, count in fitness_ranges.items():
            bar = "█" * min(count * 2, 40)
            lines.append(f"║    {label}: {bar} ({count}){' ' * (46 - len(label) - len(bar) - len(str(count)))}║")

        lines.append("╠══════════════════════════════════════════════════════════════════════╣")
        lines.append("║  DOMAIN COVERAGE:                                                    ║")
        for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1])[:10]:
            bar = "█" * min(count, 40)
            lines.append(f"║    {domain}: {bar} ({count}){' ' * (52 - len(domain) - len(bar) - len(str(count)))}║")

        lines.append("╚══════════════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="DARWIN Engine — Self-Evolving Agent Fleet Management"
    )
    parser.add_argument("command", choices=[
        "bootstrap", "evolve", "dashboard", "report", "breed",
        "specialize", "learn", "stats", "recommend",
    ], help="Command to execute")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    parser.add_argument("--intensity", type=float, default=0.1,
                        help="Mutation intensity (0.0-1.0)")

    args = parser.parse_args()
    engine = DarwinEngine()

    if args.command == "bootstrap":
        result = engine.bootstrap()
        print(f"✅ Bootstrapped {result['registered']} agents, skipped {result['skipped']}")
        for agent_id in result["agents"][:20]:
            print(f"   🧬 {agent_id}")
        if result["registered"] > 20:
            print(f"   ... and {result['registered'] - 20} more")

    elif args.command == "evolve":
        result = engine.evolve(args.intensity)
        print(f"🧬 Evolution cycle complete:")
        print(f"   Total agents: {result['total_agents']}")
        print(f"   Top fitness: {result['top_fitness']:.3f}")
        print(f"   Crossbreeds: {result['crossbreeds']}")
        print(f"   Mutations: {result['mutations']}")
        print(f"   Culled: {result['culled']}")

    elif args.command == "dashboard":
        print(engine.db.fleet_dashboard())

    elif args.command == "report":
        print(engine.fleet_report())

    elif args.command == "breed":
        if len(args.args) < 2:
            print("Usage: darwin_engine.py breed AGENT_A AGENT_B")
            sys.exit(1)
        a = engine.db.load_genome(args.args[0])
        b = engine.db.load_genome(args.args[1])
        if not a or not b:
            print("Error: one or both agents not found in DARWIN DB")
            sys.exit(1)
        child = engine.mutator.crossbreed(a, b)
        print(f"🧬 Crossbreed created: {child.agent_id}")
        print(f"   Generation: {child.generation}")
        print(f"   Domains: {', '.join(child.expertise_domains)}")

    elif args.command == "specialize":
        if len(args.args) < 2:
            print("Usage: darwin_engine.py specialize AGENT_ID DOMAIN")
            sys.exit(1)
        genome = engine.db.load_genome(args.args[0])
        if not genome:
            print(f"Error: agent {args.args[0]} not found")
            sys.exit(1)
        specialist = engine.mutator.speciate(genome, args.args[1])
        print(f"🧬 Specialist created: {specialist.agent_id}")

    elif args.command == "learn":
        if len(args.args) < 2:
            print("Usage: darwin_engine.py learn AGENT_ID 'failure notes'")
            sys.exit(1)
        genome = engine.db.load_genome(args.args[0])
        if not genome:
            print(f"Error: agent {args.args[0]} not found")
            sys.exit(1)
        evolved = engine.mutator.adversarial_learn(genome, args.args[1])
        print(f"🧬 Agent adapted from failure: {evolved.agent_id}")
        print(f"   New verifications: {evolved.required_verifications}")

    elif args.command == "stats":
        if not args.args:
            print("Usage: darwin_engine.py stats AGENT_ID")
            sys.exit(1)
        stats = engine.db.get_agent_stats(args.args[0])
        genome = engine.db.load_genome(args.args[0])
        if genome:
            print(f"🧬 Agent: {genome.name} (Gen {genome.generation})")
            print(f"   Fitness: {genome.fitness_score:.3f}")
            print(f"   Domains: {', '.join(genome.expertise_domains)}")
        print(f"   Stats: {json.dumps(stats, indent=2)}")

    elif args.command == "recommend":
        if not args.args:
            print("Usage: darwin_engine.py recommend 'task description'")
            sys.exit(1)
        task = " ".join(args.args)
        recs = engine.recommend_agent(task)
        print(f"🎯 Best agents for: '{task[:60]}...'")
        for agent_id, name, score in recs:
            print(f"   {score:.3f} │ {agent_id} ({name})")


if __name__ == "__main__":
    main()
