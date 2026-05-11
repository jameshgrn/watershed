# tributary/

**Agent ingest, validation, merge.** Where work fans back in.

## Provenance

Half of `dgov/` — the fan-in half. Ingest, validate, merge, baseline (sentrux).

## What it owns

- **Ingest** — receive typed agent outputs from distributary's worktrees
- **Validation** — check that outputs satisfy the typed contracts
- **Merge** — bring valid outputs back into the main trunk
- **Baseline** — sentrux-backed reproducibility snapshot at merge points

## Public types it exposes (planned)

- `Deposit` — a typed proposed change emitted by an agent
- `Validation` — pass/fail report against the contract a Deposit claims to satisfy
- `Merge` — a record of a successful integration of a Deposit back to main
- `Baseline` — a sentrux snapshot anchoring a known-good state

## Why "tributary"

In a river system, tributaries are smaller channels flowing *into* a larger one — the inverse of a distributary. In agentic terms: many parallel agent outputs flowing back into the main trunk after validation.

The metaphor goes the right way: tributary is *inflow*. Work returns here, gets vetted, joins the main channel.

## Pair

`distributary/` is the matched fan-out. Together they replace dgov, with the dispatch/ingest split made explicit by separate modules.

## Why split dgov in two

Different invariants on each side. Distributary is concerned with *creating valid work* (planning, dispatch, governance of in-flight runs). Tributary is concerned with *certifying completed work* (typed validation, merge integrity, baseline anchoring). Combining them in one module hid that asymmetry; splitting them makes each phase auditable on its own terms.

## Status

Placeholder. Awaiting migration from `~/projects/dgov/` (fan-in half of the split).
