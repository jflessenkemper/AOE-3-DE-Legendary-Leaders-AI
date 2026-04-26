"""Single source of truth: per-civ expected runtime behaviour.

We parse the same files the static validators read (`leaderCommon.xs`,
`civmods.xml`, `data/*homecity*.xml`) and emit a flat per-civ record
that downstream verifiers compare against the actual game state.

Each `CivExpectation` carries:
  * civ_id           — the constant the engine uses (`cCivBritish`, or
                       a `RvltMod*` string for revolutions).
  * label            — human-readable display label ("British",
                       "Napoleonic France").
  * leader_key       — the `gLLLeaderKey` string the leader portrait /
                       name override is wired to.
  * deck_name        — the deck label that should appear in the in-game
                       Deck Builder for this civ.
  * terrain_primary  — `cLLTerrain*` constant, e.g. "cLLTerrainCoast".
  * terrain_secondary
  * terrain_strength — float in [0.0, 1.0]
  * heading          — `cLLHeading*` constant
  * heading_strength
  * water_bias       — derived: +1 (toward water), -1 (toward inland),
                       0 (neutral). Used by the layout verifier.
  * heading_axis     — derived: "tangent" (AlongCoast/Upriver/Trade),
                       "outward" (Frontier/IslandHop), "inward"
                       (Defensive/OutwardRings), or "none".

The module re-uses the brace-walking parser from
`tools/validation/validate_terrain_heading.py` so we don't rewrite that
logic.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.validation.validate_terrain_heading import (  # noqa: E402
    BASE_CIVS,
    REVOLUTION_CIVS,
    _extract_apply_body,
    _split_branches,
)

LEADER_COMMON = REPO_ROOT / "game/ai/leaders/leaderCommon.xs"
CIVMODS = REPO_ROOT / "data/civmods.xml"
DATA_DIR = REPO_ROOT / "data"

# Terrain → semantic water bias. Coast/River/Wetland gravitate toward
# the navy vector; Highland/DesertOasis push inland. Plain/Forest/Any
# don't directly imply a water relationship.
TERRAIN_WATER_BIAS = {
    "cLLTerrainCoast": +1,
    "cLLTerrainRiver": +1,
    "cLLTerrainWetland": +1,
    "cLLTerrainHighland": -1,
    "cLLTerrainDesertOasis": -1,
    "cLLTerrainPlain": 0,
    "cLLTerrainForestEdge": 0,
    "cLLTerrainJungle": 0,
    "cLLTerrainAny": 0,
}

# Heading → expected expansion axis relative to base.
HEADING_AXIS = {
    "cLLHeadingAlongCoast": "tangent",
    "cLLHeadingUpriver": "tangent",
    "cLLHeadingFollowTradeRoute": "tangent",
    "cLLHeadingFrontierPush": "outward",
    "cLLHeadingIslandHop": "outward",
    "cLLHeadingDefensive": "inward",
    "cLLHeadingOutwardRings": "inward",
    "cLLHeadingAny": "none",
}

# Civ-id → display label. Base-civ ids match `cCiv*` constants; rvlt ids
# match the rvltName string keys used in leaderCommon.xs.
CIV_LABELS = {
    "cCivBritish": "British",
    "cCivChinese": "Chinese",
    "cCivDEAmericans": "Americans",
    "cCivDEEthiopians": "Ethiopians",
    "cCivDEHausa": "Hausa",
    "cCivDEInca": "Inca",
    "cCivDEItalians": "Italians",
    "cCivDEMaltese": "Maltese",
    "cCivDEMexicans": "Mexicans",
    "cCivDESwedish": "Swedish",
    "cCivDutch": "Dutch",
    "cCivFrench": "French (Bourbon)",
    "cCivGermans": "Germans",
    "cCivIndians": "Indians",
    "cCivJapanese": "Japanese",
    "cCivOttomans": "Ottomans",
    "cCivPortuguese": "Portuguese",
    "cCivRussians": "Russians",
    "cCivSpanish": "Spanish",
    "cCivXPAztec": "Aztecs",
    "cCivXPIroquois": "Iroquois (Haudenosaunee)",
    "cCivXPSioux": "Lakota (Sioux)",
    "RvltModAmericans": "Americans (Revolution)",
    "RvltModArgentines": "Argentina",
    "RvltModBajaCalifornians": "Baja California",
    "RvltModBarbary": "Barbary States",
    "RvltModBrazil": "Brazil",
    "RvltModCalifornians": "California",
    "RvltModCanadians": "Canada",
    "RvltModCentralAmericans": "Central America",
    "RvltModChileans": "Chile",
    "RvltModColumbians": "Colombia",
    "RvltModEgyptians": "Egypt",
    "RvltModFinnish": "Finland",
    "RvltModFrenchCanadians": "French Canada",
    "RvltModHaitians": "Haiti",
    "RvltModHungarians": "Hungary",
    "RvltModIndonesians": "Indonesia",
    "RvltModMayans": "Maya",
    "RvltModMexicans": "Mexico (Revolution)",
    "RvltModNapoleonicFrance": "Napoleonic France",
    "RvltModPeruvians": "Peru",
    "RvltModRevolutionaryFrance": "Revolutionary France",
    "RvltModRioGrande": "Rio Grande",
    "RvltModRomanians": "Romania",
    "RvltModSouthAfricans": "South Africa",
    "RvltModTexians": "Texas",
    "RvltModYucatan": "Yucatán",
}


@dataclass(frozen=True)
class CivExpectation:
    civ_id: str
    label: str
    leader_key: str
    deck_name: str
    terrain_primary: str
    terrain_secondary: str
    terrain_strength: float
    heading: str
    heading_strength: float

    @property
    def water_bias(self) -> int:
        # Primary outweighs secondary 2:1.
        primary = TERRAIN_WATER_BIAS.get(self.terrain_primary, 0)
        secondary = TERRAIN_WATER_BIAS.get(self.terrain_secondary, 0)
        score = 2 * primary + secondary
        if score > 0:
            return +1
        if score < 0:
            return -1
        return 0

    @property
    def heading_axis(self) -> str:
        return HEADING_AXIS.get(self.heading, "none")

    @property
    def is_revolution(self) -> bool:
        return self.civ_id.startswith("RvltMod")


# --- parsing -----------------------------------------------------------------

_TERRAIN_CALL_RE = re.compile(
    r"llSetPreferredTerrain\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^\)]+?)\s*\)"
)
_HEADING_CALL_RE = re.compile(
    r"llSetExpansionHeading\s*\(\s*([^,]+?)\s*,\s*([^\)]+?)\s*\)"
)
_LEADER_KEY_RE = re.compile(
    r"""(?:cMyCiv\s*==\s*(?P<civ>cCiv[A-Za-z0-9_]+)
       | rvltName\s*==\s*"(?P<rvlt>[^"]+)")
       \s*\)\s*\{\s*gLLLeaderKey\s*=\s*"(?P<key>[^"]+)"\s*;""",
    re.VERBOSE,
)


