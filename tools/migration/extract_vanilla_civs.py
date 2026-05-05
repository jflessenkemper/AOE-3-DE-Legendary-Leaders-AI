"""Phase 2b of the ANW migration: pull vanilla civ definitions from the
engine's `civs.xml` (inside `Data/Data.bar`) and use them to fill in the
22 base-civ stubs in `data/civmods.anw.xml`.

For each ANW base-civ AnwCiv, we:

  1. Read vanilla `civs.xml` for the matching civ (case-insensitive lookup
     on `<name>{old_civ_token}</name>`).
  2. Lift the engine-specific fields (StatsID, AgeTechs, starting units,
     BuildingEfficiency, EmpireWars params, MultipleBlockTrain entries,
     flag textures, etc.) out of the vanilla block.
  3. Build a complete `<Civ>` block for civmods.xml:
       - `<Name>` → ANWBritish (etc.)
       - DisplayNameID / RolloverNameID → ANW range (410000-410999)
       - HomeCityFilename → anwhomecitybritish.xml
       - Everything else → exact vanilla values

  4. Replace the existing TODO-ANW-VANILLA stub in `data/civmods.anw.xml`
     with the filled block.

Required path:

  Default: /var/home/jflessenkemper/.local/share/Steam/steamapps/common/AoE3DE/
  Override: --aoe3de-root /path/to/AoE3DE

CLI:
  python3 tools/migration/extract_vanilla_civs.py
        Read vanilla civs.xml, fill stubs in data/civmods.anw.xml.
        Idempotent — re-running on a filled file produces no diff.

  python3 tools/migration/extract_vanilla_civs.py --check
        Exit non-zero if data/civmods.anw.xml still has TODO-ANW-VANILLA.

  python3 tools/migration/extract_vanilla_civs.py --dump-vanilla DIR
        Just extract the parsed vanilla civs.xml to a readable XML file
        in DIR (for debugging).
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.cardextract.xmb import parse_xmb  # noqa: E402
from tools.migration.anw_token_map import AnwCiv, iter_anw_civs  # noqa: E402

DEFAULT_AOE3DE_ROOT = Path(
    "/var/home/jflessenkemper/.local/share/Steam/steamapps/common/AoE3DE"
)

CIVMODS_ANW = REPO / "data" / "civmods.anw.xml"


# Field-by-field allow-list of vanilla tags we lift into ANW. Some fields
# we OVERRIDE (Name → ANW token; DisplayNameID/RolloverNameID → ANW range;
# HomeCityFilename → anwhomecity*) — those are not in this list.
#
# Tags whose vanilla token references the OLD civ token (e.g. age-up tech
# names like "ColonializeBritish") are taken verbatim — these are
# base-game tech defs that already exist in the engine and our ANW civ
# can keep using them. The mod's *own* mod-defined techs (e.g.
# ANWFortressizeAmericans) are inside techtreemods.xml — out of scope here.
LIFTED_FIELDS = {
    "main",
    "statsid",
    "portrait",
    "culture",
    "settlerprotoname",
    "alliedid",
    "alliedotherid",
    "unalliedid",
    "hcshipmentmodifier",
    "agetech",  # appears 5x
    "postindustrialtech",
    "postimperialtech",
    "deathmatchtech",
    "treatytech",
    "empirewarstech",
    "buildingefficiency",
    "freebuildingefficiency",
    "gold",
    "food",
    "wood",
    "startingunit",
    "townstartingunit",
    "empirewarsstartingunit",
    "empirewarsresources",
    "empirewarsshipmentxpmaximummodifier",
    "empirewarsshipmentgrowthmodifier",
    "empirewarsshipmentmodifier",
    "empirewarsshipmentrates",
    "empirewarsageuprates",
    "randomstartingunits",
    "homecityflagtexture",
    "homecityflagbuttonset",
    "homecityflagbuttonsetlarge",
    "postgameflagtexture",
    "postgameflagiconwpf",
    "homecityflagiconwpf",
    "homecitypreviewwpf",
    "homecityflagbuttonwpf",
    "matchmakingtextures",
    "unitregen",
    "multipleblocktrain",
}

# String IDs for the 22 base civs reside in 410000-410999.
BASE_CIV_DISPLAY_ID_BASE = 410000
BASE_CIV_ROLLOVER_ID_BASE = 410500


# ──────────────────────────────────────────────────────────────────────────────
# Vanilla civs.xml extraction
# ──────────────────────────────────────────────────────────────────────────────


def load_vanilla_civs(aoe3de_root: Path) -> dict[str, ET.Element]:
    """Return a case-insensitive dict {lower(name) → vanilla <civ> element}."""
    bar_path = aoe3de_root / "Game" / "Data" / "Data.bar"
    if not bar_path.is_file():
        raise SystemExit(f"missing {bar_path}")

    # Inline-extract civs.xml.XMB without spawning bar_extract.py
    from tools.bar_extract import parse_header, read_entries, maybe_decompress  # noqa: E402

    with bar_path.open("rb") as f:
        version, _n, table_offset = parse_header(f)
        _root_name, entries = read_entries(f, version, table_offset)
        target_entry = next(
            (e for e in entries
             if e["name"].lower().endswith("civs.xml.xmb")),
            None,
        )
        if target_entry is None:
            raise SystemExit("Data.bar: civs.xml.XMB not found")
        f.seek(target_entry["offset"])
        raw = f.read(target_entry["size2"])

    data = maybe_decompress(raw)
    root = parse_xmb(data)

    out: dict[str, ET.Element] = {}
    for c in root:
        if c.tag != "civ":
            continue
        name = c.findtext("name") or ""
        if name:
            out[name.lower()] = c
    print(f"  vanilla civs.xml: {len(out)} <civ> blocks loaded", file=sys.stderr)
    return out


# ──────────────────────────────────────────────────────────────────────────────
# ANW <Civ> block builder
# ──────────────────────────────────────────────────────────────────────────────


def _serialize_lifted_child(child: ET.Element, indent: str = "\t\t") -> str:
    """Serialize a child element with PascalCase tag name + same indent style
    as the existing civmods.xml. The vanilla XMB parser lowercased everything;
    we restore the canonical PascalCase used in civmods.xml."""
    pascal_tag = _to_pascal(child.tag)

    def _walk(el: ET.Element, depth: int) -> str:
        tag = _to_pascal(el.tag)
        # Build attrib string
        attribs = ""
        for k, v in el.attrib.items():
            attribs += f' {k}="{v}"'
        children = list(el)
        ind = "\t" * depth
        if not children and (el.text is None or el.text.strip() == ""):
            return f"{ind}<{tag}{attribs}/>\n"
        if not children:
            text = (el.text or "").strip()
            return f"{ind}<{tag}{attribs}>{text}</{tag}>\n"
        body = "".join(_walk(c, depth + 1) for c in children)
        return f"{ind}<{tag}{attribs}>\n{body}{ind}</{tag}>\n"

    return _walk(child, len(indent.replace("\t\t", "\t")) + 1)


_PASCAL_OVERRIDES = {
    "statsid": "StatsID",
    "alliedid": "AlliedID",
    "alliedotherid": "AlliedOtherID",
    "unalliedid": "UnAlliedID",
    "displaynameid": "DisplayNameID",
    "rollovernameid": "RolloverNameID",
    "agetech": "AgeTech",
    "postindustrialtech": "PostIndustrialTech",
    "postimperialtech": "PostImperialTech",
    "deathmatchtech": "DeathMatchTech",
    "treatytech": "TreatyTech",
    "empirewarstech": "EmpireWarsTech",
    "buildingefficiency": "BuildingEfficiency",
    "freebuildingefficiency": "FreeBuildingEfficiency",
    "homecityflagtexture": "HomeCityFlagTexture",
    "homecityflagbuttonset": "HomeCityFlagButtonSet",
    "homecityflagbuttonsetlarge": "HomeCityFlagButtonSetLarge",
    "postgameflagtexture": "PostgameFlagTexture",
    "postgameflagiconwpf": "PostgameFlagIconWPF",
    "homecityflagiconwpf": "HomeCityFlagIconWPF",
    "homecitypreviewwpf": "HomeCityPreviewWPF",
    "homecityflagbuttonwpf": "HomeCityFlagButtonWPF",
    "homecityfilename": "HomeCityFilename",
    "matchmakingtextures": "MatchmakingTextures",
    "settlerprotoname": "SettlerProtoName",
    "hcshipmentmodifier": "HCShipmentModifier",
    "startingunit": "StartingUnit",
    "townstartingunit": "TownStartingUnit",
    "empirewarsstartingunit": "EmpireWarsStartingUnit",
    "empirewarsresources": "EmpireWarsResources",
    "empirewarsshipmentxpmaximummodifier": "EmpireWarsShipmentXPMaximumModifier",
    "empirewarsshipmentgrowthmodifier": "EmpireWarsShipmentGrowthModifier",
    "empirewarsshipmentmodifier": "EmpireWarsShipmentModifier",
    "empirewarsshipmentrates": "EmpireWarsShipmentRates",
    "empirewarsageuprates": "EmpireWarsAgeUpRates",
    "randomstartingunits": "RandomStartingUnits",
    "unitregen": "UnitRegen",
    "multipleblocktrain": "MultipleBlockTrain",
    "bannertexture": "BannerTexture",
    "bannertexturecoords": "BannerTextureCoords",
    "portraittexture": "PortraitTexture",
    "portraittexturecoords": "PortraitTextureCoords",
    "smallportraittexture": "SmallPortraitTexture",
    "smallportraittexturecoords": "SmallPortraitTextureCoords",
    "smallportraittexturewpf": "SmallPortraitTextureWPF",
    "main": "Main",
    "name": "Name",
    "portrait": "Portrait",
    "culture": "Culture",
    "gold": "Gold",
    "food": "Food",
    "wood": "Wood",
    "civ": "Civ",
    "age0": "Age0",
    "age1": "Age1",
    "age2": "Age2",
    "age3": "Age3",
    "age4": "Age4",
    "age": "Age",
    "tech": "Tech",
    "xp": "XP",
    "ships": "Ships",
    "unittype": "UnitType",
    "rate": "Rate",
    "idletimeout": "IdleTimeout",
    "building": "Building",
    "multipleblockunit": "MultipleBlockUnit",
    "units": "Units",
    "unit": "Unit",
    "unitcounts": "UnitCounts",
    "count": "Count",
}


def _to_pascal(tag: str) -> str:
    """Convert lowercased XMB tag back to its civmods.xml canonical casing.

    XMB normalizes everything to lowercase. The vanilla civs.xml uses
    PascalCase (e.g. <StatsID>, <AgeTech>). We have to manually map back.
    """
    return _PASCAL_OVERRIDES.get(tag, tag)


def build_anw_civ_block(
    civ: AnwCiv,
    vanilla: ET.Element,
    *,
    display_id: int,
    rollover_id: int,
) -> str:
    """Render a complete <Civ>...</Civ> block for civmods.xml from vanilla data.

    Override fields (set by us):
      - <Name>{anw_token}</Name>
      - <DisplayNameID>{ANW range}</DisplayNameID>
      - <RolloverNameID>{ANW range}</RolloverNameID>
      - <HomeCityFilename>{anwhomecity*}</HomeCityFilename>

    All other fields lifted verbatim from vanilla.
    """
    lines: list[str] = []
    lines.append("\t<Civ>")
    lines.append(f"\t\t<Name>{civ.anw_token}</Name>")

    # Walk vanilla children in order, but inject our overrides at the right
    # positions to match civmods.xml conventions:
    #   <Main> after <Name>
    #   <DisplayNameID>/<RolloverNameID> right after <SettlerProtoName>
    #   <HomeCityFilename> just before <HomeCityFlagTexture>
    overrides_emitted = {"DisplayNameID", "RolloverNameID", "HomeCityFilename"}
    written = set()

    for child in vanilla:
        tag_lower = child.tag.lower()
        if tag_lower == "name":
            continue  # already wrote ANW token
        if tag_lower == "displaynameid":
            lines.append(f"\t\t<DisplayNameID>{display_id}</DisplayNameID>")
            written.add("DisplayNameID")
            continue
        if tag_lower == "rollovernameid":
            lines.append(f"\t\t<RolloverNameID>{rollover_id}</RolloverNameID>")
            written.add("RolloverNameID")
            continue
        if tag_lower == "homecityfilename":
            lines.append(f"\t\t<HomeCityFilename>{civ.new_homecity_filename}</HomeCityFilename>")
            written.add("HomeCityFilename")
            continue
        if tag_lower not in LIFTED_FIELDS:
            # Skip vanilla fields we don't carry forward (tag drift, deprecated
            # tags, anything not in our allow-list).
            continue
        # Emit the child verbatim with PascalCase
        lines.append(_render_element(child, depth=2).rstrip())

    # Inject any overrides that vanilla didn't have (rare — most civs have
    # all three; revolution-derived ones might lack RolloverNameID).
    if "DisplayNameID" not in written:
        lines.append(f"\t\t<DisplayNameID>{display_id}</DisplayNameID>")
    if "RolloverNameID" not in written:
        lines.append(f"\t\t<RolloverNameID>{rollover_id}</RolloverNameID>")
    if "HomeCityFilename" not in written:
        lines.append(f"\t\t<HomeCityFilename>{civ.new_homecity_filename}</HomeCityFilename>")

    lines.append("\t</Civ>")
    return "\n".join(lines) + "\n"


def _render_element(el: ET.Element, depth: int = 0) -> str:
    """Recursive PascalCase XML serializer. Mirrors civmods.xml indentation
    (1 tab per depth level, opening/closing tags on their own lines for
    elements with children, single-line for leafs)."""
    tag = _to_pascal(el.tag)
    ind = "\t" * depth
    children = list(el)
    text = (el.text or "").strip()
    if not children:
        if text:
            return f"{ind}<{tag}>{text}</{tag}>\n"
        return f"{ind}<{tag}></{tag}>\n"
    body = "".join(_render_element(c, depth + 1) for c in children)
    return f"{ind}<{tag}>\n{body}{ind}</{tag}>\n"


# ──────────────────────────────────────────────────────────────────────────────
# Stub replacement in civmods.anw.xml
# ──────────────────────────────────────────────────────────────────────────────


def replace_stubs(text: str, vanilla: dict[str, ET.Element]) -> tuple[str, int, list[str]]:
    """Walk the 22 base ANW civs (alphabetical) and replace each stub block
    with a fully-populated block built from vanilla data.

    Returns (new_text, replaced_count, missing_civ_names).
    """
    base_civs = [c for c in iter_anw_civs() if not c.is_revolution]
    base_civs.sort(key=lambda c: c.slug)

    replaced = 0
    missing: list[str] = []

    for i, civ in enumerate(base_civs):
        van = vanilla.get(civ.old_civ_token.lower())
        if van is None:
            missing.append(civ.old_civ_token)
            continue

        new_block = build_anw_civ_block(
            civ,
            van,
            display_id=BASE_CIV_DISPLAY_ID_BASE + i,
            rollover_id=BASE_CIV_ROLLOVER_ID_BASE + i,
        )

        # Match the existing stub: <Civ>...<Name>{anw_token}</Name>...</Civ>
        # The stubs all have the same structure (with TODO-ANW-VANILLA marker).
        stub_re = re.compile(
            r"\t<Civ>\s*\n"
            r"\t\t<Name>" + re.escape(civ.anw_token) + r"</Name>\s*\n"
            r"(?:[^<].*\n|\t\t<[^/].*\n|\t\t<!--.*?-->\s*\n)*?"
            r"\t</Civ>\s*\n",
            re.MULTILINE,
        )
        m = stub_re.search(text)
        if not m:
            missing.append(f"{civ.anw_token} (stub not found)")
            continue
        text = text[:m.start()] + new_block + text[m.end():]
        replaced += 1

    return text, replaced, missing


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--aoe3de-root", type=Path, default=DEFAULT_AOE3DE_ROOT,
                        help=f"Path to AoE3DE install root (default: {DEFAULT_AOE3DE_ROOT})")
    parser.add_argument("--check", action="store_true",
                        help="Exit non-zero if civmods.anw.xml still has TODO-ANW-VANILLA.")
    parser.add_argument("--dump-vanilla", type=Path, default=None,
                        help="Dump parsed vanilla civs.xml to this directory (debug).")
    args = parser.parse_args()

    if args.check:
        if not CIVMODS_ANW.is_file():
            print(f"missing {CIVMODS_ANW}", file=sys.stderr)
            return 1
        text = CIVMODS_ANW.read_text(encoding="utf-8")
        if "TODO-ANW-VANILLA" in text:
            print("DRIFT: civmods.anw.xml still has TODO-ANW-VANILLA stubs.", file=sys.stderr)
            return 1
        print("OK: civmods.anw.xml fully populated.", file=sys.stderr)
        return 0

    print(f"Reading vanilla civs.xml from {args.aoe3de_root}", file=sys.stderr)
    vanilla = load_vanilla_civs(args.aoe3de_root)

    if args.dump_vanilla:
        args.dump_vanilla.mkdir(parents=True, exist_ok=True)
        for name_lower, el in vanilla.items():
            xml_text = _render_element(el, depth=0)
            (args.dump_vanilla / f"{name_lower}.xml").write_text(xml_text, encoding="utf-8")
        print(f"  dumped {len(vanilla)} vanilla civs to {args.dump_vanilla}", file=sys.stderr)
        return 0

    if not CIVMODS_ANW.is_file():
        print(f"missing {CIVMODS_ANW}; run build_anw_civmods.py first", file=sys.stderr)
        return 1

    text = CIVMODS_ANW.read_text(encoding="utf-8")
    new_text, replaced, missing = replace_stubs(text, vanilla)

    print(f"  replaced {replaced}/22 base-civ stubs", file=sys.stderr)
    if missing:
        print(f"  MISSING: {missing}", file=sys.stderr)
        return 1

    if "TODO-ANW-VANILLA" in new_text:
        # Possible if a stub block didn't match the regex
        unmatched = new_text.count("TODO-ANW-VANILLA")
        print(f"  warn: {unmatched} TODO-ANW-VANILLA marker(s) remain", file=sys.stderr)

    CIVMODS_ANW.write_text(new_text, encoding="utf-8")
    print(f"wrote {CIVMODS_ANW}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
