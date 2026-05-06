# TIER 2: Gameplay Validation Scenario Design

## Overview

This document specifies the scenario structure needed to validate all 48 civs' AI behavior against their documented doctrines in ~5-6 hours total (5-8 min per civ).

## Scenario Architecture

### Name
`ANW Doctrine Validator`

### Map
- **Type**: Random map (any, small)
- **Size**: Tiny (fast games)
- **Players**: 2 (Computer AI + Neutral/Human observer)
- **Victory**: Conquest (disabled - we're testing AI behavior, not winning)
- **Game Speed**: Fast (or Normal)

### Initialization Rules

Run these at the start of the game via triggers:

```
EVENT: Game Start → TRIGGER: Initialize Validator
  ACTION: Clear all scores
  ACTION: Start game timer
  ACTION: Enable logging trigger group "AI_BEHAVIOR"
  ACTION: Output initial message to chat: "ANW Validator initialized for {CivName}"
```

## Trigger Suite

### 1. Age-Up Detection

```
EVENT: Player → Technology researched
CONDITION: Technology == Age UP (any feudal/castle/imperial)
ACTION: Log to chat: "[TIME] {PlayerName} aged up to Age {N}"
ACTION: Write to output file: "AGE_UP;{Time};{PlayerName};{Age}"
```

**Metrics extracted**: First age-up time per civ

---

### 2. Unit Training Detection

```
EVENT: Unit → Unit created/trained
ACTION: Log to chat: "[TIME] {PlayerName} trained {UnitType}"
ACTION: Count unit type and accumulate:
  - Infantry (Musketeer, Pikeman, Skirmisher, etc.)
  - Cavalry (Dragoon, Hussar, Lancer, etc.)
  - Artillery (Cannon, Mortar, etc.)
  - Native units
ACTION: Write to output file: "UNIT_TRAINED;{Time};{PlayerName};{UnitType}"
```

**Metrics extracted**: Unit composition by type (% Infantry, % Cavalry, etc.)

---

### 3. Building Placement Detection

```
EVENT: Building → Building completed
CONDITION: BuildingType != House (ignore housing)
ACTION: Log to chat: "[TIME] {PlayerName} built {BuildingType}"
ACTION: Count buildings by type:
  - Military buildings (Barracks, Stable, Artillery Foundry)
  - Economic buildings (Farm, Mill, Marketplace)
  - Special buildings (Factory, Trade Post, etc.)
ACTION: Write to output file: "BUILDING;{Time};{PlayerName};{BuildingType}"
```

**Metrics extracted**: Building order and priorities

---

### 4. Card Shipment Detection

```
EVENT: Card → Card played/shipment sent
ACTION: Log to chat: "[TIME] {PlayerName} played {CardName}"
ACTION: Extract card name from shipment
ACTION: Write to output file: "CARD;{Time};{PlayerName};{CardName};{Age}"
```

**Metrics extracted**: Card order and selection (validate against decks_anw.json)

---

### 5. Trade Route Activation

```
EVENT: Player → Trade post created OR Trade route activated
ACTION: Log to chat: "[TIME] {PlayerName} activated trade routes"
ACTION: Write to output file: "TRADE;{Time};{PlayerName};active"
```

**Metrics extracted**: Trade route timing (1 = present, 0 = absent)

---

### 6. Game Timer & Verdict

```
EVENT: Time elapsed == 10 minutes
ACTION: Stop AI
ACTION: Output final message: "Validator complete. See log file for details."
ACTION: Write to output file: "END;{TotalTime}"

EVENT: AI crashes or soft-locks
ACTION: Output: "ERROR;{PlayerName};crash_or_softlock"
ACTION: Mark test as FAILED
ACTION: End game
```

**Metrics extracted**: Completion status, total gameplay time

---

## Output Format

All trigger outputs write to a single log file: `age3log_validator_output.txt`

Format: `TYPE;TIMESTAMP;PLAYER;VALUE;[OPTIONAL]`

Example:
```
AGE_UP;00:47;ANWBritish;2
UNIT_TRAINED;01:15;ANWBritish;Musketeer
UNIT_TRAINED;01:22;ANWBritish;Musketeer
BUILDING;02:04;ANWBritish;Barracks
CARD;02:30;ANWBritish;Royal Mint;Exploration
TRADE;03:44;ANWBritish;active
UNIT_TRAINED;04:16;ANWBritish;Dragoon
END;10:00
```

---

## How to Build (Manual Steps in Scenario Editor)

1. Create new random map scenario, select Tiny size
2. Place 2 start positions: one for human observer, one for AI
3. Set Computer player to the target civ (rotates per test)
4. Add trigger group "AI_BEHAVIOR" with the 6 triggers above
5. Set game length: 10 minutes max (time elapsed trigger)
6. Enable logging: Scenario → Options → Log game events to file
7. Save as: `maps/ANW_Doctrine_Validator.scn`

---

## Execution Workflow (After scenario is built)

**For each of 48 civs:**

1. Load scenario in AOE3 DE
2. Open scenario editor → Set Computer player civ to [Civ N]
3. Play the game (10 minutes)
4. Export scenario output file
5. Run validation: `python3 tools/validation/validate_tier2_gameplay.py <output_file> [expected_doctrine]`
6. Compare metrics against doctrine baseline
7. Next civ

**Estimated time per civ**: 5-8 minutes (1-2 min gameplay + log parsing + comparison)

**Total: ~4-6 hours for all 48 civs**

---

## Validation Thresholds

The Python validator (TIER 2B) will compare actual behavior against doctrine baseline:

- **Age-up time**: Expected 6-10 min (rushers 6-8 min, boomers 8-10 min)
- **Unit composition**: Allow ±20% variance from doctrine biases
- **Building order**: Military buildings should appear before economic (for rushers)
- **Trade routes**: Should activate by minute 4-5 if btBiasTrade > 0.0
- **Card selection**: All cards played must be from decks_anw.json

---

## Success Criteria

All 48 civs pass if:
✓ Game runs 10 minutes without crash/soft-lock
✓ Age-up timing within expected range
✓ Unit composition ±20% of doctrine bias
✓ All cards played are in decks_anw.json
✓ Trade routes activated per doctrine

---

## Notes

- Scenario can be used repeatedly; just change the Computer player civ before each test
- Log file is overwritten each game; save/rename before next test
- This is the most time-efficient method because:
  - Single scenario template reused 48 times
  - Triggers automate all metric collection
  - Python validation script is fully automated
  - No manual observation needed
