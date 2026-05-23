# Architecture

## Purpose

Custom Zone is a Home Assistant custom integration that evaluates whether configured tracked entities are inside a user-defined polygon.

## System shape

This is a compact integration with one primary runtime path:

1. Home Assistant loads the integration from `custom_components/custom_zone`.
2. The config flow captures a zone name, tracker entities, and polygon points.
3. A config entry is created and forwarded to the sensor platform.
4. The sensor entity subscribes to tracker state changes.
5. The sensor evaluates polygon membership and exposes aggregate state and attributes.

## Main modules

### `custom_components/custom_zone/__init__.py`

Integration bootstrap.

- registers the `sensor` platform
- forwards config entries
- unloads and reloads the platform cleanly through Home Assistant config-entry lifecycle hooks

### `custom_components/custom_zone/config_flow.py`

Configuration capture and in-place editing.

- collects zone identity
- collects selected tracker entities
- collects polygon points one at a time
- rejects blank names
- rejects empty tracker sets
- rejects repeated points and self-intersecting polygons at finish time
- stores polygon coordinates as structured coordinate lists
- updates the same config entry through an options flow for rename, tracker-set, and polygon editing

Accepted UX constraint:

- polygon edits are still form-based rather than point-level inline or map-based editing

### `custom_components/custom_zone/sensor.py`

Runtime engine.

- validates stored polygon coordinates before setup
- watches tracker state changes
- classifies tracker state quality
- runs polygon membership logic
- computes boundary distance
- emits sensor state and attributes

### `custom_components/custom_zone/strings.json` and `translations/en.json`

Frontend copy for the Home Assistant config and options flows.

## Data model

### Config entry data

Stored fields:

- `name`
- `trackers`
- `zone_type`
- `coordinates`

Storage rule:

- `coordinates` must be a structured list of `[latitude, longitude]` pairs
- malformed stored polygon data is rejected during runtime setup

### Runtime tracker model

Per tracker, the runtime tracks:

- latitude
- longitude
- accuracy
- in-zone status
- distance to polygon boundary
- tracker classification
- diagnostic reason when unusable

Observed classifications:

- `counted_in_zone`
- `counted_out_of_zone`
- `unusable`

Observed diagnostic reasons:

- `tracker_unavailable`
- `confidence_data_missing`
- `confidence_data_invalid`
- `confidence_failure`
- `stale_location`

## Entity model

Each config entry creates one sensor.

Identity rules:

- sensor identity is zone-based
- tracker membership is not encoded into the entity ID
- rename, tracker-set changes, and polygon changes preserve sensor identity in the current harness

Observed naming pattern:

- `sensor.customzone_<zone>`

Observed state model:

- `<count> in zone`

Observed availability model:

- tracker degradation does not collapse aggregate availability
- aggregate unavailability is reserved for zone-level setup failure
- unload transitions the entity to Home Assistant's unavailable restored state until reload reactivates it

Stable aggregate attributes:

- `count_in_zone`
- `count_out_of_zone`
- `count_unusable`
- `trackers_in_zone`
- `trackers_out_of_zone`
- `trackers_unusable`
- `trackers_detail`

## Design pressure points

### Geometry correctness

The integration uses in-repo polygon math rather than an external geometry library. That keeps distribution simple but makes correctness a core repository responsibility.

### Availability semantics

The most consequential product decision is how the sensor behaves when one or more trackers do not provide usable coordinates.

Current verified runtime posture:

- the aggregate sensor remains available through tracker degradation
- tracker usability depends on geometry, `gps_accuracy`, and staleness
- the aggregate confidence surface is `trackers_detail`

### Identity stability

Zone naming, unique IDs, entity IDs, and reconfiguration behavior are treated as part of the public contract, not incidental implementation details.

## Non-goals for now

- architecture astronautics
- unnecessary subsystem layering
- speculative abstractions for future zone types
- point-level polygon editing UI beyond Home Assistant's standard config-flow forms

The repo is small enough that the correct ongoing posture is preserving explicit behavior and tests, not expanding internal structure for its own sake.
