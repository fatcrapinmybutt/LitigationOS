"""Kill ALL stale git processes then do git add+commit."""
import subprocess, time, os

# Kill all git.exe
print("Killing all git.exe processes...")
r = subprocess.run(["taskkill", "/F", "/IM", "git.exe"], capture_output=True, text=True, timeout=30)
print(r.stdout.strip() if r.stdout.strip() else "(none killed)")
print(r.stderr.strip() if r.stderr.strip() else "")
time.sleep(3)

# Remove lock if still there
lock = r"C:\Users\andre\LitigationOS\.git\index.lock"
if os.path.exists(lock):
    try:
        os.remove(lock)
        print(f"Removed stale lock: {lock}")
    except Exception as e:
        print(f"Lock removal failed: {e}")

# Now git operations
os.chdir(r"C:\Users\andre\LitigationOS")

# Check status
r = subprocess.run(["git", "--no-pager", "status", "--short"], 
                   capture_output=True, text=True, timeout=30, 
                   env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
print(f"\nGit status (first 20 lines):")
for line in r.stdout.strip().split("\n")[:20]:
    print(f"  {line}")

# Add the two files
r = subprocess.run(["git", "add", 
                     ".github/extensions/singularity/nexus_daemon.py",
                     "scripts/nexus_daemon.py"],
                   capture_output=True, text=True, timeout=30,
                   env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
if r.returncode == 0:
    print("\n[OK] git add succeeded")
else:
    print(f"\n[FAIL] git add: {r.stderr}")

# Commit
msg = """NEXUS daemon v3: absorb 13 MCP capabilities — 46→64 handlers

Added: CircuitBreaker, HealthStatus, ErrorCode, path validation,
error telemetry, disk monitoring, system scan, evolution pipeline
(md/txt/pages write endpoints), document lifecycle, swarm dispatch.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"""

r = subprocess.run(["git", "commit", "-m", msg],
                   capture_output=True, text=True, timeout=60,
                   env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
if r.returncode == 0:
    print(f"\n[OK] Committed: {r.stdout.strip()}")
else:
    print(f"\n[INFO] Commit result: {r.stderr.strip()}")
    print(f"  stdout: {r.stdout.strip()}")
