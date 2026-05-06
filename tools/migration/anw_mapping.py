"""Phase 6 canonical mappings for unified 48-ANW validator path.

Single source of truth for validators and tools that need to:
- Iterate all 48 ANW civs uniformly
- Map ANW stems ↔ homecity filenames
- Identify deferred civs (those without HTML sections)

Replaces fragmented dicts like CIV_TO_HOMECITY, _BASE_CIV_HOMECITY, CIV_FILES.
"""

from tools.migration.anw_token_map import ANW_CIVS


# All 48 ANW civs in canonical order (22 base + 26 rev), indexed by anw_stem
ANW_CIVS_BY_STEM = {c.anw_stem: c for c in ANW_CIVS}

# Homecity filename map: anw_stem → anwhomecity{stem}.xml (post-migration filename)
ANW_HOMECITY_MAP = {
    c.anw_stem: c.new_homecity_filename
    for c in ANW_CIVS
}

# All 48 ANW tokens in canonical order
ANW_ALL_TOKENS = [c.anw_token for c in ANW_CIVS]

# All 48 ANW stems in canonical order
ANW_ALL_STEMS = [c.anw_stem for c in ANW_CIVS]

# Slug → AnwCiv lookup for HTML-based validators
ANW_CIVS_BY_SLUG = {c.slug: c for c in ANW_CIVS}

# Slugs of civs deferred from HTML (no nation-node in a_new_world.html)
# These civs ARE first-class in civmods + personalities + decks; they just
# lack HTML sections (see MOD_HISTORY.md). Validators exclude them from
# expected-section validation but process them in all other contexts.
ANW_DEFERRED_SLUGS = {"Americans", "Mexicans (Revolution)"}
