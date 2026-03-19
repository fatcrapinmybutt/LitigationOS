import os
import subprocess
import urllib.request

print("\n🔧 Beginning pip recovery process...\n")

# Step 1: Download get-pip.py to current directory
get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
get_pip_path = os.path.join(os.getcwd(), "get-pip.py")

try:
    print("⬇️ Downloading get-pip.py from:", get_pip_url)
    urllib.request.urlretrieve(get_pip_url, get_pip_path)
    print("✅ get-pip.py downloaded successfully.\n")
except Exception as e:
    print("❌ Failed to download get-pip.py:", e)
    exit(1)

# Step 2: Attempt to reinstall pip
try:
    print("⚙️ Running get-pip.py with your current Python installation...\n")
    subprocess.run(["python", "get-pip.py"], check=True)
    print("\n✅ pip has been successfully reinstalled.")
except subprocess.CalledProcessError as e:
    print("❌ Error during pip installation:", e)
except Exception as e:
    print("❌ Unexpected error:", e)

# Step 3: Check if pip is working
try:
    print("\n🔎 Verifying pip installation...")
    subprocess.run(["python", "-m", "pip", "--version"], check=True)
    print("\n🎉 pip is now functional.")
except:
    print("❌ pip installation still appears broken. Manual intervention required.")
