#!/usr/bin/env python3
"""Tests for messaging module."""

import io
import json
import os
import tempfile
import unittest
import urllib.error
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


class TestChannels(unittest.TestCase):
    """Each channel builds the right request; failures return False without leaking secrets."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.config = Path(self.tmpdir.name) / "config.json"
        patcher = patch.object(messaging, "CONFIG_FILE", self.config)
        patcher.start()
        self.addCleanup(patcher.stop)

    def send(self, messaging_cfg, text="hello", msg_type="morning", urlopen=None, raw=None):
        self.config.write_text(raw if raw is not None else json.dumps({"messaging": messaging_cfg}))
        os.chmod(self.config, 0o600)
        out, err = io.StringIO(), io.StringIO()
        urlopen = urlopen or patch("urllib.request.urlopen").start()
        self.addCleanup(patch.stopall)
        with redirect_stdout(out), redirect_stderr(err):
            ok = messaging.send_message(text, msg_type)
        return ok, urlopen, out.getvalue(), err.getvalue()

    def test_cli_prints(self):
        ok, urlopen, out, _ = self.send({"channel": "cli"})
        self.assertTrue(ok)
        self.assertEqual(out, "[wellbeing] hello\n")
        urlopen.assert_not_called()

    def test_missing_config_defaults_to_cli(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertTrue(messaging.send_message("hello"))
        self.assertIn("hello", out.getvalue())

    def test_broken_config_reports_failure(self):
        ok, urlopen, out, err = self.send(None, raw='{"messaging": {"channel": "telegram",}}')
        self.assertFalse(ok)
        self.assertEqual(out, "")
        self.assertIn("cannot read", err)
        urlopen.assert_not_called()

    def test_telegram_request(self):
        ok, urlopen, _, _ = self.send({"channel": "telegram", "telegram_bot_token": "123:abc",
                                       "telegram_chat_id": "42"})
        self.assertTrue(ok)
        req = urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://api.telegram.org/bot123:abc/sendMessage")
        self.assertEqual(json.loads(req.data), {"chat_id": "42", "text": "hello"})

    def test_telegram_http_error_does_not_leak_token(self):
        def fail(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, None)
        ok, _, out, err = self.send({"channel": "telegram", "telegram_bot_token": "123:abc",
                                     "telegram_chat_id": "42"},
                                    urlopen=patch("urllib.request.urlopen", side_effect=fail).start())
        self.assertFalse(ok)
        self.assertIn("401", err)
        self.assertNotIn("123:abc", err + out)

    def test_telegram_missing_fields(self):
        ok, urlopen, _, _ = self.send({"channel": "telegram", "telegram_bot_token": "123:abc"})
        self.assertFalse(ok)
        urlopen.assert_not_called()

    def test_slack_request(self):
        ok, urlopen, _, _ = self.send({"channel": "slack", "slack_webhook_url": "https://hooks.example/x"})
        self.assertTrue(ok)
        req = urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://hooks.example/x")
        self.assertEqual(json.loads(req.data), {"text": "hello"})

    def test_webhook_request_carries_type(self):
        ok, urlopen, _, _ = self.send({"channel": "webhook", "webhook_url": "https://example.test/n"},
                                      msg_type="bedtime")
        self.assertTrue(ok)
        req = urlopen.call_args[0][0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(json.loads(req.data), {"text": "hello", "type": "bedtime"})

    def test_unknown_channel_fails(self):
        ok, urlopen, _, err = self.send({"channel": "pager"})
        self.assertFalse(ok)
        self.assertIn("Unknown messaging channel", err)

    def test_imessage_passes_escaped_text_as_single_argv(self):
        with patch("subprocess.run") as run:
            run.return_value.returncode = 0
            ok, _, _, _ = self.send({"channel": "imessage", "imessage_recipient": "+100"},
                                    text='say "hi"; do shell script "x"')
        self.assertTrue(ok)
        argv = run.call_args[0][0]
        self.assertEqual(argv[:2], ["osascript", "-e"])
        self.assertEqual(len(argv), 3)
        self.assertIn('send "say \\"hi\\"; do shell script \\"x\\"" to buddy "+100"', argv[2])


if __name__ == "__main__":
    unittest.main()
