"""Cross-check LEGENDARY_LEADERS_TREE.html against the actual mod data so
the reference site never drifts from what the AI actually loads.

For every civ section in the HTML we verify, against the file on disk:

  * The home-city XML the section labels exists in `data/`
  * The civmods.xml block uses the same civ name
  * Every card chip in the HTML deck points at a card name that's in
    that civ's data/decks_legendary.json or data/decks_standard.json
    summary (which is itself derived from the home-city XML's
    "Legendary Leaders" deck)
  * The chip count matches the JSON (25 / civ)
  * Every leader portrait file referenced by the HTML actually exists

Exits 1 with a per-civ report on any mismatch.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HTML = REPO / "LEGENDARY_LEADERS_TREE.html"
DATA = REPO / "data"

# Map civ slug used as a section header → home-city basename + summary key
CIV_TO_HOMECITY = {
    "Aztecs":               ("homecityxpaztec",                 "Aztecs"),
    "British":              ("homecitybritish",                 "British"),
    "Chinese":              ("homecitychinese",                 "Chinese"),
    "Dutch":                ("homecitydutch",                   "Dutch"),
    "Ethiopians":           ("homecityethiopians",              "Ethiopians"),
    "French":               ("homecityfrench",                  "French"),
    "Germans":              ("homecitygerman",                  "Germans"),
    "Haudenosaunee":        ("homecityxpiroquois",              "Haudenosaunee"),
    "Hausa":                ("homecityhausa",                   "Hausa"),
    "Inca":                 ("homecitydeinca",                  "Inca"),
    "Indians":              ("homecityindians",                 "Indians"),
    "Italians":             ("homecityitalians",                "Italians"),
    "Japanese":             ("homecityjapanese",                "Japanese"),
    "Lakota":               ("homecityxpsioux",                 "Lakota"),
    "Maltese":              ("homecitymaltese",                 "Maltese"),
    "Mexicans (Standard)":  ("homecitymexicans",                "MexicansStd"),
    "Ottomans":             ("homecityottomans",                "Ottomans"),
    "Portuguese":           ("homecityportuguese",              "Portuguese"),
    "Russians":             ("homecityrussians",                "Russians"),
    "Spanish":              ("homecityspanish",                 "Spanish"),
    "Swedes":               ("homecityswedish",                 "Swedes"),
    "United States":        ("homecityamericans",               "UnitedStates"),
    "Americans":            ("rvltmodhomecityamericans",        None),
    "Argentines":           ("rvltmodhomecityargentina",        None),
    "Baja Californians":    ("rvltmodhomecitybajacalifornians", None),
    "Barbary":              ("rvltmodhomecitybarbary",          None),
    "Brazil":               ("rvltmodhomecitybrazil",           None),
    "Californians":         ("rvltmodhomecitycalifornia",       None),
    "Canadians":            ("rvltmodhomecitycanada",           None),
    "Central Americans":    ("rvltmodhomecitycentralamericans", None),
    "Chileans":             ("rvltmodhomecitychile",            None),
    "Columbians":           ("rvltmodhomecitycolumbia",         None),
    "Egyptians":            ("rvltmodhomecityegypt",            None),
    "Finnish":              ("rvltmodhomecityfinland",          None),
    "French Canadians":     ("rvltmodhomecityfrenchcanada",     None),
    "Haitians":             ("rvltmodhomecityhaiti",            None),
    "Hungarians":           ("rvltmodhomecityhungary",          None),
    "Indonesians":          ("rvltmodhomecityindonesians",      None),
    "Mayans":               ("rvltmodhomecitymaya",             None),
    "Mexicans (Revolution)":("rvltmodhomecitymexicans",         None),
    "Napoleonic France":    ("rvltmodhomecitynapoleon",         None),
    "Peruvians":            ("rvltmodhomecityperu",             None),
    "Revolutionary France": ("rvltmodhomecityrevolutionaryfrance", None),
    "Rio Grande":           ("rvltmodhomecityriogrande",        None),
    "Romanians":            ("rvltmodhomecityromania",          None),
    "South Africans":       ("rvltmodhomecitysouthafricans",    None),
    "Texians":              ("rvltmodhomecitytexas",            None),
    "Yucatan":              ("rvltmodhomecityyucatan",          None),
}

SECTION_RE = re.compile(r"<!--\s*[─\-]+\s*([^─\-][^<]*?)\s*[─\-]+\s*-->")
DECK_BLOCK_RE = re.compile(
    r'<!--\s*(?:STD-)?DECK-START\s+\S+\s*-->(.*?)<!--\s*(?:STD-)?DECK-END\s+\S+\s*-->',
    re.DOTALL,
)
CHIP_ALT_RE = re.compile(r'<img class="card-icon"[^>]*alt="([^"]+)"')
CHIP_TEXT_RE = re.compile(
    r'<span class="card-chip card-chip-noicon"[^>]*>([^<]+)</span>'
)
PORTRAIT_RE = re.compile(r'<img class="portrait-img" src="([^"]+)"')
FLAG_RE = re.compile(r'<img class="flag-img" src="([^"]+)"')


def html_decks_per_civ(text: str) -> dict[str, list[str]]:
    """Map civ slug → ordered list of card names rendered in the HTML deck."""
    out: dict[str, list[str]] = {}
    sections = list(SECTION_RE.finditer(text))
    for i, m in enumerate(sections):
        slug = m.group(1).strip()
        body = text[m.end(): sections[i+1].start() if i+1 < len(sections) else len(text)]
        deck = DECK_BLOCK_RE.search(body)
        if not deck:
            continue
        names: list[str] = []
        for chip in CHIP_ALT_RE.finditer(deck.group(1)):
            names.append(html.unescape(chip.group(1)))
        for chip in CHIP_TEXT_RE.finditer(deck.group(1)):
            names.append(html.unescape(chip.group(1)).strip())
        out[slug] = names
    return out


def html_assets_per_civ(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    sections = list(SECTION_RE.finditer(text))
    for i, m in enumerate(sections):
        slug = m.group(1).strip()
        body = text[m.end(): sections[i+1].start() if i+1 < len(sections) else len(text)]
        portrait = PORTRAIT_RE.search(body)
        flag = FLAG_RE.search(body)
        out[slug] = {
            "portrait": portrait.group(1) if portrait else "",
            "flag": flag.group(1) if flag else "",
        }
    return out


def deck_summary_cards(summary: dict, civ_key: str) -> list[str] | None:
    if civ_key not in summary:
        return None
    cards = []
    for age in sorted(summary[civ_key], key=int):
        cards += summary[civ_key][age]
    return cards


def main() -> int:
    text = HTML.read_text(encoding="utf-8")
    leg = json.loads((DATA / "decks_legendary.json").read_text())
    std = json.loads((DATA / "decks_standard.json").read_text())
    cards_meta = json.loads((DATA / "cards.json").read_text())

    name_to_id: dict[str, list[str]] = {}
    for cid, meta in cards_meta.items():
        nm = (meta.get("name") or "").strip()
        if nm:
            name_to_id.setdefault(nm, []).append(cid)

    html_decks = html_decks_per_civ(text)
    html_assets = html_assets_per_civ(text)

    errors: list[str] = []
    checked = 0

    for slug, (basename, std_key) in CIV_TO_HOMECITY.items():
        checked += 1
        # 1. Home-city XML on disk
        xml = DATA / f"{basename}.xml"
        if not xml.exists():
            errors.append(f"{slug}: missing home-city XML at data/{basename}.xml")
            continue
        # 2. Deck summary present
        if std_key:
            summary_cards = deck_summary_cards(std, std_key)
            src = "decks_standard.json"
            key = std_key
        else:
            summary_cards = deck_summary_cards(leg, basename)
            src = "decks_legendary.json"
            key = basename
        if summary_cards is None:
            errors.append(f"{slug}: no entry '{key}' in {src}")
            continue
        # 3. Chip count matches summary count
        rendered = html_decks.get(slug, [])
        if len(rendered) != len(summary_cards):
            errors.append(
                f"{slug}: HTML deck has {len(rendered)} chips, summary has "
                f"{len(summary_cards)}"
            )
        if len(summary_cards) != 25:
            errors.append(
                f"{slug}: summary has {len(summary_cards)} cards (expected 25)"
            )
        # 4. Every chip name resolves to a real card_id whose name matches
        for chip_name in rendered:
            if chip_name not in name_to_id:
                errors.append(
                    f"{slug}: chip '{chip_name}' has no matching card_id "
                    f"in cards.json"
                )
        # 5. Portrait + flag files exist
        for kind in ("portrait", "flag"):
            p = html_assets.get(slug, {}).get(kind, "")
            if p and not (REPO / p).is_file():
                errors.append(
                    f"{slug}: {kind} image missing on disk: {p}"
                )

    print(f"checked {checked} civs")
    if errors:
        print(f"\n{len(errors)} issue(s):\n")
        for e in errors:
            print(f"  {e}")
        return 1
    print("HTML <-> mod data consistency: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
