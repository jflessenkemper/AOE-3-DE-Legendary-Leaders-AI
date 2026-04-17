# Legendary Leaders Test Map

This custom random map is a flat 2v2 test arena for fast validation of the current Legendary Leaders AI behavior, especially when you want one allied AI and two opposing AIs on a clean battlefield.

## What It Gives You

- fixed team-based west vs east spawns in 2v2
- very open battlefield with minimal terrain noise
- three dirt test lanes: north, center, south
- rich starting mines, hunts, cattle, and trees so you can field armies quickly
- extra neutral mines, hunts, and nuggets in each lane for repeated fights
- allied starts share the west side, enemy starts share the east side, so flanks stay readable regardless of slot order

## What To Test Here

- ordinary-unit surrender at low health
- elite units refusing to auto-surrender
- elite support preventing nearby ordinary units from surrendering
- prisoners routing back toward the enemy main Town Center / shipment-drop area
- explorer reclaim of imprisoned units
- AI attack order with regulars in front, elites behind, and explorer behind both
- elite disengage after the AI explorer dies
- nation style differences in a more natural 2v2 flow instead of a pure duel

## Recommended Use

1. Start a 2v2 skirmish on this map with the mod enabled.
2. Use locked 2v2 teams with you and your allied AI on one team and the two opponents on the other.
3. Team 0 is placed on the west side and team 1 is placed on the east side, so slot order inside a team no longer matters.
4. Pick civs you want to compare for style, because the open layout makes army composition and attack rhythm easy to read.
5. Use the north and south lanes for flank pressure checks.
6. Use the center lane for elite-protection, surrender, and larger teamfight observations.

## Limits

- This is a controlled skirmish map, not a hand-authored scenario.
- The fixed 2v2 layout is tuned around exactly two teams of two; other player counts or uneven teams fall back to simpler placement.
- It does not pre-damage units or pre-place custom prisoner states.
- The undocumented trigger/debug surface is still too thin to claim a fully automated scenario-style test harness.