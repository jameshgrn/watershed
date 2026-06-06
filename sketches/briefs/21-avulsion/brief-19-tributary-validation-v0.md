# Brief 19 — tributary Validation v0

State: accepted
Compiled by: Watermaster Avulsion
Compiled at: 2026-05-28
Engineer: Watermaster Avulsion

## Source Utterance

"if you feel capable still watermaster avulsion (my phd thesis <3) then lets keep going"

## Context

Tributary can now ingest submitted `Deposit` records. The next narrow slice is a `Validation` record over a submitted Deposit, starting with supplied-data integrity rather than semantic settlement.

Relevant discipline:

- `/Users/jakegearon/projects/watershed/sops/validation-shape.md`
- `/Users/jakegearon/projects/watershed/sops/deposit-shape.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/return-18.md`

## Write Scope

- `/Users/jakegearon/projects/watershed/tributary/src/tributary/**`
- `/Users/jakegearon/projects/watershed/tributary/tests/**`
- `/Users/jakegearon/projects/watershed/tributary/README.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/**`
- `/Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md`

## Build

Add v0 Validation support:

- `Validation`
- `ValidationVerdict`
- `ValidationCheck`
- `SchemaPin`
- `derive_validation_id`
- `validate_deposit_integrity`
- a pure helper deriving the Deposit state authorized by a Validation verdict

The integrity validator may check only:

- the Deposit is in `state == "submitted"`
- every Deposit claim appears in an explicitly supplied `known_claims` tuple
- the Deposit's existing `FileChangeSet` has stable content identity

## Non-Goals

- No Deposit mutation.
- No registry or persistence.
- No Merge, Baseline, sentrux, or event emission.
- No pressure-test execution.
- No schema-check execution.
- No semantic settlement.
- No shared claim registry beyond explicitly supplied known claims.
- No dgov imports.

## Verification

From `/Users/jakegearon/projects/watershed/tributary`:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest -q tests/test_validation.py tests/test_deposit.py
```
