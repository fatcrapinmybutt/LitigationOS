import time
import sys

# Change to pipeline directory
import os
os.chdir(r'C:\Users\andre\LitigationOS\00_SYSTEM\pipeline')
sys.path.insert(0, r'C:\Users\andre\LitigationOS\00_SYSTEM\pipeline')

# Test config import speed
t=time.time()
import config
config_time = time.time()-t

# Test intake_router import
t=time.time()
import intake_router
router_time = time.time()-t

# Test that pipeline module loads
t=time.time()
import run_omega_pipeline
list_time = time.time()-t

print(f'config.py import:        {config_time:.3f}s')
print(f'intake_router.py import: {router_time:.3f}s')
print(f'run_omega_pipeline load: {list_time:.3f}s')

# Verify lane detection in intake_router
for lane in ('A','B','C','D','E','F'):
    reg = config.LANE_REGISTRY.get(lane, {})
    name = reg.get("name","MISSING")
    meek = reg.get("meek","none")
    print(f'  Lane {lane}: {name} (MEEK={meek})')

total = config_time+router_time+list_time
print(f'Total import time: {total:.3f}s')
if total < 3:
    print('FAST IMPORTS: PASS')
else:
    print('SLOW IMPORTS: FAIL')
