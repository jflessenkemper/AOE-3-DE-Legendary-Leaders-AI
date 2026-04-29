#!/usr/bin/env python3
"""Full 48-civ matrix driver. Uses keyboard navigation for the civ picker so
we don't need per-civ row-click coordinates.

Per civ cycle:
1. Ensure at main menu
2. Click Skirmish (80, 490)
3. Click P1 civ flag (585, 176) to open picker
4. Press Up × 60 (force highlight to top = Random Personality, index 0)
5. Press Down × idx (move highlight to Nth civ)
6. Press Return (select + close picker)
7. Screenshot setup (captures P1 slot flag for gallery)
8. Click PLAY (1646, 1030); wait for in-game via top-bar brightness
9. Screenshot in-game; check XS error dialog pixel
10. Resign: Escape → Down×5 → Return → Left → Return
11. Exit: Escape → Down×3 → Return → back at main menu

Detects "past end of list" when the same civ is selected for two consecutive
indices (keyboard Down stopped advancing).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageFile

# Tolerate partially-written PNGs from gamescopectl (race between write + read)
ImageFile.LOAD_TRUNCATED_IMAGES = True

os.environ["GAMESCOPE_WAYLAND_DISPLAY"] = "gamescope-0"
os.environ["WAYLAND_DISPLAY"] = "gamescope-0"
XDO = {**os.environ, "DISPLAY": ":1"}

ART = Path("/tmp/aoe_test/civ_matrix_all")
ART.mkdir(parents=True, exist_ok=True)
for sub in ("setup", "in_game", "errors"):
    (ART / sub).mkdir(exist_ok=True)
LOG = ART / "run.jsonl"

MAX_CIVS = 60  # safety upper bound; terminator is duplicate-civ detection

# Indices known to hang or be DLC-locked. Skip and move on.
SKIP_INDICES = set()  # user owns all DLC  # 14 = Ethiopians (African Royals DLC not owned)


def log(e):
    e["t"] = time.time()
    with LOG.open("a") as f:
        f.write(json.dumps(e) + "\n")
    print(json.dumps(e), flush=True)


def shot(path, retries=3):
    for attempt in range(retries + 1):
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass
        subprocess.run(["gamescopectl", "screenshot", path],
                       timeout=20, capture_output=True)
        # Wait longer on each retry for the write to complete.
        time.sleep(1.0 + 0.5 * attempt)
        if Path(path).exists() and Path(path).stat().st_size > 100_000:
            # Verify it's a valid PNG
            try:
                with Image.open(path) as img:
                    img.verify()
                return True
            except Exception:
                continue
    return False


def click(x, y):
    subprocess.run(["xdotool", "mousemove", str(x), str(y)], env=XDO)
    time.sleep(0.2)
    subprocess.run(["xdotool", "click", "1"], env=XDO)


def press(key, n=1, delay=0.15):
    for _ in range(n):
        subprocess.run(["xdotool", "key", key], env=XDO)
        time.sleep(delay)


def pixel(path, x, y):
    img = Image.open(path).convert("RGB")
    return img.getpixel((x, y))


def pixel_sum(path, x, y):
    p = pixel(path, x, y)
    return p[0] + p[1] + p[2]


def roi_hash(path, region):
    img = Image.open(path).convert("RGB").crop(
        (region[0], region[1], region[0]+region[2], region[1]+region[3]))
    return hashlib.md5(img.tobytes()).hexdigest()[:16]


def xs_error_dialog(path):
    return pixel_sum(path, 960, 500) < 90


# Coordinates
SKIRMISH_BTN = (80, 490)
P1_CIV_FLAG = (585, 176)
PLAY_BTN = (1646, 1030)
ROI_P1_SLOT = (260, 130, 440, 100)   # player 1 row: flag + name


def is_main_menu(path):
    """Main menu has a bright center (sky/scene) but NOT the dark-wood setup
    background. Also not very dark (which would be loading/in-game transitions).
    Backdrops vary between launches so only the center-brightness criterion is
    used plus the left-nav-text check to distinguish from bright transitions."""
    c = pixel_sum(path, 960, 540)
    if c < 180:
        return False
    # Left-nav text area (~80, 490) has dark-wood brown when nav is present
    # (the menu-button background). Post-loading/in-game doesn't have this UI.
    # A dark-ish value here (< 200) suggests the nav panel is visible.
    nav = pixel_sum(path, 80, 490)
    return nav < 300  # dark wood brown of menu strip


def is_setup_screen(path):
    """Skirmish setup: dark wood center + top."""
    return pixel_sum(path, 960, 540) < 80


def ensure_main_menu(max_attempts=5):
    for i in range(max_attempts):
        if not shot(str(ART / "_probe.png")):
            time.sleep(2)
            continue
        try:
            if is_main_menu(str(ART / "_probe.png")):
                return True
        except Exception as e:
            log({"event": "is_main_menu_exception", "error": str(e)})
        press("Escape")
        time.sleep(2)
    return False


def enter_skirmish_setup(max_attempts=3):
    for i in range(max_attempts):
        click(*SKIRMISH_BTN)
        time.sleep(3)
        if shot(str(ART / "_probe.png")) and is_setup_screen(str(ART / "_probe.png")):
            return True
        # Try next nearby y
        time.sleep(1)
    return False


PICKER_OK = (240, 976)


def select_civ_by_keyboard(idx):
    """Open picker, press Up×60 (home) then Down×idx (highlight target), then
    click OK button. Return-key doesn't confirm in this picker; OK click does."""
    click(*P1_CIV_FLAG)
    time.sleep(1.8)
    press("Up", n=60, delay=0.03)
    time.sleep(0.4)
    press("Down", n=idx, delay=0.04)
    time.sleep(0.4)
    click(*PICKER_OK)
    time.sleep(2.5)


