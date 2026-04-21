"""Replace the variable-dump <dl class="buildparam"> inside every civ's
Buildstyle <details> block with a plain-English prose paragraph that explains
how the AI is wired to build for that archetype.

The HTML's existing pattern is:

    <details><summary><span class="cat-label">Buildstyle: <NAME></span></summary>
    <dl class="buildparam">
      <dt>Wall Level</dt><dd>0</dd>
      ...
    </dl>
    </details>

After this script:

    <details><summary><span class="cat-label">Buildstyle: <NAME></span></summary>
    <!-- BS-PROSE-START -->
    <p class="bs-prose">…prose for NAME…</p>
    <!-- BS-PROSE-END -->
    </details>

Idempotent — re-runs replace any existing BS-PROSE block.
"""
from __future__ import annotations

import re
from pathlib import Path

HTML = Path(__file__).resolve().parents[2] / "LEGENDARY_LEADERS_TREE.html"

PROSE: dict[str, str] = {
    "Compact Fortified Core":
        "Clusters every production building tight around the Town Center, walls early "
        "with stone, and only walks out for nearby resources. Expects to be sieged, not "
        "skirmished &mdash; the AI hunkers in and counter-attacks from a hardened core.",

    "Forward Operational Line":
        "Pushes barracks, stables, and outposts up toward the map's contested edge, "
        "leaving the home base lightly fortified. Sustained pressure is the doctrine: "
        "shipments rally to the forward base, and lost ground is re-walled rather than "
        "abandoned.",

    "Mobile Frontier Scatter":
        "Spreads buildings far and wide, plants extra Town Centers and Trading Posts on "
        "the map perimeter, and skips walls almost entirely. Built for raid-economy and "
        "map control rather than turtling.",

    "Distributed Economic Network":
        "Scatters Mills, Plantations, and Markets across multiple resource patches so "
        "production never bottlenecks on one site. Light walling, heavy investment in "
        "Market upgrades, and a constant villager trickle to the most under-worked node.",

    "Civic Militia Center":
        "Tight civic core. The AI relies on settler-callable defenses &mdash; Town Centers "
        "and Outposts that summon militia &mdash; rather than a forward army. Reactive: "
        "hits hard when threatened, less aggressive on the open map.",

    "Shrine or Trade Node Spread":
        "Plants shrines, Trading Posts, or fishing posts the moment the route is found, "
        "then defends them with isolated towers and fast cavalry response. The XP and "
        "resource trickle from these structures funds everything else.",

    "Jungle Guerrilla Network":
        "Hugs natural chokes &mdash; cliffs, jungle, river bends &mdash; and substitutes "
        "War Huts and causeways for walls. Stages quick, repeated infantry strikes from "
        "forward warbands and refuses to fight in the open.",

    "Naval Mercantile Compound":
        "Builds the docks first. Two or three Docks plus a full fishing fleet come before "
        "the second barracks, then a wall ring locks down the harbor. Land army arrives "
        "via naval shipments and mercenary contracts &mdash; the home city pays for the "
        "war.",

    "Highland Citadel":
        "Fortifies a single high-ground position with stone walls, layered towers, and a "
        "fort. Slow to expand and slow to push, but extremely hard to dislodge once "
        "entrenched. Builds wide only after the citadel is unbreakable.",

    "Siege Train Concentration":
        "Over-builds Artillery Foundries and stockpiles cannons. Every push is a slow "
        "siege column with infantry escort, and walls are stone-and-forward to give the "
        "guns a safe staging line.",

    "Steppe Cavalry Wedge":
        "Over-builds Stables and runs cavalry-heavy compositions. The base is loosely "
        "walled so horsemen can pour out fast, and the AI keeps constant pressure rather "
        "than waiting for a deathball.",

    "Cossack Voisko":
        "Plays a wide, mobile game: cheap horsemen raid in roving bands, the home base "
        "leans on Blockhouses rather than full stone walls, and the AI rushes to a third "
        "Town Center to fuel the cavalry stream.",

    "Republican Levee":
        "Mass-produces cheap line infantry from many barracks and trains General units to "
        "inspire them. Civic-style layout &mdash; production hugs the Town Center, "
        "Outposts call up militia, and shipments favor more of the same line over elite "
        "alternatives.",

    "Andean Terrace Fortress":
        "Tier-walls the high ground in two or three concentric rings, plants Kallankas "
        "and Tambos in the gaps, and never overextends. A slow snowball to a tightly "
        "defended Industrial timing rather than an early aggressive game.",
}

# Match a Buildstyle <details> block — capture the archetype name and the
# original buildparam DL.  Non-greedy on body so we stop at the first </details>.
BLOCK_RE = re.compile(
    r'(<details><summary><span class="cat-label">Buildstyle:\s*'
    r'(?P<name>[^<]+?)\s*</span></summary>\s*)'
    r'(?P<body>.*?)'
    r'(\s*</details>)',
    re.DOTALL,
)

PROSE_BLOCK_RE = re.compile(
    r'<!-- BS-PROSE-START -->.*?<!-- BS-PROSE-END -->',
    re.DOTALL,
)


def render_prose(name: str) -> str:
    paragraph = PROSE.get(name)
    if not paragraph:
        return f'<!-- BS-PROSE-START -->\n<p class="bs-prose"><em>(no prose for {name})</em></p>\n<!-- BS-PROSE-END -->'
    return (
        f'<!-- BS-PROSE-START -->\n'
        f'<p class="bs-prose">{paragraph}</p>\n'
        f'<!-- BS-PROSE-END -->'
    )


CSS_BLOCK = ("/* BS-PROSE-CSS-START */\n"
             ".bs-prose{margin:6px 2px 4px;font-size:.9rem;line-height:1.45;color:var(--fg)}\n"
             "/* BS-PROSE-CSS-END */\n")


def ensure_css(text: str) -> str:
    if "BS-PROSE-CSS-START" in text:
        return re.sub(
            r"/\* BS-PROSE-CSS-START \*/.*?/\* BS-PROSE-CSS-END \*/\n?",
            CSS_BLOCK,
            text,
            count=1,
            flags=re.DOTALL,
        )
    return text.replace("</style>", CSS_BLOCK + "</style>", 1)


def replace_block(match: re.Match) -> str:
    head = match.group(1)
    name = match.group("name").strip()
    body = match.group("body")
    tail = match.group(4)
    new_body = render_prose(name)
    # If body already contains a prose block, keep our new one and drop the rest.
    return head + new_body + tail


def main() -> int:
    text = HTML.read_text(encoding="utf-8")
    text = ensure_css(text)
    new_text, n = BLOCK_RE.subn(replace_block, text)
    HTML.write_text(new_text, encoding="utf-8")
    print(f"rewrote {n} Buildstyle <details> blocks to prose")
    # Tell us if any archetype name showed up that we don't have prose for.
    missing = set()
    for m in BLOCK_RE.finditer(new_text):
        name = m.group("name").strip()
        if name not in PROSE:
            missing.add(name)
    if missing:
        print("\nMissing prose for these archetype names (please add to PROSE):")
        for n in sorted(missing):
            print(f"  - {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
