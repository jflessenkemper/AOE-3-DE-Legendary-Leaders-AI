#!/usr/bin/env python3
"""Full-coverage civ matrix driver.

For every civ in the Skirmish "Select Home City" picker (all ~48 including
base + mod + DLC), captures:
  1. setup_shot     — Skirmish setup screen with P1 slot showing the civ
  2. deck_builder   — Deck Builder view of the civ's current deck
  3. loading_shot   — Loading screen at t+3s post-Start (shows portrait/flags)
  4. in_game_shot   — Match view at first resource-bar-bright frame
  5. xs_error_flag  — pixel-based heuristic for XS error dialogs

Writes JSONL results + a post-run summary to /tmp/aoe_test/civ_matrix_full/.

Navigation primitives (gamescope+gamescopectl+DISPLAY=:1 xdotool) are the same
as civ_matrix_all.py. Picker navigation uses keyboard Down-arrow; for civs
past the visible-window limit the highlight scrolls automatically.

End-of-list detection: two consecutive civs with the same P1 slot hash = the
Down key has stopped advancing. Driver terminates with a clean end event.
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

ImageFile.LOAD_TRUNCATED_IMAGES = True

os.environ["GAMESCOPE_WAYLAND_DISPLAY"] = "gamescope-0"
os.environ["WAYLAND_DISPLAY"] = "gamescope-0"
XDO = {**os.environ, "DISPLAY": ":1"}

ART = Path("/tmp/aoe_test/civ_matrix_full")
ART.mkdir(parents=True, exist_ok=True)
for sub in ("setup", "deck_builder", "loading", "in_game", "errors"):
    (ART / sub).mkdir(exist_ok=True)
LOG = ART / "run.jsonl"

MAX_CIVS = 55  # safety upper bound; terminator is duplicate-civ detection


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
        time.sleep(1.0 + 0.5 * attempt)
        if Path(path).exists() and Path(path).stat().st_size > 100_000:
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
    """Better heuristic: require BOTH center-dark AND a bright text stripe
    consistent with the XS error title row (white text ~y=100 on dark bg)."""
    if pixel_sum(path, 960, 500) >= 90:
        return False
    # Check for title-band bright text in the error dialog region
    try:
        img = Image.open(path).convert("RGB")
        # Sample a horizontal strip at y=100 (top area of centered dialog)
        # If ANY of these sampled pixels are bright (text), it's an error dialog
        for x in range(700, 1200, 50):
            r, g, b = img.getpixel((x, 100))
            if r + g + b > 350:
                return True
    except Exception:
        pass
    return False


# Coordinates verified 2026-04-22
SKIRMISH_BTN = (80, 490)
P1_CIV_FLAG = (585, 176)
PICKER_OK = (240, 976)
PICKER_DECK_BUILDER = (336, 976)
PICKER_CANCEL = (784, 976)
PLAY_BTN = (1646, 1030)
ROI_P1_SLOT = (260, 130, 440, 100)


def is_main_menu(path):
    c = pixel_sum(path, 960, 540)
    if c < 180:
        return False
    nav = pixel_sum(path, 80, 490)
    return nav < 300


def is_setup_screen(path):
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
    for _ in range(max_attempts):
        click(*SKIRMISH_BTN)
        time.sleep(3)
        if shot(str(ART / "_probe.png")) and is_setup_screen(str(ART / "_probe.png")):
            return True
        time.sleep(1)
    return False


def open_picker_and_navigate(idx):
    """Open picker, press Up×60 (home) then Down×idx to highlight target."""
    click(*P1_CIV_FLAG)
    time.sleep(1.8)
    press("Up", n=60, delay=0.03)
    time.sleep(0.4)
    press("Down", n=idx, delay=0.04)
    time.sleep(0.4)


def confirm_picker_ok():
    click(*PICKER_OK)
    time.sleep(2.5)


def deck_builder_screenshot(idx):
    """From picker highlighted state, click Deck Builder, screenshot, back."""
    click(*PICKER_DECK_BUILDER)
    time.sleep(2.5)
    path = str(ART / "deck_builder" / f"idx_{idx:02d}_deck.png")
    shot(path)
    # Escape back to picker
    press("Escape")
    time.sleep(1.5)
    return path


def play_and_wait(idx, timeout_s=70):
    """Click PLAY. Capture loading screen (t+3s). Wait for in-game (top bar bright)."""
    click(*PLAY_BTN)
    log({"event": "play_clicked", "idx": idx})
    time.sleep(3)
    # Loading shot (t+3s)
    loading_path = str(ART / "loading" / f"idx_{idx:02d}_loading.png")
    shot(loading_path)
    # Continue waiting for in-game
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(4)
        p = str(ART / "_wait.png")
        if shot(p):
            if pixel_sum(p, 200, 15) > 280:
                return True, loading_path
    return False, loading_path


def resign_and_exit():
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

    # Step 1: open picker, navigate to civ
    open_picker_and_navigate(idx)

    # Step 2: capture deck builder BEFORE selecting
    try:
        deck_path = deck_builder_screenshot(idx)
        result["deck_builder_shot"] = deck_path
    except Exception as e:
        log({"event": "deck_builder_error", "idx": idx, "error": str(e)})

    # Step 3: re-navigate (Deck Builder escape returned us to picker, still highlighted)
    # Confirm with OK to close picker and apply civ selection
    confirm_picker_ok()

    # Step 4: setup screenshot
    setup_path = str(ART / "setup" / f"idx_{idx:02d}_setup.png")
    if not shot(setup_path):
        result["outcome"] = "shot_failed_after_select"
        log({"event": "civ_result", **result})
        return result, prior_slot_hash

    slot_h = roi_hash(setup_path, ROI_P1_SLOT)
    result["slot_hash"] = slot_h
    result["duplicate_of_prior"] = (slot_h == prior_slot_hash)
    if result["duplicate_of_prior"]:
        log({"event": "duplicate_civ_detected", "idx": idx, "hash": slot_h})
        result["outcome"] = "duplicate_skip"
        log({"event": "civ_result", **result})
        return result, slot_h

    # Step 5: PLAY + loading + in-game
    ok, loading_path = play_and_wait(idx)
    result["loading_shot"] = loading_path
    if not ok:
        result["outcome"] = "play_timeout"
        log({"event": "civ_result", **result})
        press("Escape"); time.sleep(2)
        return result, slot_h

    time.sleep(2)
    in_game_path = str(ART / "in_game" / f"idx_{idx:02d}_ingame.png")
    shot(in_game_path)
    result["in_game_shot"] = in_game_path
    try:
        result["xs_error"] = xs_error_dialog(in_game_path)
        if result["xs_error"]:
            import shutil as sh
            sh.copy(in_game_path, str(ART / "errors" / f"idx_{idx:02d}_xs_error.png"))
            log({"event": "XS_ERROR_DETECTED", "idx": idx})
    except Exception as e:
        log({"event": "xs_error_check_exception", "idx": idx, "error": str(e)})
        result["xs_error"] = None

    # Step 6: resign + exit
    try:
        resign_and_exit()
    except Exception as e:
        log({"event": "resign_exception", "idx": idx, "error": str(e)})

    result["outcome"] = "complete"
    log({"event": "civ_result", **result})
    return result, slot_h


def main():
    log({"event": "matrix_full_start"})
    if not ensure_main_menu():
        log({"event": "fatal_not_on_main_menu_at_start"})
        return 1

    prior_hash = ""
    consecutive_duplicates = 0
    consecutive_exceptions = 0

    # Resume support
    start_idx = 1
    for i, arg in enumerate(sys.argv):
        if arg == "--start-idx" and i + 1 < len(sys.argv):
            start_idx = int(sys.argv[i + 1])
    log({"event": "start_idx", "value": start_idx})

    for idx in range(start_idx, MAX_CIVS):
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
                    log({"event": "end_of_list_reached", "last_tested_idx": idx - 1})
                    break
                press("Escape"); time.sleep(2)
            else:
                consecutive_duplicates = 0
            consecutive_exceptions = 0
        except Exception as e:
            log({"event": "civ_exception", "idx": idx, "error": str(e)})
            consecutive_exceptions += 1
            if consecutive_exceptions >= 3:
                log({"event": "halt_too_many_consecutive_exceptions"})
                break

    log({"event": "matrix_full_end"})

    # Write summary
    summary = {"total_attempted": 0, "complete": 0, "duplicate_skip": 0,
               "play_timeout": 0, "shot_failed": 0, "xs_errors": 0,
               "civs": []}
    with LOG.open() as f:
        for line in f:
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("event") == "civ_result":
                summary["total_attempted"] += 1
                oc = e.get("outcome", "unknown")
                if oc in summary:
                    summary[oc] += 1
                else:
                    summary[oc] = summary.get(oc, 0) + 1
                if e.get("xs_error"):
                    summary["xs_errors"] += 1
                summary["civs"].append({k: e.get(k) for k in
                    ("idx", "slot_hash", "outcome", "xs_error", "duplicate_of_prior")})
    with (ART / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    log({"event": "summary_written", **{k: v for k, v in summary.items() if k != "civs"}})
    return 0


if __name__ == "__main__":
    sys.exit(main())
