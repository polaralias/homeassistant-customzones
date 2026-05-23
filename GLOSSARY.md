# Glossary

Domain language for the Custom Zone integration. This file exists to keep product, verification, and future maintenance discussions precise.

## Language

**Custom Zone**:
A user-defined polygon area used to evaluate tracker presence.
_Avoid_: Area, fence, region

**Tracker**:
A Home Assistant `person` or `device_tracker` entity used as an input to zone evaluation.
_Avoid_: Device, subject, member

**Tracker Set**:
The configured set of trackers a Custom Zone evaluates.
_Avoid_: Single primary tracker, special tracker mode

**Usable Tracker**:
A tracker whose current state provides valid coordinates for zone evaluation.
_Avoid_: Healthy tracker, live tracker

**Unusable Tracker**:
A tracker whose current state cannot currently be trusted for zone evaluation.
_Avoid_: Offline tracker, broken tracker

**Diagnostic Tracker Reason**:
Optional detail explaining why a **Tracker** is currently an **Unusable Tracker**.
_Avoid_: Primary tracker state, public contract state

**Confidence Failure**:
A diagnostic reason indicating that a tracker has location data, but not enough confidence to affect zone counting.
_Avoid_: Missing data, unavailable tracker

**Stale Location**:
A diagnostic reason indicating that tracker data exists but is too old to trust for counting.
_Avoid_: Missing coordinates, live confidence failure

**Boundary Inclusion**:
The rule that a tracker on a polygon edge or vertex is treated as inside the zone.
_Avoid_: Edge exception, geometry fallback

**Boundary Clearance**:
The distance from a reported tracker position to the nearest polygon boundary.
_Avoid_: Rough zone size, implied confidence

**Counted In Zone**:
A tracker state that currently contributes to the aggregate in-zone count.
_Avoid_: Definitely present, physically confirmed inside

**Counted Out of Zone**:
A tracker state that is currently usable and not counted as inside the zone.
_Avoid_: Definitely absent, physically confirmed gone

**Trusted Distance**:
A distance-to-zone value that is only valid for a usable tracker.
_Avoid_: Best guess distance, stale distance

**Count Confidence**:
The confidence that a tracker's current location fix is good enough to affect the in-zone count.
_Avoid_: Raw GPS number, optional metadata

**Zone-Relative Confidence**:
The rule that count confidence depends on tracker accuracy in relation to the size or geometry of the zone being evaluated.
_Avoid_: One global threshold, fixed GPS rule

**Boundary-Distance Confidence**:
The rule that count confidence is determined primarily by comparing tracker accuracy against the distance to the nearest polygon boundary.
_Avoid_: Area-only confidence, coarse zone-size heuristic

**Safety Margin**:
The extra confidence buffer requiring a tracker to be comfortably inside a zone before it counts as inside.
_Avoid_: Knife-edge threshold, exact-boundary confidence

**Staleness Threshold**:
The fixed age limit beyond which tracker data is treated as too old for counting.
_Avoid_: Per-zone freshness tuning, informal timeout

**Aggregate Sensor**:
The single sensor entity that reports the zone result for all trackers configured for one Custom Zone.
_Avoid_: Zone entity, summary tracker

**Zone Identity**:
The stable identity of a Custom Zone, independent of how many trackers it currently evaluates.
_Avoid_: Tracker identity, current membership identity

**Display Name**:
The user-facing label for a Custom Zone, distinct from its stable identity.
_Avoid_: Permanent identity, automation identity

**Zone-Level Failure**:
A failure that prevents the Custom Zone itself from being evaluated at all.
_Avoid_: Tracker outage, missing update

**In-Zone Count**:
The number of trackers currently counted as inside the polygon.
_Avoid_: Presence count, occupancy count

**Numeric State Grammar**:
The rule that the aggregate sensor state is always expressed as `<count> in zone`.
_Avoid_: Mixed phrase grammar, special zero phrase

**Confidence Surface**:
The attribute-level detail that lets users judge whether the aggregate state is based on complete or degraded tracker information.
_Avoid_: Debug noise, optional metadata

**Tracker Detail Map**:
A nested attribute structure that stores per-tracker contract data keyed by full entity identity.
_Avoid_: Flat prefixed attribute sprawl, lossy short names

**Aggregate Attribute Set**:
The stable top-level attribute set that summarizes zone counts and tracker groupings.
_Avoid_: Ad hoc aggregate fields, uncontrolled attribute growth

