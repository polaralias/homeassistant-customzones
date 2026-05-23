# AGENTS

This repository is being converted from "mostly works" into a small, public, defensible Home Assistant integration.

## Operating stance

- Treat docs as claims until verified.
- Treat code as implementation intent, not automatic truth.
- Do not refactor first.
- Lock down the product contract before redesigning internals.
- Prefer explicit behavior rules over inferred convention.

## Current repo priorities

1. defend the documented product contract with stronger verification
2. close the remaining code-versus-contract gaps in small slices
3. keep docs, tests, and plan surfaces aligned in the same tranche
4. improve internals only after behavior is explicit and defended

## Where to start

Read in this order:

1. `README.md`
2. `ARCHITECTURE.md`
3. `docs/PRODUCT_SENSE.md`
4. `docs/RELIABILITY.md`
5. `docs/SECURITY.md`
6. `docs/product-specs/custom-zone-contract.md`
7. `GLOSSARY.md`
8. `CODEBASE_MAP.md`
9. `CONTRACT_DELTA.md`
10. `AUDIT_CHECKLIST.md`
11. `docs/PLANS.md`

## Repo invariants

- The main product value is polygon-based zone evaluation for Home Assistant tracker entities.
- The main risk concentration is `custom_components/custom_zone/sensor.py`.
- The current frontend surface is the Home Assistant config flow, translations, and branding assets.
- Geometry correctness is product-critical.
- Availability semantics are product-critical.

## Documentation rules

- Outcome docs describe the desired end state.
- Audit docs describe verified current state.
- If the two differ, keep both and make the gap explicit.
- Avoid generic process docs that do not help operate or verify this integration.

## Engineering workflow

Before changing behavior:

1. identify the relevant contract doc
2. identify the existing tests
3. identify what is still unknown
4. make the contract more explicit if needed
5. only then change code

After changing behavior:

1. update tests
2. update the relevant product/reliability/security docs
3. update plan or tech debt docs if the change closes or opens work

## Definition of useful work here

Useful work has at least one of these outcomes:

- a clearer product contract
- stronger verification
- narrower ambiguity
- lower operational risk
- better public explainability

If a proposed change does not improve one of those, it is probably premature.
