"""Tests for tools.playtest.replay_probes — runtime probe validator."""
from __future__ import annotations

import unittest
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.playtest.expectations import load_expectations
from tools.playtest.replay_probes import parse_probes, validate


def _probe(t: int, p: int, civ: str, ldr: str, tag: str, tail: str = "") -> str:
    return f"[LLP v=2 t={t} p={p} civ={civ} ldr={ldr} tag={tag}] {tail}"


class TestProbeParsing(unittest.TestCase):
    def test_parses_atomic_kv_pairs(self) -> None:
        line = _probe(120, 2, "British", "wellington",
                      "meta.buildstyle",
                      "style=ManorBoom walls=1 terrain_primary=cLLTerrainCoast")
        records = parse_probes(line.encode())
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r.player, 2)
        self.assertEqual(r.civ, "British")
        self.assertEqual(r.tag, "meta.buildstyle")
        self.assertEqual(r.fields["walls"], "1")
        self.assertEqual(r.fields["terrain_primary"], "cLLTerrainCoast")

    def test_handles_binary_noise_around_probes(self) -> None:
        # .age3Yrec has binary garbage between chat strings; the regex
        # must still extract LLP lines from inside that.
        blob = (
            b"\x00\x10\xfe junk header bytes "
            + _probe(60, 1, "British", "wellington", "meta.leader_assigned",
                     "civ_id=22 civ_name=British leader=wellington chatset=wellington").encode()
            + b"\xab\xcd more binary "
            + _probe(120, 1, "British", "wellington", "meta.buildstyle",
                     "style=ManorBoom walls=1 terrain_primary=cLLTerrainCoast "
                     "terrain_secondary=cLLTerrainPlain terrain_bias=0.55 "
                     "heading=cLLHeadingAlongCoast heading_bias=0.45 civic_anchor=false").encode()
            + b"\x00\x00 trailing"
        )
        records = parse_probes(blob)
        self.assertEqual(len(records), 2)
        tags = {r.tag for r in records}
        self.assertEqual(tags, {"meta.leader_assigned", "meta.buildstyle"})


class TestValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.expectations = {e.label: e for e in load_expectations()}
        self.british = self.expectations["British"]

    def _good_pair(self, pid: int, exp) -> str:
        return "\n".join([
            _probe(60, pid, exp.label, exp.leader_key, "meta.leader_assigned",
                   f"civ_id=0 civ_name={exp.label} leader={exp.leader_key} chatset={exp.leader_key}"),
            _probe(120, pid, exp.label, exp.leader_key, "meta.buildstyle",
                   f"style=Test walls=1 "
                   f"terrain_primary={exp.terrain_primary} "
                   f"terrain_secondary={exp.terrain_secondary} "
                   f"terrain_bias={exp.terrain_strength} "
                   f"heading={exp.heading} "
                   f"heading_bias={exp.heading_strength} "
                   f"civic_anchor=false"),
        ])

    def test_matching_probes_pass(self) -> None:
        text = self._good_pair(1, self.british)
        issues, summary = validate(parse_probes(text.encode()))
        self.assertEqual(issues, [], f"unexpected issues: {issues}")
        self.assertEqual(len(summary), 1)

    def test_leader_mismatch_flagged(self) -> None:
        text = self._good_pair(1, self.british).replace("leader=wellington", "leader=napoleon")
        issues, _ = validate(parse_probes(text.encode()))
        self.assertTrue(any("leader_key mismatch" in i for i in issues), issues)

    def test_unassigned_fallback_flagged(self) -> None:
        text = self._good_pair(1, self.british).replace(
            "leader=wellington", "leader=unassigned-British", 1
        )
        issues, _ = validate(parse_probes(text.encode()))
        self.assertTrue(any("unassigned fallback" in i for i in issues), issues)

    def test_terrain_bias_drift_flagged(self) -> None:
        text = self._good_pair(1, self.british).replace(
            f"terrain_bias={self.british.terrain_strength}",
            "terrain_bias=0.99",
        )
        issues, _ = validate(parse_probes(text.encode()))
        self.assertTrue(any("terrain_bias mismatch" in i for i in issues), issues)

    def test_missing_buildstyle_probe_flagged(self) -> None:
        text = _probe(60, 1, "British", "wellington", "meta.leader_assigned",
                      "civ_id=0 civ_name=British leader=wellington chatset=wellington")
        issues, _ = validate(parse_probes(text.encode()))
        self.assertTrue(any("missing meta.buildstyle" in i for i in issues), issues)

    def test_no_probes_at_all_returns_helpful_error(self) -> None:
        issues, _ = validate(parse_probes(b"no probes in this file"))
        self.assertTrue(any("no [LLP v=2] probes" in i for i in issues), issues)


if __name__ == "__main__":
    unittest.main()
