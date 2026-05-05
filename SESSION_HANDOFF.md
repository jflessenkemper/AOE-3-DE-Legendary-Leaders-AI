# Session Handoff — continue on phone via Remote Control

**Last updated:** 2026-04-24
**Origin session ID (desktop, reference only):** `7673ed5b-19c9-4704-b3d6-3a4e62a3bef3`
**Repo:** `jflessenkemper/AOE-3-DE-A-New-World-DLC`
**Branch everything is on:** `claude/hungry-banzai-e122dc` (the active worktree branch; merge / FF to `main` to publish)
**GitHub Pages live URL for the reference site:**
<https://jflessenkemper.github.io/AOE-3-DE-A-New-World-DLC/a_new_world.html>

---

## Latest shipped state

Two earlier commits remain the foundation:

- `bdf83d6` — Historical terrain + heading enforcement for 48 nations (XS layer in `game/ai/aiHeader.xs`, `game/ai/leaders/leaderCommon.xs`, `game/ai/core/aiBuildings.xs`).
- `a695a53` — First-pass Playstyle panel replacing the canonical-map SVG modal.

This session shipped a **v2 Playstyle modal** on top of `a695a53` that:

1. **Absorbed the per-nation `Playstyle:` and `Buildstyle:` subtrees.** All 48 of each were stripped from the HTML; their content now lives inside the modal so each nation card has one canonical place to look. The buildstyle prose became a "How they build" paragraph; the per-age narrative became a 5-card "Strategy by age" section (Discovery / Colonial / Fortress / Industrial / Imperial).
2. **Re-keyed data by `data-name`.** `window.NATION_PROFILES` was retired. The new `window.NATION_PLAYSTYLE` is keyed by each `<details class="nation-node" data-name="…">` attribute, so the renderer does a direct lookup instead of fuzzy name matching. This fixed the two nations that were previously missing a button (United States / Washington and Yucatan / Carrillo Puerto Revolution).
3. **Plain-English bullets.** Every bullet was rewritten to drop internal jargon — no "1.30×", no "level 3/5", no "wall strategy 5". The defense layer now reads as e.g. *"Coastal batteries — moderate stone wall ring · Age-2 perimeter towers · Age-3 forward fort · plants a forward tower on the push axis."*
4. **Modal sections** (in order): pills (terrain / heading / wall / civic flag) → How they build → Strategy by age → Combat doctrine → Military composition → Economy posture → Defensive layer. The raw 20-variable table from the v1 modal was removed — it was internal-facing and not useful for end users.

48/48 `.nation-node` data-names map to a `NATION_PLAYSTYLE` entry. JS validated cleanly via Node `vm`.

---

## Known limitations / not done yet

- **GitHub Pages update delay.** Pages deploys `main` via workflow — allow a couple minutes after push before the live URL shows the new modal.
- **No in-game playtesting yet** of the terrain/heading enforcement. XS compiles cleanly but real-match validation (via the `tools/aoe3_automation/` rig) is pending.
- **`tools/aoe3_automation/*.py` scripts** (13 files: `afk_driver*.py`, `civ_matrix_*.py`, `wall_verify.py`, etc.) are **untracked** — left out of the mod commits intentionally. Add separately if/when you want them versioned.
- **Not touched this session:** achievements, scenario scripts, anything outside the AI / presentation layer.

---

## Key files to know

| Area | Path |
|---|---|
| Terrain/heading constants | `game/ai/aiHeader.xs` |
| Per-nation wiring | `game/ai/leaders/leaderCommon.xs` → `llApplyBuildStyleForActiveCiv()` |
| Placement math | `game/ai/core/aiBuildings.xs` → `llGetTerrainFeatureVector`, `llGetHeadingFeatureVector`, `llGetPlacementBiasedCenter`, `llApplyLegendaryBaseInfluence`, `selectTCBuildPlanPosition` |
| Reference site | `a_new_world.html` (modal block marked `<!-- PLAYSTYLE-MODAL-START -->` / `<!-- PLAYSTYLE-MODAL-END -->`) |
| Playstyle data | inside modal block — `window.NATION_PLAYSTYLE` literal, keyed by `data-name` |
| Historical guide | `docs/design/map-placement-historical-guide.md` |
| Terrain system doc | `docs/design/terrain-character-system.md` |
| Variable inventory | `docs/design/ai-knob-inventory.md` |

---

## How to continue on phone

You're in a fresh Remote Control session. Paste this as your first message:

> Read `SESSION_HANDOFF.md` and `docs/design/terrain-character-system.md` at the repo root. We just shipped the v2 Playstyle modal to `main`. I want to [YOUR NEXT TASK HERE].

Good next-task candidates:
- Tweak a specific nation's terrain bias strength and verify the modal preview updates
- Add a new terrain primitive (e.g. `cLLTerrainTundra`) and wire it for Swedes/Finns
- Playtest via `tools/aoe3_automation/` and capture a build-order replay
- Polish a specific nation's bullets / age narrative in `window.NATION_PLAYSTYLE`
- Add missing docs for a specific nation in `map-placement-historical-guide.md`

---

*This file is itself committed to the repo so any fresh Claude Code session in this worktree can read it.*
