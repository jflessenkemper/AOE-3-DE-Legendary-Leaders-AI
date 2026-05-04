#!/usr/bin/env python3
"""Final civ-matrix driver. Full cycle per civ:

1. Main menu → Skirmish button (80, 490)
2. Setup → click P1_CIV_FLAG to open picker
3. Click civ row by alphabetical idx (Y = 294 + idx*60 within picker list)
4. Click picker OK (240, 976)
5. Click PLAY button (1646, 1030)
6. Wait up to 60s for in-game
7. Screenshot loading (t≈15s) and in-game (t≈45s)
8. Escape (pause) → 5 Down + Return (Resign) → Left + Return (Yes)
9. Post-match → Escape → 3 Down + Return (Quit) → back at main menu
10. Loop to next civ

Expects game running in gamescope. Input via xdotool DISPLAY=:1.
Screenshot via gamescopectl.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from PIL import Image

os.environ["GAMESCOPE_WAYLAND_DISPLAY"] = "gamescope-0"
os.environ["WAYLAND_DISPLAY"] = "gamescope-0"
XDO = {**os.environ, "DISPLAY": ":1"}

ART = Path("/tmp/aoe_test/civ_final")
ART.mkdir(parents=True, exist_ok=True)
(ART / "loading").mkdir(exist_ok=True)
(ART / "in_game").mkdir(exist_ok=True)
(ART / "errors").mkdir(exist_ok=True)
LOG = ART / "run.jsonl"


def log(e):
    e["t"] = time.time()
    with LOG.open("a") as f:
        f.write(json.dumps(e) + "\n")
    print(json.dumps(e), flush=True)


def shot(path):
    subprocess.run(["gamescopectl", "screenshot", path],
                   timeout=15, capture_output=True)
    time.sleep(0.6)
    return Path(path).exists() and Path(path).stat().st_size > 1024


def click(x, y):
    subprocess.run(["xdotool", "mousemove", str(x), str(y)], env=XDO)
    time.sleep(0.2)
    subprocess.run(["xdotool", "click", "1"], env=XDO)


def press(key, n=1, delay=0.2):
    for _ in range(n):
        subprocess.run(["xdotool", "key", key], env=XDO)
        time.sleep(delay)


def center_sum(path):
    img = Image.open(path).convert("RGB")
    p = img.getpixel((960, 540))
    return p[0] + p[1] + p[2]


def top_sum(path):
    """Brightness at (200, 15) = resource-bar area (bright when in-game)."""
    img = Image.open(path).convert("RGB")
    p = img.getpixel((200, 15))
    return p[0] + p[1] + p[2]


def xs_error_dialog(path):
    img = Image.open(path).convert("RGB")
    p = img.getpixel((960, 500))
    return p[0] + p[1] + p[2] < 90


# Coordinates — verified in 2026-04-22 session
SKIRMISH_BTN = (80, 490)
P1_CIV_FLAG = (585, 176)
PICKER_OK = (240, 976)
PICKER_ROW_X = 500
PICKER_Y0 = 294              # Random Personality (idx 0)
PICKER_ROW_DY = 60
PLAY_BTN = (1646, 1030)

# Alphabetical indices in the Select Home City picker, hand-identified from
# the picker screenshot (includes both base and mod civs). Only indices with
# verified positions; scroll-requiring entries commented out for now.
TARGETS = [
    ("argentines",        1),
    ("barbary_states",    3),  # note: Baja Californians might bump this to 4
    ("brazilians",        4),
    ("central_americans", 8),
    ("chileans",          9),
    # For deeper indices we'd need picker scroll — leave as future work.
]


def ensure_main_menu():
    """Try to get to main menu from whatever state. Best-effort."""
    for _ in range(3):
        shot(str(ART / "_state.png"))
        s = center_sum(str(ART / "_state.png"))
        # main menu has bright center (tan sky ~200+)
        if 180 < s < 500:
            return True
        press("Escape")
        time.sleep(2)
    return False


def enter_skirmish_setup():
    click(*SKIRMISH_BTN)
    time.sleep(3)


def select_civ(idx):
    """Open picker, click idx-th row, OK."""
    click(*P1_CIV_FLAG)
    time.sleep(2)
    y = PICKER_Y0 + idx * PICKER_ROW_DY
    click(PICKER_ROW_X, y)
    time.sleep(0.8)
    click(*PICKER_OK)
    time.sleep(2.5)


def play_and_wait():
    click(*PLAY_BTN)
    log({"event": "play_clicked"})
    # Wait up to 70s for in-game (top bar gets bright)
    for i in range(18):
        time.sleep(4)
        p = str(ART / "_loading.png")
        shot(p)
        top = top_sum(p)
        if top > 280:
            return True
    return False


def resign():
    """Escape → pause → 5 Down + Return → Resign dialog → Left + Return → yes."""
    press("Escape")
    time.sleep(1.5)
    press("Down", n=5, delay=0.2)
    press("Return")
    time.sleep(2)
    # Resign confirmation dialog — YES is left button
    press("Left")
    time.sleep(0.3)
    press("Return")
    time.sleep(3.5)


def exit_to_main():
    """Post-match → Escape → 3 Down + Return (Quit) → main menu."""
    press("Escape")
    time.sleep(1.5)
    press("Down", n=3, delay=0.2)
    press("Return")
    time.sleep(3)


def run_civ(civ_tag, idx):
    log({"event": "civ_start", "civ": civ_tag, "idx": idx})
    result = {"civ": civ_tag, "idx": idx}

    # Select civ + play
    select_civ(idx)
    shot(str(ART / f"{civ_tag}_setup.png"))

    if not play_and_wait():
        result["outcome"] = "play_didnt_register"
        log({"event": "civ_result", **result})
        return result

    # In-game. Screenshot.
    time.sleep(2)
    in_game_path = str(ART / "in_game" / f"{civ_tag}_t{int(time.time())%100}.png")
    shot(in_game_path)
    result["in_game_shot"] = in_game_path
    result["xs_error"] = xs_error_dialog(in_game_path)
    if result["xs_error"]:
        import shutil as sh
        sh.copy(in_game_path, str(ART / "errors" / f"{civ_tag}_xs_error.png"))
        log({"event": "XS_ERROR_DETECTED", "civ": civ_tag})

    # Resign + exit
    resign()
    exit_to_main()

    result["outcome"] = "complete"
    log({"event": "civ_result", **result})
    return result


def main():
    log({"event": "final_driver_start"})
    # We expect to be on main menu.
    if not ensure_main_menu():
        log({"event": "fatal_not_on_main_menu"})
        return 1

    for civ_tag, idx in TARGETS:
        try:
            enter_skirmish_setup()
            run_civ(civ_tag, idx)
        except Exception as e:
            log({"event": "civ_exception", "civ": civ_tag, "error": str(e)})
        # Ensure we end iteration on main menu
        if not ensure_main_menu():
            log({"event": "cant_return_to_main_menu"})
            break

    log({"event": "final_driver_end"})
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
