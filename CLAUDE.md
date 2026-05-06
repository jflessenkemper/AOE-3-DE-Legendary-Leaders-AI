# A New World DLC — Claude Code Guide

## Quick-start (run at session start)

```bash
python3 tools/validation/validate_leader_vs_spec.py   # must show 20/20 PASS
```

Then ask the user what to tackle before spawning any subagents.

## Project state

- **Mod name:** A New World DLC (AOE 3 DE)
- **Version:** `0.9.0-rc1` (`modinfo.json`)
- **v1.0 gate:** `playtest_report.txt` must show 0 FAIL rows across all 48 civs (doctrine matrix run on Bazzite/Proton rig). This is hardware-gated — not code.
- **Static checks:** 16/16 content checks pass (`bash tools/test.sh --no-packaged`). 20/20 leaders pass static linter.

## Key constants (don't re-grep these)

**Wall strategy** — `game/ai/aiHeader.xs:202-207`
```
0=FortressRing  1=ChokepointSegments  2=CoastalBatteries
3=FrontierPalisades  4=UrbanBarricade  5=MobileNoWalls
```

**Leader key bridge** (engine slug → spec slug):
```
wellington→elizabeth  catherine→ivan  crazyhorse→gall  jean→valette  usman→muhammadu
```
Defined at `game/ai/leaders/leaderCommon.xs:480-485`.

**Style helpers** — `game/ai/leaders/leaderCommon.xs:191-327`
(llUseCompactFortifiedCoreStyle, llUseForwardOperationalLineStyle, etc.)
One call per leader file; last write wins for gLLWallStrategy.

**Probe format:**
```
[LLP v=2 t=<ms> p=<id> civ=<name> ldr=<key> tag=<x.y>] k=v ...
```
Triple-channel: aiEcho + aiChat to host + aiChat to self. Gated on `cLLReplayProbes`.

**15 canonical doctrines** — `tools/playtest/extract_playstyle_spec.py:94`

## Common tasks

| Task | Command |
|------|---------|
| Static linter (no engine) | `python3 tools/validation/validate_leader_vs_spec.py` |
| Full static suite | `bash tools/test.sh --no-packaged` |
| Preflight table | `bash tools/test.sh --preflight` |
| Doctrine matrix (needs rig) | `python3 tools/aoe3_automation/matrix_runner.py --batch-size 8 --auto-resign-ms 90000` |
| Personality string check | `python3 tools/validation/validate_personality_overrides.py` |

## Validation pipeline layout

```
tools/validation/validate_leader_vs_spec.py     ← static linter (no engine)
tools/validation/validate_doctrine_compliance.py ← runtime validator (needs match.log)
tools/validation/validate_personality_overrides.py ← nameID/tooltipID vs stringmods.xml
tools/validation/compile_playtest_report.py     ← assembles playtest_report.txt
tools/playtest/extract_playstyle_spec.py        ← regenerates playstyle_spec.json
tools/playtest/html_reference.py               ← parses LEGENDARY_LEADERS_TREE.html
```

## v1.0 release checklist (remaining)

- [ ] **B1 ⛔ BLOCKER** Doctrine matrix run → 0 FAIL rows in playtest_report.txt (~60 min on rig)
- [ ] B2 Install sanity (no error dialogs, mod in Mods list)
- [ ] B3 Lobby personality matrix — 22 overrides show correct name/portrait/tooltip
- [ ] B4 Four archetype matches — AI build order matches HTML reference prose
- [ ] B5 Save/Load smoke test
- [ ] B6 Uninstall clean-up
- [ ] After all above: bump `modinfo.json` → `1.0.0`, finalize CHANGELOG, tag `v1.0.0`

## File map (avoid re-grepping)

| What | Where |
|------|-------|
| AI leader files | `game/ai/leaders/leader_*.xs` (23 files) |
| Personality files | `game/ai/*.personality` (48 files) |
| String overrides | `data/strings/english/stringmods.xml` |
| Playstyle spec | `playstyle_spec.json` (46 civs × 15 doctrines) |
| HTML reference | `LEGENDARY_LEADERS_TREE.html` |
| Card decks | `data/decks_standard.json`, `data/decks_legendary.json` |
| Release plan | `/home/jflessenkemper/.claude/plans/what-does-version-1-0-tingly-reef.md` |

## Token-budget mode (always on)

The user is on a 5-hour usage limit and wants every session to minimise context burn. Treat the rules below as hard defaults. Only break them if the user explicitly asks.

**Reading files**
- Never `Read` a file >500 lines without `offset`/`limit`. For unknown-size files, `Grep` first to find the right line range, then `Read` with `limit`.
- Never re-read a file already read this session unless it was edited. Cite from memory.
- Use `Grep` (not `Read` + scan) to locate symbols. Prefer `output_mode: "files_with_matches"` first, then narrow.

**Delegation**
- Multi-file exploration → `Agent` (Explore, "quick" thoroughness). The agent's summary returns to me; raw file contents do not pollute this context.
- Long-running content writing (blurbs, docs, refactors across many files) → `Agent` with `model: sonnet` or `haiku`. Don't do it inline.
- Batch independent tool calls in one message (parallel) instead of sequentially.

**Editing**
- `Edit` over `Write` for existing files (sends diff, not full contents).
- No emojis, no new docs, no proactive README/CHANGELOG additions unless asked.

**Scope discipline**
- One task at a time. After finishing the user's ask, stop — don't drift into adjacent cleanup. Use `mcp__ccd_session__spawn_task` to flag follow-ups instead of doing them inline.
- Don't re-state the plan; don't recap; don't narrate. Output text only when it answers the question or reports a result.

**Validation**
- Don't auto-run validators after every edit. Run them once at logical checkpoints or when the user asks.
- Don't run `tools/validation/run_staged_validation.py` (18 validators, slow) unless asked or as part of a release gate.

**Model**
- Default model for routine tool calls: whatever the user has selected. Don't switch models silently. If a heavy synthesis task arises, ask before promoting to Opus.

**ANW migration state (so I don't re-derive it)**
- Phase 1-5 scripts written and dry-run-clean. `data/civmods.anw.xml` has 0 TODO-ANW-VANILLA markers — apply gate is unblocked.
- `python3 tools/migration/run_anw_migration.py --apply` is the next destructive step. **Requires explicit user confirmation** before running.
- After apply: phases 6 (validators rewrite), 7 (in-engine smoke), 8 (tag v1.0.0) remain.
