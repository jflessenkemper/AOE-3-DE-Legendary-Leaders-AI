# AI Rout Architecture

This document defines the mod-wide contract for AI non-elite rout behavior.

## Goal

- AI-controlled non-elite military units become eligible to rout at 25% health or below.
- Nearby friendly elite support blocks rout.
- Routed AI units fall back toward their own return point and disengage.
- Player-controlled units never auto-rout.

## Engine Constraint

The AI XS layer in this repo can detect low health, elite status, and nearby support, and it can issue a fallback move toward the unit's return point. It does not transfer ownership of any unit to Gaia or any other player.

If a future scenario or random map wants additional behavior beyond fallback (for example, conversion or cosmetic flags), that work belongs in scenario or RMS triggers, not in the AI XS layer.

## Repo Contract

The AI side owns the eligibility contract and the fallback move:

- health threshold: `25%`
- excluded units: elite units, heroes, and player-controlled units
- blocker: nearby friendly elite support
- action: issue a fallback move toward the AI's own return point and log the rout markers

## Logging Contract

The runtime suites depend on these markers in `Age3Log.txt`:

- `Legendary Leaders: [RULE] AI non-elite rout enabled at 25% health; elite units hold and human-controlled units keep manual control`
- `Legendary Leaders: [UNIT] ai-rout-start unit=...`
- `Legendary Leaders: [UNIT] ai-rout-move unit=...`
- `Legendary Leaders: [UNIT] ai-rout-arrival unit=...`
- `Legendary Leaders: [UNIT] ai-rout-blocked unit=... reason=elite-support`

## Scope Reality

There is no per-unit ownership transfer in the AI side anymore. The AI side only routes its own units toward its own return point. Anything beyond that has to be handled by trigger work in the specific scenario or random map.

## Validation Guidance

- `ai_rout_bootstrap` should pass by finding the bootstrap log marker.
- `ai_rout_lane` should pass by finding the start, move, and arrival markers in order.
- `elite_support_blocks_rout` should pass when nearby elite support stops a rout.
- `elite_retreat_lane` should pass when the explorer dies and the elite line disengages.
