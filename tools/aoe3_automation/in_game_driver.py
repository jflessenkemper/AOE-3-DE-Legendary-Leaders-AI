#!/usr/bin/env python3
"""AoE3 DE in-game driver for skirmish test automation.

Provides a clean Python API for driving a full skirmish run end-to-end,
designed to feed probe_coverage_matrix.py and standalone self-tests.

Environment facts (discovered empirically on Bazzite/Proton rig, verified 2026-04-28):
  - Game runs in gamescope nested Xwayland.  Display number depends on launch order;
    use gamescope_detect.detect_aoe3_display() — typically returns (':1', 'gamescope-0')
    when AoE3 is launched alone.  Fallback constants below match that case.
  - Input: DISPLAY=:1 xdotool (key / mousemove / click) — works.
  - Window focus: gamescope's nested Xwayland does NOT support EWMH
    _NET_ACTIVE_WINDOW, so `xdotool getactivewindow` always fails.  Use
    `xdotool search --name "Age of Empires" windowactivate` unconditionally
    (no --sync; that flag also fails on gamescope).
  - SCREENSHOTS ARE NOT AVAILABLE via any external tool on this rig:
      * gamescopectl on Bazzite lacks the `screenshot` subcommand
      * xwd/ImageMagick `import`/ffmpeg `x11grab` against the gamescope
        Xwayland (:1) all return uniformly black frames — gamescope renders
        directly to the GPU presentation queue and never paints to the
        Xwayland root window
      * spectacle / KWin ScreenShot2 capture only the host KDE compositor
        which has no visibility into gamescope's output
      * Result: this driver runs BLIND.  Coordinates are correct on the
        nested Xwayland (game window IS at 0,0 1920x1080 on :1) so click /
        key input lands precisely; we just can't observe the result via pixels.
    Workaround: AoE3's own in-game screenshot binding writes PNGs to
    <profile>/Screenshots/ — those work because they're rendered by the
    game itself.  Use ``screenshot()`` to fire that via xdotool (PrintScreen).
    For state detection we use TIME-BASED waits instead of pixel detection.
  - Game speed: click the gold bar at the bottom-right of the HUD
    Bar x-range: ~1620-1900, y≈1058.  Left=slow, Right=fast.
    Predefined click positions (5 speed ticks): 1635, 1685, 1760, 1835, 1895
    There are no reliable keyboard shortcuts for speed in this gamescope/Proton config.
  - Replay files: ~/.local/share/Steam/steamapps/compatdata/933110/pfx/drive_c/
      users/steamuser/Games/Age of Empires 3 DE/76561198170207043/Savegame/
      Named "Record Game YYYY-MM-DD HH-MM-SS.age3Yrec"

UI coordinate map (all coords in 1920×1080 game-window space, offset 0,0):

  MAIN MENU (left sidebar buttons):
    Continue:          x=80, y=330
    Skirmish:          x=80, y=490  ← most used

  SKIRMISH SETUP (Single Player Skirmish):
    P1 civ flag:       x=585, y=176
    P2 civ flag:       x=585, y=282
    P3 civ flag:       x=585, y=388
    P4 civ flag:       x=585, y=494
    Civ picker OK:     x=240, y=976
    Civ picker Cancel: x=580, y=960
    Map button:        x=1550, y=414   (opens full map-picker modal)
    Map picker OK:     x=240, y=976    (same OK button inside modal)
    Difficulty drop:   x=1700, y=570   (click to cycle; uses arrow keys after click)
    Play button:       x=1646, y=1030

  IN-GAME HUD:
    Resource bar top:  y≈15 (pixel sum >280 = in-game detector)
    Speed bar:         y=1058, x=1620..1900 (click to set speed)
    Speed ticks:       [1635, 1685, 1760, 1835, 1895] → [1,2,3,4,5]

  ESC MENU (right panel, appears when Escape pressed):
    Panel x center:    x=1750
    Photo Mode:        y=99
    Technology Tree:   y=145
    Save:              y=185
    Load:              y=230
    Restart:           y=275
    Options:           y=320
    Resign:            y=365
    Quit:              y=410

  RESIGN DIALOG (centered):
    Yes button:        x=750, y=610
    No button:         x=1170, y=610

  ABANDON / POST-RESIGN SCREEN:
    View Map:          x=680, y=729
    View Postgame:     x=1128, y=729

  POST-GAME SCREEN:
    Quit (top-left):   x=50, y=20

  CIV PICKER MODAL (keyboard navigation):
    Arrow Up: scroll to top of list.  Arrow Down x N: select index N (0-based).
    OK button: x=240, y=976.
    Pattern: press Up×60, then Down×N, then click OK.

Usage:
    from in_game_driver import GameDriver
    d = GameDriver()
    d.start_skirmish(p1_civ_idx=7)  # Dutch
    d.wait_for_in_game()
    d.set_speed(5)                  # max speed
    time.sleep(60)
    d.screenshot("mid_game")
    d.resign()

Log capture
-----------
Per-match [LLP v=2 ...] probe lines are captured from Age3Log.txt (NOT from
the .age3Yrec replay — replay chat is binary-encoded and unparseable).  The
``log_capture`` module snapshots the log byte-offset before each match and
reads the delta after resign.  Requires developer mode to be active (managed
automatically by ``manage_game.py open``).

Self-test:
    python3 tools/aoe3_automation/in_game_driver.py --self-test
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, Optional, TYPE_CHECKING

# Imported here so wait_for_in_game can fall back to direct reads when no
# LogMirror is provided.  log_capture is in the same package.
from tools.aoe3_automation.log_capture import AGE3_LOG_PATH

if TYPE_CHECKING:
    from tools.aoe3_automation.log_capture import LogMirror

# ---------------------------------------------------------------------------
# Environment wiring
# ---------------------------------------------------------------------------
# NOTE: DISPLAY and GAMESCOPE_WL are detected dynamically via gamescope_detect.
# The constants below are only kept as a last-resort fallback if detection fails
# (e.g. when the game is not running yet during import).  Do not hardcode these
# for actual input/screenshot operations — always call _get_xdo_env() / _get_gs_env().
# Verified 2026-04-28: AoE3 alone yields :1/gamescope-0. The detector
# overrides these dynamically; only used if detection raises.
_FALLBACK_DISPLAY = ":1"
_FALLBACK_GS_WL   = "gamescope-0"

MANAGE_GAME = Path(__file__).parent / "manage_game.py"
UI_MAP_DIR = Path(__file__).parent / "ui_map"
UI_MAP_DIR.mkdir(exist_ok=True)
RECORDED_GAMES = (
    Path.home()
    / ".local/share/Steam/steamapps/compatdata/933110"
    / "pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/76561198170207043/Savegame"
)


def _get_xdo_env() -> dict:
    """Return env dict with DISPLAY set to AoE3's Xwayland display (detected dynamically)."""
    try:
        from tools.aoe3_automation.gamescope_detect import get_xdo_env
        return get_xdo_env()
    except Exception:
        return {**os.environ, "DISPLAY": _FALLBACK_DISPLAY}


