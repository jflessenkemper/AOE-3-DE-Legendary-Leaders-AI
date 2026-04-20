from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.validation.validate_live_mod_install import validate_live_mod_install


class ValidateLiveModInstallTests(unittest.TestCase):
    def test_live_install_matches_packaged_payload(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        live_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)
        self.addCleanup(live_temp.cleanup)

        repo_root = Path(repo_temp.name)
        live_root = Path(live_temp.name)

        (repo_root / "data").mkdir()
        (repo_root / "data" / "example.xml").write_text("<root />", encoding="utf-8")
        (repo_root / "modinfo.json").write_text("{}", encoding="utf-8")

        (live_root / "data").mkdir()
        (live_root / "data" / "example.xml").write_text("<root />", encoding="utf-8")
        (live_root / "modinfo.json").write_text("{}", encoding="utf-8")

        result = validate_live_mod_install(repo_root=repo_root, live_root=live_root)
        self.assertEqual(result.issues, [])

    def test_live_install_reports_missing_extra_and_mismatched_files(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        live_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)
        self.addCleanup(live_temp.cleanup)

        repo_root = Path(repo_temp.name)
        live_root = Path(live_temp.name)

        (repo_root / "data").mkdir()
        (repo_root / "data" / "example.xml").write_text("<root />", encoding="utf-8")
        (repo_root / "data" / "missing.xml").write_text("<required />", encoding="utf-8")
        (repo_root / "modinfo.json").write_text("{}", encoding="utf-8")

        (live_root / "data").mkdir()
        (live_root / "data" / "example.xml").write_text("<changed />", encoding="utf-8")
        (live_root / "data" / "extra.xml").write_text("<unexpected />", encoding="utf-8")
        (live_root / "modinfo.json").write_text("{}", encoding="utf-8")

        result = validate_live_mod_install(repo_root=repo_root, live_root=live_root)
        self.assertIn("Live install missing file: data/missing.xml", result.issues)
        self.assertIn("Live install has unexpected file: data/extra.xml", result.issues)
        self.assertIn("Live install content mismatch: data/example.xml", result.issues)


if __name__ == "__main__":
    unittest.main()