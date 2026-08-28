#!/usr/bin/env python3
"""Tests for error_registry module."""

import unittest
from error_registry import _normalize, check_errors

CONFIG = {
    "error_registry": {
        "repeat_threshold": 3,
        "loop_threshold": 5,
        "log_patterns": ["ERROR", "FAIL", "Exception", "Traceback"],
    }
}


class TestNormalize(unittest.TestCase):

    def test_strips_timestamps(self):
        a = _normalize("2026-03-01T10:00:00 ERROR connection refused")
        b = _normalize("2026-03-02T23:59:59 ERROR connection refused")
        self.assertEqual(a, b)

    def test_strips_uuids(self):
        a = _normalize("ERROR job 550e8400-e29b-41d4-a716-446655440000 failed")
        b = _normalize("ERROR job 6ba7b810-9dad-11d1-80b4-00c04fd430c8 failed")
        self.assertEqual(a, b)

    def test_strips_hex_ids(self):
        a = _normalize("ERROR request deadbeef1234 timed out")
        b = _normalize("ERROR request cafebabe5678 timed out")
        self.assertEqual(a, b)

    def test_strips_numbers(self):
        a = _normalize("ERROR retry 3 of 10 failed")
        b = _normalize("ERROR retry 7 of 99 failed")
        self.assertEqual(a, b)


class TestCheckErrors(unittest.TestCase):

    def test_clean_log(self):
        results = check_errors(["all good", "still fine"], CONFIG)
        self.assertEqual(results["total_errors"], 0)
        self.assertEqual(results["alerts"], [])

    def test_counts_errors(self):
        results = check_errors(["ERROR one", "ERROR two", "info line"], CONFIG)
        self.assertEqual(results["total_errors"], 2)

    def test_repeating_detection(self):
        lines = ["ERROR connection refused"] * 3
        results = check_errors(lines, CONFIG)
        self.assertEqual(len(results["repeating"]), 1)
        self.assertNotEqual(results["alerts"], [])

    def test_below_threshold_not_repeating(self):
        lines = ["ERROR connection refused"] * 2
        results = check_errors(lines, CONFIG)
        self.assertEqual(len(results["repeating"]), 0)

    def test_loop_detection(self):
        lines = ["ERROR stuck on step 5"] * 5
        results = check_errors(lines, CONFIG)
        self.assertEqual(len(results["loops"]), 1)

    def test_varied_metadata_same_fingerprint(self):
        lines = [
            "2026-03-01T10:00:01 ERROR timeout on request 12345",
            "2026-03-01T10:00:05 ERROR timeout on request 67890",
            "2026-03-01T10:00:09 ERROR timeout on request 11111",
        ]
        results = check_errors(lines, CONFIG)
        self.assertEqual(len(results["repeating"]), 1)


if __name__ == "__main__":
    unittest.main()
