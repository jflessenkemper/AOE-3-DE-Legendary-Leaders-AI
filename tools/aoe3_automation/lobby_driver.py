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
SCROLL_TABLE_PATH = Path(__file__).parent / "picker_scroll_table.json"
RAW_DIR = Path(__file__).parent / "templates" / "matrix" / "_raw"
CLEAN_LOBBY_REF = RAW_DIR / "05_skirmish_lobby.png"
ARTIFACT_DIR = Path(__file__).parent / "artifacts" / "lobby_driver"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# Authoritative civ order — sourced from picker_scroll_table.json["civ_names"].
# Loaded lazily so the driver still works for non-civ-select commands.
CIV_ORDER: list[str] | None = None


def get_civ_order() -> list[str]:
    global CIV_ORDER
    if CIV_ORDER is None:
        CIV_ORDER = list(load_scroll_table()["civ_names"])
    return CIV_ORDER


def load_coords() -> dict:
    return json.loads(COORDS_PATH.read_text())


def load_scroll_table() -> dict:
    """Load picker_scroll_table.json — empirically built mapping
    scroll_count → top visible civ_index. The picker advances ~0.74
    rows per wheel-down click (NOT 1:1), so we can't compute scrolls
    needed analytically; we look it up.
    """
    return json.loads(SCROLL_TABLE_PATH.read_text())


def find_scrolls_for_civ(table: dict, civ_idx: int) -> tuple[int, int]:
    """Given a target civ_idx, return (scrolls_needed, click_row_within_visible).

    Targets a STABLE click row (0..rows_visible-3) — never the bottom 2 rows,
    because empirically the picker sometimes only fully renders 9/10 rows
    during a scroll animation, so row=9 (and sometimes row=8) can be missing.

    Strategy:
      - Prefer scroll counts where civ_idx lands at row in [0..7]
      - Among those, pick the smallest scroll count (least scrolling work)
      - Fall back to row 8 then 9 for civs near the very end of the list
        that have no choice (the picker has already saturated)
    """
    rows_visible = int(table["rows_visible"])  # 10
    safe_max_row = rows_visible - 3            # 7
    s2t = table["scroll_to_top_idx"]
    candidates: list[tuple[int, int, int]] = []  # (preference, n, click_row)
    for n_str in sorted(s2t.keys(), key=int):
        n = int(n_str)
        top = int(s2t[n_str])
        if top <= civ_idx <= top + rows_visible - 1:
            click_row = civ_idx - top
            # Prefer rows 0..7 (safe), else row 8, else row 9
            if click_row <= safe_max_row:
                pref = 0
            elif click_row == rows_visible - 2:
                pref = 1
            else:
                pref = 2
            candidates.append((pref, n, click_row))
    if not candidates:
        raise ValueError(
            f"civ_idx {civ_idx} not reachable; max top in table is "
            f"{max(int(v) for v in s2t.values())}"
        )
    candidates.sort(key=lambda t: (t[0], t[1]))
    _, scrolls, click_row = candidates[0]
    return scrolls, click_row


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
    """Wheel-down at the picker's scroll anchor. Re-anchors every iter
    because empirically the cursor sometimes drifts (or a hover-tooltip
    shifts focus) and the next wheel event gets dropped. Re-anchoring is
    cheap and makes the scroll deterministic.
    """
    sa = coords["civ_picker"]["scroll_anchor"]
    for _ in range(n):
        xdo(f"mousemove {sa[0]} {sa[1]}")
        time.sleep(0.12)
        xdo("click 5")  # button 5 = wheel-down
        time.sleep(0.25)


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


