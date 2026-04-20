# Gaia Neutralization Architecture

This document replaces the old prison-system direction with the mod-wide contract for Gaia neutralization.

## Goal

- Non-elite military units become eligible for neutralization at 25% health or below.
- Nearby elite support blocks neutralization.
- AI-only scripts do not own prisoners, prison routing, or explorer-only reclaim anymore.
- Converted Gaia units may be reclaimed by any explorer or killed normally by surrounding troops.

## Engine Constraint

The AI XS layer in this repo can detect low health, elite status, and nearby support, but it does not expose a general-purpose API to transfer arbitrary unit ownership to Gaia.

Because of that, true Gaia neutralization must be performed by scenario or random-map triggers using effects such as `Convert Units in Area`.

## Repo Contract

The AI side now owns only the eligibility contract:

- health threshold: `25%`
- excluded units: elite units and heroes treated as elite
- blocker: nearby elite support
- no longer a blocker: nearby explorer support

The central legacy hook in `aiPrisoners.xs` stays callable by leader files, but it only logs that trigger-backed ownership transfer is required.

## Recommended Mod-Wide Implementation

### Phase 1: Shared Contract

- Keep eligibility logic in AI XS.
- Keep legacy leader calls intact for backward compatibility.
- Validate bootstrap logs rather than prison activation logs.

### Phase 2: Trigger Conversion Layer

Each supported scenario or random map should provide:

- one neutralization anchor per player or per lane
- a periodic trigger that converts eligible surrender traffic from the source player to Gaia near that anchor
- a reclaim trigger that converts nearby Gaia military from Gaia to the explorer owner's player ID

Reference effect shape:

- `Convert Units in Area`
- `SrcPlayer = <original owner>`
- `TrgPlayer = 0`
- `UnitType = <ordinary military proto or logical bucket supported by the map>`
- `SrcObject = <anchor object>`

For reclaim:

- `Convert Units in Area`
- `SrcPlayer = 0`
- `TrgPlayer = <explorer owner>`
- `SrcObject = <reclaim anchor or explorer-linked anchor>`

## Scope Reality

There is no single global XML-only switch that makes every stock and custom map perform Gaia neutralization. Every map or scenario that wants the full mechanic must ship the trigger layer.

That makes the practical rollout:

1. shared AI eligibility contract in the repo
2. shared validation language and bootstrap markers
3. per-map or per-scenario trigger implementations

## Validation Guidance

Until trigger-backed maps are wired:

- `ai_rout_bootstrap` should pass by finding the compatibility log markers
- `elite_support_blocks_rout` should only assert the `elite-support` block reason
- old custody and reclaim suites remain legacy and should not be treated as the forward-looking behavior target