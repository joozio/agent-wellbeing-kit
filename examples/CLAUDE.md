## Wellbeing

Wellbeing system in automation/wellbeing/. Config: config.json.

Before sending notifications, check quiet hours:
```bash
python3 automation/wellbeing/quiet_hours.py --check --tag "your-tag"
# Exit 0 = send, Exit 1 = suppressed (quiet hours active)
```

Scan agent logs for silent failures:
```bash
python3 automation/wellbeing/error_registry.py --scan /path/to/agent.log
```

Check memory health:
```bash
python3 automation/wellbeing/memory_health.py --check /path/to/memory/
```
