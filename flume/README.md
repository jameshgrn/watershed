# flume/

**Strict-typed scientific workshop.** Where the science actually runs.

## Provenance

Strict-typed scientific operators carved out of existing `quarry/` — D8, Priority-Flood, flow accumulation, registry, lineage, pressure-tests. The science floor.

## What it owns

- **Operators** — first-class typed scientific operations (D8 flow direction, Priority-Flood depression filling, flow accumulation, ...) — each takes typed input, emits typed output
- **Registry** — every operator output registered with content hash + lineage
- **Lineage** — the DAG of which artifacts produced which
- **Pressure tests** — invariant checks fired on every operator
- **Lanes** — operator / executor separation (orchestrator-style work moves to quarry)

## Public types it exposes (planned)

- `Operator` — a typed scientific operation with strict input/output types
- `Artifact` — anything an operator produces
- `Lineage` — the DAG of artifact provenance (likely lifted to `shared/`)
- `PressureTest` — a checkable invariant about an operator's behavior

## Type discipline

**Flume refuses non-canonical input.** Everything that enters the workshop is already typed by quarry's transforms. The strict discipline is what makes the science reproducible — no operator inside flume needs to wonder whether its input is well-formed.

## Why "flume"

A flume is an engineered channel where you run hydraulic experiments — control the flow, measure the response, observe the dynamics. That's what the workshop is. Where the actual science happens.

## Status

Placeholder. Awaiting migration of strict-typed operators from existing `~/projects/quarry/`. Existing `~/projects/gauges/` likely contributes — a stream gauge's role *is* a flume measurement.
