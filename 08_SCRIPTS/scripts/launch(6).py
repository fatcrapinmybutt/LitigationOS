from __future__ import annotations
import sys
import webbrowser
import threading
import time
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from state_bootstrap import bootstrap  # noqa
from replay_log import append_event  # noqa
from local_server import serve  # noqa
from deterministic_cycle_id import CycleSeed, make_cycle_record  # noqa

PORT = 8765

def main() -> None:
    boot = bootstrap()

    cycle_state_path = ROOT / "manifests" / "cycle_state.json"
    cycle = {"cycle_id":"CYCLE-UNSET"}
    try:
        state = json.loads(cycle_state_path.read_text(encoding="utf-8"))
        cycle = make_cycle_record(CycleSeed(
            directive_name=state.get("directive_name", "EVENTHORIZON_CMDCTR_EXECUTOR_v2_2026-02-22"),
            cycle_index=int(state.get("cycle_index", 0)),
            delta_level=int(state.get("delta_level", 0)),
            lane_scope=("MEEK1","MEEK2","MEEK3","MEEK4"),
        ))
        (ROOT / "manifests" / "deterministic_cycle_id.json").write_text(json.dumps(cycle, indent=2), encoding="utf-8")
    except Exception as exc:
        cycle = {"cycle_id":"CYCLE-UNSET", "error": str(exc)}

    append_event("bootstrap", {"bootstrap": boot, "cycle": cycle}, cycle_id=cycle.get("cycle_id","CYCLE-UNSET"))

    server = serve(PORT)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    url = f"http://127.0.0.1:{PORT}/index.html"
    append_event("server_started", {"url": url}, cycle_id=cycle.get("cycle_id","CYCLE-UNSET"))
    print(json.dumps({"status":"running","url":url,"cycle_id":cycle.get("cycle_id")}, indent=2))

    time.sleep(0.6)
    try:
        webbrowser.open(url)
        append_event("browser_open", {"url": url}, cycle_id=cycle.get("cycle_id","CYCLE-UNSET"))
    except Exception as exc:
        append_event("browser_open_failed", {"url": url, "error": str(exc)}, cycle_id=cycle.get("cycle_id","CYCLE-UNSET"))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        append_event("shutdown", {"reason":"keyboard_interrupt"}, cycle_id=cycle.get("cycle_id","CYCLE-UNSET"))
        server.shutdown()
        server.server_close()

if __name__ == "__main__":
    main()
