#!/usr/bin/env python3
"""
Simple game launcher and log monitor.

Launches AOE3, monitors Age3Log.txt for game completion, parses results.
"""

import subprocess
import time
import sys
import re
from pathlib import Path

LOG_PATH = (
    Path.home()
    / ".steam/steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser"
    / "Games/Age of Empires 3 DE/Logs/Age3Log.txt"
)

def launch_game():
    """Launch AOE3 DE."""
    print("🎮 Launching AOE3 DE...")
    subprocess.Popen(["steam", "-forcesteamruntime", "run", "933110"])
    time.sleep(10)
    print("⏳ Game launched, waiting for it to become playable...")

def monitor_log_until_game_end(timeout_seconds=900):
    """Monitor log file until game ends or timeout."""
    start_time = time.time()
    deadline = start_time + timeout_seconds
    last_size = 0

    print(f"📊 Monitoring Age3Log.txt for up to {timeout_seconds}s...")

    while time.time() < deadline:
        if not LOG_PATH.exists():
            time.sleep(5)
            continue

        try:
            current_size = LOG_PATH.stat().st_size
            if current_size > last_size:
                last_size = current_size
                log_text = LOG_PATH.read_text(encoding="utf-8", errors="replace")

                # Check for game start (scenario loaded)
                if "Game startup complete" in log_text and "Scenario" in log_text:
                    print("✓ Game loaded")

                # Check for triggers
                if "[AGEUP]" in log_text:
                    print("✓ Age-up trigger detected")
                if "[UNITS" in log_text:
                    print("✓ Units trigger detected")
                if "[BUILDINGS" in log_text:
                    print("✓ Buildings trigger detected")
                if "[CARDS" in log_text:
                    print("✓ Cards trigger detected")
                if "[TRADE" in log_text:
                    print("✓ Trade routes trigger detected")
                if "[GAME_END]" in log_text or "Victory" in log_text or "Defeat" in log_text:
                    print("✓ Game ended")
                    return log_text

            time.sleep(5)
        except Exception as e:
            print(f"⚠ Error reading log: {e}")
            time.sleep(5)

    print(f"⏱ Timeout after {timeout_seconds}s")
    if LOG_PATH.exists():
        return LOG_PATH.read_text(encoding="utf-8", errors="replace")
    return ""

def analyze_log(log_text):
    """Analyze log for triggers and game events."""
    results = {
        "triggers": {},
        "game_end": None,
        "errors": [],
    }

    patterns = {
        "ageup": r"\[AGEUP\]",
        "units": r"\[UNITS(?:_TRAINED)?\]",
        "buildings": r"\[BUILDINGS?\]",
        "cards": r"\[CARDS?\]",
        "trade": r"\[TRADE(?:_ROUTES)?\]",
        "game_end": r"\[GAME_END\]|Victory|Defeat",
    }

    for trigger, pattern in patterns.items():
        results["triggers"][trigger] = bool(re.search(pattern, log_text))

    if re.search(r"Victory|Defeat", log_text):
        match = re.search(r"(Victory|Defeat)", log_text)
        if match:
            results["game_end"] = match.group(1)

    if re.search(r"crash|exception|error", log_text, re.IGNORECASE):
        results["errors"].append("Possible crash/error in log")

    return results

def print_results(results):
    """Print test results."""
    print("\n" + "="*60)
    print("GAME TEST RESULTS")
    print("="*60)

    print("\nTriggers:")
    for trigger, found in results["triggers"].items():
        icon = "✓" if found else "✗"
        print(f"  {icon} {trigger:15} {'fired' if found else 'not fired'}")

    fired_count = sum(1 for v in results["triggers"].values() if v)
    total_triggers = len(results["triggers"])

    print(f"\nResult: {fired_count}/{total_triggers} triggers")

    if results["game_end"]:
        print(f"Game ended with: {results['game_end']}")

    if results["errors"]:
        print(f"\nErrors:")
        for e in results["errors"]:
            print(f"  ⚠ {e}")

    if fired_count >= 4:
        print("\n✓ TEST PASSED")
        return 0
    else:
        print("\n✗ TEST FAILED")
        return 1

def main():
    print("\n" + "="*60)
    print("AOE3 GAME TEST RUNNER")
    print("="*60)

    # Clear old log
    if LOG_PATH.exists():
        LOG_PATH.write_text("", encoding="utf-8")

    launch_game()
    log_text = monitor_log_until_game_end(timeout_seconds=900)

    if not log_text:
        print("\n✗ No log file created")
        return 1

    results = analyze_log(log_text)
    return print_results(results)

if __name__ == "__main__":
    sys.exit(main())
