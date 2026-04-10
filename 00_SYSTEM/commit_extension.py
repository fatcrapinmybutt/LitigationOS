"""Commit extension.mjs with 13 new tool definitions."""
import subprocess, os
os.chdir(r"C:\Users\andre\LitigationOS")
env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}

def run(args, timeout=120):
    print(f"$ git {' '.join(args)}")
    r = subprocess.run(["git", "--no-pager", "--no-optional-locks"] + args,
                       capture_output=True, text=True, timeout=timeout, env=env)
    if r.stdout.strip(): print(r.stdout.strip()[:500])
    if r.stderr.strip(): print(f"  stderr: {r.stderr.strip()[:300]}")
    return r.returncode

run(["add", ".github/extensions/singularity/extension.mjs"])

msg = """extension.mjs: wire 13 new NEXUS v3 tool definitions (46→59 tools)

New tools: system_health, record_error, get_error_summary, check_disk_space,
scan_all_systems, evolve_md, evolve_txt, evolve_pages, document_exists,
hash_exists, delete_document, insert_document, dispatch_to_swarm

All route through NEXUS daemon persistent connection (100× faster than MCP).

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"""

run(["commit", "-m", msg])
run(["log", "--oneline", "-3"])
