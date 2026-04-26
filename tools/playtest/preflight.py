"""Print the per-civ ground truth so you can spot-check while playing.

Usage:
    python3 -m tools.playtest.preflight              # full table
    python3 -m tools.playtest.preflight --civ British  # one civ, full detail
    python3 -m tools.playtest.preflight --revolutions  # only the 26 rvlt civs
    python3 -m tools.playtest.preflight --markdown     # markdown table

The output is the answer key. While the game is open, alt-tab to a
terminal showing this table and verify each row against what you see:

  * the lobby leader portrait + name match `leader_key`
  * the deck shown in Deck Builder matches `deck_name`
  * the AI's first 4–5 buildings cluster in the direction implied by
    `terrain` and `heading`
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.playtest.expectations import (  # noqa: E402
    CivExpectation,
    load_expectations,
)


def _short_terrain(t: str) -> str:
    return t.replace("cLLTerrain", "")


def _short_heading(h: str) -> str:
    return h.replace("cLLHeading", "")


def _water_arrow(b: int) -> str:
    if b > 0:
        return "→ water"
    if b < 0:
        return "→ inland"
    return "neutral"


def _print_table(rows: list[CivExpectation], markdown: bool = False) -> None:
    headers = (
        "Civ",
        "Leader",
        "Deck",
        "Terrain (str)",
        "Heading (str)",
        "Bias",
    )
    body: list[tuple[str, ...]] = []
    for e in rows:
        body.append(
            (
                e.label,
                e.leader_key,
                e.deck_name,
                f"{_short_terrain(e.terrain_primary)}+{_short_terrain(e.terrain_secondary)} ({e.terrain_strength:.2f})",
                f"{_short_heading(e.heading)} ({e.heading_strength:.2f})",
                f"{_water_arrow(e.water_bias)} / {e.heading_axis}",
            )
        )

    if markdown:
        print("| " + " | ".join(headers) + " |")
        print("|" + "|".join(["---"] * len(headers)) + "|")
        for row in body:
            print("| " + " | ".join(row) + " |")
        return

    widths = [
        max(len(h), max((len(r[i]) for r in body), default=0))
        for i, h in enumerate(headers)
    ]
    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in body:
        print(fmt.format(*row))


def _print_detail(e: CivExpectation) -> None:
    print(f"== {e.label} ({e.civ_id}) ==")
    print(f"  leader portrait / name override : {e.leader_key}")
    print(f"  Deck Builder slot name          : {e.deck_name!r}")
    print(f"  Preferred terrain (primary)     : {_short_terrain(e.terrain_primary)}")
    print(f"  Preferred terrain (secondary)   : {_short_terrain(e.terrain_secondary)}")
    print(f"  Terrain bias strength           : {e.terrain_strength:.2f}")
    print(f"  Expansion heading               : {_short_heading(e.heading)}")
    print(f"  Heading bias strength           : {e.heading_strength:.2f}")
    print(f"  Derived water-bias              : {_water_arrow(e.water_bias)}")
    print(f"  Derived heading axis            : {e.heading_axis}")
    print()
    print("  in-engine spot checks:")
    print(f"    [ ] lobby thumbnail shows portrait keyed '{e.leader_key}'")
    print(f"    [ ] match scoreboard / chat name match the lobby pick")
    print(f"    [ ] Deck Builder shows a deck named '{e.deck_name}'")
    expected_dir = (
        "toward water" if e.water_bias > 0
        else "toward inland" if e.water_bias < 0
        else "no preference"
    )
    print(f"    [ ] AI's first 4–5 buildings cluster {expected_dir} of TC")
    if e.heading_axis == "outward":
        print("    [ ] secondary TC pushes toward enemy (frontier doctrine)")
    elif e.heading_axis == "inward":
        print("    [ ] base stays compact, no forward TC")
    elif e.heading_axis == "tangent":
        print(f"    [ ] expansion runs along the {_short_heading(e.heading).replace('Along', '').replace('Up', 'up').lower()}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--civ", help="single civ label or id; prints detailed checklist")
    ap.add_argument("--revolutions", action="store_true", help="only show the 26 revolution civs")
    ap.add_argument("--base", action="store_true", help="only show the 22 base civs")
    ap.add_argument("--markdown", action="store_true", help="emit a markdown table")
    args = ap.parse_args()

    exps = load_expectations()

    if args.civ:
        wanted = args.civ.lower()
        match = next(
            (
                e for e in exps
                if e.civ_id.lower() == wanted
                or e.label.lower() == wanted
                or e.label.lower().startswith(wanted)
            ),
            None,
        )
        if match is None:
            print(f"no civ matched '{args.civ}'. Try one of:")
            for e in exps:
                print(f"  {e.label}  ({e.civ_id})")
            return 2
        _print_detail(match)
        return 0

    rows = exps
    if args.revolutions:
        rows = [e for e in exps if e.is_revolution]
    elif args.base:
        rows = [e for e in exps if not e.is_revolution]

    _print_table(rows, markdown=args.markdown)
    print()
    print(f"loaded {len(rows)} of {len(exps)} civ expectations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
