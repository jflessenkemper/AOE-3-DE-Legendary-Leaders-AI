"""Minimap analysis for layout spot-checks.

Given a full-screen AoE3 DE screenshot, this module:

  1. Crops to the minimap rectangle (configurable; default = bottom-left
     ~290×290 region for 1920×1080, with a `--minimap` flag override).
  2. Segments three classes of pixels:
        * player buildings  — high-saturation pixels in the player's
          team color (defaults to Blue = team 1).
        * water             — medium/dark blue pixels that aren't the
          player color.
        * land              — everything else.
  3. Computes a *centroid bearing* for each class relative to the
     minimap center (which is approximately where the AI's starting TC
     sits at game start).

The bearing is in standard nav degrees:
    0°   = north (top of minimap)
    90°  = east  (right)
    180° = south (bottom)
    270° = west  (left)

Output is a `MinimapReading` dataclass that the layout verifier then
compares against a `CivExpectation`.

The implementation is Pillow-only; no OpenCV dependency.
"""
from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

# Default minimap rect (left, top, right, bottom) for 1920×1080 AoE3 DE.
# Calibrate at runtime by passing `--minimap LEFT,TOP,RIGHT,BOTTOM`.
DEFAULT_MINIMAP_RECT_1080P = (24, 760, 314, 1050)

# Player team colors in the AoE3 DE palette (rough HSV centers).
# Hue is in [0, 360); sat/val in [0, 1]. Tolerance widths are wide
# enough to absorb the minimap's slightly desaturated rendering.
TEAM_COLORS = {
    "blue":   {"hue": 220, "hue_tol": 18, "sat_min": 0.45, "val_min": 0.35},
    "red":    {"hue":   0, "hue_tol": 14, "sat_min": 0.50, "val_min": 0.35},
    "yellow": {"hue":  55, "hue_tol": 14, "sat_min": 0.55, "val_min": 0.55},
    "green":  {"hue": 120, "hue_tol": 16, "sat_min": 0.45, "val_min": 0.35},
    "cyan":   {"hue": 185, "hue_tol": 14, "sat_min": 0.40, "val_min": 0.45},
    "purple": {"hue": 285, "hue_tol": 16, "sat_min": 0.40, "val_min": 0.35},
    "orange": {"hue":  25, "hue_tol": 12, "sat_min": 0.55, "val_min": 0.55},
    "pink":   {"hue": 320, "hue_tol": 14, "sat_min": 0.40, "val_min": 0.55},
}

# Water in the minimap is medium-blue, low-to-medium saturation, and
# darker than player-blue buildings. We segment it explicitly so we can
# subtract it from the player-blue mask when the player is on team blue.
WATER_BAND = {"hue": 215, "hue_tol": 30, "sat_min": 0.20, "sat_max": 0.65, "val_max": 0.50}


@dataclass
class MinimapReading:
    rect: tuple[int, int, int, int]
    width: int
    height: int
    player_pixel_count: int
    water_pixel_count: int
    land_pixel_count: int
    # All bearings in degrees, 0 = north (toward top of minimap).
    # `None` if that class had no pixels.
    player_bearing: float | None
    player_distance: float  # 0..1, normalized by half the minimap diagonal
    water_bearing: float | None
    water_distance: float
    confidence: float  # 0..1, fraction of player-color pixels not co-occurring with water-band

    def summary(self) -> str:
        def fmt(b: float | None) -> str:
            return f"{b:6.1f}°" if b is not None else "  (none)"
        return (
            f"player={self.player_pixel_count:>5}px @ {fmt(self.player_bearing)} "
            f"r={self.player_distance:.2f}  "
            f"water={self.water_pixel_count:>5}px @ {fmt(self.water_bearing)} "
            f"r={self.water_distance:.2f}  "
            f"conf={self.confidence:.2f}"
        )


# --- helpers -----------------------------------------------------------------