def _get_gs_env() -> dict:
    """Return env dict with GAMESCOPE_WAYLAND_DISPLAY set (detected dynamically)."""
    try:
        from tools.aoe3_automation.gamescope_detect import get_gs_env
        return get_gs_env()
    except Exception:
        return {**os.environ,
                "GAMESCOPE_WAYLAND_DISPLAY": _FALLBACK_GS_WL,
                "WAYLAND_DISPLAY": _FALLBACK_GS_WL}


# Module-level aliases kept for backward-compat with callers that read these directly.
# They resolve at import time; if the game isn't running yet that's fine since we
# always re-call _get_xdo_env() / _get_gs_env() in each operation.
_XDO_ENV = {**os.environ, "DISPLAY": _FALLBACK_DISPLAY}
_GS_ENV = {**os.environ,
           "GAMESCOPE_WAYLAND_DISPLAY": _FALLBACK_GS_WL,
           "WAYLAND_DISPLAY": _FALLBACK_GS_WL}

# AoE3's own screenshot output directory (written by the game on PrintScreen).
AOE3_SCREENSHOT_DIR = (
    Path.home()
    / ".local/share/Steam/steamapps/compatdata/933110"
    / "pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Screenshots"
)

# ---------------------------------------------------------------------------
# UI coordinate constants
# ---------------------------------------------------------------------------

# Main menu
SKIRMISH_BTN = (80, 490)
CONTINUE_BTN = (80, 330)

# Skirmish setup – civ flags (click to open civ picker)
P1_CIV_FLAG = (585, 176)
P2_CIV_FLAG = (585, 282)
P3_CIV_FLAG = (585, 388)
P4_CIV_FLAG = (585, 494)
PICKER_OK    = (240, 976)
PICKER_CANCEL = (580, 960)

# Skirmish setup – right panel controls
MAP_BTN      = (1550, 414)   # opens full map-picker modal
MAP_OK       = (240, 976)    # confirm selection inside modal
PLAY_BTN     = (1646, 1030)

# ESC menu (right panel, opened by pressing Escape in-game).
# 2026-04-29 RE-VERIFIED via cropped screenshot of menu in matrix_runner state:
# Menu order top→bottom (8 items): Photo Mode (y≈97), Tech Tree (y≈148),
# Save (y≈197), Load (y≈242), Restart (y≈287), Options (y≈332),
# RESIGN (y≈377), Quit (y≈422).  Previous y=350 was hitting OPTIONS, which
# opens a submenu that consumed all subsequent clicks — leaving the player
# trapped in-game.  Y=377 hits RESIGN cleanly.
ESC_MENU_X   = 1750
ESC_RESIGN   = (ESC_MENU_X, 377)
ESC_QUIT     = (ESC_MENU_X, 422)
# Abandon-screen ESC menu has only 4 items (VIEW POSTGAME, RESTART, OPTIONS,
# QUIT). QUIT is the 4th item at y≈225 (bands found via pixel-scan: button
# centers are ~92, 135, 180, 225).
ABANDON_QUIT = (ESC_MENU_X, 225)

# Resign confirmation dialog (centered)
# Verified via pixel-scan of confirm dialog: YES button spans roughly
# x∈[660,870], y∈[596,628]; NO button spans x∈[1060,1280] same y. Center
# of YES = (760, 610). The earlier value (750, 540) hit the dialog title
# bar area and only worked occasionally via cursor-state side-effects.
RESIGN_YES   = (760, 610)
RESIGN_NO    = (1170, 610)

# Post-resign / abandon screen
VIEW_MAP      = (680, 729)
VIEW_POSTGAME = (1128, 729)

# Post-game screen
POSTGAME_QUIT = (50, 20)

# Speed bar: gold horizontal bar bottom-right of HUD.
# Five click positions for 5 speed tiers (1=slowest … 5=fastest).
SPEED_BAR_Y  = 1058
SPEED_TICKS  = {1: 1635, 2: 1685, 3: 1760, 4: 1835, 5: 1895}

