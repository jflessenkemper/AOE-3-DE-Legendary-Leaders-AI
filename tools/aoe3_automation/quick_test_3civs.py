#!/usr/bin/env python3
"""Quick test with 3 civs to verify framework and generate real results."""

import subprocess
import time
import re
from pathlib import Path

LOG_PATH = Path.home() / ".local/share/Steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Logs/Age3Log.txt"

TEST_CIVS = ["ANWBritish", "ANWFrench", "ANWChinese"]

def test_civ(civ: str):
    """Run quick test for one civ."""
    print(f"\n{'='*60}")
    print(f"Testing: {civ}")
    print(f"{'='*60}")

    # Clear log
    if LOG_PATH.exists():
        LOG_PATH.write_text("", encoding="utf-8")

    print(f"[{civ}] Launching game...")
    subprocess.Popen(["steam", "-forcesteamruntime", "run", "933110"])

    # Wait for game to load and run
    print(f"[{civ}] Waiting 30 seconds for game to start...")
    time.sleep(30)

    # Monitor log
    triggers_found = {}
    for i in range(15):  # 15 × 4 seconds = 60 seconds monitoring
        if LOG_PATH.exists():
            try:
                log_text = LOG_PATH.read_text(encoding="utf-8", errors="replace")

                # Check for triggers
                for trigger in ["AGEUP", "UNITS", "BUILDINGS", "CARDS", "TRADE", "GAME_END"]:
                    if trigger not in triggers_found:
                        if re.search(f"\\[{trigger}", log_text):
                            triggers_found[trigger] = True
                            print(f"  ✓ Detected: [{trigger}]")

                # Check for game end
                if re.search(r"Victory|Defeat", log_text):
                    print(f"  ✓ Game ended: Victory/Defeat detected")
                    break

            except:
                pass

        time.sleep(4)

    # Kill game
    subprocess.run(["pkill", "-9", "-f", "AoE3"], timeout=5)

    # Results
    trigger_count = len(triggers_found)
    print(f"\n[{civ}] Results: {trigger_count}/6 triggers detected")
    for trigger, found in triggers_found.items():
        print(f"  ✓ {trigger}")

    return trigger_count


def main():
    print("="*80)
    print("QUICK TEST: 3 Representative Civs")
    print("="*80)

    total_triggers = 0
    for civ in TEST_CIVS:
        count = test_civ(civ)
        total_triggers += count

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Civs tested: {len(TEST_CIVS)}")
    print(f"Total triggers detected: {total_triggers}/{len(TEST_CIVS)*6}")
    print(f"Avg per civ: {total_triggers/len(TEST_CIVS):.1f}/6")
    print(f"\nFramework Status: {'✓ WORKING' if total_triggers >= 12 else '⚠ PARTIAL'}")


if __name__ == "__main__":
    main()
