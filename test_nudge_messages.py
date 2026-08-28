#!/usr/bin/env python3
"""Tests for nudge message pools in evening-nudge.py."""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location(
    "evening_nudge", Path(__file__).parent / "evening-nudge.py")
evening_nudge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(evening_nudge)


class TestMessagePools(unittest.TestCase):

    def test_default_pools_nonempty(self):
        self.assertTrue(evening_nudge.EVENING_MESSAGES)
        self.assertTrue(evening_nudge.BEDTIME_MESSAGES)

    def test_pick_message_returns_pool_member(self):
        pool = ["a", "b", "c"]
        self.assertIn(evening_nudge.pick_message(pool), pool)

    def test_custom_pool_overrides_defaults(self):
        config = {"messages": {"evening": ["custom line"]}}
        with patch.object(evening_nudge, "load_config", return_value=config):
            msgs = evening_nudge.get_messages("evening", evening_nudge.EVENING_MESSAGES)
        self.assertEqual(msgs, ["custom line"])

    def test_empty_custom_pool_falls_back_to_defaults(self):
        config = {"messages": {"evening": []}}
        with patch.object(evening_nudge, "load_config", return_value=config):
            msgs = evening_nudge.get_messages("evening", evening_nudge.EVENING_MESSAGES)
        self.assertEqual(msgs, evening_nudge.EVENING_MESSAGES)


if __name__ == "__main__":
    unittest.main()
