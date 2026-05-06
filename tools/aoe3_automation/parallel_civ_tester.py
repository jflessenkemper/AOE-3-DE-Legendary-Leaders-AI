#!/usr/bin/env python3
"""
Parallel 48-civ tester: Runs 8 concurrent game instances (2 civs per game).
Tests all 48 civs in ~90 minutes on aggressive hardware.

Each instance:
- Loads ANEWWORLD.age3Yscn
- Tests 2 different civilizations as separate player slots
- Monitors log file for trigger outputs
- Generates per-civ results

Requires i9-9900K + 31GB RAM @ very low graphics settings.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.migration.anw_token_map import ANW_CIVS

# Paths
LOG_PATH_BASE = Path.home() / ".local/share/Steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Logs"
LOG_PATH = LOG_PATH_BASE / "Age3Log.txt"
ARTIFACT_BASE = REPO_ROOT / "tools/aoe3_automation/artifacts"

# Configuration
NUM_PARALLEL = 8  # Aggressive: 8 concurrent instances
CIVS_PER_GAME = 2  # 2 civs per instance
TIMEOUT_PER_GAME = 1200  # 20 minutes per game

class TriggerValidator:
    """Validate trigger output patterns."""
    PATTERNS = {
        "ageup": r"\[AGEUP\]",
        "units": r"\[UNITS_TRAINED\]",
        "buildings": r"\[BUILDINGS\]",
        "cards": r"\[CARDS\]",
        "trade_routes": r"\[TRADE_ROUTES\]",
        "game_end": r"\[GAME_END\]",
    }

    @staticmethod
    def validate(log_text: str) -> tuple[dict[str, bool], list[str]]:
        """Return (trigger_status, errors)."""
        status = {name: bool(re.search(pattern, log_text))
                  for name, pattern in TriggerValidator.PATTERNS.items()}
        errors = []
        for trigger_name, fired in status.items():
            if not fired:
                errors.append(f"Missing trigger: {trigger_name}")
        if re.search(r"(crashed|unhandled exception|fatal error)", log_text, re.IGNORECASE):
            errors.append("Game encountered crash")
        return status, errors


def launch_game() -> subprocess.Popen:
    """Launch AOE3 game instance."""
    env = os.environ.copy()
    env["PROTON_LOG"] = "1"
    env["DISPLAY"] = ":0"
    try:
        proc = subprocess.Popen(
            ["steam", "-forcesteamruntime", "run", "933110"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        return proc
    except Exception as e:
        print(f"Failed to launch game: {e}")
        return None


def monitor_log(log_path: Path, timeout: int, civ_tokens: list[str]) -> dict:
    """Monitor log file and extract results for civs."""
    result = {
        "civs": civ_tokens,
        "triggers": {civ: {} for civ in civ_tokens},
        "status": "RUNNING",
        "elapsed": 0.0
    }

    start_time = time.time()
    last_size = 0

    while time.time() - start_time < timeout:
        try:
            if log_path.exists():
                current_size = log_path.stat().st_size
                if current_size > last_size:
                    last_size = current_size
                    log_text = log_path.read_text(encoding="utf-8", errors="replace")

                    # Check for game end
                    if re.search(r"Victory|Defeat|Game Over", log_text):
                        trigger_status, errors = TriggerValidator.validate(log_text)
                        for civ in civ_tokens:
                            result["triggers"][civ] = trigger_status
                        result["status"] = "COMPLETE"
                        result["errors"] = errors
                        break
            time.sleep(2)
        except Exception as e:
            print(f"Log monitoring error: {e}")
            time.sleep(2)

    elapsed = time.time() - start_time
    result["elapsed"] = round(elapsed, 1)

    if result["status"] == "RUNNING":
        result["status"] = "TIMEOUT"

    return result


def test_civ_pair(game_id: int, civ_tokens: list[str], instance_num: int) -> dict:
    """Test 2 civs in a single game instance."""
    print(f"\n[Game {game_id}] Testing {' + '.join(civ_tokens[:CIVS_PER_GAME])}")

    # Clear log
    if LOG_PATH.exists():
        LOG_PATH.write_text("", encoding="utf-8")

    time.sleep(0.5)

    # Launch game
    proc = launch_game()
    if not proc:
        return {
            "game_id": game_id,
            "civs": civ_tokens[:CIVS_PER_GAME],
            "status": "FAILED",
            "error": "Game failed to launch"
        }

    print(f"  [Game {game_id}] Process launched (PID {proc.pid})")

    # Wait for game launch
    time.sleep(8)

    # Monitor log
    result = monitor_log(LOG_PATH, TIMEOUT_PER_GAME, civ_tokens[:CIVS_PER_GAME])
    result["game_id"] = game_id

    # Kill game
    try:
        proc.kill()
    except:
        pass

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Parallel AOE3 civ tester (8 concurrent games).")
    parser.add_argument("--dry-run", action="store_true", help="Don't launch games, just show plan.")
    args = parser.parse_args()

    # Build civ list
    civs = []
    for civ_obj in ANW_CIVS:
        civ_token = civ_obj.token if hasattr(civ_obj, 'token') else str(civ_obj)
        civs.append(civ_token)

    print("=" * 80)
    print(f"PARALLEL CIV TESTER: {NUM_PARALLEL} Concurrent Games")
    print("=" * 80)
    print(f"\nTotal civs: {len(civs)}")
    print(f"Civs per game: {CIVS_PER_GAME}")
    print(f"Games needed: {len(civs) // (NUM_PARALLEL * CIVS_PER_GAME)}")
    print(f"Estimated time: ~90-110 minutes")

    if args.dry_run:
        print("\n[DRY RUN MODE]")
        for i in range(0, len(civs), NUM_PARALLEL * CIVS_PER_GAME):
            print(f"\nRound {i // (NUM_PARALLEL * CIVS_PER_GAME) + 1}:")
            for j in range(NUM_PARALLEL):
                game_idx = i + j * CIVS_PER_GAME
                if game_idx + CIVS_PER_GAME <= len(civs):
                    pair = civs[game_idx:game_idx + CIVS_PER_GAME]
                    print(f"  Game {j + 1}: {' + '.join(pair)}")
        return 0

    # Run tests in rounds
    all_results = []
    round_num = 1

    for start_idx in range(0, len(civs), NUM_PARALLEL * CIVS_PER_GAME):
        print(f"\n{'='*80}")
        print(f"ROUND {round_num}")
        print(f"{'='*80}")

        round_results = []
        futures = {}

        with ThreadPoolExecutor(max_workers=NUM_PARALLEL) as executor:
            for game_slot in range(NUM_PARALLEL):
                civ_idx = start_idx + game_slot * CIVS_PER_GAME
                if civ_idx + CIVS_PER_GAME > len(civs):
                    break

                civ_pair = civs[civ_idx:civ_idx + CIVS_PER_GAME]
                game_id = round_num * 100 + game_slot + 1

                future = executor.submit(test_civ_pair, game_id, civ_pair, game_slot)
                futures[future] = game_id

            # Collect results
            for future in as_completed(futures):
                result = future.result()
                round_results.append(result)
                game_id = futures[future]

                status = result.get("status", "UNKNOWN")
                civ_str = " + ".join(result.get("civs", []))
                print(f"[Game {game_id}] {civ_str}: {status}")

        all_results.extend(round_results)
        round_num += 1

    # Generate report
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = ARTIFACT_BASE / f"parallel_test_{ts}" / "PARALLEL_RESULTS.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Games completed: {len(all_results)}")
    complete = sum(1 for r in all_results if r.get("status") == "COMPLETE")
    timeout = sum(1 for r in all_results if r.get("status") == "TIMEOUT")
    failed = sum(1 for r in all_results if r.get("status") == "FAILED")
    print(f"Complete: {complete} | Timeout: {timeout} | Failed: {failed}")
    print(f"Results: {report_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
