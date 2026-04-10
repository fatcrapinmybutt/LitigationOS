"""Rewrite master.code-workspace: 164 folders → 6 focused folders, preserve settings block."""
import json, re

ws_path = r"C:\Users\andre\LitigationOS\master.code-workspace"

# Read current file and extract settings block
with open(ws_path, "r", encoding="utf-8") as f:
    raw = f.read()

# Parse with relaxed JSON (has trailing commas) — extract settings manually
settings_start = raw.index('"settings"')
# Find the matching closing brace
brace_depth = 0
settings_json = ""
for i, ch in enumerate(raw[settings_start:]):
    if ch == '{':
        brace_depth += 1
    elif ch == '}':
        brace_depth -= 1
        if brace_depth == 0:
            settings_json = raw[settings_start:settings_start + i + 1]
            break

# Clean trailing commas for valid JSON parsing
clean = re.sub(r',(\s*[}\]])', r'\1', settings_json)
settings_obj = json.loads('{' + clean + '}')

# Build new workspace
workspace = {
    "folders": [
        {"path": ".", "name": "📁 LitigationOS"},
        {"path": "00_SYSTEM", "name": "⚙️ System & Engines"},
        {"path": "04_ANALYSIS", "name": "📊 Analysis"},
        {"path": "05_FILINGS", "name": "📄 Filings & Golden Set"},
        {"path": "scripts", "name": "🔧 Scripts"},
        {"path": ".github", "name": "🤖 Agents & Instructions"},
    ],
    "settings": settings_obj["settings"],
}

# Write
with open(ws_path, "w", encoding="utf-8") as f:
    json.dump(workspace, f, indent=2)
    f.write("\n")

print(f"✅ Workspace rewritten: 164 folders → {len(workspace['folders'])} folders")
print(f"✅ Settings block preserved ({len(workspace['settings'])} keys)")
