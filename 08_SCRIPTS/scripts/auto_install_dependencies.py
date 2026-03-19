import subprocess, os, logging

WHEEL_DIR = r"Z:\site-packages\wheels"
TARGET_DIR = r"Z:\site-packages\Python311\site-packages"
LOG_PATH = os.path.join(WHEEL_DIR, "install_log.txt")
os.makedirs(WHEEL_DIR, exist_ok=True)
os.makedirs(TARGET_DIR, exist_ok=True)

with open(LOG_PATH, "w") as log:
    try:
        subprocess.check_call([
            "python", "-m", "pip", "install", "*.whl",
            "--no-cache-dir", "--force-reinstall",
            f"--target={TARGET_DIR}"
        ], cwd=WHEEL_DIR, stdout=log, stderr=log)
        print("✅ Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ pip install failed. See install_log.txt")
