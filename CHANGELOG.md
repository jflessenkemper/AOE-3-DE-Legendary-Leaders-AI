# Changelog

All notable changes to **AOE 3 DE - A New World** are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-05-01

First public release. The mod is now `status: release` and has been verified
end-to-end through the in-engine automated test harness — every one of the 48
selectable civilizations was loaded into a real Skirmish match, the AI script
was confirmed to start under each leader's personality, and the harness
captured a clean resign on every match.

### Added
- **48 selectable civilizations** in the lobby picker — 22 base civs + 26
  revolutions promoted to top-level pickable nations.
- **Per-leader AI doctrine** (`game/ai/leaders/*.xs`) — distinct build orders,
  military comp, and explorer-escort posture per nation.
- **Leader-escort doctrine** — AI treats its explorer as the battlefield
  leader with a living screen of units around them.
- **Smart rout** — only AI non-elite land units rout (≤25% HP, no friendly
  elite nearby); elites and player-controlled units never auto-rout.
- **Historical map placement** — every civ pinned to a terrain bias and
  expansion heading via `cBuildPlanCenterPosition` (real coordinates, not
  just labels).
- **Curated 25-card deck per civ** matched to leader playstyle.
- **Lobby-matched leader portraits, names, and chat quotes** — consistent
  from lobby thumbnail through scoreboard.
- **Revolutions disabled on base civs** — the 26 revolution nations are
  already top-level picks, so age-up doesn't offer the old options.
- **Reference site** at <https://jflessenkemper.github.io/AOE-3-DE-A-New-World-DLC/>
  with per-civ playstyle panels.

### Test harness
- **Matrix runner** (`tools/aoe3_automation/matrix_runner.py`) — drives the
  in-engine lobby, plays Skirmish matches batched 8-civs-per-match, captures
  personality probes from every AI, and writes per-civ coverage reports.
- **`--auto-resign-ms` flag** — rewrites `cLLTestModeAutoResignMs` in
  `game/ai/core/aiGlobals.xs` so every AI calls `aiResign()` after a fixed
  game-time threshold, bounding match length for fast deterministic coverage
  runs (~5 min per 8-civ batch). Always reset to `0` on exit so release
  builds never carry test instrumentation.
- **Biome → civ map** (`tools/aoe3_automation/biome_to_civ_map.json`) —
  routes each civ to an official AoE3 DE map that exercises its environmental
  preference (temperate / arid / tropical / arctic / subtropical / andean /
  mediterranean) using stock RMS scripts (no custom map authoring required).

### Release verification — 2026-05-01
- 48/48 picker civs loaded a Skirmish match successfully
- 48/48 AI personality probes fired in `postInit()`
- ~110 AI scripts loaded per match (full leader doctrine + opponents)
- 0 engine errors across all match logs
- Auto-resign verified to fire and harness captured clean resigns

[1.0.0]: https://github.com/jflessenkemper/AOE-3-DE-A-New-World-DLC/releases/tag/v1.0.0
