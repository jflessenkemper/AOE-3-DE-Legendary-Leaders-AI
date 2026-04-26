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

    def test_flags_non_ascii_inside_string_literals(self) -> None:
        # Regression: a U+2014 em-dash inside a quoted log message caused the
        # AoE3 DE XS tokenizer to crash with "Token Error 0008: STRING NOT
        # TERMINATED" mid-game. Comments are still allowed to contain Unicode.
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai" / "core"
        ai_root.mkdir(parents=True)
        (ai_root / "bad.xs").write_text(
            "// em-dash in comment is fine \u2014 ok\n"
            "void f()\n"
            "{\n"
            "   aiChat(\"oops \u2014 bad\");\n"
            "}\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)
        self.assertTrue(
            any(
                "non-ASCII character" in i and "U+2014" in i and "bad.xs:4" in i
                for i in issues
            ),
            issues,
        )

    def test_flags_undefined_g_variable(self) -> None:
        # Regression for the gTownCenterUnit / gFishingBoatUnit typos that
        # crashed the AI with "XS Error 0172: '<name>' is not a valid operator".
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai" / "core"
        ai_root.mkdir(parents=True)
        (ai_root / "uses.xs").write_text(
            "void f()\n"
            "{\n"
            "   int n = kbUnitCount(0, gTownCenterUnit, 1);\n"
            "}\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)
        self.assertTrue(
            any(
                "undefined g-variable 'gTownCenterUnit'" in i and "uses.xs:3" in i
                for i in issues
            ),
            issues,
        )

    def test_allows_declared_g_variable(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai" / "core"
        ai_root.mkdir(parents=True)
        (ai_root / "globals.xs").write_text(
            "extern int gFishingUnit = 0;\n",
            encoding="utf-8",
        )
        (ai_root / "uses.xs").write_text(
            "void f()\n"
            "{\n"
            "   int n = kbUnitCount(0, gFishingUnit, 1);\n"
            "}\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)
        self.assertFalse(
            any("undefined g-variable" in i for i in issues), issues
        )

    def test_allows_static_g_variable_inside_function(self) -> None:
        # AI files use ``static int gFoo = ...`` for function-local persistent
        # state with the g-prefix convention.
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai" / "core"
        ai_root.mkdir(parents=True)
        (ai_root / "naval.xs").write_text(
            "void tick()\n"
            "{\n"
            "   static int gPlanCreationTime = -1;\n"
            "   if (gPlanCreationTime > 0) { gPlanCreationTime = 0; }\n"
            "}\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)
        self.assertFalse(
            any("undefined g-variable" in i for i in issues), issues
        )

    def test_allows_non_ascii_in_comments(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        ai_root = repo_root / "game" / "ai" / "core"
        ai_root.mkdir(parents=True)
        (ai_root / "ok.xs").write_text(
            "// Wellington \u2014 Torres Vedras doctrine\n"
            "/* multi-line \u2014 also fine */\n"
            "void f()\n"
            "{\n"
            "   aiChat(\"plain ascii only\");\n"
            "}\n",
            encoding="utf-8",
        )

        issues = validate_xs_scripts(repo_root)
        self.assertFalse(
            any("non-ASCII" in i for i in issues), issues
        )