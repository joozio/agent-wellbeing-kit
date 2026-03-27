#!/usr/bin/env python3
"""
Error Registry - Detect silent agent failures.

Scans log files for repeating errors, stuck loops, and rising error rates.
Catches the problems your agent won't tell you about.

CLI usage:
    python3 error_registry.py --scan agent.log
    python3 error_registry.py --feed              # reads stdin
    python3 error_registry.py --summary           # show current error state
    python3 error_registry.py --clear             # reset error state

Library usage:
    from error_registry import check_errors, get_summary
"""

import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from utils import load_config, load_state, save_state


def _normalize(line):
    """Normalize a log line for fingerprinting.

    Strips timestamps, UUIDs, hex IDs, and numeric sequences so that
    repeated errors with different metadata match the same fingerprint.
    """
    line = line.strip().lower()
    # Strip ISO timestamps
    line = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d]*[z]?', '', line)
    # Strip UUIDs
    line = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<id>', line)
    # Strip hex IDs (8+ chars)
    line = re.sub(r'[0-9a-f]{8,}', '<hex>', line)
    # Strip bare numbers
    line = re.sub(r'\b\d+\b', '<n>', line)
    return line[:120]


def _is_error_line(line, patterns):
    """Check if a line matches any of the configured error patterns."""
    lower = line.lower()
    return any(p.lower() in lower for p in patterns)


def check_errors(lines, config=None):
    """Scan log lines and return error analysis.

    Args:
        lines: iterable of log lines (strings)
        config: optional config dict (loaded from config.json if None)

    Returns:
        dict with keys: repeating, loops, total_errors, alerts
    """
    if config is None:
        config = load_config()

    er_config = config.get("error_registry", {})
    repeat_threshold = er_config.get("repeat_threshold", 3)
    loop_threshold = er_config.get("loop_threshold", 5)
    patterns = er_config.get("log_patterns", ["ERROR", "FAIL", "Exception", "Traceback"])

    fingerprints = Counter()
    error_count = 0

    for line in lines:
        line = line.rstrip('\n')
        if _is_error_line(line, patterns):
            error_count += 1
            fp = _normalize(line)
            fingerprints[fp] += 1

    # Repeating errors: same fingerprint appears N+ times
    repeating = {fp: count for fp, count in fingerprints.items()
                 if count >= repeat_threshold}

    # Loop detection: any single fingerprint appears loop_threshold+ times
    loops = {fp: count for fp, count in fingerprints.items()
             if count >= loop_threshold}

    # Build alerts
    alerts = []
    if repeating:
        alerts.append(f"{len(repeating)} repeating error(s) detected")
    if loops:
        alerts.append(f"{len(loops)} possible stuck loop(s)")
    if error_count > 50:
        alerts.append(f"High error volume: {error_count} errors")

    return {
        "repeating": repeating,
        "loops": loops,
        "total_errors": error_count,
        "alerts": alerts,
        "scanned_at": datetime.now().isoformat(),
    }


def get_summary():
    """Get the most recent error registry summary from state."""
    state = load_state()
    return state.get("error_registry", {})


def _save_results(results):
    """Persist scan results to state.json."""
    state = load_state()
    state["error_registry"] = {
        "last_scan": results["scanned_at"],
        "total_errors": results["total_errors"],
        "repeating_count": len(results["repeating"]),
        "loop_count": len(results["loops"]),
        "alerts": results["alerts"],
        "top_errors": dict(Counter(results["repeating"]).most_common(5)),
    }
    save_state(state)


def _print_results(results):
    """Print human-readable scan results."""
    if not results["total_errors"]:
        print("Clean. No errors found.")
        return

    print(f"Errors found: {results['total_errors']}")

    if results["repeating"]:
        print(f"\nRepeating ({len(results['repeating'])}):")
        for fp, count in sorted(results["repeating"].items(), key=lambda x: -x[1]):
            print(f"  {count}x  {fp[:80]}")

    if results["loops"]:
        print(f"\nPossible stuck loops ({len(results['loops'])}):")
        for fp, count in sorted(results["loops"].items(), key=lambda x: -x[1]):
            print(f"  {count}x  {fp[:80]}")

    if results["alerts"]:
        print(f"\nAlerts:")
        for a in results["alerts"]:
            print(f"  ! {a}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Agent error registry")
    parser.add_argument("--scan", metavar="FILE", help="Scan a log file for errors")
    parser.add_argument("--feed", action="store_true", help="Read from stdin")
    parser.add_argument("--summary", action="store_true", help="Show last scan summary")
    parser.add_argument("--clear", action="store_true", help="Clear error state")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.summary:
        summary = get_summary()
        if args.json:
            print(json.dumps(summary, indent=2))
        elif summary:
            print(f"Last scan: {summary.get('last_scan', 'never')}")
            print(f"Errors: {summary.get('total_errors', 0)}")
            print(f"Repeating: {summary.get('repeating_count', 0)}")
            print(f"Loops: {summary.get('loop_count', 0)}")
            for a in summary.get("alerts", []):
                print(f"  ! {a}")
        else:
            print("No scan data yet. Run --scan or --feed first.")
        return

    if args.clear:
        state = load_state()
        state.pop("error_registry", None)
        save_state(state)
        print("Error registry cleared.")
        return

    if args.scan:
        try:
            lines = Path(args.scan).read_text().splitlines()
        except FileNotFoundError:
            print(f"File not found: {args.scan}", file=sys.stderr)
            sys.exit(1)
    elif args.feed:
        lines = sys.stdin.readlines()
    else:
        parser.print_help()
        sys.exit(2)

    results = check_errors(lines)
    _save_results(results)

    if args.json:
        out = {**results, "repeating": dict(results["repeating"]), "loops": dict(results["loops"])}
        print(json.dumps(out, indent=2))
    else:
        _print_results(results)

    sys.exit(1 if results["alerts"] else 0)


if __name__ == "__main__":
    main()
