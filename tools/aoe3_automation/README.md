# AoE3 UI Automation

This is a small desktop automation harness for repeatedly launching and driving Age of Empires III: DE menu flows.

It supports two automation styles:

- `record-input`: raw mouse and keyboard event recording, then `replay-input`.
- `run-flow`: image-driven, step-by-step UI automation using screenshots as anchors.

It also includes two support commands:

- `probe-environment`: report which Linux desktop automation backends are available.
- `collect-artifacts`: copy AoE3 log files and optionally grab a screenshot after a failure.

The image-driven flow is the safer mode for game menus because it is less sensitive to timing drift than pure replay.

## Dependencies

Install into a virtual environment if you want to keep it isolated:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r tools/aoe3_automation/requirements.txt
```

## Linux Note

This script is intended for X11 or XWayland. Pure Wayland sessions often block input injection and sometimes screen scraping.

If you run VS Code inside Flatpak, the script can also use host-side tools through `flatpak-spawn --host`. On this machine that means:

- host `xdotool` can drive input
- host `spectacle` can capture screenshots

That makes image-driven flows viable from inside the sandbox, as long as the host X display remains reachable.

If host passthrough is not available, you will still need a compositor-approved injector such as `ydotool` or a normal X11/XWayland session.

Check your current environment with:

```bash
python3 tools/aoe3_automation/aoe3_ui_automation.py probe-environment
```

## Commands

Record raw input until `Esc`:

```bash
python3 tools/aoe3_automation/aoe3_ui_automation.py record-input tools/aoe3_automation/recordings/start_match.json
```

Replay the captured input:

```bash
python3 tools/aoe3_automation/aoe3_ui_automation.py replay-input tools/aoe3_automation/recordings/start_match.json --speed 1.0
```

Capture a reference image for button matching:

```bash
python3 tools/aoe3_automation/aoe3_ui_automation.py capture-reference tools/aoe3_automation/templates/single_player_button.png
```

Run an image-driven flow:

```bash
python3 tools/aoe3_automation/aoe3_ui_automation.py run-flow tools/aoe3_automation/flows/example_skirmish_flow.json
```

Collect failure artifacts:

```bash
python3 tools/aoe3_automation/aoe3_ui_automation.py collect-artifacts tools/aoe3_automation/artifacts/latest --screenshot
```

Validate the resulting AoE3 runtime log against a named Legendary Leaders suite:

```bash
python tools/validation/validate_runtime_logs.py \
	--log-path "$HOME/.steam/steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Logs/Age3Log.txt" \
	--suite elite_retreat_lane
```

Orchestrate the whole sequence with one command:

```bash
./.venv/bin/python tools/aoe3_automation/run_runtime_validation.py \
	tools/aoe3_automation/flows/dutch_napoleon_vs_russia_egypt_skirmish.json \
	--suite prisoner_system_bootstrap \
	--artifacts-dir tools/aoe3_automation/artifacts/dutch_napoleon_vs_russia_egypt \
	--screenshot
```

This is the preferred way to promote runtime systems from "structurally wired" to "behaviorally verified": drive the menu flow, run a deterministic scenario or skirmish, collect `Age3Log.txt`, and assert on `Legendary Leaders:` log markers.

Retest the current mod install with one shell command:

```bash
tools/aoe3_automation/launch_retest_mod.sh
```

Useful variants:

```bash
tools/aoe3_automation/launch_retest_mod.sh --skip-launch --flow tools/aoe3_automation/flows/capture_open_menu.json
tools/aoe3_automation/launch_retest_mod.sh --skip-launch --skip-flow
tools/aoe3_automation/launch_retest_mod.sh --runtime-suite prisoner_system_bootstrap
```

The script snapshots the previous `Age3Log.txt`, runs the static validation profiles, optionally launches AoE3, optionally runs a UI flow, collects artifacts, and writes a grep-based runtime error scan into the run artifact directory.

## Flow Format

`run-flow` expects a JSON object with a `steps` array. Supported actions:

- `launch`
- `sleep`
- `wait_image`
- `click_image`
- `click`
- `press`
- `hotkey`
- `type_text`
- `scroll`
- `screenshot`

See [tools/aoe3_automation/flows/example_skirmish_flow.json](tools/aoe3_automation/flows/example_skirmish_flow.json) for a starting template.

## Recommended Workflow

1. Capture reference images for the exact buttons and civ/map slots you want.
2. Build a `run-flow` JSON that waits for those images before clicking.
3. Keep the game resolution and UI scale fixed.
4. Use `record-input` only for short stable segments, not as the primary whole-run approach.
5. Run `probe-environment` first if you are inside Flatpak or Wayland, so you know which host backends are actually usable.
6. After the match or scenario run, validate `Age3Log.txt` with `tools/validation/validate_runtime_logs.py` and the appropriate suite name.

## Current Limits

- It does not inspect game memory or internal UI objects.
- It relies on the game window being visible.
- It will be brittle if the UI layout, resolution, or language changes.
- `Esc` is the stop key for recording.
- `record-input` still depends on local Python packages such as `pynput`; host passthrough currently helps with playback and flow execution, not raw event capture.
- Image matching still depends on Python dependencies from [tools/aoe3_automation/requirements.txt](tools/aoe3_automation/requirements.txt).