#!/usr/bin/env python3
"""Basic tests for quiet_hours module."""

import io
import json
import os
import tempfile
import time as time_mod
import unittest
from contextlib import redirect_stderr
from datetime import datetime, time
from pathlib import Path
from unittest.mock import patch

import quiet_hours
from quiet_hours import _in_window, is_quiet_hours, should_send_message

EXAMPLE_CONFIG = Path(__file__).resolve().parent / "config.example.json"
NIGHT = datetime(2026, 10, 30, 3, 0)
MIDDAY = datetime(2026, 10, 30, 12, 0)


class ConfigTestCase(unittest.TestCase):
    """Runs quiet_hours against a temporary config.json."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.tmpdir.name) / "config.json"
        patcher = patch.object(quiet_hours, "CONFIG_FILE", self.config_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmpdir.cleanup)

    def write_config(self, **overrides):
        config = json.loads(EXAMPLE_CONFIG.read_text())
        config.update(overrides)
        self.config_path.write_text(json.dumps(config))


class TestTimeWindows(unittest.TestCase):

    def test_normal_window(self):
        """07:00-09:30 should catch 08:00."""
        self.assertTrue(_in_window(time(8, 0), "07:00", "09:30"))

    def test_normal_window_outside(self):
        """07:00-09:30 should not catch 10:00."""
        self.assertFalse(_in_window(time(10, 0), "07:00", "09:30"))

    def test_overnight_window_late(self):
        """19:30-07:00 should catch 23:00."""
        self.assertTrue(_in_window(time(23, 0), "19:30", "07:00"))

    def test_overnight_window_early(self):
        """19:30-07:00 should catch 05:00."""
        self.assertTrue(_in_window(time(5, 0), "19:30", "07:00"))

    def test_overnight_window_outside(self):
        """19:30-07:00 should not catch 12:00."""
        self.assertFalse(_in_window(time(12, 0), "19:30", "07:00"))

    def test_window_boundary_start(self):
        """Start time should be inclusive."""
        self.assertTrue(_in_window(time(7, 0), "07:00", "09:30"))

    def test_window_boundary_end(self):
        """End time should be exclusive."""
        self.assertFalse(_in_window(time(9, 30), "07:00", "09:30"))


class TestEmergencyOverride(unittest.TestCase):

    def test_emergency_always_sends(self):
        """Emergency flag should bypass quiet hours."""
        self.assertTrue(should_send_message(tag="anything", is_emergency=True))


class TestEmergencyKeywords(ConfigTestCase):

    def test_empty_keyword_does_not_bypass_quiet_hours(self):
        self.write_config(emergency_keywords=[""])
        self.assertFalse(should_send_message(tag="build-status", now=NIGHT))

    def test_keyword_in_tag_bypasses_quiet_hours(self):
        self.write_config(emergency_keywords=["", "server_down"])
        self.assertTrue(should_send_message(tag="prod-server_down", now=NIGHT))


class TestGate(ConfigTestCase):
    """Pins the central gate against the shipped default config."""

    def test_night_blocks_untagged_and_unknown_tags(self):
        self.write_config()
        self.assertFalse(should_send_message(tag="", now=NIGHT))
        self.assertFalse(should_send_message(tag="build-status", now=NIGHT))

    def test_night_allows_listed_tags(self):
        self.write_config()
        self.assertTrue(should_send_message(tag="wellbeing-nudge", now=NIGHT))
        self.assertTrue(should_send_message(tag="emergency", now=NIGHT))

    def test_morning_routine_allows_only_its_own_list(self):
        self.write_config()
        eight = datetime(2026, 10, 30, 8, 0)
        self.assertEqual(is_quiet_hours(eight), "morning_routine")
        self.assertTrue(should_send_message(tag="wellbeing-nudge", now=eight))
        self.assertFalse(should_send_message(tag="emergency", now=eight))

    def test_daytime_sends_everything(self):
        self.write_config()
        self.assertIsNone(is_quiet_hours(MIDDAY))
        self.assertTrue(should_send_message(tag="build-status", now=MIDDAY))

    def test_window_edges(self):
        self.write_config()
        self.assertIsNone(is_quiet_hours(datetime(2026, 10, 30, 19, 29)))
        self.assertEqual(is_quiet_hours(datetime(2026, 10, 30, 19, 30)), "evening")
        self.assertEqual(is_quiet_hours(datetime(2026, 10, 30, 6, 59)), "evening")
        self.assertEqual(is_quiet_hours(datetime(2026, 10, 30, 7, 0)), "morning_routine")
        self.assertIsNone(is_quiet_hours(datetime(2026, 10, 30, 9, 30)))

    def test_disabled_sends_everything(self):
        self.write_config(enabled=False)
        self.assertIsNone(is_quiet_hours(NIGHT))
        self.assertTrue(should_send_message(tag="build-status", now=NIGHT))

    def test_missing_config_disables_gate(self):
        self.assertFalse(self.config_path.exists())
        self.assertTrue(should_send_message(tag="build-status", now=NIGHT))


class TestBrokenConfig(ConfigTestCase):
    """A typo in config.json must not turn quiet hours off."""

    def _check(self, text):
        self.config_path.write_text(text)
        err = io.StringIO()
        with redirect_stderr(err):
            night = should_send_message(tag="build-status", now=NIGHT)
            midday = should_send_message(tag="build-status", now=MIDDAY)
        return night, midday, err.getvalue()

    def test_invalid_json_keeps_default_quiet_hours(self):
        night, midday, err = self._check('{"enabled": true,, "quiet_hours": {}}')
        self.assertFalse(night)
        self.assertTrue(midday)
        self.assertIn("Warning", err)

    def test_non_object_json_keeps_default_quiet_hours(self):
        night, _, err = self._check("[]")
        self.assertFalse(night)
        self.assertIn("Warning", err)


@unittest.skipUnless(hasattr(time_mod, "tzset"), "needs time.tzset (POSIX)")
class TestDaylightSaving(ConfigTestCase):
    """Windows are local wall-clock times, so DST shifts must not move them."""

    def setUp(self):
        super().setUp()
        self.write_config()
        self._old_tz = os.environ.get("TZ")
        os.environ["TZ"] = "America/New_York"
        time_mod.tzset()

    def tearDown(self):
        if self._old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = self._old_tz
        time_mod.tzset()

    def _local(self, utc_iso):
        epoch = datetime.fromisoformat(utc_iso + "+00:00").timestamp()
        return datetime.fromtimestamp(epoch)

    def test_fall_back_repeated_hour_stays_quiet(self):
        # 2026-11-01: 01:30 happens twice in New York (EDT, then EST).
        first, second = self._local("2026-11-01T05:30:00"), self._local("2026-11-01T06:30:00")
        self.assertEqual((first.hour, first.minute), (1, 30))
        self.assertEqual((second.hour, second.minute), (1, 30))
        self.assertEqual(is_quiet_hours(first), "evening")
        self.assertEqual(is_quiet_hours(second), "evening")

    def test_spring_forward_morning_window_starts_at_local_seven(self):
        # 2026-03-08: clocks jump 02:00 EST to 03:00 EDT. 07:00 EDT is 11:00 UTC.
        self.assertEqual(is_quiet_hours(self._local("2026-03-08T10:59:00")), "evening")
        self.assertEqual(is_quiet_hours(self._local("2026-03-08T11:00:00")), "morning_routine")
        self.assertIsNone(is_quiet_hours(self._local("2026-03-08T13:30:00")))

    def test_evening_window_starts_at_local_time_after_fall_back(self):
        # 2026-11-02 19:30 EST is 00:30 UTC on Nov 3.
        self.assertIsNone(is_quiet_hours(self._local("2026-11-03T00:29:00")))
        self.assertEqual(is_quiet_hours(self._local("2026-11-03T00:30:00")), "evening")


if __name__ == "__main__":
    unittest.main()
