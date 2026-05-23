# Contract Delta

This file tracks the gap between the desired product contract and the current implementation.

## Current state

There is no active code-versus-contract delta in the publish surface.

The current implementation matches the canonical contract for:

- zone creation with non-empty names and non-empty tracker sets
- polygon validation for repeated points and self-intersection
- zone-based sensor identity
- numeric aggregate state grammar
- aggregate availability that survives tracker degradation
- confidence gating through `gps_accuracy`, boundary distance, and staleness
- stable aggregate attributes and nested `trackers_detail`
- in-place editing through the options flow
- structured polygon storage requirements

## Canonical references

- `docs/product-specs/custom-zone-contract.md`
- `docs/RELIABILITY.md`
- `GLOSSARY.md`
- `ARCHITECTURE.md`

## Evidence basis

Current implementation evidence comes primarily from:

- `custom_components/custom_zone/config_flow.py`
- `custom_components/custom_zone/sensor.py`
- `tests/test_config_flow.py`
- `tests/test_sensor.py`

## Accepted limitations that are not contract gaps

- Polygon edits remain form-based and do not provide arbitrary point-level or map-based editing.
- Geometry remains an in-repo responsibility and should continue to be treated as a contract-critical area for future regression coverage.
- Delete-and-recreate is treated as a new config-entry lifecycle. Identity preservation is guaranteed for in-place edits, not for replacement by deletion.
