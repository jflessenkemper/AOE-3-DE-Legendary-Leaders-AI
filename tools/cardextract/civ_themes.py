"""Per-civ thematic config used by build_themed_decks.py.

For each civ we keep:
  keywords      - substrings (case-insensitive, matched against the card NAME)
                  that earn a big scoring bonus. Drives "give Napoleon his
                  Napoleonic cards" behaviour.
  must_include  - card names that MUST land in the 25-card deck (use sparingly,
                  reserved for absolute icons of the civ/leader).
  must_exclude  - card names that MUST NOT land in the deck (overrides scoring).
  buildstyle    - the archetype name for this civ (matches prose_buildstyle.py).
                  Maps to extra keywords via BUILDSTYLE_KEYWORDS so the deck
                  reinforces the build doctrine.

Keys are the homecity XML basename (without .xml) so the build script can look
them up directly from data/.
"""
from __future__ import annotations

# Buildstyle archetype → extra keyword hints. Lets the deck pick cards that
# reinforce how the AI is wired to build/play.
BUILDSTYLE_KEYWORDS: dict[str, list[str]] = {
    "Compact Fortified Core":     ["fort", "wall", "tower", "outpost", "garrison", "fortif", "bastion"],
    "Forward Operational Line":   ["fort", "outpost", "barrack", "stable", "frontier", "assault"],
    "Mobile Frontier Scatter":    ["townceneter", "trading", "scout", "settler", "wagon", "explorer"],
    "Distributed Economic Network": ["mill", "plantation", "market", "bank", "factory", "trade", "exotic", "refrig"],
    "Civic Militia Center":       ["militia", "minute", "outpost", "townceneter", "townwatch"],
    "Shrine or Trade Node Spread": ["shrine", "trading", "sacred", "wonder", "monastery"],
    "Jungle Guerrilla Network":   ["guerr", "warhut", "warchief", "ambush", "forest", "jungle", "raid"],
    "Naval Mercantile Compound":  ["dock", "fish", "caravel", "frigate", "galleon", "ironclad", "monitor", "fleet", "merchant"],
    "Highland Citadel":           ["fort", "wall", "citadel", "stone", "highland", "bastion", "fortif"],
    "Siege Train Concentration":  ["cannon", "mortar", "falconet", "culverin", "artillery", "foundry", "siege", "battery", "bombard"],
    "Steppe Cavalry Wedge":       ["hussar", "dragoon", "cuirass", "cossack", "cavalry", "rider", "lancer", "horse", "stable"],
    "Cossack Voisko":             ["cossack", "ataman", "raider", "horseman", "townceneter", "blockhouse"],
    "Republican Levee":           ["musketeer", "skirmisher", "regular", "infantry", "general", "barrack", "officer"],
    "Andean Terrace Fortress":    ["fort", "wall", "kallanka", "tambo", "stone", "andean", "highland"],
}


