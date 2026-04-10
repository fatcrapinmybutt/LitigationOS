"""Read key sections of themanbearpig.py launcher."""
import re

path = r"C:\Users\andre\LitigationOS\scripts\themanbearpig.py"
lines = open(path, encoding="utf-8").readlines()

# Section 1: Path setup and VIS_DIR (lines 100-120)
print("=== PATH SETUP (lines 100-120) ===")
for i in range(99, min(120, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

# Section 2: UnifiedAPI class definition - find it
print("\n\n=== UnifiedAPI CLASS START ===")
for i, line in enumerate(lines):
    if "class UnifiedAPI" in line:
        for j in range(i, min(i+30, len(lines))):
            print(f"{j+1}: {lines[j]}", end="")
        break

# Section 3: Find all method names in UnifiedAPI
print("\n\n=== ALL UnifiedAPI METHODS ===")
in_api = False
methods = []
for i, line in enumerate(lines):
    if "class UnifiedAPI" in line:
        in_api = True
    elif in_api and line.strip().startswith("class "):
        break
    if in_api and "    def " in line:
        m = re.match(r'\s+def (\w+)\(', line)
        if m and not m.group(1).startswith('_'):
            methods.append(m.group(1))

print(f"Total public methods: {len(methods)}")
for m in methods:
    print(f"  - {m}")

# Section 4: main() function
print("\n\n=== main() FUNCTION ===")
for i, line in enumerate(lines):
    if "def main(" in line:
        for j in range(i, min(i+60, len(lines))):
            print(f"{j+1}: {lines[j]}", end="")
        break

# Section 5: webview.create_window call
print("\n\n=== webview.create_window CALL ===")
for i, line in enumerate(lines):
    if "webview.create_window" in line:
        start = max(0, i-3)
        for j in range(start, min(i+10, len(lines))):
            print(f"{j+1}: {lines[j]}", end="")
        print()

print(f"\nTotal lines: {len(lines)}")
