from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.validation.validate_xs_scripts import validate_xs_scripts


class ValidateXsScriptsTests(unittest.TestCase):
    def test_reports_duplicate_locals_across_loop_bodies(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai" / "core"
        ai_root.mkdir(parents=True)
        (ai_root / "duplicate_local.xs").write_text(
            """
void testFunction()
{
    int i = 0;
    for (i = 0; < 1)
   {
      int value = 2;
   }
    for (i = 0; < 1)
    {
        int value = 3;
    }
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)

        self.assertEqual(
            issues,
            [
                "game/ai/core/duplicate_local.xs:10: duplicate local 'value' in function 'testFunction' (first declared on line 6)"
            ],
        )

    def test_allows_stock_xs_calls(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai" / "core"
        ai_root.mkdir(parents=True)
        (ai_root / "stock_call.xs").write_text(
            """
void testFunction()
{
   int now = xsGetTime();
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)

        self.assertEqual(issues, [])

    def test_reports_unsupported_builtin(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai" / "core"
        ai_root.mkdir(parents=True)
        (ai_root / "broken.xs").write_text(
            """
void testFunction()
{
   int value = xsFloor(2.9);
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)

        self.assertEqual(issues, ["game/ai/core/broken.xs:3: unsupported XS builtin 'xsFloor'"])

    def test_reports_unknown_xs_call_outside_stock_surface(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai" / "core"
        ai_root.mkdir(parents=True)
        (ai_root / "unknown_call.xs").write_text(
            """
void testFunction()
{
   int value = xsInventedBuiltin(2);
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)

        self.assertEqual(
            issues,
            [
                "game/ai/core/unknown_call.xs:3: unknown xs-prefixed call 'xsInventedBuiltin' is outside the stock AoE3 XS surface"
            ],
        )

    def test_ignores_unsupported_builtin_mentions_in_comments(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai" / "core"
        ai_root.mkdir(parents=True)
        (ai_root / "comment_only.xs").write_text(
            """
void testFunction()
{
   int value = 2; // xsFloor(2.9)
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)

        self.assertEqual(issues, [])

    def test_reports_helper_used_before_loader_order_declaration(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai"
        (ai_root / "core").mkdir(parents=True)
        (ai_root / "leaders").mkdir(parents=True)

        (ai_root / "aiLoaderStandard.xs").write_text(
            'include "aiMain.xs";\ninclude "leaders\\leaderCommon.xs";\n',
            encoding="utf-8",
        )
        (ai_root / "aiMain.xs").write_text('include "core\\aiCore.xs";\n', encoding="utf-8")
        (ai_root / "core" / "aiCore.xs").write_text('include "core\\aiBuildingsWalls.xs";\n', encoding="utf-8")
        (ai_root / "core" / "aiBuildingsWalls.xs").write_text(
            """
void rebuildLostForts()
{
   int fortsWanted = llGetWantedFortCount();
}
""".strip()
            + "\n",
            encoding="utf-8",
        )
        (ai_root / "leaders" / "leaderCommon.xs").write_text(
            """
int llGetWantedFortCount(void)
{
   return (1);
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)

        self.assertIn(
            "game/ai/core/aiBuildingsWalls.xs:3: helper call 'llGetWantedFortCount' appears before any declaration in aiLoaderStandard include order",
            issues,
        )

    def test_allows_helper_when_declared_in_core_before_use(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai"
        (ai_root / "core").mkdir(parents=True)
        (ai_root / "leaders").mkdir(parents=True)

        (ai_root / "aiLoaderStandard.xs").write_text(
            'include "aiMain.xs";\ninclude "leaders\\leaderCommon.xs";\n',
            encoding="utf-8",
        )
        (ai_root / "aiMain.xs").write_text('include "core\\aiCore.xs";\n', encoding="utf-8")
        (ai_root / "core" / "aiCore.xs").write_text(
            'mutable int llGetWantedFortCount(void) { return (0); }\ninclude "core\\aiBuildingsWalls.xs";\n',
            encoding="utf-8",
        )
        (ai_root / "core" / "aiBuildingsWalls.xs").write_text(
            """
void rebuildLostForts()
{
   int fortsWanted = llGetWantedFortCount();
}
""".strip()
            + "\n",
            encoding="utf-8",
        )
        (ai_root / "leaders" / "leaderCommon.xs").write_text(
            """
int llGetWantedFortCount(void)
{
   return (1);
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)

        self.assertEqual(issues, [])

    def test_reports_non_ll_helper_used_before_loader_order_declaration(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai"
        (ai_root / "core").mkdir(parents=True)
        (ai_root / "helpers").mkdir(parents=True)

        (ai_root / "aiLoaderStandard.xs").write_text('include "aiMain.xs";\ninclude "helpers\\builders.xs";\n', encoding="utf-8")
        (ai_root / "aiMain.xs").write_text('include "core\\aiCore.xs";\n', encoding="utf-8")
        (ai_root / "core" / "aiCore.xs").write_text('include "core\\aiUtilities.xs";\n', encoding="utf-8")
        (ai_root / "core" / "aiUtilities.xs").write_text(
            """
int createPlan(void)
{
   if (addBuilderToPlan(1, 2, 3) == false)
   {
      return (-1);
   }
   return (0);
}
""".strip()
            + "\n",
            encoding="utf-8",
        )
        (ai_root / "helpers" / "builders.xs").write_text(
            """
bool addBuilderToPlan(int planID = -1, int puid = -1, int numberBuilders = 1)
{
   return (true);
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)

        self.assertIn(
            "game/ai/core/aiUtilities.xs:3: helper call 'addBuilderToPlan' appears before any declaration in aiLoaderStandard include order",
            issues,
        )