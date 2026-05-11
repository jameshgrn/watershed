---
name: schema-versioning
title: Schema Versioning
summary: How bedrock-registered Dataset schemas evolve. Monotonic integer version with change-class classification. Frozen-pin truth model — prior versions stay valid; evolution is a new computation; migration is a typed operator.
applies_to: [schema, version, evolution, migration, dataset, bedrock, lineage, change]
priority: must
version: 1
authored_by: Watermaster Thalweg
inscribed: 2026-05-07
canon_anchor: Articles II, IV
---

## When

- proposing a new bedrock-registered Dataset schema
- evolving an existing bedrock-registered Dataset schema
- migrating Artifacts pinned to a prior schema version up to a current version
- resolving a schema-version mismatch between an Artifact and a downstream consumer

## Do

- assign every Dataset schema a monotonic integer `version` field; start at 1; increment on every accepted change
- classify every schema change as exactly one of: `additive` (new optional field; new enum value with default; widened numeric type), `breaking` (removed field; renamed field; narrowed type; semantically changed field), or `cosmetic` (description text; validator-message wording; no contract change)
- record `schema_version` and `change_class` on the Dataset's lineage anchor at registration time
- include `schema_version: int` in the Lineage record of every Artifact registered against the Dataset; this version travels with the Artifact through every downstream operation
- treat Artifacts registered under a prior schema version as frozen-pinned: they remain valid against the version they were produced under in perpetuity
- when a downstream consumer needs an Artifact under a different schema version, materialize a new Artifact via a typed `MigrateOperator` in flume; the source Artifact is the input, the target Artifact carries new lineage referencing the source artifact_id, source schema_version, and migration params
- preflight every `breaking` change per `watermaster-preflight.md`; `additive` and `cosmetic` changes still increment `version` and pass through the verify checks below, but do not require preflight
- archive prior schema versions per bedrock's versioning policy (parallel to SOP archival under `_archive/`)

## Do Not

- mutate a registered schema in place — every change increments the version
- treat schema evolution as a textual edit; it is a typed event with a change-class
- migrate Artifacts in-place under an evolved schema; a migration produces a new Artifact with new lineage and a new artifact_id
- read an Artifact under a schema version other than the one its lineage declares without an explicit `MigrateOperator` step
- omit `schema_version` from Artifact lineage at registration time; absence is not a default
- classify a `breaking` change as `additive` to bypass preflight
- introduce parallel version axes (semver, content-hash, date-stamp) for the same Dataset; integer + change-class is the canonical model

## Verify

- every Dataset registered in bedrock carries a `version: int` and the `change_class` of its most recent transition
- every Artifact's Lineage record declares the `schema_version` of the Dataset it was registered against
- a query for "Artifacts pinned to schema v_N of Dataset D" returns exactly those whose lineage matches; no shadowing
- a `MigrateOperator` run produces a downstream Artifact whose lineage references both the source artifact_id and the source schema_version
- prior schema versions are recoverable by version number; the registry returns a typed Schema object for each
- a downstream consumer that accepts only `schema_version >= K` rejects, with a typed error, any Artifact pinned to an older version

## Escalate

- if a proposed change cannot be classified as `additive`, `breaking`, or `cosmetic` without distortion
- if the same field needs to be both added and removed in a single evolution — decompose into two versions
- if migration cost makes frozen-pin operationally untenable for a specific Dataset (rare; usually a sign the schema design is wrong, not the SOP)
- if two Datasets have an effective shared schema that must evolve in lockstep — propose explicit cross-Dataset schema linking before either evolves
- if a consumer's version-acceptance contract becomes broader than `>= K` (open-ended unions are usually a smell)
