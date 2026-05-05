from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.validation.validate_playstyle_modal import validate_playstyle_modal


def _good_entry(nation: str = "British", leader: str = "Queen Elizabeth I") -> dict:
    return {
        "nation": nation,
        "leader": leader,
        "psTitle": "Tudor naval and mercantile",
        "bsTitle": "Naval Mercantile Compound",
        "bsProse": "Builds the docks first.",
        "ages": {
            "Discovery": "Manor sprawl.",
            "Colonial": "Pikemen and trade.",
            "Fortress": "Stone walls and sea power.",
            "Industrial": "Steam fleet.",
            "Imperial": "Imperial line ships.",
        },
        "terrainLabel": "Coast / Plain",
        "headingLabel": "Along coast",
        "wallLabel": "Coastal batteries",
        "civicAnchor": False,
        "combatDoctrine": "Reactive — pushes when the enemy is weak.",
        "ecoBullets": ["plants forward fishing fleet"],
        "militaryBullets": ["balanced infantry line"],
        "defenseBullets": ["coastal batteries — moderate stone wall ring"],
        # Imperial-peer doctrine fields.
        "imperialPsTitle": "Tudor Maritime Empire",
        "imperialBsProse": "Royal Navy + chartered companies project the realm overseas.",
        "imperialCombatDoctrine": "Combined — naval projection with militia core.",
        "imperialAges": {
            "Discovery": "Charters trade companies (Muscovy, Levant).",
            "Colonial": "Plantation outposts on contested coasts.",
            "Fortress": "Galleon fleet plus trained-bands militia.",
            "Industrial": "Privateer Sea Dog squadron harasses flanks.",
            "Imperial": "Tudor Armada at full strength; trained bands defend the realm.",
        },
        "imperialEcoBullets": ["chartered company trade-route monopolies"],
        "imperialMilitaryBullets": ["heavy galleon and privateer mass"],
        "imperialDefenseBullets": ["coastal forts with deep harbour"],
    }


def _build_html(node_keys: list[str], data: dict) -> str:
    nodes = "\n".join(
        f'<details class="nation-node" data-name="{key}"><summary>{key}</summary></details>'
        for key in node_keys
    )
    return (
        "<html><body>"
        f"{nodes}"
        "<!-- PLAYSTYLE-MODAL-START -->"
        "<script>"
        f"window.NATION_PLAYSTYLE = {json.dumps(data, indent=2)};"
        "</script>"
        "<!-- PLAYSTYLE-MODAL-END -->"
        "</body></html>"
    )


