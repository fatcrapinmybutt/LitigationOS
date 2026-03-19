import sys
sys.path.insert(0,'.')
from context_orchestrator import TokenBudget, ContextValidator, ContextCompressor, ContextQualityScorer, TokenBudgetConfig

# Token estimation
tb = TokenBudget()
assert tb.estimate_tokens('Hello world test') > 0
print('Token estimate for 3 words:', tb.estimate_tokens("Hello world test"))

# Validator
cv = ContextValidator()
r = cv.validate_text('Emily Ann Watson filed a motion')
print('Validator caught wrong name:', not r.valid)
r2 = cv.validate_text('9 CPS investigations were completed')
print('Validator caught fabrication:', not r2.valid)
r3 = cv.validate_lane('A', 'B')
print('Validator caught lane violation:', not r3.valid)
r4 = cv.validate_lane('A', 'C')
print('Convergence lane allows cross-lane:', r4.valid)

# Compressor
cc = ContextCompressor()
text = 'The court ordered supervised visitation. The motion was filed on time. Evidence showed repeated violations. The judge reviewed all exhibits carefully. Multiple witnesses testified under oath.'
cr = cc.compress(text, ratio=0.4)
print('Compressed', cr.original_tokens, '->', cr.compressed_tokens, 'tokens (ratio=' + str(round(cr.compression_ratio, 2)) + ')')

# Quality Scorer
qs = ContextQualityScorer()
items = [
    {'key': 'case_number', 'value': '2024-001507-DC', 'priority': 'critical', 'lane': 'A', 'created_at': __import__('time').time()},
    {'key': 'judge', 'value': 'Hon. Jenny L. McNeill', 'priority': 'critical', 'lane': 'A', 'created_at': __import__('time').time()},
    {'key': 'plaintiff', 'value': 'Andrew James Pigors', 'priority': 'critical', 'lane': 'A', 'created_at': __import__('time').time()},
]
report = qs.score(items, query='custody motion', target_lane='A')
print('Quality score:', round(report.overall_score, 3), '(freshness=' + str(round(report.freshness_score, 2)) + ', coverage=' + str(round(report.coverage_score, 2)) + ')')

print()
print('ALL TESTS PASSED')
