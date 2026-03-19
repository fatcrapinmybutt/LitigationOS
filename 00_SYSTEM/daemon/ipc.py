"""
Named Pipe IPC for LitigationOS Daemon.
Enables external tools (CLI, GUI, MCP) to communicate with the running daemon.

Protocol: JSON-RPC 2.0 over named pipes.
- Windows: \\\\.\\pipe\\litigationos-daemon
"""
import json
import os
import sys
import threading
from typing import Any, Callable, Optional

from .models import IPCRequest, IPCResponse


PIPE_NAME = r"\\.\pipe\litigationos-daemon"
BUFFER_SIZE = 65536


class IPCServer:
    """Named pipe IPC server for the daemon."""

    def __init__(self, logger=None):
        self.logger = logger
        self._handlers: dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def register(self, method: str, handler: Callable):
        """Register a method handler."""
        self._handlers[method] = handler

    def start(self):
        """Start the IPC server in a background thread."""
        if sys.platform != "win32":
            if self.logger:
                self.logger.warning("Named pipe IPC only supported on Windows")
            return

        self._running = True
        self._thread = threading.Thread(target=self._serve_loop, daemon=True)
        self._thread.start()
        if self.logger:
            self.logger.info(f"IPC server started on {PIPE_NAME}")

    def stop(self):
        """Stop the IPC server."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self.logger:
            self.logger.info("IPC server stopped")

    def _serve_loop(self):
        """Main serve loop — accepts connections, dispatches to handlers."""
        import win32pipe
        import win32file
        import pywintypes

        while self._running:
            try:
                pipe = win32pipe.CreateNamedPipe(
                    PIPE_NAME,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    (win32pipe.PIPE_TYPE_MESSAGE
                     | win32pipe.PIPE_READMODE_MESSAGE
                     | win32pipe.PIPE_WAIT),
                    1,  # max instances
                    BUFFER_SIZE,
                    BUFFER_SIZE,
                    0,  # default timeout
                    None,
                )

                # Wait for client connection
                win32pipe.ConnectNamedPipe(pipe, None)

                try:
                    # Read request
                    _, data = win32file.ReadFile(pipe, BUFFER_SIZE)
                    request_str = data.decode("utf-8")
                    response = self._handle_request(request_str)

                    # Write response
                    win32file.WriteFile(pipe, response.encode("utf-8"))
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"IPC request error: {e}")
                finally:
                    win32file.CloseHandle(pipe)

            except pywintypes.error as e:
                if not self._running:
                    break
                if self.logger:
                    self.logger.error(f"IPC pipe error: {e}")
            except ImportError:
                if self.logger:
                    self.logger.warning("pywin32 not installed — IPC unavailable")
                break
            except Exception as e:
                if self.logger:
                    self.logger.error(f"IPC server error: {e}")

    def _handle_request(self, raw: str) -> str:
        """Parse and dispatch a JSON-RPC request."""
        try:
            data = json.loads(raw)
            request = IPCRequest(**data)
        except Exception as e:
            resp = IPCResponse(id="error", success=False, error=f"Parse error: {e}")
            return resp.model_dump_json()

        handler = self._handlers.get(request.method)
        if handler is None:
            resp = IPCResponse(
                id=request.id, success=False,
                error=f"Unknown method: {request.method}"
            )
            return resp.model_dump_json()

        try:
            result = handler(**request.params)
            resp = IPCResponse(id=request.id, success=True, result=result)
        except Exception as e:
            resp = IPCResponse(id=request.id, success=False, error=str(e))

        return resp.model_dump_json()


class IPCClient:
    """Named pipe IPC client for communicating with the daemon."""

    def __init__(self, timeout_ms: int = 5000):
        self.timeout_ms = timeout_ms

    def call(self, method: str, params: dict = None) -> IPCResponse:
        """Send a request to the daemon and get a response."""
        if sys.platform != "win32":
            return IPCResponse(id="0", success=False, error="Windows only")

        import win32file
        import win32pipe
        import pywintypes

        request = IPCRequest(
            id=f"{method}-{id(self)}",
            method=method,
            params=params or {},
        )

        try:
            # Connect to pipe
            handle = win32file.CreateFile(
                PIPE_NAME,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None,
            )

            # Set to message mode
            win32pipe.SetNamedPipeHandleState(
                handle,
                win32pipe.PIPE_READMODE_MESSAGE,
                None, None,
            )

            # Send request
            win32file.WriteFile(handle, request.model_dump_json().encode("utf-8"))

            # Read response
            _, data = win32file.ReadFile(handle, BUFFER_SIZE)
            win32file.CloseHandle(handle)

            return IPCResponse(**json.loads(data.decode("utf-8")))

        except pywintypes.error as e:
            return IPCResponse(
                id=request.id, success=False,
                error=f"Connection failed (daemon not running?): {e}"
            )
        except ImportError:
            return IPCResponse(
                id=request.id, success=False,
                error="pywin32 not installed"
            )
        except Exception as e:
            return IPCResponse(
                id=request.id, success=False,
                error=str(e)
            )

    def ping(self) -> bool:
        """Check if daemon is running."""
        resp = self.call("ping")
        return resp.success

    def status(self) -> dict:
        """Get daemon health status."""
        resp = self.call("status")
        return resp.result if resp.success else {"error": resp.error}

    def enqueue_task(self, task_type: str, payload: dict = None,
                     priority: str = "normal") -> Optional[str]:
        """Enqueue a task. Returns task ID or None on error."""
        resp = self.call("enqueue", {
            "task_type": task_type,
            "payload": payload or {},
            "priority": priority,
        })
        return resp.result if resp.success else None
