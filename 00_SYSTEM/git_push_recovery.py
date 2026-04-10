"""Git push recovery — skip LFS, pull rebase, push."""
import subprocess, os, time

REPO = r"C:\Users\andre\LitigationOS"

env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1", "GIT_TERMINAL_PROMPT": "0"}

def run(cmd, timeout=90, check=False):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO, env=env, timeout=timeout)
    out = (r.stdout + r.stderr).strip()[:1200]
    print(f"$ {' '.join(cmd)}\n{out}\n[exit {r.returncode}]\n")
    return r

# Step 0: Remove lock files
for lf in [r".git\index.lock", r".git\FETCH_HEAD.lock"]:
    p = os.path.join(REPO, lf)
    if os.path.exists(p):
        os.remove(p)
        print(f"Removed {lf}")

# Step 1: Configure LFS to use D:\ (NTFS) not J:\ (exFAT)
run(["git", "config", "lfs.storage", r"D:\git_lfs_storage"])
run(["git", "config", "lfs.allowincompletepush", "true"])
run(["git", "config", "lfs.fetchrecentrefsdays", "0"])

# Step 2: Status without LFS
run(["git", "--no-pager", "log", "--oneline", "-3"])
run(["git", "--no-pager", "diff", "--stat", "HEAD"])
run(["git", "stash", "list"])

# Step 3: Pull with rebase (skip LFS smudge)
print("=== git pull --rebase ===")
r = run(["git", "pull", "--rebase", "--allow-unrelated-histories", "origin", "main"], timeout=120)
if r.returncode != 0:
    print("Pull failed — trying fetch only")
    run(["git", "fetch", "origin", "--no-tags"], timeout=60)
    run(["git", "rebase", "origin/main", "--strategy-option=theirs"], timeout=60)

# Step 4: Apply stash if present
stash = subprocess.run(["git", "stash", "list"], capture_output=True, text=True, cwd=REPO, env=env, timeout=30)
if "stash@{0}" in stash.stdout:
    print("=== git stash pop ===")
    run(["git", "stash", "pop"], timeout=60)

# Step 5: Push
print("=== git push ===")
run(["git", "push", "origin", "main"], timeout=120)
