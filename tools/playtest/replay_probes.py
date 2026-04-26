"""Post-match validator for in-game runtime probes.

When you finish a game and save the .age3Yrec replay, every CPU AI has
broadcast two probes via `aiChat()` from the Legendary Leaders XS hooks:

  meta.leader_assigned   — fired at the end of llAssignLeaderIdentity()
                           Carries: civ_name, leader, chatset
  meta.buildstyle        — fired at the end of llApplyBuildStyleForActiveCiv()
                           Carries: terrain_primary, terrain_secondary,
                           terrain_bias, heading, heading_bias, ...

This script reads the replay file, extracts every `[LLP v=2 …]` chat line,
and cross-checks the values against `tools.playtest.expectations`. Any
mismatch is a real bug in the game-side dispatch / build-style mapping.

The .age3Yrec is a binary container, but chat strings are stored verbatim
as ASCII somewhere in the payload — we just regex over the raw bytes,
which is what AoE3 replay parsers traditionally do for chat extraction.

Usage:
    python3 -m tools.playtest.replay_probes path/to/game.age3Yrec
    python3 -m tools.playtest.replay_probes path/to/game.age3Yrec --strict
    python3 -m tools.playtest.replay_probes path/to/log.txt    # any text file works too

Exit code: 0 = all probes match, 1 = mismatch, 2 = no probes found.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.playtest.expectations import (  # noqa: E402
    CIV_LABELS,
    CivExpectation,
    load_expectations,
)


# `[LLP v=2 t=<int> p=<int> civ=<civ> ldr=<ldr> tag=<domain.name>] <tail>`
# We match against bytes so the same regex can scan both raw .age3Yrec
# binary payloads and plain-text log files.
PROBE_RE = re.compile(
    rb"\[LLP v=2 t=(?P<t>\d+) p=(?P<p>\d+) civ=(?P<civ>\S+) "
    rb"ldr=(?P<ldr>\S+) tag=(?P<tag>\S+)\]\s*(?P<tail>[ -~]*)"  # tail = printable ASCII only
)
KV_RE = re.compile(rb"(\w+)=([^\s]+)")


@dataclass
class ProbeRecord:
    time: int
    player: int
    civ: str
    leader: str
    tag: str
    fields: dict[str, str]


def parse_probes(data: bytes) -> list[ProbeRecord]:
    out: list[ProbeRecord] = []
    for m in PROBE_RE.finditer(data):
        tail = m.group("tail")
        fields = {k.decode(): v.decode() for k, v in KV_RE.findall(tail)}
        out.append(
            ProbeRecord(
                time=int(m.group("t")),
                player=int(m.group("p")),
                civ=m.group("civ").decode(),
                leader=m.group("ldr").decode(),
                tag=m.group("tag").decode(),
                fields=fields,
            )
        )
    return out


def _expect_index() -> dict[str, CivExpectation]:
    """Index expectations by both engine civ_id (cCivBritish) and rvltName
    (RvltModBrazil) — the probe carries `civ=<rvltName>` from kbGetCivName(),
    which for base civs is e.g. "British", and for revolutions is the
    "RvltModBrazil" form. So we index by every plausible key shape."""
    out: dict[str, CivExpectation] = {}
    for e in load_expectations():
        out[e.civ_id] = e
        out[e.label] = e
        # Strip "cCiv" prefix for base civs ("cCivBritish" -> "British").
        if e.civ_id.startswith("cCiv"):
            out[e.civ_id[4:]] = e
        # Drop "DE"/"XP" prefixes that some base civ_ids carry.
        m = re.match(r"^cCiv(?:DE|XP)?(.*)$", e.civ_id)
        if m:
            out[m.group(1)] = out.get(m.group(1), e)
    return out


def validate(probes: list[ProbeRecord]) -> tuple[list[str], list[str]]:
    """Return (issues, summary_lines)."""
    expected = _expect_index()

    by_player: dict[int, dict[str, ProbeRecord]] = defaultdict(dict)
    for p in probes:
        by_player[p.player][p.tag] = p

    issues: list[str] = []
    summary: list[str] = []

    if not by_player:
        issues.append("no [LLP v=2] probes found — was cLLReplayProbes set true?")
        return issues, summary

    for pid in sorted(by_player):
        tags = by_player[pid]
        leader_p = tags.get("meta.leader_assigned")
        build_p = tags.get("meta.buildstyle")

        civ_label = (leader_p or build_p).civ if (leader_p or build_p) else "?"
        line = f"  p{pid}  civ={civ_label}"

        if leader_p is None:
            issues.append(f"p{pid}: missing meta.leader_assigned probe")
        if build_p is None:
            issues.append(f"p{pid}: missing meta.buildstyle probe")
        if leader_p is None or build_p is None:
            summary.append(line + "  [INCOMPLETE]")
            continue

        # Leader name must not be the unassigned-* sentinel.
        leader_name = leader_p.fields.get("leader", leader_p.leader)
        if leader_name.startswith("unassigned-"):
            issues.append(
                f"p{pid}: civ {civ_label} hit the unassigned fallback "
                f"(leader={leader_name}). Add a dispatch entry to "
                f"llAssignLeaderIdentity()."
            )

        exp = expected.get(civ_label) or expected.get(leader_p.fields.get("civ_name", ""))
        if exp is None:
            summary.append(line + f"  ldr={leader_name}  [no expectation row]")
            continue

        # Leader key check
        if leader_name != exp.leader_key:
            issues.append(
                f"p{pid} {civ_label}: leader_key mismatch "
                f"(expected {exp.leader_key}, got {leader_name})"
            )

        # Build-style check (terrain + heading + biases)
        b = build_p.fields
        for key, want in (
            ("terrain_primary", exp.terrain_primary),
            ("terrain_secondary", exp.terrain_secondary),
            ("heading", exp.heading),
        ):
            got = b.get(key)
            if got != want:
                issues.append(
                    f"p{pid} {civ_label}: {key} mismatch (expected {want}, got {got})"
                )

        try:
            tb = float(b.get("terrain_bias", "nan"))
            if abs(tb - exp.terrain_strength) > 0.001:
                issues.append(
                    f"p{pid} {civ_label}: terrain_bias mismatch "
                    f"(expected {exp.terrain_strength}, got {tb})"
                )
        except ValueError:
            issues.append(f"p{pid} {civ_label}: terrain_bias not numeric ({b.get('terrain_bias')!r})")

        try:
            hb = float(b.get("heading_bias", "nan"))
            if abs(hb - exp.heading_strength) > 0.001:
                issues.append(
                    f"p{pid} {civ_label}: heading_bias mismatch "
                    f"(expected {exp.heading_strength}, got {hb})"
                )
        except ValueError:
            issues.append(f"p{pid} {civ_label}: heading_bias not numeric ({b.get('heading_bias')!r})")

        summary.append(
            f"  p{pid}  {CIV_LABELS.get(exp.civ_id, exp.label):<24s}  "
            f"ldr={leader_name:<22s}  "
            f"terr={b.get('terrain_primary','?')}+{b.get('terrain_secondary','?')} "
            f"({b.get('terrain_bias','?')})  "
            f"head={b.get('heading','?')} ({b.get('heading_bias','?')})"
        )

    return issues, summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", type=Path, help=".age3Yrec replay file or text log")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any AI lacks probes")
    args = ap.parse_args()

    if not args.path.exists():
        print(f"file not found: {args.path}", file=sys.stderr)
        return 2

    data = args.path.read_bytes()
    probes = parse_probes(data)

    print(f"replay probes: {args.path}")
    print(f"  total probe lines: {len(probes)}")
    print(f"  AI players covered: {len({p.player for p in probes})}")
    print()

    issues, summary = validate(probes)
    if summary:
        print("Per-AI snapshot:")
        for line in summary:
            print(line)
        print()

    if not probes:
        return 2

    if issues:
        print(f"FAIL — {len(issues)} issue(s):")
        for line in issues:
            print(f"  - {line}")
        return 1

    print("PASS — every AI loaded its expected leader and build-style profile.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
