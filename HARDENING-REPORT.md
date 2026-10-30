# Hardening Report

Branch: `claude/agent-wellbeing-hardening-uiyfyh`, based on `0d92799`.
File:line references point at the code as it was before this pass (`0d92799`) unless noted.

Commits:

| Phase | Commit | Summary |
|-------|--------|---------|
| A | `39b859a` | Security fixes: dashboard escaping, config.json permissions, empty emergency keyword |
| B | `6c91dfe` | Critical-path tests; fixed quiet hours failing open on a broken config.json |
| C | `b1fb110` | Broken flows: cron permission denied, bedtime customization, skills paths, non-UTF-8 logs, dashboard dates |

## Summary

| Severity | Found | Fixed | Not fixed |
|----------|-------|-------|-----------|
| HIGH | 2 | 2 | 0 |
| MEDIUM | 6 | 5 | 1 |
| LOW | 18 | 6 | 12 |

The "not fixed" rows include hardening ideas (no concrete failure scenario) and items that need a product decision. Each one is listed below with the reason.

## Test commands and counts

All runs use the repo's own command: `python3 -m unittest discover -p "test_*.py"` (same as `make test` and CI).

| When | Python 3.13.17 | Python 3.12 | Python 3.8.20 |
|------|----------------|-------------|---------------|
| Before (`0d92799`) | 31 tests, OK | not run | not run |
| After Phase A (`39b859a`) | 37 tests, OK | not run | not run |
| After Phase B (`6c91dfe`) | 81 tests, OK | 81 tests, OK | 81 tests, OK |
| After Phase C (`b1fb110`) | 96 tests, OK | 96 tests, OK | 96 tests, OK |

- No test was failing before this pass. CI on `main` was green (runs 1 and 2).
- `test_dashboard.py` (4 tests) drives headless Chromium through Node Playwright. It skips when `node` or the `playwright` package is missing, as on the stock CI runner. With `node` removed from PATH, the result is `OK (skipped=4)`.
- Regression proof: for each phase I reverted only the production files (`git stash` of the fixed files) and re-ran the suite with the new tests in place. Phase A: 3 failures. Phase B: 4 failures/errors. Phase C: 12 failures/errors. With the fixes in place, all pass.
- `make smoke` and the exact CI smoke steps from `.github/workflows/ci.yml`, run on a fresh clone of the branch, pass.
- Python 3.8 was installed with `uv python install 3.8` to match the oldest CI matrix entry.

## Phase A: security audit

Scope reviewed: there are no HTTP routes, sessions, auth, payment handlers or CORS. The kit is a local CLI. Untrusted or semi-trusted input comes from: `config.json` (secrets plus user-edited JSON), `state.json` (loaded into `dashboard.html`), agent log files (`error_registry.py`), message tags passed by agents (`quiet_hours.py`), the `osascript` subprocess call (`messaging.py`), and outbound HTTP to Telegram, Slack, webhooks and wttr.in.

### Fixed

**A1. LOW. Script injection in dashboard from state.json.** `dashboard.html:135`, `:150`, `:153`.
Failure scenario: load a `state.json` whose `error_registry.alerts` contains `<img src=x onerror="...">` (or put it in `memory_health.overall` or `error_registry.total_errors`). The value went into `innerHTML` unescaped, so the script ran in the dashboard page. The file the kit writes itself only contains fixed alert strings, so the realistic vector is a shared or hand-edited state file, and impact is limited to the `file://` page.
Fix: `39b859a`. All three values are HTML-escaped. Test: `test_dashboard.TestDashboardEscaping`.

**A2. MEDIUM. Messaging credentials in a world-readable config.json.** `README.md:28`, `SETUP.md:9`, `messaging.py:67-81`.
Failure scenario: the documented `cp config.example.json config.json` creates the file as mode 0644. After the user adds `telegram_bot_token` or a Slack webhook URL, any other local account can read it (e.g. on a shared Linux box where home directories are world-traversable) and post as the bot.
Fix: `39b859a`. README and SETUP now include `chmod 600 config.json`. `send_message` prints a one-line warning on stderr (it does not print the secret) when credentials are present and the file is group- or other-readable. Tests: `test_messaging.TestConfigPermissionWarning`.

**A3. LOW. Empty emergency keyword turns quiet hours off.** `quiet_hours.py:73`.
Failure scenario: `"emergency_keywords": [""]` (a natural way to "clear" the list). `"" in tag` is true for every tag, so every message bypassed quiet hours at 3 AM.
Fix: `39b859a`. Empty keywords are ignored. Test: `test_quiet_hours.TestEmergencyKeywords`.

