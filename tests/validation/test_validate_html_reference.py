"""Unit tests for the HTML reference structural validator.

Each test builds a minimal in-memory HTML snippet that exercises a
single check, plus one lock-in test against the real repo HTML so we
notice any regression.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.validation.validate_html_reference import (
    REPO,
    validate_html_reference,
)
from tools.validation.validate_html_vs_mod import CIV_TO_HOMECITY


def _section(slug: str, leader: str = "Leader X", flag: str = "f.png", portrait: str = "p.png") -> str:
    return f"""
<!-- ──────────── {slug} ──────────── -->
<details class="nation-node" data-name="{slug}">
<summary><span class="nation-header">
<img class="flag-img" src="{flag}" alt="flag">
<img class="portrait-img" src="{portrait}" alt="{leader}"> {slug} &mdash; {leader}
</span></summary>
<!-- EXPLORER-START {slug} {leader} -->
<!-- LL-FLAGSHIP-QUOTES-START {slug} -->
<!-- WALLING-START {slug} -->
</details>
"""


class _Repo:
    """Tiny helper: writes an HTML doc + dummy flag/portrait files into a tmp dir."""

    def __init__(self, tc: unittest.TestCase, html: str, files: list[str]) -> None:
        tmp = tempfile.TemporaryDirectory()
        tc.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "LEGENDARY_LEADERS_TREE.html").write_text(html, encoding="utf-8")
        for rel in files:
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"x")


def _full_html(extra: str = "") -> str:
    """Build a doc with one section per civ in CIV_TO_HOMECITY (so the
    'every civ' loop is satisfied for civs not under test)."""
    parts = [_section(slug) for slug in CIV_TO_HOMECITY]
    return "<html><body>" + "\n".join(parts) + extra + "</body></html>"


class ValidateHtmlReferenceTests(unittest.TestCase):
    def _repo(self, html: str, files: list[str] | None = None) -> Path:
        if files is None:
            files = ["f.png", "p.png"]
        return _Repo(self, html, files).root

    def test_full_synthetic_doc_passes(self) -> None:
        repo = self._repo(_full_html())
        self.assertEqual(validate_html_reference(repo), [])

    def test_missing_section_header_reported(self) -> None:
        # Drop British's section entirely.
        parts = [_section(s) for s in CIV_TO_HOMECITY if s != "British"]
        html = "<html><body>" + "\n".join(parts) + "</body></html>"
        issues = validate_html_reference(self._repo(html))
        self.assertTrue(any("British: missing section header" in i for i in issues), issues)

    def test_missing_explorer_block_reported(self) -> None:
        # Render Argentines with no EXPLORER-START marker.
        broken = """
<!-- ──────────── Argentines ──────────── -->
<details><summary><span class="nation-header">
<img class="flag-img" src="f.png"><img class="portrait-img" src="p.png" alt="X"> Argentines &mdash; X
</span></summary>
<!-- LL-FLAGSHIP-QUOTES-START Argentines -->
<!-- WALLING-START Argentines -->
</details>
"""
        parts = [_section(s) for s in CIV_TO_HOMECITY if s != "Argentines"]
        html = "<html><body>" + "\n".join(parts) + broken + "</body></html>"
        issues = validate_html_reference(self._repo(html))
        self.assertTrue(any("Argentines: no `<!-- EXPLORER-START" in i for i in issues), issues)

    def test_missing_flag_file_on_disk_reported(self) -> None:
        # Synthetic doc references f.png + p.png; supply only p.png.
        repo = self._repo(_full_html(), files=["p.png"])
        issues = validate_html_reference(repo)
        self.assertTrue(any("flag image missing on disk" in i for i in issues), issues)

    def test_deferred_civs_do_not_fail(self) -> None:
        # Strip Americans + Mexicans (Revolution) sections; validator
        # tolerates them because they are in the deferred-section set.
        parts = [
            _section(s) for s in CIV_TO_HOMECITY
            if s not in {"Americans", "Mexicans (Revolution)"}
        ]
        html = "<html><body>" + "\n".join(parts) + "</body></html>"
        issues = validate_html_reference(self._repo(html))
        self.assertNotIn(
            "Americans: missing section header `<!-- ─── Americans ─── -->`",
            issues,
        )

    def test_lockin_real_repo(self) -> None:
        # The real repo must keep passing the structural validator.
        self.assertEqual(validate_html_reference(REPO), [])


if __name__ == "__main__":
    unittest.main()
