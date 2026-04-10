"""Check git state and complete push."""
import subprocess, os, time

REPO = r"C:\Users\andre\LitigationOS"

def run(cmd, env=None, timeout=60):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO, env=env, timeout=timeout)
    out = (r.stdout + r.stderr).strip()[:800]
    print(f"$ {' '.join(cmd)}\n{out}\n[exit {r.returncode}]\n")
    return r

# Remove any leftover locks
for lockf in [r".git\index.lock", r".git\MERGE_HEAD", r".git\rebase-merge"]:
    full = os.path.join(REPO, lockf)
    if os.path.exists(full):
        try:
            if os.path.isdir(full):
                import shutil
                shutil.rmtree(full)
            else:
                os.remove(full)
            print(f"Removed: {lockf}")
        except Exception as e:
            print(f"Cannot remove {lockf}: {e}")

time.sleep(1)

# Check status
run(["git", "stash", "list"])
run(["git", "status", "--short"])
run(["git", "log", "--oneline", "-3"])
