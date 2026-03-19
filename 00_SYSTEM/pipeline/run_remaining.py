import sys, time, traceback
sys.path.insert(0, '.')
from litigationos_boot import LitigationOSOrchestrator

orch = LitigationOSOrchestrator()
orch.discovery.detect_all_drives()
orch.discovery.scan_for_litigos_variants()
orch.discovery.load_previous_runs()

phases = ['5-CASEINT', '6-WARFARE', '7-CONVERGE', '8-PRODUCE', '9-VALIDATE']
for p in phases:
    print()
    print('=' * 60)
    print('  PHASE: %s' % p)
    print('=' * 60)
    sys.stdout.flush()
    t0 = time.time()
    try:
        orch._run_phase(p)
        elapsed = time.time() - t0
        print('  Phase %s done in %.0fs' % (p, elapsed))
    except Exception as e:
        elapsed = time.time() - t0
        print('  Phase %s FAILED after %.0fs: %s' % (p, elapsed, e))
        traceback.print_exc()
    sys.stdout.flush()

print()
print('=== ALL REMAINING PHASES COMPLETE ===')
