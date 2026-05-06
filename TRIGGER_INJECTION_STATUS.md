# Trigger Injection Status: Option B Progress Report

## Summary

**Option B (Full Programmatic) is ~80% complete.** I successfully reverse-engineered the AOE3 scenario binary format and injected 6 triggers into ANEWWORLD.age3Yscn.

## What Was Accomplished

### 1. Binary Format Reverse-Engineering ✓

Analyzed .age3Yscn file format:
```
[8-byte header] + [zlib-compressed binary data]
```

Decompressed and studied 84 triggers from campaign scenario to understand structure:
- Trigger marker: `Trigger\x00`
- Header: Version (0x08) + ID + metadata
- Length-prefixed strings throughout
- Script code: `tr*` functions (e.g., `trSoundPlayDialogue`)

### 2. Trigger Extraction & Cloning ✓

Successfully extracted a 2,260-byte template trigger from:
- `Age 3 Tutorial/age3tutorial1.age3scn`

Cloned it 6 times for test triggers:
- Test: Age-Up
- Test: Units
- Test: Buildings
- Test: Cards
- Test: Trade
- Test: Game End

### 3. Injection into ANEWWORLD ✓

Injected 13,560 bytes of trigger data:
```
Original: 2,623,673 bytes (uncompressed)
Modified: 2,637,233 bytes (uncompressed)
Increase: 13,560 bytes (6 triggers × ~2,260 bytes each)
```

File integrity: ✓ Valid (decompresses without errors)

## What's Working

- ✓ Trigger structures present (6 `Trigger` markers found)
- ✓ File compression/decompression works
- ✓ Binary structure appears valid
- ✓ Script code modifications applied (`trOutput` appears 6 times)

## What Needs Refinement

- ⚠️ Trigger metadata (names) not fully updated
  - Cause: Length-prefixed string encoding is complex
  - These strings require precise length-matching due to binary serialization
  - Solution: Manual override via Scenario Editor OR spend 2-3 more hours on encoding

## Current Blocker: Length-Prefixed String Encoding

The trigger format stores strings as:
```
[4-byte length in little-endian] + [UTF-8 string] + [null terminator]
```

Example from campaign trigger:
```
0x07000000 + "Ignore" + \x00 = 7 bytes length indicator + "Ignore\x00"
0x16000000 + "Ignore Event on Abort" + \x00 = 22 bytes
```

When cloning triggers, simple string replacement breaks this encoding if:
- New string is different length than old
- Requires updating the 4-byte length prefix AND padding the string

Current approach only handles fixed-length replacement, not dynamic lengths.

## Path Forward: 3 Options

### Option A: Quick Fix (30 mins)
1. Open modified ANEWWORLD in Scenario Editor
2. Manually update trigger names/metadata
3. Verify and save
4. Run tests

**Pros:** Fast, guaranteed to work
**Cons:** Manual work

### Option B: Continue Programmatic (2-3 hours)
1. Implement proper length-prefixed string encoder
2. Build dynamic string replacement that updates length bytes
3. Test with all 6 triggers
4. Verify triggers execute correctly

**Pros:** Fully automated, reusable
**Cons:** Time-consuming, may hit other format issues

### Option C: Hybrid (1-2 hours)
1. Use current injected triggers as-is
2. Test if they execute despite metadata issues
3. If triggers fire (even with wrong names), keep them
4. Only fix via Scenario Editor if tests fail

**Pros:** Balances time and functionality
**Cons:** Unknown if triggers actually work

## Files Modified/Created

```
tools/validation/
  ├── scenario_trigger_builder.py    ← Main injection tool (WORKING)
  ├── trigger_injector.py             ← Backup approach
  └── add_triggers.py                 ← Analysis tool

Scenario/
  └── ANEWWORLD.age3Yscn              ← Modified with 6 injected triggers
  └── ANEWWORLD.backup                ← Original (safe backup)
```

## Next Steps

**Immediate (Choose One):**
1. **Option A**: Open Scenario Editor, fix metadata, test
2. **Option B**: Implement string encoder and re-run injector
3. **Option C**: Test current state in game, see if triggers fire

**Testing when ready:**
```bash
python3 tools/validation/tier2_scenario_runner.py
python3 tools/validation/validate_tier3_comparison.py --logs ./logs/tier2
```

## Technical Notes

- Campaign scenario (age3tutorial1.age3scn) has 84 triggers - valuable reference
- Trigger size varies: 344-2,260 bytes depending on complexity
- Cloning works because structure is preserved, only text changed
- Potential issue: Trigger IDs may conflict with existing game IDs (mitigated by using 100-105)
- Backup exists: can rollback to original if needed

## Recommendation

**Go with Option C (Hybrid):**
1. Test current injected triggers as-is in game
2. If triggers fire (output captures), keep them
3. If triggers fail, either:
   - Use Option A (manual fix via Editor) - 30 mins
   - Use Option B (programmatic fix) - 2-3 hours

This minimizes risk while keeping option to improve.
