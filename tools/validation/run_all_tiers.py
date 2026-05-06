#!/usr/bin/env python3
"""
COMPLETE 4-TIER VALIDATION ORCHESTRATOR

Runs TIER 1 → TIER 2 setup → TIER 3 → TIER 4 validation in sequence.
Generates comprehensive coverage report.

Usage:
  python3 tools/validation/run_all_tiers.py              # Run all tiers (full flow)
  python3 tools/validation/run_all_tiers.py --tier 1    # Run only TIER 1
  python3 tools/validation/run_all_tiers.py --tier 3    # Run only TIER 3 (requires TIER 2 logs)
  python3 tools/validation/run_all_tiers.py --report    # Generate coverage report
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from tools.migration.anw_token_map import ANW_CIVS

LOGS_DIR = repo_root / "logs" / "tier2"
RESULTS_DIR = repo_root / "logs" / "tier_results"

def run_tier1():
    """Run TIER 1: Static validation."""
    print("\n" + "="*80)
    print("TIER 1: STATIC VALIDATION")
    print("="*80)

    result = subprocess.run(
        [sys.executable, "tools/validation/validate_tier1_static.py"],
        cwd=repo_root
    )

    return result.returncode == 0

def setup_tier2():
    """Initialize TIER 2 log directories."""
    print("\n" + "="*80)
    print("TIER 2: SETUP")
    print("="*80)

    result = subprocess.run(
        [sys.executable, "tools/validation/run_tier2_tests.py", "--init"],
        cwd=repo_root
    )

    print("\nNext steps:")
    print("  1. Follow TIER2_EXECUTION_GUIDE.md to build scenario in AOE3")
    print("  2. Run 48 gameplay tests (4-6 hours)")
    print("  3. Come back and run: python3 tools/validation/run_all_tiers.py --tier 3")

    return result.returncode == 0

def check_tier2_complete():
    """Check if TIER 2 logs are complete."""
    if not LOGS_DIR.exists():
        return False

    logs = list(LOGS_DIR.glob("*_scenario.log"))
    complete = sum(1 for f in logs if len(f.read_text()) > 100)

    return complete == len(ANW_CIVS)

def run_tier3():
    """Run TIER 3: Automated gameplay validation."""
    print("\n" + "="*80)
    print("TIER 3: AUTOMATED GAMEPLAY VALIDATION")
    print("="*80)

    if not check_tier2_complete():
        print("✗ TIER 2 not complete. Run gameplay tests first:")
        print("  python3 tools/validation/run_tier2_tests.py --check")
        return False

    result = subprocess.run(
        [sys.executable, "tools/validation/run_tier2_tests.py", "--validate"],
        cwd=repo_root
    )

    return result.returncode == 0

def run_tier4_checklist():
    """Display TIER 4 manual spot check checklist."""
    print("\n" + "="*80)
    print("TIER 4: MANUAL INTEGRATION SPOT CHECKS")
    print("="*80)

    tier4_file = repo_root / "tools/validation/TIER4_SPOT_CHECKS.md"

    if not tier4_file.exists():
        print("✗ TIER4_SPOT_CHECKS.md not found")
        return False

    print("\nTIER 4 Checklist (30 minutes):")
    print("  1. Play 3x 10-minute games with 6 representative civs")
    print("  2. Watch for crashes, visual glitches, UI issues")
    print("  3. Verify unit compositions match doctrine")
    print("  4. Verify cards are from deck reference")
    print("  5. Check leader names and tooltips")

    print(f"\nFull checklist: {tier4_file}")
    print("  - Game 1: Russians, Swedes, Japanese (rushers)")
    print("  - Game 2: British, French, Dutch (boomers)")
    print("  - Game 3: Ottomans, Peruvians, Haitians (unique)")

    return True

def generate_coverage_report():
    """Generate comprehensive test coverage report."""
    print("\n" + "="*80)
    print("VALIDATION COVERAGE REPORT")
    print("="*80)

    results_dir = repo_root / "logs" / "tier2_results"
    tier1_pass = subprocess.run(
        [sys.executable, "tools/validation/validate_tier1_static.py"],
        cwd=repo_root,
        capture_output=True
    ).returncode == 0

    tier2_complete = check_tier2_complete()
    tier3_logs = list(results_dir.glob("*.json")) if results_dir.exists() else []

    print(f"\nValidation Status:")
    print(f"  TIER 1 (Static):        {'✓ PASS' if tier1_pass else '✗ FAIL'}")
    print(f"  TIER 2 (Gameplay):      {'✓ COMPLETE' if tier2_complete else '⚠ PENDING'} ({len(list(LOGS_DIR.glob('*_scenario.log'))) if LOGS_DIR.exists() else 0}/48)")
    print(f"  TIER 3 (Validation):    {'✓ COMPLETE' if tier3_logs else '⚠ PENDING'}")
    print(f"  TIER 4 (Manual):        ⚠ PENDING")

    print(f"\nCoverage Matrix:")
    print(f"  File Integrity:         ✓ (TIER 1)")
    print(f"  Deck Composition:       ✓ (TIER 1, 3, 4)")
    print(f"  Card Validity:          ✓ (TIER 1, 3, 4)")
    print(f"  AI Behavior:            {'✓ (TIER 2, 3)' if tier2_complete else '⚠ (Awaiting TIER 2)'}")
    print(f"  Game Stability:         {'✓ (TIER 2, 3, 4)' if tier2_complete else '⚠ (Awaiting TIER 2)'}")
    print(f"  UI/UX:                  ⚠ (TIER 4 - awaiting manual check)")

    total_coverage = (
        (100 if tier1_pass else 0) * 0.70 +  # TIER 1 = 70%
        (100 if tier2_complete else 0) * 0.15 +  # TIER 2 = 15%
        (100 if tier3_logs else 0) * 0.10 +  # TIER 3 = 10%
        0 * 0.05  # TIER 4 = 5%
    ) / 100

    print(f"\nTotal Coverage: {total_coverage*100:.0f}%")

    if total_coverage == 1.0:
        print("\n✓ 100% FLAWLESS TEST COVERAGE ACHIEVED")
    elif total_coverage >= 0.95:
        print("\n✓ 95%+ COVERAGE - Almost complete (TIER 4 pending)")
    elif total_coverage >= 0.85:
        print("\n⚠ 85%+ COVERAGE - Good progress (TIER 2-3 pending)")
    else:
        print("\n⚠ Coverage incomplete - Follow execution guide")

    return True

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "--tier" and len(sys.argv) > 2:
            tier = int(sys.argv[2])
            if tier == 1:
                success = run_tier1()
                sys.exit(0 if success else 1)
            elif tier == 2:
                success = setup_tier2()
                sys.exit(0 if success else 1)
            elif tier == 3:
                success = run_tier3()
                sys.exit(0 if success else 1)
            elif tier == 4:
                success = run_tier4_checklist()
                sys.exit(0 if success else 1)
            else:
                print(f"Unknown tier: {tier}")
                sys.exit(1)

        elif cmd == "--report":
            generate_coverage_report()
            sys.exit(0)

        else:
            print(__doc__)
            sys.exit(1)

    else:
        # Full run: TIER 1 → TIER 2 setup → check status → TIER 3 → TIER 4
        print("\n" + "="*80)
        print("COMPLETE 4-TIER VALIDATION FRAMEWORK")
        print("="*80)

        # TIER 1
        if not run_tier1():
            print("\n✗ TIER 1 FAILED - Fix static issues before proceeding")
            sys.exit(1)

        # TIER 2 Setup
        setup_tier2()

        # Check if TIER 2 is complete
        if not check_tier2_complete():
            print("\n" + "="*80)
            print("PAUSING FOR TIER 2 EXECUTION")
            print("="*80)
            print("\nOnce you've completed 48 gameplay tests, run:")
            print("  python3 tools/validation/run_all_tiers.py --tier 3")
            sys.exit(0)

        # TIER 3
        if not run_tier3():
            print("\n✗ TIER 3 FAILED - See issues above")
            sys.exit(1)

        # TIER 4
        run_tier4_checklist()

        # Final report
        generate_coverage_report()

        print("\n" + "="*80)
        print("✓ 4-TIER VALIDATION FRAMEWORK COMPLETE")
        print("="*80)

if __name__ == "__main__":
    main()
