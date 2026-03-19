import os, json, requests, difflib
from datetime import datetime

class RuleWatcher:
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data", "ruleswatch")
        os.makedirs(self.data_dir, exist_ok=True)
        self.sources = json.load(open(os.path.join(self.root, "..", "..", "configs", "rules_sources.json"), "r"))

    def run_once(self):
        results = {}
        for name, url in self.sources.items():
            try:
                r = requests.get(url, timeout=20)
                r.raise_for_status()
                content = r.content.decode("utf-8", errors="ignore")
                snap_dir = os.path.join(self.data_dir, name)
                os.makedirs(snap_dir, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                snap_path = os.path.join(snap_dir, f"{ts}.txt")
                with open(snap_path, "w", encoding="utf-8") as f:
                    f.write(content)

                # Find previous snapshot to diff
                snaps = sorted([s for s in os.listdir(snap_dir) if s.endswith(".txt")])
                delta = None
                if len(snaps) >= 2:
                    prev = snaps[-2]
                    prev_content = open(os.path.join(snap_dir, prev), encoding="utf-8").read().splitlines()
                    new_content = content.splitlines()
                    diff = difflib.unified_diff(prev_content, new_content, lineterm="")
                    delta = list(diff)

                results[name] = {
                    "url": url,
                    "snapshot": snap_path,
                    "delta_lines": len(delta) if delta else 0,
                    "delta_preview": delta[:20] if delta else []
                }
            except Exception as e:
                results[name] = {"url": url, "error": str(e)}
        return {"run_at": datetime.now().isoformat(), "results": results}
