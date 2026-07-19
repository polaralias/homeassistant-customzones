# Core Beliefs

## 1. False confidence is worse than visible limitation

If tracker data is unusable, the system should prefer explicit degraded behaviour over confidently wrong zone membership.

## 2. The contract matters more than the current code

A passing implementation is not automatically the product definition. The desired end state must be written down explicitly.

## 3. Small repos still need first-class docs

A small codebase becomes hard to maintain when its behaviour lives only in one developer's memory.

## 4. Geometry is not a detail here

Polygon maths is part of the product, not just a helper. Boundary behaviour, degenerate inputs, and coordinate semantics are user-facing concerns.

## 5. Home Assistant UX is part of the product

The config flow, naming model, translations, and automation ergonomics are part of what users experience. They are not secondary polish.

## 6. Documentation should lead implementation

When behaviour is important enough to defend publicly, it should exist as a clear written rule before or alongside code.
