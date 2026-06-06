# Brief 16 — distributary v0 outbound records

State: sent
Compiled by: Watermaster Avulsion
Compiled at: 2026-05-28
Engineer: FirePass trio

## Source Utterance

"use a a firepass trio"

## Context

Watershed is moving useful dgov doctrine into watershed without carrying the old
Python monolith forward. The Rust kernel owns lawful motion. Python
`distributary/` owns orchestration around it.

Read these first:

- `/Users/jakegearon/projects/watershed/sketches/dgov-to-watershed-port-map.md`
- `/Users/jakegearon/projects/watershed/CANON.md`
- `/Users/jakegearon/projects/watershed/watershed-kernel/STOP_LINE.md`
- `/Users/jakegearon/projects/watershed/watershed-kernel/watershed-contracts/src/lib.rs`
- `/Users/jakegearon/projects/dgov/src/dgov/plan.py`
- `/Users/jakegearon/projects/dgov/src/dgov/dag_parser.py`
- `/Users/jakegearon/projects/dgov/src/dgov/dispatch_run.py`
- `/Users/jakegearon/projects/dgov/tests/test_dispatch_run.py`
- narrow `PlanUnitFiles` and file-conflict cases in `/Users/jakegearon/projects/dgov/tests/test_plan.py`

## Write Scope

You may create or edit only:

- `/Users/jakegearon/projects/watershed/distributary/pyproject.toml`
- `/Users/jakegearon/projects/watershed/distributary/uv.lock`
- `/Users/jakegearon/projects/watershed/distributary/src/distributary/**`
- `/Users/jakegearon/projects/watershed/distributary/tests/**`
- `/Users/jakegearon/projects/watershed/distributary/README.md`

Do not write outside `/Users/jakegearon/projects/watershed/distributary/`.

## What To Build

Build a minimal Python distributary package that proves the in-memory outbound
record path:

typed intent-shaped input -> `PlanSpec` -> `PlanUnit` -> kernel-shaped
`FileClaim` mirrors -> `DispatchRun` pending -> active.

Keep this v0 intentionally small.

## Required Types And Behavior

1. Scaffold a small Python package under `distributary/` with a real test
   harness. Prefer `uv`-managed `pyproject.toml`; keep dependencies minimal.
2. Port the plan data shapes:
   - `PlanUnitFiles`
   - `PlanUnit`
   - `PlanSpec`
   - `PlanIssue`
3. Port narrow plan validation:
   - slug format `^[a-z0-9-]+$`
   - path normalization and parent/child overlap detection
   - conflict detection for independent units with overlapping write claims
   - no conflict when overlapping units have dependency ordering
   - read-only files do not count as write claims
4. Add a kernel-shaped `FileClaim` mirror and `ClaimKind` enum matching the Rust
   contract shape, without binding to Rust:
   - `path`
   - `kind`
   - kinds: `ReadOnly`, `Exclusive`, `Shared`
5. Add an adapter from `PlanUnitFiles` to kernel-shaped `FileClaim` mirrors:
   - `read` -> `ReadOnly`
   - `create` / `edit` / `delete` / `touch` -> `Exclusive`
   - if the same path appears as both read and write-capable, write authority
     wins and only one `Exclusive` claim is emitted
   - preserve stable first-seen order as much as possible after write-wins
   - do not emit `Shared` until an actual source field consumes it
6. Port the `DispatchRun` record:
   - content-derived id with `disprun:` strategy tag
   - UTC tz-aware timestamp validation
   - lineage validation for `retried_from`, `forked_from`, `retry_index`,
     `fork_depth`
   - legal states: `pending`, `active`, `done`, `failed`, `timed_out`,
     `abandoned`
   - pending -> active transition preserving id and frozen input fields
   - no `run_source` field in v0
7. Add a hello-ceremony helper or test path that constructs:
   - a minimal intent-shaped dict or dataclass
   - a `PlanSpec` with one `PlanUnit`
   - `FileClaim` mirrors for that unit
   - a pending `DispatchRun`
   - the active `DispatchRun`

## Non-Goals

- No tributary code.
- No CLI.
- No worktrees.
- No real worker execution.
- No persistence or event store.
- No direct dgov package imports from watershed code or tests.
- No Python-to-Rust binding, FFI, subprocess call, or generated-schema loader.
- No kernel changes.
- No root governance docs.
- Do not mint `Deposit`, `Validation`, `Merge`, or `Baseline`.
- Do not port dgov runner, worker, prompt builder, sop bundler, policy drift,
  pane management, or persistence.

## Design Constraints

- Prefer frozen dataclasses or simple enums. Keep invalid states rejected early.
- Fail fast with clear `ValueError` or typed local exceptions; do not silently
  coerce illegal lineage.
- Keep code readable and explicit; no premature abstraction.
- Do not add compatibility shims for dgov imports. This is a clean watershed
  package, not a package alias.
- If a dgov behavior is useful but outside this first slice, flag it in the
  return instead of implementing it.

## Verification Gates

Run from `/Users/jakegearon/projects/watershed/distributary`:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest -q
```

If `uv run ty check` needs a package/dependency adjustment in `pyproject.toml`,
make the smallest package-local adjustment. Do not skip it silently.

## Return Shape

Return:

- summary of what changed
- files written
- verification commands and results
- any deviations from this Brief
- any follow-up needed before the next slice

## Push Back Welcome

Stop and report instead of implementing if:

- satisfying the Brief requires editing outside `distributary/`
- a kernel change appears necessary
- a dgov import seems necessary for the hello ceremony
- the package harness cannot be made local to `distributary/`
- the minimal scope starts pulling in worktrees, workers, CLI, persistence,
  events, or tributary
