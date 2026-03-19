
import json
import os

REGISTRY_PATH = "F:\THE_PROGRAM_REGISTRY.json"
DIST_FOLDER = "F:\dist_installer"

def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {"name": "THE_PROGRAM_REGISTRY", "version": "auto", "description": "Auto-managed registry", "components": []}
    with open(REGISTRY_PATH, "r") as f:
        return json.load(f)

def save_registry(data):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[✓] Registry updated: {REGISTRY_PATH}")

def scan_and_update_registry():
    print(f"[SCAN] Looking in: {DIST_FOLDER}")
    registry = load_registry()
    files = os.listdir(DIST_FOLDER)
    executables = [f for f in files if f.endswith(".exe")]

    added = 0
    for exe in executables:
        name = os.path.splitext(exe)[0].replace("_", " ").title()
        if name not in registry["components"]:
            registry["components"].append(name)
            print(f"[+] Added to registry: {name}")
            added += 1

    if added:
        save_registry(registry)
    else:
        print("[=] No new components added.")

if __name__ == "__main__":
    scan_and_update_registry()