class ValidatePlaystyleModalTests(unittest.TestCase):
    def make_repo(self, html: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "a_new_world.html").write_text(html, encoding="utf-8")
        return root

    def test_accepts_complete_data(self) -> None:
        data = {"British Elizabeth": _good_entry()}
        html = _build_html(["British Elizabeth"], data)
        self.assertEqual(validate_playstyle_modal(self.make_repo(html)), [])

    def test_reports_missing_node_for_data_key(self) -> None:
        data = {"British Elizabeth": _good_entry()}
        html = _build_html([], data)  # no nation-node for the entry
        issues = validate_playstyle_modal(self.make_repo(html))
        self.assertIn(
            "British Elizabeth: NATION_PLAYSTYLE entry has no matching nation-node",
            issues,
        )

    def test_reports_missing_data_for_node(self) -> None:
        html = _build_html(["British Elizabeth"], {})
        issues = validate_playstyle_modal(self.make_repo(html))
        self.assertIn(
            "British Elizabeth: nation-node has no NATION_PLAYSTYLE entry",
            issues,
        )

    def test_reports_missing_string_field(self) -> None:
        entry = _good_entry()
        entry["bsProse"] = ""
        html = _build_html(["British Elizabeth"], {"British Elizabeth": entry})
        issues = validate_playstyle_modal(self.make_repo(html))
        self.assertIn(
            "British Elizabeth: missing or empty string field 'bsProse'",
            issues,
        )

    def test_reports_missing_age_key(self) -> None:
        entry = _good_entry()
        del entry["ages"]["Imperial"]
        html = _build_html(["British Elizabeth"], {"British Elizabeth": entry})
        issues = validate_playstyle_modal(self.make_repo(html))
        self.assertIn(
            "British Elizabeth: ages['Imperial'] missing or empty",
            issues,
        )

    def test_reports_all_empty_bullet_sections(self) -> None:
        entry = _good_entry()
        entry["ecoBullets"] = []
        entry["militaryBullets"] = []
        entry["defenseBullets"] = []
        html = _build_html(["British Elizabeth"], {"British Elizabeth": entry})
        issues = validate_playstyle_modal(self.make_repo(html))
        self.assertIn(
            "British Elizabeth: all bullet sections empty (eco/military/defense) — no doctrine signal",
            issues,
        )

    def test_reports_jargon_leak_multiplier(self) -> None:
        entry = _good_entry()
        entry["ecoBullets"] = ["spreads economy widely (1.30×)"]
        html = _build_html(["British Elizabeth"], {"British Elizabeth": entry})
        issues = validate_playstyle_modal(self.make_repo(html))
        self.assertTrue(
            any("jargon leak" in i and "1.30×" in i for i in issues),
            f"expected jargon-leak finding, got {issues!r}",
        )

    def test_reports_jargon_leak_level_notation(self) -> None:
        entry = _good_entry()
        entry["defenseBullets"] = ["walls level 3/5"]
        html = _build_html(["British Elizabeth"], {"British Elizabeth": entry})
        issues = validate_playstyle_modal(self.make_repo(html))
        self.assertTrue(
            any("jargon leak" in i and "level 3/5" in i.lower() for i in issues),
            f"expected jargon-leak finding, got {issues!r}",
        )


    def test_reports_missing_imperial_field(self) -> None:
        entry = _good_entry()
        del entry["imperialPsTitle"]
        html = _build_html(["British Elizabeth"], {"British Elizabeth": entry})
        issues = validate_playstyle_modal(self.make_repo(html))
        self.assertIn(
            "British Elizabeth: missing or empty imperial-peer field 'imperialPsTitle'",
            issues,
        )

    def test_reports_missing_imperial_age(self) -> None:
        entry = _good_entry()
        del entry["imperialAges"]["Imperial"]
        html = _build_html(["British Elizabeth"], {"British Elizabeth": entry})
        issues = validate_playstyle_modal(self.make_repo(html))
        self.assertIn(
            "British Elizabeth: imperialAges['Imperial'] missing or empty",
            issues,
        )

    def test_reports_empty_imperial_bullet_section(self) -> None:
        entry = _good_entry()
        entry["imperialEcoBullets"] = []
        html = _build_html(["British Elizabeth"], {"British Elizabeth": entry})
        issues = validate_playstyle_modal(self.make_repo(html))
        self.assertIn(
            "British Elizabeth: 'imperialEcoBullets' must not be empty",
            issues,
        )

    def test_imperial_enforcement_can_be_disabled(self) -> None:
        # Until tools/playstyle/imperial_data.py is authored, the staged
        # validator passes require_imperial=False. Confirm the kwarg
        # bypass actually skips the new fields.
        entry = _good_entry()
        for f in (
            "imperialPsTitle", "imperialBsProse", "imperialCombatDoctrine",
            "imperialAges", "imperialEcoBullets",
            "imperialMilitaryBullets", "imperialDefenseBullets",
        ):
            entry.pop(f, None)
        html = _build_html(["British Elizabeth"], {"British Elizabeth": entry})
        self.assertEqual(
            validate_playstyle_modal(self.make_repo(html), require_imperial=False),
            [],
        )


if __name__ == "__main__":
    unittest.main()
