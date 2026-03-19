#!/usr/bin/env python3
"""Simple runner that executes all 3 commands directly and writes output to file."""
import sys
import os
import io
from contextlib import redirect_stdout, redirect_stderr

# Force UTF-8
os.environ["PYTHONUTF8"] = "1"
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Change to safe dir
os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")

# Import the safe_shell module
import safe_shell

output_lines = []

def capture_output(func, *args, **kwargs):
    """Capture stdout and return output."""
    f = io.StringIO()
    try:
        with redirect_stdout(f):
            result = func(*args, **kwargs)
        return f.getvalue(), result
    except Exception as e:
        return f.getvalue(), f"ERROR: {type(e).__name__}: {e}"

# Command 1: env-check
output_lines.append("=" * 70)
output_lines.append("COMMAND 1: env-check")
output_lines.append("=" * 70)
out, result = capture_output(safe_shell.env_check)
output_lines.append(out)
if result:
    output_lines.append(f"Result: {result}\n")
output_lines.append("")

# Command 2: shadow-audit
output_lines.append("=" * 70)
output_lines.append("COMMAND 2: shadow-audit")
output_lines.append("=" * 70)
out, result = capture_output(safe_shell.shadow_audit)
output_lines.append(out)
if result:
    output_lines.append(f"Result: {result}\n")
output_lines.append("")

# Command 3: check __init__.py
output_lines.append("=" * 70)
output_lines.append("COMMAND 3: check org_agents/__init__.py")
output_lines.append("=" * 70)
out, result = capture_output(safe_shell.check_syntax, [r"C:\Users\andre\LitigationOS\00_SYSTEM\org_agents\__init__.py"])
output_lines.append(out)
if result:
    output_lines.append(f"Result: {result}\n")
output_lines.append("")

output_lines.append("=" * 70)
output_lines.append("ALL COMMANDS COMPLETED")
output_lines.append("=" * 70)

# Write everything to file
result_text = "\n".join(str(x) for x in output_lines)
output_file = r"C:\Users\andre\LitigationOS\00_SYSTEM\tools\_test_output.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(result_text)

print(f"Output written to {output_file}")
sys.exit(0)
