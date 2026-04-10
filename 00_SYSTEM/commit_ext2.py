"""Commit extension.mjs with fsmonitor disabled for speed."""
import subprocess, os
os.chdir(r"C:\Users\andre\LitigationOS")
env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}

def run(args, timeout=180):
    cmd = ["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
           "--no-pager", "--no-optional-locks"] + args
    print(f"$ {' '.join(cmd[:6])} ... {' '.join(args[:3])}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    if r.stdout.strip(): print(r.stdout.strip()[:500])
    if r.stderr.strip(): print(f"  stderr: {r.stderr.strip()[:300]}")
    return r.returncode

# Stage just the one file
run(["add", ".github/extensions/singularity/extension.mjs"])

# Short commit message to avoid shell escaping issues
msg = ("extension.mjs: wire 13 new NEXUS v3 tools (46->59 total)\n\n"
       "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>")

rc = run(["commit", "-m", msg])
if rc != 0:
    print("Commit may have already succeeded from prior attempt, checking log...")

run(["log", "--oneline", "-3"])
