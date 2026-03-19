import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Redirect output to file to ensure we capture it
outfile = open("_test_v2_output.txt", "w", encoding="utf-8")

def log(msg):
    print(msg, flush=True)
    outfile.write(msg + "\n")
    outfile.flush()

log("step1: cwd=" + os.getcwd())

try:
    log("step2: importing opinion_parser...")
    from legal_ai.opinion_parser import OpinionParser
    log("step3: opinion_parser imported OK")
except Exception as e:
    log(f"step2-FAIL: {e}")

try:
    log("step4: creating OpinionParser (no deps)...")
    p = OpinionParser(use_citation_extractor=False, use_entity_extractor=False)
    log("step5: OpinionParser created OK")
    log(f"stats: {p.get_stats()}")
except Exception as e:
    log(f"step4-FAIL: {e}")

try:
    log("step6: testing parse...")
    result = p.parse("IT IS HEREBY ORDERED that the motion is denied without hearing.")
    log(f"step7: parse OK - type={result.order_type}, defects={len(result.procedural_defects)}")
except Exception as e:
    log(f"step6-FAIL: {e}")

try:
    log("step8: importing brain_evolver...")
    from legal_ai.brain_evolver import BrainEvolver
    log("step9: brain_evolver imported OK")
except Exception as e:
    log(f"step8-FAIL: {e}")

try:
    log("step10: creating BrainEvolver...")
    e = BrainEvolver(auto_execute=False)
    log("step11: BrainEvolver created OK")
    log(f"stats: {e.get_stats()}")
except Exception as e:
    log(f"step10-FAIL: {e}")

log("ALL DONE")
outfile.close()
