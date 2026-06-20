# Brief 20 — tributary validation application

State: accepted
Compiled by: Watermaster Avulsion
Compiled at: 2026-05-28
Engineer: Watermaster Avulsion

## Source Utterance

"proceed"

## Context

Tributary has submitted `Deposit` records and frozen `Validation` records. The next slice is the smallest in-memory application surface: use a Validation verdict to return the authorized Deposit state without persistence or merge.

Relevant discipline:

- `/Users/jakegearon/projects/watershed/sops/deposit-shape.md`
- `/Users/jakegearon/projects/watershed/sops/validation-shape.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/return-19.md`

## Write Scope

- `/Users/jakegearon/projects/watershed/tributary/src/tributary/**`
- `/Users/jakegearon/projects/watershed/tributary/tests/**`
- `/Users/jakegearon/projects/watershed/tributary/README.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/**`
- `/Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md`

## Build

Add a pure helper:

- `apply_validation_to_deposit(deposit: Deposit, validation: Validation) -> Deposit`

Behavior:

- require `validation.deposit_id == deposit.id`
- require `deposit.state == "submitted"` before applying any Validation
- `pass` returns a new frozen Deposit with `state == "validated"` and the same id
- `fail` returns a new frozen Deposit with `state == "rejected"` and the same id
- `needs_human` returns the submitted Deposit unchanged

## Non-Goals

- No registry or persistence.
- No mutation.
- No Merge, Baseline, sentrux, repository operations, or event emission.
- No applying stale/latest Validation ordering.
- No human override workflow.
- No dgov imports.

## Verification

From `/Users/jakegearon/projects/watershed/tributary`:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest -q tests/test_validation.py tests/test_deposit.py
```