**Full Tracker Identity**:
The full Home Assistant entity identity, including domain, used to distinguish one tracker from another.
_Avoid_: Object ID only, short tracker name

**Valid Polygon**:
A zone shape that the product accepts as a well-formed area for evaluation.
_Avoid_: Any polygon-like point set, mathematically interesting shape

## Relationships

- A **Custom Zone** has one **Aggregate Sensor**
- A **Zone Identity** belongs to the **Custom Zone**, not to any particular **Tracker**
- A **Display Name** can change without changing **Zone Identity**
- A **Custom Zone** evaluates a **Tracker Set**
- A **Tracker Set** contains one or more **Trackers**
- A **Tracker** must be **Usable** to be **Counted In Zone**
- A **Tracker** must be **Usable** to be **Counted Out of Zone**
- A **Tracker** must be **Usable** to have a **Trusted Distance**
- A **Tracker** must have sufficient **Count Confidence** to be **Counted In Zone**
- A **Tracker** must have sufficient **Count Confidence** to be **Counted Out of Zone**
- **Count Confidence** should follow **Zone-Relative Confidence**
- **Zone-Relative Confidence** should be evaluated primarily through **Boundary-Distance Confidence**
- **Boundary-Distance Confidence** should include a **Safety Margin**
- A **Tracker** with missing or invalid accuracy data is not **Usable**
- A **Tracker** older than the **Staleness Threshold** is not **Usable**
- An **In-Zone Count** is derived only from trackers currently **Counted In Zone**
- The **Aggregate Sensor** uses **Numeric State Grammar** to expose the **In-Zone Count**
- The **Confidence Surface** exposes which **Trackers** are usable, unusable, counted in zone, or counted out of zone
- The **Confidence Surface** should key per-tracker detail by **Full Tracker Identity**
- The **Confidence Surface** should preferably expose per-tracker detail through a **Tracker Detail Map**
- The **Aggregate Sensor** should expose a stable **Aggregate Attribute Set**
- A **Custom Zone** should be created only from a **Valid Polygon**
- **Boundary Inclusion** means edge and vertex positions still count toward the **In-Zone Count**
- **Boundary Clearance** influences whether **Boundary Inclusion** is trusted enough for counting
- An **Unusable Tracker** must not make the **Aggregate Sensor** unavailable by itself
- A **Diagnostic Tracker Reason** may explain an **Unusable Tracker** without becoming the main public state model
- **Confidence Failure** is a **Diagnostic Tracker Reason**
- **Stale Location** is a **Diagnostic Tracker Reason**
- A **Zone-Level Failure** can make the **Aggregate Sensor** unavailable

## Example dialogue

> **Dev:** "If one **Tracker** loses coordinates but another is still inside the **Custom Zone**, should the **Aggregate Sensor** go unavailable?"
> **Domain expert:** "No. The bad input becomes an **Unusable Tracker**, but the **Aggregate Sensor** should still report the current **In-Zone Count** from the remaining **Usable Trackers**."

## Flagged ambiguities

