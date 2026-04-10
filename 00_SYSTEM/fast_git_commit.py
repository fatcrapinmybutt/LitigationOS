"""Fast git commit — targeted add + commit for daemon files only."""
import subprocess, os, sys

os.chdir(r"C:\Users\andre\LitigationOS")
env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}

def run(args, timeout=120):
    print(f"$ git {' '.join(args)}")
    r = subprocess.run(["git", "--no-pager", "--no-optional-locks"] + args,
                       capture_output=True, text=True, timeout=timeout, env=env)
    if r.stdout.strip():
        print(r.stdout.strip()[:500])
    if r.stderr.strip():
        print(f"  stderr: {r.stderr.strip()[:300]}")
    return r.returncode

# Kill fsmonitor if running
subprocess.run(["git", "config", "--local", "core.fsmonitor", "false"],
               capture_output=True, env=env)
subprocess.run(["git", "config", "--local", "core.untrackedCache", "false"],
               capture_output=True, env=env)

# Stage only the 2 daemon files
rc = run(["add", ".github/extensions/singularity/nexus_daemon.py",
          "scripts/nexus_daemon.py"])
if rc != 0:
    print("ADD failed")
    sys.exit(1)

# Commit
msg = """NEXUS daemon v3: absorb 13 MCP capabilities — 46→64 handlers

Added:
- CircuitBreaker (CLOSED→OPEN after 5 failures, 60s auto-reset)
- HealthStatus singleton + health action
- ErrorCode enum with 6 codes + recovery hints
- Path validation with 7-drive safe roots
- Error telemetry (record_error, get_error_summary)
- Disk space monitoring (check_disk_space)
- System scan (scan_all_systems — composite diagnostics)
- Evolution pipeline (evolve_md, evolve_txt, evolve_pages)
- Document lifecycle (document_exists, hash_exists, delete_document, insert_document)
- Fleet dispatch (dispatch_to_swarm — agent routing)

Infrastructure: 2,325→3,224 lines, 46→64 registered handlers
Backup synced to scripts/nexus_daemon.py

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"""

rc = run(["commit", "-m", msg])
if rc != 0:
    print("COMMIT failed or nothing to commit")
    sys.exit(1)

print("\n[OK] Commit succeeded")
run(["log", "--oneline", "-3"])
