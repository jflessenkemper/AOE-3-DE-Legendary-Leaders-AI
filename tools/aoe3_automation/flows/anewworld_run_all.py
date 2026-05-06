#!/usr/bin/env python3
"""anewworld_run_all.py — Run ANEWWORLD scenario across all 48 civs.

Usage
-----
    python3 tools/aoe3_automation/flows/anewworld_run_all.py [options]

Options
-------
    --dry-run           Print steps without actually running flows.
    --civ CIV_TOKEN     Run a single civ (e.g., ANWBritish). Repeatable.
    --skip CIV_TOKEN    Skip a civ. Repeatable.
    --log-path PATH     Age3Log.txt path (default: Proton location).
    --artifact-dir DIR  Override artifact root (default: artifacts/anewworld_<ts>/).

Flow
----
For each civ in ANW_CIVS:
  1. Set CIV_NAME env var.
  2. Run anewworld_scenario_run.json via aoe3_ui_automation run-flow.
  3. Rotate Age3Log.txt to per-civ slice.
  4. Parse for trigger validation (check for [AGEUP], [UNITS_TRAINED], etc).
  5. Write per-civ artifact dir.
Final: write report.md with trigger validation results per civ.

Speed knobs
-----------
Each match runs for up to 10 minutes (600s timeout).
Target: 15-20 minutes wall-clock per civ → 48 civs in ~12-16 hours.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Ensure repo root is on sys.path regardless of CWD.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.migration.anw_token_map import ANW_CIVS

DEFAULT_LOG_PATH = (
    Path.home()
    / ".steam/steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser"
    / "Games/Age of Empires 3 DE/Logs/Age3Log.txt"
)
FLOW_RUNNER = REPO_ROOT / "tools/aoe3_automation/aoe3_ui_automation.py"
ANEWWORLD_FLOW = Path(__file__).parent / "anewworld_scenario_run.json"
ARTIFACT_BASE = REPO_ROOT / "tools/aoe3_automation/artifacts"


# ---------------------------------------------------------------------------
# Log rotation and parsing
# ---------------------------------------------------------------------------

def rotate_log(log_path: Path, dest: Path) -> None:
    """Copy current log to dest and truncate the source."""
    if log_path.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(log_path, dest)
        log_path.write_text("", encoding="utf-8")


class TriggerValidator:
    """Validate trigger output from game logs."""

    # Expected triggers: [AGEUP], [UNITS_TRAINED], [BUILDINGS], [CARDS], [TRADE_ROUTES], [GAME_END]
    TRIGGER_PATTERNS = {
        "ageup": r"\[AGEUP\]",
        "units": r"\[UNITS_TRAINED\]",
        "buildings": r"\[BUILDINGS\]",
        "cards": r"\[CARDS\]",
        "trade_routes": r"\[TRADE_ROUTES\]",
        "game_end": r"\[GAME_END\]",
    }

    @staticmethod
    def validate_triggers(log_text: str) -> tuple[dict, list]:
        """Check which triggers fired. Returns (trigger_status, errors)."""
        status = {}
        errors = []

        for trigger_name, pattern in TriggerValidator.TRIGGER_PATTERNS.items():
            if re.search(pattern, log_text):
                status[trigger_name] = True
            else:
                status[trigger_name] = False
                errors.append(f"Missing trigger: {trigger_name}")

        # Check for crashes
        if re.search(r"(crashed|exception|error|failed)", log_text, re.IGNORECASE):
            errors.append("Game may have encountered an error or crash")

        return status, errors


# ---------------------------------------------------------------------------
# Per-civ execution
# ---------------------------------------------------------------------------

def run_one_civ(
    civ_token: str,
    civ_name: str,
    log_path: Path,
    civ_artifact_dir: Path,
    dry_run: bool,
) -> dict:
    """Run the per-civ flow, collect log, validate triggers."""
    result: dict = {
        "civ_token": civ_token,
        "civ_name": civ_name,
        "status": "unknown",
        "triggers": {},
        "errors": [],
        "warnings": [],
        "elapsed_s": 0,
    }
    civ_artifact_dir.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "CIV_NAME": civ_name,
    }

    cmd = [
        sys.executable,
        str(FLOW_RUNNER),
        "run-flow",
        str(ANEWWORLD_FLOW),
    ]
    if dry_run:
        cmd.append("--dry-run")

    t0 = time.monotonic()
    print(f"\n=== [{civ_token}] {civ_name} ===")

    if dry_run:
        print(f"  DRY RUN: would execute {' '.join(cmd)}")
    else:
        try:
            completed = subprocess.run(cmd, env=env, timeout=900)  # 15 min timeout per civ
            if completed.returncode != 0:
                result["errors"].append(f"flow runner exited with code {completed.returncode}")
        except subprocess.TimeoutExpired:
            result["errors"].append("flow execution timed out (15 minutes)")

    elapsed = time.monotonic() - t0
    result["elapsed_s"] = round(elapsed, 1)

    # Rotate log
    slice_path = civ_artifact_dir / "Age3Log_slice.txt"
    if not dry_run:
        rotate_log(log_path, slice_path)
    else:
        slice_path.write_text("", encoding="utf-8")

    # Validate triggers
    if slice_path.exists():
        log_text = slice_path.read_text(encoding="utf-8", errors="replace")
        trigger_status, errors = TriggerValidator.validate_triggers(log_text)
        result["triggers"] = trigger_status
        result["errors"].extend(errors)
    else:
        result["errors"].append("No log file to validate")

    # Overall status
    if result["errors"]:
        result["status"] = "FAIL"
    elif not all(result["triggers"].values()):
        result["status"] = "WARN"
        result["warnings"].append("Not all triggers fired")
    else:
        result["status"] = "PASS"

    print(f"  status={result['status']} elapsed={elapsed:.1f}s " +
          f"triggers={'✓' if all(result['triggers'].values()) else '✗'} " +
          f"errors={len(result['errors'])}")
    return result


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_report(results: list[dict], report_path: Path) -> None:
    """Write markdown report of trigger validation results."""
    lines = [
        "# ANEWWORLD Scenario Trigger Validation Report",
        "",
        f"Generated: {datetime.datetime.now().isoformat()}",
        "",
        "## Summary",
        "",
        "| Civ | Status | AgeUp | Units | Buildings | Cards | Trade | GameEnd | Elapsed |",
        "|----|--------|-------|-------|-----------|-------|-------|---------|---------|",
    ]

    for r in results:
        triggers = r.get("triggers", {})
        trigger_str = " | ".join([
            "✓" if triggers.get("ageup", False) else "✗",
            "✓" if triggers.get("units", False) else "✗",
            "✓" if triggers.get("buildings", False) else "✗",
            "✓" if triggers.get("cards", False) else "✗",
            "✓" if triggers.get("trade_routes", False) else "✗",
            "✓" if triggers.get("game_end", False) else "✗",
        ])
        lines.append(
            f"| {r['civ_token']:<15} | {r['status']:<6} | {trigger_str} | {r['elapsed_s']:.0f}s |"
        )

    lines.extend(["", "## Results by Status", ""])

    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    total_elapsed = sum(r["elapsed_s"] for r in results)

    lines += [
        f"**Summary**: {pass_count} PASS / {warn_count} WARN / {fail_count} FAIL",
        f"**Total elapsed**: {total_elapsed/3600:.1f}h",
        "",
    ]

    # Failures
    if fail_count > 0:
        lines.append("## Failures")
        lines.append("")
        for r in results:
            if r["status"] == "FAIL":
                lines.append(f"### {r['civ_token']} — {r['civ_name']}")
                for e in r["errors"]:
                    lines.append(f"- {e}")
                lines.append("")

    # Warnings
    if warn_count > 0:
        lines.append("## Warnings")
        lines.append("")
        for r in results:
            if r["status"] == "WARN":
                lines.append(f"### {r['civ_token']} — {r['civ_name']}")
                for e in r["errors"]:
                    lines.append(f"- {e}")
                for w in r["warnings"]:
                    lines.append(f"- WARN: {w}")
                lines.append("")

    # Trigger summary
    lines.extend(["", "## Trigger Summary", ""])
    trigger_totals = {
        "ageup": 0,
        "units": 0,
        "buildings": 0,
        "cards": 0,
        "trade_routes": 0,
        "game_end": 0,
    }
    for r in results:
        for trigger, fired in r.get("triggers", {}).items():
            if fired:
                trigger_totals[trigger] += 1

    for trigger, count in trigger_totals.items():
        pct = (count / len(results) * 100) if results else 0
        lines.append(f"- **{trigger}**: {count}/{len(results)} ({pct:.0f}%)")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✓ Report written to {report_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="ANEWWORLD scenario trigger validator.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print steps without running flows.")
    parser.add_argument("--civ", action="append", default=[],
                        help="Run only this civ_token (repeatable).")
    parser.add_argument("--skip", action="append", default=[],
                        help="Skip this civ_token (repeatable).")
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH,
                        help="Path to Age3Log.txt.")
    parser.add_argument("--artifact-dir", type=Path,
                        help="Override artifact root directory.")
    args = parser.parse_args()

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    artifact_root = args.artifact_dir or (ARTIFACT_BASE / f"anewworld_{ts}")
    artifact_root.mkdir(parents=True, exist_ok=True)

    # Load civs
    civs_to_run = []
    for civ_token in ANW_CIVS:
        if args.civ and civ_token not in args.civ:
            continue
        if args.skip and civ_token in args.skip:
            continue
        civ_name = civ_token.replace("ANW", "")
        civs_to_run.append((civ_token, civ_name))

    print("="*80)
    print(f"ANEWWORLD Scenario Trigger Validator")
    print("="*80)
    print(f"\nRunning {len(civs_to_run)} civs")
    print(f"Artifacts: {artifact_root}")
    print(f"Log path: {args.log_path}")

    results: list[dict] = []
    for civ_token, civ_name in civs_to_run:
        civ_dir = artifact_root / civ_token
        r = run_one_civ(
            civ_token=civ_token,
            civ_name=civ_name,
            log_path=args.log_path,
            civ_artifact_dir=civ_dir,
            dry_run=args.dry_run,
        )
        results.append(r)

    report_path = artifact_root / "ANEWWORLD_TRIGGERS_REPORT.md"
    write_report(results, report_path)

    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    print("\n" + "="*80)
    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
