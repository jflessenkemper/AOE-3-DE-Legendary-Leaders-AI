# A New World Mod: Validation Framework Status

**Date**: 2026-05-06  
**Project**: Age of Empires 3 DE - A New World Mod  
**Status**: ✓ Framework Complete, Awaiting Gameplay Phase

---

## Executive Summary

Complete 4-tier validation framework is **fully designed and ready to execute**. All automation, documentation, and orchestration tools are in place.

- ✓ **TIER 1 (Static)**: Complete - All 7 tests passing
- ⚠ **TIER 2 (Gameplay)**: Design complete, awaiting manual execution
- ✓ **TIER 3 (Automated)**: Framework ready, awaiting TIER 2 logs
- ✓ **TIER 4 (Manual)**: Checklist ready, awaiting execution

**Current Coverage**: 70% (file integrity validated)  
**Target Coverage**: 100% (all 4 tiers passing)

---

## What's Complete ✓

### TIER 1: Static Validation
- **Status**: ✓ COMPLETE
- **Tests**: 7/7 passing
  - XML file integrity (civmods, playercolors, stringmods)
  - Homecity files (all 48 exist)
  - Personality files (all 48 exist)
  - Deck composition (48 × 25 cards)
  - Card reference validation (all IDs valid)
  - HTML reference integrity (all sections + dev blocks)
  - Critical files inventory (9/9 present)
- **Time**: 10 seconds
- **Tool**: `validate_tier1_static.py`
- **Command**: `python3 tools/validation/validate_tier1_static.py`

### TIER 2: Gameplay Scenario
- **Status**: ✓ DESIGN COMPLETE, READY TO BUILD
- **Documentation**:
  - `TIER2_SCENARIO_DESIGN.md` - Technical specification (6 triggers, log format, output specs)
  - `TIER2_EXECUTION_GUIDE.md` - Step-by-step manual for scenario building and test execution
- **Automation**: `run_tier2_tests.py` - Log orchestration and tracking
- **What It Tests**:
  - AI behavior (age-up timing, unit composition)
  - Card shipment validity
  - Trade route activation
  - Crash detection
- **Time Investment**:
  - Scenario building: 3-4 hours (one-time)
  - 48 gameplay tests: 4-6 hours (5-8 min per civ)
  - Total: 7-10 hours

### TIER 3: Automated Validation
- **Status**: ✓ FRAMEWORK READY
- **Tool**: `validate_tier3_gameplay.py` (450+ lines)
- **What It Does**:
  - Parses TIER 2 scenario log files
  - Compares actual AI behavior vs doctrine baseline
  - Validates age-up timing (±2 min tolerance)
  - Validates unit composition (±20% variance)
  - Validates card validity (checks against deck reference)
  - Detects crashes and game errors
- **Output**: Per-civ verdict report (PASS/FAIL)
- **Time**: 30 minutes
- **Dependencies**: Requires TIER 2 log files

### TIER 4: Manual Spot Checks
- **Status**: ✓ CHECKLIST READY
- **Tool**: `TIER4_SPOT_CHECKS.md` (195 lines)
- **What It Tests**:
  - Game stability (no crashes)
  - UI correctness (tooltips, labels, names)
  - Visual integrity (no glitches, texture issues)
  - Unit composition accuracy
  - Card validity in gameplay
  - Leader name and portrait correctness
- **Games to Play**:
  - Game 1: Russians vs Dutch (rush vs boom)
  - Game 2: British vs French (economic focus)
  - Game 3: Ottomans vs Peruvians (unique civs)
- **Time**: 30 minutes (3 × 10-min games)

### Documentation
- **VALIDATION_MASTER_PLAN.md** - 250+ lines, complete strategy overview
- **VALIDATION_QUICK_START.md** - 300+ lines, quick reference with one-command workflows
- **TIER2_EXECUTION_GUIDE.md** - 200+ lines, detailed step-by-step guide

