# Testing Workflow

This repo now has a staged testing model so changes do not depend on one long manual match to catch basic breakage.

## Gates

1. `Content validation`
   Run the structural validators for XML, civ cross-references, homecity links, UI assets, proto, techtree, stringtables, and XS scripts.
2. `Validator regression tests`
   Run the Python regression tests so changes to validators do not silently weaken the safety net.
3. `Packaged mod validation`
   Build a clean packaged tree in a temp directory and validate the exact payload shape that should ship.
4. `Live mod install validation`
   Compare the active Proton local mod copy against the packaged repo payload so runtime failures are not caused by a stale install.
5. `Runtime log validation`
   Validate `Age3Log.txt` against objective `Legendary Leaders:` runtime suites after a scenario or skirmish run.
6. `Manual observer pass`
   Keep subjective AI feel, pressure rhythm, and formation-quality checks separate from the objective machine-checked gates.

## One Command

Run the local staged workflow:

```bash
./.venv/bin/python tools/validation/run_staged_validation.py
```

Or in VS Code, run `Tasks: Run Task` and pick one of the `Validation:` tasks from `.vscode/tasks.json`.
That path keeps validation in the repo and terminal instead of depending on this chat session.

That runs all five machine-check stages. The live stage and runtime stage will report `SKIPPED` until the local install and runtime log exist.

Useful variants:

```bash
./.venv/bin/python tools/validation/run_staged_validation.py --stage content --stage packaged
./.venv/bin/python tools/validation/run_staged_validation.py --stage live
./.venv/bin/python tools/validation/run_staged_validation.py --stage runtime --runtime-suite elite_retreat_lane
./.venv/bin/python tools/validation/run_staged_validation.py --report-file .validation-reports/staged-validation.txt
```

Useful editor-native task entry points:

- `Validation: staged`
- `Validation: content + regression`
- `Validation: live install`
- `Validation: runtime log`
- `Validation: sandbox ai rout bootstrap`
- `Validation: sandbox elite retreat lane`
- `Validation: sandbox elite support blocks rout`

## Runtime Passes

Use a controlled environment for runtime validation instead of free-play-only testing.

For deterministic AI-rout and explorer mechanics:

- `Scenario/TEST_SCENARIO_SETUP.md`
- `Scenario/CHECKLIST_AUTOMATION_MATRIX.md`

For broader skirmish behavior, teamfight shape, and naval checks:

- `RandMaps/Legendary Leaders Test.md`
- `Scenario/TEST_MAP_ROADMAP.md`
- `Scenario/COMMANDER_NAVAL_STRESS_MAP.md`

After the match or scenario finishes, validate the objective log markers:

```bash
tools/validation/run_objective_runtime_checks.sh
```

The runtime suites also include `elite_support_blocks_rout`, which machine-checks the negative case where elite support correctly prevented AI non-elite rout.

`ai_rout_bootstrap` is the canonical AI-rout bootstrap suite. It verifies that AI-only non-elite rout activates at 25% health while elite units and player-controlled units remain outside the auto-rout path.

Or run the broader staged command against an explicit log path:

```bash
./.venv/bin/python tools/validation/run_staged_validation.py \
  --stage runtime \
  --runtime-log-path "$HOME/.steam/steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Logs/Age3Log.txt"
```

For unattended local runtime retests that also sync the live install and launch the existing harness, use the sandbox runner directly:

```bash
./.venv/bin/python tools/aoe3_automation/run_sandbox.py --runtime-suite ai_rout_bootstrap
./.venv/bin/python tools/aoe3_automation/run_sandbox.py --runtime-suite elite_retreat_lane
./.venv/bin/python tools/aoe3_automation/run_sandbox.py --runtime-suite elite_support_blocks_rout
```

Those same flows are exposed as VS Code tasks so they can be launched without chat.

## Manual Pass

Leave these in a short observer checklist instead of pretending they are objective today:

- nation feel and tempo differences
- whether explorers stay screened in believable ways
- whether artillery presence feels core or incidental
- whether assault composition looks regular-first and elite-second in practice

Those items should move into machine validation only after explicit `Legendary Leaders:` logging exists for them.