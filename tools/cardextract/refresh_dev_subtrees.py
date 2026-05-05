"""Refresh the per-nation Development subtree in a_new_world.html.

Inserts a fifth `<details>` block under each nation-node summarising the 17
in-game identity surfaces (lobby name + portrait + blurb, deck-builder cards,
scoreboard flag/name, HUD HC button, player-summary flag/HC/deck, diplomacy
portrait/tooltip, chat portrait/name, end-game flag/name) with the exact
asset path or string ID that backs each surface. Lets a reviewer scan one
panel per civ and audit visual consistency without grepping the codebase.

Reads:
  - data/civmods.xml                                 (rev-civ UI fields)
  - data/strings/english/stringmods.xml              (mod string overrides)
  - game/ai/*.personality                            (per-leader nameID, icon, chatset)
  - game/ai/chatsetsmods.xml                         (chatset → leader)
  - data/decks_legendary.json + data/decks_standard.json + data/cards.json
  - data/homecity*.xml + data/rvltmodhomecity*.xml   (HC name/civ/flag)
  - tools/validation/validate_html_vs_mod.CIV_TO_HOMECITY  (canonical 48 slugs)

Writes:
  - a_new_world.html
        Idempotently rewrites the block bounded by
        `<!-- DEV-START name="<slug>" -->` ... `<!-- DEV-END name="<slug>" -->`
        inside each nation-node. Inserts the markers (and the wrapping
        `<details>` for the subtree) on first run.

CLI:
  python3 tools/cardextract/refresh_dev_subtrees.py [--check]
        --check  exit non-zero if any subtree would change (CI drift gate).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

# Reuse existing parsers/loaders.
from tools.validation.common import (  # noqa: E402
    child_elements,
    find_first_child,
    get_child_text,
    local_name,
)
from tools.validation.validate_html_vs_mod import CIV_TO_HOMECITY  # noqa: E402
from tools.validation.validate_personality_overrides import (  # noqa: E402
    load_string_table,
    parse_personality,
)

HTML_PATH = REPO / "a_new_world.html"
CIVMODS = REPO / "data" / "civmods.xml"
STRINGS = REPO / "data" / "strings" / "english" / "stringmods.xml"
CARDS = REPO / "data" / "cards.json"
DECKS_LEG = REPO / "data" / "decks_legendary.json"
DECKS_STD = REPO / "data" / "decks_standard.json"
AI_DIR = REPO / "game" / "ai"
CHATSETS = AI_DIR / "chatsetsmods.xml"

AGE_NAMES = ["Discovery", "Colonial", "Fortress", "Industrial", "Imperial"]

# slug (CIV_TO_HOMECITY key) → (engine civ-token used in <forcedciv>, personality file stem)
# Built from forcedciv values empirically + manual aliases. Skipped slugs (Americans /
# Mexicans (Revolution)) are deferred sections without HTML nation-nodes — see
# validate_html_reference._DEFERRED_SECTION.
SLUG_TO_LEADER: dict[str, tuple[str, str]] = {
    # Base civs
    "Aztecs":             ("XPAztec",        "montezuma"),
    "British":            ("british",        "wellington"),
    "Chinese":            ("chinese",        "kangxi"),
    "Dutch":              ("dutch",          "maurice"),
    "Ethiopians":         ("DEEthiopians",   "menelik"),
    "French":             ("french",         "napoleon"),
    "Germans":            ("germans",        "Frederick"),
    "Haudenosaunee":      ("XPIroquois",     "Hiawatha"),
    "Hausa":              ("DEHausa",        "usman"),
    "Inca":               ("DEInca",         "pachacuti"),
    "Indians":            ("indians",        "shivaji"),
    "Italians":           ("DEItalians",     "garibaldi"),
    "Japanese":           ("japanese",       "tokugawa"),
    "Lakota":             ("XPSioux",        "crazyhorse"),
    "Maltese":            ("DEMaltese",      "jean"),
    "Mexicans (Standard)": ("demexicans",    "hidalgo"),
    "Ottomans":           ("ottomans",       "Suleiman"),
    "Portuguese":         ("portuguese",     "henry"),
    "Russians":           ("russians",       "catherine"),
    "Spanish":            ("spanish",        "isabella"),
    "Swedes":             ("deswedish",      "Gustav"),
    "United States":      ("deamericans",    "washington"),
    # Revolution civs (slug → RvltMod canonical Name + personality stem)
    "Argentines":         ("RvltModArgentines",         "rvltmodargentines"),
    "Baja Californians":  ("RvltModBajaCalifornians",   "rvltmodbajacalifornians"),
    "Barbary":            ("RvltModBarbary",            "rvltmodbarbary"),
    "Brazil":             ("RvltModBrazil",             "rvltmodbrazil"),
    "Californians":       ("RvltModCalifornians",       "rvltmodcalifornians"),
    "Canadians":          ("RvltModCanadians",          "rvltmodcanadians"),
    "Central Americans":  ("RvltModCentralAmericans",   "rvltmodcentralamericans"),
    "Chileans":           ("RvltModChileans",           "rvltmodchileans"),
    "Columbians":         ("RvltModColumbians",         "rvltmodcolumbians"),
    "Egyptians":          ("RvltModEgyptians",          "rvltmodegyptians"),
    "Finnish":            ("RvltModFinnish",            "rvltmodfinnish"),
    "French Canadians":   ("RvltModFrenchCanadians",    "rvltmodfrenchcanadians"),
    "Haitians":           ("RvltModHaitians",           "rvltmodhaitians"),
    "Hungarians":         ("RvltModHungarians",         "rvltmodhungarians"),
    "Indonesians":        ("RvltModIndonesians",        "rvltmodindonesians"),
    "Mayans":             ("RvltModMayans",             "rvltmodmayans"),
    "Napoleonic France":  ("RvltModNapoleonicFrance",   "rvltmodnapoleonicfrance"),
    "Peruvians":          ("RvltModPeruvians",          "rvltmodperuvians"),
    "Revolutionary France": ("RvltModRevolutionaryFrance", "rvltmodrevolutionaryfrance"),
    "Rio Grande":         ("RvltModRioGrande",          "rvltmodriogrande"),
    "Romanians":          ("RvltModRomanians",          "rvltmodromanians"),
    "South Africans":     ("RvltModSouthAfricans",      "rvltmodsouthafricans"),
    "Texians":            ("RvltModTexians",            "rvltmodtexians"),
    "Yucatan":            ("RvltModYucatan",            "rvltmodyucatan"),
}

# Slugs whose section is deferred — skip them silently (mirrors
# validate_html_reference._DEFERRED_SECTION).
DEFERRED_SLUGS = {"Americans", "Mexicans (Revolution)"}


# ─── Data classes ─────────────────────────────────────────────────────────────


_AOE_COLOR_RE = re.compile(r"&lt;color=([0-9.]+),\s*([0-9.]+),\s*([0-9.]+)&gt;(.*?)&lt;/color&gt;",
                            re.DOTALL)


def _render_aoe_text(text: str) -> str:
    """Render AOE3-style markup `<color=r, g, b>...</color>` and literal `\\n`s
    into a small styled block. Input is the raw string-table value (already
    contains `&lt;`/`&gt;` escapes from the XML); we keep escaping safe by
    only converting our specific tag pattern."""
    if not text:
        return ""
    # First convert literal '\n' (two chars) into real newlines so <pre> wraps.
    s = text.replace("\\n", "\n").replace("\\r", "")

    def _color_sub(m: re.Match[str]) -> str:
        r, g, b = (float(m.group(i)) for i in (1, 2, 3))
        rr, gg, bb = (max(0, min(255, int(round(c * 255)))) for c in (r, g, b))
        inner = m.group(4)
        # inner is already HTML-safe (came from XML) — emit it verbatim.
        return f'<span style="color:rgb({rr},{gg},{bb})">{inner}</span>'

    s = _AOE_COLOR_RE.sub(_color_sub, s)
    return f'<pre class="dev-blurb">{s}</pre>'


@dataclass
class StringRef:
    """A string-table reference: the ID + resolved value (or empty if missing)."""

    string_id: str = ""
    value: str = ""
    note: str = ""
    rich: bool = False  # True ⇒ value contains AOE color markup; render via _render_aoe_text

    @property
    def populated(self) -> bool:
        return bool(self.string_id) and bool(self.value)

    def render_html(self) -> str:
        if not self.string_id:
            return f'<em>{html.escape(self.note or "(unset)")}</em>'
        sid_html = html.escape(self.string_id)
        if self.value:
            if self.rich:
                val_html = _render_aoe_text(self.value)
            else:
                val_html = html.escape(self.value)
        else:
            # Heuristic: mod IDs are 400000+; lower IDs come from base-game stringtable.
            base_game = self.string_id.isdigit() and int(self.string_id) < 400000
            if base_game:
                val_html = '<em>(base-game stringtable_x.xml — not in mod repo)</em>'
            else:
                val_html = '<em>(empty / not resolved)</em>'
        prefix = f"{val_html}"
        suffix = f' <code class="dev-id">_locID={sid_html}</code>'
        if self.note:
            suffix += f' <span class="dev-note">— {html.escape(self.note)}</span>'
        return prefix + suffix


@dataclass
class AssetRef:
    """An on-disk asset reference (path + presence)."""

    path: str = ""
    note: str = ""

    @property
    def populated(self) -> bool:
        return bool(self.path)

    def render_html(self) -> str:
        if not self.path:
            return f'<em>{html.escape(self.note or "(unset)")}</em>'
        path_html = html.escape(self.path)
        exists = (REPO / self.path).is_file()
        marker = "" if exists else ' <span class="dev-warn">(missing)</span>'
        suffix = ""
        if self.note:
            suffix = f' <span class="dev-note">— {html.escape(self.note)}</span>'
        return f'<code class="dev-path">{path_html}</code>{marker}{suffix}'


@dataclass
class CivAssets:
    slug: str
    is_revolution: bool
    leader_personality: str  # personality file stem
    chatset_name: str = ""

    # Lobby
    civ_picker_name: StringRef = field(default_factory=StringRef)
    ai_lobby_name: StringRef = field(default_factory=StringRef)
    flag_hover_blurb: StringRef = field(default_factory=StringRef)
    lobby_portrait: AssetRef = field(default_factory=AssetRef)

    # Decks
    deck_source: str = ""
    deck_name: str = ""
    cards_by_age: list[list[tuple[str, str, str]]] = field(default_factory=list)
    # cards_by_age[age_idx] = list[(card_id, card_name, icon_relpath)]

    # In-match HUD
    scoreboard_flag: AssetRef = field(default_factory=AssetRef)
    scoreboard_name: StringRef = field(default_factory=StringRef)
    hud_hc_button: AssetRef = field(default_factory=AssetRef)
    player_summary_flag: AssetRef = field(default_factory=AssetRef)
    player_summary_hc_name: StringRef = field(default_factory=StringRef)
    player_summary_hc_civ: str = ""

    # Diplomacy
    diplomacy_portrait: AssetRef = field(default_factory=AssetRef)

    # Chat
    speaker_portrait: AssetRef = field(default_factory=AssetRef)

    # End-game
    endgame_total_flag: AssetRef = field(default_factory=AssetRef)
    endgame_civ_name: StringRef = field(default_factory=StringRef)


# ─── Loaders ──────────────────────────────────────────────────────────────────


def load_civmods_index() -> dict[str, ET.Element]:
    """Map civmods <Name> → <Civ> element."""
    root = ET.parse(CIVMODS).getroot()
    out: dict[str, ET.Element] = {}
    for civ in child_elements(root):
        if local_name(civ.tag) != "civ":
            continue
        name = get_child_text(civ, "Name")
        if name:
            out[name] = civ
    return out


def get_civmod_field(civ: ET.Element, tag: str) -> str:
    return get_child_text(civ, tag)


def get_matchmaking_portrait(civ: ET.Element) -> str:
    mm = find_first_child(civ, "MatchmakingTextures")
    if mm is None:
        return ""
    return get_child_text(mm, "SmallPortraitTextureWPF")


def load_homecity_meta(homecity_basename: str) -> tuple[StringRef, str, str]:
    """Return (HC name string-ref, HC civ token, HC flag relative path).

    The base-game homecity*.xml uses `<civ>` (token) + a localized `<name>`.
    Mod rvltmodhomecity*.xml does the same.
    """
    path = REPO / "data" / f"{homecity_basename}.xml"
    if not path.is_file():
        return (StringRef(note=f"{path.name} not found"), "", "")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return (StringRef(note=f"parse error: {exc}"), "", "")

    civ_tag = get_child_text(root, "civ")
    name_raw = get_child_text(root, "name")
    flag_path = ""

    name_ref = StringRef()
    # Names in homecity files are typically `$$NNN$$` references into stringtable.
    m = re.match(r"\$\$(\d+)\$\$", name_raw)
    if m:
        name_ref.string_id = m.group(1)
        # value populated later when string-table loader passes it in
    elif name_raw:
        name_ref.value = name_raw
        name_ref.note = "literal text"

    # Try to find a flag asset reference inside the homecity XML.
    flag_el = find_first_child(root, "flag")
    if flag_el is not None and flag_el.text:
        flag_path = flag_el.text.strip()
    return name_ref, civ_tag, flag_path


def load_chatset_for_personality(personality_chatset: str) -> str:
    """Confirm chatset name exists in chatsetsmods.xml; return the name as-is."""
    if not personality_chatset:
        return ""
    if not CHATSETS.is_file():
        return personality_chatset
    txt = CHATSETS.read_text(encoding="utf-8", errors="ignore")
    if f'name="{personality_chatset}"' in txt:
        return personality_chatset
    return personality_chatset  # name retained even if not found; validator can flag


def load_decks() -> tuple[dict, dict, dict]:
    return (
        json.loads(DECKS_LEG.read_text(encoding="utf-8")),
        json.loads(DECKS_STD.read_text(encoding="utf-8")),
        json.loads(CARDS.read_text(encoding="utf-8")),
    )


# ─── Main per-civ collector ───────────────────────────────────────────────────


def collect_civ(slug: str, *, civmods_index: dict[str, ET.Element], strings: dict[str, str],
                 decks_leg: dict, decks_std: dict, cards: dict) -> CivAssets:
    forcedciv, leader_stem = SLUG_TO_LEADER[slug]
    homecity_basename, std_key = CIV_TO_HOMECITY[slug]
    is_revolution = std_key is None

    # Personality
    personality_path = AI_DIR / f"{leader_stem}.personality"
    pinfo = parse_personality(personality_path) if personality_path.is_file() else {
        "nameID": None, "tooltipID": None, "forcedciv": None, "icon": None, "chatset": None,
    }

    civ = CivAssets(
        slug=slug,
        is_revolution=is_revolution,
        leader_personality=personality_path.name,
        chatset_name=load_chatset_for_personality(pinfo.get("chatset") or ""),
    )

    # ── Surface 2/7/11: AI lobby / scoreboard / diplomacy tooltip name ─────────
    name_id = pinfo.get("nameID") or ""
    civ.ai_lobby_name = StringRef(
        string_id=name_id,
        value=strings.get(name_id, ""),
        note="from .personality <nameID>",
    )

    # ── Surface 4 / 10 / 12 portrait (personality icon) ────────────────────────
    icon_path = pinfo.get("icon") or ""
    if icon_path:
        # Icon paths are typically `resources/images/...png`.
        icon_rel = icon_path.replace("\\", "/").lstrip("/")
        civ.lobby_portrait = AssetRef(path=icon_rel, note="personality <icon>")
        civ.diplomacy_portrait = AssetRef(path=icon_rel, note="reuses personality <icon>")
        civ.speaker_portrait = AssetRef(path=icon_rel, note="reuses personality <icon>")

    civ.scoreboard_name = StringRef(
        string_id=name_id,
        value=strings.get(name_id, ""),
        note="same as AI lobby name",
    )

    # ── civmods.xml fields (revolution civs only — base civs use base game) ───
    civ_el = civmods_index.get(forcedciv)
    if civ_el is None and is_revolution:
        # Should not happen for rev civs.
        civ_el = civmods_index.get(forcedciv.replace(" ", ""))

    if civ_el is not None:
        # Surface 1: civ-picker name
        display_id = get_civmod_field(civ_el, "DisplayNameID")
        civ.civ_picker_name = StringRef(
            string_id=display_id,
            value=strings.get(display_id, ""),
            note="civmods.xml <DisplayNameID>",
        )

        # Surface 3: lobby flag-hover blurb (multi-line, with AOE color markup)
        rollover_id = get_civmod_field(civ_el, "RolloverNameID")
        civ.flag_hover_blurb = StringRef(
            string_id=rollover_id,
            value=strings.get(rollover_id, ""),
            note="civmods.xml <RolloverNameID>",
            rich=True,
        )

        # Surface 4 fallback: lobby portrait via HomeCityPreviewWPF if personality has none
        if not civ.lobby_portrait.populated:
            preview = get_civmod_field(civ_el, "HomeCityPreviewWPF")
            if preview:
                civ.lobby_portrait = AssetRef(
                    path=preview,
                    note="civmods.xml <HomeCityPreviewWPF>",
                )
        # Lobby small portrait too
        small = get_matchmaking_portrait(civ_el)
        if small and not civ.diplomacy_portrait.populated:
            civ.diplomacy_portrait = AssetRef(
                path=small,
                note="civmods.xml <MatchmakingTextures><SmallPortraitTextureWPF>",
            )

        # Surface 6 / 8 / 9 / 15-17: in-match flags
        flag_icon = get_civmod_field(civ_el, "HomeCityFlagIconWPF") or get_civmod_field(civ_el, "PostgameFlagIconWPF")
        flag_button = get_civmod_field(civ_el, "HomeCityFlagButtonWPF")
        postgame_tex = get_civmod_field(civ_el, "PostgameFlagTexture")
        portrait_tex = get_civmod_field(civ_el, "Portrait")

        # Scoreboard flag (uses HomeCityFlagIconWPF / PostgameFlagIconWPF — same png in DE).
        if flag_icon:
            civ.scoreboard_flag = AssetRef(
                path=flag_icon,
                note="civmods.xml <HomeCityFlagIconWPF>",
            )
        elif portrait_tex:
            civ.scoreboard_flag = AssetRef(
                path=portrait_tex.replace("\\", "/"),
                note="civmods.xml <Portrait> (engine asset, not WPF)",
            )

        if flag_button:
            civ.hud_hc_button = AssetRef(path=flag_button, note="civmods.xml <HomeCityFlagButtonWPF>")
        if flag_icon:
            civ.player_summary_flag = AssetRef(path=flag_icon, note="civmods.xml <HomeCityFlagIconWPF>")
        # End-game total flag — DE uses PostgameFlagTexture (engine asset).
        if postgame_tex:
            civ.endgame_total_flag = AssetRef(
                path=postgame_tex.replace("\\", "/"),
                note="civmods.xml <PostgameFlagTexture> (engine asset, not WPF)",
            )

        # End-game civ name == civ-picker name (same DisplayNameID).
        civ.endgame_civ_name = StringRef(
            string_id=display_id,
            value=strings.get(display_id, ""),
            note="same as civ-picker name",
        )
    else:
        # Base civ — civmods has no override; everything is base-game default.
        note_base = "(base-game default — mod does not override)"
        civ.civ_picker_name = StringRef(note=note_base)
        civ.flag_hover_blurb = StringRef(note=note_base)
        civ.scoreboard_flag = AssetRef(note=note_base)
        civ.hud_hc_button = AssetRef(note=note_base)
        civ.player_summary_flag = AssetRef(note=note_base)
        civ.endgame_total_flag = AssetRef(note=note_base)
        civ.endgame_civ_name = StringRef(note=note_base)

    # ── Surface 13: Player Summary HC + flag + name ────────────────────────────
    hc_name_ref, hc_civ, hc_flag = load_homecity_meta(homecity_basename)
    if hc_name_ref.string_id and not hc_name_ref.value:
        hc_name_ref.value = strings.get(hc_name_ref.string_id, "")
    civ.player_summary_hc_name = hc_name_ref
    civ.player_summary_hc_civ = hc_civ

    # ── Surface 5 / 14: deck (Deck Builder = Player Summary deck) ──────────────
    if std_key:  # base civ → decks_standard.json
        deck = decks_std.get(std_key, {})
        civ.deck_source = f"data/decks_standard.json[{std_key!r}]"
    else:  # rev civ → decks_legendary.json
        deck = decks_leg.get(homecity_basename, {})
        civ.deck_source = f"data/decks_legendary.json[{homecity_basename!r}]"

    civ.deck_name = '"A New World"'
    cards_by_age: list[list[tuple[str, str, str]]] = [[], [], [], [], []]
    if isinstance(deck, dict):
        for age_str, card_ids in deck.items():
            try:
                idx = int(age_str)
            except ValueError:
                continue
            if not (0 <= idx <= 4):
                continue
            for cid in card_ids:
                meta = cards.get(cid, {})
                cname = meta.get("name") or cid
                cicon = meta.get("icon") or ""
                cards_by_age[idx].append((cid, cname, cicon))
    civ.cards_by_age = cards_by_age

    return civ


# ─── Renderer ─────────────────────────────────────────────────────────────────


def _row(label: str, body_html: str) -> str:
    return f'<tr><td class="dev-cell-label">{html.escape(label)}</td><td>{body_html}</td></tr>'


def _section_head(text: str) -> str:
    return f'<tr><th colspan="2" class="dev-section">{html.escape(text)}</th></tr>'


def render_dev_table(civ: CivAssets) -> str:
    deck_chips_by_age: list[str] = []
    icon_dir = "resources/images/icons/cards"
    for age_idx, cards in enumerate(civ.cards_by_age):
        if not cards:
            continue
        chips: list[str] = []
        for cid, cname, cicon in cards:
            title = html.escape(f"{cname} (id={cid})", quote=True)
            display = html.escape(cname, quote=True)
            if cicon:
                src = html.escape(f"{icon_dir}/{cicon}", quote=True)
                chips.append(
                    f'<span class="card-chip" title="{title}">'
                    f'<img class="card-icon" src="{src}" alt="{display}"></span>'
                )
            else:
                chips.append(
                    f'<span class="card-chip card-chip-noicon" title="{title}">{display}</span>'
                )
        deck_chips_by_age.append(
            f"<dt>{AGE_NAMES[age_idx]}</dt><dd>{''.join(chips)}</dd>"
        )

    deck_html = (
        f'<dl class="deck-grid">{"".join(deck_chips_by_age)}</dl>'
        if deck_chips_by_age
        else "<em>(empty deck)</em>"
    )

    deck_source_label = (
        f'{html.escape(civ.deck_name)} '
        f'<code class="dev-id">{html.escape(civ.deck_source)}</code>'
    )

    hc_civ_html = html.escape(civ.player_summary_hc_civ or "(unset)")
    hc_block = (
        f"{civ.player_summary_hc_name.render_html()} "
        f'<span class="dev-note">civ token: <code>{hc_civ_html}</code></span>'
    )

    rows: list[str] = [
        _section_head("Lobby"),
        _row("Civ-picker name", civ.civ_picker_name.render_html()),
        _row("AI slot name", civ.ai_lobby_name.render_html()),
        _row("Flag-hover blurb", civ.flag_hover_blurb.render_html()),
        _row("Lobby portrait", civ.lobby_portrait.render_html()),

        _section_head("Deck Builder (when civ picked by human)"),
        _row("Deck source", deck_source_label),
        _row("Cards (Age I…IV)", deck_html),

        _section_head("In-Match HUD"),
        _row("Scoreboard flag", civ.scoreboard_flag.render_html()),
        _row("Scoreboard name", civ.scoreboard_name.render_html()),
        _row("HC button flag", civ.hud_hc_button.render_html()),
        _row("Player Summary flag", civ.player_summary_flag.render_html()),
        _row("Player Summary HC", hc_block),
        _row("Player Summary deck", deck_source_label
             + ' <span class="dev-note">— same 25 cards as Deck Builder; if empty in-game see Known gaps</span>'),

        _section_head("Diplomacy (F4)"),
        _row("Portrait", civ.diplomacy_portrait.render_html()),
        _row("Tooltip name", civ.scoreboard_name.render_html()),

        _section_head("Chat (taunts / ally chat)"),
        _row("Chatset", f'<code class="dev-id">game/ai/chatsetsmods.xml: name="{html.escape(civ.chatset_name)}"</code>'
             if civ.chatset_name else "<em>(no chatset)</em>"),
        _row("Speaker portrait", civ.speaker_portrait.render_html()),
        _row("Speaker name", civ.scoreboard_name.render_html()),

        _section_head("End-Game Screens"),
        _row("Total-score flag", civ.endgame_total_flag.render_html()),
        _row("Other-tabs flag", civ.endgame_total_flag.render_html()
             + ' <span class="dev-note">— engine reuses one PostgameFlagTexture</span>'),
        _row("End-game civ name", civ.endgame_civ_name.render_html()),
    ]

    rows.append(_section_head("Provenance"))
    rows.append(_row("Personality file",
                     f'<code class="dev-path">game/ai/{html.escape(civ.leader_personality)}</code>'))

    return f'<table class="dev-table"><tbody>{"".join(rows)}</tbody></table>'


# ─── HTML rewriter ────────────────────────────────────────────────────────────


def _build_dev_block(slug: str, body_html: str) -> str:
    return (
        f'<details><summary><span class="cat-label">Development</span></summary>\n'
        f'<!-- DEV-START name="{slug}" -->\n'
        f'{body_html}\n'
        f'<!-- DEV-END name="{slug}" -->\n'
        f'</details>'
    )


def _section_span(html_text: str, slug: str) -> tuple[int, int] | None:
    """Return (start, end_exclusive) of the slug's section content (between
    its `<!-- ─── slug ─── -->` marker and the next section's marker, or EOF)."""
    section_re = re.compile(r"<!--\s*[─-]+\s*([^─\-][^<]*?)\s*[─-]+\s*-->")
    matches = list(section_re.finditer(html_text))
    for i, m in enumerate(matches):
        if m.group(1).strip() == slug:
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(html_text)
            return start, end
    return None


