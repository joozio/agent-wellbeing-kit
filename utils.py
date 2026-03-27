#!/usr/bin/env python3
"""Shared utilities for the wellbeing kit."""

import json
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
    """Write state back to state.json."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_config():
    """Load configuration from config.json."""
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
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
