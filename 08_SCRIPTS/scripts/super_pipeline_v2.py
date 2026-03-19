
import subprocess
import sys

MODULES = [
    "async_oswalker.py",
    "SmartClassifier.py",
    "ChronoMapper.py",
    "GUI_BridgeController.py",
    "MCR_MCL_ViolationScanner.py",
    "AutoAffidavitBuilder.py",
    "AutoComplaintGenerator.py",
    "AutoProposedOrderGenerator.py",
    "AutoShowCauseMotionGenerator.py"
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
    print("📦 Launching SUPRA PIPELINE v2: Full litigation output builder...")
    for module in MODULES:
        run_module(module)
    print("🎯 Litigation output fully generated.")

if __name__ == "__main__":
    main()
