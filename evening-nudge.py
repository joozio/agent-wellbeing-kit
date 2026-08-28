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

import sys
from datetime import datetime

from utils import load_state, save_state, load_config, already_sent_today
from messaging import send_message

EVENING_MESSAGES = [
    "Your evening. Do something you enjoy. The work will be there tomorrow.",
    "Evening time. Step away from the screens. You've done enough today.",
    "Wind-down time. Whatever makes you happy tonight.",
    "Close the laptop. The agent keeps working. That's the point.",
    "Evening now. Go be a person for a few hours.",
    "Screens off. Anything left will still be there in the morning.",
    "Day's done. Cook something, read something, call someone.",
]

BEDTIME_MESSAGES = [
    "Bedtime. Sleep is the best investment. Good night.",
    "Time to wind down. Good night.",
    "Bed now = full sleep. Good night.",
    "Nothing good ships after midnight. Good night.",
    "Tomorrow's focus is built tonight. Bed.",
    "The inbox can wait eight hours. Good night.",
    "Lights out. You'll think better tomorrow for it.",
]


def get_messages(key, defaults):
    """Return the custom message pool from config, or the built-in defaults."""
    custom = load_config().get("messages", {}).get(key, [])
    return custom if custom else defaults


def pick_message(messages):
    """Rotate through messages based on day of year."""
    day_num = datetime.now().timetuple().tm_yday
    return messages[day_num % len(messages)]


def evening_nudge(dry_run=False):
    state = load_state()
    if not dry_run and already_sent_today(state, "evening_nudge_sent_at"):
        print("Evening nudge already sent today, skipping")
        return

    msg = pick_message(get_messages("evening", EVENING_MESSAGES))

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

    msg = pick_message(get_messages("bedtime", BEDTIME_MESSAGES))

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
