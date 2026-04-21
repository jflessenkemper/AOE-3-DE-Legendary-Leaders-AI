# Commander Naval Stress Map

This is the combined replacement for the previously separate Commander Stress Map and Naval Behavior Strip ideas.

The goal is one controlled test surface that pressures both systems at the same time:

- commander-dependent attack behavior
- elite retreat and ransom behavior
- dock placement and fishing commitment
- fleet response and transport pressure
- land and naval decision overlap under high load

## Why Combine Them

The separate-map model is clean, but it also hides one of the likely failure modes: the AI can look correct on land-only and water-only maps while still breaking when both theaters compete for attention.

This combined map is meant to expose exactly that.

## Core Design

- map size: small to medium
- team layout: fixed west vs east, best in 2v2
- terrain: very readable and mostly open
- land center: short travel distance for rapid pressure
- north water lane: protected dock and fish lane
- south water lane: contested warship and transport lane
- starting resources: high enough to reach meaningful armies quickly
- natives and treasures: none or minimal

## Layout

### Center Land Corridor

Use one broad center lane for the main commander tests.

Include:

- obvious forward rally path
- enough open room for regular-first and elite-second formations to be readable
- enough pressure that explorer death changes the battle immediately

Primary checks:

- commanderless major attacks do not continue
- elite retreat still triggers under crowded fights
- explorer ransom or recovery still queues correctly
- AI rout tracking does not collapse under multi-unit engagements

### North Water Economy Lane

Use the north side as a quieter but still relevant economy-and-presence water lane.

Include:

- safe-ish dock pockets near each side
- guaranteed fish and at least one whale pocket
- simple shoreline pathing

Primary checks:

- dock placement quality
- fishing commitment
- whether the AI keeps water economy alive while commander logic is active on land

### South Water Combat Lane

Use the south side as the active naval pressure lane.

Include:

- direct ship-to-ship engagement route
- obvious transport path
- coastal access points that let naval pressure influence land behavior

Primary checks:

- fleet patrol and engagement
- naval response timing under land pressure
- transport interference with commander recovery or assault timing
- whether land AI falls apart when naval tasks are also demanding attention

## Recommended Test Setup

- 2v2 only for the intended first version
- west team: human plus allied AI
- east team: two enemy AIs
- very high starting resources
- fast age-up or pre-aged starts if practical
- civ matchups that stress both artillery and escort logic

Best first matchup set:

- Dutch + ally vs Napoleon + Egypt
- Russia + ally vs Egypt + naval-oriented civ

## Trigger Ideas

If built as a scenario, add these fast actions:

- reset land armies
- reset fleets
- kill AI explorer
- spawn replacement fleet wave
- teleport owner explorer to a recovery point
- force a dock rebuild case

If built as an RMS, keep the geometry deterministic and use it as a repeatable skirmish stress surface rather than a fully scripted lab.

## What This Map Should Replace

This map replaces:

- the separate Commander Stress Map concept
- the separate Naval Behavior Strip concept

The reason is not simplicity for its own sake. It is to test multi-front decision pressure, which is more realistic and more likely to reveal regressions.

## What It Does Not Replace

Do not use this map as a replacement for the deterministic Mechanics Lab Scenario.

Keep the mechanics lab for:

- exact AI non-elite rout threshold checks
- elite-support negative cases
- AI rout fallback verification
- clean elite retreat verification

Use this combined map for system interaction, load, and theater competition.