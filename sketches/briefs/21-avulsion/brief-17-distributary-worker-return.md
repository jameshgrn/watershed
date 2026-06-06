# Brief 17 — distributary worker return envelope

State: accepted
Compiled by: Watermaster Avulsion
Compiled at: 2026-05-28
Engineer: Watermaster Avulsion

## Source Utterance

"agree"

## Context

The Source agreed with the next narrow move after Brief 16: add a terminal dispatch result or worker-shaped return envelope only if it helps the distributary -> tributary seam, and stop before worktrees, workers, CLI, persistence, tributary, or Deposit.

Relevant discipline:

- `/Users/jakegearon/projects/watershed/sops/dispatch-run-shape.md`
- `/Users/jakegearon/projects/watershed/sops/deposit-shape.md`
- `/Users/jakegearon/projects/watershed/sketches/dgov-to-watershed-port-map.md`
- `/Users/jakegearon/projects/dgov/src/dgov/types.py` (`WorkerExit` as history, not authority)

## Write Scope

- `/Users/jakegearon/projects/watershed/distributary/src/distributary/**`
- `/Users/jakegearon/projects/watershed/distributary/tests/**`
- `/Users/jakegearon/projects/watershed/distributary/README.md`
- `/Users/jakegearon/projects/watershed/sketches/briefs/21-avulsion/**`
- `/Users/jakegearon/projects/watershed/sketches/lineage/21-avulsion.md`

## Build

Add a small `WorkerReturn` envelope under `distributary/`:

- keyed by `dispatch_run_id`, not pane slug or worktree surface
- terminal states only: `done`, `failed`, `timed_out`, `abandoned`
- terminal telemetry: `exit_code`, `last_error`, `output_dir`, token counts, `iteration_count`, `terminated_at`
- UTC timestamp validation
- terminal payload validation aligned with `DispatchRun.complete_*`
- method to apply the envelope to an active `DispatchRun`

## Non-Goals

- No real worker execution.
- No worktree inspection.
- No git diff or file-change scan.
- No Deposit, Validation, Merge, or Baseline.
- No tributary code.
- No persistence, event store, or CLI.
- No direct dgov imports.
- No pane slug or terminal UI state.

## Verification

From `/Users/jakegearon/projects/watershed/distributary`:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest -q tests/test_worker_return.py tests/test_dispatch_run.py tests/test_hello_ceremony.py
```
