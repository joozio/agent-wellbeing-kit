#!/usr/bin/env python3
"""
Morning Routine Nudge

Sends a brief, warm message to start your morning routine.
Includes weather for your location and suggests outdoor vs indoor activity.

Run modes:
    python3 morning-nudge.py              # Main morning nudge
    python3 morning-nudge.py --followup   # Follow-up nudge (weekdays only)
    python3 morning-nudge.py --dry-run    # Print message without sending
"""

import json
import subprocess
import sys
from datetime import datetime, date

from utils import load_state, save_state, load_config, already_sent_today
from messaging import send_message


def get_weather(location):
    """Fetch current weather via wttr.in (free, no API key)."""
    if not location:
        return None
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", f"wttr.in/{location}?format=j1"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        desc = current["weatherDesc"][0]["value"].lower()
        precip_mm = float(current.get("precipMM", 0))
        return {
            "temp": int(temp_c),
            "desc": desc,
            "rainy": precip_mm > 0.5 or any(w in desc for w in ["rain", "drizzle", "shower", "snow", "sleet"]),
        }
    except Exception:
        return None


def suggest_activity(weather, config):
    """Suggest activity based on weather and config."""
    activities = config.get("routine", {}).get("activities", {})
    outdoor = activities.get("outdoor", "running")
    indoor = activities.get("indoor", "yoga or stretching")

    if weather is None:
        return f"{outdoor} or {indoor}"
    if weather["rainy"] or weather["temp"] < -5:
        return indoor
    return outdoor


def main_nudge(dry_run=False):
    state = load_state()
    if not dry_run and already_sent_today(state, "morning_nudge_sent_at"):
        print("Morning nudge already sent today, skipping")
        return

    config = load_config()
    location = config.get("routine", {}).get("location", "")
    today = datetime.now()
    is_weekend = today.weekday() >= 5
    weather = get_weather(location)

    if is_weekend:
        if weather:
            msg = f"Morning. {weather['temp']}C, {weather['desc']}. Routine when you're ready. Enjoy the day."
        else:
            msg = "Morning. Routine when you're ready. Enjoy the day."
    else:
        activity = suggest_activity(weather, config)
        if weather:
            msg = f"Morning. {weather['temp']}C, {weather['desc']}. Good day for {activity}."
        else:
            msg = f"Morning. Good day for {activity}."

    if dry_run:
        print(f"[dry-run] Would send: {msg}")
        return

    if send_message(msg, "morning"):
        state["morning_nudge_sent_at"] = datetime.now().isoformat()
        state["today_routine_suggestion"] = suggest_activity(weather, config)
        weekly = state.setdefault("weekly_stats", {})
        routine_days = weekly.setdefault("routine_days", [])
        today_str = date.today().isoformat()
        if today_str not in routine_days:
            routine_days.append(today_str)
        save_state(state)
        print(f"Morning nudge sent: {msg}")
    else:
        print("Failed to send morning nudge", file=sys.stderr)


def followup_nudge(dry_run=False):
    """Follow-up nudge, weekdays only."""
    if datetime.now().weekday() >= 5:
        print("Weekend, skipping followup")
        return

    state = load_state()
    if not dry_run and already_sent_today(state, "morning_followup_sent_at"):
        print("Followup already sent today, skipping")
        return

    msg = "Time to move."

    if dry_run:
        print(f"[dry-run] Would send: {msg}")
        return

    if send_message(msg, "morning"):
        state["morning_followup_sent_at"] = datetime.now().isoformat()
        save_state(state)
        print(f"Followup sent: {msg}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if "--followup" in sys.argv:
        followup_nudge(dry_run)
    else:
        main_nudge(dry_run)
