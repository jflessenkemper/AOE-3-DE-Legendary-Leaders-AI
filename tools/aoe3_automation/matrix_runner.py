"""Fully-automated 100%-civ-coverage skirmish matrix runner.

Stitches together:
  - lobby_driver.py       — pixel-coord-driven Skirmish-lobby control
  - in_game_driver.py     — GameDriver: launch/wait/speed/resign lifecycle
  - log_capture.py        — Age3Log.txt mirror per match
  - manage_game.py        — process lifecycle / crash recovery

For every civ_idx in `picker_scroll_table.json["civ_names"]` (skipping
idx 0 = Random Personality by default) we:

  1. Verify game is alive at clean Skirmish lobby; relaunch + recover if not.
  2. Open civ picker, scroll to target row (using the empirical scroll table
     since one wheel-down ≠ one row), click civ, OK.
  3. Start Age3Log.txt mirror to artifacts/matrix/<idx>/match.log.
  4. Click PLAY.
  5. Wait for `WorldAssetPreloadingTime` (match playable).
  6. Set max speed (tick 5 = ~Fast x effective).
  7. Observe `observe_seconds` of gameplay (default 600 = ~10 min wall).
  8. Resign → confirm → return to main menu.
  9. Stop log mirror; write per-civ summary.
  10. Re-enter Skirmish lobby; reset P1 to Random Personality.

Crash recovery: if any step throws or the game exits, we call
`manage_game.cycle` (close + relaunch + main menu) and continue with the
NEXT civ. No iteration ever blocks the matrix indefinitely.

Run from gamescope-host context (game already at lobby helps but isn't
required):
    flatpak-spawn --host python3 tools/aoe3_automation/matrix_runner.py \\
        --observe-seconds 600 --start-idx 1 --end-idx 48

Use --dry-run to skip the actual PLAY (just exercises the lobby flow per civ).
Use --civs aztec_empire,spain  to run a subset by name.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# Make sibling modules importable when invoked as a script.
# in_game_driver.py imports as `tools.aoe3_automation.log_capture`, so we need
# the repo root on sys.path *before* HERE.
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import lobby_driver as lobby                                          # noqa: E402
from tools.aoe3_automation.in_game_driver import GameDriver           # noqa: E402
from tools.aoe3_automation.log_capture import (                       # noqa: E402
    start_log_tail, stop_log_tail, LogMirror, ensure_dev_mode,
)

ARTIFACT_DIR = HERE / "artifacts" / "matrix_runner"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

MANAGE_GAME = HERE / "manage_game.py"


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------


def slugify(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()


def game_is_running() -> bool:
    rc = subprocess.run(
        [sys.executable, str(MANAGE_GAME), "status"],
        capture_output=True, text=True,
    ).returncode
    return rc == 0


def cycle_game() -> bool:
    """Close + relaunch via manage_game cycle; returns True on success."""
    rc = subprocess.run(
        [sys.executable, str(MANAGE_GAME), "cycle", "--timeout", "240"],
        capture_output=False,
    ).returncode
    return rc == 0


def ensure_lobby(coords: dict, *, attempts: int = 3) -> bool:
    """Make best-effort attempt to land at a clean Skirmish lobby.

    Strategy (each attempt):
      1. If clean lobby → done.
      2. Try cancelling any open civ-picker.
      3. If the game is in a match (HUD detected by GameDriver) → resign.
      4. Click Skirmish from main menu.
    Last resort: cycle (close + relaunch) the game.
    """
    for i in range(attempts):
        try:
            if lobby.is_clean_lobby(coords):
                return True
        except Exception:
            pass
        try:
            lobby.cancel_civ_picker(coords)
        except Exception:
            pass
        # In-match recovery: if we're inside a skirmish, resign first.
        if i == 0:
            try:
                d = GameDriver(art_dir=ARTIFACT_DIR / "_recovery")
                d.resign()
                time.sleep(2.0)
            except Exception:
                pass
        try:
            lobby.xdo("key Escape")
            time.sleep(0.6)
        except Exception:
            pass
        try:
            sk = coords["main_menu"]["skirmish_button"]
            lobby.click(sk[0], sk[1])
            time.sleep(2.5)
        except Exception:
            pass
        try:
            if lobby.is_clean_lobby(coords):
                return True
        except Exception:
            pass
    # Last resort: cycle the game
    print("  ensure_lobby: attempting cycle_game last-resort recovery")
    if cycle_game():
        time.sleep(3.0)
        try:
            sk = coords["main_menu"]["skirmish_button"]
            lobby.click(sk[0], sk[1])
            time.sleep(3.0)
        except Exception:
            pass
        try:
            return lobby.is_clean_lobby(coords)
        except Exception:
            return False
    return False


# ---------------------------------------------------------------------------
# Per-civ run
# ---------------------------------------------------------------------------


@dataclass
class CivResult:
    civ_idx: int
    civ_name: str
    started_at: str
    ended_at: str = ""
    duration_s: float = 0.0
    selected_civ: bool = False
    started_match: bool = False
    reached_in_game: bool = False
    observed_s: float = 0.0
    resigned: bool = False
    artifact_dir: str = ""
    log_lines: int = 0
    probe_count: int = 0
    error: str = ""
    notes: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return self.resigned and not self.error


def run_one_civ(
    coords: dict,
    civ_idx: int,
    civ_name: str,
    *,
    observe_seconds: int,
    in_game_timeout: int,
    speed_tick: int,
    dry_run: bool,
) -> CivResult:
    art = ARTIFACT_DIR / f"{civ_idx:02d}_{slugify(civ_name)}"
    art.mkdir(parents=True, exist_ok=True)
    res = CivResult(
        civ_idx=civ_idx,
        civ_name=civ_name,
        started_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        artifact_dir=str(art),
    )
    t0 = time.monotonic()
    mirror: LogMirror | None = None
    log_path = art / "match.log"
    driver = GameDriver(art_dir=art)

    def _annotate(msg: str) -> None:
        print(f"  [civ {civ_idx:02d} {civ_name}] {msg}")
        res.notes.append(msg)

    try:
        # 1. Make sure we're at clean lobby
        if not ensure_lobby(coords):
            raise RuntimeError("could not reach clean lobby state")

        # 2. Select civ
        _annotate(f"selecting civ_idx={civ_idx}")
        lobby.set_civ_by_index(coords, civ_idx)
        # Snapshot post-select state so we can manually verify the right civ
        # was picked (the lobby UI shows the civ portrait).
        try:
            lobby.screenshot(art / "01_after_select.png")
        except Exception as e:
            _annotate(f"screenshot warn: {e}")
        res.selected_civ = True

        if dry_run:
            _annotate("dry-run: skipping PLAY; resetting to Random")
            try:
                lobby.reset_p1_to_random(coords)
            except Exception as e:
                _annotate(f"reset warn: {e}")
            res.duration_s = time.monotonic() - t0
            res.ended_at = time.strftime("%Y-%m-%dT%H:%M:%S")
            return res

        # 3. Start log mirror BEFORE click_play so we capture the boot probes.
        try:
            ensure_dev_mode()
        except Exception as e:
            _annotate(f"ensure_dev_mode warn: {e}")
        mirror = start_log_tail(log_path)

        # 4. PLAY
        _annotate("clicking PLAY")
        lobby.click_play(coords)
        res.started_match = True

        # 5. Wait for in-game
        ok = driver.wait_for_in_game(timeout=in_game_timeout, log_mirror=mirror)
        if not ok:
            raise RuntimeError(
                f"timed out ({in_game_timeout}s) waiting for "
                "WorldAssetPreloadingTime — match never went playable"
            )
        res.reached_in_game = True
        _annotate("in-game; setting speed")

        # 6. Set max speed
        try:
            driver.set_speed(speed_tick)
        except Exception as e:
            _annotate(f"set_speed warn: {e}")

        # 7. Observe
        obs_t0 = time.monotonic()
        try:
            driver.observe(wall_seconds=observe_seconds)
        except Exception as e:
            _annotate(f"observe interrupted: {e}")
        res.observed_s = time.monotonic() - obs_t0

        # 8. Resign
        _annotate("resigning")
        try:
            driver.resign()
            res.resigned = True
        except Exception as e:
            _annotate(f"resign error: {e}")

    except Exception as e:
        res.error = f"{type(e).__name__}: {e}"
        _annotate(f"ERROR: {res.error}")
        traceback.print_exc()
    finally:
        # 9. Close mirror, capture log size + probe count
        if mirror is not None:
            try:
                content = stop_log_tail(mirror)
                res.log_lines = content.count("\n")
                res.probe_count = mirror.current_probe_count()
            except Exception as e:
                _annotate(f"stop_log_tail warn: {e}")
        res.duration_s = time.monotonic() - t0
        res.ended_at = time.strftime("%Y-%m-%dT%H:%M:%S")

    # 10. Recovery for the next iteration: ensure we're back at clean lobby.
    # If resign succeeded we're at main menu; click Skirmish to re-enter.
    if res.resigned:
        try:
            sk = coords["main_menu"]["skirmish_button"]
            lobby.click(sk[0], sk[1])
            time.sleep(2.5)
        except Exception:
            pass
    # Always reset to Random Personality so the next iteration starts clean.
    try:
        if lobby.is_clean_lobby(coords):
            lobby.reset_p1_to_random(coords)
    except Exception as e:
        _annotate(f"post-run reset warn: {e}")

    # Save per-civ JSON snapshot
    try:
        (art / "result.json").write_text(json.dumps(asdict(res), indent=2))
    except Exception:
        pass

    return res


# ---------------------------------------------------------------------------
# Matrix entrypoint
# ---------------------------------------------------------------------------


def run_matrix(
    *,
    observe_seconds: int,
    in_game_timeout: int,
    speed_tick: int,
    start_idx: int,
    end_idx: int,
    civ_names: list[str] | None,
    dry_run: bool,
    abort_on_crash: bool,
) -> int:
    coords = lobby.load_coords()
    table = lobby.load_scroll_table()
    civs: list[str] = list(table["civ_names"])

    # Build the iteration order
    if civ_names:
        wanted: list[tuple[int, str]] = []
        slug_lookup = {slugify(n): (i, n) for i, n in enumerate(civs)}
        for raw in civ_names:
            key = slugify(raw)
            if key not in slug_lookup:
                # try contains-match
                hits = [(i, n) for i, n in enumerate(civs) if key in slugify(n)]
                if not hits:
                    print(f"WARN: unknown civ {raw!r}; skipping")
                    continue
                wanted.append(hits[0])
            else:
                wanted.append(slug_lookup[key])
        iteration = wanted
    else:
        lo, hi = max(start_idx, 0), min(end_idx, len(civs) - 1)
        iteration = [(i, civs[i]) for i in range(lo, hi + 1)]

    print(f"Matrix run: {len(iteration)} civ(s)")
    for i, (idx, nm) in enumerate(iteration):
        print(f"  {i+1:2d}/{len(iteration)}: idx={idx:02d} {nm}")
    print()

    results: list[CivResult] = []
    run_started = time.strftime("%Y-%m-%dT%H:%M:%S")

    for i, (civ_idx, civ_name) in enumerate(iteration):
        print(f"=== [{i+1}/{len(iteration)}] civ_idx={civ_idx} {civ_name} ===")

        # Make sure the game is even up
        if not game_is_running():
            print("  game not running — cycling")
            if not cycle_game():
                print("  ERROR: cycle_game failed; aborting matrix")
                if abort_on_crash:
                    break

        try:
            res = run_one_civ(
                coords, civ_idx, civ_name,
                observe_seconds=observe_seconds,
                in_game_timeout=in_game_timeout,
                speed_tick=speed_tick,
                dry_run=dry_run,
            )
        except Exception as e:
            print(f"  unhandled iter error: {e}")
            res = CivResult(
                civ_idx=civ_idx, civ_name=civ_name,
                started_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                error=f"unhandled: {e}",
            )
        results.append(res)
        ok = "OK" if res.ok() else ("DRY" if dry_run and res.selected_civ else "FAIL")
        print(f"  → {ok}  duration={res.duration_s:.0f}s  "
              f"in_game={res.reached_in_game}  resigned={res.resigned}  "
              f"probes={res.probe_count}  err={res.error or '-'}")

        # If something crashed the game, cycle before next iter
        if not game_is_running():
            print("  game appears dead — cycling for next iter")
            if not cycle_game():
                print("  ERROR: cycle_game failed mid-matrix")
                if abort_on_crash:
                    break

    # Summary report
    report_path = ARTIFACT_DIR / "matrix_report.json"
    md_path = ARTIFACT_DIR / "matrix_report.md"
    summary = {
        "started_at": run_started,
        "ended_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "observe_seconds": observe_seconds,
        "speed_tick": speed_tick,
        "dry_run": dry_run,
        "results": [asdict(r) for r in results],
        "totals": {
            "attempted": len(results),
            "selected_civ": sum(r.selected_civ for r in results),
            "reached_in_game": sum(r.reached_in_game for r in results),
            "resigned": sum(r.resigned for r in results),
            "errors": sum(bool(r.error) for r in results),
        },
    }
    report_path.write_text(json.dumps(summary, indent=2))

    md_lines = [
        f"# Matrix run — {run_started}",
        "",
        f"- Civs attempted: **{len(results)}**",
        f"- Reached in-game: **{summary['totals']['reached_in_game']}**",
        f"- Resigned cleanly: **{summary['totals']['resigned']}**",
        f"- Errors: **{summary['totals']['errors']}**",
        f"- Observe seconds per civ: {observe_seconds}",
        f"- Speed tick: {speed_tick}",
        f"- Dry run: {dry_run}",
        "",
        "| idx | civ | sel | in-game | resign | obs(s) | probes | err |",
        "|-----|-----|-----|---------|--------|--------|--------|-----|",
    ]
    for r in results:
        md_lines.append(
            f"| {r.civ_idx} | {r.civ_name} | "
            f"{'✓' if r.selected_civ else '✗'} | "
            f"{'✓' if r.reached_in_game else '✗'} | "
            f"{'✓' if r.resigned else '✗'} | "
            f"{r.observed_s:.0f} | {r.probe_count} | "
            f"{(r.error or '-')[:60]} |"
        )
    md_path.write_text("\n".join(md_lines) + "\n")
    print(f"\nWrote: {report_path}\nWrote: {md_path}")
    return 0 if all(r.ok() or (dry_run and r.selected_civ) for r in results) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--observe-seconds", type=int, default=600,
                    help="Wall-clock seconds to observe per match before resigning")
    ap.add_argument("--in-game-timeout", type=int, default=240,
                    help="Max seconds to wait for WorldAssetPreloadingTime after PLAY")
    ap.add_argument("--speed-tick", type=int, default=5,
                    help="Game-speed bar tick (1..5; 5=fastest)")
    ap.add_argument("--start-idx", type=int, default=1,
                    help="First civ_idx to run (skip 0=Random by default)")
    ap.add_argument("--end-idx", type=int, default=48,
                    help="Last civ_idx (inclusive)")
    ap.add_argument("--civs", default="",
                    help="Comma-separated civ-name slugs to run (overrides idx range)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Select civ + screenshot only; no PLAY, no observe, no resign")
    ap.add_argument("--abort-on-crash", action="store_true",
                    help="Stop matrix immediately on cycle_game failure")
    args = ap.parse_args()

    civ_names = [c.strip() for c in args.civs.split(",") if c.strip()]
    return run_matrix(
        observe_seconds=args.observe_seconds,
        in_game_timeout=args.in_game_timeout,
        speed_tick=args.speed_tick,
        start_idx=args.start_idx,
        end_idx=args.end_idx,
        civ_names=civ_names or None,
        dry_run=args.dry_run,
        abort_on_crash=args.abort_on_crash,
    )


if __name__ == "__main__":
    sys.exit(main())
