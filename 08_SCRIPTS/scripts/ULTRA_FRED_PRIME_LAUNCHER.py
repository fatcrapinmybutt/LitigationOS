
import subprocess
import time

print("🔁 Initializing ULTRA-FRED-PRIME v2025.7.0...")

modules = [
    "FRED_CASE_MASTER_LOADER.py",
    "RUN_ALL_COMMANDS.py",
    "FRED_TOGGLE_BOARD_ENHANCED.py",
    "_PLUGINS/Plugin_Signature_Validator.py",
    "Generate_Evidence_Report.py",
    "_AGENTS/The_Bloodhound/module_task.py",
    "_AGENTS/The_Librarian/module_task.py",
    "GOD_MODE_COMPLEX.py"
]

for mod in modules:
    try:
        print(f"🚀 Launching: {mod}")
        subprocess.run(["python", mod], check=True)
    except Exception as e:
        print(f"⚠ Error running {mod}: {e}")

print("✅ ULTRA-FRED-PRIME system boot complete.")