def _parse_apply_branches(leader_text: str) -> dict[str, dict]:
    body = _extract_apply_body(leader_text)
    if body is None:
        raise RuntimeError("llApplyBuildStyleForActiveCiv() body not found in leaderCommon.xs")

    out: dict[str, dict] = {}
    for label, branch in _split_branches(body):
        terrain = _TERRAIN_CALL_RE.search(branch)
        heading = _HEADING_CALL_RE.search(branch)
        if not terrain or not heading:
            continue
        out[label] = {
            "terrain_primary": terrain.group(1).strip(),
            "terrain_secondary": terrain.group(2).strip(),
            "terrain_strength": float(terrain.group(3).strip()),
            "heading": heading.group(1).strip(),
            "heading_strength": float(heading.group(2).strip()),
        }
    return out


def _parse_leader_keys(leader_text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in _LEADER_KEY_RE.finditer(leader_text):
        label = m.group("civ") or m.group("rvlt")
        out[label] = m.group("key")
    return out


def _parse_homecity_for_civ(civmods_text: str) -> dict[str, str]:
    """Map civ Name → HomeCityFilename. Naive line-walking, sufficient
    for the very regular structure of civmods.xml.
    """
    out: dict[str, str] = {}
    current_name: str | None = None
    for line in civmods_text.splitlines():
        m_name = re.search(r"<Name>\s*(\S+?)\s*</Name>", line)
        if m_name:
            current_name = m_name.group(1)
            continue
        m_hc = re.search(r"<HomeCityFilename>\s*(\S+?)\s*</HomeCityFilename>", line)
        if m_hc and current_name:
            out[current_name] = m_hc.group(1)
            current_name = None
    return out


_DECK_NAME_RE = re.compile(
    r"<decks>(?P<body>.*?)</decks>", re.DOTALL
)
_INNER_NAME_RE = re.compile(r"<deck>\s*<name>(?P<name>[^<]+)</name>", re.DOTALL)


def _parse_deck_name(homecity_path: Path) -> str:
    """Return the first <deck>'s <name>. The mod renames every slot to
    the same string per civ, so the first slot is canonical.
    """
    if not homecity_path.exists():
        return "<missing homecity>"
    text = homecity_path.read_text(encoding="utf-8")
    decks = _DECK_NAME_RE.search(text)
    if not decks:
        return "<no <decks> block>"
    inner = _INNER_NAME_RE.search(decks.group("body"))
    if not inner:
        return "<no inner deck name>"
    return inner.group("name").strip()


# civmods.xml only registers the 26 revolution civs (base civs use
# stock packed homecity data). For base civs we map directly to the
# `data/homecity<slug>.xml` file the mod ships alongside.
_BASE_CIV_HOMECITY = {
    "cCivBritish": "homecitybritish.xml",
    "cCivChinese": "homecitychinese.xml",
    "cCivDEAmericans": "homecityamericans.xml",
    "cCivDEEthiopians": "homecityethiopians.xml",
    "cCivDEHausa": "homecityhausa.xml",
    "cCivDEInca": "homecitydeinca.xml",
    "cCivDEItalians": "homecityitalians.xml",
    "cCivDEMaltese": "homecitymaltese.xml",
    "cCivDEMexicans": "homecitymexicans.xml",
    "cCivDESwedish": "homecityswedish.xml",
    "cCivDutch": "homecitydutch.xml",
    "cCivFrench": "homecityfrench.xml",
    "cCivGermans": "homecitygerman.xml",
    "cCivIndians": "homecityindians.xml",
    "cCivJapanese": "homecityjapanese.xml",
    "cCivOttomans": "homecityottomans.xml",
    "cCivPortuguese": "homecityportuguese.xml",
    "cCivRussians": "homecityrussians.xml",
    "cCivSpanish": "homecityspanish.xml",
    "cCivXPAztec": "homecityxpaztec.xml",
    "cCivXPIroquois": "homecityxpiroquois.xml",
    "cCivXPSioux": "homecityxpsioux.xml",
}


def _resolve_homecity_filename(
    civ_id: str, civmods_map: dict[str, str]
) -> Path | None:
    if civ_id.startswith("RvltMod"):
        # Revolution civs: civmods <Name> matches the rvlt id directly.
        fname = civmods_map.get(civ_id)
    else:
        fname = _BASE_CIV_HOMECITY.get(civ_id)
    if not fname:
        return None
    return DATA_DIR / fname


def load_expectations(repo_root: Path = REPO_ROOT) -> list[CivExpectation]:
    leader_text = (repo_root / "game/ai/leaders/leaderCommon.xs").read_text(encoding="utf-8")
    civmods_text = (repo_root / "data/civmods.xml").read_text(encoding="utf-8")

    apply_branches = _parse_apply_branches(leader_text)
    leader_keys = _parse_leader_keys(leader_text)
    civmods_map = _parse_homecity_for_civ(civmods_text)

    out: list[CivExpectation] = []
    for civ_id in (*BASE_CIVS, *REVOLUTION_CIVS):
        if civ_id not in apply_branches:
            continue
        b = apply_branches[civ_id]
        hc_path = _resolve_homecity_filename(civ_id, civmods_map)
        deck_name = _parse_deck_name(hc_path) if hc_path else "<no homecity mapping>"
        out.append(
            CivExpectation(
                civ_id=civ_id,
                label=CIV_LABELS.get(civ_id, civ_id),
                leader_key=leader_keys.get(civ_id, "<unmapped>"),
                deck_name=deck_name,
                terrain_primary=b["terrain_primary"],
                terrain_secondary=b["terrain_secondary"],
                terrain_strength=b["terrain_strength"],
                heading=b["heading"],
                heading_strength=b["heading_strength"],
            )
        )
    return out


__all__ = [
    "CivExpectation",
    "TERRAIN_WATER_BIAS",
    "HEADING_AXIS",
    "CIV_LABELS",
    "load_expectations",
]
