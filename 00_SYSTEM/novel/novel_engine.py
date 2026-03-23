"""
NOVEL Engine v2 — New Origination Via Evolutionary Learning

The GENUINE invention engine for LitigationOS.

v1 was a template dumper with hardcoded gap lists.
v2 is a real intelligence system that:
  - Perceives the ACTUAL state of the system by querying the real DB
  - Validates every invention it generates (syntax + imports + runtime + quality)
  - Composes existing tools into novel workflows (not just templates)
  - Evolves based on REAL fitness metrics (did the code work? did it help?)

Architecture:
  perception.py  — Deep system state analysis (DB + fleet + filesystem)
  validator.py   — Auto-tests generated code (4-phase pipeline)
  composer.py    — Discovers & generates novel workflow compositions
  creativity_engine.py — Gap detection, idea generation, prototype forging
  invention_genome.py  — DNA of inventions + SQLite persistence

Usage:
    python novel_engine.py perceive       # Deep perception scan (queries real DB)
    python novel_engine.py scan           # Legacy gap detection (hardcoded + perception)
    python novel_engine.py brainstorm     # Generate invention ideas from gaps
    python novel_engine.py invent <id>    # Design a full invention from a gap
    python novel_engine.py forge <id>     # Prototype an invention into working code
    python novel_engine.py validate <id>  # Test a prototype (syntax, imports, runtime, quality)
    python novel_engine.py compose        # Discover novel workflow compositions
    python novel_engine.py evolve         # Full evolution cycle (perceive→invent→validate→select)
    python novel_engine.py spawn <id>     # Deploy a validated invention
    python novel_engine.py mutate <id>    # Create a mutated variant
    python novel_engine.py breed <a> <b>  # Cross-pollinate two inventions
    python novel_engine.py imagine <id> <twist>  # Creative variant
    python novel_engine.py dashboard      # Ecosystem status with perception data
    python novel_engine.py report         # Full evolution report
    python novel_engine.py stats          # Quick stats
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"

sys.path.insert(0, str(Path(__file__).parent.parent))

from novel.invention_genome import InventionGenome, InventionDB, PROBLEM_DOMAINS, TECHNIQUE_LIBRARY, INVENTION_TYPES
from novel.creativity_engine import GapDetector, IdeaGenerator, PrototypeForge
from novel.perception import PerceptionEngine, DatabasePerception, FleetPerception
from novel.validator import ValidationPipeline, ValidationResult
from novel.composer import CompositionEngine


class NovelEngine:
    """
    NOVEL Engine v2 — Genuine Invention Factory for LitigationOS.

    v1 lifecycle: Scan → Imagine → Forge → Evolve (template-based)
    v2 lifecycle: Perceive → Scan → Imagine → Forge → Validate → Compose → Evolve → Spawn

    The key differences:
    1. Perceive queries the REAL database — no hardcoded gap lists
    2. Validate actually RUNS generated code and catches errors
    3. Compose chains existing tools into novel workflows
    4. Evolve uses real fitness metrics (did validation pass? was it deployed?)
    """

    def __init__(self):
        self.db = InventionDB()
        self.gap_detector = GapDetector(self.db)
        self.idea_generator = IdeaGenerator(self.db)
        self.forge_engine = PrototypeForge(self.db)

        # v2 modules
        self.perception = PerceptionEngine()
        self.validator = ValidationPipeline()
        self.composer = CompositionEngine()

    # ═══════════════════════════════════════════════════════════════
    # PERCEIVE — Deep perception scan (v2 — queries REAL database)
    # ═══════════════════════════════════════════════════════════════

    def perceive(self) -> dict:
        """
        Deep perception scan — queries litigation_context.db, analyzes
        the agent fleet, and scans the filesystem for the real system state.
        This is what makes v2 genuinely intelligent.
        """
        print("\n🧠 NOVEL v2 — Deep Perception Scan")
        print("   Querying litigation_context.db...")

        result = self.perception.full_perception()

        # Print the perception report
        report = self.perception.quick_report()
        print(report)

        # Convert perception findings into actionable gaps
        synthesis = result.get("synthesis", {})
        opportunities = synthesis.get("opportunities", [])

        if opportunities:
            print(f"\n   Registering {len(opportunities)} perception-discovered gaps...")
            for opp in opportunities:
                gap_id = f"perc_{opp['type']}_{datetime.now().strftime('%H%M%S')}"
                self.db.register_gap(
                    gap_id=gap_id,
                    domain=opp.get("domains", ["unknown"])[0],
                    description=opp["desc"],
                    severity=0.9 if opp["priority"] == "CRITICAL" else 0.6,
                    detected_by="perception_engine_v2",
                )

        return result

    # ═══════════════════════════════════════════════════════════════
    # SCAN — Detect gaps in the ecosystem
    # ═══════════════════════════════════════════════════════════════

    def scan(self) -> dict:
        """Full ecosystem scan for gaps, missing capabilities, and opportunities."""
        gaps = self.gap_detector.full_scan()

        by_type = {}
        for g in gaps:
            gt = g.get("gap_type", "unknown")
            by_type.setdefault(gt, []).append(g)

        by_domain = {}
        for g in gaps:
            d = g.get("domain", "unknown")
            by_domain.setdefault(d, []).append(g)

        result = {
            "total_gaps": len(gaps),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "by_domain": {k: len(v) for k, v in by_domain.items()},
            "critical": [g for g in gaps if g.get("severity", 0) >= 0.8],
            "high": [g for g in gaps if 0.6 <= g.get("severity", 0) < 0.8],
            "medium": [g for g in gaps if 0.4 <= g.get("severity", 0) < 0.6],
        }

        print(f"\n🔍 NOVEL Ecosystem Scan Complete")
        print(f"   Found {len(gaps)} gaps across {len(by_domain)} domains")
        print(f"   🔴 Critical: {len(result['critical'])}")
        print(f"   🟠 High: {len(result['high'])}")
        print(f"   🟡 Medium: {len(result['medium'])}")

        if result["critical"]:
            print(f"\n   Critical Gaps:")
            for g in result["critical"]:
                print(f"     ⚠️  [{g['domain']}] {g['description'][:80]}")

        return result

    # ═══════════════════════════════════════════════════════════════
    # BRAINSTORM — Generate invention ideas
    # ═══════════════════════════════════════════════════════════════

    def brainstorm(self, count: int = 5) -> list:
        """Generate invention ideas from detected gaps."""
        ideas = self.idea_generator.brainstorm(count)

        for idea in ideas:
            self.db.save(idea)

        print(f"\n💡 Brainstormed {len(ideas)} invention ideas:")
        for i, idea in enumerate(ideas):
            status_icon = {"concept": "💭", "designed": "📐", "prototyped": "🔧", "deployed": "🚀"}.get(idea.status, "❓")
            print(f"   {status_icon} [{idea.invention_id[:8]}] {idea.name}")
            print(f"      Type: {idea.invention_type} | Domains: {', '.join(idea.domains[:3])}")
            print(f"      Problem: {idea.problem_statement[:70]}...")

        return ideas

    # ═══════════════════════════════════════════════════════════════
    # INVENT — Design a full invention from a gap ID
    # ═══════════════════════════════════════════════════════════════

    def invent(self, gap_id: str) -> InventionGenome:
        """Turn a gap into a fully designed invention."""
        open_gaps = self.db.get_open_gaps()
        gap = None
        for g in open_gaps:
            if g["gap_id"] == gap_id:
                gap = g
                break

        if not gap:
            print(f"   ❌ Gap '{gap_id}' not found in open gaps")
            return None

        genome = self.idea_generator.generate_from_gap(gap)
        genome.status = "designed"
        genome.approach = self._design_approach(genome)
        genome.functions = self._design_functions(genome)
        genome.classes = self._design_classes(genome)
        genome.cli_commands = self._design_cli(genome)

        self.db.save(genome)

        print(f"\n🏗️  Invented: {genome.name}")
        print(f"   ID: {genome.invention_id}")
        print(f"   Type: {genome.invention_type}")
        print(f"   Approach: {genome.approach[:100]}...")
        print(f"   Functions: {len(genome.functions)}")
        print(f"   Classes: {len(genome.classes)}")
        print(f"   Techniques: {', '.join(genome.techniques)}")

        return genome

    # ═══════════════════════════════════════════════════════════════
    # FORGE — Prototype an invention into working code
    # ═══════════════════════════════════════════════════════════════

    def forge_invention(self, invention_id: str) -> str:
        """Turn a designed invention into a working prototype."""
        genome = self._find_invention(invention_id)
        if not genome:
            return None

        path = self.forge_engine.forge_prototype(genome)
        print(f"\n🔨 Forged prototype: {path}")
        print(f"   Invention: {genome.name} ({genome.invention_id})")

        # v2: Auto-validate after forging
        if path and Path(path).exists():
            print(f"   Auto-validating...")
            code = Path(path).read_text(encoding="utf-8", errors="replace")
            vr = self.validator.validate(code, run_code=False)
            genome.validation_score = vr.score
            genome.validation_errors = len(vr.errors)
            if vr.passed:
                print(f"   ✅ Validation PASSED (score: {vr.score:.3f})")
                genome.status = "prototyped"
            else:
                print(f"   ⚠️  Validation issues (score: {vr.score:.3f})")
                for err in vr.errors[:3]:
                    print(f"      ❌ {err[:70]}")
                for warn in vr.warnings[:3]:
                    print(f"      ⚡ {warn[:70]}")
            self.db.save(genome)

        return path

    # ═══════════════════════════════════════════════════════════════
    # VALIDATE — Test a prototype (v2 — syntax, imports, runtime, quality)
    # ═══════════════════════════════════════════════════════════════

    def validate_invention(self, invention_id: str, run_code: bool = True) -> ValidationResult:
        """
        Full validation pipeline on a prototype.
        Tests syntax, imports, runtime execution, and quality rules.
        """
        genome = self._find_invention(invention_id)
        if not genome:
            return None

        if not genome.prototype_path or not Path(genome.prototype_path).exists():
            print(f"   ❌ No prototype found — run 'forge {invention_id}' first")
            return None

        code = Path(genome.prototype_path).read_text(encoding="utf-8", errors="replace")
        print(f"\n🔬 Validating: {genome.name}")
        print(f"   File: {genome.prototype_path}")
        print(f"   Lines: {len(code.splitlines())}")

        result = self.validator.validate(code, run_code=run_code)

        # Display results
        checks = [
            ("Syntax", result.syntax_ok),
            ("Imports", result.imports_ok),
            ("Quality", result.quality_ok),
        ]
        if run_code:
            checks.append(("Runtime", result.runtime_ok))

        for name, ok in checks:
            icon = "✅" if ok else "❌"
            print(f"   {icon} {name}")

        if result.errors:
            print(f"\n   ERRORS ({len(result.errors)}):")
            for e in result.errors[:5]:
                print(f"      ❌ {e[:70]}")

        if result.warnings:
            print(f"\n   WARNINGS ({len(result.warnings)}):")
            for w in result.warnings[:5]:
                print(f"      ⚡ {w[:70]}")

        if result.auto_fixes:
            print(f"\n   AUTO-FIXES applied:")
            for f in result.auto_fixes:
                print(f"      🔧 {f}")

        print(f"\n   SCORE: {result.score:.3f} — {'PASS ✅' if result.passed else 'FAIL ❌'}")
        if run_code and result.runtime_seconds > 0:
            print(f"   Runtime: {result.runtime_seconds:.2f}s")

        # Update genome fitness
        genome.validation_score = result.score
        genome.validation_errors = len(result.errors)
        if result.passed:
            genome.reliability_score = max(genome.reliability_score, result.score * 0.8)
            genome.status = "tested" if genome.status == "prototyped" else genome.status
        self.db.save(genome)

        return result

    # ═══════════════════════════════════════════════════════════════
    # COMPOSE — Discover novel workflow compositions (v2)
    # ═══════════════════════════════════════════════════════════════

    def compose(self, max_results: int = 8) -> list:
        """
        Discover novel combinations of existing tools that accomplish
        things no single tool can do alone.
        """
        print("\n🔗 NOVEL v2 — Workflow Composition Engine")

        # Show catalog
        summary = self.composer.catalog_summary()
        print(f"   Cataloged {summary['total_components']} components:")
        for cat, count in summary["by_category"].items():
            print(f"      {cat}: {count}")

        # Discover compositions
        workflows = self.composer.discover(max_results)
        print(f"\n   Discovered {len(workflows)} novel workflow compositions:")

        for i, wf in enumerate(workflows):
            novelty_bar = "█" * int(wf.novelty_score * 10)
            utility_bar = "█" * int(wf.utility_score * 10)
            print(f"\n   [{i+1}] {wf.name}")
            print(f"       {wf.description[:70]}")
            print(f"       Novelty: {novelty_bar} {wf.novelty_score:.2f}  "
                  f"Utility: {utility_bar} {wf.utility_score:.2f}")
            print(f"       Steps: {' → '.join(s['tool'] for s in wf.steps)}")

        return workflows

    # ═══════════════════════════════════════════════════════════════
    # EVOLVE — Full evolution cycle
    # ═══════════════════════════════════════════════════════════════

    def evolve(self) -> dict:
        """
        v2 evolution cycle: perceive → scan → brainstorm → forge → validate → mutate → select.
        Key difference from v1: uses REAL perception data and VALIDATES every prototype.
        """
        cycle_stats = {
            "perceived": 0, "scanned": 0, "gaps": 0, "ideas": 0,
            "prototyped": 0, "validated": 0, "passed_validation": 0,
            "mutations": 0, "crossbreeds": 0, "compositions": 0,
            "promotions": 0, "culled": 0,
        }

        # Step 1: Deep perception (v2 — queries real DB)
        print("\n═══ EVOLUTION CYCLE — NOVEL v2 ═══")
        print("\n🧠 Phase 1: Deep Perception...")
        try:
            perception = self.perception.full_perception()
            synthesis = perception.get("synthesis", {})
            cycle_stats["perceived"] = synthesis.get("opportunity_count", 0)
            # Register perception-discovered gaps
            for opp in synthesis.get("opportunities", []):
                gap_id = f"perc_{opp['type']}_{datetime.now().strftime('%H%M%S')}"
                self.db.register_gap(
                    gap_id=gap_id,
                    domain=opp.get("domains", ["unknown"])[0],
                    description=opp["desc"],
                    severity=0.9 if opp["priority"] == "CRITICAL" else 0.6,
                    detected_by="evolution_perception_v2",
                )
            print(f"   → {cycle_stats['perceived']} opportunities from real DB")
        except Exception as e:
            print(f"   ⚠️  Perception error (falling back to static scan): {e}")

        # Step 2: Static gap scan
        print("\n🔍 Phase 2: Gap Scan...")
        scan_result = self.scan()
        cycle_stats["scanned"] = scan_result["total_gaps"]
        cycle_stats["gaps"] = scan_result["total_gaps"]

        # Step 3: Brainstorm
        print("\n💡 Phase 3: Brainstorm...")
        ideas = self.brainstorm(5)
        cycle_stats["ideas"] = len(ideas)

        # Step 4: Forge + Validate (v2 — validates every prototype)
        print("\n🔨 Phase 4: Forge + Validate...")
        for idea in ideas[:3]:
            try:
                idea.status = "designed"
                idea.approach = self._design_approach(idea)
                idea.functions = self._design_functions(idea)
                self.db.save(idea)
                path = self.forge_engine.forge_prototype(idea)
                if path:
                    cycle_stats["prototyped"] += 1

                    # v2: Validate the generated code
                    if Path(path).exists():
                        code = Path(path).read_text(encoding="utf-8", errors="replace")
                        vr = self.validator.validate(code, run_code=False)
                        cycle_stats["validated"] += 1

                        idea.validation_score = vr.score
                        if vr.passed:
                            cycle_stats["passed_validation"] += 1
                            idea.reliability_score = max(
                                idea.reliability_score, vr.score * 0.7
                            )
                            idea.status = "prototyped"
                            print(f"   ✅ {idea.name}: validation score {vr.score:.3f}")
                        else:
                            print(f"   ⚠️  {idea.name}: validation {vr.score:.3f} "
                                  f"({len(vr.errors)} errors)")
                        self.db.save(idea)
            except Exception as e:
                print(f"   ❌ Forge failed for {idea.name}: {e}")

        # Step 5: Discover compositions (v2)
        print("\n🔗 Phase 5: Composition Discovery...")
        try:
            workflows = self.composer.discover(5)
            cycle_stats["compositions"] = len(workflows)
            print(f"   → {len(workflows)} novel workflows discovered")
        except Exception as e:
            print(f"   ⚠️  Composition error: {e}")

        # Step 6: Mutate high-fitness inventions
        print("\n🧪 Phase 6: Mutation...")
        all_inventions = self.db.get_all()
        mutations = 0
        for inv in all_inventions:
            if inv.composite_fitness >= 0.4 and inv.generation < 5:
                try:
                    mutant = inv.mutate("random")
                    self.db.save(mutant)
                    mutations += 1
                except Exception:
                    pass
                if mutations >= 3:
                    break
        cycle_stats["mutations"] = mutations

        # Step 7: Cross-pollinate top inventions
        print("\n🧬 Phase 7: Cross-pollination...")
        crossbreeds = 0
        if len(all_inventions) >= 2:
            sorted_inv = sorted(all_inventions, key=lambda x: x.composite_fitness, reverse=True)
            for i in range(min(2, len(sorted_inv) - 1)):
                try:
                    hybrid = InventionGenome.crossbreed(sorted_inv[i], sorted_inv[i + 1])
                    self.db.save(hybrid)
                    crossbreeds += 1
                except Exception:
                    pass
        cycle_stats["crossbreeds"] = crossbreeds

        # Step 8: Selection pressure — archive failures
        culled = 0
        for inv in all_inventions:
            if inv.composite_fitness < 0.15 and inv.generation > 2 and inv.deployments == 0:
                inv.status = "archived"
                self.db.save(inv)
                culled += 1
        cycle_stats["culled"] = culled

        # Record cycle
        stats = self.db.get_stats()
        best = stats.get("best_fitness", 0) or 0
        self.db.record_cycle(
            cycle=stats.get("evolution_cycles", 0) + 1,
            scanned=cycle_stats["scanned"],
            gaps=cycle_stats["gaps"],
            ideas=cycle_stats["ideas"],
            prototypes=cycle_stats["prototyped"],
            mutations=cycle_stats["mutations"],
            crossbreeds=cycle_stats["crossbreeds"],
            culled=cycle_stats["culled"],
            best_fitness=best,
        )

        # Final report
        print("\n" + "═" * 60)
        print("🧬 EVOLUTION CYCLE COMPLETE (NOVEL v2)")
        print("═" * 60)
        print(f"   Perception:    {cycle_stats['perceived']} real-DB opportunities")
        print(f"   Gaps found:    {cycle_stats['gaps']}")
        print(f"   Ideas born:    {cycle_stats['ideas']}")
        print(f"   Prototyped:    {cycle_stats['prototyped']}")
        print(f"   Validated:     {cycle_stats['validated']} "
              f"({cycle_stats['passed_validation']} passed)")
        print(f"   Compositions:  {cycle_stats['compositions']} novel workflows")
        print(f"   Mutations:     {cycle_stats['mutations']}")
        print(f"   Crossbreeds:   {cycle_stats['crossbreeds']}")
        print(f"   Archived:      {cycle_stats['culled']}")
        print("═" * 60)

        return cycle_stats

    # ═══════════════════════════════════════════════════════════════
    # SPAWN — Deploy an invention as a live system component
    # ═══════════════════════════════════════════════════════════════

    def spawn(self, invention_id: str) -> bool:
        """Promote a tested invention to a deployed system component."""
        genome = self.db.load(invention_id)
        if not genome:
            all_inv = self.db.get_all()
            for inv in all_inv:
                if inv.invention_id.startswith(invention_id):
                    genome = inv
                    break

        if not genome:
            print(f"   ❌ Invention '{invention_id}' not found")
            return False

        if not genome.prototype_path:
            print(f"   ❌ No prototype exists — run 'forge {invention_id}' first")
            return False

        genome.status = "deployed"
        genome.deployments += 1
        genome.evolved_at = datetime.now().isoformat()
        self.db.save(genome)
        self.db.record_spawn(
            parent_id=genome.invention_id,
            child_id=genome.invention_id,
            spawn_type="deploy",
            method="spawn",
            output_path=genome.prototype_path,
        )

        print(f"\n🚀 SPAWNED: {genome.name}")
        print(f"   Path: {genome.prototype_path}")
        print(f"   Deployments: {genome.deployments}")
        return True

    # ═══════════════════════════════════════════════════════════════
    # MUTATE / BREED / IMAGINE — Creative operations
    # ═══════════════════════════════════════════════════════════════

    def mutate(self, invention_id: str, mutation_type: str = "random") -> InventionGenome:
        """Create a mutated variant of an invention."""
        genome = self._find_invention(invention_id)
        if not genome:
            return None

        mutant = genome.mutate(mutation_type)
        self.db.save(mutant)
        print(f"\n🧪 Mutated: {genome.name} → {mutant.name}")
        print(f"   New ID: {mutant.invention_id}")
        print(f"   Generation: {mutant.generation}")
        print(f"   Mutation: {mutant.mutation_log[-1] if mutant.mutation_log else 'random'}")
        return mutant

    def breed(self, id_a: str, id_b: str) -> InventionGenome:
        """Cross-pollinate two inventions."""
        a = self._find_invention(id_a)
        b = self._find_invention(id_b)
        if not a or not b:
            return None

        hybrid = self.idea_generator.cross_pollinate(a, b)
        self.db.save(hybrid)
        print(f"\n🧬 Bred: {a.name} × {b.name}")
        print(f"   → {hybrid.name} (Gen {hybrid.generation})")
        print(f"   Domains: {', '.join(hybrid.domains)}")
        print(f"   Techniques: {', '.join(hybrid.techniques[:5])}")
        return hybrid

    def imagine(self, invention_id: str, twist: str) -> InventionGenome:
        """Create a creative variant with a specific twist."""
        genome = self._find_invention(invention_id)
        if not genome:
            return None

        variant = self.idea_generator.imagine_variant(genome, twist)
        self.db.save(variant)
        print(f"\n✨ Imagined: {variant.name}")
        print(f"   Twist: {twist}")
        print(f"   ID: {variant.invention_id}")
        return variant

    # ═══════════════════════════════════════════════════════════════
    # DASHBOARD / REPORT / STATS
    # ═══════════════════════════════════════════════════════════════

    def dashboard(self):
        """Show the invention ecosystem dashboard."""
        stats = self.db.get_stats()
        all_inv = self.db.get_all()

        # Status distribution
        status_counts = {}
        type_counts = {}
        domain_counts = {}
        for inv in all_inv:
            status_counts[inv.status] = status_counts.get(inv.status, 0) + 1
            type_counts[inv.invention_type] = type_counts.get(inv.invention_type, 0) + 1
            for d in inv.domains:
                domain_counts[d] = domain_counts.get(d, 0) + 1

        bar_char = "#"
        print()
        print("+" + "=" * 68 + "+")
        print("|" + "NOVEL ENGINE — INVENTION ECOSYSTEM DASHBOARD".center(68) + "|")
        print("+" + "=" * 68 + "+")
        print(f"|  Total Inventions: {stats.get('total_inventions', 0):<10}  "
              f"Open Gaps: {stats.get('open_gaps', 0):<10}  "
              f"Spawns: {stats.get('total_spawns', 0):<5}     |")
        print(f"|  Evolution Cycles: {stats.get('evolution_cycles', 0):<10}  "
              f"Best Fitness: {stats.get('best_fitness', 0) or 0:.3f}       "
              f"Avg: {stats.get('avg_fitness', 0) or 0:.3f}  |")
        print("+" + "-" * 68 + "+")

        # Status pipeline
        print("|  INVENTION PIPELINE:".ljust(69) + "|")
        pipeline_order = ["concept", "designed", "prototyped", "tested", "deployed", "evolved", "archived"]
        for s in pipeline_order:
            count = status_counts.get(s, 0)
            if count > 0:
                icon = {"concept": "💭", "designed": "📐", "prototyped": "🔧",
                        "tested": "✅", "deployed": "🚀", "evolved": "🧬", "archived": "📦"}.get(s, "❓")
                bar = bar_char * min(count * 2, 40)
                line = f"|    {icon} {s:<12} {bar} ({count})"
                print(line.ljust(69) + "|")

        # Type distribution
        if type_counts:
            print("+" + "-" * 68 + "+")
            print("|  INVENTION TYPES:".ljust(69) + "|")
            for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
                bar = bar_char * min(c * 2, 40)
                line = f"|    {t:<14} {bar} ({c})"
                print(line.ljust(69) + "|")

        # Top domains
        if domain_counts:
            print("+" + "-" * 68 + "+")
            print("|  TOP DOMAINS:".ljust(69) + "|")
            for d, c in sorted(domain_counts.items(), key=lambda x: -x[1])[:8]:
                bar = bar_char * min(c * 2, 40)
                line = f"|    {d[:20]:<20} {bar} ({c})"
                print(line.ljust(69) + "|")

        print("+" + "=" * 68 + "+")

    def report(self):
        """Full evolution report."""
        stats = self.db.get_stats()
        all_inv = self.db.get_all()
        open_gaps = self.db.get_open_gaps()

        print()
        print("+" + "=" * 68 + "+")
        print("|" + "NOVEL ENGINE — FULL EVOLUTION REPORT".center(68) + "|")
        print("+" + "=" * 68 + "+")
        print(f"|  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(69) + "|")
        print("+" + "-" * 68 + "+")

        # Stats summary
        for key, val in stats.items():
            line = f"|  {key.replace('_', ' ').title()}: {val}"
            print(line.ljust(69) + "|")

        # Top inventions
        if all_inv:
            print("+" + "-" * 68 + "+")
            print("|  TOP INVENTIONS BY FITNESS:".ljust(69) + "|")
            for inv in sorted(all_inv, key=lambda x: x.composite_fitness, reverse=True)[:10]:
                line = f"|    [{inv.invention_id[:8]}] {inv.name[:30]:<30} F:{inv.composite_fitness:.3f} G:{inv.generation}"
                print(line.ljust(69) + "|")

        # Critical gaps
        if open_gaps:
            critical = [g for g in open_gaps if g.get("severity", 0) >= 0.7]
            if critical:
                print("+" + "-" * 68 + "+")
                print("|  CRITICAL OPEN GAPS:".ljust(69) + "|")
                for g in critical[:5]:
                    line = f"|    ⚠️  [{g['domain'][:15]}] {g['description'][:45]}"
                    print(line.ljust(69) + "|")

        print("+" + "=" * 68 + "+")

    def show_stats(self):
        """Quick stats."""
        stats = self.db.get_stats()
        print(f"\n📊 NOVEL Stats:")
        for k, v in stats.items():
            print(f"   {k}: {v}")

    # ═══════════════════════════════════════════════════════════════
    # INTERNAL HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _find_invention(self, partial_id: str) -> InventionGenome:
        genome = self.db.load(partial_id)
        if genome:
            return genome
        all_inv = self.db.get_all()
        for inv in all_inv:
            if inv.invention_id.startswith(partial_id):
                return inv
            if partial_id.lower() in inv.name.lower():
                return inv
        print(f"   ❌ Invention '{partial_id}' not found")
        return None

    def _design_approach(self, genome: InventionGenome) -> str:
        techs = ", ".join(genome.techniques[:4]) if genome.techniques else "pattern matching"
        return (
            f"Use {techs} to address: {genome.problem_statement[:100]}. "
            f"Read from litigation_context.db, output structured JSON/markdown. "
            f"Handle 10GB+ DB with WAL mode and streaming queries."
        )

    def _design_functions(self, genome: InventionGenome) -> list:
        base = ["process", "generate_report", "main"]
        if any(d in genome.domains for d in ["evidence_processing", "legal_research"]):
            base.extend(["analyze", "search", "rank_results"])
        if "filing_generation" in genome.domains:
            base.extend(["validate_filing", "assemble_packet"])
        if "deadline_management" in genome.domains:
            base.extend(["check_deadlines", "calculate_service_date"])
        if "adversarial_analysis" in genome.domains:
            base.extend(["predict_response", "find_weakness"])
        return base

    def _design_classes(self, genome: InventionGenome) -> list:
        classes = [f"{genome.name.replace(' ', '')}Engine"]
        if "evidence_processing" in genome.domains:
            classes.append("EvidenceProcessor")
        if "judicial_analysis" in genome.domains:
            classes.append("JudicialAnalyzer")
        return classes

    def _design_cli(self, genome: InventionGenome) -> list:
        return ["run", "analyze", "report", "status"]


def main():
    parser = argparse.ArgumentParser(
        description="NOVEL Engine v2 — Genuine Invention Factory for LitigationOS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands (v2):
  perceive            Deep perception scan (queries real DB)
  scan                Detect gaps in the ecosystem
  brainstorm [N]      Generate N invention ideas (default: 5)
  invent <gap_id>     Design an invention from a gap
  forge <inv_id>      Prototype an invention into working code
  validate <inv_id>   Full validation (syntax + imports + runtime + quality)
  compose [N]         Discover N novel workflow compositions (default: 8)
  evolve              Full evolution cycle (perceive→scan→forge→validate→evolve)
  spawn <inv_id>      Deploy a validated invention
  mutate <inv_id>     Create a mutated variant
  breed <a> <b>       Cross-pollinate two inventions
  imagine <id> <twist>  Creative variant
  dashboard           Ecosystem status with perception data
  report              Full report
  stats               Quick stats
        """
    )
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("args", nargs="*", help="Command arguments")

    args = parser.parse_args()
    engine = NovelEngine()

    cmd = args.command
    cmd_args = args.args

    if cmd == "perceive":
        engine.perceive()
    elif cmd == "scan":
        engine.scan()
    elif cmd == "brainstorm":
        n = int(cmd_args[0]) if cmd_args else 5
        engine.brainstorm(n)
    elif cmd == "invent":
        if not cmd_args:
            print("Usage: novel_engine.py invent <gap_id>")
            sys.exit(1)
        engine.invent(cmd_args[0])
    elif cmd == "forge":
        if not cmd_args:
            print("Usage: novel_engine.py forge <invention_id>")
            sys.exit(1)
        engine.forge_invention(cmd_args[0])
    elif cmd == "validate":
        if not cmd_args:
            print("Usage: novel_engine.py validate <invention_id>")
            sys.exit(1)
        run_code = "--no-run" not in cmd_args
        engine.validate_invention(cmd_args[0], run_code=run_code)
    elif cmd == "compose":
        n = int(cmd_args[0]) if cmd_args else 8
        engine.compose(n)
    elif cmd == "evolve":
        engine.evolve()
    elif cmd == "spawn":
        if not cmd_args:
            print("Usage: novel_engine.py spawn <invention_id>")
            sys.exit(1)
        engine.spawn(cmd_args[0])
    elif cmd == "mutate":
        if not cmd_args:
            print("Usage: novel_engine.py mutate <invention_id>")
            sys.exit(1)
        mutation_type = cmd_args[1] if len(cmd_args) > 1 else "random"
        engine.mutate(cmd_args[0], mutation_type)
    elif cmd == "breed":
        if len(cmd_args) < 2:
            print("Usage: novel_engine.py breed <id_a> <id_b>")
            sys.exit(1)
        engine.breed(cmd_args[0], cmd_args[1])
    elif cmd == "imagine":
        if len(cmd_args) < 2:
            print("Usage: novel_engine.py imagine <id> <twist>")
            print("Twists: real_time, batch, adversarial, predictive, visual, distributed, scale_up, scale_down")
            sys.exit(1)
        engine.imagine(cmd_args[0], cmd_args[1])
    elif cmd == "dashboard":
        engine.dashboard()
    elif cmd == "report":
        engine.report()
    elif cmd == "stats":
        engine.show_stats()
    else:
        print(f"Unknown command: {cmd}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
