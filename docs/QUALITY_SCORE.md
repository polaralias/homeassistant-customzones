---
type: "Quality Standard"
title: "Quality Score"
description: "Documents Quality Score for the homeassistant-customzones repository."
timestamp: 2026-07-28T21:55:36Z
authority: canonical
verification: untested
owner: polaralias
tags:
  - homeassistant-customzones
  - quality-standard
navigation:
  role: supporting
  order: 100
---
# Quality Score

## Purpose

This file defines the quality bar the repository is trying to reach and the current assessed position against that bar.

## Current scoring model

Score each area from 0 to 5.

### Product contract

- 0: behaviour mostly implicit in code
- 3: major behaviours documented, but with material ambiguity
- 5: public behaviour explicitly defined and traceable to tests

### Verification

- 0: little or no automated evidence
- 3: key paths tested, edge cases incomplete
- 5: critical behaviour and regression risks are well covered

### Architecture clarity

- 0: hard to explain where behaviour lives
- 3: main runtime path is understandable
- 5: boundaries, risks, and responsibilities are easy to understand

### Reliability posture

- 0: failure behaviour is accidental
- 3: major failure modes are known
- 5: degraded behaviour is explicit and tested

### Public readiness

- 0: private-memory project
- 3: understandable but still rough
- 5: coherent, maintainable, and credible as a public repository

## Current score

| Area | Score | Notes |
| --- | --- | --- |
| Product contract | 5 | The main public behaviour is explicit and traceable to tests across creation, runtime, and editing. |
| Verification | 5 | The suite now covers config validation, geometry inclusion and distance, mixed tracker states, lifecycle editing, malformed stored config rejection, and unload/reload behaviour. |
| Architecture clarity | 5 | The repo is small, the main risk concentration is documented, and the runtime surface is easy to locate. |
| Reliability posture | 5 | Aggregate degradation, confidence gating, staleness, unusable-tracker handling, and partial-truth semantics are explicit and test-defended. |
| Public readiness | 5 | The repo now has aligned entry docs, explicit limitations, current package metadata, and a clear release posture. |

## Done definition for this repository

The repository is considered done for public release when all of the following remain true:

- canonical contract docs and audit docs agree on current supported behaviour
- `python -m ruff check .` passes
- `python -m pytest -q` passes
- Home Assistant manifest and workflow metadata reflect the current publish posture
- accepted limitations are explicit rather than implied by gaps or chat history

## How to keep the score high

- treat geometry and reliability changes as contract changes
- update tests, docs, and manifest metadata in the same slice as behaviour changes
- preserve a small number of strong canonical docs instead of growing note sprawl

## Repository knowledge

- [Documentation map](knowledge/documentation-map.md) — RKE-managed reading order and relationship hub.