### Checked, no finding

- **Committed secrets:** none. Searched with `git grep` for token, secret, password and api key, and searched the full history for Telegram bot-token and Slack token/webhook patterns. Only placeholders were found.
- **Dependency manifests:** none. The kit uses only the standard library, so there was nothing to bump.
- **Shell and subprocess calls:** `messaging.py` runs `osascript` with an argv list (no shell). Text and recipient are escaped for `\` and `"`, which are the only characters that end an AppleScript string literal. A new test pins that a hostile message stays one argv item. `dispatch.sh` quotes every expansion.
- **Telegram token leakage on errors:** `HTTPError` and `URLError` messages do not include the URL. Pinned by `test_messaging.TestChannels.test_telegram_http_error_does_not_leak_token`.

### Hardening ideas (not fixed: no concrete failure scenario, or by design)

- **H1. LOW.** `quiet_hours.py:73`: emergency keywords match as substrings, so a routine tag like `security-digest` passes quiet hours. This is documented behaviour ("a tag containing one of the configured emergency_keywords"), so changing it would break existing setups. A token or prefix match would be stricter.
- **H2. LOW.** `messaging.py:53-57` builds AppleScript source by string interpolation. The escaping is correct. Passing the text through `on run argv` would remove the need for it. Not verified on macOS (see "Could not verify").
- **H3. LOW.** `examples/launchagent.plist:20,22` writes logs to `/tmp/wellbeing*.log`, which other local users can read. The logs hold nudge text and send errors only, never tokens. `~/Library/Logs` would be more private.
- **H4. LOW.** `quiet_hours.py:85-92`: `suppressed.jsonl` grows without bound. There is no rotation.
- **H5. LOW.** `messaging.py`: `webhook_url` accepts any scheme urllib supports (including `file://`). The config is trusted, so there is no attacker path.

## Phase B: tests on critical paths

Critical paths chosen (where a bug hurts the user most):

1. **Quiet-hours gate** (`should_send_message`, `is_quiet_hours`): the product's main promise.
2. **Scheduler routing** (`dispatch.sh`): the right nudge at the right hour, and nothing at other hours.
3. **Nudge send-once and state recording**: no duplicate nudges, no "sent" mark on failure.
4. **Weekly check-in**: counts, streak, reset only after a successful send.
5. **Message delivery** (`send_message`): request shape per channel, failure reporting, no secret leakage.
6. **Agent-facing CLI exit codes and state persistence** (`error_registry.py`, `utils.save_state`).

New and extended test files: `test_quiet_hours.py` (gate, window edges, disabled and missing config, broken config, DST in America/New_York for fall back and spring forward), `test_dispatch.py`, `test_nudges.py`, `test_messaging.py`, `test_error_registry.py`, `test_utils.py`.

DST and timezone result: windows compare naive local wall-clock time, so DST transitions do not move them. The repeated 01:30 on fall-back night is quiet both times, and the morning window starts at 07:00 local on spring-forward day. Both are now pinned by tests. `dispatch.sh` and cron use the same system timezone, so they stay consistent.

### Bugs found and fixed

**B1. HIGH. Quiet hours turn off on any config.json typo.** `quiet_hours.py:29-33`.
Failure scenario: the user adds a bot token and leaves a stray comma (`"enabled": true,,`). `_load_config` caught the parse error and returned `{"enabled": false}`. From then on every agent message passed the gate at any hour, and `quiet_hours.py --status` said "ACTIVE: not in quiet hours". Reproduced: `should_send_message("build-status", now=03:00)` returned `True`.
Fix: `6c91dfe`. A missing `config.json` still disables the gate (unchanged). A present but unreadable or invalid one prints a warning on stderr and falls back to the shipped default windows in `config.example.json`. Tests: `test_quiet_hours.TestBrokenConfig`.

**B2. MEDIUM. Nudges silently lost on a broken config.json.** `messaging.py:18-22`, `utils.py:29-34`.
Failure scenario: same typo, with `channel: telegram`. `send_message` fell back to the `cli` channel, printed the nudge into cron's stdout (usually discarded) and returned `True`. The nudge was marked sent for the day and never delivered, and no error appeared anywhere.
Fix: `6c91dfe`. `send_message` reports the parse error on stderr and returns `False`, so the nudge logs "Failed to send" and is retried on the next run. `utils.load_config` now warns instead of silently using defaults. Test: `test_messaging.TestChannels.test_broken_config_reports_failure`.

