#!/usr/bin/env bash
set -euo pipefail

INPUT_ZIP=""
CANON=""
STATE="state.json"
CONFIG="config.yaml"
WORKDIR="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input-zip) INPUT_ZIP="$2"; shift 2;;
    --canon) CANON="$2"; shift 2;;
    --state) STATE="$2"; shift 2;;
    --config) CONFIG="$2"; shift 2;;
    --workdir) WORKDIR="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "$INPUT_ZIP" || -z "$CANON" ]]; then
  echo "Usage: ./run_linux.sh --input-zip /path/to/zip --canon /path/to/canon.txt"
  exit 1
fi

cd "$WORKDIR"
python3 -m venv .venv || true
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python cycle_runner.py --input-zip "$INPUT_ZIP" --canon "$CANON" --state "$STATE" --config "$CONFIG"
