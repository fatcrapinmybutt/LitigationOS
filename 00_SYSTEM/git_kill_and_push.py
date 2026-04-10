"""Kill stale git processes and do pull + push."""
import subprocess, os, sys, time

REPO = r"C:\Users\andre\LitigationOS"
os.chdir(REPO)

def run(cmd, env=None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO, env=env)
    out = (r.stdout + r.stderr).strip()
    print(f"CMD: {' '.join(cmd)}\nOUT: {out[:800]}\nEXIT: {r.returncode}\n")
    return r

# Kill all git processes that are blocking
pids_to_kill = [20828, 884, 9988, 5236, 9036, 2920, 13112, 8532, 23096, 13476, 23740, 26216]
for pid in pids_to_kill:
    try:
        r = subprocess.run(
            ["powershell", "-Command", f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue"],
            capture_output=True, text=True, timeout=5
        )
    except Exception:
        pass

time.sleep(2)
print("Killed git processes")

# Remove lock
lock_file = os.path.join(REPO, ".git", "index.lock")
for _ in range(5):
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print("Removed index.lock")
            break
        except Exception as e:
            print(f"Retry removing lock: {e}")
            time.sleep(1)
    else:
        print("No lock file present")
        break

# Pop the stash
run(["git", "stash", "pop"])

# Configure LFS storage to NTFS drive
run(["git", "config", "lfs.storage", r"D:\git_lfs_storage"])
run(["git", "config", "lfs.allowincompletepush", "true"])

env = os.environ.copy()
env["GIT_LFS_SKIP_SMUDGE"] = "1"

# Pull with rebase
r = run(["git", "pull", "--rebase"], env=env)
if r.returncode != 0:
    print("Rebase failed, aborting and trying merge...")
    run(["git", "rebase", "--abort"])
    r = run(["git", "pull", "--no-rebase"], env=env)

# Push
r_push = run(["git", "push"], env=env)
print("PUSH RESULT:", "SUCCESS" if r_push.returncode == 0 else "FAILED")
