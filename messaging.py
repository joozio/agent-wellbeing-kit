#!/usr/bin/env python3
"""
Messaging abstraction layer for wellbeing nudges.

Reads config.json to determine the output channel and sends messages accordingly.
Supports: cli, imessage, telegram, slack, webhook.
"""

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent / "config.json"


def _load_config():
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}


def send_message(text, msg_type="nudge"):
    """Send a message via the configured channel.

    Args:
        text: Message content
        msg_type: One of morning, evening, bedtime, checkin, nudge
    Returns:
        True if sent successfully
    """
    config = _load_config()
    messaging = config.get("messaging", {"channel": "cli"})
    channel = messaging.get("channel", "cli")

    if channel == "cli":
        print(f"[wellbeing] {text}")
        return True

    elif channel == "imessage":
        recipient = messaging.get("imessage_recipient", "")
        if not recipient:
            print("Error: imessage_recipient not set in config.json", file=sys.stderr)
            return False
        try:
            script = f'tell application "Messages" to send "{text}" to buddy "{recipient}" of (1st account whose service type = iMessage)'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            print(f"iMessage send failed: {e}", file=sys.stderr)
            return False

    elif channel == "telegram":
        token = messaging.get("telegram_bot_token", "")
        chat_id = messaging.get("telegram_chat_id", "")
        if not token or not chat_id:
            print("Error: telegram_bot_token and telegram_chat_id required", file=sys.stderr)
            return False
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = json.dumps({"chat_id": chat_id, "text": text}).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception as e:
            print(f"Telegram send failed: {e}", file=sys.stderr)
            return False

    elif channel == "slack":
        webhook_url = messaging.get("slack_webhook_url", "")
        if not webhook_url:
            print("Error: slack_webhook_url required", file=sys.stderr)
            return False
        try:
            data = json.dumps({"text": text}).encode()
            req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception as e:
            print(f"Slack send failed: {e}", file=sys.stderr)
            return False

    elif channel == "webhook":
        webhook_url = messaging.get("webhook_url", "")
        if not webhook_url:
            print("Error: webhook_url required", file=sys.stderr)
            return False
        try:
            payload = json.dumps({"text": text, "type": msg_type}).encode()
            method = messaging.get("webhook_method", "POST")
            req = urllib.request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"}, method=method)
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception as e:
            print(f"Webhook send failed: {e}", file=sys.stderr)
            return False

    else:
        print(f"Unknown messaging channel: {channel}", file=sys.stderr)
        return False
