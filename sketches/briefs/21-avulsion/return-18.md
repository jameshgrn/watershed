# Return 18 — tributary Deposit v0

Brief: `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/brief-18-tributary-deposit-v0.md`
Engineer: Watermaster Avulsion
Returned at: 2026-05-28

## Summary

Scaffolded a local uv-managed `tributary` Python package and added the first fan-in seam record: `Deposit`. The slice includes state-specific file-change records, a canonical `FileChangeSet`, content-derived `deposit:` ids, and a submit helper that accepts only a protocol-shaped dispatch record in `state == "done"`.

The implementation stops at submitted Deposit records. It does not inspect worktrees, run git, import `distributary`, import dgov, create validation verdicts, merge, persist, emit events, or touch sentrux.

## Files Written

- `/Users/jakegearon/projects/watershed/tributary/README.md`
- `/Users/jakegearon/projects/watershed/tributary/pyproject.toml`
- `/Users/jakegearon/projects/watershed/tributary/uv.lock`
- `/Users/jakegearon/projects/watershed/tributary/src/tributary/__init__.py`
- `/Users/jakegearon/projects/watershed/tributary/src/tributary/_compat.py`
- `/Users/jakegearon/projects/watershed/tributary/src/tributary/deposit.py`
- `/Users/jakegearon/projects/watershed/tributary/tests/__init__.py`
- `/Users/jakegearon/projects/watershed/tributary/tests/test_deposit.py`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/brief-18-tributary-deposit-v0.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/return-18.md`
- `/Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md`

## Verification

From `/Users/jakegearon/projects/watershed/tributary`:

- `uv run ruff format --check .` — passed
- `uv run ruff check .` — passed
- `uv run ty check` — passed
- `uv run pytest -q tests/test_deposit.py` — passed: 26 passed
- `git diff --check -- /Users/jakegearon/projects/watershed/tributary /Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion /Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md /Users/jakegearon/projects/watershed/sketches/dgov-to-watershed-port-map.md` — passed

## Deviations

- Did not make `tributary` import `distributary`. The submit helper accepts a `DispatchRunRecord` protocol because `SKETCHES.md` says workers and seam records cross as data, not code imports.
- Kept the shared typed-contract registry out of scope. Claims are checked syntactically and for non-emptiness only.
- Did not add Deposit lifecycle transition helpers. Validation and Merge records should own those transitions when they exist.

## Follow-Up

Next slice should be `Validation` only if it consumes a submitted `Deposit`. It must not merge, persist, run sentrux, or widen file claims. The first validation work should likely be claim/file-change integrity over supplied data before semantic settlement.
