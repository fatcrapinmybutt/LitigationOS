#!/usr/bin/env python3
import json, os, subprocess, sys

ROOT=os.path.dirname(os.path.dirname(__file__))
DB=os.path.join(ROOT, "authority_store.sqlite")
TOOL=os.path.join(ROOT, "tools", "authority_query.py")
QFILE=os.path.join(os.path.dirname(__file__), "test_queries.json")

def run():
    with open(QFILE, "r", encoding="utf-8") as f:
        tests=json.load(f)
    ok=True
    for t in tests:
        name=t["name"]
        cmd=[sys.executable, TOOL, "--db", DB] + t["cmd"] + ["--k","25","--out-json", os.path.join(os.path.dirname(__file__), f"{name}.json")]
        r=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if r.returncode!=0:
            ok=False
            print(f"[FAIL] {name}: returncode={r.returncode}\n{r.stderr}")
            continue
        # count json lines
        import json as j
        with open(os.path.join(os.path.dirname(__file__), f"{name}.json"), "r", encoding="utf-8") as jf:
            rows=j.load(jf)
        if len(rows) < t.get("min_results",1):
            ok=False
            print(f"[FAIL] {name}: expected >= {t.get('min_results',1)} results, got {len(rows)}")
        else:
            print(f"[PASS] {name}: {len(rows)} results")
    return 0 if ok else 2

if __name__=="__main__":
    raise SystemExit(run())
