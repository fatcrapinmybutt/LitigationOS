"""Runner that executes all 3 commands and writes output to _test_output.txt"""
import sys, os, io

# Force UTF-8
os.environ["PYTHONUTF8"] = "1"
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Change to safe dir
os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")

# Import the safe_shell module
import safe_shell

output_lines = []

class Capture:
    def __init__(self):
        self.lines = []
    def write(self, text):
        self.lines.append(text)
        sys.__stdout__.write(text)
    def flush(self):
        pass
    @property
    def encoding(self):
        return 'utf-8'
    def reconfigure(self, **kwargs):
        pass

# Command 1: env-check
output_lines.append("=" * 60)
output_lines.append("COMMAND 1: env-check")
output_lines.append("=" * 60)
cap = Capture()
sys.stdout = cap
try:
    safe_shell.env_check()
except Exception as e:
    cap.lines.append(f"ERROR: {e}\n")
sys.stdout = sys.__stdout__
output_lines.extend(cap.lines)
output_lines.append("")

# Command 2: shadow-audit
output_lines.append("=" * 60)
output_lines.append("COMMAND 2: shadow-audit")
output_lines.append("=" * 60)
cap = Capture()
sys.stdout = cap
try:
    safe_shell.shadow_audit()
except Exception as e:
    cap.lines.append(f"ERROR: {e}\n")
sys.stdout = sys.__stdout__
output_lines.extend(cap.lines)
output_lines.append("")

# Command 3: check __init__.py
output_lines.append("=" * 60)
output_lines.append("COMMAND 3: check org_agents/__init__.py")
output_lines.append("=" * 60)
cap = Capture()
sys.stdout = cap
try:
    safe_shell.check_syntax([r"C:\Users\andre\LitigationOS\00_SYSTEM\org_agents\__init__.py"])
except Exception as e:
    cap.lines.append(f"ERROR: {e}\n")
sys.stdout = sys.__stdout__
output_lines.extend(cap.lines)
output_lines.append("")
output_lines.append("ALL DONE")

# Write everything to file
result = "".join(str(x) for x in output_lines)
with open(r"C:\Users\andre\LitigationOS\00_SYSTEM\tools\_test_output.txt", "w", encoding="utf-8") as f:
    f.write(result)

print("Output written to _test_output.txt")
