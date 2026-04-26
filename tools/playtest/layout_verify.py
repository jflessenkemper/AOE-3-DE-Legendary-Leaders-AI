"""Compose expectations + minimap analysis into a per-civ verdict.

Usage (one civ, one screenshot):
    python3 -m tools.playtest.layout_verify \\
        --civ British \\
        --screenshot ~/shots/british_8min.png \\
        --team blue

Verdict rule:

  *  We compute the angular delta between the player's building
     centroid bearing and the minimap's water-vector bearing.
  *  If the civ's `water_bias` says +1 (toward water), we expect that
     delta to be small (<= 60° default tolerance).
  *  If `water_bias` is -1 (inland), we expect the delta to be large
     (>= 120°).
  *  If `water_bias` is 0, we report the observation but don't flag.

Confidence and pixel counts are surfaced so a low-conf reading is
flagged as `INCONCLUSIVE` instead of a hard PASS/FAIL.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.playtest.expectations import CivExpectation, load_expectations  # noqa: E402
from tools.playtest.minimap import (  # noqa: E402
    DEFAULT_MINIMAP_RECT_1080P,
    MinimapReading,
    analyze_minimap,
    parse_rect,
)


WATER_TOLERANCE_DEG = 60.0       # PASS if delta <= this when water_bias=+1
INLAND_TOLERANCE_DEG = 120.0     # PASS if delta >= this when water_bias=-1
MIN_PLAYER_PIXELS = 30           # below this we mark INCONCLUSIVE
MIN_WATER_PIXELS = 30


@dataclass
class Verdict:
    civ_id: str
    label: str
    status: str  # "PASS" | "FAIL" | "INCONCLUSIVE"
    reason: str
    delta_deg: float | None
    expectation: CivExpectation
    reading: MinimapReading

    def line(self) -> str:
        delta = f"Δ={self.delta_deg:5.1f}°" if self.delta_deg is not None else "Δ=  n/a"
        return f"  [{self.status:^12}] {self.label:<28}  {delta}  {self.reason}"


def _angular_delta(a: float, b: float) -> float:
    """Smallest unsigned angular distance in degrees (0..180)."""
    return abs(((a - b + 180) % 360) - 180)


def verify(
    expectation: CivExpectation,
    reading: MinimapReading,
    *,
    water_tol: float = WATER_TOLERANCE_DEG,
    inland_tol: float = INLAND_TOLERANCE_DEG,
) -> Verdict:
    if reading.player_pixel_count < MIN_PLAYER_PIXELS:
        return Verdict(
            civ_id=expectation.civ_id,
            label=expectation.label,
            status="INCONCLUSIVE",
            reason=(
                f"only {reading.player_pixel_count} player-color pixels "
                f"(min {MIN_PLAYER_PIXELS}). "
                "Wrong --team, wrong --minimap rect, or screenshot too early?"
            ),
            delta_deg=None,
            expectation=expectation,
            reading=reading,
        )
    if reading.water_pixel_count < MIN_WATER_PIXELS:
        # No water on the map → only outward/inward heading matters; we
        # can't talk about water bias at all.
        return Verdict(
            civ_id=expectation.civ_id,
            label=expectation.label,
            status="INCONCLUSIVE",
            reason=(
                f"minimap shows almost no water ({reading.water_pixel_count} px) — "
                "can't evaluate terrain bias on a landlocked map"
            ),
            delta_deg=None,
            expectation=expectation,
            reading=reading,
        )

    if reading.player_bearing is None or reading.water_bearing is None:
        return Verdict(
            civ_id=expectation.civ_id,
            label=expectation.label,
            status="INCONCLUSIVE",
            reason="centroid undefined (degenerate cluster)",
            delta_deg=None,
            expectation=expectation,
            reading=reading,
        )

    delta = _angular_delta(reading.player_bearing, reading.water_bearing)

    if expectation.water_bias > 0:
        if delta <= water_tol:
            return Verdict(
                civ_id=expectation.civ_id,
                label=expectation.label,
                status="PASS",
                reason=(
                    f"buildings cluster toward water (Δ {delta:.1f}° ≤ {water_tol:.0f}°), "
                    f"matches {expectation.terrain_primary.replace('cLLTerrain', '')} bias"
                ),
                delta_deg=delta,
                expectation=expectation,
                reading=reading,
            )
        return Verdict(
            civ_id=expectation.civ_id,
            label=expectation.label,
            status="FAIL",
            reason=(
                f"expected toward-water bias but Δ {delta:.1f}° > {water_tol:.0f}° "
                f"(player @ {reading.player_bearing:.0f}°, water @ {reading.water_bearing:.0f}°)"
            ),
            delta_deg=delta,
            expectation=expectation,
            reading=reading,
        )

    if expectation.water_bias < 0:
        if delta >= inland_tol:
            return Verdict(
                civ_id=expectation.civ_id,
                label=expectation.label,
                status="PASS",
                reason=(
                    f"buildings cluster inland (Δ {delta:.1f}° ≥ {inland_tol:.0f}°), "
                    f"matches {expectation.terrain_primary.replace('cLLTerrain', '')} bias"
                ),
                delta_deg=delta,
                expectation=expectation,
                reading=reading,
            )
        return Verdict(
            civ_id=expectation.civ_id,
            label=expectation.label,
            status="FAIL",
            reason=(
                f"expected inland bias but Δ {delta:.1f}° < {inland_tol:.0f}° "
                f"(player @ {reading.player_bearing:.0f}°, water @ {reading.water_bearing:.0f}°)"
            ),
            delta_deg=delta,
            expectation=expectation,
            reading=reading,
        )

    # Neutral water-bias civ — just observe, don't grade.
    return Verdict(
        civ_id=expectation.civ_id,
        label=expectation.label,
        status="PASS",
        reason=(
            f"neutral terrain bias; observed Δ {delta:.1f}° (informational only)"
        ),
        delta_deg=delta,
        expectation=expectation,
        reading=reading,
    )


def _resolve_civ(label: str) -> CivExpectation:
    target = label.lower()
    for e in load_expectations():
        if e.civ_id.lower() == target or e.label.lower() == target:
            return e
    # Try prefix match.
    matches = [e for e in load_expectations() if e.label.lower().startswith(target)]
    if len(matches) == 1:
        return matches[0]
    raise SystemExit(f"no civ matched '{label}'")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--civ", required=True, help="civ id or label")
    ap.add_argument("--screenshot", required=True, type=Path, help="full-screen PNG")
    ap.add_argument("--team", default="blue", help="player's team color (default: blue)")
    ap.add_argument(
        "--minimap",
        type=parse_rect,
        default=None,
        help="LEFT,TOP,RIGHT,BOTTOM rect of minimap; default = 1080p preset",
    )
    ap.add_argument("--water-tol", type=float, default=WATER_TOLERANCE_DEG)
    ap.add_argument("--inland-tol", type=float, default=INLAND_TOLERANCE_DEG)
    args = ap.parse_args()

    if not args.screenshot.exists():
        print(f"screenshot not found: {args.screenshot}", file=sys.stderr)
        return 2

    expectation = _resolve_civ(args.civ)
    rect = args.minimap or DEFAULT_MINIMAP_RECT_1080P
    reading = analyze_minimap(args.screenshot, team=args.team, rect=rect)

    verdict = verify(expectation, reading, water_tol=args.water_tol, inland_tol=args.inland_tol)

    print(f"== {expectation.label} ({expectation.civ_id}) ==")
    print(f"  expected: terrain={expectation.terrain_primary} heading={expectation.heading} "
          f"water_bias={expectation.water_bias:+d}")
    print(f"  observed: {reading.summary()}")
    print(verdict.line())

    if verdict.status == "FAIL":
        return 1
    if verdict.status == "INCONCLUSIVE":
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