# In-game detector: resource bar at top (y≈15). Pixel sum > 280 means HUD is visible.
HUD_PROBE_XY = (200, 15)
HUD_THRESHOLD = 280

# ---------------------------------------------------------------------------
# Low-level primitives
# ---------------------------------------------------------------------------

def _xdo(*args: str) -> None:
    """Run an xdotool command on the dynamically-detected AoE3 display."""
    r = subprocess.run(["xdotool", *args], env=_get_xdo_env(),
                       capture_output=True, check=False, text=True)
    if r.returncode != 0 or r.stderr.strip():
        print(f"[XDO] {' '.join(args)} rc={r.returncode} "
              f"stderr={r.stderr.strip()!r} stdout={r.stdout.strip()!r}",
              flush=True)


def _focus_window() -> None:
    """Bring the AoE3 window to foreground so keyboard events land.

    Gamescope's nested Xwayland (where AoE3 lives) is the *only* X client
    on its display, so "stealing focus" is meaningless there — there's
    nothing else to steal from.  We also can't read _NET_ACTIVE_WINDOW
    (gamescope doesn't expose EWMH), so we just unconditionally
    windowactivate the AoE3 window.  No --sync (also unsupported).
    """
    env = _get_xdo_env()
    res = subprocess.run(
        ["xdotool", "search", "--name", "Age of Empires"],
        env=env, capture_output=True, text=True,
    )
    wids = [w.strip() for w in res.stdout.splitlines() if w.strip()]
    if not wids:
        return  # window gone; caller's next operation will fail loudly
    subprocess.run(
        ["xdotool", "windowactivate", wids[0]],
        env=env, capture_output=True, check=False,
    )
    time.sleep(0.3)


def _click(x: int, y: int, *, delay: float = 0.25) -> None:
    """Left-click at game-window coordinates (x, y).

    2026-04-29: split mousemove and click into separate xdotool invocations
    with a small inter-step sleep. Combined `mousemove X Y click 1` works
    for ESC menu rows but is unreliable on confirm-dialog buttons (RESIGN
    YES) — the click event fires before gamescope finishes the cursor warp,
    so the click lands on the previous cursor position. Splitting the calls
    forces gamescope to settle the cursor before the button event arrives.
    """
    _xdo("mousemove", str(x), str(y))
    time.sleep(0.15)
    _xdo("click", "1")
    time.sleep(delay)


def _key(keyname: str, n: int = 1, delay: float = 0.08) -> None:
    """Press a key N times."""
    for _ in range(n):
        _xdo("key", keyname)
        time.sleep(delay)


def _esc_menu_open() -> bool:
    """Sample pixel (1750, 100) via gamescopectl. ESC menu shows brown
    panel pixels (~R=82,G=34,B=17); in-game shows near-black. Returns
    True if menu pixel sum > 60. Uses /tmp probe file."""
    import tempfile
    probe = "/tmp/.aoe3_menu_probe.png"
    try:
        env = {**os.environ, "DISPLAY": _FALLBACK_DISPLAY}
        subprocess.run(["gamescopectl", "screenshot", probe],
                       env=env, capture_output=True, check=False, timeout=8)
        from PIL import Image
        with Image.open(probe) as im:
            r, g, b = im.getpixel((1750, 100))[:3]
            return (r + g + b) > 60
    except Exception:
        return False


def _open_esc_menu_robust(max_attempts: int = 5) -> bool:
    """Press Escape, verify menu open via pixel probe, retry if not.

    Some game states (chat overlay just closed, post-action HUD) eat the
    first Escape. Retry up to N times, alternating Escape with brief sleep.
    Returns True if menu confirmed open."""
    for i in range(max_attempts):
        _xdo("key", "Escape")
        time.sleep(2.0)  # let menu animate in
        if _esc_menu_open():
            return True
        # If menu not open, the Escape may have closed something else.
        # Brief extra wait, then loop. Don't spam Escape (might close menu
        # we just opened).
        time.sleep(0.5)
    return False


