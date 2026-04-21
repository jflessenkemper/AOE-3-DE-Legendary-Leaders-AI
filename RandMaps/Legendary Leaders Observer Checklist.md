# Legendary Leaders Observer Checklist

Use this when you want to watch the AI in `Legendary Leaders Test` without playing a full macro game.

## Lobby Setup

1. Open `Skirmish`, not `Scenario`.
2. Pick `Legendary Leaders Test`.
3. Use a `2v2` setup.
4. Put yourself in `Player 1` so your Town Center gets the observer console.
5. Lock teams so you and your allied AI are west and both enemies are east.
6. Good first matchup: `Dutch + British vs Napoleon + Egypt`.
7. Optional: enable full reveal if you want pure observation.

## Fast Observer Flow

1. Start the match and do not worry about normal build play.
2. Open your Town Center command page `2`.
3. Trigger `Observer: Water Window`.
4. Watch the north and south water lanes for `60-90` seconds.
5. Trigger `Observer: Commander Window`.
6. Move the camera to the center lane.
7. Watch the first major land engagement.
8. Trigger `Observer: Repeat Fight`.
9. Watch whether the same behaviors survive the second engagement.

## What To Watch

### Water Window

1. Do docks go down in sensible shoreline spots?
2. Do fishing boats actually start working quickly?
3. Do fleets leave port and contest the lane instead of idling?
4. Does the south water lane become more dangerous than the north one?

### Commander Window

1. Do regular units lead the attack?
2. Do elite units stay behind the regular line instead of charging first?
3. Does the explorer stay behind both lines?
4. If the fight gets messy, does the formation still make sense?
5. If a commander dies, does the elite behavior visibly change?

### Combined Stress Check

1. While water activity is happening, does the land attack still look organized?
2. Does south-lane naval pressure change land timing or target choice?
3. Do fleets keep acting while commander logic is busy on land?

## Pass / Fail Heuristic

Mark the run as a practical pass if most of these are true:

1. Water economy starts without obvious delay.
2. Naval units patrol, contest, or respond instead of sitting still.
3. Land attacks look regular-first, elite-second, explorer-behind.
4. Commander behavior does not collapse once naval activity begins.
5. The second engagement still resembles the first instead of degrading into nonsense.

Mark it as a practical fail if any of these dominate the run:

1. Docks are badly delayed or never appear when the lane is safe.
2. Fishing boats or fleets idle for long stretches.
3. Elites lead the charge too often.
4. Explorer positioning looks exposed or random.
5. The AI stops making coherent land decisions once water pressure starts.

## When To Switch To The Scenario Map

Use the scenario instead of this random map when you need exact interaction checks for:

1. AI non-elite rout thresholds
2. elite-support blocked rout
3. AI rout fallback toward the return point
4. forced explorer death and elite retreat timing

That scenario flow is described in `Scenario/TEST_SCENARIO_SETUP.md`.