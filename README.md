# Custom Zone

Custom Zone is a Home Assistant custom integration for polygon-based zones.

It lets a user:

- define an arbitrary polygon in the Home Assistant UI
- attach one or more `person` or `device_tracker` entities to that polygon
- expose a single sensor that reports how many tracked entities are currently counted inside the zone

## Repository status

This repository is now in a publish-ready state:

- the product contract is explicit
- the main runtime and lifecycle behavior is test-defended
- the active docs describe current verified behavior
- no active code-versus-contract delta remains

## Start here

Read these in order:

1. [AGENTS.md](AGENTS.md)
2. [ARCHITECTURE.md](ARCHITECTURE.md)
3. [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md)
4. [docs/RELIABILITY.md](docs/RELIABILITY.md)
5. [docs/SECURITY.md](docs/SECURITY.md)
6. [docs/product-specs/custom-zone-contract.md](docs/product-specs/custom-zone-contract.md)
7. [GLOSSARY.md](GLOSSARY.md)
8. [CODEBASE_MAP.md](CODEBASE_MAP.md)
9. [CONTRACT_DELTA.md](CONTRACT_DELTA.md)
10. [AUDIT_CHECKLIST.md](AUDIT_CHECKLIST.md)
11. [docs/PLANS.md](docs/PLANS.md)

Supporting status docs:

- [docs/QUALITY_SCORE.md](docs/QUALITY_SCORE.md)
- [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md)

## Verified local baseline

The current local publish baseline is:

- `python -m ruff check .`
- `python -m pytest -q`

The current test suite passes with 48 tests.

## Installation

### HACS

1. Go to **HACS** > **Integrations**.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add the repository URL.
4. Choose **Integration** as the category.
5. Install **Custom Zone**.
6. Restart Home Assistant.

### Manual installation

1. Copy `custom_components/custom_zone` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Verified user-visible behavior

Configuration is done through the Home Assistant UI.

Verified flow:

1. Add the **Custom Zone** integration.
2. Enter a non-empty unique zone name.
3. Select one or more `person` or `device_tracker` entities.
4. Add polygon points one at a time.
5. Finish once at least 3 distinct valid points exist.
6. Use the integration options flow to rename the zone, change trackers, or edit the polygon in place later.

The integration creates one aggregate sensor per zone:

- `sensor.customzone_<zone>`

The aggregate sensor state grammar is stable:

- `<count> in zone`

Stable aggregate attributes:

- `count_in_zone`
- `count_out_of_zone`
- `count_unusable`
- `trackers_in_zone`
- `trackers_out_of_zone`
- `trackers_unusable`
- `trackers_detail`

Current counting rules:

- boundary points are geometrically inside
- tracker degradation does not collapse aggregate availability
- a tracker without usable `gps_accuracy` is not counted
- a stale tracker fix older than 5 minutes is not counted
- a low-confidence near-boundary fix is not counted even when geometry alone says inside

## Accepted limitations

- Polygon editing in the options flow supports keeping the current polygon, appending points, removing the last point and continuing, or replacing the full polygon. There is still no arbitrary point-level inline editor or map-based polygon editor.
- Geometry is intentionally implemented in-repo rather than through an external geometry dependency. Future changes to polygon math should be treated as contract changes and kept test-defended.

## Release approach

- Patch releases should be used for documentation, verification, packaging, and non-breaking behavioral fixes.
- Minor releases should be used for additive behavior that does not change entity identity, state grammar, or stable attribute names.
- Major releases should be reserved for intentional breaking contract changes such as entity ID, state grammar, or stable attribute compatibility changes.
