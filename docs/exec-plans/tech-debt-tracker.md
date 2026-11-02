---
type: "Delivery Plan"
title: "Tech Debt Tracker"
description: "Documents Tech Debt Tracker for the homeassistant-customzones repository."
timestamp: 2026-07-28T21:55:36Z
authority: canonical
verification: untested
owner: polaralias
tags:
  - homeassistant-customzones
  - delivery-plan
navigation:
  role: supporting
  order: 100
---
# Tech Debt Tracker

This file tracks explicit debt with user or maintenance consequences.

## Current state

There is no active tech debt in the current publish surface.

The remaining product constraints are intentional and already documented in canonical docs rather than tracked here as debt:

- [README.md](../../README.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [docs/FRONTEND.md](../FRONTEND.md)
- [docs/product-specs/custom-zone-contract.md](../product-specs/custom-zone-contract.md)

## Reopen criteria

Add an item here only when all of the following are true:

- the issue is real and current
- it has user or maintenance consequences
- it is not already an intentional, accepted product constraint
- it needs tracked follow-up rather than just clearer documentation

## Repository knowledge

- [Documentation map](../knowledge/documentation-map.md) — RKE-managed reading order and relationship hub.

## Reliability fixes in 1.1.0

Version 1 entries migrate JSON-encoded or structured polygons into validated version 2 structured coordinates. Migration keeps the config entry ID and sensor identity; malformed polygons remain untouched and fail migration for repair. Renaming updates name uniqueness without replacing the sensor. Invalid final points can be corrected in the same form.

Boundary tolerance is perpendicular to each edge rather than dependent on its length. Runtime coordinates must be finite, within geographic ranges and not Boolean; accuracy must be finite and positive. A cancellable 30-second sweep expires silent trackers after the existing five-minute threshold, even without another state event.

Regression coverage includes small diagonal polygons, legacy migration, timer expiry/unload, rename collisions and non-finite inputs. Linux CI checks HA 2025.1.4/Python 3.12 and HA 2026.10.4/Python 3.14. This does not establish the accuracy of a phone's GPS observations.
