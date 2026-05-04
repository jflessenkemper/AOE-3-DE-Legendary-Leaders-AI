"""Static doctrine comparator: xs_sim execution vs playstyle_spec.json claims.

For each leader:
  1. Run leader_*.xs through xs_sim (init + 180 sim-seconds of rule ticks)
  2. Read the doctrine globals it sets (gLLWallStrategy, btOffenseDefense, ...)
  3. Look up the corresponding civ's `claims` block in playstyle_spec.json
  4. Compare and report PASS / FAIL / UNKNOWN

This is the closest a static, no-engine tool can get to "AI playstyle
confirmed". It verifies the *decision-layer code* matches the spec; it
does NOT verify in-engine execution (still requires the matrix on the
Bazzite/Proton rig).

Usage:
    python3 -m tools.xs_sim.compare_doctrine
    python3 -m tools.xs_sim.compare_doctrine --json
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

from .gamestate import scenario_open_age2
from .interpreter import Interpreter
from .harness import LEADERS_DIR

REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "playstyle_spec.json"


# A leader_*.xs file's stem maps to a portrait slug. We then resolve
# the spec entry by matching that slug against the spec's portrait_path.
# Examples:
#   leader_napoleon.xs        → "napoleon"   (matches *_napoleon.png)
#   leader_crazy_horse.xs     → "crazy_horse"
#   leader_revolution_*.xs    → multi-civ aggregator (skip)


def _leader_slug(leader_file: Path) -> str:
    return leader_file.stem.removeprefix("leader_")


# engine slug → spec leader_label slug (per CLAUDE.md leader_key bridge).
# The portrait file uses the engine slug; the spec sometimes uses the
# canonical historical name. These are the known divergences.
_SPEC_SLUG_BRIDGE = {
    "wellington": "elizabeth",
    "catherine":  "ivan",
    "crazy_horse": "gall",
    "jean":       "valette",
    "usman":      "muhammadu",
}


def _spec_for_slug(spec_civs: dict, slug: str) -> dict | None:
    """Find spec entry. Try the leader's engine slug first via portrait path;
    fall back to the historical-name bridge for the few mismatches."""
    for needle in (f"_{slug}.png", f"_{_SPEC_SLUG_BRIDGE.get(slug, slug)}.png"):
        for civ_data in spec_civs.values():
            if civ_data.get("portrait_path", "").endswith(needle):
                return civ_data
        # Also try matching the data_name / leader_label directly
        bridged = _SPEC_SLUG_BRIDGE.get(slug, slug).replace("_", " ").lower()
        for civ_data in spec_civs.values():
            ll = civ_data.get("leader_label", "").lower()
            if bridged in ll:
                return civ_data
    return None


def _wall_strategy_label(value: int) -> str:
    return {
        0: "FortressRing", 1: "ChokepointSegments", 2: "CoastalBatteries",
        3: "FrontierPalisades", 4: "UrbanBarricade", 5: "MobileNoWalls",
    }.get(value, f"Unknown({value})")


def run_one(leader_file: Path) -> dict:
    interp = Interpreter(gs=scenario_open_age2(),
                         search_paths=[REPO / "game" / "ai",
                                       REPO / "game" / "ai" / "leaders",
                                       REPO / "game" / "ai" / "core"])
    # Pre-load aiHeader.xs so cLLWallStrategy*, cLLBuildStyle*, cAge*, etc.
    # constants resolve to their declared engine values, not the simulator's
    # zero-default. Then load leaderCommon.xs so the llUse*Style helpers
    # are defined and `gLLWallStrategy = cLLWallStrategyMobileNoWalls;`
    # actually means 5 instead of 0.
    for hdr in (REPO / "game" / "ai" / "aiHeader.xs",
                REPO / "game" / "ai" / "leaders" / "leaderCommon.xs"):
        if hdr.exists():
            try:
                interp.load_file(hdr)
            except Exception:
                pass  # degrade gracefully if a header uses unsupported syntax
    interp.load_file(leader_file)
    init_fn = next((n for n in interp.functions if n.startswith("initLeader")), None)
    if init_fn:
        interp.call_init(init_fn)
    for r in interp.rules.values():
        r.active = True
    interp.run(180.0, dt=1.0)

    return {
        "wall_strategy": interp.globals.get("gLLWallStrategy"),
        "military_distance_multiplier": interp.globals.get("gLLMilitaryDistanceMultiplier"),
        "ok_to_build_forts": interp.globals.get("cvOkToBuildForts"),
        "max_army_pop": interp.globals.get("cvMaxArmyPop"),
        "rush_boom": interp.globals.get("btRushBoom"),
        "offense_defense": interp.globals.get("btOffenseDefense"),
        "bias_trade": interp.globals.get("btBiasTrade"),
        "bias_native": interp.globals.get("btBiasNative"),
    }


def compare_one(observed: dict, claims: dict) -> tuple[list[str], list[str], list[str]]:
    """Return (passes, fails, unknowns) for one leader."""
    passes: list[str] = []
    fails: list[str] = []
    unknowns: list[str] = []

    # wall_strategy: exact integer match
    if "wall_strategy" in claims:
        want = claims["wall_strategy"]
        got = observed.get("wall_strategy")
        if got is None:
            unknowns.append(
                f"wall_strategy: spec wants {want} ({_wall_strategy_label(want)}); "
                f"sim observed nothing (leader didn't set gLLWallStrategy)"
            )
        elif got == want:
            passes.append(f"wall_strategy={got} ({_wall_strategy_label(got)})")
        else:
            fails.append(
                f"wall_strategy: want {want} ({_wall_strategy_label(want)}), "
                f"got {got} ({_wall_strategy_label(got)})"
            )

    # military_distance_band: [low, high] — observed must fall inside
    if "military_distance_band" in claims:
        lo, hi = claims["military_distance_band"]
        got = observed.get("military_distance_multiplier")
        if got is None:
            unknowns.append(
                f"military_distance_band: spec wants {lo}..{hi}; sim observed nothing"
            )
        elif lo <= got <= hi:
            passes.append(f"military_distance={got} in [{lo}, {hi}]")
        else:
            fails.append(f"military_distance={got} outside spec band [{lo}, {hi}]")

    # expects_forward: a forward-base doctrine should at minimum NOT pin
    # all military to a tight inner ring. We check the military distance
    # multiplier is ≥ 1.0 (= "push military out from TC"). cvOkToBuildForts
    # is intentionally NOT required — several civs (Aztec, Lakota) have
    # forward-aggressive doctrines but lack a fort unit type entirely.
    if claims.get("expects_forward") is True:
        got = observed.get("military_distance_multiplier")
        if got is not None and got < 1.0 and "military_distance_band" not in claims:
            fails.append(
                f"expects_forward=True but military_distance={got} (<1.0); "
                f"doctrine pulls inward, not outward"
            )
        elif got is not None and got >= 1.0:
            passes.append(f"expects_forward → military_distance={got} ≥ 1.0 ✓")

    return passes, fails, unknowns


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args(argv)

    if not SPEC.exists():
        print(f"FATAL: {SPEC} not found. Run tools/playtest/extract_playstyle_spec.py first.")
        return 2

    spec = json.load(open(SPEC))
    spec_civs = spec.get("civs", {})

    leaders = sorted(LEADERS_DIR.glob("leader_*.xs"))
    # Skip aggregator files that drive multiple civs at once.
    leaders = [f for f in leaders if "revolution_" not in f.name]

    rows: list[dict] = []
    for f in leaders:
        slug = _leader_slug(f)
        spec_entry = _spec_for_slug(spec_civs, slug)
        observed = run_one(f)

        if spec_entry is None:
            rows.append({
                "leader": slug,
                "status": "NO_SPEC",
                "passes": [],
                "fails": [],
                "unknowns": [f"no spec entry found for slug {slug!r}"],
                "observed": observed,
            })
            continue

        claims = spec_entry.get("claims", {})
        if not claims:
            rows.append({
                "leader": slug,
                "civ": spec_entry["data_name"],
                "status": "NO_CLAIMS",
                "passes": [], "fails": [], "unknowns": [],
                "observed": observed,
            })
            continue

        p, fl, u = compare_one(observed, claims)
        status = "FAIL" if fl else ("UNKNOWN" if u and not p else "PASS")
        rows.append({
            "leader": slug,
            "civ": spec_entry["data_name"],
            "status": status,
            "passes": p, "fails": fl, "unknowns": u,
            "observed": observed,
        })

    if args.json:
        print(json.dumps(rows, indent=2, default=str))
    else:
        print(f"{'Leader':<22} {'Status':<8} Detail")
        print("-" * 100)
        n_pass = n_fail = n_unk = n_nospec = 0
        for r in rows:
            s = r["status"]
            if s == "PASS":      n_pass += 1
            elif s == "FAIL":    n_fail += 1
            elif s == "UNKNOWN": n_unk += 1
            else:                n_nospec += 1
            detail_lines: list[str] = []
            if r["fails"]:
                detail_lines.extend(f"FAIL: {x}" for x in r["fails"])
            if args.verbose:
                detail_lines.extend(f"PASS: {x}" for x in r["passes"])
                detail_lines.extend(f"???:  {x}" for x in r["unknowns"])
            elif s == "UNKNOWN" and not detail_lines:
                detail_lines.extend(f"???:  {x}" for x in r["unknowns"])

            first = detail_lines[0] if detail_lines else ""
            print(f"{r['leader']:<22} {s:<8} {first}")
            for d in detail_lines[1:]:
                print(f"{'':<22} {'':<8} {d}")
        print("-" * 100)
        print(f"PASS={n_pass}  FAIL={n_fail}  UNKNOWN={n_unk}  NO_SPEC={n_nospec}  "
              f"(of {len(rows)} leaders)")

    return 1 if any(r["status"] == "FAIL" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
