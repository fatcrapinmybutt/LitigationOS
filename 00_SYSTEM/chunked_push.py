"""
Chunked push strategy for LitigationOS.
Splits the mega-commit into directory-based chunks and pushes each individually.

Strategy:
1. git reset --mixed origin/main  (undo squash, changes go to working dir)
2. git add <dir_group> && git commit for each chunk
3. git push after each commit

CRITICAL: GIT_LFS_SKIP_PUSH=1 for all pushes
"""
import subprocess, os, sys, time, collections

os.chdir(r"C:\Users\andre\LitigationOS")
os.environ["GIT_LFS_SKIP_PUSH"] = "1"

DRY_RUN = "--dry-run" in sys.argv  # pass --dry-run to simulate

def run(cmd, timeout=300, check=True):
    """Run a command, return (returncode, stdout, stderr)."""
    print(f"  $ {cmd}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
    if r.stdout.strip():
        lines = r.stdout.strip().split('\n')
        if len(lines) > 5:
            print(f"    ({len(lines)} lines, first 3:)")
            for l in lines[:3]:
                print(f"    {l}")
        else:
            for l in lines:
                print(f"    {l}")
    if r.stderr.strip():
        for l in r.stderr.strip().split('\n')[:3]:
            print(f"    [err] {l}")
    if check and r.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return r.returncode, r.stdout, r.stderr

def git_push(msg_prefix, attempt=1):
    """Push current HEAD to origin/main with retry."""
    print(f"\n{'='*60}")
    print(f"PUSHING: {msg_prefix} (attempt {attempt})")
    print(f"{'='*60}")
    if DRY_RUN:
        print("  [DRY RUN] Would push here")
        return True
    try:
        rc, out, err = run("git push origin main", timeout=600, check=False)
        if rc == 0:
            print(f"  ✅ Push succeeded!")
            return True
        else:
            print(f"  ❌ Push failed (rc={rc})")
            if attempt < 3:
                print(f"  Retrying in 10s...")
                time.sleep(10)
                return git_push(msg_prefix, attempt + 1)
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⏱️ Push timed out after 600s")
        if attempt < 2:
            print(f"  Retrying in 15s...")
            time.sleep(15)
            return git_push(msg_prefix, attempt + 1)
        return False

# Define chunks — ordered from smallest/most important to largest
# Goal: keep each commit under ~20K files, ideally under 10K
CHUNKS = [
    {
        "name": "config-and-agents",
        "msg": "feat: config, agents, and instructions",
        "patterns": [
            ".github/", ".agents/", ".agentMemory/", ".copilot/",
            ".vscode/", ".agent/", "agents/", "configs/", "config/",
            ".editorconfig", ".gitignore", ".lesshst", ".node_repl_history",
            ".codex_config.yaml", "copilot-instructions.md",
            "justfile", "pyproject.toml", "requirements.txt",
            "master.code-workspace", "desktop.ini",
            "litigationos_mi_appellate_docforge_v8.jsonc",
            "litigationos_mi_appellate_docforge_v9_accel.jsonc",
        ],
    },
    {
        "name": "root-docs",
        "msg": "feat: root documentation and reference files",
        "patterns": [
            "README.md", "AGENTS.md", "ARCHITECTURE.md", "CHANGELOG.md",
            "CODE_OF_CONDUCT.md", "CONTRIBUTING.md", "LICENSE",
            "ARCHITECTURE_MAP.txt", "COA_366810_QUICK_INDEX.md",
            "CONSOLIDATED_FILING_SUMMARY_2026-02-22.txt",
            "COPILOT_INSTRUCTIONS_ENHANCED.md", "COPILOT_STARTUP_STATE.md",
            "FTS_TABLE_REFERENCE.txt", "IMPROVEMENT_ROADMAP.md",
            "INDEX.md", "INDEX_ORCHESTRATION_EXPLORATION.md",
            "JUDICIALyaml.yaml", "MANBEARPIG_SESSION_STATE.md",
            "MASTER_PLAN.md", "MASTER_SESSION_CONTEXT.md",
            "MASTER_SYSTEM_ARCHITECTURE.md", "MCNEILL_ACTION_PLAN.txt",
            "MCNEILL_INDEX_GUIDE.txt", "MCNEILL_QUICK_REFERENCE.txt",
            "MOTION_PREPARATION_CHECKLIST.txt",
            "OperationalLoop_MissingRadar_MI_LitigationOS_v2026-01-19.md",
            "PPO_QUICK_REFERENCE.md", "PROCESS_BLUEPRINT.md",
            "README_SESSION_INTELLIGENCE.md", "SESSION_HANDOFF_LAUNCH.md",
            "SESSION_INTELLIGENCE_QUICK_REFERENCE.txt",
            "SESSION_STORE_INTELLIGENCE.txt",
            "STRUCTURED_SESSION_INTELLIGENCE.md",
            "TOOL_276_INDEX.md", "TOOL_276_MICHIGAN_AUTHORITY_DATABASE.md",
            "UNIQUE_FACTS_NOT_IN_SUMMARIES.md",
            "docs/", "scripts/", "_rels/", "temp/", "core/",
            "08_SCRIPTS/", "11_CODE/", "script_vault.db",
        ],
    },
    {
        "name": "filings-and-court",
        "msg": "feat: court filings, golden set, and court records",
        "patterns": [
            "05_FILINGS/", "01_FILINGS/", "GENERATED_FILINGS/",
            "COURT_READY/", "JTC_COMPLAINT_EXTRACTED/",
            "03_COURT/", "02_TRIAL_14TH/",
        ],
    },
    {
        "name": "analysis-and-authority",
        "msg": "feat: analysis, authority, and reference materials",
        "patterns": [
            "04_ANALYSIS/", "02_AUTHORITY/", "09_REFERENCE/",
            "06_DATA/", "Legal/",
        ],
    },
    {
        "name": "evidence",
        "msg": "feat: evidence corpus",
        "patterns": [
            "01_EVIDENCE/", "03_EVIDENCE/", "08_MEDIA/",
        ],
    },
    {
        "name": "system-engines",
        "msg": "feat: system engines and shared modules",
        "patterns": [
            "00_SYSTEM/engines/", "00_SYSTEM/shared/",
            "00_SYSTEM/brains/", "00_SYSTEM/mcp_server/",
            "00_SYSTEM/daemon/", "00_SYSTEM/templates/",
            "00_SYSTEM/tools/", "00_SYSTEM/local_model/",
            "00_SYSTEM/autonomos/", "00_SYSTEM/pipeline/",
            "00_SYSTEM/scripts/",
        ],
    },
    {
        "name": "system-apps-reports",
        "msg": "feat: system apps and reports",
        "patterns": [
            "00_SYSTEM/apps/", "00_SYSTEM/reports/", "00_SYSTEM/",
        ],
    },
    {
        "name": "workspace",
        "msg": "feat: workspace and triage files",
        "patterns": [
            "12_WORKSPACE/",
        ],
    },
    {
        "name": "code-python-js",
        "msg": "feat: code - python and javascript",
        "patterns": [
            "07_CODE/py/", "07_CODE/python/",
            "07_CODE/js/", "07_CODE/javascript/",
            "07_CODE/SCRIPTS/", "07_CODE/dup_scripts/",
        ],
    },
    {
        "name": "code-ts-java-misc",
        "msg": "feat: code - typescript, java, and misc",
        "patterns": [
            "07_CODE/ts/", "07_CODE/typescript/",
            "07_CODE/java/", "07_CODE/",
        ],
    },
    {
        "name": "external",
        "msg": "feat: external artifacts and dependencies",
        "patterns": [
            "10_EXTERNAL/",
        ],
    },
    {
        "name": "remaining",
        "msg": "feat: remaining files",
        "patterns": ["."],  # catch-all — git add everything left
    },
]


def count_staged():
    """Count currently staged files."""
    rc, out, _ = run("git diff --cached --name-only", check=False)
    return len([l for l in out.strip().split('\n') if l.strip()]) if out.strip() else 0


def main():
    print("=" * 60)
    print("CHUNKED PUSH STRATEGY")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print("=" * 60)

    # Verify we're on the right commit
    rc, out, _ = run("git rev-parse HEAD", check=False)
    head = out.strip()
    print(f"\nCurrent HEAD: {head[:10]}")

    rc, out, _ = run("git rev-parse origin/main", check=False)
    origin = out.strip()
    print(f"Origin/main:  {origin[:10]}")

    if head == origin:
        print("Already up to date with origin!")
        return

    # Step 1: Reset to origin/main (mixed — changes go to working directory)
    print(f"\n{'='*60}")
    print("STEP 1: git reset --mixed origin/main")
    print("(All changes will be unstaged in working directory)")
    print(f"{'='*60}")

    if not DRY_RUN:
        run("git reset --mixed 6911aa7fb", timeout=120)

    # Step 2: Commit and push each chunk
    total_pushed = 0
    failed_chunks = []

    for i, chunk in enumerate(CHUNKS):
        print(f"\n{'='*60}")
        print(f"CHUNK {i+1}/{len(CHUNKS)}: {chunk['name']}")
        print(f"{'='*60}")

        # Stage the patterns for this chunk
        staged_any = False
        for pattern in chunk["patterns"]:
            # Check if path exists before trying to add
            if pattern == ".":
                # Catch-all: add everything remaining
                if not DRY_RUN:
                    rc, _, _ = run(f"git add -A", check=False)
                    staged_any = True
            elif os.path.exists(pattern) or os.path.exists(pattern.rstrip('/')):
                if not DRY_RUN:
                    # Use -- to separate paths
                    rc, _, _ = run(f'git add -A -- "{pattern}"', check=False)
                    if rc == 0:
                        staged_any = True
            else:
                # Try anyway — might be deleted files that git knows about
                if not DRY_RUN:
                    rc, _, _ = run(f'git add -A -- "{pattern}"', check=False)
                    if rc == 0:
                        staged_any = True

        # Count staged files
        n = count_staged() if not DRY_RUN else 999
        print(f"  Staged files: {n}")

        if n == 0:
            print(f"  (nothing to commit, skipping)")
            continue

        # Commit
        msg = chunk["msg"]
        print(f"  Committing: {msg}")
        if not DRY_RUN:
            rc, _, _ = run(f'git commit -m "{msg}" --no-verify', check=False)
            if rc != 0:
                print(f"  ⚠️ Commit failed, skipping push")
                failed_chunks.append(chunk["name"])
                continue

        # Push
        success = git_push(chunk["name"])
        if success:
            total_pushed += 1
            print(f"  ✅ Chunk {i+1} pushed successfully ({n} files)")
        else:
            failed_chunks.append(chunk["name"])
            print(f"  ❌ Chunk {i+1} FAILED to push")
            print(f"  Stopping — need to investigate before continuing")
            break

        # Brief pause between pushes
        if not DRY_RUN:
            time.sleep(3)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Pushed: {total_pushed}/{len(CHUNKS)} chunks")
    if failed_chunks:
        print(f"  Failed: {', '.join(failed_chunks)}")

    # Check final state
    if not DRY_RUN:
        rc, out, _ = run("git log --oneline origin/main..HEAD", check=False)
        ahead = len([l for l in out.strip().split('\n') if l.strip()]) if out.strip() else 0
        print(f"  Commits ahead of origin: {ahead}")


if __name__ == "__main__":
    main()
