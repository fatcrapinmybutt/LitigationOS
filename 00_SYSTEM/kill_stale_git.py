"""Kill stale git processes and remove index.lock."""
import subprocess, os, time

# Kill small git processes first (likely lock holders), then all
small_pids = [8552, 11044, 1372, 10768, 5572, 5088]
for pid in small_pids:
    try:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                       capture_output=True, timeout=5)
        print(f"  Killed PID {pid}")
    except Exception as e:
        print(f"  Skip PID {pid}: {e}")

time.sleep(2)

# Try removing lock
lock = r"C:\Users\andre\LitigationOS\.git\index.lock"
try:
    os.remove(lock)
    print(f"\n[OK] Removed {lock}")
except FileNotFoundError:
    print("\n[OK] Lock already gone")
except PermissionError:
    print("\n[WARN] Lock still held — killing ALL git.exe processes")
    # Count them first
    result = subprocess.run(["tasklist", "/fi", "imagename eq git.exe", "/fo", "csv", "/nh"],
                           capture_output=True, text=True, timeout=10)
    count = len([l for l in result.stdout.strip().split("\n") if l.strip()])
    print(f"  Found {count} git processes — killing all")
    subprocess.run(["taskkill", "/F", "/IM", "git.exe"], capture_output=True, timeout=15)
    time.sleep(3)
    try:
        os.remove(lock)
        print(f"  [OK] Removed {lock}")
    except Exception as e:
        print(f"  [FAIL] {e}")
