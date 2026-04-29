"""Verify (and if needed, recalibrate) the P2..P8 civ-picker click coords.

The matrix_runner --batch-size>1 mode packs up to 7 AI opponents into one
match by clicking each opponent's civ-picker button. P1 is empirically
measured at (630, 170); P2..P4 were measured by in_game_driver.py at
y=276/382/488 (106px row spacing). P5..P8 are extrapolated with the same
delta and stored in lobby_coords.json.

This script clicks each slot's picker button, verifies it opened (pixel-
diff vs clean lobby), and Cancels back. If a slot fails, it sweeps a small
Y-window around the expected coord, looking for the working Y, and patches
lobby_coords.json on success.

Run from a clean Skirmish lobby (8-player FFA configuration):
    python3 tools/aoe3_automation/verify_opponent_pickers.py

Add --dry-run to just probe without writing back.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lobby_driver as lobby  # noqa: E402

COORDS_PATH = HERE / "lobby_coords.json"


def probe_slot(coords: dict, slot: int, *, x: int, y: int,
               settle: float = 1.5) -> bool:
    """Click (x,y), check picker opened, Cancel back. Returns True if ok."""
    # Make sure we're at clean lobby first.
    if not lobby.is_clean_lobby(coords):
        # Try Escape to back out of any leftover state.
        lobby.xdo("key Escape")
        time.sleep(0.8)
        if not lobby.is_clean_lobby(coords):
            print(f"  slot {slot}: not at clean lobby — aborting probe")
            return False
    lobby.click(x, y)
    time.sleep(settle)
    opened = lobby.is_picker_open(coords)
    if opened:
        lobby.cancel_civ_picker(coords)
        time.sleep(0.8)
    return opened


def sweep_y(coords: dict, slot: int, x: int, y_center: int,
            *, deltas=(0, -8, 8, -16, 16, -24, 24)) -> int | None:
    """Try y_center first, then small deltas. Return working y or None."""
    for dy in deltas:
        y = y_center + dy
        print(f"  slot {slot}: probing ({x}, {y}) …", end=" ", flush=True)
        ok = probe_slot(coords, slot, x=x, y=y)
        print("OK" if ok else "no")
        if ok:
            return y
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Probe but don't update lobby_coords.json")
    args = ap.parse_args()

    coords = lobby.load_coords()
    pickers = list(coords["lobby"]["opponent_civ_pickers"])
    if not lobby.is_clean_lobby(coords):
        print("ERROR: lobby is not in clean state. Enter the Skirmish lobby first.")
        return 2

    print(f"Verifying {len(pickers)} opponent picker coords (P2..P{1+len(pickers)})…")
    updates: list[tuple[int, list[int]]] = []
    failures: list[int] = []

    for i, (x, y) in enumerate(pickers):
        slot = i + 1  # 1..7 -> P2..P8
        print(f"\nP{slot+1} (slot={slot}): expected ({x}, {y})")
        ok = probe_slot(coords, slot, x=x, y=y)
        if ok:
            print(f"  ✓ P{slot+1} picker opens at ({x}, {y})")
            continue
        # Sweep around the expected y.
        print(f"  ✗ first probe missed; sweeping Y around {y}")
        new_y = sweep_y(coords, slot, x, y)
        if new_y is None:
            print(f"  FAIL: P{slot+1} no working Y found in sweep")
            failures.append(slot)
            continue
        print(f"  ✓ P{slot+1} works at ({x}, {new_y}) (delta={new_y - y})")
        updates.append((i, [x, new_y]))

    if updates and not args.dry_run:
        for i, new_coord in updates:
            pickers[i] = new_coord
        coords["lobby"]["opponent_civ_pickers"] = pickers
        COORDS_PATH.write_text(json.dumps(coords, indent=2) + "\n")
        print(f"\nUpdated {len(updates)} coord(s) in {COORDS_PATH.name}")
    elif updates:
        print(f"\nDRY-RUN: would update {len(updates)} coord(s)")

    if failures:
        print(f"\nFAIL: {len(failures)} slots un-probed: P{[s+1 for s in failures]}")
        return 1
    print("\nAll opponent pickers verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
