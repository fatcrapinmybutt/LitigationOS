#!/usr/bin/env bash
# Session Logger — Session End Hook
# Logs session end event

set -euo pipefail

LOG_DIR="logs/copilot"
LOG_FILE="${LOG_DIR}/session.log"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Skip if disabled
[ "${SKIP_LOGGING:-}" = "true" ] && exit 0
[ "${LOG_LEVEL}" = "ERROR" ] && exit 0

mkdir -p "${LOG_DIR}"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
EVENT="{\"timestamp\":\"${TIMESTAMP}\",\"event\":\"sessionEnd\",\"level\":\"${LOG_LEVEL}\"}"

echo "${EVENT}" >> "${LOG_FILE}"
