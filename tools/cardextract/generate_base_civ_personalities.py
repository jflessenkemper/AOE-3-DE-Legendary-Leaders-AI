"""Generate base-civ .personality files for mod-designated leaders.

Base AoE3 DE ships personality files like `elizabeth.personality` (British) and
`amina.personality` (Hausa), but the mod's AI logic dispatches unconditionally
to `leader_wellington.xs` (British) and `leader_usman.xs` (Hausa). That creates
a UX mismatch: in-game the AI shows as "Queen Elizabeth" / "Queen Amina" while
actually running Wellington / Usman doctrine.

This generator writes new `.personality` files into `game/ai/` that expose the
mod-intended leaders as selectable AI personalities in the Skirmish setup. It
also appends the matching name strings to `data/strings/english/stringmods.xml`
in a safe ID range starting at 490200.

The portrait icons (resources/images/icons/singleplayer/cpai_avatar_*.png) are
already present in the mod repo — this script only creates the .personality
and stringmods entries to wire them up.

Chatsets are reused from existing base-game sets (Wellington reuses Elizabeth's
voice lines etc.). The mod's own legendary-leader-quote system fires
independently of chatset, so the doctrinal dialogue is still leader-correct.

Idempotent: re-running replaces prior entries. Safe to run after each mod update.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AI_DIR = REPO / "game" / "ai"
STRINGS_PATH = REPO / "data" / "strings" / "english" / "stringmods.xml"

STRING_ID_BASE = 490200

# (personality_filename, forcedciv, icon_filename, display_name, chatset, tooltip_suffix)
LEADERS = [
    ("wellington.personality",   "british",        "cpai_avatar_british_wellington.png",    "Duke of Wellington",      "elizabeth", "British · line-and-logistics · Naval Mercantile Compound"),
    ("usman.personality",        "DEHausa",        "cpai_avatar_hausa_usman.png",           "Usman dan Fodio",         "amina",     "Hausa · Sokoto Caliphate jihadist mobilization"),
    ("catherine.personality",    "russians",       "cpai_avatar_russians_catherine.png",    "Catherine the Great",     "Ivan",      "Russian · Cossack voisko + enlightened absolutism"),
    ("maurice.personality",      "dutch",          "cpai_avatar_dutch_maurice.png",         "Maurice of Nassau",       "William",   "Dutch · mercantile drill + fortification"),
    ("menelik.personality",      "DEEthiopians",   "cpai_avatar_ethiopians_menelik.png",    "Menelik II",              "tewodros",  "Ethiopian · Adwa-victorious highland defense"),
    ("shivaji.personality",      "indians",        "cpai_avatar_indians_shivaji.png",       "Shivaji Bhonsle",         "akbar",     "Indian · Maratha hill-fort guerilla"),
    ("montezuma.personality",    "xpaztec",        "cpai_avatar_aztecs_montezuma.png",      "Montezuma",               "cuauhtemoc","Aztec · tribute empire"),
    ("pachacuti.personality",    "deinca",         "cpai_avatar_inca_pachacuti.png",        "Pachacuti",               "Huayna",    "Inca · Andean terrace fortress"),
]

PERSONALITY_TEMPLATE = """\
<AI>
   <version>2</version>
   <script>aiLoaderStandard</script>
   <nameID>{name_id}</nameID>
   <tooltipID>{tooltip_id}</tooltipID>
   <forcedciv>{forcedciv}</forcedciv>
   <rushboom>0</rushboom>
   <icon>resources/images/icons/singleplayer/{icon}</icon>
   <chatset>{chatset}</chatset>
   <playerNames>
      <nameID>{name_id}</nameID>
      <civ>{forcedciv}</civ>
   </playerNames>
</AI>
"""


def generate_strings() -> list[tuple[int, str, str]]:
    """Return list of (string_id, purpose, text) to inject into stringmods.xml."""
    out = []
    for i, (filename, forcedciv, icon, display, chatset, tooltip) in enumerate(LEADERS):
        name_id = STRING_ID_BASE + i * 2
        tooltip_id = STRING_ID_BASE + i * 2 + 1
        out.append((name_id, "name", display))
        out.append((tooltip_id, "tooltip", tooltip))
    return out


def write_personality_files():
    for i, (filename, forcedciv, icon, display, chatset, tooltip) in enumerate(LEADERS):
        name_id = STRING_ID_BASE + i * 2
        tooltip_id = STRING_ID_BASE + i * 2 + 1
        content = PERSONALITY_TEMPLATE.format(
            name_id=name_id,
            tooltip_id=tooltip_id,
            forcedciv=forcedciv,
            icon=icon,
            chatset=chatset,
        )
        path = AI_DIR / filename
        path.write_text(content, encoding="utf-8")
        print(f"  wrote {path.relative_to(REPO)} (nameID={name_id})")


def update_stringmods():
    content = STRINGS_PATH.read_text(encoding="utf-8")

    # Remove prior injection (marked by start/end comments)
    start_marker = "<!-- BASE-CIV-LEADER-NAMES-START -->"
    end_marker = "<!-- BASE-CIV-LEADER-NAMES-END -->"
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\n?",
        re.DOTALL,
    )
    content = pattern.sub("", content)

    # Build new injection block
    lines = [start_marker]
    for string_id, purpose, text in generate_strings():
        # XML-escape minimal
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f"      <String _locID='{string_id}'>{safe}</String>")
    lines.append(end_marker)
    injection = "\n".join(lines) + "\n"

    # Insert right before the closing </Language></StringTable></stringmods>
    # Safest: insert before </Language>
    closing = "</Language>"
    if closing not in content:
        print(f"ERROR: {closing} not found in stringmods.xml; skipping")
        return
    content = content.replace(closing, injection + closing, 1)
    STRINGS_PATH.write_text(content, encoding="utf-8")
    print(f"  updated {STRINGS_PATH.relative_to(REPO)} with {len(LEADERS)*2} entries")


def main():
    print(f"Generating {len(LEADERS)} base-civ mod-leader personality files...")
    write_personality_files()
    print("\nUpdating stringmods.xml...")
    update_stringmods()
    print("\nDone. Run validators and sync to live install.")


if __name__ == "__main__":
    main()