**B3. LOW. Concurrent state saves crash.** `utils.py:22-26`.
Failure scenario: a cron nudge and an agent's `memory_health.py --check` both call `save_state` at once. Both wrote `state.json.tmp`. The first `os.replace` moved the file, and the second raised `FileNotFoundError` after the message had already been sent.
Fix: `6c91dfe`. Each save uses its own temp file (`mkstemp` in the same directory), which is removed on failure. Test: `test_utils.TestSaveState.test_concurrent_save_does_not_crash`, which interleaves a second save deterministically.

### Not fixed

- **B4. LOW. Lost update between processes.** Nudges load state, then spend up to 15 s on network calls (weather fetch, then send) before saving. A scan result saved by another process in that window is overwritten. Fixing this needs file locking (`fcntl`) or a merge on save. That is a design change, and the only loss is a scan summary that the next scan rewrites.
- **B5. LOW. Duplicate warning.** With a broken config, `quiet_hours.py --check` prints the warning twice, because the config is loaded twice per call. This is cosmetic, and fixing it means restructuring the gate.
- **B6. LOW. Invalid window time crashes the gate.** `quiet_hours.py:36-38`: a window time like `"24:00"` raises `ValueError` on every `should_send_message` call. An agent that uses the library then crashes, and the CLI exits 1 (reads as "suppressed"). It fails loudly rather than silently. Whether `24:00` should mean midnight is a product decision.

## Phase C: broken user flows

Walked on a fresh clone with the README and SETUP steps followed literally: Quick Start, dry runs, `make test`, `make smoke`, the CI smoke steps, invoking the cron entry the way cron does (`/bin/sh -c`, minimal PATH), the skills install into an empty `$HOME`, the error registry and memory health CLIs, and the dashboard in headless Chromium (sample data, file load, 375 px width).

### Fixed

**C1. HIGH. No scheduled nudge ever fires on Linux.** `dispatch.sh` (git mode `100644`), `SETUP.md:109-112`, `examples/crontab.example`.
Failure scenario: the documented cron line `0 7 * * * /path/to/agent-wellbeing-kit/dispatch.sh` runs as `sh -c ./dispatch.sh` and fails with `Permission denied` (exit 126). Every morning, evening, bedtime and weekly nudge fails silently.
Fix: `b1fb110`. The file is now `100755`. The crontab example and SETUP call it as `/bin/bash /path/.../dispatch.sh`, which also works if a store download drops the mode. Verified: both forms exit 0 on a fresh clone. Tests: `test_dispatch.TestExecutable`.

**C2. MEDIUM. Changing bedtime as documented stops the bedtime nudge.** `dispatch.sh:18-43`, `SETUP.md:125,127`.
Failure scenario: SETUP says "Different bedtime: change `routine.bedtime` and the 23:00 schedule". But `dispatch.sh` hardcoded hours 07, 08 and 23, and nothing read `routine.bedtime` or `routine.wake_time`. A cron entry at 22:30 logged "No scheduled action for hour 22", and the bedtime nudge never ran again. Moving the wake time had the same problem.
Fix: `b1fb110`. `dispatch.sh` reads the morning, followup and bedtime hours from `routine.wake_time` and `routine.bedtime`. It falls back to 07:00 and 23:00 when the value is missing, unparseable, or the config is broken. The SETUP wake-time line now says to move the schedule entries too. Tests: `test_dispatch.TestConfiguredHours`. The default schedule is pinned by `test_dispatch.TestDefaultSchedule`.

**C3. MEDIUM. Skill commands fail from the agent's working directory, including the emergency override.** `skills/wellbeing-boundaries/SKILL.md:34,42`, `skills/agent-health-check/SKILL.md:21,35`.
Failure scenario: README says to replace the `/path/to/agent-wellbeing-kit` placeholders, but these commands had no placeholder (`python3 quiet_hours.py ... --emergency`). Run from the agent's project directory, they fail with "can't open file" and exit 2. The skill treats any non-zero exit as "do not send", so a real emergency could be held back.
Fix: `b1fb110`. Every command now uses the kit path placeholder. Docs only, so there is no automated test. Verified by running the fixed command from `/tmp`, which exits 0.

**C4. MEDIUM. Error registry crashes on real-world logs.** `error_registry.py:184`, `:189`.
Failure scenario: an agent log containing one non-UTF-8 byte (`ERROR bad \xff byte`). `--scan` died with `UnicodeDecodeError` and exit 1, which the agent-health-check skill reads as "alerts fired". `tail agent.log | error_registry.py --feed` did the same under a strict UTF-8 locale (reproduced with `PYTHONIOENCODING=utf-8`). `--scan` on a directory printed a traceback.
Fix: `b1fb110`. Undecodable bytes are replaced, and unreadable paths give a one-line error with exit 1. Tests: `test_error_registry.TestCli` (non-UTF-8 scan, non-UTF-8 feed in a subprocess, directory).

