# TIER 4: MANUAL INTEGRATION SPOT CHECKS

**Purpose**: Quick smoke tests to catch what automation missed.
**Time**: ~30 minutes (3x 10-minute games + manual observation)
**Coverage**: Spot check 6 representative civs across different doctrines

---

## Pre-Game Setup Checklist

### Installation
- [ ] Mod folder extracted to: `%USERPROFILE%\Games\Age of Empires 3 DE\<steamID>\mods\local\A New World`
- [ ] Mod enabled in-game: Home City → Mods → Local Mods → "A New World" → Enable
- [ ] Game restarted after mod enable

### Expected Results
- [ ] All 48 civs appear in civ picker (no crashes)
- [ ] No duplicate civs
- [ ] Leader portraits match civ names (e.g., Elizabeth I for British)

---

## Game 1: Rush Doctrine Test
**Civs to test**: ANWRussians, ANWSwedes, ANWJapanese

Load: Random map, Tiny, Moderate difficulty vs AI

### Checklist
- [ ] Game launches without crash
- [ ] First age-up by 8 minutes (rushers should age early)
- [ ] Multiple infantry/cavalry units in first 10 minutes
- [ ] Visible military presence (multiple barracks/stables)
- [ ] Cards played: Check in scoreboard → verify cards exist in deck reference

### Expected Behavior
| Civ | Expected | Verify |
|---|---|---|
| ANWRussians | Infantry focused, early age-up | 60%+ infantry, age ≤8min |
| ANWSwedes | Cavalry focused, gunpowder | 40%+ cavalry, artillery present |
| ANWJapanese | Samurai units | Samurai/unique units visible |

---

## Game 2: Boom Doctrine Test
**Civs to test**: ANWBritish, ANWFrench, ANWDutch

Load: Random map, Tiny, Moderate difficulty vs AI

### Checklist
- [ ] Game launches without crash
- [ ] Later age-up (9-10 minutes)
- [ ] Economic buildings prominent (mills, markets)
- [ ] Gradual military buildup (not aggressive early)
- [ ] Trade posts/routes if applicable (Dutch should have one)

### Expected Behavior
| Civ | Expected | Verify |
|---|---|---|
| ANWBritish | Infantry + ranged mix | Rangers visible, balanced army |
| ANWFrench | Cavalry heavy, fortified | Cuirassier/cavalry units |
| ANWDutch | Economic + naval | Trade posts, ships/fishing |

---

## Game 3: Hybrid/Unique Doctrine Test
**Civs to test**: ANWOttomans, ANWPeruvians, ANWHaitians

Load: Random map, Tiny, Moderate difficulty vs AI

### Checklist
- [ ] Game launches without crash
- [ ] Unique units/cards actually play (not just generic)
- [ ] Doctrine-specific buildings (mosques for Ottomans, etc.)
- [ ] Cards match their documented playstyles

### Expected Behavior
| Civ | Expected | Verify |
|---|---|---|
| ANWOttomans | Grenadiers, siege artillery | Unique Ottoman cards visible |
| ANWPeruvians | Guerrilla/mountain | Alpacas, unique cards play |
| ANWHaitians | Guerrilla, uprising units | Unique units train, cards match |

---

## Visual/UI Spot Checks

During all 3 games, watch for:

### Tooltips & Labels
- [ ] Unit tooltips display correctly (no truncation/corruption)
- [ ] Building names match UI
- [ ] Card names match deck reference
- [ ] Leader name in scoreboard matches civ name

### No Glitches
- [ ] No visual artifacts (missing textures, broken models)
- [ ] No UI overlaps or text cutoff
- [ ] Flag/portrait icons load correctly
- [ ] Civ colors render properly

### Sound & Audio
- [ ] No audio crashes/stuttering
- [ ] Appropriate sound for units/buildings
- [ ] Chat/voice lines don't spam or repeat

---

## Scoreboard Verification

End each game and check scoreboard:

- [ ] All civ names spelled correctly
- [ ] Leader names match HTML reference (e.g., "Elizabeth I" for British)
- [ ] Resources tracked correctly
- [ ] Score calculations sensible
- [ ] Card shipments logged correctly

---

## Post-Game Card Deck Spot Check

For each game, verify cards played match deck reference:

```bash
# Run this after each game:
python3 tools/validation/validate_tier1_static.py
```

Should show:
- ✓ All deck cards reference valid card IDs
- ✓ All 48 decks have exactly 25 cards

---

## Crash/Soft-Lock Detection

If the game crashes or soft-locks during a spot check:

1. **Document the moment**: What was happening? (age-up, unit training, card play?)
2. **Note the civ**: Which civ was playing?
3. **Check game logs**: `My Documents\My Games\Age of Empires 3 DE\Age3Log.txt`
4. **Search for errors**: Look for stack traces or "Fatal error"
5. **Report**: Create issue with:
   - Civ name
   - Timestamp of crash
   - Error message (if any)
   - What was happening in-game

---

## Final Verdict

### PASS Criteria
✓ All 3 games complete 10 minutes without crash
✓ All civs appear and are selectable
✓ Unit compositions match doctrine (within reason)
✓ Cards played are from deck reference
✓ No visual glitches or UI corruption
✓ Tooltips/labels display correctly

### FAIL Criteria
✗ Game crashes or soft-locks
✗ Missing civs in picker
✗ Visual glitches/corruption
✗ Tooltips show wrong/corrupted text
✗ Invalid cards played (not in deck reference)

---

## Quick Checklist (TL;DR)

Run 3x quick 10-minute games:
1. [ ] Russian vs Dutch (Rush vs Boom)
2. [ ] British vs French (Economic)
3. [ ] Ottoman vs Peruvian (Unique)

Watch for:
- [ ] No crashes
- [ ] Correct unit compositions
- [ ] Cards from deck reference only
- [ ] Clean UI/tooltips
- [ ] Leader names match

If all checks pass: **✓ TIER 4 COMPLETE**

---

## Notes

- These are *spot checks*, not comprehensive tests
- Each game is only 10 minutes (not a full match)
- Focus on behavior that matches TIERS 1-3 results
- If a civ fails here, re-run TIER 1 static validation first
- Use these games to catch what automated testing missed