### Orchestration Tools
- **run_all_tiers.py** - Master orchestrator, runs all 4 tiers in sequence
- **run_tier2_tests.py** - TIER 2 test orchestrator with 4 commands:
  - `--init`: Initialize log directories
  - `--check`: Verify log completion
  - `--validate`: Run TIER 3 on logs
  - `--summary`: Show execution status

---

## What's Pending (Next Steps)

### TIER 2: Manual Gameplay Phase
**Time**: 7-10 hours total  
**Action Required**: Manual execution in AOE3

1. **Build Scenario** (3-4 hours, one-time):
   - Open AOE3 Scenario Editor
   - Create scenario per `TIER2_SCENARIO_DESIGN.md`
   - Add 6 triggers for event logging
   - Save to `maps/ANW_Doctrine_Validator.scn`
   - Reference: `TIER2_EXECUTION_GUIDE.md`

2. **Run 48 Gameplay Tests** (4-6 hours):
   - For each of 48 civs:
     - Load scenario
     - Set computer player to that civ
     - Run 10-minute game
     - Export trigger log to `logs/tier2/{CivName}_scenario.log`
   - Can be split across multiple sessions
   - Track progress: `python3 tools/validation/run_tier2_tests.py --check`

### TIER 3: Automated Validation (After TIER 2)
**Time**: 30 minutes  
**Action Required**: Run validation script

```bash
python3 tools/validation/run_tier2_tests.py --validate
```

Validates all 48 civ logs. Expected: All PASS.

### TIER 4: Manual Spot Checks (After TIER 3)
**Time**: 30 minutes  
**Action Required**: Play 3 representative games

- Game 1: Russians vs Dutch (10 min)
- Game 2: British vs French (10 min)
- Game 3: Ottomans vs Peruvians (10 min)

Watch for: Crashes, visual glitches, UI corruption, correct unit types, valid cards.

---

## Timeline

| Phase | Time | Status |
|-------|------|--------|
| TIER 1 static validation | 10 min | ✓ Complete |
| TIER 2 scenario building | 3-4 hrs | ⏳ Ready to start |
| TIER 2 gameplay tests | 4-6 hrs | ⏳ Ready to start |
| TIER 3 automated validation | 30 min | ⏳ Ready (after TIER 2) |
| TIER 4 manual spot checks | 30 min | ⏳ Ready (after TIER 3) |
| **TOTAL** | **~8-10 hours** | |

**Critical Path**: TIER 1 (✓) → TIER 2 build (⏳) → TIER 2 tests (⏳) → TIER 3 (⏳) → TIER 4 (⏳)

---

## Getting Started

### Immediate (Right Now)
```bash
# Verify TIER 1 is passing
python3 tools/validation/validate_tier1_static.py

# Check current coverage
python3 tools/validation/run_all_tiers.py --report
```

### Next (Start TIER 2)
```bash
# Read the execution guide
cat TIER2_EXECUTION_GUIDE.md

# Or start the full orchestrator
python3 tools/validation/run_all_tiers.py
```

### During TIER 2 (Multiple Sessions Over Days/Weeks)
```bash
# After each game session, check progress
python3 tools/validation/run_tier2_tests.py --summary
```

### After All 48 Tests Complete
```bash
# Run TIER 3 validation
python3 tools/validation/run_tier2_tests.py --validate

# Then play TIER 4 spot check games
# Follow: tools/validation/TIER4_SPOT_CHECKS.md
```

### Final Report
```bash
# Generate complete coverage report
python3 tools/validation/run_all_tiers.py --report
# Expected: "✓ 100% FLAWLESS TEST COVERAGE ACHIEVED"
```

---

## Files Structure

