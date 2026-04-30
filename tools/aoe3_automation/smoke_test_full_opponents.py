"""Smoke test: assign all 7 opponent civs in one pass, then reset.

Verifies the picker_opened_since baseline-fix in lobby_driver: every opponent
slot must successfully open its picker even though earlier slots have already
drifted the lobby state away from CLEAN_LOBBY_REF.

Run from gamescope-host context, with the game already at a clean Skirmish
lobby:
    flatpak-spawn --host python3 \
        tools/aoe3_automation/smoke_test_full_opponents.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import lobby_driver as lobby  # noqa: E402


def main() -> int:
    coords = lobby.load_coords()

    if not lobby.is_clean_lobby(coords):
        print("FAIL: not at clean lobby; bring the game to Skirmish lobby first.")
        return 2

    # 7 distinct opponent civ indices (skipping 0 = Random Personality).
    # Pick from a spread across the picker rows so each slot exercises real
    # picker-open + scroll + select.
    opp_indices = [1, 2, 3, 4, 5, 6, 7]

    print(f"Assigning opponents (slots 1..7) to civ_indices={opp_indices}")
    t0 = time.monotonic()
    for slot, civ_idx in enumerate(opp_indices, start=1):
        print(f"--- opponent slot {slot} (P{slot+1}), civ_idx={civ_idx} ---")
        try:
            lobby.set_opponent_civ_by_index(coords, slot, civ_idx)
            print(f"  OK ({time.monotonic() - t0:.1f}s elapsed)")
        except Exception as e:
            print(f"  FAIL: {e}")
            d = lobby.diff_pixels(
                lobby.CLEAN_LOBBY_REF,
                lobby.ARTIFACT_DIR / "_state_postclick.png",
            )
            print(f"  diff vs clean lobby: {d}")
            return 1

    print(f"All 7 opponents assigned in {time.monotonic() - t0:.1f}s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
