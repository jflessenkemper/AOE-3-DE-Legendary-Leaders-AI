"""Pixel-coord-driven Skirmish-lobby driver for AoE3 DE under gamescope.

Fully deterministic — no OCR, no template matching. Click coords are baked
into lobby_coords.json (empirically measured 2026-04-28). State transitions
are verified by ImageMagick AE pixel-diff against reference screenshots.

Run from gamescope-host context:
    flatpak-spawn --host python3 tools/aoe3_automation/lobby_driver.py --select-civ aztecs

The driver assumes the game is already at the Skirmish lobby (default
state). Use manage_game.py / launch_retest_mod.sh to get there first.

Why not pyautogui? Because pyautogui talks to the host X server, but our
display is gamescope's nested Xwayland on :1. Use xdotool with explicit
DISPLAY=:1 instead. Why not template matching? OCR/template matching
proved unreliable on AoE3 DE's Trajan-style caps over textured wood.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
COORDS_PATH = Path(__file__).parent / "lobby_coords.json"
RAW_DIR = Path(__file__).parent / "templates" / "matrix" / "_raw"
CLEAN_LOBBY_REF = RAW_DIR / "05_skirmish_lobby.png"
ARTIFACT_DIR = Path(__file__).parent / "artifacts" / "lobby_driver"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# 0-indexed civ row in the picker. Pulled from civ_picker_v2.png:
# (Random Personality at index 0, alphabetical thereafter).
# This is the OBSERVED order — rebuild from a fresh picker capture if
# the game updates and reorders.
CIV_ORDER = [
    "Random Personality",     # 0
    "American Republic",      # 1   (United States)
    "Argentines",             # 2   (Argentina)
    "Aztecs",                 # 3   (Aztec Empire)
    "Baja Californians",      # 4   (Baja California)
    "Barbary",                # 5   (Barbary States)
    "Brazilians",             # 6   (Brazil)
    "British",                # 7   (Britain)
    "Californians",           # 8   (California)
    "Canadians",              # 9   (Canada)
    # rows 10..47 still need to be confirmed by scrolling — use --map-civs
]


def load_coords() -> dict:
    return json.loads(COORDS_PATH.read_text())


def sh(cmd: str, *, check: bool = True) -> str:
    """Run a host command via flatpak-spawn if we're inside the Flatpak."""
    if Path("/.flatpak-info").exists():
        cmd = f"flatpak-spawn --host bash -lc {json.dumps(cmd)}"
    out = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
    )
    if check and out.returncode != 0:
        raise RuntimeError(
            f"command failed (rc={out.returncode}):\n  cmd: {cmd}\n  stderr: {out.stderr}"
        )
    return out.stdout


def xdo(cmd: str) -> None:
    """Run an xdotool command against gamescope's :1 display."""
    sh(f"DISPLAY=:1 xdotool {cmd}")


def screenshot(out_path: Path, *, retries: int = 5) -> Path:
    """gamescopectl screenshot, with retry — first call after a click is flaky."""
    out_path.unlink(missing_ok=True)
    for i in range(retries):
        sh(f"DISPLAY=:1 gamescopectl screenshot {out_path}", check=False)
        time.sleep(0.4)
        if out_path.exists() and out_path.stat().st_size > 0:
            return out_path
    raise RuntimeError(f"screenshot failed after {retries} retries: {out_path}")


def diff_pixels(a: Path, b: Path) -> int:
    """Total absolute-error pixel count between two images.

    Uses 'magick compare -metric AE'. Output format is '<sum-sq> (<n_pixels>)';
    we want the n_pixels in parens (the raw number of differing pixels).
    """
    out = sh(
        f"magick compare -metric AE {a} {b} null: 2>&1 || true",
        check=False,
    )
    m = re.search(r"\(([0-9.eE+-]+)\)", out)
    if m:
        return int(float(m.group(1)))
    nums = re.findall(r"[0-9.eE+-]+", out)
    return int(float(nums[0])) if nums else 0


def click(x: int, y: int, *, settle: float = 0.2) -> None:
    xdo(f"mousemove {x} {y}")
    time.sleep(settle)
    xdo("click 1")


def move_mouse_off(x: int = 100, y: int = 500) -> None:
    """Park the cursor somewhere harmless to avoid hover-tooltip artifacts."""
    xdo(f"mousemove {x} {y}")
    time.sleep(0.2)


def scroll_down(coords: dict, n: int = 1) -> None:
    sa = coords["civ_picker"]["scroll_anchor"]
    xdo(f"mousemove {sa[0]} {sa[1]}")
    time.sleep(0.2)
    for _ in range(n):
        xdo("click 5")  # button 5 = wheel-down
        time.sleep(0.15)


# ---- state checks ---------------------------------------------------------


def is_clean_lobby(coords: dict) -> bool:
    p = ARTIFACT_DIR / "_state.png"
    screenshot(p)
    d = diff_pixels(CLEAN_LOBBY_REF, p)
    return d <= coords["diff_thresholds"]["noise_floor"]


def is_picker_open(coords: dict) -> bool:
    """Picker open means the screen differs significantly from clean lobby."""
    p = ARTIFACT_DIR / "_state.png"
    screenshot(p)
    d = diff_pixels(CLEAN_LOBBY_REF, p)
    return d >= coords["diff_thresholds"]["significant_change"]


