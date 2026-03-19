#!/usr/bin/env python3
"""
sanitize_vscode_settings.py

Splits a VS Code settings JSON/JSONC file into:
- .vscode/settings.jsonc (safe, repo-shareable)
- .vscode/settings.local.jsonc (secrets/personal)

Usage:
  python scripts/sanitize_vscode_settings.py --in path/to/settings.jsonc --out-dir .vscode
"""

from __future__ import annotations
import argparse, json, re
from pathlib import Path

SECRET_KEY_PAT = re.compile(r"(apiKey|token|secret|password|key)$", re.IGNORECASE)
LONG_TOKEN_PAT = re.compile(r"^sk-[A-Za-z0-9_\\-]{20,}$")

def load_jsonc(text: str) -> dict:
    lines = []
    for ln in text.splitlines():
        ln = re.sub(r"//.*$", "", ln)
        lines.append(ln)
    t = "\\n".join(lines)
    t = re.sub(r",\\s*([}\\]])", r"\\1", t)
    return json.loads(t)

def is_secret(k: str, v) -> bool:
    if SECRET_KEY_PAT.search(k):
        return True
    if isinstance(v, str) and (LONG_TOKEN_PAT.match(v) or len(v) > 80):
        return True
    return False

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    src = Path(args.inp)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    data = load_jsonc(src.read_text(encoding="utf-8", errors="ignore"))

    safe = {}
    local = {}
    for k, v in data.items():
        (local if is_secret(k, v) else safe)[k] = v

    (out_dir/"settings.jsonc").write_text(json.dumps(safe, indent=2) + "\\n", encoding="utf-8")
    (out_dir/"settings.local.jsonc").write_text(json.dumps(local, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps({"ok": True, "safe_keys": len(safe), "local_keys": len(local)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
