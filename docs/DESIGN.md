---
type: "Design Concept"
title: "Design"
description: "Documents Design for the homeassistant-customzones repository."
timestamp: 2026-07-28T21:55:36Z
authority: canonical
verification: untested
owner: polaralias
tags:
  - homeassistant-customzones
  - design-concept
navigation:
  role: supporting
  order: 100
---
# Design

## Design problem

Home Assistant's built-in zone model is circle-based. Some real spaces are not.

Custom Zone exists to model places like:

- driveways
- gardens
- parking areas
- property boundaries
- irregular approach paths

## UX principles

- configuration should be understandable without reading source code
- the product should communicate degraded confidence clearly
- names and attributes should be predictable enough for automations
- geometry complexity should not leak into ordinary usage more than necessary

## Current design constraints

- configuration is currently point-by-point through the Home Assistant config flow
- the frontend surface is limited to native Home Assistant integration UI patterns
- the sensor state model has to remain automation-friendly, not just technically precise

## Geometry design constraint

The product should optimise for ordinary user-comprehensible polygons, not for mathematically permissive authoring.

That means invalid or ambiguous shapes such as self-intersecting polygons, repeated points, and zero-length edges should be rejected rather than interpreted.

Point order should not become a user burden. Clockwise and counter-clockwise authoring should be treated as equivalent for a valid polygon.

## Automation design implication

The product should support two levels of user reasoning:

- a simple aggregate state for common automations
- attribute-level tracker detail for users who need stricter confidence rules because their trackers are unreliable

## Confidence design implication

Geometry alone is not enough. A tracker can be mathematically inside a polygon while still being too inaccurate to count confidently.

That means the product needs an explicit confidence rubric, likely tied to both:

- reported tracker accuracy
- zone size or shape characteristics

The intended direction is zone-relative confidence rather than a single global accuracy cutoff.

The preferred geometric basis is nearest-boundary distance, because polygon area alone is too coarse for narrow or irregular zones.

The preferred counting model is conservative: a tracker should be comfortably inside the zone relative to its accuracy, not merely mathematically inside by a negligible margin.

The first product version of this rule should use one fixed safety-margin factor rather than per-zone tuning.

Initial chosen factor:

- `0.75`

The confidence rule should apply symmetrically. A noisy fix should not be trusted to say "outside" if that same level of noise would prevent trusting it to say "inside."

The preferred shape of that symmetry is one boundary-distance rule used on both sides of the polygon boundary.

Additional design choices:

- `gps_accuracy` is treated directly as a radius in meters
- there is no area-based escape hatch around the boundary-distance confidence rule
- stale tracker data should degrade confidence just like missing or malformed data
- advanced confidence semantics should live mainly in docs and attributes before being surfaced as complex UI controls
- the initial freshness threshold is `5 minutes`
- nested per-tracker attributes are preferred over flat attribute sprawl
- if there is no meaningful installed-user compatibility burden, the product should move forward directly to the nested structure

## Repository knowledge

- [Documentation map](knowledge/documentation-map.md) — RKE-managed reading order and relationship hub.
