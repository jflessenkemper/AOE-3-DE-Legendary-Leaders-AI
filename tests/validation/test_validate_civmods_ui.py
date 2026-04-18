from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.validation.validate_civmods_ui import validate_civmods_ui


LOWERCASE_CIVMODS = """<civsmods>
  <civ>
    <name>zpExample</name>
    <homecityflagtexture>objects\\flags\\example</homecityflagtexture>
        <homecityflagbuttonset>exampleFlagBtn</homecityflagbuttonset>
        <homecityflagbuttonsetlarge>exampleFlagBtnLarge</homecityflagbuttonsetlarge>
    <postgameflagtexture>ui\\ingame\\example</postgameflagtexture>
    <postgameflagiconwpf>resources/images/icons/flags/postgame_flag_example.png</postgameflagiconwpf>
    <homecityflagiconwpf>resources/images/icons/flags/flag_example.png</homecityflagiconwpf>
    <homecityflagbuttonwpf>resources/images/icons/flags/flag_hc_example.png</homecityflagbuttonwpf>
  </civ>
</civsmods>
"""


class ValidateCivmodsUiTests(unittest.TestCase):
    def make_repo(self, civmods_xml: str, resources: list[str]) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        repo_root = Path(temp_dir.name)
        data_root = repo_root / "data"
        data_root.mkdir(parents=True, exist_ok=True)
        (data_root / "civmods.xml").write_text(civmods_xml, encoding="utf-8")

        for relative_path in resources:
            file_path = repo_root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("placeholder", encoding="utf-8")

        return repo_root

    def test_supports_lowercase_civ_tags_for_external_repos(self) -> None:
        repo_root = self.make_repo(
            LOWERCASE_CIVMODS,
            [
                "resources/images/icons/flags/postgame_flag_example.png",
                "resources/images/icons/flags/flag_example.png",
                "resources/images/icons/flags/flag_hc_example.png",
            ],
        )
        self.assertEqual(validate_civmods_ui(repo_root, name_prefixes=None), [])

    def test_reports_missing_ui_fields(self) -> None:
        repo_root = self.make_repo(
            """<civsmods><civ><name>zpExample</name><homecityflagtexture>objects\\flags\\example</homecityflagtexture></civ></civsmods>""",
            [],
        )
        self.assertEqual(
            validate_civmods_ui(repo_root, name_prefixes=None),
            [
                "zpExample: missing required civ UI fields: HomeCityFlagButtonSet, HomeCityFlagButtonSetLarge, PostgameFlagTexture, PostgameFlagIconWPF, HomeCityFlagIconWPF, HomeCityFlagButtonWPF"
            ],
        )