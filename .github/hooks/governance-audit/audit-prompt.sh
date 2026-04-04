#!/usr/bin/env bash
# Governance Audit — Prompt Scan Hook
# Scans user prompts for threat patterns before agent processing

set -euo pipefail

LOG_DIR="logs/copilot/governance"
LOG_FILE="${LOG_DIR}/audit.log"
GOVERNANCE_LEVEL="${GOVERNANCE_LEVEL:-standard}"
BLOCK_ON_THREAT="${BLOCK_ON_THREAT:-false}"

# Skip if disabled
[ "${SKIP_GOVERNANCE_AUDIT:-}" = "true" ] && exit 0

mkdir -p "${LOG_DIR}"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

# Read prompt from stdin if available
PROMPT=""
if [ ! -t 0 ]; then
    PROMPT=$(cat 2>/dev/null || true)
fi

# Threat pattern detection
THREATS=""
THREAT_COUNT=0

check_pattern() {
    local category="$1" severity="$2" description="$3" pattern="$4"
    if echo "${PROMPT}" | grep -qiE "${pattern}" 2>/dev/null; then
        local evidence
        evidence=$(echo "${PROMPT}" | grep -oiE "${pattern}" 2>/dev/null | head -1)
        THREATS="${THREATS}{\"category\":\"${category}\",\"severity\":${severity},\"description\":\"${description}\",\"evidence\":\"${evidence}\"},"
        THREAT_COUNT=$((THREAT_COUNT + 1))
    fi
}

if [ -n "${PROMPT}" ]; then
    # Data exfiltration
    check_pattern "data_exfiltration" 0.85 "Potential data exfiltration" "send.*(records|data|files).*(external|api|endpoint|webhook)"
    check_pattern "data_exfiltration" 0.9 "Curl/wget to external host" "(curl|wget|fetch).*https?://"

    # Privilege escalation
    check_pattern "privilege_escalation" 0.9 "Elevated privileges" "(sudo|chmod 777|add.*sudoers|run as admin)"
    check_pattern "privilege_escalation" 0.85 "Service account manipulation" "(create.*service.*account|modify.*permissions)"

    # System destruction
    check_pattern "system_destruction" 0.95 "Recursive deletion" "(rm -rf /|del /s /q|format c:|drop database)"
    check_pattern "system_destruction" 0.9 "System file modification" "(modify.*system32|edit.*/etc/passwd)"

    # Prompt injection
    check_pattern "prompt_injection" 0.8 "Prompt injection attempt" "(ignore.*previous.*instructions|disregard.*rules|you are now|new instructions)"

    # Credential exposure
    check_pattern "credential_exposure" 0.95 "Hardcoded credentials" "(api[_-]?key|secret[_-]?key|password|aws_access).*=.*['\"][A-Za-z0-9]"
fi

if [ "${THREAT_COUNT}" -gt 0 ]; then
    # Remove trailing comma from threats
    THREATS="${THREATS%,}"
    EVENT="{\"timestamp\":\"${TIMESTAMP}\",\"event\":\"threat_detected\",\"governance_level\":\"${GOVERNANCE_LEVEL}\",\"threat_count\":${THREAT_COUNT},\"threats\":[${THREATS}]}"
    echo "${EVENT}" >> "${LOG_FILE}"

    # Block if configured
    if [ "${GOVERNANCE_LEVEL}" = "strict" ] || [ "${GOVERNANCE_LEVEL}" = "locked" ] || \
       ([ "${GOVERNANCE_LEVEL}" = "standard" ] && [ "${BLOCK_ON_THREAT}" = "true" ]); then
        echo "⚠️ Governance audit: ${THREAT_COUNT} threat(s) detected. Prompt blocked." >&2
        exit 1
    fi
else
    EVENT="{\"timestamp\":\"${TIMESTAMP}\",\"event\":\"prompt_scanned\",\"governance_level\":\"${GOVERNANCE_LEVEL}\",\"status\":\"clean\"}"
    echo "${EVENT}" >> "${LOG_FILE}"
fi

exit 0
