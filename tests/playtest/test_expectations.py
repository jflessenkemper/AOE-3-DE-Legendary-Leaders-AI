"""Tests for tools.playtest.expectations."""
from __future__ import annotations

import unittest

from tools.playtest.expectations import (
    CIV_LABELS,
    CivExpectation,
    HEADING_AXIS,
    TERRAIN_WATER_BIAS,
    load_expectations,
)


class WaterBiasTests(unittest.TestCase):
    def _mk(self, primary: str, secondary: str) -> CivExpectation:
        return CivExpectation(
            civ_id="cCivTest",
            label="Test",
            leader_key="test",
            deck_name="Test",
            terrain_primary=primary,
            terrain_secondary=secondary,
            terrain_strength=0.5,
            heading="cLLHeadingAny",
            heading_strength=0.0,
        )

    def test_double_coast_is_strongly_water(self):
        self.assertEqual(self._mk("cLLTerrainCoast", "cLLTerrainRiver").water_bias, +1)

    def test_double_inland_is_strongly_inland(self):
        self.assertEqual(self._mk("cLLTerrainHighland", "cLLTerrainDesertOasis").water_bias, -1)

    def test_primary_outweighs_secondary(self):
        # Plain (0) primary + River (+1) secondary → +1 (river still pulls)
        self.assertEqual(self._mk("cLLTerrainPlain", "cLLTerrainRiver").water_bias, +1)
        # Highland (-1) primary + River (+1) secondary → 2*(-1)+1 = -1 → -1
        self.assertEqual(self._mk("cLLTerrainHighland", "cLLTerrainRiver").water_bias, -1)

    def test_neutral_when_balanced_to_zero(self):
        # Plain (0) + Plain (0) = 0
        self.assertEqual(self._mk("cLLTerrainPlain", "cLLTerrainPlain").water_bias, 0)


class HeadingAxisTests(unittest.TestCase):
    def test_known_axes(self):
        self.assertEqual(HEADING_AXIS["cLLHeadingAlongCoast"], "tangent")
        self.assertEqual(HEADING_AXIS["cLLHeadingFrontierPush"], "outward")
        self.assertEqual(HEADING_AXIS["cLLHeadingDefensive"], "inward")

    def test_every_known_heading_maps_to_a_known_axis(self):
        for axis in HEADING_AXIS.values():
            self.assertIn(axis, {"tangent", "outward", "inward", "none"})


class LoadExpectationsIntegrationTests(unittest.TestCase):
    """Real-source-tree integration: every civ in the static validator
    list must round-trip through expectations."""

    def setUp(self):
        self.exps = load_expectations()
        self.by_id = {e.civ_id: e for e in self.exps}

    def test_loads_48_civs(self):
        self.assertEqual(len(self.exps), 48)

    def test_every_civ_has_a_label(self):
        for e in self.exps:
            self.assertIn(e.civ_id, CIV_LABELS, f"missing label for {e.civ_id}")
            self.assertEqual(e.label, CIV_LABELS[e.civ_id])

    def test_strengths_in_range(self):
        for e in self.exps:
            self.assertGreaterEqual(e.terrain_strength, 0.0)
            self.assertLessEqual(e.terrain_strength, 1.0)
            self.assertGreaterEqual(e.heading_strength, 0.0)
            self.assertLessEqual(e.heading_strength, 1.0)

    def test_terrain_constants_are_known(self):
        for e in self.exps:
            self.assertIn(e.terrain_primary, TERRAIN_WATER_BIAS)
            self.assertIn(e.terrain_secondary, TERRAIN_WATER_BIAS)

    def test_heading_constants_are_known(self):
        for e in self.exps:
            self.assertIn(e.heading, HEADING_AXIS)

    def test_revolution_civs_have_country_named_decks(self):
        # All revolution civs were renamed to their country in the deck
        # rename pass; the parser must surface that.
        rvlt = [e for e in self.exps if e.is_revolution]
        self.assertEqual(len(rvlt), 26)
        for e in rvlt:
            self.assertNotIn("$$", e.deck_name, f"{e.civ_id}: deck still has $$ stringtable: {e.deck_name!r}")
            self.assertNotIn("<", e.deck_name, f"{e.civ_id}: deck unresolved: {e.deck_name!r}")

    def test_base_civs_have_a_new_world_deck(self):
        base = [e for e in self.exps if not e.is_revolution]
        self.assertEqual(len(base), 22)
        for e in base:
            self.assertEqual(e.deck_name, "A New World", f"{e.civ_id}: deck={e.deck_name!r}")


if __name__ == "__main__":
    unittest.main()
