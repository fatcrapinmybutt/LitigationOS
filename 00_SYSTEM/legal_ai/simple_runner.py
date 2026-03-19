"""Direct execution of _bisect with file output."""
import subprocess
import sys
import os

os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai")

# Run the bisect script directly
sys.exit(subprocess.call([sys.executable, "tests/_bisect.py"]))
