#!/usr/bin/env python3
"""Shared utilities for the wellbeing kit."""

import json
import os
import sys
import tempfile
from datetime import datetime, date
from pathlib import Path

WELLBEING_DIR = Path(__file__).resolve().parent
STATE_FILE = WELLBEING_DIR / "state.json"
CONFIG_FILE = WELLBEING_DIR / "config.json"


def load_state():
    """Load persistent state from state.json."""
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state):
    """Write state back to state.json atomically (temp file + rename).

    The temp file name is unique per call, so two processes saving at once
    (a cron nudge and an agent's health check) cannot rename each other's file.
    """
    fd, tmp = tempfile.mkstemp(dir=str(STATE_FILE.parent), prefix=".state.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(state, indent=2))
        os.replace(tmp, str(STATE_FILE))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_config():
    """Load configuration from config.json."""
    try:
        return json.loads(CONFIG_FILE.read_text())
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Warning: cannot read {CONFIG_FILE} ({e}). Using defaults.", file=sys.stderr)
        return {}


def already_sent_today(state, key):
    """Check if a nudge identified by key was already sent today."""
    sent_at = state.get(key)
    if not sent_at:
        return False
    try:
        return datetime.fromisoformat(sent_at).date() == date.today()
    except Exception:
        return False
