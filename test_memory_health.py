#!/usr/bin/env python3
"""Tests for memory_health module."""

import os
import tempfile
import time
import unittest
from pathlib import Path

from memory_health import check_file


class TestCheckFile(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _make_file(self, name, size_bytes=100, age_days=0):
        p = self.dir / name
        p.write_bytes(b"x" * size_bytes)
        if age_days:
            past = time.time() - age_days * 86400
            os.utime(p, (past, past))
        return p

    def test_healthy_file(self):
        p = self._make_file("memory.md")
        result = check_file(p, max_size_kb=50, stale_days=7)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["issues"], [])

    def test_missing_file(self):
        result = check_file(self.dir / "nope.md")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["issue"], "not found")

    def test_bloated_file(self):
        p = self._make_file("big.md", size_bytes=60 * 1024)
        result = check_file(p, max_size_kb=50, stale_days=7)
        self.assertEqual(result["status"], "warn")
        self.assertTrue(any("bloat" in i for i in result["issues"]))

    def test_stale_file(self):
        p = self._make_file("old.md", age_days=10)
        result = check_file(p, max_size_kb=50, stale_days=7)
        self.assertEqual(result["status"], "warn")
        self.assertTrue(any("stale" in i for i in result["issues"]))

    def test_bloated_and_stale(self):
        p = self._make_file("bad.md", size_bytes=60 * 1024, age_days=10)
        result = check_file(p, max_size_kb=50, stale_days=7)
        self.assertEqual(result["status"], "warn")
        self.assertEqual(len(result["issues"]), 2)


if __name__ == "__main__":
    unittest.main()
