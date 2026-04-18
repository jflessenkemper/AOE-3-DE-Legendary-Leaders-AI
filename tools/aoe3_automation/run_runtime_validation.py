#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTOMATION_SCRIPT = REPO_ROOT / "tools" / "aoe3_automation" / "aoe3_ui_automation.py"
RUNTIME_VALIDATOR = REPO_ROOT / "tools" / "validation" / "validate_runtime_logs.py"
DEFAULT_LOG_DIR = Path.home() / ".steam/steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Logs"
DEFAULT_ARTIFACT_DIR = REPO_ROOT / "tools" / "aoe3_automation" / "artifacts" / "latest_runtime_validation"


def run_command(args: list[str]) -> int:
    result = subprocess.run(args, cwd=REPO_ROOT)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an AoE3 UI flow, collect artifacts, and validate runtime logs.")
    parser.add_argument("flow", type=Path, help="Flow JSON to run with aoe3_ui_automation.py")
    parser.add_argument("--python", default=sys.executable, help="Python executable to use for child commands")
    parser.add_argument("--suite", action="append", default=[], help="Runtime suite to validate. Repeat for multiple suites.")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR, help="AoE3 log directory.")
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACT_DIR, help="Directory to collect logs and screenshots into.")
    parser.add_argument("--dry-run", action="store_true", help="Pass through to the UI flow runner.")
    parser.add_argument("--skip-flow", action="store_true", help="Skip the UI flow and only collect artifacts plus validate logs.")
    parser.add_argument("--skip-artifacts", action="store_true", help="Skip artifact collection and only validate logs.")
    parser.add_argument("--screenshot", action="store_true", help="Capture a desktop screenshot during artifact collection.")
    args = parser.parse_args()

    flow_path = args.flow.resolve()
    if flow_path.exists() is False:
        print(f"error: flow file not found: {flow_path}", file=sys.stderr)
        return 1

    if args.skip_flow is False:
        flow_cmd = [args.python, str(AUTOMATION_SCRIPT), "run-flow", str(flow_path)]
        if args.dry_run:
            flow_cmd.append("--dry-run")
        if run_command(flow_cmd) != 0:
            return 1

    if args.skip_artifacts is False:
        artifacts_cmd = [
            args.python,
            str(AUTOMATION_SCRIPT),
            "collect-artifacts",
            str(args.artifacts_dir.resolve()),
            "--log-dir",
            str(args.log_dir.resolve()),
        ]
        if args.screenshot:
            artifacts_cmd.append("--screenshot")
        if run_command(artifacts_cmd) != 0:
            return 1

    validator_cmd = [
        args.python,
        str(RUNTIME_VALIDATOR),
        "--log-path",
        str((args.log_dir.resolve() / "Age3Log.txt")),
    ]
    for suite_name in args.suite:
        validator_cmd.extend(["--suite", suite_name])

    return run_command(validator_cmd)


if __name__ == "__main__":
    raise SystemExit(main())