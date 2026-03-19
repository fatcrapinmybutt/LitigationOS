
#!/usr/bin/env python3
import os, subprocess, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS = os.path.join(ROOT, "scripts")
ARTIFACTS = os.path.join(ROOT, "artifacts")
DATA = os.path.join(ROOT, "data")

def run(cmd, cwd=None):
    print(">>", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd or ROOT)
    if r.returncode != 0:
        sys.exit(r.returncode)

def main():
    # 1) Pull from Drive
    run([sys.executable, os.path.join(SCRIPTS, "drive_puller.py")])
    # 2) Normalize artifacts to nodes/edges
    run([sys.executable, os.path.join(SCRIPTS, "collector_normalizer.py")])
    print("Sync + Build complete. See data/nodes.csv and data/edges.csv")

if __name__ == "__main__":
    main()
