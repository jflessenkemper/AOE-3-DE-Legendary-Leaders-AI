from __future__ import annotations

import unittest

from tools.aoe3_automation.aoe3_ui_automation import collect_text_box_matches, locate_text_box


def make_entry(text: str, left: int, top: int, word: int, line: int = 1) -> dict[str, object]:
    return {
        "text": text,
        "normalized": text.lower(),
        "token": "".join(character for character in text.lower() if character.isalnum()),
        "left": left,
        "top": top,
        "width": 40,
        "height": 12,
        "block": 1,
        "paragraph": 1,
        "line": line,
        "word": word,
        "confidence": 95.0,
    }


class Aoe3UiAutomationOcrTests(unittest.TestCase):
    def test_collect_text_box_matches_returns_repeated_single_token_matches_in_order(self) -> None:
        entries = [
            make_entry("Team", 20, 10, 1, line=1),
            make_entry("1", 70, 10, 2, line=1),
            make_entry("Team", 20, 40, 1, line=2),
            make_entry("1", 70, 40, 2, line=2),
        ]

        matches = collect_text_box_matches(entries, targets=["Team 1"], partial=False)

        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0], (65, 16, "Team 1"))
        self.assertEqual(matches[1], (65, 46, "Team 1"))

    def test_locate_text_box_uses_match_index_for_repeated_labels(self) -> None:
        entries = [
            make_entry("Player", 20, 10, 1, line=1),
            make_entry("1", 70, 10, 2, line=1),
            make_entry("Player", 20, 40, 1, line=2),
            make_entry("1", 70, 40, 2, line=2),
        ]

        match = locate_text_box(entries, targets=["Player 1"], partial=False, match_index=1)

        self.assertEqual(match, (65, 46, "Player 1"))

    def test_locate_text_box_returns_none_when_match_index_exceeds_matches(self) -> None:
        entries = [
            make_entry("Skirmish", 20, 10, 1),
        ]

        match = locate_text_box(entries, targets=["Skirmish"], partial=True, match_index=2)

        self.assertIsNone(match)