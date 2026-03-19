import time
t=time.time()
from local_ai_engine import LocalAI
ai = LocalAI()
print(f'LocalAI loaded in {time.time()-t:.2f}s')
print(f'Engine: {ai.name}')
print(f'Online: {ai.is_online}')

# Test all 6 lanes
tests = [
    ('Watson custody case 2024-001507-DC Judge McNeill parenting time', 'A'),
    ('Shady Oaks habitability mold case 2025-002760-CZ Judge Hoopes', 'B'),
    ('Muskegon County 14th Circuit 42 USC 1983 Monell liability', 'C'),
    ('PPO violation personal protection order MCL 600.2950 contempt no contact', 'D'),
    ('JTC judicial misconduct disqualification MCR 2.003 bias canon ex parte', 'E'),
    ('leave to appeal COA MCR 7.205 standard of review abuse of discretion', 'F'),
]
for text, expected in tests:
    r = ai.detect_lane(text)
    ok = 'PASS' if r['lane'] == expected else 'FAIL'
    print(f'{ok}: expected={expected} got={r["lane"]} conf={r["confidence"]:.0%}')

# Test classify
r = ai.classify_document('Motion to Modify Parenting Time filed under MCR 3.210')
print(f'Classify: {r["category"]} ({r["confidence"]:.0%})')
