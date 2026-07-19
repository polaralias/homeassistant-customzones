# Codebase Map

## Scope and stance

This document maps the repository in its current verified state without assuming the code is correct just because it exists.

- Documents are treated as claims until verified.
- Code is treated as implementation intent, not proof.
- Tests are treated as evidence for the paths they exercise.

Verification performed for this pass:

- `python -m ruff check .` passed.
- `python -m pytest -q` passed with 48 tests.

## Project identity

Repository purpose:

- a Home Assistant custom integration named `Custom Zone`
- a UI-configurable polygon zone definition
- one aggregate sensor per zone
- explicit handling for degraded tracker confidence

Primary sources:

- `README.md`
- `custom_components/custom_zone/manifest.json`
- `docs/product-specs/custom-zone-contract.md`

## Top-level layout

### Runtime integration

- `custom_components/custom_zone/__init__.py`
- `custom_components/custom_zone/manifest.json`
- `custom_components/custom_zone/const.py`
- `custom_components/custom_zone/config_flow.py`
- `custom_components/custom_zone/sensor.py`
- `custom_components/custom_zone/strings.json`
- `custom_components/custom_zone/translations/en.json`

### Tests

- `tests/test_config_flow.py`
- `tests/test_sensor.py`
- `tests/conftest.py`

### Distribution and repo metadata

- `README.md`
- `hacs.json`
- `.github/workflows/ci.yml`
- `.github/workflows/hassfest.yml`
- branding assets under `brands/` and `custom_components/custom_zone/brand/`

## Runtime map

### 1. Integration entry point

`custom_components/custom_zone/__init__.py` is minimal.

- it registers one platform: `sensor`
- on setup it forwards the config entry to that platform
- on unload it delegates to Home Assistant platform unloading

Interpretation:

- the integration has one real runtime surface today: a sensor entity
- there is no coordinator, service layer, storage layer, or background polling loop

### 2. Config flow

`custom_components/custom_zone/config_flow.py` is the UI entry path.

It currently does all of the following:

- collects a non-empty zone name
- collects one or more trackers
- keeps the zone type fixed to `polygon`
- collects polygon points iteratively
- validates latitude and longitude ranges at point-entry time
- rejects repeated points and self-intersecting polygons at finish time
- stores new entries with structured coordinate lists
- supports in-place editing of name, trackers, and polygon through an options flow

Important implications:

- the product does not impose the old 10-tracker cap
- the product does not auto-complete at 15 polygon points
- polygon editing supports keep, append, remove-last, and replace modes inside the options flow

### 3. Sensor runtime

`custom_components/custom_zone/sensor.py` contains nearly all application behaviour.

It currently does all of the following:

- reads zone name, tracker IDs, and polygon coordinates from the config entry
- validates stored polygon coordinate structure before setup
- creates exactly one `SensorEntity` per config entry
- subscribes to state changes for all configured trackers
- extracts tracker coordinates and `gps_accuracy`
- classifies tracker data into counted-in-zone, counted-out-of-zone, or unusable
- computes polygon inclusion and nearest-boundary distance
- exposes numeric aggregate state and stable aggregate attributes

State model:

- `<count> in zone`

Availability model:

- tracker degradation does not collapse aggregate availability
- malformed or unreadable zone config prevents runtime setup instead of creating a misleading active sensor

### 4. Geometry subsystem

Also inside `sensor.py`.

Contained algorithms:

- point-in-polygon via ray casting
- explicit boundary and vertex inclusion
- distance-to-boundary calculation using a local degrees-to-meters approximation

Interpretation:

- geometry is hand-rolled in-repo
- there is no external geometry dependency
- correctness rests on the custom maths and the regression tests that defend it

## Data model

Observed config entry fields:

- `name`
- `trackers`
- `zone_type`
- `coordinates`

Observed stable aggregate attributes:

- `count_in_zone`
- `count_out_of_zone`
- `count_unusable`
- `trackers_in_zone`
- `trackers_out_of_zone`
- `trackers_unusable`
- `trackers_detail`

Observed per-tracker detail fields:

- `classification`
- `diagnostic_reason`
- `counted_in_zone`
- `trusted_distance_m`
- `gps_accuracy_m`

## Verified behaviour covered by tests

The current suite exercises:

- duplicate and blank-name rejection
- empty tracker rejection
- structured coordinate storage for new entries
- repeated-point and self-intersection rejection
- no arbitrary 10-tracker or 15-point caps
- options-flow editing with stable identity across rename-based edits
- convex, concave, tiny, high-latitude, and longitude-sign-change polygons
- boundary and vertex inclusion
- representative boundary-distance calculations for inside, outside, and exact-boundary cases
- tracker degradation without aggregate outage
- stale, unavailable, missing-accuracy, invalid-coordinate, and low-confidence tracker handling
- mixed multi-tracker aggregate behaviour including all-outside and all-unusable cases
- malformed stored polygon rejection
- unload/reload lifecycle behaviour

## Accepted limitations

- polygon editing is still form-based rather than arbitrary point-level or map-based editing
- geometry is intentionally maintained without an external library

## Practical reading order

For future contributors, the fastest way to understand the repo is:

1. `README.md`
2. `docs/product-specs/custom-zone-contract.md`
3. `custom_components/custom_zone/config_flow.py`
4. `custom_components/custom_zone/sensor.py`
5. `tests/test_config_flow.py`
6. `tests/test_sensor.py`

## Summary

This repository is a compact Home Assistant custom integration whose value proposition is straightforward: polygon-based zone evaluation for existing tracker entities.

The codebase is small enough to stay explainable. The main ongoing responsibility is preserving the documented contract and the geometry/reliability test harness rather than expanding the architecture.
