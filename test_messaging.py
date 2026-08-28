#!/usr/bin/env python3
"""Tests for messaging module."""

import unittest
from messaging import _applescript_escape


class TestAppleScriptEscape(unittest.TestCase):

    def test_plain_text_unchanged(self):
        self.assertEqual(_applescript_escape("Morning. Good day for running."),
                         "Morning. Good day for running.")

    def test_double_quotes_escaped(self):
        self.assertEqual(_applescript_escape('Say "hello"'), 'Say \\"hello\\"')

    def test_backslashes_escaped(self):
        self.assertEqual(_applescript_escape("path\\to\\file"), "path\\\\to\\\\file")

    def test_backslash_before_quote(self):
        self.assertEqual(_applescript_escape('\\"'), '\\\\\\"')


if __name__ == "__main__":
    unittest.main()
