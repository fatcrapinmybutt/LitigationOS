"""
Network Safety Net — Python side
Monkey-patches requests, urllib, httplib, socket to block outbound calls.
Import this ONCE at the top of any Python entry point.

Usage:
    import network_safety_net  # That's it — patches are applied on import
"""

import sys
import types
import logging

logger = logging.getLogger("NetworkSafetyNet")

BLOCKED_MSG = "[NetworkSafetyNet] Blocked outbound call — LitigationOS is local-only"
_blocked_count = 0


class NetworkBlockedError(ConnectionError):
    """Raised when an outbound network call is intercepted."""
    pass


class SafeResponse:
    """A fake response object returned instead of crashing."""
    status_code = 499
    ok = False
    text = '{"error":"network_blocked","message":"LitigationOS is local-only"}'
    content = b'{"error":"network_blocked","message":"LitigationOS is local-only"}'
    headers = {"content-type": "application/json"}
    reason = "Network Blocked"
    url = ""

    def __init__(self, url=""):
        self.url = url

    def json(self):
        return {"error": "network_blocked", "message": BLOCKED_MSG, "url": self.url}

    def raise_for_status(self):
        pass  # Silently pass — don't crash

    def __bool__(self):
        return False

    def __repr__(self):
        return f"<SafeResponse 499 NetworkBlocked {self.url}>"


def _block(url=""):
    global _blocked_count
    _blocked_count += 1
    logger.warning("%s: %s", BLOCKED_MSG, url)
    return SafeResponse(url)


# ---------- 1. Patch 'requests' ----------
def _patch_requests():
    try:
        import requests as _req

        for method in ("get", "post", "put", "patch", "delete", "head", "options"):
            orig = getattr(_req, method, None)

            def _safe_method(url, _orig=orig, _name=method, **kwargs):
                if _is_local(url):
                    return _orig(url, **kwargs)
                return _block(url)

            setattr(_req, method, _safe_method)

        # Patch Session too
        _orig_send = _req.Session.send

        def _safe_send(self, request, **kwargs):
            url = getattr(request, "url", "")
            if _is_local(url):
                return _orig_send(self, request, **kwargs)
            return _block(url)

        _req.Session.send = _safe_send

    except ImportError:
        pass


# ---------- 2. Patch 'urllib' ----------
def _patch_urllib():
    try:
        import urllib.request as _ur

        _orig_urlopen = _ur.urlopen

        def _safe_urlopen(url, *args, **kwargs):
            url_str = url if isinstance(url, str) else getattr(url, "full_url", str(url))
            if _is_local(url_str):
                return _orig_urlopen(url, *args, **kwargs)
            logger.warning("%s (urllib): %s", BLOCKED_MSG, url_str)
            global _blocked_count
            _blocked_count += 1
            # Return a file-like object with the error
            import io
            body = b'{"error":"network_blocked","message":"LitigationOS is local-only"}'
            resp = io.BytesIO(body)
            resp.status = 499
            resp.code = 499
            resp.headers = {}
            resp.getcode = lambda: 499
            resp.geturl = lambda: url_str
            resp.info = lambda: {}
            resp.read = resp.read
            return resp

        _ur.urlopen = _safe_urlopen

    except ImportError:
        pass


# ---------- 3. Patch 'http.client' ----------
def _patch_httplib():
    try:
        import http.client as _hc

        _orig_connect = _hc.HTTPConnection.connect

        def _safe_connect(self):
            host = self.host or ""
            if host in ("localhost", "127.0.0.1", "0.0.0.0", ""):
                return _orig_connect(self)
            logger.warning("%s (http.client): %s:%s", BLOCKED_MSG, host, self.port)
            global _blocked_count
            _blocked_count += 1
            raise NetworkBlockedError(f"{BLOCKED_MSG}: {host}:{self.port}")

        _hc.HTTPConnection.connect = _safe_connect

        if hasattr(_hc, "HTTPSConnection"):
            _orig_sconnect = _hc.HTTPSConnection.connect

            def _safe_sconnect(self):
                host = self.host or ""
                if host in ("localhost", "127.0.0.1", "0.0.0.0", ""):
                    return _orig_sconnect(self)
                logger.warning("%s (https): %s:%s", BLOCKED_MSG, host, self.port)
                global _blocked_count
                _blocked_count += 1
                raise NetworkBlockedError(f"{BLOCKED_MSG}: {host}:{self.port}")

            _hc.HTTPSConnection.connect = _safe_sconnect

    except ImportError:
        pass


# ---------- 4. Patch 'socket.create_connection' ----------
def _patch_socket():
    import socket as _s

    _orig_create = _s.create_connection

    # Known local addresses
    _local = {"localhost", "127.0.0.1", "0.0.0.0", "::1", ""}

    def _safe_create(address, *args, **kwargs):
        host = address[0] if isinstance(address, (tuple, list)) else str(address)
        if host in _local:
            return _orig_create(address, *args, **kwargs)
        # Allow unix sockets (no port = local pipe)
        if isinstance(address, str) and "/" in address:
            return _orig_create(address, *args, **kwargs)
        logger.warning("%s (socket): %s", BLOCKED_MSG, address)
        global _blocked_count
        _blocked_count += 1
        raise NetworkBlockedError(f"{BLOCKED_MSG}: {address}")

    _s.create_connection = _safe_create


# ---------- Helper ----------
def _is_local(url):
    """Return True if url points to localhost / file / is empty."""
    if not url:
        return True
    url_lower = str(url).lower()
    if url_lower.startswith(("file:", "data:")):
        return True
    for local in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        if local in url_lower:
            return True
    # Relative URLs are local
    if not url_lower.startswith(("http://", "https://")):
        return True
    return False


def get_blocked_count():
    return _blocked_count


def status():
    return {
        "active": True,
        "blocked_calls": _blocked_count,
        "patched": ["requests", "urllib", "http.client", "socket"],
    }


# ---------- Apply all patches on import ----------
_patch_requests()
_patch_urllib()
_patch_httplib()
_patch_socket()

logger.info("[NetworkSafetyNet] Active — all outbound network calls will be blocked")
