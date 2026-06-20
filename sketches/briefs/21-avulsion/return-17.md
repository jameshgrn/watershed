# Return 17 — distributary worker return envelope

Brief: `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/brief-17-distributary-worker-return.md`
Engineer: Watermaster Avulsion
Returned at: 2026-05-28

## Summary

Added `WorkerReturn`, a terminal worker telemetry envelope keyed by `dispatch_run_id`. It validates terminal payloads and applies itself to an active `DispatchRun`, producing the canonical terminal `DispatchRun` without introducing worker execution, worktree inspection, persistence, tributary, or Deposit.

## Files Written

- `/Users/jakegearon/projects/watershed/distributary/src/distributary/worker_return.py`
- `/Users/jakegearon/projects/watershed/distributary/src/distributary/__init__.py`
- `/Users/jakegearon/projects/watershed/distributary/tests/test_worker_return.py`
- `/Users/jakegearon/projects/watershed/distributary/README.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/brief-17-distributary-worker-return.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/return-17.md`
- `/Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md`

## Verification

From `/Users/jakegearon/projects/watershed/distributary`:

- `uv run ruff format --check .` — passed
- `uv run ruff check .` — passed
- `uv run ty check` — passed
- `uv run pytest -q tests/test_worker_return.py tests/test_dispatch_run.py tests/test_hello_ceremony.py` — passed: 41 passed
- `uv run pytest -q tests/test_plan.py tests/test_claims.py tests/test_dispatch_run.py tests/test_hello_ceremony.py tests/test_worker_return.py` — passed: 93 passed
- `git diff --check -- /Users/jakegearon/projects/watershed/distributary /Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion /Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md /Users/jakegearon/projects/watershed/sketches/dgov-to-watershed-port-map.md` — passed

## Deviations

- Named the watershed-side shape `WorkerReturn` rather than `WorkerExit` because dgov's `WorkerExit` includes `pane_slug`, which is runtime UI state forbidden by `dispatch-run-shape.md`.
- Did not add content-addressed file changes. That belongs to Deposit and `FileChangeSet`, not the worker return envelope.
