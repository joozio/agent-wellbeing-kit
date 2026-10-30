#!/usr/bin/env python3
"""Browser tests for dashboard.html.

Runs headless Chromium through Node Playwright. Skipped when node or the
playwright package is not available, so the stdlib-only suite still passes.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parent / "dashboard.html"

# Loads a state.json through the file picker and reports what rendered.
NODE_SCRIPT = r"""
const { chromium } = require('playwright');
const [url, stateJson, tz, fixedTime] = process.argv.slice(1);
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext(tz ? { timezoneId: tz } : {});
  const page = await context.newPage();
  if (fixedTime) await page.clock.setFixedTime(new Date(fixedTime));
  await page.goto(url);
  await page.setInputFiles('#file-input', {
    name: 'state.json', mimeType: 'application/json', buffer: Buffer.from(stateJson),
  });
  await page.waitForSelector('#dashboard', { state: 'visible' });
  await page.waitForTimeout(200);
  const out = await page.evaluate(() => ({
    xss: window.__xss === 1,
    errorDetailText: document.getElementById('error-detail').textContent,
    memoryText: document.getElementById('memory-status').textContent,
    bars: [...document.querySelectorAll('#week-chart .bar')].map(b => !b.classList.contains('missed')),
    nudges: [...document.querySelectorAll('#nudge-list li')].map(li => ({
      name: li.textContent, sent: li.querySelector('.dot').classList.contains('sent'),
    })),
  }));
  console.log(JSON.stringify(out));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def _playwright_available():
    if not shutil.which("node"):
        return False
    r = subprocess.run(["node", "-e", "require('playwright')"], capture_output=True)
    return r.returncode == 0


def render(state, tz="", fixed_time=""):
    r = subprocess.run(
        ["node", "-e", NODE_SCRIPT, DASHBOARD.as_uri(), json.dumps(state), tz, fixed_time],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout.strip().splitlines()[-1])


@unittest.skipUnless(_playwright_available(), "node + playwright not installed")
class TestDashboardEscaping(unittest.TestCase):

    def test_state_values_are_not_executed_as_html(self):
        payload = '<img src=x onerror="window.__xss=1">'
        out = render({
            "memory_health": {"overall": payload, "summary": {}},
            "error_registry": {"last_scan": "2026-01-01T00:00:00", "total_errors": payload,
                               "alerts": [payload]},
        })
        self.assertFalse(out["xss"])
        self.assertIn(payload, out["errorDetailText"])


if __name__ == "__main__":
    unittest.main()
