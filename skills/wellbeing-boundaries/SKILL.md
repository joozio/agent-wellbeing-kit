---
name: wellbeing-boundaries
description: Gate outbound notifications through the human's quiet hours. Use before sending any message, notification, nudge, or alert to the human, and when deciding whether something is urgent enough to interrupt them outside working hours.
---

# Wellbeing Boundaries

The human configured quiet hours. Respect them. A notification that can wait until morning should wait until morning.

## Before sending anything to the human

Run the quiet-hours check from the kit directory (adjust the path to where agent-wellbeing-kit is installed):

```bash
python3 /path/to/agent-wellbeing-kit/quiet_hours.py --check --tag "<short-tag>"
```

- Exit 0: OK to send.
- Exit 1: quiet hours are active and this tag is not on the allowed list. Do not send. The suppression is logged automatically to `suppressed.jsonl`.

Pick a tag that names the message category (`build-status`, `daily-report`, `error-alert`). Tags let the human allow specific categories through specific windows in `config.json`.

## When a message is suppressed

- Queue it and send after quiet hours end, or fold it into the next scheduled report.
- Never retry in a loop until the window opens. Check once, then wait.
- Never reword or re-tag a message to slip past the gate. If it was suppressed, it waits.

## Emergencies

A genuine emergency bypasses quiet hours in two ways:

```bash
python3 quiet_hours.py --check --tag "server_down" --emergency
```

or by using a tag containing one of the configured `emergency_keywords`. Reserve this for things the human would want to be woken up for: data loss, security incidents, payment failures, production down. A failed cron job at 2 AM is not an emergency.

## Checking status

```bash
python3 quiet_hours.py --status
```

Prints the active window name, or that quiet hours are off. Useful when planning when to deliver a batch of updates.
