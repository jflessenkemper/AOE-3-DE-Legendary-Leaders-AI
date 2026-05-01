# Changelog

All notable changes to **AOE 3 DE — A New World DLC** are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

Tracking the v1.0.0 release. v1.0.0 is gated on the AI actually *playing
well* — i.e. behaving the way each civ's
[reference-site Playstyle panel](https://jflessenkemper.github.io/AOE-3-DE-A-New-World-DLC/)
describes — not just loading.

### Added since 0.9.0-rc1

- **Per-civ doctrine validation pipeline.** Closes the rc1 release-blocker
  ("playstyle fidelity not yet validated"). New tooling cross-checks the
  runtime AI against the HTML reference's per-civ doctrine claims:
  - `tools/playtest/extract_playstyle_spec.py` parses
    `LEGENDARY_LEADERS_TREE.html` into `playstyle_spec.json` (46 civs ×
    15 canonical doctrines, with claim bundles: wall-strategy,
    first-military-building, dock/barracks/wall time budgets, naval/
    forward/treaty/cavalry/infantry/artillery flags, military-distance
    band).
  - `game/ai/core/aiDoctrineProbes.xs` emits 8 `milestone.first_*` probes
    (dock/barracks/stable/wall_segment/fort/trading_post/artillery/
    forward_base) plus rolling `comp.snapshot` and `posture.snapshot`
    every 60s of game time. Gated on `cLLReplayProbes` so release builds
    skip everything in one branch.
  - `tools/validation/validate_doctrine_compliance.py` reads
    `match.log` probe streams and produces a PASS/FAIL/UNKNOWN ledger
    per civ, including HTML-deck card-name compliance.
  - `tools/validation/validate_leader_vs_spec.py` is a static linter:
    parses each `game/ai/leaders/leader_*.xs` for its `llUse*Style()`
    pick + direct `gLLWallStrategy` / `gLLMilitaryDistanceMultiplier`
    overrides and verifies they satisfy the spec without needing an
    engine run. **20/20 leaders pass.**
  - `tools/validation/compile_playtest_report.py` and the matrix
    runner's new `--validate-doctrine` flag stitch all of the above
    into a single `playtest_report.txt` per matrix run (per-civ
    section + doctrine ledger + MM:SS timeline + cards summary + top
    regressions).

### Fixed since 0.9.0-rc1

- **Wall-strategy off-by-one in `tools/playtest/html_reference.py`.** The
  `WALL_*` constants used 1–6 instead of 0–5 (per `aiHeader.xs:202-207`
  `cLLWallStrategy*`), so every wall-strategy assertion in
  `tools/playtest/replay_probes.py:684` silently disagreed with what the
  runtime emits via `gLLWallStrategy`. Fixed both the constants and the
  self-test int→name table.
- **Runtime/spec leader-key bridge for British/Russian/Lakota/Maltese/
  Hausa.** Engine personality slugs (`wellington`, `catherine`,
  `crazyhorse`, `jean`, `usman`) differ from the spec leader slugs
  (`elizabeth`, `ivan`, `gall`, `valette`, `muhammadu`). Without the
  bridge the doctrine validator and card-deck lookup silently failed
  for every match those civs played. Bridge added to both
  `validate_doctrine_compliance.py` and `validate_leader_vs_spec.py`.
- **Three leader files picked the wrong style helper for their
  HTML-declared doctrine.** Surfaced by the new static linter:
  `leader_frederick.xs` swapped `llUseSiegeTrainConcentrationStyle` →
  `llUseRepublicanLeveeStyle` (Republican Levee per spec);
  `leader_gustavus.xs` swapped to `llUseForwardOperationalLineStyle`
  (Forward Operational Line per spec);
  `leader_shivaji.xs` swapped `llUseShrineTradeNodeSpreadStyle` →
  `llUseHighlandCitadelStyle` (Highland Citadel per spec, Maratha
  hill-fort network).

### Fixed since 0.9.0-rc1 (pre-doctrine-pipeline)

- **Wall gap-fill now proactive instead of fallback.** `fillInWallGapsNew`
  previously skipped whenever the main ring plan was alive, which let
  ring plans complete with visible gaps (engine refuses to drop a piece
  on terrain conflicts) and never re-trigger fill. Now samples the
  outer ring at 16 points per tick, computes coverage, and lays a
  parallel inner-ring (radius − 5) plan at priority 78 whenever
  coverage drops below 75%. Coexists with the main ring (both are ring
  plans but distinct radii). Interval tightened 51s → 25s. New
  `wall.coverage` and `plan.wall.gapfill` probes for replay validation.
  MobileNoWalls doctrines (Napoleon, Crazy Horse, Hiawatha, Montezuma,
  Usman) still opt out cleanly. (`game/ai/core/aiBuildingsWalls.xs:516`)
- **Military buildings spread along heading axis (no more TC clump).**
  `selectBuildPlanPosition` previously called
  `llApplyLegendaryBaseInfluence` with the default 30u centerDistance /
  100u influenceDistance for *every* default-case building, including
  Barracks/Stable/Artillery Depot/War Hut/Embassy/etc. — so the
  per-civ heading bias (already computed in
  `llGetPlacementBiasedCenter`) only nudged a tiny anchor and the
  buildings effectively stacked on the TC. Bumped the military-building
  defaults to 55/140/240 so the placement gradient walks outward along
  the (heading-biased) anchor. Per-doctrine
  `gLLMilitaryDistanceMultiplier` (0.7–1.3) still scales this.
  (`game/ai/core/aiBuildings.xs:1599`)
- **Military building spam capped by age.** The mil-building demand
  formula in `buildingMonitor` previously chained engine build-limit and
  `villagers/20` ceilings only, which by Age 4–5 sized each family
  (Barracks / Stable / Artillery Depot / War Hut / Embassy / etc.) at
  4–6 buildings — clumping 15–25 mil-buildings around the main base.
  Added a per-age per-family cap on top: 1/2/3/4/6 across Ages 1–5
  (+2 during active treaty). (`game/ai/core/aiBuildings.xs:3121`)
- **Hero recovery rewritten.** Ransom is now queued unconditionally when a
  Town Center exists, with `cResearchPlanResourcePriority=95` so the
  resource manager escrows gold up to the ransom cost instead of giving
  up when short. When no TC exists, the field-rescue path is a real
  `cPlanCombat` attack-at-point with 4–8 generic land military
  (`cUnitTypeLogicalTypeLandMilitary`) targeting the fallen explorer's
  location — replacing the prior single-scout `cPlanExplore` rescue that
  died on arrival. Removed the `kbUnitGetHealth < 0.3` early-abort.
  (`game/ai/core/aiMilitary.xs:208`)

### Known release-blocking AI bugs (caught by 0.9.0-rc1 playtest)

- **Per-civ playstyle fidelity not yet validated.** All four cross-cutting
  AI bugs from the rc1 playtest are now fixed in code, but the AI's
  actual behaviour has not been re-validated against the per-civ
  doctrine prose at
  [reference-site Playstyle panels](https://jflessenkemper.github.io/AOE-3-DE-A-New-World-DLC/).
  `tools/playtest/html_reference.py` parses 45 of 46 nation-nodes today;
  the matrix runner uses it for wall-strategy assertions but not for
  the richer doctrine claims (docks-first, citadel-only, line-infantry
  mass, mercenary-heavy, etc.). v1.0.0 ships once the matrix harness
  cross-checks all 48 civs against their reference-site descriptions
  with a green report.

## [0.9.0-rc1] — 2026-05-01

Release candidate. The 48-civ roster is complete and the AI loads + runs
under every leader, but per-civ playstyle fidelity vs. the reference site
is unverified and the four bugs above were caught in playtest.

### Added
- **48 selectable civilizations** in the lobby picker — 22 base civs + 26
  revolutions promoted to top-level pickable nations.
- **Per-leader AI doctrine** (`game/ai/leaders/*.xs`) — distinct build
  orders, military comp, and explorer-escort posture per nation.
- **Leader-escort doctrine** — AI treats its explorer as the battlefield
  leader with a living screen of units around them.
- **Smart rout** — only AI non-elite land units rout (≤25% HP, no
  friendly elite nearby); elites and player-controlled units never
  auto-rout.
- **Historical map placement scaffolding** — every civ pinned to a
  terrain bias and expansion heading via `cBuildPlanCenterPosition`
  (real coordinates, not just labels). NOTE: actual offset wiring per
  heading is unverified — see Known issues above.
- **Curated 25-card deck per civ** matched to leader playstyle.
- **Lobby-matched leader portraits, names, and chat quotes** — consistent
  from lobby thumbnail through scoreboard.
- **Revolutions disabled on base civs** — the 26 revolution nations are
  already top-level picks, so age-up doesn't offer the old options.
- **Reference site** at <https://jflessenkemper.github.io/AOE-3-DE-A-New-World-DLC/>
  with per-civ playstyle panels.

### Test harness
- **Matrix runner** (`tools/aoe3_automation/matrix_runner.py`) — drives
  the in-engine lobby, plays Skirmish matches batched 8-civs-per-match,
  captures personality probes from every AI, writes per-civ coverage
  reports.
- **`--auto-resign-ms` flag** — rewrites `cLLTestModeAutoResignMs` in
  `game/ai/core/aiGlobals.xs` so every AI calls `aiResign()` after a
  fixed game-time threshold. Always reset to `0` on exit.
- **Biome → civ map** (`tools/aoe3_automation/biome_to_civ_map.json`) —
  routes each civ to an official AoE3 DE map that exercises its
  environmental preference.
- **`tools/validators/civ_asset_audit.py`** — comprehensive asset audit
  catching the bug class that produced the "pirate flag on Town Center"
  issue: malformed portrait paths, unresolved `nameID`s, missing
  personality icons, flag-style mismatches.

### Fixed in 0.9.0-rc1
- `RvltModRevolutionaryFrance` Town Center pirate-flag fallback —
  `civmods.xml:276` had `objects\flags/french` (mixed slash). Engine
  couldn't resolve and rendered the default placeholder. Fixed to
  `objects\flags\french`. Validator wired into CI to prevent regression.

### Verification (covers loading only — NOT play quality)
- 48/48 picker civs successfully loaded a Skirmish match
- 48/48 AI personality probes fired in `postInit()`
- ~110 AI scripts loaded per match
- 0 engine errors across all match logs
- One unbounded 32-min Britain match completed without crash

[Unreleased]: https://github.com/jflessenkemper/AOE-3-DE-A-New-World-DLC/compare/v0.9.0-rc1...HEAD
[0.9.0-rc1]: https://github.com/jflessenkemper/AOE-3-DE-A-New-World-DLC/releases/tag/v0.9.0-rc1