def _replace_dev_block(html_text: str, slug: str, body_html: str) -> tuple[str, bool]:
    """Replace or insert the slug's Dev block. Returns (new_text, changed?)."""
    span = _section_span(html_text, slug)
    if span is None:
        print(f"  SKIP {slug}: section comment not found", file=sys.stderr)
        return html_text, False
    sec_start, sec_end = span
    section = html_text[sec_start:sec_end]

    block_html = _build_dev_block(slug, body_html)

    # Marker pattern (idempotent rewrite).
    marker_re = re.compile(
        r'<details>\s*<summary><span class="cat-label">Development</span></summary>\s*'
        r'<!--\s*DEV-START\s+name="' + re.escape(slug) + r'"\s*-->'
        r'.*?'
        r'<!--\s*DEV-END\s+name="' + re.escape(slug) + r'"\s*-->\s*'
        r'</details>',
        re.DOTALL,
    )
    m = marker_re.search(section)
    if m:
        new_section = section[:m.start()] + block_html + section[m.end():]
    else:
        # Insert before the LAST </details> in the section (the nation-node closer).
        last_close = section.rfind("</details>")
        if last_close == -1:
            print(f"  SKIP {slug}: no </details> in section", file=sys.stderr)
            return html_text, False
        new_section = (
            section[:last_close]
            + block_html
            + "\n"
            + section[last_close:]
        )

    if new_section == section:
        return html_text, False
    return html_text[:sec_start] + new_section + html_text[sec_end:], True


