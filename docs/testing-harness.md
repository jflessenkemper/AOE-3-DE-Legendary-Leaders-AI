# Testing harness

This mod ships with a layered testing harness. Everything below is
runnable locally — the same checks run in CI, but you don't have to
push to find out what broke.

## TL;DR

```sh
# fast smoke test (skips packaged-mod stage)
tools/test.sh --no-packaged

# full local sweep — what CI runs
tools/test.sh

# write a transcript of the run for later review
tools/test.sh --report .validation-reports/local.txt
```

If the script exits 0, every static / data-side check the mod has is
green. The final block prints a small inventory (civ counts, leader XS
files, validators, workflows) so you can sanity-check the surface area.

## What the harness covers

There are three layers:

### 1. Static / data-side checks (no game running)

`python -m tools.validation.run_staged_validation --stage content` runs
every validator under `tools/validation/`:

| Check | What it verifies |
|---|---|
| Civ Crossrefs | Every civ in `civmods.xml` has a leader XS file, leader portrait, and matching homecity binding. |
| Civ HomeCities | Every `<HomeCityFilename>` in `civmods.xml` resolves to a real `data/*.xml` and the inner `<civ>` matches. |
| HomeCity Cards | Every `<card>` inside a homecity references a real card name and is well-formed. |
| HomeCity Visuals | Every home-city XML (48 total) keeps `<visual>` / `<watervisual>` / `<backgroundvisual>` / `<pathdata>` / `<camera>` / `<widescreencamera>` in the same art namespace. Regression guard for the "floating citizens" bug — a pathdata namespace mismatch makes units snap to the wrong heightmap. |
| Civ UI | `civmods.xml` UI fields (icon, banner, deck) point at files that exist. |
| Proto | `protomods.xml` overrides reference real protounits. |
| StringTables | Every `$$NNNN$$` reference in the mod resolves either to a base-game ID or to one defined in `stringmods.xml`. |
| TechTree | Tech IDs referenced from cards / protomods exist. |
| XML Well-Formedness | Every `*.xml` / `*.tactics` / `*.material` / `*.dmg` in the repo parses. |
| XS | Every `*.xs` script uses only the documented stock AoE3 XS surface (allowlist-based). |
| Terrain/Heading Wiring | Every of the 48 civs has a branch in `llApplyBuildStyleForActiveCiv()` that calls `llSetPreferredTerrain` + `llSetExpansionHeading` with valid constants and in-range strengths. |
| Playstyle Modal | Every `.nation-node[data-name]` in `a_new_world.html` has a `window.NATION_PLAYSTYLE` entry with all required base-doctrine and **imperial-peer doctrine** fields populated (each civ now carries an `imperialPsTitle` + `imperialAges{Discovery..Imperial}` + imperial bullet sets, anchored on its historical leader from `data/playercolors.xml`). No internal jargon (multipliers, level n/N, raw `gLL*` / `cLL*` constants) may leak into end-user prose. |
| Player Colors | `data/playercolors.xml` is well-formed, has unique civ + leader entries with valid 0..255 RGB channels, and binds every revolution civ declared in `civmods.xml`. |

### 2. Validator regression tests (Python unittest)

`python -m unittest discover -s tests/validation` runs the validator
unit tests — fixtures + assertions that prove each validator catches
the specific failures it claims to catch. If a future change to a
validator stops detecting a real bug, this layer fails.

### 3. Packaged-mod validation

`python tools/validation/validate_packaged_mod.py` zips the mod the
same way the Steam Workshop publish path would and re-runs the static
checks against the packaged tree. Slowest stage; skip with
`--no-packaged` for fast iteration.

## What the harness does **not** cover

Full in-engine playtesting (build-order pacing, card pick order, combat
micro). The `tools/aoe3_automation/` folder (intentionally not
committed — see `SESSION_HANDOFF.md`) drives the real game via UI
automation: `np_wel_1v1_observer.py`, `civ_matrix_*.py`,
`wall_verify.py`, etc. Those rely on a running AoE3 DE install, RDP,
and Proton.

**However**, two complementary checks now ship with the repo:

- `tools/test.sh --preflight` prints a per-civ ground-truth table
  (leader, deck, terrain, heading, derived bias) so you have an
  answer key while playing.
- `tools/test.sh --layout-spot-check DIR` walks a folder of in-game
  screenshots, segments the minimap, and verifies that each civ's
  building cluster lands on the side of the map its declared
  `cLLTerrain*` bias says it should.

See [`playtest-harness.md`](playtest-harness.md) for the full flow.

When you have the rig connected, run:

```sh
python tools/aoe3_automation/civ_matrix_driver_v2.py
python tools/aoe3_automation/wall_verify.py
```

Their reports go under `.claude/session_*-artifacts/`.

## Adding a new check

1. Write a validator: `tools/validation/validate_<thing>.py` that
   exposes `validate_<thing>(repo_root: Path) -> list[str]` (returning
   a list of human-readable issues; empty = pass) and a `main()` for
   CLI use.
2. Wire it into `tools/validation/run_staged_validation.py` ↦
   `build_content_checks(...)`.
3. Write unit tests: `tests/validation/test_validate_<thing>.py` —
   create a temp repo with `tempfile.TemporaryDirectory()` and assert
   both the green and red paths.
4. Add the validator to `.github/workflows/validation-suite.yml`. If
   the check is small and isolated, also create a focused workflow
   (see `terrain-heading-validation.yml` /
   `playstyle-modal-validation.yml` for the pattern).
5. `tools/test.sh --no-packaged` should pass before you commit.

## Workflow inventory

| Workflow | What it runs |
|---|---|
| `validation-suite.yml` | Full content sweep + packaged validation. Everything. |
| `validator-tests.yml` | Just the unittest suite. |
| `package-validation.yml` | Just the packaged-mod validator. |
| `civ-homecity-validation.yml` | Just the homecity binding check. |
| `civ-crossref-validation.yml` | Just the cross-reference check. |
| `xml-malformation-check.yml` | Just XML well-formedness. |
| `stringtable-validation.yml` | Just stringtable references. |
| `proto-validation.yml` | Just proto overrides. |
| `techtree-validation.yml` | Just techtree references. |
| `xs-validation.yml` | Just XS surface allowlist. |
| `homecity-card-validation.yml` | Just card definitions inside homecities. |
| `civmods-ui-validation.yml` | Just the civmods UI asset check. |
| `terrain-heading-validation.yml` | Just the terrain/heading wiring check (new). |
| `playstyle-modal-validation.yml` | Just the v2 playstyle modal check (new). |
| `pages-deploy.yml` | Deploys `a_new_world.html` + reference site to GitHub Pages from `main`. |
