"""Update each civ block's `Buildstyle: <NAME>` heading in the HTML to match
the new bespoke archetype assignment in leaderCommon.xs.

Each civ block in a_new_world.html is anchored by a
`<!-- ──────────── <CIV> ──────────── -->` section comment. We rewrite the
FIRST `Buildstyle: ...` label that follows that comment to its bespoke name.
The descriptive `<dl class="buildparam">` knob values are left untouched —
they already carry per-civ commentary that would be lossy to regenerate.
"""
from __future__ import annotations

import re
from pathlib import Path

HTML = Path(__file__).resolve().parents[2] / "a_new_world.html"

# civ-comment slug (between the box-drawing dashes) → bespoke archetype label
LABEL = {
    # ── Standard 22 ──
    "Aztecs":              "Jungle Guerrilla Network",
    "British":             "Naval Mercantile Compound",
    "Chinese":             "Compact Fortified Core",
    "Dutch":               "Naval Mercantile Compound",
    "Ethiopians":          "Highland Citadel",
    "French":              "Compact Fortified Core",
    "Germans":             "Siege Train Concentration",
    "Haudenosaunee":       "Shrine or Trade Node Spread",
    "Hausa":               "Distributed Economic Network",
    "Inca":                "Andean Terrace Fortress",
    "Indians":             "Shrine or Trade Node Spread",
    "Italians":            "Republican Levee",
    "Japanese":            "Shrine or Trade Node Spread",
    "Lakota":              "Steppe Cavalry Wedge",
    "Maltese":             "Highland Citadel",
    "Mexicans (Standard)": "Republican Levee",
    "Ottomans":            "Siege Train Concentration",
    "Portuguese":          "Naval Mercantile Compound",
    "Russians":            "Cossack Voisko",
    "Spanish":             "Forward Operational Line",
    "Swedes":              "Siege Train Concentration",
    "United States":       "Republican Levee",
    # ── Revolution 26 ──
    "Americans":           "Republican Levee",
    "Argentines":          "Forward Operational Line",
    "Baja Californians":   "Mobile Frontier Scatter",
    "Barbary":             "Naval Mercantile Compound",
    "Brazil":              "Distributed Economic Network",
    "Californians":        "Distributed Economic Network",
    "Canadians":           "Compact Fortified Core",
    "Central Americans":   "Distributed Economic Network",
    "Chileans":            "Andean Terrace Fortress",
    "Colombians":          "Forward Operational Line",
    "Columbians":          "Forward Operational Line",
    "Egyptians":           "Highland Citadel",
    "Finns":               "Compact Fortified Core",
    "Finnish":             "Compact Fortified Core",
    "French Canadians":    "Civic Militia Center",
    "Haitians":            "Jungle Guerrilla Network",
    "Hungarians":          "Steppe Cavalry Wedge",
    "Indonesians":         "Shrine or Trade Node Spread",
    "Mayans":              "Jungle Guerrilla Network",
    "Mexicans (Revolution)": "Republican Levee",
    "Napoleon":            "Forward Operational Line",
    "Napoleonic France":   "Forward Operational Line",
    "Peruvians":           "Andean Terrace Fortress",
    "Revolutionary France":"Republican Levee",
    "Rio Grande":          "Mobile Frontier Scatter",
    "Romanians":           "Civic Militia Center",
    "South Africans":      "Naval Mercantile Compound",
    "Texians":             "Forward Operational Line",
    "Yucatans":            "Jungle Guerrilla Network",
    "Yucatan":             "Jungle Guerrilla Network",
}


def main() -> int:
    text = HTML.read_text(encoding="utf-8")
    # Find all civ section comments with their positions, in order.
    civ_re = re.compile(r"<!--\s*[─-]+\s*([^─\-][^<]*?)\s*[─-]+\s*-->")
    headings = list(civ_re.finditer(text))
    if not headings:
        raise RuntimeError("no civ section comments found")

    label_re = re.compile(
        r'(<span class="cat-label">Buildstyle:\s*)([^<]+)(</span>)'
    )

    edits: list[tuple[int, int, str]] = []
    for i, h in enumerate(headings):
        slug = h.group(1).strip()
        if slug not in LABEL:
            print(f"  SKIP unrecognised civ heading: {slug!r}")
            continue
        block_start = h.end()
        block_end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        m = label_re.search(text, block_start, block_end)
        if not m:
            # Some sections (intermediate `<details class="section-head">`
            # headers) don't carry a Buildstyle label themselves.
            continue
        new_name = LABEL[slug]
        if m.group(2).strip() == new_name:
            continue
        edits.append((m.start(2), m.end(2), new_name))
        print(f"  {slug:22s}  {m.group(2).strip():32s} -> {new_name}")

    # Apply in reverse so indices stay valid
    for start, end, new in reversed(edits):
        text = text[:start] + new + text[end:]
    HTML.write_text(text, encoding="utf-8")
    print(f"\nrelabelled {len(edits)} civ headings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
