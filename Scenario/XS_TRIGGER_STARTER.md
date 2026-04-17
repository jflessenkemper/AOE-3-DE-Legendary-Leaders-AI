# AoE3DE Scenario Scripting Notes

## Short Answer

No reliable text-to-text conversion path showed up for `.age3Yscn` itself. The supported code-first paths I could verify are:

- Scenario Editor GUI triggers
- Random Map scripts with embedded trigger creation
- XS trigger output inspection through `Trigger/trigtemp.xs`

What I could not verify is a maintained external parser or generator that round-trips `.age3Yscn` safely.

## Verified Sources

- Official support says Scenario Editor triggers are configured in the editor UI.
- Official support also says random map scripts can create triggers with functions like `rmCreateTrigger`, `rmAddTriggerCondition`, and `rmAddTriggerEffect`.
- Official support says loading an RMS into the map editor generates `Trigger/trigtemp.xs` so you can inspect the trigger-side XS code.
- The AOE3MC XS guide states XS is used for AI scripts, custom maps, and custom triggers.

## What Exists On Your Machine

- `Trigger/trigtemp.xs` exists in your AoE3DE profile and is plain text.
- It is currently just the default stub:

```xs
//==============================================================================
// TEST TRIGGER SCRIPT
//==============================================================================

void main(void)
{
}
```

That confirms there is a trigger-script surface, but it does not by itself prove a full `.age3Yscn` import/export workflow.

## Best Practical Workflow

If you want a code-first test map workflow, the cleanest path is:

1. Keep the `.age3Yscn` scenario as the playable asset.
2. Build the scenario layout in the Scenario Editor.
3. Use GUI triggers for scenario-specific tests.
4. If you want repeatable code generation, build a small RMS prototype that creates terrain, starting layout, and simple triggers.
5. Inspect `Trigger/trigtemp.xs` after loading the RMS into the editor to learn the trigger-side XS structure the game emits.

## Official RMS Trigger Example

This is the officially documented trigger pattern for an AoE3 random map script. It is not pasted into `.age3Yscn` directly. It belongs in an RMS script and is one of the few code-driven trigger flows that is actually documented.

```xs
// Create triggers first.
for (j = 1; <= 2)
{
    rmCreateTrigger("MyTrigger" + j);
}

// Trigger 1: grant food to every non-Gaia player.
rmSwitchToTrigger(rmTriggerID("MyTrigger1"));
for (i = 1; <= cNumberNonGaiaPlayers)
{
    rmAddTriggerEffect("Grant Resources");
    rmSetTriggerEffectParamInt("PlayerID", i);
    rmSetTriggerEffectParam("ResName", "Food");
    rmSetTriggerEffectParamInt("Amount", 1000);
}
rmSetTriggerPriority(4);
rmSetTriggerActive(true);
rmSetTriggerRunImmediately(true);
rmSetTriggerLoop(false);

// Trigger 2: placeholder for later conditions/effects.
rmSwitchToTrigger(rmTriggerID("MyTrigger2"));
rmSetTriggerPriority(4);
rmSetTriggerActive(false);
rmSetTriggerRunImmediately(false);
rmSetTriggerLoop(false);
```

## How To Use This For Your Test Map

- Use the Scenario Editor for the three-lane test layout in `TEST_SCENARIO_SETUP.md`.
- Use GUI triggers for fast scenario-specific actions like lane reset, explorer teleport, and AI explorer kill.
- If you want to experiment with code, start with a separate RMS prototype rather than trying to patch the binary scenario file directly.

## What I Did Not Find

- No maintained online AoE3DE scenario generator.
- No maintained `.age3Yscn` parser or round-trip editor in the quick search.
- No local `typetest.xml` trigger debug reference on this machine, even though the official docs mention it as a reference path in older installs.

## Good Inspiration Sources

- Official support article: Scenario Editor triggers
- Official support article: Random Map Scripting Commands
- AOE3MC XS guide
- Community forum threads about `.age3Yscn` extraction limits