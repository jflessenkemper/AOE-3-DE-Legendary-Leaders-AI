# TIER 2: Doctrine Validator Scenario Design

## Overview
Custom AOE3 scenario that tests all 48 civs' AI behavior against documented doctrines.
**Goal:** Run 10-minute games per civ and capture trigger outputs proving AI behaves as documented.

---

## Scenario Architecture

### Map Setup
- **Size:** Small (2v1 or 1v1 format for speed)
- **Opponents:** 48 Player slots (one per civ) vs neutral AI
- **Starting:** Standard TC start, fixed resources
- **Speed:** Fast

### Trigger System

#### 1. Age-Up Detection
```
Trigger: "On Research Finished"
Condition: Tech is Age upgrade
Action: Log "{CivName} aged up to {Age} at {GameTime}"
```

#### 2. Unit Training Detection
```
Trigger: "On Unit Created"
Condition: Unit in [Infantry, Cavalry, Artillery, Native]
Action: Log "{CivName} trained {UnitType}"
       Increment: TrainedUnits[CivName][UnitType]++
```

#### 3. Building Placement Detection
```
Trigger: "On Building Created"
Condition: Building in [House, Mill, Barracks, Stable, etc.]
Action: Log "{CivName} built {BuildingType}"
       Increment: Buildings[CivName][BuildingType]++
```

#### 4. Card Shipment Detection
```
Trigger: "On Card Used"
Condition: Any shipment card
Action: Log "{CivName} used card {CardName}"
       Validate: CardName in decks_anw.json[CivName]
```

#### 5. Trade Route Detection
```
Trigger: "On Trade Route Created"
Action: Log "{CivName} activated trade routes"
```

#### 6. Game End Detection
```
Trigger: "On Timer (10 minutes)"
Action: Dump all counters to log file

Trigger: "On Game End" (early)
Action: Log "{CivName} ended early: {Reason}"
```

### Log Output Format
```
DOCTRINE VALIDATOR TEST LOG
Player: [CivName] ([CivToken])
Time: [GameStartTime]
─────────────────────────────────
[Time] AGE_UP: Colonial Age
[Time] TRAIN: Infantry x3
[Time] TRAIN: Cavalry x2
[Time] BUILD: Barracks
[Time] CARD: [CardName]
[Time] TRADE_ROUTE: activated
─────────────────────────────────
SUMMARY:
- First age-up: 8m 23s
- Units trained: Infantry(8), Cavalry(5), Artillery(2)
- Buildings: Barracks, Stable, House
- Trade routes: Yes
- Cards: [Card1], [Card2], [Card3]
```

---

## Execution

### Setup (One-time)
1. Create scenario in AOE3 DE editor: 2-3 hours
2. Build trigger suite: 1-2 hours
3. **Total: 3-4 hours**

### Testing (Per run)
1. Load scenario
2. Set player to test civ
3. Run 10 minutes
4. Export trigger log
5. Parse and compare: 30 min for all 48

**Total per cycle: ~5 hours (4.5 game hours + 0.5 parse)**

---

## Validation Matrix

After running all 48 tests:

| Civ | XS Doctrine | Expected | Observed | Match |
|-----|-------------|----------|----------|-------|
| ANWBritish | Infantry(0.4) | 40-50% Inf | 42% | ✓ |
| ANWFrench | Cavalry(0.3) | 30-40% Cav | 35% | ✓ |
| ANWRussians | Rusher(0.8) | Age-up 8-9m | 8m 15s | ✓ |

**Pass Criteria:**
- Age-up within ±2 minutes
- Unit composition within ±15% of expected
- Cards all from decks_anw.json[civ]
- No crashes

---

## Success Criteria

✓ All 48 civs tested
✓ No crashes/soft-locks
✓ Age-up timing ±2 min
✓ Unit compositions ±15%
✓ 100% card validation
✓ Comparison matrix PASS/FAIL per civ
