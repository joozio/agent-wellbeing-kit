# Agent Wellbeing Kit

Your AI agent can produce infinite output. You cannot consume infinite output. This kit protects the human side of the human-agent loop.

**Zero dependencies. Python 3.8+. Runs locally. Advisory, not blocking.**

## The Problem

AI agents remove friction from production. The bottleneck shifts to you: the human who still has to review, decide, and live with the output. Without boundaries, you'll find yourself checking agent results at midnight, skipping morning routines, and burning out faster than before AI.

This kit gives your agent the concept of "not now" and gives you visibility into silent failures.

## What It Does

- **Quiet hours** - gate outbound messages during morning routine, evenings, and sleep. Emergency override built in.
- **Morning nudge** - weather-aware activity suggestion (outdoor vs indoor based on conditions).
- **Evening + bedtime nudge** - rotating wind-down reminders with sleep tracking.
- **Weekly check-in** - Sunday summary of routine adherence, screen-free evenings, sleep.
- **Error registry** - detect repeating errors, stuck loops, and silent agent failures before they waste hours.
- **Memory health** - check agent memory files for bloat, staleness, and thrashing.
- **Dashboard** - single HTML file, dark mode, loads your state.json for a visual overview.

## Quick Start (30 seconds)

```bash
git clone https://github.com/joozio/agent-wellbeing-kit.git
cd agent-wellbeing-kit
cp config.example.json config.json    # then edit with your settings
python3 morning-nudge.py --dry-run
```

Schedule with cron or LaunchAgent. See [SETUP.md](SETUP.md) for full instructions, or check [examples/](examples/) for ready-to-paste configs.

## Error Registry

Catch when your agent is silently failing:

```bash
python3 error_registry.py --scan /path/to/agent.log

# Output:
# Errors found: 47
# Repeating (3):
#   12x  failed to connect to <hex>
#   8x   timeout waiting for response
#   5x   permission denied: /tmp/<hex>
# Possible stuck loops (1):
#   12x  failed to connect to <hex>
# Alerts:
#   ! 3 repeating error(s) detected
#   ! 1 possible stuck loop(s)
```

Also works as a library:
```python
from error_registry import check_errors
results = check_errors(open("agent.log").readlines())
```

## Memory Health

Detect when agent memory files silently degrade:

```bash
python3 memory_health.py --check ~/.claude/memory/

# Memory health: DEGRADED
#   [OK]   memory.md (12.3KB, 1d old)
#   [WARN] context.json (89.2KB, 0d old)
#          bloat: 89KB (threshold: 50KB)
```

## Use With Your AI Agent

Add to CLAUDE.md (or equivalent):
```markdown
## Wellbeing
Before sending notifications: python3 quiet_hours.py --check --tag "your-tag"
Scan for errors: python3 error_registry.py --scan agent.log
```

See [examples/](examples/) for LangChain, OpenAI, and CrewAI integration snippets.

## Messaging Channels

Set `messaging.channel` in `config.json`:

| Channel | Setup |
|---------|-------|
| **cli** (default) | Prints to stdout |
| **imessage** | macOS Messages.app via AppleScript |
| **telegram** | Bot API (token + chat_id) |
| **slack** | Webhook URL |
| **webhook** | Generic HTTP POST endpoint |

## Example Output

```
[wellbeing] Morning. 12C, partly cloudy. Good day for running.
```

```
[wellbeing] Weekly check-in (Mar 17 - Mar 23):
Morning routine: 5/7 days
Screen-free evenings: 3/7
In bed on time: 4/7
Decent week. Room to improve.
```

## No Dependencies

Python 3.8+ standard library only. Optional `curl` for weather. No pip install. No Docker. No accounts. No cloud. Runs on your machine, reads your config, that's it.

## Files

| File | What it does |
|------|-------------|
| `config.example.json` | All settings (copy to `config.json`) |
| `utils.py` | Shared state/config utilities |
| `quiet_hours.py` | Message gating library + CLI |
| `morning-nudge.py` | Weather-aware morning nudge |
| `evening-nudge.py` | Wind-down + bedtime nudges |
| `weekly-checkin.py` | Sunday routine summary |
| `error_registry.py` | Silent failure detection |
| `memory_health.py` | Memory file health checker |
| `messaging.py` | Multi-channel messaging abstraction |
| `dispatch.sh` | Cron/LaunchAgent entry point |
| `dashboard.html` | Visual overview (open in browser) |

## Background

Built by [Pawel Jozefiak](https://thoughts.jock.pl) after realizing that building a 24/7 AI agent made him work more, not less. The agent was great at producing. The human was drowning in output. Morning routines broke. Sleep dropped. The fix wasn't turning the agent off. It was teaching it boundaries.

Read the full story: [The AI Productivity Paradox](https://thoughts.jock.pl/p/ai-productivity-paradox-wellbeing-agent-age-2026)

## License

MIT
