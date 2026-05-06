# TIER 2: EXECUTION GUIDE

## Overview
TIER 2 tests all 48 civilizations' AI behavior by running scenario games and logging their actions.
Once logs are collected, TIER 3 automatically validates behavior against documented doctrines.

**Time Investment:**
- Scenario building (one-time): 3-4 hours
- Gameplay tests (48 civs × 5-8 min): 4-6 hours
- **Total: 7-10 hours** (can be spread across multiple sessions)

---

## Step 1: Build the Scenario (3-4 hours, one-time)

### Prerequisites
- Age of Empires 3 DE installed with Scenario Editor
- `tools/validation/TIER2_SCENARIO_DESIGN.md` (complete technical spec)

### Process
1. Open **Scenario Editor**
2. Create new scenario → Random Map → Tiny size
3. Name it: `ANW_Doctrine_Validator`
4. Add 48 player slots (one per civ)
5. Configure 6 triggers (see TIER2_SCENARIO_DESIGN.md for full details):
   - Age-up detection
   - Unit training tracking
   - Building placement logging
   - Card shipment validation
   - Trade route activation
   - Game timer + crash detection
6. Set log output format to `logs/tier2/{CivName}_scenario.log`
7. Save as: `maps/ANW_Doctrine_Validator.scn`

**Reference:** Full trigger specifications in `tools/validation/TIER2_SCENARIO_DESIGN.md`

---

## Step 2: Run 48 Gameplay Tests (4-6 hours, can be parallelized)

For each civilization:

1. **Load scenario** in AOE3
2. **Select civ**: Set computer player to that civ
3. **Start game**: Tiny difficulty, 10 minutes
4. **Watch**: Let AI play; trigger logs run automatically
5. **Export log**: Once game ends, trigger system dumps log file to `logs/tier2/{CivName}_scenario.log`
6. **Next civ**: Repeat

### Time per civ: 5-8 minutes (including game + log export)
### Total for all 48: ~4-6 hours

**Optimization Tips:**
- Run on fast computer (reduces per-game time)
- Can batch multiple civs in one session
- Logs auto-save; no manual intervention needed
- Keep track of completed civs using: `python3 tools/validation/run_tier2_tests.py --summary`

---

## Step 3: Verify Logs and Run TIER 3 (30 minutes)

### Check log collection
```bash
python3 tools/validation/run_tier2_tests.py --check
```

Should show:
```
✓ Complete logs: 48/48
```

### Run TIER 3 validation
```bash
python3 tools/validation/run_tier2_tests.py --validate
```

This will:
- Parse all 48 scenario logs
- Compare actual AI behavior vs doctrine baseline
- Generate per-civ verdict (PASS/FAIL)
- Save results to `logs/tier2_results/`

---

## Step 4: Interpret TIER 3 Results

### Expected Output
```
[VALIDATE] TIER 3 Comparison Matrix
================================================================================

✓ PASS: 46/48
✗ FAIL: 2/48

Failed civs:
  - ANWOttomans: unit_composition (expected Inf:0.4, got Inf:0.25)
  - ANWPeruvians: age_up_timing (expected 480s, got 680s)
```

### If all pass
→ Proceed to **TIER 4 manual spot checks**

### If any fail
1. Note the failed civs and failed tests
2. Check the specific issue:
   - **age_up_timing**: Adjust XS doctrine (btRushBoom) in `game/ai/core/aiSetup.xs`
   - **unit_composition**: Adjust unit bias in personality files
   - **card_validity**: Check `data/decks_anw.json` for invalid cards
   - **crash**: Check game logs for errors
3. Fix the issue
4. Re-run just that civ's test
5. Re-run TIER 3

---

## Helper Script Reference

### Initialize log directories
```bash
python3 tools/validation/run_tier2_tests.py --init
```

### Check log completion status
```bash
python3 tools/validation/run_tier2_tests.py --check
```

### Run TIER 3 validation on all logs
```bash
python3 tools/validation/run_tier2_tests.py --validate
```

### View execution summary
```bash
python3 tools/validation/run_tier2_tests.py --summary
```

---

## Log File Format

Each log file at `logs/tier2/{CivName}_scenario.log` contains:

```
AGE_UP;8:23;ANWBritish;Colonial Age
UNIT_TRAINED;5:12;ANWBritish;Musketeer
UNIT_TRAINED;5:45;ANWBritish;Musketeer
BUILD;6:30;ANWBritish;Barracks
BUILD;7:15;ANWBritish;House
CARD;8:50;ANWBritish;Royal Mint
TRADE;9:12;ANWBritish;active
END;10:00;ANWBritish;completed
```

**Format**: `EventType;Timestamp;CivName;Value;[Optional]`

The TIER 3 validator automatically parses this format.

---

## Troubleshooting

### "Log file not found"
→ Make sure game exported the log to correct path. Check AOE3 scenario trigger output settings.

### "Crash or soft-lock during test"
→ Check `My Documents/My Games/Age of Empires 3 DE/Age3Log.txt` for errors
→ Document the civ name and error message, report as issue

### "Card validation failed"
→ Check `data/decks_anw.json` for the civ; verify all cards exist in `data/cards.json`
→ Run TIER 1 validator to confirm: `python3 tools/validation/validate_tier1_static.py`

### "Unit composition doesn't match expected"
→ Check personality file for that civ: `game/ai/anw{civ}.personality`
→ Verify XS doctrine traits in `game/ai/core/aiSetup.xs`
→ May need to adjust unit bias values (btBiasCav, btBiasInf, etc.)

---

## Next: TIER 4 Manual Spot Checks

Once TIER 3 passes for all 48 civs:

```bash
python3 tools/validation/run_tier2_tests.py --summary
# Should show: ✓ TIER 2 EXECUTION COMPLETE
```

Then proceed to **TIER 4** (30 minutes):
- Play 3 manual games
- Spot-check UI, crashes, unit compositions
- Verify cards match deck reference

See: `tools/validation/TIER4_SPOT_CHECKS.md`

---

## Timeline Estimate

| Phase | Time | Notes |
|-------|------|-------|
| Scenario building | 3-4 hrs | One-time, can be done once |
| Gameplay tests | 4-6 hrs | 48 × 5-8 min per civ |
| TIER 3 validation | 30 min | Automated |
| **TIER 2 Total** | **~8-10 hrs** | Can spread across sessions |

After first run, future re-validation = TIER 1 (10 min) + TIER 4 (30 min) = 40 min

---

## Files Reference

| File | Purpose |
|------|---------|
| `tools/validation/TIER2_SCENARIO_DESIGN.md` | Full technical specification |
| `tools/validation/run_tier2_tests.py` | Helper script for test orchestration |
| `tools/validation/validate_tier3_gameplay.py` | Automated validator (runs on logs) |
| `maps/ANW_Doctrine_Validator.scn` | Scenario file (you create this) |
| `logs/tier2/` | Directory for scenario log files |
| `logs/tier2_results/` | TIER 3 validation results |
