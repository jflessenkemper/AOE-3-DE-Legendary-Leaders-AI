from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.validation.validate_homecity_cards import validate_homecity_cards


GOOD_TECHTREE = """<techtreemods>
  <tech name='RvltModCardTech'><dbid>1</dbid></tech>
  <tech name='RvltModPrereqTech'><dbid>2</dbid></tech>
</techtreemods>
"""

GOOD_HOMECITY = """<homecity>
  <cards>
    <card>
      <name>CardOne</name>
      <prereqtech>-1</prereqtech>
    </card>
    <card>
      <name>RvltModCardTech</name>
      <prereqtech>CardOne</prereqtech>
    </card>
  </cards>
</homecity>
"""


class ValidateHomecityCardsTests(unittest.TestCase):
    def make_repo(self, homecity_xml: str, techtree_xml: str = GOOD_TECHTREE) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        repo_root = Path(temp_dir.name)
        data_root = repo_root / "data"
        data_root.mkdir(parents=True, exist_ok=True)
        (data_root / "techtreemods.xml").write_text(techtree_xml, encoding="utf-8")
        (data_root / "rvltmodhomecityexample.xml").write_text(homecity_xml, encoding="utf-8")
        return repo_root

    def test_accepts_valid_homecity_cards(self) -> None:
        repo_root = self.make_repo(GOOD_HOMECITY)
        self.assertEqual(validate_homecity_cards(repo_root), [])

    def test_reports_case_mismatched_prereq(self) -> None:
        repo_root = self.make_repo(
            """<homecity><cards><card><name>HCShipWoodCrates2</name><prereqtech>-1</prereqtech></card><card><name>CardTwo</name><prereqtech>HCShipwoodCrates2</prereqtech></card></cards></homecity>"""
        )
        self.assertEqual(
            validate_homecity_cards(repo_root),
            [
                "data/rvltmodhomecityexample.xml: card 'CardTwo' has case-mismatched prereqtech 'HCShipwoodCrates2' (did you mean 'HCShipWoodCrates2')"
            ],
        )

    def test_reports_missing_custom_prereqtech(self) -> None:
        repo_root = self.make_repo(
            """<homecity><cards><card><name>CardOne</name><prereqtech>RvltModPrereqTech</prereqtech></card></cards></homecity>""",
            techtree_xml="<techtreemods></techtreemods>",
        )
        self.assertEqual(
            validate_homecity_cards(repo_root),
            [
                "data/rvltmodhomecityexample.xml: card 'CardOne' references missing custom prereqtech 'RvltModPrereqTech'"
            ],
        )

        def test_reports_unreachable_same_file_prereq_cycle(self) -> None:
          repo_root = self.make_repo(
            """<homecity><cards><card><name>CardOne</name><prereqtech>CardTwo</prereqtech></card><card><name>CardTwo</name><prereqtech>CardOne</prereqtech></card></cards></homecity>"""
          )
          self.assertEqual(
            validate_homecity_cards(repo_root),
            [
              "data/rvltmodhomecityexample.xml: unreachable same-file prereq chain involving cards: CardOne, CardTwo"
            ],
          )

        def test_accepts_same_file_chain_with_root(self) -> None:
          repo_root = self.make_repo(
            """<homecity><cards><card><name>CardOne</name><prereqtech>-1</prereqtech></card><card><name>CardTwo</name><prereqtech>CardOne</prereqtech></card><card><name>CardThree</name><prereqtech>CardTwo</prereqtech></card></cards></homecity>"""
          )
          self.assertEqual(validate_homecity_cards(repo_root), [])