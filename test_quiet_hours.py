#!/usr/bin/env python3
"""Basic tests for quiet_hours module."""

import unittest
from datetime import datetime, time
from quiet_hours import _in_window, is_quiet_hours, should_send_message


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


if __name__ == "__main__":
    unittest.main()
