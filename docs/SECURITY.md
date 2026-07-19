# Security

## Scope

This integration is local and narrow in scope. It does not currently present as an authentication-heavy or network-heavy system.

That does not remove the need for a security posture.

## Security principles

- minimise trust in malformed input
- validate user-provided coordinates conservatively
- fail safely on invalid configuration data
- avoid broad attack surface expansion without clear product need

## Current security-relevant surfaces

### Config input

The config flow accepts:

- zone names
- entity selections
- coordinate input

These should be treated as untrusted input until validated.

### Stored configuration

Polygon coordinates are persisted in config entry data. The repository should define and defend the accepted shape of that data.

### Runtime state ingestion

Tracker entity states come from Home Assistant state. Missing or malformed coordinate data should never be treated as trustworthy location truth.

## Current verified posture

- invalid or malformed input is rejected or degraded safely
- configuration parsing does not create silent bad state
- runtime data quality failures do not masquerade as real-world movement

## Current note

Security risk in this repository is more about input trust and safe degradation than about classic auth or internet exposure. The docs and tests should reflect that reality instead of pretending this repo has a different threat model.
