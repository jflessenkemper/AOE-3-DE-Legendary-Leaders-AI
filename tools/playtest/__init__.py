"""In-engine spot-check harness for A New World.

The static validators under `tools/validation/` prove the data is
internally consistent. This package proves it actually plays correctly:

  * `expectations` — extracts per-civ ground truth (terrain, heading,
    leader, deck) from the source files so we have a single answer key.
  * `preflight` — prints a human-readable rundown to keep next to the
    keyboard while playing.
  * `minimap` — image processing: read a full-screen screenshot, locate
    the minimap region, segment building dots from water/land tiles.
  * `layout_verify` — composes the above: given (civ, screenshot),
    return PASS/FAIL with reasoning ("centroid bears 240° from TC,
    water bears 235°, terrain=Coast → consistent").
  * `spot_check` — orchestrator that walks a folder of `<civ>.png`
    screenshots and reports a per-civ verdict matrix.

The package is import-light — Pillow is the only third-party dep, and
even that is only required for the screenshot-side modules.
"""
