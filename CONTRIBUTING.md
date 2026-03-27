# Contributing

Thanks for your interest. Here's how to help.

## Rules

1. **Zero dependencies.** Python 3.8+ standard library only. No pip install.
2. **Keep it simple.** If a feature needs more than 150 lines, it's probably too complex.
3. **Advisory, not blocking.** Nothing should prevent the user from working.

## Adding a nudge type

1. Create `your-nudge.py` following the pattern in `morning-nudge.py`
2. Import shared functions from `utils.py`
3. Add a schedule entry to `dispatch.sh`
4. Add `--dry-run` support
5. Update README.md

## Adding a messaging channel

1. Add the channel handler to `messaging.py` (follow the existing pattern)
2. Add config fields to `config.example.json`
3. Document in SETUP.md

## Pull requests

- Describe what it does and why
- Include `--dry-run` test output
- Keep PRs focused (one feature per PR)

## Issues

Bug reports, feature requests, and questions are all welcome. Open an issue.
