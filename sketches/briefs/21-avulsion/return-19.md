# Return 19 — tributary Validation v0

Brief: `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/brief-19-tributary-validation-v0.md`
Engineer: Watermaster Avulsion
Returned at: 2026-05-28

## Summary

Added v0 Validation support to tributary: frozen `Validation` records, `ValidationCheck` evidence, `SchemaPin` pins, content-derived `validation:` ids, an integrity validator for submitted Deposits, and a pure helper mapping Validation verdicts to the Deposit state they authorize.

The validator consumes supplied data only. It checks that the Deposit is submitted, that Deposit claims appear in an explicit `known_claims` tuple, and that the FileChangeSet exposes stable content identity. It does not mutate Deposits or run external checks.

## Files Written

- `/Users/jakegearon/projects/watershed/tributary/README.md`
- `/Users/jakegearon/projects/watershed/tributary/src/tributary/__init__.py`
- `/Users/jakegearon/projects/watershed/tributary/src/tributary/validation.py`
- `/Users/jakegearon/projects/watershed/tributary/tests/test_validation.py`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/brief-19-tributary-validation-v0.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/return-19.md`
- `/Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md`

## Verification

From `/Users/jakegearon/projects/watershed/tributary`:

- `uv run ruff format --check .` — passed
- `uv run ruff check .` — passed
- `uv run ty check` — passed
- `uv run pytest -q tests/test_validation.py tests/test_deposit.py` — passed: 46 passed
- `git diff --check -- /Users/jakegearon/projects/watershed/tributary /Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion /Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md` — passed

## Deviations

- Did not model full pressure-test, schema-check, or semantic-settlement evidence. This v0 record is an integrity Validation, not the full settlement stack.
- Represented `schema_pins` as frozen `tuple[SchemaPin, ...]` rather than a mutable `Mapping[str, int]`, preserving the SOP's pinning intent without mutable state.
- Did not mutate Deposit state. `authorized_deposit_state(validation)` derives `validated`, `rejected`, or `None`; a later registry/lifecycle slice can apply that authorization.
- Did not add a shared claim registry. `known_claims` is explicit supplied data for the validation run.

## Follow-Up

Next slice should not be Merge yet unless there is a concrete validated Deposit state transition surface. The next useful step is likely a small in-memory lifecycle helper or registry that applies `Validation` verdict authorization to a `Deposit` without persistence. Keep semantic settlement, sentrux, and repository merge out until their inputs are typed.
