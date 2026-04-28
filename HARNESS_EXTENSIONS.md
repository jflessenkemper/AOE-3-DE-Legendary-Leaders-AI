# Harness Extensions — coverage_v2 + 48-civ Matrix Runner

_Branch: claude/hungry-banzai-e122dc_

---

## What was added

### 1. XS probe emitters (game AI)

| File | Change |
|------|--------|
| `game/ai/core/aiCore.xs` | Added `event.age_up` probe (emits `age=<n> t=<ms>`) immediately before the existing `econ.aged` probe, fired when this AI finishes aging up. |
| `game/ai/core/aiEliteTactics.xs` | Added `mil.escort_check` probe inside `legendaryEliteGuardMonitor` (fires every 5 s during an active attack plan). Records `attack_active=1 leader_dist=<m> explorerID=<id> attackPlan=<id>`. |

Existing probes used by the new validators:
- `tech.ship` (`aiHCCards.xs`) — card index, tech ID, age at time of shipment.
- `elite.escort` (`aiEliteTactics.xs`) — fires when an escort plan is created.

---

### 2. `tools/playtest/coverage_v2.py`

Three new gap checks:

| Suite | Probe consumed | Logic |
|-------|---------------|-------|
| `pacing_v2` | `event.age_up` | Age-to-Commerce time ≤ per-civ budget (rush 4:00, eco 5:00, native 5:30). First age-2 probe per player. |
| `shipment_order_v2` | `tech.ship` | Card index must not appear twice in the same age (duplicate shipment = FAIL). Out-of-order swaps are WARN. |
| `escort_v2` | `mil.escort_check` | Leader must be ≤ 30 m from nearest army unit in ≥ 90 % of attack-active samples. |

Public constant: `PACING_BUDGET_MS` dict (civ name → ms). Override per-civ by editing this dict before test runs.

---

### 3. `tools/validation/run_staged_validation.py` extensions

- New flag `--all-runtime-suites` — includes `pacing_v2`, `shipment_order_v2`, `escort_v2` on top of the existing JSON-spec suites.
- Suite names `pacing_v2` / `shipment_order_v2` / `escort_v2` are also accepted via `--runtime-suite`.

---

### 4. `tools/aoe3_automation/aoe3_ui_automation.py` — env-var interpolation

`_interpolate_step()` expands `${VAR}` in all string step parameters (including `texts` lists and `image`/`path` fields) using `os.environ`. Unknown variables are left as-is. Applied automatically in `run_flow()` before each step is dispatched.

---

### 5. Flow files

| File | Purpose |
|------|---------|
| `tools/aoe3_automation/flows/matrix_setup_skirmish.json` | One-shot: launches AoE3, dismisses update dialog, opens Skirmish. Run once before the matrix loop. |
| `tools/aoe3_automation/flows/matrix_run_one_civ.json` | Per-civ parametric flow. Uses `${CIV_NAME}` and `${LEADER_NAME}`. Picks civ, picks leader, starts match, waits for Victory/Defeat, saves screenshot, returns to lobby. |
| `tools/aoe3_automation/flows/matrix_run_all.py` | Python driver. Loops 48 civs, runs the flow, rotates log, runs coverage_v2, writes per-civ artifact dir + final `report.md`. |

---

### 6. Unit tests

| File | Coverage |
|------|---------|
| `tests/playtest/test_coverage_v2.py` | Green + red path for each of the three new validators; `parse_probes` filter; `run_all_checks` combined path. |
| `tests/validation/test_aoe3_ui_automation.py` | Added `InterpolateStepTests` for `_interpolate_step()`. |

---

## How to invoke

### Run staged validation (content + regression, offline)

```bash
python3 tools/validation/run_staged_validation.py --stage content --stage regression
```

### Run the three new suites against a real log

```bash
python3 tools/playtest/coverage_v2.py ~/.steam/.../Age3Log.txt \
    --suite pacing_v2 --suite shipment_order_v2 --suite escort_v2
```

Or via the staged runner (runtime stage):

```bash
python3 tools/validation/run_staged_validation.py --stage runtime --all-runtime-suites
```

### Full 48-civ matrix

```bash
# 1. Setup (once)
python3 tools/aoe3_automation/aoe3_ui_automation.py run-flow \
    tools/aoe3_automation/flows/matrix_setup_skirmish.json

# 2. Matrix loop (~6-8 hours)
python3 tools/aoe3_automation/flows/matrix_run_all.py

# Dry-run to verify without a game:
python3 tools/aoe3_automation/flows/matrix_run_all.py --dry-run
```

Per-civ artifact dirs land in `tools/aoe3_automation/artifacts/matrix_<timestamp>/`.
Final report: `artifacts/matrix_<timestamp>/report.md`.

### Speed optimisation

In Advanced Settings (set once in setup flow or manually):
- Game speed: **Fastest** (≈ 2×)
- Reveal Map: **On**
- No Fog: **On**
- Player handicap: **200 %** (player gets double resources → CPU loses faster)

Target: 6–10 min wall-clock per match → 48 civs in ~6–8 hours.

---

## Templates still needed (capture in-game)

The image-based actions reference templates that must be captured from a live 1920×1080 English-locale game session. Run:

```bash
python3 tools/aoe3_automation/aoe3_ui_automation.py capture-reference
```

Templates to capture and save under `tools/aoe3_automation/templates/matrix/`:

1. `single_player_button.png` — Main menu "Single Player" button
2. `skirmish_button.png` — Single-player mode list "Skirmish" entry
3. `dismiss_update.png` — Steam / game update dialog dismiss button (optional)
4. `player1_civ_dropdown.png` — Player 1 civilisation dropdown in Skirmish lobby
5. `leader_dropdown.png` — Leader portrait / dropdown (if separate from civ)
6. `advanced_settings_button.png` — Advanced Settings toggle button
7. `game_speed_fastest.png` — Game Speed "Fastest" option
8. `reveal_map_on.png` — Reveal Map toggle in Advanced Settings
9. `advanced_settings_close.png` — Close / confirm Advanced Settings
10. `start_game_button.png` — "Launch" / "Start Game" button

OCR-only steps (no template needed): `${CIV_NAME}`, `${LEADER_NAME}`, Victory/Defeat/Continue.

---

## Suites now available

| Suite | Stage | Needs live log |
|-------|-------|----------------|
| (all 15 existing) | content / regression | No |
| `pacing_v2` | runtime | Yes |
| `shipment_order_v2` | runtime | Yes |
| `escort_v2` | runtime | Yes |
