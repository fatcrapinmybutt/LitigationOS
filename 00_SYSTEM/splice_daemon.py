"""Splice new handlers into nexus_daemon.py.

Reads the data module and patches the daemon file:
1. Inserts new handler code after line 1057 (end of handle_deadlines)
2. Replaces the HANDLERS dict with the expanded 46-entry version
3. Replaces the docstring actions section
"""
import sys, os
sys.path.insert(0, r"D:\LitigationOS_tmp")
from new_daemon_handlers import NEW_HANDLERS_CODE, NEW_HANDLERS_DICT, NEW_DOCSTRING_ACTIONS

DAEMON = r"C:\Users\andre\LitigationOS\.github\extensions\singularity\nexus_daemon.py"

with open(DAEMON, "r", encoding="utf-8") as f:
    text = f.read()
lines = text.split("\n")

# ── 1. Replace docstring actions (lines 17-42, 0-indexed 16-41) ──
old_actions_start = "Actions:"
old_actions_end = "Started by extension.mjs on load. Stays alive for entire session."

idx_start = None
idx_end = None
for i, line in enumerate(lines):
    if old_actions_start in line and idx_start is None:
        idx_start = i
    if old_actions_end in line:
        idx_end = i
        break

if idx_start is None or idx_end is None:
    print(f"ERROR: Could not find docstring markers. start={idx_start}, end={idx_end}")
    sys.exit(1)

new_docstring_lines = NEW_DOCSTRING_ACTIONS.split("\n")
lines = lines[:idx_start] + new_docstring_lines + lines[idx_end + 1:]
print(f"Docstring replaced: lines {idx_start+1}-{idx_end+1} with {len(new_docstring_lines)} new lines")

# Recombine to work with string replacement for remaining edits
text = "\n".join(lines)

# ── 2. Insert new handler code before ACTION ROUTER ──
marker = "# ══════════════════════════════════════════════════════════════════════════\n# ACTION ROUTER\n# ══════════════════════════════════════════════════════════════════════════"
if marker not in text:
    print("ERROR: ACTION ROUTER marker not found")
    sys.exit(1)

# Insert new code right before the ACTION ROUTER marker
text = text.replace(marker, NEW_HANDLERS_CODE + "\n\n" + marker)
print(f"Inserted {len(NEW_HANDLERS_CODE)} chars of new handler code")

# ── 3. Replace HANDLERS dict ──
old_handlers_start = "HANDLERS = {"
old_handlers_end = "}"
# Find the HANDLERS dict specifically
h_start = text.find("HANDLERS = {")
if h_start == -1:
    print("ERROR: HANDLERS dict not found")
    sys.exit(1)
# Find the matching closing brace — it's the one followed by two newlines and another section comment
h_end = text.find("}\n\n\n# ══", h_start)
if h_end == -1:
    # Try alternate pattern
    h_end = text.find("}\n\n\n#", h_start)
if h_end == -1:
    print("ERROR: Could not find HANDLERS dict end")
    sys.exit(1)
h_end += 1  # include the closing brace

old_handlers = text[h_start:h_end]
text = text[:h_start] + NEW_HANDLERS_DICT + text[h_end:]
print(f"HANDLERS dict replaced: {old_handlers.count(chr(10))+1} old lines -> {NEW_HANDLERS_DICT.count(chr(10))+1} new lines")

# ── 4. Write ──
with open(DAEMON, "w", encoding="utf-8") as f:
    f.write(text)

# ── 5. Syntax check ──
import ast
try:
    ast.parse(text)
    print("Syntax check: PASS")
except SyntaxError as e:
    print(f"Syntax check: FAIL — {e}")
    sys.exit(1)

# Count functions
func_count = text.count("\ndef handle_")
print(f"Total handle_* functions: {func_count}")
handler_entries = NEW_HANDLERS_DICT.count('"')
print(f"HANDLERS dict entries (quote pairs): {handler_entries // 2}")
total_lines = text.count("\n") + 1
print(f"Total lines: {total_lines}")
print("DONE — nexus_daemon.py patched successfully")
