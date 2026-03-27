.PHONY: test status errors health dashboard

test:
	python3 morning-nudge.py --dry-run
	python3 evening-nudge.py --dry-run
	python3 quiet_hours.py --status

status:
	python3 quiet_hours.py --status

errors:
	python3 error_registry.py --summary

health:
	python3 memory_health.py --check

dashboard:
	open dashboard.html
