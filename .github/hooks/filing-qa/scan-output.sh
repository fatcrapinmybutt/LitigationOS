#!/usr/bin/env bash
# Filing QA — Output Scan Hook (POSIX version)
# Catches litigation-specific errors in AI-generated content

set -euo pipefail

LOG_DIR="logs/copilot/filing-qa"
LOG_FILE="$LOG_DIR/qa.log"

[[ "${SKIP_FILING_QA:-}" == "true" ]] && exit 0

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
CONTENT=$(cat 2>/dev/null || true)

[[ -z "$CONTENT" ]] && exit 0

VIOLATIONS=0
MESSAGES=""

check_pattern() {
    local rule="$1" severity="$2" desc="$3" pattern="$4" fix="$5"
    if echo "$CONTENT" | grep -qiP "$pattern"; then
        VIOLATIONS=$((VIOLATIONS + 1))
        MESSAGES="${MESSAGES}\n  [$severity] $desc: $fix"
    fi
}

# Rule 2: Child's full name
check_pattern 'R2' 'CRITICAL' 'Child full name exposed' 'L\.?\s*D\.?\s*W\w+' 'Use initials L.D.W. only'

# Rule 4: AI/DB references
check_pattern 'R4' 'HIGH' 'AI/DB reference in output' '(LitigationOS|litigation_context\.db|evidence_quotes|impeachment_matrix)' 'Strip AI/DB refs'

# Rule 10: Pro se
check_pattern 'R10' 'HIGH' 'Counsel language' '(undersigned counsel|attorney for plaintiff)' 'Use pro se language'

# Rule 13: Non-existent statute
check_pattern 'R13' 'HIGH' 'MCL 722.27c cited' 'MCL\s+722\.27c' 'Use MCL 722.23(j)'

# Rule 14: Brady in family law
check_pattern 'R14' 'MEDIUM' 'Brady v Maryland in family law' 'Brady\s+v\.?\s+Maryland' 'Use Mathews v Eldridge'

if [[ $VIOLATIONS -gt 0 ]]; then
    echo "{\"timestamp\":\"$TIMESTAMP\",\"event\":\"filing_qa_violations\",\"count\":$VIOLATIONS}" >> "$LOG_FILE"
    echo -e "⚠️ Filing QA: $VIOLATIONS violation(s)$MESSAGES" >&2
else
    echo "{\"timestamp\":\"$TIMESTAMP\",\"event\":\"filing_qa_passed\",\"status\":\"clean\"}" >> "$LOG_FILE"
fi

exit 0
