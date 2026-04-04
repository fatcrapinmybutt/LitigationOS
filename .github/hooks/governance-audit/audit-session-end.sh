#!/usr/bin/env bash
# Governance Audit — Session End Hook
# Logs session end with threat summary

set -euo pipefail

LOG_DIR="logs/copilot/governance"
LOG_FILE="${LOG_DIR}/audit.log"

# Skip if disabled
[ "${SKIP_GOVERNANCE_AUDIT:-}" = "true" ] && exit 0

mkdir -p "${LOG_DIR}"

# Count threats from this session (if jq available)
THREAT_COUNT=0
if command -v jq &>/dev/null && [ -f "${LOG_FILE}" ]; then
    THREAT_COUNT=$(grep -c '"event":"threat_detected"' "${LOG_FILE}" 2>/dev/null || echo 0)
fi

TOTAL_EVENTS=$(wc -l < "${LOG_FILE}" 2>/dev/null || echo 0)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
EVENT="{\"timestamp\":\"${TIMESTAMP}\",\"event\":\"session_end\",\"total_events\":${TOTAL_EVENTS},\"threats_detected\":${THREAT_COUNT}}"

echo "${EVENT}" >> "${LOG_FILE}"
