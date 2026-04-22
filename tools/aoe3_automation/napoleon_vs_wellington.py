#!/usr/bin/env python3
"""Set up Napoleon vs Wellington match, launch, and observe without intervening.

Flow:
1. Ensure main menu
2. Enter Skirmish setup
3. Select player 1 = Napoleonic France (picker idx 33)
4. Select player 2 (first AI) = British (picker idx 5) — base British AI auto-uses
   Wellington personality via aiLoaderStandard.xs dispatch
5. Click PLAY
6. Wait for in-game; screenshot every 3 minutes for 18 minutes total
7. Resign at end via standard keyboard flow
"""
from __future__ import annotations
import os, subprocess, time
from pathlib import Path
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
os.environ["GAMESCOPE_WAYLAND_DISPLAY"] = "gamescope-0"
os.environ["WAYLAND_DISPLAY"] = "gamescope-0"
XDO = {**os.environ, "DISPLAY": ":1"}

ART = Path("/tmp/aoe_test/napoleon_wellington")
ART.mkdir(parents=True, exist_ok=True)
LOG = ART / "run.log"


def log(msg):
    with LOG.open("a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def shot(path):
    for _ in range(4):
        try: Path(path).unlink()
        except FileNotFoundError: pass
        subprocess.run(["gamescopectl", "screenshot", path], timeout=20, capture_output=True)
        time.sleep(1.2)
        if Path(path).exists() and Path(path).stat().st_size > 100_000:
            try:
                with Image.open(path) as img: img.verify()
                return True
            except Exception: continue
    return False


def click(x, y):
    subprocess.run(["xdotool","mousemove",str(x),str(y)], env=XDO)
    time.sleep(0.2)
    subprocess.run(["xdotool","click","1"], env=XDO)


def press(key, n=1, delay=0.15):
    for _ in range(n):
        subprocess.run(["xdotool","key",key], env=XDO)
        time.sleep(delay)


def pixel_sum(path, x, y):
    p = Image.open(path).convert("RGB").getpixel((x,y))
    return p[0]+p[1]+p[2]


SKIRMISH_BTN = (80, 490)
P1_CIV_FLAG = (585, 176)
P2_CIV_FLAG = (585, 282)
PICKER_OK = (240, 976)
PLAY_BTN = (1646, 1030)


def select_civ_for_slot(flag_coord, idx):
    click(*flag_coord)
    time.sleep(1.8)
    press("Up", n=60, delay=0.03)
    time.sleep(0.4)
    press("Down", n=idx, delay=0.04)
    time.sleep(0.4)
    click(*PICKER_OK)
    time.sleep(2.5)


def ensure_main_menu():
    for _ in range(5):
        if shot(str(ART/"_probe.png")):
            # Crude check: center bright-ish + nav dark-wood
            c = pixel_sum(str(ART/"_probe.png"), 960, 540)
            nav = pixel_sum(str(ART/"_probe.png"), 80, 490)
            if c > 150 and nav < 300:
                return True
        press("Escape"); time.sleep(2)
    return False


def main():
    log("start")
    if not ensure_main_menu():
        log("FAIL: not on main menu"); return 1
    log("on main menu")

    # Enter Skirmish setup
    click(*SKIRMISH_BTN)
    time.sleep(3)
    shot(str(ART/"00_skirmish_setup.png"))

    # Player 1: Napoleonic France (idx 33)
    log("selecting P1 = Napoleonic France")
    select_civ_for_slot(P1_CIV_FLAG, 33)
    shot(str(ART/"01_p1_napoleon.png"))

    # Player 2 AI: British (idx 5)
    log("selecting P2 AI = British (Wellington profile)")
    select_civ_for_slot(P2_CIV_FLAG, 5)
    shot(str(ART/"02_p2_british.png"))

    # Start match
    log("clicking PLAY")
    click(*PLAY_BTN)
    time.sleep(5)

    # Wait for in-game
    for i in range(20):
        time.sleep(4)
        p = str(ART/"_wait.png")
        if shot(p) and pixel_sum(p, 200, 15) > 280:
            log(f"in-game reached after {(i+1)*4}s")
            break
    else:
        log("timeout waiting for in-game")
        return 2

    match_start = time.time()
    shot(str(ART/"t00_match_start.png"))
    log("match started; will observe without intervening for 18 minutes")

    # Screenshot every 3 min without touching input
    for minute in (3, 6, 9, 12, 15, 18):
        target = match_start + minute*60
        while time.time() < target:
            time.sleep(5)
        p = str(ART / f"t{minute:02d}_min.png")
        shot(p)
        log(f"captured t+{minute}m")

    log("18 minutes observed; initiating resign")

    # Resign via keyboard only
    press("Escape"); time.sleep(1.5)
    press("Down", n=5, delay=0.2)
    press("Return"); time.sleep(2)
    press("Left"); time.sleep(0.3)
    press("Return"); time.sleep(4)
    shot(str(ART/"t19_post_resign.png"))
    log("resigned; exiting to main menu")

    press("Escape"); time.sleep(1.5)
    press("Down", n=3, delay=0.2)
    press("Return"); time.sleep(3)
    shot(str(ART/"t20_main_menu.png"))

    log("done")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
