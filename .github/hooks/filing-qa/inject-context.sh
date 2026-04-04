#!/usr/bin/env bash
# Filing QA — Session Start Context Injection (POSIX version)

set -euo pipefail

LOG_DIR="logs/copilot/filing-qa"
mkdir -p "$LOG_DIR"

[[ "${SKIP_FILING_QA:-}" == "true" ]] && exit 0

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LAST_CONTACT="2025-07-29"

# Compute separation days
LAST_EPOCH=$(date -d "$LAST_CONTACT" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$LAST_CONTACT" +%s 2>/dev/null || echo 0)
NOW_EPOCH=$(date +%s)
SEPARATION_DAYS=$(( (NOW_EPOCH - LAST_EPOCH) / 86400 ))

echo "{\"timestamp\":\"$TIMESTAMP\",\"event\":\"session_context_injected\",\"separation_days\":$SEPARATION_DAYS}" >> "$LOG_DIR/qa.log"

echo "SEPARATION_DAYS=$SEPARATION_DAYS"
echo "LAST_CONTACT=$LAST_CONTACT"

exit 0
