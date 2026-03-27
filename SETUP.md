# Agent Wellbeing Kit - Setup Guide

Get running in 5 minutes.

## Quick Start

1. Copy the config template:
   ```bash
   cp config.example.json config.json
   ```

2. Edit `config.json`:
   - Set your `location` (city name, for weather-based morning suggestions)
   - Set your `wake_time` and `bedtime`
   - Choose your `messaging.channel` (see Messaging section below)
   - Optionally configure `error_registry` thresholds
   - Optionally add `memory_health.paths` for memory monitoring

3. Test it:
   ```bash
   python3 morning-nudge.py --dry-run
   python3 evening-nudge.py --dry-run
   python3 quiet_hours.py --status
   python3 error_registry.py --summary
   ```

4. Schedule with cron or LaunchAgent (see Scheduling section below).

## Files

| File | What it does |
|------|-------------|
| `config.example.json` | Template config (copy to `config.json`) |
| `utils.py` | Shared utilities (state, config loading) |
| `morning-nudge.py` | 7:00 AM nudge with weather + activity suggestion |
| `evening-nudge.py` | 19:30 wind-down + 23:00 bedtime nudge |
| `weekly-checkin.py` | Sunday summary: routine days, screen-free evenings, bedtime adherence |
| `quiet_hours.py` | Message gating library + CLI tool |
| `error_registry.py` | Silent failure detection for agent logs |
| `memory_health.py` | Memory file health checker |
| `messaging.py` | Multi-channel messaging abstraction |
| `dispatch.sh` | Single entry point for all nudges |
| `dashboard.html` | Visual overview (open in browser, load state.json) |
| `state.json` | Auto-created. Tracks sent nudges, weekly stats, error/memory state |

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

See `examples/launchagent.plist` for a ready-to-use template. Copy it, update the path, and load:

```bash
cp examples/launchagent.plist ~/Library/LaunchAgents/com.agent.wellbeing.plist
# Edit the path in the plist file
launchctl load ~/Library/LaunchAgents/com.agent.wellbeing.plist
```

### Linux (cron)

See `examples/crontab.example` or add these lines to your crontab (`crontab -e`):

```
0 7 * * * /path/to/agent-wellbeing-kit/dispatch.sh
0 8 * * 1-5 /path/to/agent-wellbeing-kit/dispatch.sh
30 19 * * * /path/to/agent-wellbeing-kit/dispatch.sh
0 23 * * * /path/to/agent-wellbeing-kit/dispatch.sh
```

### Claude Code / AI Agent

Point your agent at this folder in CLAUDE.md. See `examples/CLAUDE.md` for a ready-to-paste snippet.

Your agent can call `quiet_hours.py --check` before sending notifications to respect your boundaries.

## Customization

Everything is in `config.json`. Common changes:

- **Different wake time**: Change `routine.wake_time`
- **No morning followup**: Remove the 08:00 schedule entry
- **Different bedtime**: Change `routine.bedtime` and the 23:00 schedule
- **Add lunch break**: Add a new quiet_hours window
- **Change activities**: Edit `routine.activities` with your preferred activities
- **Emergency overrides**: Add keywords to `emergency_keywords`
- **Error sensitivity**: Adjust `error_registry.repeat_threshold` and `loop_threshold`
- **Memory monitoring**: Add file paths to `memory_health.paths`

## Philosophy

Advisory, not blocking. You are an adult.

These are nudges, not gates. Your agent reminds you, but never prevents you from working. The goal is awareness, not restriction.

Built from a real production system that runs every day.
