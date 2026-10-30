#!/usr/bin/env python3
"""Tests for the scheduled nudges: send once per day, record state only on success."""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import utils

KIT_DIR = Path(__file__).resolve().parent


def _load(filename, name):
    spec = importlib.util.spec_from_file_location(name, KIT_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


morning = _load("morning-nudge.py", "morning_nudge")
evening = _load("evening-nudge.py", "evening_nudge_t")
weekly = _load("weekly-checkin.py", "weekly_checkin")


class StateTestCase(unittest.TestCase):
    """Points utils.STATE_FILE at a temp file and silences output."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.state_file = Path(self.tmpdir.name) / "state.json"
        for target in (patch.object(utils, "STATE_FILE", self.state_file),
                       redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO())):
            target.__enter__()
            self.addCleanup(target.__exit__, None, None, None)

    def state(self):
        return json.loads(self.state_file.read_text()) if self.state_file.exists() else {}


class TestMorningNudge(StateTestCase):

    def run_nudge(self, sent_ok=True):
        with patch.object(morning, "send_message", return_value=sent_ok) as send, \
                patch.object(morning, "get_weather", return_value=None), \
                patch.object(morning, "load_config", return_value={}):
            morning.main_nudge()
        return send

    def test_sends_once_per_day_and_records_routine_day(self):
        self.assertEqual(self.run_nudge().call_count, 1)
        state = self.state()
        self.assertEqual(datetime.fromisoformat(state["morning_nudge_sent_at"]).date(), date.today())
        self.assertEqual(state["weekly_stats"]["routine_days"], [date.today().isoformat()])
        self.assertEqual(self.run_nudge().call_count, 0)
        self.assertEqual(self.state()["weekly_stats"]["routine_days"], [date.today().isoformat()])

    def test_failed_send_records_nothing_and_retries(self):
        self.run_nudge(sent_ok=False)
        self.assertEqual(self.state(), {})
        self.assertEqual(self.run_nudge().call_count, 1)

    def test_sent_yesterday_sends_again(self):
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        utils.save_state({"morning_nudge_sent_at": yesterday})
        self.assertEqual(self.run_nudge().call_count, 1)

    def test_dry_run_sends_and_records_nothing(self):
        with patch.object(morning, "send_message") as send, \
                patch.object(morning, "get_weather", return_value=None), \
                patch.object(morning, "load_config", return_value={}):
            morning.main_nudge(dry_run=True)
        send.assert_not_called()
        self.assertEqual(self.state(), {})


class TestEveningNudges(StateTestCase):

    def test_bedtime_sends_once_per_day(self):
        with patch.object(evening, "send_message", return_value=True) as send, \
                patch.object(evening, "load_config", return_value={}):
            evening.bedtime_nudge()
            evening.bedtime_nudge()
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args[0][1], "bedtime")

    def test_evening_and_bedtime_are_tracked_separately(self):
        with patch.object(evening, "send_message", return_value=True) as send, \
                patch.object(evening, "load_config", return_value={}):
            evening.evening_nudge()
            evening.bedtime_nudge()
        self.assertEqual([c[0][1] for c in send.call_args_list], ["evening", "bedtime"])


class FakeSunday(date):
    @classmethod
    def today(cls):
        return cls(2026, 11, 1)  # a Sunday; week is Oct 26 to Nov 1


class TestWeeklyCheckin(StateTestCase):

    def setUp(self):
        super().setUp()
        patcher = patch.object(weekly, "date", FakeSunday)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_checkin(self, stats, sent_ok=True):
        utils.save_state({"weekly_stats": stats})
        with patch.object(weekly, "send_message", return_value=sent_ok) as send:
            weekly.generate_checkin()
        return send.call_args[0][0] if send.called else None

    def test_counts_only_this_week_and_resets_after_send(self):
        msg = self.run_checkin({
            "routine_days": ["2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28"],
            "evening_cli_sessions": ["2026-10-27"],
            "bedtime_breaches": ["2026-10-19", "2026-10-30"],
            "streak": 2,
        })
        self.assertIn("Morning routine: 3/7 days", msg)
        self.assertIn("Screen-free evenings: 6/7", msg)
        self.assertIn("In bed on time: 6/7", msg)
        self.assertIn("Streak: 3 good weeks in a row", msg)
        stats = self.state()["weekly_stats"]
        self.assertEqual(stats["streak"], 3)
        self.assertEqual(stats["routine_days"], [])
        self.assertEqual(stats["week_start"], "2026-11-02")

    def test_failed_send_keeps_stats(self):
        stats = {"routine_days": ["2026-10-26"], "streak": 4}
        self.run_checkin(stats, sent_ok=False)
        self.assertEqual(self.state()["weekly_stats"], stats)

    def test_bad_week_resets_streak(self):
        msg = self.run_checkin({
            "routine_days": [],
            "evening_cli_sessions": ["2026-10-2%d" % d for d in range(6, 10)] + ["2026-10-30", "2026-10-31", "2026-11-01"],
            "bedtime_breaches": ["2026-10-2%d" % d for d in range(6, 10)] + ["2026-10-30", "2026-10-31", "2026-11-01"],
            "streak": 5,
        })
        self.assertIn("Rough week", msg)
        self.assertEqual(self.state()["weekly_stats"]["streak"], 0)


if __name__ == "__main__":
    unittest.main()
