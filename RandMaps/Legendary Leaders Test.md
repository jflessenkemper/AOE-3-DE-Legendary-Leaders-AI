# Legendary Leaders Test Map

This custom random map is a flat 1v1 test arena for fast validation of the current Legendary Leaders AI behavior.

## What It Gives You

- fixed west vs east spawns in 1v1
- very open battlefield with minimal terrain noise
- three dirt test lanes: north, center, south
- rich starting mines, hunts, cattle, and trees so you can field armies quickly
- extra neutral mines, hunts, and nuggets in each lane for repeated fights

## What To Test Here

- ordinary-unit surrender at low health
- elite units refusing to auto-surrender
- elite support preventing nearby ordinary units from surrendering
- prisoners routing back toward the enemy main Town Center / shipment-drop area
- explorer reclaim of imprisoned units
- AI attack order with regulars in front, elites behind, and explorer behind both
- elite disengage after the AI explorer dies

## Recommended Use

1. Start a 1v1 skirmish on this map with the mod enabled.
2. Pick one civ matchup you know well so you can identify ordinary vs elite units quickly.
3. Use the three lanes separately:
4. North lane for surrender and reclaim.
5. Center lane for elite-protection checks.
6. South lane for larger AI attack-shape checks.

## Limits

- This is a controlled skirmish map, not a hand-authored scenario.
- It does not pre-damage units or pre-place custom prisoner states.
- The undocumented trigger/debug surface is still too thin to claim a fully automated scenario-style test harness.