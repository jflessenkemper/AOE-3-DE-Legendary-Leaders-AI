# Playtest spot-check harness

The static validators under `tools/validation/` prove the mod's data is
*internally consistent*. They can't tell you whether the AI actually
builds along the coast as British, or pushes the frontier as Napoleon.
This package — `tools/playtest/` — is the runtime layer.

It has two halves. Both work without driving the game; you supply the
inputs (a checklist for your eyes, screenshots for the verifier).

## TL;DR

```sh
# Print the per-civ ground truth — leader, deck, terrain, heading.
# Keep this on a second monitor while you play.
tools/test.sh --preflight

# After playing, drop screenshots into a folder and run:
tools/test.sh --layout-spot-check ~/aoe3-shots/ --team blue
```

## Layer 1 — preflight ground truth

`tools/test.sh --preflight` (or `python3 -m tools.playtest.preflight`)
prints a compact table derived from the same files the static
validators read (`game/ai/leaders/leaderCommon.xs`, `data/civmods.xml`,
`data/*homecity*.xml`):

| column | source | what to check in-game |
|---|---|---|
| `Leader` | `gLLLeaderKey = "<key>"` in `leaderCommon.xs` | lobby thumbnail + match scoreboard portrait + chat name |
| `Deck` | first `<deck>/<name>` in the homecity XML | label shown over the deck in the in-game Deck Builder |
| `Terrain (str)` | `llSetPreferredTerrain(...)` arguments | direction the AI's building cluster grows (toward water vs inland) |
| `Heading (str)` | `llSetExpansionHeading(...)` arguments | secondary TC / forward-tower placement |
| `Bias` | derived: water/inland + tangent/outward/inward | one-line spot-check answer |

Useful flags:

- `--civ British` → expand into a checklist for one civ (with
  per-row checkboxes ready to tick off).
- `--revolutions` / `--base` → narrow to one half of the roster.
- `--markdown` → emit the table for pasting into a doc.

## Layer 2 — screenshot spot-check

`tools/test.sh --layout-spot-check DIR` walks a folder of full-screen
PNGs (one per civ) and reports per-civ PASS / FAIL / INCONCLUSIVE.

### How it works

1. Each screenshot is matched to a civ by filename stem
   (`british.png`, `napoleon.png`, `british_8min.png` are all valid;
   trailing `_NNN`, `_NNNmin`, `_NNNsec` suffixes are stripped before
   matching).
2. The minimap region (default = a 290×290 rect at the bottom-left of
   a 1080p frame) is cropped from each shot.
3. Pillow scans every minimap pixel and HSV-classifies it as
   `player` (your team color), `water` (medium-blue, low-sat) or
   `land`.
4. We compute the **bearing** of the player-color centroid and the
   water-vector centroid relative to the minimap center (which is
   approximately your starting TC).
5. We compare that bearing-delta to the civ's expected `water_bias`:
    - **toward-water civs** (Coast/River/Wetland primary) PASS when
      the delta is ≤ 60° (default `--water-tol`).
    - **inland civs** (Highland/DesertOasis primary) PASS when the
      delta is ≥ 120° (default `--inland-tol`).
    - **neutral civs** (Plain/Forest/Jungle primary) are reported but
      not graded.

### Running it

```sh
# 1080p, you're team blue (default). Report to .validation-reports/.
tools/test.sh --layout-spot-check ~/shots/ \
    --team blue \
    --report .validation-reports/playtest.txt

# Different resolution → pass an explicit minimap rect.
python3 -m tools.playtest.spot_check ~/shots/ \
    --minimap 32,1010,418,1396 \
    --team red

# Verify a single civ from a single screenshot.
python3 -m tools.playtest.layout_verify \
    --civ "Napoleonic France" \
    --screenshot ~/shots/napoleon_8min.png \
    --team blue
```

### When to take the screenshot

Take the shot **after** the AI has placed at least its TC, market,
4–5 houses, and a barracks/stable. That's typically 4–8 minutes into
a Skirmish, depending on the civ's age-up speed. Earlier than that
and the centroid is noisy; later than that and military placement
starts to dominate over civic placement.

A fixed-seed map and the same opponent civ each time make the per-civ
results comparable across runs.

### Failure modes the harness catches

- **Wrong leader portrait wired** — caught by preflight, not by
  screenshots.
- **Wrong deck name in Deck Builder** — caught by preflight (we read
  the homecity file directly).
- **AI placing buildings against its declared bias** — caught by
  layout spot-check. Example: a Highland civ whose buildings cluster
  on the coastline → FAIL: "expected inland bias but Δ 23° < 120°".

### Failure modes the harness doesn't catch (yet)

- Build-order pacing (does British actually rush age 2 by 4 min?).
- Card pick order during shipments.
- Combat micro and leader-escort behaviour under fire.

These belong to the older `tools/aoe3_automation/` rig (replay/observer
flows, not committed). The two layers compose: preflight + screenshot
spot-check covers data + topology; the full observer rig covers
sequencing + combat.

## Calibrating the minimap rect

For a non-1080p screen, take one full-screen screenshot at the start
of a match (so the minimap shows just the dark canvas). Open it in any
image editor with a coordinate readout, find the minimap's outer
bounding box, and pass `--minimap LEFT,TOP,RIGHT,BOTTOM`. The default
`(24, 760, 314, 1050)` is correct for 1920×1080 with default UI scale.

## Adding more checks

The harness is a thin Python package; extending it is straightforward.

- New per-civ check based on screenshot data → extend
  `tools/playtest/layout_verify.py::verify()`. Pull whatever you need
  from the `MinimapReading` and the `CivExpectation`. Add a unit test
  in `tests/playtest/test_minimap.py` that synthesizes a minimap with
  a known layout and asserts the verdict.
- New per-civ ground-truth column → add it to the `CivExpectation`
  dataclass in `tools/playtest/expectations.py`, populate it in
  `load_expectations()`, render it in `preflight.py::_print_table()`.

The unit tests in `tests/playtest/` synthesize tiny PNGs in a
temporary directory, so they're CI-portable — no game install needed.
