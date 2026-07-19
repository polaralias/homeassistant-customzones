# Product Sense

## Why this should exist

The product only earns its place if it solves a real limitation in Home Assistant's built-in zoning model.

That limitation is shape fidelity.

Circular zones are a poor fit for many real-world spaces. A polygon can express:

- a driveway without including a road
- a garden without including a neighbouring plot
- an approach path without including an entire property

## What a good version of this product feels like

- easy to configure
- conservative when data quality is poor
- predictable in automations
- explicit about what it knows and does not know

## Product failure modes

- reporting a false exit because a tracker stopped publishing coordinates
- unstable naming that breaks automations
- undocumented edge behaviour for points on boundaries
- geometry behaviour that is only accidentally correct

## Product standard

The product should be understandable to:

- a Home Assistant user installing it from HACS
- a contributor reading the repo cold
- an employer reviewing the public codebase as evidence of engineering judgement
