# quarry/

**Data orchestration.** Connectors, transforms, the untyped→typed boundary.

## Provenance

Carved from existing `quarry/`. Keeps the connector / transform / ETL portion. The strict-typed scientific operators (D8, Priority-Flood, flow accumulation) move to `flume/`.

## What it owns

- **Connectors** — bridges to external data sources (SWORD, ICESat-2, Sentinel-2, gauges, etc.)
- **Transforms** — operations that convert raw / external / messy inputs into the canonical typed forms `flume/` consumes
- **Adapter lane** — the lane in your existing quarry that handles I/O against external systems
- **The boundary** — quarry is where untyped reality meets the lab's strict type discipline

## Public types it exposes (planned)

- `Connector` — a typed bridge to an external data source
- `Transform` — an operation that takes one type and emits another (often: untyped → typed)
- `RawArtifact` — typed handle to data that hasn't yet been canonicalized
- `IngestPlan` — the chain of transforms required to canonicalize a `RawArtifact`

## Why "quarry"

You quarry the substrate to extract material. Bedrock holds canonical data + schemas; quarry is where you actively pull from bedrock (and from external sources) and transform it into something flume can use. The dynamic-extraction sense of quarry is what fits — not the static-rock-pile sense.

## Type discipline

Quarry is the only module in the lab that *accepts non-canonical input* and *emits canonical typed output*. Everything downstream (flume, mosaic, strata) refuses non-canonical input. Quarry is the boundary; the rest of the lab is interior.

## Status

Placeholder. Awaiting carve-up of existing `~/projects/quarry/`. Connectors and transforms stay; scientific operators move to flume.
