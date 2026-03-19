import os
import shutil
import subprocess
import urllib.request

# Paths
python_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Programs', 'Python', 'Python312')
pip_dir = os.path.join(python_dir, 'Lib', 'site-packages', 'pip')
pip_exe = os.path.join(python_dir, 'Scripts', 'pip.exe')
get_pip_path = 'F:/get-pip.py'

# Step 1: Download get-pip.py
print("[1/4] Downloading get-pip.py...")
try:
    urllib.request.urlretrieve(
        'https://bootstrap.pypa.io/pip/get-pip.py',
        get_pip_path
    )
    print(f"Downloaded get-pip.py to {get_pip_path}")
except Exception as e:
    print(f"[ERROR] Failed to download get-pip.py: {e}")
    exit(1)

# Step 2: Purge broken pip installation
print("[2/4] Purging broken pip installation...")
try:
    if os.path.exists(pip_dir):
        shutil.rmtree(pip_dir)
        print(f"Removed directory: {pip_dir}")
    if os.path.exists(pip_exe):
        os.remove(pip_exe)
        print(f"Removed file: {pip_exe}")
except Exception as e:
    print(f"[ERROR] Failed to purge pip: {e}")
    exit(1)

# Step 3: Reinstall pip
print("[3/4] Running get-pip.py to reinstall pip...")
try:
    subprocess.run(['python', get_pip_path], check=True)
except subprocess.CalledProcessError as e:
    print(f"[ERROR] pip reinstallation failed: {e}")
    exit(1)

# Step 4: Install python-docx
print("[4/4] Installing python-docx...")
try:
    subprocess.run(['python', '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
    subprocess.run(['python', '-m', 'pip', 'install', 'python-docx'], check=True)
    print("python-docx installed successfully.")
except subprocess.CalledProcessError as e:
    print(f"[ERROR] Failed to install python-docx: {e}")
    exit(1)

print("✅ pip and python-docx are now installed and repaired.")
