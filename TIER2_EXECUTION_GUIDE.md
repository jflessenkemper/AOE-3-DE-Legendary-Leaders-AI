# TIER 2 Execution Guide

This guide explains how to run the automated TIER 2 scenario tests for all 48 civilizations.

## Overview

**TIER 2** validates AI behavior by running actual gameplay in the ANEWWORLD scenario and capturing test data:

```
Configure Triggers in Scenario
        ↓
Run scenario for all 48 civs
        ↓
Capture trigger logs
        ↓
Parse & validate with TIER 3
```

**Timeline:**
- Scenario trigger setup: 2-3 hours (manual in Scenario Editor)
- Test execution: 4-8 hours (automated, ~5-10 min per civ × 48)
- Log parsing & validation: 10 minutes (automated)

---

## Prerequisites

1. **ANEWWORLD scenario created** ✓
   - Location: `~/.local/share/Steam/userdata/209941315/933110/remote/scenario@ANEWWORLD.age3Yscn`
   - Status: Already exists

2. **Triggers configured** ✗ (Still needed)
   - See `Scenario/ANEWWORLD_TRIGGER_SPECIFICATION.md`
   - 6 triggers required to capture: age-ups, units, buildings, cards, trade routes, game end

3. **Python environment** ✓
   - Installed: Python 3.9+
   - All validation scripts ready to use

---

## Step 1: Configure Triggers in ANEWWORLD Scenario

### Open the Scenario Editor

1. Launch Age of Empires III: Definitive Edition
2. Main Menu → Scenario Editor
3. Load: `Scenario/ANEWWORLD.age3Yscn`

### Add the 6 Required Triggers

Follow the specification in `Scenario/ANEWWORLD_TRIGGER_SPECIFICATION.md`:

1. **Trigger 1: Age-Up Detection**
   - Logs: `[AGEUP]: First age-up: 8m 30s`

2. **Trigger 2: Unit Training Detection**
   - Logs: `[UNITS_TRAINED]: Infantry(12), Cavalry(8), Artillery(3)`

3. **Trigger 3: Building Placement**
   - Logs: `[BUILDINGS]: House, Farm, Stable`

4. **Trigger 4: Card Shipment Detection**
   - Logs: `[CARDS]: [Card1], [Card2]`

5. **Trigger 5: Trade Route Detection**
   - Logs: `[TRADE_ROUTES]: Yes`

6. **Trigger 6: Game End Detection**
   - Logs: `[GAME_END]: Game ended at 10m 00s`

### Save and Test

1. Save scenario in editor
2. Run a test game with one civ
3. Verify all 6 triggers fire and output correctly
4. Logs should appear in `./logs/tier2/` directory

---

## Step 2: Run Automated Test Suite

### Generate and Execute Tests

```bash
cd /var/home/jflessenkemper/AOE-3-DE-A-New-World
python3 tools/validation/tier2_scenario_runner.py
```

This script:
- Analyzes the ANEWWORLD scenario
- Creates log placeholders for all 48 civs
- Generates a summary report

**Note:** Actual game execution requires running the scenario 48 times. The script above prepares templates. You can:
- Run games manually, one by one
- Or enhance the script to automate via wine/proton

---

## Step 3: Validate Results with TIER 3

Once test logs are populated with actual game data:

```bash
python3 tools/validation/validate_tier3_comparison.py --logs ./logs/tier2
```

**Output shows:**
- Each civ's test results
- Validation matrix (AgeUp, Units, Cards, Crash status)
- Overall pass/fail per civ
- Summary: X/48 civs passed

---

## File Locations

| File | Purpose |
|------|---------|
| `Scenario/ANEWWORLD.age3Yscn` | Main test scenario |
| `Scenario/ANEWWORLD_TRIGGER_SPECIFICATION.md` | Trigger requirements |
| `tools/validation/tier2_scenario_runner.py` | Test executor |
| `tools/validation/validate_tier3_comparison.py` | Validator |
| `logs/tier2/` | Test output logs |
| `logs/tier2/TIER2_SUMMARY.json` | Summary report |

---

## Validation Criteria

Each test passes if:

- ✓ Age-up timing: Within ±2 minutes of expected
- ✓ Unit composition: Within ±15% of expected
- ✓ Card validation: All used cards exist in decks_anw.json[civ]
- ✓ No crash: Game runs full 10 minutes

**Pass rate target:** 100% of 48 civs

---

## Next Steps

After TIER 2 passes:
1. Run TIER 3 validation
2. Run TIER 4 manual spot checks

---

## Questions?

See `Scenario/ANEWWORLD_TRIGGER_SPECIFICATION.md` for detailed trigger setup instructions.
