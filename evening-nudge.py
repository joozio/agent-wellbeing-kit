#!/usr/bin/env python3
"""
Evening Nudges - Wind-down + Bedtime

Wind-down (default): Remind to enjoy the evening.
Bedtime (--bedtime): Nudge for sleep.

Run modes:
    python3 evening-nudge.py              # Wind-down nudge
    python3 evening-nudge.py --bedtime    # Bedtime nudge
    python3 evening-nudge.py --dry-run    # Print without sending
"""

import json
import sys
from datetime import datetime, date
from pathlib import Path

WELLBEING_DIR = Path(__file__).resolve().parent
STATE_FILE = WELLBEING_DIR / "state.json"
CONFIG_FILE = WELLBEING_DIR / "config.json"

from messaging import send_message

EVENING_MESSAGES = [
    "Your evening. Do something you enjoy. The work will be there tomorrow.",
    "Evening time. Step away from the screens. You've done enough today.",
    "Wind-down time. Whatever makes you happy tonight.",
]

BEDTIME_MESSAGES = [
    "Bedtime. Sleep is the best investment. Good night.",
    "Time to wind down. Good night.",
    "Bed now = full sleep. Good night.",
]


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}


def already_sent_today(state, key):
    sent_at = state.get(key)
    if not sent_at:
        return False
    try:
        return datetime.fromisoformat(sent_at).date() == date.today()
    except Exception:
        return False


def pick_message(messages):
    """Rotate through messages based on day of year."""
    day_num = datetime.now().timetuple().tm_yday
    return messages[day_num % len(messages)]


def evening_nudge(dry_run=False):
    state = load_state()
    if not dry_run and already_sent_today(state, "evening_nudge_sent_at"):
        print("Evening nudge already sent today, skipping")
        return

    msg = pick_message(EVENING_MESSAGES)

    if dry_run:
        print(f"[dry-run] Would send: {msg}")
        return

    if send_message(msg, "evening"):
        state["evening_nudge_sent_at"] = datetime.now().isoformat()
        save_state(state)
        print(f"Evening nudge sent: {msg}")


def bedtime_nudge(dry_run=False):
    state = load_state()
    if not dry_run and already_sent_today(state, "bedtime_nudge_sent_at"):
        print("Bedtime nudge already sent today, skipping")
        return

    config = load_config()
    bedtime = config.get("routine", {}).get("bedtime", "23:00")
    wake_time = config.get("routine", {}).get("wake_time", "07:00")

    # Calculate sleep hours
    bh, bm = map(int, bedtime.split(":"))
    wh, wm = map(int, wake_time.split(":"))
    sleep_hours = (wh + wm/60) - (bh + bm/60)
    if sleep_hours < 0:
        sleep_hours += 24

    msg = pick_message(BEDTIME_MESSAGES)

    if dry_run:
        print(f"[dry-run] Would send: {msg}")
        return

    if send_message(msg, "bedtime"):
        state["bedtime_nudge_sent_at"] = datetime.now().isoformat()
        save_state(state)
        print(f"Bedtime nudge sent: {msg}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if "--bedtime" in sys.argv:
        bedtime_nudge(dry_run)
    else:
        evening_nudge(dry_run)
