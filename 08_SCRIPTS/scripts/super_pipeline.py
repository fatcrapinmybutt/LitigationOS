
import subprocess
import sys

MODULES = [
    "async_oswalker.py",
    "SmartClassifier.py",
    "ChronoMapper.py",
    "GUI_BridgeController.py",
    "MCR_MCL_ViolationScanner.py",
    "AutoAffidavitBuilder.py"
]

def run_module(module):
    print(f"🚀 Running {module}...")
    result = subprocess.run([sys.executable, module], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error in {module}:
{result.stderr}")
    else:
        print(f"✅ {module} completed.
{result.stdout}")

def main():
    print("📦 Starting full SUPRA pipeline...")
    for module in MODULES:
        run_module(module)
    print("🎯 All modules completed. Litigation system is updated.")

if __name__ == "__main__":
    main()
