# bedrock/

**Canonical data store + policy layer.** Source of truth.

## Provenance

New module. Consolidates existing data layouts (local Postgres, life-db, on-disk artifacts, cloud buckets) under one substrate with schema-defined contracts and policy alignment.

## What it owns

- **Canonical data** — the authoritative version of every dataset the lab uses
- **Schemas** — typed definitions for what each dataset must conform to
- **Policy** — versioning, retention, access, lineage requirements
- **Pointers** — registry of where data physically lives (local Postgres, S3, GCS, etc.) abstracted behind typed handles

## Public types it exposes (planned)

- `Dataset` — a typed handle to canonical data; wraps the physical location
- `Schema` — the contract a dataset must satisfy
- `Policy` — versioning + retention + access rules attached to a dataset
- `Pointer` — an opaque reference to physical storage that satisfies a policy

## Why "bedrock"

The substrate. Doesn't move while the rest of the watershed flows over it. Naming the data + policy layer `bedrock` says exactly what its role is: foundation everything else operates against.

## Status

Placeholder. The biggest *new conceptual* lift in the lab — most data currently lives in ad-hoc places. Migration involves consolidating + schematizing.
