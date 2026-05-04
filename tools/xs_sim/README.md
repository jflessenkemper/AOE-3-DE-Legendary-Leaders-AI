# xs_sim — standalone interpreter for AoE3 DE XS scripts

A zero-dependency Python interpreter for the XS scripting language used by
Age of Empires III: Definitive Edition AI. Built to test AI **decision
logic** (rule bodies, doctrine globals, age branches) without launching the
game engine.

> **Status:** experimental. Decision-layer simulator, not a full engine.
> See [Coverage](#coverage) for what is and isn't simulated.

---

## Quick start

```bash
# Parse-coverage check across the whole AI codebase
python3 -m tools.xs_sim.harness --parse-only

# Run every leader through 180s of simulated time
python3 -m tools.xs_sim.harness

# Run one leader, verbose JSON output
python3 -m tools.xs_sim.harness napoleon --json

# Unit tests
python3 -m unittest tools.xs_sim.tests.test_smoke
```

---

## Coverage

| Layer | Coverage | Notes |
|-------|----------|-------|
| **XS language** | ~95% | Types, control flow, rules, arrays, vectors, ternary, switch/case, both `for` styles, bitwise ops, `#include`. Lambdas + fn-pointer params not yet supported (used in a handful of `core/*.xs` files). |
| **AI decision logic** | ~85% | All `kb*`/`ai*` queries the leaders use are mocked against a configurable `GameState`. Rule scheduler honors `minInterval`, `active`/`inactive`, `xsEnableRule`/`xsDisableSelf`. |
| **Action verbs** (`aiTask*`, `aiTrainUnit`) | logged-only | Calls are recorded into `gs.actions` for assertion, but unit training/combat/pathfinding are **not** simulated. |
| **Actual game outcomes** | 0% | Use the in-engine doctrine matrix for that — this tool can't substitute. |

In numbers: **26/26 leader files parse, 24/24 leaders execute their `init` and tick rules to mutate doctrine globals.** That covers the v1.0 doctrine compliance question for the *decision* half — does the leader file set the right wall strategy / military focus / trade bias for the right age? — without burning a Bazzite/Proton matrix run.

---

## Architecture

```
lexer.py        zero-dep tokenizer
ast_nodes.py    dataclass AST
parser.py       recursive-descent parser
interpreter.py  tree-walker + rule scheduler
gamestate.py    GameState + scenario_open_age2() etc.
builtins.py     xs*/kb*/ai* mocks + unknown-call fallthrough
harness.py      CLI: load leader → init → tick → report doctrine
```

### Scheduler model

Each `rule` declaration is registered with its `minInterval` (seconds) and `active` flag.  `Interpreter.tick(dt)` advances `gs.sim_time_s` and fires every rule whose `(now - last_fire) ≥ minInterval`. Rules can self-disable via `xsDisableSelf()` or be enabled/disabled by other rules via `xsEnableRule(name)` — same semantics as the engine.

### Mock GameState

Pre-baked scenarios in `gamestate.py`:

```python
scenario_open_age2()        # Age II, balanced resources, no threat
scenario_coastal_age2()     # + has_water=True, map_class="coastal"
scenario_under_threat_age2()# + threat_level=0.7
scenario_industrial()       # Age IV
```

Builtins read directly from this. Unknown builtins (the long tail of ~280 game APIs) return a typed zero and are tracked in `interp.unknown_calls` for visibility.

---

## What this is for

- **Modders:** sanity-check that a new leader's init function and rule bodies set the doctrine globals you intended, without 60-min in-engine runs.
- **CI:** parse-coverage check on every PR ensures no XS file is broken.
- **Doctrine refactors:** verify a `leaderCommon.xs` change doesn't silently change downstream leader behavior.

## What this is **not** for

- Replacing the in-engine doctrine matrix (`tools/aoe3_automation/matrix_runner.py`). That validates actual unit training, combat, and pathing — none of which this simulator touches.
- Performance-critical regression testing. The tree-walker is slow.
- Validating XS code against the real engine's strict typing — the simulator is permissive (unknown vars treated as 0/false in non-strict mode).

---

## Extending

Adding a new builtin:

```python
# tools/xs_sim/builtins.py
def _kbGetWaterPercentage(args, gs, interp):
    return 0.5 if gs.has_water else 0.0

BUILTINS["kbGetWaterPercentage"] = _kbGetWaterPercentage
```

Adding a new scenario:

```python
# tools/xs_sim/gamestate.py
def scenario_late_game_naval() -> GameState:
    gs = scenario_industrial()
    gs.has_water = True
    gs.counts["naval"] = 8
    return gs
```

---

## License

Same as the parent repo.
