#!/usr/bin/env python3
"""1v1 Deathmatch — Napoleonic France (me, idle) vs British (Wellington AI).

After match starts:
- Open chat (Enter)
- Type "x marks the spot" (map reveal cheat)
- Enter to send
- Wait + screenshot overview (whole revealed map)
- Observe every 2 min for 20 min
- Resign + exit

Deathmatch start = Post-Imperial Age + max resources by default.
"""
from __future__ import annotations
import os, subprocess, time
from pathlib import Path
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
os.environ["GAMESCOPE_WAYLAND_DISPLAY"] = "gamescope-0"
os.environ["WAYLAND_DISPLAY"] = "gamescope-0"
XDO = {**os.environ, "DISPLAY": ":1"}

ART = Path("/tmp/aoe_test/np_wel_deathmatch")
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
        subprocess.run(["gamescopectl","screenshot",path], timeout=20, capture_output=True)
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


def type_text(text):
    """Type a literal string via xdotool."""
    subprocess.run(["xdotool","type","--delay","30",text], env=XDO)


def pixel_sum(path, x, y):
    p = Image.open(path).convert("RGB").getpixel((x,y))
    return p[0]+p[1]+p[2]


SKIRMISH_BTN = (80, 490)
PLAYER_COUNT_BTN = (1800, 25)   # "4 PLAYERS" dropdown top-right
P1_CIV_FLAG = (585, 176)
P2_CIV_FLAG = (585, 282)
PICKER_OK = (240, 976)
PLAY_BTN = (1646, 1030)


def select_civ_for_slot(flag_coord, idx):
    click(*flag_coord); time.sleep(1.8)
    press("Up", n=60, delay=0.03); time.sleep(0.4)
    press("Down", n=idx, delay=0.04); time.sleep(0.4)
    click(*PICKER_OK); time.sleep(2.5)


def set_player_count_to_2():
    """Click the '4 PLAYERS' dropdown, pick 2 PLAYERS if the dropdown opens.
    AoE3 DE uses a dropdown — top option is usually 2. We'll click dropdown,
    then click the first entry below.
    """
    click(*PLAYER_COUNT_BTN); time.sleep(1.0)
    # Dropdown entries appear below. First entry "2 Players" should be at
    # ~(PLAYER_COUNT_BTN x, PLAYER_COUNT_BTN y + 40).
    click(PLAYER_COUNT_BTN[0], PLAYER_COUNT_BTN[1] + 40)
    time.sleep(1.5)


def ensure_main_menu():
    for _ in range(5):
        if shot(str(ART/"_probe.png")):
            c = pixel_sum(str(ART/"_probe.png"), 960, 540)
            nav = pixel_sum(str(ART/"_probe.png"), 80, 490)
            if c > 150 and nav < 300:
                return True
        press("Escape"); time.sleep(2)
    return False


def main():
    log("start")
    if not ensure_main_menu():
        log("FAIL not main menu"); return 1
    log("main menu confirmed")

    click(*SKIRMISH_BTN); time.sleep(3)
    shot(str(ART/"00_skirmish_setup.png"))

    # Reduce to 2 players (1v1)
    log("setting player count to 2")
    set_player_count_to_2()
    shot(str(ART/"01_two_players.png"))

    # P1 = Napoleonic France (idx 33)
    log("P1 = Napoleonic France")
    select_civ_for_slot(P1_CIV_FLAG, 33)

    # P2 AI = British (idx 5)
    log("P2 AI = British (Wellington via leader_wellington.xs)")
    select_civ_for_slot(P2_CIV_FLAG, 5)
    shot(str(ART/"02_ready_to_play.png"))

    # Start (Deathmatch + Post-Imperial defaults preserved from prior session)
    log("clicking PLAY")
    click(*PLAY_BTN)
    time.sleep(5)

    # Wait in-game
    for i in range(25):
        time.sleep(4)
        p = str(ART/"_wait.png")
        if shot(p) and pixel_sum(p, 200, 15) > 280:
            log(f"in-game at {(i+1)*4}s")
            break
    else:
        log("timeout waiting for in-game"); return 2

    match_start = time.time()
    shot(str(ART/"t00_in_game.png"))

    # Map-reveal cheat: Enter → "x marks the spot" → Enter
    log("applying map-reveal cheat")
    time.sleep(3)  # let initial UI settle
    press("Return"); time.sleep(0.8)  # opens chat input
    type_text("x marks the spot")
    time.sleep(0.5)
    press("Return"); time.sleep(2.0)  # submits cheat

    shot(str(ART/"t01_after_cheat.png"))

    # Zoom out via mouse-wheel up repeatedly (scroll-wheel button 4)
    log("zooming out for map overview")
    for _ in range(25):
        subprocess.run(["xdotool","click","4"], env=XDO)
        time.sleep(0.08)
    time.sleep(1.5)
    shot(str(ART/"t02_zoomed_out.png"))

    # Also pan camera to center by pressing Home key (centers on town center)
    press("Home"); time.sleep(1.5)
    shot(str(ART/"t03_centered.png"))

    # Observe every 2 min for 20 min
    for minute in (2, 4, 6, 8, 10, 12, 14, 16, 18, 20):
        target = match_start + minute * 60
        while time.time() < target:
            time.sleep(5)
        p = str(ART / f"t{minute:02d}_min.png")
        shot(p)
        log(f"captured t+{minute}m")

    log("20 min observed; resigning")
    press("Escape"); time.sleep(1.5)
    press("Down", n=5, delay=0.2); press("Return"); time.sleep(2)
    press("Left"); time.sleep(0.3); press("Return"); time.sleep(4)
    shot(str(ART/"t21_post_resign.png"))

    press("Escape"); time.sleep(1.5)
    press("Down", n=3, delay=0.2); press("Return"); time.sleep(3)
    shot(str(ART/"t22_main_menu.png"))

    log("done")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
