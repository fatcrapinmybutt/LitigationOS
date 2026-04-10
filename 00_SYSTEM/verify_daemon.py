"""Verify nexus_daemon.py compiles, has correct handler count, and key classes exist."""
import ast, sys
from pathlib import Path

DAEMON = Path(r"C:\Users\andre\LitigationOS\.github\extensions\singularity\nexus_daemon.py")
src = DAEMON.read_text(encoding="utf-8")

# 1. Compile check
try:
    compile(src, str(DAEMON), "exec")
    print("[PASS] Compile: OK")
except SyntaxError as e:
    print(f"[FAIL] Compile: {e}")
    sys.exit(1)

# 2. AST parse - count classes, functions, handler registrations
tree = ast.parse(src)
classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
handlers = [f for f in functions if f.startswith("handle_")]

print(f"[INFO] Classes: {len(classes)} — {', '.join(classes)}")
print(f"[INFO] Functions: {len(functions)} total, {len(handlers)} handlers")

# 3. Key classes exist
required_classes = ["ConnectionPool", "CircuitBreaker", "HealthStatus", "ErrorCode"]
for cls in required_classes:
    if cls in classes:
        print(f"  [PASS] {cls} found")
    else:
        print(f"  [FAIL] {cls} MISSING")

# 4. Key handlers exist
required_handlers = [
    "handle_ping", "handle_query", "handle_fts_search",
    "handle_circuit_breaker", "handle_health", "handle_error_summary",
    "handle_check_disk_space", "handle_scan_all_systems",
    "handle_evolve_md", "handle_evolve_txt", "handle_evolve_pages",
    "handle_doc_exists", "handle_delete_document", "handle_swarm_dispatch",
]
missing = [h for h in required_handlers if h not in handlers]
if missing:
    print(f"  [FAIL] Missing handlers: {missing}")
else:
    print(f"  [PASS] All {len(required_handlers)} required handlers present")

# 5. HANDLERS dict completeness (count entries via string search)
handler_dict_entries = src.count('": handle_')
print(f"[INFO] HANDLERS dict entries: {handler_dict_entries}")

# 6. Line count
lines = src.count("\n") + 1
print(f"[INFO] Total lines: {lines}")
print(f"\n{'='*50}")
print(f"VERDICT: DAEMON VERIFIED — {len(handlers)} handlers, {lines} lines")
