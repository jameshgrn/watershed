# Return 20 — tributary validation application

Brief: `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/brief-20-tributary-validation-application.md`
Engineer: Watermaster Avulsion
Returned at: 2026-05-28

## Summary

Added `apply_validation_to_deposit(deposit, validation)`, a pure in-memory lifecycle helper. It verifies Validation identity against the Deposit, requires the Deposit to be `submitted`, and returns the authorized frozen Deposit state:

- `pass` -> new Deposit in `validated` with the same id
- `fail` -> new Deposit in `rejected` with the same id
- `needs_human` -> original submitted Deposit unchanged

The helper does not mutate, persist, rank latest Validations, merge, emit events, or inspect a repository.

## Files Written

- `/Users/jakegearon/projects/watershed/tributary/README.md`
- `/Users/jakegearon/projects/watershed/tributary/src/tributary/__init__.py`
- `/Users/jakegearon/projects/watershed/tributary/src/tributary/validation.py`
- `/Users/jakegearon/projects/watershed/tributary/tests/test_validation.py`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/brief-20-tributary-validation-application.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/return-20.md`
- `/Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md`

## Verification

From `/Users/jakegearon/projects/watershed/tributary`:

- `uv run ruff format --check .` — passed
- `uv run ruff check .` — passed
- `uv run ty check` — passed
- `uv run pytest -q tests/test_validation.py tests/test_deposit.py` — passed: 51 passed
- `git diff --check -- /Users/jakegearon/projects/watershed/tributary /Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion /Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md` — passed

## Deviations

- Returned the original Deposit object for `needs_human`, because Validation authorizes no Deposit state transition in that case.
- Did not model latest-Validation ordering; that requires a registry or append-only record surface and is deliberately out of scope.

## Follow-Up

Merge is now technically reachable as a data model, but only if the input is a `validated` Deposit plus a pass Validation that cites the same Deposit. The next slice can mint `Merge` as an inert record, but must still avoid repository operations, sentrux, persistence, and automatic merge behavior.
