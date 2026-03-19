from __future__ import annotations
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]

def serve(port: int = 8765) -> ThreadingHTTPServer:
    os.chdir(ROOT / "ui")
    server = ThreadingHTTPServer(("127.0.0.1", port), SimpleHTTPRequestHandler)
    return server

if __name__ == "__main__":
    server = serve()
    print(f"Serving UI at http://127.0.0.1:{server.server_port}/index.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        server.server_close()
