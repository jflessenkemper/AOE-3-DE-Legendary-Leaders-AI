#!/usr/bin/env python3
"""Dynamic gamescope / Xwayland display detection for AoE3 DE on Bazzite/Proton.

The user may run two gamescope instances simultaneously (e.g. AoE3 DE + CoH2).
The gamescope-N → DISPLAY-N mapping is dynamic — order depends on launch order.
This module detects the AoE3 instance at runtime by sweeping every known
X display and gamescope socket until it finds the combination that owns the
"Age of Empires III" window.

Public API:
    detect_aoe3_display() -> tuple[str, str]
        Returns (X_DISPLAY, GAMESCOPE_WAYLAND_DISPLAY), e.g. (":2", "gamescope-1").
        Raises RuntimeError if AoE3 is not running.

    get_xdo_env()   -> dict  # {DISPLAY: ..., ...os.environ}
    get_gs_env()    -> dict  # {GAMESCOPE_WAYLAND_DISPLAY: ..., WAYLAND_DISPLAY: ..., ...}
    get_both_env()  -> dict  # both merged into os.environ copy

The result is cached process-wide after the first successful detection.
Call invalidate_cache() to force a re-detect on the next call (useful when
resetting between packs if CoH2 may have started/stopped).
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import time
from typing import Optional

WINDOW_TITLE_SUBSTR = "Age of Empires III"
_CACHE: Optional[tuple[str, str]] = None  # (X_DISPLAY, GAMESCOPE_WL)


def invalidate_cache() -> None:
    """Force re-detection on the next call to detect_aoe3_display()."""
    global _CACHE
    _CACHE = None


def _x_displays() -> list[str]:
    """Return all candidate X displays from /tmp/.X*-lock files, lowest first."""
    candidates: list[str] = []
    for lock in sorted(glob.glob("/tmp/.X*-lock")):
        n = lock.removeprefix("/tmp/.X").removesuffix("-lock")
        if n.isdigit():
            candidates.append(f":{n}")
    # Also honour the inherited $DISPLAY.
    env_display = os.environ.get("DISPLAY", "")
    if env_display and env_display not in candidates:
        candidates.insert(0, env_display)
    return candidates


def _gamescope_sockets() -> list[str]:
    """Return all gamescope-N wayland socket names found in $XDG_RUNTIME_DIR."""
    xdg = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    sockets = sorted(glob.glob(os.path.join(xdg, "gamescope-*")))
    names = [os.path.basename(s) for s in sockets]
    # Fallback to well-known names if directory scan finds nothing.
    if not names:
        names = ["gamescope-0", "gamescope-1", "gamescope-2"]
    return names


_XWININFO_RE = re.compile(
    r'^\s*(0x[0-9a-fA-F]+)\s+"([^"]*)":\s*\([^)]*\)\s+(\d+)x(\d+)\+(-?\d+)\+(-?\d+)'
)


def _has_aoe3_window(display: str) -> bool:
    """Return True if 'Age of Empires III' window exists on this X display."""
    env = {**os.environ, "DISPLAY": display}
    # Try wmctrl first (fast on EWMH-capable displays).
    res = subprocess.run(
        ["wmctrl", "-lG"], env=env, capture_output=True, text=True
    )
    if res.returncode == 0 and WINDOW_TITLE_SUBSTR in res.stdout:
        return True
    # Fallback: xwininfo (works on gamescope nested Xwayland).
    res2 = subprocess.run(
        ["xwininfo", "-root", "-tree"], env=env, capture_output=True, text=True
    )
    if res2.returncode == 0:
        for line in res2.stdout.splitlines():
            if WINDOW_TITLE_SUBSTR in line:
                return True
    return False


def _gs_socket_works(gs_socket: str, *, timeout: int = 5) -> bool:
    """Return True if gamescopectl can reach the given gamescope socket."""
    env = {
        **os.environ,
        "GAMESCOPE_WAYLAND_DISPLAY": gs_socket,
        "WAYLAND_DISPLAY": gs_socket,
    }
    try:
        res = subprocess.run(
            ["gamescopectl", "status"],
            env=env, capture_output=True, timeout=timeout,
        )
        return res.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def detect_aoe3_display(*, use_cache: bool = True) -> tuple[str, str]:
    """Detect (X_DISPLAY, GAMESCOPE_WL) for the running AoE3 DE instance.

    Algorithm:
      1. For each X display with an X-lock file, check for the AoE3 window.
      2. For each gamescope socket in $XDG_RUNTIME_DIR, try `gamescopectl status`.
      3. Pair the first valid X display with the first valid gamescope socket.
         (They are typically co-indexed: :1 + gamescope-0, :2 + gamescope-1, etc.
         but we verify each independently rather than assuming the offset.)

    Returns (X_DISPLAY, GAMESCOPE_WL), e.g. (":2", "gamescope-1").
    Raises RuntimeError if no AoE3 window is found on any display.
    """
    global _CACHE
    if use_cache and _CACHE is not None:
        return _CACHE

    displays = _x_displays()
    sockets = _gamescope_sockets()

    aoe3_display: Optional[str] = None
    for d in displays:
        if _has_aoe3_window(d):
            aoe3_display = d
            break

    if aoe3_display is None:
        raise RuntimeError(
            f"AoE3 DE window not found on any X display "
            f"(checked: {displays}). Is the game running?"
        )

    # Find the first gamescope socket that responds to gamescopectl.
    aoe3_gs: Optional[str] = None
    for gs in sockets:
        if _gs_socket_works(gs):
            aoe3_gs = gs
            break

    if aoe3_gs is None:
        # Hard fallback: derive from display number (offset -1 for display :1 -> gamescope-0).
        num_str = aoe3_display.lstrip(":")
        try:
            idx = max(0, int(num_str) - 1)
        except ValueError:
            idx = 0
        aoe3_gs = f"gamescope-{idx}"
        print(
            f"[gamescope_detect] WARNING: gamescopectl did not respond on any socket; "
            f"falling back to derived name '{aoe3_gs}' (from DISPLAY={aoe3_display})."
        )

    print(
        f"[gamescope_detect] AoE3 detected: DISPLAY={aoe3_display}  "
        f"GAMESCOPE_WAYLAND_DISPLAY={aoe3_gs}"
    )
    _CACHE = (aoe3_display, aoe3_gs)
    return _CACHE


# ---------------------------------------------------------------------------
# Convenience helpers for callers that build subprocess env dicts.
# ---------------------------------------------------------------------------

def get_xdo_env(*, use_cache: bool = True) -> dict[str, str]:
    """Return os.environ copy with DISPLAY set to the AoE3 Xwayland display."""
    display, _ = detect_aoe3_display(use_cache=use_cache)
    return {**os.environ, "DISPLAY": display}


def get_gs_env(*, use_cache: bool = True) -> dict[str, str]:
    """Return os.environ copy with GAMESCOPE_WAYLAND_DISPLAY and WAYLAND_DISPLAY set."""
    _, gs = detect_aoe3_display(use_cache=use_cache)
    return {**os.environ, "GAMESCOPE_WAYLAND_DISPLAY": gs, "WAYLAND_DISPLAY": gs}


def get_both_env(*, use_cache: bool = True) -> dict[str, str]:
    """Return os.environ copy with DISPLAY + GAMESCOPE_WAYLAND_DISPLAY + WAYLAND_DISPLAY set."""
    display, gs = detect_aoe3_display(use_cache=use_cache)
    return {
        **os.environ,
        "DISPLAY": display,
        "GAMESCOPE_WAYLAND_DISPLAY": gs,
        "WAYLAND_DISPLAY": gs,
    }


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        d, gs = detect_aoe3_display()
        print(f"PASS: DISPLAY={d}  GAMESCOPE_WAYLAND_DISPLAY={gs}")
    except RuntimeError as e:
        print(f"FAIL: {e}")
        raise SystemExit(1)
