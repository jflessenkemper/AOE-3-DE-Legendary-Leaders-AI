from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.validation.validate_packaged_mod import DEV_ONLY_TOP_LEVEL, build_packaged_tree


class ValidatePackagedModTests(unittest.TestCase):
    def test_build_packaged_tree_excludes_dev_only_paths(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        package_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)
        self.addCleanup(package_temp.cleanup)

        repo_root = Path(repo_temp.name)
        packaged_root = Path(package_temp.name)

        (repo_root / "data").mkdir()
        (repo_root / "modinfo.json").write_text("{}", encoding="utf-8")
        (repo_root / "tests").mkdir()
        (repo_root / "tests" / "placeholder.txt").write_text("ignore", encoding="utf-8")
        (repo_root / "tools").mkdir()
        (repo_root / "tools" / "placeholder.txt").write_text("ignore", encoding="utf-8")

        included_entries = build_packaged_tree(repo_root, packaged_root)

        self.assertEqual(sorted(included_entries), ["data", "modinfo.json"])
        for path_name in DEV_ONLY_TOP_LEVEL:
            self.assertFalse((packaged_root / path_name).exists())