**C5. LOW. Skills install fails on a clean machine.** `README.md:83`.
Failure scenario: `cp -r skills/... ~/.claude/skills/` fails with "No such file or directory" when `~/.claude/skills` does not exist yet.
Fix: `b1fb110`. Added `mkdir -p ~/.claude/skills` to README and a note in SETUP. Verified in an empty `$HOME`.

**C6. LOW. A custom message given as a string sends one letter.** `evening-nudge.py:43-44`, `morning-nudge.py:117`.
Failure scenario: `"messages": {"evening": "Go outside tonight"}` (a string instead of a list). The rotation indexed into the string, so the dry run printed `Would send: g`.
Fix: `b1fb110`. Non-list values fall back to the built-in pool. Tests: `test_nudge_messages...test_string_custom_pool_falls_back_to_defaults`, `test_nudges.TestMorningFollowup`.

**C7. LOW. Dashboard shows the wrong day outside UTC.** `dashboard.html:96`, `:119`.
Failure scenario: `state.json` stores local timestamps, but the dashboard compared them with `toISOString()`, which is UTC. In New York after 20:00, or in Sydney before 11:00, every week-chart bar was shifted by one day and today's sent nudges showed as pending.
Fix: `b1fb110`. Dates are compared as local dates, and the sample data uses the same format. Tests: `test_dashboard.TestDashboardDates` (New York, Sydney, UTC, with a fixed clock).

### Not fixed

- **C8. MEDIUM. Weekly check-in reports numbers it never measures.** `weekly-checkin.py:39-43`, `morning-nudge.py:89-93`. Nothing in the kit ever writes `evening_cli_sessions` or `bedtime_breaches`, so "Screen-free evenings" and "In bed on time" always show N/N. "Morning routine" counts mornings when the nudge was *sent*, not routines done. The README example (`Screen-free evenings: 3/7`) cannot happen with the shipped code. Fixing this needs a way to record evenings and bedtimes, which is a new feature and a product decision. The current arithmetic is pinned by `test_nudges.TestWeeklyCheckin`.
- **C9. LOW. Dashboard quiet-hours card ignores the user's config.** `dashboard.html:89-92`: the windows are hardcoded to the example config (07:00-09:30 and 19:30-07:00). The dashboard only loads `state.json`, so it cannot know the user's windows without a design change.
- **C10. LOW. `make dashboard` fails on Linux.** `Makefile:22` runs macOS `open`. On Debian and Ubuntu, `open` is `openvt` and fails. This target is not part of the README flow.
- **C11. LOW. Quiet hours need a timezone setting for agents in containers.** Quiet hours use the host's local time. An agent running in a UTC container while the human lives elsewhere is gated on UTC. A `timezone` setting needs `zoneinfo` (Python 3.9+), but the kit supports 3.8, so this is a feature, not a fix.
- **C12. LOW. A missed launchd job is skipped, not delayed.** macOS launchd runs missed `StartCalendarInterval` jobs when the machine wakes. Because `dispatch.sh` routes by the current hour, a Mac that wakes at 09:10 runs nothing for the missed 07:00 and 08:00 slots. The result is a missed nudge, never a wrong one. Not verified on macOS.

Checked and fine: Quick Start dry runs, `quiet_hours.py --status`, `error_registry.py --summary`, `memory_health.py --check`, `make test` and `make smoke` all work on a fresh clone. The dashboard at 375 px has no horizontal scroll (`scrollWidth == clientWidth == 375`) and the sample data renders.

## Could not verify

- **macOS-only paths:** LaunchAgent loading (`examples/launchagent.plist`), iMessage delivery through `osascript`, and whether AppleScript accepts the multi-line weekly check-in inside a string literal. This environment is Linux only. The argv and escaping are covered by unit tests with `subprocess.run` mocked.
- **Live channels:** I sent nothing to real Telegram, Slack or webhooks, as required. Request shape and error handling are tested with `urlopen` mocked. `get_weather` (wttr.in) was only exercised with an empty location.
- **Windows:** not tested. `dispatch.sh` and cron are POSIX-only, and the permission warning is skipped off POSIX.
- **CI:** the branch was not pushed to a PR, so GitHub Actions did not run on it. Locally the suite passes on Python 3.8, 3.12 and 3.13. On CI, `test_dashboard.py` will skip because the runner has no Playwright package.