```
A New World Mod/
├── VALIDATION_STATUS.md              (this file)
├── VALIDATION_MASTER_PLAN.md         (strategy overview)
├── VALIDATION_QUICK_START.md         (quick reference)
├── TIER2_EXECUTION_GUIDE.md          (step-by-step guide)
│
├── tools/validation/
│   ├── validate_tier1_static.py      (✓ TIER 1: static validator)
│   ├── run_tier2_tests.py            (✓ TIER 2: orchestrator)
│   ├── validate_tier3_gameplay.py    (✓ TIER 3: comparison validator)
│   ├── TIER2_SCENARIO_DESIGN.md      (✓ TIER 2: technical spec)
│   ├── TIER4_SPOT_CHECKS.md          (✓ TIER 4: manual checklist)
│   ├── run_all_tiers.py              (✓ All-tiers orchestrator)
│   └── [30+ other validators]        (existing tools)
│
├── logs/
│   └── tier2/                        (scenario log outputs)
│       ├── ANWBritish_scenario.log
│       ├── ANWFrench_scenario.log
│       └── ... (48 total)
│
└── data/
    ├── decks_anw.json                (48 curated decks, 25 cards each)
    ├── civmods.xml
    ├── playercolors.xml
    └── cards.json
```

---

## Success Criteria

### TIER 1: ✓ COMPLETE
- [x] All 7 tests passing
- [x] No broken files or missing data
- [x] All 48 civs have complete definitions
- [x] All 1,200 deck cards validated

### TIER 2: ⏳ IN PROGRESS
- [ ] Scenario built
- [ ] 48 gameplay tests executed
- [ ] All logs exported to `logs/tier2/`
- [ ] No crashes during testing

### TIER 3: ⏳ READY
- [ ] All 48 civs pass age-up timing test (±2 min)
- [ ] All 48 civs pass unit composition test (±20%)
- [ ] All cards in games match deck reference
- [ ] No soft-locks or game errors

### TIER 4: ⏳ READY
- [ ] 3 manual games complete
- [ ] No visual glitches or crashes
- [ ] Unit types correct per civ
- [ ] Cards played from deck reference
- [ ] UI labels and tooltips correct

### Final: 100% Coverage
- [ ] All 4 tiers passing
- [ ] All 48 civs validated
- [ ] All 1,200 cards verified
- [ ] Complete test coverage report generated

---

## Key Resources

| What | Where | Why |
|------|-------|-----|
| Strategy overview | `VALIDATION_MASTER_PLAN.md` | Understand the full approach |
| Quick reference | `VALIDATION_QUICK_START.md` | One-command workflows |
| TIER 2 setup | `TIER2_EXECUTION_GUIDE.md` | Step-by-step scenario building |
| TIER 2 technical spec | `tools/validation/TIER2_SCENARIO_DESIGN.md` | Trigger specifications |
| TIER 4 checklist | `tools/validation/TIER4_SPOT_CHECKS.md` | What to watch for |
| Run validation | `python3 tools/validation/run_all_tiers.py` | Execute complete framework |
| Check progress | `python3 tools/validation/run_tier2_tests.py --check` | Track TIER 2 completion |

---

## Notes

- **No Breaking Changes**: Complete validation framework added without modifying existing mod code
- **Incremental Execution**: TIER 2 can be spread across multiple sessions (one civ per session possible)
- **Reversible**: All test logs and results go to `logs/` (git-ignored), original mod files unchanged
- **CI/CD Ready**: Framework can be integrated into automated testing pipeline
- **Regression Testing**: After first complete run, future validation = TIER 1 (10 min) + TIER 4 (30 min) = 40 min

---

## Questions or Issues?

- **TIER 1 failing?** → Check `validate_tier1_static.py` output
- **Need TIER 2 help?** → Read `TIER2_EXECUTION_GUIDE.md`
- **TIER 3 failing?** → Check civ doctrine in `game/ai/core/aiSetup.xs`
- **TIER 4 issues?** → See `TIER4_SPOT_CHECKS.md` troubleshooting section
- **Want overview?** → See `VALIDATION_MASTER_PLAN.md`
