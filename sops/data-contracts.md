---
name: data-contracts
title: Data Contracts
summary: The artifact-level discipline for typed data. Identity, the Connector boundary, fresh metadata, mutability rules, and the three-state temporal contract.
applies_to: [artifact, connector, materialize, lineage, metadata, spatial, temporal, schema, mutability]
priority: must
version: 2
authored_by: Watermaster Reach
inscribed: 2026-05-06
canon_anchor: Articles II, III, IV
---

## When

- producing an Artifact (any module that creates one)
- writing a Connector or modifying an existing one
- writing an Operator or modifying an existing one
- defining or evolving an Artifact-shaped schema
- reviewing code that creates, mutates, or registers an Artifact

## Do

- treat the Artifact's `id` as the only identity; never identify by path, name, or backing-store URI
- materialize untyped reality through a Connector and only through a Connector
- emit a `MaterializeResult` from every Connector materialize call: artifact + strategy + source_ref + notes
- regenerate the output Artifact's spatial and temporal metadata from the actual output file; never copy from input
- attach a `Lineage` record to every Artifact at creation: operation, input_ids, params, timestamp, executor_id; for Artifacts registered against a bedrock Dataset, additionally include `schema_version: int` per `schema-versioning.md`
- treat `Artifact.metadata` as opaque connector-extension context only; never as authoritative for typed fields
- strip duplicate spatial keys (`crs`, `extent`, `bounds`, `resolution`, `feature_count`, `band_count`) and temporal keys (`temporal_start`, `temporal_end`, `temporal_resolution`, `temporal_observation_count`) at Artifact construction
- represent temporal in three states: `Artifact.temporal = None` (no contract), `TemporalDescriptor(start=None, end=None)` (declared but unknown), `TemporalDescriptor(start=t, end=t)` (known); UTC tz-aware required
- preserve the source `SourceRef` in lineage when it reveals provenance (catalog item, database ref, etc.)
- represent operator failure as `RunStatus.FAILED` on the returned RunRecord; never as a fabricated side channel

## Do Not

- mutate `id`, `lineage`, or `backing` after Artifact construction
- depend on metadata keys for operator behavior
- copy spatial or temporal metadata from input artifacts to output artifacts
- accept untyped data anywhere except at a Connector
- materialize through a path that bypasses the Connector protocol
- represent absence of temporal information as a special timestamp value (epoch zero, far future); use the typed three-state pattern
- store the same fact in both a typed contract field and a metadata key
- shadow a typed contract field (spatial, temporal, lineage) with a metadata entry

## Verify

- the Artifact's `id` is content-derived and stable across re-materialization of the same source bytes via the same Connector with the same parameters
- output spatial metadata matches the actual output file (run rasterio/fiona/etc. on the produced file and compare)
- the Lineage record on an output Artifact references real input Artifact ids
- `Artifact.metadata` does not contain any of the stripped keys after construction
- temporal state matches one of the three legal patterns; naive datetimes are rejected at construction
- a failing operator surfaces a FAILED RunRecord; nothing else

## Escalate

- if a Connector cannot materialize without violating the typed-output contract (raw bytes, malformed spatial reference, etc.)
- if an Operator legitimately needs to copy spatial metadata from input (rare; usually a smell)
- if a third temporal model becomes necessary (paleo, year-only, decade) — defer until the case is real
- if the metadata-stripping rules block a legitimate use of metadata for context (likely fixable by promoting the field to typed)
- if the boundary between Connector and Operator becomes unclear in a new module
