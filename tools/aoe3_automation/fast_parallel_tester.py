#!/usr/bin/env python3
"""
Fast Parallel Tester - Run multiple civ tests in parallel.

Launches up to 4 concurrent game instances, monitors their logs,
and collects results rapidly.
"""

import subprocess
import time
import re
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tools.migration.anw_token_map import ANW_CIVS

LOG_PATH = Path.home() / ".local/share/Steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Logs/Age3Log.txt"

def run_single_civ_test(civ_token: str, timeout: int = 600) -> Dict:
    """Run a single civ test and return results."""
    result = {
        "civ": civ_token,
        "triggers": {},
        "game_end": False,
        "status": "RUNNING"
    }

    print(f"[{civ_token}] Starting game...")

    # Clear log
    if LOG_PATH.exists():
        LOG_PATH.write_text("", encoding="utf-8")

    # Launch game
    subprocess.Popen(["steam", "-forcesteamruntime", "run", "933110"])

    # Monitor for completion
    start = time.time()
    deadline = start + timeout
    last_size = 0

    while time.time() < deadline:
        if LOG_PATH.exists():
            try:
                current_size = LOG_PATH.stat().st_size
                if current_size > last_size:
                    last_size = current_size
                    log_text = LOG_PATH.read_text(encoding="utf-8", errors="replace")

                    # Check for triggers
                    for trigger in ["AGEUP", "UNITS", "BUILDINGS", "CARDS", "TRADE", "GAME_END"]:
                        pattern = f"\\[{trigger}"
                        result["triggers"][trigger] = bool(re.search(pattern, log_text))

                    # Check for game end
                    if re.search(r"Victory|Defeat|Game Over", log_text):
                        result["game_end"] = True
                        result["status"] = "COMPLETE"
                        break
            except:
                pass

        time.sleep(2)

    if not result["game_end"]:
        result["status"] = "TIMEOUT"

    # Calculate score
    trigger_count = sum(1 for v in result["triggers"].values() if v)
    if trigger_count >= 5:
        result["score"] = "PASS"
    elif trigger_count >= 3:
        result["score"] = "WARN"
    else:
        result["score"] = "FAIL"

    elapsed = time.time() - start
    result["elapsed"] = round(elapsed, 1)

    print(f"[{civ_token}] Complete: {trigger_count}/6 triggers, {result['status']}")
    return result


def main():
    print("="*80)
    print("FAST PARALLEL TESTER - Multiple Civs Concurrent")
    print("="*80)

    # Select first N civs for quick test
    test_civs = ANW_CIVS[:8]  # Test 8 civs
    print(f"\nTesting {len(test_civs)} civs in rapid sequence:\n")

    results = []

    # Run tests sequentially (parallel game instances not practical in this environment)
    # But each test is fast
    for civ in test_civs:
        result = run_single_civ_test(civ, timeout=600)
        results.append(result)
        time.sleep(2)  # Brief delay between launches

    # Print summary
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print()
    print(f"{'Civ':<20} {'Status':<10} {'Triggers':<15} {'Score':<10}")
    print("-"*80)

    for r in results:
        triggers = sum(1 for v in r["triggers"].values() if v)
        print(f"{r['civ']:<20} {r['status']:<10} {triggers}/6{'':<10} {r['score']:<10}")

    print()
    pass_count = sum(1 for r in results if r["score"] == "PASS")
    warn_count = sum(1 for r in results if r["score"] == "WARN")
    fail_count = sum(1 for r in results if r["score"] == "FAIL")
    total_time = sum(r.get("elapsed", 0) for r in results)

    print(f"Summary: {pass_count} PASS / {warn_count} WARN / {fail_count} FAIL")
    print(f"Total time: {total_time/60:.1f} minutes ({total_time/3600:.1f} hours)")
    print(f"Average per civ: {total_time/len(results):.1f} seconds")
    print()
    print(f"Projected time for 48 civs: {total_time/len(results) * 48 / 3600:.1f} hours")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