def open_civ_picker(coords: dict, *, attempts: int = 3, settle: float = 2.0) -> None:
    """Click P1 civ '?' to open the picker; verify by pixel-diff vs clean lobby.

    The picker animation can take 1.5-2s to fully render. We wait `settle` s
    after each click, then sample. If the picker is already open (e.g. from
    a leftover state), the second click will close it — handle that by
    re-clicking until detection is positive.
    """
    cx, cy = coords["lobby"]["p1_civ_picker"]
    for i in range(attempts):
        click(cx, cy)
        time.sleep(settle)
        if is_picker_open(coords):
            return
        # Wait a bit more in case animation was slow, before retry
        time.sleep(0.8)
        if is_picker_open(coords):
            return
        print(f"  open_civ_picker: attempt {i+1} did not open picker, retrying")
    raise RuntimeError("Failed to open civ picker after multiple attempts")


def cancel_civ_picker(coords: dict) -> None:
    cx, cy = coords["civ_picker"]["cancel_button"]
    click(cx, cy)
    time.sleep(0.9)
    move_mouse_off()


def select_civ_in_picker(coords: dict, civ_index: int) -> None:
    """With picker open + scrolled to top, scroll then click target row.

    Uses picker_scroll_table.json to look up exact scroll count, since each
    wheel-down advances ~0.74 rows (NOT 1:1) on this build.

    For civs at/near the saturation boundary (last few rows where the
    picker can't scroll further), we over-scroll well past saturation
    (~+8 extra wheel-downs) so the row positions stabilize on the
    "fully-saturated" layout (matches picker_scroll_53 empirical Ys).
    Without this, fractional scroll variance leaves rows at unpredictable
    pixel offsets between consecutive scroll counts at the same top_idx.
    """
    cp = coords["civ_picker"]
    if civ_index < 0:
        raise ValueError(f"civ_index must be >= 0, got {civ_index}")
    table = load_scroll_table()
    scrolls_needed, click_row = find_scrolls_for_civ(table, civ_index)
    # If we'd be clicking near the bottom of a saturated picker, over-scroll
    # to stabilize the layout. Cheap insurance: ~8 extra wheel events.
    s2t = table["scroll_to_top_idx"]
    max_top = max(int(v) for v in s2t.values())
    top_at_n = int(s2t[str(scrolls_needed)])
    overscroll = 0
    if top_at_n == max_top and click_row >= 7:
        overscroll = 10  # past saturation; the wheel events are safe no-ops
    total_scrolls = scrolls_needed + overscroll
    if total_scrolls > 0:
        scroll_down(coords, n=total_scrolls)
    target_row_y = cp["row_y_start"] + click_row * cp["row_spacing"]
    click(cp["row_x_center"], target_row_y, settle=0.4)
    time.sleep(0.6)


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
    order = get_civ_order()
    norm = name.strip().lower()
    matches = [i for i, c in enumerate(order) if c.lower() == norm]
    if not matches:
        matches = [i for i, c in enumerate(order) if c.lower().startswith(norm)]
    if not matches:
        matches = [i for i, c in enumerate(order) if norm in c.lower()]
    if not matches:
        print(f"Unknown civ: {name!r}. Known: {order}")
        return 2
    idx = matches[0]
    print(f"Selecting civ #{idx}: {order[idx]}")
    set_civ_by_index(coords, idx)
    print("Done. Capturing post-selection state…")
    safe = re.sub(r"[^A-Za-z0-9]+", "_", order[idx]).strip("_")
    p = ARTIFACT_DIR / f"after_select_{safe}.png"
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


