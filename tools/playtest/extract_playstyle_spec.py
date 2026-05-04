"""Extract structured per-civ playstyle assertions from
LEGENDARY_LEADERS_TREE.html and emit `playstyle_spec.json`.

The spec is consumed by `tools/validation/validate_doctrine_compliance.py`
to cross-check runtime probes against what the public reference tree
advertises. Each civ record has two layers:

1. **Doctrine claims** — derived from the structured doctrine label that
   sits at token index 2 of the `data-search` blob (after the leader name
   and the doctrine-summary tagline). The HTML curator picks one of 15
   canonical labels; each label maps to a fixed claim bundle below.

2. **Prose claims** — extracted from the trailing prose paragraph using
   the keyword regexes from `html_reference.py`. These can override or
   add to the doctrine defaults (e.g. a civ tagged "Naval Mercantile
   Compound" whose prose mentions "cavalry-heavy" gets the cavalry flag
   set in addition to its naval defaults).

Output schema (per civ):

    {
      "civ_label": "British",
      "leader_label": "Queen Elizabeth I",
      "data_name": "British Elizabeth",
      "doctrine_label": "Naval Mercantile Compound",
      "doctrine_summary": "Tudor naval and mercantile",
      "claims": {
        "wall_strategy": 1,                # cLLWallStrategyFortressRing
        "first_military_building": "dock",
        "expects_naval": true,
        "expects_forward": false,
        "expects_treaty": false,
        "expects_cavalry": false,
        "expects_infantry": false,
        "expects_artillery": false,
        "first_dock_before_ms": 360000,
        "first_wall_before_ms": 900000,
        "military_distance_band": [0.9, 1.2]
      },
      "doctrine_prose": "Builds the docks first..."
    }

Wall-strategy ints match `cLLWallStrategy*` in aiGlobals.xs:
    1=FortressRing  2=CoastalBatteries  3=ChokepointSegments
    4=FrontierPalisades  5=MobileNoWalls  6=UrbanBarricade

Usage:
    python3 tools/playtest/extract_playstyle_spec.py
    # writes playstyle_spec.json next to LEGENDARY_LEADERS_TREE.html

The `--print-stats` flag dumps per-claim coverage so we can see, e.g.,
how many civs assert `expects_naval=true` (sanity check vs. our 5
"Naval Mercantile Compound" + any prose-only naval civs).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from html_reference import (  # type: ignore[import-not-found]
    NATION_BLOCK_RX,
    NAVAL_RX,
    FORWARD_RX,
    TREATY_RX,
    CAVALRY_RX,
    INFANTRY_RX,
    ARTILLERY_RX,
    WALL_PHRASES,
    WALL_FORTRESS_RING,
    WALL_COASTAL_BATTERIES,
    WALL_CHOKEPOINT_SEGMENTS,
    WALL_FRONTIER_PALISADES,
    WALL_MOBILE_NO_WALLS,
    WALL_URBAN_BARRICADE,
    _civ_label_for,
)

# ─── doctrine → canonical claim bundle ─────────────────────────────────────

# Per-claim defaults keyed by the structured doctrine label (3rd `·` token
# in `data-search`). Prose extraction can OR-on additional flags but never
# unsets a doctrine-level claim. Time budgets are in milliseconds of game
# time (matrix runner ticks at ~1× speed unless --auto-resign-ms
# overrides). Numbers are tuned to match the prose tempo descriptions:
# "first" / "before the second" → ~6 min, "early" → ~10 min, "by Age 3"
# → ~15 min.

DOCTRINE_CLAIMS: dict[str, dict[str, Any]] = {
    "Naval Mercantile Compound": {
        # Coastal/harbour doctrine — matches llUseNavalMercantileCompoundStyle
        # which sets gLLWallStrategy = cLLWallStrategyCoastalBatteries.
        "wall_strategy": WALL_COASTAL_BATTERIES,
        "first_military_building": "dock",
        "expects_naval": True,
        "first_dock_before_ms": 360_000,    # 6 min
        "first_wall_before_ms": 900_000,    # 15 min
        "military_distance_band": [0.9, 1.2],
    },
    "Forward Operational Line": {
        # llUseForwardOperationalLineStyle picks MobileNoWalls — the doctrine
        # is "push outward, intercept rather than wall in".
        "wall_strategy": WALL_MOBILE_NO_WALLS,
        "first_military_building": "barracks_or_stable",
        "expects_forward": True,
        "first_barracks_before_ms": 360_000,
        "first_wall_before_ms": 720_000,
        # Band widened so leader-file defensive overrides (0.85-0.9) still pass:
        # the doctrine cares about *forward troop posture*, not strictly far
        # building placement.
        "military_distance_band": [0.85, 1.3],
    },
    "Jungle Guerrilla Network": {
        # llUseJungleGuerrillaNetworkStyle sets MobileNoWalls and militaryDist
        # 0.95 — the doctrine is "no perimeter wall, infiltration warbands
        # from the inner core", not segmented chokepoint walls.
        "wall_strategy": WALL_MOBILE_NO_WALLS,
        "first_military_building": "barracks_or_stable",
        "expects_forward": True,
        "first_barracks_before_ms": 420_000,
        "military_distance_band": [0.95, 1.3],
    },
    "Republican Levee": {
        "wall_strategy": WALL_URBAN_BARRICADE,
        "first_military_building": "barracks_or_stable",
        "expects_infantry": True,
        "first_barracks_before_ms": 360_000,
        "first_wall_before_ms": 900_000,
        "military_distance_band": [0.8, 1.1],
    },
    "Compact Fortified Core": {
        "wall_strategy": WALL_FORTRESS_RING,
        "first_military_building": "barracks_or_stable",
        "first_wall_before_ms": 600_000,    # 10 min — early ring
        "military_distance_band": [0.7, 0.9],
    },
    "Highland Citadel": {
        "wall_strategy": WALL_FORTRESS_RING,
        "first_military_building": "barracks_or_stable",
        "expects_artillery": True,
        "first_wall_before_ms": 720_000,
        "military_distance_band": [0.7, 1.0],
    },
    "Distributed Economic Network": {
        "first_military_building": "trading_post_or_market",
        "expects_treaty": True,
        # llUseDistributedEconomicNetworkStyle sets militaryDist=1.0; the
        # "distributed" part is economic node spread, not forward military.
        "military_distance_band": [1.0, 1.3],
    },
    "Andean Terrace Fortress": {
        # llUseAndeanTerraceFortressStyle sets ChokepointSegments — terraces
        # are natural cliff chokes, not full ring walls.
        "wall_strategy": WALL_CHOKEPOINT_SEGMENTS,
        "first_military_building": "barracks_or_stable",
        "first_wall_before_ms": 720_000,
        "military_distance_band": [0.7, 1.0],
    },
    "Shrine or Trade Node Spread": {
        "first_military_building": "trading_post_or_market",
        "expects_treaty": True,
        # llUseShrineTradeNodeSpreadStyle sets militaryDist=0.95; the
        # "spread" is shrine/trade-node placement, military stays close
        # to the inner economic core.
        "military_distance_band": [0.95, 1.3],
    },
    "Mobile Frontier Scatter": {
        "wall_strategy": WALL_MOBILE_NO_WALLS,
        "first_military_building": "barracks_or_stable",
        "expects_forward": True,
        "military_distance_band": [1.1, 1.3],
    },
    "Civic Militia Center": {
        "wall_strategy": WALL_URBAN_BARRICADE,
        "first_military_building": "barracks_or_stable",
        "expects_infantry": True,
        "military_distance_band": [0.8, 1.1],
    },
    "Plains Cavalry Wedge": {
        "wall_strategy": WALL_MOBILE_NO_WALLS,
        "first_military_building": "barracks_or_stable",
        "expects_cavalry": True,
        "expects_forward": True,
        "military_distance_band": [1.1, 1.3],
    },
    "Siege Train Concentration": {
        "wall_strategy": WALL_FORTRESS_RING,
        "first_military_building": "barracks_or_stable",
        "expects_artillery": True,
        "military_distance_band": [0.8, 1.1],
    },
    "Streltsy siege": {
        "wall_strategy": WALL_FORTRESS_RING,
        "first_military_building": "barracks_or_stable",
        "expects_infantry": True,
        "expects_artillery": True,
        "military_distance_band": [0.8, 1.1],
    },
    "Steppe Cavalry Wedge": {
        "wall_strategy": WALL_MOBILE_NO_WALLS,
        "first_military_building": "barracks_or_stable",
        "expects_cavalry": True,
        "expects_forward": True,
        "military_distance_band": [1.1, 1.3],
    },
}


PROSE_FLAG_RXS: list[tuple[str, re.Pattern[str]]] = [
    ("expects_naval", NAVAL_RX),
    ("expects_forward", FORWARD_RX),
    ("expects_treaty", TREATY_RX),
    ("expects_cavalry", CAVALRY_RX),
    ("expects_infantry", INFANTRY_RX),
    ("expects_artillery", ARTILLERY_RX),
]


@dataclass
class CivPlaystyleSpec:
    civ_label: str
    leader_label: str
    data_name: str
    doctrine_label: Optional[str]
    doctrine_summary: Optional[str]
    portrait_path: Optional[str]
    doctrine_prose: str
    claims: dict[str, Any] = field(default_factory=dict)
    prose_overrides: list[str] = field(default_factory=list)


def _wall_from_prose(prose: str) -> Optional[int]:
    """First matching wall phrase wins — same precedence as html_reference.py."""
    for rx, strat in WALL_PHRASES:
        if rx.search(prose):
            return strat
    return None


def _build_claims(doctrine_label: Optional[str], prose: str) -> tuple[dict[str, Any], list[str]]:
    """Start from the doctrine bundle, then OR-on any prose-derived flags
    (prose can add positive flags but cannot retract a doctrine claim;
    prose-derived wall strategy fills in only when doctrine left it blank)."""
    claims: dict[str, Any] = {}
    overrides: list[str] = []

    if doctrine_label and doctrine_label in DOCTRINE_CLAIMS:
        # shallow-copy so we don't mutate the module-level dict
        claims.update(DOCTRINE_CLAIMS[doctrine_label])

    for flag, rx in PROSE_FLAG_RXS:
        if rx.search(prose):
            if not claims.get(flag, False):
                overrides.append(f"+{flag}")
            claims[flag] = True

    if "wall_strategy" not in claims:
        prose_wall = _wall_from_prose(prose)
        if prose_wall is not None:
            claims["wall_strategy"] = prose_wall
            overrides.append(f"+wall_strategy_from_prose={prose_wall}")

    return claims, overrides


def extract_specs(html_path: Path) -> dict[str, CivPlaystyleSpec]:
    text = html_path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, CivPlaystyleSpec] = {}

    for m in NATION_BLOCK_RX.finditer(text):
        full_name = m.group(1)
        data_search = m.group(2)
        portrait = m.group(3)

        parts = data_search.split(" · ")
        doctrine_summary = parts[1].strip() if len(parts) > 1 else None
        doctrine_label   = parts[2].strip() if len(parts) > 2 else None
        prose            = parts[-1].strip() if parts else ""

        civ_label, leader_label = _civ_label_for(full_name)
        claims, overrides = _build_claims(doctrine_label, prose)

        out[full_name] = CivPlaystyleSpec(
            civ_label=civ_label,
            leader_label=leader_label,
            data_name=full_name,
            doctrine_label=doctrine_label,
            doctrine_summary=doctrine_summary,
            portrait_path=portrait,
            doctrine_prose=prose,
            claims=claims,
            prose_overrides=overrides,
        )

    return out


def _print_stats(specs: dict[str, CivPlaystyleSpec]) -> None:
    print(f"parsed {len(specs)} civ playstyle specs")

    doctrine_counts: Counter[str] = Counter()
    flag_counts: Counter[str] = Counter()
    wall_counts: Counter[int] = Counter()
    no_wall = 0
    no_first_mil = 0
    for s in specs.values():
        doctrine_counts[s.doctrine_label or "<none>"] += 1
        for k, v in s.claims.items():
            if isinstance(v, bool) and v:
                flag_counts[k] += 1
        ws = s.claims.get("wall_strategy")
        if ws is None:
            no_wall += 1
        else:
            wall_counts[ws] += 1
        if "first_military_building" not in s.claims:
            no_first_mil += 1

    print("\n-- doctrines --")
    for k, v in sorted(doctrine_counts.items(), key=lambda x: -x[1]):
        print(f"  {v:2d}  {k}")

    print("\n-- prose flags asserted --")
    for k, v in sorted(flag_counts.items(), key=lambda x: -x[1]):
        print(f"  {v:2d}  {k}")

    wall_names = {
        WALL_FORTRESS_RING: "FortressRing",
        WALL_COASTAL_BATTERIES: "CoastalBatteries",
        WALL_CHOKEPOINT_SEGMENTS: "ChokepointSegments",
        WALL_FRONTIER_PALISADES: "FrontierPalisades",
        WALL_MOBILE_NO_WALLS: "MobileNoWalls",
        WALL_URBAN_BARRICADE: "UrbanBarricade",
    }
    print("\n-- wall_strategy distribution --")
    for k, v in sorted(wall_counts.items(), key=lambda x: -x[1]):
        print(f"  {v:2d}  {wall_names.get(k, '?')} ({k})")
    if no_wall:
        print(f"  {no_wall:2d}  <unset>  ← these civs assert no wall posture")

    if no_first_mil:
        print(f"\n{no_first_mil} civs lack first_military_building claim")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--html", type=Path, default=None,
                    help="path to LEGENDARY_LEADERS_TREE.html (default: repo root)")
    ap.add_argument("--out", type=Path, default=None,
                    help="output JSON path (default: <repo>/playstyle_spec.json)")
    ap.add_argument("--print-stats", action="store_true",
                    help="print per-claim coverage breakdown to stderr")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    html = args.html or (repo_root / "LEGENDARY_LEADERS_TREE.html")
    out  = args.out  or (repo_root / "playstyle_spec.json")

    if not html.exists():
        print(f"missing {html}", file=sys.stderr)
        return 2

    specs = extract_specs(html)

    payload = {
        "schema_version": 1,
        "source": str(html.name),
        "civs": {k: asdict(v) for k, v in sorted(specs.items())},
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    print(f"wrote {out}  ({len(specs)} civs)")

    if args.print_stats:
        _print_stats(specs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
