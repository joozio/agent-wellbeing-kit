#!/usr/bin/env python3
"""
Weekly Wellbeing Check-in

Summarizes the week's routine adherence:
- Morning routine days
- CLI-free evenings
- Bedtime adherence
- Current streak

Run modes:
    python3 weekly-checkin.py              # Send check-in
    python3 weekly-checkin.py --dry-run    # Print without sending
"""

import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

WELLBEING_DIR = Path(__file__).resolve().parent
STATE_FILE = WELLBEING_DIR / "state.json"

from messaging import send_message


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_week_dates():
    """Get the 7 dates of the current week (Mon-Sun)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def generate_checkin(dry_run=False):
    state = load_state()
    weekly = state.get("weekly_stats", {})

    week_dates = get_week_dates()
    total_days = min(7, (date.today() - week_dates[0]).days + 1)

    # Morning routine days
    routine_days = weekly.get("routine_days", [])
    routine_count = len([d for d in routine_days if d in [x.isoformat() for x in week_dates]])

    # CLI-free evenings
    evening_sessions = weekly.get("evening_cli_sessions", [])
    cli_free_count = total_days - len([d for d in evening_sessions if d in [x.isoformat() for x in week_dates]])

    # Bedtime adherence
    bedtime_breaches = weekly.get("bedtime_breaches", [])
    bedtime_good = total_days - len([d for d in bedtime_breaches if d in [x.isoformat() for x in week_dates]])

    streak = weekly.get("streak", 0)

    # Build message
    lines = [f"Weekly check-in ({week_dates[0].strftime('%b %d')} - {week_dates[-1].strftime('%b %d')}):"]
    lines.append(f"Morning routine: {routine_count}/{total_days} days")
    lines.append(f"Screen-free evenings: {cli_free_count}/{total_days}")
    lines.append(f"In bed on time: {bedtime_good}/{total_days}")

    if streak > 0:
        lines.append(f"Streak: {streak} days")

    # Overall assessment
    score = routine_count + cli_free_count + bedtime_good
    max_score = total_days * 3
    if max_score > 0:
        pct = score / max_score
        if pct >= 0.8:
            lines.append("Strong week.")
        elif pct >= 0.6:
            lines.append("Decent week. Room to improve.")
        elif pct >= 0.4:
            lines.append("Mixed week. Tomorrow is a fresh start.")
        else:
            lines.append("Rough week. But you're aware of it. That matters.")

    msg = "\n".join(lines)

    if dry_run:
        print(f"[dry-run] Would send:\n{msg}")
        return

    if send_message(msg, "checkin"):
        state["weekly_stats"] = {
            "week_start": (date.today() + timedelta(days=1)).isoformat(),
            "routine_days": [],
            "cli_free_evenings": [],
            "evening_cli_sessions": [],
            "bedtime_breaches": [],
            "streak": streak,
        }
        save_state(state)
        print(f"Weekly check-in sent:\n{msg}")
    else:
        print("Failed to send weekly check-in", file=sys.stderr)


if __name__ == "__main__":
    generate_checkin(dry_run="--dry-run" in sys.argv)
