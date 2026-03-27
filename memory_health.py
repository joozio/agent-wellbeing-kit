#!/usr/bin/env python3
"""
Memory Health - Check agent memory files for bloat, staleness, and thrashing.

Memory systems degrade silently. This catches it before output quality drops.

CLI usage:
    python3 memory_health.py --check                     # check configured paths
    python3 memory_health.py --check /path/to/memory/    # check specific path
    python3 memory_health.py --json                      # output as JSON

Library usage:
    from memory_health import check_health
    report = check_health(["/path/to/memory.md"])
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from utils import load_config, load_state, save_state


def check_file(path, max_size_kb=50, stale_days=7):
    """Check a single file's health.

    Returns dict with status (ok/warn/error) and details.
    """
    p = Path(path).expanduser()
    if not p.exists():
        return {"path": str(p), "status": "error", "issue": "not found"}

    stat = p.stat()
    size_kb = stat.st_size / 1024
    modified = datetime.fromtimestamp(stat.st_mtime)
    age_days = (datetime.now() - modified).days

    issues = []
    status = "ok"

    if size_kb > max_size_kb:
        issues.append(f"bloat: {size_kb:.0f}KB (threshold: {max_size_kb}KB)")
        status = "warn"

    if age_days > stale_days:
        issues.append(f"stale: not modified in {age_days} days (threshold: {stale_days}d)")
        status = "warn"

    return {
        "path": str(p),
        "status": status,
        "size_kb": round(size_kb, 1),
        "age_days": age_days,
        "last_modified": modified.isoformat(),
        "issues": issues,
    }


def check_health(paths=None, config=None):
    """Check all configured memory paths.

    Args:
        paths: list of file/dir paths to check (uses config if None)
        config: optional config dict

    Returns:
        dict with files list, summary counts, and overall status
    """
    if config is None:
        config = load_config()

    mh_config = config.get("memory_health", {})
    max_size_kb = mh_config.get("max_size_kb", 50)
    stale_days = mh_config.get("stale_days", 7)

    if paths is None:
        paths = mh_config.get("paths", [])

    results = []
    for path in paths:
        p = Path(path).expanduser()
        if p.is_dir():
            for f in sorted(p.iterdir()):
                if f.is_file() and not f.name.startswith('.'):
                    results.append(check_file(f, max_size_kb, stale_days))
        else:
            results.append(check_file(p, max_size_kb, stale_days))

    ok = sum(1 for r in results if r["status"] == "ok")
    warn = sum(1 for r in results if r["status"] == "warn")
    error = sum(1 for r in results if r["status"] == "error")

    overall = "healthy" if warn == 0 and error == 0 else "degraded" if error == 0 else "unhealthy"

    report = {
        "checked_at": datetime.now().isoformat(),
        "overall": overall,
        "files": results,
        "summary": {"ok": ok, "warn": warn, "error": error, "total": len(results)},
    }

    # Persist to state
    state = load_state()
    state["memory_health"] = {
        "last_check": report["checked_at"],
        "overall": overall,
        "summary": report["summary"],
    }
    save_state(state)

    return report


def _print_report(report):
    """Print human-readable health report."""
    print(f"Memory health: {report['overall'].upper()}")
    print(f"Checked {report['summary']['total']} file(s)\n")

    for f in report["files"]:
        icon = "OK" if f["status"] == "ok" else "WARN" if f["status"] == "warn" else "ERR"
        line = f"  [{icon}] {f['path']}"
        if f.get("size_kb") is not None:
            line += f" ({f['size_kb']}KB, {f['age_days']}d old)"
        print(line)
        for issue in f.get("issues", []):
            print(f"        {issue}")

    s = report["summary"]
    if s["warn"] or s["error"]:
        print(f"\n{s['warn']} warning(s), {s['error']} error(s)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Agent memory health checker")
    parser.add_argument("--check", nargs="*", default=None,
                        help="Check paths (or configured defaults if no args)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.check is None:
        parser.print_help()
        sys.exit(2)

    paths = args.check if args.check else None
    report = check_health(paths)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_report(report)

    sys.exit(0 if report["overall"] == "healthy" else 1)


if __name__ == "__main__":
    main()
