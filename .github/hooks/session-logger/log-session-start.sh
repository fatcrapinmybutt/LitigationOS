#!/usr/bin/env bash
# Session Logger — Session Start Hook
# Logs session start event for audit trail

set -euo pipefail

LOG_DIR="logs/copilot"
LOG_FILE="${LOG_DIR}/session.log"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Skip if disabled
[ "${SKIP_LOGGING:-}" = "true" ] && exit 0
[ "${LOG_LEVEL}" = "ERROR" ] && exit 0

mkdir -p "${LOG_DIR}"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
EVENT="{\"timestamp\":\"${TIMESTAMP}\",\"event\":\"sessionStart\",\"cwd\":\"$(pwd)\",\"level\":\"${LOG_LEVEL}\"}"

echo "${EVENT}" >> "${LOG_FILE}"
