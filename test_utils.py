#!/usr/bin/env python3
"""Tests for utils state handling."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import utils


class TestSaveState(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.state_file = Path(self.tmpdir.name) / "state.json"
        patcher = patch.object(utils, "STATE_FILE", self.state_file)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_round_trip(self):
        utils.save_state({"a": 1})
        self.assertEqual(utils.load_state(), {"a": 1})
        self.assertEqual(os.listdir(self.tmpdir.name), ["state.json"])

    def test_concurrent_save_does_not_crash(self):
        # Simulate a second process (e.g. an agent's memory_health check)
        # saving between this process writing its temp file and renaming it.
        real_replace = os.replace
        nested = []

        def interleaved_replace(src, dst):
            if not nested:
                nested.append(True)
                utils.save_state({"writer": "other"})
            real_replace(src, dst)

        with patch.object(os, "replace", side_effect=interleaved_replace):
            utils.save_state({"writer": "this"})
        self.assertEqual(json.loads(self.state_file.read_text()), {"writer": "this"})
        self.assertEqual(os.listdir(self.tmpdir.name), ["state.json"])

    def test_corrupt_state_loads_empty(self):
        self.state_file.write_text("{not json")
        self.assertEqual(utils.load_state(), {})


if __name__ == "__main__":
    unittest.main()