def cmd_map_picker(coords: dict, max_scrolls: int = 60) -> int:
    """Open civ picker, scroll through entire list, save each state.

    Detects end of list when two consecutive scrolls produce the same
    pixel-equal screenshot (no further scrolling possible). Saves each
    distinct state as picker_scroll_NN.png and writes
    picker_states.json with metadata.
    """
    out_dir = ARTIFACT_DIR / "picker_map"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Clean any old captures
    for p in out_dir.glob("picker_scroll_*.png"):
        p.unlink()

    open_civ_picker(coords)
    print("Picker open. Capturing scroll states...")

    cap0 = out_dir / "picker_scroll_00.png"
    screenshot(cap0)
    states = [{"scroll": 0, "path": str(cap0)}]
    print(f"  scroll=0 → {cap0.name}")
    last_path = cap0
    consecutive_zero = 0

    for i in range(1, max_scrolls + 1):
        scroll_down(coords, n=1)
        time.sleep(0.55)  # longer settle so list state is stable when we capture
        cap = out_dir / f"picker_scroll_{i:02d}.png"
        screenshot(cap)
        d = diff_pixels(last_path, cap)
        states.append({"scroll": i, "path": str(cap), "diff_from_prev": d})
        # End-of-list detection: 3 consecutive zero-diffs. A single zero-diff
        # can be a race (screenshot taken before scroll finished propagating);
        # only treat sustained no-change as "we hit the bottom".
        if d <= coords["diff_thresholds"]["noise_floor"]:
            consecutive_zero += 1
            print(f"  scroll={i} → {cap.name}  (diff={d}, zero-streak={consecutive_zero})")
            if consecutive_zero >= 3:
                print(f"  hit bottom (3 consecutive zero-diffs at scroll={i})")
                break
        else:
            consecutive_zero = 0
            print(f"  scroll={i} → {cap.name}  (diff={d})")
        last_path = cap

    # Cancel out
    cancel_civ_picker(coords)

    meta_path = out_dir / "picker_states.json"
    meta_path.write_text(json.dumps({
        "row_count_visible": coords["civ_picker"]["row_count_visible"],
        "row_y_start": coords["civ_picker"]["row_y_start"],
        "row_spacing": coords["civ_picker"]["row_spacing"],
        "states": states,
        "last_scroll_idx": states[-1]["scroll"],
    }, indent=2))

    last = states[-1]["scroll"]
    visible = coords["civ_picker"]["row_count_visible"]
    print(f"\nMapped picker. Last scroll={last}, visible={visible}.")
    print(f"Estimated total civs: {last + visible}")
    print(f"States saved: {out_dir}/picker_scroll_*.png")
    print(f"Metadata: {meta_path}")
    return 0


def cmd_full_run_dry(coords: dict, civ_idx: int) -> int:
    """Dry-run: select civ at idx, capture state, reset. Don't click PLAY."""
    print(f"[1/3] Verifying clean lobby state…")
    if not is_clean_lobby(coords):
        print("WARN: not at clean lobby; attempting Cancel + Escape recovery…")
        cancel_civ_picker(coords)
    print(f"[2/3] Selecting civ index {civ_idx}…")
    set_civ_by_index(coords, civ_idx)
    p = ARTIFACT_DIR / f"dryrun_civ_{civ_idx:02d}.png"
    screenshot(p)
    print(f"  saved: {p}")
    print(f"[3/3] Resetting to Random Personality…")
    reset_p1_to_random(coords)
    print("Done.")
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
    ap.add_argument("--map-picker", action="store_true",
                    help="Open civ picker, scroll through entire list, save each scroll-state PNG to artifacts/lobby_driver/picker_map/")
    ap.add_argument("--select-civ-by-idx", type=int, metavar="N",
                    help="Select civ at picker index N (0-based; 0=Random)")
    ap.add_argument("--dry-run-civ", type=int, metavar="N",
                    help="Select civ at index N, capture, reset (no PLAY)")
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
    if args.map_picker:
        return cmd_map_picker(coords)
    if args.select_civ_by_idx is not None:
        print(f"Selecting civ_index {args.select_civ_by_idx}…")
        set_civ_by_index(coords, args.select_civ_by_idx)
        p = ARTIFACT_DIR / f"after_select_idx{args.select_civ_by_idx:02d}.png"
        screenshot(p)
        print(f"saved: {p}")
        return 0
    if args.dry_run_civ is not None:
        return cmd_full_run_dry(coords, args.dry_run_civ)

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
