#!/usr/bin/env python3
"""rclone_bridge.py — LitigationOS wrapper for rclone (Windows-friendly)

Design goals:
- One-command launcher from our system (bat/cmd calls this).
- Deterministic logs under RUNS/.
- Policy-gated: refuses to run unless OnlineUpdateMode=true AND allowlist tool id 'rclone' enabled.
- No assumptions about remote name; prompts and persists last-used in CONFIG/rclone_bridge.json.

This wrapper DOES NOT download rclone or any model weights.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def die(msg: str, code: int = 2) -> None:
    print("FAIL:", msg, file=sys.stderr)
    raise SystemExit(code)


def now_utc() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())


def ensure_not_c_drive(root: Path) -> None:
    # root may be on C: if user unzipped wrong; enforce deny-by-default
    s = str(root.resolve())
    if len(s) >= 2 and s[1] == ":" and s[0].upper() == "C":
        die("Root is on C: (excluded by policy). Move to F:/D:/Z:/Q:/E: and retry.")


def load_json(p: Path) -> dict:
    if not p.exists():
        die(f"Missing required file: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def resolve_policy_paths(root: Path, policy: dict) -> tuple[Path | None, Path | None]:
    ks = policy.get("killSwitch") or {}
    logcfg = policy.get("logging") or {}
    ks_path = None
    if ks.get("enabled", True) and ks.get("flagFile"):
        flag = Path(ks.get("flagFile"))
        ks_path = (root / flag).resolve() if not flag.is_absolute() else flag.resolve()
    log_path = None
    if logcfg.get("enabled", True) and logcfg.get("path"):
        lp = Path(logcfg.get("path"))
        log_path = (root / lp).resolve() if not lp.is_absolute() else lp.resolve()
    return ks_path, log_path


def policy_allows_rclone(root: Path) -> tuple[bool, str]:
    policy_path = root / "CONFIG" / "network_policy.json"
    policy = load_json(policy_path)

    ks_path, _ = resolve_policy_paths(root, policy)
    if ks_path and ks_path.exists():
        return (False, "Network kill-switch flag present")

    if not policy.get("OnlineUpdateMode", False):
        return (False, "OnlineUpdateMode=false")

    allow_id = "rclone"
    for entry in policy.get("allowlist", []) or []:
        if entry.get("type") != "tool":
            continue
        if entry.get("id") == allow_id and entry.get("enabled", False):
            return (True, "allowlisted tool rclone")
    return (False, "rclone tool not enabled in allowlist")


def write_run_log(run_dir: Path, event: dict) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / "LOGS" / "rclone_bridge.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def find_rclone(root: Path, explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if p.exists():
            return p
        die(f"--rclone not found: {explicit}")

    # Prefer bundled locations
    candidates = [
        root / "APP" / "Tools" / "RcloneBridge" / "bin" / "rclone.exe",
        root / "APP" / "Tools" / "RcloneBridge" / "bin" / "rclone",
        root / "bin" / "rclone.exe",
        root / "bin" / "rclone",
    ]
    for c in candidates:
        if c.exists():
            return c

    # Fall back to PATH
    which = shutil.which("rclone")
    if which:
        return Path(which)

    die("rclone not found. Install rclone or place rclone.exe in APP/Tools/RcloneBridge/bin/")


def prompt(msg: str) -> str:
    print(msg, end="", flush=True)
    return sys.stdin.readline().strip()


def load_bridge_cfg(root: Path) -> tuple[Path, dict]:
    cfg_path = root / "CONFIG" / "rclone_bridge.json"
    cfg = load_json(cfg_path)
    return cfg_path, cfg


def ensure_remote(cfg_path: Path, cfg: dict) -> tuple[str, str]:
    remote_name = (cfg.get("remote") or {}).get("name")
    remote_root = (cfg.get("remote") or {}).get("root_path", "")
    if not remote_name:
        remote_name = prompt("Enter your rclone remote name (e.g., gdrive, drive, ESD-USB): ")
        if not remote_name:
            die("Remote name is required.")
        cfg.setdefault("remote", {})["name"] = remote_name
        save_json(cfg_path, cfg)
    return remote_name, remote_root or ""


def run_cmd(run_dir: Path, cmd: list[str]) -> int:
    write_run_log(run_dir, {"ts": now_utc(), "event": "exec", "cmd": cmd})
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=False)
    out_path = run_dir / "LOGS" / "rclone_stdout.log"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as f:
        for line in proc.stdout or []:
            f.write(line)
    rc = proc.wait()
    write_run_log(run_dir, {"ts": now_utc(), "event": "exit", "code": rc})
    return rc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Path to LITIGATIONOS__MASTERv1.0")
    ap.add_argument("--rclone", help="Explicit path to rclone.exe")
    ap.add_argument("--once", action="store_true", help="(daemon mode) run one cycle then exit")

    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Show detected configuration and rclone path")

    p_ls = sub.add_parser("lsjson", help="Run rclone lsjson and store as a run artifact")
    p_ls.add_argument("--remote-path", default="", help="Remote subpath (e.g., /Litigation_OS$)")
    p_ls.add_argument("--out", default="", help="Output file path (defaults to RUNS/.../rclone_lsjson.json)")
    p_ls.add_argument("--recursive", action="store_true")

    p_sync = sub.add_parser("sync", help="Run rclone sync remote -> local mirror under DATA/INBOX/gdrive_mirror")
    p_sync.add_argument("--remote-path", default="")
    p_sync.add_argument("--local", default="", help="Local destination (default derived from config)")
    p_sync.add_argument("--dry-run", action="store_true")

    p_mount = sub.add_parser("mount", help="Run rclone mount (requires WinFsp on Windows)")
    p_mount.add_argument("--remote-path", default="")
    p_mount.add_argument("--mount", required=True, help="Mount point folder (or drive letter target) already created")

    args = ap.parse_args()
    root = Path(args.root).resolve()
    if root.name != "LITIGATIONOS__MASTERv1.0":
        die("--root must point to the LITIGATIONOS__MASTERv1.0 folder")
    ensure_not_c_drive(root)

    policy_ok, why = policy_allows_rclone(root)

    cfg_path, cfg = load_bridge_cfg(root)
    remote_name, remote_root = ensure_remote(cfg_path, cfg)
    rclone = find_rclone(root, args.rclone)

    # Run directory
    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    run_dir = root / "RUNS" / f"RUN_{ts}_RCLONE"

    # Persist last used
    cfg.setdefault("last_used", {})
    cfg["last_used"].update({"remote_name": remote_name, "remote_path": "", "local_path": "", "ts_utc": now_utc()})
    save_json(cfg_path, cfg)

    if args.cmd == "doctor":
        print("OK")
        print("root=", str(root))
        print("rclone=", str(rclone))
        print("remote=", f"{remote_name}:{remote_root}")
        print("policy=", "ALLOW" if policy_ok else f"DENY ({why})")
        print("hint: enable CONFIG/network_policy.json -> OnlineUpdateMode=true and allowlist entry id=rclone enabled=true")
        return 0

    if not policy_ok:
        # Fail closed with an acquisition plan
        run_dir.mkdir(parents=True, exist_ok=True)
        report = run_dir / "REPORTS" / "RCLONE_BLOCKED.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            "# Rclone blocked by policy\n\n"
            f"Reason: {why}\n\n"
            "## How to enable\n"
            "1) Edit CONFIG/network_policy.json\n"
            "2) Set OnlineUpdateMode=true\n"
            "3) Set allowlist entry {id:'rclone'} enabled=true\n"
            "4) Re-run this command\n",
            encoding="utf-8",
        )
        die(f"rclone blocked by policy: {why}")

    if args.cmd == "lsjson":
        rp = (args.remote_path or "").lstrip("/")
        src = f"{remote_name}:{('/' + rp) if rp else ''}"
        out = Path(args.out) if args.out else (run_dir / "ARTIFACTS" / "rclone_lsjson.json")
        out = out if out.is_absolute() else (root / out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = [str(rclone), "lsjson", src]
        if args.recursive:
            cmd.append("--recursive")
        cmd.extend(["--files-only"])
        # capture to file via rclone --output not available; redirect with python
        write_run_log(run_dir, {"ts": now_utc(), "event": "lsjson", "src": src, "out": str(out)})
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
        out.write_text(proc.stdout, encoding="utf-8")
        write_run_log(run_dir, {"ts": now_utc(), "event": "exit", "code": proc.returncode})
        if proc.returncode != 0:
            die(f"rclone lsjson failed; see {run_dir / 'LOGS' / 'rclone_stdout.log'}", proc.returncode)
        print("OK wrote", str(out))
        return 0

    if args.cmd == "sync":
        rp = (args.remote_path or "").lstrip("/")
        src = f"{remote_name}:{('/' + rp) if rp else ''}"
        mirror_subdir = (cfg.get("operations") or {}).get("default_mirror_subdir", "DATA/INBOX/gdrive_mirror")
        dst = Path(args.local) if args.local else (root / mirror_subdir / remote_name)
        dst = dst if dst.is_absolute() else (root / dst).resolve()
        dst.mkdir(parents=True, exist_ok=True)
        cmd = [str(rclone), "sync", src, str(dst)]
        if args.dry_run:
            cmd.append("--dry-run")
        # safe defaults
        cmd.extend(["--create-empty-src-dirs", "--progress"])
        rc = run_cmd(run_dir, cmd)
        if rc != 0:
            die(f"rclone sync failed rc={rc}. See {run_dir / 'LOGS' / 'rclone_stdout.log'}", rc)
        print("OK synced", src, "->", str(dst))
        return 0

    if args.cmd == "mount":
        rp = (args.remote_path or "").lstrip("/")
        src = f"{remote_name}:{('/' + rp) if rp else ''}"
        mnt = Path(args.mount)
        if not mnt.exists():
            die("Mount point does not exist; create it first.")
        cmd = [str(rclone), "mount", src, str(mnt), "--vfs-cache-mode", "writes"]
        print("Starting mount. Press Ctrl+C to stop.")
        rc = run_cmd(run_dir, cmd)
        return rc

    die("Unhandled command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
