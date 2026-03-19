import sys
sys.path.insert(0, r'C:\Users\andre\LitigationOS\00_SYSTEM\pipeline')
import time
t = time.time()
import config
print(f'config import: {time.time()-t:.3f}s')
from local_ai_engine import LocalAI
ai = LocalAI()
r = ai.detect_lane('PPO violation MCL 600.2950')
print(f'Lane D detect: {r["lane"]} ({r["confidence"]:.0%})')
