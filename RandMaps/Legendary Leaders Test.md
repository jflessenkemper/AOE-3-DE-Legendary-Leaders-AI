# Legendary Leaders Test Map

This custom random map is a flat 2v2 test arena for fast validation of the current Legendary Leaders AI behavior, especially when you want one allied AI and two opposing AIs on a clean battlefield.

It now also serves as the base surface for the combined commander-and-naval stress profile rather than only a generic skirmish sandbox.

## What It Gives You

- fixed team-based west vs east spawns in 2v2
- very open battlefield with minimal terrain noise
- three land test lanes: north, center, south
- two naval test lanes: one along the north edge and one along the south edge
- rich starting mines, hunts, cattle, and trees so you can field armies quickly
- extra neutral mines, hunts, and nuggets in each lane for repeated fights
- fish, whales, and shoreline resource pockets so docks and naval lanes matter
- allied starts share the west side, enemy starts share the east side, so flanks stay readable regardless of slot order
- a natural split between a safer north water economy lane and a more contested south water combat lane
- ready-to-load flat 2v2 stress arena for manual observation without the scenario editor

## What To Test Here

- AI non-elite units routing at low health
- AI elite units refusing to auto-rout
- elite support preventing nearby AI non-elite units from routing
- routed AI units falling back to their own return point and disengaging
- AI attack order with regulars in front, elites behind, and explorer behind both
- elite disengage after the AI explorer dies
- nation style differences in a more natural 2v2 flow instead of a pure duel
- dock placement, fishing behavior, and whether fleets actually contest the north and south naval lanes
- whether commander-dependent land decisions still hold when water economy and naval combat are active at the same time

## Commander + Naval Stress Profile

Use this map as the lighter-weight implementation of the combined commander-naval stress concept.

Exact layout anchors already present in the RMS:

- west south start: `(0.18, 0.33)`
- west north start: `(0.18, 0.67)`
- east south start: `(0.82, 0.33)`
- east north start: `(0.82, 0.67)`
- north land lane: `(0.50, 0.72)`
- center land lane: `(0.50, 0.50)`
- south land lane: `(0.50, 0.28)`
- north water lane: `(0.50, 0.86)`
- south water lane: `(0.50, 0.14)`

Read those anchors this way:

- center land lane: main commander behavior lane
- north water lane: safer dock and fishing lane
- south water lane: more exposed naval combat and transport lane
- south land lane: best place to observe whether naval pressure changes land timing

Primary combined checks:

- commanderless attacks stop instead of continuing through inertia
- elite retreat and ransom still fire under crowded fights
- dock placement and fishing stay reasonable during active land pressure
- naval patrol and engagement still happen while commander logic is busy
- south-lane land behavior changes visibly if south-lane naval pressure becomes meaningful

For the stronger build spec, see `RandMaps/Commander Naval Stress Build.md`.

## Observation Flow

The current build of this map is the stable loadable arena version.

That means:

- no RMS observer trigger sequence is active right now
- no Town Center observer-console buttons are active right now
- use it as a clean fixed-layout skirmish surface and observe the AI directly

This keeps the map loadable while the trigger plumbing is rebuilt in a stock-safe way.

If you want a compact beside-the-game version, use `RandMaps/Legendary Leaders Observer Checklist.md`.

## Recommended Use

1. Start a 2v2 skirmish on this map with the mod enabled.
2. Use locked 2v2 teams with you and your allied AI on one team and the two opponents on the other.
3. Team 0 is placed on the west side and team 1 is placed on the east side, so slot order inside a team no longer matters.
4. Pick civs you want to compare for style, because the open layout makes army composition and attack rhythm easy to read.
5. Use the north and south lanes for flank pressure checks.
6. Use the center lane for elite-protection, AI-rout, and larger teamfight observations.
7. Use the north and south water lanes for dock placement, fishing, patrol paths, and naval response checks.
8. Use the south land lane and south water lane together when you want to see whether commander logic degrades under simultaneous naval demands.

## Recommended Matchups

Best first commander-and-naval stress sets:

1. Dutch + British vs Napoleon + Egypt
2. Russia + Portuguese vs Egypt + Ottomans
3. Human + allied AI vs two opposing AIs when you want to intervene manually and still keep the run readable

Why these work:

- they produce clear artillery, escort, and doctrine differences
- they keep water relevant without turning the whole run into a pure naval test
- they make commander failure more obvious than mirror matchups do

## How To Load It In Skirmish

1. Make sure the mod is enabled in Age of Empires III: DE.
2. Make sure these files exist inside the active mod's `RandMaps` folder:
	- `Legendary Leaders Test.xs`
	- `Legendary Leaders Test.xml`
3. Start a standard Skirmish lobby, not the Scenario menu.
4. Open the random map list and pick `Legendary Leaders Test`.
5. Use a 2v2 setup for the intended west-vs-east layout.
6. Put yourself in Player 1 if you want the observer console buttons on your Town Center.

If the map does not appear in the Skirmish map list, the usual cause is that the `RandMaps` files were not copied into the active local mod folder yet.

## Limits

- This is a controlled skirmish map, not a hand-authored scenario.
- The fixed 2v2 layout is tuned around exactly two teams of two; other player counts or uneven teams fall back to simpler placement.
- It does not pre-damage units or pre-place custom rout states.
- The undocumented trigger/debug surface is still too thin to claim a fully automated scenario-style test harness.
- The prior trigger-driven observer slice was removed from the live build because it caused map-load failures.
- The observer console is currently disabled until the RMS trigger plumbing is rebuilt in a stock-safe form.
- The naval lanes are deliberately simple test strips, meant to expose docking, fishing, and fleet pathing behavior rather than simulate a full water map.
- This map is the practical combined-stress surface, but it is still not a full replacement for the deterministic scenario when you need exact AI-rout-threshold or fallback-path assertions.