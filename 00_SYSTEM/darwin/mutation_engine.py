"""
DARWIN Engine — Mutation & Crossbreeding
Evolves agent genomes through:
  - Point mutations (tweak single genes)
  - Crossover breeding (combine two high-performers)
  - Adversarial selection (learn from failures)
  - Speciation (spawn specialists from generalists)
"""

import sys
import json
import random
import copy
from datetime import datetime
from typing import Tuple

import os
os.environ["PYTHONUTF8"] = "1"

from .agent_genome import AgentGenome, GenomeDB


class MutationEngine:
    """Evolves agent genomes through controlled mutations."""

    # Weight genes that can be mutated
    WEIGHT_GENES = [
        "evidence_weight", "filing_weight", "research_weight",
        "investigation_weight", "qa_weight", "strategy_weight",
        "citation_strictness",
    ]

    # Known anti-hallucination patterns (always added, never removed)
    PERMANENT_FORBIDDEN = [
        "Jane Berry", "Patricia Berry", "91% alienation",
        "Tiffany Watson", "Lincoln David Watson", "Ron Berry Esq",
        "Amy McNeill", "Emily Ann", "Emily M.",
    ]

    def __init__(self, db: GenomeDB = None):
        self.db = db or GenomeDB()

    def mutate(self, genome: AgentGenome, intensity: float = 0.1) -> AgentGenome:
        """
        Apply random mutations to a genome.
        intensity: 0.0 (no change) to 1.0 (radical mutation)
        Returns a new genome (original unchanged).
        """
        child = copy.deepcopy(genome)
        child.generation += 1
        child.parent_ids = [genome.agent_id]
        child.last_evolved = datetime.now().isoformat()

        mutations_applied = []

        # 1. Weight mutations — nudge capability weights
        for gene in self.WEIGHT_GENES:
            if random.random() < intensity:
                old_val = getattr(child, gene)
                delta = random.gauss(0, intensity * 0.2)
                new_val = max(0.0, min(1.0, old_val + delta))
                setattr(child, gene, round(new_val, 3))
                mutations_applied.append(f"{gene}: {old_val:.3f} → {new_val:.3f}")

        # 2. Domain expansion — occasionally add new expertise
        all_domains = [
            "evidence", "filing", "research", "investigation",
            "custody", "judicial", "housing", "appellate", "criminal",
            "ppo", "federal", "foia", "damages", "emergency",
        ]
        if random.random() < intensity * 0.5:
            missing = [d for d in all_domains if d not in child.expertise_domains]
            if missing:
                new_domain = random.choice(missing)
                child.expertise_domains.append(new_domain)
                mutations_applied.append(f"+domain: {new_domain}")

        # 3. Anti-hallucination reinforcement (only adds, never removes)
        for pattern in self.PERMANENT_FORBIDDEN:
            if pattern not in child.forbidden_patterns:
                child.forbidden_patterns.append(pattern)

        # 4. Verification gene mutations
        all_verifications = [
            "party_names", "case_numbers", "bar_numbers", "statistics",
            "dates", "addresses", "citations", "exhibit_references",
            "service_compliance", "mcr_compliance", "signature_blocks",
        ]
        if random.random() < intensity * 0.3:
            missing = [v for v in all_verifications if v not in child.required_verifications]
            if missing:
                new_ver = random.choice(missing)
                child.required_verifications.append(new_ver)
                mutations_applied.append(f"+verification: {new_ver}")

        child.compute_hash()

        # Log the evolution
        self.db.save_genome(child)
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO evolution_log
                (event_type, parent_ids, child_id, mutation_type, detail)
                VALUES ('mutation', ?, ?, 'point_mutation', ?)
            """, (
                json.dumps([genome.agent_id]),
                child.agent_id,
                json.dumps(mutations_applied),
            ))

        return child

    def crossbreed(self, parent_a: AgentGenome, parent_b: AgentGenome,
                   child_id: str = None) -> AgentGenome:
        """
        Combine two high-performing genomes into a new agent.
        Takes the best traits from each parent.
        """
        child_id = child_id or f"{parent_a.agent_id}-x-{parent_b.agent_id}"
        child = AgentGenome(
            agent_id=child_id,
            name=f"Hybrid: {parent_a.name} × {parent_b.name}",
            generation=max(parent_a.generation, parent_b.generation) + 1,
            parent_ids=[parent_a.agent_id, parent_b.agent_id],
        )

        # Weight genes: pick the higher-fitness parent's weights with some blending
        a_fitness = parent_a.fitness_score or 0.5
        b_fitness = parent_b.fitness_score or 0.5
        total = a_fitness + b_fitness
        a_ratio = a_fitness / total if total > 0 else 0.5

        for gene in self.WEIGHT_GENES:
            a_val = getattr(parent_a, gene)
            b_val = getattr(parent_b, gene)
            blended = a_val * a_ratio + b_val * (1 - a_ratio)
            setattr(child, gene, round(blended, 3))

        # Domains: union of both parents
        child.expertise_domains = list(set(
            parent_a.expertise_domains + parent_b.expertise_domains
        ))

        # OMEGA skills: union
        child.omega_skills = list(set(
            parent_a.omega_skills + parent_b.omega_skills
        ))

        # Anti-hallucination: union (safety genes always accumulate)
        child.forbidden_patterns = list(set(
            parent_a.forbidden_patterns + parent_b.forbidden_patterns +
            self.PERMANENT_FORBIDDEN
        ))
        child.required_verifications = list(set(
            parent_a.required_verifications + parent_b.required_verifications
        ))

        # Court formats: union
        child.court_formats = list(set(
            parent_a.court_formats + parent_b.court_formats
        ))
        child.mcr_rules_known = list(set(
            parent_a.mcr_rules_known + parent_b.mcr_rules_known
        ))

        # System prompt: take the longer/more detailed one
        if len(parent_a.system_prompt) >= len(parent_b.system_prompt):
            child.system_prompt = parent_a.system_prompt
        else:
            child.system_prompt = parent_b.system_prompt

        child.role_description = (
            f"Hybrid agent combining {parent_a.name} ({parent_a.fitness_score:.2f}) "
            f"and {parent_b.name} ({parent_b.fitness_score:.2f}). "
            f"Gen {child.generation}. Domains: {', '.join(child.expertise_domains)}."
        )

        # Citation strictness: take the stricter parent
        child.citation_strictness = max(
            parent_a.citation_strictness, parent_b.citation_strictness
        )

        child.compute_hash()
        self.db.save_genome(child)

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO evolution_log
                (event_type, parent_ids, child_id, mutation_type, detail)
                VALUES ('crossbreed', ?, ?, 'crossover', ?)
            """, (
                json.dumps([parent_a.agent_id, parent_b.agent_id]),
                child.agent_id,
                json.dumps({
                    "a_fitness": a_fitness,
                    "b_fitness": b_fitness,
                    "domains": child.expertise_domains,
                    "skills": child.omega_skills,
                }),
            ))

        return child

    def speciate(self, generalist: AgentGenome, domain: str,
                 specialist_id: str = None) -> AgentGenome:
        """
        Create a specialist from a generalist by amplifying one domain.
        Like biological speciation — adaptation to a niche.
        """
        specialist_id = specialist_id or f"{generalist.agent_id}-{domain}-specialist"
        specialist = copy.deepcopy(generalist)
        specialist.agent_id = specialist_id
        specialist.name = f"{domain.title()} Specialist (from {generalist.name})"
        specialist.generation = generalist.generation + 1
        specialist.parent_ids = [generalist.agent_id]
        specialist.last_evolved = datetime.now().isoformat()

        # Amplify the target domain
        domain_weight_map = {
            "evidence": "evidence_weight",
            "filing": "filing_weight",
            "research": "research_weight",
            "investigation": "investigation_weight",
            "qa": "qa_weight",
            "strategy": "strategy_weight",
        }

        if domain in domain_weight_map:
            setattr(specialist, domain_weight_map[domain], 0.95)
            # Slightly reduce other weights (specialization cost)
            for d, gene in domain_weight_map.items():
                if d != domain:
                    current = getattr(specialist, gene)
                    setattr(specialist, gene, round(current * 0.8, 3))

        if domain not in specialist.expertise_domains:
            specialist.expertise_domains.append(domain)

        specialist.role_description = (
            f"Specialized {domain} agent evolved from {generalist.name}. "
            f"Gen {specialist.generation}. "
            f"Primary focus: {domain} with {domain_weight_map.get(domain, 'general')} at 0.95."
        )

        specialist.compute_hash()
        self.db.save_genome(specialist)

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO evolution_log
                (event_type, parent_ids, child_id, mutation_type, detail)
                VALUES ('speciation', ?, ?, 'specialize', ?)
            """, (
                json.dumps([generalist.agent_id]),
                specialist.agent_id,
                json.dumps({"domain": domain, "weight": 0.95}),
            ))

        return specialist

    def adversarial_learn(self, genome: AgentGenome, failure_notes: str) -> AgentGenome:
        """
        Learn from a failure by strengthening the genes that would prevent it.
        This is the 'immune system' of the agent fleet.
        """
        child = copy.deepcopy(genome)
        child.generation += 1
        child.parent_ids = [genome.agent_id]
        child.last_evolved = datetime.now().isoformat()

        adaptations = []

        # Parse failure notes for known failure modes
        failure_lower = failure_notes.lower()

        if "hallucination" in failure_lower or "fabricat" in failure_lower:
            child.citation_strictness = min(1.0, child.citation_strictness + 0.1)
            if "statistics" not in child.required_verifications:
                child.required_verifications.append("statistics")
            adaptations.append("↑ citation_strictness, +verify statistics")

        if "placeholder" in failure_lower:
            child.qa_weight = min(1.0, child.qa_weight + 0.15)
            if "exhibit_references" not in child.required_verifications:
                child.required_verifications.append("exhibit_references")
            adaptations.append("↑ qa_weight, +verify exhibit_references")

        if "wrong name" in failure_lower or "party name" in failure_lower:
            if "party_names" not in child.required_verifications:
                child.required_verifications.append("party_names")
            adaptations.append("+verify party_names")

        if "citation" in failure_lower or "mcr" in failure_lower or "mcl" in failure_lower:
            child.citation_strictness = min(1.0, child.citation_strictness + 0.1)
            if "citations" not in child.required_verifications:
                child.required_verifications.append("citations")
            adaptations.append("↑ citation_strictness, +verify citations")

        if "timeout" in failure_lower or "goaway" in failure_lower:
            # Failure was infrastructure, not behavioral — reduce complexity
            child.strategy_weight = max(0.3, child.strategy_weight - 0.1)
            adaptations.append("↓ strategy_weight (reduce complexity for speed)")

        if not adaptations:
            # Generic improvement: boost QA
            child.qa_weight = min(1.0, child.qa_weight + 0.05)
            adaptations.append("↑ qa_weight (generic improvement)")

        child.compute_hash()
        self.db.save_genome(child)

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO evolution_log
                (event_type, parent_ids, child_id, mutation_type, detail)
                VALUES ('adversarial_learn', ?, ?, 'failure_adaptation', ?)
            """, (
                json.dumps([genome.agent_id]),
                child.agent_id,
                json.dumps({"failure": failure_notes[:200], "adaptations": adaptations}),
            ))

        return child

    def _get_conn(self):
        import sqlite3
        conn = sqlite3.connect(str(self.db.db_path))
        conn.execute("PRAGMA busy_timeout=60000")
        return conn


