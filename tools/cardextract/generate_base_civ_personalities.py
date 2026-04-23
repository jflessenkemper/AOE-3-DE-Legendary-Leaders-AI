"""Author 22 mod-leader .personality files so the in-game Skirmish AI
picker shows the mod's designated legendary leaders (portrait + name +
tooltip + chatset) as distinct entries.

Strategy (post-2026-04-22 bugfix):
  - Eight files are renamed to LEADER-matching filenames because the
    AoE3 DE mod loader does NOT override base-game .personality files by
    same-filename shadowing. Evidence: with elizabeth.personality present
    in both base game and mod, the picker rendered the BASE-GAME content.
  - Filenames: wellington, usman, catherine, maurice, menelik, shivaji,
    montezuma, pachacuti. These get registered in game/ai/personalities.xml
    so the picker lists them.
  - The remaining 14 files keep base-game filenames because their
    mod-intended leader happens to match the base-game name (Napoleon,
    Washington, etc.) — content is still rewritten to point to our
    mod-owned strings for precise wording (e.g. "Isabella I of Castile"
    instead of "Queen Isabella").

Idempotent: overwrites existing mod .personality files on each run.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AI_DIR = REPO / "game" / "ai"
STRINGS_PATH = REPO / "data" / "strings" / "english" / "stringmods.xml"

STRING_ID_BASE = 490200

# (base_game_filename, forcedciv, icon_filename, display_name, chatset, tooltip)
# The filename matches AoE3 DE's base file so placing it in game/ai/ overrides.
OVERRIDES = [
    # Mismatches the user asked to fix — renamed to leader-matching filenames
    # so the in-game picker displays them as distinct personalities (not just
    # renamed versions of base-game files, which the engine doesn't override).
    ("wellington.personality", "british",       "cpai_avatar_british_wellington.png",     "Duke of Wellington",          "elizabeth",  "British · line-and-logistics · Naval Mercantile Compound"),
    ("usman.personality",      "DEHausa",       "cpai_avatar_hausa_usman.png",            "Usman dan Fodio",             "amina",      "Hausa · Sokoto Caliphate jihadist mobilization"),
    ("catherine.personality",  "russians",      "cpai_avatar_russians_catherine.png",     "Catherine the Great",         "Ivan",       "Russian · Cossack voisko + enlightened absolutism"),
    ("maurice.personality",    "dutch",         "cpai_avatar_dutch_maurice.png",          "Maurice of Nassau",           "William",    "Dutch · mercantile drill + fortification"),
    ("menelik.personality",    "DEEthiopians",  "cpai_avatar_ethiopians_menelik.png",     "Menelik II",                  "tewodros",   "Ethiopian · Adwa-victorious highland defense"),
    ("shivaji.personality",    "indians",       "cpai_avatar_indians_shivaji.png",        "Shivaji Bhonsle",             "akbar",      "Indian · Maratha hill-fort guerilla"),
    ("montezuma.personality",  "XPAztec",       "cpai_avatar_aztecs_montezuma.png",       "Montezuma",                   "cuauhtemoc", "Aztec · tribute empire"),
    ("pachacuti.personality",  "DEInca",        "cpai_avatar_inca_pachacuti.png",         "Pachacuti",                   "Huayna",     "Inca · Andean terrace fortress"),

    # Civs where base name already matches mod intent — override anyway to
    # guarantee the displayed name is exactly the mod's preferred wording
    # (e.g. "Isabella I of Castile" instead of generic "Queen Isabella").
    ("isabella.personality",   "spanish",       "cpai_avatar_spanish_isabella.png",       "Isabella I of Castile",       "isabella",   "Spanish · conquistador crown"),
    ("napoleon.personality",   "french",        "cpai_avatar_french_napoleon.png",        "Napoleon Bonaparte",          "napoleon",   "French · Grande Armee forward operational line"),
    ("hidalgo.personality",    "demexicans",    "cpai_avatar_mexicans_hidalgo.png",       "Miguel Hidalgo",              "hidalgo",    "Mexican · Grito de Dolores clergy-led revolution"),
    ("washington.personality", "deamericans",   "cpai_avatar_united_states_washington.png", "George Washington",        "washington", "American · continental republic"),
    ("henry.personality",      "portuguese",    "cpai_avatar_portuguese_henry.png",       "Prince Henry the Navigator",  "henry",      "Portuguese · maritime discovery"),
    ("garibaldi.personality",  "DEItalians",    "cpai_avatar_italians_garibaldi.png",     "Giuseppe Garibaldi",          "garibaldi",  "Italian · Risorgimento Redshirt levee"),
    ("Gustav.personality",     "deswedish",     "cpai_avatar_swedes_gustavus.png",        "Gustavus Adolphus",           "Gustav",     "Swedish · Hakkapelit cavalry + line infantry"),
    ("jean.personality",       "DEMaltese",     "cpai_avatar_maltese_valette.png",        "Jean de Valette",             "jean",       "Maltese · Hospitaller siege endurance"),
    ("kangxi.personality",     "chinese",       "cpai_avatar_chinese_kangxi.png",         "Kangxi Emperor",              "kangxi",     "Chinese · banner-army central planning"),
    ("Suleiman.personality",   "ottomans",      "cpai_avatar_ottomans_suleiman.png",      "Suleiman the Magnificent",    "Suleiman",   "Ottoman · Janissary siege modernization"),
    ("tokugawa.personality",   "japanese",      "cpai_avatar_japanese_tokugawa.png",      "Tokugawa Ieyasu",             "tokugawa",   "Japanese · Sakoku consolidated shogunate"),
    ("Hiawatha.personality",   "XPIroquois",    "cpai_avatar_haudenosaunee_hiawatha.png", "Hiawatha",                    "Hiawatha",   "Haudenosaunee · Confederacy council"),
    ("crazyhorse.personality", "XPSioux",       "cpai_avatar_lakota_crazy_horse.png",     "Crazy Horse",                 "crazyhorse", "Lakota · steppe cavalry wedge"),
    ("Frederick.personality",  "germans",       "cpai_avatar_germans_frederick.png",      "Frederick the Great",         "Frederick",  "German · oblique-order Prussian drill"),
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


def generate_strings() -> list[tuple[int, str]]:
    """Return list of (string_id, text) pairs to inject into stringmods.xml."""
    out = []
    for i, (_, _, _, display, _, tooltip) in enumerate(OVERRIDES):
        out.append((STRING_ID_BASE + i * 2, display))
        out.append((STRING_ID_BASE + i * 2 + 1, tooltip))
    return out


def write_overrides():
    for i, (filename, forcedciv, icon, display, chatset, tooltip) in enumerate(OVERRIDES):
        name_id = STRING_ID_BASE + i * 2
        tooltip_id = STRING_ID_BASE + i * 2 + 1
        content = PERSONALITY_TEMPLATE.format(
            name_id=name_id, tooltip_id=tooltip_id, forcedciv=forcedciv,
            icon=icon, chatset=chatset,
        )
        (AI_DIR / filename).write_text(content, encoding="utf-8")
        print(f"  wrote game/ai/{filename}  →  {display}")


def update_stringmods():
    content = STRINGS_PATH.read_text(encoding="utf-8")
    start = "<!-- BASE-CIV-LEADER-NAMES-START -->"
    end = "<!-- BASE-CIV-LEADER-NAMES-END -->"
    content = re.sub(
        re.escape(start) + r".*?" + re.escape(end) + r"\n?",
        "", content, flags=re.DOTALL,
    )
    lines = [start]
    for sid, text in generate_strings():
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f"      <String _locID='{sid}'>{safe}</String>")
    lines.append(end)
    injection = "\n".join(lines) + "\n"
    content = content.replace("</Language>", injection + "</Language>", 1)
    STRINGS_PATH.write_text(content, encoding="utf-8")
    print(f"  wrote {len(OVERRIDES)*2} string entries to stringmods.xml")


def main():
    print(f"Writing {len(OVERRIDES)} mod-leader personality OVERRIDES (same filenames as base game)...")
    write_overrides()
    print("\nUpdating stringmods.xml...")
    update_stringmods()
    print("\nDone — these files replace the base-game personalities at the same paths.")
    print("Every civ's default AI personality now = the mod's designated leader.")


if __name__ == "__main__":
    main()
