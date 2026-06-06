# Brief 18 — tributary Deposit v0

State: accepted
Compiled by: Watermaster Avulsion
Compiled at: 2026-05-28
Engineer: Watermaster Avulsion

## Source Utterance

"okay sounds good. proceed"

## Context

Distributary can now produce terminal `DispatchRun` records through `WorkerReturn`. Tributary may begin only with the typed seam record it consumes: `Deposit`.

Relevant discipline:

- `/Users/jakegearon/projects/watershed/sops/deposit-shape.md`
- `/Users/jakegearon/projects/watershed/sops/dispatch-run-shape.md`
- `/Users/jakegearon/projects/watershed/sketches/dgov-to-watershed-port-map.md`
- `/Users/jakegearon/projects/watershed/SKETCHES.md`

## Write Scope

- `/Users/jakegearon/projects/watershed/tributary/pyproject.toml`
- `/Users/jakegearon/projects/watershed/tributary/uv.lock`
- `/Users/jakegearon/projects/watershed/tributary/src/tributary/**`
- `/Users/jakegearon/projects/watershed/tributary/tests/**`
- `/Users/jakegearon/projects/watershed/tributary/README.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/**`
- `/Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md`

## Build

Scaffold a minimal uv-managed `tributary` Python package with:

- `Deposit`
- `DepositState`
- `FileChangeSet`
- state-specific file change records for create, modify, and delete
- `derive_deposit_id`
- a `submit_deposit_from_dispatch_run` helper that accepts a protocol-shaped dispatch record and rejects anything not in `state == "done"`

Design constraints:

- `Deposit.id` is content-derived with `deposit:` prefix from `(from_dispatch_run_id, claims, file_changes, commit_ref)`.
- `FileChangeSet` is content-addressed data supplied to tributary, not discovered by tributary.
- File changes must carry content hashes in the positions required by their change kind.
- Claims must be non-empty typed-contract strings. Do not build the shared claim registry in this slice.
- Do not import `distributary` at runtime from `tributary`; validate the dispatch record by protocol shape and `disprun:` identity.

## Non-Goals

- No Validation, Merge, Baseline, sentrux, or registry.
- No git diff, worktree inspection, file IO, or subprocess.
- No direct dgov imports.
- No claim registry beyond local syntactic checks.
- No persistence, event store, or CLI.
- No lifecycle transition helpers that imply validation or merge has happened.

## Verification

From `/Users/jakegearon/projects/watershed/tributary`:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest -q tests/test_deposit.py
```
