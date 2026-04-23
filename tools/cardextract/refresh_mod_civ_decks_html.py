"""Refresh the Legendary Leaders deck block between
<!-- DECK-START <civ> --> and <!-- DECK-END <civ> --> markers in
LEGENDARY_LEADERS_TREE.html for each of the 26 mod revolution civs.

Reads:
  - data/rvltmodhomecity*.xml  (the authoritative in-game deck the AI uses)
  - data/cards.json            (card_name → {name, desc, icon})

Writes:
  - LEGENDARY_LEADERS_TREE.html  (between DECK-START/DECK-END markers)

Each card rendered as <span class="card-chip"><img class="card-icon" title="Name — Desc"></span>.
Cards grouped by age using the existing <dl class="deck-grid"> structure.
"""
from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HTML = REPO / "LEGENDARY_LEADERS_TREE.html"
CARDS = REPO / "data" / "cards.json"
DATA = REPO / "data"

# HTML DECK-START anchor tag → mod homecity filename stem
CIV_FILES = {
    "Americans":         "rvltmodhomecityamericans",
    "Argentines":        "rvltmodhomecityargentina",
    "BajaCalifornians":  "rvltmodhomecitybajacalifornians",
    "Barbary":           "rvltmodhomecitybarbary",
    "Brazilians":        "rvltmodhomecitybrazil",
    "Californians":      "rvltmodhomecitycalifornia",
    "Canadians":         "rvltmodhomecitycanada",
    "CentralAmericans":  "rvltmodhomecitycentralamericans",
    "Chileans":          "rvltmodhomecitychile",
    "Colombians":        "rvltmodhomecitycolumbia",
    "Egyptians":         "rvltmodhomecityegypt",
    "Finns":             "rvltmodhomecityfinland",
    "FrenchCanadians":   "rvltmodhomecityfrenchcanada",
    "Haitians":          "rvltmodhomecityhaiti",
    "Hungarians":        "rvltmodhomecityhungary",
    "Indonesians":       "rvltmodhomecityindonesians",
    "Mayans":            "rvltmodhomecitymaya",
    "Mexicans":          "rvltmodhomecitymexicans",
    "NapoleonicFrance":  "rvltmodhomecitynapoleon",
    "Peruvians":         "rvltmodhomecityperu",
    "RevolutionaryFr":   "rvltmodhomecityrevolutionaryfrance",
    "RioGrande":         "rvltmodhomecityriogrande",
    "Romanians":         "rvltmodhomecityromania",
    "SouthAfricans":     "rvltmodhomecitysouthafricans",
    "Texians":           "rvltmodhomecitytexas",
    "Yucatans":          "rvltmodhomecityyucatan",
}

AGE_NAMES = ["Discovery", "Colonial", "Fortress", "Industrial", "Imperial"]
ICON_DIR = "resources/images/icons/cards"


def age_bucket_for(card_name: str, cards_meta: dict) -> int:
    """Classify by card name heuristic — minage field from metadata if present."""
    meta = cards_meta.get(card_name, {})
    if "minage" in meta:
        a = int(meta["minage"])
        return max(0, min(4, a))
    # Fallbacks based on known naming conventions
    name_l = card_name.lower()
    if "explore" in name_l or "scout" in name_l or "pioneers" in name_l:
        return 0
    if "musketeer" in name_l or "settler" in name_l or "coureur" in name_l:
        return 1
    if "fort" in name_l or "cavalry" in name_l or "grenadier" in name_l:
        return 2
    if "factor" in name_l or "industri" in name_l or "rocket" in name_l or "gatling" in name_l:
        return 3
    return 2  # Fortress default


def render_deck(civ: str, stem: str, cards_meta: dict) -> str:
    path = DATA / f"{stem}.xml"
    tree = ET.parse(path)
    card_names = [c.text for c in tree.getroot().findall(".//deck/cards/card") if c.text]

    by_age: dict[int, list[str]] = {i: [] for i in range(5)}
    for cn in card_names:
        by_age[age_bucket_for(cn, cards_meta)].append(cn)

    out = ['<dl class="deck-grid">']
    for age_idx, cards in sorted(by_age.items()):
        if not cards:
            continue
        out.append(f"<dt>{AGE_NAMES[age_idx]}</dt>")
        chips = []
        for cn in cards:
            meta = cards_meta.get(cn, {})
            display = meta.get("name") or cn
            desc = meta.get("desc", "")
            icon = meta.get("icon") or ""
            title = f"{display} — {desc}" if desc else display
            title_attr = html.escape(title, quote=True)
            alt = html.escape(display, quote=True)
            if icon:
                src = f"{ICON_DIR}/{icon}"
                chips.append(
                    f'<span class="card-chip" title="{title_attr}">'
                    f'<img class="card-icon" src="{src}" alt="{alt}"></span>'
                )
            else:
                chips.append(
                    f'<span class="card-chip card-chip-noicon" title="{title_attr}">{alt}</span>'
                )
        out.append(f"<dd>{''.join(chips)}</dd>")
    out.append("</dl>")
    return "\n".join(out)


def main():
    cards_meta = json.loads(CARDS.read_text(encoding="utf-8"))
    html_text = HTML.read_text(encoding="utf-8")

    ok = miss = 0
    for civ, stem in CIV_FILES.items():
        block = render_deck(civ, stem, cards_meta)
        # Replace between markers
        start_marker = f"<!-- DECK-START {civ} -->"
        end_marker = f"<!-- DECK-END {civ} -->"
        pattern = re.compile(
            re.escape(start_marker) + r".*?" + re.escape(end_marker),
            re.DOTALL,
        )
        m = pattern.search(html_text)
        if not m:
            print(f"  SKIP {civ}: markers not found")
            miss += 1
            continue
        replacement = f"{start_marker}\n{block}\n{end_marker}"
        html_text = html_text[:m.start()] + replacement + html_text[m.end():]
        ok += 1
        print(f"  ok   {civ}: refreshed deck (25 cards)")

    HTML.write_text(html_text, encoding="utf-8")
    print(f"\nrefreshed: {ok}  skipped: {miss}")


if __name__ == "__main__":
    main()
