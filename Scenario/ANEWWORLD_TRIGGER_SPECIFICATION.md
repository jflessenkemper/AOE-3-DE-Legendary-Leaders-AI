# ANEWWORLD Scenario - Trigger Specification

This document defines the 6 required triggers for the ANEWWORLD testing scenario to capture AI behavior metrics for all 48 civilizations.

## Trigger Configuration

All triggers should **log output to a specific location** that can be parsed by `tier2_scenario_runner.py` and `validate_tier3_comparison.py`.

### Logging Format

Each trigger should output to the game's debug log or trigger output stream with this format:
```
[METRIC_TYPE]: value1, value2, value3
```

Example:
```
[AGEUP]: First age-up: 8m 30s
[UNITS_TRAINED]: Infantry(12), Cavalry(8), Artillery(3)
[BUILDINGS]: House, Farm, Stable
[CARDS]: [Shipment1], [Shipment2], [Shipment3]
[TRADE_ROUTES]: Yes
[GAME_END]: Game ended at 10m 00s
```

---

## Trigger 1: Age-Up Detection

**Purpose:** Detect and log when each player ages up for the first time.

**Trigger Type:** Player Property Change

**Setup:**
1. Create a trigger for each player (1-48)
2. Condition: `Player {X} -> Age == 2` (or higher)
3. Action: Display message with timestamp
4. Message format: `Player {X}: First age-up: {elapsed_time}m {seconds}s`

**Alternative (using timer):**
1. Start a timer when game begins
2. Detect age change to Age 2
3. Log elapsed time when first triggered
4. Set flag to prevent duplicate logging

**Expected Output:**
```
[AGEUP]: First age-up: 8m 30s
```

---

## Trigger 2: Unit Training Detection

**Purpose:** Track and count units trained by AI player during game.

**Setup:**
1. Create triggers to detect unit creation
2. For each civvic, track these unit types:
   - Infantry units (Musketeers, Pikemen, etc.)
   - Cavalry units (Dragoons, Cuirassiers, etc.)
   - Artillery units (Cannons, Mortars, etc.)

**Method:**
1. Use "Object Created" condition for major unit types
2. Increment counters per unit class
3. Output at game end or at intervals (e.g., every 2 minutes)

**Expected Output:**
```
[UNITS_TRAINED]: Infantry(12), Cavalry(8), Artillery(3)
```

**Note:** Count should reflect actual units trained, not home city shipments.

---

## Trigger 3: Building Placement Logging

**Purpose:** Track which buildings the AI constructs.

**Setup:**
1. Detect building creation via "Object Created" condition
2. Filter for player's buildings only
3. Log building names/types to output
4. Output at game end

**Expected Output:**
```
[BUILDINGS]: House, Farm, Stable, Barracks
```

---

## Trigger 4: Card Shipment Detection

**Purpose:** Validate that each card shipment comes from the civ's deck.

**Setup:**
1. Monitor for "Card Shipment" or "Technology Researched" events
2. Log each shipment used
3. Validate against decks_anw.json[civ_token]
4. Output all cards used during game

**Expected Output:**
```
[CARDS]: [Card1], [Card2], [Card3]
```

**Post-Processing:** validate_tier3_comparison.py will validate these against decks_anw.json

---

## Trigger 5: Trade Route Detection

**Purpose:** Log if trade routes were established.

**Setup:**
1. Monitor for "Trade Route Established" or similar condition
2. Simple boolean: Yes/No
3. Output at game end

**Expected Output:**
```
[TRADE_ROUTES]: Yes
```

---

## Trigger 6: Game End Detection

**Purpose:** Mark end of game and force log flush.

**Setup:**
1. Trigger when timer reaches 10 minutes (game end time limit)
2. OR trigger when game ends via victory/defeat
3. Output final timestamp and "Game ended" marker

**Expected Output:**
```
[GAME_END]: Game ended at 10m 00s
```

---

## Implementation Steps

1. Open ANEWWORLD.age3Yscn in Scenario Editor
2. For each of the 6 triggers above:
   - Configure conditions and actions
   - Set logging output format per specification
   - Test with one civ first
3. Ensure all 48 players can be monitored
4. Set game length to 10 minutes
5. Save scenario

## Log Output Location

Logs should be written to:
```
./logs/tier2/{CIV_TOKEN}_scenario.log
```

Format: Plain text with [METRIC_TYPE] prefixed lines

## Testing the Trigger Setup

Once triggers are configured:
```bash
python3 tools/validation/tier2_scenario_runner.py
```

This will:
1. Load ANEWWORLD.age3Yscn
2. Detect trigger configuration
3. Run scenario for all 48 civs
4. Collect logs
5. Output TIER2_SUMMARY.json

Then validate with:
```bash
python3 tools/validation/validate_tier3_comparison.py --logs ./logs/tier2
```

This will compare observed behavior against XS doctrines.

## Troubleshooting

**"Has triggers: False" warning:**
- Triggers aren't being detected by the analyzer
- Try adding a dummy trigger to confirm detection works
- Check trigger output is being logged

**Missing log files:**
- Ensure game is actually running (not crashing)
- Check logs directory has write permissions
- Verify trigger actions are actually outputting

**Invalid card references:**
- Ensure card names in triggers match exactly those in data/cards.json
- Double-check spelling and casing
