#!/usr/bin/env bash
# Session Logger — Prompt Submission Hook
# Logs prompt submission events (no prompt content for privacy)

set -euo pipefail

LOG_DIR="logs/copilot"
PROMPT_LOG="${LOG_DIR}/prompts.log"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Skip if disabled
[ "${SKIP_LOGGING:-}" = "true" ] && exit 0
[ "${LOG_LEVEL}" = "ERROR" ] && exit 0

mkdir -p "${LOG_DIR}"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
EVENT="{\"timestamp\":\"${TIMESTAMP}\",\"event\":\"promptSubmitted\",\"level\":\"${LOG_LEVEL}\"}"

echo "${EVENT}" >> "${PROMPT_LOG}"
