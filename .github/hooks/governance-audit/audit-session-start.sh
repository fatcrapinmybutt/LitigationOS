#!/usr/bin/env bash
# Governance Audit — Session Start Hook
# Logs session start event for governance audit trail

set -euo pipefail

LOG_DIR="logs/copilot/governance"
LOG_FILE="${LOG_DIR}/audit.log"
GOVERNANCE_LEVEL="${GOVERNANCE_LEVEL:-standard}"

# Skip if disabled
[ "${SKIP_GOVERNANCE_AUDIT:-}" = "true" ] && exit 0

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Log session start
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
EVENT="{\"timestamp\":\"${TIMESTAMP}\",\"event\":\"session_start\",\"governance_level\":\"${GOVERNANCE_LEVEL}\",\"cwd\":\"$(pwd)\"}"

echo "${EVENT}" >> "${LOG_FILE}"