def _rgb_to_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Return (hue_deg, sat, val) in (deg, [0,1], [0,1])."""
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return h * 360.0, s, v


def _in_hue_band(hue: float, center: float, tol: float) -> bool:
    diff = abs(((hue - center + 180) % 360) - 180)
    return diff <= tol


def _classify(rgb: tuple[int, int, int], team: str) -> str:
    h, s, v = _rgb_to_hsv(*rgb)
    if v < 0.06:  # near-black background, ignore
        return "bg"
    spec = TEAM_COLORS[team]
    is_team = (
        _in_hue_band(h, spec["hue"], spec["hue_tol"])
        and s >= spec["sat_min"]
        and v >= spec["val_min"]
    )
    is_water = (
        _in_hue_band(h, WATER_BAND["hue"], WATER_BAND["hue_tol"])
        and WATER_BAND["sat_min"] <= s <= WATER_BAND["sat_max"]
        and v <= WATER_BAND["val_max"]
    )
    if is_team and not is_water:
        return "player"
    if is_water and not is_team:
        return "water"
    if is_team and is_water:
        # Ambiguous (e.g. player on Blue team next to water). Bias to
        # whichever has higher saturation — buildings are saturated.
        return "player" if s >= 0.55 else "water"
    return "land"


def _bearing(dx: float, dy: float) -> float | None:
    """Return bearing in degrees, 0 = north (negative y)."""
    if dx == 0 and dy == 0:
        return None
    # Image coords: +y is down. Map to nav: 0=N, 90=E, 180=S, 270=W.
    angle = math.degrees(math.atan2(dx, -dy))
    return angle % 360.0


# --- public API --------------------------------------------------------------


def crop_minimap(image: Image.Image, rect: tuple[int, int, int, int] | None = None) -> Image.Image:
    if rect is None:
        rect = DEFAULT_MINIMAP_RECT_1080P
    return image.crop(rect)


def analyze_minimap(
    image_path: Path,
    team: str = "blue",
    rect: tuple[int, int, int, int] | None = None,
) -> MinimapReading:
    if team not in TEAM_COLORS:
        raise ValueError(f"unknown team '{team}'; pick one of {sorted(TEAM_COLORS)}")

    full = Image.open(image_path).convert("RGB")
    if rect is None:
        rect = DEFAULT_MINIMAP_RECT_1080P
    mm = full.crop(rect)
    width, height = mm.size
    pixels = mm.load()
    cx, cy = width / 2, height / 2
    half_diag = math.hypot(cx, cy)

    player_count = 0
    water_count = 0
    land_count = 0
    player_dx = 0.0
    player_dy = 0.0
    water_dx = 0.0
    water_dy = 0.0
    overlap_count = 0  # pixels where player+water both flagged

    for y in range(height):
        for x in range(width):
            rgb = pixels[x, y]
            klass = _classify(rgb, team)
            if klass == "player":
                player_count += 1
                player_dx += x - cx
                player_dy += y - cy
            elif klass == "water":
                water_count += 1
                water_dx += x - cx
                water_dy += y - cy
            elif klass == "land":
                land_count += 1
            # 'bg' ignored

    if player_count > 0:
        avg_dx = player_dx / player_count
        avg_dy = player_dy / player_count
        player_bearing = _bearing(avg_dx, avg_dy)
        player_distance = min(1.0, math.hypot(avg_dx, avg_dy) / half_diag)
    else:
        player_bearing = None
        player_distance = 0.0

    if water_count > 0:
        avg_dx = water_dx / water_count
        avg_dy = water_dy / water_count
        water_bearing = _bearing(avg_dx, avg_dy)
        water_distance = min(1.0, math.hypot(avg_dx, avg_dy) / half_diag)
    else:
        water_bearing = None
        water_distance = 0.0

    # Confidence: proportion of player-pixels relative to total
    # non-background pixels in the minimap. Low confidence (<0.005)
    # likely means the rect is wrong or the player is the wrong team.
    classified = player_count + water_count + land_count
    confidence = (player_count / classified) if classified else 0.0

    return MinimapReading(
        rect=rect,
        width=width,
        height=height,
        player_pixel_count=player_count,
        water_pixel_count=water_count,
        land_pixel_count=land_count,
        player_bearing=player_bearing,
        player_distance=player_distance,
        water_bearing=water_bearing,
        water_distance=water_distance,
        confidence=confidence,
    )


def parse_rect(s: str) -> tuple[int, int, int, int]:
    parts = [int(p) for p in s.split(",")]
    if len(parts) != 4:
        raise ValueError("rect must be LEFT,TOP,RIGHT,BOTTOM")
    return tuple(parts)  # type: ignore[return-value]


__all__ = [
    "MinimapReading",
    "TEAM_COLORS",
    "DEFAULT_MINIMAP_RECT_1080P",
    "analyze_minimap",
    "crop_minimap",
    "parse_rect",
]
