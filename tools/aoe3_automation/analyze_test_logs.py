#!/usr/bin/env python3
"""
Analyze logs from ANEWWORLD scenario tests.

Parses Age3Log.txt for trigger output and validates against expected patterns.
"""

import re
import sys
from pathlib import Path
from datetime import datetime

DEFAULT_LOG_PATH = (
    Path.home()
    / ".steam/steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser"
    / "Games/Age of Empires 3 DE/Logs/Age3Log.txt"
)

TRIGGER_PATTERNS = {
    "ageup": r"\[AGEUP\]",
    "units": r"\[UNITS(?:_TRAINED)?\]",
    "buildings": r"\[BUILDINGS?\]",
    "cards": r"\[CARDS?\]",
    "trade_routes": r"\[TRADE(?:_ROUTES)?\]",
    "game_end": r"\[GAME_END\]|(?:Victory|Defeat|Resignation)",
}


def analyze_log(log_path: Path) -> dict:
    """Parse log file and extract metrics."""
    result = {
        "file": str(log_path),
        "exists": log_path.exists(),
        "size": 0,
        "triggers": {},
        "errors": [],
        "game_end": None,
        "game_duration": None,
    }

    if not log_path.exists():
        result["errors"].append("Log file not found")
        return result

    try:
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        result["size"] = len(log_text)

        # Check for triggers
        for trigger_name, pattern in TRIGGER_PATTERNS.items():
            matches = re.findall(pattern, log_text)
            result["triggers"][trigger_name] = len(matches) > 0

        # Check for game end
        if re.search(r"Victory|Defeat|Resignation", log_text):
            match = re.search(r"(Victory|Defeat|Resignation)", log_text)
            if match:
                result["game_end"] = match.group(1)

        # Try to extract game duration
        time_match = re.search(r"Game time: (\d+):(\d+):(\d+)", log_text)
        if time_match:
            h, m, s = int(time_match.group(1)), int(time_match.group(2)), int(time_match.group(3))
            result["game_duration"] = f"{h}:{m:02d}:{s:02d}"

        # Look for errors/crashes
        if re.search(r"(crash|exception|error|failed)", log_text, re.IGNORECASE):
            result["errors"].append("Potential error/crash detected in log")

    except Exception as e:
        result["errors"].append(f"Failed to parse log: {e}")

    return result


def print_report(result: dict) -> None:
    """Print formatted report."""
    print("\n" + "="*80)
    print("ANEWWORLD SCENARIO TEST RESULTS")
    print("="*80)

    print(f"\nLog File: {result['file']}")
    print(f"Exists: {'✓' if result['exists'] else '✗'}")
    print(f"Size: {result['size']:,} bytes")

    if result["errors"]:
        print(f"\n⚠ Errors ({len(result['errors'])}):")
        for e in result["errors"]:
            print(f"  - {e}")

    print(f"\nTriggers Detected:")
    for trigger_name, found in result["triggers"].items():
        icon = "✓" if found else "✗"
        print(f"  {icon} {trigger_name:15} {'found' if found else 'not found'}")

    if result["game_end"]:
        print(f"\nGame Result: {result['game_end']}")

    if result["game_duration"]:
        print(f"Game Duration: {result['game_duration']}")

    # Summary
    trigger_count = sum(1 for v in result["triggers"].values() if v)
    total_triggers = len(result["triggers"])
    print(f"\n📊 Summary: {trigger_count}/{total_triggers} triggers detected")

    if trigger_count == total_triggers:
        print("✓ TEST PASSED — All triggers fired!")
    elif trigger_count >= 4:
        print("⚠ TEST PARTIAL — Most triggers fired")
    else:
        print("✗ TEST FAILED — Insufficient triggers detected")

    print("="*80)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Analyze ANEWWORLD scenario test logs")
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH,
                        help="Path to Age3Log.txt")
    args = parser.parse_args()

    result = analyze_log(args.log_path)
    print_report(result)

    # Return non-zero if test failed
    trigger_count = sum(1 for v in result["triggers"].values() if v)
    return 0 if trigger_count >= 4 else 1


if __name__ == "__main__":
    sys.exit(main())
