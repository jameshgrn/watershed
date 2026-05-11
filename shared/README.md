# shared/

**Typed contracts that cross module boundaries.**

`shared/` is the keystone of the lab. Everything that flows between modules is typed here. No module mutates these contracts unilaterally.

## Planned types

| type | logical owner | crosses into |
|---|---|---|
| `Run` | distributary | tributary, flume, mosaic, strata |
| `Plan` | distributary | tributary |
| `Deposit` | distributary → tributary | (only those two) |
| `Merge` | tributary | bedrock (snapshots) |
| `Baseline` | tributary | distributary (next-run anchoring) |
| `Dataset` | bedrock | quarry |
| `Schema` | bedrock | quarry |
| `Policy` | bedrock | quarry, distributary (governance can require) |
| `RawArtifact` | quarry | (internal mostly) |
| `Transform` | quarry | (internal mostly) |
| `Operator` | flume | strata, mosaic |
| `Artifact` | flume | mosaic, strata |
| `Lineage` | flume | mosaic, strata, tributary |
| `Figure` (Artifact) | mosaic | strata |
| `Reference` | outcrop | strata |
| `ReadingList` | outcrop | (internal mostly) |
| `Manuscript` | strata | mosaic, outcrop |
| `Section` | strata | mosaic (figure refs), outcrop (citation refs) |
| `PressureTest` | flume | distributary (governance can require) |

## Why this exists

Without `shared/`, you have eight tools that share a directory. With it, you have a lab. The contracts are what allow:

- `strata` to ask `mosaic` "is this figure still current for run_id=..." without importing mosaic internals
- `distributary` to govern a multi-module run that touches `flume → mosaic → strata` because they all speak `Run` and `Artifact`
- `tributary` to validate an agent's `Deposit` against the contract it claims to satisfy without knowing which module produced it
- `outcrop` to provide citations that `strata` binds by `Reference.id` without touching outcrop internals

## Where contracts emerge from

Many contracts already exist *implicitly* in the existing quarry's registry (`Artifact`, `Lineage`) and dgov's plan / run model (`Plan`, `Run`). Migration involves lifting these to `shared/` as canonical types, then having modules depend on the shared definitions instead of their own.

## Status

Placeholder. Types will be defined as the migration proceeds.
