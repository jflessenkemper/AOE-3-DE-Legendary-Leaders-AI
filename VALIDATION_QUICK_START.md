# A New World Mod: Complete Validation Quick Start

## 100% Test Coverage in 5-6 Hours

This document provides the fastest path to complete mod validation using the 4-tier framework.

---

## What Gets Tested

✓ All 48 civilizations  
✓ All 1,200 deck cards (25 per civ)  
✓ All AI doctrines and playstyles  
✓ Game stability and crash detection  
✓ UI/UX and visual correctness  
✓ Card validity and historical accuracy  

---

## Quick Reference

### Current Status
- **TIER 1** (Static): ✓ **COMPLETE** (10 minutes)
- **TIER 2** (Gameplay): ⚠ Ready to build
- **TIER 3** (Automated): Ready to run
- **TIER 4** (Manual): Ready to execute

### Time Breakdown

| Tier | Focus | Time | Status |
|------|-------|------|--------|
| 1 | Static file validation | 10 min | ✓ Done |
| 2 | Gameplay scenario building | 3-4 hrs | To do |
| 2 | Run 48 gameplay tests | 4-6 hrs | To do |
| 3 | Automated comparison | 30 min | Ready |
| 4 | Manual spot checks | 30 min | Ready |
| **TOTAL** | **100% coverage** | **~8-10 hrs** | |

---

## One-Command Workflows

### Run TIER 1 only (quick sanity check)
```bash
python3 tools/validation/validate_tier1_static.py
```
**Time: 10 seconds | Status: ✓ all pass**

### Initialize TIER 2 and check status
```bash
python3 tools/validation/run_tier2_tests.py --init
python3 tools/validation/run_tier2_tests.py --summary
```

### Run full validation (auto-pauses for TIER 2)
```bash
python3 tools/validation/run_all_tiers.py
```
**Runs TIER 1 → initializes TIER 2 → pauses for 48 gameplay tests → ready for TIER 3**

### Check validation coverage
```bash
python3 tools/validation/run_all_tiers.py --report
```

---

## Step-by-Step: Full Validation (8-10 hours)

### Phase 1: Static Validation (10 minutes)
```bash
# TIER 1: Validate all static files
python3 tools/validation/validate_tier1_static.py
```
Expected: ✓ All 7 tests pass

### Phase 2: Scenario Building (3-4 hours, one-time)
```bash
# Initialize log directories
python3 tools/validation/run_tier2_tests.py --init

# Follow the scenario building guide
open TIER2_EXECUTION_GUIDE.md
```

Then in AOE3 Scenario Editor:
1. Create scenario: `ANW_Doctrine_Validator`
2. Add 6 triggers (see guide)
3. Save to `maps/ANW_Doctrine_Validator.scn`

### Phase 3: Gameplay Tests (4-6 hours)
```bash
# Run 48 civ tests in AOE3 (follow TIER2_EXECUTION_GUIDE.md)
# For each civ:
#   - Load scenario
#   - Set computer to that civ
#   - Play 10 minutes
#   - Export log to logs/tier2/{CivName}_scenario.log
```

Track progress:
```bash
python3 tools/validation/run_tier2_tests.py --check
```

### Phase 4: Automated Validation (30 minutes)
```bash
# TIER 3: Validate all gameplay logs
python3 tools/validation/run_tier2_tests.py --validate
```
Expected: ✓ All 48 civs pass (age-up timing, unit composition, cards, stability)

### Phase 5: Manual Spot Checks (30 minutes)
```bash
# TIER 4: Play 3 representative games
# Open: tools/validation/TIER4_SPOT_CHECKS.md
```

Games to play:
- Game 1: Russians vs Dutch (10 min)
- Game 2: British vs French (10 min)
- Game 3: Ottomans vs Peruvians (10 min)

Watch for: No crashes, correct units, valid cards, clean UI

### Final: Generate Coverage Report
```bash
python3 tools/validation/run_all_tiers.py --report
```

Expected:
```
Total Coverage: 100%
✓ 100% FLAWLESS TEST COVERAGE ACHIEVED
```

