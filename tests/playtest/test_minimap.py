"""Tests for tools.playtest.minimap.

We synthesize tiny minimap images with known player/water layouts and
assert the bearing math points where it should.
"""
from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.playtest.minimap import analyze_minimap


# Reference colors that fall inside the analyzer's HSV bands.
PLAYER_BLUE = (40, 90, 230)    # bright saturated blue → "player" on team blue
WATER_BLUE = (70, 85, 110)     # darker, low-sat blue → "water" (clear of player band)
LAND_GREEN = (70, 110, 50)     # mid green → "land"
BG_BLACK = (0, 0, 0)


def _make_minimap(
    size: int,
    player_pixels: list[tuple[int, int]],
    water_pixels: list[tuple[int, int]],
    land_color: tuple[int, int, int] = LAND_GREEN,
    bg: tuple[int, int, int] = LAND_GREEN,
) -> Image.Image:
    img = Image.new("RGB", (size, size), bg)
    px = img.load()
    for x, y in water_pixels:
        if 0 <= x < size and 0 <= y < size:
            px[x, y] = WATER_BLUE
    for x, y in player_pixels:
        if 0 <= x < size and 0 <= y < size:
            px[x, y] = PLAYER_BLUE
    return img


def _save(img: Image.Image, path: Path) -> None:
    img.save(path, "PNG")


class MinimapBearingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.size = 80

    def tearDown(self):
        self._tmp.cleanup()

    def _read(self, img: Image.Image, team: str = "blue"):
        path = self.tmp / "minimap.png"
        _save(img, path)
        return analyze_minimap(path, team=team, rect=(0, 0, self.size, self.size))

    def test_player_north_of_center(self):
        # Player buildings at top of minimap → bearing ≈ 0° (north).
        img = _make_minimap(
            self.size,
            player_pixels=[(x, y) for x in range(35, 45) for y in range(5, 15)],
            water_pixels=[(x, y) for x in range(35, 45) for y in range(65, 75)],
        )
        r = self._read(img)
        self.assertGreater(r.player_pixel_count, 50)
        self.assertGreater(r.water_pixel_count, 50)
        self.assertIsNotNone(r.player_bearing)
        # 0° ± 30° tolerance — synthetic block centered at (40,10) on
        # a 80px minimap means dy = 10 - 40 = -30 (north).
        self.assertLess(abs(((r.player_bearing - 0 + 180) % 360) - 180), 25)
        # Water should be south.
        self.assertLess(abs(((r.water_bearing - 180 + 180) % 360) - 180), 25)

    def test_player_east_of_center_water_west(self):
        img = _make_minimap(
            self.size,
            player_pixels=[(x, y) for x in range(65, 75) for y in range(35, 45)],
            water_pixels=[(x, y) for x in range(5, 15) for y in range(35, 45)],
        )
        r = self._read(img)
        # Player at east → bearing ≈ 90°.
        self.assertLess(abs(((r.player_bearing - 90 + 180) % 360) - 180), 25)
        # Water at west → bearing ≈ 270°.
        self.assertLess(abs(((r.water_bearing - 270 + 180) % 360) - 180), 25)

    def test_no_player_pixels_returns_none_bearing(self):
        img = _make_minimap(
            self.size,
            player_pixels=[],
            water_pixels=[(x, y) for x in range(0, 80) for y in range(0, 10)],
        )
        r = self._read(img)
        self.assertEqual(r.player_pixel_count, 0)
        self.assertIsNone(r.player_bearing)
        self.assertGreater(r.water_pixel_count, 100)

    def test_team_red_finds_red_pixels(self):
        # Build a minimap with bright red player blocks. Should be
        # detected when team='red'.
        img = Image.new("RGB", (self.size, self.size), LAND_GREEN)
        px = img.load()
        for x in range(35, 45):
            for y in range(5, 15):
                px[x, y] = (220, 50, 50)  # saturated red
        path = self.tmp / "red.png"
        _save(img, path)
        r = analyze_minimap(path, team="red", rect=(0, 0, self.size, self.size))
        self.assertGreater(r.player_pixel_count, 50)


