---
type: "Validation Evidence"
title: "Audit Checklist"
description: "Documents Audit Checklist for the homeassistant-customzones repository."
timestamp: 2026-07-28T21:55:36Z
authority: evidence
verification: verified-limited
owner: polaralias
tags:
  - homeassistant-customzones
  - validation-evidence
navigation:
  role: reference
  order: 200
---
# Audit Checklist

This checklist tracks the public-readiness audit for converting the repository from "works enough" into a defensible Home Assistant integration.

## Status

Audit tranche complete.

Principles used for this pass:

- verify behaviour before redesigning it
- distinguish product decisions from accidental implementation details
- prefer small, testable claims over broad confidence statements

## Phase 1: Product contract

### Zone semantics

- [x] Define whether points on polygon edges count as inside.
- [x] Define whether polygon vertices count as inside.
- [x] Define whether self-intersecting polygons are allowed, rejected, or undefined.
- [x] Define whether repeated points are allowed.
- [x] Define whether degenerate polygons should be rejected.
- [x] Define whether polygon point order matters beyond geometry.

### Tracker semantics

- [x] Define what counts as a usable tracker state.
- [x] Define how `unknown` differs from `unavailable`, if at all.
- [x] Define how missing `latitude` or `longitude` should be handled.
- [x] Define how invalid coordinate values should be handled.
- [x] Define whether GPS accuracy should affect in-zone calculation or only be exposed as metadata.

### Aggregate sensor semantics

- [x] Define whether one bad tracker should make the whole sensor unavailable.
- [x] Define expected behaviour for mixed tracker states.
- [x] Define whether aggregate count should represent all configured trackers or only usable trackers.
- [x] Define whether the sensor should ever expose partial truth instead of going unavailable.

### Identity semantics

- [x] Define the stable identity of a zone.
- [x] Define whether renaming a zone should change the entity ID.
- [x] Define whether changing trackers or polygon points should preserve entity identity.

## Phase 2: Configuration lifecycle

### Creation flow

- [x] Verify the initial config step with valid and invalid names.
- [x] Verify empty tracker selection behaviour.
- [x] Verify tracker-count behaviour without an arbitrary small fixed cap.
- [x] Verify the point entry flow for 1, 2, 3, and larger point counts.
- [x] Verify that finishing with fewer than 3 points fails cleanly.
- [x] Verify that the flow does not auto-complete at 15 points.

### Reconfiguration and maintenance

- [x] Determine whether users can edit an existing polygon through the UI today.
- [x] Determine whether users can change tracked entities after creation.
- [x] Determine whether users can rename an existing zone.
- [x] Determine what removing and recreating a zone means for compatibility.
- [x] Determine whether an options flow is needed.

Compatibility conclusion:

- in-place edits preserve sensor identity in the current harness
- delete-and-recreate is treated as a new config-entry lifecycle, not an identity-preserving path

### Persistence and migration

- [x] Verify the stored config entry shape in Home Assistant.
- [x] Verify whether coordinates being stored as JSON text is intentional or historical accident.
- [x] Determine whether there are older config formats to support.
- [x] Determine whether a config entry migration path is needed before public release hardening.

Migration conclusion:

- current runtime storage is structured coordinate lists only

## Phase 3: Geometry correctness

### Core inclusion behaviour

- [x] Test convex polygons beyond the current square.
- [x] Test concave polygons.
- [x] Test points clearly outside but near an edge.
- [x] Test points on horizontal, vertical, and diagonal boundaries.
- [x] Test points exactly on vertices.
- [x] Test polygons with clockwise and counter-clockwise point order.

### Edge cases

- [x] Test repeated adjacent points.
- [x] Test repeated non-adjacent points.
- [x] Test degenerate edges of zero length.
- [x] Test self-intersecting polygons.
- [x] Test very small polygons.
- [x] Test polygons near the poles or at high latitude.
- [x] Test polygons crossing longitude sign changes if that matters for intended use.

### Distance behaviour

- [x] Define whether distance is distance to the boundary, nearest edge, or nearest vertex in degenerate cases.
- [x] Verify units and approximation quality at multiple latitudes.
- [x] Verify expected distance for inside vs outside points.
- [x] Verify distance on exact boundary points.

Distance conclusion:

- distance is the minimum distance to the polygon boundary
- exact boundary points report zero distance
- inside and outside points use the same nearest-boundary interpretation
- the current approximation is defended at representative equatorial and high-latitude cases

## Phase 4: Runtime behaviour

### Tracker state changes

- [x] Verify startup behaviour when tracker states already exist.
- [x] Verify startup behaviour when tracker states do not yet exist.
- [x] Verify transition from inside to outside.
- [x] Verify transition from outside to inside.
- [x] Verify transition from tracked to unavailable.
- [x] Verify transition from tracked to missing coordinates.
- [x] Verify recovery from unavailable back to tracked.
- [x] Verify recovery from invalid coordinates back to tracked.

### Multi-tracker aggregation

- [x] Verify two-trackers-inside behaviour.
- [x] Verify one-inside one-outside behaviour.
- [x] Verify one-inside one-unavailable behaviour.
- [x] Verify all-outside behaviour.
- [x] Verify all-unavailable behaviour.
- [x] Verify attribute counts stay consistent with tracker lists.

### Attribute contract

- [x] Verify all documented aggregate attributes are present.
- [x] Verify undocumented flat compatibility attributes are removed.
- [x] Verify namespaced tracker attributes cannot collide.
- [x] Verify attribute values are stable enough for automations/templates.

## Phase 5: Packaging and integration quality

### Home Assistant integration hygiene

- [x] Verify manifest fields are complete and current for the intended Home Assistant target.
- [x] Verify translations are present and aligned with the current flow.
- [x] Verify branding and icon surfaces exist for the current packaging posture.
- [x] Verify the chosen `iot_class` is accurate.
- [x] Verify unload/reload behaviour.

### Repository hygiene

- [x] Verify README claims match actual behaviour.
- [x] Add a documented limitations section.
- [x] Populate `codeowners`.
- [x] Verify CI is sufficient for the intended support bar.
- [x] Verify a Hassfest workflow is present in CI.

## Phase 6: Public portfolio readiness

### Documentation

- [x] Add an architecture overview.
- [x] Document explicit invariants and non-goals.
- [x] Document expected entity naming and migration consequences.
- [x] Document behaviour for unavailable trackers and boundary points.

### Quality story

- [x] Define what "done" means for verification.
- [x] Identify the minimum regression test suite for future changes.
- [x] Identify intentionally unsupported scenarios.
- [x] Decide the versioning and release approach.

## Publish-ready conclusion

The repository now has:

- explicit canonical contract docs
- aligned audit and status docs
- current Home Assistant packaging metadata
- a passing local lint and test baseline
- explicit accepted limitations instead of open-ended hardening notes

## Repository knowledge

- [Documentation map](docs/knowledge/documentation-map.md) — RKE-managed reading order and relationship hub.