---

## File Reference

### Main Documentation
- `VALIDATION_MASTER_PLAN.md` — Complete overview of 4-tier strategy
- `TIER2_EXECUTION_GUIDE.md` — Detailed TIER 2 setup and execution guide
- `tools/validation/TIER2_SCENARIO_DESIGN.md` — Full technical specification for scenario
- `tools/validation/TIER4_SPOT_CHECKS.md` — Manual testing checklist

### Python Tools
- `tools/validation/validate_tier1_static.py` — TIER 1: Static validator (7 tests)
- `tools/validation/run_tier2_tests.py` — TIER 2: Test orchestrator
- `tools/validation/validate_tier3_gameplay.py` — TIER 3: Gameplay comparison
- `tools/validation/run_all_tiers.py` — All-tiers orchestrator

### Data Files
- `data/decks_anw.json` — All 48 curated decks (25 cards each)
- `data/civmods.xml` — Civilization definitions
- `data/cards.json` — Complete card database
- `game/ai/core/aiSetup.xs` — AI doctrine traits

### Log Directories
- `logs/tier2/` — Scenario log files (one per civ)
- `logs/tier2_results/` — TIER 3 validation results

---

## Success Criteria

### TIER 1: ✓ PASS
- All 7 static tests pass
- No broken files, XML issues, or card references
- All 48 civs have homecity + personality files

### TIER 2: ✓ PASS
- 48 gameplay tests complete without crashes
- Trigger logs successfully exported

### TIER 3: ✓ PASS
- All 48 civs match doctrine baseline
- Age-up timing: ±2 minutes tolerance
- Unit composition: ±20% variance acceptable
- All cards from deck reference
- No game crashes

### TIER 4: ✓ PASS
- 3 manual games complete
- No visual glitches, crashes, or UI corruption
- Unit compositions follow doctrine
- Cards are from deck reference
- Leader names and tooltips correct

**Final: 100% coverage = all 4 tiers PASS**

---

## Troubleshooting

### TIER 1 fails
→ Check `tools/validation/validate_tier1_static.py` output
→ Usually: missing file or invalid card reference
→ Fix: Run TIER 1 again to confirm

### TIER 2 scenario doesn't save
→ Check AOE3 is in Scenario Editor mode
→ Verify trigger syntax
→ Save to `maps/ANW_Doctrine_Validator.scn` explicitly

### TIER 3 finds invalid cards
→ Check `data/decks_anw.json` for that civ
→ Run TIER 1 to validate all card IDs
→ Fix deck composition and re-test

### TIER 4 shows visual glitches
→ Check homecity file for that civ
→ Verify portrait/flag files exist
→ Run TIER 1 to check file integrity

---

## Continuous Integration

For future changes, run quick regression test:
```bash
# 10 min: TIER 1 static check
python3 tools/validation/validate_tier1_static.py

# 30 min: TIER 4 spot checks (play 3 manual games)
# Follow: tools/validation/TIER4_SPOT_CHECKS.md
```
= **40 minutes for confidence that nothing broke**

---

## Next Steps

1. **Now:** Run TIER 1
   ```bash
   python3 tools/validation/validate_tier1_static.py
   ```

2. **Next:** Read TIER 2 guide
   ```bash
   open TIER2_EXECUTION_GUIDE.md
   ```

3. **Then:** Build scenario in AOE3 (3-4 hours)

4. **Then:** Run 48 gameplay tests (4-6 hours)

5. **Finally:** Run TIER 3 + TIER 4 (1 hour)

---

## Questions?

- TIER 1 issue? → See `validate_tier1_static.py` output
- TIER 2 setup? → See `TIER2_EXECUTION_GUIDE.md`
- TIER 2 technical spec? → See `tools/validation/TIER2_SCENARIO_DESIGN.md`
- TIER 3 validation? → See `tools/validation/validate_tier3_gameplay.py`
- TIER 4 checklist? → See `tools/validation/TIER4_SPOT_CHECKS.md`
- Overview? → See `VALIDATION_MASTER_PLAN.md`
