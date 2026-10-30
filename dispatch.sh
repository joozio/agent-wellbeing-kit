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

# Morning and bedtime hours follow routine.wake_time and routine.bedtime in
# config.json (defaults 07:00 and 23:00), so moving them together with the
# matching cron/LaunchAgent entry keeps the nudges firing.
read -r WAKE_HOUR BED_HOUR <<< "$("$PYTHON_BIN" -c '
import json, sys
try:
    routine = json.load(open(sys.argv[1])).get("routine", {})
except Exception:
    routine = {}
def hour(key, default):
    try:
        return int(str(routine.get(key) or default).split(":")[0]) % 24
    except ValueError:
        return default
print(hour("wake_time", 7), hour("bedtime", 23))
' "$SCRIPT_DIR/config.json" 2>/dev/null)"
WAKE_HOUR=${WAKE_HOUR:-7}
BED_HOUR=${BED_HOUR:-23}
FOLLOWUP_HOUR=$(( (WAKE_HOUR + 1) % 24 ))
NOW_HOUR=$((10#$HOUR))

if [ "$NOW_HOUR" -eq "$WAKE_HOUR" ]; then
    log "Morning nudge"
    "$PYTHON_BIN" "$SCRIPT_DIR/morning-nudge.py"
elif [ "$NOW_HOUR" -eq "$FOLLOWUP_HOUR" ]; then
    log "Morning followup"
    "$PYTHON_BIN" "$SCRIPT_DIR/morning-nudge.py" --followup
elif [ "$NOW_HOUR" -eq 19 ]; then
    log "Evening wind-down"
    "$PYTHON_BIN" "$SCRIPT_DIR/evening-nudge.py"
    # Sunday = weekly check-in
    if [ "$DOW" = "7" ]; then
        log "Weekly check-in (Sunday)"
        "$PYTHON_BIN" "$SCRIPT_DIR/weekly-checkin.py"
    fi
elif [ "$NOW_HOUR" -eq "$BED_HOUR" ]; then
    log "Bedtime nudge"
    "$PYTHON_BIN" "$SCRIPT_DIR/evening-nudge.py" --bedtime
else
    log "No scheduled action for hour $HOUR"
fi
