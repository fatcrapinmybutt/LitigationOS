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
from deterministic_cycle_id import build_cycle_id  # noqa

PORT = 8765

def main() -> None:
    cycle_id = build_cycle_id(delta_level=11)
    boot = bootstrap()
    append_event("bootstrap", boot, cycle_id=cycle_id)

    server = serve(PORT)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    url = f"http://127.0.0.1:{PORT}/index.html"
    append_event("server_started", {"url": url}, cycle_id=cycle_id)
    print(json.dumps({"status":"running","url":url,"cycle_id":cycle_id}, indent=2))

    time.sleep(0.6)
    try:
        webbrowser.open(url)
        append_event("browser_open", {"url": url}, cycle_id=cycle_id)
    except Exception as exc:
        append_event("browser_open_failed", {"url": url, "error": str(exc)}, cycle_id=cycle_id)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        append_event("shutdown", {"reason":"keyboard_interrupt"}, cycle_id=cycle_id)
        server.shutdown()
        server.server_close()

if __name__ == "__main__":
    main()
