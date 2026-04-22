"""Override the displayed personality names for the 26 mod civs to show the
mod's designated LEADER (not the civ name).

Each mod civ .personality file already references a nameID pointing to the
base-game string table (e.g. "Americans" for Jefferson). This script adds
overrides in stringmods.xml at those same nameIDs so the in-game display
shows "Thomas Jefferson" instead of "Americans" etc.

Idempotent via <!-- MOD-CIV-LEADER-NAMES-START/END --> markers.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AI_DIR = REPO / "game" / "ai"
STRINGS_PATH = REPO / "data" / "strings" / "english" / "stringmods.xml"

# (personality_filename_stem, leader_display_name)
# Matches the mod's HTML explorer sub-tree mapping.
MOD_LEADERS = {
    "rvltmodnapoleonicfrance":   "Napoleon Bonaparte",
    "rvltmodrevolutionaryfrance": "Maximilien Robespierre",
    "rvltmodamericans":          "Thomas Jefferson",
    "rvltmodmexicans":           "Miguel Hidalgo",
    "rvltmodcanadians":          "Isaac Brock",
    "rvltmodfrenchcanadians":    "Louis-Joseph Papineau",
    "rvltmodbrazil":             "Pedro I of Brazil",
    "rvltmodargentines":         "José de San Martín",
    "rvltmodchileans":           "Bernardo O'Higgins",
    "rvltmodperuvians":          "Andrés de Santa Cruz",
    "rvltmodcolumbians":         "Simón Bolívar",
    "rvltmodhaitians":           "Toussaint L'Ouverture",
    "rvltmodindonesians":        "Prince Diponegoro",
    "rvltmodsouthafricans":      "Paul Kruger",
    "rvltmodfinnish":            "Carl Gustaf Mannerheim",
    "rvltmodhungarians":         "Lajos Kossuth",
    "rvltmodromanians":          "Alexandru Ioan Cuza",
    "rvltmodbarbary":            "Hayreddin Barbarossa",
    "rvltmodegyptians":          "Muhammad Ali Pasha",
    "rvltmodcentralamericans":   "Francisco Morazán",
    "rvltmodbajacalifornians":   "Juan Bautista Alvarado",
    "rvltmodyucatan":            "Felipe Carrillo Puerto",
    "rvltmodriogrande":          "Antonio Canales Rosillo",
    "rvltmodmayans":             "Jacinto Canek",
    "rvltmodcalifornians":       "Mariano Vallejo",
    "rvltmodtexians":            "Sam Houston",
}


def get_name_id(personality_stem: str) -> int | None:
    path = AI_DIR / f"{personality_stem}.personality"
    if not path.exists():
        return None
    m = re.search(r"<nameID>(\d+)</nameID>", path.read_text())
    return int(m.group(1)) if m else None


def main():
    overrides = []
    for stem, leader in MOD_LEADERS.items():
        nid = get_name_id(stem)
        if nid is None:
            print(f"  WARN: {stem} has no nameID, skipping")
            continue
        overrides.append((nid, leader, stem))

    # Update stringmods.xml with <!-- MOD-CIV-LEADER-NAMES --> block
    content = STRINGS_PATH.read_text(encoding="utf-8")
    start = "<!-- MOD-CIV-LEADER-NAMES-START -->"
    end = "<!-- MOD-CIV-LEADER-NAMES-END -->"
    content = re.sub(
        re.escape(start) + r".*?" + re.escape(end) + r"\n?",
        "", content, flags=re.DOTALL,
    )
    # ALSO remove any pre-existing entries for the nameIDs we're about to
    # inject (so we replace instead of duplicate).
    for nid, _, _ in overrides:
        content = re.sub(
            r"\s*<String _locID=['\"]" + str(nid) + r"['\"][^>]*>[^<]*</String>\s*\n?",
            "\n", content,
        )
    lines = [start]
    for nid, leader, stem in sorted(overrides):
        safe = leader.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f"      <String _locID='{nid}'>{safe}</String>  <!-- {stem} -->")
    lines.append(end)
    injection = "\n".join(lines) + "\n"
    content = content.replace("</Language>", injection + "</Language>", 1)
    STRINGS_PATH.write_text(content, encoding="utf-8")
    print(f"wrote {len(overrides)} mod-civ leader-name overrides to stringmods.xml")
    for nid, leader, stem in overrides:
        print(f"  {stem} (nameID {nid}) → {leader!r}")


if __name__ == "__main__":
    main()
