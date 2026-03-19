
import json
import os

# Set file path
json_path = "FRED_PRIME_NEXTGEN_FULL_SYSTEMS.json"

# Load system expansions
if not os.path.exists(json_path):
    raise FileNotFoundError(f"Missing {json_path}")

with open(json_path, "r") as file:
    data = json.load(file)

# Simulate system registry injection
def register_to_system_registry(expansions):
    print("🔐 Injecting into FRED-PRIME system registry...")
    for system in expansions.get("SystemExpansions", []):
        print(f"✅ Registered: [{system['type']}] {system['name']} — {system['function'][:60]}...")

# Execute registration
register_to_system_registry(data)
