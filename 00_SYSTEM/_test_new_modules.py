import sys
import os

# Force UTF-8
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# Ensure we're NOT in the repo root (shadow modules)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("CWD:", os.getcwd())
print("Testing opinion_parser import...")
try:
    from legal_ai.opinion_parser import OpinionParser, ParsedOpinion, OrderSection, ProceduralDefect
    print("  opinion_parser import OK")
except Exception as e:
    print(f"  opinion_parser FAILED: {e}")
    import traceback
    traceback.print_exc()

print("Testing brain_evolver import...")
try:
    from legal_ai.brain_evolver import BrainEvolver, BrainHealthScore, EvolutionReport
    print("  brain_evolver import OK")
except Exception as e:
    print(f"  brain_evolver FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting OpinionParser instantiation (no deps)...")
try:
    parser = OpinionParser(use_citation_extractor=False, use_entity_extractor=False)
    stats = parser.get_stats()
    print(f"  OpinionParser OK: {stats}")
except Exception as e:
    print(f"  OpinionParser instantiation FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting OpinionParser.parse()...")
try:
    sample = """STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON
FAMILY DIVISION

Case No. 2024-001507-DC

IT IS HEREBY ORDERED that the defendant's parenting time is suspended
without hearing and without notice to the defendant.

Dated: January 15, 2025
Hon. Annette Smedley
"""
    result = parser.parse(sample)
    print(f"  order_type={result.order_type}")
    print(f"  is_ex_parte={result.is_ex_parte}")
    print(f"  sections={len(result.sections)}")
    print(f"  defects={len(result.procedural_defects)}")
    for d in result.procedural_defects:
        print(f"    [{d.severity}] {d.defect_type}: {d.description[:80]}")
    print(f"  case_number={result.case_number}")
    print(f"  judge={result.judge}")
    print(f"  parse_time_ms={result.parse_time_ms:.1f}")
    print("  parse OK")
except Exception as e:
    print(f"  parse FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting BrainEvolver instantiation...")
try:
    evolver = BrainEvolver(auto_execute=False)
    stats = evolver.get_stats()
    print(f"  BrainEvolver OK: available_brains={stats['available_brains']}/{stats['known_brains']}")
    print(f"  brain_dir_exists={stats['brain_dir_exists']}")
    print(f"  available: {stats['available_brain_names']}")
except Exception as e:
    print(f"  BrainEvolver instantiation FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting BrainEvolver.assess_health()...")
try:
    scores = evolver.assess_health()
    for s in scores:
        print(f"  {s.brain_name}: score={s.health_score:.0%} tables={s.total_tables} rows={s.total_rows}")
        if s.issues:
            for issue in s.issues:
                print(f"    ! {issue}")
except Exception as e:
    print(f"  assess_health FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nAll tests complete.")
