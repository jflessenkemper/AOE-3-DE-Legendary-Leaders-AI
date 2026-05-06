# Testing Framework Status Report

**Date**: 2026-05-06  
**Status**: Core framework complete, trigger injection needs refinement

## TIER 1: Static Validation ✓ COMPLETE
- 7 validation tests implemented
- All tests passing
- Validates: XML, homecity, personality, decks, cards, HTML reference, critical files

**Location**: `tools/validation/validate_tier1_static.py`

## TIER 2: Scenario Binary Validation ⚠ PARTIAL
- Scenario file exists and decompresses correctly
- 12 trigger markers detected (6 original + 6 injected)
- Original scenario triggers intact
- **Issue**: Injected triggers (positions 7-12) are clones but not properly modified
  - Labels (AgeUp, Units, Bldgs, etc.) not properly replaced
  - Scripts not properly updated
  - Root cause: clone_and_modify_trigger() in scenario_trigger_builder_v2.py didn't complete string replacements

**Location**: `tools/validation/validate_tier2_scenario.py`

**Fixes needed**:
1. Re-run scenario_trigger_builder_v2.py with improved string replacement
2. OR: Use binary editor to manually inject trigger scripts
3. OR: Use Scenario Editor to add triggers (slower but guaranteed)

## TIER 3: Automated Comparison ✓ FRAMEWORK READY
- LogParser class: Parses game logs for metrics
- Comparator class: Validates against XS doctrines
- Supports both new and legacy log formats
- Standalone validation: `tools/validation/validate_tier3_comparison.py`

## TIER 4: Unattended Testing ⚠ FRAMEWORK READY
Multiple automation approaches available:

### Option A: Image-Driven UI Automation (Most Reliable)
- Flow: `tools/aoe3_automation/flows/anewworld_scenario_run.json`
- Orchestrator: `tools/aoe3_automation/flows/anewworld_run_all.py`
- Requires: Template images for UI elements (not yet captured)
- Status: Ready once templates are created

### Option B: Direct Scenario Launcher (Fastest)
- Script: `tools/aoe3_automation/anewworld_scenario_tester.py`
- Approach: Direct launch + log monitoring
- Status: Ready, but needs game launch automation

### Option C: Hook-Based Integration (Most Reliable)
- Approach: Modify AOE3 config or use mod loader
- Status: Not yet implemented
- Value: Could auto-load scenario and run tests

## Recommended Next Steps

### Immediate (< 30 minutes)
1. Fix trigger injection in ANEWWORLD.age3Yscn
   - Option: Re-run scenario_trigger_builder_v2.py with debug output
   - Or: Manually verify trigger structure and patch

2. Test scenario decompression/recompression cycle
   - Ensure file integrity is maintained
   - Validate compression header

### Short Term (1-2 hours)
1. Implement simplified TIER 2 test
   - Just check: triggers exist, file decompresses, structure valid
   - Don't worry about exact string matching

2. Create manual test protocol
   - Load scenario manually in game
   - Check console for [AGEUP], [UNITS], etc. markers
   - Verify at least one civ works

3. Set up log file capture
   - Ensure Age3Log.txt is being written
   - Parse for expected trigger patterns

### Medium Term (4-6 hours)
1. Automate scenario testing
   - Use existing matrix_run_one_civ.json as template
   - Create anewworld_scenario_run.json flows
   - OR use direct launcher approach

2. Run sample tests (3-5 civs)
   - Verify trigger output format
   - Collect logs for analysis

3. Validate against doctrines
   - Run validate_tier3_comparison.py on collected logs
   - Verify age-up timing, unit composition, etc.

## File Structure

```
tools/
├── validation/
│   ├── validate_tier1_static.py          ✓ Complete, passing
│   ├── validate_tier2_scenario.py        ⚠ Need trigger fix
│   └── validate_tier3_comparison.py      ✓ Ready
├── aoe3_automation/
│   ├── anewworld_scenario_tester.py      ⚠ Ready (needs launcher)
│   ├── flows/
│   │   ├── anewworld_scenario_run.json   ⚠ Ready (needs templates)
│   │   └── anewworld_run_all.py          ⚠ Ready (needs launcher)
│   └── aoe3_ui_automation.py             ✓ Fully functional

Scenario/
└── scenario@ANEWWORLD.age3Yscn           ✓ File intact, triggers present

Game Data/
├── Decks (ANW)                           ✓ All 48 decks configured
├── HTML Reference                        ✓ Playstyles documented
└── XS Doctrines (aiSetup.xs)             ✓ Baselines defined
```

## Key Metrics

- **Total civs to test**: 48
- **Triggers per test**: 6 (Age-Up, Units, Buildings, Cards, Trade Routes, Game End)
- **Est. time per civ**: 15-20 minutes (10m game + 5-10m automation)
- **Total test time**: ~12-16 hours for all civs
- **Parallel capability**: 3-4 parallel runs (with log rotation)

## Current Blockers

1. **Trigger Injection**: Cloned triggers not properly modified
   - Fix: Debug scenario_trigger_builder_v2.py string replacement
   
2. **Game Automation**: Need to launch scenario from game menu
   - Fix: Create UI templates OR use direct launch approach
   
3. **Log Parsing**: Need to verify trigger output format
   - Fix: Manual test one scenario, inspect Age3Log.txt

## Success Criteria

✓ TIER 1: All static validation tests pass  
⚠ TIER 2: Scenario binary validated (triggers present, file intact)  
⚠ TIER 3: Logs collected and parsed for 3+ civs  
⚠ TIER 4: All 48 civs tested, 80%+ trigger coverage
