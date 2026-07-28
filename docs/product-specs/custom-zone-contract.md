---
type: "Product Contract"
title: "Custom Zone Contract"
description: "Documents Custom Zone Contract for the homeassistant-customzones repository."
timestamp: 2026-07-28T21:55:36Z
authority: canonical
verification: untested
owner: polaralias
tags:
  - homeassistant-customzones
  - product-contract
navigation:
  role: foundational
  order: 20
---
# Custom Zone Contract

## Purpose

Custom Zone should give Home Assistant users a way to define irregular geographic areas and reason about tracker presence inside those areas without relying on Home Assistant's built-in circular zones.

## Core outcome

A user should be able to create a named polygon zone, attach a set of one or more tracker entities to it, and use a single sensor as an automation-friendly representation of zone membership.

## Primary user

A Home Assistant user who wants better spatial fidelity than a circle can provide.

## Functional surfaces

### Zone creation

The product should support:

- naming a zone
- selecting a set of one or more tracker entities
- defining polygon coordinates through the Home Assistant UI

Tracker-set invariant:

- a zone must have a non-empty tracker set
- a zone with zero trackers is invalid and should not be supported
- the product contract should not impose an arbitrary small fixed tracker-count limit such as 10 without a demonstrated product reason

### Zone evaluation

The product should:

- evaluate whether each usable tracker is inside the polygon
- expose an aggregate sensor state
- expose enough attributes for debugging and automation authoring

Aggregate zone evaluation should remain available even when an individual tracker is unavailable or unusable.

The intended rule is:

- a single bad tracker must not make the whole zone sensor unavailable
- an unavailable or unusable tracker should be excluded from the in-zone count
- the sensor should report the best current aggregate truth from the remaining usable trackers
- degraded tracker quality should still be visible through attributes

When no usable trackers are currently inside the polygon, the aggregate state should be `0 in zone`.

`all out of zone` should not be the canonical aggregate state, because it overclaims certainty about trackers that may currently be unavailable or unusable.

Aggregate state grammar:

- the aggregate state should use one numeric grammar only
- examples: `0 in zone`, `1 in zone`, `2 in zone`
- special phrase variants such as `all out of zone` should not be part of the public contract

Meaning of `0 in zone`:

- no tracker is currently counted as inside the zone
- unusable trackers are not counted as inside
- unusable trackers may still physically be inside the zone, but the product does not treat them as in-zone for aggregate state purposes
- attributes must make unusable trackers explicit so users can see the difference between "confirmed not counted inside" and "not currently evaluable"

The aggregate sensor should become unavailable only for zone-level evaluation failure, such as:

- invalid or unreadable polygon configuration
- irrecoverable config-entry corruption
- complete inability to evaluate the zone as a product surface

Tracker-level data quality issues alone should not make the aggregate sensor unavailable.

Even when zero configured trackers are currently usable, the aggregate sensor should still report `0 in zone`.

In that case:

- the aggregate state remains available
- attributes should show that all trackers are currently unusable
- users who need stronger confidence should rely on attribute-level tracker usability in their automations

For the public contract, tracker degradation should use one canonical concept:

- `unusable tracker`

Diagnostic detail may still explain why a tracker is unusable, but those finer reasons are secondary debugging data rather than primary product states.

This includes Home Assistant distinctions such as `unknown` and `unavailable`:

- they may remain distinct as diagnostic reasons
- they should collapse into the same public contract concept of `unusable tracker`

Confidence failure should also be a distinct diagnostic reason:

- users should be able to tell the difference between "no usable data" and "data present but not trusted enough to count"
- the same confidence-failure reason should apply whether the low-confidence fix is geometrically inside or outside

Recommended diagnostic reason vocabulary:

- `tracker_unavailable`
- `confidence_data_missing`
- `confidence_data_invalid`
- `confidence_failure`
- `stale_location`

For the aggregate sensor attributes, the contract should explicitly surface:

- which trackers are currently counted as in zone
- which trackers are currently counted as out of zone
- which trackers are currently unusable

Users must be able to tell when `0 in zone` means "nothing is currently counted inside" rather than "every configured tracker is confirmed outside."

These per-tracker classifications should be treated as stable contract surfaces, not loose debugging-only data.

Per-tracker attribute naming contract:

- per-tracker attributes should be namespaced by full entity identity, not just object ID
- `person.example` and `device_tracker.example` must remain distinguishable
- attribute naming should optimise for collision resistance over visual brevity

Stable per-tracker attribute contract:

- `classification`
- `diagnostic_reason`
- `counted_in_zone`
- `trusted_distance_m`
- `gps_accuracy_m`

Optional per-tracker attribute:

- `source_entity_id`

Preferred structure:

- per-tracker detail should live under one nested top-level attribute such as `trackers_detail`
- full entity identity should be used as the key within that nested structure
- nested structure is preferred over flat prefixed attribute explosion
- flat prefixed per-tracker attributes should be treated as legacy implementation detail rather than part of the intended forward contract

