"""Resilient single-commit git push with retry logic.
Pushes each commit individually to work around GitHub HTTP 500 on large packs.
v2: 600s timeout for large commits, --no-thin flag, diff.renameLimit=0
"""
import subprocess, time, sys, os

REPO = r"C:\Users\andre\LitigationOS"
REMOTE = "origin"
BRANCH = "main"
MAX_RETRIES = 5
RETRY_DELAYS = [10, 30, 60, 120, 180]

os.environ["GIT_LFS_SKIP_PUSH"] = "1"

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO, **kw)

def get_commit_file_count(sha):
    r = run(["git", "diff", "--stat", "--diff-filter=AMDRT", f"{sha}~1", sha])
    lines = r.stdout.strip().split("\n") if r.stdout.strip() else []
    return max(len(lines) - 1, 0)  # last line is summary

def get_remaining():
    r = run(["git", "rev-parse", f"{REMOTE}/{BRANCH}"])
    remote_head = r.stdout.strip()
    r = run(["git", "rev-list", "--reverse", f"{remote_head}..HEAD"])
    return r.stdout.strip().split("\n") if r.stdout.strip() else []

def push_one(sha, file_count=0):
    # Large commits get longer timeout and --no-thin
    is_large = file_count > 100
    timeout = 600 if is_large else 180
    extra_args = ["--no-thin"] if is_large else []

    for attempt in range(MAX_RETRIES):
        cmd = ["git", "-c", "diff.renameLimit=0", "push"] + extra_args + [REMOTE, f"{sha}:refs/heads/{BRANCH}"]
        try:
            r = run(cmd, timeout=timeout)
        except subprocess.TimeoutExpired:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS)-1)]
            print(f"  ⏱ Timeout ({timeout}s) attempt {attempt+1}/{MAX_RETRIES}, retry in {delay}s...")
            time.sleep(delay)
            continue

        combined = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 0:
            return True, combined
        if any(err in combined for err in ["HTTP 500", "curl 22", "sideband", "HTTP 502", "HTTP 503"]):
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS)-1)]
            print(f"  ⚠ Server error (attempt {attempt+1}/{MAX_RETRIES}), retry in {delay}s...")
            time.sleep(delay)
            continue
        return False, combined
    return False, f"Max retries exceeded (timeout={timeout}s, large={is_large})"

def main():
    commits = get_remaining()
    total = len(commits)
    if total == 0:
        print("✅ Already up to date!")
        return
    print(f"📦 {total} commits to push\n")

    pushed = 0
    for i, sha in enumerate(commits):
        short = sha[:11]
        r = run(["git", "log", "--format=%s", "-1", sha])
        subject = r.stdout.strip()[:60]
        file_count = get_commit_file_count(sha)
        tag = f" [{file_count} files]" if file_count > 50 else ""
        print(f"[{i+1}/{total}] {short} {subject}{tag}")

        ok, msg = push_one(sha, file_count)
        if ok:
            pushed += 1
            print(f"  ✅ pushed ({pushed}/{total})")
        else:
            print(f"  ❌ FAILED after {MAX_RETRIES} retries")
            print(f"  {msg[:300]}")
            print(f"\n⛔ Stopped at commit {short}. {pushed}/{total} pushed.")
            print(f"Resume: python {__file__}")
            sys.exit(1)

        delay = 5 if file_count > 100 else 2
        if i < total - 1:
            time.sleep(delay)

    print(f"\n🎉 ALL {pushed} commits pushed successfully!")

if __name__ == "__main__":
    main()