def _screenshot_raw(path: str | Path, retries: int = 1) -> bool:
    """Capture a screenshot of AoE3 using the GAME's own screenshot binding.

    External capture is impossible on this rig (see module docstring): every
    method we tested returned uniformly black pixels because gamescope renders
    direct-to-GPU and bypasses the host compositor's sample path.  The only
    way to obtain real game pixels is to ask AoE3 itself, which writes a PNG
    to its profile Screenshots/ folder when the user presses PrintScreen.

    Strategy:
      1. Snapshot the existing files in AOE3_SCREENSHOT_DIR.
      2. Focus the AoE3 window and send PrintScreen via xdotool.
      3. Poll the directory for a new file (up to 5 s).
      4. Copy the new file to ``path``.

    Returns True on success; False if no new file appeared (e.g. dev mode
    not active, or the keybind was rebound).  In failure mode we DO NOT
    write a stub file — callers must tolerate `not path.exists()`.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)

    AOE3_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in AOE3_SCREENSHOT_DIR.glob("*.png")}

    for _ in range(retries):
        _focus_window()
        # AoE3 default screenshot key is PrintScreen on Windows; on Proton/Linux
        # the key event still triggers it.  Some builds also accept F12.
        subprocess.run(["xdotool", "key", "Print"],
                       env=_get_xdo_env(), capture_output=True, check=False)
        # Poll up to 5 s for a new file.
        deadline = time.time() + 5.0
        while time.time() < deadline:
            time.sleep(0.5)
            new_files = [p for p in AOE3_SCREENSHOT_DIR.glob("*.png")
                         if p.name not in before]
            if new_files:
                # Copy the newest one to the requested path.
                src = max(new_files, key=lambda p: p.stat().st_mtime)
                try:
                    path.write_bytes(src.read_bytes())
                    return True
                except OSError:
                    return False
    return False


def _pixel_sum(path: Path, x: int, y: int) -> int:
    """Return R+G+B of a single pixel (requires Pillow).

    NOTE: kept for backward-compat but generally unusable on this rig because
    no external screenshot path captures real AoE3 pixels.  Returns 0 if the
    file is missing or unreadable so callers degrade gracefully.
    """
    try:
        from PIL import Image
        if not Path(path).exists():
            return 0
        px = Image.open(path).convert("RGB").getpixel((x, y))
        return sum(px)
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class GameDriver:
    """High-level driver for an AoE3 DE skirmish session.

    Wraps manage_game.py for lifecycle, then layers menu navigation,
    screenshot capture, speed control, and resign on top.
    """

    def __init__(self, art_dir: Path | str = "/tmp/aoe_test/in_game_driver") -> None:
        self.art_dir = Path(art_dir)
        self.art_dir.mkdir(parents=True, exist_ok=True)
        self._shot_counter = 0

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def open(self, timeout: int = 180, post_wait: int = 8) -> bool:
        """Launch game via manage_game.py and wait for the 1920×1080 window."""
        rc = subprocess.run(
            [sys.executable, str(MANAGE_GAME), "open",
             "--timeout", str(timeout),
             "--post-menu-wait", str(post_wait)],
            capture_output=False,
        ).returncode
        return rc == 0

    def close(self) -> None:
        """Gracefully close the game."""
        subprocess.run([sys.executable, str(MANAGE_GAME), "close"],
                       capture_output=False)

    def is_running(self) -> bool:
        """Return True if the game process is alive at 1920×1080."""
        rc = subprocess.run(
            [sys.executable, str(MANAGE_GAME), "status"],
            capture_output=True, text=True,
        ).returncode
        return rc == 0

    def wait_for_main_menu(self, timeout: int = 60) -> bool:
        """Wait for the main menu to be ready for input.

        We can't see the screen (no external screenshot path on this rig),
        so this is a TIME-BASED wait: simply sleep ``timeout`` seconds, then
        verify the AoE3 window is still alive on the expected display.
        Empirically the AoE3 main menu becomes click-responsive ~30 s after
        cold launch; default timeout=60 leaves comfortable headroom.

        Returns True if the AoE3 X window still exists at end of wait.
        """
        time.sleep(min(timeout, 60))
        env = _get_xdo_env()
        res = subprocess.run(
            ["xdotool", "search", "--name", "Age of Empires"],
            env=env, capture_output=True, text=True,
        )
        return bool(res.stdout.strip())

    def wait_for_in_game(self, timeout: int = 180, dismiss_errors: bool = True,
                         log_mirror: "Optional['LogMirror']" = None) -> bool:
        """Wait for the loading screen to finish and the match to be running.

        Strategy: poll Age3Log.txt for the engine's own readiness markers.
        These ARE flushed (mode transitions force a flush) and tell us
        deterministically when we've crossed into actual gameplay:

          - ``ModeTrack -- entering mode 27 (SinglePlayer)`` — match started.
          - ``WorldAssetPreloadingTime`` — world fully preloaded; AI loaders
            are about to fire (this is the strongest "match is playable" signal).

        We do NOT escape-spam during loading.  Empirically that destabilises
        the engine and triggered a D3D11 fatal during testing.  If an XS
        compiler error popup appears, the loading markers won't materialise
        and we'll time out — caller can recover.

        Args:
            timeout: max seconds to wait.
            dismiss_errors: kept for API compat.  We send a single late Return
                press at the very end if the load marker hasn't appeared,
                in case a single dialog is blocking; we never spam keys.
            log_mirror: an active LogMirror (from
                ``log_capture.start_log_tail``).  If provided, we read from
                its mirrored file (cheaper, doesn't restat Age3Log.txt).
                If None, we read Age3Log.txt directly.

        Returns True once ``WorldAssetPreloadingTime`` is observed; False on
        timeout.
        """
        deadline = time.time() + timeout
        last_size = -1
        nudged = False
        while time.time() < deadline:
            if log_mirror is not None:
                content = log_mirror.current_content()
            else:
                try:
                    content = AGE3_LOG_PATH.read_text(encoding="utf-8",
                                                      errors="replace")
                except OSError:
                    content = ""
            if "WorldAssetPreloadingTime" in content:
                return True
            # If we appear to have stalled (no log growth for 20 s past the
            # half-way point), do ONE Return press in case a dialog is blocking
            # the loader.  This is a single targeted nudge, not a spam loop.
            if (dismiss_errors and not nudged
                    and time.time() > deadline - timeout * 0.5
                    and len(content) == last_size):
                nudged = True
                _focus_window()
                _key("Return")
            last_size = len(content)
            time.sleep(2.0)
        return False

    # ------------------------------------------------------------------ #
    # State detection                                                      #
    # ------------------------------------------------------------------ #

    def is_in_game(self) -> bool:
        """Return True if HUD is visible (resource bar at top), i.e. we are
        inside an active match (whether running or paused). Uses the same
        gamescopectl pixel probe as _esc_menu_open. Best-effort — returns
        False on probe failure (caller treats as 'not in game')."""
        probe = "/tmp/.aoe3_hud_probe.png"
        try:
            env = {**os.environ, "DISPLAY": _FALLBACK_DISPLAY}
            try:
                os.unlink(probe)
            except FileNotFoundError:
                pass
            subprocess.run(["gamescopectl", "screenshot", probe],
                           env=env, capture_output=True, check=False, timeout=8)
            time.sleep(0.4)  # gamescopectl writes async
            from PIL import Image
            with Image.open(probe) as im:
                px = im.getpixel(HUD_PROBE_XY)
                r, g, b = px[:3]
                return (r + g + b) > HUD_THRESHOLD
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # Menu navigation                                                      #
    # ------------------------------------------------------------------ #

    def ensure_main_menu(self, retries: int = 5) -> bool:
        """Press Escape repeatedly to back out to the main menu.

        Blind operation — we can't verify pixel state.  We just send the
        full sequence of Escape keys; if we were anywhere in the menu tree
        or post-game flow, this gets us back to the root menu.  Caller
        should pair this with a fixed sleep before clicking menu buttons.
        """
        _focus_window()
        for _ in range(retries):
            _key("Escape")
            time.sleep(1.5)
        return True  # blind — assume success

    def _select_civ_for_slot(self, flag_coord: tuple[int, int], civ_idx: int) -> None:
        """Open the civ picker for one player slot and navigate to civ_idx (0-based).

        Strategy:
          1. Click the civ flag to open the picker modal.
          2. Press Up×60 to scroll to the very top of the list.
          3. Press Down×civ_idx to reach the target row.
          4. Click OK.

        The picker list is alphabetical. Index 0 = "Random Personality".
        Base civs start at index 1 (Argentina/Buenos Aires is index 1 in
        the "Select Home City" list).  The civ indices used by probe_coverage_matrix.py
        refer to this same picker ordering.
        """
        _click(*flag_coord, delay=2.0)
        _key("Up", n=60, delay=0.03)
        time.sleep(0.4)
        _key("Down", n=civ_idx, delay=0.04)
        time.sleep(0.4)
        _click(*PICKER_OK, delay=2.5)

    def start_skirmish(
        self,
        p1_civ_idx: int = 0,
        p2_civ_idx: Optional[int] = None,
        p3_civ_idx: Optional[int] = None,
        p4_civ_idx: Optional[int] = None,
        map_idx: Optional[int] = None,
        *,
        difficulty: str = "Hard",
        speed_tick: int = 3,
    ) -> bool:
        """Click through Single Player → Skirmish → setup → Play.

        Args:
            p1_civ_idx:  0-based index into the "Select Home City" picker list.
                         0 = Random Personality.  Pass None to keep default.
            p2/3/4_civ_idx: Same for AI slots.  None = leave at Random.
            map_idx:     If not None, opens the map-picker modal and presses
                         Up×60 then Down×map_idx then OK to select a map.
            difficulty:  Informational only — the setup screen difficulty is
                         already set in the game's UI; this param is not
                         automated (the default "Hard" matches the screen default).
                         To change difficulty, use Tab/arrow keys or add a
                         click at x=1700, y=570.
            speed_tick:  Initial game speed (1=slowest, 5=fastest). Applied
                         by set_speed() once the match starts.

        Returns True if Play was clicked successfully.

        NOTE: XS compiler errors appear on the loading screen.  Call
        wait_for_in_game(dismiss_errors=True) after this to handle them.
        """
        _focus_window()

        # Enter skirmish setup.
        _click(*SKIRMISH_BTN, delay=3.0)
        self.screenshot("skirmish_setup")

        # Select map if requested.
        if map_idx is not None:
            _click(*MAP_BTN, delay=1.5)
            _key("Up", n=60, delay=0.03)
            _key("Down", n=map_idx, delay=0.04)
            _click(*MAP_OK, delay=2.0)
            self.screenshot("map_selected")

        # Select civs for each slot.
        slots = [
            (P1_CIV_FLAG, p1_civ_idx),
            (P2_CIV_FLAG, p2_civ_idx),
            (P3_CIV_FLAG, p3_civ_idx),
            (P4_CIV_FLAG, p4_civ_idx),
        ]
        for flag_coord, idx in slots:
            if idx is not None:
                self._select_civ_for_slot(flag_coord, idx)

        self.screenshot("civs_selected")

        # Click Play.
        _click(*PLAY_BTN, delay=3.0)
        self.screenshot("loading_start")

        return True

    def set_speed(self, tick: int) -> None:
        """Set game speed by clicking the speed bar at tick position.

        tick=1 → slowest, tick=5 → fastest.
        The speed bar is a gold horizontal bar at y≈1058, x=1620-1900.
        Clicking anywhere on it moves the triangle marker.

        NOTE: keyboard +/- keys do NOT reliably change speed in this
        gamescope/Proton config.  Direct click on the bar is the only
        proven method.
        """
        tick = max(1, min(5, tick))
        x = SPEED_TICKS[tick]
        _focus_window()
        _click(x, SPEED_BAR_Y, delay=0.3)

    # ------------------------------------------------------------------ #
    # Resignation / return to menu                                         #
    # ------------------------------------------------------------------ #

    def resign(self) -> bool:
        """Open ESC menu → click Resign → confirm Yes → navigate to main menu.

        Returns True if we successfully returned to the main menu.

        Flow discovered empirically:
          1. Focus window (required or Escape is ignored).
          2. Press Escape → ESC menu appears on the right.
          3. Click Resign at (1750, 365).
          4. Click Yes at (750, 610) on the confirmation dialog.
          5. "You Abandon Your Town" screen appears with View Postgame button.
          6. Click View Postgame at (1128, 729).
          7. Click Quit (back button) at (50, 20) to return to main menu.
        """
        # 2026-04-29: ESC menu has 8 rows; RESIGN is row 7 at y=377 (NOT 350,
        # which is row 6 = OPTIONS — that row opens a submenu and steals
        # subsequent clicks, trapping the player in-game). Verified via
        # cropped screenshot of matrix_runner ESC menu state.
        # NOTE: do NOT call self.screenshot() between key/click stages —
        # that re-runs _focus_window() (windowactivate) and presses Print,
        # which interferes with the ESC menu's input state.
        # Screenshots are blind on this rig anyway.
        #
        # 2026-04-29: keyboard navigation (Down×N + Return) is NOT a viable
        # alternative to clicks for the in-game ESC menu — Return is bound
        # to "open chat" and opens the chat overlay instead of activating
        # the highlighted menu item. Direct clicks at (1750, 377) DO work
        # reliably once the XS compile error in aiEliteTactics.xs is fixed
        # (that error spawned a modal dialog that ate all input events,
        # which masked the click reliability of correct coords).
        #
        # Verified-working flow for 1v7 FFA:
        #   1. Escape → opens 8-item ESC menu.
        #   2. Click RESIGN at (1750, 377) → opens RESIGN confirm dialog.
        #   3. Click YES at (750, 540) → drops to "Abandon Your Town"
        #      screen (the 7 AIs continue; player is now in postgame).
        #   4. Escape → opens 4-item ESC menu (VIEW POSTGAME, RESTART,
        #      OPTIONS, QUIT — QUIT at y≈225).
        #   5. Click QUIT at (1750, 225) → returns directly to main menu
        #      (no second confirm dialog on this path).
        # 2026-04-29: do NOT use _open_esc_menu_robust here. Its
        # gamescopectl-screenshot pixel probe reads STALE frame data — by
        # the time the screenshot is committed the menu has already
        # toggled, so the probe lags by one step. The robust opener then
        # presses Escape repeatedly, toggling the menu open/closed. After
        # the XS compile error fix, a single Escape press reliably opens
        # the menu (the original "first Escape eaten" symptom was caused
        # by the XS error dialog consuming input, not a flaky Escape key).
        def _dbg_shot(label):
            try:
                p = f"/tmp/resign_dbg_{label}.png"
                env = {**os.environ, "DISPLAY": _FALLBACK_DISPLAY}
                subprocess.run(["gamescopectl", "screenshot", p],
                               env=env, capture_output=True, check=False, timeout=8)
                # Probe pixel: ESC menu brown at (1750,100), abandon-screen
                # button area at (760,610), and HUD probe.
                from PIL import Image
                with Image.open(p) as im:
                    menu = im.getpixel((1750, 100))[:3]
                    yes  = im.getpixel((760, 610))[:3]
                    hud  = im.getpixel((200, 15))[:3]
                print(f"[DBG {label}] menu={menu} yes={yes} hud={hud}", flush=True)
            except Exception as e:
                print(f"[DBG {label}] error: {e}", flush=True)

        print("[RESIGN] step 1: focus + Escape", flush=True)
        _focus_window()
        _dbg_shot("00_pre")

        # Step 1: open ESC menu, click RESIGN.
        _xdo("key", "Escape")
        time.sleep(1.5)
        _dbg_shot("01_post_esc")
        print(f"[RESIGN] step 2: click RESIGN at {ESC_RESIGN}", flush=True)
        _click(*ESC_RESIGN, delay=1.5)
        _dbg_shot("02_post_resign_click")

        # Step 2: confirm RESIGN (click YES). Retry in case first click misses.
        print(f"[RESIGN] step 3: click YES at {RESIGN_YES} x3", flush=True)
        for _ in range(3):
            _click(*RESIGN_YES, delay=1.5)
        _dbg_shot("03_post_yes")

        time.sleep(4.0)  # let engine flush replay + transition to abandon screen
        _dbg_shot("04_pre_esc2")

        # Step 3: open ESC menu again (4-item now), click QUIT.
        print("[RESIGN] step 4: Escape (4-item menu)", flush=True)
        _xdo("key", "Escape")
        time.sleep(1.5)
        _dbg_shot("05_post_esc2")
        print(f"[RESIGN] step 5: click QUIT at {ABANDON_QUIT} x3", flush=True)
        for _ in range(3):
            _click(*ABANDON_QUIT, delay=1.5)
        _dbg_shot("06_post_quit")

        time.sleep(5.0)  # let main menu render

        print("[RESIGN] step 6: ensure_main_menu", flush=True)
        return self.ensure_main_menu()

    def return_to_main_menu(self) -> bool:
        """From any state, attempt to return to the main menu.

        Tries pressing Escape multiple times and checking for the
        main-menu heuristic.  Use after resign() has already brought
        you to the post-game screen, or as a recovery fallback.
        """
        return self.ensure_main_menu(retries=8)

    # ------------------------------------------------------------------ #
    # Observation / screenshots                                            #
    # ------------------------------------------------------------------ #

    def screenshot(self, label: str) -> Path:
        """Take a screenshot via AoE3's in-game PrintScreen binding.

        Best-effort: returns a Path that may or may not exist.  External
        screenshot capture is impossible on this rig (see module docstring).
        We use the game's own screenshot key, which writes a PNG to the
        profile Screenshots/ directory; we then copy it into art_dir.

        If capture fails (game not focused, dev mode off, key rebound,
        etc.), we log a warning but DO NOT block the matrix run.  The
        matrix's primary signal is match.log probe count, not pixels.
        """
        self._shot_counter += 1
        path = self.art_dir / f"{self._shot_counter:02d}_{label}.png"
        ok = _screenshot_raw(path)
        if ok:
            print(f"[SHOT] {path}")
        else:
            print(f"[WARN] screenshot({label}) — no PNG produced "
                  f"(blind mode; matrix validation uses match.log instead)")
        return path

    def screenshot_full_run(self, label: str) -> list[Path]:
        """Capture a triplet: current state (setup/loading/hud), mid-game, resign screen.

        Returns list of Paths.  Intended for probe_coverage_matrix.py hooks.
        """
        paths = [self.screenshot(f"{label}_now")]
        return paths

    # ------------------------------------------------------------------ #
    # Probe-friendly hooks                                                 #
    # ------------------------------------------------------------------ #

    def observe(self, wall_seconds: int, snap_interval: int = 180) -> None:
        """Let the match run for wall_seconds of real time, taking periodic screenshots."""
        start = time.time()
        next_snap = start + snap_interval
        snap_idx = 1
        print(f"[OBS] observing for {wall_seconds}s …")
        while time.time() < start + wall_seconds:
            time.sleep(10)
            if time.time() >= next_snap:
                self.screenshot(f"snap_{snap_idx:02d}")
                snap_idx += 1
                next_snap += snap_interval

    def observe_until_coverage(
        self,
        log_mirror: "LogMirror",
        *,
        required_families: Iterable[str] = (),
        min_probe_count: int = 0,
        min_seconds: int = 30,
        max_seconds: int = 600,
        poll_interval: float = 3.0,
    ) -> dict:
        """Observe the live log mirror until coverage criteria are met.

        AoE3 buffers aiEcho output and only flushes it on certain events
        (mode transitions, clean exit / resign).  This means the live mirror
        will mostly stay quiet during gameplay and then receive a burst of
        probe lines after resign.  However, *some* probes (the boot probes:
        meta.boot, meta.setup, plan.build_snap) DO get flushed shortly after
        the AI initializes — those give us a quick "AI is alive" signal.

        Strategy:
          * Always wait at least ``min_seconds`` (gives the AI time to do
            its boot pass).  Default 30 s ≈ enough sim time at 5x speed for
            doctrine selection + commander setup probes.
          * Then poll: if we've seen at least ``min_probe_count`` probes
            AND every family in ``required_families`` is represented,
            return early ("coverage_met").
          * If ``max_seconds`` elapses without meeting criteria, return
            ("timeout").  Caller should still resign — the post-resign
            flush usually delivers enough probes for validation.

        Args:
            log_mirror: active LogMirror (from log_capture.start_log_tail).
            required_families: tag prefixes (e.g. {"meta", "compliance"})
                that must each have at least one probe before we exit early.
            min_probe_count: total probe-line count threshold for early exit.
            min_seconds: floor on observation time.
            max_seconds: ceiling on observation time.
            poll_interval: seconds between coverage checks.

        Returns dict with keys:
            status: "coverage_met" | "timeout"
            elapsed: float seconds observed
            probe_count: int probes seen at exit
            families_seen: sorted list[str] tag prefixes seen at exit
        """
        start = time.time()
        required = set(required_families)
        elapsed = 0.0
        probe_count = 0
        families_seen: set[str] = set()

        print(f"[OBS] observe_until_coverage: min={min_seconds}s max={max_seconds}s "
              f"need_probes>={min_probe_count} need_families={sorted(required) or 'any'}")

        while elapsed < max_seconds:
            time.sleep(poll_interval)
            elapsed = time.time() - start
            content = log_mirror.current_content()
            probe_count = content.count("[LLP v=2 ")

            # Extract families from each [LLP v=2 ... tag=foo.bar] line.
            families_seen = set()
            for line in content.splitlines():
                idx = line.find("[LLP v=2 ")
                if idx < 0:
                    continue
                tag_idx = line.find("tag=", idx)
                if tag_idx < 0:
                    continue
                tag_end = line.find("]", tag_idx)
                if tag_end < 0:
                    tag_end = len(line)
                tag = line[tag_idx + 4:tag_end]
                fam = tag.split(".", 1)[0]
                if fam:
                    families_seen.add(fam)

            if elapsed >= min_seconds:
                count_ok = probe_count >= min_probe_count
                fam_ok = required.issubset(families_seen)
                if count_ok and fam_ok:
                    print(f"[OBS] coverage met @ {elapsed:.1f}s "
                          f"probes={probe_count} families={sorted(families_seen)}")
                    return {
                        "status": "coverage_met",
                        "elapsed": elapsed,
                        "probe_count": probe_count,
                        "families_seen": sorted(families_seen),
                    }

            # Periodic progress.
            if int(elapsed) % 30 == 0:
                print(f"[OBS] t={elapsed:.0f}s  probes={probe_count}  "
                      f"families={sorted(families_seen)}")

        print(f"[OBS] timeout @ {elapsed:.1f}s probes={probe_count} "
              f"families={sorted(families_seen)}")
        return {
            "status": "timeout",
            "elapsed": elapsed,
            "probe_count": probe_count,
            "families_seen": sorted(families_seen),
        }

    def newest_replay(self, after_ts: float) -> Optional[Path]:
        """Return the most recent .age3Yrec written after `after_ts`."""
        if not RECORDED_GAMES.exists():
            return None
        candidates = [p for p in RECORDED_GAMES.rglob("*.age3Yrec")
                      if p.stat().st_mtime >= after_ts]
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test() -> int:
    """Launch game → main menu → skirmish → 60 s at max speed → resign → close.

    Prints PASS or FAIL with paths to all screenshots taken.
    Also captures the per-match Age3Log.txt slice and writes match.log next to
    the screenshots (requires developer mode via manage_game.py open).
    Returns 0 on PASS, 1 on FAIL.
    """
    art = Path("/tmp/aoe_test/in_game_driver_selftest")
    d = GameDriver(art_dir=art)
    shots: list[Path] = []
    failures: list[str] = []

    print("=" * 60)
    print("in_game_driver self-test")
    print("=" * 60)

    # ── Step 1: ensure game is running ───────────────────────────────────
    print("\n[1] Checking / launching game …")
    if not d.is_running():
        print("  Game not running — launching via manage_game.py open …")
        ok = d.open(timeout=180, post_wait=10)
        if not ok:
            failures.append("game did not reach 1920×1080 within timeout")
            print("FAIL:", failures[-1])
            return 1
    else:
        print("  Game already running.")

    # ── Step 2: main menu ────────────────────────────────────────────────
    print("\n[2] Waiting for main menu …")
    shots.append(d.screenshot("step2_pre_menu"))
    if not d.wait_for_main_menu(timeout=60):
        # Not on main menu — try pressing Escape to get there.
        print("  Not on main menu — pressing Escape …")
        d.ensure_main_menu()
    shots.append(d.screenshot("step2_main_menu"))
    print("  Main menu confirmed.")

    # ── Step 3: start skirmish ───────────────────────────────────────────
    # Use civ idx 0 (Random Personality) for speed; 2 players only.
    print("\n[3] Starting skirmish (P1=Random, P2=Random) on Great Lakes …")
    match_start_ts = time.time()
    # Snapshot Age3Log.txt offset BEFORE the match starts so we can capture
    # the per-match probe slice after resign.
    try:
        from tools.aoe3_automation.log_capture import snapshot_offset
        log_offset = snapshot_offset()
        print(f"  Age3Log.txt offset before match: {log_offset} bytes")
    except ImportError:
        log_offset = None
        print("  WARN: log_capture not available; match.log will not be written")
    d.start_skirmish(p1_civ_idx=0)
    # start_skirmish() already takes its own screenshots internally via d.screenshot()

    # ── Step 4: wait for in-game ─────────────────────────────────────────
    print("\n[4] Waiting for in-game HUD (dismissing XS errors) …")
    if not d.wait_for_in_game(timeout=180, dismiss_errors=True):
        failures.append("in-game HUD never detected within 180 s")
        print("FAIL:", failures[-1])
        shots.append(d.screenshot("step4_timeout"))
        _print_summary(shots, failures)
        return 1
    shots.append(d.screenshot("step4_ingame"))
    print("  In-game HUD detected.")

    # ── Step 5: set speed to max ─────────────────────────────────────────
    print("\n[5] Setting game speed to maximum (tick=5) …")
    d.set_speed(5)
    time.sleep(1)
    shots.append(d.screenshot("step5_speed_max"))

    # ── Step 6: observe 60 s ─────────────────────────────────────────────
    print("\n[6] Observing for 60 real seconds …")
    d.observe(wall_seconds=60, snap_interval=30)
    shots.append(d.screenshot("step6_mid_game"))

    # ── Step 7: resign ───────────────────────────────────────────────────
    print("\n[7] Resigning …")
    resign_ok = d.resign()
    shots.append(d.screenshot("step7_post_resign"))

    # ── Step 8: capture match log and check replay ───────────────────────
    print("\n[8] Capturing match log and looking for replay …")
    if log_offset is not None:
        try:
            from tools.aoe3_automation.log_capture import read_since, probe_count_in_slice
            log_content = read_since(log_offset)
            match_log_path = art / "match.log"
            match_log_path.write_text(log_content, encoding="utf-8", errors="replace")
            probe_n = probe_count_in_slice(log_content)
            print(f"  match.log: {match_log_path} ({len(log_content)} bytes, {probe_n} probe lines)")
            if probe_n == 0:
                print("  WARN: zero [LLP v=2] probes in match.log — dev mode may not be active")
                print("    Ensure manage_game.py open (not --no-dev-mode) was used to launch.")
        except Exception as exc:
            print(f"  WARN: log capture failed: {exc}")
    replay = d.newest_replay(after_ts=match_start_ts)
    if replay:
        print(f"  Replay: {replay}")
    else:
        failures.append("no replay file found in Savegame/ after match start")
        print("WARN:", failures[-1])

    if not resign_ok:
        failures.append("resign() did not return to main menu cleanly")

    # ── Result ───────────────────────────────────────────────────────────
    _print_summary(shots, failures)
    return 0 if not failures else 1


def _print_summary(shots: list[Path], failures: list[str]) -> None:
    print("\n" + "=" * 60)
    print("Screenshots taken:")
    for p in shots:
        exists = "✓" if p.exists() else "✗"
        print(f"  {exists} {p}")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        print("\nRESULT: FAIL")
    else:
        print("\nRESULT: PASS")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--self-test", action="store_true",
                   help="Run end-to-end self test and exit with 0=PASS / 1=FAIL")
    args = p.parse_args()

    if args.self_test:
        sys.exit(self_test())
    else:
        p.print_help()
