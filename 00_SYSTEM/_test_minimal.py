import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("step1: cwd=" + os.getcwd(), flush=True)

print("step2: importing opinion_parser module...", flush=True)
import legal_ai.opinion_parser as op_mod
print("step3: opinion_parser module imported", flush=True)

print("step4: creating OpinionParser (no deps)...", flush=True)
p = op_mod.OpinionParser(use_citation_extractor=False, use_entity_extractor=False)
print("step5: OpinionParser created", flush=True)
print("stats:", p.get_stats(), flush=True)

print("step6: importing brain_evolver module...", flush=True)
import legal_ai.brain_evolver as be_mod
print("step7: brain_evolver module imported", flush=True)

print("step8: creating BrainEvolver...", flush=True)
e = be_mod.BrainEvolver(auto_execute=False)
print("step9: BrainEvolver created", flush=True)
print("stats:", e.get_stats(), flush=True)

print("ALL OK", flush=True)
