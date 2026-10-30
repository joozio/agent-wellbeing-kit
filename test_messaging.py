#!/usr/bin/env python3
"""Tests for messaging module."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import messaging
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


@unittest.skipUnless(os.name == "posix", "file modes are POSIX-only")
class TestConfigPermissionWarning(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.config = Path(self.tmpdir.name) / "config.json"

    def tearDown(self):
        self.tmpdir.cleanup()

    def _send(self, messaging_cfg, mode):
        self.config.write_text(json.dumps({"messaging": messaging_cfg}))
        os.chmod(self.config, mode)
        err = io.StringIO()
        with patch.object(messaging, "CONFIG_FILE", self.config), \
                redirect_stderr(err), redirect_stdout(io.StringIO()):
            messaging.send_message("hi")
        return err.getvalue()

    def test_world_readable_config_with_token_warns(self):
        err = self._send({"channel": "cli", "telegram_bot_token": "123:abc"}, 0o644)
        self.assertIn("chmod 600", err)
        self.assertNotIn("123:abc", err)

    def test_private_config_does_not_warn(self):
        err = self._send({"channel": "cli", "telegram_bot_token": "123:abc"}, 0o600)
        self.assertEqual(err, "")

    def test_config_without_secrets_does_not_warn(self):
        err = self._send({"channel": "cli"}, 0o644)
        self.assertEqual(err, "")


if __name__ == "__main__":
    unittest.main()