Stable aggregate attribute contract:

- `count_in_zone`
- `count_out_of_zone`
- `count_unusable`
- `trackers_in_zone`
- `trackers_out_of_zone`
- `trackers_unusable`
- `trackers_detail`

Automation guidance:

- the aggregate state is the default automation surface
- attribute-level tracker classifications are the confidence surface
- users with unreliable trackers should be able to build stricter automations that inspect unusable-tracker attributes directly

Distance contract:

- distance should be reported only for usable trackers
- unusable trackers should not expose a trusted distance value
- `null` or an equivalent absent value is the correct representation for unusable-tracker distance

Accuracy contract:

- tracker accuracy should influence whether a tracker is counted as inside the zone
- low-confidence location fixes should be able to exclude a tracker from the in-zone count
- when accuracy excludes a tracker from the count, attributes should explain that outcome clearly
- the exact confidence rubric must be explicit and testable, not left as an implementation guess
- the confidence rubric should be zone-relative rather than one global fixed threshold
- the primary confidence measure should be distance to the nearest polygon boundary, not polygon area alone
- the counting rule should include a safety margin, not a knife-edge threshold at the boundary
- the safety-margin factor should be fixed across zones rather than user-configurable per zone
- the initial fixed safety-margin factor should be `0.75`
- `gps_accuracy` should be interpreted directly as an accuracy radius in meters
- valid coordinates without usable accuracy data should result in an unusable tracker, not a fallback to pure geometry

Initial counting rule:

- a tracker counts as inside only if it is geometrically inside the polygon
- and its reported accuracy is less than or equal to `nearest_boundary_distance * 0.75`
- a tracker counts as outside only if it is geometrically outside the polygon
- and its reported accuracy is good enough to support that classification under the same confidence rule
- otherwise the tracker is unusable for counting purposes
- the same nearest-boundary-distance rule applies on both sides of the boundary
- no area-based override should bypass the boundary-distance confidence rule

Boundary behaviour:

- a tracker on a polygon edge counts as inside the zone
- a tracker on a polygon vertex counts as inside the zone

This is an intended product rule, not merely a current implementation detail.

Confidence interaction:

- boundary inclusion is a geometric rule
- count confidence is a separate operational rule
- a boundary-position fix is still geometrically inside
- but a boundary-position fix will normally be unusable for counting because its boundary clearance is zero

Important distinction:

- zone polygon coordinates are authored through the config flow and should be valid at creation time
- tracker coordinates are runtime input from Home Assistant state and can still be missing, stale, malformed, or otherwise unusable
- tracker accuracy is also runtime input and should influence whether a location fix is trusted for counting purposes

Staleness rule:

- stale location data should make a tracker unusable
- staleness should start with one fixed global threshold rather than per-zone tuning
- the initial fixed global staleness threshold should be `5 minutes`

Polygon validity rules:

- a valid polygon must contain at least 3 distinct points
- self-intersecting polygons should be rejected
- repeated adjacent points should be rejected
- repeated non-adjacent points should be rejected
- zero-length edges should be rejected
- clockwise and counter-clockwise point order should be treated as equivalent
- the product contract should treat self-intersection as invalid zone authoring, not as an advanced supported geometry case
- the product contract should treat repeated points and zero-length edges as invalid zone authoring, not as input to silently normalise
- users should not need to repeat the first point to close the polygon; closure is implicit
- the product contract should not impose an arbitrary small fixed point-count ceiling such as 15 without a demonstrated product reason

### Automation ergonomics

The product should make it obvious when a zone result is trustworthy and when tracker data quality prevents a trustworthy answer.

## Contract areas that must be explicit

The following must be treated as part of the product contract, not accidental implementation details:

- whether boundary points count as inside
- what happens when tracker coordinates are missing or invalid
- how mixed tracker states are aggregated
- which entity IDs are created
- which attributes are stable for automations
- what configuration changes preserve or break identity

Entity identity contract:

- the zone is the stable identity surface
- tracker membership must not be encoded into the aggregate sensor entity ID
- one-tracker and many-tracker zones are the same product model with different set sizes
- changing tracker membership should not rename the aggregate sensor
- renaming a zone should preserve aggregate sensor identity
- changing the polygon shape should preserve aggregate sensor identity
- changing the tracker set should preserve aggregate sensor identity
- display naming and stable identity should be treated as separate concerns

Migration and editing direction:

- the intended end state is in-place editing rather than forced delete-and-recreate
- moving to zone-based stable identity should preserve entity identity where Home Assistant allows it
- if an identity-preserving migration is impossible, a single documented breaking migration is preferable to long-term mixed naming

## Desired qualities

- predictable
- automation-friendly
- conservative with bad data
- easy to explain
- easy to verify with tests

## Current known ambiguity

The repository has an implementation, but some of the intended rules are still not written down as formal product decisions. The audit process should close those gaps before major code changes.

## Repository knowledge

- [Documentation map](../knowledge/documentation-map.md) — RKE-managed reading order and relationship hub.
