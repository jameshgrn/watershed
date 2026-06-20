# Return 16 — distributary v0 outbound records

Brief: `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/brief-16-distributary-v0-outbound-records.md`
Engineer: FirePass trio
Received by: Watermaster Avulsion
Received at: 2026-05-28 11:05 EDT

## Summary

FirePass created the first executable `distributary` slice: a local uv-managed Python package with typed plan shapes, kernel-shaped file claim mirrors, a `PlanUnitFiles` -> `FileClaim` adapter, `DispatchRun` records, and tests proving the in-memory `PlanSpec` -> `PlanUnit` -> pending `DispatchRun` -> active `DispatchRun` path.

The FirePass tool timed out before returning a structured EngineerReturn. Avulsion reviewed and integrated the generated files directly, cleaned the package-local toolchain, tightened the hello ceremony back to pending -> active, and verified the gates.

## Files Written

- `/Users/jakegearon/projects/watershed/distributary/README.md`
- `/Users/jakegearon/projects/watershed/distributary/pyproject.toml`
- `/Users/jakegearon/projects/watershed/distributary/uv.lock`
- `/Users/jakegearon/projects/watershed/distributary/src/distributary/__init__.py`
- `/Users/jakegearon/projects/watershed/distributary/src/distributary/_compat.py`
- `/Users/jakegearon/projects/watershed/distributary/src/distributary/claims.py`
- `/Users/jakegearon/projects/watershed/distributary/src/distributary/dispatch_run.py`
- `/Users/jakegearon/projects/watershed/distributary/src/distributary/plan.py`
- `/Users/jakegearon/projects/watershed/distributary/tests/__init__.py`
- `/Users/jakegearon/projects/watershed/distributary/tests/test_claims.py`
- `/Users/jakegearon/projects/watershed/distributary/tests/test_dispatch_run.py`
- `/Users/jakegearon/projects/watershed/distributary/tests/test_hello_ceremony.py`
- `/Users/jakegearon/projects/watershed/distributary/tests/test_plan.py`

## Verification

From `/Users/jakegearon/projects/watershed/distributary`:

- `uv run ruff format --check .` — passed
- `uv run ruff check .` — passed
- `uv run ty check` — passed
- `uv run pytest -q` — passed before final path-normalization regression
- `uv run pytest -q tests/test_plan.py tests/test_claims.py tests/test_dispatch_run.py tests/test_hello_ceremony.py` — passed after final path-normalization regression: 75 passed
- `git diff --check -- /Users/jakegearon/projects/watershed/distributary /Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion /Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md /Users/jakegearon/projects/watershed/sketches/dgov-to-watershed-port-map.md` — passed

## Deviations

- FirePass timed out after writing files, so there was no structured FirePass return to accept.
- FirePass initially used `basedpyright`, a pytest marker with no local registration, and an unused type ignore. Avulsion replaced the type gate with `ty`, removed the unregistered marker, removed the unused ignore, and regenerated `uv.lock`.
- FirePass carried unconsumed dgov plan metadata into `PlanUnit` and `PlanSpec`. Avulsion trimmed the v0 plan records back to fields used by this slice.
- FirePass implemented terminal `DispatchRun` transitions and tests beyond the hello ceremony's pending -> active proof. Avulsion accepted them as contained lifecycle validation for the `DispatchRun` record, while trimming the hello ceremony test itself back to the requested active state.

## Follow-Up

Next slice should stay above the Rust kernel and add only the next consumed outbound record. A reasonable candidate is a worker-shaped return envelope from terminal dispatch state, but not worktrees, workers, CLI, persistence, tributary, or kernel binding.

Do not add `run_source`, `Deposit`, `Validation`, `Merge`, or `Baseline` until a specific consumer forces that shape.
