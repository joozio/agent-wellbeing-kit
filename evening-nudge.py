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

from utils import load_state, save_state, already_sent_today
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