class MinimapVerdictIntegrationTests(unittest.TestCase):
    """End-to-end: synthesize a minimap, route it through layout_verify
    against a real CivExpectation, expect PASS or FAIL appropriately."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.size = 80

    def tearDown(self):
        self._tmp.cleanup()

    def _make_and_read(self, player_quadrant: str, water_quadrant: str):
        from tools.playtest.minimap import analyze_minimap

        # Map quadrant → block position on an 80px minimap.
        quad_blocks = {
            "north": [(x, y) for x in range(35, 45) for y in range(5, 15)],
            "south": [(x, y) for x in range(35, 45) for y in range(65, 75)],
            "east":  [(x, y) for x in range(65, 75) for y in range(35, 45)],
            "west":  [(x, y) for x in range(5, 15) for y in range(35, 45)],
        }
        img = _make_minimap(
            self.size,
            player_pixels=quad_blocks[player_quadrant],
            water_pixels=quad_blocks[water_quadrant],
        )
        path = self.tmp / "mm.png"
        _save(img, path)
        return analyze_minimap(path, team="blue", rect=(0, 0, self.size, self.size))

    def test_coast_civ_with_buildings_toward_water_passes(self):
        from tools.playtest.expectations import CivExpectation
        from tools.playtest.layout_verify import verify
        from tools.playtest.minimap import analyze_minimap

        british = CivExpectation(
            civ_id="cCivBritish",
            label="British",
            leader_key="wellington",
            deck_name="A New World",
            terrain_primary="cLLTerrainCoast",
            terrain_secondary="cLLTerrainPlain",
            terrain_strength=0.55,
            heading="cLLHeadingAlongCoast",
            heading_strength=0.45,
        )
        # Player buildings + water both at east side but at different y
        # rows so they don't overwrite each other. Both centroids resolve
        # to ~east (≈90°) → small Δ → PASS.
        img = _make_minimap(
            self.size,
            player_pixels=[(x, y) for x in range(60, 70) for y in range(35, 45)],
            water_pixels=[(x, y) for x in range(70, 78) for y in range(35, 45)],
        )
        path = self.tmp / "coast_pass.png"
        _save(img, path)
        reading = analyze_minimap(path, team="blue", rect=(0, 0, self.size, self.size))
        v = verify(british, reading)
        self.assertEqual(v.status, "PASS", f"reason: {v.reason}")

    def test_coast_civ_with_buildings_inland_fails(self):
        from tools.playtest.expectations import CivExpectation
        from tools.playtest.layout_verify import verify

        british = CivExpectation(
            civ_id="cCivBritish",
            label="British",
            leader_key="wellington",
            deck_name="A New World",
            terrain_primary="cLLTerrainCoast",
            terrain_secondary="cLLTerrainPlain",
            terrain_strength=0.55,
            heading="cLLHeadingAlongCoast",
            heading_strength=0.45,
        )
        reading = self._make_and_read(player_quadrant="east", water_quadrant="west")
        v = verify(british, reading)
        # Δ ≈ 180° ≫ 60° → FAIL.
        self.assertEqual(v.status, "FAIL", f"reason: {v.reason}")

    def test_inland_civ_with_buildings_inland_passes(self):
        from tools.playtest.expectations import CivExpectation
        from tools.playtest.layout_verify import verify

        ethiopia = CivExpectation(
            civ_id="cCivDEEthiopians",
            label="Ethiopians",
            leader_key="menelik",
            deck_name="A New World",
            terrain_primary="cLLTerrainHighland",
            terrain_secondary="cLLTerrainRiver",
            terrain_strength=0.25,
            heading="cLLHeadingDefensive",
            heading_strength=0.0,
        )
        # Player east, water west → Δ = 180° → ≥ 120° → PASS for inland.
        reading = self._make_and_read(player_quadrant="east", water_quadrant="west")
        v = verify(ethiopia, reading)
        self.assertEqual(v.status, "PASS", f"reason: {v.reason}")


if __name__ == "__main__":
    unittest.main()
