# Agent Wellbeing Kit - Setup Guide

Get running in 5 minutes.

## Quick Start

1. Copy this folder into your agent's automation directory:
   ```
   cp -r agent-wellbeing-kit ~/your-agent/automation/wellbeing/
   ```

2. Edit `config.json`:
   - Set your `location` (for weather-based morning suggestions)
   - Set your `wake_time` and `bedtime`
   - Choose your `messaging.channel` (see Messaging section below)

3. Test it:
   ```
   python3 morning-nudge.py --dry-run
   python3 evening-nudge.py --dry-run
   python3 quiet_hours.py --status
   ```

4. Schedule with cron or LaunchAgent (see Scheduling section below).

## Files

| File | What it does |
|------|-------------|
| `config.json` | All settings: quiet hours, routine, messaging channel |
| `morning-nudge.py` | 7:00 AM nudge with weather + activity suggestion |
| `evening-nudge.py` | 19:30 wind-down + 23:00 bedtime nudge |
| `weekly-checkin.py` | Sunday summary: routine days, CLI-free evenings, bedtime adherence |
| `quiet_hours.py` | Message gating library + CLI tool |
| `dispatch.sh` | Single entry point for all nudges |
| `state.json` | Auto-created. Tracks sent nudges and weekly stats |

## Messaging Channels

Edit `config.json` > `messaging.channel` to choose how nudges reach you:

### CLI (default)
```json
"messaging": { "channel": "cli" }
```
Prints to stdout. Good for testing or if your agent has a terminal.

### iMessage (macOS only)
```json
"messaging": {
  "channel": "imessage",
  "imessage_recipient": "+1234567890"
}
```
Uses AppleScript. Must be on a Mac with Messages.app signed in.

### Telegram
```json
"messaging": {
  "channel": "telegram",
  "telegram_bot_token": "YOUR_BOT_TOKEN",
  "telegram_chat_id": "YOUR_CHAT_ID"
}
```

### Slack
```json
"messaging": {
  "channel": "slack",
  "slack_webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
}
```

### Webhook (generic)
```json
"messaging": {
  "channel": "webhook",
  "webhook_url": "https://your-endpoint.com/nudge",
  "webhook_method": "POST"
}
```
Sends JSON: `{ "text": "message", "type": "morning|evening|bedtime|checkin" }`

## Scheduling

### macOS (LaunchAgent)

Save as `~/Library/LaunchAgents/com.agent.wellbeing.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.agent.wellbeing</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/path/to/agent-wellbeing-kit/dispatch.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>19</integer><key>Minute</key><integer>30</integer></dict>
    <dict><key>Hour</key><integer>23</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  <key>StandardOutPath</key>
  <string>/tmp/wellbeing.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/wellbeing-error.log</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.agent.wellbeing.plist
```

### Linux (cron)

```
0 7 * * * /path/to/agent-wellbeing-kit/dispatch.sh
0 8 * * 1-5 /path/to/agent-wellbeing-kit/dispatch.sh
30 19 * * * /path/to/agent-wellbeing-kit/dispatch.sh
0 23 * * * /path/to/agent-wellbeing-kit/dispatch.sh
```

### Claude Code / AI Agent

Point your agent at this folder in CLAUDE.md:
```
## Wellbeing
Wellbeing system in automation/wellbeing/. Config: config.json.
Quiet hours check: python3 quiet_hours.py --check --tag "your-tag"
```

Your agent can call `quiet_hours.py --check` before sending notifications to respect your boundaries.

## Customization

Everything is in `config.json`. Common changes:

- **Different wake time**: Change `routine.wake_time`
- **No morning followup**: Remove the 08:00 schedule entry
- **Different bedtime**: Change `routine.bedtime` and the 23:00 schedule
- **Add lunch break**: Add a new quiet_hours window
- **Change activities**: Edit `routine.apps` with your preferred apps
- **Emergency overrides**: Add keywords to `emergency_keywords`

## Philosophy

Advisory, not blocking. You are an adult.

These are nudges, not gates. Your agent reminds you, but never prevents you from working. The goal is awareness, not restriction.

Built from a real production system that runs every day.
