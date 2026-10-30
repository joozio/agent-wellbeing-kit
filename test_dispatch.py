#!/usr/bin/env python3
"""Tests for dispatch.sh: the right nudge runs at the right hour.

dispatch.sh is copied into a temp dir next to stub nudge scripts that only
record how they were called, and `date` is faked on PATH.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent
REAL_DATE = shutil.which("date")

STUB = """import sys
from pathlib import Path
with open(Path(__file__).parent / "calls.log", "a") as f:
    f.write(" ".join([Path(__file__).name] + sys.argv[1:]) + "\\n")
"""

FAKE_DATE = """#!/bin/sh
case "$1" in
  +%H) echo "$FAKE_HOUR" ;;
  +%u) echo "$FAKE_DOW" ;;
  *) exec "{real}" "$@" ;;
esac
"""


@unittest.skipUnless(shutil.which("bash") and REAL_DATE, "needs bash and date")
class DispatchTestCase(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.kit = Path(self.tmpdir.name) / "kit"
        self.kit.mkdir()
        shutil.copy(KIT_DIR / "dispatch.sh", self.kit / "dispatch.sh")
        for name in ("morning-nudge.py", "evening-nudge.py", "weekly-checkin.py"):
            (self.kit / name).write_text(STUB)
        self.bin = Path(self.tmpdir.name) / "bin"
        self.bin.mkdir()
        fake = self.bin / "date"
        fake.write_text(FAKE_DATE.format(real=REAL_DATE))
        fake.chmod(0o755)

    def write_config(self, routine):
        config = json.loads((KIT_DIR / "config.example.json").read_text())
        config["routine"].update(routine)
        (self.kit / "config.json").write_text(json.dumps(config))

    def dispatch(self, hour, dow=3):
        env = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}",
                   FAKE_HOUR=hour, FAKE_DOW=str(dow), PYTHON_BIN=sys.executable)
        r = subprocess.run(["bash", str(self.kit / "dispatch.sh")], env=env,
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.kit / "calls.log"
        calls = log.read_text().splitlines() if log.exists() else []
        if log.exists():
            log.unlink()
        return calls


class TestDefaultSchedule(DispatchTestCase):

    def test_morning(self):
        self.assertEqual(self.dispatch("07"), ["morning-nudge.py"])

    def test_followup(self):
        self.assertEqual(self.dispatch("08"), ["morning-nudge.py --followup"])

    def test_evening_weekday_has_no_checkin(self):
        self.assertEqual(self.dispatch("19", dow=3), ["evening-nudge.py"])

    def test_evening_sunday_adds_weekly_checkin(self):
        self.assertEqual(self.dispatch("19", dow=7), ["evening-nudge.py", "weekly-checkin.py"])

    def test_bedtime(self):
        self.assertEqual(self.dispatch("23"), ["evening-nudge.py --bedtime"])

    def test_other_hours_do_nothing(self):
        for hour in ("00", "03", "09", "12", "18", "20", "22"):
            self.assertEqual(self.dispatch(hour), [], hour)


class TestConfiguredHours(DispatchTestCase):
    """SETUP.md: change routine.bedtime / wake_time and the matching schedule entry."""

    def test_bedtime_follows_config(self):
        self.write_config({"bedtime": "22:30"})
        self.assertEqual(self.dispatch("22"), ["evening-nudge.py --bedtime"])
        self.assertEqual(self.dispatch("23"), [])

    def test_bedtime_after_midnight(self):
        self.write_config({"bedtime": "00:15"})
        self.assertEqual(self.dispatch("00"), ["evening-nudge.py --bedtime"])

    def test_wake_time_moves_morning_and_followup(self):
        self.write_config({"wake_time": "06:00"})
        self.assertEqual(self.dispatch("06"), ["morning-nudge.py"])
        self.assertEqual(self.dispatch("07"), ["morning-nudge.py --followup"])
        self.assertEqual(self.dispatch("08"), [])

    def test_unparseable_times_fall_back_to_defaults(self):
        self.write_config({"wake_time": "early", "bedtime": ""})
        self.assertEqual(self.dispatch("07"), ["morning-nudge.py"])
        self.assertEqual(self.dispatch("23"), ["evening-nudge.py --bedtime"])

    def test_broken_config_falls_back_to_defaults(self):
        (self.kit / "config.json").write_text("{not json")
        self.assertEqual(self.dispatch("07"), ["morning-nudge.py"])
        self.assertEqual(self.dispatch("23"), ["evening-nudge.py --bedtime"])


@unittest.skipUnless(os.name == "posix", "cron is POSIX-only")
class TestExecutable(unittest.TestCase):

    def test_dispatch_is_executable(self):
        # crontab entries in older installs call dispatch.sh directly.
        self.assertTrue(os.access(KIT_DIR / "dispatch.sh", os.X_OK))

    def test_cron_examples_call_through_bash(self):
        for doc in (KIT_DIR / "examples" / "crontab.example", KIT_DIR / "SETUP.md"):
            for line in doc.read_text().splitlines():
                if line.rstrip().endswith("dispatch.sh") and line[:1].isdigit():
                    self.assertIn("/bin/bash ", line, f"{doc.name}: {line}")


if __name__ == "__main__":
    unittest.main()
