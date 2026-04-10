"""Remove stale git index.lock file."""
import os, time
lock = r"C:\Users\andre\LitigationOS\.git\index.lock"
try:
    os.remove(lock)
    print(f"Removed {lock}")
except PermissionError:
    print("Lock held by another process — waiting 3s and retrying...")
    time.sleep(3)
    try:
        os.remove(lock)
        print(f"Removed {lock} on retry")
    except Exception as e:
        print(f"Still locked: {e}")
        print("Try: Stop-Process on any git.exe processes")
except FileNotFoundError:
    print("Lock already gone")
