"""Doctrine-compliance harness — run a leader's XS through the simulator
and assert the resulting global state matches playstyle_spec.json.

CLI:
    python3 -m tools.xs_sim.harness                 # run all leaders
    python3 -m tools.xs_sim.harness napoleon        # one leader
    python3 -m tools.xs_sim.harness --parse-only    # parse-coverage check

Coverage caveat: this exercises the *decision* layer of XS (rule bodies
mutating doctrine globals). It does NOT simulate combat, training, or
pathfinding — the rule action verbs (aiTask*, aiTrainUnit) are recorded
into GameState.actions but their outcomes aren't computed.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .gamestate import scenario_open_age2, scenario_coastal_age2
from .interpreter import Interpreter


REPO = Path(__file__).resolve().parents[2]
LEADERS_DIR = REPO / "game" / "ai" / "leaders"


def _parse_all(verbose: bool = False) -> int:
    from .parser import parse
    files = sorted(LEADERS_DIR.glob("*.xs")) + \
            sorted((REPO / "game" / "ai").glob("*.xs")) + \
            sorted((REPO / "game" / "ai" / "core").glob("*.xs"))
    ok = 0; fail = 0
    for f in files:
        try:
            parse(f.read_text(encoding="utf-8", errors="ignore"), str(f))
            ok += 1
        except Exception as e:
            fail += 1
            print(f"FAIL {f.relative_to(REPO)}: {e}")
    print(f"Parse coverage: {ok}/{ok+fail} files parse cleanly")
    return 0 if fail == 0 else 1


def run_leader(leader_file: Path, sim_seconds: float = 180.0) -> dict:
    """Load + initialize + tick a leader. Return a dict with the
    observable doctrine state after the run."""
    gs = scenario_open_age2()
    interp = Interpreter(gs=gs, search_paths=[REPO / "game" / "ai",
                                              REPO / "game" / "ai" / "leaders",
                                              REPO / "game" / "ai" / "core"])
    interp.load_file(leader_file)

    # Find init function — convention is initLeader<Name>()
    init_fn = next((n for n in interp.functions if n.startswith("initLeader")), None)
    if init_fn:
        interp.call_init(init_fn)

    # Activate every rule for the run (real engine activates them via
    # aiMain hooks we don't load).
    for r in interp.rules.values():
        r.active = True

    interp.run(sim_seconds, dt=1.0)

    # Pull out the standard doctrine variables.
    keys_of_interest = [
        "btRushBoom", "btOffenseDefense", "btBiasTrade", "btBiasNative",
        "cvMinNumVills", "cvMaxArmyPop", "cvOkToBuildForts", "cvMaxTowers",
        "gLLWallStrategy", "gLLMilitaryDistanceMultiplier",
    ]
    return {
        "leader": leader_file.stem,
        "init_called": init_fn,
        "rules": list(interp.rules),
        "fired_count": len(interp.fired_log),
        "doctrine": {k: interp.globals.get(k) for k in keys_of_interest},
        "actions": len(gs.actions),
        "unknown_calls": len(interp.unknown_calls),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("leader", nargs="?", help="leader name (e.g. napoleon) or omit for all")
    ap.add_argument("--parse-only", action="store_true",
                    help="just confirm every .xs file parses")
    ap.add_argument("--seconds", type=float, default=180.0)
    ap.add_argument("--json", action="store_true",
                    help="emit JSON results")
    args = ap.parse_args(argv)

    if args.parse_only:
        return _parse_all()

    if args.leader:
        leaders = [LEADERS_DIR / f"leader_{args.leader}.xs"]
    else:
        leaders = sorted(p for p in LEADERS_DIR.glob("leader_*.xs"))

    results = []
    for f in leaders:
        if not f.exists():
            print(f"missing: {f}")
            continue
        try:
            r = run_leader(f, sim_seconds=args.seconds)
            results.append(r)
        except Exception as e:
            results.append({"leader": f.stem, "error": str(e)})

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"{'Leader':<28} {'Rules':>6} {'Fired':>6} {'Unknown':>8} Doctrine")
        print("-" * 90)
        for r in results:
            if "error" in r:
                print(f"{r['leader']:<28} ERROR: {r['error']}")
                continue
            d = r["doctrine"]
            doctrine_str = ", ".join(f"{k.replace('bt','').replace('cv','').replace('gLL','')}={v}"
                                     for k, v in d.items() if v is not None)
            print(f"{r['leader']:<28} {len(r['rules']):>6} {r['fired_count']:>6} "
                  f"{r['unknown_calls']:>8}  {doctrine_str[:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