class NaturalSelection:
    """Prunes underperformers and promotes top agents."""

    def __init__(self, db: GenomeDB = None):
        self.db = db or GenomeDB()

    def evaluate_fitness(self, genome: AgentGenome) -> float:
        """
        Calculate overall fitness score from task outcomes.
        Fitness = weighted average of quality, completeness, accuracy
        minus penalties for hallucinations and failures.
        """
        stats = self.db.get_agent_stats(genome.agent_id)

        if stats["total_tasks"] == 0:
            return 0.5  # Neutral for untested agents

        quality = stats["avg_quality"]
        completeness = stats["avg_completeness"]
        accuracy = stats["avg_accuracy"]

        # Weighted average (accuracy matters most in litigation)
        base_fitness = (
            quality * 0.25 +
            completeness * 0.25 +
            accuracy * 0.35 +
            stats.get("avg_citation_accuracy", 0.5) * 0.15
        )

        # Penalties
        hallucination_penalty = min(0.3, stats["total_hallucinations"] * 0.05)
        placeholder_penalty = min(0.2, stats["avg_placeholders"] * 0.02)

        fitness = max(0.0, base_fitness - hallucination_penalty - placeholder_penalty)

        # Update genome
        genome.fitness_score = round(fitness, 3)
        genome.avg_quality = round(quality, 3)
        genome.tasks_completed = stats["total_tasks"]
        self.db.save_genome(genome)

        return fitness

    def select_for_breeding(self, n_parents: int = 4) -> list:
        """Tournament selection: pick top performers for crossbreeding."""
        all_agents = self.db.get_all_active()
        if len(all_agents) < 2:
            return all_agents

        # Evaluate fitness for all
        for genome in all_agents:
            self.evaluate_fitness(genome)

        # Sort by fitness
        all_agents.sort(key=lambda g: g.fitness_score, reverse=True)

        return all_agents[:n_parents]

    def cull_underperformers(self, min_tasks: int = 5, fitness_threshold: float = 0.3):
        """Deactivate agents that consistently underperform."""
        import sqlite3
        with sqlite3.connect(str(self.db.db_path)) as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            # Find agents with enough tasks but low fitness
            rows = conn.execute("""
                SELECT agent_id, fitness_score, tasks_completed, hallucination_count
                FROM genomes
                WHERE is_active = 1
                  AND tasks_completed >= ?
                  AND fitness_score < ?
            """, (min_tasks, fitness_threshold)).fetchall()

            culled = []
            for row in rows:
                conn.execute(
                    "UPDATE genomes SET is_active = 0 WHERE agent_id = ?",
                    (row[0],)
                )
                conn.execute("""
                    INSERT INTO evolution_log
                    (event_type, parent_ids, child_id, mutation_type, detail)
                    VALUES ('cull', ?, ?, 'underperformer', ?)
                """, (
                    json.dumps([row[0]]), row[0],
                    json.dumps({
                        "fitness": row[1],
                        "tasks": row[2],
                        "hallucinations": row[3],
                    }),
                ))
                culled.append(row[0])

            return culled

    def evolution_cycle(self, intensity: float = 0.1) -> dict:
        """
        Run one full evolution cycle:
        1. Evaluate all agents
        2. Select top performers
        3. Crossbreed top 2
        4. Mutate mid-tier agents
        5. Cull underperformers
        Returns summary of changes.
        """
        mutator = MutationEngine(self.db)

        # Step 1: Evaluate
        all_agents = self.db.get_all_active()
        for g in all_agents:
            self.evaluate_fitness(g)

        # Step 2: Select parents
        parents = self.select_for_breeding(4)
        results = {
            "total_agents": len(all_agents),
            "top_fitness": parents[0].fitness_score if parents else 0,
            "crossbreeds": [],
            "mutations": [],
            "culled": [],
        }

        # Step 3: Crossbreed top 2 (if we have at least 2)
        if len(parents) >= 2:
            child = mutator.crossbreed(parents[0], parents[1])
            results["crossbreeds"].append(child.agent_id)

        # Step 4: Mutate mid-tier (positions 2-5 in fitness ranking)
        all_agents.sort(key=lambda g: g.fitness_score, reverse=True)
        mid_tier = all_agents[2:6] if len(all_agents) > 2 else []
        for genome in mid_tier:
            mutated = mutator.mutate(genome, intensity)
            results["mutations"].append(mutated.agent_id)

        # Step 5: Cull
        results["culled"] = self.cull_underperformers()

        return results


if __name__ == "__main__":
    db = GenomeDB()
    selector = NaturalSelection(db)
    print("DARWIN Natural Selection initialized.")
    print("Run selector.evolution_cycle() to evolve the fleet.")
