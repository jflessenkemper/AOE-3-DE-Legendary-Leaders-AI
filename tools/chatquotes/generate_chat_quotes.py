"""Generate chatsetsmods.xml tags, stringmods.xml entries, and HTML
reference quote-block updates from a single `quotes.json` source of truth.

Inputs:
  - tools/chatquotes/quotes.json  — per-leader quote data

Outputs:
  - game/ai/chatsetsmods.xml       — per-leader <Chatset> with <Tag> + <Sentence>
  - data/strings/english/stringmods.xml
                                   — <String _locID> entries per quote
  - LEGENDARY_LEADERS_TREE.html    — per-civ Quotes block refreshed
  - game/ai/*.personality          — each personality's <chatset> updated to the leader name

Idempotent via markers.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
QUOTES_JSON = REPO / "tools" / "chatquotes" / "quotes.json"
CHATSETS_PATH = REPO / "game" / "ai" / "chatsetsmods.xml"
STRINGS_PATH = REPO / "data" / "strings" / "english" / "stringmods.xml"
HTML_PATH = REPO / "LEGENDARY_LEADERS_TREE.html"
AI_DIR = REPO / "game" / "ai"

CHAT_START = "<!-- LL-LEADER-QUOTES-START -->"
CHAT_END = "<!-- LL-LEADER-QUOTES-END -->"
STR_START = "<!-- LL-QUOTE-STRINGS-START -->"
STR_END = "<!-- LL-QUOTE-STRINGS-END -->"

# Personality file stem → chatset name (1:1 with leader key in quotes.json)
# For base-civ overrides + the 26 rvltmod civs.
PERSONALITY_CHATSET = {
    "wellington":  "wellington",
    "catherine":   "catherine",
    "maurice":     "maurice",
    "usman":       "usman",
    "menelik":     "menelik",
    "shivaji":     "shivaji",
    "montezuma":   "montezuma",
    "pachacuti":   "pachacuti",
    "napoleon":    "napoleon",
    "washington":  "washington",
    "isabella":    "isabella",
    "henry":       "henry",
    "Frederick":   "Frederick",
    "garibaldi":   "garibaldi",
    "Gustav":      "Gustav",
    "hidalgo":     "hidalgo",
    "Hiawatha":    "Hiawatha",
    "crazyhorse":  "crazyhorse",
    "jean":        "jean",
    "kangxi":      "kangxi",
    "Suleiman":    "suleiman",   # persist `suleiman` lowercase chatset name
    "tokugawa":    "tokugawa",
}

# Map rvltmod*.personality → chatset key
RVLT_CHATSET = {
    "rvltmodnapoleonicfrance":    "rvltmodnapoleonicfrance",
    "rvltmodrevolutionaryfrance": "rvltmodrevolutionaryfrance",
    "rvltmodamericans":           "rvltmodamericans",
    "rvltmodmexicans":            "rvltmodmexicans",
    "rvltmodcanadians":           "rvltmodcanadians",
    "rvltmodfrenchcanadians":     "rvltmodfrenchcanadians",
    "rvltmodbrazil":              "rvltmodbrazil",
    "rvltmodargentines":          "rvltmodargentines",
    "rvltmodchileans":            "rvltmodchileans",
    "rvltmodperuvians":           "rvltmodperuvians",
    "rvltmodcolumbians":          "rvltmodcolumbians",
    "rvltmodhaitians":            "rvltmodhaitians",
    "rvltmodindonesians":         "rvltmodindonesians",
    "rvltmodsouthafricans":       "rvltmodsouthafricans",
    "rvltmodfinnish":             "rvltmodfinnish",
    "rvltmodhungarians":          "rvltmodhungarians",
    "rvltmodromanians":           "rvltmodromanians",
    "rvltmodbarbary":             "rvltmodbarbary",
    "rvltmodegyptians":           "rvltmodegyptians",
    "rvltmodcentralamericans":    "rvltmodcentralamericans",
    "rvltmodbajacalifornians":    "rvltmodbajacalifornians",
    "rvltmodyucatan":             "rvltmodyucatan",
    "rvltmodriogrande":           "rvltmodriogrande",
    "rvltmodmayans":              "rvltmodmayans",
    "rvltmodcalifornians":        "rvltmodcalifornians",
    "rvltmodtexians":             "rvltmodtexians",
}

# HTML civ-name → leader key used in quotes.json. For 48 civs.
# Mirrors the anchor patterns inject_walling_doctrine uses.
HTML_CIV_TO_LEADER = {
    # 22 base civ HTML sections
    "Aztecs":               "montezuma",
    "British":              "wellington",
    "Chinese":              "kangxi",
    "Dutch":                "maurice",
    "Ethiopians":           "menelik",
    "French":               "napoleon",   # Bourbon France — we use napoleon key for base French too
    "Germans":              "Frederick",
    "Haudenosaunee":        "Hiawatha",
    "Hausa":                "usman",
    "Inca":                 "pachacuti",
    "Indians":              "shivaji",
    "Italians":             "garibaldi",
    "Japanese":             "tokugawa",
    "Lakota":               "crazyhorse",
    "Maltese":              "jean",
    "Mexicans (Standard)":  "hidalgo",
    "Ottomans":              "suleiman",
    "Portuguese":            "henry",
    "Russians":              "catherine",
    "Spanish":               "isabella",
    "Swedes":                "Gustav",
    "United States":         "washington",
    # 26 rvltmod civ HTML sections (spelled per actual HTML anchors)
    "Americans":             "rvltmodamericans",
    "Argentines":            "rvltmodargentines",
    "Barbary":               "rvltmodbarbary",
    "Brazil":                "rvltmodbrazil",
    "Canadians":             "rvltmodcanadians",
    "Central Americans":     "rvltmodcentralamericans",
    "Chileans":              "rvltmodchileans",
    "Columbians":            "rvltmodcolumbians",
    "Egyptians":             "rvltmodegyptians",
    "Finnish":               "rvltmodfinnish",
    "French Canadians":      "rvltmodfrenchcanadians",
    "Haitians":              "rvltmodhaitians",
    "Hungarians":            "rvltmodhungarians",
    "Indonesians":           "rvltmodindonesians",
    "Mayans":                "rvltmodmayans",
    "Mexicans (Revolution)": "rvltmodmexicans",
    "Napoleonic France":     "rvltmodnapoleonicfrance",
    "Peruvians":             "rvltmodperuvians",
    "Revolutionary France":  "rvltmodrevolutionaryfrance",
    "Romanians":             "rvltmodromanians",
    "South Africans":        "rvltmodsouthafricans",
    "Texians":               "rvltmodtexians",
    "Yucatan":               "rvltmodyucatan",
    "Californians":          "rvltmodcalifornians",
    "Baja Californians":     "rvltmodbajacalifornians",
    "Rio Grande":            "rvltmodriogrande",
}


def escape_xml(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;"))


def allocate_string_id(leader_idx: int, trigger_idx: int, base: int) -> int:
    return base + leader_idx * 50 + trigger_idx


def generate(quotes: dict) -> tuple[str, str, dict]:
    """Return (chatsets_block, strings_block, leader_quotes_map) for injection."""
    meta = quotes["_meta"]
    triggers = meta["full_trigger_list"]
    trigger_idx = {t: i for i, t in enumerate(triggers)}
    base_id = meta["string_id_base"]

    leaders = quotes["leaders"]
    leader_keys = sorted(leaders.keys())

    chat_lines = [CHAT_START, "<!-- Generated by tools/chatquotes/generate_chat_quotes.py -->"]
    str_lines = [STR_START]
    per_leader_quotes: dict[str, dict[str, tuple[str, int]]] = {}

    for li, leader_key in enumerate(leader_keys):
        leader = leaders[leader_key]
        quotes_for_leader = {k: v for k, v in leader.items() if k != "display"}
        if not quotes_for_leader:
            continue

        chat_lines.append(f'<Chatset name="{leader_key}">')
        per_leader_quotes[leader_key] = {}

        for trigger_key, quote_text in quotes_for_leader.items():
            if trigger_key not in trigger_idx:
                continue
            ti = trigger_idx[trigger_key]
            sid = allocate_string_id(li, ti, base_id)
            safe = escape_xml(quote_text)

            chat_lines.append(f'   <Tag type="AiChat" name="{trigger_key}" priority="Background">')
            chat_lines.append('      <Sentence>')
            chat_lines.append(f'         <String>{safe}</String>')
            chat_lines.append(f'         <StringID>{sid}</StringID>')
            chat_lines.append('      </Sentence>')
            chat_lines.append('   </Tag>')

            str_lines.append(f"      <String _locID='{sid}'>{safe}</String>")
            per_leader_quotes[leader_key][trigger_key] = (quote_text, sid)

        chat_lines.append('</Chatset>')

    chat_lines.append(CHAT_END)
    str_lines.append(STR_END)

    return ("\n".join(chat_lines), "\n".join(str_lines), per_leader_quotes)


def inject_into_chatsets(block: str) -> None:
    path = CHATSETS_PATH
    if not path.exists():
        path.write_text(f"<root>\n{block}\n</root>\n", encoding="utf-8")
        return
    txt = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(CHAT_START) + r".*?" + re.escape(CHAT_END), re.DOTALL)
    if pattern.search(txt):
        new_txt = pattern.sub(block, txt)
    else:
        # Insert before </root>
        if "</root>" in txt:
            new_txt = txt.replace("</root>", block + "\n</root>", 1)
        else:
            new_txt = txt + "\n" + block + "\n"
    path.write_text(new_txt, encoding="utf-8")


def inject_into_stringmods(block: str) -> None:
    path = STRINGS_PATH
    txt = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(STR_START) + r".*?" + re.escape(STR_END), re.DOTALL)
    if pattern.search(txt):
        new_txt = pattern.sub(block, txt)
    else:
        new_txt = txt.replace("</Language>", block + "\n</Language>", 1)
    path.write_text(new_txt, encoding="utf-8")


def update_personality_chatsets(leader_keys: list[str]) -> int:
    """Rewrite each personality file's <chatset>...</chatset> to use its own
    chatset name (so each leader gets its own voice)."""
    mapping = {**PERSONALITY_CHATSET, **RVLT_CHATSET}
    updated = 0
    for stem, chatset_name in mapping.items():
        p = AI_DIR / f"{stem}.personality"
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8")
        new = re.sub(r"<chatset>[^<]*</chatset>", f"<chatset>{chatset_name}</chatset>", txt)
        if new != txt:
            p.write_text(new, encoding="utf-8")
            updated += 1
    return updated


def update_html_quotes(per_leader_quotes: dict) -> int:
    """For each civ in HTML_CIV_TO_LEADER, refresh its Quotes block
    to show the new flagship quotes.

    We don't remove the existing <details><summary>Quotes</summary>... block
    since it has hand-authored content; instead we INSERT a new
    <details class="ll-flagship-quotes"> block right after EXPLORER-END for
    each civ, between markers for idempotent updates.
    """
    if not HTML_PATH.exists():
        return 0
    txt = HTML_PATH.read_text(encoding="utf-8")
    count = 0
    for civ, leader_key in HTML_CIV_TO_LEADER.items():
        quotes = per_leader_quotes.get(leader_key)
        if not quotes:
            continue

        start_marker = f"<!-- LL-FLAGSHIP-QUOTES-START {civ} -->"
        end_marker = f"<!-- LL-FLAGSHIP-QUOTES-END {civ} -->"
        content = render_html_quote_block(quotes)
        wrapped = f"{start_marker}\n{content}\n{end_marker}"

        pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
        if pattern.search(txt):
            txt = pattern.sub(wrapped, txt)
            count += 1
            continue

        civ_anchor = re.compile(
            r'(<!-- ──────────── ' + re.escape(civ) + r' ──────────── -->.*?<!-- EXPLORER-END -->)',
            re.DOTALL,
        )
        m = civ_anchor.search(txt)
        if not m:
            continue
        insertion = m.group(1) + "\n" + wrapped
        txt = txt[:m.start()] + insertion + txt[m.end():]
        count += 1

    HTML_PATH.write_text(txt, encoding="utf-8")
    return count


def render_html_quote_block(quotes: dict) -> str:
    TRIGGER_LABEL = {
        "ToAllyIntro":              ("Encouragement", "ally at game start"),
        "ToEnemyIntro":             ("Taunt",         "enemy at game start"),
        "ToAllyWhenIWallIn":        ("Fortification", "I wall in"),
        "ToEnemyWhenHeWallsIn":     ("Derision",      "enemy walls in"),
        "ToAllyILoseExplorerEnemy": ("Retreat",       "my explorer dies"),
        "ToAllyBattleOverIWonAsExpected": ("Victory", "battle won"),
    }
    lines = ['<details class="ll-flagship-quotes"><summary>Leader Voice &mdash; Flagship Quotes</summary>']
    for key, (label, trigger_desc) in TRIGGER_LABEL.items():
        if key not in quotes:
            continue
        text, sid = quotes[key]
        safe = html.escape(text, quote=True)
        lines.append(f'<details><summary>{label} <span class="trigger">{trigger_desc}</span></summary>')
        lines.append(f'<ul><li><span class="quote">{safe}</span></li></ul></details>')
    lines.append('</details>')
    return "\n".join(lines)


def main():
    quotes = json.loads(QUOTES_JSON.read_text(encoding="utf-8"))
    chat_block, str_block, per_leader = generate(quotes)

    inject_into_chatsets(chat_block)
    print(f"Injected chatsetsmods.xml block ({len(per_leader)} leaders)")

    inject_into_stringmods(str_block)
    print(f"Injected {sum(len(v) for v in per_leader.values())} strings into stringmods.xml")

    n = update_personality_chatsets(list(per_leader.keys()))
    print(f"Updated {n} personality files' <chatset> field")

    n = update_html_quotes(per_leader)
    print(f"Refreshed {n} HTML civ quote blocks")


if __name__ == "__main__":
    main()
