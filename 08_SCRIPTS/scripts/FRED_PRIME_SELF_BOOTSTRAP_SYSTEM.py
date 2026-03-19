# 🧠 FRED-PRIME AUTOLOAD SYSTEM – SELF-DIRECTED FULL DEPLOYMENT
# System knows Andrew J. Pigors' cases, court rules, and workflows permanently.

import os
import json
from pathlib import Path
import shutil
import time

# CORE PROFILE: Andrew J. Pigors
USER_PROFILE = {
    "full_name": "Andrew J. Pigors",
    "address": "1977 Whitehall Rd Lot 17, Muskegon, MI 49445",
    "email": "andrewjpigors@gmail.com",
    "phone": "231-903-5690",
    "jurisdiction": "Muskegon County Circuit Court (14th), 60th District, WDMI Federal",
    "core_issues": [
        "Custody Modification",
        "Parental Alienation",
        "PPO Defense",
        "Housing/Fraud (Shady Oaks)",
        "Contempt and Sanctions",
        "Emergency Motions",
        "1983 Civil Rights",
        "Benchbook Compliance",
    ],
    "required_modules": [
        "FRED-PRIME-OS", "GOD-COMPLEX", "CENTRAL-DASHBOARD", "BLOODHOUND", "LIBRARIAN",
        "EXPOSURE-CORE", "DOMINION-ENGINE", "APOCALYPSE-KERNEL"
    ],
    "federal_escalation_ready": True,
    "benchbooks": ["Custody", "Contempt", "Evidentiary", "LT Civil Procedure"],
}

# LOCATION & INDEX ROOT
FRED_ROOT = Path.cwd() / "FRED_PRIME_OS_REBUILT"
MIRROR_VERSIONS = [
    "FRED-PRIME-TOTAL-DEPLOYMENT-PACKAGE.zip",
    "FRED-PRIME-REUPLOAD-STUB.zip",
    "Legacy_FRED_v1.3.zip",
    "FRED_PRIME_EVIDENCE_CORE_PACK.zip"
]

# Bootstrap Execution
def boot_fred_prime():
    print("🚀 BOOTING FRED-PRIME OS...")

    # Step 1: Construct System
    os.system("python FRED_PRIME_OS_FULL_DEPLOY.py")
    time.sleep(2)

    # Step 2: Inject User Profile Permanently
    profile_path = FRED_ROOT / "SYSTEM_MANIFEST" / "user_profile.json"
    FRED_ROOT.mkdir(parents=True, exist_ok=True)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profile_path, "w") as f:
        json.dump(USER_PROFILE, f, indent=2)
    print(f"✅ User Profile saved to {profile_path}")

    # Step 3: Sync Legacy Versions & Modules
    sync_versions(FRED_ROOT)

    # Step 4: Confirm Directory Health
    print("🔁 Validating system directories...")
    required_dirs = ["CORES", "MODULES", "ENGINES", "TRIGGERS", "EXHIBIT_MATRIX", "POLICE_REPORTS"]
    missing = [d for d in required_dirs if not (FRED_ROOT / d).exists()]
    if missing:
        print(f"⚠️ Missing folders: {missing}")
    else:
        print("✅ All system folders verified.")

def sync_versions(destination):
    sync_dir = destination / "INTEGRATED_VERSIONS"
    sync_dir.mkdir(parents=True, exist_ok=True)
    for zip_name in MIRROR_VERSIONS:
        src = Path("/mnt/data") / zip_name
        if src.exists():
            shutil.copy(src, sync_dir / zip_name)
            print(f"🔗 Integrated legacy module: {zip_name}")

    print("🧬 Legacy versions integrated into master system.")

# Self-trigger
if __name__ == "__main__":
    boot_fred_prime()