CSS_BLOCK = """
/* dev-subtree styles (refresh_dev_subtrees.py) — AOE 3 DE menu palette */
.dev-table{width:100%;border-collapse:collapse;font-size:13px;margin:6px 0;background:rgba(28,18,8,0.55);border:1px solid var(--border,#6e4f24);border-radius:3px}
.dev-table td,.dev-table th{padding:5px 9px;border:1px solid rgba(110,79,36,0.45);vertical-align:top;color:var(--text,#e8d9b3)}
.dev-section{background:rgba(58,38,22,0.85);color:var(--accent,#e9c971);font-family:'Cinzel','Trajan Pro',serif;font-weight:600;letter-spacing:.05em;text-align:left;text-transform:uppercase;font-size:11px}
.dev-cell-label{width:24%;color:var(--accent,#e9c971);font-weight:600;white-space:nowrap;font-family:'EB Garamond',Georgia,serif}
.dev-id{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;color:var(--dim,#a8946a);background:rgba(0,0,0,0.35);padding:1px 5px;border-radius:2px;border:1px solid rgba(110,79,36,0.4)}
.dev-path{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;color:var(--text,#e8d9b3);background:rgba(0,0,0,0.35);padding:1px 5px;border-radius:2px;border:1px solid rgba(110,79,36,0.4);word-break:break-all}
.dev-note{color:var(--dim,#a8946a);font-size:11px;font-style:italic}
.dev-warn{color:#f5a37a;font-weight:600}
.dev-blurb{font-family:'EB Garamond',Georgia,serif;font-size:13.5px;line-height:1.5;background:rgba(20,12,4,0.7);color:var(--text,#e8d9b3);padding:10px 14px;margin:0 0 4px 0;white-space:pre-wrap;border-left:3px solid var(--accent,#e9c971);border-radius:2px;text-shadow:0 1px 0 rgba(0,0,0,0.5)}
"""


