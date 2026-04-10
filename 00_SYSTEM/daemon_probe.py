"""Probe nexus_daemon.py directly — send JSON-RPC requests, capture raw responses."""
import subprocess, json, sys, time, os

daemon_path = r"C:\Users\andre\LitigationOS\.github\extensions\singularity\nexus_daemon.py"
python_exe = sys.executable

# Start daemon subprocess
env = os.environ.copy()
env["PYTHONUTF8"] = "1"
proc = subprocess.Popen(
    [python_exe, "-I", daemon_path],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"C:\Users\andre\LitigationOS",
    env=env,
    text=True,
    bufsize=1,
)

# Read startup signal
startup = proc.stdout.readline().strip()
print(f"STARTUP: {startup}")
startup_data = json.loads(startup)
if not startup_data.get("ok"):
    print("DAEMON FAILED TO START!")
    sys.exit(1)

# Test actions
test_actions = [
    {"action": "case_health", "id": "probe-1"},
    {"action": "adversary_threats", "id": "probe-2"},
    {"action": "filing_pipeline", "id": "probe-3"},
    {"action": "evolution_stats", "id": "probe-4"},
    {"action": "convergence_status", "id": "probe-5"},
    {"action": "self_test", "id": "probe-6"},
    {"action": "system_health", "id": "probe-7"},
    {"action": "self_audit", "id": "probe-8"},
    {"action": "stats_extended", "id": "probe-9"},
]

for req in test_actions:
    try:
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        resp_line = proc.stdout.readline().strip()
        resp = json.loads(resp_line)
        
        # Check what keys are present
        keys = set(resp.keys())
        data_keys = keys - {"ok", "id"}
        
        status = "✅ HAS DATA" if data_keys else "❌ EMPTY (only ok+id)"
        print(f"\n{req['action']}: {status}")
        print(f"  Keys: {sorted(keys)}")
        if data_keys:
            for k in sorted(data_keys):
                val = resp[k]
                if isinstance(val, dict):
                    print(f"  {k}: dict with {len(val)} keys")
                elif isinstance(val, list):
                    print(f"  {k}: list with {len(val)} items")
                elif isinstance(val, str) and len(val) > 100:
                    print(f"  {k}: str({len(val)} chars)")
                else:
                    print(f"  {k}: {val}")
        else:
            print(f"  RAW: {resp_line[:500]}")
    except Exception as e:
        print(f"\n{req['action']}: ⚠️ ERROR: {e}")

# Read stderr for any error messages
proc.stdin.close()
time.sleep(1)
stderr = proc.stderr.read()
if stderr:
    print(f"\n--- STDERR ---")
    for line in stderr.strip().split("\n")[-20:]:
        print(f"  {line}")

proc.terminate()
print("\nDone.")
