"""Orchestrator for the ANW migration. Runs all phase scripts in order.

The migration touches ~3000+ token references across 15+ files plus 96 file
renames (.personality + homecity files). Applying any subset would leave the
mod in a half-migrated state where the engine can't load AI personalities or
civ definitions, so this script's --apply mode runs everything as one
atomic operation.

Phases (each script defaults to dry-run; --apply propagates):

  1. tools.migration.anw_token_map               (no I/O — sanity check)
  2. tools.migration.build_anw_civmods           → data/civmods.xml
  3. tools.migration.migrate_strings             → stringmods.xml,
                                                    randomnamemods.xml,
                                                    techtreemods.xml,
                                                    playercolors.xml
  4. tools.migration.migrate_personalities       → 48 game/ai/anw*.personality
                                                    + chatsetsmods.xml
  5a. tools.migration.migrate_homecities         → 48 data/anwhomecity*.xml
  5b. tools.migration.build_anw_decks            → data/decks_anw.json

Usage:
  python3 tools/migration/run_anw_migration.py             # dry-run all phases
  python3 tools/migration/run_anw_migration.py --apply     # APPLY ALL
  python3 tools/migration/run_anw_migration.py --check     # CI drift gate

WARNING: --apply is destructive. It rewrites and deletes files. Before running
with --apply you MUST have:

  1. The 22 base-civ stubs in data/civmods.anw.xml filled in with vanilla
     civ data (StatsID, AgeTechs, starting units, flag textures). See the
     TODO-ANW-VANILLA markers — these block the migration.
  2. A clean git working tree, so you can `git diff` the apply state.
  3. A full validation suite green BEFORE the apply
     (tools/validation/run_staged_validation.py).
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


PHASES = [
    ("Phase 1: token map self-check",     "tools.migration.anw_token_map", "_self_check"),
    ("Phase 2: build_anw_civmods",        "tools.migration.build_anw_civmods", "main"),
    ("Phase 3: migrate_strings",          "tools.migration.migrate_strings", "main"),
    ("Phase 4: migrate_personalities",    "tools.migration.migrate_personalities", "main"),
    ("Phase 5a: migrate_homecities",      "tools.migration.migrate_homecities", "main"),
    ("Phase 5b: build_anw_decks",         "tools.migration.build_anw_decks", "main"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Apply all phases atomically. DESTRUCTIVE.")
    parser.add_argument("--check", action="store_true",
                        help="CI drift gate — exit non-zero if any phase would change anything.")
    args = parser.parse_args()

    if args.apply and args.check:
        parser.error("--apply and --check are mutually exclusive")

    # Pre-flight: confirm vanilla extraction has been done
    civmods_anw = REPO / "data" / "civmods.anw.xml"
    if args.apply:
        if not civmods_anw.is_file():
            print(f"ERROR: {civmods_anw} not found. Run phase 2 first.", file=sys.stderr)
            return 1
        # Look for unfilled TODO markers
        anw_text = civmods_anw.read_text(encoding="utf-8")
        if "TODO-ANW-VANILLA" in anw_text:
            print(
                "ERROR: data/civmods.anw.xml still contains TODO-ANW-VANILLA markers. "
                "The 22 base-civ stubs need vanilla civs.xml data filled in before applying. "
                "Run `python3 tools/migration/extract_vanilla_civs.py` (after that script "
                "is built) to extract the engine's vanilla civs.xml from .bar archives.",
                file=sys.stderr,
            )
            return 1

    # Run phases in order
    forwarded: list[str] = []
    if args.apply:
        forwarded = ["--apply"]
    elif args.check:
        forwarded = ["--check"]

    failed = 0
    for label, mod_name, fn_name in PHASES:
        print(f"\n=== {label} ===", file=sys.stderr)
        # Inject argv so each script's argparse picks up our flags
        old_argv = sys.argv[:]
        sys.argv = [mod_name] + forwarded
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, fn_name)
            rc = fn()
            if rc:
                failed += 1
                print(f"  ✗ {label} returned {rc}", file=sys.stderr)
        except SystemExit as e:  # argparse / sys.exit() inside scripts
            if e.code:
                failed += 1
                print(f"  ✗ {label} exited {e.code}", file=sys.stderr)
        finally:
            sys.argv = old_argv

    if failed:
        print(f"\n{failed} phase(s) failed.", file=sys.stderr)
        return 1
    print("\nAll phases completed successfully.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
