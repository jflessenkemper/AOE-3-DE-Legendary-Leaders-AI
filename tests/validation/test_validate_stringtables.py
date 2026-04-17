from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.validation.validate_stringtables import validate_stringmods


VALID_STRINGMODS = """<root>
  <StringTable>
    <Language name='english'>
      <String _locID='400001'>Valid</String>
    </Language>
  </StringTable>
</root>
"""

INVALID_STRINGMODS = """<root>
  <StringTable>
    <Language name='english'>
      <String _locID='abc'>Bad</String>
      <String _locID='abc'></String>
    </Language>
  </StringTable>
</root>
"""


class ValidateStringtablesTests(unittest.TestCase):
    def make_stringmods(self, language: str, content: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        file_path = Path(temp_dir.name) / "data" / "strings" / language / "stringmods.xml"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def test_accepts_valid_stringmods(self) -> None:
        file_path = self.make_stringmods("english", VALID_STRINGMODS)
        self.assertEqual(validate_stringmods(file_path), [])

    def test_reports_invalid_locids_and_empty_strings(self) -> None:
        file_path = self.make_stringmods("english", INVALID_STRINGMODS)
        issues = validate_stringmods(file_path)
        self.assertEqual(
            issues,
            [
                "data/strings/english/stringmods.xml: invalid _locID values: abc",
                "data/strings/english/stringmods.xml: duplicate _locID values: abc",
                "data/strings/english/stringmods.xml: empty string values for locids: abc",
            ],
        )
