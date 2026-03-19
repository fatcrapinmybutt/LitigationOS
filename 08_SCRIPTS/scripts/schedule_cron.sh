#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: ./schedule_cron.sh /path/to/input.zip /path/to/canon.txt [workdir] [minutes]"
  exit 1
fi

INPUT_ZIP="$1"
CANON="$2"
WORKDIR="${3:-$(pwd)}"
MINUTES="${4:-30}"

mkdir -p "${WORKDIR}/logs"

CRON_LINE="*/${MINUTES} * * * * cd ${WORKDIR} && ./run_linux.sh --input-zip \"${INPUT_ZIP}\" --canon \"${CANON}\" --workdir \"${WORKDIR}\" >> ${WORKDIR}/logs/cron.log 2>&1"

( crontab -l 2>/dev/null; echo "${CRON_LINE}" ) | crontab -
echo "Cron installed:"
echo "${CRON_LINE}"
