---
name: agent-health-check
description: Detect silent agent failures and memory degradation. Use when asked for an agent health check, when agent behavior seems off or output quality drops, after long unattended runs, or as part of a scheduled maintenance pass.
---

# Agent Health Check

Agents fail silently: they retry the same broken call for hours, or their memory files bloat and go stale until output quality drops. This skill catches both. Run the tools from the kit directory (adjust the path to where agent-wellbeing-kit is installed).

## Error scan

Scan the agent's log for repeating errors and stuck loops:

```bash
python3 /path/to/agent-wellbeing-kit/error_registry.py --scan /path/to/agent.log
```

Or pipe recent output directly:

```bash
tail -n 500 agent.log | python3 error_registry.py --feed
```

Exit 1 means alerts fired. How to read the output:

- **Repeating**: the same error fingerprint 3+ times. Something is broken and being retried. Find the root cause; do not just note it.
- **Possible stuck loops**: one fingerprint 5+ times. The agent is likely wedged on a single operation. Check whether that process should be restarted or that task abandoned.
- **High error volume**: more than 50 errors in the scanned window. Widen the investigation beyond single fingerprints.

Timestamps, UUIDs, hex IDs, and numbers are stripped before fingerprinting, so the counts group true repeats even when metadata differs.

## Memory health

```bash
python3 memory_health.py --check /path/to/memory/
```

- **bloat**: file over the size threshold. Compact it: summarize, archive old entries, split by topic.
- **stale**: not modified past the threshold. Either the memory system stopped writing (a bug worth chasing) or the file is dead weight (archive it).
- **not found**: a configured path is missing. The memory system may be writing somewhere else; find where.

## Reporting

Summarize findings at a high level: what is broken, since when, and the one action that fixes it. If everything is clean, say so in one line. Persisted results land in `state.json` and show up in `dashboard.html`.

If a finding needs the human's attention right now, check quiet hours first (see the wellbeing-boundaries skill). Most health findings belong in the next scheduled report, not a midnight ping.
