#!/bin/bash
#
# dispatch.sh - Wellbeing nudge dispatcher
#
# Called by LaunchAgent/cron at scheduled times.
# Routes to the correct Python script based on current hour.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOUR=$(date +"%H")
DOW=$(date +"%u")  # 1=Monday, 7=Sunday

log() {
    echo "[wellbeing $(date +%H:%M:%S)] $1"
}

case "$HOUR" in
    07)
        log "Morning nudge"
        "$PYTHON_BIN" "$SCRIPT_DIR/morning-nudge.py"
        ;;
    08)
        log "Morning followup"
        "$PYTHON_BIN" "$SCRIPT_DIR/morning-nudge.py" --followup
        ;;
    19)
        log "Evening wind-down"
        "$PYTHON_BIN" "$SCRIPT_DIR/evening-nudge.py"
        # Sunday = weekly check-in
        if [ "$DOW" = "7" ]; then
            log "Weekly check-in (Sunday)"
            "$PYTHON_BIN" "$SCRIPT_DIR/weekly-checkin.py"
        fi
        ;;
    23)
        log "Bedtime nudge"
        "$PYTHON_BIN" "$SCRIPT_DIR/evening-nudge.py" --bedtime
        ;;
    *)
        log "No scheduled action for hour $HOUR"
        ;;
esac
