# Agent Wellbeing Kit

Advisory boundaries for AI agents and their humans. Quiet hours, morning/evening nudges, weekly check-ins. Built from a real production system that runs every day.

## Why

If you're building an AI agent that actually works, you'll eventually face this: you can produce unlimited output now. But you (the human) are still the receiver. The bottleneck moved from production to consumption. This kit helps you protect yourself from your own agent.

**Philosophy: advisory, not blocking.** You are an adult. These are nudges, not gates.

## What's Inside

| File | What it does |
|------|-------------|
| `config.json` | All settings: quiet hours, routine, messaging channel |
| `morning-nudge.py` | Weather-aware morning nudge with activity suggestions |
| `evening-nudge.py` | Wind-down (19:30) and bedtime (23:00) nudges |
| `weekly-checkin.py` | Sunday summary: routine days, screen-free evenings, sleep adherence |
| `quiet_hours.py` | Message gating library + CLI for respecting boundaries |
| `messaging.py` | Multi-channel abstraction (CLI, iMessage, Telegram, Slack, webhook) |
| `dispatch.sh` | Single entry point for LaunchAgent/cron scheduling |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/joozio/agent-wellbeing-kit.git
cd agent-wellbeing-kit

# 2. Configure
# Edit config.json: set your location, wake/bedtime, messaging channel
nano config.json

# 3. Test
python3 morning-nudge.py --dry-run
python3 evening-nudge.py --dry-run
python3 quiet_hours.py --status
```

Then schedule with cron or LaunchAgent. See [SETUP.md](SETUP.md) for full instructions.

## Messaging Channels

Set `messaging.channel` in `config.json`:

- **cli** (default) - prints to stdout
- **imessage** - macOS Messages.app via AppleScript
- **telegram** - via Bot API
- **slack** - via webhook
- **webhook** - generic HTTP endpoint (sends JSON)

## Example Output

```
[wellbeing] Morning. 12C, partly cloudy. Good day for a run.
```

```
[wellbeing] Weekly check-in (Mar 17 - Mar 23):
Morning routine: 5/7 days
Screen-free evenings: 3/7
In bed on time: 4/7
Decent week. Room to improve.
```

## Use With Your AI Agent

Add to your CLAUDE.md (or equivalent agent config):

```markdown
## Wellbeing
Wellbeing system in automation/wellbeing/. Config: config.json.
Before sending notifications: python3 quiet_hours.py --check --tag "your-tag"
Exit 0 = send, Exit 1 = suppressed (quiet hours active).
```

Your agent will automatically respect your quiet hours.

## No Dependencies

Python 3.8+ and standard library only. `curl` for weather (optional). No pip install needed.

## Background

Built by [Pawel Jozefiak](https://thoughts.jock.pl) after realizing that building a 24/7 AI agent made him work more, not less.

Read the full story: [The AI Productivity Paradox](https://thoughts.jock.pl/p/ai-productivity-paradox-wellbeing-agent-age-2026)

Also available as a free download: [Wiz Store](https://wiz.jock.pl/store/agent-wellbeing-kit)

## License

MIT
