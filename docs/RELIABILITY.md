---
type: "Reliability Contract"
title: "Reliability"
description: "Documents Reliability for the homeassistant-customzones repository."
timestamp: 2026-07-28T21:55:36Z
authority: canonical
verification: untested
owner: polaralias
tags:
  - homeassistant-customzones
  - reliability-contract
navigation:
  role: supporting
  order: 100
---
# Reliability

## Purpose

Reliability in this repository is not about uptime alone. It is about trustworthy zone answers.

## Reliability principle

The integration should prefer explicit degradation over silently wrong spatial conclusions.

In practice, that means:

- a bad tracker state should be visible
- stale in-zone conclusions should not survive invalid data
- the aggregate sensor should not imply certainty it does not have
- one bad tracker should not collapse the whole aggregate sensor if other trackers still provide usable truth

## Desired reliability contract

The reliability model should explicitly define:

- what counts as usable tracker data
- how unavailable and unknown states are handled
- how missing coordinates are handled
- how invalid coordinates are handled
- how mixed tracker quality affects the aggregate sensor state

Current desired direction:

- tracker unavailability is a per-tracker degradation, not an automatic aggregate outage
- aggregate state should stay available when at least one tracker still provides usable coordinates
- unusable trackers should be surfaced explicitly in attributes
- aggregate counts should be derived from usable trackers, not blocked by unusable ones
- when no usable trackers are inside the zone, the aggregate state should be `0 in zone`
- aggregate unavailability should be reserved for zone-level evaluation failure, not ordinary tracker degradation
- the public reliability contract should expose one canonical tracker degradation state, with optional diagnostic detail underneath

Diagnostic detail can remain more specific than the public contract. For example:

- `unknown`
- `unavailable`

may remain distinct internal or attribute-level reasons while still mapping to the single public concept of an unusable tracker.

Interpretation rule:

- `0 in zone` is an aggregate counting result, not a claim that every configured tracker is confirmed outside the zone
- unusable trackers may still physically be in the zone, but they are not counted as in-zone until they become usable again
- attributes must surface tracker usability clearly enough that users can see when aggregate certainty is reduced
- this remains true even when every configured tracker is currently unusable

The aggregate state grammar should remain numeric-only so that reliability semantics stay uniform across zero, one, or many trackers.

Required stable attribute distinctions:

- counted in zone
- counted out of zone
- unusable

These distinctions are part of the public reliability surface because the aggregate state intentionally compresses them.

Per-tracker attribute identity must also be stable enough to avoid collisions between different tracker domains that share an object ID.

Required stable per-tracker attributes:

- `classification`
- `diagnostic_reason`
- `counted_in_zone`
- `trusted_distance_m`
- `gps_accuracy_m`

Preferred attribute shape:

- one nested per-tracker structure is preferred over many flat prefixed attributes
- the forward reliability contract should target the nested structure directly rather than preserve flat compatibility aliases

Stable aggregate attributes:

- `count_in_zone`
- `count_out_of_zone`
- `count_unusable`
- `trackers_in_zone`
- `trackers_out_of_zone`
- `trackers_unusable`
- `trackers_detail`

Operational guidance:

- the aggregate state is suitable for default automations
- attribute-level usability is the recommended confidence check for users whose trackers are known to be unreliable

Distance reliability rule:

- distance is only trustworthy for usable trackers
- unusable trackers must not report a trusted distance

Accuracy reliability rule:

- a location fix can be geometrically inside the zone and still be excluded from the count if its accuracy is too poor
- low-confidence fixes should degrade count truth rather than silently count as inside
- the confidence rubric must be defined in a way users can understand and tests can defend
- the confidence rubric should scale relative to zone size rather than rely on one global threshold
- the primary confidence measure should compare accuracy radius against nearest-boundary distance
- the confidence rule should require a comfortable inside margin rather than treat the boundary threshold as sufficient confidence
- the initial confidence model should use one fixed safety-margin factor across zones
- the initial fixed factor is `0.75`
- the confidence gate should be symmetric for in-zone and out-of-zone counting
- the same nearest-boundary-distance confidence rule should be used for both inside and outside classification
- `gps_accuracy` should be treated as an accuracy radius in meters
- if usable accuracy data is missing or invalid, the tracker should be unusable rather than classified through pure geometry
- no area-based override should bypass the confidence rule

Boundary confidence interpretation:

- geometric inclusion and count confidence are separate concepts
- a tracker on the boundary is geometrically inside
- a tracker on the boundary will normally fail count confidence because it has no clearance margin

Confidence failure should be surfaced as its own diagnostic reason so users can distinguish:

- unavailable or missing data
- malformed data
- low-confidence but otherwise present data

This confidence-failure reason should be symmetric across inside and outside candidates.

Staleness reliability rule:

- stale location data should degrade a tracker to unusable
- the initial staleness model should use one fixed global threshold
- the initial fixed global staleness threshold is `5 minutes`

Important distinction:

- config-authored polygon points should normally be valid once a zone exists
- tracker runtime coordinates remain untrusted input and must still be handled defensively
- tracker runtime accuracy remains untrusted input and must still be handled defensively

Boundary inclusion is also a reliability choice:

- points on polygon edges count as inside
- points on polygon vertices count as inside

This reduces edge jitter and makes automation behaviour more stable.

## Known reliability hotspot

The main reliability hotspot is the interaction between:

- tracker state quality
- polygon membership
- aggregate sensor availability

That logic currently lives primarily in `custom_components/custom_zone/sensor.py`.

## Standard for changes

Any change to:

- tracker state classification
- aggregate availability semantics
- in-zone persistence
- distance calculation behaviour

should be treated as a reliability change and should update:

- tests
- product contract docs
- this document

## Repository knowledge

- [Documentation map](knowledge/documentation-map.md) — RKE-managed reading order and relationship hub.
