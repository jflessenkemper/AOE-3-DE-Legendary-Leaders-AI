# Session Handoff — continue on phone via Remote Control

**Last updated:** 2026-04-24
**Origin session ID (desktop, reference only):** `7673ed5b-19c9-4704-b3d6-3a4e62a3bef3`
**Repo:** `jflessenkemper/AOE-3-DE-Legendary-Leaders-AI`
**Branch everything is on:** `main`
**GitHub Pages live URL for the reference site:**
<https://jflessenkemper.github.io/AOE-3-DE-Legendary-Leaders-AI/LEGENDARY_LEADERS_TREE.html>

---

## What just shipped (commit `bdf83d6` on `main`)

**Historical terrain + heading enforcement for 48 nations.** Not cosmetic — the AI actually obeys it when placing buildings.

1. **XS enforcement layer** — `game/ai/aiHeader.xs`, `game/ai/leaders/leaderCommon.xs`, `game/ai/core/aiBuildings.xs`
   - 9 terrain primitives: `Any / Coast / River / ForestEdge / Plain / Highland / Wetland / DesertOasis / Jungle`
   - 8 expansion headings: `Any / AlongCoast / Upriver / FrontierPush / IslandHop / OutwardRings / FollowTradeRoute / Defensive`
   - Per-nation strength knobs: `gLLTerrainBiasStrength`, `gLLHeadingBiasStrength`
   - Center-anchored civic flag tightens influence clamp ~0.65× for non-military/non-house/non-TC plans
   - All 48 civs wired in `llApplyBuildStyleForActiveCiv()` — British Coast/AlongCoast, Russians River/Upriver, Lakota Plain/FrontierPush, Maltese Highland/Defensive, Napoleonic France Plain/FrontierPush, etc.
   - Water-adjacent terrains bias toward `gNavyVec`; land terrains toward baseLocation; `Upriver` reflects water vector across base; frontier headings bias toward `gForwardBaseLocation`
   - TC placement (`selectTCBuildPlanPosition`) blends mine-anchored TC toward heading before committing `gTCSearchVector`

2. **Playstyle panel** — `LEGENDARY_LEADERS_TREE.html` (replaced the earlier "Map Placement" SVG modal)
   - Per-nation "Playstyle" button opens a 760px textual modal
   - 6 sections: Terrain & expansion, Build tempo, Combat doctrine, Military composition, Economy posture, Defensive layer
   - Bullets generated deterministically from `window.NATION_PROFILES` (same data structure as before)
   - Toggle button below sections expands a raw 20-variable table
   - All markers in HTML are now `PLAYSTYLE-MODAL-START` / `PLAYSTYLE-MODAL-END`
   - The earlier canonical 600×600 SVG map was scrapped — it looked impressive but the abstraction was misleading and the textual panel carries the actual signal

3. **Rebrand to "AOE 3 DE - A New World DLC"** across README, modinfo, stringtables, playercolors, nation reference

4. **Lobby-matched leader portraits**: Queen Elizabeth I (British), Ivan the Terrible (Russians), Chief Gall (Lakota), Louis XVIII (base French), Napoleon (Napoleonic France). New avatar PNGs under `resources/images/icons/singleplayer/`.

5. **Design docs** in `docs/design/`:
   - `map-placement-historical-guide.md` — per-nation historical rationale for terrain/heading picks (48 nations)
   - `terrain-character-system.md` — design of the 9-terrain / 8-heading model
   - `ai-knob-inventory.md` — 20-variable tuning inventory driving the diagram

6. **README** has a new "🗺️ Historical Map Placement" section documenting all of the above.

---

## Known limitations / not done yet

- **GitHub Pages update delay.** Pages deploys `main` via workflow — allow a couple minutes after the last push (commit `bdf83d6`) before the live URL shows the new modal.
- **No in-game playtesting yet** of the terrain/heading enforcement. XS compiles cleanly but real-match validation (via the `tools/aoe3_automation/` rig) is pending.
- **`tools/aoe3_automation/*.py` scripts** (13 files: `afk_driver*.py`, `civ_matrix_*.py`, `wall_verify.py`, etc.) are **untracked** — left out of commit `bdf83d6` intentionally, not part of the mod proper. Add them separately if/when you want them versioned.
- **Not touched this session:** achievements, scenario scripts, anything outside the AI/presentation layer.

---

## Key files to know

| Area | Path |
|---|---|
| Terrain/heading constants | `game/ai/aiHeader.xs` |
| Per-nation wiring | `game/ai/leaders/leaderCommon.xs` → `llApplyBuildStyleForActiveCiv()` |
| Placement math | `game/ai/core/aiBuildings.xs` → `llGetTerrainFeatureVector`, `llGetHeadingFeatureVector`, `llGetPlacementBiasedCenter`, `llApplyLegendaryBaseInfluence`, `selectTCBuildPlanPosition` |
| Reference site | `LEGENDARY_LEADERS_TREE.html` (modal block marked `<!-- MAP-PLACEMENT-MODAL-START -->`) |
| Historical guide | `docs/design/map-placement-historical-guide.md` |
| Terrain system doc | `docs/design/terrain-character-system.md` |
| Variable inventory | `docs/design/ai-knob-inventory.md` |

---

## How to continue on phone

You're in a fresh Remote Control session. Paste this as your first message:

> Read `SESSION_HANDOFF.md` and `docs/design/terrain-character-system.md` at the repo root. We just shipped commit `bdf83d6` to `main`. I want to [YOUR NEXT TASK HERE].

Good next-task candidates:
- Tweak a specific nation's terrain bias strength and verify the modal preview updates
- Add a new terrain primitive (e.g. `cLLTerrainTundra`) and wire it for Swedes/Finns
- Playtest via `tools/aoe3_automation/` and capture a build-order replay
- Fix something you spotted in the modal UI
- Add missing docs for a specific nation in `map-placement-historical-guide.md`

---

*This file is itself committed to the repo so any fresh Claude Code session in this worktree can read it.*
