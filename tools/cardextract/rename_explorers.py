"""Rename every civ's explorer / war chief / monk / general / grandmaster
to the chosen leader name from the reference HTML, so the in-game unit
panel and the leader-protect chat lines all reference the right person.

Mechanism: AoE3 has a tech effect `<Effect type='SetName' proto='X'
newName='LOCID'>` that overrides the display name of a proto. We use it
two ways:

  Revolution civs (26): we own each civ's existing RvltModAge0* tech in
  data/techtreemods.xml — we just append the SetName effect inside its
  <Effects> block.

  Standard civs (22): we don't own the vanilla Age0<Civ> techs, and
  re-declaring them in techtreemods.xml would clobber every vanilla
  bonus they apply. Instead we create a NEW shadow tech per civ
  (LLRenameExplorer<Civ>) that auto-fires when the vanilla Age0<Civ>
  tech becomes Active (via <prereqs><techstatus status='Active'>...).

Each leader name gets a fresh _locID in data/strings/english/stringmods.xml
in the 490300-490399 range. Both the strings block and the per-tech
SetName effect are wrapped in markers so re-runs are idempotent.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TECH = REPO / "data" / "techtreemods.xml"
STRINGS = REPO / "data" / "strings" / "english" / "stringmods.xml"

# civ_id (matches the AgeTech name suffix) → (Age0 tech name, explorer proto,
# leader display name, fresh _locID we'll assign)
LEADERS: list[tuple[str, str, str, str, int]] = [
    # Age0 tech                              proto          leader name                     locID
    ("RvltModAge0NapoleonicFrench",         "Explorer",   "Napoleon Bonaparte",            490300),
    ("RvltModAge0RevolutionaryFrench",      "Explorer",   "Maximilien Robespierre",        490301),
    ("RvltModAge0Haitians",                 "Explorer",   "Toussaint Louverture",          490302),
    ("RvltModAge0Argentines",               "Explorer",   "Jose de San Martin",            490303),
    ("RvltModAge0Brazilians",               "Explorer",   "Pedro I of Brazil",             490304),
    ("RvltModAge0Chileans",                 "Explorer",   "Bernardo O'Higgins",            490305),
    ("RvltModAge0Columbians",               "Explorer",   "Simon Bolivar",                 490306),
    ("RvltModAge0Mexicans",                 "Explorer",   "Miguel Hidalgo y Costilla",     490307),
    ("RvltModAge0Texas",                    "deGeneral",  "Sam Houston",                   490308),
    ("RvltModAge0California",               "deGeneral",  "Mariano Guadalupe Vallejo",     490309),
    ("RvltModAge0BajaCalifornia",           "deGeneral",  "Juan Bautista Alvarado",        490310),
    ("RvltModAge0CentralAmericans",         "deGeneral",  "Francisco Morazan",             490311),
    ("RvltModAge0Maya",                     "deGeneral",  "Jacinto Canek",                 490312),
    ("RvltModAge0Yucatan",                  "deGeneral",  "Felipe Carrillo Puerto",        490313),
    ("RvltModAge0RioGrande",                "deGeneral",  "Antonio Canales Rosillo",       490314),
    ("RvltModAge0Peruvians",                "Explorer",   "Andres de Santa Cruz",          490315),
    ("RvltModAge0FrenchCanadians",          "Explorer",   "Louis-Joseph Papineau",         490316),
    ("RvltModAge0Canadians",                "Explorer",   "Isaac Brock",                   490317),
    ("RvltModAge0Americans",                "Explorer",   "Thomas Jefferson",              490318),
    ("RvltModAge0Finnish",                  "Explorer",   "Carl Gustaf Emil Mannerheim",   490319),
    ("RvltModAge0Hungarians",               "Explorer",   "Lajos Kossuth",                 490320),
    ("RvltModAge0Romanians",                "Explorer",   "Alexandru Ioan Cuza",           490321),
    ("RvltModAge0SouthAfricans",            "Explorer",   "Paul Kruger",                   490322),
    ("RvltModAge0Egypt",                    "Explorer",   "Muhammad Ali Pasha",            490323),
    ("RvltModAge0Barbary",                  "Explorer",   "Hayreddin Barbarossa",          490324),
    ("RvltModAge0Indonesians",              "Explorer",   "Prince Diponegoro",             490325),
]

# Standard civs: we don't own vanilla Age0<Civ> techs, so we add a NEW
# shadow tech per civ that fires off the vanilla Age0 tech as a prereq.
# Format: (new_tech_name, prereq_age0_tech, proto, leader_name, locID)
STANDARD_CIVS: list[tuple[str, str, str, str, int]] = [
    ("LLRenameExplorerBritish",      "Age0British",     "Explorer",            "Duke of Wellington",        490350),
    ("LLRenameExplorerFrench",       "Age0French",      "Explorer",            "Louis XVIII",               490351),
    ("LLRenameExplorerDutch",        "Age0Dutch",       "Explorer",            "Maurice of Nassau",         490352),
    ("LLRenameExplorerGerman",       "Age0German",      "Explorer",            "Frederick the Great",       490353),
    ("LLRenameExplorerOttoman",      "Age0Ottoman",     "Explorer",            "Suleiman the Magnificent",  490354),
    ("LLRenameExplorerPortuguese",   "Age0Portuguese",  "Explorer",            "Henry the Navigator",       490355),
    ("LLRenameExplorerRussian",      "Age0Russian",     "Explorer",            "Catherine the Great",       490356),
    ("LLRenameExplorerSpanish",      "Age0Spanish",     "Explorer",            "Isabella I of Castile",     490357),
    ("LLRenameExplorerSwedish",      "DEAge0Swedish",   "Explorer",            "Gustavus Adolphus",         490358),
    ("LLRenameExplorerEthiopian",    "DEAge0Ethiopian", "dePrince",            "Menelik II",                490359),
    ("LLRenameExplorerHausa",        "DEAge0Hausa",     "deEmir",              "Usman dan Fodio",           490360),
    ("LLRenameExplorerItalian",      "DEAge0Italian",   "Explorer",            "Giuseppe Garibaldi",        490361),
    ("LLRenameExplorerMaltese",      "DEAge0Maltese",   "deGrandMaster",       "Jean Parisot de Valette",   490362),
    ("LLRenameExplorerMexicanStd",   "DEAge0Mexican",   "deGeneral",           "Miguel Hidalgo y Costilla", 490363),
    ("LLRenameExplorerAmericanStd",  "DEAge0American",  "deGeneral",           "George Washington",         490364),
    ("LLRenameExplorerInca",         "DEAge0Inca",      "deIncaWarChief",      "Pachacuti",                 490365),
    ("LLRenameExplorerJapanese",     "YPAge0Japanese",  "ypMonkJapanese",      "Tokugawa Ieyasu",           490366),
    ("LLRenameExplorerChinese",      "YPAge0Chinese",   "ypMonkChinese",       "Kangxi Emperor",            490367),
    ("LLRenameExplorerIndian",       "YPAge0Indians",   "ypMonkIndian",        "Shivaji Maharaj",           490368),
    ("LLRenameExplorerAztec",        "Age0XPAztec",     "xpAztecWarchief",     "Montezuma II",              490369),
    ("LLRenameExplorerLakota",       "Age0XPSioux",     "xpLakotaWarchief",    "Crazy Horse",               490370),
    ("LLRenameExplorerHaud",         "Age0XPIroquois",  "xpIroquoisWarchief",  "Hiawatha",                  490371),
]


def upsert_strings() -> None:
    text = STRINGS.read_text(encoding="utf-8")
    text = re.sub(
        r"\s*<!-- LL-LEADER-NAMES-START -->.*?<!-- LL-LEADER-NAMES-END -->",
        "",
        text,
        flags=re.DOTALL,
    )
    block_lines = ["         <!-- LL-LEADER-NAMES-START -->"]
    rows = [(name, locid) for _, _, name, locid in LEADERS]
    rows += [(name, locid) for _, _, _, name, locid in STANDARD_CIVS]
    for name, locid in rows:
        safe = name.replace("&", "&amp;").replace("'", "&apos;")
        block_lines.append(
            f"         <String _locID='{locid}' "
            f"symbol='cStringLLLeader{locid}'>{safe}</String>"
        )
    block_lines.append("         <!-- LL-LEADER-NAMES-END -->")
    block = "\n".join(block_lines)
    text = text.replace(
        "      </Language>",
        block + "\n      </Language>",
        1,
    )
    STRINGS.write_text(text, encoding="utf-8")


def upsert_tech_effects() -> int:
    text = TECH.read_text(encoding="utf-8")
    edits = 0
    for tech_name, proto, name, locid in LEADERS:
        # Find the tech block
        m = re.search(
            rf"(<Tech name\s*='{re.escape(tech_name)}'[^>]*>.*?)"
            rf"(\s*</Tech>)",
            text, re.DOTALL,
        )
        if not m:
            print(f"  WARN tech not found: {tech_name}")
            continue
        head, tail = m.group(1), m.group(2)

        # Strip any prior managed effect for this tech
        head = re.sub(
            r"\s*<!-- LL-RENAME-START -->.*?<!-- LL-RENAME-END -->",
            "",
            head,
            flags=re.DOTALL,
        )

        # Append our SetName effect inside the existing <Effects> block
        # (every Age0 tech in techtreemods.xml has one). If there's no
        # <Effects>, fall through and skip with a warning.
        if "</Effects>" not in head:
            print(f"  WARN no <Effects> in {tech_name}; skipping")
            continue
        injection = (
            "\n\t\t\t<!-- LL-RENAME-START -->\n"
            f"\t\t\t<Effect type='SetName' proto='{proto}' culture='none' "
            f"newName='{locid}'></Effect>\n"
            "\t\t\t<!-- LL-RENAME-END -->\n\t\t"
        )
        new_head = head.replace("</Effects>", injection + "</Effects>", 1)
        text = text[: m.start()] + new_head + tail + text[m.end():]
        edits += 1
    TECH.write_text(text, encoding="utf-8")
    return edits


def upsert_standard_shadow_techs() -> int:
    """Add (or replace) one shadow tech per standard civ that fires off
    its vanilla Age0<Civ> tech as a prereq and renames the explorer."""
    text = TECH.read_text(encoding="utf-8")
    # Strip any existing managed block
    text = re.sub(
        r"\s*<!-- LL-STANDARD-RENAMES-START -->.*?<!-- LL-STANDARD-RENAMES-END -->",
        "",
        text,
        flags=re.DOTALL,
    )
    block_lines = ["", "\t<!-- LL-STANDARD-RENAMES-START -->"]
    for tech_name, prereq, proto, _, locid in STANDARD_CIVS:
        block_lines.append(
            f"\t<Tech name='{tech_name}' type='Normal'>\n"
            f"\t\t<Status>UNOBTAINABLE</Status>\n"
            f"\t\t<Flag>Shadow</Flag>\n"
            f"\t\t<Prereqs>\n"
            f"\t\t\t<TechStatus status='Active'>{prereq}</TechStatus>\n"
            f"\t\t</Prereqs>\n"
            f"\t\t<Effects>\n"
            f"\t\t\t<Effect type='SetName' proto='{proto}' culture='none' "
            f"newName='{locid}'></Effect>\n"
            f"\t\t</Effects>\n"
            f"\t</Tech>"
        )
    block_lines.append("\t<!-- LL-STANDARD-RENAMES-END -->")
    block = "\n".join(block_lines)
    # Insert before the closing </techtreemods>
    text = text.replace("</techtreemods>", block + "\n</techtreemods>", 1)
    TECH.write_text(text, encoding="utf-8")
    return len(STANDARD_CIVS)


def main() -> int:
    upsert_strings()
    print(f"upserted {len(LEADERS) + len(STANDARD_CIVS)} leader-name strings "
          f"into {STRINGS.relative_to(REPO)}")
    n = upsert_tech_effects()
    print(f"upserted SetName on {n}/{len(LEADERS)} revolution-civ Age0 techs")
    s = upsert_standard_shadow_techs()
    print(f"injected {s} new standard-civ rename shadow techs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