# ---- high-level operations ------------------------------------------------


def open_civ_picker(coords: dict, *, attempts: int = 3) -> None:
    cx, cy = coords["lobby"]["p1_civ_picker"]
    for i in range(attempts):
        click(cx, cy)
        time.sleep(1.4)
        if is_picker_open(coords):
            return
        print(f"  open_civ_picker: attempt {i+1} did not open picker, retrying")
    raise RuntimeError("Failed to open civ picker")


def cancel_civ_picker(coords: dict) -> None:
    cx, cy = coords["civ_picker"]["cancel_button"]
    click(cx, cy)
    time.sleep(0.9)
    move_mouse_off()


def select_civ_in_picker(coords: dict, civ_index: int) -> None:
    """With picker open + list scrolled to top, click row at civ_index.

    For civ_index < row_count_visible: click directly at row Y.
    For civ_index >= row_count_visible: scroll down (civ_index - last_visible_row)
    times to bring target row to the bottom of the visible window, then click
    the bottom-row Y. Each wheel-down click scrolls exactly 1 row in this
    AoE3 DE build (verified empirically 2026-04-28).
    """
    cp = coords["civ_picker"]
    if civ_index < 0:
        raise ValueError(f"civ_index must be >= 0, got {civ_index}")
    last_visible = cp["row_count_visible"] - 1  # 9
    if civ_index <= last_visible:
        target_row_y = cp["row_y_start"] + civ_index * cp["row_spacing"]
    else:
        # Scroll so that civ_index lands at the bottom (row last_visible)
        scrolls_needed = civ_index - last_visible
        scroll_down(coords, n=scrolls_needed)
        target_row_y = cp["row_y_start"] + last_visible * cp["row_spacing"]
    click(cp["row_x_center"], target_row_y, settle=0.3)
    time.sleep(0.5)


def confirm_civ_selection(coords: dict) -> None:
    ok = coords["civ_picker"]["ok_button"]
    click(*ok, settle=0.3)
    time.sleep(1.5)
    move_mouse_off()


def set_civ_by_index(coords: dict, civ_index: int) -> None:
    """End-to-end: open picker → click row → click OK → mouse-off."""
    open_civ_picker(coords)
    select_civ_in_picker(coords, civ_index)
    confirm_civ_selection(coords)


def reset_p1_to_random(coords: dict) -> None:
    set_civ_by_index(coords, 0)


def click_play(coords: dict) -> None:
    px, py = coords["lobby"]["play_button"]
    click(px, py, settle=0.3)


# ---- entrypoints ----------------------------------------------------------


def cmd_check_state(coords: dict) -> int:
    p = ARTIFACT_DIR / "_state.png"
    screenshot(p)
    d = diff_pixels(CLEAN_LOBBY_REF, p)
    nf = coords["diff_thresholds"]["noise_floor"]
    sig = coords["diff_thresholds"]["significant_change"]
    if d <= nf:
        state = "clean_lobby"
    elif d >= sig:
        state = "picker_or_dropdown_open"
    else:
        state = "uncertain (transient/tooltip?)"
    print(f"diff vs clean lobby: {d} pixels  → {state}")
    print(f"snapshot: {p}")
    return 0


def cmd_select_civ(coords: dict, name: str) -> int:
    norm = name.strip().lower()
    matches = [i for i, c in enumerate(CIV_ORDER) if c.lower() == norm]
    if not matches:
        # also accept startswith
        matches = [i for i, c in enumerate(CIV_ORDER) if c.lower().startswith(norm)]
    if not matches:
        print(f"Unknown civ: {name!r}. Known: {CIV_ORDER}")
        return 2
    idx = matches[0]
    print(f"Selecting civ #{idx}: {CIV_ORDER[idx]}")
    set_civ_by_index(coords, idx)
    print("Done. Capturing post-selection state…")
    p = ARTIFACT_DIR / f"after_select_{CIV_ORDER[idx].replace(' ', '_')}.png"
    screenshot(p)
    print(f"saved: {p}")
    return 0


def cmd_reset(coords: dict) -> int:
    print("Resetting P1 to Random Personality…")
    reset_p1_to_random(coords)
    print("Done.")
    return 0


def cmd_play(coords: dict) -> int:
    if not is_clean_lobby(coords):
        print("WARN: not at clean lobby — refusing to click PLAY")
        return 1
    print("Clicking PLAY…")
    click_play(coords)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-state", action="store_true",
                    help="Diff current screen vs clean-lobby reference")
    ap.add_argument("--select-civ", metavar="NAME",
                    help="Open picker and select civ by name (first 10 only without scroll)")
    ap.add_argument("--reset", action="store_true",
                    help="Reset P1 to Random Personality")
    ap.add_argument("--play", action="store_true",
                    help="Click PLAY (requires clean-lobby state)")
    args = ap.parse_args()

    coords = load_coords()

    if args.check_state:
        return cmd_check_state(coords)
    if args.reset:
        return cmd_reset(coords)
    if args.select_civ:
        return cmd_select_civ(coords, args.select_civ)
    if args.play:
        return cmd_play(coords)

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