# Standard 22 civs ──────────────────────────────────────────────────────────
STANDARD: dict[str, dict] = {
    "homecitybritish": {
        "keywords": ["british", "manor", "longbow", "musketeer", "rogers", "redcoat", "tea", "anglican", "highlander", "naval"],
        "must_include": ["HCRogersRangers"] if False else [],
        "must_exclude": [],
        "buildstyle": "Compact Fortified Core",
    },
    "homecityfrench": {
        # Standard French = Joan of Arc / pre-revolutionary monarchy flavour.
        # Napoleonic + revolutionary cards are the REVOLUTION civs' job.
        "keywords": ["french", "coureur", "cuirass", "skirmisher", "voltigeur", "voyageur", "tirail", "cherokee"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Mobile Frontier Scatter",
    },
    "homecitydutch": {
        "keywords": ["dutch", "ruyter", "fluyt", "bank", "stadhouder", "fishing", "envoy", "settler", "envoy", "halberdier"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Naval Mercantile Compound",
    },
    "homecitygerman": {
        "keywords": ["german", "uhlan", "doppelsold", "warwagon", "settler", "landsknecht", "habsburg", "hesse", "needle"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Steppe Cavalry Wedge",
    },
    "homecityottomans": {
        "keywords": ["ottoman", "janissary", "abus", "spahi", "bombard", "topkapi", "imam", "vizier", "harem", "mosque"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Siege Train Concentration",
    },
    "homecityportuguese": {
        "keywords": ["portuguese", "cassador", "dragoon", "carrack", "feitoria", "henriquan", "organ", "naval"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Naval Mercantile Compound",
    },
    "homecityrussians": {
        "keywords": ["russian", "strelet", "cossack", "oprichnik", "kalmuck", "bashkir", "ataman", "blockhouse", "fishing", "siberian"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Cossack Voisko",
    },
    "homecityspanish": {
        "keywords": ["spanish", "rodelero", "missionary", "lancer", "tercio", "habsburg", "peninsular", "inquisition", "conquistador"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Highland Citadel",
    },
    "homecityswedish": {
        "keywords": ["swed", "carolean", "leather", "torp", "blakulla", "hakkapeliitta", "leatherstocking", "nordic"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Siege Train Concentration",
    },
    "homecityethiopians": {
        "keywords": ["ethiop", "abuna", "lalibela", "axum", "neftenya", "shotelai", "gascenya", "monastery", "shrine", "monk"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Shrine or Trade Node Spread",
    },
    "homecityhausa": {
        "keywords": ["hausa", "lifidi", "fulani", "raider", "palace", "diffa", "sokoto", "kano", "tribute", "marabout"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Distributed Economic Network",
    },
    "homecitychinese": {
        "keywords": ["chinese", "ming", "manchu", "qing", "porcelain", "silk", "kowtow", "rattan", "arquebus", "flaming", "monk", "village", "wonder"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Civic Militia Center",
    },
    "homecityjapanese": {
        "keywords": ["japan", "samurai", "ashigaru", "yumi", "naginata", "shogun", "rice", "tokugawa", "shrine", "daimyo", "consulate"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Shrine or Trade Node Spread",
    },
    "homecityindians": {
        "keywords": ["india", "sepoy", "mahout", "urumi", "rajput", "gurkha", "wonder", "monk", "consulate", "agra"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Distributed Economic Network",
    },
    "homecityitalians": {
        "keywords": ["italian", "bersagl", "elmetto", "papal", "schiavoni", "lombard", "cavour", "garibald", "cathedral", "lampara", "condotta", "pavisier"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Distributed Economic Network",
    },
    "homecitymaltese": {
        "keywords": ["maltese", "malta", "knight", "hospital", "auberge", "commander", "valette", "fortif", "bastion", "cathedral", "balista", "siege", "tongue"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Highland Citadel",
    },
    "homecitymexicans": {
        # Standard Mexican civ (independence-era through reform).
        "keywords": ["mexican", "soldado", "salinero", "insurgent", "cazador", "agave", "hidalgo", "puebla", "guerrero", "fortifiedhacienda"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Civic Militia Center",
    },
    "homecityamericans": {
        "keywords": ["united", "american", "pioneer", "owlhoot", "lawman", "carbine", "gatling", "regular", "minutemen", "frontier", "stagecoach"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Forward Operational Line",
    },
    "homecitydeinca": {
        "keywords": ["inca", "macehua", "runa", "huaminca", "chimu", "bolas", "kancha", "tambo", "kallanka", "andean", "huaca", "huayna"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Andean Terrace Fortress",
    },
    "homecityxpaztec": {
        "keywords": ["aztec", "jaguar", "eagle", "macehualtin", "puma", "skull", "ritual", "calmec", "calendar", "tlaxcal", "zapotec", "chichi"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Jungle Guerrilla Network",
    },
    "homecityxpiroquois": {
        "keywords": ["iroquois", "haud", "tomahawk", "musketrider", "mantlet", "warchief", "kanya", "longhouse", "wampum"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Forward Operational Line",
    },
    "homecityxpsioux": {
        "keywords": ["sioux", "lakota", "dog", "rifle", "axe", "wakina", "pte", "tipi", "tashunke", "tokala", "warchief"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Mobile Frontier Scatter",
    },
}


# Revolution 26 civs ───────────────────────────────────────────────────────
REVOLUTION: dict[str, dict] = {
    "rvltmodhomecitynapoleon": {
        "keywords": ["napoleon", "imperial", "oldguard", "grandbattery", "flyingbattery",
                     "hundreddays", "continental", "sister", "client", "horsehunter",
                     "rustam", "tirail", "cuirass", "balloon", "genie", "bosniak", "mountedrifle",
                     "navalgunner", "centsuisses", "wittelsbach", "frenchroyal", "fencing", "theater"],
        "must_include": ["DEHCREVImperialOldGuard", "DEHCREVNapoleonicWarfare",
                         "DEHCREVHundredDays", "DEHCREVGrandBattery", "DEHCREVFlyingBattery",
                         "DEHCREVHorseHunters", "DEHCREVContinentalBlockade",
                         "DEHCREVRustamsRegiment", "DEHCREVClientStates"],
        "must_exclude": [],
        "buildstyle": "Siege Train Concentration",
    },
    "rvltmodhomecityrevolutionaryfrance": {
        "keywords": ["bastille", "guillotine", "robespierre", "cantinier", "supremebeing",
                     "horsehunter", "client", "revolutionar", "frenchroyal", "tirail",
                     "skirmisher", "musketeer", "general", "officer"],
        "must_include": ["DEHCREVBastilleStorming", "DEHCREVGuillotine", "DEHCREVRobespierre",
                         "DEHCREVCultSupremeBeing", "DEHCREVCantinieres",
                         "DEHCREVShipmentRevolutionaries"],
        "must_exclude": [],
        "buildstyle": "Republican Levee",
    },
    "rvltmodhomecityhaiti": {
        "keywords": ["haiti", "vodou", "sevites", "amazon", "akan", "marque", "picket",
                     "citizenship", "pirate", "privateer", "african", "letter"],
        "must_include": ["DEHCREVVodouCeremonies", "DEHCREVDahomeyAmazonsHaiti",
                         "DEHCREVSevites", "DEHCREVAfricanAllies", "DEHCAkanAllies",
                         "DEHCREVLetterOfMarque", "DEHCREVPickets"],
        "must_exclude": [],
        "buildstyle": "Jungle Guerrilla Network",
    },
    "rvltmodhomecityargentina": {
        "keywords": ["argentina", "argentine", "blandengue", "criollo", "sanmartin",
                     "trattoria", "cattle", "mortar", "pampa", "gaucho", "liberation",
                     "lombardy", "marvelous"],
        "must_include": ["DEHCREVSanMartin", "DEHCREVBlandengues", "DEHCREVCriollos",
                         "DEHCREVCattleDeliveryArgentina", "DEHCLiberationMarch"],
        "must_exclude": [],
        "buildstyle": "Forward Operational Line",
    },
    "rvltmodhomecitybrazil": {
        "keywords": ["brazil", "carioca", "ordenanca", "samba", "bandeirante",
                     "candomble", "ironclad", "amazon", "rainforest"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Distributed Economic Network",
    },
    "rvltmodhomecitychile": {
        "keywords": ["chile", "chilean", "huaso", "pacific", "andes", "ohiggins",
                     "valparaiso", "fronda"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Highland Citadel",
    },
    "rvltmodhomecitycolumbia": {
        "keywords": ["columbia", "colombia", "bolivar", "llanero", "panama", "magdalena", "andean"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Mobile Frontier Scatter",
    },
    "rvltmodhomecitymexicans": {
        "keywords": ["mexican", "soldado", "salinero", "insurgent", "cazador", "agave",
                     "puebla", "hidalgo", "guerrero", "criollo", "alhondiga"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Civic Militia Center",
    },
    "rvltmodhomecitytexas": {
        "keywords": ["texas", "ranger", "lancer", "burnet", "alamo", "sanjacinto",
                     "frontier", "ironclad", "fortwagon", "robberbaron", "empresario",
                     "gonzales", "sharpshooter", "haciendawagon"],
        "must_include": ["DEHCREVMXTexasArmy", "DEHCREVMXTexasLancers", "DEHCREVMXTexasNavy",
                         "DEHCREVMXEmpresarioContracts", "DEHCREVMXGonzalesGuns"],
        "must_exclude": [],
        "buildstyle": "Forward Operational Line",
    },
    "rvltmodhomecitycalifornia": {
        "keywords": ["california", "californio", "frontier", "gold", "ranchero",
                     "vaquero", "missionary", "padre"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Mobile Frontier Scatter",
    },
    "rvltmodhomecitybajacalifornians": {
        "keywords": ["baja", "california", "ranchero", "californio", "gold", "vaquero",
                     "padre", "frontier"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Mobile Frontier Scatter",
    },
    "rvltmodhomecitycentralamericans": {
        "keywords": ["central", "criollo", "panama", "campesino", "guatemala",
                     "nicaragua", "morazan", "filibuster"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Civic Militia Center",
    },
    "rvltmodhomecitymaya": {
        "keywords": ["maya", "yucatan", "jaguar", "calendar", "stelae", "ritual",
                     "milpa", "mayapan", "chichen"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Jungle Guerrilla Network",
    },
    "rvltmodhomecityyucatan": {
        "keywords": ["yucatan", "maya", "campeche", "henequen", "castas", "merida",
                     "guerra", "milpa"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Jungle Guerrilla Network",
    },
    "rvltmodhomecityriogrande": {
        "keywords": ["riogrande", "rio", "ranchero", "frontier", "lancer", "cattle",
                     "vaquero", "norteno", "juarez"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Mobile Frontier Scatter",
    },
    "rvltmodhomecityperu": {
        "keywords": ["peru", "andean", "inca", "huaylas", "tupac", "potosi", "cuzco", "ayacucho"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Andean Terrace Fortress",
    },
    "rvltmodhomecityfrenchcanada": {
        "keywords": ["quebec", "canad", "voyageur", "coureur", "metis", "fur", "habitant",
                     "patriot", "papineau"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Mobile Frontier Scatter",
    },
    "rvltmodhomecitycanada": {
        "keywords": ["canad", "mountie", "voyageur", "metis", "habitant", "lumber",
                     "fur", "redcoat", "loyalist", "doublestack"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Distributed Economic Network",
    },
    "rvltmodhomecityamericans": {
        "keywords": ["american", "united", "pioneer", "minute", "ranger", "carbine",
                     "frontier", "regular", "musketeer", "continental", "washington",
                     "franklin", "gatling"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Republican Levee",
    },
    "rvltmodhomecityfinland": {
        "keywords": ["finland", "finnish", "jaeger", "torp", "sissi", "lake", "sami",
                     "saimaa", "karelian"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Jungle Guerrilla Network",
    },
    "rvltmodhomecityhungary": {
        "keywords": ["hungar", "magyar", "hussar", "pandour", "honved", "hajduk",
                     "kossuth", "frontier"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Steppe Cavalry Wedge",
    },
    "rvltmodhomecityromania": {
        "keywords": ["romania", "carpathian", "calarasi", "vlach", "boyar",
                     "wallachia", "moldavia", "transylvania"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Highland Citadel",
    },
    "rvltmodhomecitysouthafricans": {
        "keywords": ["south", "africa", "boer", "afrikaner", "kommando", "voortrekker",
                     "trek", "zulu", "kimberley"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Mobile Frontier Scatter",
    },
    "rvltmodhomecityegypt": {
        "keywords": ["egypt", "muhammadali", "mameluke", "fellah", "nizami", "pasha",
                     "nile", "alexandria", "cairo", "bedouin"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Republican Levee",
    },
    "rvltmodhomecitybarbary": {
        "keywords": ["barbary", "berber", "corsair", "salerover", "sale", "crabat",
                     "dey", "janissary", "algiers", "tunis", "tripoli"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Naval Mercantile Compound",
    },
    "rvltmodhomecityindonesians": {
        "keywords": ["indon", "java", "sumatra", "aceh", "jong", "kraton", "lantaka",
                     "wokou", "majapahit", "spice", "bali"],
        "must_include": [],
        "must_exclude": [],
        "buildstyle": "Naval Mercantile Compound",
    },
}


def get(civ_id: str) -> dict:
    """Return theme dict for a civ_id (homecity basename), with fall-throughs."""
    if civ_id in STANDARD:
        return {"is_revolution": False, **STANDARD[civ_id]}
    if civ_id in REVOLUTION:
        return {"is_revolution": True, **REVOLUTION[civ_id]}
    raise KeyError(f"no themes registered for {civ_id}")


def all_civs() -> list[str]:
    return list(STANDARD.keys()) + list(REVOLUTION.keys())
