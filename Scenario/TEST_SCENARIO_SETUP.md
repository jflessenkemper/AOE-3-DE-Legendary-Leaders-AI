# Legendary Leaders AI Test Scenario

The `.age3Yscn` file in this folder is a binary AoE3DE scenario file, so it is not practical to author or review safely with normal repo tools. The reliable workflow is to edit it in the in-game Scenario Editor and keep this file as the source of truth for what the test map should contain.

## Goal

Build one small repeatable scenario that verifies the current mod behavior:

- ordinary land units surrender at low health
- elite units do not auto-surrender
- nearby elite support prevents ordinary units from surrendering
- surrendered units walk to the enemy prison point
- the prison point is the first Town Center or main military shipment drop point
- only the original owner's explorer can reclaim prisoners
- AI assault shape keeps regular units in front, elites behind, explorer behind both
- if the AI explorer dies, the elite line disengages

## Recommended Map Setup

- Map size: small
- Terrain: flat, open, minimal obstacles
- Trade route: none
- Native settlements: none
- Treasures: none
- Starting resources: high enough to ignore economy during testing
- Player 1: human
- Player 2: AI

## Core Layout

Use three lanes across the same scenario so one load can test several behaviors.

### Lane A: Human Prison Test

- Put Player 1 Town Center on the west side.
- Put Player 2 Town Center on the east side.
- Place one Player 1 explorer near the Player 1 Town Center.
- Place one Player 2 explorer near the Player 2 Town Center.
- Place 8 ordinary Player 1 land units in the center at roughly 15% health.
- Place 8 ordinary Player 2 land units opposite them at full health.

Expected result:

- when combat starts, damaged ordinary Player 1 units can surrender at about 10% health
- surrendered Player 1 units should route toward the Player 2 Town Center area
- once they arrive, they should remain held there instead of rejoining combat
- moving the Player 1 explorer into the prison area should reclaim them

### Lane B: Elite Protection Test

- Duplicate Lane A slightly north of center.
- Add 2 known elite Player 1 units close to the damaged ordinary Player 1 group.
- Keep the rest of the setup the same.

Expected result:

- ordinary Player 1 units should not auto-surrender while their elite support is nearby
- the elite units themselves should not auto-surrender
- after you manually kill or move the elite support away, ordinary units should become eligible to surrender again

### Lane C: AI Formation and Explorer Test

- Place a larger Player 2 force south of center:
- 12 ordinary land units
- 4 elite units
- 1 explorer
- Place a smaller but durable Player 1 defending force nearby.
- Give the AI enough space to form up before first contact.

Expected result:

- regular AI units should advance as the first line
- elite AI units should trail as the second line
- the AI explorer should remain behind the fighting line
- if you kill the AI explorer during the attack, the elite line should disengage

## Recommended Unit Choice

Pick one civ pair you can identify quickly in the editor and use one clearly ordinary unit plus one clearly elite unit from the README tables.

Safe pattern:

- ordinary unit: a common infantry or cavalry unit that is not listed as elite for that nation
- elite unit: a unit explicitly listed in the README elite column for that nation

If you want the cleanest first pass, use only one nation pair for the whole scenario and duplicate the same test geometry in all three lanes.

## Editor Steps

1. Open `Scenario/Legendary Leaders Test.age3Yscn` in the AoE3DE Scenario Editor.
2. Set Player 1 to human and Player 2 to AI.
3. Place one Town Center for each player first. This matters because prison routing falls back to the first Town Center when no better shipment drop building is available.
4. Place explorers before placing combat groups so reclaim tests are easy to run.
5. Build the three lanes above with wide spacing so tests do not interfere with each other.
6. Lower the health of the surrender-test units so they reach the threshold almost immediately.
7. Save the scenario and run it with the mod enabled.

## Fast Trigger Ideas

If you want to make repeated testing faster in the editor, add these optional triggers:

- Intro message trigger that labels each lane.
- One-button unit heal trigger to reset a lane without rebuilding it.
- One-button respawn trigger for each lane.
- Explorer teleport trigger that moves the original owner's explorer into the prison radius.
- AI explorer kill trigger for the elite-retreat test.

## Pass Checklist

- Lane A: damaged ordinary units surrender and path to the enemy Town Center area.
- Lane A: surrendered units stay in custody when they arrive.
- Lane A: the original owner's explorer reclaims them.
- Lane B: nearby elite support blocks ordinary-unit surrender.
- Lane B: elite units do not auto-surrender.
- Lane C: AI regulars lead, elites follow, explorer stays behind.
- Lane C: killing the AI explorer causes the elite line to back off.

## Limits

- This repo can store the scenario file, but it cannot reliably perform structured edits to `.age3Yscn` content from text tools.
- If you want automation beyond this, the viable next step is to build the scenario in the in-game editor and then keep a written spec plus screenshots in the repo.

## Map Picker Notes

- `Legendary Leaders Test.age3Yscn` is the Custom Maps or Scenario version and should appear in the in-game `Custom Maps` list.
- `RandMaps/Legendary Leaders Test.xs` is the random-map version and should appear in the Skirmish picker under the `Legendary Leaders Test Maps` set.
- If the scenario entry itself still shows as `Unknown`, the remaining metadata is inside the binary `.age3Yscn` payload and must be refreshed by opening and re-saving that scenario in the AoE3DE Scenario Editor.