def play_and_wait(timeout_s=80):
    click(*PLAY_BTN)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(4)
        p = str(ART / "_wait.png")
        if shot(p):
            if pixel_sum(p, 200, 15) > 280:  # resource bar bright = in-game
                return True
    return False


def resign_and_exit():
    """Escape → Down×5 + Return (Resign) → Left+Return (Yes) →
       Escape → Down×3 + Return (Quit back to main menu)."""
    press("Escape")
    time.sleep(1.5)
    press("Down", n=5, delay=0.2)
    press("Return")
    time.sleep(2)
    press("Left")
    time.sleep(0.3)
    press("Return")
    time.sleep(4)
    press("Escape")
    time.sleep(1.5)
    press("Down", n=3, delay=0.2)
    press("Return")
    time.sleep(3)


def run_one(idx, prior_slot_hash):
    log({"event": "civ_start", "idx": idx})
    result = {"idx": idx}

    select_civ_by_keyboard(idx)

    # Screenshot setup; capture the P1 slot to both confirm a NEW civ got
    # selected vs prior and to preserve the flag + civ name row for the gallery.
    setup_path = str(ART / "setup" / f"idx_{idx:02d}_setup.png")
    if not shot(setup_path):
        result["outcome"] = "shot_failed_after_select"
        log({"event": "civ_result", **result})
        return result, prior_slot_hash

    slot_h = roi_hash(setup_path, ROI_P1_SLOT)
    result["slot_hash"] = slot_h
    result["duplicate_of_prior"] = (slot_h == prior_slot_hash)

    if result["duplicate_of_prior"]:
        log({"event": "civ_duplicate_detected", "idx": idx,
             "hash": slot_h, "note": "list may have ended"})
        result["outcome"] = "duplicate_skip"
        log({"event": "civ_result", **result})
        return result, slot_h

    if not play_and_wait():
        result["outcome"] = "play_timeout"
        log({"event": "civ_result", **result})
        # best-effort: Escape + exit to main menu
        press("Escape"); time.sleep(2)
        return result, slot_h

    # In-game. Screenshot for verification.
    time.sleep(2)
    in_game_path = str(ART / "in_game" / f"idx_{idx:02d}_ingame.png")
    shot(in_game_path)
    result["in_game_shot"] = in_game_path
    result["xs_error"] = xs_error_dialog(in_game_path)
    if result["xs_error"]:
        import shutil as sh
        sh.copy(in_game_path, str(ART / "errors" / f"idx_{idx:02d}_xs_error.png"))
        log({"event": "XS_ERROR_DETECTED", "idx": idx})

    resign_and_exit()

    result["outcome"] = "complete"
    log({"event": "civ_result", **result})
    return result, slot_h


def main():
    log({"event": "matrix_all_start"})

    if not ensure_main_menu():
        log({"event": "fatal_not_on_main_menu_at_start"})
        return 1

    prior_hash = ""
    consecutive_duplicates = 0
    consecutive_shot_failures = 0

    # Parse optional --start-idx argument (for resumes)
    start_idx = 1
    for i, arg in enumerate(sys.argv):
        if arg == "--start-idx" and i + 1 < len(sys.argv):
            start_idx = int(sys.argv[i + 1])

    log({"event": "start_idx", "value": start_idx})
    # idx=0 is "Random Personality" — we skip it (not a testable civ per se)
    for idx in range(start_idx, MAX_CIVS):
        if idx in SKIP_INDICES:
            log({"event": "civ_skipped", "idx": idx, "reason": "in SKIP_INDICES (DLC-locked or known hang)"})
            continue
        try:
            if not ensure_main_menu():
                log({"event": "cant_recover_main_menu", "idx": idx})
                break
            if not enter_skirmish_setup():
                log({"event": "cant_enter_skirmish_setup", "idx": idx})
                continue
            result, prior_hash = run_one(idx, prior_hash)
            if result["outcome"] == "duplicate_skip":
                consecutive_duplicates += 1
                if consecutive_duplicates >= 2:
                    log({"event": "end_of_list_reached", "last_idx": idx})
                    break
                # Try to exit setup screen
                press("Escape"); time.sleep(2)
            else:
                consecutive_duplicates = 0
        except Exception as e:
            log({"event": "civ_exception", "idx": idx, "error": str(e)})
            consecutive_shot_failures += 1
            if consecutive_shot_failures >= 3:
                log({"event": "consecutive_shot_failures_halting",
                     "last_idx": idx,
                     "note": "gamescopectl screenshot pipeline needs reset; restart game"})
                break
        else:
            consecutive_shot_failures = 0

    log({"event": "matrix_all_end"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
