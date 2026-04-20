from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.validation.run_staged_validation import StageResult, format_stage_report, normalize_stage_names, run_runtime_stage, summarize_check_results, ValidationCheckResult


class RunStagedValidationTests(unittest.TestCase):
    def test_normalize_stage_names_defaults_to_order(self) -> None:
        self.assertEqual(
            normalize_stage_names([]),
            ["content", "regression", "packaged", "live", "runtime"],
        )

    def test_normalize_stage_names_preserves_known_stage_order(self) -> None:
        self.assertEqual(
            normalize_stage_names(["runtime", "content", "runtime", "packaged", "live"]),
            ["content", "packaged", "live", "runtime"],
        )

    def test_summarize_check_results_marks_failures(self) -> None:
        status, details, summary = summarize_check_results(
            [
                ValidationCheckResult("Proto", []),
                ValidationCheckResult("XS", ["missing helper declaration"]),
            ]
        )
        self.assertEqual(status, "fail")
        self.assertEqual(summary, "1/2 checks passed")
        self.assertIn("PASS Proto", details)
        self.assertIn("FAIL XS", details)
        self.assertIn("  - missing helper declaration", details)

    def test_run_runtime_stage_skips_when_log_is_missing(self) -> None:
        repo_temp = tempfile.TemporaryDirectory()
        self.addCleanup(repo_temp.cleanup)

        repo_root = Path(repo_temp.name)
        missing_log = repo_root / "missing" / "Age3Log.txt"
        result = run_runtime_stage(repo_root, missing_log, ["elite_retreat_lane"])

        self.assertEqual(result.status, "skipped")
        self.assertIn("runtime log not found", result.summary)
        self.assertTrue(any("Scenario/TEST_SCENARIO_SETUP.md" in detail for detail in result.details))

    def test_format_stage_report_includes_stage_statuses(self) -> None:
        report = format_stage_report(
            [
                StageResult("Content Validation", "pass", "9/9 checks passed", ["PASS Proto"]),
                StageResult("Runtime Log Validation", "skipped", "runtime log not found", ["next steps"]),
            ]
        )
        self.assertIn("[PASS] Content Validation: 9/9 checks passed", report)
        self.assertIn("[SKIPPED] Runtime Log Validation: runtime log not found", report)


if __name__ == "__main__":
    unittest.main()