# A dev-subtree CSS block is "/* dev-subtree styles ... */" followed by a
# contiguous run of `.dev-...{...}` rules (one per line, the format CSS_BLOCK
# emits). This regex strips every such block so re-injection is idempotent
# even when an earlier buggy run left a stale or duplicate block behind.
_CSS_BLOCK_RE = re.compile(
    r"\n*/\* dev-subtree styles[^\n]*\n(?:\.dev-[^\n]+\n)+",
)


def _ensure_css(html_text: str) -> tuple[str, bool]:
    """Inject/refresh the dev-subtree CSS block immediately before </style>.

    Idempotent: strips any prior (stale or duplicated) dev-subtree CSS blocks
    in the inline <style> and reinserts the canonical CSS_BLOCK. Any drift
    between the generator template and the inline copy is healed on every run.
    """
    style_close = re.search(r"</style>", html_text)
    if not style_close:
        return html_text, False

    head = html_text[:style_close.start()]
    tail = html_text[style_close.start():]
    cleaned_head = _CSS_BLOCK_RE.sub("\n", head)
    new_head = cleaned_head.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n\n"
    new_text = new_head + tail
    return new_text, new_text != html_text


# ─── Entry point ──────────────────────────────────────────────────────────────


def run(check_only: bool = False) -> int:
    print(f"Loading data sources from {REPO}", file=sys.stderr)
    strings = load_string_table(STRINGS)
    civmods_index = load_civmods_index()
    decks_leg, decks_std, cards = load_decks()

    html_text = HTML_PATH.read_text(encoding="utf-8")
    original = html_text
    html_text, css_changed = _ensure_css(html_text)

    refreshed = 0
    skipped: list[str] = []
    for slug in CIV_TO_HOMECITY:
        if slug in DEFERRED_SLUGS:
            continue
        if slug not in SLUG_TO_LEADER:
            print(f"  SKIP {slug}: no SLUG_TO_LEADER entry", file=sys.stderr)
            skipped.append(slug)
            continue
        try:
            civ = collect_civ(slug, civmods_index=civmods_index, strings=strings,
                              decks_leg=decks_leg, decks_std=decks_std, cards=cards)
        except Exception as exc:  # noqa: BLE001 — surface the error and continue
            print(f"  ERR  {slug}: {exc}", file=sys.stderr)
            skipped.append(slug)
            continue
        body = render_dev_table(civ)
        html_text, changed = _replace_dev_block(html_text, slug, body)
        if changed:
            refreshed += 1
            print(f"  ok   {slug}: dev subtree refreshed", file=sys.stderr)

    if check_only:
        if html_text != original:
            print(f"DRIFT: {refreshed} dev subtree(s) would change. "
                  f"Run `python3 tools/cardextract/refresh_dev_subtrees.py` to update.",
                  file=sys.stderr)
            return 1
        print("OK: dev subtrees in sync.", file=sys.stderr)
        return 0

    HTML_PATH.write_text(html_text, encoding="utf-8")
    print(f"\nrefreshed: {refreshed}  skipped: {len(skipped)}  css_injected: {css_changed}",
          file=sys.stderr)
    if skipped:
        print(f"  skipped slugs: {skipped}", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="Exit non-zero if any dev subtree would change.")
    args = parser.parse_args()
    return run(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
