#!/usr/bin/env python3
"""
nucleus_bundle_autopilot.py

Bundle: NucleusWheel_AllInOne_v3
Purpose:
    Orchestrate ALL graph + module work INSIDE THIS SAME BUNDLE:

    - Watch canonical intake paths on F:\LINKY:
        F:\LINKY\INTAKE\police_txt         -> tools\parse_nspd.bat
        F:\LINKY\INTAKE\texts              -> tools\crosswire_authorities.bat
        F:\LINKY\INTAKE\conversations.json -> tools\ingest_chatgpt.bat (if present)

    - Write all parsed/derived artifacts to:
        modules\out\   (already used by your existing modules)

    - After any new/updated data:
        Run run_windows.bat to rebuild the Nucleus Wheel bundle and viewer.

    - Maintain a small state JSON so we only re-run modules + builder when needed:
        OUT\autopilot_state.json

    - Log to:
        OUT\autopilot.log

Usage:

    # One-shot (scan → run modules if needed → rebuild viewer → exit)
    py -3 nucleus_bundle_autopilot.py --once

    # Continuous loop (scan every 60s, rebuild as needed)
    py -3 nucleus_bundle_autopilot.py --loop

Environment assumptions:

    - You are running this from inside the bundle folder:
        C:\Users\andre\Desktop\NucleusWheel_AllInOne_v3
      which contains:
        run_windows.bat
        tools\parse_nspd.bat
        tools\crosswire_authorities.bat
        tools\ingest_chatgpt.bat
        modules\out\
        OUT\

    - F:\LINKY exists and may contain:
        F:\LINKY\INTAKE\police_txt
        F:\LINKY\INTAKE\texts
        F:\LINKY\INTAKE\conversations.json
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


# === CONFIG SECTION ==========================================================

# Bundle root = folder containing this script (NucleusWheel_AllInOne_v3)
BUNDLE_ROOT: Path = Path(__file__).resolve().parent

# Canonical intake root on F:
LINKY_ROOT: Path = Path("F:/LINKY")

POLICE_TXT_DIR: Path = LINKY_ROOT / "INTAKE" / "police_txt"
TEXTS_DIR: Path = LINKY_ROOT / "INTAKE" / "texts"
CONVERSATIONS_FILE: Path = LINKY_ROOT / "INTAKE" / "conversations.json"

# Tools inside this same bundle
TOOLS_DIR: Path = BUNDLE_ROOT / "tools"
PARSE_NSPD_BAT: Path = TOOLS_DIR / "parse_nspd.bat"
CROSSWIRE_AUTHORITIES_BAT: Path = TOOLS_DIR / "crosswire_authorities.bat"
INGEST_CHATGPT_BAT: Path = TOOLS_DIR / "ingest_chatgpt.bat"

# Nucleus wheel builder batch (already present in your bundle)
RUN_WINDOWS_BAT: Path = BUNDLE_ROOT / "run_windows.bat"

# Output/log/state inside the same bundle
OUT_DIR: Path = BUNDLE_ROOT / "OUT"
STATE_PATH: Path = OUT_DIR / "autopilot_state.json"
LOG_PATH: Path = OUT_DIR / "autopilot.log"

# Poll interval in seconds when running in loop mode
DEFAULT_LOOP_INTERVAL_SECONDS: int = 60


# === UTILS ===================================================================

def ensure_out_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {
            "police_latest_mtime": None,
            "texts_latest_mtime": None,
            "conversations_mtime": None,
            "last_builder_run": None,
        }
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {
            "police_latest_mtime": None,
            "texts_latest_mtime": None,
            "conversations_mtime": None,
            "last_builder_run": None,
        }


def save_state(state: Dict[str, Any]) -> None:
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


def get_latest_mtime(path: Path) -> Optional[float]:
    """
    If path is file: return its mtime.
    If path is directory: walk it and return max mtime of all files.
    If nothing exists / no files: return None.
    """
    if not path.exists():
        return None
    if path.is_file():
        try:
            return path.stat().st_mtime
        except FileNotFoundError:
            return None
    # directory
    latest: Optional[float] = None
    for p in path.rglob("*"):
        if not p.is_file():
            continue
        try:
            m = p.stat().st_mtime
        except FileNotFoundError:
            continue
        if latest is None or m > latest:
            latest = m
    return latest


def run_bat(logger: logging.Logger, bat_path: Path, args: Optional[list] = None) -> Tuple[bool, str]:
    """
    Run a .bat file via cmd.exe /c inside this bundle.
    """
    if args is None:
        args = []
    if not bat_path.exists():
        msg = f"Batch file not found: {bat_path}"
        logger.error(msg)
        return False, msg

    cmd = ["cmd.exe", "/c", str(bat_path)] + args
    logger.info("Running: %s", " ".join(cmd))
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(BUNDLE_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert proc.stdout is not None
        output_lines = []
        for line in proc.stdout:
            line = line.rstrip("\n")
            output_lines.append(line)
            logger.info("[BAT] %s", line)
        proc.wait()
        if proc.returncode == 0:
            return True, "ok"
        msg = f"exit code {proc.returncode}"
        logger.error("Batch failed: %s", msg)
        return False, msg
    except Exception as e:
        msg = f"exception: {e}"
        logger.exception("Batch failed: %s", e)
        return False, msg


def setup_logger() -> logging.Logger:
    ensure_out_dir()
    logger = logging.getLogger("NUCLEUS_AUTOPILOT")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


# === CORE AUTOPILOT LOGIC ====================================================

def run_cycle(logger: logging.Logger, force_modules: bool = False, force_builder: bool = False) -> None:
    """
    One full cycle:
      1. Check intake dirs/files for changes.
      2. Run modules whose inputs changed (or force_modules=True).
      3. If any module ran or force_builder=True, run run_windows.bat to rebuild the viewer.
      4. Update state.
    """
    state = load_state()
    logger.info("=== AUTOPILOT CYCLE START ===")

    # Detect changes
    police_mtime = get_latest_mtime(POLICE_TXT_DIR)
    texts_mtime = get_latest_mtime(TEXTS_DIR)
    conv_mtime = get_latest_mtime(CONVERSATIONS_FILE)

    logger.info("Current mtimes -> police=%s texts=%s conversations=%s",
                police_mtime, texts_mtime, conv_mtime)

    prev_police = state.get("police_latest_mtime")
    prev_texts = state.get("texts_latest_mtime")
    prev_conv = state.get("conversations_mtime")

    police_changed = force_modules or (police_mtime is not None and police_mtime != prev_police)
    texts_changed = force_modules or (texts_mtime is not None and texts_mtime != prev_texts)
    conv_changed = force_modules or (conv_mtime is not None and conv_mtime != prev_conv)

    any_module_ran = False

    # 1) Police reports (NSPD text)
    if police_changed and police_mtime is not None:
        if POLICE_TXT_DIR.exists():
            logger.info("Detected change in police_txt; running parse_nspd module.")
            ok, msg = run_bat(logger, PARSE_NSPD_BAT, ["--in", str(POLICE_TXT_DIR), "--out", "modules\\out"])
            if ok:
                any_module_ran = True
                state["police_latest_mtime"] = police_mtime
            else:
                logger.error("parse_nspd failed: %s", msg)
        else:
            logger.warning("POLICE_TXT_DIR does not exist: %s", POLICE_TXT_DIR)

    # 2) Authority cross-wiring (texts)
    if texts_changed and texts_mtime is not None:
        if TEXTS_DIR.exists():
            logger.info("Detected change in texts; running crosswire_authorities module.")
            ok, msg = run_bat(logger, CROSSWIRE_AUTHORITIES_BAT, ["--in", str(TEXTS_DIR), "--out", "modules\\out"])
            if ok:
                any_module_ran = True
                state["texts_latest_mtime"] = texts_mtime
            else:
                logger.error("crosswire_authorities failed: %s", msg)
        else:
            logger.warning("TEXTS_DIR does not exist: %s", TEXTS_DIR)

    # 3) ChatGPT ingest (conversations.json)
    if conv_changed and conv_mtime is not None:
        if CONVERSATIONS_FILE.exists():
            logger.info("Detected change in conversations.json; running ingest_chatgpt module.")
            ok, msg = run_bat(
                logger,
                INGEST_CHATGPT_BAT,
                ["--in", str(CONVERSATIONS_FILE), "--out", "modules\\out"],
            )
            if ok:
                any_module_ran = True
                state["conversations_mtime"] = conv_mtime
            else:
                logger.error("ingest_chatgpt failed: %s", msg)
        else:
            logger.warning("CONVERSATIONS_FILE does not exist: %s", CONVERSATIONS_FILE)

    # 4) If any module ran or builder is forced, rebuild Nucleus Wheel
    if any_module_ran or force_builder:
        logger.info("Modules changed or builder forced -> running run_windows.bat to rebuild nucleus wheel.")
        ok, msg = run_bat(logger, RUN_WINDOWS_BAT, [])
        if ok:
            logger.info("Nucleus wheel rebuilt successfully.")
            state["last_builder_run"] = time.time()
        else:
            logger.error("Nucleus wheel rebuild failed: %s", msg)
    else:
        logger.info("No module changes detected and builder not forced; skipping rebuild.")

    save_state(state)
    logger.info("=== AUTOPILOT CYCLE END ===")


# === CLI / ENTRYPOINT ========================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NucleusWheel_AllInOne_v3 bundle autopilot orchestrator (single bundle only)."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single cycle and exit.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuous cycles; defaults to 60-second interval.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_LOOP_INTERVAL_SECONDS,
        help=f"Loop interval in seconds (default={DEFAULT_LOOP_INTERVAL_SECONDS}).",
    )
    parser.add_argument(
        "--force-modules",
        action="store_true",
        help="Force all modules to run even if inputs appear unchanged.",
    )
    parser.add_argument(
        "--force-builder",
        action="store_true",
        help="Force Nucleus Wheel builder (run_windows.bat) even if no modules ran.",
    )
    return parser.parse_args()


def main() -> None:
    ensure_out_dir()
    logger = setup_logger()
    args = parse_args()

    if not (args.once or args.loop):
        logger.info("No mode specified; defaulting to '--once'.")
        args.once = True

    logger.info("Bundle root: %s", BUNDLE_ROOT)
    logger.info("LINKY root: %s", LINKY_ROOT)
    logger.info("Mode: %s", "loop" if args.loop else "once")
    logger.info("Interval: %s seconds", args.interval)

    if args.once:
        run_cycle(logger, force_modules=args.force_modules, force_builder=args.force_builder)
        return

    # Loop mode
    try:
        while True:
            run_cycle(logger, force_modules=args.force_modules, force_builder=args.force_builder)
            logger.info("Sleeping %s seconds before next cycle.", args.interval)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, exiting autopilot.")


if __name__ == "__main__":
    main()