- "unavailable" was being used both for a single bad tracker and for the whole aggregate result — resolved: a tracker can be unusable without making the **Aggregate Sensor** unavailable
- "all out of zone" implied complete certainty across all trackers — resolved: the canonical zero-membership aggregate state is `0 in zone`
- "state wording" could have mixed numeric and phrase-based variants — resolved: **Numeric State Grammar** means the aggregate state is always `<count> in zone`
- "failure" was ambiguous between tracker degradation and aggregate failure — resolved: only a **Zone-Level Failure** should make the **Aggregate Sensor** unavailable
- "missing coordinates" and "invalid coordinates" sounded like zone-authoring failures — resolved: those are runtime tracker-data reasons under the broader **Unusable Tracker** concept
- "`unknown` and `unavailable` could have become separate public states" — resolved: they may remain separate **Diagnostic Tracker Reasons**, but they collapse into the public concept of **Unusable Tracker**
- "on the line" could have been treated as outside or special-case undefined — resolved: **Boundary Inclusion** means edge and vertex points are inside
- "boundary inside" and "countable inside" could have been conflated — resolved: **Boundary Inclusion** is geometric, while **Boundary Clearance** governs count confidence
- "unusable" could have hidden the difference between missing data and low-confidence data — resolved: **Confidence Failure** is a distinct **Diagnostic Tracker Reason**
- "low-confidence inside" and "low-confidence outside" could have become separate diagnostic states — resolved: **Confidence Failure** is one symmetric **Diagnostic Tracker Reason**
- "`0 in zone` could be read as 'everyone is confirmed outside'" — resolved: it means no tracker is currently **Counted In Zone**, while unusable trackers remain visible in attributes
- "tracker attributes" could have been treated as unstable debug spill — resolved: **Counted In Zone**, **Counted Out of Zone**, and **Unusable Tracker** are stable contract-level distinctions
- "distance" could have been left stale on a bad tracker — resolved: only a **Usable Tracker** can have a **Trusted Distance**
- "accuracy" could have been treated as display-only metadata — resolved: **Count Confidence** affects whether a tracker is counted in zone
- "accuracy threshold" could have become one global cutoff — resolved: **Zone-Relative Confidence** ties count trust to zone size or geometry
- "zone-relative confidence" could have been reduced to polygon area alone — resolved: **Boundary-Distance Confidence** is the preferred primary rule
- "accuracy versus boundary distance" could have become a knife-edge rule — resolved: **Safety Margin** is part of count confidence
- "safety margin" could have become a per-zone tuning burden — resolved: the initial **Safety Margin** factor is fixed across zones
- "confidence factor" could have remained hand-wavy — resolved: the initial **Safety Margin** factor is `0.75`
- "count confidence" could have applied only to inside classification — resolved: **Count Confidence** gates both **Counted In Zone** and **Counted Out of Zone**
- "inside confidence" and "outside confidence" could have diverged into separate rules — resolved: **Boundary-Distance Confidence** applies symmetrically on both sides
- "missing accuracy" could have fallen back to pure geometry — resolved: a tracker without usable accuracy data is not **Usable**
- "stale data" could have remained silently trusted — resolved: **Stale Location** makes a tracker not **Usable**
- "fresh enough" could have remained undefined — resolved: the initial **Staleness Threshold** is `5 minutes`
- "single-tracker naming" could have made tracker membership part of identity — resolved: **Zone Identity** is stable and tracker membership must not be encoded into the aggregate sensor entity ID
- "single-tracker mode" could have become a separate product concept — resolved: a **Tracker Set** is the canonical model, and one tracker is just the one-element case
- "empty zone" could have been treated as a valid configuration — resolved: a **Tracker Set** must contain at least one **Tracker**
- "10 trackers max" could have been mistaken for a product rule — resolved: an arbitrary small fixed tracker cap is not part of the intended contract
- "15 polygon points max" could have been mistaken for a product rule — resolved: an arbitrary small fixed polygon-point cap is not part of the intended contract
- "minimum polygon size" could have been treated as just a UI rule — resolved: a **Valid Polygon** requires at least 3 distinct points
- "zone rename" could have been treated as identity replacement — resolved: **Display Name** can change while **Zone Identity** remains stable
- "polygon edits" could have been treated as a new zone identity — resolved: geometry changes are configuration changes, not **Zone Identity** replacement
- "tracker-set edits" could have been treated as a new zone identity — resolved: tracker membership changes are configuration changes, not **Zone Identity** replacement
- "`0 in zone` with all trackers unusable could have implied sensor failure" — resolved: the aggregate state remains numeric, while the **Confidence Surface** carries degraded-trust detail
- "per-tracker attributes" could have collided across domains — resolved: the **Confidence Surface** uses **Full Tracker Identity**
- "per-tracker attributes" could have sprawled into many flat keys — resolved: the preferred shape is a **Tracker Detail Map**
- "flat compatibility aliases" could have become accidental long-term contract — resolved: the forward contract is the **Tracker Detail Map**
- "aggregate attributes" could have grown ad hoc — resolved: the forward contract uses a stable **Aggregate Attribute Set**
- "self-intersection" could have been treated as a supported advanced polygon case — resolved: a **Valid Polygon** excludes self-intersecting shapes
- "repeated points" or "zero-length edges" could have been silently normalized — resolved: a **Valid Polygon** excludes those authoring errors and they should be rejected
- "point order" could have become a hidden correctness burden — resolved: a **Valid Polygon** treats clockwise and counter-clockwise ordering as equivalent
- "polygon closure" could have required the user to repeat the first point — resolved: a **Valid Polygon** closes implicitly and repeated points are rejected
