#!/usr/bin/env python3
"""
Quiet Hours - Message gating for wellbeing boundaries.

Shared library + CLI tool. Checks whether the current time falls in a
quiet-hours window and whether a given message tag is allowed through.

CLI usage:
    python3 quiet_hours.py --check [--tag TAG]
    python3 quiet_hours.py --status
    Exit 0 = OK to send, Exit 1 = suppressed (quiet hours)

Library usage:
    from quiet_hours import should_send_message
    if should_send_message(tag="health-monitor"):
        send_message(...)
"""

import json
import sys
from datetime import datetime, time
from pathlib import Path

WELLBEING_DIR = Path(__file__).resolve().parent
CONFIG_FILE = WELLBEING_DIR / "config.json"
SUPPRESSED_LOG = WELLBEING_DIR / "suppressed.jsonl"


def _load_config():
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {"enabled": False}


def _parse_time(t_str):
    h, m = t_str.split(":")
    return time(int(h), int(m))


def _in_window(now_time, start_str, end_str):
    """Check if now_time falls within [start, end). Handles overnight windows."""
    start = _parse_time(start_str)
    end = _parse_time(end_str)
    if start <= end:
        return start <= now_time < end
    else:
        return now_time >= start or now_time < end


def is_quiet_hours(now=None):
    """Return the active quiet-hours window name, or None."""
    config = _load_config()
    if not config.get("enabled", True):
        return None
    now_time = (now or datetime.now()).time()
    for name, window in config.get("quiet_hours", {}).items():
        if _in_window(now_time, window["start"], window["end"]):
            return name
    return None


def should_send_message(tag="", is_emergency=False, now=None):
    """Central gate for outbound messages. Returns True if OK to send."""
    if is_emergency:
        return True

    config = _load_config()
    if not config.get("enabled", True):
        return True

    emergency_keywords = config.get("emergency_keywords", [])
    if any(kw in tag.lower() for kw in emergency_keywords):
        return True

    window_name = is_quiet_hours(now)
    if window_name is None:
        return True

    window = config.get("quiet_hours", {}).get(window_name, {})
    allowed = window.get("allowed", [])
    return tag in allowed


def log_suppressed(tag, reason):
    """Log a suppressed message for transparency."""
    entry = {"timestamp": datetime.now().isoformat(), "tag": tag, "reason": reason}
    try:
        with open(SUPPRESSED_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Quiet hours check")
    parser.add_argument("--check", action="store_true", help="Check if message can be sent")
    parser.add_argument("--tag", default="", help="Message tag (e.g. 'wellbeing-nudge')")
    parser.add_argument("--emergency", action="store_true", help="Mark as emergency (always sends)")
    parser.add_argument("--status", action="store_true", help="Show current quiet hours status")
    args = parser.parse_args()

    if args.status:
        window = is_quiet_hours()
        if window:
            print(f"QUIET_HOURS: {window}")
        else:
            print("ACTIVE: not in quiet hours")
        sys.exit(0)

    if args.check:
        if should_send_message(tag=args.tag, is_emergency=args.emergency):
            sys.exit(0)
        else:
            window = is_quiet_hours()
            log_suppressed(args.tag, f"quiet_hours:{window}")
            sys.exit(1)

    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
