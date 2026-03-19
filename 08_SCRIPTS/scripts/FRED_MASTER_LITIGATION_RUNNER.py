
import subprocess

def run_script(script_path):
    print(f"🚀 Running {script_path}...")
    subprocess.run(["python", script_path], check=True)

scripts = [
    "BuildMiFILE_ZIP.py",
    "BuildExhibitIndex.py",
    "InjectSignaturePages.py",
    "DeployTimelineAnalyzer.py"
]

for script in scripts:
    try:
        run_script(script)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script}: {e}")
    except FileNotFoundError:
        print(f"⚠️ Script not found: {script}")

print("\n✅ All scripts completed. Your court binder is ready.")
