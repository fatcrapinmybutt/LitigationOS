#!/usr/bin/env python3
import os
import sys

os.environ["PYTHONUTF8"] = "1"

# Change to safe dir
os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")

# Create output file
output_file = r"C:\Users\andre\LitigationOS\00_SYSTEM\tools\_direct_output.txt"
f = open(output_file, "w", encoding="utf-8")

# Write header
f.write("=" * 70 + "\n")
f.write("COMMAND 1: env-check\n")
f.write("=" * 70 + "\n")
sys.stdout = f
sys.stderr = f

try:
    import safe_shell
    safe_shell.env_check()
except Exception as e:
    f.write(f"ERROR: {e}\n")

# Flush and prepare for next command
f.flush()
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

f.write("\n" + "=" * 70 + "\n")
f.write("COMMAND 2: shadow-audit\n")
f.write("=" * 70 + "\n")
sys.stdout = f
sys.stderr = f

try:
    safe_shell.shadow_audit()
except Exception as e:
    f.write(f"ERROR: {e}\n")

# Flush and prepare for next command
f.flush()
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

f.write("\n" + "=" * 70 + "\n")
f.write("COMMAND 3: check org_agents/__init__.py\n")
f.write("=" * 70 + "\n")
sys.stdout = f
sys.stderr = f

try:
    safe_shell.check_syntax([r"C:\Users\andre\LitigationOS\00_SYSTEM\org_agents\__init__.py"])
except Exception as e:
    f.write(f"ERROR: {e}\n")

f.flush()
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

f.write("\n" + "=" * 70 + "\n")
f.write("DONE\n")
f.write("=" * 70 + "\n")

f.close()
print(f"Output saved to {output_file}")
