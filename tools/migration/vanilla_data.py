"""Loader for vanilla AoE3:DE civ data + string table.

Used by `tools/cardextract/refresh_dev_subtrees.py` to surface the actual
text and art that the engine displays for base-game civs (British, Dutch,
Aztec, …) instead of placeholder "(base-game default)" notes. The base
civs aren't defined in our `data/civmods.xml` (the mod patches DLC content
on top of vanilla), so without vanilla data we'd have nothing to show.

Sources:

  - Vanilla civs.xml         — extracted from {AOE3DE}/Game/Data/Data.bar
                               via tools/migration/extract_vanilla_civs.py
                               OR directly via the BarExtractor below.
  - Vanilla stringtabley.xml — same archive, English language

Both are cached in /tmp/aoe3_data_extract/ on first read so subsequent
generator runs don't re-decompress the archive.

Public API:

  load_vanilla_data(aoe3de_root: Path | None = None) -> VanillaData

  VanillaData.civs[token_lower] = ET.Element        # one per civ
  VanillaData.strings[stringid]  = "resolved text"   # 45000+ entries
  VanillaData.resolve(stringid)  -> str
  VanillaData.field(civ_token, field_lower) -> str  # text of a civ field

If the AoE3DE install is not available, `load_vanilla_data()` returns None
and callers fall back to their existing behavior. The dev subtree generator
must NOT crash when this loader can't run.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.bar_extract import (  # noqa: E402
    maybe_decompress,
    parse_header,
    read_entries,
)
from tools.cardextract.xmb import parse_xmb  # noqa: E402

DEFAULT_AOE3DE_ROOT = Path(
    "/var/home/jflessenkemper/.local/share/Steam/steamapps/common/AoE3DE"
)
CACHE_DIR = Path("/tmp/aoe3_data_extract")


@dataclass
class VanillaData:
    civs: dict[str, ET.Element] = field(default_factory=dict)   # lower(token) → <civ>
    strings: dict[str, str] = field(default_factory=dict)       # stringID → text

    def resolve(self, sid: str) -> str:
        return self.strings.get(sid, "")

    def field(self, civ_token: str, field_lower: str) -> str:
        c = self.civs.get(civ_token.lower())
        if c is None:
            return ""
        return c.findtext(field_lower) or ""


def _read_xmb_from_bar(bar_path: Path, name_substring: str) -> bytes:
    """Pull the first XMB inside `bar_path` whose archive name contains
    `name_substring` (case-insensitive, slash-agnostic). Returns the
    decompressed bytes."""
    needle = name_substring.lower().replace("/", "\\")
    with bar_path.open("rb") as f:
        version, _n, table_offset = parse_header(f)
        _root, entries = read_entries(f, version, table_offset)
        target = next(
            (e for e in entries
             if needle in e["name"].lower().replace("/", "\\")),
            None,
        )
        if target is None:
            raise SystemExit(f"{bar_path.name}: '{name_substring}' not found")
        f.seek(target["offset"])
        raw = f.read(target["size2"])
    return maybe_decompress(raw)


def load_vanilla_data(aoe3de_root: Path | None = None) -> VanillaData | None:
    """Load + cache vanilla civs.xml + stringtable. Returns None if the
    AoE3DE install isn't available (caller should fall back gracefully).
    """
    root_path = aoe3de_root or DEFAULT_AOE3DE_ROOT
    bar = root_path / "Game" / "Data" / "Data.bar"
    if not bar.is_file():
        return None

    out = VanillaData()

    # ── Civs ──────────────────────────────────────────────────────────────
    civs_xmb = CACHE_DIR / "civs.xml.XMB"
    if not civs_xmb.is_file():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        civs_xmb.write_bytes(_read_xmb_from_bar(bar, "civs.xml.XMB"))
    civs_root = parse_xmb(civs_xmb.read_bytes())
    for c in civs_root:
        if c.tag != "civ":
            continue
        n = c.findtext("name") or ""
        if n:
            out.civs[n.lower()] = c

    # ── String table (English) ────────────────────────────────────────────
    strings_xmb = CACHE_DIR / "stringtabley.xml.XMB"
    if not strings_xmb.is_file():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        strings_xmb.write_bytes(_read_xmb_from_bar(bar, "strings/English/stringtabley.xml.XMB"))
    st_root = parse_xmb(strings_xmb.read_bytes())
    lang = next((c for c in st_root if c.tag == "language"), None)
    if lang is not None:
        for s in lang:
            if s.tag != "string":
                continue
            sid = s.attrib.get("_locid") or s.attrib.get("_locID") or s.attrib.get("id") or ""
            if sid:
                out.strings[sid] = s.text or ""

    return out


if __name__ == "__main__":
    data = load_vanilla_data()
    if data is None:
        print("Vanilla data unavailable.")
        sys.exit(1)
    print(f"Vanilla civs: {len(data.civs)}")
    print(f"Vanilla strings: {len(data.strings)}")
    for token in ("british", "dutch", "xpaztec", "deamericans"):
        c = data.civs.get(token)
        if c is None:
            print(f"  {token}: not found")
            continue
        dn = c.findtext("displaynameid")
        print(f"  {token}: DisplayNameID={dn} → {data.resolve(dn)!r}")
