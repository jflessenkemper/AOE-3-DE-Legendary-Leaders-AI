"""Canonical 48-civ ANW namespace map.

Single source of truth for the ANW migration. Every other migration script
(build_anw_civmods, migrate_strings, migrate_personalities, build_anw_decks)
imports `ANW_CIVS` and `iter_anw_civs()` from here so the slug → token mapping
is defined exactly once.

After the migration lands, the validators and refreshers in
`tools/validation/` and `tools/cardextract/` rebase onto this module too,
collapsing their existing base/rev branching into a single code path.

Schema for each row:

    AnwCiv(
        slug                = canonical English name (matches HTML data-name root,
                              and the existing CIV_TO_HOMECITY key)
        anw_token           = `ANW{PascalCase}` — the <Civ><Name> in civmods.xml
                              and the <forcedciv> token in .personality files
        anw_stem            = `anw{lower}` — used for filenames
                              (anw{stem}.personality, anwhomecity{stem}.xml)
        old_civ_token       = the engine civ-token before migration
                              (base-game token like "british" / "dutch" / "XPAztec",
                              or "RvltMod{X}" for revolution civs)
        old_personality_stem = filename stem of the existing .personality file
                              (without `.personality` extension)
        old_homecity_stem   = filename stem of the existing homecity file
                              (without `.xml` extension)
        leader_display      = English display name of the leader
                              (used for HTML, dev-subtree, lobby tooltip)
        is_revolution       = True if this civ is a revolution-style civ
                              (had a RvltMod prefix before migration)
        chatset_old         = chatset name in the old `<chatset>` field
                              (the personality `.personality` file's existing
                              chatset name, e.g. "wellington" for base British,
                              "rvltmodbarbary" for rev Barbary). The new chatset
                              name will always be f"anw_{anw_stem[3:]}".
    )

To consume:

    from tools.migration.anw_token_map import ANW_CIVS, iter_anw_civs, by_anw_token

    for civ in iter_anw_civs():
        print(civ.anw_token, civ.leader_display)

    british = by_anw_token("ANWBritish")
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class AnwCiv:
    slug: str
    anw_token: str
    anw_stem: str
    old_civ_token: str
    old_personality_stem: str
    old_homecity_stem: str
    leader_display: str
    is_revolution: bool
    chatset_old: str

    @property
    def chatset_new(self) -> str:
        # anw_stem is `anw<civ>`; strip the `anw` prefix and re-prefix as `anw_<civ>`
        # for the new chatset namespace (separator makes downstream parsing trivial).
        return f"anw_{self.anw_stem[3:]}"

    @property
    def new_personality_filename(self) -> str:
        return f"{self.anw_stem}.personality"

    @property
    def new_homecity_filename(self) -> str:
        return f"anwhomecity{self.anw_stem[3:]}.xml"

    @property
    def old_personality_filename(self) -> str:
        return f"{self.old_personality_stem}.personality"

    @property
    def old_homecity_filename(self) -> str:
        return f"{self.old_homecity_stem}.xml"


# ──────────────────────────────────────────────────────────────────────────────
# The canonical 48 civs. Order: 22 base civs (alphabetical), then 26 revolution
# civs (alphabetical). Two of the revolution civs (Americans, Mexicans Revolution)
# are currently deferred from the HTML reference but ARE first-class in civmods +
# personality + decks data, so they're included here. After migration there are
# no deferred slugs — every ANW civ has an HTML nation-node.
# ──────────────────────────────────────────────────────────────────────────────

ANW_CIVS: tuple[AnwCiv, ...] = (
    # ── Base civs (22) ─────────────────────────────────────────────────────────
    AnwCiv("Aztecs",            "ANWAztecs",          "anwaztecs",
           "XPAztec",      "montezuma", "homecityxpaztec",
           "Montezuma II",                    False, "montezuma"),
    AnwCiv("British",           "ANWBritish",         "anwbritish",
           "british",      "wellington", "homecitybritish",
           "Queen Elizabeth I",               False, "wellington"),
    AnwCiv("Chinese",           "ANWChinese",         "anwchinese",
           "chinese",      "kangxi", "homecitychinese",
           "Kangxi",                          False, "kangxi"),
    AnwCiv("Dutch",             "ANWDutch",           "anwdutch",
           "dutch",        "maurice", "homecitydutch",
           "Maurice of Nassau",               False, "maurice"),
    AnwCiv("Ethiopians",        "ANWEthiopians",      "anwethiopians",
           "DEEthiopians", "menelik", "homecityethiopians",
           "Menelik II",                      False, "menelik"),
    AnwCiv("French",            "ANWFrench",          "anwfrench",
           "french",       "napoleon", "homecityfrench",
           "Louis XVIII",                     False, "napoleon"),
    AnwCiv("Germans",           "ANWGermans",         "anwgermans",
           "germans",      "Frederick", "homecitygerman",
           "Frederick the Great",             False, "Frederick"),
    AnwCiv("Haudenosaunee",     "ANWHaudenosaunee",   "anwhaudenosaunee",
           "XPIroquois",   "Hiawatha", "homecityxpiroquois",
           "Hiawatha",                        False, "Hiawatha"),
    AnwCiv("Hausa",             "ANWHausa",           "anwhausa",
           "DEHausa",      "usman", "homecityhausa",
           "Muhammadu Kanta",                 False, "usman"),
    AnwCiv("Inca",              "ANWInca",            "anwinca",
           "DEInca",       "pachacuti", "homecitydeinca",
           "Pachacuti",                       False, "pachacuti"),
    AnwCiv("Indians",           "ANWIndians",         "anwindians",
           "indians",      "shivaji", "homecityindians",
           "Shivaji Maharaj",                 False, "shivaji"),
    AnwCiv("Italians",          "ANWItalians",        "anwitalians",
           "DEItalians",   "garibaldi", "homecityitalians",
           "Garibaldi",                       False, "garibaldi"),
    AnwCiv("Japanese",          "ANWJapanese",        "anwjapanese",
           "japanese",     "tokugawa", "homecityjapanese",
           "Tokugawa Ieyasu",                 False, "tokugawa"),
    AnwCiv("Lakota",            "ANWLakota",          "anwlakota",
           "XPSioux",      "crazyhorse", "homecityxpsioux",
           "Gall",                            False, "crazyhorse"),
    AnwCiv("Maltese",           "ANWMaltese",         "anwmaltese",
           "DEMaltese",    "jean", "homecitymaltese",
           "Jean de Valette",                 False, "jean"),
    AnwCiv("Mexicans (Standard)", "ANWMexicans",      "anwmexicans",
           "demexicans",   "hidalgo", "homecitymexicans",
           "Hidalgo",                         False, "hidalgo"),
    AnwCiv("Ottomans",          "ANWOttomans",        "anwottomans",
           "ottomans",     "Suleiman", "homecityottomans",
           "Suleiman the Magnificent",        False, "Suleiman"),
    AnwCiv("Portuguese",        "ANWPortuguese",      "anwportuguese",
           "portuguese",   "henry", "homecityportuguese",
           "Henry the Navigator",             False, "henry"),
    AnwCiv("Russians",          "ANWRussians",        "anwrussians",
           "russians",     "catherine", "homecityrussians",
           "Ivan the Terrible",               False, "catherine"),
    AnwCiv("Spanish",           "ANWSpanish",         "anwspanish",
           "spanish",      "isabella", "homecityspanish",
           "Isabella of Castile",             False, "isabella"),
    AnwCiv("Swedes",            "ANWSwedes",          "anwswedes",
           "deswedish",    "Gustav", "homecityswedish",
           "Gustavus Adolphus",               False, "Gustav"),
    AnwCiv("United States",     "ANWUSA",             "anwusa",
           "deamericans",  "washington", "homecityamericans",
           "George Washington",               False, "washington"),

    # ── Revolution civs (26) ───────────────────────────────────────────────────
    AnwCiv("Americans",         "ANWAmericansRev",    "anwamericansrev",
           "RvltModAmericans",        "rvltmodamericans",         "rvltmodhomecityamericans",
           "Thomas Jefferson",                True, "rvltmodamericans"),
    AnwCiv("Argentines",        "ANWArgentines",      "anwargentines",
           "RvltModArgentines",       "rvltmodargentines",        "rvltmodhomecityargentina",
           "José de San Martín",              True, "rvltmodargentines"),
    AnwCiv("Baja Californians", "ANWBajaCalifornians","anwbajacalifornians",
           "RvltModBajaCalifornians", "rvltmodbajacalifornians",  "rvltmodhomecitybajacalifornians",
           "Manuel Pineda Muñoz",             True, "rvltmodbajacalifornians"),
    AnwCiv("Barbary",           "ANWBarbary",         "anwbarbary",
           "RvltModBarbary",          "rvltmodbarbary",           "rvltmodhomecitybarbary",
           "Hayreddin Barbarossa",            True, "rvltmodbarbary"),
    AnwCiv("Brazil",            "ANWBrazil",          "anwbrazil",
           "RvltModBrazil",           "rvltmodbrazil",            "rvltmodhomecitybrazil",
           "Pedro I",                         True, "rvltmodbrazil"),
    AnwCiv("Californians",      "ANWCalifornians",    "anwcalifornians",
           "RvltModCalifornians",     "rvltmodcalifornians",      "rvltmodhomecitycalifornia",
           "Mariano Guadalupe Vallejo",       True, "rvltmodcalifornians"),
    AnwCiv("Canadians",         "ANWCanadians",       "anwcanadians",
           "RvltModCanadians",        "rvltmodcanadians",         "rvltmodhomecitycanada",
           "Isaac Brock",                     True, "rvltmodcanadians"),
    AnwCiv("Central Americans", "ANWCentralAmericans","anwcentralamericans",
           "RvltModCentralAmericans", "rvltmodcentralamericans",  "rvltmodhomecitycentralamericans",
           "Francisco Morazán",               True, "rvltmodcentralamericans"),
    AnwCiv("Chileans",          "ANWChileans",        "anwchileans",
           "RvltModChileans",         "rvltmodchileans",          "rvltmodhomecitychile",
           "Bernardo O'Higgins",              True, "rvltmodchileans"),
    AnwCiv("Columbians",        "ANWColumbians",      "anwcolumbians",
           "RvltModColumbians",       "rvltmodcolumbians",        "rvltmodhomecitycolumbia",
           "Simón Bolívar",                   True, "rvltmodcolumbians"),
    AnwCiv("Egyptians",         "ANWEgyptians",       "anwegyptians",
           "RvltModEgyptians",        "rvltmodegyptians",         "rvltmodhomecityegypt",
           "Muhammad Ali",                    True, "rvltmodegyptians"),
    AnwCiv("Finnish",           "ANWFinnish",         "anwfinnish",
           "RvltModFinnish",          "rvltmodfinnish",           "rvltmodhomecityfinland",
           "Carl Gustaf Emil Mannerheim",     True, "rvltmodfinnish"),
    AnwCiv("French Canadians",  "ANWFrenchCanadians", "anwfrenchcanadians",
           "RvltModFrenchCanadians",  "rvltmodfrenchcanadians",   "rvltmodhomecityfrenchcanada",
           "Louis-Joseph Papineau",           True, "rvltmodfrenchcanadians"),
    AnwCiv("Haitians",          "ANWHaitians",        "anwhaitians",
           "RvltModHaitians",         "rvltmodhaitians",          "rvltmodhomecityhaiti",
           "Toussaint Louverture",            True, "rvltmodhaitians"),
    AnwCiv("Hungarians",        "ANWHungarians",      "anwhungarians",
           "RvltModHungarians",       "rvltmodhungarians",        "rvltmodhomecityhungary",
           "Lajos Kossuth",                   True, "rvltmodhungarians"),
    AnwCiv("Indonesians",       "ANWIndonesians",     "anwindonesians",
           "RvltModIndonesians",      "rvltmodindonesians",       "rvltmodhomecityindonesians",
           "Diponegoro",                      True, "rvltmodindonesians"),
    AnwCiv("Mayans",            "ANWMayans",          "anwmayans",
           "RvltModMayans",           "rvltmodmayans",            "rvltmodhomecitymaya",
           "Jacinto Canek",                   True, "rvltmodmayans"),
    AnwCiv("Mexicans (Revolution)", "ANWMexicansRev", "anwmexicansrev",
           "RvltModMexicans",         "rvltmodmexicans",          "rvltmodhomecitymexicans",
           "Benito Juárez",                   True, "rvltmodmexicans"),
    AnwCiv("Napoleonic France", "ANWNapoleonicFrance","anwnapoleonicfrance",
           "RvltModNapoleonicFrance", "rvltmodnapoleonicfrance",  "rvltmodhomecitynapoleon",
           "Napoleon Bonaparte",              True, "rvltmodnapoleonicfrance"),
    AnwCiv("Peruvians",         "ANWPeruvians",       "anwperuvians",
           "RvltModPeruvians",        "rvltmodperuvians",         "rvltmodhomecityperu",
           "Andrés de Santa Cruz",            True, "rvltmodperuvians"),
    AnwCiv("Revolutionary France", "ANWRevFrance",    "anwrevfrance",
           "RvltModRevolutionaryFrance", "rvltmodrevolutionaryfrance", "rvltmodhomecityrevolutionaryfrance",
           "Maximilien Robespierre",          True, "rvltmodrevolutionaryfrance"),
    AnwCiv("Rio Grande",        "ANWRioGrande",       "anwriogrande",
           "RvltModRioGrande",        "rvltmodriogrande",         "rvltmodhomecityriogrande",
           "Antonio Canales Rosillo",         True, "rvltmodriogrande"),
    AnwCiv("Romanians",         "ANWRomanians",       "anwromanians",
           "RvltModRomanians",        "rvltmodromanians",         "rvltmodhomecityromania",
           "Alexandru Ioan Cuza",             True, "rvltmodromanians"),
    AnwCiv("South Africans",    "ANWSouthAfricans",   "anwsouthafricans",
           "RvltModSouthAfricans",    "rvltmodsouthafricans",     "rvltmodhomecitysouthafricans",
           "Paul Kruger",                     True, "rvltmodsouthafricans"),
    AnwCiv("Texians",           "ANWTexians",         "anwtexians",
           "RvltModTexians",          "rvltmodtexians",           "rvltmodhomecitytexas",
           "Sam Houston",                     True, "rvltmodtexians"),
    AnwCiv("Yucatan",           "ANWYucatan",         "anwyucatan",
           "RvltModYucatan",          "rvltmodyucatan",           "rvltmodhomecityyucatan",
           "Felipe Carrillo Puerto",          True, "rvltmodyucatan"),
)


# ──────────────────────────────────────────────────────────────────────────────
# Lookup helpers
# ──────────────────────────────────────────────────────────────────────────────


def iter_anw_civs() -> Iterator[AnwCiv]:
    """Yield all 48 civs in canonical order (base civs first, then revolutions)."""
    yield from ANW_CIVS


def by_slug(slug: str) -> AnwCiv:
    """Look up by canonical slug (e.g. 'British', 'Mexicans (Revolution)')."""
    for c in ANW_CIVS:
        if c.slug == slug:
            return c
    raise KeyError(slug)


def by_anw_token(token: str) -> AnwCiv:
    """Look up by ANW civ token (e.g. 'ANWBritish')."""
    for c in ANW_CIVS:
        if c.anw_token == token:
            return c
    raise KeyError(token)


def by_old_civ_token(token: str) -> AnwCiv:
    """Look up by pre-migration civ token (e.g. 'british', 'RvltModBarbary').

    Case-insensitive match — base-game tokens vary in casing.
    """
    lt = token.lower()
    for c in ANW_CIVS:
        if c.old_civ_token.lower() == lt:
            return c
    raise KeyError(token)


def by_old_personality_stem(stem: str) -> AnwCiv:
    """Look up by pre-migration personality filename stem (e.g. 'wellington')."""
    ls = stem.lower()
    for c in ANW_CIVS:
        if c.old_personality_stem.lower() == ls:
            return c
    raise KeyError(stem)


def by_old_homecity_stem(stem: str) -> AnwCiv:
    """Look up by pre-migration homecity filename stem (e.g. 'homecitybritish')."""
    ls = stem.lower()
    for c in ANW_CIVS:
        if c.old_homecity_stem.lower() == ls:
            return c
    raise KeyError(stem)


# ──────────────────────────────────────────────────────────────────────────────
# Self-check (runs as `python3 -m tools.migration.anw_token_map`)
# ──────────────────────────────────────────────────────────────────────────────

def _self_check() -> None:
    """Sanity-check the table for typos: uniqueness + counts."""
    slugs = [c.slug for c in ANW_CIVS]
    tokens = [c.anw_token for c in ANW_CIVS]
    stems = [c.anw_stem for c in ANW_CIVS]
    old_pers = [c.old_personality_stem for c in ANW_CIVS]
    old_hcs = [c.old_homecity_stem for c in ANW_CIVS]

    assert len(ANW_CIVS) == 48, f"expected 48 civs, got {len(ANW_CIVS)}"
    assert len(set(slugs)) == 48, f"duplicate slug: {sorted(slugs)}"
    assert len(set(tokens)) == 48, f"duplicate ANW token: {sorted(tokens)}"
    assert len(set(stems)) == 48, f"duplicate ANW stem: {sorted(stems)}"
    assert len(set(old_pers)) == 48, (
        f"duplicate personality stem: "
        f"{[s for s in old_pers if old_pers.count(s) > 1]}"
    )
    assert len(set(old_hcs)) == 48, (
        f"duplicate homecity stem: "
        f"{[s for s in old_hcs if old_hcs.count(s) > 1]}"
    )

    base_count = sum(1 for c in ANW_CIVS if not c.is_revolution)
    rev_count = sum(1 for c in ANW_CIVS if c.is_revolution)
    assert base_count == 22, f"expected 22 base civs, got {base_count}"
    assert rev_count == 26, f"expected 26 revolution civs, got {rev_count}"

    for c in ANW_CIVS:
        assert c.anw_token.startswith("ANW"), c
        assert c.anw_stem.startswith("anw"), c
        assert c.anw_stem == c.anw_token.lower().replace(" ", ""), (
            f"{c.slug}: anw_stem {c.anw_stem!r} should match "
            f"anw_token.lower() = {c.anw_token.lower()!r}"
        )

    print(f"anw_token_map: 48/48 civs ({base_count} base + {rev_count} rev), "
          f"all unique, all ANW-prefixed.")


if __name__ == "__main__":
    _self_check()
